package com.mrjackspade.kairox86

import android.content.Context
import android.net.Uri
import android.os.ParcelFileDescriptor
import android.provider.DocumentsContract
import android.provider.DocumentsContract.Document
import android.system.Os
import com.mrjackspade.kairo.frontend.DiskArchive
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
 * ([uri] its document), or one the library scan found in the games folder ([X86Library.disks], [uri]
 * its document). A disk image inside a ZIP or 7z archive ([zipEntry], KairoX86#217) has the archive
 * as its [uri] and [path]; a drive takes it once it is unpacked into the running machine's folder
 * ([X86Library.Session.unpack]). The scan also keeps an entry for each archive itself, which no drive
 * takes, so an archive it has read is not read again. The library lists machines only.
 */
data class X86Entry(
    override val id: String,
    /** The 86box.cfg document; for a disk, its document, or its archive's. */
    override val uri: String,
    /** The folder's path in the games folder ("" for the games folder itself); for a disk, its file's, or its archive's. */
    override val path: String,
    /** The document's size and modification time; for a disk in an archive, the archive's. */
    val size: Long,
    val modified: Long,
    override val contentId: String?,
    override val error: String? = null,
    override val catalogId: String? = contentId,
    override val member: String? = null,
    val disk: Boolean = false,
    /** The disk image's path inside its archive, or null for any other entry. */
    override val zipEntry: String? = null,
    /**
     * An eXoWin9x game (KairoX86#219, [ExoWin9x]): [uri] is its ZIP's document, and [path] the
     * machine folder KairoX86 makes for it in the collection, where its machine runs from.
     */
    val exo: Boolean = false
) : LibraryItem {
    /** The disk image's own file name, by which a drive takes it: its member's in an archive. */
    val diskName: String get() = zipEntry ?: path
    override val displayName: String get() = (zipEntry ?: path).substringAfterLast('/').ifEmpty { "86Box" }
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
    private val docs = X86Documents(context)
    /** eXoWin9x games' machine folders (KairoX86#219). */
    private val exoBuilder = X86Exo(context, docs)
    // Version 2 keeps the games folder's disk images beside the machines (KairoX86#209); version 3
    // each machine's first catalog ID (KairoX86#213); version 4 the disk images inside archives (KairoX86#217);
    // version 5 eXoWin9x games (KairoX86#219).
    private val cache = VersionedLibraryCache(File(context.filesDir, "library-v1.bin"), 5, 8 * 1024 * 1024, 100_000,
        ::writeEntry, ::readEntry, earlierRecords = mapOf(3 to ::readEntryV3, 4 to ::readEntryV4))
    private val pipeline = LibraryScanPipeline<DocumentTreeWalker.FileEntry, X86Entry>(context, cache,
        entryId = { it.id },
        enumerate = { tree, depth, cancelled, progress ->
            // The walk finds the disk images too, unread: a drive's Other choice (KairoX86#209). An
            // archive is read for the images in it (KairoX86#217).
            val files = walker.scan(tree, cancelled, { isConfig(it) || diskKind(it) != null || DiskArchive.isArchive(it) },
                progress, depth = depth).files
            val (images, work) = files.partition { diskKind(it.path) != null }
            LibraryScanPipeline.Plan(work, finalEntries = images.map { file ->
                X86Entry(file.path, file.uri.toString(), file.path, file.size, file.modified, DISK, disk = true)
            })
        },
        inspect = { file, scan ->
            val exo = ExoWin9x.game(file.path)
            when {
                // An eXoWin9x game's machine folder (KairoX86#219): its game's entry is the library's
                isConfig(file.path) -> if (ExoWin9x.isMachineFolder(file.path)) emptyList() else listOf(inspect(file, scan))
                exo != null -> listOf(exoEntry(file, exo))
                ExoWin9x.isCollectionFile(file.path) -> emptyList()
                else -> inspectArchive(file, scan)
            }
        },
        failed = { file, scan, error ->
            val message = error.message ?: "Unreadable"
            val exo = ExoWin9x.game(file.path)
            when {
                isConfig(file.path) -> listOf(entryOf(file, null, message, scan.earlier[folderOf(file.path)]?.catalogId))
                exo != null -> listOf(exoEntry(file, exo).copy(error = message))
                else -> listOf(archiveOf(file, message))
            }
        },
        describe = { it.path },
        known = { file, scan -> when {
            isConfig(file.path) -> scan.prior[folderOf(file.path)]?.let { it.size == file.size && it.modified == file.modified } == true
            // Nothing is read for a collection's files: they are listed afresh
            ExoWin9x.game(file.path) != null || ExoWin9x.isCollectionFile(file.path) -> false
            else -> knownArchive(file, scan) != null
        } },
        sourceOf = { it.uri },
        displayOrder = { entries -> entries.sortedBy { it.displayName.lowercase() } })

    val hashCount: Int get() = pipeline.hashCount
    fun cached(tree: Uri): List<X86Entry> = machinesOf(tree, pipeline.cached(tree))
    fun scan(tree: Uri, depth: ScanDepth, cancelled: AtomicBoolean, progress: (String) -> Unit): List<X86Entry> =
        machinesOf(tree, pipeline.scan(tree, depth, cancelled, progress))
    /** Saves the library's machines, with the disk images the last scan found. */
    fun store(tree: Uri, entries: List<X86Entry>) = pipeline.store(tree, entries.filterNot { it.disk } + disks(tree))

    /** The games folder [tree] and the disk images its last scan found there, in path order. */
    private class FolderDisks(val tree: String, val disks: List<X86Entry>)
    @Volatile private var folderDisks: FolderDisks? = null

    /** Every disk image the library scan found in [tree] (KairoX86#209); empty until it is read or scanned. */
    fun disks(tree: Uri): List<X86Entry> = folderDisks?.takeIf { it.tree == tree.toString() }?.disks.orEmpty()

    private fun machinesOf(tree: Uri, entries: List<X86Entry>): List<X86Entry> {
        val (images, machines) = entries.partition { it.disk }
        // By path, an archive's images by theirs in it.
        folderDisks = FolderDisks(tree.toString(), images.sortedBy { it.id.lowercase() })
        return machines
    }

    private fun inspect(file: DocumentTreeWalker.FileEntry, scan: LibraryScanPipeline.ScanContext<X86Entry>): X86Entry {
        scan.prior[folderOf(file.path)]?.let { prior ->
            if (!scan.forceHash && prior.size == file.size && prior.modified == file.modified) return prior
        }
        scan.hashStarted(file.path)
        val bytes = checkNotNull(context.contentResolver.openInputStream(file.uri)) { context.getString(R.string.machine_open_failed, file.path) }
            .use { it.readBytes() }
        // A changed 86box.cfg (a setting changed, or 86Box rewriting it) keeps the catalog ID the
        // machine was first scanned with, so its catalog record still applies (LibraryItem.catalogId,
        // KairoX86#213). Rechecking every file keeps it too: [scan.earlier] ignores forceHash.
        val contentId = contentIdOf(bytes)
        return entryOf(file, contentId, null, scan.earlier[folderOf(file.path)]?.catalogId ?: contentId)
    }

    /** An eXoWin9x game's entry (KairoX86#219): its machine folder, keyed by it; nothing is read. */
    private fun exoEntry(file: DocumentTreeWalker.FileEntry, game: ExoWin9x.Game) =
        X86Entry(game.folder, file.uri.toString(), game.folder, file.size, file.modified, "exowin9x-v1:${game.year}/${game.name}", exo = true)

    /** The game [entry] is of its eXoWin9x collection. */
    private fun exoGame(entry: X86Entry): ExoWin9x.Game = checkNotNull(ExoWin9x.gameOfFolder(entry.path)) { "${entry.path} is no eXoWin9x game's folder" }

    /** Makes the files an eXoWin9x game's machine needs before it starts (KairoX86#219). */
    fun makeExoDisks(entry: X86Entry, tree: Uri, cancelled: AtomicBoolean, progress: (String) -> Unit) =
        exoBuilder.makeDisks(tree, exoGame(entry), cancelled, progress)

    private fun entryOf(file: DocumentTreeWalker.FileEntry, contentId: String?, error: String?, catalogId: String? = contentId) =
        X86Entry(folderOf(file.path), file.uri.toString(), folderOf(file.path), file.size, file.modified, contentId, error, catalogId)

    /**
     * The archive [file]'s entries (KairoX86#217): its own, which no drive takes, then one for each
     * disk image in it. The images are listed, not read: a drive's disk is unpacked when it is chosen.
     */
    private fun inspectArchive(file: DocumentTreeWalker.FileEntry, scan: LibraryScanPipeline.ScanContext<X86Entry>): List<X86Entry> {
        if (!scan.forceHash) knownArchive(file, scan)?.let { return it }
        scan.hashStarted(file.path)
        return listOf(archiveOf(file, null)) + archiveDisks(file.uri, file.path, file.size, file.modified) { member -> GameKey.inArchive(file.path, member).path }
    }

    /** What the last scan found in the archive [file], when it is the same document still; else null. */
    private fun knownArchive(file: DocumentTreeWalker.FileEntry, scan: LibraryScanPipeline.ScanContext<X86Entry>): List<X86Entry>? =
        scan.priorFrom(file.uri.toString()).takeIf { found ->
            found.any { it.id == file.path && it.zipEntry == null && it.error == null } &&
                found.all { it.size == file.size && it.modified == file.modified }
        }

    /** The archive [file]'s own entry, failed with [error] when it could not be read. */
    private fun archiveOf(file: DocumentTreeWalker.FileEntry, error: String?) =
        X86Entry(file.path, file.uri.toString(), file.path, file.size, file.modified, DISK, error, disk = true)

    /** The disk images a drive takes in the archive [name] at [uri], each keyed by [key] of its path in it. */
    private fun archiveDisks(uri: Uri, name: String, size: Long, modified: Long, key: (String) -> String): List<X86Entry> =
        DiskArchive.open(context, uri, name, size).use { archive ->
            archive.members.filter { diskKind(DiskArchive.safeName(it.name)) != null }.map { member ->
                X86Entry(key(member.name), uri.toString(), name, size, modified, DISK, disk = true, zipEntry = member.name)
            }
        }

    /**
     * Prepares [entry]'s session folder from its folder in [tree] and returns the session, whose
     * folder 86Box runs (`-P`).
     */
    fun prepare(entry: X86Entry, tree: Uri, cancelled: AtomicBoolean): Session {
        val folder = findFolder(tree, entry.path)
        val dir = File(context.filesDir, "session/${GameKey(entry.id).hashName}")
        check(!dir.exists() || dir.deleteRecursively()) { context.getString(R.string.machine_session_failed) }
        check(dir.mkdirs()) { context.getString(R.string.machine_session_failed) }
        val media = File(context.filesDir, "session-media/${dir.name}")
        check(!media.exists() || media.deleteRecursively()) { context.getString(R.string.machine_session_failed) }
        val session = Session(entry.id, tree, folder, dir, media)
        try {
            session.fill(folder, dir, "", cancelled)
            check(File(dir, CONFIG).isFile) { context.getString(R.string.machine_config_missing, entry.displayName) }
            // A disk its 86box.cfg names that is not in its folder (KairoX86#63): 86Box would start with the drive empty.
            missingMedium(IniText(File(dir, CONFIG).readText())) { path -> File(dir, path).isFile }
                ?.let { throw MissingDisk(missingDisk(it)) }
            // The files an eXoWin9x game copies into Windows before it boots (KairoX86#225)
            if (entry.exo) exoBuilder.prepareStart(tree, exoGame(entry), dir)
        } catch (failure: Exception) {
            session.close()
            throw failure
        }
        return session
    }

    /** The document ID of the folder [path] in [tree], by name from its root. */
    private fun findFolder(tree: Uri, path: String): String = docs.findFolder(tree, path)

    private fun children(tree: Uri, parent: String): List<X86Documents.Child> = docs.children(tree, parent)

    /**
     * Where in its machine's folder the disk [entry] inside an archive is unpacked to (KairoX86#217):
     * in a folder named after the archive with its kind ("Game (zip)" for Game.zip), at its path in
     * the archive. The kind keeps a ZIP's and a 7z's of one name apart, and the folder's name is never
     * the archive's own, which may be beside it.
     */
    fun unpackedPath(entry: X86Entry): String {
        val member = DiskArchive.safeName(checkNotNull(entry.zipEntry) { "${entry.displayName} is in no archive" })
        val archive = entry.path.substringAfterLast('/')
        val kind = archive.substringAfterLast('.').lowercase()
        return "${archive.substringBeforeLast('.')} ($kind)/$member"
    }

    /**
     * Unpacks the disk [entry] inside an archive into the folder [folder] of [tree] at
     * [unpackedPath], checked against the archive's size and CRC-32, through a partial file renamed
     * when it is whole; returns the disk's document. One unpacked before is kept, not replaced.
     */
    fun unpackInto(tree: Uri, folder: String, entry: X86Entry, cancelled: AtomicBoolean, progress: (String) -> Unit): Uri {
        val relative = unpackedPath(entry)
        var parent = folder
        for (name in relative.split('/').dropLast(1)) {
            val existing = children(tree, parent).firstOrNull { it.name == name }
            check(existing == null || existing.folder) { context.getString(R.string.machine_create_failed, relative) }
            parent = existing?.id ?: created(DocumentsContract.createDocument(context.contentResolver,
                DocumentsContract.buildDocumentUriUsingTree(tree, parent), Document.MIME_TYPE_DIR, name), name)
                .let(DocumentsContract::getDocumentId)
        }
        val name = relative.substringAfterLast('/')
        children(tree, parent).firstOrNull { it.name == name }?.let { done ->
            check(!done.folder) { context.getString(R.string.machine_create_failed, relative) }
            return DocumentsContract.buildDocumentUriUsingTree(tree, done.id)
        }
        progress(context.getString(FrontendR.string.kairo_disk_preparing, entry.displayName))
        // A partial file a crash left goes first: the new one would get another name.
        children(tree, parent).filter { it.name == "$name.part" && !it.folder }.forEach { stale ->
            check(DocumentsContract.deleteDocument(context.contentResolver, DocumentsContract.buildDocumentUriUsingTree(tree, stale.id))) {
                context.getString(R.string.machine_delete_failed, stale.name)
            }
        }
        val partial = created(DocumentsContract.createDocument(context.contentResolver, DocumentsContract.buildDocumentUriUsingTree(tree, parent),
            "application/octet-stream", "$name.part"), "$name.part")
        return try {
            DiskArchive.open(context, Uri.parse(entry.uri), entry.path, entry.size).use { archive ->
                val member = archive.members.firstOrNull { it.name == entry.zipEntry }
                    ?: error(context.getString(FrontendR.string.kairo_disk_member_missing, entry.zipEntry))
                checkNotNull(context.contentResolver.openOutputStream(partial, "wt")) { context.getString(R.string.machine_write_failed, name) }
                    .use { output ->
                        archive.copy(member, output) {
                            if (cancelled.get()) throw java.util.concurrent.CancellationException("Cancelled")
                        }
                    }
            }
            created(DocumentsContract.renameDocument(context.contentResolver, partial, name), name)
        } catch (failure: Exception) {
            // The partial file goes; the failure that stopped the unpacking is the one reported.
            try {
                DocumentsContract.deleteDocument(context.contentResolver, partial)
            } catch (cleanup: Exception) {
                failure.addSuppressed(cleanup)
            }
            throw failure
        }
    }

    /**
     * The document [uri] a provider made as [name], failing when it made none or gave it another
     * name, as a provider does for a name that is taken ("Game (1)").
     */
    private fun created(uri: Uri?, name: String): Uri = docs.created(uri, name)

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
                // Keyed by its path in the games folder, as the scan keys the same image (otherDisks).
                X86Entry(if (entryId.isEmpty()) path else "$entryId/$path", file.absolutePath, path, 0, 0, DISK, disk = true)
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
            check(media.isDirectory || media.mkdirs()) { context.getString(R.string.machine_session_failed) }
            val file = File(media, "${open.size}-${entry.path.substringAfterLast('/')}")
            // A floppy may be written, as on the PC; a CD only read.
            val descriptor = checkNotNull(context.contentResolver.openFileDescriptor(Uri.parse(entry.uri),
                if (kind == DiskKind.FLOPPY) "rw" else "r")) { context.getString(R.string.machine_open_failed, entry.path) }
            open += descriptor
            Os.symlink("/proc/self/fd/${descriptor.fd}", file.path)
            return file
        }

        /** The file of this session folder the disk [entry] inside an archive is unpacked to ([unpackedPath]). */
        fun unpacked(entry: X86Entry): File = File(dir, unpackedPath(entry))

        /**
         * Makes the disk [entry] inside an archive one of this machine's own (KairoX86#217): unpacked,
         * the first time it is chosen, into the machine's folder ([unpackInto]), and linked into this
         * session as the folder's other files are. From then on that file is the disk: 86Box writes
         * to it in place, and the archive is left as it was. Returns the session file.
         */
        fun unpack(entry: X86Entry, cancelled: AtomicBoolean, progress: (String) -> Unit): File {
            val target = unpacked(entry)
            if (target.exists()) return target
            val relative = unpackedPath(entry)
            check(target.parentFile!!.isDirectory || target.parentFile!!.mkdirs()) { context.getString(R.string.machine_create_failed, relative) }
            val document = unpackInto(tree, folder, entry, cancelled, progress)
            val descriptor = checkNotNull(context.contentResolver.openFileDescriptor(document, "rw")) { context.getString(R.string.machine_open_failed, relative) }
            open += descriptor
            Os.symlink("/proc/self/fd/${descriptor.fd}", target.path)
            return target
        }

        /** Copies the small files 86Box rewrites and links every other file, in [source]'s folder at [relative]. */
        fun fill(source: String, target: File, relative: String, cancelled: AtomicBoolean) {
            for (child in children(tree, source)) {
                if (cancelled.get()) throw java.util.concurrent.CancellationException("Cancelled")
                val path = if (relative.isEmpty()) child.name else "$relative/${child.name}"
                val file = File(target, child.name)
                require(file.canonicalPath.startsWith(dir.canonicalPath + File.separator)) { context.getString(R.string.machine_unsafe_name, child.name) }
                val uri = DocumentsContract.buildDocumentUriUsingTree(tree, child.id)
                when {
                    child.folder -> {
                        check(file.mkdirs()) { context.getString(R.string.machine_create_failed, path) }
                        fill(child.id, file, path, cancelled)
                    }
                    copied(path) -> checkNotNull(context.contentResolver.openInputStream(uri)) { context.getString(R.string.machine_open_failed, path) }
                        .use { input -> file.outputStream().use { input.copyTo(it) } }
                    else -> {
                        // The file opened in place, for reading and writing (its disk may be written).
                        val descriptor = checkNotNull(context.contentResolver.openFileDescriptor(uri, "rw")) { context.getString(R.string.machine_open_failed, path) }
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
                ?: error(context.getString(R.string.machine_create_failed, NVR))
            for (file in nvr.listFiles().orEmpty().filter { it.isFile }) writeFile(nvrFolder, file, file.name)
        }

        private fun writeFile(parent: String, file: File, name: String) {
            if (!file.isFile) return
            val existing = children(tree, parent).firstOrNull { it.name == name && !it.folder }
            val uri = existing?.let { DocumentsContract.buildDocumentUriUsingTree(tree, it.id) }
                ?: DocumentsContract.createDocument(context.contentResolver, DocumentsContract.buildDocumentUriUsingTree(tree, parent),
                    "application/octet-stream", name)
                ?: error(context.getString(R.string.machine_create_failed, name))
            checkNotNull(context.contentResolver.openOutputStream(uri, "wt")) { context.getString(R.string.machine_write_failed, name) }
                .use { output -> file.inputStream().use { it.copyTo(output) } }
        }

        override fun close() {
            open.forEach(ParcelFileDescriptor::close)
            open.clear()
            media.deleteRecursively()
        }
    }

    /**
     * Deletes [entry], the game being its folder (KairoX86#211): the folder goes, disks and all. A
     * machine in the games folder itself loses only its 86box.cfg and nvr/, since that folder holds
     * every other machine and disk too.
     */
    fun delete(entry: X86Entry, tree: Uri) {
        val folder = findFolder(tree, entry.path)
        val doomed = if (entry.path.isEmpty())
            children(tree, folder).filter { it.name.equals(CONFIG, ignoreCase = true) || (it.folder && it.name == NVR) }
                .map { it.id to it.name }
        else listOf(folder to entry.path)
        for ((id, name) in doomed)
            check(DocumentsContract.deleteDocument(context.contentResolver, DocumentsContract.buildDocumentUriUsingTree(tree, id))) {
                context.getString(R.string.machine_delete_failed, name)
            }
    }

    /**
     * Makes [disk] [machine]'s first hard disk, or leaves it none for null (KairoX86#217); returns
     * the 86box.cfg changes, which are made. A disk in an archive is unpacked into the machine's
     * folder first ([unpackInto]); one already in the folder is used where it is. Its geometry is the
     * one the image names (X86HardDisk), and the drive keeps the bus and channel it had, an IDE
     * drive on the first channel for a machine with none. 86Box takes the change when the machine
     * next starts.
     */
    fun setHardDisk(machine: X86Entry, tree: Uri, disk: X86Entry?, cancelled: AtomicBoolean, progress: (String) -> Unit): List<X86Settings.Change> {
        val config = config(machine, tree)
        val changes = if (disk == null) listOf(X86Settings.Change(HARD_DISKS, "hdd_01_fn", null),
            X86Settings.Change(HARD_DISKS, "hdd_01_parameters", null), X86Settings.Change(HARD_DISKS, "hdd_01_ide_channel", null))
        else {
            val folder = findFolder(tree, machine.path)
            val (relative, document) = if (disk.zipEntry != null) {
                    val unpacked = unpackedPath(disk)
                    val uri = unpackInto(tree, folder, disk, cancelled, progress)
                    remember(tree, machine, unpacked, uri)
                    unpacked to uri
                } else {
                    val prefix = if (machine.path.isEmpty()) "" else "${machine.path}/"
                    require(disk.path.startsWith(prefix)) { "${disk.path} is not in ${machine.displayName}'s folder" }
                    disk.path.removePrefix(prefix) to Uri.parse(disk.uri)
                }
            val geometry = checkNotNull(context.contentResolver.openFileDescriptor(document, "r")) { context.getString(R.string.machine_open_failed, relative) }
                .use { descriptor ->
                    val channel = java.io.FileInputStream(descriptor.fileDescriptor).channel
                    X86HardDisk.geometry(relative, descriptor.statSize) { offset, length ->
                        val buffer = java.nio.ByteBuffer.allocate(length)
                        while (buffer.hasRemaining()) check(channel.read(buffer, offset + buffer.position()) > 0) { context.getString(R.string.machine_open_failed, relative) }
                        buffer.array()
                    }
                }
            // The drive's write protection and bus, as 86box.cfg had them.
            val had = config[HARD_DISKS, "hdd_01_parameters"]?.split(',')?.map { it.trim() }
            val bus = had?.getOrNull(4) ?: "ide"
            listOf(X86Settings.Change(HARD_DISKS, "hdd_01_fn", relative),
                X86Settings.Change(HARD_DISKS, "hdd_01_parameters",
                    "${geometry.sectors}, ${geometry.heads}, ${geometry.cylinders}, ${had?.getOrNull(3) ?: "0"}, $bus")) +
                listOfNotNull(X86Settings.Change(HARD_DISKS, "hdd_01_ide_channel", "0:0")
                    .takeIf { bus == "ide" && config[HARD_DISKS, "hdd_01_ide_channel"] == null })
        }
        change(machine, tree, changes)
        return changes
    }

    /**
     * Adds the disk unpacked to [relative] in [machine]'s folder to the disks the last scan found, so
     * the machine's own disks list it before the next scan does.
     */
    private fun remember(tree: Uri, machine: X86Entry, relative: String, uri: Uri) {
        val path = if (machine.path.isEmpty()) relative else "${machine.path}/$relative"
        val found = disks(tree)
        if (found.any { it.id == path }) return
        folderDisks = FolderDisks(tree.toString(),
            (found + X86Entry(path, uri.toString(), path, -1, 0, DISK, disk = true)).sortedBy { it.id.lowercase() })
    }

    /** The machine folder's 86box.cfg (Kairo#142), as it is now. */
    fun config(entry: X86Entry, tree: Uri): IniText = IniText(readConfig(tree, entry))

    /** Makes [changes] to the machine folder's 86box.cfg (Kairo#142): each key set, or removed for null. */
    fun change(entry: X86Entry, tree: Uri, changes: List<X86Settings.Change>) {
        val text = config(entry, tree)
        for (change in changes) text[change.section, change.key] = change.value
        val uri = configUri(tree, entry)
        checkNotNull(context.contentResolver.openOutputStream(uri, "wt")) { context.getString(R.string.machine_write_failed, "${entry.path}/$CONFIG") }
            .use { it.write(text.toString().toByteArray(Charsets.UTF_8)) }
    }

    private fun configUri(tree: Uri, entry: X86Entry): Uri {
        val folder = findFolder(tree, entry.path)
        val config = children(tree, folder).firstOrNull { !it.folder && it.name.equals(CONFIG, ignoreCase = true) }
            ?: error(context.getString(R.string.machine_config_missing, entry.displayName))
        return DocumentsContract.buildDocumentUriUsingTree(tree, config.id)
    }

    private fun readConfig(tree: Uri, entry: X86Entry): String {
        if (entry.exo) exoBuilder.makeConfig(tree, exoGame(entry))
        return readConfigFile(tree, entry)
    }

    private fun readConfigFile(tree: Uri, entry: X86Entry): String =
        checkNotNull(context.contentResolver.openInputStream(configUri(tree, entry))) { context.getString(R.string.machine_open_failed, "${entry.path}/$CONFIG") }
            .use { it.readBytes().toString(Charsets.UTF_8) }

    /** A disk image picked on the device (MachineLibrary.inspectExternal), for a drive. */
    fun pickedDisk(uri: Uri, name: String, size: Long, modified: Long): X86Entry {
        checkNotNull(diskKind(name)) { context.getString(R.string.machine_not_disk, name) }
        return X86Entry("disk-picked:$uri", uri.toString(), name, size, modified, DISK, disk = true)
    }

    /**
     * The disk images a drive takes in an archive picked on the device (KairoX86#217); one chosen is
     * unpacked into the running machine's folder, as one the library found is.
     */
    fun pickedArchive(uri: Uri, name: String, size: Long, modified: Long): List<X86Entry> =
        archiveDisks(uri, name, size, modified) { member -> "disk-picked:$uri/$member" }.also { disks ->
            require(disks.isNotEmpty()) { context.getString(FrontendR.string.kairo_disk_no_image_in, "IBM PC", name) }
        }

    private fun writeEntry(output: DataOutputStream, entry: X86Entry) {
        output.writeUTF(entry.id)
        output.writeUTF(entry.uri)
        output.writeUTF(entry.path)
        output.writeLong(entry.size)
        output.writeLong(entry.modified)
        output.writeUTF(entry.contentId ?: "")
        output.writeUTF(entry.error ?: "")
        output.writeBoolean(entry.disk)
        output.writeUTF(entry.catalogId ?: "")
        output.writeUTF(entry.zipEntry ?: "")
        output.writeBoolean(entry.exo)
    }

    private fun readEntry(input: DataInputStream): X86Entry = readEntryV4(input).copy(exo = input.readBoolean())

    /** A record of version 4, before eXoWin9x games. */
    private fun readEntryV4(input: DataInputStream): X86Entry =
        readEntryV3(input).copy(zipEntry = input.readUTF().ifEmpty { null })

    /** A record of version 3, before disks inside archives. */
    private fun readEntryV3(input: DataInputStream): X86Entry {
        val id = input.readUTF()
        val uri = input.readUTF()
        val path = input.readUTF()
        val size = input.readLong()
        val modified = input.readLong()
        val contentId = input.readUTF().ifEmpty { null }
        val error = input.readUTF().ifEmpty { null }
        val disk = input.readBoolean()
        val catalogId = input.readUTF().ifEmpty { null }
        return X86Entry(id, uri, path, size, modified, contentId, error, catalogId, disk = disk)
    }

    /** A drive's kind of disk image; a hard disk goes in when the machine starts (KairoX86#217). */
    enum class DiskKind { FLOPPY, CD, HARD_DISK }

    companion object {
        const val CONFIG = "86box.cfg"
        const val NVR = "nvr"
        /** The 86box.cfg section of the hard disks. */
        const val HARD_DISKS = "Hard disks"
        /** A disk entry's content ID: disks are no games of the catalog. */
        private const val DISK = "disk"

        /** The floppy and CD images 86Box reads, by extension. */
        private val FLOPPY_IMAGES = setOf("img", "ima", "dsk", "flp", "vfd", "xdf", "86f", "td0", "imd", "mfm", "fdi", "fdf")
        private val CD_IMAGES = setOf("iso", "cue", "chd", "mds", "ccd")

        /** What a drive takes a file named [name] as, or null for no disk image. */
        fun diskKind(name: String): DiskKind? = when (name.substringAfterLast('.', "").lowercase()) {
            in FLOPPY_IMAGES -> DiskKind.FLOPPY
            in CD_IMAGES -> DiskKind.CD
            in X86HardDisk.IMAGES -> DiskKind.HARD_DISK
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
                    medium.key.matches(key) && value.isNotEmpty() && !folderHas(value.removePrefix("wp://"), inFolder) &&
                        // 86Box makes a differencing disk over its parent when it is missing (KairoX86#219)
                        !(medium.section == HARD_DISKS && config[HARD_DISKS, key.removeSuffix("_fn") + "_vhd_parent"] != null)
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

        /** Whether the file at [path] is a machine's 86box.cfg. */
        private fun isConfig(path: String) = path.substringAfterLast('/').equals(CONFIG, ignoreCase = true)

        /** The files 86Box rewrites, copied into the session and back: its configuration and CMOS. */
        private fun copied(path: String) = path.equals(CONFIG, ignoreCase = true) || path.startsWith("$NVR/")

        fun contentIdOf(bytes: ByteArray): String = "sha256-vm-v1:" +
            MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
    }
}
