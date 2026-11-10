<#
.SYNOPSIS
Records the core's profile (KairoX86#123): runs the core built to record one (-fprofile-generate)
through machines of the exactness standard on the device and freezes the merged profile into
core/pgo (arm64.proftext and profile.json, shared/tools/pgo_freeze.py), which the app's arm64 build
then compiles the core with.

.DESCRIPTION
Builds game_profile and the 86Box library from the working tree with KAIROX86_PGO_GENERATE (and
KAIRO_PGO off), pushes them with the machines of core/test/exact/machines.py, and runs each
training machine through its frames (core/test/exact/run.sh), every run writing its raw profiles.
They are pulled and merged with the NDK's llvm-profdata, and the merged profile frozen into core/pgo.
Train from the tree you commit: a function whose code no longer matches the profile is a build
error. The machines not trained on (v20, at, 386sx and pentium by default) stay to evaluate it with
tools/exact.ps1 -BasePgo off -TreePgo use.

.EXAMPLE
tools\pgo-train.ps1 -Device 192.168.1.118:5555 -Game <the owner's doom486 machine folder>
The profile in core/pgo is trained so (KairoX86#378): the standard machines and DOOM's demo.
#>
param(
    [Parameter(Mandatory)][string]$Device,
    # The training machines of core/test/exact/machines.py (comma-separated).
    [string]$Machine = 'xt,486,win98-486,win98-pentium',
    # The player's ROM set on the device.
    [string]$RomSet = '/data/local/tmp/kx86/bios',
    # A game machine folder to train on as well (KairoX86#378: the owner's doom486, DOOM's demo), which the
    # repository cannot hold: run for GameWarmup + GameFrames frames with GameCommands typed at its prompt.
    [string]$Game,
    [int]$GameWarmup = 3500,
    [int]$GameFrames = 2500,
    [string]$GameCommands = 'C:|DOOM'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $PSScriptRoot 'CoreBuild.psm1') -Force
$tools = Get-CoreTools
$adb = $tools.Adb
$work = Join-Path $root '.build\pgo'
# The exactness standard's device folder: its machines and reference disks (ref/) are shared.
$remote = '/data/local/tmp/kx86/exact'
$build = 'pgogen'
New-Item -ItemType Directory -Force $work | Out-Null

$out = Build-Core $root (Join-Path $work 'build-generate') 'generate'
$machines = Join-Path $work 'machines'
& python (Join-Path $root 'core\test\exact\machines.py') (Join-Path $root 'roms\uitest') $machines "$remote/ref"
if ($LASTEXITCODE -ne 0) { throw 'machines.py failed' }
$frames = Get-Content -Raw (Join-Path $machines 'machines.json') | ConvertFrom-Json

& $adb -s $Device shell "su 0 sh -c 'rm -rf $remote/machines $remote/$build; mkdir -p $remote/$build/profiles'"
Push-ToDevice $Device $machines "$remote/"
Push-ToDevice $Device (Join-Path $root 'core\test\exact\run.sh') "$remote/run.sh"
foreach ($file in @((Join-Path $out 'game_profile'), (Join-Path $out 'libkairox86_86box.so'), $tools.CxxShared)) {
    Push-ToDevice $Device $file "$remote/$build/"
}
& $adb -s $Device shell "su 0 sh -c 'chmod 755 $remote/run.sh $remote/$build/game_profile'"

foreach ($m in ($Machine -split ',')) {
    if (-not $frames.$m) { throw "No machine $m in core/test/exact/machines.py" }
    # Each module (game_profile, each loaded copy of the library) writes its own raw profile.
    $lines = & $adb -s $Device shell "su 0 sh -c 'LLVM_PROFILE_FILE=$remote/$build/profiles/$m-%p-%m.profraw $remote/run.sh $remote $build $m $($frames.$m) $RomSet'"
    if ($LASTEXITCODE -ne 0) { throw "$m did not run: $($lines -join ' ')" }
    "{0,-14} {1,-8} {2}" -f $m, $frames.$m, (($lines | Where-Object { $_ -like 'host *' }) -join ' ')
}

if ($Game) {
    if (-not (Test-Path (Join-Path $Game '86box.cfg'))) { throw "$Game is not a machine folder (no 86box.cfg)" }
    $name = Split-Path -Leaf $Game
    Push-ToDevice $Device $Game "$remote/machines/"
    $d = "$remote/$build"
    $lines = & $adb -s $Device shell "su 0 sh -c 'rm -rf $d/machine-game $d/work-game; cp -r $remote/machines/$name $d/machine-game; mkdir -p $d/work-game; echo kx86pgo > /sys/power/wake_lock; cd $d; LLVM_PROFILE_FILE=$d/profiles/$name-%p-%m.profraw LD_LIBRARY_PATH=$d ./game_profile $RomSet $d/work-game $d/machine-game $GameFrames - --warmup $GameWarmup --commands \`"$GameCommands\`" > $d/game.log 2>&1; S=`$?; echo kx86pgo > /sys/power/wake_unlock; grep -E ^host $d/game.log; rm -rf $d/machine-game $d/work-game; exit `$S'"
    if ($LASTEXITCODE -ne 0) { throw "$name did not run: $($lines -join ' ')" }
    "{0,-14} {1,-8} {2}" -f $name, ($GameWarmup + $GameFrames), (($lines | Where-Object { $_ -like 'host *' }) -join ' ')
}

$raw = Join-Path $work 'profiles'
if (Test-Path $raw) { Remove-Item -Recurse -Force $raw }
& $adb -s $Device pull "$remote/$build/profiles" $work | Out-Null
$files = @(Get-ChildItem $raw -Filter *.profraw)
if (-not $files) { throw "The runs wrote no raw profiles in $remote/$build/profiles" }
$merged = Join-Path $work 'merged.profdata'
& $tools.Profdata merge -o $merged @($files.FullName)
if ($LASTEXITCODE -ne 0) { throw 'llvm-profdata could not merge the raw profiles' }
$pgo = Join-Path $root 'core\pgo'
New-Item -ItemType Directory -Force $pgo | Out-Null
& python (Join-Path $root 'shared\tools\pgo_freeze.py') --profdata $merged --llvm-profdata $tools.Profdata --root $root `
    --text (Join-Path $pgo 'arm64.proftext') --manifest (Join-Path $pgo 'profile.json') --ndk (Split-Path -Leaf $tools.Ndk) `
    --sparse --note "tools/pgo-train.ps1 on the RG DS: $Machine through their exactness-standard frames$(if ($Game) { ', and ' + (Split-Path -Leaf $Game) + ' (' + $GameCommands + ')' })" @($files.FullName)
if ($LASTEXITCODE -ne 0) { throw 'pgo_freeze.py failed' }
& $adb -s $Device shell "su 0 sh -c 'rm -rf $remote/$build'"
"Profile recorded from $($files.Count) raw profiles: core/pgo"
