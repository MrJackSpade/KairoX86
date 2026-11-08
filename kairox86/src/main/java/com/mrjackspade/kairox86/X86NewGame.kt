package com.mrjackspade.kairox86

import android.content.Context
import com.mrjackspade.kairo.frontend.BlankDisk
import com.mrjackspade.kairo.frontend.ChoiceOption
import com.mrjackspade.kairo.frontend.NewGameWorkflow
import com.mrjackspade.kairo.frontend.UiText
import com.mrjackspade.kairo.frontend.WorkflowField
import com.mrjackspade.kairo.frontend.WorkflowPage
import java.io.OutputStream
import com.mrjackspade.kairo.frontend.R as FrontendR

/**
 * KairoX86's New game workflow (KairoX86#332, the shared engine Kairo#181):
 * 1. **Kind:** a preset PC (X86Presets), a Custom PC, or a blank floppy.
 * 2. **Machine**, 3. **Processor and memory**, 4. **Cards:** 86Box's choices as the machine settings
 *    list them (X86Settings, so each narrows by the machine and the choices before it), for a PC.
 *    A preset's own `86box.cfg` gives the defaults; a Custom PC takes 86Box's.
 * 5. **Hard disk:** none or a blank disk's size, for a PC with a hard disk controller. The sizes are
 *    the controller's kind: IDE disks to 8 GB, the XT and AT controllers' small MFM disks.
 * 6. The name (the shared engine's page).
 *
 * Create writes the machine folder: its `86box.cfg` (the preset's, or a new one, with every choice
 * made), the preset's CMOS while its machine and disk are the preset's own (the CMOS holds the
 * disk's geometry), and the blank disk.
 */
object X86NewGame {
    private const val CUSTOM = "custom"
    private const val PRESET = "preset-"
    private const val DISK = "hard_disk"
    private const val NO_DISK = "none"

    /** A blank hard disk's geometry, as its choice keeps it ("cylinders,heads,sectors"). */
    private class Geometry(val cylinders: Int, val heads: Int, val sectors: Int) {
        val id get() = "$cylinders,$heads,$sectors"
        val megabytes: Long get() = cylinders.toLong() * heads * sectors * 512 / (1024 * 1024)
        companion object {
            fun of(id: String) = id.split(',').map(String::toInt).let { Geometry(it[0], it[1], it[2]) }
        }
    }

    // IDE: 63 sectors and 16 heads, by cylinders from a CHS BIOS's 504 MB to 8 GB (LBA)
    private val IDE_DISKS = listOf(260, 520, 1024, 2048, 4096, 8192, 16383).map { Geometry(it, 16, 63) }
    // MFM and XTA (the XT's and AT's controllers): 17 sectors a track, the sizes of the time
    private val MFM_DISKS = listOf(Geometry(306, 4, 17), Geometry(615, 4, 17), Geometry(977, 5, 17), Geometry(1024, 8, 17))
    // RLL (the ST-11R, the WD 27X cards): 26 sectors a track
    private val RLL_DISKS = listOf(Geometry(615, 4, 26), Geometry(820, 6, 26), Geometry(1024, 8, 26))
    // ESDI: 36 sectors a track
    private val ESDI_DISKS = listOf(Geometry(1024, 9, 36), Geometry(1224, 15, 36))

    fun workflow(context: Context): NewGameWorkflow {
        val presets = X86Presets.all.associateBy { PRESET + it.id }
        // A preset's 86box.cfg, read once, for its defaults and its folder
        val configs = HashMap<String, IniText>()
        fun configOf(kind: String): IniText? = presets[kind]?.let { preset ->
            configs.getOrPut(kind) { IniText(context.assets.open("presets/${preset.id}/86box.cfg").use { it.readBytes().toString(Charsets.UTF_8) }) }
        }
        val floppies = X86BlankFloppy.all.map { floppy ->
            BlankDisk.Image(floppy.id, UiText.res(FrontendR.string.kairo_blank_floppy, floppy.label), "img", floppy::write)
        }
        fun pc(values: Map<String, String>) = values[NewGameWorkflow.KIND].let { it == CUSTOM || it in presets }

        /** A machine setting as a field: its choices as the machine settings narrow them, its default the preset's. */
        fun field(setting: X86Settings.Setting) = WorkflowField.Select(setting.option.id, setting.option.label,
            { values -> setting.option.choices(values) },
            { values -> configOf(values.getValue(NewGameWorkflow.KIND))?.let(setting.read) ?: newDefault(setting, values) })

        val kinds = WorkflowField.Select(NewGameWorkflow.KIND, UiText.res(FrontendR.string.kairo_new_game_kind), {
            presets.map { (id, preset) -> ChoiceOption(id, UiText.res(preset.label), null, X86Presets.unavailable(preset)) } +
                ChoiceOption(CUSTOM, UiText.res(R.string.preset_custom)) +
                floppies.map { ChoiceOption(it.id, it.label) }
        }, { PRESET + X86Presets.DOS_486.id })
        val hardware = listOf(X86Settings.machine, X86Settings.processor, X86Settings.memory)
        val cards = listOf(X86Settings.video, X86Settings.sound, X86Settings.midi, X86Settings.network, X86Settings.hdc,
            X86Settings.scsi, X86Settings.fdc, X86Settings.mouse, X86Settings.joystick)
        val disk = WorkflowField.Select(DISK, UiText.res(FrontendR.string.kairo_hard_disk), { values ->
            listOf(ChoiceOption(NO_DISK, UiText.res(FrontendR.string.kairo_none))) +
                disksFor(values).map { ChoiceOption(it.id, UiText.res(FrontendR.string.kairo_memory_mb, it.megabytes.toInt())) }
        }, { values ->
            val preset = presets[values[NewGameWorkflow.KIND]]
            preset?.hardDisk?.let { Geometry(it.cylinders, it.heads, it.sectors).id } ?: if (preset != null) NO_DISK else disksFor(values).firstOrNull()?.id ?: NO_DISK
        })
        val pages = listOf(
            WorkflowPage(NewGameWorkflow.KIND, UiText.res(FrontendR.string.kairo_library_new_game), listOf(kinds)),
            WorkflowPage("machine", UiText.res(FrontendR.string.kairo_option_machine), listOf(field(X86Settings.machine)), ::pc),
            WorkflowPage("processor", UiText.res(R.string.new_game_processor_memory), listOf(field(X86Settings.processor), field(X86Settings.memory)), ::pc),
            WorkflowPage("cards", UiText.res(R.string.new_game_cards), cards.map(::field), ::pc),
            WorkflowPage("disk", UiText.res(FrontendR.string.kairo_hard_disk), listOf(disk)) { values -> pc(values) && values[X86Settings.hdc.option.id] != "none" })

        return NewGameWorkflow(pages) { values ->
            val kind = values.getValue(NewGameWorkflow.KIND)
            floppies.firstOrNull { it.id == kind } ?: machineFolder(context, kind, presets[kind], configOf(kind), hardware + cards, values)
        }
    }

