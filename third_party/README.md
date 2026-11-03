# Third-party source snapshots

These directories contain copied, pinned source snapshots. They are not Git submodules or forks, and this repository has no upstream remote.

- `86box/`: 86Box at commit `fc675106a7f7eae57bf89b212f634cb4a6758015`, with its license notices preserved. Its Qt and macOS front ends, test suite, CI and packaging files were omitted.

`shared/tools/local_patches.py` applies KairoX86's local changes (`tools/patches.py`) to these snapshots; the source import lists them.

See [source import](../docs/source-import.md) for URLs, hashes, dates, and what was included. Do not replace these snapshots through a Git remote or automated sync.
