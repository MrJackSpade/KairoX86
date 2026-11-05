package com.mrjackspade.kairox86

import android.content.Context
import android.net.Uri
import android.provider.DocumentsContract.Document
import com.mrjackspade.kairo.frontend.DiskArchive
import com.mrjackspade.kairo.frontend.R as FrontendR
import org.apache.commons.compress.archivers.zip.ZipArchiveEntry
import org.apache.commons.compress.archivers.zip.ZipFile
import java.io.File
import java.io.FileInputStream
import java.io.InputStream
import java.io.OutputStream
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.channels.NonWritableChannelException
import java.nio.channels.SeekableByteChannel
import java.security.MessageDigest
import java.util.concurrent.CancellationException
import java.util.concurrent.atomic.AtomicBoolean
import java.util.zip.CRC32

/**
 * Makes an eXoWin9x game's machine folder from its collection (KairoX86#219, [ExoWin9x]): the
 * 86box.cfg and CMOS when the folder is first needed ([makeConfig]), and the game's files and the
 * Windows image it starts from when it first starts ([makeDisks]). Whatever is already there is kept:
 * the player's settings and what the game wrote. The collection's own files are only read.
 */
class X86Exo(private val context: Context, private val docs: X86Documents) {
    /** Whether [game]'s machine folder is made: its 86box.cfg is the last thing [makeConfig] writes. */
    fun isMade(tree: Uri, game: ExoWin9x.Game): Boolean = docs.find(tree, "${game.folder}/${X86Library.CONFIG}")?.folder == false

    /**
     * The machine folder of [game], with its 86box.cfg and CMOS, made when it is missing. A DOSBox-X
     * game's machine is the one its Windows image knows (KairoX86#224), so that image is unpacked
     * first when it is not yet ([makeDisks] would unpack it at the start).
     */
    fun makeConfig(tree: Uri, game: ExoWin9x.Game, cancelled: AtomicBoolean, progress: (String) -> Unit) {
        val folder = docs.makeFolders(tree, game.folder)
        if (docs.children(tree, folder).any { it.name == X86Library.CONFIG && !it.folder }) return
        val members = gameArchive(tree, game).use { archive -> archive.members.map { it.name } }
        val (kind, text) = gameConfig(tree, game)
        var cmosAsset: String? = null
        val translation = if (kind == ExoWin9x.PLAY_86BOX) {
            ExoWin9x.translate(text, members) { parent -> parentFile(game, parent).absolutePath }
        } else {
            // A DOSBox-X game runs on the machine its Windows image knows (KairoX86#219, #224)
            val windows = windows(tree, game, ExoWin9x.dosboxParent(ExoWin9x.dosboxWindows(text)), cancelled, progress)
            cmosAsset = windows.machine.board.cmosAsset
            // An archive DOSBox-X mounts as a drive is a CD image of its files here (KairoX86#223)
            val images = mounts(tree, game, folder, ExoWin9x.dosboxMounts(text), members)
            val mounts = images.first
            val template = checkNotNull(emulatorFile(tree, game, "${ExoWin9x.EMULATOR_FOLDER}/${ExoWin9x.EMULATOR_CONFIG}")) {
                "${game.name}'s collection has no ${ExoWin9x.EMULATORS_ROOT}/${ExoWin9x.EMULATOR_FOLDER}/${ExoWin9x.EMULATOR_CONFIG}"
            }.use { it.readBytes().toString(Charsets.UTF_8) }
            ExoWin9x.translateDosbox(template, windows, mounts, images.second, { parent -> parentFile(game, parent).absolutePath }) { disk ->
                // A hard disk's geometry comes from its size: it is unpacked now, as its start would
                vhdSectors(tree, unpackMember(tree, game, folder, disk, cancelled))
            }
        }
        val nvr = docs.makeFolders(tree, "${game.folder}/${X86Library.NVR}")
        val cmos = cmosAsset
        if (cmos != null) {
            // A board eXo has no machine of: the CMOS its BIOS saved with its defaults, which KairoX86 ships
            val name = "${translation.machine}.nvr"
            if (docs.children(tree, nvr).none { it.name == name }) context.assets.open(cmos).use { input -> docs.writeWhole(tree, nvr, name) { input.copyTo(it) } }
        } else for (name in listOf("${translation.machine}.nvr", "${translation.machine}.bin")) {
            if (docs.children(tree, nvr).any { it.name == name }) continue
            emulatorFile(tree, game, "${ExoWin9x.EMULATOR_FOLDER}/nvr/$name")?.use { input -> docs.writeWhole(tree, nvr, name) { input.copyTo(it) } }
        }
        docs.writeWhole(tree, folder, X86Library.CONFIG) { it.write(translation.config.toByteArray(Charsets.UTF_8)) }
    }

