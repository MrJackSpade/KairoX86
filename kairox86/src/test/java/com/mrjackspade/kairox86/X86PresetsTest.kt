package com.mrjackspade.kairox86

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/** The hardware presets a new machine starts from (KairoX86#184). */
class X86PresetsTest {
    private fun folder(preset: X86Presets.Preset) = File("src/main/assets/presets/${preset.id}")

    @Test
    fun everyPresetFileShips() {
        for (preset in X86Presets.all) {
            for (path in preset.files) assertTrue("${preset.id}/$path", File(folder(preset), path).isFile)
            // Nothing else ships with it: no firmware, no flash copy.
            val shipped = folder(preset).walkTopDown().filter { it.isFile }.map { it.relativeTo(folder(preset)).invariantSeparatorsPath }.toSet()
            assertEquals(preset.id, preset.files.toSet(), shipped)
        }
    }

    @Test
    fun eachConfigIsTheHardwareThePresetChecks() {
        for (preset in X86Presets.all) {
            val config = IniText(File(folder(preset), "86box.cfg").readText())
            assertEquals(preset.id, preset.machine, config["Machine", "machine"])
            assertEquals(preset.id, preset.cards[X86Hardware.VIDEO], config["Video", "gfxcard"])
            assertEquals(preset.id, preset.cards[X86Hardware.SOUND], config["Sound", "sndcard"])
            // A new machine names no media: its disks are the player's.
            assertNull(preset.id, X86Library.missingMedium(config) { false })
        }
    }

    @Test
    fun theXtRunsOnTheFreeBios() {
        val config = IniText(File(folder(X86Presets.XT), "86box.cfg").readText())
        assertEquals("glabios_040_8088", config["IBM PC (1982)", "bios"])
    }
}
