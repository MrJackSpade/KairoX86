package com.mrjackspade.kairox86

import android.content.Context
import com.mrjackspade.kairo.frontend.BlankDisk
import com.mrjackspade.kairo.frontend.UiText

/**
 * The hardware sets a new machine starts from (KairoX86#184), offered under Manage library › New
 * game: each a machine folder's 86box.cfg (assets/presets/<id>), every setting changeable afterwards
 * (X86Settings). None needs firmware from the player: each runs on the free firmware the app ships.
 * - [XT]: an IBM PC on GLaBIOS; CGA, AdLib, a 720K and a 360K drive (FreeDOS 1.3's 720K installer).
 * - [DOS_486] and [WIN9X] run on the free machine (KairoX86#446, "[i440FX] KairoX86 PC", which boots
 *   SeaBIOS), with a Cirrus Logic GD5446 on SeaVGABIOS and a Sound Blaster 16, IDE with a blank hard
 *   disk SeaBIOS detects at each start, and an ATAPI CD-ROM. Their boot order is 86box.cfg's
 *   [KairoX86] boot_order, which SeaBIOS takes as it starts:
 *   - [DOS_486]: a 486DX2-66, 16 MB, a 1.44M and a 1.2M drive and a 504 MB disk, the size a DOS-era
 *     BIOS addresses by CHS (1024 cylinders, 16 heads, 63 sectors); boots A, then C: an installer
 *     floppy when one is in, the installed disk when none is (FreeDOS 1.3's 1.44M installer).
 *   - [WIN9X]: a Pentium MMX 233, 64 MB, a 1.44M drive and a 2 GB disk; boots A, then the CD, then C:
 *     a boot floppy or bootable CD always starts, the installed disk when neither is in (KairoX86#342).
 */
object X86Presets {
    /**
     * A preset: its folder in assets/presets, its row's name, the hardware whose firmware it needs, and
     * the blank hard disk its 86box.cfg names (KairoX86#162), written into the new folder as [HARD_DISK].
     */
    class Preset(val id: String, val label: Int, val machine: String, val cards: Map<String, String>,
                 val hardDisk: X86BlankDisk? = null)

    /** A new machine's blank hard disk, as its 86box.cfg names it (hdd_01_fn). */
    const val HARD_DISK = "disk.vhd"

    /** The preset's 86box.cfg, the one file of its folder. */
    const val CONFIG = "86box.cfg"

    /** The free machine (KairoX86#446) and its video card, as 86Box names them. */
    const val FREE_MACHINE = "kairo_pc"
    const val FREE_VIDEO = "cl_gd5446_migrated_pci"

    val XT = Preset("xt", R.string.preset_xt, "ibmpc82", mapOf(X86Hardware.VIDEO to "cga", X86Hardware.SOUND to "adlib"))
    val DOS_486 = Preset("486", R.string.preset_486, FREE_MACHINE,
        mapOf(X86Hardware.VIDEO to FREE_VIDEO, X86Hardware.SOUND to "sb16"), X86BlankDisk(1024, 16, 63))
    val WIN9X = Preset("pentium", R.string.preset_win9x, FREE_MACHINE,
        mapOf(X86Hardware.VIDEO to FREE_VIDEO, X86Hardware.SOUND to "sb16"), X86BlankDisk(4096, 16, 63))

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
        val config = BlankDisk.File(CONFIG) { output -> context.assets.open("presets/${preset.id}/$CONFIG").use { it.copyTo(output) } }
        val disk = preset.hardDisk?.let { blank -> listOf(BlankDisk.File(HARD_DISK) { output -> blank.write(output) }) }.orEmpty()
        BlankDisk.Folder("preset-${preset.id}", UiText.res(preset.label), listOf(config) + disk) { unavailable(preset) }
    }
}
