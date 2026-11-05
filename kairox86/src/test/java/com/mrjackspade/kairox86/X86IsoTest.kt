package com.mrjackspade.kairox86

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File

class X86IsoTest {
    private fun content(file: X86Iso.File) = ByteArray(file.size.toInt()) { (it * 7 + file.path.length).toByte() }

    private val files = listOf(
        X86Iso.File("SETUP.EXE", 5000),
        X86Iso.File("Read Me First.txt", 2048),
        X86Iso.File("data/levels/level one.dat", 70000),
        X86Iso.File("data/a very long file name indeed.bin", 1),
        X86Iso.File("data/empty.txt", 0),
        X86Iso.File("Data2/x.y.z", 300))

    @Test
    fun anImageHasEveryFileAtItsSectors() {
        val out = ByteArrayOutputStream()
        X86Iso.write("TEST", files, out) { ByteArrayInputStream(content(it)) }
        val image = out.toByteArray()
        assertEquals(0, image.size % 2048)
        assertEquals("CD001", String(image, 16 * 2048 + 1, 5))
        assertEquals("CD001", String(image, 17 * 2048 + 1, 5))
        assertEquals(0xff, image[18 * 2048].toInt() and 0xff)
        // The file structure version, at 881 in both descriptors (ECMA-119 8.4.31)
        assertEquals(1, image[16 * 2048 + 881].toInt())
        assertEquals(1, image[17 * 2048 + 881].toInt())
        // For checking with an ISO reader outside the test (7-Zip): build/x86iso/test.iso
        File("build/x86iso").apply { mkdirs() }.resolve("test.iso").writeBytes(image)
    }

    @Test
    fun aFileOfTheWrongSizeFails() {
        assertThrows(IllegalStateException::class.java) {
            X86Iso.write("TEST", files, ByteArrayOutputStream()) { ByteArrayInputStream(ByteArray(3)) }
        }
    }
}
