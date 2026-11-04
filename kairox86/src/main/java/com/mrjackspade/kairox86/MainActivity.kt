package com.mrjackspade.kairox86

import com.mrjackspade.kairo.frontend.R as FrontendR
import android.net.Uri
import android.os.Bundle
import android.os.SystemClock
import android.util.Log
import com.mrjackspade.kairo.frontend.BlankDisk
import com.mrjackspade.kairo.frontend.CatalogGame
import com.mrjackspade.kairo.frontend.ControllerGuestSpec
import com.mrjackspade.kairo.frontend.ExternalGameFile
import com.mrjackspade.kairo.frontend.RowGroup
import com.mrjackspade.kairo.frontend.GamePathMigration
import com.mrjackspade.kairo.frontend.LayeredGameCatalog
import com.mrjackspade.kairo.frontend.LibraryStrings
import com.mrjackspade.kairo.frontend.MachineActivity
import com.mrjackspade.kairo.frontend.MachineFirstRun
import com.mrjackspade.kairo.frontend.MachineLibrary
import com.mrjackspade.kairo.frontend.MachineOption
import com.mrjackspade.kairo.frontend.GuestKeyboardLayout
import com.mrjackspade.kairo.frontend.GameMachineStore
import com.mrjackspade.kairo.frontend.StartupCommands
import com.mrjackspade.kairox86.X86Library.DiskKind
import com.mrjackspade.kairo.frontend.NativeMachine
import com.mrjackspade.kairo.frontend.ScanDepth
import com.mrjackspade.kairo.frontend.ShippedAssets
import com.mrjackspade.kairo.frontend.UiText
import java.io.File
import java.util.concurrent.atomic.AtomicBoolean

/**
 * KairoX86: IBM PC compatibles on 86Box, in the shared Kairo frontend. A library entry is a machine
 * folder (X86Library): its 86box.cfg, its disks and its CMOS, run in place.
 */
class MainActivity : MachineActivity<X86Entry>() {
    override val identity = Identity("KAIROX86", BRAND_ACCENT, "KairoX86", "IBM PC compatible", "kairox86",
        LibraryStrings("KAIROX86", "KairoX86"),
        UiText.res(R.string.credits, "KairoX86", "86Box", "IBM PC compatible", "GLaBIOS", "MrJackSpade/KairoX86"),
        UiText.res(R.string.library_empty), UiText.res(FrontendR.string.kairo_library_expired),
        MachineFirstRun.Folder(UiText.res(FrontendR.string.kairo_folder_title),
            UiText.res(R.string.folder_description, "IBM PC compatible", "KairoX86"),
            UiText.res(FrontendR.string.kairo_folder_button)),
        UiText.res(FrontendR.string.kairo_saves_group), "MrJackSpade/KairoX86")
    // A VGA screen; mouse motion is counted in the picture's pixels (core/kairo/kairo_x86.h).
    override val machine = Machine(640, 480, 4.0 / 3.0, "state.86s")
    // Direct tap through the DOS mouse driver, else by motion from the corner (x86_core.cpp, KairoX86#44).
    override val directTouchExplanation = UiText.res(R.string.direct_touch_explanation)
    // 86Box keeps no save states the frontend can take yet: the machine's own disks and CMOS keep its saves.
    override val saveStates = false

    /**
     * A machine's settings live in its folder's 86box.cfg (Kairo#142, X86Settings); one changed while
     * the machine runs goes over what 86Box saves as it ends.
     */
    private val configStore = ConfigStore()
    override val machineStore: GameMachineStore<X86Entry> get() = configStore

    private inner class ConfigStore : GameMachineStore<X86Entry> {
        // Each machine's 86box.cfg as last read, until a setting is written or its machine ends.
        private val configs = HashMap<String, IniText>()

        @Synchronized private fun config(entry: X86Entry) = configs.getOrPut(entry.id) { machines.config(entry, libraryTree()) }

        @Synchronized fun forget(entryId: String) {
            configs.remove(entryId)
        }

        override fun read(entry: X86Entry, option: MachineOption): String? = X86Settings.of(option).read(config(entry))

        override fun write(entry: X86Entry, option: MachineOption, value: String?) {
            val changes = X86Settings.of(option).changes(value)
            forget(entry.id)
            machines.change(entry, libraryTree(), changes)
            session?.takeIf { it.entryId == entry.id }?.let { running -> changes.forEach { running.edit(it.section, it.key, it.value) } }
        }
    }

