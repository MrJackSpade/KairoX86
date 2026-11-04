#!/usr/bin/env python3
"""Writes KairoX86's sound test machine (KairoX86#117): the 486 booting a floppy whose boot sector
(tone.S) plays a stepping PC speaker tone without a pause and takes every input, for checking that
the sound never crackles or drops under touch, mouse and controller input.

  make_tone.py <out folder>     writes <out folder>/tone
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
    machine = out / 'tone'
    machine.mkdir(parents=True, exist_ok=True)
    write_floppy(machine / 'tone.img', boot_sector(HERE / 'tone.S', out / '.asm', 'tone', []))
    (machine / '86box.cfg').write_text(CONFIG.format(mouse='ps2', extra='', image='tone.img'), encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
