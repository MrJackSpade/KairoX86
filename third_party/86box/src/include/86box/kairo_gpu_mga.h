/*
 * The Matrox Millennium and Mystique's drawing engine on the GPU (KairoX86#264): the operation record of its batch
 * (kairo_gpu_seg.h), a pixel's stream words, and the batch's opening (core/kairo/gpu_mga.c,
 * core/kairo/shaders/mga.comp).
 *
 * The record: DWGCTL's boolean operation; the bytes a pixel takes (1 to 4). A pixel's words: its kind (MGK_STORE, the
 * value stored; MGK_BOP, the value put through the boolean operation with the destination; MGK_BOP_BGR, the same with
 * the destination's blue and red swapped first) and its value.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_MGA_H
#define KAIRO_GPU_MGA_H

#include <stdint.h>

enum { MG_BOP = 0, MG_BYTES = 1, MG_WORDS = 4 };
#define MG_PIXEL_WORDS 2
#define MGK_STORE      0u
#define MGK_BOP        1u
#define MGK_BOP_BGR    2u /* MGK_BOP with the destination's blue and red swapped first (32-bit pixels, ILOAD BU32BGR) */

struct kairo_seg;
struct kairo_seg *kairo_mga_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp);

#endif
