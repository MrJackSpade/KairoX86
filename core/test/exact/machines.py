#!/usr/bin/env python3
"""The machines of KairoX86's exactness standard (docs/development.md, "The core"): each runs a fixed
number of frames under game_profile, and a change to the core goes in only if every machine's picture
and sound hashes, frame by frame, and its state at the end (registers, tsc and all RAM) match the core
without the change.

  machines.py <test set> <out folder> <reference folder on the device>

<test set> is the local UI test set (roms/uitest: xt/fd13-720k.img, dos486/freedos.img and
dos486/nvr). <out folder> receives one folder per machine, and machines.json: each machine's frames.
The free machine's (free-486, free-pentium) firmware is the app's own (firmware/), which tools/exact.ps1
lays over the ROM set.
The Windows 98 machines boot the reference disks kept on the device, <reference folder>/win98-486,
<reference folder>/win98-pentium and <reference folder>/win98-voodoo3 (base.vhd and nvr/ each;
docs/development.md): each run opens a new differencing disk over the base, so every run starts from
the same disk.
"""
import json
import shutil
import sys
from pathlib import Path

GENERAL = """[General]
confirm_exit = 0
confirm_reset = 0
confirm_save = 0
host_cpu = Unknown

"""


def floppy(image, kind):
    return f"""[Floppy and CD-ROM drives]
fdd_01_fn = {image}
fdd_01_type = {kind}
fdd_02_type = none
"""


def machine(name, cpu, speed, multi, memory, video, extra='', keyboard='', time_sync=True):
    lines = [f"[Machine]", f"machine = {name}", f"cpu_family = {cpu}", f"cpu_speed = {speed}", f"cpu_multi = {multi}",
             f"mem_size = {memory}"]
    if time_sync:
        lines.append("time_sync = disabled")
    lines += [extra.strip()] if extra.strip() else []
    text = "\n".join(lines) + f"\n\n[Video]\ngfxcard = {video}\n\n"
    if keyboard:
        text += f"[Input devices]\nkeyboard_type = {keyboard}\nmouse_type = none\n\n"
    return text


XT_FLOPPY = "fd13-720k.img"
DOS_FLOPPY = "freedos.img"

# name: (86box.cfg, the files it needs from the test set, frames)
MACHINES = {
    "xt": (GENERAL + machine("ibmpc82", "8088", 4772728, 1, 256, "cga", keyboard="keyboard_pc_xt")
           + "[IBM PC (1982)]\nbios = glabios_040_8088\n\n[Sound]\nsndcard = adlib\n\n" + floppy(XT_FLOPPY, "35_2dd"),
           [("xt", XT_FLOPPY)], 3000),
    "v20": (GENERAL + machine("ibmpc82", "necv20", 4772728, 1, 256, "cga", keyboard="keyboard_pc_xt")
            + "[IBM PC (1982)]\nbios = glabios_040_8088\n\n[Sound]\nsndcard = adlib\n\n" + floppy(XT_FLOPPY, "35_2dd"),
            [("xt", XT_FLOPPY)], 3000),
    "at": (GENERAL + machine("ibmat", "286", 8000000, 1, 640, "cga", keyboard="keyboard_at")
           + "[Sound]\nsndcard = adlib\n\n" + floppy(XT_FLOPPY, "35_2dd"), [("xt", XT_FLOPPY)], 1500),
    "386sx": (GENERAL + machine("pc916sx", "i386sx", 16000000, 1, 2048, "cga")
              + "[Sound]\nsndcard = adlib\n\n" + floppy(XT_FLOPPY, "35_2dd"), [("xt", XT_FLOPPY)], 1500),
    "486": (GENERAL + machine("486ap4", "i486dx2", 66666666, 2, 32768, "s3_trio64v2dx_pci",
                              extra="cpu_use_dynarec = 1\nfpu_type = internal")
            + "[S3 Trio64V2/DX PCI #1]\nbios = trio64v2dx_pci\n\n[Input devices]\nkeyboard_type = keyboard_ps2\nmouse_type = ps2\n\n"
            + "[Sound]\nfm_driver = ymfm\nsndcard = sb16\n\n" + floppy(DOS_FLOPPY, "35_2hd"),
            [("dos486", DOS_FLOPPY), ("dos486", "nvr")], 1500),
    "pentium": (GENERAL + machine("tx97", "pentium_p55c", 233333333, 3.5, 65536, "s3_trio64v2dx_pci",
                                  extra="cpu_use_dynarec = 1\nfpu_type = internal")
                + "[S3 Trio64V2/DX PCI #1]\nbios = trio64v2dx_pci\n\n[Input devices]\nkeyboard_type = keyboard_ps2\nmouse_type = ps2\n\n"
                + "[Sound]\nfm_driver = ymfm\nsndcard = sb16\n\n" + floppy(XT_FLOPPY, "35_2hd"), [("xt", XT_FLOPPY)], 1500),
}


