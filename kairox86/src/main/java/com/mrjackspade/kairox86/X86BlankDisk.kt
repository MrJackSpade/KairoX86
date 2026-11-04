package com.mrjackspade.kairox86

import java.io.OutputStream
import java.nio.ByteBuffer
import java.util.UUID

/**
 * A new machine's blank hard disk (KairoX86#162): an empty dynamic VHD, the image format 86Box reads
 * (its minivhd), which holds only a header and an empty block table until the guest writes to it,
 * so a 504 MB disk is a few KB on the device until it fills.
 *
 * The layout is the VHD specification's dynamic disk: a footer, the dynamic disk header at 512, the
 * block allocation table at 1536 (every entry unallocated), and the footer again at the end. Its
 * geometry is the disk's CHS, which 86Box takes from the footer as the drive's cylinders, heads and
 * sectors, and which the PC's BIOS then detects.
 */
class X86BlankDisk(val cylinders: Int, val heads: Int, val sectors: Int) {
    init {
        require(cylinders in 1..65535 && heads in 1..16 && sectors in 1..63) {
            "A VHD's geometry is at most 65535 cylinders, 16 heads and 63 sectors ($cylinders, $heads, $sectors)"
        }
    }

    /** The disk's size in bytes: every sector of its geometry. */
    val size: Long get() = cylinders.toLong() * heads * sectors * SECTOR

    /** Writes the whole empty image. [id] is the disk's unique ID, which VHDs keep in their footer. */
    fun write(output: OutputStream, id: UUID = UUID.randomUUID(), timestamp: Int = 0) {
        val blocks = ((size + BLOCK - 1) / BLOCK).toInt()
        val footer = footer(id, timestamp)
        output.write(footer)
        output.write(header(blocks))
        val table = ByteArray(((blocks * 4 + SECTOR - 1) / SECTOR) * SECTOR) { 0xFF.toByte() }
        output.write(table)
        output.write(footer)
    }

    private fun footer(id: UUID, timestamp: Int): ByteArray {
        val b = ByteBuffer.allocate(SECTOR)
        b.put("conectix".toByteArray(Charsets.US_ASCII))
        b.putInt(2)                       // features: reserved bit, always set
        b.putInt(0x00010000)              // file format version 1.0
        b.putLong(SECTOR.toLong())        // data offset: the dynamic header
        b.putInt(timestamp)               // seconds since 2000-01-01 UTC
        b.put("kx86".toByteArray(Charsets.US_ASCII))
        b.putInt(0x00010000)              // creator version
        b.put("Wi2k".toByteArray(Charsets.US_ASCII))
        b.putLong(size)                   // original size
        b.putLong(size)                   // current size
        b.putShort(cylinders.toShort())
        b.put(heads.toByte())
        b.put(sectors.toByte())
        b.putInt(DYNAMIC)
        val checksumAt = b.position()
        b.putInt(0)
        b.putLong(id.mostSignificantBits)
        b.putLong(id.leastSignificantBits)
        b.put(0)                          // not in a saved state
        val bytes = b.array()
        ByteBuffer.wrap(bytes).putInt(checksumAt, checksum(bytes))
        return bytes
    }

    private fun header(blocks: Int): ByteArray {
        val b = ByteBuffer.allocate(HEADER)
        b.put("cxsparse".toByteArray(Charsets.US_ASCII))
        b.putLong(-1L)                    // data offset: unused
        b.putLong((SECTOR + HEADER).toLong()) // the block table, right after this header
        b.putInt(0x00010000)              // header version 1.0
        b.putInt(blocks)                  // table entries
        b.putInt(BLOCK.toInt())           // block size
        val checksumAt = b.position()
        b.putInt(0)
        val bytes = b.array()             // the parent fields stay zero: no parent
        ByteBuffer.wrap(bytes).putInt(checksumAt, checksum(bytes))
        return bytes
    }

    companion object {
        const val SECTOR = 512
        private const val HEADER = 1024
        /** 2 MB blocks, the VHD default (minivhd's too). */
        private const val BLOCK = 2L * 1024 * 1024
        private const val DYNAMIC = 3

        /** The VHD checksum: the ones' complement of the sum of every byte, with the checksum field zero. */
        internal fun checksum(bytes: ByteArray): Int = bytes.sumOf { it.toInt() and 0xFF }.inv()
    }
}

/**
 * A new game's blank floppy (KairoX86#162): a raw image of the format's every sector, zero, as a new
 * unformatted disk is. 86Box takes its geometry from its size; DOS's FORMAT, or a game's own
 * "make a save disk", prepares it in the drive.
 */
class X86BlankFloppy(val id: String, val label: String, val cylinders: Int, val heads: Int, val sectors: Int) {
    /** The image's size in bytes. */
    val size: Int get() = cylinders * heads * sectors * X86BlankDisk.SECTOR

    fun write(output: OutputStream) {
        val track = ByteArray(sectors * X86BlankDisk.SECTOR)
        repeat(cylinders * heads) { output.write(track) }
    }

    companion object {
        /** The PC's floppy formats, from the 5¼″ drives to the 3½″ (DOS's FORMAT /F sizes). */
        val all = listOf(
            X86BlankFloppy("floppy-360k", "360 KB · 5¼″ DD", 40, 2, 9),
            X86BlankFloppy("floppy-720k", "720 KB · 3½″ DD", 80, 2, 9),
            X86BlankFloppy("floppy-1200k", "1.2 MB · 5¼″ HD", 80, 2, 15),
            X86BlankFloppy("floppy-1440k", "1.44 MB · 3½″ HD", 80, 2, 18))
    }
}
