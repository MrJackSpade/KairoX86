package com.mrjackspade.kairox86

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

class X86HardDiskTest {
    private fun reader(bytes: ByteArray): (Long, Int) -> ByteArray = { offset, length ->
        bytes.copyOfRange(offset.toInt(), offset.toInt() + length)
    }

    @Test
    fun aVhdNamesTheGeometryOfItsFooter() {
        val vhd = ByteArrayOutputStream().also { X86BlankDisk(1024, 16, 63).write(it) }.toByteArray()
        assertEquals(X86HardDisk.Geometry(63, 16, 1024), X86HardDisk.geometry("disk.VHD", vhd.size.toLong(), reader(vhd)))
    }

    private fun header(signature: Long, sectorSize: Int, sectors: Int, heads: Int, cylinders: Int): ByteArray =
        ByteBuffer.allocate(4096).order(ByteOrder.LITTLE_ENDIAN).apply {
            putLong(0, signature)
            putInt(16, sectorSize)
            putInt(20, sectors)
            putInt(24, heads)
            putInt(28, cylinders)
        }.array()

    @Test
    fun anHdiAndAnHdxNameTheGeometryOfTheirHeaders() {
        val hdi = header(0, 512, 17, 8, 615)
        assertEquals(X86HardDisk.Geometry(17, 8, 615), X86HardDisk.geometry("c.hdi", hdi.size.toLong(), reader(hdi)))
        val hdx = header(0xD778A82044445459uL.toLong(), 512, 63, 16, 520)
        assertEquals(X86HardDisk.Geometry(63, 16, 520), X86HardDisk.geometry("c.hdx", hdx.size.toLong(), reader(hdx)))
    }

    private fun fails(name: String, bytes: ByteArray) {
        val failure = runCatching { X86HardDisk.geometry(name, bytes.size.toLong(), reader(bytes)) }.exceptionOrNull()
        assertTrue("$name should fail", failure is IllegalArgumentException || failure is IllegalStateException)
    }

    @Test
    fun anImageThatIsNotWhatItsNameSaysFails() {
        fails("raw.vhd", ByteArray(4096))
        fails("raw.hdx", header(0, 512, 63, 16, 520))
        fails("big.hdi", header(0, 2048, 63, 16, 520))
        fails("empty.hdi", header(0, 512, 0, 0, 0))
        fails("raw.img", ByteArray(4096))
    }
}
