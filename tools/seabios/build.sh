#!/usr/bin/env bash
# Builds the free machine's firmware (docs/source-import.md, "SeaBIOS") from the pinned snapshot in
# third_party/seabios, with the configuration in tools/seabios/seabios.config:
#   firmware/machines/kairo_pc/seabios.bin       SeaBIOS for the free machine
#   firmware/video/kairo/seavgabios_cirrus.bin   SeaVGABIOS for its Cirrus Logic GD5446
#
#   tools/seabios/build.sh            builds them and writes them into firmware/
#   tools/seabios/build.sh --check    builds them and fails unless they are the committed files, byte for byte
#
# The build is reproducible: the same snapshot, configuration and toolchain give the same bytes (its version
# string carries no date or host). It runs in Git Bash with:
#   - GCC 13.2.0 / binutils 2.41 for i686-elf (lordmilko/i686-elf-tools 13.2.0, i686-elf-tools-windows.zip,
#     sha256 79307a5e3a7465ac39874d2b8d73751ecf1e1b230eed091c6e0c2880c83f327d), in $SEABIOS_TOOLCHAIN
#     (G:/tools/i686-elf-13.2.0 by default);
#   - GNU Make 4.4.1 (MSYS2 make-4.4.1-3-x86_64.pkg.tar.zst, sha256
#     af0bdba17f06fe037f0194069adaa31a8fe45f1a11381501896aea1fae37bd5d), in $SEABIOS_MAKE
#     (G:/tools/msys-make-4.4.1-3/usr/bin by default);
#   - Python 3 as "python".
# SeaBIOS's kconfig host tool needs POSIX headers the Windows toolchain lacks, so kconfig.py writes its
# configuration instead.
set -euo pipefail

check=0
if [ "${1:-}" = "--check" ]; then
    check=1
elif [ $# -ne 0 ]; then
    echo "usage: tools/seabios/build.sh [--check]" >&2
    exit 2
fi

root="$(cd "$(dirname "$0")/../.." && pwd)"
toolchain="${SEABIOS_TOOLCHAIN:-/g/tools/i686-elf-13.2.0}"
make_dir="${SEABIOS_MAKE:-/g/tools/msys-make-4.4.1-3/usr/bin}"
for tool in "$toolchain/bin/i686-elf-gcc.exe" "$make_dir/make.exe"; do
    if [ ! -f "$tool" ]; then
        echo "build.sh: $tool is missing (see this script's header for the toolchain)" >&2
        exit 1
    fi
done
version="$("$toolchain/bin/i686-elf-gcc" --version | head -1 | tr -d '\r')"
if [ "$version" != "i686-elf-gcc.exe (GCC) 13.2.0" ]; then
    echo "build.sh: the toolchain is \"$version\", not GCC 13.2.0" >&2
    exit 1
fi

# SeaBIOS's Makefile cannot take a path with spaces: build in a temporary folder by its short name.
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
work="$(cygpath -u "$(cygpath -d "$work")")"
case "$work" in
    *" "*) echo "build.sh: no space-free path for $work" >&2; exit 1 ;;
esac
cp -r "$root/third_party/seabios" "$work/src"
cd "$work/src"
mkdir -p out/include/config out/scripts/kconfig out/src/hw out/src/fw out/src/std out/vgasrc
python "$root/tools/seabios/kconfig.py" . "$root/tools/seabios/seabios.config" .config out/autoconf.h
PATH="$make_dir:$toolchain/bin:$PATH" make CURDIR="$work/src" PYTHON=python CROSS_PREFIX=i686-elf- \
    CPP=i686-elf-cpp EXTRAVERSION=-kairox86 > "$work/build.log" 2>&1 || { cat "$work/build.log" >&2; exit 1; }

status=0
for pair in "out/bios.bin:firmware/machines/kairo_pc/seabios.bin" \
            "out/vgabios.bin:firmware/video/kairo/seavgabios_cirrus.bin"; do
    built="${pair%%:*}"
    shipped="$root/${pair#*:}"
    if [ $check -eq 1 ]; then
        if ! cmp -s "$built" "$shipped"; then
            echo "build.sh: ${pair#*:} is not what the snapshot builds" >&2
            status=1
        fi
    else
        mkdir -p "$(dirname "$shipped")"
        cp "$built" "$shipped"
    fi
    sha256sum "$built" | sed "s|$built|${pair#*:}|"
done
exit $status
