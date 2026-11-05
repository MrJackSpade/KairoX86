package com.mrjackspade.kairox86

/**
 * An eXoWin9x collection in the games folder (KairoX86#219), read where it lies. Its layout:
 *  - `eXo/eXoWin9x/<year>/<Game (year)>.zip`: a game, its own VHD (its installed files, the second
 *    hard disk) and its CD images;
 *  - `Content/!Win9Xmetadata.zip`: each game's folder `eXo/eXoWin9x/!win9x/<year>/<Game (year)>/`
 *    with its emulator configuration, `Play.cfg` for a game set up for 86Box (or, once eXo's setup
 *    has run, the same folder unpacked under the collection);
 *  - `eXo/util/utilWin9x.zip`, holding `EXTWin9x.zip` (stored, so it is read where it lies) with
 *    the Windows images games start from (`emulators/86Box98/parent/W98-P.vhd`) and the CMOS and
 *    flash of eXo's machines (`emulators/86Box98/nvr/`).
 *
 * A game is a library entry whose machine is a folder KairoX86 makes for it in the collection,
 * `KairoX86/<year>/<Game (year)>/`: its 86box.cfg (the game's configuration in KairoX86's terms,
 * [translate]), the CMOS, and the game's files unpacked from its ZIP, so what the game writes stays
 * there. None of the collection's own files is ever written.
 */
object ExoWin9x {
    /** A game of a collection: [root] the collection's path ("" for the games folder itself). */
    data class Game(val root: String, val year: String, val name: String) {
        private val prefix get() = if (root.isEmpty()) "" else "$root/"
        val zipPath get() = "${prefix}eXo/eXoWin9x/$year/$name.zip"
        /** The machine folder KairoX86 makes for the game. */
        val folder get() = "${prefix}$MACHINES/$year/$name"
        /** The game's configuration folder, in the metadata archive and once unpacked under the collection. */
        val metadataFolder get() = "eXo/eXoWin9x/!win9x/$year/$name"
        val metadataPath get() = "$prefix$metadataFolder"
        val metadataArchive get() = "${prefix}Content/$METADATA"
        val utilArchive get() = "${prefix}eXo/util/$UTIL"
        /** eXo's 86Box folder, once its setup has unpacked it under the collection. */
        val emulatorFolder get() = "${prefix}eXo/emulators/86Box98"
    }

    /** The folder of every game's machine, at the collection's root. */
    const val MACHINES = "KairoX86"
    const val METADATA = "!Win9Xmetadata.zip"
    const val UTIL = "utilWin9x.zip"
    /** The archive inside [UTIL] holding the emulators' files. */
    const val EMULATORS = "EXTWin9x.zip"
    const val EMULATOR_FOLDER = "emulators/86Box98"
    const val PLAY_86BOX = "Play.cfg"
    const val PLAY_DOSBOX_X = "Play.conf"

    private val GAME = Regex("^(?:(.*)/)?eXo/eXoWin9x/((?:19|20)\\d\\d)/([^/]+)\\.zip$", RegexOption.IGNORE_CASE)
    private val COLLECTION_FILE = Regex("(^|/)(eXo/(util|eXoWin9x|emulators)/|Content/(!Win9Xmetadata|XOWin9xMetadata|LaunchBox)\\.zip$)",
        RegexOption.IGNORE_CASE)

    /** The game whose ZIP is at [path], or null for any other file. */
    fun game(path: String): Game? = GAME.matchEntire(path)?.let { Game(it.groupValues[1], it.groupValues[2], it.groupValues[3]) }

    private val MACHINE_FOLDER = Regex("^(?:(.*)/)?$MACHINES/((?:19|20)\\d\\d)/([^/]+)$")

    /** The game whose machine folder is at [path] ([Game.folder]), or null for any other folder. */
    fun gameOfFolder(path: String): Game? = MACHINE_FOLDER.matchEntire(path)?.let { Game(it.groupValues[1], it.groupValues[2], it.groupValues[3]) }

    /** Whether [path] is one of a collection's own files that is not a game: no disk archive of the library. */
    fun isCollectionFile(path: String): Boolean = game(path) == null && COLLECTION_FILE.containsMatchIn(path)

    /** Whether [path] is inside the machine folders KairoX86 makes for a collection's games. */
    fun isMachineFolder(path: String): Boolean = path.split('/').let { parts ->
        val at = parts.indexOfFirst { it.equals(MACHINES, ignoreCase = true) }
        at >= 0 && parts.size > at + 1 && parts.getOrNull(at + 1)?.matches(Regex("(?:19|20)\\d\\d")) == true
    }

    /** What [translate] makes of a game's Play.cfg. */
    data class Translation(
        /** The machine's 86box.cfg. */
        val config: String,
        /** The Windows image the game starts from, by its name in eXo's parent folder ("W98-P.vhd"). */
        val parent: String,
        /** The machine, whose CMOS and flash come from eXo's nvr folder ("686bx"). */
        val machine: String
    )

    /**
     * A game's Play.cfg as KairoX86's 86box.cfg. eXo runs it from its emulator folder over a
     * differencing disk it makes fresh for every start (`W98-C.vhd` over `parent/W98-P.vhd`), with the
     * game's files at `../../eXoWin9x/<year>/<game>/`. Here that disk is the child 86Box makes over
     * [parentPath] in the session ([CHILD]), and the game's files are those unpacked into its machine
     * folder by their names in its ZIP ([members]), which a reference must name, whatever its case.
     * The host's own settings ([General]) go.
     */
    fun translate(playCfg: String, members: Collection<String>, parentPath: (String) -> String): Translation {
        val byName = members.associateBy { it.substringAfterLast('/').lowercase() }
        var parent: String? = null
        var machine: String? = null
        var section = ""
        val out = StringBuilder()
        for (raw in playCfg.lines()) {
            val line = raw.trimEnd()
            if (line.startsWith("[") && line.endsWith("]")) {
                section = line.substring(1, line.length - 1)
                if (section != "General") out.append(line).append('\n')
                continue
            }
            if (section == "General") continue
            val equals = line.indexOf('=')
            if (equals < 0) {
                out.append(line).append('\n')
                continue
            }
            val key = line.substring(0, equals).trim()
            val value = line.substring(equals + 1).trim()
            when {
                section == "Machine" && key == "machine" -> {
                    machine = value
                    out.append(line).append('\n')
                }
                // eXo's Windows disk: the session's child over the parent (eXo's own naming, X-C over X-P)
                key.matches(Regex("hdd_\\d\\d_fn")) && !value.contains('/') && value.matches(Regex("(?i).+-C\\.vhd")) -> {
                    check(parent == null) { "$PLAY_86BOX names two Windows disks" }
                    parent = value.replace(Regex("(?i)-C\\.vhd$"), "-P.vhd")
                    out.append("$key = $CHILD\n")
                    out.append("${key.removeSuffix("_fn")}_vhd_parent = ${parentPath(parent)}\n")
                }
                value.contains("../") -> {
                    val name = value.substringAfterLast('/').lowercase()
                    val member = checkNotNull(byName[name]) { "$PLAY_86BOX names ${value.substringAfterLast('/')}, which is not in the game's archive" }
                    out.append("$key = ${member.substringAfterLast('/')}\n")
                }
                else -> out.append(line).append('\n')
            }
        }
        return Translation(out.toString(), checkNotNull(parent) { "$PLAY_86BOX names no Windows disk" },
            checkNotNull(machine) { "$PLAY_86BOX names no machine" })
    }

    /** The differencing disk 86Box makes over the parent in the session, so every start begins from the parent. */
    const val CHILD = "windows.vhd"
}