    /**
     * The options of each card [entry]'s machine has (KairoX86#201): a group for each card, named by
     * 86Box, with its own options, kept in its section of the folder's 86box.cfg.
     */
    override fun machineExtraGroups(entry: X86Entry, enabled: () -> Boolean): List<RowGroup> =
        chosenCards(entry).mapNotNull { (kind, card) ->
            val own = X86Hardware.options(kind, card.id)
            own.options.takeIf { it.isNotEmpty() }?.let { options ->
                RowGroup(card.name.uppercase(), options.map { option -> machineChoiceRow(entry, X86Settings.cardOption(own.section, option), enabled) })
            }
        }

    /**
     * The cards [entry]'s machine has, each with its kind: those its 86box.cfg chooses or 86Box's
     * default, other than none or the board's own. A card the machine does not take is left out: the
     * player is asked for another (askUnfit).
     */
    private fun chosenCards(entry: X86Entry): List<Pair<String, X86Hardware.Card>> {
        val machine = configStore.read(entry, X86Settings.machine.option) ?: X86Settings.machine.option.default
        val values = mapOf(X86Settings.machine.option.id to machine)
        val takes = X86Hardware.takes(machine)
        return X86Settings.cards.mapNotNull { (setting, kind) ->
            val chosen = configStore.read(entry, setting.option) ?: setting.option.default(values)
            takes.cards.getValue(kind).firstOrNull { it.id == chosen }
                ?.takeIf { it.id != "none" && it.id != "internal" }?.let { kind to it }
        }
    }

    /** One thread that reads ahead what the library's machine pages show (KairoX86#203). */
    private val readAhead = java.util.concurrent.Executors.newSingleThreadExecutor { task ->
        Thread(task, "KairoX86-read-ahead").apply { isDaemon = true }
    }

    /**
     * Reads each machine's 86box.cfg and asks 86Box for its hardware and the chosen cards' options
     * ahead of its page, into the caches the page reads (ConfigStore, X86Hardware): reading them as
     * the page opened froze the app for a moment (KairoX86#203). A read that fails leaves nothing
     * cached, so the page reads it again and fails there, as it did before the read-ahead.
     */
    override fun libraryLoaded(entries: List<X86Entry>) {
        super.libraryLoaded(entries)
        if (tree == null) return
        readAhead.submit { X86Hardware.machines() }
        for (entry in entries.filter { !it.disk && it.playable }) readAhead.submit {
            for ((kind, card) in chosenCards(entry)) X86Hardware.options(kind, card.id)
        }
    }

    private fun libraryTree() = checkNotNull(tree) { getString(FrontendR.string.kairo_library_choose_in_manage) }
    override val bridge by lazy { NativeMachine("kairox86", X86Keys.locks) }
    override val keyboard = X86Keys.layout
    override val maxKeyCode = X86Keys.MAX_CODE
    override fun guestKey(androidKey: Int) = X86Keys.fromAndroid(androidKey)
    override val joystickControls get() = X86Keys.joystick
    override val controllerSpec = ControllerGuestSpec("IBM PC", X86Keys.bindableCodes, { X86Keys.label(it) ?: error("KairoX86 has no key $it") },
        X86Keys.modifiers, X86Keys.joystick.zip(X86Keys.joystickLabels), UiText.res(R.string.joystick_help),
        ControllerGuestSpec.STANDARD_ACTIONS, X86Keys.layout)
    override val bindingsCodec = X86Keys.bindings
    override val artworkDownloadsEnabled: Boolean get() = resources.getBoolean(R.bool.catalog_art_download_enabled)

    /** A new machine starts from a hardware preset (KairoX86#184); its blank disks are KairoX86#162. */
    override val blankDisks: List<BlankDisk> by lazy { X86Presets.blankDisks(this) }

    // The removable drives (KairoX86#48), in the core's slot order (kairo_x86.h): floppy drives A
    // and B, then the first CD-ROM drive.
    override val mediaSlots = listOf(
        MediaSlot<X86Entry>(UiText.res(R.string.media_floppy_a)) { it.disk && X86Library.diskKind(it.path) == DiskKind.FLOPPY },
        MediaSlot(UiText.res(R.string.media_floppy_b)) { it.disk && X86Library.diskKind(it.path) == DiskKind.FLOPPY },
        MediaSlot(UiText.res(FrontendR.string.kairo_cd_rom)) { it.disk && X86Library.diskKind(it.path) == DiskKind.CD })

