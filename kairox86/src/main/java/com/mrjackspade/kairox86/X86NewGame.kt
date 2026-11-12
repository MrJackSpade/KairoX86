package com.mrjackspade.kairox86

import android.content.Context
import com.mrjackspade.kairo.frontend.BlankDisk
import com.mrjackspade.kairo.frontend.ChoiceOption
import com.mrjackspade.kairo.frontend.CustomValue
import com.mrjackspade.kairo.frontend.FirmwareNeed
import com.mrjackspade.kairo.frontend.FirmwareSet
import com.mrjackspade.kairo.frontend.GameDisks
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
 * 5. **Disks** (KairoX86#338): the hard disk, none or a blank disk's size (the controller's kind's
 *    sizes, or one typed, KairoX86#337), for a PC with a hard disk controller; and an image from the
 *    games folder, or none, for each floppy and CD-ROM drive the machine being made has.
 * 6. The name (the shared engine's page).
 *
 * Create writes the machine folder: its `86box.cfg` (the preset's, or a new one, with every choice
 * made), the preset's CMOS while its machine and hard disk controller are the preset's own, with the
 * hard disk the player chose in it (KairoX86#341: [X86Cmos]), the blank disk, and the drives'
 * images, copied in (unpacked from an archive).
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

    /** The drive fields' IDs, by media slot (X86Library.DRIVE_KEYS): Floppy A, Floppy B, the CD-ROM. */
    private val DRIVE_FIELDS = listOf("drive-a", "drive-b", "drive-cd")

    /**
     * New game's workflow; [images] gives the games folder's disk images, for the Disks page's drives,
     * and [filesOf] the files each is made of (X86Library.imageFiles: a cue sheet's tracks too).
     */
    fun workflow(context: Context, images: () -> List<X86Entry>, filesOf: (X86Entry) -> List<X86Library.ImageFile>,
                 firmware: () -> FirmwareSet): NewGameWorkflow {
        val presets = X86Presets.all.associateBy { PRESET + it.id }
        // A preset's 86box.cfg, read once, for its defaults and its folder
        val configs = HashMap<String, IniText>()
        fun configOf(kind: String): IniText? = presets[kind]?.let { preset ->
            configs.getOrPut(kind) { IniText(context.assets.open("presets/${preset.id}/86box.cfg").use { it.readBytes().toString(Charsets.UTF_8) }) }
        }
        val floppies = X86BlankFloppy.all.map { floppy ->
            BlankDisk.Image(floppy.id, UiText.res(FrontendR.string.kairo_blank_floppy, floppy.label), "img", write = floppy::write)
        }
        fun pc(values: Map<String, String>) = values[NewGameWorkflow.KIND].let { it == CUSTOM || it in presets }

        /**
         * A machine setting as a field: its choices as the machine settings narrow them, its default the preset's.
         * Hardware whose firmware is missing can be chosen here, marked as needing it: the firmware page then
         * asks for it (KairoX86#438).
         */
        fun field(setting: X86Settings.Setting) = WorkflowField.Select(setting.option.id, setting.option.label,
            { values -> setting.option.choices(values).map { pickable(it, firmwareKind(setting)) } },
            { values -> configOf(values.getValue(NewGameWorkflow.KIND))?.let(setting.read) ?: newDefault(setting, values) },
            custom = { values -> setting.option.custom(values) })

        // A preset's hardware, or the player's own (Custom PC), apart from the blank floppies (KairoX86#335)
        val presetSection = UiText.res(R.string.new_game_presets)
        val customSection = UiText.res(R.string.new_game_custom)
        val floppySection = UiText.res(R.string.new_game_blank_floppies)
        val kinds = WorkflowField.Select(NewGameWorkflow.KIND, UiText.res(FrontendR.string.kairo_new_game_kind), {
            // Marked by the files the preset's own hardware reads, as the firmware page lists them: a card's other
            // firmware versions make it available to 86Box, but the preset runs the one its 86box.cfg names
            presets.map { (id, preset) ->
                val needs = firmwareNeeds(firmware(), configOf(id), preset.machine, preset.cards.toList())
                ChoiceOption(id, UiText.res(preset.label), FIRMWARE_NEEDED.takeIf { needs.isNotEmpty() }, section = presetSection)
            } +
                ChoiceOption(CUSTOM, UiText.res(R.string.preset_custom), section = customSection) +
                floppies.map { ChoiceOption(it.id, it.label, section = floppySection) }
        }, { PRESET + X86Presets.DOS_486.id })
        val hardware = listOf(X86Settings.machine, X86Settings.processor, X86Settings.memory)
        val cards = listOf(X86Settings.video, X86Settings.sound, X86Settings.midi, X86Settings.network, X86Settings.hdc,
            X86Settings.scsi, X86Settings.fdc, X86Settings.mouse, X86Settings.joystick)
        // A machine without a hard disk controller takes none
        fun takesDisk(values: Map<String, String>) = values[X86Settings.hdc.option.id] != "none"
        val disk = WorkflowField.Select(DISK, UiText.res(FrontendR.string.kairo_hard_disk), { values ->
            listOf(ChoiceOption(NO_DISK, UiText.res(FrontendR.string.kairo_none))) +
                (if (takesDisk(values)) disksFor(values).map { ChoiceOption(it.id, sizeLabel(it)) } else emptyList())
        }, { values ->
            val preset = presets[values[NewGameWorkflow.KIND]]
            preset?.hardDisk?.let { Geometry(it.cylinders, it.heads, it.sectors).id } ?: if (preset != null) NO_DISK else disksFor(values).firstOrNull()?.id ?: NO_DISK
        }, custom = { values -> typedDisk(values).takeIf { takesDisk(values) } })
        /** The drives the machine being made has: its preset's 86box.cfg's (or 86Box's defaults, for a Custom PC). */
        fun drives(values: Map<String, String>) = X86Library.drives(configOf(values.getValue(NewGameWorkflow.KIND)) ?: IniText(""))
        val driveFields = DRIVE_FIELDS.mapIndexed { slot, id ->
            val kind = if (slot < 2) X86Library.DiskKind.FLOPPY else X86Library.DiskKind.CD
            // A drive the machine does not have offers nothing, so the page leaves it out
            WorkflowField.Select(id, UiText.res(DRIVE_LABELS[slot]), { values ->
                if (slot !in drives(values)) emptyList()
                else listOf(ChoiceOption(NO_DISK, UiText.res(FrontendR.string.kairo_empty))) +
                    GameDisks.options(images().filter { it.playable && kind in it.kinds }) { it.imageSize.takeIf { size -> size >= 0 } }
            }, { NO_DISK })
        }
        val pages = listOf(
            WorkflowPage(NewGameWorkflow.KIND, UiText.res(FrontendR.string.kairo_library_new_game), listOf(kinds)),
            WorkflowPage("machine", UiText.res(FrontendR.string.kairo_option_machine), listOf(field(X86Settings.machine)), ::pc),
            WorkflowPage("processor", UiText.res(R.string.new_game_processor_memory), listOf(field(X86Settings.processor), field(X86Settings.memory)), ::pc),
            WorkflowPage("cards", UiText.res(R.string.new_game_cards), cards.map(::field), ::pc),
            WorkflowPage("disks", UiText.res(FrontendR.string.kairo_media_disks), listOf(disk) + driveFields, ::pc))

        // The firmware the PC's board and cards read that the player's set lacks, a page of its own (KairoX86#438)
        val firmwareFor = { values: Map<String, String> ->
            if (!pc(values)) emptyList() else firmwareNeeds(firmware(), configOf(values.getValue(NewGameWorkflow.KIND)),
                values.getValue(X86Settings.machine.option.id), cards.mapNotNull { setting ->
                    // Joysticks have no firmware, and no kind among the cards with options
                    val kind = X86Settings.cards.firstOrNull { it.first === setting }?.second
                    values[setting.option.id]?.let { id -> kind?.to(id) }
                })
        }
        return NewGameWorkflow(pages, firmware = firmwareFor) { values ->
            val kind = values.getValue(NewGameWorkflow.KIND)
            floppies.firstOrNull { it.id == kind } ?: machineFolder(context, kind, presets[kind], configOf(kind), hardware + cards, values,
                drives(values).associateWith { slot -> values[DRIVE_FIELDS[slot]]?.takeIf { it != NO_DISK }?.let { id -> filesOf(images().first { it.id == id }) } })
        }
    }

    private val DRIVE_LABELS = listOf(R.string.media_floppy_a, R.string.media_floppy_b, FrontendR.string.kairo_cd_rom)

    /** A blank disk's size, as the player reads it. */
    private fun sizeLabel(geometry: Geometry) = UiText.res(FrontendR.string.kairo_memory_mb, geometry.megabytes.toInt())

    /**
     * A disk size the player types (KairoX86#337), in MB, from 1 MB to the most the controller's bus
     * takes (its heads and sectors a track, and its cylinders: 16383 for IDE, 1024 for the others); kept
     * as the geometry the disk is written with: the whole cylinders that hold at least the size typed, a
     * cylinder being under 1 MB, so the size shown is the size typed.
     */
    private fun typedDisk(values: Map<String, String>): CustomValue {
        val (heads, sectors, cylinders) = busGeometry(values)
        val cylinderBytes = heads.toLong() * sectors * 512
        val most = (cylinders * cylinderBytes / (1024 * 1024)).toInt()
        val sizes = CustomValue.range(1, most, 1) { UiText.res(FrontendR.string.kairo_memory_mb, it) }
        fun geometryOf(megabytes: Int) = Geometry(
            ((megabytes.toLong() * 1024 * 1024 + cylinderBytes - 1) / cylinderBytes).toInt().coerceIn(1, cylinders), heads, sectors)
        return CustomValue(sizes.hint, { id -> if (id == NO_DISK) UiText.res(FrontendR.string.kairo_none) else sizeLabel(Geometry.of(id)) },
            sizes.problem, { typed -> geometryOf(typed.toInt()).id },
            { id -> id.takeIf { it != NO_DISK && it.contains(',') }?.let { Geometry.of(it) }
                ?.takeIf { it.heads == heads && it.sectors == sectors }?.megabytes?.toString() ?: "" })
    }

    /** The heads, sectors a track and most cylinders of a disk on the chosen controller's bus. */
    private fun busGeometry(values: Map<String, String>): Triple<Int, Int, Int> = when (bus(values)) {
        "ide" -> Triple(16, 63, 16383)
        "esdi" -> Triple(16, 36, 1024)
        "mfm" -> if (rll(values)) Triple(16, 26, 1024) else Triple(16, 17, 1024)
        else -> Triple(16, 17, 1024)
    }

    /**
     * A new machine's default for [setting] where its preset says nothing: 86Box's (the board's own
     * card where it has one), except where that is none: a video card, the first the board takes; a
     * network card, one the machine's system drives (KairoX86#336).
     */
    private fun newDefault(setting: X86Settings.Setting, values: Map<String, String>): String {
        val default = setting.option.default(values)
        if (default != "none") return default
        val taken = setting.option.choices(values).filter { it.id != "none" && it.disabledReason == null }.map { it.id }
        return when {
            setting === X86Settings.video -> taken.first()
            setting === X86Settings.network -> NETWORK_CARDS.getValue(networkSystem(values)).firstOrNull { it in taken } ?: default
            else -> default
        }
    }

    /** How New game marks hardware whose firmware the player has not imported: it can be chosen (KairoX86#438). */
    private val FIRMWARE_NEEDED = UiText.res(R.string.setting_firmware_needed)

    /**
     * [option] as New game offers it: hardware the settings refuse for its missing firmware can be chosen,
     * and board or card [kind] (null for a setting that is no hardware) is marked as needing firmware when a
     * file its own firmware reads is missing, as the firmware page lists them: a card with other firmware
     * versions is available to 86Box, but runs the default one.
     */
    private fun pickable(option: ChoiceOption, kind: String?): ChoiceOption {
        val needed = kind != null && X86Hardware.files(kind, option.id, null).any { !it.present }
        if (!needed && option.disabledReason !== X86Settings.firmwareMissing) return option
        return ChoiceOption(option.id, option.label, FIRMWARE_NEEDED.takeIf { needed }, null, option.folder, option.section)
    }

    /** The hardware kind whose firmware [setting] chooses: the board, a card kind, or null (joysticks, a processor). */
    private fun firmwareKind(setting: X86Settings.Setting): String? =
        if (setting === X86Settings.machine) X86Hardware.MACHINE else X86Settings.cards.firstOrNull { it.first === setting }?.second

    /**
     * The firmware files board [machine] and [cards] (each kind with its card) read that [set], the player's,
     * lacks (KairoX86#438), each as 86Box's own check names it (X86Hardware.files), with its firmware
     * choice as [config] (the preset's 86box.cfg) gives it, else its default: what it is, and why the
     * machine needs it.
     */
    private fun firmwareNeeds(set: FirmwareSet, config: IniText?, machine: String, cards: List<Pair<String, String>>): List<FirmwareNeed> {
        val index = indexOf(set)
        val board = X86Hardware.machines().first { it.id == machine }
        return (listOf(Triple(X86Hardware.MACHINE, machine, board.name)) + cards.map { (kind, id) ->
            Triple(kind, id, X86Hardware.takes(machine).cards.getValue(kind).first { it.id == id }.name)
        }).flatMap { (kind, id, name) ->
            val files = X86Hardware.files(kind, id, config?.let { firmwareChoice(it, kind, id) })
            val device = UiText.fixed(name.replace(BUS_PREFIX, ""))
            val (label, about) = when (kind) {
                X86Hardware.MACHINE -> R.string.firmware_need_board to R.string.firmware_need_board_about
                X86Hardware.VIDEO -> R.string.firmware_need_video to R.string.firmware_need_video_about
                X86Hardware.MIDI -> R.string.firmware_need_card to R.string.firmware_need_midi_about
                else -> R.string.firmware_need_card to R.string.firmware_need_card_about
            }
            files.withIndex().filter { !it.value.present }.map { (i, file) ->
                val known = index[file.path] ?: error("86Box reads ${file.path}, which the firmware index does not list")
                val title = UiText.res(label, device)
                FirmwareNeed(set, FirmwareSet.Part(file.path,
                    if (files.size == 1) title else UiText.res(R.string.firmware_need_file_of, title, i + 1, files.size),
                    UiText.res(about, device), emptySet(), required = true, sizes = known.sizes, sha1 = known.sha1))
            }
        }
    }

    /** 86Box's bracketed prefix on a board or card name, its chipset or bus ("[i420EX] ASUS PVI-486AP4"). */
    private val BUS_PREFIX = Regex("^\\[[^]]*]\\s*")

    /** [set]'s files by their place in it, made once for the set. */
    private var indexed: Pair<FirmwareSet, Map<String, FirmwareSet.Part>>? = null

    @Synchronized private fun indexOf(set: FirmwareSet): Map<String, FirmwareSet.Part> =
        indexed?.takeIf { it.first === set }?.second ?: set.parts.associateBy { it.name }.also { indexed = set to it }

    /** The firmware choice [config] makes for board or card [id] of [kind] (its BIOS option's value), or null for its default. */
    private fun firmwareChoice(config: IniText, kind: String, id: String): String? =
        X86Hardware.options(kind, id).let { options -> options.options.firstOrNull { it.bios }?.let { config[options.section, it.key] } }

    /** What a new machine's network card is for: DOS's packet drivers, or Windows 9x's own drivers. */
    private fun networkSystem(values: Map<String, String>) =
        if (values[NewGameWorkflow.KIND] in setOf(PRESET + X86Presets.XT.id, PRESET + X86Presets.DOS_486.id)) "dos" else "windows"

    /**
     * A new machine's network card (KairoX86#336), the first the board takes: one the machine's
     * system drives with no extra drivers. DOS: an NE2000-compatible card, which DOS packet drivers
     * support most widely (16-bit, else the 8-bit NE2000 or NE1000 an XT takes). Windows 9x: the AMD
     * PCnet-PCI II on a PCI board (Windows 95 OSR2 and 98's own "AMD PCNET Family" driver), else an
     * NE2000-compatible card (Windows' own NE2000 driver). A board with no slot for any keeps none.
     */
    private val NETWORK_CARDS = mapOf(
        "dos" to listOf("ne2k", "ne2k8", "ne1k"),
        "windows" to listOf("pcnetpci", "ne2k", "ne2k8", "ne1k"))

    /** The disks the chosen controller takes, by its bus, and on an MFM card by whether it records RLL. */
    private fun disksFor(values: Map<String, String>): List<Geometry> = when (bus(values)) {
        "ide" -> IDE_DISKS
        "esdi" -> ESDI_DISKS
        "mfm" -> if (rll(values)) RLL_DISKS else MFM_DISKS
        else -> MFM_DISKS
    }

    /** Whether the chosen MFM controller records RLL (the ST-11R, the WD 27X cards): 26 sectors a track. */
    private fun rll(values: Map<String, String>) = values.getValue(X86Settings.hdc.option.id).let { it == "st506_xt_st11_r" || it.endsWith("27x") }

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
                              settings: List<X86Settings.Setting>, values: Map<String, String>, media: Map<Int, List<X86Library.ImageFile>?>): BlankDisk {
        val config = IniText(presetConfig?.toString() ?: "")
        // Each choice that differs from what the configuration already says (its key, or 86Box's default without one)
        for (setting in settings) values[setting.option.id]?.let { value ->
            if (value != (setting.read(config) ?: setting.option.default(values))) setting.changes(value).forEach { config[it.section, it.key] = it.value }
        }
        // The hard disk only on a controller that takes one (the Disks page offers it there)
        val geometry = values[DISK]?.takeIf { it != NO_DISK && values[X86Settings.hdc.option.id] != "none" }?.let(Geometry::of)
        val bus = bus(values)
        config[X86Library.HARD_DISKS, "hdd_01_fn"] = geometry?.let { X86Presets.HARD_DISK }
        config[X86Library.HARD_DISKS, "hdd_01_parameters"] = geometry?.let { "${it.sectors}, ${it.heads}, ${it.cylinders}, 0, $bus" }
        config[X86Library.HARD_DISKS, "hdd_01_ide_channel"] = geometry?.takeIf { bus == "ide" }?.let { "0:0" }
        val files = mutableListOf(BlankDisk.File("86box.cfg") { output -> output.write(config.toString().toByteArray()) })
        // The preset's CMOS holds its board's settings (its boot order among them) and its disk: kept
        // while the board and its hard disk controller are the preset's, the chosen disk written in
        // (KairoX86#341). Another board, or a disk on another controller, starts on its BIOS's defaults.
        if (preset != null && values[X86Settings.machine.option.id] == preset.machine &&
            values[X86Settings.hdc.option.id] == (X86Settings.hdc.read(presetConfig ?: config) ?: X86Settings.hdc.option.default(values))) {
            for (path in preset.files.filter { it != "86box.cfg" }) files += BlankDisk.File(path) { output ->
                val stored = context.assets.open("presets/${preset.id}/$path").use { it.readBytes() }
                output.write(if (path != preset.cmosFile) stored
                    else checkNotNull(preset.cmos).withDriveC(stored, geometry?.let { X86Cmos.Disk(it.cylinders, it.heads, it.sectors) }))
            }
        }
        geometry?.let { files += BlankDisk.File(X86Presets.HARD_DISK) { output -> X86BlankDisk(it.cylinders, it.heads, it.sectors).write(output) } }
        // Each drive's image, with the files it is made of, copied in by their own names (one image in two
        // drives, once), and named in 86box.cfg; two different files of one name cannot both be there.
        val named = HashMap<String, List<X86Library.ImageFile>>()
        for ((slot, image) in media) {
            val name = image?.first()?.name
            if (image != null && name != null && name !in named) {
                for (file in image) check(files.none { it.path.equals(file.name, ignoreCase = true) }) {
                    context.getString(R.string.machine_disk_name_taken, file.name)
                }
                named[name] = image
                // Each by its size, so the Creating page shows how far the copy is (Kairo#184); -1 is not known
                image.forEach { file -> files += BlankDisk.File(file.name, file.size.coerceAtLeast(0), file.write) }
            }
            config[X86Library.DRIVES, X86Library.DRIVE_KEYS[slot]] = name
        }
        files[0] = BlankDisk.File("86box.cfg") { output -> output.write(config.toString().toByteArray()) }
        return BlankDisk.Folder(kind, UiText.res(if (preset != null) preset.label else R.string.preset_custom), files)
    }

}
