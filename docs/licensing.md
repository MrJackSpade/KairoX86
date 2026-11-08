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

### MIDI synths and the SoundFont

A game's MIDI music plays through the synths every Kairo app shares (`shared/third_party/`, see shared's source import): Munt's libmt32emu 2.7.3 (MT-32 and CM-32L) and FluidSynth 2.5.2 (General MIDI), both LGPL-2.1-or-later, FluidSynth with GCEM 1.18.0 (Apache-2.0). Both are linked statically into the core, whose complete source is published, so the LGPL's relinking terms are met by that source. The MT-32 and CM-32L firmware is the player's own. The app ships GeneralUser GS 2.0.3 by S. Christian Collins as FluidSynth's default SoundFont, under its own licence (`shared/third_party/generaluser-gs/LICENSE.txt`), which allows it in software; players may import their own SoundFonts.

### 86Box's translations

The Machine settings translate the words of 86Box's card options with 86Box's own translations where it has them (`third_party/86box-languages/`, from its `src/qt/languages/`, GPL-2.0-or-later as 86Box), built into `kairox86/src/main/res/values*/strings_86box.xml` by `tools/device_strings.py`; the rest are KairoX86's own (`tools/device_strings_translations.json`).

### The shader runtime

Since 86Box is GPL-2.0-or-later, KairoX86 links the shared RetroArch Slang shader runtime, which uses librashader under its GPL-3.0-only option and includes Rust crates licensed only under Apache-2.0, and the combined app is distributed under GPLv3 terms, as the other Kairo apps are.

## Firmware the app ships

None of the 86Box ROM set ships with KairoX86: its files belong to their copyright owners. The app carries only free firmware, which runs inside the emulated PC, not linked into the app:

- [GLaBIOS](https://glabios.org/) 0.4.0, a free BIOS for the IBM PC and XT, under GPL-3.0: the project's release images, with their source in `third_party/glabios/`.
- A character ROM (the MDA and CGA fonts, `firmware/video/mda/mda.rom`) made for KairoX86 by `tools/make_font_rom.py` from Joseph Gil's public-domain PC fonts (`third_party/seabios-fonts/`, from SeaBIOS).
