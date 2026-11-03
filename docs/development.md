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

The core builds for the host with llvm-mingw (`shared\tools\test-core.ps1` configures `.build\host`). `core/test/boot_test` runs machine folders in turn in one process, as the app runs one machine after another, and checks each leaves no thread behind and gives its memory back (each run ends within 32 MB of where the first ended, KairoX86#186); run it under `shared\tools\run-limited.ps1`:

```
boot_test <ROM set> <work folder> <machine folder>[><stop text>][|...] <seconds> [snapshot seconds] [frame:scancode,...]
```

A machine given with `>stop text` must stop before `<seconds>` with a reason containing that text; any other must not stop.

Each run reports the keyboard the machine runs with (`keyboard:`, the model the app's on-screen keyboard follows, KairoX86#65) and the guest seconds the app would run flat out as loading (`loading:`): floppy activity, and the power-on self test while Skip memory check is on (KairoX86#60). A machine with `[Kairo]` `skip_memory_check = off` in its `86box.cfg` shows the difference.

### Measuring and repeatability

`core/test/game_profile` (target `game_profile`, for the host and, with the NDK, the device) runs a machine folder a fixed number of frames as fast as the host can, with scripted input, and reports host time per guest frame:

```
game_profile <ROM set> <work dir> <machine folder> <frames> <script> [--warmup n] [--shots n] [--hashes file] [--seed n] [--runs n]
```

It runs a fresh copy of the folder each time (86Box writes the CMOS and `86box.cfg` back as it runs). With a seed (1 unless `--seed 0`), the run is repeatable: 86Box's random numbers come from the seed and the guest's clock runs in guest time (`X86Machine::Config::seed`), so `--hashes` (each frame's picture and sound hash) of two runs or two builds can be compared line by line. `--runs n` runs the machine n times in one process, as the app runs one machine after another, and fails unless every run matches the first, which also catches the emulation reading memory it never wrote.

### The raster test

`python core/test/display/make_raster.py <folder>` writes a machine (the 486 with an S3 Trio64V2) booting a floppy (`core/test/display/raster.S`) that, in VESA mode 101h (640x480, 256 colours), changes the palette at every horizontal blank and writes video memory just behind the beam, as games' raster effects do. A build configured with `-DCMAKE_C_FLAGS=-DKAIROX86_SYNC_RENDER` draws every line in place; `game_profile --hashes` on both builds must give the same frames (KairoX86#38), so the threaded 8bpp renderer can never show anything drawing in place would not.

### The native size test

`python core/test/display/make_modes.py <folder>` writes one machine per video mode (40- and 80-column text, the CGA, EGA and 256-colour 320-wide modes and 640x480 on the 486's VGA; text and graphics on the IBM PC's CGA), each booting a floppy (`core/test/display/modes.S`) that sets the mode and fills the screen, and prints the picture size the core must hand over: the mode's own pixels, one of each pixel the card draws twice across, and of each line CGA draws twice (KairoX86#37). A build configured with `-DCMAKE_C_FLAGS=-DKAIROX86_CHECK_NATIVE_SIZE` reports any frame whose pixels are not in pairs where it keeps one of each.

### The game port test

`python core/test/input/make_joyport.py <folder>` writes three machines (the 486 with a 2-axis 2-button pair of joysticks, a 2-axis 4-button joystick and a 4-axis 4-button one) booting a floppy (`core/test/input/joyport.S`) that reads the game port at 201h as DOS games do and shows its buttons and its four axes' timings, and prints the `game_profile` script that pushes each of the joystick model's inputs in turn (`--shots 30`; frame 900 nothing, then one input every 60 frames). Each input must change exactly one reading (KairoX86#52).

### Hardware queries

`hardware_query <ROM set> <query>` prints the core's answer to a query of the machine settings (Kairo#143, `core/kairo/hardware.h`): `machines` lists every machine 86Box has, with whether the ROM set has its firmware; `machine <id>` lists what that machine takes, from 86Box's own eligibility functions: its processor families and speeds, its memory range, and its video, sound, network, hard disk, SCSI and floppy controllers.

### The mouse test

`python core/test/input/make_mouse.py <folder>` writes two machines (the 486 with a three-button PS/2 mouse, and with a Microsoft serial mouse on COM1) booting a floppy (`core/test/input/mouse.S`) that reads the mouse straight from its port and shows its buttons and the sum of its motion, and prints the `game_profile` script that moves the mouse (`x`/`y` codes) and presses each button in turn (`--shots 30`; frame 900 untouched, then one input every 60 frames). Each step must show exactly the motion sent, in picture pixels, or exactly one button (KairoX86#50).

### The Auto touch mode test

`python core/test/input/make_auto.py <folder>` writes three machines standing in for games, one for each way a game reads its input: `auto-wait` gets keys through the BIOS (`core/test/input/keys.S`), `auto-poll` checks for a key over and over, and `auto-mouse` asks the mouse driver for the mouse on every pass (`mouse.S` with `INT33`). `game_profile`'s `input` line must show waits and "waiting 1", polls and "waiting 0", and mouse reads with nothing waiting (KairoX86#43).

### The direct touch test

`python core/test/input/make_place.py <folder>` writes three machines booting a floppy (`core/test/input/place.S`) that is a DOS mouse game with its own simplest mouse driver, and shows the position the driver gives: 80x25 text with the driver's default span, the same with the game setting the span, and mode 13h. `game_profile --place 960:<x>:<y>` asks for the pointer on a picture point, and the shot after must show that point in the driver's coordinates (the expected values are in the script's help) (KairoX86#44).

### The startup commands test

`python core/test/dos/make_dos.py <FreeDOS 1.3 floppy x86BOOT.img> <folder>` writes a machine booting a copy of the FreeDOS floppy rewritten to go straight to FreeCOM's `A:\>` prompt. `game_profile ... --commands "ECHO KAIRO X86|ECHO SECOND LINE"` types the lines at the prompt with the shared startup typer, each once the last has run, and prints `typed <frame>` (KairoX86#46). The prompt is DOS asked for keyboard input while the console line it last wrote reads `X:\...>`, so a program waiting for a key elsewhere gets nothing typed.

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

### The hard disk test

`python core/test/disks/make_hdd.py <folder>` writes a machine (ABIT BX6, whose BIOS finds IDE disks itself) with no floppy disk and a 10 MB IDE hard disk image whose master boot record is the halt test's boot sector plus one active partition. It boots from the hard disk only, so stopping with "The PC halted" proves it did (KairoX86#49):

```powershell
python core\test\disks\make_hdd.py .build\disks
shared\tools\run-limited.ps1 .build\host\boot_test.exe bios .build\disks-out ".build\disks\hdd>The PC halted" 30 "" 150:0x3b,300:0x3b,450:0x3b,600:0x3b
```

Hard disks belong to the machine's folder: 86Box never swaps a fixed disk while the PC runs, so they have no slot on the Disks page.

## Catalog

KairoX86 has no game catalog. `catalog/system-v2.json` is the system definition (the controls every entry starts from); `python shared/tools/app_catalog.py .` builds the catalog's parts and update from it and an empty research file (`tools/catalog_config.py`), and `--check` fails when they are out of date.
