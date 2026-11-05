<#
.SYNOPSIS
KairoX86's exactness standard: runs the core of a base revision and the working tree's on the same
machines and fails unless the guest runs alike in both (docs/development.md, "The core").

.DESCRIPTION
Builds the core (the 86Box library and game_profile) twice: from the base revision (git archive of
it and of the shared commit it pins) and from the working tree. Each of the standard's machines
(core/test/exact/machines.py) runs its frames under each build, and their hashes must match line for
line: every frame's picture and sound, and the guest's state at the end (registers, tsc and all RAM).
Prints each machine's speed under both. Exits with 0 only when every machine matched.

With -Device, both builds are the app's release build and run on the device; with -Local, both are
built for this PC (llvm-mingw) and run here, much faster: what the guest does is the same, but the
recompiler is the PC's (x86-64), not the device's (ARM64), so a change to the recompiler's ARM64
code generation is not covered by -Local.

The Windows 98 machines boot reference disks (<reference>/<machine>/base.vhd and nvr/, not in the
repository): on the device in /data/local/tmp/kx86/exact/ref, here in .build\exact-ref by default.

.EXAMPLE
tools\exact.ps1 -Local
The working tree against HEAD on every machine, on this PC.

.EXAMPLE
tools\exact.ps1 -Device 192.168.1.118:5555 -Base HEAD~3 -Machine xt,486
Two machines on the device, against an older revision.

.EXAMPLE
tools\exact.ps1 -Device 192.168.1.118:5555 -Unlinked
The working tree's core against itself with the recompiler's block linking off (cpu_dyn_block_link
= 0), the plain C dispatch loop: a change to the recompiler goes in only if this matches too.
#>
[CmdletBinding(DefaultParameterSetName = 'Device')]
param(
    [Parameter(Mandatory, ParameterSetName = 'Device')][string]$Device,
    # Builds and runs both cores on this PC instead of the device.
    [Parameter(Mandatory, ParameterSetName = 'Local')][switch]$Local,
    # The revision whose core the working tree's is compared with.
    [string]$Base = 'HEAD',
    # Machines of core/test/exact/machines.py (comma-separated); every one otherwise.
    [string]$Machine,
    # The ROM set: the player's on the device (/data/local/tmp/kx86/bios), G:\tools\src\86box-roms here.
    [string]$RomSet,
    # The Windows 98 machines' reference disks on this PC.
    [Parameter(ParameterSetName = 'Local')][string]$Reference,
    # Compares the working tree's core with itself unlinked instead of with the base revision's.
    [switch]$Unlinked,
    # Each device build's profile (KairoX86#123): off by default, since a change to the core makes the
    # recorded profile stale; 'use' builds with core/pgo as the app does (-BasePgo off -TreePgo use
    # measures the profile itself). The PC's builds have none.
    [Parameter(ParameterSetName = 'Device')][ValidateSet('use', 'off')][string]$BasePgo = 'off',
    [Parameter(ParameterSetName = 'Device')][ValidateSet('use', 'off')][string]$TreePgo = 'off'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $PSScriptRoot 'CoreBuild.psm1') -Force
$tools = Get-CoreTools
$adb = $tools.Adb
$work = Join-Path $root '.build\exact'
$remote = '/data/local/tmp/kx86/exact'
New-Item -ItemType Directory -Force $work | Out-Null
if (-not $RomSet) { $RomSet = if ($Local) { 'G:\tools\src\86box-roms' } else { '/data/local/tmp/kx86/bios' } }
if ($Local -and -not $Reference) { $Reference = Join-Path $root '.build\exact-ref' }

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
if ($Local) {
    $tree = Build-LocalCore $root (Join-Path $work 'local-tree')
    $builds = if ($Unlinked) { [ordered]@{ base = $tree; tree = $tree } }
              else { [ordered]@{ base = (Build-LocalCore $baseSource (Join-Path $work "local-base-$($baseCommit.Substring(0, 12))")); tree = $tree } }
} else {
    $tree = Build-Core $root (Join-Path $work "build-tree-$TreePgo") $TreePgo
    $builds = if ($Unlinked) { [ordered]@{ base = $tree; tree = $tree } }
              else { [ordered]@{ base = (Build-Core $baseSource (Join-Path $work "build-base-$($baseCommit.Substring(0, 12))-$BasePgo") $BasePgo)
                                 tree = $tree } }
}
$baseMode = if ($Unlinked) { 'unlinked' } else { '' }

