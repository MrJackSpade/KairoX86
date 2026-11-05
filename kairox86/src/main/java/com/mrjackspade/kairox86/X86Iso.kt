package com.mrjackspade.kairox86

import java.io.InputStream
import java.io.OutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * A CD image (ISO 9660 with Joliet names) of a set of files (KairoX86#223): what DOSBox-X shows a
 * game as a drive when its Play.conf mounts an archive (`mount e "<game>.zip"`), for 86Box, which
 * takes disc images only. The primary tree has ISO 9660's 8.3 names; the Joliet tree, which Windows
 * reads, the files' own. The layout is worked out from the files' names and sizes alone, so the image
 * is written in one pass, each file's bytes streamed in as [write] reaches it.
 */
object X86Iso {
    /** A file of the image: its path (forward slashes) and size. */
    data class File(val path: String, val size: Long)

    private const val SECTOR = 2048

    private class Dir(val name: String, val parent: Dir?) {
        val dirs = sortedMapOf<String, Dir>(String.CASE_INSENSITIVE_ORDER)
        val files = sortedMapOf<String, File>(String.CASE_INSENSITIVE_ORDER)
        var number = 0
        var primarySector = 0
        var primarySize = 0
        var jolietSector = 0
        var jolietSize = 0
        var primaryNames = mapOf<String, String>()
    }

    /**
     * Writes the image of [files] named [volume] to [output]; [open] gives each file's bytes, which
     * must be its size exactly.
     */
    fun write(volume: String, files: List<File>, output: OutputStream, open: (File) -> InputStream) {
        val root = Dir("", null)
        for (file in files) {
            val parts = file.path.split('/').filter { it.isNotEmpty() }
            require(parts.isNotEmpty()) { "Empty path" }
            require(file.size >= 0) { "${file.path} has no known size" }
            var dir = root
            for (part in parts.dropLast(1)) dir = dir.dirs.getOrPut(part) { Dir(part, dir) }
            require(dir.files.put(parts.last(), file) == null) { "${file.path} twice" }
        }
        // Path tables list the directories by level, then parent, then name (ECMA-119 6.9.1)
        val ordered = mutableListOf(root)
        var at = 0
        while (at < ordered.size) { ordered += ordered[at].dirs.values; at++ }
        ordered.forEachIndexed { index, dir -> dir.number = index + 1 }
        for (dir in ordered) dir.primaryNames = shortNames(dir)

        val primaryTable = pathTable(ordered, joliet = false, bigEndian = false)
        val jolietTable = pathTable(ordered, joliet = true, bigEndian = false)
        val tableSectors = sectors(maxOf(primaryTable.size, jolietTable.size).toLong())
        // Sectors: 16 system, 3 descriptors, then four path tables, then the directories, then the files
        var next = 19 + 4 * tableSectors
        for (dir in ordered) { dir.primarySize = dirSize(dir, joliet = false); dir.primarySector = next; next += sectors(dir.primarySize.toLong()) }
        for (dir in ordered) { dir.jolietSize = dirSize(dir, joliet = true); dir.jolietSector = next; next += sectors(dir.jolietSize.toLong()) }
        val fileSectors = LinkedHashMap<File, Int>()
        for (dir in ordered) for (file in dir.files.values) { fileSectors[file] = next; next += sectors(file.size) }
        val total = next

        val out = CountingOutput(output)
        out.zeros(16 * SECTOR)
        out.write(descriptor(1, volume, total, primaryTable.size, 19, 19 + tableSectors, root, joliet = false))
        out.write(descriptor(2, volume, total, jolietTable.size, 19 + 2 * tableSectors, 19 + 3 * tableSectors, root, joliet = true))
        out.write(ByteArray(SECTOR).also { it[0] = 0xff.toByte(); "CD001".toByteArray().copyInto(it, 1); it[6] = 1 })
        // The tables again, now with the directories' sectors (their sizes do not depend on them)
        for (table in listOf(pathTable(ordered, false, false), pathTable(ordered, false, true),
                             pathTable(ordered, true, false), pathTable(ordered, true, true))) {
            out.write(table); out.zeros(tableSectors * SECTOR - table.size)
        }
        for (joliet in listOf(false, true)) for (dir in ordered) {
            val bytes = directory(dir, joliet, fileSectors)
            out.write(bytes); out.zeros(sectors(bytes.size.toLong()) * SECTOR - bytes.size)
        }
        for ((file, sector) in fileSectors) {
            check(out.count == sector.toLong() * SECTOR) { "The image's layout went wrong at ${file.path}" }
            val copied = open(file).use { input -> input.copyTo(out) }
            check(copied == file.size) { "${file.path} gave $copied bytes, not ${file.size}" }
            out.zeros((sectors(file.size).toLong() * SECTOR - file.size).toInt())
        }
        check(out.count == total.toLong() * SECTOR) { "The image came out ${out.count} bytes, not ${total.toLong() * SECTOR}" }
    }

    private fun sectors(bytes: Long): Int = ((bytes + SECTOR - 1) / SECTOR).toInt().coerceAtLeast(1)

    /** ISO 9660's names of [dir]'s children, 8.3 upper case, each unique in it. */
    private fun shortNames(dir: Dir): Map<String, String> {
        val taken = HashSet<String>()
        val names = HashMap<String, String>()
        fun clean(text: String, length: Int) = text.uppercase().map { if (it in 'A'..'Z' || it in '0'..'9') it else '_' }.joinToString("").take(length)
        for (name in dir.dirs.keys + dir.files.keys) {
            val isDir = name in dir.dirs
            val base = clean(if (isDir) name else name.substringBeforeLast('.', name), 8).ifEmpty { "_" }
            val ext = if (isDir || !name.contains('.')) "" else clean(name.substringAfterLast('.'), 3)
            var candidate = if (ext.isEmpty()) base else "$base.$ext"
            var n = 1
            while (!taken.add(candidate)) {
                val suffix = "~${n++}"
                val stem = base.take(8 - suffix.length) + suffix
                candidate = if (ext.isEmpty()) stem else "$stem.$ext"
            }
            names[name] = candidate
        }
        return names
    }

    private fun identifier(dir: Dir, name: String, joliet: Boolean, file: Boolean): ByteArray = when {
        joliet -> (if (file) "$name;1" else name).take(if (file) 66 else 64).toByteArray(Charsets.UTF_16BE)
        else -> (dir.primaryNames.getValue(name) + if (file) ";1" else "").toByteArray(Charsets.US_ASCII)
    }

    private fun record(id: ByteArray, sector: Int, size: Long, directory: Boolean): ByteArray {
        val length = 33 + id.size + (if (id.size % 2 == 0) 1 else 0)
        val b = ByteBuffer.allocate(length)
        b.put(length.toByte()).put(0)
        both32(b, sector.toLong()); both32(b, size)
        b.put(byteArrayOf(96, 1, 1, 0, 0, 0, 0)) // 1996-01-01 00:00:00 GMT
        b.put((if (directory) 2 else 0).toByte()).put(0).put(0)
        both16(b, 1)
        b.put(id.size.toByte()).put(id)
        return b.array()
    }

    private fun dirEntries(dir: Dir, joliet: Boolean, fileSectors: Map<File, Int>?): List<ByteArray> {
        val self = if (joliet) dir.jolietSector else dir.primarySector
        val selfSize = if (joliet) dir.jolietSize else dir.primarySize
        val parent = dir.parent ?: dir
        val entries = mutableListOf(record(byteArrayOf(0), self, selfSize.toLong(), true),
            record(byteArrayOf(1), if (joliet) parent.jolietSector else parent.primarySector,
                (if (joliet) parent.jolietSize else parent.primarySize).toLong(), true))
        // By identifier, as ECMA-119 9.3 sorts them
        val children = (dir.dirs.keys.map { it to true } + dir.files.keys.map { it to false })
            .sortedBy { (name, isDir) -> String(identifier(dir, name, joliet, !isDir), if (joliet) Charsets.UTF_16BE else Charsets.US_ASCII) }
        for ((name, isDir) in children) {
            val id = identifier(dir, name, joliet, !isDir)
            entries += if (isDir) {
                val child = dir.dirs.getValue(name)
                record(id, if (joliet) child.jolietSector else child.primarySector, (if (joliet) child.jolietSize else child.primarySize).toLong(), true)
            } else {
                val file = dir.files.getValue(name)
                record(id, fileSectors?.getValue(file) ?: 0, file.size, false)
            }
        }
        return entries
    }

    /** A directory's records, none crossing a sector (ECMA-119 6.8.1.1). */
    private fun directory(dir: Dir, joliet: Boolean, fileSectors: Map<File, Int>?): ByteArray {
        val out = java.io.ByteArrayOutputStream()
        var inSector = 0
        for (entry in dirEntries(dir, joliet, fileSectors)) {
            if (inSector + entry.size > SECTOR) { out.write(ByteArray(SECTOR - inSector)); inSector = 0 }
            out.write(entry); inSector += entry.size
        }
        return out.toByteArray()
    }

    private fun dirSize(dir: Dir, joliet: Boolean): Int = sectors(directory(dir, joliet, null).size.toLong()) * SECTOR

    private fun pathTable(ordered: List<Dir>, joliet: Boolean, bigEndian: Boolean): ByteArray {
        val out = java.io.ByteArrayOutputStream()
        for (dir in ordered) {
            val id = if (dir.parent == null) byteArrayOf(0) else if (joliet) dir.name.take(64).toByteArray(Charsets.UTF_16BE)
                else dir.parent.primaryNames.getValue(dir.name).toByteArray(Charsets.US_ASCII)
            val b = ByteBuffer.allocate(8 + id.size + id.size % 2).order(if (bigEndian) ByteOrder.BIG_ENDIAN else ByteOrder.LITTLE_ENDIAN)
            b.put(id.size.toByte()).put(0)
            // Extents are not known when the sizes are taken; written again with them below
            b.putInt(if (joliet) dir.jolietSector else dir.primarySector)
            b.putShort((dir.parent?.number ?: 1).toShort())
            b.put(id)
            out.write(b.array())
        }
        return out.toByteArray()
    }

    private fun descriptor(type: Int, volume: String, total: Int, tableSize: Int, lTable: Int, mTable: Int, root: Dir, joliet: Boolean): ByteArray {
        val b = ByteBuffer.allocate(SECTOR)
        b.put(type.toByte()).put("CD001".toByteArray()).put(1).put(0)
        // A field of [length] bytes; a UCS-2 one of odd length ends in a zero byte
        fun text(value: String, length: Int) = (if (joliet) value.padEnd(length / 2).take(length / 2).toByteArray(Charsets.UTF_16BE)
            else value.uppercase().padEnd(length).take(length).toByteArray(Charsets.US_ASCII)).copyOf(length)
        b.put(text("", 32)).put(text(volume, 32)).put(ByteArray(8))
        both32(b, total.toLong())
        b.put(ByteArray(32).also { if (joliet) "%/E".toByteArray().copyInto(it) }) // Joliet's UCS-2 level 3
        both16(b, 1); both16(b, 1); both16(b, SECTOR)
        both32(b, tableSize.toLong())
        b.order(ByteOrder.LITTLE_ENDIAN).putInt(lTable).putInt(0)
        b.order(ByteOrder.BIG_ENDIAN).putInt(mTable).putInt(0)
        b.put(record(byteArrayOf(0), if (joliet) root.jolietSector else root.primarySector,
            (if (joliet) root.jolietSize else root.primarySize).toLong(), true))
        b.put(text("", 128)).put(text("", 128)).put(text("KAIROX86", 128)).put(text("", 128))
        b.put(text("", 37)).put(text("", 37)).put(text("", 37))
        val date = "1996010100000000".toByteArray() + 0
        repeat(2) { b.put(date) }
        repeat(2) { b.put(ByteArray(16) { '0'.code.toByte() }).put(0) }
        b.put(1)
        return b.array()
    }

    private fun both16(b: ByteBuffer, value: Int) {
        b.order(ByteOrder.LITTLE_ENDIAN).putShort(value.toShort()); b.order(ByteOrder.BIG_ENDIAN).putShort(value.toShort())
    }

    private fun both32(b: ByteBuffer, value: Long) {
        b.order(ByteOrder.LITTLE_ENDIAN).putInt(value.toInt()); b.order(ByteOrder.BIG_ENDIAN).putInt(value.toInt())
    }

    private class CountingOutput(private val out: OutputStream) : OutputStream() {
        var count = 0L
        override fun write(b: Int) { out.write(b); count++ }
        override fun write(b: ByteArray, off: Int, len: Int) { out.write(b, off, len); count += len }
        fun zeros(length: Int) { val zeros = ByteArray(8192); var left = length; while (left > 0) { val n = minOf(left, zeros.size); write(zeros, 0, n); left -= n } }
    }
}
