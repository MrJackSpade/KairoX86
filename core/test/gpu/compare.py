#!/usr/bin/env python3
"""KairoX86's graphics comparison batch (KairoX86#283): every graphics card the app offers, with each test floppy
(make_tests.py), run headless twice under game_profile, the Hardware acceleration setting (#282) off and on, and
every frame compared: by hash, and a differing frame by its picture within a small margin (one with no picture kept
fails). A mismatch writes a diff image beside the run and fails. Cards run --jobs at a time.

  compare.py <ROM set> <game_profile> <hardware_query> <test floppies> <out folder> [--cards id,...] [--tests name,...]
  With --device <adb serial> the runs are on that Android device: --remote (default /data/local/tmp/kx86/gpu) holds
  bin/ (the release core's game_profile, libkairox86_86box.so and libc++_shared.so), roms/ and tests/; hardware_query
  and the ROM set given are the PC's, which list the cards.
             [--frames n] [--shots n] [--a off|on[+rec]] [--b off|on[+rec]] [--jobs n]

Each card runs on its bus's test board (the bus from the core's hardware list): PCI and AGP cards on the 686BX,
MCA cards (and the MCA XGA and XGA-2, add-ons beside the board's own VGA) on the PS/2 Model 80 type 3 (its CMOS
unset, so F1 past POST's 161 and 163), the rest (ISA, VLB, the boards' own) on the 486, period boards whose BIOSes
they suit; a card its board does not take runs on the first that does. The add-on 3D cards (Voodoo Graphics,
Voodoo2) run beside the 686BX's S3 Trio64. The 3dfx cards' software side draws with 86Box's C rasteriser
(their recompiler off: KairoX86#289; a mode's +rec turns it on, so --a off --b off+rec checks the recompiler
against the C rasteriser). Every test ends halted at TEST_END: a run that does not get there
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
    # 8 MB: a Mach64 GX's aperture must fit above the memory and below an ISA card's 16 MB
    '486ap4': "machine = 486ap4\ncpu_family = i486dx2\ncpu_speed = 66666666\ncpu_multi = 2\nmem_size = 8192\n",
    # A 486 for a short POST; 8 MB: the XGA test keeps its passes from 2 MB up, and the XGA's 1 MB aperture sits at
    # 12 MB. Not the Model 55 SX or LS: their POST stops with error 102 under the recompiler (KairoX86#304)
    'ibmps2_m80_type3': "machine = ibmps2_m80_type3\ncpu_family = i486dx2\ncpu_speed = 66666666\ncpu_multi = 2\n"
                        "mem_size = 8192\n",
    # The Chips & Technologies B69000's own board (its on-board chip, KairoX86#249)
    'nupro592': "machine = nupro592\ncpu_family = pentium_p55c\ncpu_speed = 200000000\ncpu_multi = 3\nmem_size = 32768\n",
    # The Sigma Color 400's (KairoX86#285): an AMI 386 board whose BIOS has its timer vector set when the card's ROM
    # hooks it (the later Award BIOSes of the 486AP4 and 686BX hand it a stub their memory test then wipes)
    'asus386': "machine = asus386\ncpu_family = i386dx\ncpu_speed = 33333333\ncpu_multi = 1\nmem_size = 4096\n",
}
# The machines with their own video (KairoX86#311-#324), each its first CPU and speed and its most memory (the 286s their least: a shorter memory test): the 8086
# machines (8088, 8086, 80186, 286: no 32-bit code) boot the 8086 tests (make_tests.py, rt86.S) from a 360 KB drive
BOARDS_8086 = {
    'ibmpcjr': ('8088', 4772728, 640), 'ibmpcjx': ('8088', 4772728, 512), 'tandy1000sx': ('8088', 4772728, 640),
    'tandy1000hx': ('8088', 4772728, 640), 'tandy1000sl2': ('8086', 7159092, 768), 't1000': ('8088', 4772728, 1280),
    't1200': ('8086', 7159092, 2048), 'pc1512': ('8086', 8000000, 640), 'pc1640': ('8086', 7159092, 640),
    'pc2086': ('8086', 7159092, 640), 'pc3086': ('8086', 7159092, 640), 'pc200': ('8086', 7159092, 640),
    'ppc512': ('8086', 7159092, 640), 'ibm5140': ('80c88', 4772728, 640), 'v86p': ('8086', 7159092, 1024),
    'ibmps2_m25': ('8086', 8000000, 640), 'ibmps2_m30': ('8086', 8000000, 640), 'ibm7690': ('8086', 8000000, 640), 'ibm3270pc': ('8088', 4772728, 640),
    'ibm5550': ('8086', 8000000, 640), 'portableiii': ('286', 8000000, 640), 't3100e': ('286', 12500000, 1024),
    'tandy2000': ('80186', 8000000, 768),
}
for _m, (_family, _speed, _mem) in BOARDS_8086.items():
    BOARDS[_m] = f"machine = {_m}\ncpu_family = {_family}\ncpu_speed = {_speed}\ncpu_multi = 1\nmem_size = {_mem}\n"
# The Cyrix MediaGX's board (KairoX86#315), a 586: the tests the other boards run
BOARDS['p5gxm'] = "machine = p5gxm\ncpu_family = mediagxm\ncpu_speed = 166666666\ncpu_multi = 5\nmem_size = 65536\n"
# Boards whose POST takes longer than the batch's frames: the Toshiba T3100e's memory test
BOARD_FRAMES = {'t3100e': 12000}
# The 8086 tests' floppies (make_tests.py)
FLOPPY_360K = 368640
# A board's input: the Model 80's CMOS was never set (no reference diskette), so POST stops at 161 and 163 waiting
# for F1, which it is given well after the prompt appears
SCRIPT = {'ibmps2_m80_type3': '3100:+0x3b,3106:-0x3b',
          # its battery reported discharged: any key to go on
          't1000': '300:+0x39,306:-0x39,600:+0x39,606:-0x39',
          # The 8086 machines' unset CMOS or configuration, each prompt answered as it asks (F1, or Enter to keep the
          # floppy type offered), at a few points through a POST of unknown length
          't1200': '800:+0x1c,806:-0x1c,1600:+0x1c,1606:-0x1c,2400:+0x1c,2406:-0x1c',
          # the MediaGX board's CMOS unset: F1 to continue
          'p5gxm': '600:+0x3b,606:-0x3b,1200:+0x3b,1206:-0x3b',
          **{m: '800:+0x3b,806:-0x3b,1600:+0x3b,1606:-0x3b,2400:+0x3b,2406:-0x3b,3200:+0x3b,3206:-0x3b,4000:+0x3b,4006:-0x3b'
             for m in ('ibm3270pc', 'v86p', 'ibmps2_m30', 'ibm7690', 'portableiii', 't3100e', 'ibm5140')},
          # its CMOS unset too: "CMOS checksum error", F1 to continue
          'nupro592': '600:+0x3b,606:-0x3b',
          # its CMOS unset: F1 runs Setup, left without saving (Esc, Y, Enter)
          'asus386': '200:+0x3b,206:-0x3b,400:+0x01,406:-0x01,500:+0x15,506:-0x15,520:+0x1c,526:-0x1c'}
# Boards whose drive is not the 8086 machines' 360 KB one: the IBM 5550's DSQD (720 KB 5.25") drives
BOARD_FDD = {'ibm5550': '525_2qd'}
# Boards that boot images of their own size only: the IBM 5550's IPL load modules (make_tests.py ipl_5550_image)
FLOPPY_720K = 737280
BOARD_IMAGE = {'ibm5550': FLOPPY_720K}
# Boards that run their own tests only: the Tandy 2000 has no IBM-compatible BIOS (no video calls, no tick count)
BOARD_TESTS = {'tandy2000': ('t2k86',)}
# Boards' own video settings: the Tandy 2000 with its colour graphics option, so its graphics are tested too
BOARD_VIDEO = {'tandy2000': '\n[Tandy 2000 (Video)]\ngraphics = 2\n'}
# Boards' own graphics chips (gfxcard = internal), each named as its chip's device is, on its board
ONBOARD = {'chips_69000_onboard': 'nupro592', **{f'{m}_video': m for m in BOARDS_8086}, 'p5gxm_video': 'p5gxm'}
# The add-on cards: each one's [Video] line, its own section and the card beside it, an S3 Trio64 (the Voodoos drawn
# by the C rasteriser on the software side, KairoX86#289; the PowerVR PCX2, KairoX86#269), or the IBM VGA beside the
# 8514/A, whose ports the S3 has too (KairoX86#238; IBM's, and ATI's 8514 Ultra with the Mach8 engine)
ADD_ONS = {
    'voodoo': ('voodoo = 1\n', '\n[3Dfx Voodoo Graphics]\ntype = voodoo\nrecompiler = 0\n', 's3_trio64_pci'),
    'voodoo_2': ('voodoo = 1\n', '\n[3Dfx Voodoo Graphics]\ntype = voodoo_2\nrecompiler = 0\n', 's3_trio64_pci'),
    'powervr': ('powervr = 1\n', '', 's3_trio64_pci'),
    '8514a': ('8514a = 1\n', '', 'vga'),
    '8514a_ati': ('8514a = 1\n', '\n[IBM 8514/A clone (ISA)]\nextensions = 1\n', 'vga'),
    'xga_mca': ('xga = 1\n', '\n[XGA (MCA)]\ntype = 0\n', 'internal'),
    'xga2_mca': ('xga = 1\n', '\n[XGA (MCA)]\ntype = 1\n', 'internal'),
    # The Hercules and Hercules Plus with their blend option off (on by default; KairoX86#257, #259)
    'hercules_noblend': ('', '\n[Hercules]\nblend = 0\n', 'hercules'),
    'hercules_plus_noblend': ('', '\n[Hercules Plus]\nblend = 0\n', 'hercules_plus'),
    # The IBM CGA with its light pen attached (KairoX86#241)
    'cga_lightpen': ('', '', 'cga'),
}
# The add-ons' boards, where not the 686BX
ADD_ON_BOARD = {'xga_mca': 'ibmps2_m80_type3', 'xga2_mca': 'ibmps2_m80_type3', 'hercules_noblend': '486ap4',
                'hercules_plus_noblend': '486ap4', 'cga_lightpen': '486ap4'}
# The add-ons' pointing devices, where not none
ADD_ON_MOUSE = {'cga_lightpen': 'cga_lightpen'}
# Each bus's board; any other bus (ISA, VLB, none) the 486's
BUS_BOARD = {'pci': '686bx', 'agp': '686bx', 'mca': 'ibmps2_m80_type3'}
# Cards whose software path fails on their bus's board, each on one where it works until its bug is fixed
CARD_BOARD = {
    'quadcolor': '686bx',  # KairoX86#286: on the 486AP4 it hands over no picture and the machine never boots
    'sigma400': 'asus386',  # KairoX86#285: its ROM hooks the timer before the later Award BIOSes set it
}
# The 3dfx cards (Voodoo Graphics, Voodoo2, the Banshee family): the software side draws with 86Box's C
# rasteriser, the reference its recompiler is meant to match and does not yet in every mode (KairoX86#289)
VOODOO_FAMILY = ('voodoo', 'velocity', 'ctl3d_banshee', 'q3d_raven')
# Where every test ends (runtime.c): its HLT with interrupts off, as the machine's stop reports it
TEST_END = '0000:8003'
# The 8088, 8086 and 80186 cores (808x) stop one byte on, past the same HLT (rt86.S keeps runtime.c's layout); the
# 286s' stop where the others do
TEST_END_8086 = '0000:8004'
# Each board's saved CMOS (booting A: first), from the repository's test set, where it has one
NVR = {'486ap4': Path(__file__).resolve().parents[3] / 'roms' / 'uitest' / 'dos486' / 'nvr'}


def query(tool, roms, q):
    out = subprocess.run([tool, roms, q], capture_output=True, text=True, cwd=os.path.dirname(tool))
    if out.returncode != 0:
        raise SystemExit(f'hardware_query {q}: {out.stderr}')
    return json.loads(out.stdout)


def run_mode(mode):
    """A run's mode (--a, --b): 'off' or 'on' (Hardware acceleration), with '+rec' for the 3dfx cards' recompiler on
    (KairoX86#289: off+rec against off checks the recompiler against the C rasteriser); whether each is on"""
    accel, _, extra = mode.partition('+')
    if accel not in ('off', 'on') or extra not in ('', 'rec'):
        raise SystemExit(f'unknown run mode {mode!r}: off or on, optionally +rec')
    return accel == 'on', extra == 'rec'


def machine_config(board, card, test, mode, name):
    accel, recompiler = run_mode(mode)
    video = (f"gfxcard = {card}\n" if card not in ADD_ONS else f"gfxcard = {ADD_ONS[card][2]}\n" + ADD_ONS[card][0])
    if card in ONBOARD:
        video = "gfxcard = internal\n"
    voodoo = ADD_ONS[card][1] if card in ADD_ONS else ""
    if card not in ADD_ONS and card.startswith(VOODOO_FAMILY):
        # A device reads its settings from its name's section, "<name> #<n>" for instance n > 0 (the AGP
        # Banshee is instance 1)
        voodoo = f"\n[{name}]\nrecompiler = 0\n\n[{name} #1]\nrecompiler = 0\n"
    if recompiler:
        voodoo = voodoo.replace('recompiler = 0', 'recompiler = 1')
    voodoo += BOARD_VIDEO.get(board, "")
    return (f"[Machine]\n{BOARDS[board]}cpu_use_dynarec = 1\nfpu_type = internal\ntime_sync = disabled\n\n"
            f"[Video]\n{video}{voodoo}\n[Input devices]\n"
            # The 8086 machines take their own keyboards (an XT-class board reads no PS/2 keyboard)
            + ("" if board in BOARDS_8086 else "keyboard_type = keyboard_ps2\n") + f"mouse_type = {ADD_ON_MOUSE.get(card, 'none')}\n\n"
            f"[Storage controllers]\nhdc = none\n\n"
            f"[Floppy and CD-ROM drives]\nfdd_01_type = {BOARD_FDD.get(board, '525_2dd' if board in BOARDS_8086 else '35_2hd')}\n"
            f"fdd_01_fn = {test}.img\nfdd_02_type = none\n\n"
            f"[KairoX86]\nhardware_acceleration = {1 if accel else 0}\n")


def adb(args, *command, check=True):
    """adb against the --device: its output; a failure raises with what adb said"""
    out = subprocess.run(['adb', '-s', args.device, *command], capture_output=True, text=True, encoding='utf-8',
                         errors='replace', env=dict(os.environ, MSYS_NO_PATHCONV='1'))
    if check and out.returncode != 0:
        raise RuntimeError(f'adb {" ".join(command)[:120]} failed ({out.returncode}): {(out.stdout + out.stderr).strip()[-300:]}')
    return out


def remote_folder(args, folder):
    """A run folder's place on the --device: --remote/runs/<its path under the out folder>"""
    return f"{args.remote}/runs/{folder.relative_to(Path(args.out)).as_posix()}"


def run_game_profile(args, folder, machine, work, test, frames, board):
    """game_profile over the machine folder, here or on the --device (the test's image copied from --remote/tests):
    its stdout, stderr and exit code, its hashes in folder/hashes.txt"""
    end = TEST_END_8086 if BOARDS_8086.get(board, ('286',))[0] != '286' else TEST_END
    script = SCRIPT.get(board, '-')
    if not args.device:
        out = subprocess.run([args.game_profile, args.roms, str(work), str(machine), str(frames), script, '--shots',
                              str(args.shots), '--hashes', str(folder / 'hashes.txt'), '--until-halt', end],
                             capture_output=True, text=True, cwd=os.path.dirname(args.game_profile))
        return out.stdout, out.stderr, out.returncode
    r = remote_folder(args, folder)
    adb(args, 'shell', f'rm -rf {r} && mkdir -p {r}/work')
    adb(args, 'push', str(machine), f'{r}/')
    out = adb(args, 'shell', f"cp {args.remote}/tests/{test}.img {r}/machine/ && cd {args.remote}/bin && "
                             f"LD_LIBRARY_PATH=. ./game_profile {args.remote}/roms {r}/work {r}/machine {frames} '{script}' "
                             f"--shots {args.shots} --hashes {r}/hashes.txt --until-halt {end} 2>{r}/stderr.txt; echo exit=$?",
              check=False)
    lines = out.stdout.splitlines()
    if not lines or not lines[-1].startswith('exit='):
        raise RuntimeError(f'adb shell gave no exit status: {(out.stdout + out.stderr).strip()[-300:]}')
    code = int(lines[-1][len('exit='):])
    stderr = adb(args, 'shell', f'cat {r}/stderr.txt').stdout
    if code == 0:
        adb(args, 'pull', f'{r}/hashes.txt', str(folder / 'hashes.txt'))
    return '\n'.join(lines[:-1]) + '\n', stderr, code


def run(args, folder, config, test, board):
    """Runs one test under game_profile until it halts at its end (runtime.c's TEST_END); returns its hashes, by frame
    and 'state' (the guest's state at the end), and its work folder (the pictures; from a --device, pulled as
    compare_runs needs them)."""
    machine, work = folder / 'machine', folder / 'work'
    for f in (machine, work):
        if f.exists():
            shutil.rmtree(f)
        f.mkdir(parents=True)
    (machine / '86box.cfg').write_text(config, newline='\n')
    if board in NVR:
        shutil.copytree(NVR[board], machine / 'nvr')
    if not args.device:
        shutil.copy(Path(args.tests_folder) / f'{test}.img', machine)

    class Out:
        """the run's output"""
    out = Out()
    out.stdout, out.stderr, out.returncode = run_game_profile(args, folder, machine, work, test,
                                                              max(args.frames, BOARD_FRAMES.get(board, 0)), board)
    (folder / 'run.log').write_text(out.stdout + out.stderr)
    if out.returncode != 0:
        raise RuntimeError(f'game_profile failed ({out.returncode}): {(out.stdout + out.stderr).strip()[-300:]}')
    # The test ran to its end: a machine stuck in its BIOS, or a test that never finished, matches itself but tests nothing
    if not any(line.startswith('halted ') for line in out.stdout.splitlines()):
        raise RuntimeError(f'the test did not reach its end in {max(args.frames, BOARD_FRAMES.get(board, 0))} frames')
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
    # How many lines the GPU drew (the core reports it at the machine's end, KairoX86#233)
    drawn = [line.split()[1] for line in out.stderr.splitlines() if line.startswith('kairo-gpu: ') and line.endswith(' lines drawn')]
    hashes['gpu_lines'] = int(drawn[-1]) if drawn else 0
    # And how long the driver took to build each kernel the run used (gpu.c reports it, KairoX86#237)
    hashes['gpu_kernels'] = [' '.join(line.split()[2:3] + line.split()[5:6]) + ' ms' for line in out.stderr.splitlines()
                             if line.startswith('kairo-gpu: kernel ')]
    # And the 3D engines' work (the Voodoo's triangles, KairoX86#278; the ViRGE's, #272; the Rage II+'s draws, #237):
    # every "kairo-gpu-<engine>: N <work> drawn" report, summed
    hashes['gpu_3d'] = sum(int(line.split()[1]) for line in out.stderr.splitlines()
                           if line.startswith('kairo-gpu-') and line.endswith(' drawn'))
    if not args.device:
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
    for frame in sorted(f for f in ha if isinstance(f, int)):
        if ha[frame] == hb[frame]:
            continue
        shot_a, shot_b = wa / f'frame-{frame}.bmp', wb / f'frame-{frame}.bmp'
        if args.device:
            for shot in (shot_a, shot_b):
                adb(args, 'pull', f'{remote_folder(args, shot.parent.parent)}/work/{shot.name}', str(shot), check=False)
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
    p.add_argument('--frames', type=int, default=6000)
    p.add_argument('--shots', type=int, default=10)
    p.add_argument('--a', default='off')
    p.add_argument('--b', default='on')
    p.add_argument('--jobs', type=int, default=8)
    # On an Android device (adb serial): its folder holding bin/ (game_profile and its libraries), roms/ and tests/;
    # the ROM set given is the PC's copy, which hardware_query (run here) lists the cards from
    p.add_argument('--device')
    p.add_argument('--remote', default='/data/local/tmp/kx86/gpu')
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    takes = {}
    bus = {}
    names = {}
    for board in BOARDS:
        listed = [c for c in query(args.hardware_query, args.roms, f'machine {board}')['video'] if c['available']]
        takes[board] = {c['id'] for c in listed}
        bus.update({c['id']: c['bus'] for c in listed})
        names.update({c['id']: c['name'] for c in listed})

    def board_of(card):
        """The card's test board: its bus's (BUS_BOARD), or else the first board that takes it."""
        if card in ADD_ONS:
            return ADD_ON_BOARD.get(card, '686bx')
        if card in ONBOARD:
            return ONBOARD[card]
        own = CARD_BOARD.get(card) or BUS_BOARD.get(bus.get(card), '486ap4')
        return own if card in takes[own] else next((b for b in BOARDS if card in takes[b]), None)
    cards = sorted(set().union(*takes.values()) - {'none', 'external', 'internal'}) + sorted(ADD_ONS) + sorted(ONBOARD)
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
        # A board with images of its own boots those only; the other 8086 machines the 8086 tests, the rest the others
        for8086 = board in BOARDS_8086
        for test in tests:
            size = (Path(args.tests_folder) / f'{test}.img').stat().st_size
            if (board in BOARD_TESTS) and (test not in BOARD_TESTS[board]):
                continue
            if board in BOARD_IMAGE:
                if size != BOARD_IMAGE[board]:
                    continue
            elif (size in BOARD_IMAGE.values()) or ((size == FLOPPY_360K) != for8086):
                continue
            folder = out / card / test
            try:
                try:
                    ha, wa = run(args, folder / f'a-{args.a}', machine_config(board, card, test, args.a, names.get(card)), test, board)
                    hb, wb = run(args, folder / f'b-{args.b}', machine_config(board, card, test, args.b, names.get(card)), test, board)
                except RuntimeError as e:
                    found.append((card, test, str(e)))
                    print(f'{card} {test}: {e}', flush=True)
                    continue
                problem = compare_runs(args, ha, wa, hb, wb, folder)
            finally:
                # The device keeps nothing once the runs are compared (what a failure shows was pulled), pass, fail or
                # error: kept, a batch's failed runs (machine images and all) filled the RP6's storage
                if args.device:
                    adb(args, 'shell', f'rm -rf {remote_folder(args, folder)}')
            if problem:
                found.append((card, test, problem))
            else:
                shutil.rmtree(folder)
            gpu_a, gpu_b = run_mode(args.a)[0], run_mode(args.b)[0]
            on = hb if gpu_b else ha
            drawn = (f"GPU lines {on['gpu_lines']}" + (f", 3D {on['gpu_3d']}" if on['gpu_3d'] else '')
                     + (f", built {', '.join(on['gpu_kernels'])}" if on['gpu_kernels'] else ''))
            print(f'{card} ({board}) {test}: ' + ('match' if problem is None else f'DIFFERS: {problem}')
                  + (f' ({drawn})' if gpu_a or gpu_b else ''), flush=True)
        return found

    with ThreadPoolExecutor(args.jobs) as pool:
        failures = [f for found in pool.map(check, cards) for f in found]
    print(f'{len(cards)} cards, {len(tests)} tests, {len(failures)} failing')
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
