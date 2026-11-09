package com.mrjackspade.kairox86

import com.mrjackspade.kairox86.X86Library.DiskKind
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

/** KairoX86#340 (a disk's kinds from its name) and #334 (the files a CD image is made of). */
class DiskKindTest {
    @Test
    fun aRawImageCanBeAFloppyOrTheHardDisk() {
        // Its extension says nothing of what it is: the player tells by the size shown beside it (KairoX86#340)
        assertEquals(setOf(DiskKind.FLOPPY, DiskKind.HARD_DISK), X86Library.diskKinds("win98.img"))
        assertEquals(setOf(DiskKind.FLOPPY, DiskKind.HARD_DISK), X86Library.diskKinds("DISK.IMA"))
        // A format that says its kind keeps it
        assertEquals(setOf(DiskKind.FLOPPY), X86Library.diskKinds("protected.86f"))
        assertEquals(setOf(DiskKind.CD), X86Library.diskKinds("game.iso"))
        assertEquals(setOf(DiskKind.HARD_DISK), X86Library.diskKinds("disk.vhd"))
        assertEquals(emptySet<DiskKind>(), X86Library.diskKinds("readme.txt"))
    }

    @Test
    fun aRawHardDiskTakesItsGeometryFromItsPartitionTable() {
        val heads = 16
        val sectors = 63
        val cylinders = 100
        val size = cylinders.toLong() * heads * sectors * 512
        val mbr = ByteArray(512)
        mbr[446 + 4] = 0x06 // FAT16
        mbr[446 + 5] = (heads - 1).toByte()
        mbr[446 + 6] = sectors.toByte()
        mbr[510] = 0x55
        mbr[511] = 0xAA.toByte()
        assertEquals(X86HardDisk.Geometry(sectors, heads, cylinders), X86HardDisk.geometry("disk.img", size) { _, _ -> mbr })
        // No partition table: no geometry
        assertThrows(IllegalArgumentException::class.java) { X86HardDisk.geometry("disk.img", size) { _, _ -> ByteArray(512) } }
        // Not a whole number of cylinders
        assertThrows(IllegalArgumentException::class.java) { X86HardDisk.geometry("disk.img", size + 512) { _, _ -> mbr } }
    }

    @Test
    fun aCdIndexNeedsItsTracks() {
        val cue = "FILE \"Game (Track 1).bin\" BINARY\n  TRACK 01 MODE1/2352\nFILE track2.wav WAVE\n"
        assertEquals(listOf("Game (Track 1).bin", "track2.wav"), X86Library.companions("Game.cue", emptyList()) { cue })
        assertEquals(listOf("Game.img", "Game.sub"), X86Library.companions("Game.ccd", listOf("Game.img", "Game.sub")) { "" })
        assertEquals(listOf("Game.img"), X86Library.companions("Game.ccd", listOf("Game.img")) { "" })
        assertEquals(listOf("Game.mdf"), X86Library.companions("Game.mds", emptyList()) { "" })
        assertEquals(emptyList<String>(), X86Library.companions("Game.iso", emptyList()) { error("an ISO is not read") })
        assertThrows(IllegalArgumentException::class.java) { X86Library.companions("Game.cue", emptyList()) { "FILE \"data/track.bin\" BINARY" } }
    }

    @Test
    fun aCdsTrackIsNoDiskOfItsOwn() {
        fun image(path: String, size: Long) = X86Entry(path, "content://$path", path, size, 0, "disk", disk = true)
        val images = listOf(image("Game/Game.ccd", 800), image("Game/Game.img", 700_000_000), image("Game/Game.sub", 1),
            image("Other/win98.img", 811_597_824), image("Other/boot.img", 1_474_560))
        assertEquals(listOf("Game/Game.ccd", "Game/Game.sub", "Other/win98.img", "Other/boot.img"),
            X86Library.withoutTracks(images).map { it.path })
    }
}
