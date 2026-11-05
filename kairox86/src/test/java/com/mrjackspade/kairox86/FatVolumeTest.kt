package com.mrjackspade.kairox86

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.nio.ByteBuffer
import java.nio.ByteOrder

class FatVolumeTest {
    /** A disk in memory, sectors never written reading as zeros. */
    class MemoryDisk(override val count: Long) : Sectors {
        val sectors = HashMap<Long, ByteArray>()
        override fun read(lba: Long): ByteArray = sectors[lba]?.copyOf() ?: ByteArray(Vhd.SECTOR)
        override fun write(lba: Long, data: ByteArray) {
            require(data.size == Vhd.SECTOR)
            sectors[lba] = data.copyOf()
        }
    }

    private class Layout(val fat32: Boolean) {
        val start = 63L
        val reserved = if (fat32) 32 else 1
        val clusters = if (fat32) 70000L else 5000L
        val rootEntries = if (fat32) 0 else 512
        val fatSectors = ((clusters + 2) * (if (fat32) 4 else 2) + 511) / 512
        val rootSectors = (rootEntries * 32 + 511) / 512
        val firstData = start + reserved + 2 * fatSectors + rootSectors
        val total = reserved + 2 * fatSectors + rootSectors + clusters
        fun cluster(c: Long) = firstData + (c - 2)
    }

    private val systemIni = ByteArray(100) { (it * 3).toByte() }
    private val longFile = ByteArray(700) { (it * 5).toByte() }

    /**
     * A one-partition disk holding WINDOWS (cluster 3) with SYSTEM.INI (cluster 4, 100 bytes) and
     * "Long File Name.txt" (LONGFI~1.TXT, clusters 5 and 6), one sector a cluster.
     */
    private fun format(fat32: Boolean): MemoryDisk {
        val l = Layout(fat32)
        val disk = MemoryDisk(l.start + l.total)
        val mbr = ByteArray(512)
        ByteBuffer.wrap(mbr).order(ByteOrder.LITTLE_ENDIAN).apply {
            put(446 + 4, (if (fat32) 0x0c else 0x06).toByte())
            putInt(446 + 8, l.start.toInt())
            putInt(446 + 12, l.total.toInt())
            put(510, 0x55); put(511, 0xaa.toByte())
        }
        disk.write(0, mbr)
        val boot = ByteArray(512)
        ByteBuffer.wrap(boot).order(ByteOrder.LITTLE_ENDIAN).apply {
            putShort(11, 512); put(13, 1); putShort(14, l.reserved.toShort()); put(16, 2); putShort(17, l.rootEntries.toShort())
            putInt(32, l.total.toInt())
            if (fat32) {
                putInt(36, l.fatSectors.toInt()); putInt(44, 2); putShort(48, 1)
            } else putShort(22, l.fatSectors.toShort())
            put(510, 0x55); put(511, 0xaa.toByte())
        }
        disk.write(l.start, boot)
        if (fat32) {
            val info = ByteArray(512)
            ByteBuffer.wrap(info).order(ByteOrder.LITTLE_ENDIAN).apply {
                putInt(0, 0x41615252); putInt(484, 0x61417272); putInt(488, (l.clusters - 5).toInt()); putInt(492, 7)
            }
            disk.write(l.start + 1, info)
        }
        val end = if (fat32) 0x0fffffffL else 0xffffL
        val fat = mapOf(0L to (if (fat32) 0x0ffffff8L else 0xfff8L), 1L to end, 2L to (if (fat32) end else 0L), 3L to end, 4L to end, 5L to 6L, 6L to end)
        for (copy in 0..1) for ((cluster, value) in fat) setFat(disk, l, copy, cluster, value)
        val windows = entry("WINDOWS    ", 0x10, 3, 0)
        val root = if (fat32) l.cluster(2) else l.start + l.reserved + 2 * l.fatSectors
        disk.write(root, entries(entry("TESTDISK   ", 0x08, 0, 0), windows))
        disk.write(l.cluster(3), entries(entry(".          ", 0x10, 3, 0), entry("..         ", 0x10, 0, 0),
            *longName("Long File Name.txt"), entry("LONGFI~1TXT", 0x20, 5, longFile.size),
            entry("SYSTEM  INI", 0x20, 4, systemIni.size), entry("HIDDEN  INI", 0x22, 0, 0)))
        disk.write(l.cluster(4), systemIni.copyOf(512))
        disk.write(l.cluster(5), longFile.copyOfRange(0, 512))
        disk.write(l.cluster(6), longFile.copyOfRange(512, 700).copyOf(512))
        return disk
    }

