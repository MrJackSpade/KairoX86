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

    private val hellbender = """
        [dosbox]
        machine                   = svga_s3
        [autoexec]
        # Lines in this section will be run at startup.
        echo off
        vhdmake -f -l .\emulators\dosbox\x98\parent/W98-C.vhd .\emulators\dosbox\x98\W98-C.vhd
        IMGMOUNT c .\emulators\dosbox\x98\W98-C.vhd
        IMGMOUNT d ".\eXoWin9x\1996\Hellbender (1996)\Hellbender (1996).vhd"
        IMGMOUNT e ".\eXoWin9x\1996\Hellbender (1996)\hellbender.cue" ".\eXoWin9x\1996\Hellbender (1996)\disc2.cue" -t cdrom -ide 2m
        BOOT -l c
    """.trimIndent()

    private val template = """
        [General]
        emu_build_num = 7012

        [Machine]
        machine = 686bx
        mem_size = 1048576

        [Hard disks]
        hdd_01_fn = parent/W98-P.vhd
        hdd_01_parameters = 255, 16, 32896, 0, ide

        [Floppy and CD-ROM drives]
        cdrom_01_ide_channel = 1:0
        cdrom_01_image_path = ../../eXoWin9x/1996/x/y.cue
        cdrom_01_parameters = 1, atapi
    """.trimIndent()

    /** eXo's 86Box Windows 98 (W98-P.vhd) as its registry knows its machine. */
    private val english = ExoWin9x.Windows("W98-P.vhd", 32896, 16, 255, Win9xMachine.Machine(Win9xMachine.GA686BX, listOf(
        Win9xMachine.Setting("Video", "gfxcard", "voodoo3_3k_agp"), Win9xMachine.Setting("Video", "voodoo", null),
        Win9xMachine.Setting("Sound", "sndcard", "sbawe32_pnp"),
        Win9xMachine.Setting("Storage controllers", "ide_ter", "1"), Win9xMachine.Setting("Storage controllers", "ide_qua", null))))

    @Test
    fun aDosboxGameRunsOnTheMachineItsWindowsKnows() {
        assertEquals("W98-P.vhd", ExoWin9x.dosboxParent("W98-C.vhd"))
        assertEquals("W98-P.vhd", ExoWin9x.dosboxParent(null))
        assertEquals("win98Jap.vhd", ExoWin9x.dosboxParent("win98Jap.vhd"))
        assertEquals("dosbox/x98/parent/win98Jap.vhd", ExoWin9x.parentSource("win98Jap.vhd"))
        assertEquals("86Box98/parent/W98-P.vhd", ExoWin9x.parentSource("W98-P.vhd"))
        val japanese = ExoWin9x.Windows("win98Jap.vhd", 16645, 16, 63, Win9xMachine.Machine(Win9xMachine.GA686BX, listOf(
            Win9xMachine.Setting("Video", "gfxcard", "s3_trio64_pci"), Win9xMachine.Setting("Video", "voodoo", "1"),
            Win9xMachine.Setting("3Dfx Voodoo Graphics", "type", "voodoo"), Win9xMachine.Setting("Sound", "sndcard", "sb16"),
            Win9xMachine.Setting("Sound Blaster 16 #1", "irq", "5"))))
        val withVoodoo = template + "\n[Video]\ngfxcard = voodoo3_3k_agp\n\n[Storage controllers]\nide_qua = 1\nide_ter = 1\n"
        val members = listOf("G/G.vhd")
        val mounts = ExoWin9x.dosboxMounts("[autoexec]\nIMGMOUNT d \"G.vhd\"\n")
        val translation = ExoWin9x.translateDosbox(withVoodoo, japanese, mounts, members, { "/data/exowin9x/$it" }) { 1008L * 10 }
        assertEquals("win98Jap.vhd", translation.parent)
        val config = IniText(translation.config)
        assertEquals("/data/exowin9x/win98Jap.vhd", config["Hard disks", "hdd_01_vhd_parent"])
        assertEquals("63, 16, 16645, 0, ide", config["Hard disks", "hdd_01_parameters"])
        assertEquals("s3_trio64_pci", config["Video", "gfxcard"])
        assertEquals("1", config["Video", "voodoo"])
        assertEquals("voodoo", config["3Dfx Voodoo Graphics", "type"])
        assertEquals("sb16", config["Sound", "sndcard"])
        assertEquals("5", config["Sound Blaster 16 #1", "irq"])
        // The board's own settings over eXo's
        val board = ExoWin9x.Windows("Win95DX8.vhd", 511, 16, 63, Win9xMachine.Machine(Win9xMachine.PCEM_430VX, Win9xMachine.PCEM_430VX.settings))
        val pcem = IniText(ExoWin9x.translateDosbox(withVoodoo, board, mounts, members, { it }) { 1008L * 10 }.config)
        assertEquals("430vx", pcem["Machine", "machine"])
        assertEquals("65536", pcem["Machine", "mem_size"])
        assertEquals("1", pcem["KairoX86", "pcem_piix"])
        // A machine without the quaternary controller has no IDE position 4
        val english = IniText(ExoWin9x.translateDosbox(withVoodoo, english, mounts, members, { it }) { 1008L * 10 }.config)
        assertEquals(null, english["Storage controllers", "ide_qua"])
        assertEquals("1", english["Storage controllers", "ide_ter"])
        val failure = assertThrows(IllegalStateException::class.java) {
            ExoWin9x.translateDosbox(withVoodoo, this.english, ExoWin9x.dosboxMounts("[autoexec]\nIMGMOUNT d \"G.vhd\" -ide 4m\n"), members, { it }) { 1008L * 10 }
        }
        assertTrue(failure.message, failure.message!!.contains("4:0") || failure.message!!.contains("3:0"))
    }

    @Test
    fun aDosboxGameRunsOnTheCollections86BoxMachine() {
        assertEquals("W98-C.vhd", ExoWin9x.dosboxWindows(hellbender))
        val mounts = ExoWin9x.dosboxMounts(hellbender)
        assertEquals(listOf('d', 'e'), mounts.map { it.drive })
        assertEquals(2, mounts[1].images.size)
        assertTrue(mounts[1].cdrom)
        val members = listOf("Hellbender (1996)/Hellbender (1996).vhd", "Hellbender (1996)/HELLBENDER.CUE",
            "Hellbender (1996)/disc2.cue", "Hellbender (1996)/hellbender.bin")
        val translation = ExoWin9x.translateDosbox(template, english, mounts, members, { "/data/exowin9x/$it" }) { 4195296L }
        assertEquals("W98-P.vhd", translation.parent)
        assertEquals("686bx", translation.machine)
        val config = translation.config
        assertFalse(config.contains("emu_build_num"))
        assertFalse(config.contains("parent/W98-P.vhd"))
        assertFalse(config.contains("y.cue"))
        assertTrue(config.contains("[Machine]\nmachine = 686bx\n"))
        assertTrue(config.contains("hdd_01_fn = ${ExoWin9x.CHILD}\nhdd_01_vhd_parent = /data/exowin9x/W98-P.vhd\nhdd_01_ide_channel = 0:0\nhdd_01_parameters = 255, 16, 32896, 0, ide\n"))
        assertTrue(config.contains("hdd_02_fn = Hellbender (1996).vhd\nhdd_02_ide_channel = 0:1\nhdd_02_parameters = 63, 16, 4162, 0, ide\n"))
        assertTrue(config.contains("cdrom_01_ide_channel = 1:0\ncdrom_01_image_path = HELLBENDER.CUE\n"))
        // One section of each name: 86Box reads one
        for (section in listOf("[Hard disks]", "[Floppy and CD-ROM drives]", "[Machine]"))
            assertEquals(section, 1, Regex(Regex.escape(section)).findAll(config).count())
    }

    @Test
    fun drivesTakeTheIdePositionsDosboxXGivesThem() {
        val members = listOf("G/G.vhd", "G/G.cue", "G/G v1.zip", "G/G (zip).vhd")
        // A CD naming -ide 2m sits at 1:0 even with no hard disk before it; a hard disk takes the first free
        val cdFirst = ExoWin9x.dosboxMounts("[autoexec]\nIMGMOUNT e \"G.cue\" -t cdrom -ide 2m\nIMGMOUNT d \"G.vhd\"\n")
        assertEquals("2m", cdFirst[0].ide)
        val config = ExoWin9x.translateDosbox(template, english, cdFirst, members, { it }) { 1008L * 10 }.config
        assertTrue(config, config.contains("cdrom_01_ide_channel = 1:0\n"))
        assertTrue(config, config.contains("hdd_02_fn = G.vhd\nhdd_02_ide_channel = 0:1\n"))
        // A mounted archive becomes, at BOOT, a disk at the first position free after every mount: here 1:1
        val mounts = ExoWin9x.dosboxMounts("[autoexec]\nIMGMOUNT d \"G.vhd\"\nmount f \"G v1.zip\"\nIMGMOUNT e \"G.cue\" -t cdrom -ide 2m\n")
            .map { if (it.folder) ExoWin9x.Mount(it.drive, listOf("G (zip).vhd"), cdrom = false, folder = true, converted = true) else it }
        val withZip = ExoWin9x.translateDosbox(template, english, mounts, members, { it }) { 1008L * 10 }.config
        assertTrue(withZip, withZip.contains("hdd_02_fn = G.vhd\nhdd_02_ide_channel = 0:1\n"))
        assertTrue(withZip, withZip.contains("hdd_03_fn = G (zip).start.vhd\nhdd_03_vhd_parent = G (zip).vhd\nhdd_03_ide_channel = 1:1\nhdd_03_parameters = 63, 16, 10, 0, ide\n"))
        assertTrue(withZip, withZip.contains("cdrom_01_ide_channel = 1:0\n"))
        // eXo's 86box.cfg starts with a byte order mark: its [General] still goes
        assertFalse(ExoWin9x.translateDosbox("﻿" + template, english, mounts, members, { it }) { 1008L * 10 }.config.contains("emu_build_num"))
        // Two drives at one position fail
        assertThrows(IllegalStateException::class.java) {
            ExoWin9x.translateDosbox(template, english, ExoWin9x.dosboxMounts("[autoexec]\nIMGMOUNT d \"G.vhd\" -ide 1s\nIMGMOUNT e \"G.cue\" -t cdrom -ide 1s\n"), members, { it }) { 1008L * 10 }
        }
    }

    @Test
    fun aFolderCdIsMarked() {
        val mounts = ExoWin9x.dosboxMounts("[autoexec]\nIMGMOUNT d \"a.vhd\"\nmount e \".\\eXoWin9x\\1995\\G (1995)\\CD\"\n")
        assertTrue(mounts.single { it.drive == 'e' }.folder)
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

    @Test
    fun aPlayConfsCopiesBeforeBootAreRead() {
        val conf = """
            [autoexec]
            vhdmake -f -l .\emulators\dosbox\x98\parent/W98-C.vhd .\emulators\dosbox\x98\W98-C.vhd
            IMGMOUNT c .\emulators\dosbox\x98\W98-C.vhd
            IMGMOUNT d ".\eXoWin9x\1996\FlagTower - The Unexplained (1996)\FlagTower - The Unexplained (1996).vhd"
            xcopy d:\windows\system\cdaint2f.vxd c:\windows\system\ /Y
            xcopy D:\Windows\*.ini c:\Windows\ /y
            BOOT -l c
        """.trimIndent()
        val copies = ExoWin9x.dosboxCopies(conf)
        assertEquals(listOf(ExoWin9x.Copy('d', "windows/system", "cdaint2f.vxd", 'c', "windows/system"),
            ExoWin9x.Copy('d', "Windows", "*.ini", 'c', "Windows")), copies)
        assertTrue(copies[1].matches("SYSTEM.INI"))
        assertTrue(copies[1].matches("qtw.ini"))
        assertFalse(copies[1].matches("SYSTEM.INF"))
        assertTrue(copies[0].matches("CDAINT2F.VXD"))
        assertFalse(copies[0].matches("CDAINT2F.VXD2"))
        assertEquals(emptyList<ExoWin9x.Copy>(), ExoWin9x.dosboxCopies(conf.lines().filter { !it.startsWith("xcopy") }.joinToString("\n")))
        // Anything but files into a folder fails, not copied some other way
        assertThrows(IllegalStateException::class.java) { ExoWin9x.dosboxCopies("[autoexec]\nxcopy d:\\x\\*.* c:\\x\\ /s /y") }
        assertThrows(IllegalStateException::class.java) { ExoWin9x.dosboxCopies("[autoexec]\nxcopy d:\\x\\a.ini c:\\x\\b.ini /y") }
    }
}