    /**
     * The Windows image [name] a DOSBox-X game runs on, unpacked into the app's storage when it is not
     * there yet: its geometry and the machine its registry (WINDOWS/SYSTEM.DAT) knows.
     */
    private fun windows(tree: Uri, game: ExoWin9x.Game, asked: String, cancelled: AtomicBoolean, progress: (String) -> Unit): ExoWin9x.Windows {
        // The image by the name the collection gives it, however the Play.conf spells it
        val name = checkNotNull(emulatorName(tree, game, ExoWin9x.parentSource(asked))) {
            "${game.name}'s collection has no ${ExoWin9x.EMULATORS_ROOT}/${ExoWin9x.parentSource(asked)}"
        }.substringAfterLast('/')
        val image = parentFile(game, name)
        if (!image.isFile) {
            progress(context.getString(FrontendR.string.kairo_disk_preparing, name))
            unpackParent(tree, game, image, cancelled)
        }
        return Vhd.open(image).use { disk ->
            val volume = FatVolume(disk)
            val hive = checkNotNull(volume.find(SYSTEM_HIVE)) { "$name has no $SYSTEM_HIVE" }
            // The Voodoo its Glide is built for (KairoX86#228), when it has Glide
            val glide = Win9xMachine.glideVoodoo(volume.find(GLIDE)?.let { volume.read(it) })
            val machine = Win9xMachine.of(Win9xRegistry.read(volume.read(hive)), glide)
            ExoWin9x.Windows(name, disk.footer.cylinders, disk.footer.heads, disk.footer.sectorsPerTrack, machine)
        }
    }

    /**
     * The files [game]'s machine needs before it starts: its own, unpacked from its ZIP into its
     * folder (checked against their size and CRC-32), and the Windows image it starts from, unpacked
     * once into the app's storage, where 86Box opens it read-only beneath each start's own disk.
     */
    fun makeDisks(tree: Uri, game: ExoWin9x.Game, cancelled: AtomicBoolean, progress: (String) -> Unit) {
        makeConfig(tree, game, cancelled, progress)
        val folder = docs.findFolder(tree, game.folder)
        gameArchive(tree, game).use { archive ->
            for (member in archive.members) {
                val name = DiskArchive.safeName(member.name).substringAfterLast('/')
                if (docs.children(tree, folder).any { it.name == name }) continue
                progress(context.getString(FrontendR.string.kairo_disk_preparing, name))
                docs.writeWhole(tree, folder, name) { output -> archive.copy(member, output) { checkCancelled(cancelled) } }
            }
        }
        val config = IniText(checkNotNull(context.contentResolver.openInputStream(docs.uri(tree,
            checkNotNull(docs.children(tree, folder).firstOrNull { it.name == X86Library.CONFIG }) { "${game.name} has no ${X86Library.CONFIG}" }.id)))
            { context.getString(R.string.machine_open_failed, X86Library.CONFIG) }.use { it.readBytes().toString(Charsets.UTF_8) })
        val parent = File(checkNotNull(config[X86Library.HARD_DISKS, "hdd_01_vhd_parent"]) { "${game.name}'s ${X86Library.CONFIG} names no Windows image" })
        if (!parent.isFile) {
            progress(context.getString(FrontendR.string.kairo_disk_preparing, parent.name))
            unpackParent(tree, game, parent, cancelled)
        }
    }

