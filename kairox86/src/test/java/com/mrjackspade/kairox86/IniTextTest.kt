package com.mrjackspade.kairox86

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/** 86box.cfg read and changed one key at a time, everything else kept (Kairo#142). */
class IniTextTest {
    private val config = "﻿[General]\r\nconfirm_exit = 0\r\n\r\n[Machine]\r\nmachine = 486ap4\r\ncpu_speed = 66666666\r\n\r\n[Video]\r\ngfxcard = cga\r\n"

    @Test
    fun readsAKeyOfASection() {
        val text = IniText(config)
        assertEquals("486ap4", text["Machine", "machine"])
        assertEquals("cga", text["video", "GFXCARD"])
        assertNull(text["Machine", "time_sync"])
        assertNull(text["Sound", "sndcard"])
    }

    @Test
    fun changesOnlyTheKey() {
        val text = IniText(config)
        text["Machine", "machine"] = "bx6"
        assertEquals(config.replace("machine = 486ap4", "machine = bx6"), text.toString())
    }

    @Test
    fun addsAKeyAtTheEndOfItsSection() {
        val text = IniText(config)
        text["Machine", "time_sync"] = "utc"
        assertEquals(config.replace("cpu_speed = 66666666\r\n", "cpu_speed = 66666666\r\ntime_sync = utc\r\n"), text.toString())
    }

    @Test
    fun removesAKey() {
        val text = IniText(config)
        text["Machine", "cpu_speed"] = null
        assertEquals(config.replace("cpu_speed = 66666666\r\n", ""), text.toString())
        text["Machine", "absent"] = null
        assertEquals(config.replace("cpu_speed = 66666666\r\n", ""), text.toString())
    }

    @Test
    fun addsASectionAtTheEnd() {
        val text = IniText(config)
        text["Sound", "sndcard"] = "sb16"
        assertEquals(config + "\r\n[Sound]\r\nsndcard = sb16\r\n", text.toString())
        assertEquals("sb16", IniText(text.toString())["Sound", "sndcard"])
    }

    @Test
    fun keepsTheByteOrderMarkOutOfTheFirstHeader() {
        val text = IniText(config)
        text["General", "confirm_exit"] = "1"
        assertEquals("1", text["General", "confirm_exit"])
        assertEquals('﻿', text.toString()[0])
    }
}
