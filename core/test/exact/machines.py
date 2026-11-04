#!/usr/bin/env python3
"""The machines of KairoX86's exactness standard (docs/development.md, "The core"): each runs a fixed
number of frames under game_profile, and a change to the core goes in only if every machine's picture
and sound hashes, frame by frame, and its state at the end (registers, tsc and all RAM) match the core
without the change.

  machines.py <test set> <out folder> <reference folder on the device>

<test set> is the local UI test set (roms/uitest: xt/fd13-720k.img, dos486/freedos.img and
dos486/nvr). <out folder> receives one folder per machine, and machines.json: each machine's frames.
The Windows 98 machines boot the reference disks kept on the device, <reference folder>/win98-486 and
<reference folder>/win98-p5 (base.vhd and nvr/ each; docs/development.md): each run opens a new
differencing disk over the base, so every run starts from the same disk.
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
    (out / "machines.json").write_text(json.dumps(frames, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(frames)} machines in {out}")


if __name__ == "__main__":
    main()
