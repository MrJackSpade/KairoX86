package com.mrjackspade.kairox86

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * A hard disk image a machine can take (KairoX86#217): one that names its own geometry, as 86Box
 * reads it when the machine starts (third_party/86box/src/disk/hdd_image.c), so its 86box.cfg can
 * say the same. A raw image names none: 86Box would take whatever 86box.cfg says, and grow the file
 * to it, so a raw image is no hard disk here.
 */
object X86HardDisk {
    /** A disk's geometry: sectors per track, heads and cylinders, as 86box.cfg's hdd_NN_parameters give them. */
    data class Geometry(val sectors: Int, val heads: Int, val cylinders: Int)

    /** The hard disk images 86Box reads with their geometry, by extension. */
    val IMAGES = setOf("vhd", "hdi", "hdx")

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
            else -> error("$name is no hard disk image (${IMAGES.joinToString()})")
        }.also { geometry ->
            require(geometry.sectors > 0 && geometry.heads > 0 && geometry.cylinders > 0) { "$name names no geometry" }
        }
}
