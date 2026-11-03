package com.mrjackspade.kairox86

import com.mrjackspade.kairo.frontend.ChoiceOption
import com.mrjackspade.kairo.frontend.MachineOption
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
    private const val MACHINE_ID = "machine"
    private const val FIRST_MACHINE = "ibmpc"

    /** A setting kept in one key. */
    private fun single(option: MachineOption, section: String, key: String) =
        Setting(option, { it[section, key] }, { listOf(Change(section, key, it)) })

    private fun takes(values: Map<String, String>) = X86Hardware.takes(values[MACHINE_ID] ?: FIRST_MACHINE)

    private val firmwareMissing = UiText.res(R.string.setting_firmware_missing)

    /** The PC: every machine 86Box has, by type; one whose firmware the ROM set lacks shows but cannot be picked. */
    val machine = single(MachineOption(MACHINE_ID, UiText.res(R.string.setting_machine), {
        X86Hardware.machines().map { machine ->
            ChoiceOption(machine.id, UiText.fixed(machine.name), null, firmwareMissing.takeIf { !machine.available }, machine.type)
        }
    }, FIRST_MACHINE), MACHINE, "machine")

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
    val memory = single(MachineOption("memory", UiText.res(R.string.setting_memory), { emptyList() }, "",
        dependsOn = listOf(MACHINE_ID),
        choicesWith = { values ->
            val takes = takes(values)
            val step = if (takes.ramStep > 0) takes.ramStep else takes.ramMax - takes.ramMin
            generateSequence(takes.ramMin) { size -> (size + step).takeIf { step > 0 && it <= takes.ramMax } }
                .map { size -> ChoiceOption(size.toString(), UiText.fixed(memoryLabel(size))) }.toList()
        },
        // No mem_size in 86box.cfg: 86Box takes 64 KB, at most the machine's most, whatever its least.
        defaultWith = { values -> minOf(64, takes(values).ramMax).toString() },
        labelOf = { memoryLabel(it.toInt()) }), MACHINE, "mem_size")

    /** A card of [kind] the machine takes: 86Box's default without the key is its onboard one, else none. */
    private fun card(id: String, label: Int, kind: String, section: String, key: String, onboardFirst: Boolean) =
        single(MachineOption(id, UiText.res(label), { emptyList() }, "",
            dependsOn = listOf(MACHINE_ID),
            choicesWith = { values ->
                takes(values).cards.getValue(kind).map { card ->
                    ChoiceOption(card.id, UiText.fixed(card.name), null, firmwareMissing.takeIf { !card.available })
                }
            },
            defaultWith = { values ->
                val cards = takes(values).cards.getValue(kind)
                if (onboardFirst && cards.any { it.id == "internal" }) "internal" else "none"
            }), section, key)

    val video = card("video", R.string.setting_video, X86Hardware.VIDEO, "Video", "gfxcard", onboardFirst = true)
    val sound = card("sound", R.string.setting_sound, X86Hardware.SOUND, "Sound", "sndcard", onboardFirst = false)
    val network = card("network", R.string.setting_network, X86Hardware.NETWORK, "Network", "net_01_card", onboardFirst = false)
    val hdc = card("hdc", R.string.setting_hdc, X86Hardware.HDC, "Storage controllers", "hdc", onboardFirst = true)
    val scsi = card("scsi", R.string.setting_scsi, X86Hardware.SCSI, "Storage controllers", "scsicard_1", onboardFirst = false)
    val fdc = card("fdc", R.string.setting_fdc, X86Hardware.FDC, "Storage controllers", "fdc", onboardFirst = true)
    val mouse = card("mouse", R.string.setting_mouse, X86Hardware.MOUSE, "Input devices", "mouse_type", onboardFirst = false)
    val joystick = card("joystick", R.string.setting_joystick, X86Hardware.JOYSTICK, "Input devices", "joystick_type", onboardFirst = false)

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

    /** In the order they show; each after the ones it depends on. */
    val all = listOf(machine, processor, memory, video, sound, network, hdc, scsi, fdc, mouse, joystick, clock, skipMemoryCheck)

    /** The setting [option] is. */
    fun of(option: MachineOption): Setting = all.firstOrNull { it.option.id == option.id }
        ?: error("${option.id} is no KairoX86 machine setting")

    private fun memoryLabel(kb: Int): String = if (kb % 1024 == 0) "${kb / 1024} MB" else "$kb KB"
}
