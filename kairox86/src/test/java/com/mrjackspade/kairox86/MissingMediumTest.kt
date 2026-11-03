package com.mrjackspade.kairox86

import com.mrjackspade.kairo.frontend.UiText
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import com.mrjackspade.kairo.frontend.R as FrontendR

/** A disk a machine's 86box.cfg names that its folder lacks is reported at launch (KairoX86#63). */
class MissingMediumTest {
    private val folder = setOf("freedos.img", "disks/game2.img", "cd/game.cue", "hdd.img")
    private fun missing(text: String) = X86Library.missingMedium(IniText(text)) { it in folder }

    @Test
    fun aMachineWithAllItsDisks() {
        assertNull(missing("[Floppy and CD-ROM drives]\nfdd_01_fn = freedos.img\nfdd_02_fn = wp://disks\\game2.img\n" +
            "cdrom_01_image_path = cd/game.cue\ncdrom_01_image_history_01 = gone.iso\n\n[Hard disks]\nhdd_01_fn = hdd.img\n"))
    }

    @Test
    fun aSecondFloppyThatIsNotThere() {
        assertEquals(UiText.res(FrontendR.string.kairo_floppy_disk),
            missing("[Floppy and CD-ROM drives]\nfdd_01_fn = freedos.img\nfdd_02_fn = disk2.img\n"))
    }

    @Test
    fun aCdAndAHardDisk() {
        assertEquals(UiText.res(FrontendR.string.kairo_companion_cd),
            missing("[Floppy and CD-ROM drives]\ncdrom_01_image_path = game.iso\n"))
        assertEquals(UiText.res(FrontendR.string.kairo_hard_disk), missing("[Hard disks]\nhdd_02_fn = other.img\n"))
    }

    @Test
    fun mediaOutsideTheFolderAreNeverThere() {
        for (path in listOf("C:\\86Box\\freedos.img", "/home/me/freedos.img", "../freedos.img", "<exe_path>/freedos.img"))
            assertEquals(path, UiText.res(FrontendR.string.kairo_floppy_disk), missing("[Floppy and CD-ROM drives]\nfdd_01_fn = $path\n"))
        assertEquals(UiText.res(FrontendR.string.kairo_companion_cd),
            missing("[Floppy and CD-ROM drives]\ncdrom_01_image_path = ioctl://D:\n"))
    }

    @Test
    fun removableDisksTapesAndCartridges() {
        assertEquals(UiText.res(R.string.media_removable_disk), missing("[Other removable devices]\nzip_01_image_path = zip.img\n"))
        assertEquals(UiText.res(R.string.media_tape), missing("[Other removable devices]\ntape_01_image_path = backup.tap\n"))
        assertEquals(UiText.res(FrontendR.string.kairo_cartridge), missing("[Storage controllers]\ncartridge_01_fn = basic.jrc\n"))
    }
}
