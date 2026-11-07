/*
 * The S3 86C801 to Trio64's graphics engine on the GPU (KairoX86#271): the operation record of its batch
 * (kairo_gpu_seg.h), a pixel's stream words, and the batch's opening (core/kairo/gpu_s3.c, core/kairo/shaders/s3.comp).
 *
 * A pixel's words: its kind (the mix code in bits 7:0, S3K_ROP3 for a ternary raster operation with the pattern,
 * S3K_NIBBLE and the shift in bits 19:17 for a 4 bpp pixel), its source and its pattern.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_S3_H
#define KAIRO_GPU_S3_H

#include <stdint.h>

enum { S3_WRT_MASK = 0, S3_BYTES = 1, S3_WORDS = 4 };
#define S3_PIXEL_WORDS 3
#define S3K_ROP3       0x100u
#define S3K_NIBBLE     0x10000u

struct kairo_seg;
struct kairo_seg *kairo_s3_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp);

#endif
