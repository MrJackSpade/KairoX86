<#
.SYNOPSIS
The device's core as the app's release build makes it, for the tools that run it over adb
(tools/exact.ps1, tools/pgo-train.ps1): the NDK, CMake and adb they use, and the build itself.
#>
$ErrorActionPreference = 'Stop'
$sdk = [Environment]::GetEnvironmentVariable('ANDROID_HOME', 'User')
if (-not $sdk) { throw 'ANDROID_HOME is not set: it names the Android SDK' }
$script:Ndk = Join-Path $sdk 'ndk\28.2.13676358'
$script:CMake = Join-Path $sdk 'cmake\3.22.1\bin\cmake.exe'
$script:Ninja = Join-Path $sdk 'cmake\3.22.1\bin\ninja.exe'
$script:Adb = Join-Path $sdk 'platform-tools\adb.exe'

function Get-CoreTools {
    [pscustomobject]@{
        Ndk = $script:Ndk
        Adb = $script:Adb
        # The NDK's llvm-profdata and the C++ runtime the device's binaries load.
        Profdata = Join-Path $script:Ndk 'toolchains\llvm\prebuilt\windows-x86_64\bin\llvm-profdata.exe'
        CxxShared = Join-Path $script:Ndk 'toolchains\llvm\prebuilt\windows-x86_64\sysroot\usr\lib\aarch64-linux-android\libc++_shared.so'
    }
}

<#
Builds game_profile and the 86Box library of the tree at $Source into $Build\out and returns that
folder. The arguments are the app's release build's, $Pgo choosing the core's profile: 'use' (the
recorded one, as the app builds it), 'off' or 'generate' (the build that records one).
#>
# $Options: more CMake options for the build's configuration (-DK9X_DIAG=ON for the diagnostic counters).
function Build-Core([string]$Source, [string]$Build, [ValidateSet('use', 'off', 'generate')][string]$Pgo = 'use', [string[]]$Options = @()) {
    $out = Join-Path $Build 'out'
    if (-not (Test-Path (Join-Path $Build 'build.ninja'))) {
        # An array even for one argument: splatting a lone string would pass it character by character.
        $pgoArgs = @(switch ($Pgo) {
            'use' { '-DKAIRO_PGO=ON' }
            'off' { '-DKAIRO_PGO=OFF' }
            'generate' { '-DKAIRO_PGO=OFF'; '-DKAIROX86_PGO_GENERATE=ON' }
        })
        $ndk = $script:Ndk
        & $script:CMake "-H$Source\kairox86\src\main\cpp" "-B$Build" -GNinja "-DCMAKE_MAKE_PROGRAM=$script:Ninja" `
            -DCMAKE_SYSTEM_NAME=Android -DCMAKE_SYSTEM_VERSION=26 -DANDROID_PLATFORM=android-26 -DANDROID_ABI=arm64-v8a `
            -DCMAKE_ANDROID_ARCH_ABI=arm64-v8a "-DANDROID_NDK=$ndk" "-DCMAKE_ANDROID_NDK=$ndk" `
            "-DCMAKE_TOOLCHAIN_FILE=$ndk\build\cmake\android.toolchain.cmake" -DANDROID_STL=c++_shared `
            -DCMAKE_BUILD_TYPE=RelWithDebInfo @pgoArgs @Options "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=$out" "-DCMAKE_RUNTIME_OUTPUT_DIRECTORY=$out" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "CMake could not configure the core in $Build" }
    }
    & $script:Ninja -C $Build game_profile 86Box | Select-Object -Last 1 | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "The core in $Build did not build" }
    return $out
}

# Pushes $Local to $Remote on $Device, failing at once if adb couldn't (a full device, a dropped link).
function Push-ToDevice([string]$Device, [string]$Local, [string]$Remote) {
    & $script:Adb -s $Device push $Local $Remote | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "adb could not push $Local to $Remote on $Device" }
}

Export-ModuleMember -Function Get-CoreTools, Build-Core, Push-ToDevice
