/*
 * The Cyrix MediaGX's BitBLT and vector engine on the GPU (KairoX86#315): the operation record of its batch
 * (kairo_gpu_seg.h), a pixel's stream words, and the batch's opening (core/kairo/gpu_gxm.c, core/kairo/shaders/gxm.comp).
 * vid_cyrix_gxm.c's walks (gxm_gp_blt, gxm_gp_vector) stay the CPU's and record each pixel they draw as a run of
 * pixels (kairo_seg_run), its pattern decided and its source read on the CPU wherever that needs no frame buffer.
 *
 * A pixel's words: its pattern value, and its source: the value (GXW_IMM), or the frame buffer offset of the pixel it is.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_GXM_H
#define KAIRO_GPU_GXM_H

#include <stdint.h>

/* The record: the ternary raster operation, the flags, the transparency key (a BLT buffer's first pixel), the
   pixel's bits (0xff, 0xffff) */
enum { GX_ROP = 0, GX_FLAGS = 1, GX_KEY = 2, GX_ONES = 3, GX_WORDS = 4 };
#define GXF_DEST 1u /* the destination is read (else all ones) */
#define GXF_KEY  2u /* a pixel whose source is the key is not drawn */

#define GX_PIXEL_WORDS 2
#define GXW_IMM        0x80000000u /* the second word is the source itself, in its low 16 bits */

struct kairo_seg;
struct kairo_seg *kairo_gxm_open(uint8_t *gmem, uint32_t gmem_mask);

#endif
