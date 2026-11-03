package com.mrjackspade.kairox86

import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/**
 * The hardware 86Box offers (Kairo#143), as the core answers (core/kairo/hardware.h): every machine,
 * and for each machine the processors, memory and cards 86Box lets it take, with whether the player's
 * ROM set has their firmware. Read once per app run and kept: 86Box's tables do not change, and the ROM
 * set is the player's one folder.
 */
object X86Hardware {
    class Machine(val id: String, val name: String, val type: String, val available: Boolean)
    class Speed(val speed: Long, val multi: String, val name: String)
    class Family(val id: String, val name: String, val speeds: List<Speed>)
    class Card(val id: String, val name: String, val available: Boolean)
    class Takes(val cpus: List<Family>, val ramMin: Int, val ramMax: Int, val ramStep: Int, val cards: Map<String, List<Card>>)

    /** The card kinds a machine takes, as the core names them. */
    const val VIDEO = "video"
    const val SOUND = "sound"
    const val NETWORK = "network"
    const val HDC = "hdc"
    const val SCSI = "scsi"
    const val FDC = "fdc"
    const val MOUSE = "mouse"
    const val JOYSTICK = "joystick"
    private val KINDS = listOf(VIDEO, SOUND, NETWORK, HDC, SCSI, FDC, MOUSE, JOYSTICK)

    /** The player's 86Box ROM set (MainActivity.firmwareFolder), set before the first query. */
    @Volatile lateinit var roms: File

    private var machines: List<Machine>? = null
    private val takes = HashMap<String, Takes>()

    @Synchronized fun machines(): List<Machine> = machines ?: JSONArray(query("machines")).let { list ->
        (0 until list.length()).map { list.getJSONObject(it) }
            .map { Machine(it.getString("id"), it.getString("name"), it.getString("type"), it.getBoolean("available")) }
    }.also { machines = it }

    /** What machine [id] takes. */
    @Synchronized fun takes(id: String): Takes = takes.getOrPut(id) {
        val answer = JSONObject(query("machine $id"))
        val cpus = answer.getJSONArray("cpus").let { list ->
            (0 until list.length()).map { list.getJSONObject(it) }.map { family ->
                val speeds = family.getJSONArray("speeds")
                Family(family.getString("family"), family.getString("name"), (0 until speeds.length()).map { speeds.getJSONObject(it) }
                    .map { Speed(it.getLong("speed"), multi(it.getDouble("multi")), it.getString("name")) })
            }
        }
        val ram = answer.getJSONObject("ram")
        val cards = KINDS.associateWith { kind ->
            val list = answer.getJSONArray(kind)
            (0 until list.length()).map { list.getJSONObject(it) }
                .map { Card(it.getString("id"), it.getString("name"), it.getBoolean("available")) }
        }
        Takes(cpus, ram.getInt("min"), ram.getInt("max"), ram.getInt("step"), cards)
    }

    /** A processor multiplier as one text for each value, whether 86Box wrote "2" or "2.000000". */
    fun multi(value: Double): String = java.math.BigDecimal.valueOf(value).stripTrailingZeros().toPlainString()

    private fun query(query: String): String = nativeQuery(roms.absolutePath, query)

    @JvmStatic private external fun nativeQuery(roms: String, query: String): String

    init {
        System.loadLibrary("kairox86")
    }
}