    /** A machine's own disks are the images of its folder, and what its drives hold. */
    override fun ownDisks(current: X86Entry, takes: (X86Entry) -> Boolean): List<X86Entry> =
        ((session?.disks() ?: emptyList()) + mountedMedia().filterNotNull()).distinctBy { it.id }.filter(takes)

    private val machines by lazy { X86Library(this) }
    override fun createCatalog() = LayeredGameCatalog(this, X86Catalog)
    override fun createLibrary(catalog: LayeredGameCatalog): MachineLibrary<X86Entry> = Library()

    /** The machine folders as the machine activity reads them; a machine runs in place (X86Library.Session). */
    private inner class Library : MachineLibrary<X86Entry> {
        override val hashCount: Int get() = machines.hashCount
        override fun cached(tree: Uri) = machines.cached(tree)
        override fun scan(tree: Uri, depth: ScanDepth, cancelled: AtomicBoolean, progress: (String) -> Unit) =
            machines.scan(tree, depth, cancelled, progress)
        override fun store(tree: Uri, entries: List<X86Entry>) = machines.store(tree, entries)
        // A disk image picked for a drive on the Disks page (KairoX86#48).
        override fun inspectExternal(file: ExternalGameFile, cancelled: AtomicBoolean): List<X86Entry> =
            listOf(machines.pickedDisk(file.uri, file.name, file.size, file.modified))
        override fun prepareMedia(entry: X86Entry, cancelled: AtomicBoolean, progress: (String) -> Unit): File {
            val running = checkNotNull(session) { getString(R.string.machine_disk_no_machine) }
            // A disk of the machine's folder is its session file; one picked on the device gets a link.
            return if (entry.id.startsWith("disk:")) File(entry.uri) else running.link(entry)
        }
        override fun deleteSource(entry: X86Entry, entries: List<X86Entry>) = error(getString(R.string.machine_delete))
        override fun hasWorkingImage(entry: X86Entry) = false
        override fun withMember(entry: X86Entry, member: String) = entry.copy(member = member)
        override fun resetWorkingImage(entry: X86Entry) = error("A machine runs in place, with no working copy")
        override fun prepare(entry: X86Entry, cancelled: AtomicBoolean, progress: (String) -> Unit): File =
            error("A machine runs in place (startGame)")
        override fun entryForWorkingImage(path: String, entries: List<X86Entry>): X86Entry? = session?.diskAt(path)
        override fun statePaths(entries: List<X86Entry>): Map<String, String> = emptyMap()
        override fun withError(entry: X86Entry, message: String) = entry.copy(error = message)
        override fun hashNamedWorkingCopies(): GamePathMigration.Store<X86Entry> = NoHashNamedCopies()
    }

    /** KairoX86 was never released with working copies named by hash, so none move. */
    private class NoHashNamedCopies : GamePathMigration.Store<X86Entry> {
        override fun refresh(claims: List<GamePathMigration.Claim<X86Entry>>, every: Boolean) {}
        override fun has(hashName: String) = false
        override fun move(claim: GamePathMigration.Claim<X86Entry>, keep: Set<GamePathMigration.Conflict>) =
            error("KairoX86 has no hash-named working copies")
        override fun isEmpty() = true
    }

    /** The running machine's session, written back to its folder when it ends. */
    @Volatile private var session: X86Library.Session? = null

    /** The player's 86Box ROM set itself (its machines/, video/... folders), which 86Box's rom path names. */
    private val firmwareFolder by lazy { File(filesDir, "roms") }

    /** The player's 86Box ROM set, imported by content into [firmwareFolder] (KairoX86#67). */
    override val firmwareSets by lazy { listOf(UiText.res(R.string.firmware_rom_set) to X86Firmware.set(this, firmwareFolder)) }

    override fun startGame(entry: X86Entry, game: CatalogGame, cancelled: AtomicBoolean, progress: (String) -> Unit) =
        start(entry, X86Catalog.startupCommands.value(game, emptyMap()), cancelled, progress)

    /** The library's command line (KairoX86#47): the machine with the drives its 86box.cfg gives, nothing typed. */
    override val commandLine = true