    /**
     * Makes this start's Windows disk ([ExoWin9x.CHILD] in the session folder [dir]) when [game]'s
     * Play.conf copies files into Windows before it boots (KairoX86#225): a differencing disk over
     * the Windows image holding those files, as DOSBox-X's `xcopy` would have left them, copied from
     * the game's own disk in the session. Without such copies 86Box makes the disk itself, empty.
     * Neither the Windows image nor the game's disk is written.
     */
    fun prepareStart(tree: Uri, game: ExoWin9x.Game, dir: File) {
        val (kind, text) = gameConfig(tree, game)
        if (kind != ExoWin9x.PLAY_DOSBOX_X) return
        val config = IniText(File(dir, X86Library.CONFIG).readText())
        // Each disk DOSBox-X makes of a mounted archive: a fresh child over it, as DOSBox-X keeps
        // nothing written to it (KairoX86#223)
        for (n in 2..MAX_DISKS) {
            val parentName = config[X86Library.HARD_DISKS, "hdd_%02d_vhd_parent".format(n)] ?: continue
            val childName = checkNotNull(config[X86Library.HARD_DISKS, "hdd_%02d_fn".format(n)]) { "${game.name}'s disk $n has no file" }
            val image = File(dir, parentName)
            check(image.isFile) { context.getString(FrontendR.string.kairo_disk_member_missing, parentName) }
            Vhd.open(image).use { parent -> Vhd.writeChild(File(dir, childName), parent, image, java.util.TreeMap()) }
        }
        val copies = ExoWin9x.dosboxCopies(text)
        if (copies.isEmpty()) return
        val mounts = ExoWin9x.dosboxMounts(text)
        val parentFile = File(checkNotNull(config[X86Library.HARD_DISKS, "hdd_01_vhd_parent"]) { "${game.name}'s ${X86Library.CONFIG} names no Windows image" })
        val child = File(dir, checkNotNull(config[X86Library.HARD_DISKS, "hdd_01_fn"]) { "${game.name}'s ${X86Library.CONFIG} names no Windows disk" })
        check(!child.exists()) { "${child.name} is already in ${game.name}'s session" }
        Vhd.open(parentFile).use { parent ->
            val windows = SectorChanges(parent)
            val volume = FatVolume(windows)
            for (copy in copies) {
                check(copy.targetDrive == 'c') { "${game.name}'s ${ExoWin9x.PLAY_DOSBOX_X} copies into drive ${copy.targetDrive}:, not Windows' C:" }
                val mount = checkNotNull(mounts.firstOrNull { it.drive == copy.sourceDrive }) {
                    "${game.name}'s ${ExoWin9x.PLAY_DOSBOX_X} copies from drive ${copy.sourceDrive}:, which it doesn't mount"
                }
                check(!mount.cdrom && !mount.folder) { "${game.name}'s ${ExoWin9x.PLAY_DOSBOX_X} copies from drive ${copy.sourceDrive}:, which is not a hard disk" }
                val name = mount.images.single().substringAfterLast('/')
                val image = checkNotNull(dir.listFiles().orEmpty().firstOrNull { it.name.equals(name, ignoreCase = true) && it.isFile }) {
                    context.getString(FrontendR.string.kairo_disk_member_missing, name)
                }
                Vhd.open(image).use { disk ->
                    val source = FatVolume(disk)
                    // As xcopy without /H: files only, not hidden or system ones
                    for (entry in source.list(copy.sourceFolder).filter { !it.folder && !it.hidden && (copy.matches(it.name) || it.longName?.let(copy::matches) == true) }) {
                        volume.write(copy.targetFolder, entry, source.read(entry))
                    }
                }
            }
            Vhd.writeChild(child, parent, parentFile, windows.changed)
        }
    }

    /**
     * [mounts] with each archive a drive takes made the FAT hard disk DOSBox-X makes of it at BOOT
     * (KairoX86#223, [DosboxFat]): the archive, one of the game's own, is unpacked into the machine
     * folder and its disk written beside it once as a fixed VHD named after it ("x (zip).vhd"), which
     * each start's child then sits over ([ExoWin9x.startChild]). The game's files are [members],
     * returned with the disks made.
     */
    private fun mounts(tree: Uri, game: ExoWin9x.Game, folder: String, mounts: List<ExoWin9x.Mount>,
                       members: List<String>): Pair<List<ExoWin9x.Mount>, List<String>> {
        val all = members.toMutableList()
        val made = mounts.map { mount ->
            if (!mount.folder) return@map mount
            val name = mount.images.single().substringAfterLast('/')
            check(name.endsWith(".zip", ignoreCase = true)) { context.getString(R.string.exo_folder_cd, game.name) }
            val archive = checkNotNull(members.firstOrNull { it.substringAfterLast('/').equals(name, ignoreCase = true) }) {
                context.getString(FrontendR.string.kairo_disk_member_missing, name)
            }.substringAfterLast('/')
            val disk = archive.substringBeforeLast('.') + " (zip).vhd"
            if (docs.children(tree, folder).none { it.name == disk && !it.folder }) {
                val source = unpackMember(tree, game, folder, archive, AtomicBoolean(false))
                val entries = checkNotNull(context.contentResolver.openFileDescriptor(source, "r")) {
                    context.getString(R.string.machine_open_failed, archive)
                }.use { descriptor -> ZipListing.read(FileInputStream(descriptor.fileDescriptor).channel) }
                val layout = DosboxFat.layout(entries)
                val cylinders = ((layout.sectors + 63 * 16 - 1) / (63 * 16)).toInt()
                DiskArchive.open(context, source, archive, -1).use { inner ->
                    docs.writeWhole(tree, folder, disk) { output ->
                        val buffered = java.io.BufferedOutputStream(output, 1 shl 20)
                        DosboxFat.write(layout, cylinders.toLong() * 63 * 16, buffered) { entry -> inner.open(entry.member as String) }
                        buffered.write(Vhd.fixedFooter(cylinders, 16, 63))
                        buffered.flush()
                    }
                }
            }
            all += disk
            ExoWin9x.Mount(mount.drive, listOf(disk), cdrom = false, folder = true, converted = true)
        }
        return made to all
    }

