package com.mrjackspade.kairox86

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class ExoWin9xTest {
    @Test
    fun aGameIsAZipOfAYearFolder() {
        val game = ExoWin9x.game("Roms/eXoWin9x/eXo/eXoWin9x/1996/Daytona USA (1996).zip")!!
        assertEquals("Roms/eXoWin9x", game.root)
        assertEquals("1996", game.year)
        assertEquals("Daytona USA (1996)", game.name)
        assertEquals("Roms/eXoWin9x/KairoX86/1996/Daytona USA (1996)", game.folder)
        assertEquals("Roms/eXoWin9x/Content/!Win9Xmetadata.zip", game.metadataArchive)
        assertEquals("eXo/eXoWin9x/!win9x/1996/Daytona USA (1996)", game.metadataFolder)
        assertEquals("", ExoWin9x.game("eXo/eXoWin9x/1995/Fury 3 (1995).zip")!!.root)
        assertNull(ExoWin9x.game("eXo/eXoWin9x/!win9x/1996/x.zip"))
        assertNull(ExoWin9x.game("Games/Daytona USA (1996).zip"))
        assertEquals(game, ExoWin9x.gameOfFolder(game.folder))
        assertEquals(ExoWin9x.game("eXo/eXoWin9x/1995/Fury 3 (1995).zip"), ExoWin9x.gameOfFolder("KairoX86/1995/Fury 3 (1995)"))
        assertNull(ExoWin9x.gameOfFolder("doom486"))
    }

    @Test
    fun theCollectionsOtherArchivesAreNoDisks() {
        assertTrue(ExoWin9x.isCollectionFile("eXoWin9x/eXo/util/utilWin9x.zip"))
        assertTrue(ExoWin9x.isCollectionFile("eXoWin9x/Content/!Win9Xmetadata.zip"))
        assertTrue(ExoWin9x.isCollectionFile("Content/LaunchBox.zip"))
        assertFalse(ExoWin9x.isCollectionFile("eXoWin9x/eXo/eXoWin9x/1996/Quake (1996).zip"))
        assertFalse(ExoWin9x.isCollectionFile("doom/doomhd.zip"))
        assertTrue(ExoWin9x.isMachineFolder("eXoWin9x/KairoX86/1996/Quake (1996)/86box.cfg"))
        assertFalse(ExoWin9x.isMachineFolder("KairoX86/doom486/86box.cfg"))
    }

    private val daytona = """
        [General]
        host_cpu = AMD Ryzen 5 3600 6-Core Processor
        uuid = 0b1e1a64-6910-59bd-b585-a2c2e7fc785f

        [Machine]
        cpu_family = pentiumpro
        machine = 686bx
        mem_size = 1048576

        [Hard disks]
        hdd_01_fn = W98-C.vhd
        hdd_01_ide_channel = 0:0
        hdd_01_parameters = 255, 16, 32896, 0, ide
        hdd_02_fn = ../../eXoWin9x/1996/Daytona USA (1996)/Daytona USA (1996).vhd
        hdd_02_ide_channel = 0:1

        [Floppy and CD-ROM drives]
        cdrom_01_image_path = ../../eXoWin9x/1996/Daytona USA (1996)/DAYTONA USA.cue
        cdrom_01_parameters = 1, atapi
    """.trimIndent()

    private val members = listOf("Daytona USA (1996)/Daytona USA (1996).vhd", "Daytona USA (1996)/DAYTONA USA.CUE",
        "Daytona USA (1996)/DAYTONA USA.BIN")

    @Test
    fun aPlayCfgBecomesTheMachines86boxCfg() {
        val translation = ExoWin9x.translate(daytona, members) { "/data/exowin9x/$it" }
        assertEquals("W98-P.vhd", translation.parent)
        assertEquals("686bx", translation.machine)
        val config = translation.config
        assertFalse(config.contains("[General]"))
        assertFalse(config.contains("host_cpu"))
        assertTrue(config.contains("hdd_01_fn = ${ExoWin9x.CHILD}\nhdd_01_vhd_parent = /data/exowin9x/W98-P.vhd\n"))
        assertTrue(config.contains("hdd_01_parameters = 255, 16, 32896, 0, ide\n"))
        assertTrue(config.contains("hdd_02_fn = Daytona USA (1996).vhd\n"))
        // The member's own case, whatever the configuration wrote
        assertTrue(config.contains("cdrom_01_image_path = DAYTONA USA.CUE\n"))
        assertTrue(config.contains("[Machine]\ncpu_family = pentiumpro\nmachine = 686bx\n"))
    }

    @Test
    fun aMissingFileFails() {
        assertThrows(IllegalStateException::class.java) {
            ExoWin9x.translate(daytona, members.dropLast(2)) { it }
        }
        assertThrows(IllegalStateException::class.java) {
            ExoWin9x.translate(daytona.replace("W98-C.vhd", "../../x/W98.vhd"), members) { it }
        }
    }
}
