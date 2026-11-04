package com.mrjackspade.kairox86

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.util.UUID

/** A new machine's blank hard disk, an empty dynamic VHD (KairoX86#162). */
class X86BlankDiskTest {
    private val disk = X86BlankDisk(1024, 16, 63)
    private val bytes = ByteArrayOutputStream().also { disk.write(it, UUID(1, 2), 0) }.toByteArray()
    private fun at(offset: Int) = ByteBuffer.wrap(bytes, offset, bytes.size - offset).slice()

    @Test
    fun itIsTheVhdSpecificationsDynamicLayout() {
        val footer = at(0)
        assertEquals("conectix", String(bytes, 0, 8, Charsets.US_ASCII))
        assertEquals(512L, footer.getLong(16))
        assertEquals(disk.size, footer.getLong(40))
        assertEquals(disk.size, footer.getLong(48))
        assertEquals(1024, footer.getShort(56).toInt() and 0xFFFF)
        assertEquals(16, footer.get(58).toInt())
        assertEquals(63, footer.get(59).toInt())
        assertEquals(3, footer.getInt(60))
        val header = at(512)
        assertEquals("cxsparse", String(bytes, 512, 8, Charsets.US_ASCII))
        assertEquals(1536L, header.getLong(16))
        val blocks = ((disk.size + (2 shl 20) - 1) / (2 shl 20)).toInt()
        assertEquals(blocks, header.getInt(28))
        assertEquals(2 shl 20, header.getInt(32))
        // Every block unallocated, then the footer again, at the end of a whole number of sectors.
        val table = (blocks * 4 + 511) / 512 * 512
        assertEquals(1536 + table + 512, bytes.size)
        for (i in 0 until blocks * 4) assertEquals(0xFF.toByte(), bytes[1536 + i])
        assertArrayEquals(bytes.copyOfRange(0, 512), bytes.copyOfRange(bytes.size - 512, bytes.size))
    }

    @Test
    fun itsChecksumsHold() {
        fun holds(start: Int, length: Int, field: Int) {
            val part = bytes.copyOfRange(start, start + length)
            val stored = ByteBuffer.wrap(part).getInt(field)
            ByteBuffer.wrap(part).putInt(field, 0)
            assertEquals(X86BlankDisk.checksum(part), stored)
        }
        holds(0, 512, 64)
        holds(512, 1024, 36)
    }

    @Test
    fun aBlankFloppyIsEveryZeroSectorOfItsFormat() {
        // DOS's own sizes, which 86Box reads a raw image's geometry from.
        assertEquals(listOf(368_640, 737_280, 1_228_800, 1_474_560), X86BlankFloppy.all.map { it.size })
        for (floppy in X86BlankFloppy.all) {
            val image = ByteArrayOutputStream().also { floppy.write(it) }.toByteArray()
            assertEquals(floppy.id, floppy.size, image.size)
            assertEquals(floppy.id, true, image.all { it == 0.toByte() })
        }
    }

    @Test
    fun a504MegabyteDiskIsAFewKilobytes() {
        assertEquals(528_482_304L, disk.size)
        assertEquals(1536 + 1024 + 512, bytes.size)
    }
}
