/*
 * The Chips & Technologies B69000 BitBLT engine on the GPU (KairoX86#249): the operation record of its batch
 * (kairo_gpu_seg.h), a pixel's stream words, and the batch's opening (core/kairo/gpu_chips69000.c,
 * core/kairo/shaders/chips69000.comp).
 *
 * A pixel's words: its source (CH_IMM and the pixel, or the address of its first byte) and its pattern (CH_IMM and
 * the pixel; CH_MONO and the bit address of its mono pattern bit; or the address of its first byte).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_CHIPS69000_H
#define KAIRO_GPU_CHIPS69000_H

#include <stdint.h>

enum { CH_ROP = 0, CH_CTRL = 1, CH_KEY = 2, CH_PAT_FG = 3, CH_PAT_BG = 4, CH_BYTES = 5, CH_WORDS = 8 };

#define CH_PIXEL_WORDS 2
#define CH_IMM         0x80000000u
#define CH_MONO        0x40000000u
#define CH_ADDR_MASK   0x0fffffffu

struct kairo_seg;
struct kairo_seg *kairo_chips69000_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp);

#endif
