package com.mrjackspade.kairox86

import java.io.InputStream
import java.io.OutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.zip.CRC32

/**
 * The hard disk DOSBox-X gives a booted guest for a drive mounted from an archive (eXo's
 * `mount e game.zip`): at `BOOT` its `convertdrivefat` turns every mounted drive that isn't a disk
 * image into a FAT hard disk on the next free IDE position (KairoX86#223). A ZIP drive has no write
 * folder, so it reports no free space and the disk is read-only: every entry marked read-only and
 * the FAT's spare clusters reserved. This is DOSBox-X's own `fatFromDOSDrive` (src/ints/bios_disk.cpp)
 * for that case, with its drive cache's 8.3 names (src/dos/drive_cache.cpp) as its ZIP drive lists
 * them, at its DOS 7.1 and code page 437: the same sectors, byte for byte.
 */
object DosboxFat {
    /** An entry of the archive: [name] its name in its folder, a file's [size], its DOS [date] and [time]. */
    class Entry(val name: String, val folder: Boolean, val size: Long, val date: Int, val time: Int,
                val children: List<Entry> = emptyList(), val member: Any? = null)

    private const val SECTOR = 512
    private const val HEADS = 255
    private const val SPT = 63
    private const val SECT_BOOT = 32
    private const val ATTR_READ_ONLY = 0x01
    private const val ATTR_DIRECTORY = 0x10
    private const val ATTR_ARCHIVE = 0x20
    private const val ATTR_LONG_NAME = 0x0f
    private const val ATTR_PENDING_SHORT_NAME = 0x80

    /** The date and time PhysFS gives a folder the archive doesn't list itself (time 0, as UTC). */
    val IMPLICIT_DATE = packDate(1970, 1, 1)
    const val IMPLICIT_TIME = 0

    /** DOS_PackDate: the year is kept to its low 7 bits after 1980, as DOSBox-X keeps it. */
    fun packDate(year: Int, month: Int, day: Int): Int = (((year - 1980) and 0x7f) shl 9) or ((month and 0x3f) shl 5) or (day and 0x1f)

    // ---- 8.3 names (DOS_Drive_Cache) ----

    private class Info(val orgname: String, var shortname: String = "", var shortNr: Int = 0)

    /**
     * The 8.3 names DOSBox-X's drive cache gives the entries of one folder, named [names] in the
     * order its ZIP drive lists them (PhysFS: by strcmp), "." and ".." first as it lists them: the
     * cache's ReadDir, which makes each name in that order before sorting the folder.
     */
    fun shortNames(names: List<String>): List<String> {
        val fileList = ArrayList<Info>()
        val longNameList = ArrayList<Info>()
        for (dot in listOf(".", "..")) fileList += Info(dot, dot)
        val made = names.map { name ->
            val info = Info(name)
            createShortName(fileList, longNameList, info)
            fileList += info
            info.shortname
        }
        return made
    }

    private fun createShortName(fileList: List<Info>, longNameList: MutableList<Info>, info: Info) {
        var tmp = upcase(info.orgname)
        var createShort = tmp.contains(' ')
        tmp = tmp.replace(" ", "")
        var pos = tmp.indexOf('.')
        val len: Int
        if (pos >= 0) {
            // Ignore preceding '.' if the extension is longer than 3
            if (tmp.length - pos > 4 || (pos == 0 && tmp != "." && tmp != "..")) {
                tmp = tmp.trimStart('.')
                createShort = true
            }
            pos = tmp.indexOf('.')
            len = if (pos >= 0) pos else tmp.length
        } else len = tmp.length
        if (tmp != "." && tmp != ".." && notEightThree(tmp)) {
            createShort = true
            tmp = String(tmp.map { c -> if (c.code <= 32 || c.code == 127 || c in "\"+=,;:<>[]|\\?*") '_' else c }.toCharArray())
        }
        createShort = createShort || len > 8
        if (!createShort) createShort = getLongName(fileList, tmp) >= 0
        if (createShort) {
            info.shortNr = createShortNameId(longNameList, tmp)
            check(info.shortNr <= 9999999) { "~9999999 same name files overflow" }
            val number = info.shortNr.toString()
            val toCopy = if (len + number.length + 1 > 8) 8 - number.length - 1 else len
            var short = tmp.substring(0, minOf(toCopy, tmp.length)) + "~" + number
            if (pos >= 0) short += tmp.substring(tmp.lastIndexOf('.')).take(4)
            info.shortname = short.take(12)
            // keep the list sorted for createShortNameId
            val at = longNameList.indexOfFirst { strcmp(info.shortname, it.shortname) < 0 }
            if (at < 0) longNameList += info else longNameList.add(at, info)
        } else info.shortname = tmp
        info.shortname = removeTrailingDot(info.shortname)
    }

