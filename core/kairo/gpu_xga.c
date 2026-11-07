/*
 * The IBM XGA's drawing engine on the GPU (KairoX86#280): its batch on the drawing engines' shared batches
 * (86box/kairo_gpu_seg.h, gpu_seg.c, gpu_seg_run.c) with its kernel, shaders/xga.comp. vid_xga.c records the pixels its
 * walks draw.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_xga.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t xga_spirv[] = {
#include "xga.comp.inc"
};

struct kairo_seg *
kairo_xga_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp)
{
    return kairo_seg_open("xga", xga_spirv, sizeof(xga_spirv), vram, vram_mask, XG_WORDS, changed, stamp);
}
