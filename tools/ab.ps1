<#
.SYNOPSIS
An interleaved speed comparison of two prebuilt cores on the device (KairoX86#349): the A/B protocol
whose noise floor docs/core-performance.md records.

.DESCRIPTION
Builds nothing. Pushes core A and core B (each a Build-Core output folder: out\game_profile and
out\libkairox86_86box.so), and runs each of the standard's machines (core/test/exact/machines.py)
under A then B, round after round (A B A B ...), through core/test/exact/run.sh. Prints every run's
frames a second, each core's median and spread (min-max), and the difference of the medians. Fails
if any run's hashes differ between the cores: a speed comparison is only meaningful between cores
that run the guest alike. The exactness standard itself is tools/exact.ps1.

.EXAMPLE
tools\ab.ps1 -Device 192.168.1.118:5555 -A .build\exact\build-tree-use -B ..\other\build -Machine win98-486,486 -Rounds 5
#>
param(
    [Parameter(Mandatory)][string]$Device,
    # Build-Core output folders.
    [Parameter(Mandatory)][string]$A,
    [Parameter(Mandatory)][string]$B,
    # Machines of core/test/exact/machines.py (a list, or comma-separated).
    [Parameter(Mandatory)][string[]]$Machine,
    [int]$Rounds = 5,
    [string]$RomSet = '/data/local/tmp/kx86/bios'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $PSScriptRoot 'CoreBuild.psm1') -Force
$tools = Get-CoreTools
$adb = $tools.Adb
$work = Join-Path $root '.build\ab'
$remote = '/data/local/tmp/kx86/exact'
New-Item -ItemType Directory -Force $work | Out-Null

$builds = [ordered]@{ 'ab-a' = (Resolve-Path $A).Path; 'ab-b' = (Resolve-Path $B).Path }
foreach ($build in $builds.Values) {
    foreach ($file in 'game_profile', 'libkairox86_86box.so') {
        if (-not (Test-Path (Join-Path $build "out\$file"))) { throw "$build has no out\$file" }
    }
}

# The machines (the exactness standard's, with its reference disks on the device), and both cores.
$machines = Join-Path $work 'machines'
& python (Join-Path $root 'core\test\exact\machines.py') (Join-Path $root 'roms\uitest') $machines "$remote/ref"
if ($LASTEXITCODE -ne 0) { throw 'machines.py failed' }
$frames = Get-Content -Raw (Join-Path $machines 'machines.json') | ConvertFrom-Json
& $adb -s $Device shell "su 0 sh -c 'rm -rf $remote/machines $remote/ab-a $remote/ab-b; mkdir -p $remote/ab-a $remote/ab-b'"
if ($LASTEXITCODE -ne 0) { throw "could not prepare $remote on $Device" }
Push-ToDevice $Device $machines "$remote/"
Push-ToDevice $Device (Join-Path $root 'core\test\exact\run.sh') "$remote/run.sh"
foreach ($name in $builds.Keys) {
    foreach ($file in @((Join-Path $builds[$name] 'out\game_profile'), (Join-Path $builds[$name] 'out\libkairox86_86box.so'), $tools.CxxShared)) {
        Push-ToDevice $Device $file "$remote/$name/"
    }
}
& $adb -s $Device shell "su 0 sh -c 'chmod 755 $remote/run.sh $remote/ab-a/game_profile $remote/ab-b/game_profile'"

$median = { param([double[]]$v) $s = $v | Sort-Object; if ($s.Count % 2) { $s[($s.Count - 1) / 2] } else { ($s[$s.Count / 2 - 1] + $s[$s.Count / 2]) / 2 } }
$different = @()
foreach ($m in ($Machine | ForEach-Object { $_ -split ',' })) {
    if (-not $frames.$m) { throw "No machine $m in core/test/exact/machines.py" }
    $speeds = @{ 'ab-a' = @(); 'ab-b' = @() }
    for ($round = 1; $round -le $Rounds; $round++) {
        foreach ($name in $builds.Keys) {
            $lines = & $adb -s $Device shell "su 0 sh -c '$remote/run.sh $remote $name $m $($frames.$m) $RomSet'"
            if ($LASTEXITCODE -ne 0) { throw "$m under $name did not run: $($lines -join ' ')" }
            $host_line = $lines | Where-Object { $_ -like 'host *' }
            if (-not $host_line) { throw "$m under $name printed no host line: $($lines -join ' ')" }
            $speeds[$name] += [double]($host_line -replace '^host ([0-9.]+) frames/s.*', '$1')
        }
        & $adb -s $Device shell "cmp $remote/ab-a/$m.hashes $remote/ab-b/$m.hashes" | Out-Null
        $same = ($LASTEXITCODE -eq 0)
        if (-not $same) { $different += "$m (round $round)" }
        '{0,-14} round {1}  A {2,7:N2}  B {3,7:N2}  {4}' -f $m, $round, $speeds['ab-a'][-1], $speeds['ab-b'][-1], $(if ($same) { 'alike' } else { 'DIFFERENT' })
    }
    $ma = & $median $speeds['ab-a']; $mb = & $median $speeds['ab-b']
    $sa = ($speeds['ab-a'] | Measure-Object -Minimum -Maximum); $sb = ($speeds['ab-b'] | Measure-Object -Minimum -Maximum)
    '{0,-14} median A {1:N2} ({2:N2}-{3:N2})  B {4:N2} ({5:N2}-{6:N2})  B-A {7:+0.0;-0.0;0.0}%' -f $m, $ma, $sa.Minimum, $sa.Maximum, $mb, $sb.Minimum, $sb.Maximum, (($mb / $ma - 1) * 100)
}
& $adb -s $Device shell "su 0 sh -c 'rm -rf $remote/ab-a $remote/ab-b'" | Out-Null
if ($different) { throw "The cores ran the guest differently: $($different -join ', ')" }
