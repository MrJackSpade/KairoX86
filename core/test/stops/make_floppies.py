#!/usr/bin/env python3
"""Writes KairoX86's stop tests (KairoX86#34): one machine folder per way a PC stops, each booting a
floppy whose boot sector (boot.S) stops it that way, and the boot_test machine list that expects each
stop.

  make_floppies.py <out folder>

Assembles boot.S with core/test/floppy.py (llvm-mingw's clang and ld.lld). Prints the machine
list for boot_test's third argument:

  boot_test <ROM set> <work folder> "<list>" 20

The halt, keyboard and idle machines are the 486 the other host tests use; power off and Voodoo are
an Intel 440BX board (ABIT BX6, PIIX4 ACPI) with a Voodoo 2. Their firmware comes from the ROM set.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from floppy import boot_sector, write_floppy  # noqa: E402

M486 = """[Machine]
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
fdd_01_fn = boot.img
fdd_02_type = none
"""

BX6 = """[Machine]
machine = bx6
cpu_family = pentium2_deschutes
cpu_speed = 300000000
cpu_multi = 4.5
cpu_use_dynarec = 1
fpu_type = internal
mem_size = 65536
time_sync = disabled

[Video]
gfxcard = s3_trio64v2dx_pci
voodoo = {voodoo}

[S3 Trio64V2/DX PCI #1]
bios = trio64v2dx_pci

[3Dfx Voodoo Graphics]
type = voodoo_2

[Input devices]
keyboard_type = keyboard_ps2
mouse_type = ps2

[Floppy and CD-ROM drives]
fdd_01_type = 35_2hd
fdd_01_fn = boot.img
fdd_02_type = none
"""

# (folder, boot.S MODE, configuration, the stop boot_test expects or None)
TESTS = [
    ('idle', 5, M486, None),
    ('halt', 1, M486, 'The PC halted'),
    ('keyboard', 2, M486, 'Scan code set [05] invalid'),
    ('power-off', 3, BX6.format(voodoo=0), 'The PC turned itself off'),
    ('voodoo', 4, BX6.format(voodoo=1), 'bad blit command'),
]


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1]).resolve()
    work = out / '.asm'
    work.mkdir(parents=True, exist_ok=True)
    machines = []
    for folder, mode, cfg, stop in TESTS:
        machine = out / folder
        machine.mkdir(parents=True, exist_ok=True)
        write_floppy(machine / 'boot.img', boot_sector(HERE / 'boot.S', work, f'boot{mode}', [f'MODE={mode}']))
        (machine / '86box.cfg').write_text(cfg, encoding='utf-8', newline='\n')
        for stale in machine.glob('nvr'):
            for file in stale.iterdir():
                file.unlink()
        machines.append(str(machine) + ('>' + stop if stop else ''))
    print('|'.join(machines))


if __name__ == '__main__':
    main()
