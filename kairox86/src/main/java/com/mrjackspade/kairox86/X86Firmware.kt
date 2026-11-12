package com.mrjackspade.kairox86

import android.content.Context
import com.mrjackspade.kairo.frontend.FirmwareSet
import com.mrjackspade.kairo.frontend.UiText
import com.mrjackspade.kairo.frontend.WebLink
import java.io.File

/**
 * The player's firmware (KairoX86#67): 86Box's ROM set, which 86Box reads by each file's place in
 * the set (machines/486ap4/..., video/...). The app knows every file of the set by its SHA-1
 * (assets/firmware/86box-roms.tsv, tools/firmware_index.py), so a folder the player gives is
 * recognized by content under any names and in any layout, a ZIP's members too, and each file
 * goes to the place 86Box reads it from; each machine then runs on the files its model needs. No
 * file is required: a machine whose firmware is missing cannot be picked (X86Settings).
 */
object X86Firmware {
    /** A file of the set: its SHA-1 (lower-case hex), its size, and its place in the set. */
    class Entry(val sha1: String, val size: Long, val path: String)

    private val SHA1 = Regex("[0-9a-f]{40}")

    /** The index's files, failing on any line that is not a file's identity. */
    fun entries(text: String): List<Entry> = text.lineSequence().filter { it.isNotEmpty() && !it.startsWith("#") }.map { line ->
        val fields = line.split('\t')
        require(fields.size == 3) { "The firmware index has a line of ${fields.size} fields: $line" }
        val (sha1, size, path) = fields
        require(SHA1.matches(sha1)) { "The firmware index names no SHA-1 for $path" }
        val bytes = requireNotNull(size.toLongOrNull()?.takeIf { it > 0 }) { "The firmware index gives $path no size" }
        require(path.isNotEmpty() && !path.startsWith("/") && path.split('/').none { it.isEmpty() || it == "." || it == ".." }) {
            "The firmware index has a path outside the set: $path"
        }
        Entry(sha1, bytes, path)
    }.toList()

    /** The set in [folder] (the ROM set 86Box runs on), from the app's index. */
    fun set(context: Context, folder: File): FirmwareSet {
        val index = context.assets.open(INDEX).use { it.readBytes().toString(Charsets.UTF_8) }
        val description = UiText.res(R.string.firmware_rom_description)
        val parts = entries(index).map { entry ->
            FirmwareSet.Part(entry.path, UiText.fixed(entry.path), description, emptySet(), required = false,
                sizes = setOf(entry.size), sha1 = setOf(entry.sha1))
        }
        return FirmwareSet(folder, parts, requirements = emptyList(), note = UiText.res(R.string.firmware_rom_set_note),
            listed = false, project = WebLink(UiText.res(R.string.firmware_source_86box), SOURCE))
    }

    const val INDEX = "firmware/86box-roms.tsv"

    /**
     * 86Box's source, linked beside the firmware (KairoX86#438): the project, never its ROM repository, whose
     * dumps are copyrighted by their makers (Google Play bars linking to copyrighted content).
     */
    const val SOURCE = "https://github.com/86Box/86Box"
}
