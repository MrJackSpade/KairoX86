package com.mrjackspade.kairox86

import com.mrjackspade.kairo.frontend.R as FrontendR
import com.mrjackspade.kairo.frontend.CatalogSetting
import com.mrjackspade.kairo.frontend.LayeredGameCatalog
import com.mrjackspade.kairo.frontend.PcKey
import com.mrjackspade.kairo.frontend.UiText
import org.json.JSONArray

/**
 * KairoX86's catalog: the system definition alone (catalog/system-v2.json: the controls every
 * entry starts from), with no games (KairoX86#66, #72). An entry's machine settings live in its
 * own 86box.cfg, not in a catalog record, so the catalog gives no machine settings; a machine's
 * startup commands are the player's own (KairoX86#46).
 */
object X86Catalog : LayeredGameCatalog.Schema {
    override val platform = "pc"
    override val catalogUrl = "https://raw.githubusercontent.com/MrJackSpade/KairoX86/main/catalog/"
    override val selfHostedArt = "/MrJackSpade/KairoX86/main/catalog/artwork/art/catalog/"
    /** An entry is a machine folder, identified by its 86box.cfg ("vm"); its drives take these media. */
    override val contentId = Regex("sha256-(?:vm|fd|hd|cd)-v1:[0-9a-f]{64}")
    /** The PC's Esc, and its Enter and keypad Enter. */
    override val escapeKeys = setOf(PcKey.ESCAPE.scanCode)
    override val enterKeys = setOf(PcKey.ENTER.scanCode, PcKey.PAD_ENTER.scanCode)
    /** The pointer goes where the screen is touched: through the DOS mouse driver, else by motion (x86_core.cpp). */
    override val directTouch = true
    override val mediaExtensions = Regex("\\.(?:cfg|img|ima|imd|td0|86f|mfm|vfd|flp|dsk|xdf|hdm|fdi|hdi|hdx|vhd" +
        "|iso|cue|bin|mds|mdf|ccd|chd)$", RegexOption.IGNORE_CASE)

    /** The lines typed at the machine's DOS prompt to start a game, such as `CD \GAME` and `GAME` (KairoX86#46). */
    val startupCommands = CatalogSetting.Lines(LAUNCH, COMMANDS, UiText.res(FrontendR.string.kairo_startup_commands),
        UiText.res(FrontendR.string.kairo_startup_commands_hint), Regex("[ -~]{1,120}"), 8) { _, _ -> emptyList() }

    override val settings: List<CatalogSetting> = listOf(startupCommands)
    override val fields = CatalogSetting.fields(settings)

    override fun validMedia(role: String, contentId: String) = false

    override fun validField(field: String, value: Any): Boolean =
        field in fields && CatalogSetting.valid(settings, contentId, field, value)

    override fun validBindings(bindings: JSONArray) = X86Keys.bindings.valid(bindings)

    const val LAUNCH = "launch"
    const val COMMANDS = "commands"
}
