# Development

## A fresh clone

```sh
git clone https://github.com/MrJackSpade/KairoX86.git
cd KairoX86
git submodule update --init shared
git config core.hooksPath shared/githooks
```

The hooks every Kairo app shares (`shared/githooks`) check each commit's author and message and, before a push, the workflow pins. On Windows, Git's default 260-character path limit is enough since Kairo `d73ab80`.

## Building

Build the app, and optionally install it, with the shared build script (see [Android build](../shared/docs/android-build.md)):

```powershell
shared\tools\build.ps1 -Install <adb serial>
```

## The core

`third_party/86box/` is 86Box at a pinned commit; `tools/patches.py` holds every local change, which `shared/tools/local_patches.py` applies to a fresh copy of the snapshot and checks (`--check`). The core is shared with Kairo9X (KairoX86#183): a change to it goes into `tools/patches.py` here, never into a copy of its own.

Every change to the core's code is exact or it does not go in: the guest state at a fixed emulated time must match the reference fingerprint bit for bit (Kairo9X `PERF-FINDINGS.md`, `poc/vm/ab.sh`).

## Catalog

KairoX86 has no game catalog. `catalog/system-v2.json` is the system definition (the controls every entry starts from); `python shared/tools/app_catalog.py .` builds the catalog's parts and update from it and an empty research file (`tools/catalog_config.py`), and `--check` fails when they are out of date.
