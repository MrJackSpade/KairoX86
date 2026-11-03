#!/usr/bin/env python3
"""Writes KairoX86's native size test machines (KairoX86#37): one machine per video mode, each booting
a floppy (modes.S) that sets the mode and fills the screen, on the 486 with a VGA (S3 Trio64V2) and on
the IBM PC with a CGA, and prints each machine with the picture size the core must hand over.

  make_modes.py <out folder>

Each machine: game_profile <ROM set> <work> <out folder>/<name> 1200 "<script>" --shots 300, on a build
configured with -DCMAKE_C_FLAGS=-DKAIROX86_CHECK_NATIVE_SIZE (every pixel dropped across checked
against the one kept): it must run to the end, and frame-900.bmp must be the size printed.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from floppy import boot_sector  # noqa: E402

VGA = """[Machine]
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

[Floppy and CD-ROM drives]
fdd_01_type = 35_2hd
fdd_01_fn = {image}
fdd_02_type = none
"""

CGA = """[Machine]
machine = ibmpc
cpu_family = 8088
cpu_speed = 4772728
mem_size = 640
time_sync = disabled

[Video]
gfxcard = cga

[Input devices]
keyboard_type = keyboard_pc_xt

[Floppy and CD-ROM drives]
fdd_01_type = 525_2dd
fdd_01_fn = {image}
fdd_02_type = none
"""

# Name, card, BIOS mode, its pixels (graphics), and the picture the core must hand over: VGA scans
# every 200-line mode at 400 lines, which are its own; CGA's 200 lines are drawn twice for the window.
MACHINES = [
    ('vga-text40', VGA, 0x01, 0, 0, '360x400'),
    ('vga-text80', VGA, 0x03, 0, 0, '720x400'),
    ('vga-cga4', VGA, 0x04, 320, 200, '320x400'),
    ('vga-ega16', VGA, 0x0d, 320, 200, '320x400'),
    ('vga-256', VGA, 0x13, 320, 200, '320x400'),
    ('vga-640', VGA, 0x12, 640, 480, '640x480'),
    ('cga-text40', CGA, 0x01, 0, 0, '320x200'),
    ('cga-text80', CGA, 0x03, 0, 0, '640x200'),
    ('cga-320', CGA, 0x04, 320, 200, '320x200'),
    ('cga-640', CGA, 0x06, 640, 200, '640x200'),
]

FLOPPY_BYTES = {VGA: 1474560, CGA: 368640}


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1]).resolve()
    for name, card, mode, width, height, picture in MACHINES:
        machine = out / name
        machine.mkdir(parents=True, exist_ok=True)
        sector = boot_sector(HERE / 'modes.S', out / '.asm', name, [f'MODE={mode}', f'WIDTH={width}', f'HEIGHT={height}'])
        (machine / f'{name}.img').write_bytes(sector.ljust(FLOPPY_BYTES[card], b'\0'))
        (machine / '86box.cfg').write_text(card.format(image=f'{name}.img'), encoding='utf-8', newline='\n')
        print(name, picture)


if __name__ == '__main__':
    main()
