package com.mrjackspade.kairox86

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * A hard disk image a machine can take (KairoX86#217): one whose geometry it carries, as 86Box
 * reads it when the machine starts (third_party/86box/src/disk/hdd_image.c), so its 86box.cfg can
 * say the same. A raw image (.img, .ima, KairoX86#340) carries none in a header: its geometry is
 * its partition table's (where its partitions end gives the heads and
 * sectors a track), and its size gives the cylinders. One whose partition table says nothing, or
 * whose size is no whole number of cylinders, is no hard disk here: 86Box would take whatever
 * 86box.cfg says and grow the file to it.
 */
object X86HardDisk {
    /** A disk's geometry: sectors per track, heads and cylinders, as 86box.cfg's hdd_NN_parameters give them. */
    data class Geometry(val sectors: Int, val heads: Int, val cylinders: Int)

    /** The hard disk images 86Box reads with their geometry, by extension. */
    val IMAGES = setOf("vhd", "hdi", "hdx")
    /** Raw images: a floppy's or a hard disk's, the player choosing (X86Library.diskKinds). */
    val RAW_IMAGES = setOf("img", "ima")

    private const val SECTOR = 512
    /** The HDX signature, as 86Box reads its first 8 bytes (little-endian). */
    private val HDX_SIGNATURE = 0xD778A82044445459uL.toLong()

    /**
     * The geometry of the image [name] of [size] bytes, whose bytes [read] gives (offset, length);
     * fails for one that is not the image its extension says.
     */
    fun geometry(name: String, size: Long, read: (Long, Int) -> ByteArray): Geometry =
        when (val kind = name.substringAfterLast('.', "").lowercase()) {
            // The footer at its end: "conectix", then the CHS at 56 (cylinders, heads, sectors; big-endian).
            "vhd" -> {
                require(size >= SECTOR) { "$name is too small to be a VHD" }
                val footer = ByteBuffer.wrap(read(size - SECTOR, SECTOR)).order(ByteOrder.BIG_ENDIAN)
                require(String(footer.array(), 0, 8, Charsets.US_ASCII) == "conectix") { "$name has no VHD footer" }
                Geometry(footer.get(59).toInt() and 0xFF, footer.get(58).toInt() and 0xFF, footer.getShort(56).toInt() and 0xFFFF)
            }
            // A header of little-endian fields: the sector size at 16, then sectors, heads and cylinders.
            "hdi", "hdx" -> {
                val header = ByteBuffer.wrap(read(0, 32)).order(ByteOrder.LITTLE_ENDIAN)
                if (kind == "hdx") require(header.getLong(0) == HDX_SIGNATURE) { "$name has no HDX signature" }
                require(header.getInt(16) == SECTOR) { "$name has sectors of ${header.getInt(16)} bytes, not $SECTOR" }
                Geometry(header.getInt(20), header.getInt(24), header.getInt(28))
            }
            in RAW_IMAGES -> rawGeometry(name, size, read(0, SECTOR))
            else -> error("$name is no hard disk image (${(IMAGES + RAW_IMAGES).joinToString()})")
        }.also { geometry ->
            require(geometry.sectors > 0 && geometry.heads > 0 && geometry.cylinders > 0) { "$name names no geometry" }
        }

    /**
     * A raw image's geometry from its master boot record [mbr]: each partition's end in CHS (head,
     * then sector in the low 6 bits) gives the heads (the end head + 1) and the sectors a track, which
     * every partition must agree on; the cylinders are the size over a cylinder's bytes, exactly.
     */
    private fun rawGeometry(name: String, size: Long, mbr: ByteArray): Geometry {
        require(mbr.size == SECTOR && (mbr[510].toInt() and 0xFF) == 0x55 && (mbr[511].toInt() and 0xFF) == 0xAA) {
            "$name has no partition table, so names no geometry"
        }
        val ends = (0 until 4).map { 446 + it * 16 }.filter { mbr[it + 4].toInt() != 0 }.map { entry ->
            (mbr[entry + 5].toInt() and 0xFF) + 1 to (mbr[entry + 6].toInt() and 0x3F)
        }.distinct()
        require(ends.size == 1) { "$name's partitions name ${if (ends.isEmpty()) "no" else "different"} geometry" }
        val (heads, sectors) = ends.single()
        val cylinder = heads.toLong() * sectors * SECTOR
        require(sectors > 0 && size % cylinder == 0L) { "$name is no whole number of its partitions' cylinders" }
        return Geometry(sectors, heads, (size / cylinder).toInt())
    }
}
