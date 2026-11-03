#!/usr/bin/env python3
"""Writes KairoX86's character ROM, firmware/video/mda/mda.rom, from the public-domain PC fonts in
third_party/seabios-fonts/vgafonts.c (Joseph Gil's, as SeaBIOS carries them): the free stand-in for
the IBM MDA/CGA character ROM, which 86Box needs for every MDA, CGA and Hercules card.

  make_font_rom.py <app root> [--check]   (--check fails when the committed ROM is out of date)

The layout is the IBM ROM's, as 86Box reads it (video_load_font, FONT_FORMAT_MDA): 8 KB, the MDA's
8x14 glyphs as their lines 0-7 at 0x0000 and lines 8-13 (and two blank) at 0x0800, then the CGA's
8x8 glyphs at 0x1000 (the thin font) and 0x1800 (the thick font, which 86Box takes). Code page 437.
"""
import argparse
import re
import sys
from pathlib import Path

OUT = Path("firmware/video/mda/mda.rom")


def font(source, name, height):
    match = re.search(rf"u8 {name}\[256 \* {height}\] VAR16 = \{{(.*?)\}};", source, re.S)
    if not match:
        raise SystemExit(f"{name} not found")
    values = [int(v, 16) for v in re.findall(r"0x[0-9a-fA-F]{2}", match.group(1))]
    if len(values) != 256 * height:
        raise SystemExit(f"{name}: {len(values)} bytes, expected {256 * height}")
    return [values[c * height:(c + 1) * height] for c in range(256)]


def rom(source):
    mda = font(source, "vgafont14", 14)
    cga = font(source, "vgafont8", 8)
    data = bytearray(8192)
    for c in range(256):
        data[c * 8:c * 8 + 8] = bytes(mda[c][0:8])
        data[0x800 + c * 8:0x800 + c * 8 + 6] = bytes(mda[c][8:14])
        data[0x1000 + c * 8:0x1000 + c * 8 + 8] = bytes(cga[c])
        data[0x1800 + c * 8:0x1800 + c * 8 + 8] = bytes(cga[c])
    return bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = (args.root / "third_party/seabios-fonts/vgafonts.c").read_text(encoding="utf-8")
    data = rom(source)
    out = args.root / OUT
    if args.check:
        if not out.is_file() or out.read_bytes() != data:
            sys.exit(f"{OUT} is out of date: run tools/make_font_rom.py")
        print(f"{OUT} is current")
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
