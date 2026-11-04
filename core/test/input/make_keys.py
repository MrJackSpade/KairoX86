#!/usr/bin/env python3
"""Writes KairoX86's key test machine (KairoX86#95): the 486 booting a floppy whose boot sector
(keys.S MODE_SCAN) shows each key the BIOS gets as its scan code in hex, so the cursor keys show
as well as the rest (48 up, 50 down, 4B left, 4D right, 1C Enter, 39 Space).

  make_keys.py <out folder>     writes <out folder>/keys-scan
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from floppy import boot_sector, write_floppy  # noqa: E402
from make_mouse import CONFIG  # noqa: E402


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1]).resolve()
    machine = out / 'keys-scan'
    machine.mkdir(parents=True, exist_ok=True)
    write_floppy(machine / 'keys-scan.img', boot_sector(HERE / 'keys.S', out / '.asm', 'keys-scan', ['MODE=MODE_SCAN']))
    (machine / '86box.cfg').write_text(CONFIG.format(mouse='ps2', extra='', image='keys-scan.img'), encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
