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
 *   mouse, IDE with an ATAPI CD-ROM (FreeDOS 1.3's 1.44M installer).
 * - [WIN9X]: a Pentium MMX 233 on the ASUS TX97, 64 MB, S3 Trio64V2/DX, Sound Blaster 16, IDE with
 *   an ATAPI CD-ROM, its BIOS booting the CD first (Windows 98 SE Setup, started from a DOS floppy
 *   with the CD's driver).
 */
object X86Presets {
    /** A preset: its folder in assets/presets, its row's name, and the hardware whose firmware it needs. */
    class Preset(val id: String, val label: Int, val files: List<String>, val machine: String, val cards: Map<String, String>)

    val XT = Preset("xt", R.string.preset_xt, listOf("86box.cfg"), "ibmpc82",
        mapOf(X86Hardware.VIDEO to "cga", X86Hardware.SOUND to "adlib"))
    val DOS_486 = Preset("486", R.string.preset_486, listOf("86box.cfg", "nvr/486ap4.nvr"), "486ap4",
        mapOf(X86Hardware.VIDEO to "s3_trio64v2dx_pci", X86Hardware.SOUND to "sb16"))
    val WIN9X = Preset("pentium", R.string.preset_win9x, listOf("86box.cfg", "nvr/tx97.nvr"), "tx97",
        mapOf(X86Hardware.VIDEO to "s3_trio64v2dx_pci", X86Hardware.SOUND to "sb16"))

    val all = listOf(XT, DOS_486, WIN9X)

    /**
     * Why [preset] cannot be made with the player's firmware (its machine's or a card's is missing),
     * or null when it can.
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
        BlankDisk.Folder("preset-${preset.id}", UiText.res(preset.label), preset.files.map { path ->
            path to { output: java.io.OutputStream ->
                context.assets.open("presets/${preset.id}/$path").use { it.copyTo(output) }
                Unit
            }
        }) { unavailable(preset) }
    }
}
