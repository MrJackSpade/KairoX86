package com.mrjackspade.kairox86

import android.view.KeyEvent
import com.mrjackspade.kairo.frontend.PcKey
import com.mrjackspade.kairo.frontend.PcKeyboard
import com.mrjackspade.kairo.frontend.PcKeyboardModel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** The PC's keys as the core takes them, and the keyboard that follows the running model (KairoX86#65). */
class X86KeysTest {
    @Test
    fun theUsKeyboardIsTheDefault() {
        assertEquals(PcKeyboard.layout("KAIROX86") { it.scanCode }, X86Keys.layout)
    }

    @Test
    fun eachModelTheCoreNamesHasItsLayout() {
        for (model in PcKeyboardModel.entries) assertEquals(X86Keys.layoutOf(model), X86Keys.layoutFor(model.id))
        assertEquals(X86Keys.layout, X86Keys.layoutFor("internal"))
    }

    @Test
    fun androidKeysTypeTheirScanCodes() {
        assertEquals(0x1E, X86Keys.fromAndroid(KeyEvent.KEYCODE_A))
        assertEquals(0x148, X86Keys.fromAndroid(KeyEvent.KEYCODE_DPAD_UP))
        assertEquals(0x7D, X86Keys.fromAndroid(KeyEvent.KEYCODE_YEN))
        assertEquals("Esc", X86Keys.label(0x01))
    }

    @Test
    fun everyKeyCanBeBoundAndTheLocksIncludeKana() {
        for (model in PcKeyboardModel.entries)
            for (code in X86Keys.layoutOf(model).pages.flatMap { it.rows.flatten() }.map { it.code })
                assertTrue("$model $code", code in X86Keys.bindableCodes && code <= X86Keys.MAX_CODE)
        assertEquals(listOf(0x3A, 0x45, 0x46, PcKey.KANA.scanCode), X86Keys.locks)
    }
}
