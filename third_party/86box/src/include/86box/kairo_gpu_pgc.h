/*
 * The IBM Professional Graphics Controller's drawing processor on the GPU (KairoX86#268), and with it the Vermont
 * Microsystems ImageManager 1024's (#261), which draws through the PGC's pixel functions: a pixel's stream word, and
 * the batch's opening (core/kairo/gpu_pgc.c, core/kairo/shaders/pgc.comp). The walks (lines, fills, polygons, text,
 * images) stay the CPU's; each pixel they draw is recorded (vid_pgc.c pgc_plot, pgc_write_pixel) with what it does.
 *
 * A pixel's word: bits 0-7 the value, bits 8-9 the operation (below). The batch's operation record is one word,
 * unused: every pixel carries its own.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_PGC_H
#define KAIRO_GPU_PGC_H

#include <stdint.h>

enum { PGC_K_SET = 0, PGC_K_INVERT = 1, PGC_K_XOR = 2, PGC_K_AND = 3 };
#define PGC_K_WORDS 1

struct kairo_seg;
struct kairo_seg *kairo_pgc_open(uint8_t *vram, uint32_t vram_mask);

#endif
