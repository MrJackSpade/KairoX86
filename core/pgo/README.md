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

Training: the standard's `xt`, `486`, `win98-486` and `win98-pentium` machines, and DOOM's demo on
the owner's `doom486` machine (PVI-486AP4, DX2-66, S3, SB16; `C:` and `DOOM` typed at FreeDOS's
prompt, 3,500 frames of title and demo then 2,500 more), which the repository cannot hold:
`tools\pgo-train.ps1 -Device <adb address> -Game <doom486 folder>`
([#378](https://github.com/MrJackSpade/KairoX86/issues/378)). `v20`, `at`, `386sx`, `pentium` and
`win98-voodoo3` are held out, so the evaluation includes machines the profile has never seen.

RG DS, the retrain of #378 (frames a second, interleaved `tools/ab.ps1` rounds, medians; every run's
end state alike). Against the profile it replaced, trained on the standard machines alone before
#376, #408 and #410 changed the core:

| Workload | Before | After | |
| --- | --- | --- | --- |
| DOOM's demo (trained) | 69.98 | 73.37 | +4.8% |
| xt (trained) | 102.18 | 104.33 | +2.1% |
| 486 (trained) | 74.01 | 74.92 | +1.2% |
| win98-pentium (trained) | 52.52 | 53.94 | +2.7% |
| v20 (held out) | 72.39 | 72.39 | 0.0% |
| pentium (held out) | 33.43 | 34.28 | +2.5% |

DOOM in the training set, against the same retrain without it: DOOM +1.4%, pentium +3.3%,
win98-pentium +4.5%, win98-voodoo3 about +1%, xt +0.7%, at +0.5%, 386sx +0.3%, win98-486 −0.2%,
v20 −0.7%, 486 −1.4%. With it, DOOM's demo and the 486's floppy boot both run faster than the real
DX2-66 (71.4 frames a second).

As first recorded (#123), `tools/exact.ps1 -BasePgo off -TreePgo use` from the same source (frames a second, the core
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
