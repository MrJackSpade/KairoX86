package com.mrjackspade.kairox86.uitest

import com.mrjackspade.kairo.frontend.PcKey
import com.mrjackspade.kairo.uitest.AppUnderTest
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
    override val bootGame = "xt"
    override val bootGameFile = "games/xt/86box.cfg"
    override val otherGame = "dos486"
    override val defaultOption = "clock"
    override val searchTerm = "xt"
    override val arrowKeys = listOf(PcKey.UP.scanCode, PcKey.DOWN.scanCode, PcKey.LEFT.scanCode, PcKey.RIGHT.scanCode)
    override val returnKey = PcKey.ENTER.scanCode
    override val spaceKey = PcKey.SPACE.scanCode
    // 86Box saves no state of a running machine (KairoX86#187).
    override val hasStates = false
    // The disks of the machine's own folder are the Disks page's choices (MainActivity.ownDisks).
    override val mediaSwap = MediaSwap("dos486", "Floppy A", "freedos", filler = "img")
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
        screens.completeFirstRun().open(KairoX86App.otherGame).play()
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
