package com.mrjackspade.kairox86

import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Writes a Windows 9x registry hive (CREG) for tests, laid out as Windows lays one out
 * ([Win9xRegistry]): the key tree in RGKN, the records in RGDB blocks of up to [perBlock] each.
 */
class CregWriter(private val perBlock: Int = 3) {
    class Key(val name: String, val values: Map<String, Pair<Int, ByteArray>> = emptyMap(), val children: List<Key> = emptyList())

    companion object {
        fun string(text: String) = 1 to (text.toByteArray(Charsets.ISO_8859_1) + 0)
        fun binary(bytes: ByteArray) = 3 to bytes

        /** A key at [path] ("Enum\PCI\VEN_x\BUS_00&DEV_08&FUNC_00") with [values], its parents made as needed. */
        fun tree(entries: List<Pair<String, Map<String, Pair<Int, ByteArray>>>>): List<Key> {
            class Node(val name: String) {
                val children = LinkedHashMap<String, Node>()
                var values: Map<String, Pair<Int, ByteArray>> = emptyMap()
                fun key(): Key = Key(name, values, children.values.map { it.key() })
            }
            val root = Node("")
            for ((path, values) in entries) {
                var node = root
                for (part in path.split('\\')) node = node.children.getOrPut(part) { Node(part) }
                node.values = values
            }
            return root.children.values.map { it.key() }
        }
    }

    fun write(top: List<Key>): ByteArray {
        // Every key in tree order, each with its node offset and record number
        class Placed(val key: Key, val node: Int, val block: Int, val number: Int, val parent: Int)
        val placed = ArrayList<Placed>()
        val nodeSize = 0x1c
        var nextNode = 0x20 + nodeSize // the root's node is at 0x20
        var count = 0
        fun place(keys: List<Key>, parent: Int): List<Placed> = keys.map { key ->
            val at = Placed(key, nextNode, count / perBlock, count % perBlock, parent)
            nextNode += nodeSize
            count++
            placed += at
            at
        }.also { siblings -> siblings.forEach { place(it.key.children, it.node) } }
        val rootChildren = place(top, 0x20)
        val nodes = ByteBuffer.allocate(nextNode).order(ByteOrder.LITTLE_ENDIAN)
        fun node(at: Int, parent: Int, child: Int, next: Int, number: Int, block: Int) {
            nodes.putInt(at, 0).putInt(at + 4, 0).putInt(at + 8, -1).putInt(at + 12, parent).putInt(at + 16, child)
                .putInt(at + 20, next).putShort(at + 24, number.toShort()).putShort(at + 26, block.toShort())
        }
        fun firstChild(key: Key): Int = placed.firstOrNull { it.key === key.children.firstOrNull() }?.node ?: -1
        node(0x20, -1, rootChildren.firstOrNull()?.node ?: -1, -1, 0xffff, 0xffff)
        for (p in placed) {
            val siblings = placed.filter { it.parent == p.parent }
            val next = siblings.getOrNull(siblings.indexOf(p) + 1)?.node ?: -1
            node(p.node, p.parent, firstChild(p.key), next, p.number, p.block)
        }
        val rgkn = nodes.array()
        "RGKN".toByteArray().copyInto(rgkn, 0)
        ByteBuffer.wrap(rgkn).order(ByteOrder.LITTLE_ENDIAN).putInt(4, rgkn.size).putInt(8, 0x20)
        // The blocks, each with a free record of another block's number left in it
        val blocks = placed.groupBy { it.block }.toSortedMap().map { (block, records) ->
            val body = ByteArrayOutputStream()
            fun record(number: Int, owner: Int, key: Key) {
                val name = key.name.toByteArray(Charsets.ISO_8859_1)
                val values = ByteArrayOutputStream()
                for ((valueName, value) in key.values) {
                    val vn = valueName.toByteArray(Charsets.ISO_8859_1)
                    values.write(ByteBuffer.allocate(12).order(ByteOrder.LITTLE_ENDIAN).putInt(value.first).putInt(0)
                        .putShort(vn.size.toShort()).putShort(value.second.size.toShort()).array())
                    values.write(vn)
                    values.write(value.second)
                }
                val used = 20 + name.size + values.size()
                val length = used + 4
                body.write(ByteBuffer.allocate(20).order(ByteOrder.LITTLE_ENDIAN).putInt(length).putShort(number.toShort())
                    .putShort(owner.toShort()).putInt(used).putShort(name.size.toShort()).putShort(key.values.size.toShort()).putInt(0).array())
                body.write(name)
                values.writeTo(body)
                body.write(ByteArray(length - used))
            }
            for (r in records) record(r.number, block, r.key)
            record(records.first().number, block + 1, Key("stale"))
            val head = ByteBuffer.allocate(0x20).order(ByteOrder.LITTLE_ENDIAN)
            head.put("RGDB".toByteArray()).putInt(0x20 + body.size()).putInt(0).putInt(block shl 16 or 8)
            head.array() + body.toByteArray()
        }
        val header = ByteBuffer.allocate(0x20).order(ByteOrder.LITTLE_ENDIAN)
        header.put("CREG".toByteArray()).putInt(0x10000).putInt(0x20 + rgkn.size).putInt(0).putShort(blocks.size.toShort())
        val out = ByteArrayOutputStream()
        out.write(header.array())
        out.write(rgkn)
        blocks.forEach { out.write(it) }
        return out.toByteArray()
    }
}
