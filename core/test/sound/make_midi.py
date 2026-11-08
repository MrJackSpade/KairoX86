#!/usr/bin/env python3
"""Writes KairoX86's MIDI test machines (KairoX86#306): the 486 with a standalone MPU-401 at 330h,
booting a floppy whose boot sector (midi.S) plays notes through it, one machine for each MIDI out
device: midi-none (nothing to play them), midi-mt32 and midi-cm32l (Munt, with the ROM set's
firmware) and midi-fluidsynth (FluidSynth, with the SoundFont the app ships in the ROM set,
sound/kairo/GeneralUser-GS.sf2), and midi-kairo_midi_port (the "MIDI port" device, KairoX86#305). A
run's sound (game_profile --audio) is silent on midi-none and carries the notes on the synths; on
midi-kairo_midi_port the messages the host's MIDI port gets (game_profile --midi) are the guest's
bytes as it wrote them: F0 7E 7F 09 01 F7, C1 00, then 91 nn 64 and, under running status,
nn 00 for each note.

  make_midi.py <out folder>     writes <out folder>/midi-<device>, and prints the input script that
                                presses F1 past the BIOS's CMOS prompt (game_profile's script)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from floppy import boot_sector, write_floppy  # noqa: E402

DEVICES = ['none', 'mt32', 'cm32l', 'fluidsynth', 'kairo_midi_port']

CONFIG = """[Machine]
machine = 486ap4
cpu_family = i486dx2
cpu_speed = 66666666
cpu_multi = 2
cpu_use_dynarec = 1
fpu_type = internal
mem_size = 32768
time_sync = disabled

[Video]
gfxcard = s3_trio64v2dx_pci

[S3 Trio64V2/DX PCI #1]
bios = trio64v2dx_pci

[Sound]
mpu401_standalone = 1
{midi}
[Input devices]
keyboard_type = keyboard_ps2

[Floppy and CD-ROM drives]
fdd_01_type = 35_2hd
fdd_01_fn = midi.img
fdd_02_type = none
"""


def script():
    # F1 past the BIOS's CMOS prompt, as the input tests press it (make_mouse.py).
    return ','.join(f'{frame}:+0x3b,{frame + 4}:-0x3b' for frame in (150, 300, 450, 600))


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1]).resolve()
    sector = boot_sector(HERE / 'midi.S', out / '.asm', 'midi')
    for device in DEVICES:
        machine = out / f'midi-{device}'
        machine.mkdir(parents=True, exist_ok=True)
        write_floppy(machine / 'midi.img', sector)
        midi = '' if device == 'none' else f'midi_device = {device}\n'
        (machine / '86box.cfg').write_text(CONFIG.format(midi=midi), encoding='utf-8', newline='\n')
    print(script())


if __name__ == '__main__':
    main()
