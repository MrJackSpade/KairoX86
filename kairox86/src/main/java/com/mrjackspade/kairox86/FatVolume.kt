package com.mrjackspade.kairox86

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * The FAT16 or FAT32 file system of a hard disk's first partition (DOS's and Windows 9x's), on
 * [disk]: its files found and read by path, and files written into a folder as DOS writes them
 * (their clusters, both FATs, the folder's entry and FAT32's free count). Written sectors go to
 * [disk] (a [SectorChanges] keeps them off the image beneath).
 */
class FatVolume(private val disk: Sectors) {
    /** A folder entry: [name] its 8.3 name ("SYSTEM.INI"), [longName] its Windows name when it has one. */
    class Entry(val name: String, val longName: String?, internal val raw: ByteArray, internal val sector: Long, internal val offset: Int) {
        val attributes get() = raw[11].toInt() and 0xff
        val folder get() = attributes and DIRECTORY != 0
        val hidden get() = attributes and (HIDDEN or SYSTEM) != 0
        val size get() = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN).getInt(28).toLong() and 0xffffffffL
        internal val cluster get() = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN).let {
            ((it.getShort(20).toLong() and 0xffff) shl 16) or (it.getShort(26).toLong() and 0xffff)
        }
        /** Whether [text] names this entry, by its 8.3 name or its Windows name, whatever the case. */
        fun named(text: String) = name.equals(text, ignoreCase = true) || longName?.equals(text, ignoreCase = true) == true
    }

    private val start: Long
    private val sectorsPerCluster: Int
    private val reserved: Int
    private val fats: Int
    private val fatSectors: Long
    private val rootEntries: Int
    private val rootCluster: Long
    private val fsInfo: Int
    private val clusters: Long
    private val fat32: Boolean
    private val firstData: Long

    init {
        val mbr = disk.read(0)
        check(mbr[510] == 0x55.toByte() && mbr[511] == 0xaa.toByte()) { "The disk has no partition table" }
        val m = ByteBuffer.wrap(mbr).order(ByteOrder.LITTLE_ENDIAN)
        val type = mbr[446 + 4].toInt() and 0xff
        check(type in setOf(0x04, 0x06, 0x0b, 0x0c, 0x0e)) { "The disk's first partition is of type %02x, not FAT16 or FAT32".format(type) }
        start = m.getInt(446 + 8).toLong() and 0xffffffffL
        val boot = disk.read(start)
        val b = ByteBuffer.wrap(boot).order(ByteOrder.LITTLE_ENDIAN)
        check(b.getShort(11).toInt() == Vhd.SECTOR) { "The partition's sectors are not ${Vhd.SECTOR} bytes" }
        sectorsPerCluster = boot[13].toInt() and 0xff
        check(sectorsPerCluster > 0 && sectorsPerCluster and (sectorsPerCluster - 1) == 0) { "The partition has $sectorsPerCluster sectors a cluster" }
        reserved = b.getShort(14).toInt() and 0xffff
        fats = boot[16].toInt() and 0xff
        rootEntries = b.getShort(17).toInt() and 0xffff
        val total = (b.getShort(19).toInt() and 0xffff).toLong().takeIf { it != 0L } ?: (b.getInt(32).toLong() and 0xffffffffL)
        fatSectors = (b.getShort(22).toInt() and 0xffff).toLong().takeIf { it != 0L } ?: (b.getInt(36).toLong() and 0xffffffffL)
        val rootSectors = (rootEntries * 32 + Vhd.SECTOR - 1) / Vhd.SECTOR
        firstData = start + reserved + fats * fatSectors + rootSectors
        clusters = (total - (reserved + fats * fatSectors + rootSectors)) / sectorsPerCluster
        check(clusters >= 4085) { "The partition is FAT12" }
        fat32 = clusters >= 65525
        rootCluster = if (fat32) b.getInt(44).toLong() and 0x0fffffff else 0
        fsInfo = if (fat32) b.getShort(48).toInt() and 0xffff else 0
    }

    private val end = if (fat32) 0x0ffffff8L else 0xfff8L

    /** The entries of the folder at [path] ("WINDOWS/SYSTEM", "" for the root), found by either name. */
    fun list(path: String): List<Entry> = entries(folderCluster(path))

    /** The entry at [path], or null when there is none. */
    fun find(path: String): Entry? {
        val parent = path.substringBeforeLast('/', "")
        val name = path.substringAfterLast('/')
        return entries(folderCluster(parent)).firstOrNull { it.named(name) }
    }

    /** The bytes of the file [entry]. */
    fun read(entry: Entry): ByteArray {
        check(!entry.folder) { "${entry.name} is a folder" }
        val out = ByteArray(entry.size.toInt())
        var at = 0
        for (cluster in chain(entry.cluster)) {
            for (i in 0 until sectorsPerCluster) {
                if (at >= out.size) break
                val sector = disk.read(clusterSector(cluster) + i)
                val n = minOf(Vhd.SECTOR, out.size - at)
                sector.copyInto(out, at, 0, n)
                at += n
            }
        }
        check(at == out.size) { "${entry.name}'s clusters hold less than its size" }
        return out
    }

    /**
     * Writes [data] as the file [source] names (its 8.3 name, attributes and time) in the folder at
     * [folder], over the file of that name there (keeping its entry, and Windows name) or as a new
     * one. A new file whose source has a Windows name that its 8.3 name doesn't give fails.
     */
    fun write(folder: String, source: Entry, data: ByteArray) {
        val dir = folderCluster(folder)
        val existing = entries(dir).firstOrNull { it.named(source.longName ?: source.name) || it.named(source.name) }
        check(existing?.folder != true) { "$folder/${source.name} is a folder" }
        val first = allocate(data)
        if (existing != null) {
            free(existing.cluster)
            val raw = existing.raw.copyOf()
            stamp(raw, source, first, data.size.toLong())
            writeEntry(existing.sector, existing.offset, raw)
        } else {
            check(source.longName == null || source.longName.equals(source.name, ignoreCase = true)) {
                "${source.longName} needs a Windows name, which is not written"
            }
            val raw = source.raw.copyOf()
            stamp(raw, source, first, data.size.toLong())
            val (sector, offset) = freeSlot(dir)
            writeEntry(sector, offset, raw)
        }
    }

    /** [raw] as [source]'s file, at cluster [first] with [size] bytes: its attributes (archived) and write time. */
    private fun stamp(raw: ByteArray, source: Entry, first: Long, size: Long) {
        val r = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN)
        raw[11] = (source.attributes or ARCHIVE).toByte()
        // The write time and date, as a copy keeps them
        source.raw.copyInto(raw, 22, 22, 26)
        r.putShort(20, (first ushr 16).toShort())
        r.putShort(26, first.toShort())
        r.putInt(28, size.toInt())
    }

    private fun writeEntry(sector: Long, offset: Int, raw: ByteArray) {
        val bytes = disk.read(sector)
        raw.copyInto(bytes, offset, 0, 32)
        disk.write(sector, bytes)
    }

    /** A free entry of the folder at [dir] (0 for FAT16's root), the folder grown a cluster when it has none. */
    private fun freeSlot(dir: Long): Pair<Long, Int> {
        for (sector in folderSectors(dir)) {
            val bytes = disk.read(sector)
            for (offset in 0 until Vhd.SECTOR step 32) {
                val first = bytes[offset].toInt() and 0xff
                if (first == 0 || first == 0xe5) return sector to offset
            }
        }
        check(dir != 0L) { "The root folder is full" }
        val last = chain(dir).last()
        val added = allocateClusters(1).single()
        setFat(last, added)
        val sector = clusterSector(added)
        for (i in 0 until sectorsPerCluster) disk.write(sector + i, ByteArray(Vhd.SECTOR))
        return sector to 0
    }

    /** The cluster of the folder at [path] (0 for FAT16's root), found by either name of each part. */
    private fun folderCluster(path: String): Long {
        var cluster = rootCluster
        for (part in path.split('/').filter { it.isNotEmpty() }) {
            val entry = checkNotNull(entries(cluster).firstOrNull { it.named(part) }) { "No folder $path" }
            check(entry.folder) { "$part in $path is not a folder" }
            cluster = entry.cluster
        }
        return cluster
    }

    private fun folderSectors(cluster: Long): Sequence<Long> =
        if (cluster == 0L) {
            check(!fat32) { "A FAT32 folder at cluster 0" }
            val rootStart = start + reserved + fats * fatSectors
            (0 until (rootEntries * 32 + Vhd.SECTOR - 1) / Vhd.SECTOR).asSequence().map { rootStart + it }
        } else chain(cluster).flatMap { c -> (0 until sectorsPerCluster).asSequence().map { clusterSector(c) + it } }

    private fun entries(cluster: Long): List<Entry> {
        val out = ArrayList<Entry>()
        val long = StringBuilder()
        for (sector in folderSectors(cluster)) {
            val bytes = disk.read(sector)
            for (offset in 0 until Vhd.SECTOR step 32) {
                val first = bytes[offset].toInt() and 0xff
                if (first == 0) return out
                val attributes = bytes[offset + 11].toInt() and 0xff
                if (first == 0xe5) {
                    long.clear()
                    continue
                }
                if (attributes == LONG_NAME) {
                    // Each long-name entry holds 13 characters; they come last part first
                    val part = StringBuilder()
                    for (at in LONG_NAME_CHARACTERS) {
                        val c = ((bytes[offset + at + 1].toInt() and 0xff) shl 8) or (bytes[offset + at].toInt() and 0xff)
                        if (c == 0 || c == 0xffff) break
                        part.append(c.toChar())
                    }
                    if (first and 0x40 != 0) long.clear()
                    long.insert(0, part)
                    continue
                }
                if (attributes and VOLUME != 0) {
                    long.clear()
                    continue
                }
                val raw = bytes.copyOfRange(offset, offset + 32)
                val base = String(raw, 0, 8, Charsets.ISO_8859_1).trimEnd().let { if (raw[0] == 0x05.toByte()) "å" + it.drop(1) else it }
                val ext = String(raw, 8, 3, Charsets.ISO_8859_1).trimEnd()
                val name = if (ext.isEmpty()) base else "$base.$ext"
                if (name != "." && name != "..") out += Entry(name, long.toString().ifEmpty { null }, raw, sector, offset)
                long.clear()
            }
        }
        return out
    }

    private fun clusterSector(cluster: Long): Long {
        check(cluster in 2 until clusters + 2) { "Cluster $cluster is outside the partition" }
        return firstData + (cluster - 2) * sectorsPerCluster
    }

    private fun chain(first: Long): Sequence<Long> = sequence {
        if (first == 0L) return@sequence
        var cluster = first
        var steps = 0L
        while (cluster < end) {
            check(cluster >= 2 && cluster < clusters + 2) { "A cluster chain reaches $cluster" }
            check(++steps <= clusters) { "A cluster chain loops" }
            yield(cluster)
            cluster = fat(cluster)
        }
    }

    private fun fatPlace(cluster: Long): Pair<Long, Int> {
        val byte = cluster * if (fat32) 4 else 2
        return byte / Vhd.SECTOR to (byte % Vhd.SECTOR).toInt()
    }

    private fun fat(cluster: Long): Long {
        val (sector, offset) = fatPlace(cluster)
        val b = ByteBuffer.wrap(disk.read(start + reserved + sector)).order(ByteOrder.LITTLE_ENDIAN)
        return if (fat32) b.getInt(offset).toLong() and 0x0fffffff else b.getShort(offset).toLong() and 0xffff
    }

    /** Sets [cluster]'s entry to [value] in every FAT (FAT32's top four bits kept, as they are reserved). */
    private fun setFat(cluster: Long, value: Long) {
        val (sector, offset) = fatPlace(cluster)
        for (copy in 0 until fats) {
            val at = start + reserved + copy * fatSectors + sector
            val bytes = disk.read(at)
            val b = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
            if (fat32) b.putInt(offset, (b.getInt(offset) and 0xf0000000.toInt()) or (value.toInt() and 0x0fffffff))
            else b.putShort(offset, value.toShort())
            disk.write(at, bytes)
        }
    }

    /** Writes [data] into newly taken clusters; returns the first (0 for no data, as DOS keeps an empty file). */
    private fun allocate(data: ByteArray): Long {
        if (data.isEmpty()) return 0
        val clusterBytes = sectorsPerCluster * Vhd.SECTOR
        val taken = allocateClusters(((data.size + clusterBytes - 1) / clusterBytes))
        taken.forEachIndexed { index, cluster ->
            for (i in 0 until sectorsPerCluster) {
                val sector = ByteArray(Vhd.SECTOR)
                val from = index * clusterBytes + i * Vhd.SECTOR
                if (from < data.size) data.copyInto(sector, 0, from, minOf(data.size, from + Vhd.SECTOR))
                disk.write(clusterSector(cluster) + i, sector)
            }
        }
        return taken.first()
    }

    /** Takes [n] free clusters, chained in order, the last ending the chain; FAT32's free count follows. */
    private fun allocateClusters(n: Int): List<Long> {
        val hint = if (fat32) fsInfoField(492).takeIf { it in 2 until clusters + 2 } ?: 2L else 2L
        val taken = ArrayList<Long>(n)
        var cluster = hint
        var looked = 0L
        while (taken.size < n) {
            check(looked++ < clusters) { "The partition is full" }
            if (fat(cluster) == 0L) taken += cluster
            cluster = if (cluster + 1 >= clusters + 2) 2 else cluster + 1
        }
        taken.forEachIndexed { i, c -> setFat(c, if (i + 1 < taken.size) taken[i + 1] else if (fat32) 0x0fffffff else 0xffff) }
        adjustFree(-n.toLong(), taken.last() + 1)
        return taken
    }

    private fun free(first: Long) {
        val chain = chain(first).toList()
        for (cluster in chain) setFat(cluster, 0)
        adjustFree(chain.size.toLong(), null)
    }

    /** FAT32's FSInfo: the free count moved by [by] (when it is known) and the next free hint set to [next]. */
    private fun adjustFree(by: Long, next: Long?) {
        if (!fat32 || fsInfo == 0 || fsInfo == 0xffff) return
        val at = start + fsInfo
        val bytes = disk.read(at)
        val b = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
        check(b.getInt(0) == 0x41615252 && b.getInt(484) == 0x61417272) { "The partition's FSInfo sector is not one" }
        val free = b.getInt(488).toLong() and 0xffffffffL
        if (free != 0xffffffffL) b.putInt(488, (free + by).toInt())
        if (next != null) b.putInt(492, next.toInt())
        disk.write(at, bytes)
    }

    private fun fsInfoField(offset: Int): Long =
        ByteBuffer.wrap(disk.read(start + fsInfo)).order(ByteOrder.LITTLE_ENDIAN).getInt(offset).toLong() and 0xffffffffL

    companion object {
        private const val HIDDEN = 0x02
        private const val SYSTEM = 0x04
        private const val VOLUME = 0x08
        private const val DIRECTORY = 0x10
        private const val ARCHIVE = 0x20
        private const val LONG_NAME = 0x0f
        private val LONG_NAME_CHARACTERS = intArrayOf(1, 3, 5, 7, 9, 14, 16, 18, 20, 22, 24, 28, 30)
    }
}
