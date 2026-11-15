package com.mrjackspade.kairox86

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/** The hardware presets a new machine starts from (KairoX86#184). */
class X86PresetsTest {
    private fun folder(preset: X86Presets.Preset) = File("src/main/assets/presets/${preset.id}")
    private fun config(preset: X86Presets.Preset) = IniText(File(folder(preset), X86Presets.CONFIG).readText())

    @Test
    fun eachPresetShipsOnlyItsConfig() {
        for (preset in X86Presets.all) {
            // Nothing else ships with it: no firmware, no CMOS, no flash copy.
            val shipped = folder(preset).walkTopDown().filter { it.isFile }.map { it.relativeTo(folder(preset)).invariantSeparatorsPath }.toSet()
            assertEquals(preset.id, setOf(X86Presets.CONFIG), shipped)
        }
    }

    @Test
    fun eachConfigIsTheHardwareThePresetChecks() {
        for (preset in X86Presets.all) {
            val config = config(preset)
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
            val config = config(preset)
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
        assertEquals("glabios_040_8088", config(X86Presets.XT)["IBM PC (1982)", "bios"])
    }

    @Test
    fun theOtherPresetsRunOnTheFreeMachineAndVideoBios() {
        // KairoX86#446: SeaBIOS on the free machine, SeaVGABIOS on its GD5446; both ship with the app
        for (preset in listOf(X86Presets.DOS_486, X86Presets.WIN9X)) {
            val config = config(preset)
            assertEquals(preset.id, X86Presets.FREE_MACHINE, config["Machine", "machine"])
            assertEquals(preset.id, X86Presets.FREE_VIDEO, config["Video", "gfxcard"])
            assertEquals(preset.id, "cl_gd5446_free_pci", config["Cirrus Logic GD5446 (PCI) #1", "bios"])
        }
        assertEquals(listOf(X86Presets.XT), X86Presets.all.filter { it.machine != X86Presets.FREE_MACHINE })
    }

    @Test
    fun eachFreeMachinePresetKeepsItsBootOrder() {
        // The 486 boots A then C; the Pentium A, the CD, then C (KairoX86#342)
        assertEquals("a,c", config(X86Presets.DOS_486)["KairoX86", "boot_order"])
        assertEquals("a,cd,c", config(X86Presets.WIN9X)["KairoX86", "boot_order"])
    }

    @Test
    fun theFreeFirmwareShipsWithTheApp() {
        for (path in listOf("machines/kairo_pc/seabios.bin", "video/kairo/seavgabios_cirrus.bin")) {
            assertTrue(path, path in X86Firmware.FREE)
            assertTrue(path, File("../firmware/$path").isFile)
        }
    }
}
