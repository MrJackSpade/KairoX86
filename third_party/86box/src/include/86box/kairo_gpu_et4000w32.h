/*
 * The Tseng Labs ET4000/W32's accelerator on the GPU (KairoX86#254): the operation record of its batch
 * (kairo_gpu_seg.h), as words, and the batch's opening (core/kairo/gpu_et4000w32.c, core/kairo/shaders/et4000w32.comp).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_ET4000W32_H
#define KAIRO_GPU_ET4000W32_H

#include <stdint.h>

enum { ET_ROP_FG = 0, ET_ROP_BG = 1, ET_WORDS = 4 };
/* A byte's stream words: the pattern address, the source and the mix */
#define ET_BYTE_WORDS 3
#define ET_IMMEDIATE  0x80000000u /* a source or mix word holding the host's byte or bit */

struct kairo_seg;
struct kairo_seg *kairo_et4000w32_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp);

#endif
