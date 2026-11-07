/*
 * The IBM 8514/A's drawing engine and the ATI Mach8 and Mach32's on the GPU (KairoX86#238): the operation record of
 * their batch (kairo_gpu_seg.h), a pixel's stream words, and the batch's opening (core/kairo/gpu_ibm8514.c,
 * core/kairo/shaders/ibm8514.comp).
 *
 * The record: the write mask; the compare colour; the compare (the 8514/A's PIX_CNTL mode, or the Mach engine's mode 1
 * to 8, in bits 7:0, DEST_CMP_FN in bits 15:8); I8F_W16 for 16-bit pixels and I8F_MACH for the Mach engine's mixes and
 * compare; the bytes a pixel takes.
 *
 * A pixel's words: its kind (the mix code in bits 4:0, I8K_CMP where the compare decides whether it is drawn) and its
 * source.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_IBM8514_H
#define KAIRO_GPU_IBM8514_H

#include <stdint.h>

enum { I8_WRT_MASK = 0, I8_CMP = 1, I8_MODE = 2, I8_FLAGS = 3, I8_BYTES = 4, I8_WORDS = 8 };
#define I8_PIXEL_WORDS 2
#define I8K_CMP        0x100u
#define I8F_W16        1u
#define I8F_MACH       2u

struct kairo_seg;
struct kairo_seg *kairo_ibm8514_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp);

#endif
