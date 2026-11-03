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

## Host tests

The core builds for the host with llvm-mingw (`shared\tools\test-core.ps1` configures `.build\host`). `core/test/boot_test` runs machine folders in turn in one process, as the app runs one machine after another, and checks each leaves no thread behind; run it under `shared\tools\run-limited.ps1`:

```
boot_test <ROM set> <work folder> <machine folder>[><stop text>][|...] <seconds> [snapshot seconds] [frame:scancode,...]
```

A machine given with `>stop text` must stop before `<seconds>` with a reason containing that text; any other must not stop.

### Measuring and repeatability

`core/test/game_profile` (target `game_profile`, for the host and, with the NDK, the device) runs a machine folder a fixed number of frames as fast as the host can, with scripted input, and reports host time per guest frame:

```
game_profile <ROM set> <work dir> <machine folder> <frames> <script> [--warmup n] [--shots n] [--hashes file] [--seed n] [--runs n]
```

It runs a fresh copy of the folder each time (86Box writes the CMOS and `86box.cfg` back as it runs). With a seed (1 unless `--seed 0`), the run is repeatable: 86Box's random numbers come from the seed and the guest's clock runs in guest time (`X86Machine::Config::seed`), so `--hashes` (each frame's picture and sound hash) of two runs or two builds can be compared line by line. `--runs n` runs the machine n times in one process, as the app runs one machine after another, and fails unless every run matches the first, which also catches the emulation reading memory it never wrote.

### Stop tests

`python core/test/stops/make_floppies.py <folder>` writes one machine folder for each way a PC stops (KairoX86#34), each booting a floppy whose boot sector (`core/test/stops/boot.S`) stops it that way, and prints the machine list that expects each stop:

| Machine | Its boot sector | The stop |
| --- | --- | --- |
| `idle` | waits for interrupts | none |
| `halt` | CLI, then HLT | "The PC halted: its processor stopped with interrupts off" |
| `keyboard` | the AT keyboard's set scan code set command with set 5 | 86Box's `fatal()` on the machine's thread |
| `power-off` | the PIIX4's ACPI soft off (ABIT BX6) | "The PC turned itself off" |
| `voodoo` | a Voodoo 2 blit with an undefined command (ABIT BX6) | 86Box's `fatal()` on the Voodoo's FIFO thread |

```powershell
python core\test\stops\make_floppies.py .build\stops > .build\stops-list.txt
shared\tools\run-limited.ps1 .build\host\boot_test.exe bios .build\stops-out (Get-Content .build\stops-list.txt -Raw).Trim() 20
```

## Catalog

KairoX86 has no game catalog. `catalog/system-v2.json` is the system definition (the controls every entry starts from); `python shared/tools/app_catalog.py .` builds the catalog's parts and update from it and an empty research file (`tools/catalog_config.py`), and `--check` fails when they are out of date.
