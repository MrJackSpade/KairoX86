#!/usr/bin/env python3
"""Writes KairoX86's Auto touch mode test machines (KairoX86#43): the 486 booting a floppy that
stands in for a game, one for each way a game reads its input, and prints the game_profile script
that gets past the BIOS and types one key.

  make_auto.py <out folder>

Each machine: game_profile <ROM set> <work> <out folder>/<name> 1200 "<script>"
and its "input" line (the guest's BIOS keyboard waits and polls, mouse driver reads, and whether it
waits for a key at the end) must show what the machine stands in for:

  auto-wait   keys.S MODE_WAIT: gets keys through the BIOS, which waits for each: waits, waiting 1
  auto-poll   keys.S MODE_POLL: checks for a key over and over: polls, waiting 0
  auto-mouse  mouse.S MODE_PS2 with INT33: asks the mouse driver for the mouse on every pass:
              mouse reads, no waits or polls past the BIOS's own
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from floppy import boot_sector, write_floppy  # noqa: E402
from make_mouse import CONFIG  # noqa: E402

# The machine's folder name, its boot sector, and that sector's defines.
MACHINES = [('auto-wait', 'keys.S', ['MODE=MODE_WAIT']),
            ('auto-poll', 'keys.S', ['MODE=MODE_POLL']),
            ('auto-mouse', 'mouse.S', ['MODE=MODE_PS2', 'INT33'])]


def script():
    events = []
    # F1 past the BIOS's CMOS prompt, then A typed once.
    for frame in (150, 300, 450, 600):
        events += [f'{frame}:+0x3b', f'{frame + 4}:-0x3b']
    events += ['900:+0x1e', '904:-0x1e']
    return ','.join(events)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1]).resolve()
    for name, source, defines in MACHINES:
        machine = out / name
        machine.mkdir(parents=True, exist_ok=True)
        write_floppy(machine / f'{name}.img', boot_sector(HERE / source, out / '.asm', name, defines))
        (machine / '86box.cfg').write_text(CONFIG.format(mouse='ps2', extra='', image=f'{name}.img'), encoding='utf-8', newline='\n')
    print(script())


if __name__ == '__main__':
    main()