# The machines, and on the device both builds.
$machines = Join-Path $work 'machines'
$machineReference = if ($Local) { $Reference.Replace('\', '/') } else { "$remote/ref" }
& python (Join-Path $root 'core\test\exact\machines.py') (Join-Path $root 'roms\uitest') $machines $machineReference
if ($LASTEXITCODE -ne 0) { throw 'machines.py failed' }
$frames = Get-Content -Raw (Join-Path $machines 'machines.json') | ConvertFrom-Json
$names = if ($Machine) { $Machine -split ',' } else { $frames.PSObject.Properties.Name }
if ($Local) {
    # Each build's own folder: an unlinked run's base and tree are one build, whose hashes must not meet.
    $runs = [ordered]@{}
    foreach ($name in $builds.Keys) {
        $runs[$name] = Join-Path $work "local-run-$name"
        if (Test-Path $runs[$name]) { Remove-Item -Recurse -Force $runs[$name] }
        New-Item -ItemType Directory $runs[$name] | Out-Null
        Copy-Item (Join-Path $builds[$name] '*') $runs[$name] -Include '*.exe', '*.dll'
    }
} else {
    $cxx = $tools.CxxShared
    & $adb -s $Device shell "su 0 sh -c 'rm -rf $remote/machines $remote/base $remote/tree; mkdir -p $remote/base $remote/tree'"
    Push-ToDevice $Device $machines "$remote/"
    Push-ToDevice $Device (Join-Path $root 'core\test\exact\run.sh') "$remote/run.sh"
    foreach ($name in $builds.Keys) {
        foreach ($file in @((Join-Path $builds[$name] 'game_profile'), (Join-Path $builds[$name] 'libkairox86_86box.so'), $cxx)) {
            Push-ToDevice $Device $file "$remote/$name/"
        }
    }
    & $adb -s $Device shell "su 0 sh -c 'chmod 755 $remote/run.sh $remote/base/game_profile $remote/tree/game_profile'"
}

$failed = @()
foreach ($m in $names) {
    if (-not $frames.$m) { throw "No machine $m in core/test/exact/machines.py" }
    $lines = @{}
    foreach ($name in $builds.Keys) {
        $mode = if ($name -eq 'base') { $baseMode } else { '' }
        $lines[$name] = if ($Local) {
            & (Join-Path $root 'core\test\exact\run.ps1') $work $runs[$name] $m $frames.$m $RomSet $Reference $mode
        } else {
            & $adb -s $Device shell "su 0 sh -c '$remote/run.sh $remote $name $m $($frames.$m) $RomSet $mode'"
        }
        if ($LASTEXITCODE -ne 0) { throw "$m under the $name core did not run: $($lines[$name] -join ' ')" }
    }
    if ($Local) {
        $same = (Get-FileHash (Join-Path $runs.base "$m.hashes")).Hash -eq (Get-FileHash (Join-Path $runs.tree "$m.hashes")).Hash
    } else {
        & $adb -s $Device shell "cmp $remote/base/$m.hashes $remote/tree/$m.hashes" | Out-Null
        $same = ($LASTEXITCODE -eq 0)
    }
    if (-not $same) { $failed += $m }
    $speed = { param($text) ($text | Where-Object { $_ -like 'host *' }) -replace '^host ([0-9.]+) frames/s \(guest ([0-9.]+)\).*', '$1 of $2' }
    "{0,-14} {1,-8} base {2,-18} tree {3,-18} {4}" -f $m, $frames.$m, (& $speed $lines.base), (& $speed $lines.tree),
        $(if ($same) { 'exact' } else { 'DIFFERS' })
}
if ($failed) { throw "Not exact on: $($failed -join ', ')" }
"Every machine runs alike under both cores."