    /**
     * A new machine's default for [setting] where its preset says nothing: 86Box's, except a video card,
     * which 86Box leaves out on a board without one onboard: a new PC gets the first card the board takes.
     */
    private fun newDefault(setting: X86Settings.Setting, values: Map<String, String>): String {
        val default = setting.option.default(values)
        if (setting !== X86Settings.video || default != "none") return default
        return setting.option.choices(values).first { it.id != "none" && it.disabledReason == null }.id
    }

    /** The disks the chosen controller takes, by its bus, and on an MFM card by whether it records RLL. */
    private fun disksFor(values: Map<String, String>): List<Geometry> = when (bus(values)) {
        "ide" -> IDE_DISKS
        "esdi" -> ESDI_DISKS
        "mfm" -> if (values.getValue(X86Settings.hdc.option.id).let { it == "st506_xt_st11_r" || it.endsWith("27x") }) RLL_DISKS else MFM_DISKS
        else -> MFM_DISKS
    }

    /**
     * 86Box's bus of a hard disk on the chosen controller, by its card's internal name (86Box's disk/hdc_*.c):
     * "mfm" for the ST-506 cards (RLL ones too), "xta", "esdi", and "ide" for the rest. A board's own
     * controller ("internal") is taken as IDE, as nearly every one is: 86Box does not say which it is.
     */
    private fun bus(values: Map<String, String>): String = values.getValue(X86Settings.hdc.option.id).let { hdc ->
        when {
            hdc.startsWith("st506") -> "mfm"
            hdc.startsWith("xta") -> "xta"
            hdc.startsWith("esdi") -> "esdi"
            else -> "ide"
        }
    }

    private fun machineFolder(context: Context, kind: String, preset: X86Presets.Preset?, presetConfig: IniText?,
                              settings: List<X86Settings.Setting>, values: Map<String, String>): BlankDisk {
        val config = IniText(presetConfig?.toString() ?: "")
        // Each choice that differs from what the configuration already says (its key, or 86Box's default without one)
        for (setting in settings) values[setting.option.id]?.let { value ->
            if (value != (setting.read(config) ?: setting.option.default(values))) setting.changes(value).forEach { config[it.section, it.key] = it.value }
        }
        val geometry = values[DISK]?.takeIf { it != NO_DISK }?.let(Geometry::of)
        val bus = bus(values)
        config[X86Library.HARD_DISKS, "hdd_01_fn"] = geometry?.let { X86Presets.HARD_DISK }
        config[X86Library.HARD_DISKS, "hdd_01_parameters"] = geometry?.let { "${it.sectors}, ${it.heads}, ${it.cylinders}, 0, $bus" }
        config[X86Library.HARD_DISKS, "hdd_01_ide_channel"] = geometry?.takeIf { bus == "ide" }?.let { "0:0" }
        val files = mutableListOf<Pair<String, (OutputStream) -> Unit>>("86box.cfg" to { output -> output.write(config.toString().toByteArray()) })
        // The preset's CMOS holds its machine and disk: kept only while both are the preset's
        if (preset != null && values[X86Settings.machine.option.id] == preset.machine &&
            geometry?.id == preset.hardDisk?.let { Geometry(it.cylinders, it.heads, it.sectors).id }) {
            for (path in preset.files.filter { it != "86box.cfg" }) files += path to { output ->
                context.assets.open("presets/${preset.id}/$path").use { it.copyTo(output) }
            }
        }
        geometry?.let { files += X86Presets.HARD_DISK to { output -> X86BlankDisk(it.cylinders, it.heads, it.sectors).write(output) } }
        return BlankDisk.Folder(kind, UiText.res(if (preset != null) preset.label else R.string.preset_custom), files)
    }
}
