"""Boot floppies for KairoX86's core tests: a boot sector assembled from a .S file with llvm-mingw's
clang and ld.lld (the host test's toolchain), padded to a 1.44 MB image.

Used by core/test/stops/make_floppies.py and core/test/display/make_raster.py.
"""
import subprocess
from pathlib import Path

TOOLCHAIN = Path('G:/tools/llvm-mingw-20261006-ucrt-x86_64/bin')
FLOPPY_BYTES = 1474560


def boot_sector(source, work, name, defines=()):
    """Assembles source (a .S file whose code starts at 0x7c00) into one signed 512-byte sector."""
    work.mkdir(parents=True, exist_ok=True)
    obj, image = work / f'{name}.o', work / f'{name}.bin'
    subprocess.run([str(TOOLCHAIN / 'clang.exe'), '--target=i386-unknown-none-elf', '-c',
                    *[f'-D{d}' for d in defines], str(source), '-o', str(obj)], check=True)
    subprocess.run([str(TOOLCHAIN / 'ld.lld.exe'), '-m', 'elf_i386', '--image-base=0x7000', '-Ttext=0x7c00',
                    '-e', '_start', '--oformat=binary', str(obj), '-o', str(image)], check=True)
    sector = image.read_bytes()
    if len(sector) != 512 or sector[510:] != b'\x55\xaa':
        raise SystemExit(f'{name}: the boot sector is {len(sector)} bytes, not one signed sector')
    return sector


def write_floppy(path, sector):
    """A 1.44 MB image holding sector as its boot sector."""
    Path(path).write_bytes(sector.ljust(FLOPPY_BYTES, b'\0'))
