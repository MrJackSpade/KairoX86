package com.mrjackspade.kairox86.uitest

import com.mrjackspade.kairo.frontend.PcKey
import com.mrjackspade.kairo.uitest.AppUnderTest
import com.mrjackspade.kairo.uitest.AppUnderTest.MediaSwap

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
