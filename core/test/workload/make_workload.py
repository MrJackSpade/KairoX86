#!/usr/bin/env python3
"""Builds KairoX86's CPU workload floppies (KairoX86#417): each program here (<name>.c) compiled with core/test/gpu's
runtime and loader for a Pentium MMX (-march=pentium-mmx), as make_tests.py builds the graphics tests, on a 1.44 MB
floppy image <out folder>/<name>.img. They run forever: game_profile measures them by frames, and nothing waits for
an end.

  make_workload.py <out folder> [name ...]     every .c here when none is named
  make_workload.py <out folder> --machines <reference folder>
      also writes the machines that run mmxint (out/mmx-tx97, out/mmx-686bx: 86box.cfg, the floppy and nvr/), their
      CMOS from the exactness standard's references (<reference>/win98-pentium/nvr, <reference>/win98-voodoo3/nvr),
      as KairoX86#417 measured them (game_profile ... 2000 - --warmup 1000: the program runs from about frame 700)
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GPU = HERE.parent / 'gpu'
sys.path.insert(0, str(GPU))
sys.path.insert(0, str(HERE.parent))
import make_tests  # noqa: E402
from floppy import TOOLCHAIN, FLOPPY_BYTES, boot_sector  # noqa: E402

CFLAGS = [f for f in make_tests.CFLAGS if not f.startswith('-march=')] + ['-march=pentium-mmx']
NL = chr(10)


def build(name, work):
    work.mkdir(parents=True, exist_ok=True)
    objects = []
    for source in (GPU / 'runtime.c', HERE / f'{name}.c'):
        obj = work / f'{name}-{source.stem}.o'
        subprocess.run([str(TOOLCHAIN / 'clang.exe'), *CFLAGS, f'-I{GPU}', '-c', str(source), '-o', str(obj)], check=True)
        objects.append(str(obj))
    script = work / 'link.ld'
    script.write_text(make_tests.LINK)
    image = work / f'{name}.bin'
    subprocess.run([str(TOOLCHAIN / 'ld.lld.exe'), '-m', 'elf_i386', '-T', str(script), '--oformat=binary', '-e', '_start',
                    *objects, '-o', str(image)], check=True)
    program = image.read_bytes()
    if len(program) > make_tests.MAX_BYTES:
        raise SystemExit(f'{name}: {len(program)} bytes, more than the {make_tests.MAX_BYTES} its segment holds')
    sectors = (len(program) + 511) // 512
    loader = boot_sector(GPU / 'loader.S', work, f'{name}-loader', [f'SECTORS={sectors}'])
    return (loader + program.ljust(sectors * 512, b'\0')).ljust(FLOPPY_BYTES, b'\0')


def section(title, *lines):
    return f'[{title}]' + NL + NL.join(lines) + NL + NL


def machines(out, reference):
    sys.path.insert(0, str(HERE.parent / 'exact'))
    import machines as standard  # noqa: E402

    extra = 'cpu_use_dynarec = 1' + NL + 'fpu_type = internal'
    inputs = section('Input devices', 'keyboard_type = keyboard_ps2', 'mouse_type = ps2')
    configs = {
        # The TX97 Pentium MMX 233 with the S3 Trio64V2 (PCI), as the standard's pentium machine
        'mmx-tx97': (standard.GENERAL + standard.machine('tx97', 'pentium_p55c', 233333333, 3.5, 65536, 's3_trio64v2dx_pci',
                                                         extra=extra)
                     + section('S3 Trio64V2/DX PCI #1', 'bios = trio64v2dx_pci') + inputs
                     + section('Sound', 'fm_driver = ymfm', 'sndcard = sb16') + standard.floppy('mmxint.img', '35_2hd'),
                     'win98-pentium'),
        # The 686BX with a Pentium II 300 (the Pentium Pro has no MMX) and the Voodoo3 3000, as eXoWin9x's games run
        'mmx-686bx': (standard.GENERAL + standard.machine('686bx', 'pentium2_deschutes', 300000000, 4.5, 65536,
                                                          'voodoo3_3k_agp', extra=extra)
                      + section('3dfx Voodoo3 3000', 'render_threads = 2', 'recompiler = 1') + inputs
                      + section('Sound', 'sndcard = sbawe32_pnp') + standard.floppy('mmxint.img', '35_2hd'),
                      'win98-voodoo3'),
    }
    for name, (config, cmos) in configs.items():
        folder = out / name
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir()
        (folder / '86box.cfg').write_text(config, encoding='utf-8', newline=NL)
        shutil.copy2(out / 'mmxint.img', folder / 'mmxint.img')
        shutil.copytree(reference / cmos / 'nvr', folder / 'nvr')
        print(name)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    args = sys.argv[2:]
    reference = None
    if '--machines' in args:
        at = args.index('--machines')
        reference = Path(args[at + 1])
        args = args[:at] + args[at + 2:]
    for name in args or sorted(p.stem for p in HERE.glob('*.c')):
        (out / f'{name}.img').write_bytes(build(name, out / 'build'))
        print(f'{name}.img')
    if reference is not None:
        machines(out, reference)


if __name__ == '__main__':
    main()
