#!/usr/bin/env python3
"""The HD44780 LCD's check (KairoX86#256, for #283): the Cobalt 3000 (cobalt3k_carmel, its LCD the only display), its
firmware writing the panel as it boots, run under game_profile with Hardware acceleration off and on, every frame's
picture compared. #283's batch cannot hold it: the board has no floppy to boot a test from.

  hd44780.py <folder of game_profile.exe> <frames> <out folder>

Exits 1 unless every frame is the same."""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

binary, frames, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
for side in ('off', 'on'):
    d = out / side
    shutil.rmtree(d, ignore_errors=True)
    (d / 'machine').mkdir(parents=True)
    (d / 'work').mkdir(parents=True)
    (d / 'machine' / '86box.cfg').write_text(
        "[Machine]\nmachine = cobalt3k_carmel\ncpu_use_dynarec = 1\nfpu_type = internal\ntime_sync = disabled\nmem_size = 65536\n\n"
        "[Video]\ngfxcard = none\n\n[Storage controllers]\nhdc = none\n\n"
        f"[KairoX86]\nhardware_acceleration = {1 if side == 'on' else 0}\n", newline='\n')
    gp = str(Path(binary) / 'game_profile.exe')
    r = subprocess.run([gp, r'G:\tools\src\86box-roms', str(d / 'work'), str(d / 'machine'), frames, '-', '--shots', '1'],
                       capture_output=True, text=True, cwd=binary)
    print(side, [l for l in (r.stdout + r.stderr).splitlines() if l.startswith(('started', 'host', 'FAIL', 'kairo-gpu'))])


def pictures(side):
    return {int(p.stem[6:]): hashlib.md5(p.read_bytes()).hexdigest() for p in (out / side / 'work').glob('frame-*.bmp')}


a, b = pictures('off'), pictures('on')
bad = [n for n in sorted(a) if a.get(n) != b.get(n)]
changes = len(set(a.values()))
same = not bad and set(a) == set(b)
print(f'{len(a)}/{len(b)} frames, {changes} different pictures,', 'same' if same else f'differ from frame {bad[0] if bad else "?"}')
sys.exit(0 if same else 1)
