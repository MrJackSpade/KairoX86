package com.mrjackspade.kairox86

import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.SortedMap
import java.util.TreeMap
import java.util.UUID

/** A disk by its 512-byte sectors. */
interface Sectors {
    /** How many sectors the disk has. */
    val count: Long

    fun read(lba: Long): ByteArray
    fun write(lba: Long, data: ByteArray)
}

/** [base] with sectors written over it in memory ([changed]), [base] itself never written. */
class SectorChanges(private val base: Sectors) : Sectors {
    val changed: SortedMap<Long, ByteArray> = TreeMap()
    override val count get() = base.count

    override fun read(lba: Long): ByteArray = changed[lba]?.copyOf() ?: base.read(lba)

    override fun write(lba: Long, data: ByteArray) {
        require(data.size == Vhd.SECTOR) { "A sector is ${Vhd.SECTOR} bytes, not ${data.size}" }
        require(lba in 0 until count) { "Sector $lba is past the disk's $count" }
        changed[lba] = data.copyOf()
    }
}

/**
 * Virtual PC's disk images (Microsoft's VHD format, as 86Box's minivhd reads and writes them): a
 * fixed or dynamic image read ([open]), and a differencing image made over one ([writeChild]).
 */
object Vhd {
    const val SECTOR = 512
    private const val FIXED = 2
    private const val DYNAMIC = 3
    private const val DIFFERENCING = 4
    private const val UNUSED = 0xffffffffL
    /** VHD time counts seconds from 2000-01-01 00:00 UTC. */
    private const val EPOCH = 946684800L
    private const val LOCATOR_W2KU = 0x57326B75

    /** An image's footer: what [writeChild] copies of its parent. */
    class Footer(val bytes: ByteArray) {
        private val buffer get() = ByteBuffer.wrap(bytes).order(ByteOrder.BIG_ENDIAN)
        val size: Long get() = buffer.getLong(48)
        val type: Int get() = buffer.getInt(60)
        val uuid: ByteArray get() = bytes.copyOfRange(68, 84)
        /** The disk's geometry (cylinders at 56, heads at 58, sectors a track at 59). */
        val cylinders: Int get() = buffer.getShort(56).toInt() and 0xffff
        val heads: Int get() = bytes[58].toInt() and 0xff
        val sectorsPerTrack: Int get() = bytes[59].toInt() and 0xff
    }

    /** An open image: fixed or dynamic, read-only. */
    class Disk internal constructor(private val file: RandomAccessFile, val footer: Footer, private val table: IntArray?,
                                    private val blockSectors: Int, private val bitmapSectors: Int) : Sectors, AutoCloseable {
        override val count = footer.size / SECTOR

        override fun read(lba: Long): ByteArray {
            require(lba in 0 until count) { "Sector $lba is past the disk's $count" }
            val out = ByteArray(SECTOR)
            val at = if (table == null) lba * SECTOR else {
                val entry = table[(lba / blockSectors).toInt()].toLong() and 0xffffffffL
                // A block never written reads as zeros
                if (entry == UNUSED) return out
                (entry + bitmapSectors + lba % blockSectors) * SECTOR
            }
            file.seek(at)
            file.readFully(out)
            return out
        }

        override fun write(lba: Long, data: ByteArray) = throw UnsupportedOperationException("A VHD is opened read-only")
        override fun close() = file.close()
    }

