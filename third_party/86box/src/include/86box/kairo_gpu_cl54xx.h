/*
 * The Cirrus Logic GD54xx BitBLT engine on the GPU (KairoX86#250): the operation record of its batch (kairo_gpu_seg.h),
 * a byte's stream words, and the batch's opening (core/kairo/gpu_cl54xx.c, core/kairo/shaders/cl54xx.comp).
 *
 * A byte's words: its source, its mask and its bytes.
 * - Source: CL_IMM and the byte; or CL_CE and the bit address of a colour-expansion bit in video memory (the fg or bg
 *   byte); or the address of the byte.
 * - Mask: CL_IMM and the bit; or CL_CE, the source's colour-expansion bit; with CL_TCOMP, cleared unless the source
 *   matches the compare byte outside the compare mask (gd54xx_transparent_comp); with CL_NCOMP, cleared where the
 *   source is not the compare byte (gd54xx_normal_blit's); and CL_SKIP, a pixel the left skip leaves.
 * - Bytes: the fg byte (7:0), the bg byte (15:8), the compare byte (23:16), the compare mask (31:24).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_CL54XX_H
#define KAIRO_GPU_CL54XX_H

#include <stdint.h>

enum { CL_ROP = 0, CL_FLAGS = 1, CL_WORDS = 4 };
/* CL_FLAGS */
#define CLF_RULE_NORMAL 0x01u /* gd54xx_normal_blit's write rule, else gd54xx_blit's */
#define CLF_TRANSP      0x02u /* gd54xx_blit's is_transp; for the normal rule, transparent comparison on */
#define CLF_BGONLY      0x04u
#define CLF_COLOREXP    0x08u
#define CLF_EXPINV      0x10u

#define CL_BYTE_WORDS 3
#define CL_IMM        0x80000000u
#define CL_CE         0x40000000u
#define CL_TCOMP      0x20000000u
#define CL_NCOMP      0x10000000u
#define CL_SKIP       0x08000000u
#define CL_ADDR_MASK  0x07ffffffu /* an address or a bit address */

struct kairo_seg;
struct kairo_seg *kairo_cl54xx_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp);

#endif
