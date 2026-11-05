package com.mrjackspade.kairox86

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.TreeMap

class VhdTest {
    @get:Rule val temp = TemporaryFolder()

    private val blockSectors = 4096
    private val sectors = 3L * blockSectors

    private fun pattern(lba: Long) = ByteArray(Vhd.SECTOR) { ((lba * 31 + it) % 251).toByte() }

    private fun sum(bytes: ByteArray, range: IntRange, at: Int): Int {
        var s = 0
        for (i in range) if (i !in at until at + 4) s += bytes[i].toInt() and 0xff
        return s.inv()
    }

    /** A dynamic image of [sectors] whose first and last blocks hold [pattern], the middle one never written. */
    private fun dynamic(file: File) {
        val footer = ByteArray(512)
        ByteBuffer.wrap(footer).order(ByteOrder.BIG_ENDIAN).apply {
            put(0, "conectix".toByteArray()); putInt(8, 2); putInt(12, 0x10000); putLong(16, 512)
            putLong(40, sectors * 512); putLong(48, sectors * 512); putShort(56, 12); put(58, 16); put(59, 64)
            putInt(60, 3); put(68, ByteArray(16) { (it + 1).toByte() })
        }
        ByteBuffer.wrap(footer).order(ByteOrder.BIG_ENDIAN).putInt(64, sum(footer, 0 until 512, 64))
        val header = ByteArray(1024)
        ByteBuffer.wrap(header).order(ByteOrder.BIG_ENDIAN).apply {
            put(0, "cxsparse".toByteArray()); putLong(8, -1); putLong(16, 1536); putInt(24, 0x10000); putInt(28, 3); putInt(32, blockSectors * 512)
        }
        file.outputStream().use { out ->
            out.write(footer)
            out.write(header)
            val bat = ByteBuffer.allocate(512).order(ByteOrder.BIG_ENDIAN)
            bat.putInt(4).putInt(-1).putInt(4 + 1 + blockSectors)
            while (bat.hasRemaining()) bat.putInt(-1)
            out.write(bat.array())
            for (block in listOf(0L, 2L)) {
                out.write(ByteArray(512) { 0xff.toByte() })
                for (i in 0 until blockSectors) out.write(pattern(block * blockSectors + i))
            }
            out.write(footer)
        }
    }

    @Test
    fun aDynamicImageReadsByBlock() {
        val file = temp.newFile("parent.vhd")
        dynamic(file)
        Vhd.open(file).use { disk ->
            assertEquals(sectors, disk.count)
            for (lba in listOf(0L, 5L, 4095L, 8192L, sectors - 1)) assertArrayEquals(pattern(lba), disk.read(lba))
            assertArrayEquals(ByteArray(512), disk.read(4096))
        }
    }

    @Test
    fun aChildHoldsOnlyTheChangedSectors() {
        val parentFile = temp.newFile("parent.vhd")
        dynamic(parentFile)
        val child = File(temp.root, "child.vhd")
        val changed = TreeMap<Long, ByteArray>(mapOf(5L to ByteArray(512) { 7 }, 9000L to ByteArray(512) { 9 }))
        Vhd.open(parentFile).use { parent -> Vhd.writeChild(child, parent, parentFile, changed) }
        val bytes = child.readBytes()
        val footer = bytes.copyOfRange(bytes.size - 512, bytes.size)
        assertArrayEquals(footer, bytes.copyOfRange(0, 512))
        val f = ByteBuffer.wrap(footer).order(ByteOrder.BIG_ENDIAN)
        assertEquals("conectix", String(footer, 0, 8))
        assertEquals(4, f.getInt(60))
        assertEquals(sectors * 512, f.getLong(48))
        assertEquals(sum(footer, 0 until 512, 64), f.getInt(64))
        val header = bytes.copyOfRange(512, 1536)
        val h = ByteBuffer.wrap(header).order(ByteOrder.BIG_ENDIAN)
        assertEquals("cxsparse", String(header, 0, 8))
        assertEquals(sum(header, 0 until 1024, 36), h.getInt(36))
        assertArrayEquals(ByteArray(16) { (it + 1).toByte() }, header.copyOfRange(40, 56))
        assertEquals((parentFile.lastModified() / 1000 - 946684800L).toInt(), h.getInt(56))
        assertEquals("parent.vhd", String(header, 64, 20, Charsets.UTF_16BE))
        // The parent's absolute path, as minivhd looks for it
        assertEquals(0x57326B75, h.getInt(576))
        val locator = String(bytes, h.getLong(592).toInt(), h.getInt(584), Charsets.UTF_16LE)
        assertEquals(parentFile.absolutePath, locator)
        val bat = ByteBuffer.wrap(bytes, h.getLong(16).toInt(), 12).order(ByteOrder.BIG_ENDIAN)
        val table = IntArray(3) { bat.getInt() }
        assertEquals(-1, table[1])
        // Each sector: its bit set and its data when changed, clear (the parent's) otherwise
        fun read(lba: Long): ByteArray? {
            val entry = table[(lba / blockSectors).toInt()]
            if (entry == -1) return null
            val inBlock = (lba % blockSectors).toInt()
            val bit = bytes[entry * 512 + inBlock / 8].toInt() and (0x80 ushr (inBlock % 8))
            if (bit == 0) return null
            return bytes.copyOfRange((entry + 1 + inBlock) * 512, (entry + 2 + inBlock) * 512)
        }
        assertArrayEquals(ByteArray(512) { 7 }, read(5))
        assertArrayEquals(ByteArray(512) { 9 }, read(9000))
        assertEquals(null, read(4))
        assertEquals(null, read(6))
        assertEquals(null, read(4096))
        assertEquals(null, read(9001))
    }
}
