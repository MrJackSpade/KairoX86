/*
 * The Chips & Technologies B69000 BitBLT engine on the GPU (KairoX86#249): its batch on the drawing engines' shared
 * batches (86box/kairo_gpu_seg.h, gpu_seg.c, gpu_seg_run.c) with its kernel, shaders/chips69000.comp.
 * vid_chips_69000.c records the pixels its walks draw.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_chips69000.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t chips69000_spirv[] = {
#include "chips69000.comp.inc"
};

struct kairo_seg *
kairo_chips69000_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp)
{
    return kairo_seg_open("chips69000", chips69000_spirv, sizeof(chips69000_spirv), vram, vram_mask, CH_WORDS, changed, stamp);
}
