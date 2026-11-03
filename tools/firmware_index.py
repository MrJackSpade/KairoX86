"""Writes the identities of every file in 86Box's ROM set (KairoX86#67): one line per file, its
SHA-1, its size and its path in the set, sorted by path, for the app to recognize the player's
firmware by its content under any name and put each file where 86Box reads it.

  python tools/firmware_index.py <86Box/roms checkout> <commit> <out.tsv>

The files are read from the checkout's Git objects at <commit> (git ls-tree / cat-file), never from
its working tree, so the index is that commit's set exactly. The set's own documents and Git files
(README, LICENSE, .gitattributes ...) at its top level are no firmware and are left out, as are the
text documents in its folders (a machine's README.txt, a card's url.txt: KairoX86#198). 86Box reads
no text file from its ROM set, and a checkout that converts line endings changes their digests.
"""
import hashlib
import subprocess
import sys

NOT_FIRMWARE = {'.gitattributes', '.gitignore', 'README.md', 'LICENSE', 'LICENSE.md', 'COPYING'}
DOCUMENTS = ('.txt', '.md')


def git(repo, *args):
    return subprocess.run(['git', '-C', repo, *args], check=True, capture_output=True).stdout


def main():
    repo, commit, out = sys.argv[1:4]
    listing = git(repo, 'ls-tree', '-r', '-z', commit).split(b'\0')
    lines = []
    for record in filter(None, listing):
        meta, path = record.split(b'\t', 1)
        mode, kind, blob = meta.split()
        path = path.decode('utf-8')
        if (kind != b'blob' or ('/' not in path and path in NOT_FIRMWARE) or path.startswith('.github/')
                or path.lower().endswith(DOCUMENTS)):
            continue
        if mode == b'120000':
            raise SystemExit(f'{path} is a symbolic link: the index takes files only')
        data = git(repo, 'cat-file', 'blob', blob.decode())
        if '\t' in path or '\n' in path:
            raise SystemExit(f'{path} cannot be written in the index')
        lines.append(f'{hashlib.sha1(data).hexdigest()}\t{len(data)}\t{path}')
    lines.sort(key=lambda line: line.split('\t', 2)[2])
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'# 86Box ROM set {commit}: SHA-1, size, path (tools/firmware_index.py)\n')
        f.write('\n'.join(lines) + '\n')
    print(f'{len(lines)} files')


if __name__ == '__main__':
    main()
