#!/usr/bin/env python3
"""Writes KairoX86's hard disk test machine (KairoX86#49): an Intel 440BX board (ABIT BX6, whose BIOS
finds IDE disks itself) with no floppy disk and an IDE hard disk
image (306 cylinders, 4 heads, 17 sectors: 10 MB) whose first sector is the halt test's boot sector
(core/test/stops/boot.S, MODE_HALT). Booting from the hard disk prints "STOP 1" and halts with
interrupts off, so boot_test's expected stop proves the machine booted from it:

  make_hdd.py <out folder>
  boot_test <ROM set> <work> "<out folder>/hdd>The PC halted" 30 "" 150:0x3b,300:0x3b,450:0x3b,600:0x3b
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from floppy import boot_sector  # noqa: E402

CYLINDERS, HEADS, SECTORS = 306, 4, 17

CONFIG = f"""[Machine]
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

[S3 Trio64V2/DX PCI #1]
bios = trio64v2dx_pci

[Input devices]
keyboard_type = keyboard_ps2
mouse_type = ps2

[Hard disks]
hdd_01_parameters = {SECTORS}, {HEADS}, {CYLINDERS}, 0, ide
hdd_01_fn = hdd.img
hdd_01_ide_channel = 0:0

[Floppy and CD-ROM drives]
fdd_01_type = 35_2hd
fdd_02_type = none
"""


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1]).resolve()
    machine = out / 'hdd'
    machine.mkdir(parents=True, exist_ok=True)
    sector = bytearray(boot_sector(HERE.parent / 'stops' / 'boot.S', out / '.asm', 'hdd-halt', ['MODE=1']))
    # A master boot record's partition table: one active partition from the second track to the end
    # (BIOSes boot a hard disk only with an active partition).
    total = CYLINDERS * HEADS * SECTORS
    last = CYLINDERS - 1
    sector[446:462] = bytes([0x80, 1, 1, 0, 0x01, HEADS - 1, SECTORS | ((last >> 8) << 6), last & 0xff]) \
        + SECTORS.to_bytes(4, 'little') + (total - SECTORS).to_bytes(4, 'little')
    (machine / 'hdd.img').write_bytes(bytes(sector).ljust(total * 512, b'\0'))
    (machine / '86box.cfg').write_text(CONFIG, encoding='utf-8', newline='\n')
    print(machine)


if __name__ == '__main__':
    main()
