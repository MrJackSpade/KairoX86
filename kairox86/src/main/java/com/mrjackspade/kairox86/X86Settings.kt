package com.mrjackspade.kairox86

import com.mrjackspade.kairo.frontend.R as FrontendR
import com.mrjackspade.kairo.frontend.ChoiceOption
import com.mrjackspade.kairo.frontend.MachineOption
import com.mrjackspade.kairo.frontend.CustomValue
import com.mrjackspade.kairo.frontend.UiText

/**
 * A machine's settings (Kairo#142, #143): each a [MachineOption] kept in the machine folder's own
 * 86box.cfg, with 86Box's own values as its choices. The hardware's choices are the ones 86Box offers
 * the chosen machine (X86Hardware), and a machine without a key takes 86Box's default, which is the
 * option's default.
 */
object X86Settings {
    /** One key of 86box.cfg a setting changes: null removes it. */
    class Change(val section: String, val key: String, val value: String?)

    /**
     * A setting: [read] gives the machine's own value from its 86box.cfg (null: 86Box's default), and
     * [changes] the keys a value (null: the default) sets.
     */
    class Setting(val option: MachineOption, val read: (IniText) -> String?, val changes: (String?) -> List<Change>)

    private const val MACHINE = "Machine"
    /** The section of 86box.cfg whose keys only KairoX86's 86Box reads (config_kairo_int, tools/patches.py). */
    const val KAIROX86 = "KairoX86"
    private const val MACHINE_ID = "machine"
    private const val FIRST_MACHINE = "ibmpc"

    /** A setting kept in one key. */
    private fun single(option: MachineOption, section: String, key: String) =
        Setting(option, { it[section, key] }, { listOf(Change(section, key, it)) })

    private fun takes(values: Map<String, String>) = X86Hardware.takes(values[MACHINE_ID] ?: FIRST_MACHINE)

    /** Why a choice whose firmware the player's set lacks cannot be picked (New game takes it, KairoX86#438). */
    val firmwareMissing = UiText.res(R.string.setting_firmware_missing)

    /** [machineChoices] and the machines they were made from. */
    private var machineChoices: Pair<List<X86Hardware.Machine>, List<ChoiceOption>>? = null

    /**
     * Every machine as a choice, made again only when [X86Hardware.machines] is a new list: a settings
     * page asks for the choices for each label it shows (KairoX86#203).
     */
    @Synchronized private fun machineChoices(): List<ChoiceOption> {
        val machines = X86Hardware.machines()
        machineChoices?.takeIf { it.first === machines }?.let { return it.second }
        return machines.map { machine ->
            ChoiceOption(machine.id, UiText.fixed(machine.name), null, firmwareMissing.takeIf { !machine.available }, machine.type)
        }.also { machineChoices = machines to it }
    }

    /** The PC: every machine 86Box has, by type; one whose firmware the ROM set lacks shows but cannot be picked. */
    val machine = single(MachineOption(MACHINE_ID, UiText.res(FrontendR.string.kairo_option_machine), { machineChoices() },
        FIRST_MACHINE), MACHINE, "machine")

    /** The processor: the families and speeds the machine takes, as cpu_family, cpu_speed and cpu_multi. */
    val processor = Setting(MachineOption("processor", UiText.res(R.string.setting_processor), { emptyList() }, "",
        dependsOn = listOf(MACHINE_ID),
        choicesWith = { values ->
            takes(values).cpus.flatMap { family ->
                family.speeds.map { speed ->
                    ChoiceOption("${family.id}/${speed.speed}/${speed.multi}", UiText.fixed("${family.name} ${speed.name}"),
                        folder = family.name)
                }
            }
        },
        // No processor in 86box.cfg: 86Box takes the machine's first family's first speed.
        defaultWith = { values -> takes(values).cpus.first().let { "${it.id}/${it.speeds.first().speed}/${it.speeds.first().multi}" } }),
        read = { ini ->
            ini[MACHINE, "cpu_family"]?.let { family ->
                val speed = ini[MACHINE, "cpu_speed"] ?: error("86box.cfg names a processor family but no cpu_speed")
                val multi = ini[MACHINE, "cpu_multi"] ?: error("86box.cfg names a processor family but no cpu_multi")
                "$family/${speed.toLong()}/${X86Hardware.multi(multi.toDouble())}"
            }
        },
        changes = { value ->
            val parts = value?.split('/')
            listOf(Change(MACHINE, "cpu_family", parts?.get(0)), Change(MACHINE, "cpu_speed", parts?.get(1)),
                Change(MACHINE, "cpu_multi", parts?.get(2)))
        })