    private fun removeTrailingDot(name: String): String =
        if (name.endsWith('.') && name != "." && name != "..") name.dropLast(1) else name

    /** GetLongName: the entry [fileList] has of the 8.3 name [shortName], -1 for none (a binary search, as the cache's). */
    private fun getLongName(fileList: List<Info>, shortName: String): Int {
        if (fileList.isEmpty()) return -1
        val name = removeTrailingDot(shortName)
        var low = 0
        var high = fileList.size - 1
        while (low <= high) {
            val mid = (low + high) / 2
            val res = strcmp(name, fileList[mid].shortname)
            if (res > 0) low = mid + 1 else if (res < 0) high = mid - 1 else return mid
        }
        // LFN on (DOS 7.1, lfn = auto): any entry of that long name, whatever the case
        if (name.isNotEmpty()) fileList.forEachIndexed { i, f -> if (f.orgname.equals(name, ignoreCase = true)) return i }
        // A Wine-style short name: ABCD~###
        if (name.length < 8 || name[4] != '~' || name[5] == '.' || name[6] == '.' || name[7] == '.') return -1
        fileList.forEachIndexed { i, f -> if (wineHash(f.orgname) == name) return i }
        return -1
    }

    private fun createShortNameId(longNameList: List<Info>, name: String): Int {
        if (longNameList.isEmpty()) return 1
        var foundNr = 0
        var low = 0
        var high = longNameList.size - 1
        while (low <= high) {
            var mid = (low + high) / 2
            val res = compareShortname(name, longNameList[mid].shortname)
            if (res > 0) low = mid + 1 else if (res < 0) high = mid - 1 else {
                do {
                    foundNr = longNameList[mid].shortNr
                    mid++
                } while (mid < longNameList.size && compareShortname(name, longNameList[mid].shortname) == 0)
                break
            }
        }
        return foundNr + 1
    }

    private fun compareShortname(compareName: String, shortName: String): Int {
        val tilde = shortName.indexOf('~')
        if (tilde < 0) return strcmp(compareName, shortName)
        var count1 = tilde
        val numberSize = shortName.substring(tilde).indexOf('.').let { if (it < 0) shortName.length - tilde else it }
        var count2 = compareName.indexOf('.').let { if (it < 0) compareName.length else it }
        if (count2 > 8) count2 = 8
        if (count2 > count1 + numberSize) count1 = count2 - numberSize
        return strncmp(compareName, shortName, count1)
    }

    private fun wineHash(name: String): String {
        val hashChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
        val invalid = "*?<>|\"+=,;[] å~."
        val b = name.toByteArray(Charsets.ISO_8859_1)
        var hash = 0xbeef
        fun lower(c: Int) = if (c in 'A'.code..'Z'.code) c + 32 else c
        for (p in 0 until b.size - 1) hash = ((hash shl 3) xor (hash ushr 5) xor lower(b[p].toInt()) xor (lower(b[p + 1].toInt()) shl 8)) and 0xffff
        hash = ((hash shl 3) xor (hash ushr 5) xor lower(b.last().toInt())) and 0xffff
        var ext = -1
        for (p in 1 until b.size - 1) if (b[p] == '.'.code.toByte()) ext = p
        val out = StringBuilder()
        var i = 4
        var p = 0
        while (i > 0) {
            if (p == b.size || p == ext) break
            val c = b[p].toInt()
            out.append(if (c < 0 || invalid.indexOf(c.toChar()) >= 0) '_' else c.toChar().uppercaseChar())
            i--
            p++
        }
        while (i-- >= 0) out.append('~')
        out.append(hashChars[(hash shr 10) and 0x1f]).append(hashChars[(hash shr 5) and 0x1f]).append(hashChars[hash and 0x1f])
        if (ext >= 0) {
            out.append('.')
            var e = ext + 1
            var n = 3
            while (n > 0 && e < b.size) {
                val c = b[e].toInt()
                out.append(if (c < 0 || invalid.indexOf(c.toChar()) >= 0) '_' else c.toChar().uppercaseChar())
                n--
                e++
            }
        }
        return out.toString()
    }

