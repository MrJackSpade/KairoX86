package com.mrjackspade.kairox86

import android.content.Context
import android.net.Uri
import android.provider.DocumentsContract
import android.provider.DocumentsContract.Document
import java.io.OutputStream

/**
 * The games folder's documents, by path from its root (a Storage Access Framework tree): the
 * library's machine folders, and the folders KairoX86 makes in it (an archive's unpacked disks,
 * KairoX86#217; an eXoWin9x game's machine, KairoX86#219). Every document it makes is checked to
 * have the name asked for, since a provider renames one that is taken ("Game (1)").
 */
class X86Documents(private val context: Context) {
    /** A document in a folder: [size] in bytes (-1 for a folder, or where the provider does not say). */
    data class Child(val id: String, val name: String, val folder: Boolean, val size: Long = -1)

    fun children(tree: Uri, parent: String): List<Child> {
        val query = DocumentsContract.buildChildDocumentsUriUsingTree(tree, parent)
        return checkNotNull(context.contentResolver.query(query,
            arrayOf(Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME, Document.COLUMN_MIME_TYPE, Document.COLUMN_SIZE), null, null, null)) {
            context.getString(R.string.machine_list_failed)
        }.use { cursor ->
            buildList {
                while (cursor.moveToNext()) add(Child(cursor.getString(0), cursor.getString(1), cursor.getString(2) == Document.MIME_TYPE_DIR,
                    if (cursor.isNull(3)) -1 else cursor.getLong(3)))
            }
        }
    }

    /** The document ID of the folder [path] in [tree], by name from its root. */
    fun findFolder(tree: Uri, path: String): String {
        var id = DocumentsContract.getTreeDocumentId(tree)
        for (name in path.split('/').filter { it.isNotEmpty() }) {
            id = children(tree, id).firstOrNull { it.name == name && it.folder }?.id
                ?: error(context.getString(R.string.machine_folder_missing, path))
        }
        return id
    }

    /** The document at [path] in [tree] (a folder's or a file's), or null when there is none. */
    fun find(tree: Uri, path: String): Child? {
        var at: Child? = null
        var id = DocumentsContract.getTreeDocumentId(tree)
        for (name in path.split('/').filter { it.isNotEmpty() }) {
            at = children(tree, id).firstOrNull { it.name == name } ?: return null
            id = at.id
        }
        return at
    }

    fun uri(tree: Uri, id: String): Uri = DocumentsContract.buildDocumentUriUsingTree(tree, id)

    /** The folder [path] in [tree], made where it is missing, each folder by its own name. */
    fun makeFolders(tree: Uri, path: String): String {
        var id = DocumentsContract.getTreeDocumentId(tree)
        for (name in path.split('/').filter { it.isNotEmpty() }) {
            val existing = children(tree, id).firstOrNull { it.name == name }
            check(existing == null || existing.folder) { context.getString(R.string.machine_create_failed, path) }
            id = existing?.id ?: DocumentsContract.getDocumentId(created(DocumentsContract.createDocument(context.contentResolver,
                uri(tree, id), Document.MIME_TYPE_DIR, name), name))
        }
        return id
    }

    /**
     * Writes the file [name] in the folder [parent] through a partial file renamed when [write] has
     * finished, so a file of that name is always whole; a stale partial goes first. On a failure the
     * partial goes and the failure that stopped the write is the one reported.
     */
    fun writeWhole(tree: Uri, parent: String, name: String, write: (OutputStream) -> Unit): Uri {
        children(tree, parent).filter { it.name == "$name.part" && !it.folder }.forEach { stale ->
            check(DocumentsContract.deleteDocument(context.contentResolver, uri(tree, stale.id))) {
                context.getString(R.string.machine_delete_failed, stale.name)
            }
        }
        val partial = created(DocumentsContract.createDocument(context.contentResolver, uri(tree, parent),
            "application/octet-stream", "$name.part"), "$name.part")
        return try {
            checkNotNull(context.contentResolver.openOutputStream(partial, "wt")) { context.getString(R.string.machine_write_failed, name) }
                .use(write)
            created(DocumentsContract.renameDocument(context.contentResolver, partial, name), name)
        } catch (failure: Exception) {
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
    fun created(uri: Uri?, name: String): Uri {
        checkNotNull(uri) { context.getString(R.string.machine_create_failed, name) }
        val made = checkNotNull(context.contentResolver.query(uri, arrayOf(Document.COLUMN_DISPLAY_NAME), null, null, null)) {
            context.getString(R.string.machine_create_failed, name)
        }.use { cursor -> if (cursor.moveToFirst()) cursor.getString(0) else null }
        check(made == name) { context.getString(R.string.machine_create_failed, name) }
        return uri
    }
}
