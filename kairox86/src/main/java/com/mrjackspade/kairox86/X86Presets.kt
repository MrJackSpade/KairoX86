package com.mrjackspade.kairox86

import android.content.Context
import com.mrjackspade.kairo.frontend.BlankDisk
import com.mrjackspade.kairo.frontend.UiText

/**
 * The hardware sets a new machine starts from (KairoX86#184), offered under Manage library › New
 * game: each a complete machine folder, its 86box.cfg and the CMOS its BIOS saved (assets/presets/
 * <id>), every setting changeable afterwards (X86Settings). Each was chosen by booting its OS's
 * installer on it:
 * - [XT]: an IBM PC on GLaBIOS, the free BIOS the app ships, so it needs no firmware from the
 *   player; CGA, AdLib, a 720K and a 360K drive (FreeDOS 1.3's 720K installer).
 * - [DOS_486]: a 486DX2-66 on the ASUS PVI-486AP4, 16 MB, S3 Trio64V2/DX, Sound Blaster 16, PS/2
 *   mouse, IDE with a blank 504 MB hard disk and an ATAPI CD-ROM (FreeDOS 1.3's 1.44M installer).
 *   Its CMOS holds the disk as its BIOS's IDE HDD AUTO DETECTION found it (User Type, 1024/16/63)
 *   and boots A, then C: an installer floppy when one is in, the installed disk when none is. Its
 *   IDE HDD Block Mode is off (KairoX86#216): this BIOS's INT 13h writes a drive's control byte
 *   before it checks the drive exists, and for drives 84h-87h that byte is ROM text, which sets the
 *   no-retry flag that makes it send READ MULTIPLE as C0h. FreeDOS's FDISK asks for all eight
 *   drives, and the drive rejects the C0h, so block mode breaks FreeDOS 1.3's installer.
 * - [WIN9X]: a Pentium MMX 233 on the ASUS TX97, 64 MB, S3 Trio64V2/DX, Sound Blaster 16, IDE with
 *   a blank 2 GB hard disk, which its BIOS detects at each start (LBA), and an ATAPI CD-ROM. Its
 *   BIOS boots A, then the CD, then C (Boot Sequence A,CDROM,C: CMOS byte 3Ch, outside the
 *   checksummed 10h-2Dh): a boot floppy or bootable CD always starts, the installed disk when neither
 *   is in (KairoX86#342). It booted the CD first before, so once FDISK had written a partition
 *   table, Windows 98 Setup's boot floppy never started again: the empty partition's MBR stopped at
 *   "PRESS A KEY TO REBOOT".
 */
object X86Presets {
    /**
     * A preset: its folder in assets/presets, its row's name, the hardware whose firmware it needs,
     * the blank hard disk its 86box.cfg names (KairoX86#162), written into the new folder as
     * [HARD_DISK], and how its stored CMOS ([cmosFile], among [files]) holds that disk ([cmos]), so New
     * game keeps it for any disk (KairoX86#341).
     */
    class Preset(val id: String, val label: Int, val files: List<String>, val machine: String, val cards: Map<String, String>,
                 val hardDisk: X86BlankDisk? = null, val cmos: X86Cmos? = null) {
        /** The stored CMOS among [files], with [cmos]; none for a preset without one. */
        val cmosFile: String? = files.singleOrNull { it.startsWith("nvr/") }

        init {
            require((cmos == null) == (cmosFile == null)) { "Preset $id: a stored CMOS needs its kind (X86Cmos), and only one does" }
        }
    }

    /** A new machine's blank hard disk, as its 86box.cfg names it (hdd_01_fn). */
    const val HARD_DISK = "disk.vhd"

    val XT = Preset("xt", R.string.preset_xt, listOf("86box.cfg"), "ibmpc82",
        mapOf(X86Hardware.VIDEO to "cga", X86Hardware.SOUND to "adlib"))
    // The 486's disk is the 504 MB a DOS-era BIOS addresses by CHS (1024 cylinders, 16 heads, 63
    // sectors); the Pentium's is 2 GB, past it by LBA, room for Windows 98 and its games.
    val DOS_486 = Preset("486", R.string.preset_486, listOf("86box.cfg", "nvr/486ap4.nvr"), "486ap4",
        mapOf(X86Hardware.VIDEO to "s3_trio64v2dx_pci", X86Hardware.SOUND to "sb16"), X86BlankDisk(1024, 16, 63), X86Cmos.Award450)
    val WIN9X = Preset("pentium", R.string.preset_win9x, listOf("86box.cfg", "nvr/tx97.nvr"), "tx97",
        mapOf(X86Hardware.VIDEO to "s3_trio64v2dx_pci", X86Hardware.SOUND to "sb16"), X86BlankDisk(4096, 16, 63), X86Cmos.Detected)

    val all = listOf(XT, DOS_486, WIN9X)

    /**
     * Why [preset] cannot be made with the player's firmware (its machine's or a card's is missing),
     * or null when it can. New game offers it anyway, with a page for the firmware (KairoX86#438).
     */
    fun unavailable(preset: Preset): UiText? {
        val machine = X86Hardware.machines().firstOrNull { it.id == preset.machine }
            ?: error("86Box has no machine ${preset.machine} for preset ${preset.id}")
        val takes = X86Hardware.takes(preset.machine)
        val cards = preset.cards.map { (kind, id) ->
            takes.cards.getValue(kind).firstOrNull { it.id == id } ?: error("${preset.machine} takes no $kind $id (preset ${preset.id})")
        }
        return UiText.res(R.string.setting_firmware_missing).takeIf { !machine.available || cards.any { !it.available } }
    }

    /** The presets as new entries the create flow writes, each from its assets. */
    fun blankDisks(context: Context): List<BlankDisk> = all.map { preset ->
        val assets = preset.files.map { path ->
            BlankDisk.File(path) { output -> context.assets.open("presets/${preset.id}/$path").use { it.copyTo(output) } }
        }
        val disk = preset.hardDisk?.let { blank -> listOf(BlankDisk.File(HARD_DISK) { output -> blank.write(output) }) }.orEmpty()
        BlankDisk.Folder("preset-${preset.id}", UiText.res(preset.label), assets + disk) { unavailable(preset) }
    }
}
