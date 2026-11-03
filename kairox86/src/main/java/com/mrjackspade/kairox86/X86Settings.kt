package com.mrjackspade.kairox86

import com.mrjackspade.kairo.frontend.ChoiceOption
import com.mrjackspade.kairo.frontend.MachineOption
import com.mrjackspade.kairo.frontend.UiText

/**
 * A machine's settings, each a [MachineOption] kept in the machine folder's own 86box.cfg (Kairo#142)
 * under [Setting.section] and [Setting.key], with 86Box's own values as the choices. A machine without
 * the key takes 86Box's default, which is the option's default.
 */
object X86Settings {
    class Setting(val option: MachineOption, val section: String, val key: String)

    /** The clock the guest reads: the host's local time (86Box's default), UTC, or its own from its CMOS. */
    val clock = Setting(MachineOption("clock", UiText.res(R.string.setting_clock), listOf(
        ChoiceOption("local", UiText.res(R.string.setting_clock_local)),
        ChoiceOption("utc", UiText.res(R.string.setting_clock_utc)),
        ChoiceOption("disabled", UiText.res(R.string.setting_clock_own))), "local"), "Machine", "time_sync")

    val all = listOf(clock)

    /** The setting [option] is. */
    fun of(option: MachineOption): Setting = all.firstOrNull { it.option.id == option.id }
        ?: error("${option.id} is no KairoX86 machine setting")
}
