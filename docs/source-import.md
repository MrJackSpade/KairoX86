# Source provenance

## 86Box

- **Source:** https://github.com/86Box/86Box, commit `fc675106a7f7eae57bf89b212f634cb4a6758015` (2026-10-29, "Merge pull request #8596 from MaxwellS04/Table").
- **Copied to:** `third_party/86box/`, as `git archive` of that commit with LF line endings (`-c core.autocrlf=false -c core.eol=lf`). The archive's SHA-256 is `8c3797ba7445f68f41df742f87407cba846bf83f598dbd144567ab6bd9efe7c9`. Every copied file's Git blob matched the commit's tree (1,782 files) before the local changes.
- **Left out:** `src/qt/` (the Qt front end) except the three Windows platform files the headless build takes from it (`win_netsocket.c`, `win_dynld.c`, `win_cdrom_ioctl.c`, added back from the same commit, for the host build), `src/mac/` (macOS), `tests/`, `.ci/`, `.github/`, `debian/`, `wl_protocols/`. The headless Android build uses none of them.
- **Imported:** 2026-11-02.

### Local changes

`tools/patches.py` holds every change as text replacements that `shared/tools/local_patches.py` applies to a fresh copy and checks (`--check`: undoing and redoing them must give back the tree byte for byte).

- **`kairo9x-*` groups:** the changes made to 86Box for Kairo9X, which shares this core (KairoX86#183). They are the headless Android build (`src/unix/headless_main.c`, an SDL stub header, null audio, a SLiRP stub, the build files) and the exact speed fixes logged in Kairo9X's `PERF-FINDINGS.md` (the S3 FIFO fix, the ARM64 recompiler's block linking, timers, memory stubs, OPL synthesis and Sound Blaster mixing on their own threads, 8bpp line drawing on a second thread). Each fix reproduces the reference guest state bit for bit. They were taken from the Kairo9X working tree, and applying them to this snapshot gives back that tree's 49 changed and added files exactly.
- **`kairox86-license` group:** 86Box's cassette port (`src/device/cassette.c`, `src/include/86box/cassette.h`, from PCE) is GPL-2.0-only, which cannot ship beside the GPL-3.0-only shader runtime. Those files are removed and replaced by KairoX86's own `src/device/kairo_cassette.c` and `src/include/86box/kairo_cassette.h` (GPL-2.0-or-later), with the same calls and settings, written from the IBM cassette interface (a 1 bit is one 1 ms cycle, a 0 bit one 0.5 ms cycle) rather than from PCE's code. Every file that included the old header includes the new one. `src/network/net_vde.c` (VDE networking for Linux hosts, "GPL version 2") is removed and its build is switched off.
- **`kairox86-library` group:** KairoX86's build of the core (`core/CMakeLists.txt`). 86Box builds as a library (`KAIRO_LIBRARY`) that the machine loads afresh for each run, with KairoX86's frontend (`core/kairo/frontend.c`, `KAIRO_FRONTEND`) in place of the headless program and its null audio, and with the shared frontend's libchdr (`KAIRO_LIBCHDR`) in place of its bundled copy. libsndfile is taken through an interface target, and the CD image reader links it for its header. The version header names 86Box's own project (`PROJECT_*`), not the top-level one. The recompiler's pool goes in the nearest free place before or after the library, within 4 GiB, instead of one fixed address after the program. For Android 8 (API 26), which the app runs on: the PowerVR card's host clock uses `clock_gettime` instead of `timespec_get` (API 29), and `plat_run_command` (the serial port's host-command mode, `posix_spawn` from API 28) reports that it cannot run a host program, as an Android app cannot.
- **`kairox86-stop` group:** each CPU core's HLT that stays halted notes where it halted (`CPU_NOTE_HALT`, `cpu_halt_cs`/`cpu_halt_pc` in `src/cpu/386_common.c`): the 386 cores (`x86_ops_misc.h`), the 8088/8086 (`808x.c`), its cycle-exact core (`808x_marty_86box.c`) and the NEC V20/V30 (`vx0.c`). The frontend reads it with the flags to tell a processor stopped with interrupts off, so the machine ends with that reason (KairoX86#34). It changes no emulated state.
- **`kairox86-repeatable` group:** the SN76489 (the PCjr's and Tandy's sound) took its noise counters' start values from the C library's random numbers after seeding them from the host's clock, which also undid a repeatable run's seed for every other `rand()`. It takes them from 86Box's own random numbers (`random_generate`), seeded in a repeatable run and as random as before otherwise (KairoX86#36).
- **`kairox86-sync-render` group:** with `KAIROX86_SYNC_RENDER` defined (test builds only), every 8bpp line is drawn in place, to compare the threaded renderer against (KairoX86#38).
- **`kairox86-raster` group:** the threaded 8bpp renderer (`kairo9x-video`) drew a queued line later from VRAM and the live palette, so palette changes and VRAM written after the line was scanned showed in it, unlike drawing in place. A queued line now holds its VRAM bytes and the palette as the guest scanned it (KairoX86#38).
- **`kairox86-own-memory` group:** the platform files' `plat_mmap` and `plat_munmap` become `plat_mmap_os` and `plat_munmap_os`; the frontend's own record each mapping, and a machine's close unmaps what 86Box left (the recompiler's pool and tables). The library's `malloc` family goes through the frontend's record by the linker's `--wrap` (`core/CMakeLists.txt`), and the close frees what is left, so a closed machine gives back what it took (KairoX86#186).
- **`kairox86-mouse-enable` group:** the PS/2 mouse (its enable, disable and reset commands), the serial mouse (RTS raised) and the bus mice (their interrupt enables) tell the frontend's `kairo_observe_mouse_enable` when the guest turns their reports on or off. With Windows's start and exit broadcasts (INT 2Fh AX=1605h/1606h), the frontend tells a protected-mode system driving the mouse from a DOS driver, for the Auto touch mode (KairoX86#190).
- **`kairox86-path-append` group:** `path_append_filename` copies its first part only when it is not already the destination: `add_path` appends a relative ROM folder in place, a copy onto itself that C leaves undefined (KairoX86#192).
- **`kairox86-native-size` group:** each frame, the VGA family (`svga_doblit`: the renderers that draw each pixel twice across, when no cursor, overlay or accelerator draws over them and the same renderer drew the whole frame) and the CGA (40-column text and 320-wide graphics, not composite; its line doubling) say on their monitor how many times they drew each pixel across and each line down, and the frontend keeps one of each, so the core hands the host the machine's own pixels (KairoX86#37).
- **`kairox86-guest-input` group:** every processor's INT decoder (the 386 and later interpreters, which the recompiler runs INT through, the 8088, the cycle-exact 8088 and the NEC V20/V30) passes each INT n, with AX and the caller's code address, to the frontend's `kairo_observe_int`, through the call's registers: it counts the BIOS keyboard waits and polls (INT 16h) and the mouse driver's reads (INT 33h) for the Auto touch mode (KairoX86#43), and for direct touch turns the program's next "get the position" (INT 33h AX=03h) into the driver's "set the position" (AX=04h) to the tapped point (KairoX86#44); with DS, it follows the console line DOS writes, so a keyboard read at a DOS prompt counts as the command shell waiting for a command (KairoX86#46).

## 86Box ROM set index

- **Source:** https://github.com/86Box/roms, commit `ebefe507a659192ad4c0155b984cdec30b1e1ecd` (2026-10-29, "Merge pull request #620 from MaxwellS04/Mach64"), the ROM set of the 86Box snapshot's date.
- **Copied to:** `kairox86/src/main/assets/firmware/86box-roms.tsv`: no firmware, only each file's SHA-1, size and path in the set (1,776 files), written by `python tools/firmware_index.py <roms checkout> <commit> <out>` from the commit's Git objects. The set's own README, LICENSE and Git files are left out. The app recognizes the player's firmware by these digests under any name and puts each file at its path (KairoX86#67).
- **Imported:** 2026-11-03.

## libsndfile

- **Source:** https://github.com/libsndfile/libsndfile, tag `1.2.2` (commit `72f6af15e8f85157bd622ed45b979025828b7001`).
- **Copied to:** `third_party/libsndfile/`, as `git archive` of the tag with LF line endings, of `CMakeLists.txt`, `COPYING`, `AUTHORS`, `README.md`, `cmake/`, `include/`, `src/` and `sndfile.pc.in` (archive SHA-256 `7580e7f8272af9a18c89e484908450199e8b494fb8fa88e25eeccb5000f1152d`). Its programs, examples, tests, documentation and other platforms' build files were left out. Unchanged. Built without its external codecs (FLAC, Vorbis, Opus, MPEG): CD audio tracks in WAV and AIFF.
- **Imported:** 2026-11-02.

## FreeType

- **Source:** https://gitlab.freedesktop.org/freetype/freetype (GitHub mirror), tag `VER-2-13-3` (commit `42608f77f20749dd6ddc9e0536788eaad70ea4b5`).
- **Copied to:** `third_party/freetype/`, as `git archive` of the tag with LF line endings, of `CMakeLists.txt`, `README`, `LICENSE.TXT`, `include/`, `src/`, `devel/`, `builds/cmake/`, `builds/unix/`, `builds/windows/`, `docs/FTL.TXT` and `docs/GPLv2.TXT` (archive SHA-256 `df9be3a078158b9d096e6c0b13da21c7d8593657e5f629366c220380c4c2deed`, `README` added from the same tag). Its tests, other documentation and other platforms' build files were left out. Unchanged. Built without its optional bzip2, HarfBuzz, Brotli, PNG and zlib support, for the printers' text.
- **Imported:** 2026-11-02.

zlib, libpng and libchdr come from the shared frontend (`shared/third_party/`, `shared/cmake/KairoLibraries.cmake`, `KairoChd.cmake`).

## GLaBIOS

- **Source:** https://github.com/640-KB/GLaBIOS, tag `v0.4.0` (commit `8d126e03d619cf60fbe343cb6999bf1c4c453c09`), the release of 2025-07-18.
- **Copied to:** `third_party/glabios/`: the tag's source (`src/`, `LICENSE`, `README.md`; the GitHub tarball, SHA-256 `b5a0b2d5c9d10db8833534b670860349ccc9b954035dae07a3cd0e6d446e107d`, without its `images/` and `doc/`) and the release's two images 86Box names, `GLABIOS_0.4.0_8P.ROM` (8088, SHA-1 `fd023bbf445ed64e42ec0cf4ff10e907ccff4017`) and `GLABIOS_0.4.0_VP.ROM` (V20, SHA-1 `24e19f12baa2e4241f9b85c4127a68b617627882`), the same files as in 86Box's ROM set. Unchanged. GLaBIOS is assembled with a DOS assembler; the images are the project's own release builds of that source.
- **Imported:** 2026-11-03.

## PC fonts (from SeaBIOS)

- **Source:** https://github.com/coreboot/seabios, tag `rel-1.16.3` (commit `a6ed6b701f0a57db0569ab98b0661c12a6ec3ff8`), `vgasrc/vgafonts.c` (SHA-256 `a992a54dbc051be8b03067becb88e9f2fde580e8ba6b65797a3a069c96a96d81`): Joseph Gil's 8x8, 8x14 and 8x16 code page 437 fonts, public domain.
- **Copied to:** `third_party/seabios-fonts/vgafonts.c`, unchanged. `tools/make_font_rom.py` writes `firmware/video/mda/mda.rom` (the IBM MDA/CGA character ROM's layout) from it; `--check` (in `tools/checks.sh`) fails when the committed ROM is out of date.
- **Imported:** 2026-11-03.
