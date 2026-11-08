package com.mrjackspade.kairox86

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * The machine an installed Windows 95/98 knows, from its registry (KairoX86#224): the board and the
 * cards Windows has drivers for at the places it met them, so the image boots as it is, with no new
 * hardware to install. Only the machines KairoX86 makes for an eXoWin9x DOSBox-X game are chosen
 * this way: such an image was set up on a PC emulator before eXo moved it to DOSBox-X, and its
 * registry still holds that machine (the devices Windows met are kept under Enum).
 *
 * - The board: the one of [BOARDS] whose chipset Windows met at its places (PCI bus 0, by device
 *   number), by the IDs 86Box's (or PCem's) board gives it.
 * - The cards: the PCI ones Windows met in that board's slots, as 86Box places them: the video card
 *   in the first, a Voodoo after it (in the first when the video card is on AGP). A PCI or AGP video
 *   card whose driver is another card's (its class key's MatchingDeviceId names that one) is not the
 *   display Windows uses: the legacy one it detected is, at its ports, with no PCI identity, as
 *   DOSBox-X gave it (KairoX86#229), and that card goes in instead ([LEGACY_DISPLAYS]). When the image's
 *   Glide is built for a Voodoo Windows met only at device 0 (DOSBox-X's place for it), the Voodoo
 *   goes there instead (kairox86-pci-dev0-card).
 * - The sound card: the legacy Sound Blaster Windows was told of, at the ports, IRQ and DMA channels
 *   Windows gives it (its ForcedConfig or BootConfig), or else one it enumerated by ISA Plug and Play.
 * - 86Box's ISA Plug and Play IDE controllers, the tertiary and quaternary, when Windows met them.
 *
 * Anything else in the board's slots, or a choice the registry leaves open, fails: guessing would
 * give Windows hardware it does not know.
 */
object Win9xMachine {
    /** A setting of 86box.cfg; a null value removes the key. */
    data class Setting(val section: String, val key: String, val value: String?)

    /** The machine: the board's 86Box name ([Board.machine]) and the settings that make it. */
    data class Machine(val board: Board, val settings: List<Setting>)

    /**
     * A board: its 86Box name, its chipset's PCI functions ([Device] IDs at their device numbers), the
     * device numbers of its PCI slots in the order 86Box fills them, whether it has an AGP slot, and
     * the settings it needs besides the cards (none when eXo's own 686BX machine has them).
     */
    class Board(val machine: String, val chipset: List<Pair<String, Int>>, val slots: List<Int>, val agp: Boolean,
                val settings: List<Setting>, val cmosAsset: String? = null)

    /** A card Windows can have met: its PCI ID ("VEN_5333&DEV_8811", or with SUBSYS for one card of a family) and 86Box's name. */
    private class Card(val id: String, val kind: Kind, val device: String)

    private enum class Kind { VIDEO, AGP_VIDEO, VOODOO }

    val GA686BX = Board("686bx", listOf("VEN_8086&DEV_7190&SUBSYS_00000000&REV_02" to 0x00, "VEN_8086&DEV_7110&SUBSYS_00000000&REV_02" to 0x07),
        listOf(0x08, 0x09, 0x0a, 0x0b), agp = true, settings = emptyList())

    /**
     * PCem's Award 430VX PCI: 86Box's 430vx with the original PIIX (kairox86-pcem-430vx), a Pentium
     * MMX 166 (86Box's cpu_speed is the processor's own, 166666666, at 2.5 times the bus), 64 MB, and its own floppy controller (the Super I/O's, which eXo's 686BX machine turns
     * off) with PCem's 1.44 MB drive A: its CMOS, the BIOS's defaults saved by 86Box
     * (assets/exowin9x/nvr), has that drive, and the BIOS stops at "Floppy disk(s) fail" without it
     * (86Box's default drive A is a 360K one).
     */
    val PCEM_430VX = Board("430vx", listOf("VEN_8086&DEV_7030" to 0x00, "VEN_8086&DEV_122E" to 0x07), listOf(0x11, 0x12, 0x13, 0x14), agp = false,
        settings = listOf(Setting("Machine", "cpu_family", "pentium_p55c"), Setting("Machine", "cpu_speed", "166666666"),
            Setting("Machine", "cpu_multi", "2.5"), Setting("Machine", "mem_size", "65536"), Setting(X86Settings.KAIROX86, "pcem_piix", "1"),
            Setting("Storage controllers", "fdc", null), Setting("Floppy and CD-ROM drives", "fdd_01_type", "35_2hd")),
        cmosAsset = "exowin9x/nvr/430vx.nvr")

    private val BOARDS = listOf(GA686BX, PCEM_430VX)

    private val CARDS = listOf(
        Card("VEN_5333&DEV_8811", Kind.VIDEO, "s3_trio64_pci"),
        Card("VEN_5333&DEV_8A01", Kind.VIDEO, "virge_dx_pci"),
        Card("VEN_121A&DEV_0005&SUBSYS_003A121A", Kind.AGP_VIDEO, "voodoo3_3k_agp"),
        Card("VEN_121A&DEV_0001", Kind.VOODOO, "voodoo"),
        Card("VEN_121A&DEV_0002", Kind.VOODOO, "voodoo_2"))

    /**
     * 86Box's legacy video cards by the chip Windows' display driver found (its class key's INFO\ChipType):
     * cards with no PCI identity, which Windows meets only by legacy detection at their ports, as it met
     * DOSBox-X's S3 (KairoX86#229).
     */
    private val LEGACY_DISPLAYS = mapOf("Trio64(86C764)" to "s3_trio64_vlb")

    /** 86Box's Sound Blasters by the ISA Plug and Play ID Windows met them by. */
    private val PNP_SOUND = mapOf("CTL0042" to "sbawe32_pnp")

    /** A PCI function Windows met: its ID as the key names it, where, when on bus 0, and its key. */
    private class Instance(val id: String, val device: Int?, val function: Int?, val key: Win9xRegistry.Key)

    private val LOCATION = Regex("BUS_00&DEV_([0-9A-F]{2})&FUNC_([0-9A-F]{2})", RegexOption.IGNORE_CASE)

    /**
     * Whether the key's ID [key] ("VEN_x&DEV_y&SUBSYS_z&REV_r") is [id]: the same, or [id] followed by
     * the parts it leaves out, or [id]'s own vendor and device when the key has no SUBSYS (Windows 95
     * names functions by those alone).
     */
    private fun matches(key: String, id: String): Boolean =
        key.equals(id, ignoreCase = true) || key.startsWith("$id&", ignoreCase = true) ||
            !key.contains("&SUBSYS", ignoreCase = true) && key.equals(id.substringBefore("&SUBSYS"), ignoreCase = true)

    /**
     * The Voodoo an image's Glide ([glide], its WINDOWS/SYSTEM/GLIDE2X.DLL) is built for: 86Box's
     * "voodoo" for a Voodoo Graphics (SST-1) build, whose code is `sst1Init`; null for any other, or none.
     */
    fun glideVoodoo(glide: ByteArray?): String? =
        if (glide != null && String(glide, Charsets.ISO_8859_1).contains("sst1Init")) "voodoo" else null

    /**
     * The machine [registry]'s Windows knows; [glide] the Voodoo its Glide is built for ([glideVoodoo]),
     * which, when Windows met one where 86Box can put it, is the Voodoo the machine gets.
     */
    fun of(registry: Win9xRegistry, glide: String? = null): Machine {
        val pci = checkNotNull(registry.key("Enum\\PCI")) { "The Windows image's registry has no PCI devices (Enum\\PCI)" }
        val instances = pci.children.filter { it.name.startsWith("VEN_", ignoreCase = true) }.flatMap { id ->
            id.children.map { at ->
                val m = LOCATION.matchEntire(at.name)
                Instance(id.name, m?.groupValues?.get(1)?.toInt(16), m?.groupValues?.get(2)?.toInt(16), at)
            }
        }
        val boards = BOARDS.filter { board ->
            board.chipset.all { (id, device) -> instances.any { it.device == device && it.function == 0 && matches(it.id, id) } }
        }
        check(boards.size == 1) {
            if (boards.isEmpty()) "The Windows image knows no board KairoX86 builds (PCI chipset: " +
                instances.filter { it.device == 0 }.joinToString { it.id } + ")"
            else "The Windows image knows several boards KairoX86 builds: ${boards.joinToString { it.machine }}"
        }
        val board = boards.single()
        val settings = board.settings.toMutableList()

        // The cards in the board's slots, and on its AGP bus (a function not on bus 0)
        fun card(instance: Instance): Card? = CARDS.firstOrNull { matches(instance.id, it.id) }
        val inSlots = instances.filter { it.device != null && it.device in board.slots && it.function == 0 }
        for (instance in inSlots) checkNotNull(card(instance)) {
            "The Windows image knows a PCI card KairoX86 does not build in the board's slot ${"%02X".format(instance.device)}: ${instance.id}"
        }
        val agpInstances = if (board.agp) instances.filter { it.device == null && card(it)?.kind == Kind.AGP_VIDEO } else emptyList()
        val pciVideoInstances = inSlots.filter { it.device == board.slots[0] && card(it)!!.kind == Kind.VIDEO }
        val videos = (agpInstances + pciVideoInstances).map { card(it)!! }.distinctBy { it.device }
        check(videos.size == 1) {
            if (videos.isEmpty()) "The Windows image knows no video card KairoX86 builds on the ${board.machine}"
            else "The Windows image knows several video cards on the ${board.machine}: ${videos.joinToString { it.device }}"
        }
        val video = videos.single()
        // The video card Windows has its own driver for, or else the legacy display it uses (KairoX86#229)
        val ownDriver = (agpInstances + pciVideoInstances).any { driverFits(registry, it.key, it.id) }
        val legacy = if (ownDriver) null else legacyDisplay(registry)
        settings += Setting("Video", "gfxcard", legacy ?: video.device)
        // A Voodoo sits in the slot after the video card's, the first when that is on AGP or not on PCI
        val voodooSlot = board.slots[if (legacy != null || video.kind == Kind.AGP_VIDEO) 0 else 1]
        for (instance in inSlots) {
            val at = card(instance)!!
            check(instance.device == voodooSlot || at.kind != Kind.VOODOO) {
                "The Windows image knows a Voodoo in slot ${"%02X".format(instance.device)} of the ${board.machine}, where 86Box puts it in ${"%02X".format(voodooSlot)}"
            }
            check(at.kind == Kind.VOODOO || legacy == null && instance.device == board.slots[0] && at === video) {
                "The Windows image knows ${at.device} in slot ${"%02X".format(instance.device)} of the ${board.machine}, with ${video.device} as its video card"
            }
        }
        val inSlot = inSlots.filter { it.device == voodooSlot }.map { card(it)!! }.singleOrNull { it.kind == Kind.VOODOO }
        // The Voodoo the image's Glide is built for, where Windows met it: in that slot, or at device
        // 0, where DOSBox-X's PCI bus (no host bridge) has its first card (kairox86-pci-dev0-card,
        // KairoX86#228); otherwise the one Windows met in the slot
        val atDevice0 = glide != null && inSlot?.device != glide && instances.any { instance ->
            instance.device == 0 && instance.function == 0 && card(instance)?.let { it.kind == Kind.VOODOO && it.device == glide } == true
        }
        val voodoo = if (atDevice0) glide else inSlot?.device
        settings += Setting("Video", "voodoo", if (voodoo != null) "1" else null)
        if (voodoo != null) settings += Setting("3Dfx Voodoo Graphics", "type", voodoo)
        settings += Setting(X86Settings.KAIROX86, "voodoo_pci_dev0", if (atDevice0) "1" else null)

        settings += sound(registry)

        // 86Box's tertiary and quaternary IDE controllers are BOX0001, serials 0 and 1
        val ide = registry.key("Enum\\ISAPNP\\BOX0001")?.children?.map { it.name.lowercase() }.orEmpty()
        settings += Setting("Storage controllers", "ide_ter", if ("00000000" in ide) "1" else null)
        settings += Setting("Storage controllers", "ide_qua", if ("00000001" in ide) "1" else null)
        return Machine(board, settings)
    }

    /** The class key of a device's driver ([instance]'s Driver, such as Display\0001). */
    private fun driverKey(registry: Win9xRegistry, instance: Win9xRegistry.Key): Win9xRegistry.Key? =
        instance.string("Driver")?.let { registry.key("System\\CurrentControlSet\\Services\\Class\\$it") }

    /**
     * Whether [instance]'s driver is not known to be another device's: false only when its class key's
     * MatchingDeviceId names a device other than [id] ("PCI\" and the ID, or the start of it). Windows 95
     * keeps no MatchingDeviceId, and an instance whose driver the registry does not name has no other's.
     */
    private fun driverFits(registry: Win9xRegistry, instance: Win9xRegistry.Key, id: String): Boolean {
        val matching = driverKey(registry, instance)?.string("MatchingDeviceId") ?: return true
        return id.startsWith(matching.removePrefix("PCI\\").removePrefix("pci\\"), ignoreCase = true)
    }

    /**
     * The legacy display Windows uses when its PCI or AGP video card has no driver of its own: the
     * display adapter it detected (Enum\Root\*PNP09xx) with a driver for it, as 86Box's card for that
     * driver's chip ([LEGACY_DISPLAYS]). None, or a chip KairoX86 does not build, fails.
     */
    private fun legacyDisplay(registry: Win9xRegistry): String {
        val displays = registry.key("Enum\\Root")?.children.orEmpty().filter { it.name.startsWith("*PNP09", ignoreCase = true) }
            .flatMap { id -> id.children.map { id.name to it } }
            .filter { (id, instance) -> driverKey(registry, instance)?.string("MatchingDeviceId").equals(id, ignoreCase = true) }
        check(displays.size == 1) {
            if (displays.isEmpty()) "The Windows image's video card has no driver of its own, and it knows no legacy display with one"
            else "The Windows image knows several legacy displays: ${displays.joinToString { it.first }}"
        }
        val chip = driverKey(registry, displays.single().second)?.child("INFO")?.string("ChipType")
        return checkNotNull(LEGACY_DISPLAYS[chip]) { "The Windows image's legacy display is a ${chip ?: "chip it does not name"}, which KairoX86 does not build" }
    }

    /**
     * The Sound Blaster Windows knows: its legacy one, or else one it enumerated by Plug and Play. A
     * legacy one's driver looks for its card at its ports whatever else the machine has, and finds a
     * Plug and Play one there too: Win98Chinese.vhd's, given the AWE32 it also knows, finds the AWE's
     * synthesizer and adds an MPU-401 emulation it has no driver for. A plain Sound Blaster 16 at its
     * resources is the card it last found.
     */
    private fun sound(registry: Win9xRegistry): List<Setting> {
        val legacy = registry.key("Enum\\Root")?.children.orEmpty().flatMap { it.children }.filter { instance ->
            instance.string("HardwareID")?.split(',')?.any { it.trim().equals("*PNPB003", ignoreCase = true) } == true
        }
        check(legacy.size <= 1) { "The Windows image knows ${legacy.size} legacy Sound Blasters" }
        if (legacy.isEmpty()) {
            val pnp = registry.key("Enum\\ISAPNP")?.children.orEmpty().mapNotNull { key ->
                PNP_SOUND.entries.firstOrNull { key.name.startsWith(it.key + "_", ignoreCase = true) }?.value
            }.distinct()
            check(pnp.size == 1) {
                if (pnp.isEmpty()) "The Windows image knows no Sound Blaster KairoX86 builds" else "The Windows image knows several Plug and Play sound cards: ${pnp.joinToString()}"
            }
            return listOf(Setting("Sound", "sndcard", pnp.single()))
        }
        // The resources Windows gives it: those it was told (ForcedConfig, a card set up by hand), or else those it found (BootConfig)
        val instance = legacy.single()
        val config = LogConfig.read(checkNotNull(instance.value("ForcedConfig") ?: instance.value("BootConfig")) {
            "The Windows image's Sound Blaster has no ForcedConfig or BootConfig"
        }.data)
        // Its own ports first (22x), the MPU-401's (33x or 30x) and the FM chip's (388) after
        val base = checkNotNull(config.ports.firstOrNull { it in 0x220..0x280 && it % 0x20 == 0 }) { "The Windows image's Sound Blaster has no base port: ${config.ports}" }
        val mpu = config.ports.firstOrNull { it == 0x330 || it == 0x300 }
        check(config.irqs.size == 1) { "The Windows image's Sound Blaster has IRQs ${config.irqs}" }
        val low = config.dmas.filter { it < 4 }
        val high = config.dmas.filter { it >= 4 }
        check(low.size == 1 && high.size <= 1) { "The Windows image's Sound Blaster has DMA channels ${config.dmas}" }
        val section = "Sound Blaster 16 #1"
        return listOfNotNull(Setting("Sound", "sndcard", "sb16"), Setting(section, "base", "%04X".format(base)),
            Setting(section, "irq", config.irqs.single().toString()), Setting(section, "dma", low.single().toString()),
            high.singleOrNull()?.let { Setting(section, "dma16", it.toString()) },
            mpu?.let { Setting(section, "base401", "%04X".format(it)) })
    }

    /**
     * A configuration manager log configuration (a device's BootConfig or ForcedConfig): an 8-byte
     * header, then resource records of their length (with its 8-byte head) and type (1 memory, 2 I/O,
     * 3 DMA, 4 IRQ), a length of 0 ending them. Each record starts with what is allocated: of an I/O
     * record (IO_DES) the base at 4, of an IRQ record (IRQ_DES) the IRQ at 2, of a DMA record
     * (DMA_DES) the channel at 1; a forced one's ranges follow.
     */
    class LogConfig(val ports: List<Int>, val irqs: List<Int>, val dmas: List<Int>) {
        companion object {
            fun read(data: ByteArray): LogConfig {
                val buffer = ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN)
                val ports = ArrayList<Int>()
                val irqs = ArrayList<Int>()
                val dmas = ArrayList<Int>()
                var at = 8
                while (true) {
                    check(at + 4 <= data.size) { "A log configuration runs past its end" }
                    val length = buffer.getInt(at)
                    if (length == 0) break
                    check(length >= 8 && at + length <= data.size) { "A log configuration has a record of length $length" }
                    val body = at + 8
                    when (buffer.getInt(at + 4)) {
                        2 -> ports += buffer.getShort(body + 4).toInt() and 0xffff
                        3 -> dmas += data[body + 1].toInt() and 0xff
                        4 -> irqs += buffer.getShort(body + 2).toInt() and 0xffff
                    }
                    at += length
                }
                return LogConfig(ports, irqs, dmas)
            }
        }
    }
}
