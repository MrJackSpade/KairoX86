"""KairoX86's third-party notices: the sources shared/tools/notices.py writes kairox86/src/main/assets/THIRD_PARTY_NOTICES.txt from.
Run it again after an import."""
from notices import excerpt, text

OUT = 'kairox86/src/main/assets/THIRD_PARTY_NOTICES.txt'

HEADER = '''KairoX86 third-party notices
These notices apply to the emulator code and libraries in this package. KairoX86 emulates IBM PC
compatibles with 86Box; KairoX86 is not affiliated with the 86Box project or with IBM.'''

BOX_TERMS = '''86Box is distributed under the GNU General Public License, version 2 or (at your option) any
later version. Its authors are listed in AUTHORS of its source. A few of its files carry other
terms, given below. Its license statement and the GPL version 2 text follow. KairoX86 replaces its
GPL-2.0-only cassette code with its own (GPL-2.0-or-later) and does not build its VDE networking.'''

GLABIOS_TERMS = '''GLaBIOS is a free BIOS for the IBM PC and XT, distributed under the GNU General Public License,
version 3. KairoX86 ships its 0.4.0 release images (GLABIOS_0.4.0_8P.ROM, GLABIOS_0.4.0_VP.ROM),
which run inside the emulated PC as its firmware; their source is in third_party/glabios of
KairoX86's source. Its license follows.'''

FONT_TERMS = '''KairoX86's character ROM (the MDA and CGA fonts, firmware/video/mda/mda.rom, written by
tools/make_font_rom.py) is made from the PC fonts in SeaBIOS's vgasrc/vgafonts.c, which say:'''

# (title, source, [text]) in the order shown.
SECTIONS = [
    ('86Box', 'https://86box.net/, third_party/86box',
     [BOX_TERMS, excerpt('86box/README.md', '86Box is released under', '86Box is released under'),
      text('86box/COPYING')]),
    ('86Box: files by Fred N. van Kempen (BSD-3-Clause)', 'third_party/86box/src/device/isamem.c and others',
     [excerpt('86box/src/device/isamem.c', 'Copyright 2018      Fred N. van Kempen.', 'POSSIBILITY OF SUCH DAMAGE')]),
    ('86Box: Berkeley SoftFloat 3e (BSD-3-Clause)', 'third_party/86box/src/cpu/softfloat3e',
     [text('86box/src/cpu/softfloat3e/COPYING.txt')]),
    ('86Box: ymfm by Aaron Giles (BSD-3-Clause)', 'third_party/86box/src/sound/ymfm',
     [excerpt('86box/src/sound/ymfm/ymfm.h', 'BSD 3-Clause License', 'POSSIBILITY OF SUCH DAMAGE')]),
    ('86Box: crcspeed by Matt Stancliff (BSD-3-Clause)', 'third_party/86box/src/crcspeed',
     [excerpt('86box/src/crcspeed/crc64speed.c', 'Copyright (c) 2014, Matt Stancliff', 'POSSIBILITY OF SUCH DAMAGE')]),
    ('86Box: Dear ImGui (MIT)', 'third_party/86box/src/osd/imgui',
     [text('86box/src/osd/imgui/LICENSE.txt')]),
    ('86Box: Aaru format identification by Natalia Portillo (LGPL-2.1-or-later)', 'third_party/86box/src/cdrom/cdrom_aaru.c',
     [excerpt('86box/src/cdrom/cdrom_aaru.c', 'Format identification code (C) Natalia Portillo', 'Format identification code (C) Natalia Portillo')]),
    ('libsndfile 1.2.2 (LGPL-2.1-or-later)', 'https://libsndfile.github.io/libsndfile/, third_party/libsndfile',
     [text('libsndfile/COPYING')]),
    ('FreeType 2.13.3 (FreeType License)', 'https://freetype.org/, third_party/freetype',
     [text('freetype/docs/FTL.TXT')]),
    ('GLaBIOS 0.4.0 (GPL-3.0)', 'https://github.com/640-KB/GLaBIOS, third_party/glabios',
     [GLABIOS_TERMS, text('glabios/LICENSE')]),
    ('PC fonts by Joseph Gil (public domain)', 'third_party/seabios-fonts/vgafonts.c (from SeaBIOS)',
     [FONT_TERMS, excerpt('seabios-fonts/vgafonts.c', 'These fonts come from', 'The individual fonts are public domain')]),
    ('zlib 1.3.2', 'https://zlib.net/, shared/third_party/zlib', [text('../shared/third_party/zlib/LICENSE')]),
    ('libpng 1.6.59', 'http://www.libpng.org/pub/png/libpng.html, shared/third_party/libpng',
     [text('../shared/third_party/libpng/LICENSE')]),
]
