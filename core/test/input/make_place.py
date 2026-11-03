#!/usr/bin/env python3
"""Writes KairoX86's direct touch test machines (KairoX86#44): the 486 booting a floppy whose boot
sector (place.S) is a DOS mouse game with its own simplest mouse driver, which shows the position the
driver gives, once for each way the driver's span is set.

  make_place.py <out folder>

Each machine: game_profile <ROM set> <work> <out folder>/<name> 1200 "<script>" --place 960:<x>:<y>
--shots 100, and shot frame 1100 shows the driver's position for picture point (x, y):

  place-text   80x25 text (a 720x400 picture), the default span 640x200: (360, 200) is 0140 0064
  place-range  the same with the span set to 0-999 by 0-499: (360, 200) is 01F4 00FA
  place-vga    mode 13h (86Box draws it 640x400), the default span 640x200: (320, 200) is 0140 0064
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from floppy import boot_sector, write_floppy  # noqa: E402
from make_mouse import CONFIG  # noqa: E402

MACHINES = [('place-text', 'MODE_TEXT'), ('place-range', 'MODE_RANGE'), ('place-vga', 'MODE_VGA')]


def script():
    # F1 past the BIOS's CMOS prompt.
    return ','.join(f'{frame}:{sign}0x3b' for start in (150, 300, 450, 600)
                    for frame, sign in ((start, '+'), (start + 4, '-')))


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1]).resolve()
    for name, mode in MACHINES:
        machine = out / name
        machine.mkdir(parents=True, exist_ok=True)
        write_floppy(machine / f'{name}.img', boot_sector(HERE / 'place.S', out / '.asm', name, [f'MODE={mode}']))
        (machine / '86box.cfg').write_text(CONFIG.format(mouse='ps2', extra='', image=f'{name}.img'),
                                           encoding='utf-8', newline='\n')
    print(script())


if __name__ == '__main__':
    main()
