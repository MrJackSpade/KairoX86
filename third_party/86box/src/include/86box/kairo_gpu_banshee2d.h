/*
 * The 3dfx Voodoo Banshee and Voodoo3's 2D engine on the GPU (KairoX86#278): the operation record of its batch
 * (kairo_gpu_seg.h), a pixel's stream words, and the batch's opening (core/kairo/gpu_banshee2d.c,
 * core/kairo/shaders/banshee2d.comp).
 *
 * The record: the four raster operations (rops[0] to rops[3], a byte each, rops[n] in bits 8n+7:8n); the destination
 * key's format (B2_KEY_8, B2_KEY_16, B2_KEY_32; 0 where the destination key is off) and its range; the bytes a pixel
 * takes (1 to 4). A pixel's words: its source, its pattern, B2K_SRC_KEY where the source is in the source key.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_BANSHEE2D_H
#define KAIRO_GPU_BANSHEE2D_H

#include <stdint.h>

enum { B2_ROPS = 0, B2_DKEY = 1, B2_DKEY_MIN = 2, B2_DKEY_MAX = 3, B2_BYTES = 4, B2_WORDS = 8 };
enum { B2_KEY_8 = 1, B2_KEY_16 = 2, B2_KEY_32 = 3 };
#define B2_PIXEL_WORDS 3
#define B2K_SRC_KEY    1u

struct kairo_seg;
struct kairo_seg *kairo_banshee2d_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp);

#endif
