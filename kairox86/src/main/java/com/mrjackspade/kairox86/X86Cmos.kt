package com.mrjackspade.kairox86

/**
 * How a preset's stored CMOS holds its hard disk, so New game keeps that CMOS for whatever disk the
 * player gives the machine (KairoX86#341) instead of dropping it, which started the machine on its
 * BIOS's defaults behind a CMOS checksum error and lost the preset's boot order.
 */
sealed interface X86Cmos {
    /** The CMOS with the board's drive C as [disk] (null: no hard disk). */
    fun withDriveC(cmos: ByteArray, disk: Disk?): ByteArray

    /** A hard disk's geometry, as 86box.cfg gives it. */
    data class Disk(val cylinders: Int, val heads: Int, val sectors: Int)

    /**
     * The BIOS detects drive C at each start (its type Auto, as the TX97's Award 4.51PG has it): the
     * CMOS fits any disk, and none, as it is.
     */
    object Detected : X86Cmos {
        override fun withDriveC(cmos: ByteArray, disk: Disk?) = cmos.copyOf()
    }

    /**
     * Award 4.50's drive C (the PVI-486AP4's BIOS, which has no Auto type), as its own IDE HDD AUTO
     * DETECTION writes it: the User type (12h high nibble Fh, 19h its type), its cylinders at 26h-27h,
     * heads 28h, write precompensation 29h-2Ah (none, FFFFh), landing zone 2Bh-2Ch (the last cylinder)
     * and sectors 2Dh, the disk's own geometry, and LBA (3Bh bit 2) past the 1024 cylinders its NORMAL
     * mode reaches; None clears them. The AT checksum, the sum of 10h-2Dh, is at 2Eh-2Fh (high byte
     * first). Each value was read back from a CMOS the BIOS saved.
     */
    object Award450 : X86Cmos {
        private const val USER_TYPE = 0x31
        private const val LBA = 0x04

        override fun withDriveC(cmos: ByteArray, disk: Disk?): ByteArray {
            require(cmos.size >= 0x40) { "A CMOS of ${cmos.size} bytes has no Award drive C" }
            val out = cmos.copyOf()
            fun word(at: Int, value: Int) {
                out[at] = (value and 0xff).toByte()
                out[at + 1] = (value shr 8 and 0xff).toByte()
            }
            if (disk == null) {
                out[0x12] = (out[0x12].toInt() and 0x0f).toByte()
                out[0x19] = 0
                for (at in 0x26..0x2d) out[at] = 0
                out[0x3b] = (out[0x3b].toInt() and LBA.inv()).toByte()
            } else {
                require(disk.cylinders in 1..0xffff && disk.heads in 1..16 && disk.sectors in 1..63) { "Award drive C cannot be $disk" }
                out[0x12] = (out[0x12].toInt() and 0x0f or 0xf0).toByte()
                out[0x19] = USER_TYPE.toByte()
                word(0x26, disk.cylinders)
                out[0x28] = disk.heads.toByte()
                word(0x29, 0xffff)
                word(0x2b, disk.cylinders - 1)
                out[0x2d] = disk.sectors.toByte()
                out[0x3b] = (if (disk.cylinders > 1024) out[0x3b].toInt() or LBA else out[0x3b].toInt() and LBA.inv()).toByte()
            }
            val sum = (0x10..0x2d).sumOf { out[it].toInt() and 0xff }
            out[0x2e] = (sum shr 8 and 0xff).toByte()
            out[0x2f] = (sum and 0xff).toByte()
            return out
        }
    }
}
