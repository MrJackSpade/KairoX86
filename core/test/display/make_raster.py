#!/usr/bin/env python3
"""Writes KairoX86's raster test machine (KairoX86#38): the 486 with an S3 Trio64V2 booting a floppy
whose boot sector (raster.S) changes the palette and the video memory while each frame is drawn.

  make_raster.py <out folder>

Run it with game_profile on a normal build and on one with KAIROX86_SYNC_RENDER (every line drawn in
place) and compare the hashes: they must match. F1 at frame 150 passes the BIOS's CMOS prompt:

  game_profile <ROM set> <work> <out folder>/raster 900 150:+0x3b,154:-0x3b --hashes <file>
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from floppy import boot_sector, write_floppy  # noqa: E402

CONFIG = """[Machine]
machine = 486ap4
cpu_family = i486dx2
cpu_speed = 66666666
cpu_multi = 2
cpu_use_dynarec = 1
fpu_type = internal
mem_size = 32768
time_sync = disabled

[Video]
gfxcard = s3_trio64v2dx_pci

[S3 Trio64V2/DX PCI #1]
bios = trio64v2dx_pci

[Input devices]
keyboard_type = keyboard_ps2
mouse_type = ps2

[Floppy and CD-ROM drives]
fdd_01_type = 35_2hd
fdd_01_fn = raster.img
fdd_02_type = none
"""


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1]).resolve()
    machine = out / 'raster'
    machine.mkdir(parents=True, exist_ok=True)
    write_floppy(machine / 'raster.img', boot_sector(HERE / 'raster.S', out / '.asm', 'raster'))
    (machine / '86box.cfg').write_text(CONFIG, encoding='utf-8', newline='\n')
    print(machine)


if __name__ == '__main__':
    main()
