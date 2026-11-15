package com.mrjackspade.kairox86.uitest

import android.view.KeyEvent
import com.mrjackspade.kairo.frontend.PcKey
import com.mrjackspade.kairo.uitest.AppUnderTest
import com.mrjackspade.kairo.uitest.By
import com.mrjackspade.kairo.uitest.AppUnderTest.BiosSet
import com.mrjackspade.kairo.uitest.AppUnderTest.MediaSwap
import com.mrjackspade.kairo.uitest.KairoUiTest
import com.mrjackspade.kairo.uitest.suites.ControllerTests
import com.mrjackspade.kairo.uitest.suites.FirstRunTests
import com.mrjackspade.kairo.uitest.suites.GameTests
import com.mrjackspade.kairo.uitest.suites.LaunchTests
import com.mrjackspade.kairo.uitest.suites.LibraryTests
import com.mrjackspade.kairo.uitest.suites.LibraryManagementTests
import com.mrjackspade.kairo.uitest.suites.MediaTests
import com.mrjackspade.kairo.uitest.suites.MenuTests
import com.mrjackspade.kairo.uitest.suites.SearchTests
import com.mrjackspade.kairo.uitest.suites.SettingsTests
import com.mrjackspade.kairo.uitest.suites.TouchTests
import com.mrjackspade.kairo.uitest.suites.WordingTests
import org.junit.Test

/**
 * KairoX86 as the shared UI tests see it (KairoX86#86). Its library entries are 86Box machine
 * folders. The test resources (#89) are two of them:
 * - xt: the IBM PC XT preset with FreeDOS 1.3's 720K floppy in drive A. It starts on GLaBIOS, the
 *   free firmware the app ships, so it needs no imported firmware.
 * - dos486: the 486 DOS PC with FreeDOS 1.3's 1.44M floppy. It needs the player's 86Box ROM set
 *   (the "bios" resource).
 * The guest's keys are set 1 scan codes (X86Keys), the same as PcKey's.
 */
object KairoX86App : AppUnderTest() {
    override val name = "KairoX86"
    override val brand = "KAIROX86"
    override val biosTitle = "IBM PC compatible BIOS"
    // The ROM set is one row; the test BIOS folder installs the 486 board's BIOS and its S3 card's (KairoX86#90), beside
    // the three of the set's files the app ships and installs at start (GLaBIOS's two and the MDA/CGA font, KairoX86#446).
    override val biosSets = listOf(BiosSet(0, 5))
    override val bootGame = "xt"
    override val bootGameFile = "games/xt/86box.cfg"
    // A library entry is the machine folder, not its 86box.cfg.
    override val bootGameEntryFile = "xt"
    // A machine is its folder: launched alone before setup, it asks for the games folder (KairoX86#210).
    override val launchBeforeSetupMessage = "A machine starts from its games folder: choose the folder that holds it first."
    override val otherGame = "dos486"
    // The Auto touch mode stand-ins (core/test/input/make_auto.py): a game reading the mouse through its driver, one waiting for BIOS keys.
    override val mouseGame = "mouse"
    override val keyboardGame = "keys"
    override val defaultOption = "clock"
    // Machine settings are each machine folder's own (its 86box.cfg): no all-games defaults.
    override val machineDefaults = false
    override val searchTerm = "xt"
    override val arrowKeys = listOf(PcKey.UP.scanCode, PcKey.DOWN.scanCode, PcKey.LEFT.scanCode, PcKey.RIGHT.scanCode)
    override val returnKey = PcKey.ENTER.scanCode
    override val spaceKey = PcKey.SPACE.scanCode
    // 86Box saves no state of a running machine (KairoX86#187).
    override val hasStates = false
    // dos486 starts with its own freedos.img in drive A; xt's floppy is on its Other page (MainActivity.otherDisks).
    override val mediaSwap = MediaSwap("dos486", "Floppy A", "fd13", filler = "img")
}

// Every shared suite (KairoX86#87); no StateTests: 86Box saves no machine state (#187).
class KairoX86FirstRunTests : FirstRunTests() { override val app = KairoX86App }
class KairoX86LibraryTests : LibraryTests() { override val app = KairoX86App }
class KairoX86SearchTests : SearchTests() { override val app = KairoX86App }
class KairoX86GameTests : GameTests() { override val app = KairoX86App }
class KairoX86WordingTests : WordingTests() { override val app = KairoX86App }
class KairoX86MediaTests : MediaTests() { override val app = KairoX86App }
class KairoX86MenuTests : MenuTests() { override val app = KairoX86App }
class KairoX86ControllerTests : ControllerTests() { override val app = KairoX86App }
class KairoX86TouchTests : TouchTests() { override val app = KairoX86App }
class KairoX86LaunchTests : LaunchTests() { override val app = KairoX86App }
class KairoX86LibraryManagementTests : LibraryManagementTests() { override val app = KairoX86App }
class KairoX86SettingsTests : SettingsTests() { override val app = KairoX86App }

/**
 * KairoX86's own behavior (KairoX86#88): the firmware a machine starts on, its media, its machine
 * settings reaching 86Box (the core reports what 86Box started with: x86_core.cpp details), and its
 * boot running flat out.
 */
class X86Tests : KairoUiTest() {
    override val app = KairoX86App

