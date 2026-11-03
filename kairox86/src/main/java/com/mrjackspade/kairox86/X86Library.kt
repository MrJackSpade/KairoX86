package com.mrjackspade.kairox86

import android.content.Context
import android.net.Uri
import android.os.ParcelFileDescriptor
import android.provider.DocumentsContract
import android.provider.DocumentsContract.Document
import android.system.Os
import com.mrjackspade.kairo.frontend.DocumentTreeWalker
import com.mrjackspade.kairo.frontend.GameKey
import com.mrjackspade.kairo.frontend.LibraryItem
import com.mrjackspade.kairo.frontend.LibraryScanPipeline
import com.mrjackspade.kairo.frontend.MissingDisk
import com.mrjackspade.kairo.frontend.R as FrontendR
import com.mrjackspade.kairo.frontend.ScanDepth
import com.mrjackspade.kairo.frontend.UiText
import com.mrjackspade.kairo.frontend.VersionedLibraryCache
import com.mrjackspade.kairo.frontend.missingDisk
import java.io.DataInputStream
import java.io.DataOutputStream
import java.io.File
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicBoolean

/**
 * A machine of the library: a folder of the games folder holding an 86Box machine's 86box.cfg (its
 * hardware), the disk images it names and its nvr/ (CMOS). The entry is the folder, named after it
 * and keyed by its path, so its saves and settings follow it; its content ID is its 86box.cfg's.
 *
 * With [disk], a disk image a drive takes while a machine runs (the Disks page, KairoX86#48): one of
 * the running machine's folder ([uri] its file in the session folder) or one picked on the device
 * ([uri] its document). The library lists machines only.
 */
data class X86Entry(
    override val id: String,
    /** The 86box.cfg document. */
    override val uri: String,
    /** The folder's path in the games folder ("" for the games folder itself). */
    override val path: String,
    val size: Long,
    val modified: Long,
    override val contentId: String?,
    override val error: String? = null,
    override val catalogId: String? = contentId,
    override val member: String? = null,
    val disk: Boolean = false
) : LibraryItem {
    override val zipEntry: String? = null
    override val displayName: String get() = path.substringAfterLast('/').ifEmpty { "86Box" }
    override val playable: Boolean get() = contentId != null && error == null
    override val mediaLabel: UiText get() = UiText.res(if (disk) R.string.media_disk else R.string.media_machine)
}

/**
 * The machine folders in the games folder, and the session folder a machine runs from: the
 * machine's 86box.cfg and nvr/ copied in (86Box rewrites them), and every other file of the folder
 * opened in place and reached through a link, so the disks are read and written where they are and
 * nothing is copied but the small files, which [Session.writeBack] returns to the folder.
 */
class X86Library(private val context: Context) {
    private val walker = DocumentTreeWalker(context)
    private val cache = VersionedLibraryCache(File(context.filesDir, "library-v1.bin"), 1, 8 * 1024 * 1024, 100_000,
        ::writeEntry, ::readEntry)
    private val pipeline = LibraryScanPipeline<DocumentTreeWalker.FileEntry, X86Entry>(context, cache,
        entryId = { it.id },
        enumerate = { tree, depth, cancelled, progress ->
            LibraryScanPipeline.Plan(walker.scan(tree, cancelled, { it.equals(CONFIG, ignoreCase = true) }, progress,
                depth = depth).files)
        },
        inspect = { file, scan -> listOf(inspect(file, scan)) },
        failed = { file, _, error -> listOf(entryOf(file, null, error.message ?: "Unreadable")) },
        describe = { it.path },
        known = { file, scan -> scan.prior[folderOf(file.path)]?.let { it.size == file.size && it.modified == file.modified } == true },
        sourceOf = { it.uri },
        displayOrder = { entries -> entries.sortedBy { it.displayName.lowercase() } })

    val hashCount: Int get() = pipeline.hashCount
    fun cached(tree: Uri): List<X86Entry> = pipeline.cached(tree)
    fun scan(tree: Uri, depth: ScanDepth, cancelled: AtomicBoolean, progress: (String) -> Unit): List<X86Entry> =
        pipeline.scan(tree, depth, cancelled, progress)
    fun store(tree: Uri, entries: List<X86Entry>) = pipeline.store(tree, entries)

    private fun inspect(file: DocumentTreeWalker.FileEntry, scan: LibraryScanPipeline.ScanContext<X86Entry>): X86Entry {
        scan.prior[folderOf(file.path)]?.let { prior ->
            if (!scan.forceHash && prior.size == file.size && prior.modified == file.modified) return prior
        }
        scan.hashStarted(file.path)
        val bytes = checkNotNull(context.contentResolver.openInputStream(file.uri)) { "Unable to open ${file.path}" }
            .use { it.readBytes() }
        return entryOf(file, contentIdOf(bytes), null)
    }

