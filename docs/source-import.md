# Source provenance

## 86Box

- **Source:** https://github.com/86Box/86Box, commit `fc675106a7f7eae57bf89b212f634cb4a6758015` (2026-10-29, "Merge pull request #8596 from MaxwellS04/Table").
- **Copied to:** `third_party/86box/`, as `git archive` of that commit with LF line endings (`-c core.autocrlf=false -c core.eol=lf`). The archive's SHA-256 is `8c3797ba7445f68f41df742f87407cba846bf83f598dbd144567ab6bd9efe7c9`. Every copied file's Git blob matched the commit's tree (1,782 files) before the local changes.
- **Left out:** `src/qt/` (the Qt front end), `src/mac/` (macOS), `tests/`, `.ci/`, `.github/`, `debian/`, `wl_protocols/`. The headless Android build uses none of them.
- **Imported:** 2026-11-02.

### Local changes

`tools/patches.py` holds every change as text replacements that `shared/tools/local_patches.py` applies to a fresh copy and checks (`--check`: undoing and redoing them must give back the tree byte for byte).

- **`kairo9x-*` groups:** the changes made to 86Box for Kairo9X, which shares this core (KairoX86#183). They are the headless Android build (`src/unix/headless_main.c`, an SDL stub header, null audio, a SLiRP stub, the build files) and the exact speed fixes logged in Kairo9X's `PERF-FINDINGS.md` (the S3 FIFO fix, the ARM64 recompiler's block linking, timers, memory stubs, OPL synthesis and Sound Blaster mixing on their own threads, 8bpp line drawing on a second thread). Each fix reproduces the reference guest state bit for bit. They were taken from the Kairo9X working tree, and applying them to this snapshot gives back that tree's 49 changed and added files exactly.
- **`kairox86-license` group:** 86Box's cassette port (`src/device/cassette.c`, `src/include/86box/cassette.h`, from PCE) is GPL-2.0-only, which cannot ship beside the GPL-3.0-only shader runtime. Those files are removed and replaced by KairoX86's own `src/device/kairo_cassette.c` and `src/include/86box/kairo_cassette.h` (GPL-2.0-or-later), with the same calls and settings, written from the IBM cassette interface (a 1 bit is one 1 ms cycle, a 0 bit one 0.5 ms cycle) rather than from PCE's code. Every file that included the old header includes the new one. `src/network/net_vde.c` (VDE networking for Linux hosts, "GPL version 2") is removed and its build is switched off.
- **`kairox86-library` group:** KairoX86's build of the core (`core/CMakeLists.txt`). 86Box builds as a library (`KAIRO_LIBRARY`) that the machine loads afresh for each run, with KairoX86's frontend (`core/kairo/frontend.c`, `KAIRO_FRONTEND`) in place of the headless program and its null audio, and with the shared frontend's libchdr (`KAIRO_LIBCHDR`) in place of its bundled copy. libsndfile is taken through an interface target, and the CD image reader links it for its header. The version header names 86Box's own project (`PROJECT_*`), not the top-level one. The recompiler's pool goes in the nearest free place before or after the library, within 4 GiB, instead of one fixed address after the program. For Android 8 (API 26), which the app runs on: the PowerVR card's host clock uses `clock_gettime` instead of `timespec_get` (API 29), and `plat_run_command` (the serial port's host-command mode, `posix_spawn` from API 28) reports that it cannot run a host program, as an Android app cannot.

## libsndfile

- **Source:** https://github.com/libsndfile/libsndfile, tag `1.2.2` (commit `72f6af15e8f85157bd622ed45b979025828b7001`).
- **Copied to:** `third_party/libsndfile/`, as `git archive` of the tag with LF line endings, of `CMakeLists.txt`, `COPYING`, `AUTHORS`, `README.md`, `cmake/`, `include/`, `src/` and `sndfile.pc.in` (archive SHA-256 `7580e7f8272af9a18c89e484908450199e8b494fb8fa88e25eeccb5000f1152d`). Its programs, examples, tests, documentation and other platforms' build files were left out. Unchanged. Built without its external codecs (FLAC, Vorbis, Opus, MPEG): CD audio tracks in WAV and AIFF.
- **Imported:** 2026-11-02.

## FreeType

- **Source:** https://gitlab.freedesktop.org/freetype/freetype (GitHub mirror), tag `VER-2-13-3` (commit `42608f77f20749dd6ddc9e0536788eaad70ea4b5`).
- **Copied to:** `third_party/freetype/`, as `git archive` of the tag with LF line endings, of `CMakeLists.txt`, `README`, `LICENSE.TXT`, `include/`, `src/`, `devel/`, `builds/cmake/`, `builds/unix/`, `builds/windows/`, `docs/FTL.TXT` and `docs/GPLv2.TXT` (archive SHA-256 `df9be3a078158b9d096e6c0b13da21c7d8593657e5f629366c220380c4c2deed`, `README` added from the same tag). Its tests, other documentation and other platforms' build files were left out. Unchanged. Built without its optional bzip2, HarfBuzz, Brotli, PNG and zlib support, for the printers' text.
- **Imported:** 2026-11-02.

zlib, libpng and libchdr come from the shared frontend (`shared/third_party/`, `shared/cmake/KairoLibraries.cmake`, `KairoChd.cmake`).
