/*
 * The Trident TGUI's graphics engine on the GPU (KairoX86#274): the operation record of its batch (kairo_gpu_seg.h),
 * a pixel's stream words, and the batch's opening (core/kairo/gpu_tgui.c, core/kairo/shaders/tgui.comp).
 *
 * A pixel's words: its kind (TGK_ADDR, the source the pixel at the next word's address; TGK_CMP, left where that
 * source is the transparent colour), its source (the value, or the address) and its pattern.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_TGUI_H
#define KAIRO_GPU_TGUI_H

#include <stdint.h>

enum { TG_ROP = 0, TG_TRANS = 1, TG_BYTES = 2, TG_WORDS = 4 };
#define TG_PIXEL_WORDS 3
#define TGK_ADDR       1u
#define TGK_CMP        2u

struct kairo_seg;
struct kairo_seg *kairo_tgui_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp);

#endif