    /** The game's own file [name] in its machine folder [folder], unpacked from its ZIP when it is not there yet. */
    private fun unpackMember(tree: Uri, game: ExoWin9x.Game, folder: String, name: String, cancelled: AtomicBoolean): Uri {
        docs.children(tree, folder).firstOrNull { it.name == name && !it.folder }?.let { return docs.uri(tree, it.id) }
        return gameArchive(tree, game).use { archive ->
            val member = checkNotNull(archive.members.firstOrNull { DiskArchive.safeName(it.name).substringAfterLast('/') == name }) {
                context.getString(FrontendR.string.kairo_disk_member_missing, name)
            }
            docs.writeWhole(tree, folder, name) { output -> archive.copy(member, output) { checkCancelled(cancelled) } }
        }
    }

    /** The size in sectors of the VHD [uri], as its footer gives it (its current size, at 40 + 8). */
    private fun vhdSectors(tree: Uri, uri: Uri): Long =
        checkNotNull(context.contentResolver.openFileDescriptor(uri, "r")) { context.getString(R.string.machine_open_failed, uri.toString()) }
            .use { descriptor ->
                val channel = FileInputStream(descriptor.fileDescriptor).channel
                val footer = ByteBuffer.allocate(512)
                while (footer.hasRemaining()) check(channel.read(footer, descriptor.statSize - 512 + footer.position()) > 0) {
                    context.getString(R.string.machine_open_failed, uri.toString())
                }
                check(String(footer.array(), 0, 8, Charsets.US_ASCII) == "conectix") { "$uri has no VHD footer" }
                footer.order(java.nio.ByteOrder.BIG_ENDIAN).getLong(48) / 512
            }

    /** Where the Windows image [name] of [game]'s collection is kept, by the collection's path. */
    private fun parentFile(game: ExoWin9x.Game, name: String): File {
        val key = MessageDigest.getInstance("SHA-256").digest(game.root.toByteArray(Charsets.UTF_8))
            .take(8).joinToString("") { "%02x".format(it) }
        return File(context.filesDir, "exowin9x/$key/$name")
    }

    private fun unpackParent(tree: Uri, game: ExoWin9x.Game, target: File, cancelled: AtomicBoolean) {
        check(target.parentFile!!.isDirectory || target.parentFile!!.mkdirs()) { context.getString(R.string.machine_create_failed, target.path) }
        val partial = File(target.path + ".part")
        try {
            val (input, crc) = checkNotNull(emulatorEntry(tree, game, ExoWin9x.parentSource(target.name))) { "${game.name}'s collection has no ${target.name}" }
            input.use { source ->
                val sum = CRC32()
                partial.outputStream().use { output -> copy(source, output, sum, cancelled) }
                check(crc < 0 || sum.value == crc) { context.getString(FrontendR.string.kairo_disk_archive_checksum) }
            }
            check(partial.renameTo(target)) { context.getString(R.string.machine_create_failed, target.path) }
        } catch (failure: Exception) {
            if (partial.exists() && !partial.delete()) failure.addSuppressed(IllegalStateException("${partial.path} was left behind"))
            throw failure
        }
    }

    /** A file of eXo's emulators folder ([relative] under it), unpacked by eXo's setup or still in its archive; null when there is none. */
    private fun emulatorFile(tree: Uri, game: ExoWin9x.Game, relative: String): InputStream? = emulatorEntry(tree, game, relative)?.first

