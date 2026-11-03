#!/usr/bin/env python3
"""Writes KairoX86's DOS prompt test machine (KairoX86#46): the 486 booting a copy of the FreeDOS 1.3
floppy edition (x86BOOT.img, not in the repository) whose FDCONFIG.SYS and FDAUTO.BAT are rewritten
so it boots straight to FreeCOM's A:\\> prompt, with no installer.

  make_dos.py <FreeDOS x86BOOT.img> <out folder>

Then: game_profile <ROM set> <work> <out folder>/dos 1800 "<script>" --commands "ECHO KAIRO X86" --shots 300
prints "typed <frame>", and the shots after it show KAIRO X86 echoed below the command.
"""
import shutil
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'input'))
from make_mouse import CONFIG  # noqa: E402

FILES = {
    'FDCONFIG.SYS': b'SHELL=A:\\FREEDOS\\BIN\\COMMAND.COM A:\\FREEDOS\\BIN /E:1024 /P=A:\\FDAUTO.BAT\r\n',
    'FDAUTO.BAT': b'@ECHO OFF\r\nPROMPT $P$G\r\n',
}


def rewrite(image, name, content):
    """Puts content in the root directory's file name, in place: in its first cluster, with its size."""
    data = bytearray(image.read_bytes())
    bps, spc, reserved, fats, roots, _total, _media, spf = struct.unpack_from('<HBHBHHBH', data, 11)
    root = (reserved + fats * spf) * bps
    base, ext = name.split('.')
    wanted = base.ljust(8).encode('ascii') + ext.ljust(3).encode('ascii')
    for at in range(root, root + roots * 32, 32):
        if bytes(data[at:at + 11]) != wanted:
            continue
        cluster = struct.unpack_from('<H', data, at + 26)[0]
        if len(content) > spc * bps:
            raise SystemExit(f'{name}: {len(content)} bytes do not fit its first cluster')
        start = root + roots * 32 + (cluster - 2) * spc * bps
        data[start:start + len(content)] = content
        struct.pack_into('<I', data, at + 28, len(content))
        image.write_bytes(bytes(data))
        return
    raise SystemExit(f'no {name} in the root directory of {image}')


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    source, out = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
    machine = out / 'dos'
    machine.mkdir(parents=True, exist_ok=True)
    image = machine / 'freedos.img'
    shutil.copyfile(source, image)
    for name, content in FILES.items():
        rewrite(image, name, content)
    (machine / '86box.cfg').write_text(CONFIG.format(mouse='ps2', extra='', image='freedos.img'),
                                       encoding='utf-8', newline='\n')
    # F1 past the BIOS's CMOS prompt.
    print(','.join(f'{frame}:{sign}0x3b' for start in (150, 300, 450, 600)
                   for frame, sign in ((start, '+'), (start + 4, '-'))))


if __name__ == '__main__':
    main()
