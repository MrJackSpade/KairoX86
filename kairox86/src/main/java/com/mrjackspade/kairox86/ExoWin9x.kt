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

    /** eXo's 86Box machine for its own Windows 98, which a DOSBox-X game runs on here ([translateDosbox]). */
    const val EMULATOR_CONFIG = "86box.cfg"

    /**
     * What a DOSBox-X game's Play.conf mounts before it boots: drive [drive]'s [images] (a CD's
     * several, the first in the drive), [cdrom] or a hard disk; [folder] when it mounts a folder of
     * the host as the drive, not an image.
     */
    data class Mount(val drive: Char, val images: List<String>, val cdrom: Boolean, val folder: Boolean)

    /** The DOSBox-X Windows image a Play.conf boots (its parent, `vhdmake -f -l <parent> <child>`), by name. */
    fun dosboxWindows(playConf: String): String? = autoexec(playConf)
        .firstOrNull { it.startsWith("vhdmake", ignoreCase = true) }
        ?.let { tokens(it).getOrNull(3) }?.replace('\\', '/')?.substringAfterLast('/')

    /** The drives a Play.conf mounts besides C: (eXo's DOSBox-X Windows image). */
    fun dosboxMounts(playConf: String): List<Mount> = autoexec(playConf).mapNotNull { line ->
        val words = tokens(line)
        val command = words.firstOrNull()?.lowercase()
        if ((command != "imgmount" && command != "mount") || words.size < 3) return@mapNotNull null
        val drive = words[1].single().lowercaseChar()
        if (drive == 'c') return@mapNotNull null
        val images = words.drop(2).takeWhile { !it.startsWith("-") }.map { it.replace('\\', '/') }
        val type = words.indexOf("-t").takeIf { it >= 0 }?.let { words.getOrNull(it + 1)?.lowercase() }
        Mount(drive, images, cdrom = type == "cdrom", folder = command == "mount")
    }

    /**
     * A file copy a Play.conf makes before Windows boots (KairoX86#225): `xcopy d:\windows\*.ini
     * c:\windows\ /Y` copies the files of drive [sourceDrive]'s folder [sourceFolder] ("windows")
     * that [pattern] matches into drive [targetDrive]'s folder [targetFolder].
     */
    data class Copy(val sourceDrive: Char, val sourceFolder: String, val pattern: String, val targetDrive: Char, val targetFolder: String) {
        /** Whether [name] is one this copy takes: DOS's `*` and `?`, whatever the case. */
        fun matches(name: String): Boolean = Regex(pattern.lowercase().map { c ->
            when (c) {
                '*' -> ".*"
                '?' -> "."
                else -> Regex.escape(c.toString())
            }
        }.joinToString("")).matches(name.lowercase())
    }

    /** The copies a Play.conf makes before Windows boots, in order: each `xcopy <file or pattern> <folder>\ /Y`. */
    fun dosboxCopies(playConf: String): List<Copy> = autoexec(playConf).mapNotNull { line ->
        val words = tokens(line)
        if (!words.first().equals("xcopy", ignoreCase = true)) return@mapNotNull null
        val flags = words.drop(1).filter { it.startsWith("/") }
        check(flags.all { it.equals("/y", ignoreCase = true) }) { "$PLAY_DOSBOX_X copies with ${flags.joinToString(" ")}: \"$line\"" }
        val paths = words.drop(1).filter { !it.startsWith("/") }
        check(paths.size == 2) { "$PLAY_DOSBOX_X copies something other than files into a folder: \"$line\"" }
        val (source, target) = paths.map { it.replace('\\', '/') }
        check(source.length > 2 && source[1] == ':' && target.length > 2 && target[1] == ':' && target.endsWith("/")) {
            "$PLAY_DOSBOX_X copies something other than files into a folder: \"$line\""
        }
        val sourcePath = source.substring(2).trim('/')
        Copy(source[0].lowercaseChar(), sourcePath.substringBeforeLast('/', ""), sourcePath.substringAfterLast('/'),
            target[0].lowercaseChar(), target.substring(2).trim('/'))
    }

    /** The DOSBox-X Windows images whose 86Box counterpart is eXo's 86Box Windows 98 ([PARENT_86BOX]). */
    val DOSBOX_ENGLISH_98 = setOf("w98-c.vhd", "w98-c-net.vhd", "w98-c-net2.vhd")
    const val PARENT_86BOX = "W98-P.vhd"

    /**
     * A DOSBox-X game as an 86Box machine (KairoX86#219): eXo's own 86Box machine for its Windows 98
     * ([template], its emulator folder's 86box.cfg) with the game's drives from its Play.conf. The
     * Windows disk is the session's child over the parent ([parentPath] of [PARENT_86BOX]), the
     * game's hard disk images follow (each by its size in sectors, [sectors], at eXo's 63 x 16
     * geometry), and its CDs take the IDE channels after them, each holding the first of its images.
     */
    fun translateDosbox(template: String, mounts: List<Mount>, members: Collection<String>, parentPath: (String) -> String,
                        sectors: (String) -> Long): Translation {
        val byName = members.associateBy { it.substringAfterLast('/').lowercase() }
        fun member(path: String): String = checkNotNull(byName[path.substringAfterLast('/').lowercase()]) {
            "$PLAY_DOSBOX_X mounts ${path.substringAfterLast('/')}, which is not in the game's archive"
        }.substringAfterLast('/')
        val disks = mounts.filter { !it.cdrom && !it.folder }.map { member(it.images.single()) }
        val cds = mounts.filter { it.cdrom }.map { member(it.images.first()) }
        val ini = IniText(template)
        val machine = checkNotNull(ini["Machine", "machine"]) { "$EMULATOR_CONFIG names no machine" }
        val windows = checkNotNull(ini["Hard disks", "hdd_01_parameters"]) { "$EMULATOR_CONFIG names no Windows disk" }
        val out = StringBuilder()
        // The template's drives (besides its CDs) go into the one drives section written below: 86Box
        // reads one section of a name
        val drives = StringBuilder()
        var section = ""
        for (raw in template.lines()) {
            val line = raw.trimEnd()
            if (line.startsWith("[") && line.endsWith("]")) {
                section = line.substring(1, line.length - 1)
                if (section !in setOf("General", "Hard disks", DRIVES)) out.append(line).append('\n')
                continue
            }
            when (section) {
                "General", "Hard disks" -> {}
                DRIVES -> if (line.isNotBlank() && !line.trimStart().startsWith("cdrom_")) drives.append(line).append('\n')
                else -> out.append(line).append('\n')
            }
        }
        out.append("\n[Hard disks]\n")
        out.append("hdd_01_fn = $CHILD\nhdd_01_vhd_parent = ${parentPath(PARENT_86BOX)}\nhdd_01_ide_channel = 0:0\n")
        out.append("hdd_01_parameters = $windows\nhdd_01_speed = ramdisk\n")
        disks.forEachIndexed { index, disk ->
            val n = "%02d".format(index + 2)
            val cylinders = sectors(disk) / (63 * 16)
            check(cylinders > 0) { "$disk is smaller than a cylinder" }
            out.append("hdd_${n}_fn = $disk\nhdd_${n}_ide_channel = ${channel(index + 1)}\nhdd_${n}_parameters = 63, 16, $cylinders, 0, ide\nhdd_${n}_speed = ramdisk\n")
        }
        out.append("\n[$DRIVES]\n").append(drives)
        cds.forEachIndexed { index, cd ->
            val n = "%02d".format(index + 1)
            out.append("cdrom_${n}_ide_channel = ${channel(disks.size + 1 + index)}\ncdrom_${n}_image_path = $cd\ncdrom_${n}_parameters = 1, atapi\n")
        }
        return Translation(out.toString(), PARENT_86BOX, machine)
    }

    private const val DRIVES = "Floppy and CD-ROM drives"

    /** The [index]th IDE channel, the primary master's first. */
    private fun channel(index: Int): String {
        check(index < 8) { "More drives than the IDE channels hold" }
        return "${index / 2}:${index % 2}"
    }

    private fun autoexec(playConf: String): List<String> {
        val lines = playConf.lines().map { it.trim() }
        val start = lines.indexOfFirst { it.equals("[autoexec]", ignoreCase = true) }
        return if (start < 0) emptyList() else lines.drop(start + 1).filter { it.isNotEmpty() && !it.startsWith("#") }
    }

    /** A command line's words, a quoted one with its spaces. */
    private fun tokens(line: String): List<String> = Regex("\"([^\"]*)\"|(\\S+)").findAll(line).map { it.groupValues[1].ifEmpty { it.groupValues[2] } }.toList()
}