    /** The file and its CRC-32 (-1 when it comes unpacked, with none to check). */
    private fun emulatorEntry(tree: Uri, game: ExoWin9x.Game, relative: String): Pair<InputStream, Long>? {
        docs.find(tree, "${game.emulatorsFolder}/$relative")?.takeIf { !it.folder }?.let { unpacked ->
            return checkNotNull(context.contentResolver.openInputStream(docs.uri(tree, unpacked.id))) {
                context.getString(R.string.machine_open_failed, relative)
            } to -1L
        }
        val archive = EmulatorsArchive(tree, game)
        try {
            val entry = archive.zip.getEntry("${ExoWin9x.EMULATORS_ROOT}/$relative") ?: run {
                archive.close()
                return null
            }
            val stream = archive.zip.getInputStream(entry)
            return object : java.io.FilterInputStream(stream) {
                override fun close() {
                    try { super.close() } finally { archive.close() }
                }
            } to entry.crc
        } catch (failure: Exception) {
            try { archive.close() } catch (cleanup: Exception) { failure.addSuppressed(cleanup) }
            throw failure
        }
    }

    /**
     * [relative] as eXo's emulators folder spells it, whatever the case it is asked in, or null when
     * the folder has no such file: a Play.conf names the files of its DOS drives as DOSBox-X finds
     * them, case aside ("win98jap.vhd" for `win98Jap.vhd`).
     */
    private fun emulatorName(tree: Uri, game: ExoWin9x.Game, relative: String): String? {
        docs.find(tree, game.emulatorsFolder)?.takeIf { it.folder }?.let { root ->
            var id = root.id
            val names = ArrayList<String>()
            for (part in relative.split('/')) {
                val child = docs.children(tree, id).firstOrNull { it.name.equals(part, ignoreCase = true) } ?: break
                names += child.name
                id = child.id
            }
            if (names.size == relative.split('/').size) return names.joinToString("/")
        }
        return EmulatorsArchive(tree, game).use { archive ->
            archive.zip.entries.asSequence().map { it.name }
                .firstOrNull { it.equals("${ExoWin9x.EMULATORS_ROOT}/$relative", ignoreCase = true) }
                ?.removePrefix("${ExoWin9x.EMULATORS_ROOT}/")
        }
    }

    /** eXo's emulators archive ([ExoWin9x.EMULATORS]), read where it lies: stored in utilWin9x.zip, nothing unpacked. */
    private inner class EmulatorsArchive(tree: Uri, game: ExoWin9x.Game) : AutoCloseable {
        private val descriptor = run {
            val util = docs.find(tree, game.utilArchive)?.takeIf { !it.folder } ?: error("${game.name}'s collection has no ${ExoWin9x.UTIL}")
            checkNotNull(context.contentResolver.openFileDescriptor(docs.uri(tree, util.id), "r")) {
                context.getString(R.string.machine_open_failed, ExoWin9x.UTIL)
            }
        }
        private val outer: ZipFile
        val zip: ZipFile

        init {
            try {
                val channel = FileInputStream(descriptor.fileDescriptor).channel
                outer = ZipFile.builder().setSeekableByteChannel(channel).get()
                try {
                    val emulators = checkNotNull(outer.getEntry(ExoWin9x.EMULATORS)) { "${ExoWin9x.UTIL} has no ${ExoWin9x.EMULATORS}" }
                    check(emulators.method == ZipArchiveEntry.STORED) { "${ExoWin9x.EMULATORS} is compressed in ${ExoWin9x.UTIL}" }
                    zip = ZipFile.builder().setSeekableByteChannel(RangeChannel(channel, emulators.dataOffset, emulators.size)).get()
                } catch (failure: Exception) {
                    try { outer.close() } catch (cleanup: Exception) { failure.addSuppressed(cleanup) }
                    throw failure
                }
            } catch (failure: Exception) {
                try { descriptor.close() } catch (cleanup: Exception) { failure.addSuppressed(cleanup) }
                throw failure
            }
        }

        override fun close() {
            try { zip.close() } finally { try { outer.close() } finally { descriptor.close() } }
        }
    }