    /** filename_not_8x3 for code page 437. */
    private fun notEightThree(n: String): Boolean {
        var i = 0
        var at = 0
        fun bad(c: Char) = c.code <= 32 || c.code == 127 || c in "\"+=,;:<>[]|\\?*"
        while (at < n.length && n[at] != '.') {
            if (bad(n[at])) return true
            i++
            at++
        }
        if (i == 0 || i > 8) return true
        if (at == n.length) return false
        at++
        i = 0
        while (at < n.length) {
            if (n[at] == '.' || bad(n[at])) return true
            i++
            at++
        }
        return i > 3
    }

    private fun upcase(name: String): String {
        check(name.all { it.code in 1..127 }) { "$name: DOSBox-X's names past ASCII are not reproduced here" }
        return name.uppercase()
    }

    private fun strcmp(a: String, b: String): Int {
        for (i in 0 until minOf(a.length, b.length)) if (a[i] != b[i]) return a[i].code - b[i].code
        return a.length - b.length
    }

    private fun strncmp(a: String, b: String, n: Int): Int = strcmp(a.take(n), b.take(n))

    // ---- The disk (fatFromDOSDrive) ----

    /** A disk laid out: write it with [write]; [sectors] is where DOSBox-X's disk ends. */
    class Disk internal constructor(
        internal val fatSz: Int, internal val sectorsPerCluster: Int, internal val fat: ByteArray, internal val root: ByteArray,
        internal val dirs: ByteArray, internal val files: List<Pair<Entry, Long>>, internal val mbr: ByteArray,
        internal val boot: ByteArray, internal val fsinfo: ByteArray, internal val fat1: Long, internal val fat2: Long,
        internal val rootStart: Long, internal val dirsStart: Long, internal val filesStart: Long, internal val filesEnd: Long,
        val sectors: Long)

