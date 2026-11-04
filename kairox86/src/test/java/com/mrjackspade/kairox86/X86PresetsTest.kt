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
            // The only medium a new machine names is its own blank hard disk, written with it (KairoX86#162):
            // its other disks are the player's.
            assertNull(preset.id, X86Library.missingMedium(config) { preset.hardDisk != null && it == X86Presets.HARD_DISK })
        }
    }

    @Test
    fun aHardDiskIsNamedWithItsOwnGeometry() {
        for (preset in X86Presets.all) {
            val config = IniText(File(folder(preset), "86box.cfg").readText())
            val disk = preset.hardDisk
            if (disk == null) {
                assertNull(preset.id, config["Hard disks", "hdd_01_fn"])
                continue
            }
            assertEquals(preset.id, X86Presets.HARD_DISK, config["Hard disks", "hdd_01_fn"])
            // 86Box's order: sectors, heads, cylinders, then its write precompensation and bus.
            assertEquals(preset.id, "${disk.sectors}, ${disk.heads}, ${disk.cylinders}, 0, ide", config["Hard disks", "hdd_01_parameters"])
            assertEquals(preset.id, "0:0", config["Hard disks", "hdd_01_ide_channel"])
        }
    }

    @Test
    fun theXtRunsOnTheFreeBios() {
        val config = IniText(File(folder(X86Presets.XT), "86box.cfg").readText())
        assertEquals("glabios_040_8088", config["IBM PC (1982)", "bios"])
    }
}