    private fun setFat(disk: MemoryDisk, l: Layout, copy: Int, cluster: Long, value: Long) {
        val bytes = cluster * if (l.fat32) 4 else 2
        val at = l.start + l.reserved + copy * l.fatSectors + bytes / 512
        val sector = disk.read(at)
        val b = ByteBuffer.wrap(sector).order(ByteOrder.LITTLE_ENDIAN)
        if (l.fat32) b.putInt((bytes % 512).toInt(), value.toInt()) else b.putShort((bytes % 512).toInt(), value.toShort())
        disk.write(at, sector)
    }

    private fun fat(disk: Sectors, l: Layout, copy: Int, cluster: Long): Long {
        val bytes = cluster * if (l.fat32) 4 else 2
        val b = ByteBuffer.wrap(disk.read(l.start + l.reserved + copy * l.fatSectors + bytes / 512)).order(ByteOrder.LITTLE_ENDIAN)
        return if (l.fat32) b.getInt((bytes % 512).toInt()).toLong() and 0x0fffffff else b.getShort((bytes % 512).toInt()).toLong() and 0xffff
    }

    private fun entry(name: String, attributes: Int, cluster: Long, size: Int): ByteArray {
        val raw = ByteArray(32)
        name.toByteArray(Charsets.ISO_8859_1).copyInto(raw)
        ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN).apply {
            put(11, attributes.toByte()); putShort(20, (cluster ushr 16).toShort()); putShort(22, 0x6000); putShort(24, 0x2c21)
            putShort(26, cluster.toShort()); putInt(28, size)
        }
        return raw
    }

    /** [name]'s long-name entries, as they come before its 8.3 entry: last part first. */
    private fun longName(name: String): Array<ByteArray> {
        val parts = name.chunked(13)
        return parts.indices.reversed().map { index ->
            val raw = ByteArray(32)
            raw[0] = ((index + 1) or if (index == parts.size - 1) 0x40 else 0).toByte()
            raw[11] = 0x0f
            val chars = parts[index].map { it.code } + if (parts[index].length < 13) listOf(0) + List(12 - parts[index].length) { 0xffff } else emptyList()
            intArrayOf(1, 3, 5, 7, 9, 14, 16, 18, 20, 22, 24, 28, 30).forEachIndexed { i, at ->
                raw[at] = chars[i].toByte(); raw[at + 1] = (chars[i] shr 8).toByte()
            }
            raw
        }.toTypedArray()
    }

    private fun entries(vararg list: ByteArray): ByteArray {
        val sector = ByteArray(512)
        list.forEachIndexed { i, raw -> raw.copyInto(sector, i * 32) }
        return sector
    }

    @Test
    fun filesAreFoundByEitherNameAndRead() {
        for (fat32 in listOf(true, false)) {
            val volume = FatVolume(format(fat32))
            assertEquals(listOf("LONGFI~1.TXT", "SYSTEM.INI", "HIDDEN.INI"), volume.list("windows").map { it.name })
            assertArrayEquals(systemIni, volume.read(volume.find("WINDOWS/system.ini")!!))
            val long = volume.find("Windows/long file name.txt")!!
            assertEquals("Long File Name.txt", long.longName)
            assertArrayEquals(longFile, volume.read(long))
            assertTrue(volume.find("WINDOWS/HIDDEN.INI")!!.hidden)
            assertNull(volume.find("WINDOWS/WIN.INI"))
            // The volume label is no file
            assertEquals(listOf("WINDOWS"), volume.list("").map { it.name })
        }
    }

    @Test
    fun aFileIsWrittenOverTheOneOfItsName() {
        for (fat32 in listOf(true, false)) {
            val l = Layout(fat32)
            val base = format(fat32)
            val before = base.sectors.mapValues { it.value.copyOf() }
            val disk = SectorChanges(base)
            val volume = FatVolume(disk)
            val source = FatVolume(format(fat32)).find("WINDOWS/SYSTEM.INI")!!
            val data = ByteArray(1500) { (it * 7 + 1).toByte() }
            volume.write("WINDOWS", source, data)
            val written = volume.find("WINDOWS/SYSTEM.INI")!!
            assertArrayEquals(data, volume.read(written))
            assertEquals(0x20, written.attributes)
            // Its old cluster is free, the new chain in both FATs alike
            assertEquals(0L, fat(disk, l, 0, 4))
            for (c in 2L..20L) assertEquals(fat(disk, l, 0, c), fat(disk, l, 1, c))
            assertArrayEquals(longFile, volume.read(volume.find("WINDOWS/LONGFI~1.TXT")!!))
            if (fat32) {
                val info = ByteBuffer.wrap(disk.read(l.start + 1)).order(ByteOrder.LITTLE_ENDIAN)
                assertEquals(l.clusters - 5 - 3 + 1, info.getInt(488).toLong())
            }
            // Nothing beneath was written
            assertEquals(before.keys, base.sectors.keys)
            for ((lba, bytes) in before) assertArrayEquals(bytes, base.sectors[lba])
        }
    }

    @Test
    fun aNewFileGoesIntoTheFolderWhichGrowsWhenFull() {
        val source = FatVolume(format(true))
        val sourceEntry = source.find("WINDOWS/SYSTEM.INI")!!
        val disk = SectorChanges(format(true))
        val volume = FatVolume(disk)
        // A sector of a cluster holds 16 entries; the folder has 7, so the tenth new file grows it
        val names = (1..12).map { "NEW$it.INI" }
        for ((i, name) in names.withIndex()) {
            val other = FatVolume(renamed(format(true), name))
            volume.write("WINDOWS", other.find("WINDOWS/$name")!!, ByteArray(10 + i) { it.toByte() })
        }
        val listed = volume.list("WINDOWS").map { it.name }
        assertEquals(listOf("LONGFI~1.TXT", "SYSTEM.INI", "HIDDEN.INI") + names, listed)
        for ((i, name) in names.withIndex()) assertArrayEquals(ByteArray(10 + i) { it.toByte() }, volume.read(volume.find("WINDOWS/$name")!!))
        assertArrayEquals(systemIni, volume.read(volume.find("WINDOWS/SYSTEM.INI")!!))
        assertNotNull(sourceEntry)
    }

    @Test
    fun aNewFileNeedingAWindowsNameFails() {
        val volume = FatVolume(SectorChanges(format(true)))
        val long = FatVolume(format(true)).find("WINDOWS/Long File Name.txt")!!
        volume.write("WINDOWS", long, ByteArray(3))
        // Into another folder, where it is new
        val other = SectorChanges(format(true))
        val target = FatVolume(other)
        assertThrows(IllegalStateException::class.java) { target.write("", long, ByteArray(3)) }
    }

    /** [disk] with SYSTEM.INI renamed [name] (8.3, "NEW1.INI"). */
    private fun renamed(disk: MemoryDisk, name: String): MemoryDisk {
        val l = Layout(true)
        val sector = disk.read(l.cluster(3))
        val base = name.substringBefore('.').padEnd(8)
        val ext = name.substringAfter('.').padEnd(3)
        "$base$ext".toByteArray(Charsets.ISO_8859_1).copyInto(sector, 5 * 32)
        disk.write(l.cluster(3), sector)
        return disk
    }
}
