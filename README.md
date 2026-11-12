<!-- kairo:discord -->
<p align="center">
  <a href="https://discord.gg/ZkYQ3bPTTq"><img src="https://raw.githubusercontent.com/MrJackSpade/Kairo/main/docs/assets/discord-banner.svg" alt="Join the Kairo Discord" width="49%"></a>
  <a href="https://play.google.com/store/apps/details?id=com.loxifi.kairox86"><img src="https://raw.githubusercontent.com/MrJackSpade/Kairo/main/docs/assets/donate-banner.svg" alt="Donate: buying KairoX86 on Google Play is the donation; it adds no features" width="49%"></a>
</p>
<!-- /kairo:discord -->

<!-- kairo:family -->
<h3 align="center">Other Kairo apps</h3>
<table align="center">
  <tr>
    <td align="center" width="33%"><a href="https://github.com/MrJackSpade/Kairo98"><img src="https://raw.githubusercontent.com/MrJackSpade/Kairo98/main/kairo98/src/main/res/drawable-nodpi/product_icon_art.png" width="96" alt="Kairo98"><br><b>Kairo98</b></a><br>PC-98</td>
    <td align="center" width="33%"><a href="https://github.com/MrJackSpade/KairoDos"><img src="https://raw.githubusercontent.com/MrJackSpade/KairoDos/main/kairodos/src/main/res/drawable-nodpi/product_icon_art.png" width="96" alt="KairoDos"><br><b>KairoDos</b></a><br>DOS</td>
    <td align="center" width="33%"><a href="https://github.com/MrJackSpade/Kairo88"><img src="https://raw.githubusercontent.com/MrJackSpade/Kairo88/main/kairo88/src/main/res/drawable-nodpi/product_icon_art.png" width="96" alt="Kairo88"><br><b>Kairo88</b></a><br>PC-88</td>
  </tr>
  <tr>
    <td align="center" width="33%"><a href="https://github.com/MrJackSpade/Kairo68"><img src="https://raw.githubusercontent.com/MrJackSpade/Kairo68/main/kairo68/src/main/res/drawable-nodpi/product_icon_art.png" width="96" alt="Kairo68"><br><b>Kairo68</b></a><br>X68000</td>
    <td align="center" width="33%"><a href="https://github.com/MrJackSpade/KairoTowns"><img src="https://raw.githubusercontent.com/MrJackSpade/KairoTowns/main/kairotowns/src/main/res/drawable-nodpi/product_icon_art.png" width="96" alt="KairoTowns"><br><b>KairoTowns</b></a><br>FM Towns</td>
    <td align="center" width="33%"><a href="https://github.com/MrJackSpade/KairoMSX"><img src="https://raw.githubusercontent.com/MrJackSpade/KairoMSX/main/kairomsx/src/main/res/drawable-nodpi/product_icon_art.png" width="96" alt="KairoMSX"><br><b>KairoMSX</b></a><br>MSX</td>
  </tr>
  <tr>
    <td align="center" width="33%"><a href="https://github.com/MrJackSpade/KairoST"><img src="https://raw.githubusercontent.com/MrJackSpade/KairoST/main/kairost/src/main/res/drawable-nodpi/product_icon_art.png" width="96" alt="KairoST"><br><b>KairoST</b></a><br>Atari ST</td>
    <td align="center" width="33%"><a href="https://github.com/MrJackSpade/Kairo64"><img src="https://raw.githubusercontent.com/MrJackSpade/Kairo64/main/kairo64/src/main/res/drawable-nodpi/product_icon_art.png" width="96" alt="Kairo64"><br><b>Kairo64</b></a><br>C64</td>
  </tr>
</table>
<p align="center">Every Kairo app is built on <a href="https://github.com/MrJackSpade/Kairo">Kairo</a>, the shared frontend for the game library, controls, and settings.</p>
<!-- /kairo:family -->

# KairoX86

**Build your own period PC on Android phones and handhelds.** KairoX86 is an Android emulator for IBM PC compatibles, from the 1981 IBM PC to Pentium-era machines. It is built on the [Kairo shared frontend](https://github.com/MrJackSpade/Kairo): the same library, controller and touch controls, on-screen keyboard and settings as the other Kairo apps. It runs a pinned copy of [86Box](https://86box.net/), which models real machines with their own BIOS, chipset, video and sound cards. It is an independent project, not an official 86Box release.

## Download

<!-- kairo:download -->
- **[Google Play](https://play.google.com/store/apps/details?id=com.loxifi.kairox86)** (paid): updates automatically. Buying it supports development.
- **[GitHub Releases](https://github.com/MrJackSpade/KairoX86/releases)** (free): install the APK yourself.

Both editions are built from the same source and have the same features. Requires an ARM64 device running Android 8.0 or newer.
<!-- /kairo:download -->

## How it works

KairoX86 has no game catalog. Each library entry is a PC you set up: its hardware, its disk images and the media in its drives. It is kept as an 86Box machine folder (`86box.cfg`, its disks and its CMOS), so a machine made in desktop 86Box can be added as it is.

1. **New entry:** pick a starting machine (a preset), then change any part of it: machine, CPU, memory, video, sound, drives.
2. **Disks:** create blank hard disks and floppies in the app, and put install floppies or CDs in the drives.
3. **Install:** boot it, partition and format, and install DOS, Windows or your games as you would on the real machine.

## Firmware

KairoX86 comes with [GLaBIOS](https://glabios.org/), a free BIOS for the IBM PC, so an XT-class PC works without any firmware from you. Every other machine needs its own BIOS: import the folder holding 86Box's BIOS and device firmware (86Box calls it its ROM set), and KairoX86 recognizes each file by its contents, whatever it is named.

## Documentation

- [Adding a game](docs/add-a-game.md): setting up a game as a machine, step by step
- [Creating a new game on a blank disk](docs/create-a-game.md): a new PC, its blank hard disk, and installing DOS and games onto it
- [Licensing and credits](docs/licensing.md): code license and third-party components
- [Source provenance](docs/source-import.md): where the emulator source came from and what was copied
- [Development](docs/development.md): building, host tests and generated code
- [The core's speed record](docs/core-performance.md): what each core change gained, and the exactness standard every one passes

## Help and community

<!-- kairo:community -->
- **Report a game problem** in [Issues](https://github.com/MrJackSpade/KairoX86/issues). Include the title, disk format, and what happened.
- **Chat** with other players on [Discord](https://discord.gg/ZkYQ3bPTTq).
<!-- /kairo:community -->

## Building from source

<!-- kairo:clone -->
Clone with submodules to get the pinned shared frontend:

```sh
git clone --recurse-submodules https://github.com/MrJackSpade/KairoX86.git
```
<!-- /kairo:clone -->

Build the app, and optionally install it, with the shared build script:

```powershell
shared\tools\build.ps1 -Install <adb serial>
```

## License

<!-- kairo:license -->
First-party code is [GPL-2.0-or-later](LICENSE.md). The app as distributed is GPLv3 because it bundles GPLv3 components. Third-party components keep their own licenses; see [licensing and credits](docs/licensing.md) and [source provenance](docs/source-import.md).
<!-- /kairo:license -->
