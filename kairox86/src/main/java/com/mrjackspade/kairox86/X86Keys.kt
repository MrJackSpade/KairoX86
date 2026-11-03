package com.mrjackspade.kairox86

import com.mrjackspade.kairo.frontend.R as FrontendR
import com.mrjackspade.kairo.frontend.ControllerBindingsCodec
import com.mrjackspade.kairo.frontend.GuestKeyboardLayout
import com.mrjackspade.kairo.frontend.PcKey
import com.mrjackspade.kairo.frontend.PcKeyboard
import com.mrjackspade.kairo.frontend.UiText

/**
 * The PC's keyboard and game port as the core takes them: each key by its scan code (set 1, with
 * 0x100 for the keys sent after an E0 prefix, core/kairo/kairo_x86.h), and the game port's two
 * joysticks (x86_core.cpp).
 */
object X86Keys {
    /** The largest scan code a key has. */
    const val MAX_CODE = 0x1FF

    val layout: GuestKeyboardLayout = PcKeyboard.layout("KAIROX86") { it.scanCode }

    fun fromAndroid(androidKey: Int): Int? = PcKey.fromAndroid(androidKey)?.scanCode

    fun label(code: Int): String? = PcKey.fromScanCode(code)?.label

    val bindableCodes: List<Int> = PcKey.entries.map { it.scanCode }.sorted()

    val modifiers = setOf(PcKey.LEFT_SHIFT, PcKey.RIGHT_SHIFT, PcKey.LEFT_CTRL, PcKey.RIGHT_CTRL, PcKey.LEFT_ALT,
        PcKey.RIGHT_ALT).map { it.scanCode }.toSet()

    /** Caps Lock, Num Lock and Scroll Lock, the lock keys' bits in the core's order (X86Core::locks). */
    val locks = listOf(PcKey.CAPS_LOCK, PcKey.NUM_LOCK, PcKey.SCROLL_LOCK).map { it.scanCode }

    /**
     * The game port's controls in the core's order (x86_core.cpp): the first joystick's directions
     * and its four buttons, then the second joystick's directions.
     */
    val joystick = listOf("up", "down", "left", "right", "button1", "button2", "button3", "button4",
        "up2", "down2", "left2", "right2")
    val joystickLabels: List<UiText> = listOf(FrontendR.string.kairo_up, FrontendR.string.kairo_down,
        FrontendR.string.kairo_left, FrontendR.string.kairo_right).map { UiText.res(it) } +
        (1..4).map { UiText.res(R.string.joystick_button, it) } +
        listOf(FrontendR.string.kairo_up, FrontendR.string.kairo_down, FrontendR.string.kairo_left,
            FrontendR.string.kairo_right).map { UiText.res(R.string.joystick_2, UiText.res(it)) }

    val bindings = ControllerBindingsCodec({ it in bindableCodes }, joystick,
        setOf("menu", "pause", "restart", "exit", "fastForward"))
}