    private fun startsAndDraws(machine: String, board: String, importBios: Boolean) {
        screens.completeFirstRun(importBios = importBios).open(machine).play()
        driver.waitFrames(300)
        expect.equal("the board 86Box started $machine on", board, driver.probe().details["core.machine"])
        val picture = driver.pictures.game("$machine-start")
        expect.that("$machine draws", picture.drawn()) { "lit ${picture.litFraction()}" }
    }

    /** The XT preset starts on GLaBIOS, the free firmware the app ships, with nothing imported. */
    @Test
    fun theXtStartsOnTheFreeFirmware() = startsAndDraws(KairoX86App.bootGame, "ibmpc82", importBios = false)

    /** The 486 starts on the player's 86Box ROM set, imported from a folder and found by content. */
    @Test
    fun aMachineStartsOnTheImportedFirmware() = startsAndDraws(KairoX86App.otherGame, "486ap4", importBios = true)

    /**
     * Every default preset, made with New game on a fresh install with no firmware imported, starts on the
     * firmware the app ships (KairoX86#446): the XT on GLaBIOS, the 486 and the Pentium on the free machine
     * (SeaBIOS, SeaVGABIOS). Each boots FreeDOS from the test resources' floppy in drive A and draws.
     */
    @Test
    fun everyPresetStartsWithNothingImported() {
        val library = screens.completeFirstRun(importBios = false)
        for ((preset, board) in listOf("xt" to "ibmpc82", "486" to "kairo_pc", "pentium" to "kairo_pc")) {
            val name = "Preset $preset"
            createFromPreset(preset, name, floppy = "xt/fd13-720k.img")
            library.open(name).play()
            driver.waitFrames(600)
            val probe = driver.probe()
            expect.equal("the board the $preset preset starts on", board, probe.details["core.machine"])
            expect.that("the $preset preset boots its floppy", "fd13" in probe.details["media.Floppy A"].orEmpty().lowercase()) {
                probe.details["media.Floppy A"].orEmpty()
            }
            val picture = driver.pictures.game("preset-$preset")
            expect.that("the $preset preset draws", picture.drawn()) { "lit ${picture.litFraction()}" }
            screens.endGame()
        }
    }

    /** New game from the library: [preset]'s hardware as it comes, [floppy] in drive A, named [name]. */
    private fun createFromPreset(preset: String, name: String, floppy: String) {
        driver.find(By.id("library.new-game")).tap()
        val kinds = driver.page("New game").waitUntilShown()
        kinds.find(By.item("o:preset-$preset")).tap()
        kinds.find(By.id("footer:next")).tap()
        // The preset's hardware pages, as it fills them; no firmware page, as it needs nothing imported
        for (title in listOf("Machine", "Processor and memory", "Cards")) {
            driver.page(title).waitUntilShown().find(By.id("footer:next")).tap()
        }
        val disks = driver.page("Disks")
        screens.choose(disks.waitUntilShown(), "new-drive-a", floppy)
        disks.find(By.id("footer:next")).tap()
        val naming = driver.page("new-game-name").waitUntilShown()
        val field = naming.find(By.id("new-game.name"))
        // The default name out, the game's in, as a player types it
        field.type("")
        driver.press(KeyEvent.KEYCODE_MOVE_END, fromKeyboard = true)
        repeat(field.text().length) { driver.press(KeyEvent.KEYCODE_DEL, fromKeyboard = true) }
        driver.type(name)
        naming.find(By.id("footer:done")).tap()
        screens.library.waitForGame(name)
    }

    /** The floppy the machine's 86box.cfg names is in drive A when it starts. */
    @Test
    fun theMachinesFloppyIsInItsDrive() {
        screens.completeFirstRun().open(KairoX86App.otherGame).play()
        val held = driver.probe().details["media.Floppy A"].orEmpty()
        expect.that("Floppy A holds the machine's FreeDOS disk", "freedos" in held.lowercase()) { held }
    }

    /** A machine setting chosen in Game settings is what 86Box starts with. */
    private fun reachesTheMachine(option: String, choice: String? = null) {
        val game = screens.completeFirstRun().open(KairoX86App.otherGame)
        val picked = screens.choose(game.openSettings(), option, choice)
        game.closeSettings()
        game.play()
        expect.equal("the $option 86Box started with", picked, driver.probe().details["core.$option"])
    }

    @Test
    fun theMemoryReachesTheMachine() = reachesTheMachine("memory")

    /** No video card: the one choice besides the S3 whose firmware the test ROM set holds. */
    @Test
    fun theVideoCardReachesTheMachine() = reachesTheMachine("video", "none")

    /** While it boots, the machine runs flat out: more guest time passes than real time (KairoX86#41, #60). */
    @Test
    fun theBootRunsFasterThanTheRealMachine() {
        // The XT: a 486 does not run faster than the real machine on the RG DS (docs/core-performance.md).
        screens.completeFirstRun().open(KairoX86App.bootGame).play()
        val before = driver.probe()
        val started = System.nanoTime()
        driver.waitFrames(600)
        val after = driver.probe()
        val wall = (System.nanoTime() - started) / 1e9
        val frameUs = after.details["core.frame_us"]?.toLongOrNull() ?: error("the core reports no frame_us")
        val guest = (after.details.getValue("frames").toLong() - before.details.getValue("frames").toLong()) * frameUs / 1e6
        expect.that("the boot runs faster than the real machine", guest > wall) { "guest %.2f s in %.2f s".format(guest, wall) }
    }
}
