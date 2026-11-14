#!/usr/bin/env python3
"""The free machine's checks (KairoX86#446): small guest programs on the free machine ("[i440FX]
KairoX86 PC", SeaBIOS, SeaVGABIOS on the GD5446), each run under game_profile and checked here.

  check_free.py <game_profile.exe> <ROM set> <work folder> [group ...]

Groups: modes, vbe, boot, sb16 (all of them when none is named), so a run can be split.

<ROM set> holds the app's free firmware (firmware/, as tools/exact.ps1 lays it over the set) and the
86Box ROM set the reference machine needs (the 486 with an S3 Trio64V2/DX and its own BIOS). Each run
goes through shared/tools/run-limited.ps1. Exits 0 only when every check passes:

- video modes: core/test/display/modes.S sets each BIOS mode and fills the screen. On the free machine
  every mode's picture is the size it is on the reference; every graphics mode's pixels are the
  reference's, one for one (the palette and the memory layout SeaVGABIOS sets are a VGA BIOS's).
- VBE: vbe.S sets VESA mode 101h and fills it through its window; the picture is the reference's.
- boot order: a floppy, a hard disk and an El Torito CD whose boot sectors (mark.S) halt at addresses
  of their own; each [KairoX86] boot_order boots the drive it names first, and an empty first drive
  passes to the next.
- Sound Blaster 16: sb16.S plays a 500 Hz square wave through the DSP's direct DAC; the machine's
  sound carries it (its level, and its pitch within 5%).
"""
import array
import re
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
from floppy import FLOPPY_BYTES, boot_sector  # noqa: E402
from PIL import Image  # noqa: E402

FREE = """[Machine]
machine = kairo_pc
cpu_family = i486dx2
cpu_speed = 66666666
cpu_multi = 2
cpu_use_dynarec = 1
fpu_type = internal
mem_size = 16384
time_sync = disabled

[Video]
gfxcard = cl_gd5446_migrated_pci

[Cirrus Logic GD5446 (PCI) #1]
bios = cl_gd5446_free_pci

[Input devices]
keyboard_type = keyboard_ps2

[Sound]
sndcard = {sound}
fm_driver = ymfm

[Storage controllers]
hdc = internal
{disks}
[KairoX86]
boot_order = {order}
"""

REFERENCE = """[Machine]
machine = 486ap4
cpu_family = i486dx2
cpu_speed = 66666666
cpu_multi = 2
cpu_use_dynarec = 1
fpu_type = internal
mem_size = 16384
time_sync = disabled

[Video]
gfxcard = s3_trio64v2dx_pci

[S3 Trio64V2/DX PCI #1]
bios = trio64v2dx_pci

[Input devices]
keyboard_type = keyboard_ps2

[Floppy and CD-ROM drives]
fdd_01_type = 35_2hd
fdd_01_fn = {image}
fdd_02_type = none
"""

# BIOS mode, its pixels (0 for text), as core/test/display/make_modes.py names them
MODES = [('text40', 0x01, 0, 0), ('text80', 0x03, 0, 0), ('cga4', 0x04, 320, 200), ('ega16', 0x0d, 320, 200),
         ('256', 0x13, 320, 200), ('640', 0x12, 640, 480)]

HDD_CYLINDERS, HDD_HEADS, HDD_SECTORS = 20, 16, 63

# The picture runs: frames, and F1 pressed through the reference's CMOS prompt (game_profile's script)
FRAMES = 1800
F1_PRESSES = ','.join(f'{f}:+0x3b,{f + 5}:-0x3b' for f in range(150, 900, 150))


def floppy_only(image):
    return f"""
[Floppy and CD-ROM drives]
fdd_01_type = 35_2hd
fdd_01_fn = {image}
fdd_02_type = none
"""


