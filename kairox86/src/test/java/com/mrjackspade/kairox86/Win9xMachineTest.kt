package com.mrjackspade.kairox86

import com.mrjackspade.kairox86.CregWriter.Companion.binary
import com.mrjackspade.kairox86.CregWriter.Companion.string
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.nio.ByteBuffer
import java.nio.ByteOrder

class Win9xMachineTest {
    private fun registry(vararg keys: Pair<String, Map<String, Pair<Int, ByteArray>>>) =
        Win9xRegistry.read(CregWriter().write(CregWriter.tree(keys.toList())))

    private fun pci(id: String, at: String, vararg values: Pair<String, Pair<Int, ByteArray>>) = "Enum\\PCI\\$id\\$at" to mapOf(*values)
    private fun slot(device: Int) = "BUS_00&DEV_%02X&FUNC_00".format(device)

    /** A BootConfig: I/O ports, IRQs and DMA channels as the configuration manager records them. */
    private fun bootConfig(ports: List<Int>, irq: Int, dmas: List<Int>): ByteArray {
        val records = ArrayList<ByteArray>()
        for (port in ports) records += ByteBuffer.allocate(20).order(ByteOrder.LITTLE_ENDIAN).putInt(20).putInt(2)
            .putShort(0).putShort(0x0c).putShort(port.toShort()).putShort((port + 0xf).toShort()).putShort(0).put(0).put(3).array()
        records += ByteBuffer.allocate(16).order(ByteOrder.LITTLE_ENDIAN).putInt(16).putInt(4).putShort(0).putShort(irq.toShort()).putInt(0).array()
        for (dma in dmas) records += ByteBuffer.allocate(12).order(ByteOrder.LITTLE_ENDIAN).putInt(12).putInt(3).put(0).put(dma.toByte()).putShort(0).array()
        return ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN).putInt(0x400).putInt(0).array() + records.reduce { a, b -> a + b } + ByteArray(4)
    }

    private fun hex(text: String) = ByteArray(text.length / 2) { text.substring(it * 2, it * 2 + 2).toInt(16).toByte() }

    /** win98Jap.vhd's Sound Blaster 16 (Enum\Root\MEDIA\0000): 220, 330 and 388, IRQ 5, DMA 1 and 5, with each port's range. */
    private val JAPANESE_FORCED = "000400000000000020000000020000000100020020022f0200000000f0ff100020022002470100002000000002000000" +
        "010002003003310300000000f0ff0200300330034701000020000000020000000100020088038b0300000000f0ff04008803880347010000" +
        "100000000400000000000500000000000c00000003000000000100000c000000030000000005000000000000"

    private fun Win9xMachine.Machine.value(section: String, key: String): String? =
        settings.lastOrNull { it.section == section && it.key == key }?.value

    @Test
    fun aRegistryReadsAsWindowsWroteIt() {
        val registry = registry("Enum\\Root\\*PNPB003\\0000" to mapOf("HardwareID" to string("*PNPB003"), "BootConfig" to binary(byteArrayOf(1, 2))),
            "Enum\\PCI\\VEN_5333&DEV_8811\\${slot(8)}" to mapOf("Class" to string("Display")),
            "Software\\Microsoft" to emptyMap())
        val instance = registry.key("enum\\root\\*pnpb003\\0000")!!
        assertEquals("*PNPB003", instance.string("hardwareid"))
        assertEquals(listOf<Byte>(1, 2), instance.value("BootConfig")!!.data.toList())
        assertEquals("Display", registry.key("Enum\\PCI\\VEN_5333&DEV_8811\\${slot(8)}")!!.string("Class"))
        assertEquals(listOf("Enum", "Software"), registry.root.children.map { it.name })
        assertNull(registry.key("Enum\\ISAPNP"))
    }

    // 86Box's 686BX as Windows 98 meets it, and a VMware machine the same image was on before
    private val ga686bx = arrayOf(
        pci("VEN_8086&DEV_7190&SUBSYS_00000000&REV_02", slot(0)), pci("VEN_8086&DEV_7110&SUBSYS_00000000&REV_02", "BUS_00&DEV_07&FUNC_00"),
        pci("VEN_8086&DEV_7111&SUBSYS_00000000&REV_01", "BUS_00&DEV_07&FUNC_01"))
    private val vmware = arrayOf(
        pci("VEN_8086&DEV_7190&SUBSYS_197615AD&REV_01", slot(0)), pci("VEN_8086&DEV_7110&SUBSYS_197615AD&REV_08", "BUS_00&DEV_07&FUNC_00"),
        pci("VEN_15AD&DEV_0405&SUBSYS_040515AD&REV_00", slot(0x0f)), pci("VEN_1022&DEV_2000&SUBSYS_20001022&REV_10", "088800"))

    @Test
    fun aWindowsOnThe686bxGetsTheCardsItMetThere() {
        // win98Jap.vhd: VMware, then 86Box's 686BX with an S3 Trio64 and a Voodoo, a legacy Sound
        // Blaster 16, and 86Box's two ISA Plug and Play IDE controllers; DOSBox-X's S3 at device 1
        val machine = Win9xMachine.of(registry(*vmware, *ga686bx,
            pci("VEN_5333&DEV_8811&SUBSYS_00000000&REV_00", slot(8)), pci("VEN_5333&DEV_8811&SUBSYS_00000000&REV_00", slot(1)),
            pci("VEN_121A&DEV_0001&SUBSYS_00000000&REV_02", slot(9)),
            "Enum\\ISAPNP\\BOX0001\\00000000" to emptyMap(), "Enum\\ISAPNP\\BOX0001\\00000001" to emptyMap(),
            // Set up by hand: its ForcedConfig, as win98Jap.vhd holds it, over what it was found at
            "Enum\\Root\\MEDIA\\0000" to mapOf("HardwareID" to string("*PNPB003"), "ForcedConfig" to binary(hex(JAPANESE_FORCED)),
                "BootConfig" to binary(bootConfig(listOf(0x240), 7, listOf(3))))))
        assertEquals("686bx", machine.board.machine)
        assertEquals("s3_trio64_pci", machine.value("Video", "gfxcard"))
        assertEquals("1", machine.value("Video", "voodoo"))
        assertEquals("voodoo", machine.value("3Dfx Voodoo Graphics", "type"))
        assertEquals("sb16", machine.value("Sound", "sndcard"))
        assertEquals("0220", machine.value("Sound Blaster 16 #1", "base"))
        assertEquals("5", machine.value("Sound Blaster 16 #1", "irq"))
        assertEquals("1", machine.value("Sound Blaster 16 #1", "dma"))
        assertEquals("5", machine.value("Sound Blaster 16 #1", "dma16"))
        assertEquals("0330", machine.value("Sound Blaster 16 #1", "base401"))
        assertEquals("1", machine.value("Storage controllers", "ide_ter"))
        assertEquals("1", machine.value("Storage controllers", "ide_qua"))
        assertNull(machine.board.cmosAsset)
    }

    @Test
    fun eXosOwnMachineIsWhatItsWindowsKnows() {
        // W98-P.vhd: the Voodoo3 on AGP, the AWE32 Plug and Play, one IDE controller of 86Box's
        val w98p = arrayOf(*ga686bx, pci("VEN_121A&DEV_0005&SUBSYS_003A121A&REV_01", "000800"),
            pci("VEN_5333&DEV_8811&SUBSYS_00000000&REV_00", slot(0)),
            "Enum\\ISAPNP\\CTL0042_DEV0000\\0000C0E0" to emptyMap(), "Enum\\ISAPNP\\CTL0042_DEV0003\\0000C0E0" to emptyMap(),
            "Enum\\ISAPNP\\BOX0001\\00000000" to emptyMap())
        val machine = Win9xMachine.of(registry(*w98p))
        assertEquals("686bx", machine.board.machine)
        assertEquals("voodoo3_3k_agp", machine.value("Video", "gfxcard"))
        assertNull(machine.value("Video", "voodoo"))
        assertEquals("sbawe32_pnp", machine.value("Sound", "sndcard"))
        assertEquals("1", machine.value("Storage controllers", "ide_ter"))
        assertNull(machine.value("Storage controllers", "ide_qua"))
        // Win98Chinese.vhd: the same, and the legacy Sound Blaster DOSBox-X gave it, which would find the AWE32 too
        val chinese = Win9xMachine.of(registry(*w98p, "Enum\\Root\\*PNPB003\\0000" to mapOf("HardwareID" to string("*PNPB003"),
            "BootConfig" to binary(bootConfig(listOf(0x220, 0x388), 7, listOf(1, 5))))))
        assertEquals("sb16", chinese.value("Sound", "sndcard"))
        assertEquals("7", chinese.value("Sound Blaster 16 #1", "irq"))
        assertNull(chinese.value("Sound Blaster 16 #1", "base401"))
    }

    @Test
    fun aWindows95FromPcemsAward430vxGetsThatBoard() {
        // Win95DX8.vhd: Windows 95 names functions without SUBSYS; ViRGE/DX and Voodoo2 in PCem's slots, a Sound Blaster at IRQ 7
        val win95 = registry(pci("VEN_8086&DEV_7030", slot(0)), pci("VEN_8086&DEV_122E", "BUS_00&DEV_07&FUNC_00"),
            pci("VEN_8086&DEV_1230", "BUS_00&DEV_07&FUNC_01"), pci("VEN_5333&DEV_8A01", slot(0x11)), pci("VEN_121A&DEV_0002", slot(0x12)),
            pci("VEN_5333&DEV_8811", slot(1)), pci("VEN_121A&DEV_0001", slot(0)),
            "Enum\\Root\\*PNPB003\\0000" to mapOf("HardwareID" to string("*PNPB003"),
                "BootConfig" to binary(bootConfig(listOf(0x220, 0x330), 7, listOf(1, 5)))),
            "Enum\\Root\\*PNPB005\\0000" to mapOf("HardwareID" to string("*PNPB005")))
        val machine = Win9xMachine.of(win95)
        // Its Glide is the Voodoo Graphics build (DOSBox-X's card): the Voodoo Graphics goes where Windows
        // met it, device 0, as DOSBox-X's PCI bus had it (KairoX86#228)
        val glide = Win9xMachine.glideVoodoo("_GlideInitEnvironment sst1InitGrxClk".toByteArray())
        assertEquals("voodoo", glide)
        assertNull(Win9xMachine.glideVoodoo(null))
        assertNull(Win9xMachine.glideVoodoo("SSTH3_GAMMA".toByteArray()))
        val withGlide = Win9xMachine.of(win95, glide)
        assertEquals("voodoo", withGlide.value("3Dfx Voodoo Graphics", "type"))
        assertEquals("1", withGlide.value("Video", "voodoo"))
        assertEquals("1", withGlide.value("KairoX86", "voodoo_pci_dev0"))
        assertNull(machine.value("KairoX86", "voodoo_pci_dev0"))
        assertEquals("430vx", machine.board.machine)
        assertEquals("1", machine.value("KairoX86", "pcem_piix"))
        assertEquals("pentium_p55c", machine.value("Machine", "cpu_family"))
        assertEquals("65536", machine.value("Machine", "mem_size"))
        assertEquals("166666666", machine.value("Machine", "cpu_speed"))
        // Its own floppy controller (eXo's 686BX machine turns its off) and PCem's 1.44 MB drive A, which its CMOS has
        assertTrue(machine.settings.any { it.key == "fdc" && it.value == null })
        assertEquals("35_2hd", machine.value("Floppy and CD-ROM drives", "fdd_01_type"))
        assertEquals("virge_dx_pci", machine.value("Video", "gfxcard"))
        assertEquals("voodoo_2", machine.value("3Dfx Voodoo Graphics", "type"))
        assertEquals("7", machine.value("Sound Blaster 16 #1", "irq"))
        assertNull(machine.value("Storage controllers", "ide_ter"))
        assertEquals("exowin9x/nvr/430vx.nvr", machine.board.cmosAsset)
    }

    @Test
    fun whatTheBoardCannotHoldAsWindowsKnowsItFails() {
        val sound = "Enum\\ISAPNP\\CTL0042_DEV0000\\0000C0E0" to emptyMap<String, Pair<Int, ByteArray>>()
        // Only VMware's board
        assertThrows(IllegalStateException::class.java) { Win9xMachine.of(registry(*vmware, sound)) }
        // A card no table knows in a slot
        assertThrows(IllegalStateException::class.java) {
            Win9xMachine.of(registry(*ga686bx, sound, pci("VEN_5333&DEV_8811", slot(8)), pci("VEN_1274&DEV_1371", slot(10))))
        }
        // A Voodoo where 86Box would not put it
        val misplaced = assertThrows(IllegalStateException::class.java) {
            Win9xMachine.of(registry(*ga686bx, sound, pci("VEN_5333&DEV_8811", slot(8)), pci("VEN_121A&DEV_0001", slot(10))))
        }
        assertTrue(misplaced.message, misplaced.message!!.contains("Voodoo"))
        // No sound card
        assertThrows(IllegalStateException::class.java) { Win9xMachine.of(registry(*ga686bx, pci("VEN_5333&DEV_8811", slot(8)))) }
        // Two video cards
        assertThrows(IllegalStateException::class.java) {
            Win9xMachine.of(registry(*ga686bx, sound, pci("VEN_5333&DEV_8811", slot(8)), pci("VEN_121A&DEV_0005&SUBSYS_003A121A&REV_01", "000800")))
        }
    }
}
