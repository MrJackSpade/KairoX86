#!/usr/bin/env python3
"""KairoX86's graphics comparison batch (KairoX86#283): every graphics card the app offers, with each test floppy
(make_tests.py), run headless twice under game_profile, the Hardware acceleration setting (#282) off and on, and
every frame compared: by hash, and a differing frame by its picture within a small margin (one with no picture kept
fails). A mismatch writes a diff image beside the run and fails. Cards run --jobs at a time.

  compare.py <ROM set> <game_profile> <hardware_query> <test floppies> <out folder> [--cards id,...] [--tests name,...]
             [--frames n] [--shots n] [--a off|on] [--b off|on] [--jobs n]

Each card runs on its bus's test board (the bus from the core's hardware list): PCI and AGP cards on the 686BX,
MCA cards on the PS/2 Model 55 SX, the rest (ISA, VLB, the boards' own) on the 486, period boards whose BIOSes
they suit; a card its board does not take runs on the first that does. The add-on 3D cards (Voodoo Graphics,
Voodoo2) run beside the 686BX's S3 Trio64. Every test ends halted at TEST_END: a run that does not get there
fails. Frames match when their hashes do, or else when no channel of any pixel differs by more than
MAX_CHANNEL and at most MAX_SHARE of the pixels differ at all.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops

# The margin, the same for every card: GPU and CPU arithmetic (floats especially) are not bit-identical
MAX_CHANNEL = 4
MAX_SHARE = 0.002

# The test boards, in order of choice for a card its bus's board does not take
BOARDS = {
    '686bx': "machine = 686bx\ncpu_family = pentiumpro\ncpu_speed = 200000000\ncpu_multi = 3\nmem_size = 65536\n",
    '486ap4': "machine = 486ap4\ncpu_family = i486dx2\ncpu_speed = 66666666\ncpu_multi = 2\nmem_size = 32768\n",
    'ibmps2_m55ls': "machine = ibmps2_m55ls\ncpu_family = i386sx\ncpu_speed = 16000000\ncpu_multi = 1\nmem_size = 4096\n",
}
ADD_ONS = {'voodoo': 'voodoo', 'voodoo_2': 'voodoo_2'}
# Each bus's board; any other bus (ISA, VLB, none) the 486's
BUS_BOARD = {'pci': '686bx', 'agp': '686bx', 'mca': 'ibmps2_m55ls'}
# Where every test ends (runtime.c): its HLT with interrupts off, as the machine's stop reports it
TEST_END = '0000:8003'
# Each board's saved CMOS (booting A: first), from the repository's test set, where it has one
NVR = {'486ap4': Path(__file__).resolve().parents[3] / 'roms' / 'uitest' / 'dos486' / 'nvr'}


def query(tool, roms, q):
    out = subprocess.run([tool, roms, q], capture_output=True, text=True, cwd=os.path.dirname(tool))
    if out.returncode != 0:
        raise SystemExit(f'hardware_query {q}: {out.stderr}')
    return json.loads(out.stdout)


def machine_config(board, card, test, accel):
    video = f"gfxcard = {card}\n" if card not in ADD_ONS else "gfxcard = s3_trio64_pci\nvoodoo = 1\n"
    voodoo = f"\n[3Dfx Voodoo Graphics]\ntype = {ADD_ONS[card]}\n" if card in ADD_ONS else ""
    return (f"[Machine]\n{BOARDS[board]}cpu_use_dynarec = 1\nfpu_type = internal\ntime_sync = disabled\n\n"
            f"[Video]\n{video}{voodoo}\n[Input devices]\nkeyboard_type = keyboard_ps2\nmouse_type = none\n\n"
            f"[Storage controllers]\nhdc = none\n\n"
            f"[Floppy and CD-ROM drives]\nfdd_01_type = 35_2hd\nfdd_01_fn = {test}.img\nfdd_02_type = none\n\n"
            f"[KairoX86]\nhardware_acceleration = {1 if accel == 'on' else 0}\n")


def run(args, folder, config, test, board):
    """Runs one test under game_profile until it halts at its end (runtime.c's TEST_END); returns its hashes, by frame
    and 'state' (the guest's state at the end), and its work folder (the pictures)."""
    machine, work = folder / 'machine', folder / 'work'
    for f in (machine, work):
        if f.exists():
            shutil.rmtree(f)
        f.mkdir(parents=True)
    (machine / '86box.cfg').write_text(config, newline='\n')
    if board in NVR:
        shutil.copytree(NVR[board], machine / 'nvr')
    shutil.copy(Path(args.tests_folder) / f'{test}.img', machine)
    out = subprocess.run([args.game_profile, args.roms, str(work), str(machine), str(args.frames), '-',
                          '--shots', str(args.shots), '--hashes', str(folder / 'hashes.txt'), '--until-halt', TEST_END],
                         capture_output=True, text=True, cwd=os.path.dirname(args.game_profile))
    (folder / 'run.log').write_text(out.stdout + out.stderr)
    if out.returncode != 0:
        raise RuntimeError(f'game_profile failed ({out.returncode}): {(out.stdout + out.stderr).strip()[-300:]}')
    # The test ran to its end: a machine stuck in its BIOS, or a test that never finished, matches itself but tests nothing
    if not any(line.startswith('halted ') for line in out.stdout.splitlines()):
        raise RuntimeError(f'the test did not reach its end in {args.frames} frames')
    # A run with Hardware acceleration on must have run on the GPU: the machine names it (KairoX86#232)
    started = next((line[len('started '):] for line in out.stdout.splitlines() if line.startswith('started ')), None)
    if started is None:
        raise RuntimeError('game_profile printed no started line')
    if ('hardware_acceleration = 1' in config) != (';gpu=' in started):
        raise RuntimeError(f'the machine started with {started!r}, against its Hardware acceleration setting')
    hashes = {}
    for line in (folder / 'hashes.txt').read_text().splitlines():
        if line.startswith('state'):
            hashes['state'] = line.split()[1]
        else:
            frame, size, picture = line.split()[:3]
            hashes[int(frame)] = (size, picture)
    shutil.rmtree(work / 'machine')
    return hashes, work


def compare_frame(a_path, b_path, diff_path):
    """Whether two pictures match within the margin; writes the differing pixels (white) to diff_path if not."""
    a, b = Image.open(a_path).convert('RGB'), Image.open(b_path).convert('RGB')
    if a.size != b.size:
        return f'sizes {a.size} and {b.size}'
    diff = ImageChops.difference(a, b)
    worst = max(band.getextrema()[1] for band in diff.split())
    mask = diff.convert('L').point(lambda v: 255 if v else 0)
    share = mask.histogram()[255] / (a.size[0] * a.size[1])
    if worst <= MAX_CHANNEL and share <= MAX_SHARE:
        return None
    mask.save(diff_path)
    return f'channel difference up to {worst}, {share:.4%} of pixels differ'


def compare_runs(args, ha, wa, hb, wb, folder):
    """Why runs A and B (their hashes and work folders) do not match, or None when they do."""
    # The guest runs alike whatever draws its pictures: its state at the end (registers, tsc, all RAM)
    if ha['state'] != hb['state']:
        return f'the guest ended in another state ({ha["state"]} and {hb["state"]})'
    if set(ha) != set(hb):
        return f'{len(ha)} and {len(hb)} frames'
    for frame in sorted(f for f in ha if f != 'state'):
        if ha[frame] == hb[frame]:
            continue
        shot_a, shot_b = wa / f'frame-{frame}.bmp', wb / f'frame-{frame}.bmp'
        if not shot_a.exists():
            return f'frame {frame} differs, and no picture of it was kept'
        why = compare_frame(shot_a, shot_b, folder / f'diff-{frame}.png')
        if why:
            return f'frame {frame}: {why}'
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('roms')
    p.add_argument('game_profile')
    p.add_argument('hardware_query')
    p.add_argument('tests_folder')
    p.add_argument('out')
    p.add_argument('--cards')
    p.add_argument('--tests')
    p.add_argument('--frames', type=int, default=900)
    p.add_argument('--shots', type=int, default=10)
    p.add_argument('--a', default='off')
    p.add_argument('--b', default='on')
    p.add_argument('--jobs', type=int, default=8)
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    takes = {}
    bus = {}
    for board in BOARDS:
        listed = [c for c in query(args.hardware_query, args.roms, f'machine {board}')['video'] if c['available']]
        takes[board] = {c['id'] for c in listed}
        bus.update({c['id']: c['bus'] for c in listed})

    def board_of(card):
        """The card's test board: its bus's (BUS_BOARD), or else the first board that takes it."""
        if card in ADD_ONS:
            return '686bx'
        own = BUS_BOARD.get(bus.get(card), '486ap4')
        return own if card in takes[own] else next((b for b in BOARDS if card in takes[b]), None)
    cards = sorted(set().union(*takes.values()) - {'none', 'external', 'internal'}) + sorted(ADD_ONS)
    if args.cards:
        cards = args.cards.split(',')
    tests = args.tests.split(',') if args.tests else sorted(p.stem for p in Path(args.tests_folder).glob('*.img'))

    def check(card):
        """The card's failures, each (card, test, problem); prints each test's result."""
        board = board_of(card)
        if board is None:
            print(f'{card}: no test board takes it', flush=True)
            return [(card, '-', 'no test board takes it')]
        found = []
        for test in tests:
            folder = out / card / test
            try:
                ha, wa = run(args, folder / f'a-{args.a}', machine_config(board, card, test, args.a), test, board)
                hb, wb = run(args, folder / f'b-{args.b}', machine_config(board, card, test, args.b), test, board)
            except RuntimeError as e:
                found.append((card, test, str(e)))
                print(f'{card} {test}: {e}', flush=True)
                continue
            problem = compare_runs(args, ha, wa, hb, wb, folder)
            if problem:
                found.append((card, test, problem))
            else:
                shutil.rmtree(folder)
            print(f'{card} ({board}) {test}: ' + ('match' if problem is None else f'DIFFERS: {problem}'), flush=True)
        return found

    with ThreadPoolExecutor(args.jobs) as pool:
        failures = [f for found in pool.map(check, cards) for f in found]
    print(f'{len(cards)} cards, {len(tests)} tests, {len(failures)} failing')
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