def el_torito(boot):
    """An ISO 9660 image whose El Torito boot record names a no-emulation boot image: boot."""
    sector = 2048
    image = bytearray(sector * 21)
    pvd = bytearray(sector)
    pvd[0], pvd[1:6], pvd[6] = 1, b'CD001', 1
    pvd[40:72] = b'KAIROX86 BOOT ORDER'.ljust(32)
    pvd[80:88] = struct.pack('<I', 21) + struct.pack('>I', 21)
    pvd[128:132] = struct.pack('<H', sector) + struct.pack('>H', sector)
    image[16 * sector:17 * sector] = pvd
    record = bytearray(sector)
    record[0], record[1:6], record[6] = 0, b'CD001', 1
    record[7:39] = b'EL TORITO SPECIFICATION'.ljust(32, b'\0')
    record[0x47:0x4b] = struct.pack('<I', 19)
    image[17 * sector:18 * sector] = record
    terminator = bytearray(sector)
    terminator[0], terminator[1:6], terminator[6] = 255, b'CD001', 1
    image[18 * sector:19 * sector] = terminator
    catalog = bytearray(sector)
    validation = bytearray(32)
    validation[0] = 1
    validation[30], validation[31] = 0x55, 0xaa
    words = struct.unpack('<16H', bytes(validation))
    validation[28:30] = struct.pack('<H', (-sum(words)) & 0xffff)
    catalog[0:32] = validation
    catalog[32:64] = struct.pack('<BBHBBHI', 0x88, 0, 0, 0, 0, 4, 20).ljust(32, b'\0')
    image[19 * sector:20 * sector] = catalog
    image[20 * sector:20 * sector + len(boot)] = boot
    return bytes(image)


def run(game_profile, roms, work, machine, frames, *options, script='-'):
    """game_profile's output (its exit code is not checked: the boot order runs end in a halt)."""
    if work.exists():
        for f in work.glob('*'):
            if f.is_file():
                f.unlink()
    work.mkdir(parents=True, exist_ok=True)
    limited = ROOT / 'shared' / 'tools' / 'run-limited.ps1'
    out = subprocess.run(['pwsh', '-NoProfile', '-File', str(limited), str(game_profile), str(roms), str(work),
                          str(machine), str(frames), script, *options], capture_output=True, text=True)
    return out.stdout + out.stderr


def picture(path):
    image = Image.open(path).convert('RGB')
    return image.size, image.tobytes()


GROUPS = ('modes', 'vbe', 'boot', 'sb16')