    /** The image [file], fixed or dynamic; a differencing image fails (nothing here reads one). */
    fun open(file: File): Disk {
        val raf = RandomAccessFile(file, "r")
        try {
            check(raf.length() >= SECTOR) { "${file.name} is too small for a VHD" }
            val footer = ByteArray(SECTOR)
            raf.seek(raf.length() - SECTOR)
            raf.readFully(footer)
            check(String(footer, 0, 8, Charsets.US_ASCII) == "conectix") { "${file.name} has no VHD footer" }
            val parsed = Footer(footer)
            return when (parsed.type) {
                FIXED -> Disk(raf, parsed, null, 0, 0)
                DYNAMIC -> {
                    val header = ByteArray(1024)
                    raf.seek(ByteBuffer.wrap(footer).order(ByteOrder.BIG_ENDIAN).getLong(16))
                    raf.readFully(header)
                    check(String(header, 0, 8, Charsets.US_ASCII) == "cxsparse") { "${file.name} has no dynamic disk header" }
                    val h = ByteBuffer.wrap(header).order(ByteOrder.BIG_ENDIAN)
                    val entries = h.getInt(28)
                    val blockBytes = h.getInt(32)
                    check(blockBytes > 0 && blockBytes % SECTOR == 0) { "${file.name} has blocks of $blockBytes bytes" }
                    val bat = ByteArray(entries * 4)
                    raf.seek(h.getLong(16))
                    raf.readFully(bat)
                    val b = ByteBuffer.wrap(bat).order(ByteOrder.BIG_ENDIAN)
                    val blockSectors = blockBytes / SECTOR
                    Disk(raf, parsed, IntArray(entries) { b.getInt(it * 4) }, blockSectors, bitmapSectors(blockSectors))
                }
                else -> error("${file.name} is a VHD of type ${parsed.type}, not a fixed or dynamic one")
            }
        } catch (failure: Exception) {
            raf.close()
            throw failure
        }
    }

    /** The sectors of a block's bitmap: one bit for each sector, a whole number of sectors. */
    private fun bitmapSectors(blockSectors: Int) = (blockSectors / 8 + SECTOR - 1) / SECTOR

    /**
     * Writes [target] as a differencing image over [parent] (the file [parentFile]) holding the
     * sectors [changed] and nothing else, as minivhd makes one: every other sector reads from the
     * parent. Blocks are [blockSectors] long, as 86Box's own children (2 MiB).
     */
    fun writeChild(target: File, parent: Disk, parentFile: File, changed: SortedMap<Long, ByteArray>, blockSectors: Int = 4096) {
        require(blockSectors > 0 && blockSectors % 8 == 0) { "Blocks of $blockSectors sectors" }
        val size = parent.footer.size
        val blocks = ((size / SECTOR + blockSectors - 1) / blockSectors).toInt()
        val tableSectors = (blocks * 4 + SECTOR - 1) / SECTOR
        val path = parentFile.absolutePath.toByteArray(Charsets.UTF_16LE)
        val locatorSpace = (path.size / SECTOR + 1) * SECTOR
        val tableAt = 3L * SECTOR
        val locatorAt = tableAt + tableSectors.toLong() * SECTOR
        var next = (locatorAt + locatorSpace) / SECTOR
        val bitmap = bitmapSectors(blockSectors)
        val byBlock = changed.keys.groupBy { (it / blockSectors).toInt() }.toSortedMap()
        val table = IntArray(blocks) { -1 }
        for (block in byBlock.keys) {
            check(block < blocks) { "Sector ${byBlock.getValue(block).first()} is past the disk" }
            table[block] = next.toInt()
            next += bitmap + blockSectors
        }

        val now = (System.currentTimeMillis() / 1000 - EPOCH).toInt()
        val footer = parent.footer.bytes.copyOf()
        ByteBuffer.wrap(footer).order(ByteOrder.BIG_ENDIAN).apply {
            putInt(8, 2)
            putInt(12, 0x00010000)
            putLong(16, SECTOR.toLong())
            putInt(24, now)
            "kx86".toByteArray(Charsets.US_ASCII).copyInto(footer, 28)
            putInt(32, 0x00010000)
            "Wi2k".toByteArray(Charsets.US_ASCII).copyInto(footer, 36)
            putInt(60, DIFFERENCING)
            val uuid = UUID.randomUUID()
            putLong(68, uuid.mostSignificantBits)
            putLong(76, uuid.leastSignificantBits)
            put(84, 0.toByte())
        }
        checksum(footer, 64, 0 until 512)

        val header = ByteArray(1024)
        ByteBuffer.wrap(header).order(ByteOrder.BIG_ENDIAN).apply {
            "cxsparse".toByteArray(Charsets.US_ASCII).copyInto(header, 0)
            putLong(8, -1L)
            putLong(16, tableAt)
            putInt(24, 0x00010000)
            putInt(28, blocks)
            putInt(32, blockSectors * SECTOR)
            parent.footer.uuid.copyInto(header, 40)
            putInt(56, (parentFile.lastModified() / 1000 - EPOCH).toInt())
            val name = parentFile.name.toByteArray(Charsets.UTF_16BE)
            check(name.size <= 512) { "${parentFile.name} is too long a name for a VHD's parent" }
            name.copyInto(header, 64)
            // One locator, the parent's absolute path: minivhd tries a relative one, the child's
            // folder, then this
            putInt(576, LOCATOR_W2KU)
            putInt(580, locatorSpace)
            putInt(584, path.size)
            putLong(592, locatorAt)
        }
        checksum(header, 36, 0 until 1024)

        val partial = File(target.path + ".part")
        try {
            RandomAccessFile(partial, "rw").use { out ->
                out.setLength(0)
                out.write(footer)
                out.write(header)
                val bat = ByteBuffer.allocate(tableSectors * SECTOR).order(ByteOrder.BIG_ENDIAN)
                table.forEach { bat.putInt(it) }
                while (bat.hasRemaining()) bat.putInt(-1)
                out.write(bat.array())
                out.write(path.copyOf(locatorSpace))
                for ((block, lbas) in byBlock) {
                    val bits = ByteArray(bitmap * SECTOR)
                    val data = ByteArray(blockSectors * SECTOR)
                    for (lba in lbas) {
                        val inBlock = (lba % blockSectors).toInt()
                        bits[inBlock / 8] = (bits[inBlock / 8].toInt() or (0x80 ushr (inBlock % 8))).toByte()
                        changed.getValue(lba).copyInto(data, inBlock * SECTOR)
                    }
                    check(out.filePointer == table[block].toLong() * SECTOR) { "A block of ${target.name} out of place" }
                    out.write(bits)
                    out.write(data)
                }
                out.write(footer)
            }
            check(partial.renameTo(target)) { "Could not make ${target.path}" }
        } catch (failure: Exception) {
            if (partial.exists() && !partial.delete()) failure.addSuppressed(IllegalStateException("${partial.path} was left behind"))
            throw failure
        }
    }

