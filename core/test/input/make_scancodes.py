#!/usr/bin/env python3
"""Writes KairoX86's raw keyboard test machine (KairoX86#114): the 486 booting a floppy whose boot
sector (scancodes.S) shows every byte the keyboard sends in hex, make and break codes alike, so a key
left held shows its make code with no break code after it (1C, then 9C, for Enter).

  make_scancodes.py <out folder>     writes <out folder>/scancodes
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
    machine = out / 'scancodes'
    machine.mkdir(parents=True, exist_ok=True)
    write_floppy(machine / 'scancodes.img', boot_sector(HERE / 'scancodes.S', out / '.asm', 'scancodes', []))
    (machine / '86box.cfg').write_text(CONFIG.format(mouse='ps2', extra='', image='scancodes.img'), encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
