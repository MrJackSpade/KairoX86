<#
One machine of the exactness standard under one build of the core, on this PC (tools/exact.ps1
-Local), as run.sh runs it on the device:
  run.ps1 <exact folder> <build folder> <machine> <frames> <ROM set> <reference folder> [unlinked]
<build folder> holds game_profile and the core library; <exact folder>/machines/<machine> the machine,
and <reference folder>/<machine>/nvr the CMOS a Windows machine starts from. With "unlinked", the
machine runs with the recompiler's block linking off (cpu_dyn_block_link = 0). Writes the hashes to
<build folder>/<machine>.hashes and prints game_profile's host and state lines. game_profile runs
under shared\tools\run-limited.ps1 (its memory bound).
#>
param(
    [Parameter(Mandatory)][string]$Exact,
    [Parameter(Mandatory)][string]$Build,
    [Parameter(Mandatory)][string]$Name,
    [Parameter(Mandatory)][int]$Frames,
    [Parameter(Mandatory)][string]$RomSet,
    [Parameter(Mandatory)][string]$Reference,
    [string]$Mode = ''
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$machine = Join-Path $Build "machine-$Name"
$work = Join-Path $Build "work-$Name"
foreach ($folder in $machine, $work) { if (Test-Path $folder) { Remove-Item -Recurse -Force $folder } }
Copy-Item -Recurse (Join-Path $Exact "machines\$Name") $machine
$nvr = Join-Path $Reference "$Name\nvr"
if (Test-Path $nvr) {
    if (Test-Path (Join-Path $machine 'nvr')) { Remove-Item -Recurse -Force (Join-Path $machine 'nvr') }
    Copy-Item -Recurse $nvr (Join-Path $machine 'nvr')
}
if ($Mode -eq 'unlinked') {
    $config = Join-Path $machine '86box.cfg'
    $text = (Get-Content -Raw $config) -replace '(?m)^\[Machine\]$', "[Machine]`ncpu_dyn_block_link = 0"
    [IO.File]::WriteAllText($config, $text)
}
New-Item -ItemType Directory $work | Out-Null
$log = Join-Path $Build "$Name.log"
& (Join-Path $root 'shared\tools\run-limited.ps1') (Join-Path $Build 'game_profile.exe') $RomSet $work $machine $Frames '-' `
    --hashes (Join-Path $Build "$Name.hashes") *> $log
$status = $LASTEXITCODE
Remove-Item -Recurse -Force $work, $machine
Get-Content $log | Where-Object { $_ -match '^(host|state)' }
exit $status
