package com.mrjackspade.kairox86

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.RandomAccessFile
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

class DosboxFatTest {
    @get:Rule val temp = TemporaryFolder()

    /** The names DOSBox-X's drive cache makes, worked through by hand from drive_cache.cpp. */
    @Test
    fun eightThreeNamesAreDosboxXs() {
        // Two entries can't share an 8.3 name: the second readme finds the first (GetLongName) and is numbered
        assertEquals(listOf("README.TXT", "SETUP.EXE", "README~1.TXT"), DosboxFat.shortNames(listOf("README.TXT", "SETUP.EXE", "readme.txt")))
        // Spaces dropped, a number added; the next of the same start takes the next number
        assertEquals(listOf("LONGFI~1.TXT", "LONGFI~2.TXT"), DosboxFat.shortNames(listOf("Long File Name.txt", "Long File Other.txt")))
        // An extension longer than three
        assertEquals(listOf("A~1.HTM"), DosboxFat.shortNames(listOf("a.html")))
        // A leading dot
        assertEquals(listOf("HIDDEN~1"), DosboxFat.shortNames(listOf(".hidden")))
        // More than eight before the dot
        assertEquals(listOf("INSTALLA.EXE", "INSTAL~1.EXE"), DosboxFat.shortNames(listOf("INSTALLA.EXE", "Installation.exe")))
        // A character DOS names can't hold
        assertEquals(listOf("A_B~1.TXT"), DosboxFat.shortNames(listOf("a+b.txt")))
    }

    private fun content(n: Int, size: Int) = ByteArray(size) { ((it * 7 + n) % 251).toByte() }

    @Test
    fun aDiskHoldsTheArchivesFilesReadOnly() {
        val date = DosboxFat.packDate(1996, 5, 17)
        val sizes = listOf(3_000_000, 1_500_000, 600, 0)
        val files = listOf(
            DosboxFat.Entry("Setup.exe", false, sizes[0].toLong(), date, 0x6000, member = 0),
            DosboxFat.Entry("DATA", true, 0, DosboxFat.IMPLICIT_DATE, 0, listOf(
                DosboxFat.Entry("Level One Map.dat", false, sizes[1].toLong(), date, 0x6000, member = 1),
                DosboxFat.Entry("readme.txt", false, sizes[2].toLong(), date, 0x6000, member = 2))),
            DosboxFat.Entry("empty.txt", false, 0, date, 0x6000, member = 3))
        val layout = DosboxFat.layout(files)
        val out = ByteArrayOutputStream()
        DosboxFat.write(layout, layout.sectors, out) { e -> ByteArrayInputStream(content(e.member as Int, sizes[e.member])) }
        val image = out.toByteArray()
        assertEquals(layout.sectors * 512, image.size.toLong())
        val disk = object : Sectors {
            override val count = layout.sectors
            override fun read(lba: Long) = image.copyOfRange((lba * 512).toInt(), (lba * 512 + 512).toInt())
            override fun write(lba: Long, data: ByteArray) = throw UnsupportedOperationException()
        }
        val volume = FatVolume(disk)
        assertEquals(listOf("SETUP.EXE", "DATA", "EMPTY.TXT").sorted(), volume.list("").map { it.name }.sorted())
        assertArrayEquals(content(0, sizes[0]), volume.read(volume.find("Setup.exe")!!))
        val map = volume.find("DATA/Level One Map.dat")!!
        assertEquals("LEVELO~1.DAT", map.name)
        assertEquals("Level One Map.dat", map.longName)
        assertArrayEquals(content(1, sizes[1]), volume.read(map))
        assertArrayEquals(content(2, sizes[2]), volume.read(volume.find("data/README.TXT")!!))
        assertEquals(0L, volume.find("EMPTY.TXT")!!.size)
        // Read-only, as a ZIP drive with no write folder converts
        for (e in volume.list("") + volume.list("DATA")) assertTrue(e.name, e.attributes and 0x01 != 0)
        // DOSBox-X's partition: active, at sector 32
        assertEquals(0x80, image[446].toInt() and 0xff)
        assertEquals(32, image[454].toInt())
        assertEquals("MSDOS5.0", String(image, 32 * 512 + 3, 8))
    }

    @Test
    fun aZipIsListedAsPhysfsListsIt() {
        val zip = temp.newFile("game.zip")
        ZipOutputStream(zip.outputStream()).use { z ->
            fun put(name: String, data: ByteArray?, time: Long) {
                z.putNextEntry(ZipEntry(name).apply { this.time = time })
                if (data != null) z.write(data)
                z.closeEntry()
            }
            val t = java.util.GregorianCalendar(1996, 4, 17, 12, 0, 10).timeInMillis
            put("SETUP.EXE", ByteArray(10), t)
            put("DATA/", null, t)
            put("DATA/MAP.DAT", ByteArray(20), t)
            put("IMPLICIT/SUB/FILE.TXT", ByteArray(5), t)
        }
        val entries = RandomAccessFile(zip, "r").use { ZipListing.read(it.channel) }
        val byName = entries.associateBy { it.name }
        assertEquals(10L, byName.getValue("SETUP.EXE").size)
        assertEquals(DosboxFat.packDate(1996, 5, 17), byName.getValue("SETUP.EXE").date)
        assertEquals((12 shl 11) or 5, byName.getValue("SETUP.EXE").time)
        // A folder the archive lists keeps its time; one only its paths imply has PhysFS's
        assertEquals(DosboxFat.packDate(1996, 5, 17), byName.getValue("DATA").date)
        assertEquals(DosboxFat.IMPLICIT_DATE, byName.getValue("IMPLICIT").date)
        assertEquals("FILE.TXT", byName.getValue("IMPLICIT").children.single().children.single().name)
        assertEquals("DATA/MAP.DAT", byName.getValue("DATA").children.single().member)
    }
}
