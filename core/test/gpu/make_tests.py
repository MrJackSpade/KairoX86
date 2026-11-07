#!/usr/bin/env python3
"""Builds KairoX86's graphics test floppies (KairoX86#283): each test program (<name>.c here, with runtime.c)
compiled with llvm-mingw's clang for 16-bit real mode (-m16), linked at 0x8000, and written after the loader
(loader.S) on a 1.44 MB floppy image <out folder>/<name>.img. A test for the 8086 machines (KairoX86#311-#324) is
<name>.S, 8086 assembly with rt86.S, written after the loader without the A20 line or unreal mode on a 360 KB
floppy image (compare.py runs those tests on those machines only). The IBM 5550's test (epoch86.S) is booted by its
own IPL, which takes no PC boot sector: it is that IPL's load module on a 720 KB image (ipl_5550_image).

  make_tests.py <out folder> [test ...]     every test (each .c but runtime.c) when none is named
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from floppy import TOOLCHAIN, FLOPPY_BYTES, boot_sector  # noqa: E402

CFLAGS = ['--target=i386-unknown-none-elf', '-m16', '-march=i486', '-ffreestanding', '-fno-pic', '-fno-builtin',
          '-fno-stack-protector', '-fno-asynchronous-unwind-tables', '-Os', '-Wall', '-Werror']
LINK = """SECTIONS {
    . = 0x8000;
    .text : { *(.text.entry) *(.text*) }
    .rodata : { *(.rodata*) }
    .data : { *(.data*) }
    /DISCARD/ : { *(.comment) *(.note*) }
}
"""
# The program runs from 0x8000 up to the 64 KB its code segment (0) reaches
MAX_BYTES = 0x10000 - 0x8000
# The 8086 machines' tests: a 360 KB floppy, 9 sectors a track
FLOPPY_360K = 368640
SOURCES_8086 = ('loader.S', 'rt86.S')
# The IBM 5550's tests: its IPL's load modules on its DSQD drive's 720 KB, 9 sectors a track
TESTS_5550 = ('epoch86',)
FLOPPY_720K = 737280


def ipl_5550_image(program):
    """The IBM 5550 IPL's disk (ipl5550.rom, FC00:0C00): record 0 (C0 H0 R1, 512 bytes) its IPL record, which the IPL
    takes with D7h at 0Ah, EBCDIC "IBM5550" and six spaces at 18h, 48h at 49h for 9 sectors a track, and the load
    module's header at the record (108h) and of the bytes (10Ah) given. The header (FE54:0): its entries' count at 0Ch,
    each entry 16 bytes from 10h: its first record (+2), its bytes (+4), its segment (+6), its flags (+8; bit 0 the
    entry point), the entry point's offset (+Ah) and where it is read to in its segment (+Eh). One entry: the program
    at 0:8000h, its entry point there, as the other 8086 tests run."""
    sectors = (len(program) + 511) // 512
    ipl = bytearray(512)
    ipl[0x0a] = 0xd7
    ipl[0x18:0x25] = ('IBM5550' + ' ' * 6).encode('cp037')
    ipl[0x49] = 0x48
    ipl[0x108:0x10a] = (1).to_bytes(2, 'little')
    ipl[0x10a:0x10c] = (512).to_bytes(2, 'little')
    header = bytearray(512)
    header[0x0c] = 1
    entry = 0x10
    header[entry + 0x2:entry + 0x4] = (2).to_bytes(2, 'little')
    header[entry + 0x4:entry + 0x6] = (sectors * 512).to_bytes(2, 'little')
    header[entry + 0x6:entry + 0x8] = (0).to_bytes(2, 'little')
    header[entry + 0x8] = 0x01
    header[entry + 0xa:entry + 0xc] = (0x8000).to_bytes(2, 'little')
    header[entry + 0xe:entry + 0x10] = (0x8000).to_bytes(2, 'little')
    return (bytes(ipl) + bytes(header) + program.ljust(sectors * 512, b'\0')).ljust(FLOPPY_720K, b'\0')


def build(name, work):
    work.mkdir(parents=True, exist_ok=True)
    objects = []
    for8086 = (HERE / f'{name}.S').exists()
    sources = (HERE / 'rt86.S', HERE / f'{name}.S') if for8086 else (HERE / 'runtime.c', HERE / f'{name}.c')
    for source in sources:
        obj = work / f'{name}-{source.stem}.o'
        flags = ['--target=i386-unknown-none-elf'] if for8086 else CFLAGS
        subprocess.run([str(TOOLCHAIN / 'clang.exe'), *flags, '-c', str(source), '-o', str(obj)], check=True)
        objects.append(str(obj))
    script = work / 'link.ld'
    script.write_text(LINK)
    image = work / f'{name}.bin'
    subprocess.run([str(TOOLCHAIN / 'ld.lld.exe'), '-m', 'elf_i386', '-T', str(script), '--oformat=binary', '-e', '_start',
                    *objects, '-o', str(image)], check=True)
    program = image.read_bytes()
    if len(program) > MAX_BYTES:
        raise SystemExit(f'{name}: {len(program)} bytes, more than the {MAX_BYTES} its segment holds')
    sectors = (len(program) + 511) // 512
    if name in TESTS_5550:
        return ipl_5550_image(program)
    if for8086:
        loader = boot_sector(HERE / 'loader.S', work, f'{name}-loader', [f'SECTORS={sectors}', 'SPT=9', 'LOADER_8086'])
        return (loader + program.ljust(sectors * 512, b'\0')).ljust(FLOPPY_360K, b'\0')
    loader = boot_sector(HERE / 'loader.S', work, f'{name}-loader', [f'SECTORS={sectors}'])
    return (loader + program.ljust(sectors * 512, b'\0')).ljust(FLOPPY_BYTES, b'\0')


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    names = sys.argv[2:] or sorted([p.stem for p in HERE.glob('*.c') if p.stem != 'runtime']
                                   + [p.stem for p in HERE.glob('*.S') if p.name not in SOURCES_8086])
    for name in names:
        (out / f'{name}.img').write_bytes(build(name, out / 'build'))
        print(f'{name}.img')


if __name__ == '__main__':
    main()