    /** The memory the machine takes, from its least to its most by its step, in KB as 86Box keeps it. */
    val memory = single(MachineOption("memory", UiText.res(FrontendR.string.kairo_option_memory), { emptyList() }, "",
        dependsOn = listOf(MACHINE_ID),
        choicesWith = { values ->
            val takes = takes(values)
            val step = if (takes.ramStep > 0) takes.ramStep else takes.ramMax - takes.ramMin
            generateSequence(takes.ramMin) { size -> (size + step).takeIf { step > 0 && it <= takes.ramMax } }
                .map { size -> ChoiceOption(size.toString(), memoryLabel(size)) }.toList()
        },
        // No mem_size in 86box.cfg: KairoX86's default for the machine (core/kairo/hardware.c, KairoX86#62).
        defaultWith = { values -> takes(values).ramDefault.toString() },
        labelOf = { memoryLabel(it.toInt()) },
        // Any amount the machine takes (KairoX86#337): typed in MB where its sizes are whole MB, else in KB.
        customWith = { values ->
            val takes = takes(values)
            val step = if (takes.ramStep > 0) takes.ramStep else maxOf(takes.ramMax - takes.ramMin, 1)
            if (takes.ramMin % 1024 == 0 && takes.ramMax % 1024 == 0 && step % 1024 == 0)
                CustomValue.range(takes.ramMin / 1024, takes.ramMax / 1024, step / 1024, scale = 1024, labelOf = ::memoryLabel)
            else CustomValue.range(takes.ramMin, takes.ramMax, step, labelOf = ::memoryLabel)
        }), MACHINE, "mem_size")

    /** A card of [kind] the machine takes: 86Box's default without the key is its onboard one, else none. */
    private fun card(id: String, label: Int, kind: String, section: String, key: String, onboardFirst: Boolean) =
        single(MachineOption(id, UiText.res(label), { emptyList() }, "",
            dependsOn = listOf(MACHINE_ID),
            choicesWith = { values ->
                takes(values).cards.getValue(kind).map { card ->
                    ChoiceOption(card.id, cardLabel(card), null, firmwareMissing.takeIf { !card.available })
                }
            },
            defaultWith = { values ->
                val cards = takes(values).cards.getValue(kind)
                if (onboardFirst && cards.any { it.id == "internal" }) "internal" else "none"
            }), section, key)

    /** A card's name: 86Box's own, but the app's words for no card and the board's own (86Box's "None", "Internal"). */
    private fun cardLabel(card: X86Hardware.Card): UiText = when (card.id) {
        "none" -> UiText.res(FrontendR.string.kairo_none)
        "internal" -> UiText.res(R.string.setting_card_onboard)
        // KairoX86#305: the guest's MIDI to the device's MIDI port the player picks (Configurations)
        "kairo_midi_port" -> UiText.res(R.string.setting_midi_port)
        else -> UiText.fixed(card.name)
    }

    val video = card("video", R.string.setting_video, X86Hardware.VIDEO, "Video", "gfxcard", onboardFirst = true)
    val sound = card("sound", R.string.setting_sound, X86Hardware.SOUND, "Sound", "sndcard", onboardFirst = false)
    val network = card("network", R.string.setting_network, X86Hardware.NETWORK, "Network", "net_01_card", onboardFirst = false)
    val hdc = card("hdc", R.string.setting_hdc, X86Hardware.HDC, "Storage controllers", "hdc", onboardFirst = true)
    val scsi = card("scsi", R.string.setting_scsi, X86Hardware.SCSI, "Storage controllers", "scsicard_1", onboardFirst = false)
    val fdc = card("fdc", R.string.setting_fdc, X86Hardware.FDC, "Storage controllers", "fdc", onboardFirst = true)
    val mouse = card("mouse", FrontendR.string.kairo_mouse, X86Hardware.MOUSE, "Input devices", "mouse_type", onboardFirst = false)
    val joystick = card("joystick", FrontendR.string.kairo_joystick, X86Hardware.JOYSTICK, "Input devices", "joystick_type", onboardFirst = false)
    /** What the MPU-401 and the cards' MIDI ports play through (KairoX86#306): none, Munt's MT-32 and CM-32L, or FluidSynth. */
    val midi = card("midi", R.string.setting_midi_out, X86Hardware.MIDI, "Sound", "midi_device", onboardFirst = false)

    /** The section of 86box.cfg FluidSynth's options are kept in (its device's name). */
    const val FLUIDSYNTH = "FluidSynth"

    /**
     * FluidSynth's SoundFont (KairoX86#306): the one the app ships (no sound_font: the core takes it
     * from the ROM set), or one of the player's (X86SoundFonts), kept as its file's path, as 86Box
     * reads it. A path that is none of these (a machine set up elsewhere) reads as its file's name.
     */
    fun soundFont(actions: (select: (String) -> Unit) -> List<com.mrjackspade.kairo.frontend.SettingsRow> = { emptyList() }) = Setting(
        MachineOption(SOUND_FONT, UiText.res(R.string.setting_sound_font), {
            listOf(ChoiceOption(X86SoundFonts.DEFAULT, UiText.fixed(SHIPPED_SOUND_FONT))) +
                X86SoundFonts.files.items().map { ChoiceOption(it.id, UiText.fixed(it.label)) }
        }, X86SoundFonts.DEFAULT, actions = actions,
            labelOf = { UiText.fixed(if (it == X86SoundFonts.DEFAULT) SHIPPED_SOUND_FONT else java.io.File(it).name) }),
        read = { ini ->
            ini[FLUIDSYNTH, "sound_font"]?.takeIf { it.isNotEmpty() }?.let { path ->
                X86SoundFonts.files.items().firstOrNull { it.file.absolutePath == path }?.id ?: path
            }
        },
        changes = { value ->
            val path = value?.takeIf { it != X86SoundFonts.DEFAULT }?.let { id ->
                (X86SoundFonts.files.file(id) ?: error("No SoundFont $id among the imported ones")).absolutePath
            }
            listOf(Change(FLUIDSYNTH, "sound_font", path))
        })

