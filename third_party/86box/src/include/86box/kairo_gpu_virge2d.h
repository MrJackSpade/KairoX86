/*
 * The S3 ViRGE and Trio3D's 2D engine on the GPU (KairoX86#272): the operation record of its batch (kairo_gpu_seg.h),
 * a pixel's stream words, and the batch's opening (core/kairo/gpu_virge2d.c, core/kairo/shaders/virge2d.comp).
 *
 * The record: the ternary raster operation; the bytes a pixel takes (1 to 3). A pixel's words: its source and its
 * pattern.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_VIRGE2D_H
#define KAIRO_GPU_VIRGE2D_H

#include <stdint.h>

enum { V2_ROP = 0, V2_BYTES = 1, V2_WORDS = 4 };
#define V2_PIXEL_WORDS 2

struct kairo_seg;
struct kairo_seg *kairo_virge2d_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp);

#endif
