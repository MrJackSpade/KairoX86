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
    /** The machine folder of [game], with its 86box.cfg and CMOS, made when it is missing. */
    fun makeConfig(tree: Uri, game: ExoWin9x.Game) {
        val folder = docs.makeFolders(tree, game.folder)
        if (docs.children(tree, folder).any { it.name == X86Library.CONFIG && !it.folder }) return
        val members = gameArchive(tree, game).use { archive -> archive.members.map { it.name } }
        val (kind, text) = gameConfig(tree, game)
        val translation = if (kind == ExoWin9x.PLAY_86BOX) {
            ExoWin9x.translate(text, members) { parent -> parentFile(game, parent).absolutePath }
        } else {
            // A DOSBox-X game runs on eXo's 86Box machine and Windows (KairoX86#219)
            val windows = ExoWin9x.dosboxWindows(text)
            check(windows == null || windows.lowercase() in ExoWin9x.DOSBOX_ENGLISH_98) {
                context.getString(R.string.exo_windows_unsupported, game.name, windows)
            }
            val mounts = ExoWin9x.dosboxMounts(text)
            check(mounts.none { it.folder }) { context.getString(R.string.exo_folder_cd, game.name) }
            val template = checkNotNull(emulatorFile(tree, game, ExoWin9x.EMULATOR_CONFIG)) {
                "${game.name}'s collection has no ${ExoWin9x.EMULATOR_FOLDER}/${ExoWin9x.EMULATOR_CONFIG}"
            }.use { it.readBytes().toString(Charsets.UTF_8) }
            ExoWin9x.translateDosbox(template, mounts, members, { parent -> parentFile(game, parent).absolutePath }) { disk ->
                // A hard disk's geometry comes from its size: it is unpacked now, as its start would
                vhdSectors(tree, unpackMember(tree, game, folder, disk, AtomicBoolean(false)))
            }
        }
        val nvr = docs.makeFolders(tree, "${game.folder}/${X86Library.NVR}")
        for (name in listOf("${translation.machine}.nvr", "${translation.machine}.bin")) {
            if (docs.children(tree, nvr).any { it.name == name }) continue
            emulatorFile(tree, game, "nvr/$name")?.use { input -> docs.writeWhole(tree, nvr, name) { input.copyTo(it) } }
        }
        docs.writeWhole(tree, folder, X86Library.CONFIG) { it.write(translation.config.toByteArray(Charsets.UTF_8)) }
    }

    /**
     * The files [game]'s machine needs before it starts: its own, unpacked from its ZIP into its
     * folder (checked against their size and CRC-32), and the Windows image it starts from, unpacked
     * once into the app's storage, where 86Box opens it read-only beneath each start's own disk.
     */
    fun makeDisks(tree: Uri, game: ExoWin9x.Game, cancelled: AtomicBoolean, progress: (String) -> Unit) {
        makeConfig(tree, game)
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
            val (input, crc) = checkNotNull(emulatorEntry(tree, game, "parent/${target.name}")) { "${game.name}'s collection has no ${target.name}" }
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

    /** A file of eXo's 86Box folder ([relative] under it), unpacked by eXo's setup or still in its archive; null when there is none. */
    private fun emulatorFile(tree: Uri, game: ExoWin9x.Game, relative: String): InputStream? = emulatorEntry(tree, game, relative)?.first

    /** The file and its CRC-32 (-1 when it comes unpacked, with none to check). */
    private fun emulatorEntry(tree: Uri, game: ExoWin9x.Game, relative: String): Pair<InputStream, Long>? {
        docs.find(tree, "${game.emulatorFolder}/$relative")?.takeIf { !it.folder }?.let { unpacked ->
            return checkNotNull(context.contentResolver.openInputStream(docs.uri(tree, unpacked.id))) {
                context.getString(R.string.machine_open_failed, relative)
            } to -1L
        }
        val util = docs.find(tree, game.utilArchive)?.takeIf { !it.folder } ?: error("${game.name}'s collection has no ${ExoWin9x.UTIL}")
        val descriptor = checkNotNull(context.contentResolver.openFileDescriptor(docs.uri(tree, util.id), "r")) {
            context.getString(R.string.machine_open_failed, ExoWin9x.UTIL)
        }
        try {
            val channel = FileInputStream(descriptor.fileDescriptor).channel
            val outer = ZipFile.builder().setSeekableByteChannel(channel).get()
            // EXTWin9x.zip is stored in utilWin9x.zip: it is read where it lies, nothing unpacked
            val emulators = checkNotNull(outer.getEntry(ExoWin9x.EMULATORS)) { "${ExoWin9x.UTIL} has no ${ExoWin9x.EMULATORS}" }
            check(emulators.method == ZipArchiveEntry.STORED) { "${ExoWin9x.EMULATORS} is compressed in ${ExoWin9x.UTIL}" }
            val inner = ZipFile.builder().setSeekableByteChannel(RangeChannel(channel, emulators.dataOffset, emulators.size)).get()
            val entry = inner.getEntry("${ExoWin9x.EMULATOR_FOLDER}/$relative") ?: run {
                inner.close(); outer.close(); descriptor.close()
                return null
            }
            val stream = inner.getInputStream(entry)
            return object : java.io.FilterInputStream(stream) {
                override fun close() {
                    try { super.close() } finally { try { inner.close() } finally { try { outer.close() } finally { descriptor.close() } } }
                }
            } to entry.crc
        } catch (failure: Exception) {
            try { descriptor.close() } catch (cleanup: Exception) { failure.addSuppressed(cleanup) }
            throw failure
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
}
