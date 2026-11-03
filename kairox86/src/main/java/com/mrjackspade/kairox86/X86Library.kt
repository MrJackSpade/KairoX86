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
import com.mrjackspade.kairo.frontend.ScanDepth
import com.mrjackspade.kairo.frontend.UiText
import com.mrjackspade.kairo.frontend.VersionedLibraryCache
import java.io.DataInputStream
import java.io.DataOutputStream
import java.io.File
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicBoolean

/**
 * A machine of the library: a folder of the games folder holding an 86Box machine's 86box.cfg (its
 * hardware), the disk images it names and its nvr/ (CMOS). The entry is the folder, named after it
 * and keyed by its path, so its saves and settings follow it; its content ID is its 86box.cfg's.
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
    override val member: String? = null
) : LibraryItem {
    override val zipEntry: String? = null
    override val displayName: String get() = path.substringAfterLast('/').ifEmpty { "86Box" }
    override val playable: Boolean get() = contentId != null && error == null
    override val mediaLabel: UiText get() = UiText.res(R.string.media_machine)
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
        val session = Session(tree, folder, dir)
        try {
            session.fill(folder, dir, "", cancelled)
            check(File(dir, CONFIG).isFile) { context.getString(R.string.machine_config_missing, entry.displayName) }
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
    inner class Session(private val tree: Uri, private val folder: String, val dir: File) : AutoCloseable {
        private val open = ArrayList<ParcelFileDescriptor>()

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
            writeFile(folder, File(dir, CONFIG), CONFIG)
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
        }
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

    companion object {
        const val CONFIG = "86box.cfg"
        const val NVR = "nvr"

        /** The folder of the 86box.cfg at [path]. */
        fun folderOf(path: String) = path.substringBeforeLast('/', "")

        /** The files 86Box rewrites, copied into the session and back: its configuration and CMOS. */
        private fun copied(path: String) = path.equals(CONFIG, ignoreCase = true) || path.startsWith("$NVR/")

        fun contentIdOf(bytes: ByteArray): String = "sha256-vm-v1:" +
            MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
    }
}