    /** DOSBox-X's disk of the archive whose top folder holds [entries]. */
    fun layout(entries: List<Entry>): Disk {
        // The used size, each file counted as whole 32 KiB clusters
        var used = 0L
        fun sum(list: List<Entry>) {
            for (e in list) if (e.folder) sum(e.children) else used += (e.size + 32 * 1024 - 1) / (32 * 1024) * (32 * 1024)
        }
        sum(entries)
        val totalMB = used / (1024 * 1024)
        // Read-only: no free space added
        val (fatSz, spc) = when {
            totalMB >= 3072 -> 32 to 64
            totalMB >= 2048 -> 32 to 32
            totalMB >= 384 -> 16 to 64
            totalMB >= 192 -> 16 to 32
            totalMB >= 96 -> 16 to 16
            totalMB >= 48 -> 16 to 8
            totalMB >= 12 -> 16 to 4
            totalMB >= 4 -> 16 to 1
            totalMB >= 2 -> 12 to 4
            totalMB >= 1 -> 12 to 2
            else -> 12 to 1
        }
        val b = Builder(fatSz, spc)
        b.setFat(0, 0xFFFFFF8)
        b.setFat(1, 0xFFFFFFF)
        if (fatSz != 32) b.root = ArrayList<ByteArray>().apply { repeat(512) { add(ByteArray(32)) } }
        b.parseDir(entries, 0, 0, IMPLICIT_DATE, IMPLICIT_TIME, IMPLICIT_DATE, IMPLICIT_TIME)

        val bytesPerCluster = spc * SECTOR
        val entriesPerCluster = bytesPerCluster / 32
        var fileCluster = (2 + b.dirs.size / entriesPerCluster).toLong()
        val files = ArrayList<Pair<Entry, Long>>()
        var fileSect = 0L
        for (list in listOf(b.root, b.dirs)) for ((index, e) in list.withIndex()) {
            val size = le32(e, 28)
            if (size == 0L || (e[11].toInt() and 0x3f) == ATTR_LONG_NAME) continue
            put16(e, 20, (fileCluster ushr 16).toInt())
            put16(e, 26, fileCluster.toInt())
            val clusters = (size + bytesPerCluster - 1) / bytesPerCluster
            for (c in fileCluster until fileCluster + clusters - 1) b.setFat(c, c + 1)
            b.setFat(fileCluster + clusters - 1, 0xFFFFFFF)
            files += checkNotNull((if (list === b.root) b.rootFiles else b.dirFiles)[index]) { "A file entry with no file" } to fileSect
            fileCluster += clusters
            fileSect += clusters * spc
        }
        check(fileSect == b.fileSectors) { "The files' sectors are off" }

        // At least a FAT page after the last file, and the FAT type's minimum
        val pageClusters = SECTOR * 8 / fatSz
        val minCluster = (if (fatSz == 32) 65525 else if (fatSz == 16) 4085 else 0) + pageClusters
        val target = fileCluster + pageClusters
        b.setFat(maxOf(target, minCluster.toLong()) - 1, 0)
        val totalClusters = b.fat.size * 8L / fatSz
        // Read-only: the rest of the FAT reserved
        for (c in fileCluster until totalClusters) b.setFat(c, 0xFFFFFF7)

        val sectorsPerFat = (b.fat.size / SECTOR).toLong()
        val reserved = if (fatSz == 32) 32 else 1
        val partSize = totalClusters * spc + reserved
        val fat1 = (SECT_BOOT + reserved).toLong()
        val fat2 = fat1 + sectorsPerFat
        val rootStart = fat2 + sectorsPerFat
        val dirsStart = rootStart + (b.root.size * 32L + SECTOR - 1) / SECTOR
        val filesStart = dirsStart + (b.dirs.size * 32L + SECTOR - 1) / SECTOR
        val filesEnd = filesStart + b.fileSectors
        val diskEnd = SECT_BOOT + partSize
        check(diskEnd >= filesEnd) { "DOSBox-X's conversion of this archive fails: its disk ends before its files" }

        val fatBytes = b.fat.toByteArray()
        val rootBytes = b.root.fold(ByteArray(0)) { all, e -> all + e }
        val dirBytes = ByteArray(b.dirs.size * 32).also { out -> b.dirs.forEachIndexed { i, e -> e.copyInto(out, i * 32) } }
        val crc = CRC32()
        crc.update(fatBytes)
        crc.update(rootBytes)
        crc.update(dirBytes)
        val serial = crc.value.toInt()

        val mbr = ByteArray(SECTOR)
        ByteBuffer.wrap(mbr).order(ByteOrder.LITTLE_ENDIAN).apply {
            putInt(440, serial)
            put(446, 0x80.toByte())
            if ((diskEnd - 1) / (HEADS * SPT) <= 0x3FF) {
                chs(mbr, 447, SECT_BOOT.toLong())
                chs(mbr, 451, diskEnd - 1)
            }
            put(450, (if (fatSz == 12) 0x01 else if (fatSz == 16) (if (diskEnd < 65536) 0x04 else 0x06) else 0x0C).toByte())
            putInt(454, SECT_BOOT)
            putInt(458, partSize.toInt())
            put(510, 0x55)
            put(511, 0xaa.toByte())
        }
        val boot = ByteArray(SECTOR)
        ByteBuffer.wrap(boot).order(ByteOrder.LITTLE_ENDIAN).apply {
            byteArrayOf(0xEB.toByte(), 0x3C, 0x90.toByte()).copyInto(boot, 0)
            (if (fatSz == 32) "MSWIN4.1" else "MSDOS5.0").toByteArray(Charsets.US_ASCII).copyInto(boot, 3)
            putShort(11, SECTOR.toShort())
            put(13, spc.toByte())
            putShort(14, reserved.toShort())
            put(16, 2)
            putShort(19, 0)
            put(21, 0xF8.toByte())
            putShort(24, SPT.toShort())
            putShort(26, HEADS.toShort())
            putInt(28, SECT_BOOT)
            putInt(32, partSize.toInt())
            put(510, 0x55)
            put(511, 0xaa.toByte())
            if (fatSz != 32) {
                putShort(17, b.root.size.toShort())
                putShort(22, sectorsPerFat.toShort())
                put(36, 0x80.toByte())
                put(38, 0x29)
                putInt(39, serial + 1)
                "NO NAME    ".toByteArray(Charsets.US_ASCII).copyInto(boot, 43)
                ("FAT1" + ('0' + fatSz % 10) + "   ").toByteArray(Charsets.US_ASCII).copyInto(boot, 54)
            } else {
                putInt(36, sectorsPerFat.toInt())
                putInt(44, 2)
                putShort(48, 1)
                putShort(50, 6)
                put(64, 0x80.toByte())
                put(66, 0x29)
                putInt(67, serial + 1)
                "NO NAME    ".toByteArray(Charsets.US_ASCII).copyInto(boot, 71)
                "FAT32   ".toByteArray(Charsets.US_ASCII).copyInto(boot, 82)
            }
        }
        val fsinfo = ByteArray(SECTOR)
        if (fatSz == 32) ByteBuffer.wrap(fsinfo).order(ByteOrder.LITTLE_ENDIAN).apply {
            putInt(0, 0x41615252)
            putInt(484, 0x61417272)
            putInt(488, 0) // read-only: no free clusters
            putInt(492, (filesEnd / spc).toInt()) // DOS 7.1
            putInt(508, 0xAA550000.toInt())
        }
        return Disk(fatSz, spc, fatBytes, rootBytes, dirBytes, files, mbr, boot, fsinfo, fat1, fat2, rootStart, dirsStart,
            filesStart, filesEnd, diskEnd)
    }

