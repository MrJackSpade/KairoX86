/*
 * The Western Digital WD90C31's BitBLT engine and the WD90C33's drawing engine on the GPU (KairoX86#267): the
 * operation record of their batch (kairo_gpu_seg.h), a pixel's stream words, and the batch's opening
 * (core/kairo/gpu_wd90c3x.c, core/kairo/shaders/wd90c3x.comp). Both chips draw a pixel the same way
 * (vid_wd90c31.c wd90c31_blt_pixel, vid_wd90c33.c wd90c33_plot); each fills the record from its own registers.
 *
 * A pixel's words: its kind (below; bits 8-10 the destination's bit and bits 16-18 the source's, in planar memory)
 * and its source: the value, or (WDK_ADDR) the address of the pixel it is.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_WD90C3X_H
#define KAIRO_GPU_WD90C3X_H

#include <stdint.h>

/* The record: the raster operation (the data sheets' 4-bit truth table), the colours, the transparency colour and
   its compare mask (the bits compared: already cut to the pixel's), the write mask (planes in planar memory, bits
   else), the depth (0 planar, a pixel its bit of each plane in a dword; 1 a byte; 2 a word) and the flags */
enum { WD_ROP = 0, WD_FG = 1, WD_BG = 2, WD_TRANS = 3, WD_CMP_MASK = 4, WD_MASK = 5, WD_DEPTH = 6, WD_FLAGS = 7, WD_WORDS = 8 };
#define WDF_MONO_SKIP 1u /* a mono pixel's background not drawn */
#define WDF_DST_CMP   2u /* a colour pixel drawn only where the destination's compare comes out as WDF_CMP_MATCH says */
#define WDF_CMP_MATCH 4u /* drawn where the destination matches the transparency colour, else where it differs */
#define WDF_FIXED     8u /* a colour pixel the foreground colour */

#define WD_PIXEL_WORDS 2
#define WDK_ADDR       1u /* the source is the pixel at the second word's address */
#define WDK_MONO       2u /* the pixel is the foreground or background colour, as its mono bit says */
#define WDK_MONO_CMP   4u /* its mono bit: whether its source matches the transparency colour */
#define WDK_MONO_NZ    16u /* else whether its source is not 0 (the WD90C31's mono format over a screen source) */
#define WDK_MONO_BIT   8u /* else its mono bit itself */

struct kairo_seg;
struct kairo_seg *kairo_wd90c3x_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp);

#endif