    private fun entryOf(file: DocumentTreeWalker.FileEntry, contentId: String?, error: String?) =
        X86Entry(folderOf(file.path), file.uri.toString(), folderOf(file.path), file.size, file.modified, contentId, error)

    /**
     * Prepares [entry]'s session folder from its folder in [tree] and returns the session, whose
     * folder 86Box runs (`-P`).
     */
    fun prepare(entry: X86Entry, tree: Uri, cancelled: AtomicBoolean): Session {
        val folder = findFolder(tree, entry.path)
        val dir = File(context.filesDir, "session/${GameKey(entry.id).hashName}")
        check(!dir.exists() || dir.deleteRecursively()) { "Could not clear the session folder" }
        check(dir.mkdirs()) { "Could not create the session folder" }
        val media = File(context.filesDir, "session-media/${dir.name}")
        check(!media.exists() || media.deleteRecursively()) { "Could not clear the session's media folder" }
        val session = Session(entry.id, tree, folder, dir, media)
        try {
            session.fill(folder, dir, "", cancelled)
            check(File(dir, CONFIG).isFile) { context.getString(R.string.machine_config_missing, entry.displayName) }
            // A disk its 86box.cfg names that is not in its folder (KairoX86#63): 86Box would start with the drive empty.
            missingMedium(IniText(File(dir, CONFIG).readText())) { path -> File(dir, path).isFile }
                ?.let { throw MissingDisk(missingDisk(it)) }
        } catch (failure: Exception) {
            session.close()
            throw failure
        }
        return session
    }

    /** The document ID of the folder [path] in [tree], by name from its root. */
    private fun findFolder(tree: Uri, path: String): String {
        var id = DocumentsContract.getTreeDocumentId(tree)
        for (name in path.split('/').filter { it.isNotEmpty() }) {
            id = children(tree, id).firstOrNull { it.name == name && it.folder }?.id
                ?: error(context.getString(R.string.machine_folder_missing, path))
        }
        return id
    }

    private data class Child(val id: String, val name: String, val folder: Boolean)

    private fun children(tree: Uri, parent: String): List<Child> {
        val query = DocumentsContract.buildChildDocumentsUriUsingTree(tree, parent)
        return checkNotNull(context.contentResolver.query(query,
            arrayOf(Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME, Document.COLUMN_MIME_TYPE), null, null, null)) {
            "Could not list a folder of the games folder"
        }.use { cursor ->
            buildList { while (cursor.moveToNext()) add(Child(cursor.getString(0), cursor.getString(1), cursor.getString(2) == Document.MIME_TYPE_DIR)) }
        }
    }

