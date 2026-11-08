package com.mrjackspade.kairox86

import android.content.Context
import com.mrjackspade.kairo.frontend.ImportedFiles
import com.mrjackspade.kairo.frontend.UiText
import java.io.File

/**
 * The SoundFonts FluidSynth plays a game's General MIDI music with (KairoX86#306): GeneralUser GS,
 * which the app ships and installs into the ROM set where the core takes it when a machine names none
 * (core: sound/kairo/GeneralUser-GS.sf2), and every SoundFont the player has given the app, kept by
 * content in [files] ("sf:<hash>"), which a game picks as its own.
 */
object X86SoundFonts {
    /** The SoundFont the app ships, at its place in the ROM set. */
    const val SHIPPED = "sound/kairo/GeneralUser-GS.sf2"

    /** A game's choice of the shipped SoundFont: no sound_font in its 86box.cfg. */
    const val DEFAULT = "default"

    /** The player's SoundFonts (MainActivity sets it before the first settings page). */
    @Volatile lateinit var files: ImportedFiles

    fun library(context: Context) = ImportedFiles(File(context.filesDir, "soundfonts"), PREFIX, ".sf2", MAX_BYTES,
        context.getString(R.string.sound_font_too_large), ::validate) { file, importedName ->
        ImportedFiles.Described(importedName ?: file.name)
    }

    /** A SoundFont 2 file is a RIFF file of form "sfbk"; anything else FluidSynth cannot play. */
    private fun validate(file: File) {
        val header = ByteArray(12)
        val read = file.inputStream().use { it.read(header) }
        if (read < 12 || String(header, 0, 4, Charsets.US_ASCII) != "RIFF" || String(header, 8, 4, Charsets.US_ASCII) != "sfbk")
            throw ImportedFiles.Refused(UiText.res(R.string.sound_font_not_sf2))
    }

    private const val PREFIX = "sf"
    /** The largest SoundFont a player may bring: General MIDI banks run to a few hundred MB. */
    private const val MAX_BYTES = 2L * 1024 * 1024 * 1024
}
