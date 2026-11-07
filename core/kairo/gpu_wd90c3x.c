/*
 * The Western Digital WD90C31's BitBLT engine and the WD90C33's drawing engine on the GPU (KairoX86#267): their batch
 * on the drawing engines' shared batches (86box/kairo_gpu_seg.h, gpu_seg.c, gpu_seg_run.c) with their kernel,
 * shaders/wd90c3x.comp. vid_wd90c31.c and vid_wd90c33.c record the pixels their walks draw.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_wd90c3x.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t wd90c3x_spirv[] = {
#include "wd90c3x.comp.inc"
};

struct kairo_seg *
kairo_wd90c3x_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp)
{
    return kairo_seg_open("wd90c3x", wd90c3x_spirv, sizeof(wd90c3x_spirv), vram, vram_mask, WD_WORDS, changed, stamp);
}