def free(cpu, speed, multi, memory):
    """The free machine (KairoX86#446): SeaBIOS on the 440FX/PIIX4 board, SeaVGABIOS on its GD5446, with
    the presets' Sound Blaster 16, booting FreeDOS from floppy (its own boot order, A first)."""
    return (GENERAL + machine("kairo_pc", cpu, speed, multi, memory, "cl_gd5446_migrated_pci",
                              extra="cpu_use_dynarec = 1\nfpu_type = internal")
            + "[Cirrus Logic GD5446 (PCI) #1]\nbios = cl_gd5446_free_pci\n\n"
            + "[Input devices]\nkeyboard_type = keyboard_ps2\nmouse_type = ps2\n\n"
            + "[Sound]\nfm_driver = ymfm\nsndcard = sb16\n\n[Storage controllers]\nhdc = internal\n\n"
            + floppy(DOS_FLOPPY, "35_2hd") + "\n[KairoX86]\nboot_order = a,cd,c\n")


MACHINES["free-486"] = (free("i486dx2", 66666666, 2, 16384), [("dos486", DOS_FLOPPY)], 1500)
MACHINES["free-pentium"] = (free("pentium_p55c", 233333333, 3.5, 65536), [("dos486", DOS_FLOPPY)], 1500)


def voodoo3(reference):
    """Windows 98 on a 3dfx Voodoo3 3000 (KairoX86#222): eXoWin9x's own Windows 98 (its W98-P.vhd as the
    reference's base.vhd, its 686bx CMOS and flash as nvr/) on the hardware of its 86Box games (686BX,
    Pentium Pro 150, 1 GB, AWE32), 4000 frames from power-on, through Windows' start to its desktop:
    the Voodoo's FIFO thread blitting while the Banshee draws its lines."""
    return (GENERAL + machine("686bx", "pentiumpro", 100000000, 1.5, 1048576, "voodoo3_3k_agp",
                              extra="cpu_use_dynarec = 1\nfpu_type = internal")
            + "[Input devices]\nmouse_type = ps2\n\n"
            + "[Sound]\nsndcard = sbawe32_pnp\n\n"
            + "[Storage controllers]\nfdc = none\nhdc = ide_pci\nide_qua = 1\nide_ter = 1\n\n"
            + "[3dfx Voodoo3 3000]\nbilinear = 1\ndithersub = 1\ndacfilter = 0\nrender_threads = 2\nrecompiler = 1\n\n"
            + "[Sound Blaster AWE32 PnP #1]\nonboard_ram = 512\ncontrol_pc_speaker = 0\nreceive_input = 1\nreceive_input401 = 0\n\n"
            + "[Tertiary IDE Controller]\nirq = -1\n\n[Quaternary IDE Controller]\nirq = -1\n\n"
            + f"[Hard disks]\nhdd_01_fn = child.vhd\nhdd_01_vhd_parent = {reference}/base.vhd\nhdd_01_ide_channel = 0:0\n"
            + "hdd_01_parameters = 255, 16, 32896, 0, ide\nhdd_01_speed = ramdisk\nhdd_01_vhd_blocksize = 4096\n")


