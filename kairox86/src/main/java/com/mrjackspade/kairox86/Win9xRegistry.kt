package com.mrjackspade.kairox86

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * A Windows 95/98 registry hive (SYSTEM.DAT, the "CREG" format), read whole (KairoX86#224): what an
 * installed Windows knows of the hardware it ran on ([Win9xMachine]).
 *
 * The file is a header (CREG: the first RGDB block's offset at 8, their count at 16), the key tree
 * (RGKN at 0x20: the root's offset at 0x28, offsets relative to 0x20; each key's parent, first child
 * and next sibling, and its record's number, nrLS and nrMS), then the RGDB blocks holding the
 * records: key `(nrMS, nrLS)` is record nrLS of block nrMS, its name and its values. Names are in
 * the installation's ANSI code page; they are read byte for byte (ISO 8859-1), which keeps the ASCII
 * names devices go by as they are.
 */
class Win9xRegistry private constructor(val root: Key) {
    /** A value: its type (1 a string, 3 binary, 4 a DWORD) and its bytes. */
    class Value(val type: Int, val data: ByteArray) {
        /** A string value without its terminating NUL. */
        val string: String get() = String(data, Charsets.ISO_8859_1).trimEnd('\u0000')
    }

    class Key(val name: String, val values: Map<String, Value>, val children: List<Key>) {
        /** The child named [name], whatever its case, as Windows looks keys up. */
        fun child(name: String): Key? = children.firstOrNull { it.name.equals(name, ignoreCase = true) }

        /** The string value [name], or null when there is none. */
        fun string(name: String): String? = values.entries.firstOrNull { it.key.equals(name, ignoreCase = true) }?.value?.string

        fun value(name: String): Value? = values.entries.firstOrNull { it.key.equals(name, ignoreCase = true) }?.value
    }

    /** The key at [path] under the root ("Enum\PCI"), or null when there is none. */
    fun key(path: String): Key? = path.split('\\').filter { it.isNotEmpty() }.fold(root as Key?) { key, part -> key?.child(part) }

    companion object {
        private const val RGKN = 0x20
        private const val NONE = -1

        fun read(data: ByteArray): Win9xRegistry {
            val buffer = ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN)
            check(String(data, 0, 4, Charsets.US_ASCII) == "CREG") { "Not a Windows 9x registry (no CREG header)" }
            check(String(data, RGKN, 4, Charsets.US_ASCII) == "RGKN") { "The registry has no key tree (RGKN)" }
            // Each record by its number (block << 16 | record): its name and values
            val records = HashMap<Int, Pair<String, Map<String, Value>>>()
            var offset = buffer.getInt(8)
            repeat(buffer.getShort(16).toInt() and 0xffff) { block ->
                check(String(data, offset, 4, Charsets.US_ASCII) == "RGDB") { "The registry's block $block is not an RGDB block" }
                val end = offset + buffer.getInt(offset + 4)
                check(end in offset + 0x20..data.size) { "The registry's block $block runs past the file" }
                var at = offset + 0x20
                while (at < end) {
                    val length = buffer.getInt(at)
                    check(length >= 20 && at + length <= end) { "The registry's block $block has a record of length $length" }
                    val number = buffer.getShort(at + 4).toInt() and 0xffff
                    val owner = buffer.getShort(at + 6).toInt() and 0xffff
                    // A record of another block's number is a free one left behind
                    if (number != 0xffff && owner == block) {
                        val used = buffer.getInt(at + 8)
                        val nameLength = buffer.getShort(at + 12).toInt() and 0xffff
                        val count = buffer.getShort(at + 14).toInt() and 0xffff
                        check(used in 20 + nameLength..length) { "The registry's record $block/$number uses $used of $length bytes" }
                        val name = String(data, at + 20, nameLength, Charsets.ISO_8859_1)
                        val values = LinkedHashMap<String, Value>()
                        var v = at + 20 + nameLength
                        repeat(count) {
                            check(v + 12 <= at + used) { "The registry's record $block/$number ($name) has values past its end" }
                            val type = buffer.getInt(v)
                            val valueNameLength = buffer.getShort(v + 8).toInt() and 0xffff
                            val dataLength = buffer.getShort(v + 10).toInt() and 0xffff
                            check(v + 12 + valueNameLength + dataLength <= at + used) { "The registry's record $block/$number ($name) has values past its end" }
                            values[String(data, v + 12, valueNameLength, Charsets.ISO_8859_1)] =
                                Value(type, data.copyOfRange(v + 12 + valueNameLength, v + 12 + valueNameLength + dataLength))
                            v += 12 + valueNameLength + dataLength
                        }
                        check(records.put(block shl 16 or number, name to values) == null) { "The registry's block $block has two records $number" }
                    }
                    at += length
                }
                offset = end
            }
            fun node(at: Int, field: Int) = buffer.getInt(RGKN + at + field * 4)
            fun key(at: Int): Key {
                val number = buffer.getShort(RGKN + at + 24).toInt() and 0xffff
                val block = buffer.getShort(RGKN + at + 26).toInt() and 0xffff
                val (name, values) = checkNotNull(records[block shl 16 or number]) { "The registry's key at ${"%x".format(at)} has no record $block/$number" }
                val children = ArrayList<Key>()
                var child = node(at, 4)
                while (child != NONE) {
                    children += key(child)
                    child = node(child, 5)
                }
                return Key(name, values, children)
            }
            // The root has no record of its own
            val root = buffer.getInt(RGKN + 8)
            val children = ArrayList<Key>()
            var child = node(root, 4)
            while (child != NONE) {
                children += key(child)
                child = node(child, 5)
            }
            return Win9xRegistry(Key("", emptyMap(), children))
        }
    }
}