def main():
    if len(sys.argv) < 4 or any(g not in GROUPS for g in sys.argv[4:]):
        raise SystemExit(__doc__)
    game_profile, roms, work = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]).resolve()
    groups = set(sys.argv[4:]) or set(GROUPS)
    machines = work / 'machines'
    asm = work / '.asm'
    failures = []

    def check(ok, what, detail=''):
        print(('pass ' if ok else 'FAIL ') + what + (f': {detail}' if detail else ''))
        if not ok:
            failures.append(what)

    # Video modes and VBE: the free machine against the reference, frame 900 of each
    programs = []
    if 'modes' in groups:
        programs += [(f'mode-{name}', HERE.parent / 'display' / 'modes.S',
                      [f'MODE={mode}', f'WIDTH={w}', f'HEIGHT={h}'], w > 0) for name, mode, w, h in MODES]
    if 'vbe' in groups:
        programs += [('vbe', HERE / 'vbe.S', [], True)]
    for name, source, defines, pixels in programs:
        sector = boot_sector(source, asm, name, defines)
        shots = {}
        for kind, config in (('free', FREE.format(sound='none', disks=floppy_only(f'{name}.img'), order='a,cd,c')),
                             ('reference', REFERENCE.format(image=f'{name}.img'))):
            machine = machines / f'{kind}-{name}'
            machine.mkdir(parents=True, exist_ok=True)
            (machine / f'{name}.img').write_bytes(sector.ljust(FLOPPY_BYTES, b'\0'))
            (machine / '86box.cfg').write_text(config, encoding='utf-8', newline='\n')
            shot_dir = work / f'run-{kind}-{name}'
            # The reference's Award BIOS stops at its CMOS prompt on a new CMOS: F1 goes on
            out = run(game_profile, roms, shot_dir, machine, FRAMES, '--shots', '300',
                      script=F1_PRESSES if kind == 'reference' else '-')
            last = shot_dir / f'frame-{FRAMES - 300}.bmp'
            if not last.is_file():
                raise SystemExit(f'{kind}-{name} drew no frame {FRAMES - 300}:\n{out}')
            shots[kind] = picture(last)
        (free_size, free_pixels), (ref_size, ref_pixels) = shots['free'], shots['reference']
        check(free_size == ref_size, f'{name}: picture size', f'{free_size} (reference {ref_size})')
        if pixels:
            check(free_pixels == ref_pixels, f'{name}: pixels as the reference\'s')
        check(len(set(free_pixels)) > 1, f'{name}: drawn')

    if 'boot' in groups:
        # Boot order: floppy A (slot 1), hard disk C (slot 2), CD (slot 3)
        sectors = {slot: boot_sector(HERE / 'mark.S', asm, f'mark{slot}', [f'MARK={ord(mark)}', f'SLOT={slot}'])
                   for slot, mark in ((1, 'A'), (2, 'C'), (3, 'D'))}
        hdd_bytes = HDD_CYLINDERS * HDD_HEADS * HDD_SECTORS * 512
        cases = [('a,cd,c', True, 1), ('cd,a,c', True, 3), ('c,a,cd', True, 2), ('a,cd,c', False, 3), ('a,c', False, 2)]
        for order, floppy, expected in cases:
            name = f'boot-{order.replace(",", "-")}-{"floppy" if floppy else "nofloppy"}'
            machine = machines / name
            machine.mkdir(parents=True, exist_ok=True)
            (machine / 'a.img').write_bytes(sectors[1].ljust(FLOPPY_BYTES, b'\0'))
            (machine / 'c.img').write_bytes(sectors[2].ljust(hdd_bytes, b'\0'))
            (machine / 'd.iso').write_bytes(el_torito(sectors[3]))
            disks = (f"\n[Hard disks]\nhdd_01_fn = c.img\nhdd_01_ide_channel = 0:0\n"
                     f"hdd_01_parameters = {HDD_SECTORS}, {HDD_HEADS}, {HDD_CYLINDERS}, 0, ide\n"
                     f"\n[Floppy and CD-ROM drives]\nfdd_01_type = 35_2hd\n" + ("fdd_01_fn = a.img\n" if floppy else '') +
                     "fdd_02_type = none\ncdrom_01_parameters = 1, atapi\ncdrom_01_ide_channel = 1:0\ncdrom_01_image_path = d.iso\n")
            (machine / '86box.cfg').write_text(FREE.format(sound='none', disks=disks, order=order), encoding='utf-8', newline='\n')
            out = run(game_profile, roms, work / f'run-{name}', machine, 900)
            stop = re.search(r'halted.*\(at ([0-9A-F]{4}):([0-9A-F]{4,5})\)', out)
            slot = None
            if stop:
                linear = int(stop.group(1), 16) * 16 + int(stop.group(2), 16)
                slot = (linear - 0x7c00) // 0x40 if (linear - 0x7c00) % 0x40 == 0 else None
            check(slot == expected, f'{name}: boots slot {expected}', f'stopped {stop.group(0) if stop else "nowhere"}')

    if 'sb16' in groups:
        # Sound Blaster 16: the tone in the machine's sound
        sector = boot_sector(HERE / 'sb16.S', asm, 'sb16', [])
        machine = machines / 'sb16'
        machine.mkdir(parents=True, exist_ok=True)
        (machine / 'sb16.img').write_bytes(sector.ljust(FLOPPY_BYTES, b'\0'))
        (machine / '86box.cfg').write_text(FREE.format(sound='sb16', disks=floppy_only('sb16.img'), order='a'),
                                          encoding='utf-8', newline='\n')
        audio = work / 'sb16.raw'
        out = run(game_profile, roms, work / 'run-sb16', machine, 1200, '--audio', str(audio))
        rate = re.search(r'^audio (\d+)', out, re.M)
        check(rate is not None and audio.is_file(), 'sb16: sound written', out.strip().splitlines()[-1] if out.strip() else '')
        if rate and audio.is_file():
            samples = array.array('h', audio.read_bytes()[: (audio.stat().st_size // 4) * 4])
            left = samples[0::2]
            tail = left[len(left) // 2:]                      # the second half: the tone, well past boot
            mean = sum(tail) / max(len(tail), 1)
            level = (sum((s - mean) ** 2 for s in tail) / max(len(tail), 1)) ** 0.5
            crossings = sum(1 for a, b in zip(tail, tail[1:]) if (a - mean) < 0 <= (b - mean))
            pitch = crossings / (len(tail) / int(rate.group(1)))
            check(level > 1000, 'sb16: the tone is heard', f'level {level:.0f}')
            check(abs(pitch - 500) <= 25, 'sb16: at 500 Hz', f'{pitch:.1f} Hz')

    print(f'{len(failures)} failed' if failures else 'every check passed')
    sys.exit(1 if failures else 0)

if __name__ == '__main__':
    main()
