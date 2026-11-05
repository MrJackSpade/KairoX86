package com.mrjackspade.kairox86

import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.channels.SeekableByteChannel

/**
 * A ZIP archive's folders and files as DOSBox-X's ZIP drive (PhysFS) sees them, for [DosboxFat]:
 * each entry's name, size and DOS date and time from the central directory (PhysFS reads the DOS
 * time there, not an extra field's), its folders those it lists and those its paths imply.
 */
object ZipListing {
    /** The top folder's entries of the archive read from [channel]; each file's member is its name in the archive. */
    fun read(channel: SeekableByteChannel): List<DosboxFat.Entry> {
        val size = channel.size()
        // The end of central directory record, in the last 64 KiB + 22 bytes
        val tailSize = minOf(size, 65_557L).toInt()
        val tail = readAt(channel, size - tailSize, tailSize)
        var eocd = -1
        for (i in tailSize - 22 downTo 0) if (tail.getInt(i) == 0x06054b50) { eocd = i; break }
        check(eocd >= 0) { "No ZIP end of central directory" }
        var count = (tail.getShort(eocd + 10).toInt() and 0xffff).toLong()
        var cdSize = tail.getInt(eocd + 12).toLong() and 0xffffffffL
        var cdOffset = tail.getInt(eocd + 16).toLong() and 0xffffffffL
        if (count == 0xffffL || cdSize == 0xffffffffL || cdOffset == 0xffffffffL) {
            // ZIP64: the locator just before the record names the ZIP64 record
            check(eocd >= 20 && tail.getInt(eocd - 20) == 0x07064b50) { "A ZIP64 archive with no ZIP64 locator" }
            val record = readAt(channel, tail.getLong(eocd - 20 + 8), 56)
            check(record.getInt(0) == 0x06064b50) { "No ZIP64 end of central directory" }
            count = record.getLong(32)
            cdSize = record.getLong(40)
            cdOffset = record.getLong(48)
        }
        check(cdSize < Int.MAX_VALUE) { "A ZIP central directory of $cdSize bytes" }
        val cd = readAt(channel, cdOffset, cdSize.toInt())
        val root = Folder("", DosboxFat.IMPLICIT_DATE, DosboxFat.IMPLICIT_TIME)
        var at = 0
        repeat(count.toInt()) {
            check(cd.getInt(at) == 0x02014b50) { "A broken ZIP central directory" }
            val flags = cd.getShort(at + 8).toInt() and 0xffff
            val time = cd.getShort(at + 12).toInt() and 0xffff
            val date = cd.getShort(at + 14).toInt() and 0xffff
            var usize = cd.getInt(at + 24).toLong() and 0xffffffffL
            val nameLength = cd.getShort(at + 28).toInt() and 0xffff
            val extraLength = cd.getShort(at + 30).toInt() and 0xffff
            val commentLength = cd.getShort(at + 32).toInt() and 0xffff
            val nameBytes = ByteArray(nameLength).also { cd.position(at + 46); cd.get(it) }
            val name = String(nameBytes, if (flags and 0x800 != 0) Charsets.UTF_8 else Charsets.ISO_8859_1)
            check(name.all { it.code in 1..127 }) { "$name: archive names past ASCII are not reproduced as DOSBox-X lists them" }
            if (usize == 0xffffffffL) {
                // ZIP64 sizes in the extra field
                var e = at + 46 + nameLength
                val end = e + extraLength
                while (e + 4 <= end) {
                    val id = cd.getShort(e).toInt() and 0xffff
                    val len = cd.getShort(e + 2).toInt() and 0xffff
                    if (id == 0x0001) { usize = cd.getLong(e + 4); break }
                    e += 4 + len
                }
            }
            val path = name.replace('\\', '/')
            val parts = path.split('/').filter { it.isNotEmpty() }
            if (parts.isNotEmpty()) {
                var folder = root
                for (part in parts.dropLast(1)) folder = folder.folder(part, DosboxFat.IMPLICIT_DATE, DosboxFat.IMPLICIT_TIME)
                if (path.endsWith('/')) folder.folder(parts.last(), date, time).listed(date, time)
                else {
                    check(folder.files.none { it.name == parts.last() } && parts.last() !in folder.folders) { "$name is in the archive twice" }
                    folder.files += DosboxFat.Entry(parts.last(), false, usize, date, time, member = name)
                }
            }
            at += 46 + nameLength + extraLength + commentLength
        }
        return root.entries()
    }

    private class Folder(val name: String, var date: Int, var time: Int) {
        val folders = LinkedHashMap<String, Folder>()
        val files = ArrayList<DosboxFat.Entry>()

        fun folder(part: String, date: Int, time: Int): Folder = folders.getOrPut(part) { Folder(part, date, time) }
        fun listed(date: Int, time: Int) {
            this.date = date
            this.time = time
        }

        fun entries(): List<DosboxFat.Entry> =
            folders.values.map { DosboxFat.Entry(it.name, true, 0, it.date, it.time, it.entries()) } + files
    }

    private fun readAt(channel: SeekableByteChannel, position: Long, size: Int): ByteBuffer {
        val buffer = ByteBuffer.allocate(size).order(ByteOrder.LITTLE_ENDIAN)
        channel.position(position)
        while (buffer.hasRemaining()) check(channel.read(buffer) > 0) { "The ZIP ends early" }
        buffer.flip()
        return buffer
    }
}
