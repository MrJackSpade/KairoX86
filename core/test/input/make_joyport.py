#!/usr/bin/env python3
"""Writes KairoX86's game port test machines (KairoX86#52): the 486 booting a floppy whose boot
sector (joyport.S) shows what the game port reads, once for each of three joystick models, and
prints the game_profile script that pushes each of its inputs in turn.

  make_joyport.py <out folder>

Each machine: game_profile <ROM set> <work> <out folder>/<model> 1500 "<script>" --shots 30
Shot frame 900 has nothing pressed; each later multiple of 60 (960 to 1500) has one of the joystick
model's inputs (kairo_x86.h) pushed: buttons 1 to 4, axes 0 to 3 to their positive end, axis 0 to its
negative end, then nothing. The boot sector shows what the port's wires read for each.
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
joystick_type = {model}

[Floppy and CD-ROM drives]
fdd_01_type = 35_2hd
fdd_01_fn = joyport.img
fdd_02_type = none
"""

MODELS = ['2axis_2button', '2axis_4button', '4axis_4button']

# F1 past the BIOS's CMOS prompt, then one input at a time.
PRESSES = ['j1', 'j2', 'j3', 'j4', 'p0', 'p1', 'p2', 'p3', 'n0']


def script():
    events = []
    for frame in (150, 300, 450, 600):
        events += [f'{frame}:+0x3b', f'{frame + 4}:-0x3b']
    frame = 930
    for line in PRESSES:
        events += [f'{frame}:+{line}', f'{frame + 60}:-{line}']
        frame += 60
    return ','.join(events)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1]).resolve()
    sector = boot_sector(HERE / 'joyport.S', out / '.asm', 'joyport')
    for model in MODELS:
        machine = out / model
        machine.mkdir(parents=True, exist_ok=True)
        write_floppy(machine / 'joyport.img', sector)
        (machine / '86box.cfg').write_text(CONFIG.format(model=model), encoding='utf-8', newline='\n')
    print(script())


if __name__ == '__main__':
    main()
