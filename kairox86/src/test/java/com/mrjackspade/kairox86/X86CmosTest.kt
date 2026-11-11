package com.mrjackspade.kairox86

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

/** A preset's stored CMOS kept for the disk the player chose (KairoX86#341). */
class X86CmosTest {
    private val stored = File("src/main/assets/presets/486/nvr/486ap4.nvr").readBytes()

    private fun ByteArray.at(index: Int) = this[index].toInt() and 0xff
    private fun checksum(cmos: ByteArray) = (0x10..0x2d).sumOf { cmos.at(it) }
    private fun storedChecksum(cmos: ByteArray) = cmos.at(0x2e) shl 8 or cmos.at(0x2f)

    @Test
    fun theStoredDiskWrittenBackIsTheStoredCmos() {
        // The 486 preset's own 504 MB disk, as its BIOS saved it
        assertArrayEquals(stored, X86Cmos.Award450.withDriveC(stored, X86Cmos.Disk(1024, 16, 63)))
    }

    @Test
    fun aLargerDiskIsWhatTheBiosAutoDetectionSaves() {
        // The PVI-486AP4's IDE HDD AUTO DETECTION, a 2 GB disk (4161 cylinders), its LBA option saved: these bytes
        val cmos = X86Cmos.Award450.withDriveC(stored, X86Cmos.Disk(4161, 16, 63))
        val saved = mapOf(0x12 to 0xf0, 0x19 to 0x31, 0x26 to 0x41, 0x27 to 0x10, 0x28 to 0x10, 0x29 to 0xff, 0x2a to 0xff,
            0x2b to 0x40, 0x2c to 0x10, 0x2d to 0x3f, 0x3b to 0x07)
        for ((index, value) in saved) assertEquals("%02Xh".format(index), value, cmos.at(index))
        assertEquals(checksum(cmos), storedChecksum(cmos))
        // Nothing else moves
        for (index in stored.indices.filter { it !in saved && it != 0x2e && it != 0x2f }) assertEquals("%02Xh".format(index), stored.at(index), cmos.at(index))
    }

    @Test
    fun noDiskIsDriveCNone() {
        val cmos = X86Cmos.Award450.withDriveC(stored, null)
        assertEquals(0x00, cmos.at(0x12) and 0xf0)
        assertEquals(0, cmos.at(0x19))
        for (index in 0x26..0x2d) assertEquals(0, cmos.at(index))
        assertEquals(0, cmos.at(0x3b) and 0x04)
        assertEquals(checksum(cmos), storedChecksum(cmos))
    }

    @Test
    fun aDetectedDiskLeavesTheCmosAsItIs() {
        val tx97 = File("src/main/assets/presets/pentium/nvr/tx97.nvr").readBytes()
        assertArrayEquals(tx97, X86Cmos.Detected.withDriveC(tx97, X86Cmos.Disk(1423, 16, 63)))
    }
}
