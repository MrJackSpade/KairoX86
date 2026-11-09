# The core's speed and accuracy record

[← KairoX86](../README.md)

Every change to the core that touches the guest's path is exact or it does not go in. The standard is KairoX86's own (`tools/exact.ps1`, [development](development.md#the-core)): the core of the base revision and the changed core run the same machines on the RG DS (or the PC, `-Local`, for a change that is not about the device's speed or its ARM64 code), and every frame's picture and sound hash and the guest's state at the end (registers, tsc and all RAM) must match; a change to the recompiler must also match its own run with block linking off (`-Unlinked`).

The record below began in the Kairo9X proof of concept, whose speed fixes are the `kairo9x-*` patch groups of this core ([source import](source-import.md)). Those entries were measured with that work's harness: Windows 98 booting from the reference disks now kept for KairoX86's standard (the `win98-486` and `win98-pentium` machines), a fingerprint of every register and all RAM at a fixed emulated time, gated against the same binary with block linking off. Their file names (`86Box.*` builds) and fingerprints are that harness's.

Status: `open` · `fixed` · `rejected` (not exact, or no gain) · `measured` · `noted`

## 486DX2-66 target (ASUS PVI-486AP4, 32MB, S3 Trio64V2, SB16) — RG DS
The standard's `win98-486` machine (its reference disk was then in that harness's own folder). 100% real time = wall ≤ emulated.

| Build | 25 s emulated from power-on | Speed | Fingerprint |
|---|---|---|---|
| S3 fix only (`86Box.det`) | 35.0–35.5 s | ~71% | `8572dd37782d` |
| + #2b hot section + prefetch (`86Box.pf`) | 33.5 s | ~75% | `8572dd37782d` |

**60 s window** (power-on → Win98 desktop + Welcome; the Windows part is the real target, ~45% before #12):

| Build | 60 s emulated | Speed | Fingerprint |
|---|---|---|---|
| `86Box.pf` (#2b + prefetch) | 112.6 s | 53% | `e0be74fb289b` |
| + #12 lazy automation frame copy (`86Box.lf`) | 108.4 s | 55% | `e0be74fb289b` |

486 Windows-phase profile (RG DS): link routine 16.7%, C dispatch 10.1%, memory stubs 7% + soft-MMU 5.3%,
video 8.4% (splash = generic VGA renderer), recompile 7.6%, interp helpers/flags 5.6%, libc 5%, sound 3.8%,
timers 2.7%, translated guest code only 2.5%.

| + #14 reused fix + #15 in-routine slice crossing (`86Box.sl3`) | 106.0 s | 56.6% | `e0be74fb289b` |
| + #17 in-routine timers (`86Box.tm`) | 103.8 s | 57.8% | `e0be74fb289b` |
| + #18 in-routine page walk (`86Box.pw`) | 102.2 s | 58.7% | `e0be74fb289b` |

Rows above ran on the inexact guest path (#19). On the true (no-link) path:

| Build | 60 s emulated | Steady 15 s | Fingerprints |
|---|---|---|---|
| no link (`cpu_dyn_block_link=0`) | 111.4 s | 39.3 s | `747e90412537` / `33647c1ad272` |
| #13–#20 (`86Box.wayc`) | 104.7 s | 39.6 s | same — exact |
| + #25 PGO (`86Box.pgu`) | 94.5 s (63.5%) | 34.2 s (43.8%) | same — exact |
| + #28 hash/mem_exec invalidate-on-change (`86Box.hm`) | 93.7 s (64.0%) | 34.2 s (43.9%) | same — exact |
| + #32 unlink on block change (`86Box.ul`) | 89.8 s (66.8%) | 32.3 s (46.5%) | same — exact |
| + #33 one-cache-line slots (`86Box.sl1`) | 89.5 s (67.0%) | 30.7 s (48.9%) | same — exact |
| + #34 unbounded link registry (`86Box.li`) | 86.4 s (69.5%) | 29.1 s (51.5%) | same — exact |
| + #35 four slot ways (`86Box.w4`) | 84.5 s (71.0%) | 27.8 s (53.9%) | same — exact |
| + #36 PGO retrain (`86Box.rd`; #37 withdrawn) | 85.0 s (70.6%) | 28.1 s (53.5%) | same — exact |
| + #39 threaded OPL synthesis (`86Box.opl`) | 82.5 s (72.8%) | 27.5 s (54.6%) | same — exact |
| + #40 flags, #41 SB16 mixing thread + timer tail (`86Box.sm`) | 80.7 s (74.4%) | 27.2 s (55.1%) | same — exact |
| + #42 8bpp lines on a drawing thread (`86Box.av`) | 79.7 s (75.3%) | 26.6 s (56.4%) | same — exact |
| + #43 misaligned word reads, byte/word tracked stores in stubs (`86Box.ts`) | 78.8 s (76.2%) | 26.6 s (56.4%) | same — exact |
| + #45 pc/oldpc store peephole (`86Box.stp`) | 77.7 s (77.2%) | 25.8 s (58.2%) | same — exact |
| + #46 routine-side abort exits (`86Box.sab`) | 76.6 s (78.3%) | 24.8 s (60.4%) | same — exact |
| + #47 pool next to the program: BL / ADRP (`86Box.near`) | 75.4 s (79.5%) | 24.9 s (60.2%) | same — exact |
| + #48 eaaddr kept in its register across memory accesses (`86Box.ea`) | 74.7 s (80.3%) | 24.7 s (60.7%) | same — exact |

**Steady state (idle desktop after boot, 15 s after a 60 s warm-up, `3e0b7381a5e8`): `86Box.sl3` 38.73 s (38.7%), `86Box.tm` 37.29 s (40.2%), `86Box.pw` 35.84 s (41.9%).** Guest is not idle: 87% of PC
samples are ring-0 VMM/VxD code (CS 0028, C000xxxx), spread across many addresses (interrupt servicing,
ring transitions). Profile: link routine 20.3%, translated guest code 17.7%, soft-MMU C 13.1% + memory stubs
8.4%, C dispatch 10.8%, pmode/int/flag helpers 7.9%, video 5.5%, sound 4.4%, timers 3.0%.

### Verdict on the 486DX2-66 @ 100% goal (2026-10-30, final)
Not reachable by tuning 86Box's existing CPU core. Measured on the true guest path (gated against the no-link C
loop), best exact build `86Box.wayc`: **boot window ~57%, idle desktop ~38%** (15 s emulated = 39.4–39.6 s wall).
At the idle desktop the guest is busy (ring-0 VMM/VxD work), and link misses are no longer a factor (C dispatch
fell from ~570 to ~115 per emulated ms after #18–#20).

Idle-desktop profile (`wayc`): link-routine hit path 24.8% (of which ~16 points are cache-miss stalls on the slot
and the target block's `link_gen`/hash/dirty entries), translated guest code 16.2%, memory stubs 9.4%, C memory
access 7.3%, CPU helpers (pmode/int/flags) 7.2%, soft-MMU 6.4% (`mmutranslatereal` 3.3%), video 5.5%, sound/DMA
4.0%, timers 2.8%, dispatch/codegen 2.8%.

100% needs a 2.6× cut (15 s emulated in ≤ 15 s wall). Measured bounds, not estimates:
- Video and sound off the emulation thread can save at most what they cost there. Measured with builds that skip
  the work outright (guest state unchanged, so doing it elsewhere is exact): no scanline rendering 39.5 → 37.4 s
  (−5.3%), no sound synthesis → 38.2 s (−3.3%). Both together ≈ 36.2 s ≈ 41%.
- Executing guest instructions alone is over budget: translated code 16.2% + memory stubs 9.4% + C memory access
  7.3% + CPU helpers 7.2% + soft-MMU 6.4% = 46.5% of 39.5 s = **18.4 s per 15 emulated s**. Even with block
  transitions (link routine, dispatch), video, sound and timers all free, this core runs the 486 at ~80% at
  best — and those cannot be free.
- Link routine: #22 (slot prefetch) gained nothing; its cost is mostly misses on per-transition metadata the
  design has to re-validate.

- PGO (#25) is now in: 39.6 → 34.2 s at the idle desktop (43.8%). With the video and sound ceilings on top,
  ≈ 31.5 s ≈ 48%. PGO only speeds up the C side; the JIT-emitted share (translated code + stubs, 25.6% of the
  pre-PGO time ≈ 10.1 s) is untouched, so guest instruction execution alone still costs ≈ 16–17 s per 15 s.

- **Measured floor (PGO build `86Box.pgu`, idle-desktop profile, 34.23 s per 15 emulated s):** translated code
  16.0% + memory stubs 10.8% + C memory access 9.4% + CPU helpers/other C 8.4% + soft-MMU 4.6% = 49.2% =
  **16.85 s**. With everything else at zero — link routine (28.7%), video 5.0%, sound 3.9%, timers 2.5%, dispatch
  2.4% — this core would still need 16.85 s per 15 s: **≤ 89% real time, as an absolute upper bound**. Realistic
  bounds on those (measured video/sound ceilings, link routine already trimmed) leave it near 50%.

So 100% is out of reach for this core, not just unreached: its guest-instruction path alone exceeds the budget.
The work itself does not rule it out (#31): an exact core spending near-minimal time per event would need
≈ 0.15 s per emulated second. 86Box spends 2.28 s, almost all in cache misses. A replacement core built around
cache footprint (dense code, transition checks against hot globals only, compact per-block metadata) is the
route to 66 MHz.
hardware: direct block chaining with invalidate-on-change, guest memory through the host MMU (fastmem), register
allocation across blocks, interrupt/segment fast paths, and video/sound rendering off the emulation thread.

### Roadmap to 100% (measured on `86Box.rd`, 28.05 s per 15 emulated s at the idle desktop)
| Component | Now | Route | Saves |
|---|---|---|---|
| Link routine 22.7% | 6.4 s (~117 ns per transition: ~115 hit-path instructions + one slot-line miss) | Direct chaining with a single "attention" word kept by every setter (reset, flush, init, new_ne, interpreter overrides, DR, NMI, abrt/SMI, PIC/APIC pending, TF), target state invalidated on change (#28/#32 pattern), ~20 ns per transition | ~5.3 s |
| Video 6.2% + sound 4.7% | 3.1 s | Off the emulation thread; ceilings measured exact (#23/#24); EMU8K stays (guest-readable voice state) | ~2.6 s |
| Translated 17.9% + stubs 11.4% + C memory 9.9% | 11.0 s | Code generator built for density: inline soft-TLB fast path without growing blocks (#26 failed on size), better register use; must keep 86Box's TLB fill cycles and misaligned charges | needs ~5 s |
| Helpers 8.3%, soft-MMU 5.4%, timers 2.5%, dispatch 1.4%, other | ~7.5 s | Mostly the guest-visible model (#27, #30); small trims only | ~0.5 s |

All three big items are required together; none alone reaches 15 s.

Install notes: Award 4.51G BIOS needs IDE HDD AUTO DETECTION → LBA (128-head translation); no INT13
extensions, so the FAT32 partition must be type 0x0B (CHS), not 0x0C.

## Findings

| # | Area | Finding | Impact (Pentium 233 profile) | Status |
|---|------|---------|------------------------------|--------|
| 1 | Video / accuracy | S3 accelerator FIFO thread leaked host timing to the guest (status ports, VRAM access, display render, FIFO-empty IRQ raised from host thread). Stock 86Box gives a different guest state every run. Fixed: all guest-visible FIFO state settled on the emulation thread; FIFO-empty IRQ from an emulated-time timer. | accuracy bug; ~2% cost | fixed |
| 2 | JIT | Block-link routine runs on every block transition: ~110 instrs, ~40 loads (many double: literal-pool pointer then value). Already fills its 1000-byte allocator block. | 23.9% of all time, more than translated guest code (16.2%) | open |
| 2a | JIT | Estimate: ~13K block transitions per emulated ms, only ~660 of them misses → the link **hit path** carries most of #2's 24%. Hit path ideas: hot globals in one struct off a single base (kills the literal-pool double loads), pack the "anything pending" flags so 1–2 wide loads test them all, stop recomputing ES-flat every transition. | biggest single lever | open |
| 2b | JIT | Link routine globals moved into one ELF section `k9xhot` (`include/86box/k9x_hot.h`); routine loads each with one base-relative LDR/STR off X16 instead of literal-pool pointer + value. Also fixed upstream bug: `cpu_dr_armed` was loaded but its OR result discarded, so armed debug breakpoints never forced a miss. | Pentium gate: 114s → 108s (−5.3%), state identical | fixed |
| 3 | JIT | Link misses fall back to the C dispatch loop + re-patch the slot: ~660/emulated ms. Causes: timer due 230, target change 200, 5µs slice end 189, other 38. | `exec386_dynarec` 9% + `codegen_link_patch` 1.9% | open |
| 4 | Timers | Busy timers force block exits: PIT ch1 DRAM refresh 66.8/ms, `svga_poll` 63.2/ms, `music_poll` (OPL per sample) 49.7/ms, `sound_poll` (per sample) 48/ms, KBC polls 20/ms, `pollsb` 6.9/ms. Refresh toggle and per-sample audio can be made lazy/catch-up with identical guest-visible behaviour. | ~165 of the 230 timer misses/ms | open |
| 5 | JIT | Guest memory access goes through shared stubs: rebuilds a 64-bit table address with immediates every call, BL/RET, readlookup2 lookup, abort check after return. | stubs 8.7% | open |
| 6 | MMU | Soft-TLB refill/flush cost (`mmutranslatereal`, `addreadlookup`, `flushmmucache_nopc`). | ~5% | open |
| 7 | Host | A55 runs at IPC 0.39; 31.5M dTLB misses/s. Android kernel has no THP, so 86Box's `madvise(MADV_HUGEPAGE)` does nothing. | stalls everywhere | open |
| 8 | Build | `-mcpu=cortex-a55` + ThinLTO. | 113s → 112s | rejected (no gain) |
| 9 | CPU loop | Whole 1ms quantum instead of 5µs slices. | 115s → 114s, changed guest state | rejected (gate) |
| 10 | Frontend | Headless pacing: sleeping between quanta lets Android down-clock / stall the CPU thread (~200ms stalls). Real app needs ADPF hints + thread priority. Benchmarks run unpaced. | frontend only | open (real app) |
| 12 | Harness | Automation copied every completed frame (1.2 MB) on the emulation thread. Now copied on demand (screenshot / record). A real frontend copies on its display thread. | 486 60 s: 112.6 → 108.4 s (−3.8%) | fixed |
| 13 | JIT | Link-routine prefetch: PRFM the target's link_gen, hash entry, mem_exec entry and dirty mask right after loading the slot. | Pentium: 107 → 106 s (~1%) | fixed |
| 14 | JIT | Upstream bug: link routine set `block->used` but not `block->reused`, so blocks only ever entered through links counted as never-reused SMC strikes (interpret-only cooldown). Routine now sets both, like the C dispatch. | 486/Pentium state unchanged on gate workload | fixed |
| 15 | JIT | Link routine now crosses 5 µs slice boundaries itself (exact C-loop arithmetic: `cycles_main -= cycles_start - cycles; cycles += cyc_period; cycles_start = cycles`), committed only on a full hit; still misses if cycles stays ≤ 0 after one period (C loop adds periods without running anything) or the quantum ends. `cycles_start`/`cyc_period` now k9xhot globals. Two exactness bugs found with the lockstep differ + `K9X_TRACE` (state stored before later checks could miss; multi-period overrun). | 486 60 s: 108.5 → 106.0 s; both gates bit-exact | fixed |
| 16 | JIT | Upstream inconsistency: C dispatch interprets pages in SMC cooldown (`smc_cooldown_until > tsc`); linked transitions never check it. See #19. | — | fixed (#19) |
| 17 | JIT | Link routine runs due timers itself: out-of-line `k9x_link_timer(new_tsc)` (tsc = new; `timer_process()`), then reloads TSC/cycles/CR0+flags, re-checks interpreter/flush, continues with the slice check. A miss after that sets `k9x_post_done` so the C loop skips straight past its own timer step. First build hung the BIOS: X0 (the slots returned to C on a miss) was clobbered by the call, so `codegen_link_patch` wrote through garbage. | 486 steady 38.73 → 37.29 s, 60 s 106.0 → 103.8 s; all gates bit-exact | fixed |
| 18 | JIT | Steady-state miss breakdown: ~310/emulated ms of ~730 misses were `xlat` — the target's code page not in `readlookup2` (code pages only get entries from data reads or a C-side `get_phys` walk, and the 256-entry ring evicts them). `get_phys` has guest-visible effects (A bits, `addreadlookup` charges `cycles -= 9`), so the routine now calls the real `get_phys` out of line (`k9x_link_phys`) at the point `exec386_dynarec_dyn` would, after committing the loop-top stores; a miss after that sets `k9x_post_done = 2` and the C loop re-enters dispatch directly, where `get_phys` hits its one-entry cache. Rare paths moved to a second allocator block (hot path had ~40 bytes left). | 486 steady 37.29 → 35.84 s, 60 s 103.8 → 102.2 s, Pentium 105.3 → 104.3 s; all bit-exact | fixed |
| 19 | Accuracy | Linked 486 runs never matched the C loop (no-link run differs in both windows); Pentium did. Cause: #16 — links kept entering compiled blocks on pages the C loop interprets during SMC cooldown. Fixed by cutting every link to blocks starting on a page when its cooldown arms (`link_page_blocks_changed`); no slot is refilled during cooldown since the C loop only patches from the compiled path. | linked 486 now bit-exact with no-link | fixed |
| 20 | JIT | Two slot ways per exit (`CODEGEN_LINK_WAYS`): on an exit_pc/cs mismatch the routine tries the second way (out of line); patch keeps an existing way for the target or moves way 0 to way 1. Retargets were ~172/emulated ms (returns alternating callers). | gated with #19; see table | fixed |
| 21 | Accuracy | `-fprofile-generate` build gave a different 486 guest state (`f9eb7b855dee`), first divergence 46.16–46.18 s. Only on the inexact pre-#19 path: on the exact build the instrumented binary matches all references (60 s linked/unlinked, steady state), and linked-off traces of both builds agree. Resolved by #19. | — | fixed (#19) |
| 22 | JIT | Prefetch the block's exit slots at block entry (PRFMs patched into the prologue once the exits are known), to overlap the slot miss with the block. Exact, but no gain: 486 steady 39.55 → 39.40 s, 60 s 104.7 → 105.6 s, Pentium 105.1 → 106.4 s. | none | rejected |
| 23 | Video | Ceiling of moving scanline rendering off the emulation thread (`K9X_NO_RENDER` measurement build, render skipped, FIFO sync kept): steady 39.5 → 37.4 s, 60 s 104.7 → 100.0 s; guest state unchanged. | ≤ 5.3% | measured |
| 24 | Sound | Ceiling of moving synthesis off the emulation thread (`K9X_NO_SYNTH`, `get_buffer` calls skipped): steady → 38.2 s, 60 s → 103.7 s; guest state unchanged. | ≤ 3.3% | measured |
| 25 | Build | PGO: `-fprofile-generate` binary trained on the RG DS (boot to desktop + 15 s steady state), `llvm-profdata merge`, rebuilt with `-fprofile-use`. Profile at `poc/pgo/k9x.profdata`. | 486 steady 39.6 → 34.2 s, 60 s 104.7 → 94.5 s, Pentium 105.1 → 96.3 s; all exact | fixed |
| 26 | JIT | Inline RAM fast path for byte/word/dword loads in translated code (readlookup2 lookup, alignment and -1 checks, direct load; stub call only on the slow path), on top of PGO. Exact, but slower: 486 steady 34.74 → 37.29 s, 60 s 94.45 → 100.85 s, Pentium 96.29 → 100.15 s (larger blocks: I-cache misses outweigh the saved call/return). | −7% | rejected |
| 27 | MMU | Soft-MMU floor: `mmutranslatereal` is already two page-table reads plus accessed-bit updates; how often it runs is set by 86Box's emulated TLB (256-entry ring, `cycles -= 9` per fill, flush on CR3), which is guest-visible. Not reducible while exact. | 4.6% (PGO profile), fixed cost | noted |
| 28 | JIT | Link routine no longer loads the target's `codeblock_hash` entry or `_mem_exec` entry (2 cold loads, ~3.4% of samples). Exact by invalidate-on-change: every write that takes a hash entry from a block bumps that block's `link_gen` (`codegen_block_init`, the dispatch tree lookup; deletes already did), and slots record `mem_mapping_gen` (now a k9xhot global, also bumped by wd76c10's direct `_mem_exec` writes), compared instead of `_mem_exec`. | 486 steady 34.23 → 34.16 s, 60 s 94.45 → 93.73 s, Pentium 96.29 → 93.33 s; exact | fixed |
| 29 | JIT | Translated-code profile at the idle desktop (`86Box.hm`) is flat: 16.6% of time over 5,741 sampled addresses on 326 JIT pages (~1.3 MB); top 10 addresses 0.58%, top 200 5.3%, top 1,000 15.1%. The working set is far beyond the A55's 32 KB L1I, so code size costs directly (cf. #26, −7% from larger blocks). A replacement core has to emit denser code, not just fewer dynamic instructions; per-block hand-tuning has nothing to aim at. | — | noted |
| 30 | Model | Block boundaries are guest-visible in 86Box: blocks are recorded while the interpreter runs, every taken branch/JMP/CALL/LOOP calls `CPU_BLOCK_END()`, and timers and interrupts are only serviced at block ends. Longer blocks or traces (following JMP/CALL) would move those points and change guest state, so any core exact to 86Box keeps today's transition count and must do the per-boundary timer/IRQ/event checks at each one; only their cost can shrink (chaining, hot-global checks). | bounds the "new core" option | noted |
| 31 | Model | Event counts at the idle desktop (diag counters at block exits, stub entries and `mmutranslatereal`; lower bounds), per emulated second: ≥ 19.8 M guest instructions, ≥ 3.6 M block transitions, ≥ 14.8 M stub memory accesses, 1.08 M page walks. With the PGO profile (2.28 s wall per emulated s): link routine ≈ 180 ns per transition, translated code ≈ 18 ns (36 cycles) per instruction, stubs ≈ 17 ns per access, walks ≈ 80 ns. Minimal exact costs on the A55 (~5 ns transition, ~2 ns TLB lookup, ~2 ns instruction, ~40 ns walk) total ≈ 0.15 s per emulated s. So an 86Box-exact core is not ruled out by the work itself: 86Box spends 10–35× the minimum per event, almost all of it cache misses (1.3 MB of hot JIT code, #29; cold per-transition metadata, #22/#28). | design target for a new core | noted |
| 32 | JIT | Link routine no longer reads the target block (`link_gen`, a cold miss per transition, 3.6%). Each block keeps a list of the slots linking to it (`link_in`, 8 entries, stale entries reused); `codegen_link_block_changed()` empties those that still link to it; a slot is only filled (or moved to way 1) if it could be registered. Block changes are rare: ~240 per emulated second at the idle desktop. | 486 steady 33.29 → 32.26 s, 60 s 93.73 → 89.80 s, Pentium 93.33 → 91.57 s; exact | fixed |
| 33 | JIT | `codegen_link_slot_t` reordered and 64-byte aligned so every field a hit reads is in its first cache line (cold-path fields — gen, virt, rammask, xlat, mem_exec, hash — in the second); cr0_bits/phys_page now one LDP W. Removes the slot's second-line miss (~3% of samples). | 486 steady 31.42 → 30.66 s (same session), 60 s 89.80 → 89.50 s, Pentium 91.57 → 90.54 s; exact | fixed |
| 34 | JIT | #32's 8-entry per-target registry overflowed on hot targets (refused slots doubled C dispatches: `exec386_dynarec` 2.0 → 4.2%). Replaced by an intrusive doubly-linked list through the slots (`in_next/in_prev/in_nr/in_listed` in the slot's cold half; slot stays 128 bytes): a slot is on its target's list while it links, moved on retarget, way copy and clear. | 486 steady 30.66 → 29.11 s, 60 s 89.50 → 86.36 s; exact | fixed |
| 35 | JIT | Four slot ways per exit (`CODEGEN_LINK_WAYS 4`): the routine checks ways 1–3 out of line; a new target takes the way that already has it, else an empty one, else the ways take turns (`victim` in way 0), so no slot is ever moved. Absorbs exits with 3–4 targets (~86K retargets per emulated second before). | 486 steady 29.12 → 27.83 s, 60 s 86.36 → 84.45 s, Pentium 90.58 → 88.65 s; exact | fixed |
| 36 | Build | PGO retrained on the #35 code (486 boot + steady state): no gain — 486 steady 28.18 → 28.21 s, 60 s 84.45 → 85.19 s, Pentium 88.65 → 91.51 s (486-only training). The retrained profile replaced the first; later builds use it and are compared same-session. | none | noted |
| 37 | Video | Hoisted the per-pixel field reloads in `svga_render_8bpp_highres` — but that body is inside `#if 0`; the live function is a wrapper over the generic `svga_render_indexed_gfx()`. The change did nothing; its recorded 28.52 → 28.05 s was run-to-run noise. Reverted; see #42 for the live renderer. | none | withdrawn |
| 38 | JIT | #22 retried with one-line slots: prefetch only the hit line of each exit's way 0 at block entry (≤ 7 instructions patched into the prologue). Exact, but no gain: 486 steady 28.27 → 29.03 s, 60 s 85.02 → 85.10 s. | none | rejected |
| 39 | Sound | OPL synthesis (ymfm) on its own thread, one buffer behind: the emulation thread's chip takes writes, runs timers and answers reads, and logs writes, timer expiries and clock changes with their sample; at the buffer end (`update()`) the log goes to a second chip copy on the synthesis thread (no-op timer/IRQ interface) and the previously finished buffer is mixed. Register accesses no longer generate on the emulation thread (`catch_up()`). Audio identical, one buffer (~28 ms) later; chips read through `generate()` (midi_opl4) stay single-threaded. | 486 steady 27.95 → 27.47 s, 60 s 85.02 → 82.47 s; exact | fixed |
| 40 | JIT | The seven "nothing pending" flags the link routine reads are defined together (8-byte aligned, `386_common.c`); the routine sorts their offsets at build time and loads aligned adjacent pairs as one X, ORing into the abrt/SMI word; `used`/`reused` set with one STRH. ~7 fewer hit-path instructions. | 486 steady 27.50 → 27.35 s, 60 s 82.47 → 83.07 s, Pentium 91.05 → 89.88 s: within noise; exact | kept (marginal) |
| 41 | Sound/Timers | SB16 output mixing (FIR/IIR filters, volumes; nothing guest-visible) on its own thread, one buffer behind, with its own filter state (filters.h IIRs and the SB16 FIR refactored to per-instance state; the old `(c, i)` forms are wrappers, which also stops the SB16 sharing slot 0 with GUS/PAS16). Timer list keeps a tail: a timer due after all others is appended without the walk (same position the walk finds). | 486 steady 27.13 → 27.20 s (idle: no PCM), 60 s 83.07 → 80.68 s, Pentium 89.88 → 87.72 s; exact | fixed |
| 42 | Video | Live 8bpp renderer is the generic `svga_render_indexed_gfx()`. Diag showed every desktop line takes its `force_old_addr` path, which for packed 8bpp (forcepacked: incbypow2 0, counters 1) with CRTC 17h bits 0/1 set and a dword-aligned memaddr is plain `memaddr & mask`. Exact fast path for that case; the dwords wholly left of hdisp go to a drawing thread (SPSC ring, woken only when it found the ring empty), the rest is drawn in place so the right overscan still overwrites the same pixels; lines the cursors/overlay draw on are drawn in place; drained before blit, recalctimings and close. A first try without the force_old_addr case never ran (no gain). | 486 steady 27.94 → 26.61 s, 60 s 80.68 → 79.65 s, Pentium 87.72 → 86.94 s; exact | fixed |
| 43 | Memory | Diag of the C memory paths at the idle desktop (per wall s, 46% speed): dword reads 170K soft-TLB misses (model, stays), word reads 45K misaligned, word/byte writes 77K/52K to tracked (code) pages, dword writes 63K TLB misses. Word-load stub now serves a misaligned word inside one readlookup2 page itself (`mem_logical_addr`, `high_page`, `timing_misaligned` unless Cyrix-aligned, as `readmemwl()`); the tracked-store fast path (#5) now covers aligned bytes and words (`mem_write_ramb/ramw_page`, data masked to its width). | 486 steady 27.35 → 26.59 s (same session), 60 s 79.65 → 78.78 s, Pentium 86.94 → 86.31 s; exact | fixed |
| 44 | JIT | Ceiling of the ES-flat trim (link routine trusting `cpu_cur_status`'s NOTFLATES instead of recomputing it from ES, `K9X_NO_ES_RECOMPUTE` measurement build, not exact in general): 486 steady 26.47/26.17 s vs 26.53/26.48 s for `86Box.ts`, interleaved. ≤ ~0.7%, within noise; making it exact would need every ES writer audited. | ≤ 0.7% | measured, not done |
| 45 | JIT | Translated-code density. Hot pages (dumped at fixed offsets: block placement is deterministic) showed every faultable instruction storing pc and oldpc as two MOVZ/MOVK/STR triples of the same constant. `codegen_direct_write_32_imm` now reuses W16 when the previous immediate store (nothing emitted since, no jump destination or new block in between) had the same value, and turns STR+STR to adjacent words into one STP: 6 instructions → 3. | 486 steady 27.00 → 25.79 s (same session), 60 s 78.78 → 77.68 s, Pentium 86.31 → 86.44 s; exact | fixed |
| 46 | JIT | Memory-routine aborts: every call site checked X1 after the routine (CBNZ X1 → codegen_exit_rout, plus the NOP of the collapsed branch template). The routines' C paths now branch to codegen_exit_rout themselves when the access aborted (after popping their frame, so it runs on the block's; the block flushed its registers before the ordered access, as for the exit it would have taken); the 12 call-site checks are gone. 2 fewer instructions per guest memory access. | 486 steady 25.96 → 24.84 s (same session), 60 s 77.68 → 76.64 s, Pentium 86.44 → 85.21 s; exact | fixed |
| 47 | JIT | The recompiler's pool (131 MB) was mapped ~60 GB from the program, so every call to a C helper was MOVZ/MOVK×3 + BLR and every global address MOVZ/MOVK×3. On Android/arm64 `plat_mmap` now maps it right after the program (`MAP_FIXED_NOREPLACE`, fatal if taken); `host_arm64_call/jump` use BL/B to anything in range, and `host_arm64_MOVX_IMM` emits ADRP(+ADD) for a value within 4 GiB of the code that would need 3–4 moves. Code never moves once written, so the PC-relative forms are exact. | 486 steady 25.46 → 24.91 s (same session), 60 s 76.64 → 75.43 s, Pentium 85.21 → 82.42 s; exact | fixed |
| 48 | JIT | Hot translated code (`86Box.near` dump): stores into cpu_state are 21% of instructions, ~3.8 per guest memory access — registers written back at every memory access (an ordered uop). The commonest is `eaaddr` (cpu_state+0x30). Nothing behind a memory access reads it (routines, their C paths, an abort's exception delivery; only `fpu_postamble` and interpreted instructions do, behind full barriers), so `codegen_reg_flush_ex(mem_access)` keeps it in its (non-volatile) register; a new version then just replaces it. | 486 steady 25.24 → 24.72 s (same session), 60 s 75.43 → 74.73 s, Pentium 82.42 → 82.20 s; exact | fixed |
| 49 | JIT | Abort pads: at a guest memory access, dirty guest registers and lazy flags stayed in host registers; an out-of-line pad per access (after the block's last exit) stored them, and an aborted access found its pad from its return address (per-allocator-block lists, freed with the memory). Exact — page faults during boot went through the pads — but no gain: 486 steady 24.77 → 24.53 s, 60 s 74.73 → 75.28 s, Pentium 82.20 → 83.98 s (the registers are still written at the next full flush; the pads spread hot code). Reverted. A test for memory uops by opcode range (0x40–0x4f) also took in CMP_IMM_JZ/CMP_JB/CMP_JNBE (exits); replaced by an exact `uop_is_mem_access()`, which #48 now uses (gated: 24.90 s, same as #48). | none | rejected |
| 50 | JIT | `86Box.ea2` profile: link routine 23.5% (hot 18.6%, out-of-line 4.9% — mostly the uncached-page path's readlookup2 load, ~1.8%). Prefetching the target's readlookup2 entry at the routine's start (3 instructions): exact, no gain — 486 steady 24.39 → 24.74 s (same session). Reverted; prefetching keeps failing on this core (#22, #38). | none | rejected |
| 51 | Timers | Timer list replaced by a binary heap of {time, insertion order, timer} (same firing order: by time, the last enabled first among equal times; `timer_target` set at the same points), keys kept in the contiguous heap so ordering never touches the timers. Exact, but no gain: 486 steady 24.57 → 24.99 s (same session). `timer_enable`'s cost is not the list walk. Reverted (source rebuilt byte-identical to `86Box.ea2`). | none | rejected |
| 11 | Frontend | Automation `screenshot` frame can be stale vs guest state (frame delivery host-timed). Fingerprint uses RAM hash instead. | test tooling only | open (low) |

## Candidates from the sibling Kairo projects (git history survey, 2026-10-30)
Measured on the same RG DS in those repos; to try here:
- `sigsetjmp(buf,1)` → `sigsetjmp(buf,0)` at the interpreter's exception boundary (Kairo98 86a5b7f5: core 14.9 → 8.6 ms/frame).
- Symbol binding / hidden visibility so hot globals skip the GOT (KairoDos: `-Bsymbolic-non-weak-functions` +8.84%, hidden `paging` +3.1%, `lflags` +4.17%).
- PGO trained on device, profile checked in (KairoDos +5.06%, Kairo68 +4.3–9.8%).
- Sound synthesis on an ordered worker thread from timestamped register writes, status/timers stay on the emulation thread (KairoDos OPL +14.6% Duke; Kairo98 ymfm bit-exact, 8.8 → 7.4 ms).
- Video rendered on another thread from a VRAM copy (KairoTowns 294f422/bd36c2b); reuse unchanged indexed scanlines (KairoDos a6424f27).
- Exact idle/wait-loop skipping on backward jumps with side-effect tracking (Kairo98 e8bd3c6f/9a8efd81, KairoTowns b0d6174…). Workload-dependent (our idle desktop is spread across VMM code).
- Scheduler: compute counters on read instead of firing events (Kairo68 4d794f6: 28k → 2.7k slices/frame); cache "would the PIC fire".
- Frontend: fixed-grid frame pacing with AAudio-queue-driven slot stretch; thread priority −16 measured no gain; no ADPF anywhere.

## Pentium follow-ups
Revisit when moving to the Pentium-class target. Same authors, same patterns — expect the 486 fixes above to
apply here too, plus:
- Every finding marked `open` above was measured on the Pentium MMX 233 / TX97 config; re-measure on Pentium
  after the 486 work lands.
- P5 cycle model: 86Box's cost is per instruction, not per cycle; Pentium needs ~3.2× from the stock baseline
  (21M emulated cycles/s on RG DS) vs ~1.5× for the 486DX2-66.
- Likely needs a new CPU-core structure rather than tuning: direct block chaining with invalidate-on-change,
  fastmem (host-MMU mapped guest memory), register allocation across blocks, inline flags.
- Baseline numbers for the Pentium config: 25 emulated s of Win98 boot = 115s wall on RG DS
  (fingerprint `182d887b544e` with fix #1).

## KairoX86's own fixes

Measured with `game_profile` on the RG DS; each exact against the core without it (frame and sound hashes, and since `tools/exact.ps1` the state too).

| Ticket | Area | Change | Result | Status |
|---|---|---|---|---|
| KairoX86#200 | Start | The recompiler's free list hands out blocks lazily, in the same order (`kairox86-lazy-blocks`); the CPU reset skips refilling a page table already as it would leave it (`kairox86-pages-as-reset`). | A start's `pc_init_modules` 130-170 ms → 24-38 ms | fixed |
| KairoX86#199 | 8088 | A halted 8088's cycles before the next timer is due go by at once (`kairox86-halt-skip`). | XT loading 52 → 79 frames/s (guest 62.5) | fixed |
| KairoX86#199 | PIT | The classic PIT's timer goes straight to the next edge a counter does more than count down on; the edges between are counted down at once, or up to `tsc` before any access (`kairox86-lazy-pit`). | XT 42 → 52 frames/s; AT 55.6 → 81.4, 386SX 49.8 → 71.4 with the halt skip | fixed |
| KairoX86#199 | Video | `video_process_8_monitor` and `cga_render` read their line once, not after every pixel (no strict aliasing) (`kairox86-video-hoist`). | ~1.5% on the XT | fixed |
| KairoX86#205 | V20/V30 | The same halt skip for the NEC core, by whole halted passes (`kairox86-halt-skip-vx0`). The 286/386 interpreter and the recompiler spend no measurable time halted. | V20 XT 47.2 → 66.0 frames/s (guest 62.5) | fixed |
| KairoX86#206 | Floppy | `fdd_type_invert_densel` searched the machine's name three times for every bit; worked out once per machine (`kairox86-densel-once`). | 486 floppy load 54.1 → 61.8 frames/s (guest 71.4) | fixed |
| KairoX86#123 | Build | The arm64 core is built with a profile of the RG DS running the standard's xt, 486 and both Windows 98 machines (`core/pgo`, `tools/pgo-train.ps1`). `tools/exact.ps1 -BasePgo off -TreePgo use`, all eight exact. | Frames/s without → with: xt 86.8 → 103.4, 486 63.3 → 73.3 (guest 71.4), win98-486 44.7 → 48.7, win98-pentium 18.7 → 21.1; held out: v20 65.0 → 73.0, at 81.8 → 83.6, 386sx 71.8 → 73.7, pentium 24.3 → 29.7 | fixed |
| KairoX86#214 | Video | 320-wide packed 8bpp (mode 13h, and DOOM's unchained form) took the generic renderer's slow loop on the emulation thread, 10% of DOOM's time: the #42 fast path and drawing thread took only lines of a dot per pixel, and now take lowres lines too, each pixel twice across. The drawing thread was then woken for every line (a futex wake per line, ~4% of the emulation thread), now once 32 lines wait; a job holds its line and palette (KairoX86#38), and every line is still drawn before the frame is shown (`kairox86-lowres-8bpp`). `tools/exact.ps1`: all eight exact; DOOM's demo, 5,501 frame hashes, exact. | DOOM demo on the doom486 machine (PGO off): 16.66 → 15.15 ms a frame, 60.0 → 66.0 frames/s (guest 71.43) | fixed |
| KairoX86#214 | Sound | Nuked OPL3 (86Box's default FM driver; #39 threaded only ymfm) generated on the emulation thread, catching up at every register access. Its synthesis is now on a thread of its own, exact and without delay: the emulation thread queues each write with its sample position, and sound.c's per-sample poll tells the thread the present every 128 samples (no new timer). The thread generates up to each position before applying what is there. A read takes no catch-up (status and timers are the driver's). An address write's bank reads newm from a shadow once every 0x105 write is applied, and from the chip, after waiting for the thread to reach the present, while one is still in its write buffer. `update()` waits for the buffer's end (`kairox86-opl3-thread`). `tools/exact.ps1`: all eight exact; DOOM's demo (OPL3 music), 5,501 frame and sound hashes, exact; `--runs 2` match. | DOOM demo (PGO off): 15.21 → 14.55 ms a frame, 65.8 → 68.7 frames/s (guest 71.43) | fixed |
| KairoX86#214 | Video | The planar byte write a card that decodes its own addresses makes (the S3's in unchained 256-colour modes) in its plainest form (write mode 0, every bit taken, no logic operation, no set/reset, plain planar addressing) skips the general path's clz/ctz plane bounds and per-plane flag tests, with the same steps in the same order (`kairox86-plain-planar-write`). `tools/exact.ps1`: all eight exact; DOOM's demo, 5,501 hashes, exact. | DOOM demo (PGO off): 14.53 → 14.26 ms a frame, 68.8 → 70.1 frames/s (guest 71.43) | fixed |
| KairoX86#405 | Video | The MediaGX's display (`gxm_render_line`, `gxm_poll`'s 16% of a FreeDOS boot's samples) read every pixel through `gxm_gmem` and chose its mode per pixel. A line in one span of the graphics memory (no wrap, every access inside it) is now read straight from that span in a loop for its mode (planar, 16 bpp, 8 bpp; chain 4 keeps the loop): the same pixels. ECS P5GX-M, MediaGX 233, FreeDOS boot, 3000 frames, three interleaved rounds | 48.38 → 53.30 frames/s (of 71.43), +10.2%; picture hashes identical on core/test/gpu's gxm.c (1277 frames: 5-6-5, 5-5-5, cursor, overlay) and the FreeDOS boot (3001 frames: 640×350, 640×480, 720×400) | fixed |
| KairoX86#406 | App | The frame host copied every picture a second time on the emulation worker (publish, 0.3-0.55 ms a frame). The core now draws each picture into the spare of three buffers the host rotates (kairo_x86.h `picture_target`), and publish swaps it in | dos486 FreeDOS prompt: publish 0.55 → 0.025 ms, 51.77-52.26 → 54.01-54.23 frames/s (+4%); exact on all nine machines | fixed |
| KairoX86#381 | CPU | REP STOSD in the interpreter (`opREP_STOSL`, 14-20% of emulation in the P6 Windows 98 boot: Windows clearing its 1 GB) stored element by element through the write checks. A run of dwords on a page the write lookup maps straight (writememl's plain store), the same segment checks passed, is stored in one loop with the same registers, cycles, writes and end point | win98-voodoo3 (Pentium Pro, 1 GB): 29.01 → 30.39 frames/s (+4.8%), two interleaved rounds; win98-pentium (64 MB): within noise; exact on all nine machines | fixed |
| KairoX86#129 | Idle | A Pentium MMX 233 at its BIOS's F1 prompt runs 23-24 frames/s against 66.67, polling the keyboard from ROM in the interpreter: a wait-loop skip would apply. | — | open |
