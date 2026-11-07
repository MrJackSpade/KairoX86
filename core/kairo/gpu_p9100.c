/*
 * The Weitek Power 9100's drawing engines on the GPU (KairoX86#266): its batch on the drawing engines' shared batches
 * (86box/kairo_gpu_seg.h, gpu_seg.c) with its kernel, shaders/p9100.comp. vid_p9100.c records the operations and their
 * rows.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_p9100.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t p9100_spirv[] = {
#include "p9100.comp.inc"
};

struct kairo_seg *
kairo_p9100_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp)
{
    return kairo_seg_open("p9100", p9100_spirv, sizeof(p9100_spirv), vram, vram_mask, P9_WORDS, changed, stamp);
}
