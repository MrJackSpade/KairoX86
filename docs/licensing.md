# Licensing and credits

[← KairoX86](../README.md)

KairoX86 first-party code is [GPL-2.0-or-later](../LICENSE.md). The pinned [Kairo frontend](https://github.com/MrJackSpade/Kairo) is also GPL-2.0-or-later. Third-party components keep their own notices.

## 86Box

The PC emulation comes from [86Box](https://86box.net/) (`third_party/86box/`, see [source import](source-import.md)). Its README licenses it under the GNU General Public License, version 2 or later; the GPL version 2 text is in `third_party/86box/COPYING`, and its authors are listed in `AUTHORS`. Most source files carry no license line of their own and fall under that grant. The files that carry their own:

| Files | License |
| --- | --- |
| 194 files stating GPL-2.0-or-later (SPDX or the GPL notice) | GPL-2.0-or-later |
| Fred N. van Kempen's files (such as `src/device/isamem.c`, `isartc.c`, `src/disk/hdc_xta.c`) | BSD-3-Clause |
| `src/cpu/softfloat3e/` (Berkeley SoftFloat 3e) | BSD-3-Clause |
| `src/sound/ymfm/` (ymfm, Aaron Giles) | BSD-3-Clause |
| `src/sound/resid-fp/` (reSID-fp) | GPL-2.0-or-later |
| `src/cdrom/cdrom_aaru.c` (Aaru format identification, Natalia Portillo) | LGPL-2.1-or-later |
| `src/cdrom/libchdr/` (libchdr) | BSD-3-Clause; its LZMA SDK and miniz are public domain, dr_flac public domain or MIT-0 |
| `src/osd/imgui/` (Dear ImGui and stb) | MIT; stb public domain or MIT |
| `src/crcspeed/` | BSD-3-Clause |

86Box's cassette port (`src/device/cassette.c`, `src/include/86box/cassette.h`, from PCE) says "GNU General Public License version 2" without "or later", and `src/network/net_vde.c` "GPL version 2". KairoX86 leaves them out of its snapshot and builds its own cassette port in their place (`src/device/kairo_cassette.c`, `src/include/86box/kairo_cassette.h`, GPL-2.0-or-later); VDE networking is not built. Every file KairoX86 builds is GPL-2.0-or-later or more permissive.

### The shader runtime

Since 86Box is GPL-2.0-or-later, KairoX86 links the shared RetroArch Slang shader runtime, which uses librashader under its GPL-3.0-only option and includes Rust crates licensed only under Apache-2.0, and the combined app is distributed under GPLv3 terms, as the other Kairo apps are.

## Firmware the app ships

None of the 86Box ROM set ships with KairoX86: its files belong to their copyright owners. The app carries only free firmware, which runs inside the emulated PC, not linked into the app:

- [GLaBIOS](https://glabios.org/), a free BIOS for the IBM PC and XT, under GPL-3.0.
- The [XTIDE Universal BIOS](https://www.xtideuniversalbios.org/), the hard disk BIOS of the free XT, built from its GPL-2.0-or-later source.
- A character ROM (the MDA and CGA fonts) made for KairoX86 from a free font.