    /**
     * A machine's session: its folder in the games folder ([folder]), the session folder 86Box runs
     * ([dir]), and the files of the folder held open for it.
     */
    inner class Session(val entryId: String, private val tree: Uri, private val folder: String, val dir: File,
                        private val media: File) : AutoCloseable {
        private val open = ArrayList<ParcelFileDescriptor>()
        /** Settings changed while the machine runs (Kairo#142), put back over what 86Box saves as it ends. */
        private val edits = LinkedHashMap<Pair<String, String>, String?>()

        /** A setting the player changed while this machine runs: 86Box saves its own when it ends, then this goes over it. */
        @Synchronized fun edit(section: String, key: String, value: String?) {
            edits[section to key] = value
        }

        /**
         * The disk images of the machine's folder (the Disks page's own disks), each by its file in
         * this session folder, which is the folder's own file opened in place.
         */
        fun disks(): List<X86Entry> = dir.walkTopDown().filter { it.isFile && diskKind(it.name) != null }
            .map { file ->
                val path = file.relativeTo(dir).invariantSeparatorsPath
                X86Entry("disk:$path", file.absolutePath, path, 0, 0, DISK, disk = true)
            }.sortedBy { it.path.lowercase() }.toList()

        /** The machine's disk the session folder's [path] is, as a drive reports it; null for any other. */
        fun diskAt(path: String): X86Entry? = disks().firstOrNull { File(it.uri).absolutePath == File(path).absolutePath }

        /**
         * A disk picked on the device, opened in place and reached through a link outside this
         * session folder: 86Box holds it for this run only and keeps the machine's own disk in its
         * configuration (KairoX86#48).
         */
        fun link(entry: X86Entry): File {
            val kind = checkNotNull(diskKind(entry.path)) { "${entry.path} is no disk image" }
            check(media.isDirectory || media.mkdirs()) { "Could not create the session's media folder" }
            val file = File(media, "${open.size}-${entry.path.substringAfterLast('/')}")
            // A floppy may be written, as on the PC; a CD only read.
            val descriptor = checkNotNull(context.contentResolver.openFileDescriptor(Uri.parse(entry.uri),
                if (kind == DiskKind.FLOPPY) "rw" else "r")) { "Unable to open ${entry.path}" }
            open += descriptor
            Os.symlink("/proc/self/fd/${descriptor.fd}", file.path)
            return file
        }

        /** Copies the small files 86Box rewrites and links every other file, in [source]'s folder at [relative]. */
        fun fill(source: String, target: File, relative: String, cancelled: AtomicBoolean) {
            for (child in children(tree, source)) {
                if (cancelled.get()) throw java.util.concurrent.CancellationException("Cancelled")
                val path = if (relative.isEmpty()) child.name else "$relative/${child.name}"
                val file = File(target, child.name)
                require(file.canonicalPath.startsWith(dir.canonicalPath + File.separator)) { "Unsafe file name ${child.name}" }
                val uri = DocumentsContract.buildDocumentUriUsingTree(tree, child.id)
                when {
                    child.folder -> {
                        check(file.mkdirs()) { "Could not create ${file.path}" }
                        fill(child.id, file, path, cancelled)
                    }
                    copied(path) -> checkNotNull(context.contentResolver.openInputStream(uri)) { "Unable to open $path" }
                        .use { input -> file.outputStream().use { input.copyTo(it) } }
                    else -> {
                        // The file opened in place, for reading and writing (its disk may be written).
                        val descriptor = checkNotNull(context.contentResolver.openFileDescriptor(uri, "rw")) { "Unable to open $path" }
                        open += descriptor
                        Os.symlink("/proc/self/fd/${descriptor.fd}", file.path)
                    }
                }
            }
        }

        /** Returns 86box.cfg and nvr/ to the machine's folder, as 86Box left them. */
        fun writeBack() {
            val config = File(dir, CONFIG)
            synchronized(this) {
                if (edits.isNotEmpty() && config.isFile) {
                    val text = IniText(config.readText())
                    for ((at, value) in edits) text[at.first, at.second] = value
                    config.writeText(text.toString())
                }
            }
            writeFile(folder, config, CONFIG)
            val nvr = File(dir, NVR)
            if (!nvr.isDirectory) return
            val nvrFolder = children(tree, folder).firstOrNull { it.name == NVR && it.folder }?.id
                ?: DocumentsContract.createDocument(context.contentResolver, DocumentsContract.buildDocumentUriUsingTree(tree, folder),
                    Document.MIME_TYPE_DIR, NVR)?.let(DocumentsContract::getDocumentId)
                ?: error("Could not create nvr/ in the machine's folder")
            for (file in nvr.listFiles().orEmpty().filter { it.isFile }) writeFile(nvrFolder, file, file.name)
        }

        private fun writeFile(parent: String, file: File, name: String) {
            if (!file.isFile) return
            val existing = children(tree, parent).firstOrNull { it.name == name && !it.folder }
            val uri = existing?.let { DocumentsContract.buildDocumentUriUsingTree(tree, it.id) }
                ?: DocumentsContract.createDocument(context.contentResolver, DocumentsContract.buildDocumentUriUsingTree(tree, parent),
                    "application/octet-stream", name)
                ?: error("Could not create $name in the machine's folder")
            checkNotNull(context.contentResolver.openOutputStream(uri, "wt")) { "Could not write $name" }
                .use { output -> file.inputStream().use { it.copyTo(output) } }
        }

        override fun close() {
            open.forEach(ParcelFileDescriptor::close)
            open.clear()
            media.deleteRecursively()
        }
    }

    /** The machine folder's 86box.cfg (Kairo#142), as it is now. */
    fun config(entry: X86Entry, tree: Uri): IniText = IniText(readConfig(tree, entry))

    /** Makes [changes] to the machine folder's 86box.cfg (Kairo#142): each key set, or removed for null. */
    fun change(entry: X86Entry, tree: Uri, changes: List<X86Settings.Change>) {
        val text = config(entry, tree)
        for (change in changes) text[change.section, change.key] = change.value
        val uri = configUri(tree, entry)
        checkNotNull(context.contentResolver.openOutputStream(uri, "wt")) { "Could not write ${entry.path}/$CONFIG" }
            .use { it.write(text.toString().toByteArray(Charsets.UTF_8)) }
    }

    private fun configUri(tree: Uri, entry: X86Entry): Uri {
        val folder = findFolder(tree, entry.path)
        val config = children(tree, folder).firstOrNull { !it.folder && it.name.equals(CONFIG, ignoreCase = true) }
            ?: error(context.getString(R.string.machine_config_missing, entry.displayName))
        return DocumentsContract.buildDocumentUriUsingTree(tree, config.id)
    }

    private fun readConfig(tree: Uri, entry: X86Entry): String =
        checkNotNull(context.contentResolver.openInputStream(configUri(tree, entry))) { "Unable to open ${entry.path}/$CONFIG" }
            .use { it.readBytes().toString(Charsets.UTF_8) }

