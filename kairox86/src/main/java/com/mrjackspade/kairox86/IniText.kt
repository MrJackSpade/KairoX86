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

    /**
     * Where each section starts and where each of its keys is, built when first asked and dropped at
     * each change: a settings page reads dozens of keys per row, and a scan of the whole file for
     * each froze the app as a game's page opened (KairoX86#203).
     */
    private var index: Map<String, Section>? = null

    /** A section's header line and the line of each key in it, by lowercase name. */
    private class Section(val header: Int, val keys: Map<String, Int>)

    private fun index(): Map<String, Section> = index ?: buildIndex().also { index = it }

    /** The first section of each name and the first line of each key in it, as the lookups take them. */
    private fun buildIndex(): Map<String, Section> {
        val sections = HashMap<String, Section>()
        var keys: HashMap<String, Int>? = null
        for ((at, line) in lines.withIndex()) {
            val trimmed = line.trim()
            if (trimmed.startsWith("[")) {
                val name = trimmed.lowercase()
                keys = if (name in sections) null else HashMap<String, Int>().also { sections[name] = Section(at, it) }
            } else if (keys != null && line.contains('=')) {
                keys.putIfAbsent(line.substringBefore('=').trim().lowercase(), at)
            }
        }
        return sections
    }

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
        // The lines moved: the index is built again at the next lookup.
        index = null
    }

    override fun toString(): String = (if (bom) BOM else "") + lines.joinToString(if (crlf) "\r\n" else "\n")

    private companion object {
        const val BOM = "﻿"
    }

    private fun sectionStart(section: String): Int? = index()["[$section]".lowercase()]?.header

    /** The line after [header]'s section: the next header, or the end. */
    private fun sectionEnd(header: Int): Int {
        for (at in header + 1 until lines.size) if (lines[at].trim().startsWith("[")) return at
        return lines.size
    }

    private fun find(section: String, key: String): Int? =
        index()["[$section]".lowercase()]?.keys?.get(key.trim().lowercase())
}