    /** Writes [disk]'s first [count] sectors to [out], each file's bytes from [open]. */
    fun write(disk: Disk, count: Long, out: OutputStream, open: (Entry) -> InputStream) {
        require(count >= disk.sectors) { "The disk is ${disk.sectors} sectors" }
        val zero = ByteArray(SECTOR)
        var at = 0L
        fun sector(bytes: ByteArray, offset: Int = 0) {
            out.write(bytes, offset, SECTOR)
            at++
        }
        fun region(bytes: ByteArray) {
            var o = 0
            while (o < bytes.size) {
                sector(bytes, o)
                o += SECTOR
            }
        }
        while (at < disk.fat1) sector(when (at) {
            0L -> disk.mbr
            SECT_BOOT.toLong(), SECT_BOOT + 6L -> disk.boot
            SECT_BOOT + 1L, SECT_BOOT + 2L, SECT_BOOT + 7L, SECT_BOOT + 8L -> disk.fsinfo
            else -> zero
        })
        region(disk.fat)
        region(disk.fat)
        region(disk.root.copyOf(((disk.root.size + SECTOR - 1) / SECTOR) * SECTOR))
        region(disk.dirs.copyOf(((disk.dirs.size + SECTOR - 1) / SECTOR) * SECTOR))
        check(at == disk.filesStart) { "The disk's regions are off" }
        val clusterBytes = disk.sectorsPerCluster * SECTOR
        for ((entry, first) in disk.files) {
            check(at == disk.filesStart + first) { "${entry.name} out of place" }
            val clusters = (entry.size + clusterBytes - 1) / clusterBytes
            val buffer = ByteArray(clusterBytes)
            var left = entry.size
            open(entry).use { input ->
                repeat(clusters.toInt()) {
                    val want = minOf(left, clusterBytes.toLong()).toInt()
                    var got = 0
                    while (got < want) {
                        val n = input.read(buffer, got, want - got)
                        check(n > 0) { "${entry.name} is shorter than its ${entry.size} bytes" }
                        got += n
                    }
                    buffer.fill(0, want, clusterBytes)
                    left -= want
                    region(buffer)
                }
                check(input.read() < 0) { "${entry.name} is longer than its ${entry.size} bytes" }
            }
        }
        check(at == disk.filesEnd) { "The disk's files are off" }
        while (at < count) sector(zero)
    }

    private fun chs(mbr: ByteArray, at: Int, lba: Long) {
        val cylinder = lba / (HEADS * SPT)
        val head = (lba / SPT) % HEADS
        val sector = (lba % SPT) + 1
        mbr[at] = head.toByte()
        mbr[at + 1] = ((sector and 0x3F) or ((cylinder shr 2) and 0xC0)).toByte()
        mbr[at + 2] = cylinder.toByte()
    }