    /** A disk image picked on the device (MachineLibrary.inspectExternal), for a drive. */
    fun pickedDisk(uri: Uri, name: String, size: Long, modified: Long): X86Entry {
        checkNotNull(diskKind(name)) { context.getString(R.string.machine_not_disk, name) }
        return X86Entry("disk-picked:$uri", uri.toString(), name, size, modified, DISK, disk = true)
    }

    private fun writeEntry(output: DataOutputStream, entry: X86Entry) {
        output.writeUTF(entry.id)
        output.writeUTF(entry.uri)
        output.writeUTF(entry.path)
        output.writeLong(entry.size)
        output.writeLong(entry.modified)
        output.writeUTF(entry.contentId ?: "")
        output.writeUTF(entry.error ?: "")
    }

    private fun readEntry(input: DataInputStream) = X86Entry(input.readUTF(), input.readUTF(), input.readUTF(),
        input.readLong(), input.readLong(), input.readUTF().ifEmpty { null }, input.readUTF().ifEmpty { null })

    /** A drive's kind of disk image. */
    enum class DiskKind { FLOPPY, CD }

    companion object {
        const val CONFIG = "86box.cfg"
        const val NVR = "nvr"
        /** A disk entry's content ID: disks are no games of the catalog. */
        private const val DISK = "disk"

        /** The floppy and CD images 86Box reads, by extension. */
        private val FLOPPY_IMAGES = setOf("img", "ima", "dsk", "flp", "vfd", "xdf", "86f", "td0", "imd", "mfm", "fdi", "fdf")
        private val CD_IMAGES = setOf("iso", "cue", "chd", "mds", "ccd")

        /** What a drive takes a file named [name] as, or null for no disk image. */
        fun diskKind(name: String): DiskKind? = when (name.substringAfterLast('.', "").lowercase()) {
            in FLOPPY_IMAGES -> DiskKind.FLOPPY
            in CD_IMAGES -> DiskKind.CD
            else -> null
        }

        /** A medium 86box.cfg names: the keys that name it in its section, and what the player calls it. */
        private class Medium(val section: String, val key: Regex, val label: UiText)

        private val MEDIA = listOf(
            Medium("Floppy and CD-ROM drives", Regex("fdd_\\d+_fn"), UiText.res(FrontendR.string.kairo_floppy_disk)),
            Medium("Floppy and CD-ROM drives", Regex("cdrom_\\d+_image_path"), UiText.res(FrontendR.string.kairo_companion_cd)),
            Medium("Hard disks", Regex("hdd_\\d+_fn"), UiText.res(FrontendR.string.kairo_hard_disk)),
            Medium("Other removable devices", Regex("(zip|mo|rdisk)_\\d+_image_path"), UiText.res(R.string.media_removable_disk)),
            Medium("Other removable devices", Regex("tape_\\d+_image_path"), UiText.res(R.string.media_tape)),
            Medium("Storage controllers", Regex("cartridge_\\d+_fn"), UiText.res(FrontendR.string.kairo_cartridge)))

        /**
         * The first medium [config] names that its machine's folder lacks, by what the player calls it
         * (KairoX86#63); null when the folder has them all. [inFolder] says whether the folder has a
         * file at a relative path. The session holds the machine's folder alone, so a medium only
         * its folder can give: one at a path 86Box reads relative to it (write-protected or not), and
         * never a host drive (ioctl://), a path above it (../), beside 86Box (<exe_path>/) or absolute.
         */
        fun missingMedium(config: IniText, inFolder: (String) -> Boolean): UiText? = MEDIA.firstNotNullOfOrNull { medium ->
            medium.label.takeIf {
                config.entries(medium.section).any { (key, value) ->
                    medium.key.matches(key) && value.isNotEmpty() && !folderHas(value.removePrefix("wp://"), inFolder)
                }
            }
        }

        private fun folderHas(value: String, inFolder: (String) -> Boolean): Boolean {
            val path = value.replace('\\', '/')
            val outside = path.startsWith("ioctl://") || path.startsWith("<exe_path>/") || path.startsWith("/") ||
                Regex("^[A-Za-z]:").containsMatchIn(path) || path.split('/').contains("..")
            return !outside && inFolder(path)
        }

        /** The folder of the 86box.cfg at [path]. */
        fun folderOf(path: String) = path.substringBeforeLast('/', "")

        /** The files 86Box rewrites, copied into the session and back: its configuration and CMOS. */
        private fun copied(path: String) = path.equals(CONFIG, ignoreCase = true) || path.startsWith("$NVR/")

        fun contentIdOf(bytes: ByteArray): String = "sha256-vm-v1:" +
            MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
    }
}