    override fun startAtPrompt(entry: X86Entry, game: CatalogGame, cancelled: AtomicBoolean, progress: (String) -> Unit) =
        start(entry, emptyList(), cancelled, progress)

    /** Starts [entry]'s machine on its own drives, typing [commands] at its DOS prompt (KairoX86#46). */
    private fun start(entry: X86Entry, commands: List<String>, cancelled: AtomicBoolean,
                      progress: (String) -> Unit) {
        // A disk image opened from another app has no machine to go in.
        check(!entry.disk) { getString(R.string.machine_external) }
        val tree = checkNotNull(tree) { getString(FrontendR.string.kairo_library_choose_in_manage) }
        progress(getString(FrontendR.string.kairo_launch_preparing, entry.displayName))
        // Each step's time, for the start's measure (KairoX86#42) and player reports.
        val began = SystemClock.elapsedRealtime()
        installFreeFirmware(progress)
        val firmwareReady = SystemClock.elapsedRealtime()
        val prepared = machines.prepare(entry, tree, cancelled)
        session = prepared
        val folderReady = SystemClock.elapsedRealtime()
        // The core's media (x86_core.cpp): the machine folder 86Box runs, and the commands typed at its prompt.
        val settings = mapOf(StartupCommands.setting(commands))
        check(bridge.start(firmwareFolder.absolutePath, prepared.dir.absolutePath, listOf(prepared.dir.absolutePath),
            settings)) { getString(R.string.machine_still_running) }
        awaitRunning()
        Log.i("KairoMachine", "Started ${entry.displayName}: firmware ${firmwareReady - began} ms, " +
            "machine folder ${folderReady - firmwareReady} ms, emulator ${SystemClock.elapsedRealtime() - folderReady} ms")
        // What the machine's drives hold, from its 86box.cfg, as the Disks page shows it, with only
        // the drives it has (KairoX86#197).
        val drives = checkNotNull(bridge.mediaDrives()) { "The machine stopped before its drives were read" }
        mediaStarted(bridge.mediaPaths().orEmpty().map { path -> path.takeIf { it.isNotEmpty() }?.let(prepared::diskAt) }, drives)
    }

    /**
     * The on-screen keyboard of the machine that runs, as its first frame names it (x86_core.cpp
     * details, KairoX86#65): the legends of its keyboard model, JIS with its kana, Korean, Brazilian,
     * ISO, or the XT's and AT's fewer keys.
     */
    override val keyboardNamed: (String) -> GuestKeyboardLayout = X86Keys::layoutFor

    /**
     * The free firmware the app ships (assets/free-firmware: GLaBIOS, the character ROM), each file
     * installed at its place in the ROM folder beside the player's own, with the shared install, which
     * writes a file again only when the app changed.
     */
    private fun installFreeFirmware(progress: (String) -> Unit) {
        for (file in FREE_FIRMWARE) ShippedAssets.install(this, "free-firmware/$file", File(firmwareFolder, file), progress)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        // The machine settings' hardware choices come from the player's ROM set (Kairo#143).
        X86Hardware.roms = firmwareFolder
        super.onCreate(savedInstanceState)
    }

    override fun onDestroy() {
        readAhead.shutdownNow()
        super.onDestroy()
    }

    override fun sessionEnded() {
        super.sessionEnded()
        val ended = session ?: return
        session = null
        Thread {
            try {
                ended.writeBack()
                // 86Box saved its configuration over the folder's: the settings read it again.
                configStore.forget(ended.entryId)
            } catch (failure: Exception) {
                runOnUiThread { toast(failure.message ?: getString(R.string.machine_write_back_failed), long = true) }
            } finally {
                ended.close()
            }
        }.apply { name = "KairoX86-write-back"; start() }
    }

    private companion object {
        /** The wordmark's accent: the icon's (shared tools/app_icon/presets/kairox86.json). */
        const val BRAND_ACCENT = 0xff1FD6E8.toInt()

        /** The free firmware's files, at their places in the ROM set (kairox86/build.gradle.kts). */
        val FREE_FIRMWARE = listOf("machines/glabios/GLABIOS_0.4.0_8P.ROM", "machines/glabios/GLABIOS_0.4.0_VP.ROM",
            "video/mda/mda.rom")
    }
}