def windows(name, cpu, speed, multi, memory, reference):
    """A Windows 98 machine over the reference disk: 60 emulated seconds on the 486, 25 on the Pentium,
    from power-on, as the reference was first measured."""
    return (GENERAL + machine(name, cpu, speed, multi, memory, "s3_trio64v2dx_pci",
                              extra="cpu_use_dynarec = 1\nfpu_type = internal")
            + "[S3 Trio64V2/DX PCI #1]\nbios = trio64v2dx_pci\n\n[Input devices]\nkeyboard_type = keyboard_ps2\nmouse_type = ps2\n"
            + "tablet_type = none\n\n[Sound]\nfm_driver = ymfm\nsndcard = sb16\n\n"
            + f"[Hard disks]\nhdd_01_fn = child.vhd\nhdd_01_vhd_parent = {reference}/base.vhd\nhdd_01_ide_channel = 0:0\n"
            + "hdd_01_parameters = 63, 16, 4161, 0, ide\nhdd_01_speed = 1997_5400rpm\n\n"
            + "[Floppy and CD-ROM drives]\nfdd_01_type = 35_2hd\nfdd_02_type = none\n")


# KairoX86#437: (name, the machine it copies, game_profile's script). The FreeDOS 486 gets commands typed at its prompt
# (from frame 422 the text screen is up) at unevenly spaced frames, so presses fall in different poll phases, and PS/2
# mouse moves and a click (the controller's aux side, with no DOS driver to take them); win98-486 gets mouse moves, a
# right-click menu closed with Esc, an arrow key and a click on the desktop (up from frame 1767).
INPUT_MACHINES = (
    ("486-input", "486", "640:+0x20,643:-0x20,647:+0x17,649:-0x17,654:+0x13,657:-0x13,662:+0x1c,664:-0x1c,760:+x12,761:+y5,790:-x7,833:-y9,1001:+0x2f,1002:-0x2f,1006:+0x12,1010:-0x12,1013:+0x13,1014:-0x13,1021:+0x1c,1023:-0x1c,1200:+m1,1203:-m1,1250:+x3"),
    ("win98-486-input", "win98-486", "2600:+x40,2630:+y25,2661:-x15,2700:+m2,2703:-m2,2760:+0x01,2762:-0x01,2900:+0x14d,2903:-0x14d,3101:+x7,3207:-y9,3400:+m1,3404:-m1,3555:+y3"),
)


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    test_set, out, reference = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3].rstrip("/")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    frames = {}
    for name, (config, files, count) in MACHINES.items():
        folder = out / name
        folder.mkdir()
        (folder / "86box.cfg").write_text(config, encoding="utf-8", newline="\n")
        for source_folder, file in files:
            source = test_set / source_folder / file
            if source.is_dir():
                shutil.copytree(source, folder / file)
            else:
                shutil.copy2(source, folder / file)
        frames[name] = count
    # The Windows machines' CMOS is the reference's own: the device copies <reference>/<name>/nvr in.
    for name, args, count in (("win98-486", ("486ap4", "i486dx2", 66666666, 2, 32768), 4286),
                              ("win98-pentium", ("tx97", "pentium_p55c", 233333333, 3.5, 65536), 1667)):
        folder = out / name
        folder.mkdir()
        (folder / "86box.cfg").write_text(windows(*args, f"{reference}/{name}"), encoding="utf-8", newline="\n")
        frames[name] = count
    folder = out / "win98-voodoo3"
    folder.mkdir()
    (folder / "86box.cfg").write_text(voodoo3(f"{reference}/win98-voodoo3"), encoding="utf-8", newline="\n")
    frames["win98-voodoo3"] = 4000
    # KairoX86#437: machines that receive input, so a change to when the guest takes keys and the mouse is seen. Each is
    # another machine with script.txt (game_profile's events, typed by run.sh/run.ps1) and, for a Windows one,
    # ref.txt (the reference whose CMOS it starts from: it shares that machine's disk).
    for name, parent, script in INPUT_MACHINES:
        shutil.copytree(out / parent, out / name)
        (out / name / "script.txt").write_text(script, encoding="utf-8", newline="\n")
        if parent.startswith("win98-"):
            (out / name / "ref.txt").write_text(parent, encoding="utf-8", newline="\n")
        frames[name] = frames[parent]
    (out / "machines.json").write_text(json.dumps(frames, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(frames)} machines in {out}")


if __name__ == "__main__":
    main()