    /**
     * The footer that makes [cylinders] × [heads] × [sectorsPerTrack] sectors of raw data a fixed
     * VHD, appended after them.
     */
    fun fixedFooter(cylinders: Int, heads: Int, sectorsPerTrack: Int): ByteArray {
        require(cylinders in 1..0xffff && heads in 1..255 && sectorsPerTrack in 1..255) { "No VHD geometry $cylinders/$heads/$sectorsPerTrack" }
        val size = cylinders.toLong() * heads * sectorsPerTrack * SECTOR
        val footer = ByteArray(SECTOR)
        "conectix".toByteArray(Charsets.US_ASCII).copyInto(footer, 0)
        ByteBuffer.wrap(footer).order(ByteOrder.BIG_ENDIAN).apply {
            putInt(8, 2)
            putInt(12, 0x00010000)
            putLong(16, -1L)
            putInt(24, (System.currentTimeMillis() / 1000 - EPOCH).toInt())
            "kx86".toByteArray(Charsets.US_ASCII).copyInto(footer, 28)
            putInt(32, 0x00010000)
            "Wi2k".toByteArray(Charsets.US_ASCII).copyInto(footer, 36)
            putLong(40, size)
            putLong(48, size)
            putShort(56, cylinders.toShort())
            put(58, heads.toByte())
            put(59, sectorsPerTrack.toByte())
            putInt(60, FIXED)
            val uuid = UUID.randomUUID()
            putLong(68, uuid.mostSignificantBits)
            putLong(76, uuid.leastSignificantBits)
        }
        checksum(footer, 64, 0 until 512)
        return footer
    }

    /** Stores the ones' complement of the sum of [bytes] in [range] at [at], as VHD's checksums are. */
    private fun checksum(bytes: ByteArray, at: Int, range: IntRange) {
        ByteBuffer.wrap(bytes).order(ByteOrder.BIG_ENDIAN).putInt(at, 0)
        var sum = 0
        for (i in range) sum += bytes[i].toInt() and 0xff
        ByteBuffer.wrap(bytes).order(ByteOrder.BIG_ENDIAN).putInt(at, sum.inv())
    }
}
