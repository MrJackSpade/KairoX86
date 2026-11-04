# KairoX86's ARM64 core profile

The Android arm64 build of the core (the 86Box library and `core/`) is compiled with this profile of
the RG DS running the exactness standard's machines
([#123](https://github.com/MrJackSpade/KairoX86/issues/123)). It is on by default; `-Ppgo=false`
(Gradle) or `-DKAIRO_PGO=OFF` (CMake) builds the unprofiled core to compare against. Host and x86_64
builds don't use it.

`arm64.proftext` holds LLVM function names, CFG hashes and execution counts. It contains no guest
data. `profile.json` records the compiler that made it, the source revision it was trained on, the
text's SHA-256 and the raw profiles merged into it. `shared/cmake/KairoPgo.cmake` checks both,
restores the checkout root in function names (`@KAIRO_SOURCE@/`) and indexes the text with the NDK's
`llvm-profdata` at configure time.

## When the core changes

A function whose code no longer matches its profile is a build error
(`-Werror=profile-instr-out-of-date`), so the profile never silently stops applying. After a change
to the core, check it with the profile off, then train the profile again on the device from the tree
you commit:

```text
tools\exact.ps1 -Device <adb address>                       (both cores without the profile)
tools\pgo-train.ps1 -Device <adb address>
tools\exact.ps1 -Device <adb address> -BasePgo off -TreePgo use
```

`pgo-train.ps1` builds the core that records a profile (`-DKAIROX86_PGO_GENERATE=ON`), runs it
through the training machines' exactness-standard frames on the device, merges the raw profiles and
writes this folder with `shared/tools/pgo_freeze.py`. The text is sparse: functions that never ran
are left out, and LLVM optimizes them as it would without a profile. `tools/exact.ps1` builds
without the profile by default, since a change under test makes the recorded one stale.

## Training and evaluation

Training: the standard's `xt`, `486`, `win98-486` and `win98-pentium` machines. `v20`, `at`, `386sx`
and `pentium` are held out, so the evaluation includes machines the profile has never seen.

RG DS, `tools/exact.ps1 -BasePgo off -TreePgo use` from the same source (frames a second, the core
without the profile against the core with it; every machine's pictures, sound and end state exact):

| Machine | Without | With | |
| --- | --- | --- | --- |
| xt (trained) | 86.79 | 103.44 | +19.2% |
| 486 (trained) | 63.25 | 73.27 | +15.8% |
| win98-486 (trained) | 44.69 | 48.66 | +8.9% |
| win98-pentium (trained) | 18.74 | 21.09 | +12.5% |
| v20 (held out) | 64.95 | 72.96 | +12.3% |
| at (held out) | 81.84 | 83.64 | +2.2% |
| 386sx (held out) | 71.81 | 73.71 | +2.6% |
| pentium (held out) | 24.26 | 29.70 | +22.4% |

With the profile, the 486DX2-66 runs the standard's FreeDOS floppy boot faster than the real machine
(73.3 frames a second against its 71.4).
