package com.mrjackspade.kairox86

/**
 * An 86Box configuration file's text (86box.cfg: `[Section]` headers, `key = value` lines), read and
 * changed one key at a time with every other line kept as it was (Kairo#142).
 */
class IniText(text: String) {
    // A byte order mark (86Box writes one) stays at the front, out of the first header's way.
    private val bom = text.startsWith(BOM)
    private val lines: MutableList<String> = text.removePrefix(BOM).replace("\r\n", "\n").split('\n').toMutableList()
    private val crlf = text.contains("\r\n")

    /** The value of [key] in [section], or null when the section or key is absent. */
    operator fun get(section: String, key: String): String? {
        val at = find(section, key) ?: return null
        return lines[at].substringAfter('=').trim()
    }

    /** Every key of [section] with its value, in the file's order; none when the section is absent. */
    fun entries(section: String): List<Pair<String, String>> {
        val header = sectionStart(section) ?: return emptyList()
        return (header + 1 until sectionEnd(header)).map { lines[it] }.filter { it.contains('=') }
            .map { it.substringBefore('=').trim() to it.substringAfter('=').trim() }
    }

    /** Sets [key] in [section] to [value], adding the section or key where absent; null removes the key. */
    operator fun set(section: String, key: String, value: String?) {
        val at = find(section, key)
        when {
            at != null && value == null -> lines.removeAt(at)
            at != null -> lines[at] = "$key = $value"
            value == null -> Unit
            else -> {
                val header = sectionStart(section)
                if (header == null) {
                    // A new section at the end, after a blank line.
                    while (lines.isNotEmpty() && lines.last().isBlank()) lines.removeAt(lines.size - 1)
                    if (lines.isNotEmpty()) lines += ""
                    lines += "[$section]"
                    lines += "$key = $value"
                    lines += ""
                } else {
                    // After the section's last key, before the blank lines that end it.
                    var end = sectionEnd(header)
                    while (end > header + 1 && lines[end - 1].isBlank()) end--
                    lines.add(end, "$key = $value")
                }
            }
        }
    }

    override fun toString(): String = (if (bom) BOM else "") + lines.joinToString(if (crlf) "\r\n" else "\n")

    private companion object {
        const val BOM = "﻿"
    }

    private fun sectionStart(section: String): Int? =
        lines.indexOfFirst { it.trim().equals("[$section]", ignoreCase = true) }.takeIf { it >= 0 }

    /** The line after [header]'s section: the next header, or the end. */
    private fun sectionEnd(header: Int): Int {
        for (at in header + 1 until lines.size) if (lines[at].trim().startsWith("[")) return at
        return lines.size
    }

    private fun find(section: String, key: String): Int? {
        val header = sectionStart(section) ?: return null
        for (at in header + 1 until sectionEnd(header)) {
            val line = lines[at]
            if (line.contains('=') && line.substringBefore('=').trim().equals(key, ignoreCase = true)) return at
        }
        return null
    }
}