    private const val SOUND_FONT = "sound_font"
    /** The SoundFont the app ships, by its own name. */
    private const val SHIPPED_SOUND_FONT = "GeneralUser GS"
    private val soundFontSetting = soundFont()

    /** The clock the guest reads: the host's local time (86Box's default), UTC, or its own from its CMOS. */
    val clock = single(MachineOption("clock", UiText.res(R.string.setting_clock), listOf(
        ChoiceOption("local", UiText.res(R.string.setting_clock_local)),
        ChoiceOption("utc", UiText.res(R.string.setting_clock_utc)),
        ChoiceOption("disabled", UiText.res(R.string.setting_clock_own))), "local"), MACHINE, "time_sync")

    /**
     * Skip memory check (KairoX86#60), the option every app with a counting BIOS has: the power-on self
     * test runs flat out (core/kairo/frontend.c). KairoX86's own key, which 86Box keeps as it is.
     */
    val skipMemoryCheck = single(MachineOption.skipMemoryCheck(), "Kairo", "skip_memory_check")

    /**
     * Hardware acceleration (KairoX86#282): [KairoX86] hardware_acceleration, 1 or 0, which the core reads
     * at the machine's start. Off until the owner sets its default (#282).
     */
    val hardwareAcceleration = Setting(MachineOption.hardwareAcceleration("off"),
        read = { ini -> ini[KAIROX86, "hardware_acceleration"]?.let { if (it.trim().toInt() != 0) "on" else "off" } },
        changes = { value ->
            listOf(Change(KAIROX86, "hardware_acceleration", value?.let { if (it == "on") "1" else "0" }))
        })

    /** The card settings whose card has options of its own (KairoX86#201), with their kinds. */
    val cards = listOf(video to X86Hardware.VIDEO, sound to X86Hardware.SOUND, network to X86Hardware.NETWORK,
        hdc to X86Hardware.HDC, scsi to X86Hardware.SCSI, fdc to X86Hardware.FDC, mouse to X86Hardware.MOUSE, midi to X86Hardware.MIDI)

    /** A card option's ID: "card:<key>:<section>" (a key has no colon; a section may have any). */
    private const val CARD_OPTION = "card:"

    /** [option], kept in [section] of 86box.cfg, as a setting (KairoX86#201), with 86Box's own choices and default. */
    fun cardOption(section: String, option: X86Hardware.CardOption) =
        MachineOption("$CARD_OPTION${option.key}:$section", deviceText(option.label), option.choices.map { choice ->
            val label = if (!option.binary) deviceText(choice.label)
                else UiText.res(if (choice.value == "1") FrontendR.string.kairo_on else FrontendR.string.kairo_off)
            ChoiceOption(choice.value, label, null, firmwareMissing.takeIf { !choice.available })
        }, option.default)

    /**
     * A card option's text as the player reads it (KairoX86#207): a word of 86Box's in the player's
     * language (X86DeviceStrings), a name or a value as 86Box writes it.
     */
    private fun deviceText(english: String): UiText = X86DeviceStrings.resources[english]?.let { UiText.res(it) } ?: UiText.fixed(english)

    /** In the order they show; each after the ones it depends on. */
    val all = listOf(machine, processor, memory, video, sound, midi, network, hdc, scsi, fdc, mouse, joystick, clock, skipMemoryCheck,
        hardwareAcceleration)

    /** The setting [option] is. */
    fun of(option: MachineOption): Setting {
        if (option.id.startsWith(CARD_OPTION)) {
            // A card's option: kept in its card's section, as 86Box reads it.
            val rest = option.id.removePrefix(CARD_OPTION)
            val key = rest.substringBefore(':')
            return single(option, rest.substringAfter(':'), key)
        }
        // The SoundFont: shown in FluidSynth's group with its import row (MainActivity), read and kept the same everywhere.
        if (option.id == SOUND_FONT) return soundFontSetting
        return all.firstOrNull { it.option.id == option.id } ?: error("${option.id} is no KairoX86 machine setting")
    }

    private fun memoryLabel(kb: Int): UiText =
        if (kb % 1024 == 0) UiText.res(FrontendR.string.kairo_memory_mb, kb / 1024) else UiText.res(FrontendR.string.kairo_memory_kb, kb)
}
