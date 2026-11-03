package com.mrjackspade.kairox86

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.security.MessageDigest

/** The 86Box ROM set the app recognizes by content (KairoX86#67). */
class X86FirmwareTest {
    private val index = File("src/main/assets/${X86Firmware.INDEX}").readText()
    private val entries = X86Firmware.entries(index)

    private fun sha1(file: File) = MessageDigest.getInstance("SHA-1").digest(file.readBytes()).joinToString("") { "%02x".format(it) }

    @Test
    fun theIndexNamesEveryFileOnce() {
        assertEquals(1772, entries.size)
        assertEquals(entries.size, entries.map { it.path }.toSet().size)
        assertTrue(entries.any { it.path.startsWith("machines/486ap4/") })
    }

    @Test
    fun theFreeFirmwareIsTheSetsOwn() {
        // The app ships these (docs/licensing.md): the index knows them as the same files.
        val byPath = entries.associateBy { it.path }
        for ((path, file) in listOf("machines/glabios/GLABIOS_0.4.0_8P.ROM" to File("../third_party/glabios/GLABIOS_0.4.0_8P.ROM"),
            "machines/glabios/GLABIOS_0.4.0_VP.ROM" to File("../third_party/glabios/GLABIOS_0.4.0_VP.ROM"))) {
            val entry = checkNotNull(byPath[path]) { "The index has no $path" }
            assertEquals(path, sha1(file), entry.sha1)
            assertEquals(path, file.length(), entry.size)
        }
    }

    @Test
    fun aBrokenIndexFails() {
        assertThrows(IllegalArgumentException::class.java) { X86Firmware.entries("abc\t12\tmachines/x.bin") }
        assertThrows(IllegalArgumentException::class.java) {
            X86Firmware.entries("${"a".repeat(40)}\t12\t../outside.bin")
        }
        assertThrows(IllegalArgumentException::class.java) { X86Firmware.entries("${"a".repeat(40)}\t0\tmachines/x.bin") }
    }
}
