<#
.SYNOPSIS
KairoX86's exactness standard: runs the core of a base revision and the working tree's on the same
machines on the device and fails unless the guest runs alike in both (docs/development.md, "The core").

.DESCRIPTION
Builds the core (the 86Box library and game_profile, as the app's release build makes them) twice:
from the base revision (git archive of it and of the shared commit it pins) and from the working tree.
Both go to the device with the standard's machines (core/test/exact/machines.py). Each machine runs
its frames under each build, and their hashes must match line for line: every frame's picture and
sound, and the guest's state at the end (registers, tsc and all RAM). Prints each machine's speed
under both. Exits with 0 only when every machine matched.

The Windows 98 machines boot the reference disks kept on the device in
/data/local/tmp/kx86/exact/ref/<machine> (base.vhd and nvr/); they are not in the repository.

.EXAMPLE
tools\exact.ps1 -Device 192.168.1.118:5555
The working tree against HEAD on every machine.

.EXAMPLE
tools\exact.ps1 -Device 192.168.1.118:5555 -Base HEAD~3 -Machine xt,486
Two machines, against an older revision.

.EXAMPLE
tools\exact.ps1 -Device 192.168.1.118:5555 -Unlinked
The working tree's core against itself with the recompiler's block linking off (cpu_dyn_block_link
= 0), the plain C dispatch loop: a change to the recompiler goes in only if this matches too.
#>
param(
    [Parameter(Mandatory)][string]$Device,
    # The revision whose core the working tree's is compared with.
    [string]$Base = 'HEAD',
    # Machines of core/test/exact/machines.py (comma-separated); every one otherwise.
    [string]$Machine,
    # The player's ROM set on the device.
    [string]$RomSet = '/data/local/tmp/kx86/bios',
    # Compares the working tree's core with itself unlinked instead of with the base revision's.
    [switch]$Unlinked
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$sdk = [Environment]::GetEnvironmentVariable('ANDROID_HOME', 'User')
if (-not $sdk) { throw 'ANDROID_HOME is not set: it names the Android SDK' }
$ndk = Join-Path $sdk 'ndk\28.2.13676358'
$cmake = Join-Path $sdk 'cmake\3.22.1\bin\cmake.exe'
$ninja = Join-Path $sdk 'cmake\3.22.1\bin\ninja.exe'
$adb = Join-Path $sdk 'platform-tools\adb.exe'
$work = Join-Path $root '.build\exact'
$remote = '/data/local/tmp/kx86/exact'
New-Item -ItemType Directory -Force $work | Out-Null

# The core of the tree at $Source, built as the app's release build makes it (its CMake arguments).
function Build-Core([string]$Source, [string]$Name) {
    $build = Join-Path $work "build-$Name"
    $out = Join-Path $build 'out'
    if (-not (Test-Path (Join-Path $build 'build.ninja'))) {
        & $cmake "-H$Source\kairox86\src\main\cpp" "-B$build" -GNinja "-DCMAKE_MAKE_PROGRAM=$ninja" `
            -DCMAKE_SYSTEM_NAME=Android -DCMAKE_SYSTEM_VERSION=26 -DANDROID_PLATFORM=android-26 -DANDROID_ABI=arm64-v8a `
            -DCMAKE_ANDROID_ARCH_ABI=arm64-v8a "-DANDROID_NDK=$ndk" "-DCMAKE_ANDROID_NDK=$ndk" `
            "-DCMAKE_TOOLCHAIN_FILE=$ndk\build\cmake\android.toolchain.cmake" -DANDROID_STL=c++_shared `
            -DCMAKE_BUILD_TYPE=RelWithDebInfo -DKAIRO_PGO=ON "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=$out" "-DCMAKE_RUNTIME_OUTPUT_DIRECTORY=$out" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "CMake could not configure the $Name core" }
    }
    & $ninja -C $build game_profile 86Box | Select-Object -Last 1 | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "The $Name core did not build" }
    return $out
}