    /**
     * [game]'s configuration, unpacked by eXo's setup or still in the metadata archive: its name
     * (Play.cfg for 86Box, Play.conf for DOSBox-X) and its text.
     */
    private fun gameConfig(tree: Uri, game: ExoWin9x.Game): Pair<String, String> {
        for (name in listOf(ExoWin9x.PLAY_86BOX, ExoWin9x.PLAY_DOSBOX_X)) {
            docs.find(tree, "${game.metadataPath}/$name")?.takeIf { !it.folder }?.let { file ->
                return name to checkNotNull(context.contentResolver.openInputStream(docs.uri(tree, file.id))) {
                    context.getString(R.string.machine_open_failed, name)
                }.use { it.readBytes().toString(Charsets.UTF_8) }
            }
        }
        val metadata = docs.find(tree, game.metadataArchive)?.takeIf { !it.folder } ?: error("${game.name}'s collection has no ${ExoWin9x.METADATA}")
        checkNotNull(context.contentResolver.openFileDescriptor(docs.uri(tree, metadata.id), "r")) {
            context.getString(R.string.machine_open_failed, ExoWin9x.METADATA)
        }.use { descriptor ->
            ZipFile.builder().setSeekableByteChannel(FileInputStream(descriptor.fileDescriptor).channel).get().use { zip ->
                for (name in listOf(ExoWin9x.PLAY_86BOX, ExoWin9x.PLAY_DOSBOX_X)) {
                    val entry = zip.getEntry("${game.metadataFolder}/$name") ?: zip.getEntry("eXo/${game.metadataFolder}/$name") ?: continue
                    return name to zip.getInputStream(entry).use { it.readBytes().toString(Charsets.UTF_8) }
                }
                error("${ExoWin9x.METADATA} has no configuration for ${game.name}")
            }
        }
    }

    private fun gameArchive(tree: Uri, game: ExoWin9x.Game): DiskArchive {
        val zip = docs.find(tree, game.zipPath)?.takeIf { !it.folder } ?: error(context.getString(R.string.machine_folder_missing, game.zipPath))
        val uri = docs.uri(tree, zip.id)
        val size = checkNotNull(context.contentResolver.query(uri, arrayOf(Document.COLUMN_SIZE), null, null, null)) {
            context.getString(R.string.machine_open_failed, game.zipPath)
        }.use { cursor -> check(cursor.moveToFirst()) { context.getString(R.string.machine_open_failed, game.zipPath) }; cursor.getLong(0) }
        return DiskArchive.open(context, uri, game.zipPath, size)
    }

    private fun copy(input: InputStream, output: OutputStream, sum: CRC32, cancelled: AtomicBoolean) {
        val buffer = ByteArray(1 shl 16)
        while (true) {
            checkCancelled(cancelled)
            val read = input.read(buffer)
            if (read < 0) break
            sum.update(buffer, 0, read)
            output.write(buffer, 0, read)
        }
    }

    private fun checkCancelled(cancelled: AtomicBoolean) {
        if (cancelled.get()) throw CancellationException("Cancelled")
    }

    /** The bytes [offset] to [offset] + [length] of [channel], as a channel of their own, read-only. */
    private class RangeChannel(private val channel: FileChannel, private val offset: Long, private val length: Long) : SeekableByteChannel {
        private var position = 0L
        private var open = true

        override fun read(dst: ByteBuffer): Int {
            if (position >= length) return -1
            val limit = dst.limit()
            if (dst.remaining() > length - position) dst.limit(dst.position() + (length - position).toInt())
            try {
                val read = channel.read(dst, offset + position)
                if (read > 0) position += read
                return read
            } finally {
                dst.limit(limit)
            }
        }

        override fun write(src: ByteBuffer): Int = throw NonWritableChannelException()
        override fun position(): Long = position
        override fun position(newPosition: Long): SeekableByteChannel = apply {
            require(newPosition >= 0) { "Negative position $newPosition" }
            position = newPosition
        }
        override fun size(): Long = length
        override fun truncate(size: Long): SeekableByteChannel = throw NonWritableChannelException()
        override fun isOpen(): Boolean = open
        override fun close() { open = false }
    }

    private companion object {
        /** 86Box's hard disk count (HDD_NUM). */
        const val MAX_DISKS = 88
        /** The registry hive of an installed Windows 9x that holds what it knows of the hardware. */
        const val SYSTEM_HIVE = "WINDOWS/SYSTEM.DAT"
        /** 3dfx's Glide 2 in an installed Windows 9x, built for one Voodoo ([Win9xMachine.glideVoodoo]). */
        const val GLIDE = "WINDOWS/SYSTEM/GLIDE2X.DLL"
    }
}
