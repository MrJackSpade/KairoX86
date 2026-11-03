package com.mrjackspade.kairox86

import com.mrjackspade.kairo.frontend.R as FrontendR
import android.net.Uri
import com.mrjackspade.kairo.frontend.BlankDisk
import com.mrjackspade.kairo.frontend.CatalogGame
import com.mrjackspade.kairo.frontend.ControllerGuestSpec
import com.mrjackspade.kairo.frontend.ExternalGameFile
import com.mrjackspade.kairo.frontend.GamePathMigration
import com.mrjackspade.kairo.frontend.LayeredGameCatalog
import com.mrjackspade.kairo.frontend.LibraryStrings
import com.mrjackspade.kairo.frontend.MachineActivity
import com.mrjackspade.kairo.frontend.MachineFirstRun
import com.mrjackspade.kairo.frontend.MachineLibrary
import com.mrjackspade.kairo.frontend.NativeMachine
import com.mrjackspade.kairo.frontend.ScanDepth
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
    // A VGA screen; mouse motion is counted in host pixels (core/kairo/kairo_x86.h).
    override val machine = Machine(640, 480, 4.0 / 3.0, "state.86s")
    // 86Box keeps no save states the frontend can take yet: the machine's own disks and CMOS keep its saves.
    override val saveStates = false
    override val bridge by lazy { NativeMachine("kairox86", X86Keys.locks) }
    override val keyboard = X86Keys.layout
    override val maxKeyCode = X86Keys.MAX_CODE
    override fun guestKey(androidKey: Int) = X86Keys.fromAndroid(androidKey)
    override val joystickControls get() = X86Keys.joystick
    override val controllerSpec = ControllerGuestSpec("IBM PC", X86Keys.bindableCodes, { X86Keys.label(it) ?: "Key $it" },
        X86Keys.modifiers, X86Keys.joystick.zip(X86Keys.joystickLabels), UiText.res(R.string.joystick_help),
        ControllerGuestSpec.STANDARD_ACTIONS, X86Keys.layout)
    override val bindingsCodec = X86Keys.bindings
    override val artworkDownloadsEnabled: Boolean get() = resources.getBoolean(R.bool.catalog_art_download_enabled)

    // A new machine is made in its own flow (KairoX86#162): a hardware preset and its blank disks.
    override val blankDisks = emptyList<BlankDisk>()

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
        override fun inspectExternal(file: ExternalGameFile, cancelled: AtomicBoolean): List<X86Entry> =
            error(getString(R.string.machine_external))
        override fun deleteSource(entry: X86Entry, entries: List<X86Entry>) = error(getString(R.string.machine_delete))
        override fun hasWorkingImage(entry: X86Entry) = false
        override fun withMember(entry: X86Entry, member: String) = entry.copy(member = member)
        override fun resetWorkingImage(entry: X86Entry) = error("A machine runs in place, with no working copy")
        override fun prepare(entry: X86Entry, cancelled: AtomicBoolean, progress: (String) -> Unit): File =
            error("A machine runs in place (startGame)")
        override fun entryForWorkingImage(path: String, entries: List<X86Entry>): X86Entry? = null
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

    override fun startGame(entry: X86Entry, game: CatalogGame, cancelled: AtomicBoolean, progress: (String) -> Unit) {
        val tree = checkNotNull(tree) { getString(FrontendR.string.kairo_library_choose_in_manage) }
        progress(getString(R.string.machine_preparing, entry.displayName))
        val prepared = machines.prepare(entry, tree, cancelled)
        session = prepared
        firmwareFolder.mkdirs()
        // The core's media (x86_core.cpp): the machine folder 86Box runs.
        check(bridge.start(firmwareFolder.absolutePath, prepared.dir.absolutePath, listOf(prepared.dir.absolutePath),
            emptyMap())) { "Another machine is still running" }
        awaitRunning()
    }

    override fun sessionEnded() {
        super.sessionEnded()
        val ended = session ?: return
        session = null
        Thread {
            try {
                ended.writeBack()
            } catch (failure: Exception) {
                runOnUiThread { toast(failure.message ?: getString(R.string.machine_write_back_failed), long = true) }
            } finally {
                ended.close()
            }
        }.apply { name = "KairoX86-write-back"; start() }
    }

    private companion object {
        /** The wordmark's accent; KairoX86#5 sets it from the icon art. */
        const val BRAND_ACCENT = 0xff4FC3F7.toInt()
    }
}