    private fun le32(b: ByteArray, at: Int): Long = ByteBuffer.wrap(b).order(ByteOrder.LITTLE_ENDIAN).getInt(at).toLong() and 0xffffffffL
    private fun put16(b: ByteArray, at: Int, v: Int) {
        b[at] = v.toByte()
        b[at + 1] = (v shr 8).toByte()
    }

    private class Builder(val fatSz: Int, val spc: Int) {
        val fat = ByteArrayList()
        var root = ArrayList<ByteArray>()
        val dirs = ArrayList<ByteArray>()
        /** The file of each file entry, by its index in the root or in the folders. */
        val rootFiles = HashMap<Int, Entry>()
        val dirFiles = HashMap<Int, Entry>()
        var fileSectors = 0L
        val entriesPerCluster = spc * SECTOR / 32

        fun setFat(idx: Long, value: Long) {
            while (idx >= fat.size * 8L / fatSz) fat.grow(if (fatSz != 12) SECTOR else SECTOR * 3)
            when (fatSz) {
                32 -> fat.put32((idx * 4).toInt(), value.toInt())
                16 -> fat.put16((idx * 2).toInt(), value.toInt())
                else -> {
                    val at = (idx + idx / 2).toInt()
                    val old = fat.get16(at)
                    fat.put16(at, if (idx and 1L == 1L) (old and 0xF) or ((value.toInt() and 0xFFF) shl 4) else (old and 0xF000) or (value.toInt() and 0xFFF))
                }
            }
        }

        /** AddDirEntry: the next entry of the folder being listed ([index] its running position). */
        fun addDirEntry(useRoot: Boolean, index: IntArray): Pair<List<ByteArray>, Int> {
            if (!useRoot && index[0] % entriesPerCluster == 0) {
                if (index[0] != 0) setFat(2L + (index[0] - 1) / entriesPerCluster, 2L + dirs.size / entriesPerCluster)
                index[0] = dirs.size
                repeat(entriesPerCluster) { dirs += ByteArray(32) }
                setFat(2L + index[0] / entriesPerCluster, 0xFFFFFFFF)
            } else if (useRoot && index[0] != 0 && index[0] % 512 == 0) repeat(512) { root += ByteArray(32) }
            return (if (useRoot) root else dirs) to index[0]++
        }

