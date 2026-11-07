/*
 * The IBM XGA's drawing engine on the GPU (KairoX86#280): the operation record of its batch (kairo_gpu_seg.h), a
 * pixel's stream words, and the batch's opening (core/kairo/gpu_xga.c, core/kairo/shaders/xga.comp).
 *
 * A pixel's words: its shift in its byte (1, 2 and 4-bit maps), its source (the value, 32 bits, the CPU's read) and its
 * mix (0 background, 1 foreground).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_XGA_H
#define KAIRO_GPU_XGA_H

#include <stdint.h>

enum { XG_FRGD_MIX = 0, XG_BKGD_MIX = 1, XG_CC_COND = 2, XG_CC = 3, XG_PLANE_MASK = 4, XG_DST_BITS = 5, XG_WORDS = 8 };
#define XG_PIXEL_WORDS 3

struct kairo_seg;
struct kairo_seg *kairo_xga_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp);

#endif
