#!/system/bin/sh
# One machine of the exactness standard under one build of the core, on the device (tools/exact.ps1):
#   run.sh <exact folder> <build> <machine> <frames> <ROM set> [unlinked]
# <exact folder>/<build> holds game_profile and the core library; <exact folder>/machines/<machine> the
# machine, and <exact folder>/ref/<machine>/nvr the CMOS a Windows machine starts from. With
# "unlinked", the machine runs with the recompiler's block linking off (cpu_dyn_block_link = 0), the
# plain C dispatch loop every linked run must match. Writes the hashes to
# <exact folder>/<build>/<machine>.hashes and prints game_profile's host and state lines.
set -e
EXACT=$1; BUILD=$2; NAME=$3; FRAMES=$4; ROMS=$5; MODE=$6
DIR=$EXACT/$BUILD
MACHINE=$DIR/machine-$NAME
rm -rf "$MACHINE"
cp -r "$EXACT/machines/$NAME" "$MACHINE"
if [ -d "$EXACT/ref/$NAME/nvr" ]; then
  rm -rf "$MACHINE/nvr"
  cp -r "$EXACT/ref/$NAME/nvr" "$MACHINE/nvr"
fi
if [ "$MODE" = unlinked ]; then
  sed -i 's/^\[Machine\]$/[Machine]\ncpu_dyn_block_link = 0/' "$MACHINE/86box.cfg"
fi
WORK=$DIR/work-$NAME
rm -rf "$WORK"
mkdir -p "$WORK"
echo kx86exact > /sys/power/wake_lock
cd "$DIR"
LD_LIBRARY_PATH=$DIR ./game_profile "$ROMS" "$WORK" "$MACHINE" "$FRAMES" - --hashes "$DIR/$NAME.hashes" > "$DIR/$NAME.log" 2>&1 || STATUS=$?
echo kx86exact > /sys/power/wake_unlock
rm -rf "$WORK" "$MACHINE"
grep -E '^(host|state)' "$DIR/$NAME.log"
exit ${STATUS:-0}