        /**
         * ParseDir: the folder [entries] at depth [depth], its parent's first cluster [parentFirstCluster];
         * "." of a subfolder is dated as the folder itself, ".." as its parent (the archive's top folder as
         * PhysFS dates an implicit one).
         */
        fun parseDir(entries: List<Entry>, depth: Int, parentFirstCluster: Int, selfDate: Int, selfTime: Int, parentDate: Int, parentTime: Int) {
            val useRoot = depth == 0 && fatSz != 32
            val firstIdx = if (!useRoot) dirs.size else 0
            val myFirstCluster = if (depth != 0) 2 + firstIdx / entriesPerCluster else 0
            val list = if (useRoot) root else dirs
            val index = intArrayOf(0)
            // The ZIP drive's listing: "." and ".." (left out at the top), then by strcmp, each with its 8.3 name
            val sorted = entries.sortedWith { a, b -> strcmp(a.name, b.name) }
            val shorts = shortNames(sorted.map { it.name })
            data class Listed(val entry: Entry?, val short: String, val dot: Int)
            val listed = (listOf(Listed(null, ".", 1), Listed(null, "..", 2)) +
                sorted.indices.map { Listed(sorted[it], shorts[it], 0) }).sortedWith { a, b -> strcmp(a.short, b.short) }
            val made = ArrayList<Pair<Int, Listed>>()
            for (l in listed) {
                if (depth == 0 && l.dot != 0) continue
                val e = l.entry
                val longName = l.dot == 0
                if (longName) {
                    val name = e!!.name
                    val blocks = (name.length + 12) / 13
                    for (i in 0 until blocks) {
                        val (where, at) = addDirEntry(useRoot, index)
                        val le = where[at]
                        le[0] = ((blocks - i) or (if (i == 0) 0x40 else 0)).toByte()
                        le[11] = ATTR_LONG_NAME.toByte()
                        le[12] = 0
                        put16(le, 26, 0)
                        val start = (blocks - i - 1) * 13
                        for (j in 0 until 13) {
                            val p = start + j
                            val c = if (p > name.length) 0xFFFF else if (p == name.length) 0 else name[p].code
                            val off = NAME_OFFSETS[j]
                            le[off] = c.toByte()
                            le[off + 1] = (c shr 8).toByte()
                        }
                    }
                }
                val (where, at) = addDirEntry(useRoot, index)
                val d = where[at]
                ByteArray(11) { ' '.code.toByte() }.copyInto(d)
                val short = l.short
                val dotAt = if (l.dot != 0) -1 else short.lastIndexOf('.')
                val base = if (dotAt >= 0) short.substring(0, dotAt) else short
                base.toByteArray(Charsets.ISO_8859_1).copyInto(d, 0)
                if (dotAt >= 0) short.substring(dotAt + 1).toByteArray(Charsets.ISO_8859_1).copyInto(d, 8)
                val attr = (if (e == null || e.folder) ATTR_DIRECTORY or ATTR_ARCHIVE else ATTR_ARCHIVE) or ATTR_READ_ONLY or
                    (if (longName) ATTR_PENDING_SHORT_NAME else 0)
                d[11] = attr.toByte()
                val date = e?.date ?: if (l.dot == 1) selfDate else parentDate
                val time = e?.time ?: if (l.dot == 1) selfTime else parentTime
                put16(d, 14, time)
                put16(d, 16, date)
                put16(d, 18, date)
                put16(d, 22, time)
                put16(d, 24, date)
                when {
                    l.dot == 1 -> put16(d, 26, myFirstCluster)
                    l.dot == 2 -> put16(d, 26, parentFirstCluster)
                    e != null && !e.folder -> {
                        ByteBuffer.wrap(d).order(ByteOrder.LITTLE_ENDIAN).putInt(28, e.size.toInt())
                        (if (where === root) rootFiles else dirFiles)[at] = e
                        fileSectors += (e.size + spc * SECTOR - 1) / (spc * SECTOR) * spc
                    }
                }
                made += at to l
            }
            check(depth == 0 || made.size >= 2) { "A folder needs at least its . and .. entries" }
            // The subfolders, and each long name's checksum
            for ((at, l) in made) {
                val d = list[at]
                if (l.dot != 0) continue
                if (d[11].toInt() and ATTR_PENDING_SHORT_NAME != 0) {
                    var sum = 0
                    for (i in 0 until 11) sum = (((sum ushr 1) or (sum shl 7)) + (d[i].toInt() and 0xff)) and 0xff
                    var k = at - 1
                    while (true) {
                        list[k][13] = sum.toByte()
                        if (list[k][0].toInt() and 0x40 != 0) break
                        k--
                    }
                    d[11] = (d[11].toInt() and ATTR_PENDING_SHORT_NAME.inv()).toByte()
                }
                if (l.entry!!.folder) {
                    put16(d, 26, 2 + dirs.size / entriesPerCluster)
                    parseDir(l.entry.children, depth + 1, myFirstCluster, l.entry.date, l.entry.time, selfDate, selfTime)
                }
            }
        }
    }

    /** Where each of a long-name entry's 13 characters sits. */
    private val NAME_OFFSETS = intArrayOf(1, 3, 5, 7, 9, 14, 16, 18, 20, 22, 24, 28, 30)

    /** A growable little-endian byte array (the FAT). */
    private class ByteArrayList {
        var bytes = ByteArray(0)
        val size get() = bytes.size
        fun grow(n: Int) { bytes = bytes.copyOf(bytes.size + n) }
        fun get16(at: Int) = (bytes[at].toInt() and 0xff) or ((bytes[at + 1].toInt() and 0xff) shl 8)
        fun put16(at: Int, v: Int) { bytes[at] = v.toByte(); bytes[at + 1] = (v shr 8).toByte() }
        fun put32(at: Int, v: Int) { put16(at, v); put16(at + 2, v ushr 16) }
        fun toByteArray() = bytes.copyOf()
    }
}
