#!/usr/bin/env python3
"""Writes KairoX86's mouse test machines (KairoX86#50): the 486 booting a floppy whose boot sector
(mouse.S) reads its mouse straight from the port and shows what it reads, once with a PS/2 mouse and
once with a Microsoft serial mouse on COM1, and prints the game_profile script that moves the mouse
and presses each button in turn.

  make_mouse.py <out folder>

Each machine: game_profile <ROM set> <work> <out folder>/<model> 1440 "<script>" --shots 30
Shot frame 900 has the mouse untouched; each later multiple of 60 (960 to 1380) has had one more
input: 40 pixels right, 40 down, 10 left, 10 up, then the left, right and middle buttons one at a
time (the serial mouse, a Microsoft two-button one, has no middle button), then nothing.
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
mouse_type = {mouse}
{extra}
[Floppy and CD-ROM drives]
fdd_01_type = 35_2hd
fdd_01_fn = mouse.img
fdd_02_type = none
"""

# The machine's folder name, its 86Box mouse, that mouse's settings and mouse.S's MODE. The PS/2
# mouse gets a middle button (86Box's default is two).
MODELS = [('ps2', 'ps2', '\n[PS/2 Mouse]\nbuttons = 3\n', 'MODE_PS2'),
          ('serial', 'msserial', '', 'MODE_SERIAL')]

# One at a time: motion (left there), then each button (let go after a shot).
MOVES = ['+x40', '+y40', '-x10', '-y10']
BUTTONS = ['m1', 'm2', 'm3']


def script():
    events = []
    # F1 past the BIOS's CMOS prompt.
    for frame in (150, 300, 450, 600):
        events += [f'{frame}:+0x3b', f'{frame + 4}:-0x3b']
    frame = 930
    for move in MOVES:
        events.append(f'{frame}:{move}')
        frame += 60
    for button in BUTTONS:
        events += [f'{frame}:+{button}', f'{frame + 60}:-{button}']
        frame += 60
    return ','.join(events)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1]).resolve()
    for name, mouse, extra, mode in MODELS:
        machine = out / name
        machine.mkdir(parents=True, exist_ok=True)
        sector = boot_sector(HERE / 'mouse.S', out / '.asm', f'mouse-{name}', [f'MODE={mode}'])
        write_floppy(machine / 'mouse.img', sector)
        (machine / '86box.cfg').write_text(CONFIG.format(mouse=mouse, extra=extra), encoding='utf-8', newline='\n')
    print(script())


if __name__ == '__main__':
    main()