# The base revision's tree: its files and the shared commit it pins, as git archives.
if ($Unlinked) { $Base = 'HEAD' }
$baseCommit = (git -C $root rev-parse $Base).Trim()
$baseSource = Join-Path $work "src-$($baseCommit.Substring(0, 12))"
if (-not (Test-Path (Join-Path $baseSource 'kairox86'))) {
    New-Item -ItemType Directory -Force (Join-Path $baseSource 'shared') | Out-Null
    $sharedCommit = ((git -C $root ls-tree $baseCommit shared) -split '\s+')[2]
    git -C $root archive --format=tar -o (Join-Path $work 'base.tar') $baseCommit
    tar -x -f (Join-Path $work 'base.tar') -C $baseSource
    git -C (Join-Path $root 'shared') archive --format=tar -o (Join-Path $work 'shared.tar') $sharedCommit
    tar -x -f (Join-Path $work 'shared.tar') -C (Join-Path $baseSource 'shared')
    Remove-Item (Join-Path $work 'base.tar'), (Join-Path $work 'shared.tar')
}
$tree = Build-Core $root 'tree'
$builds = if ($Unlinked) { [ordered]@{ base = $tree; tree = $tree } }
          else { [ordered]@{ base = (Build-Core $baseSource "base-$($baseCommit.Substring(0, 12))"); tree = $tree } }
$baseMode = if ($Unlinked) { 'unlinked' } else { '' }

# The machines and both builds on the device.
$machines = Join-Path $work 'machines'
& python (Join-Path $root 'core\test\exact\machines.py') (Join-Path $root 'roms\uitest') $machines "$remote/ref"
if ($LASTEXITCODE -ne 0) { throw 'machines.py failed' }
$frames = Get-Content -Raw (Join-Path $machines 'machines.json') | ConvertFrom-Json
$names = if ($Machine) { $Machine -split ',' } else { $frames.PSObject.Properties.Name }
$cxx = Join-Path $ndk 'toolchains\llvm\prebuilt\windows-x86_64\sysroot\usr\lib\aarch64-linux-android\libc++_shared.so'
& $adb -s $Device shell "su 0 sh -c 'rm -rf $remote/machines $remote/base $remote/tree; mkdir -p $remote/base $remote/tree'"
& $adb -s $Device push $machines "$remote/" | Out-Null
& $adb -s $Device push (Join-Path $root 'core\test\exact\run.sh') "$remote/run.sh" | Out-Null
foreach ($name in $builds.Keys) {
    foreach ($file in @((Join-Path $builds[$name] 'game_profile'), (Join-Path $builds[$name] 'libkairox86_86box.so'), $cxx)) {
        & $adb -s $Device push $file "$remote/$name/" | Out-Null
    }
}
& $adb -s $Device shell "su 0 sh -c 'chmod 755 $remote/run.sh $remote/base/game_profile $remote/tree/game_profile'"

$failed = @()
foreach ($m in $names) {
    if (-not $frames.$m) { throw "No machine $m in core/test/exact/machines.py" }
    $lines = @{}
    foreach ($name in $builds.Keys) {
        $mode = if ($name -eq 'base') { $baseMode } else { '' }
        $lines[$name] = & $adb -s $Device shell "su 0 sh -c '$remote/run.sh $remote $name $m $($frames.$m) $RomSet $mode'"
        if ($LASTEXITCODE -ne 0) { throw "$m under the $name core did not run: $($lines[$name] -join ' ')" }
    }
    & $adb -s $Device shell "cmp $remote/base/$m.hashes $remote/tree/$m.hashes" | Out-Null
    $same = ($LASTEXITCODE -eq 0)
    if (-not $same) { $failed += $m }
    $speed = { param($text) ($text | Where-Object { $_ -like 'host *' }) -replace '^host ([0-9.]+) frames/s \(guest ([0-9.]+)\).*', '$1 of $2' }
    "{0,-14} {1,-8} base {2,-18} tree {3,-18} {4}" -f $m, $frames.$m, (& $speed $lines.base), (& $speed $lines.tree),
        $(if ($same) { 'exact' } else { 'DIFFERS' })
}
if ($failed) { throw "Not exact on: $($failed -join ', ')" }
"Every machine runs alike under both cores."
