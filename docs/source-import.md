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
