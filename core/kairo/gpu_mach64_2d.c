/*
 * The ATI Mach64's 2D engine on the GPU (KairoX86#237): its batch on the drawing engines' shared batches
 * (86box/kairo_gpu_seg.h, gpu_seg.c) with its kernel, shaders/mach64_2d.comp. vid_ati_mach64_accel.c records the
 * operations and their rows.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_mach64.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t mach64_2d_spirv[] = {
#include "mach64_2d.comp.inc"
};

struct kairo_seg *
kairo_mach64_2d_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp)
{
    return kairo_seg_open("mach64-2d", mach64_2d_spirv, sizeof(mach64_2d_spirv), vram, vram_mask, M2_WORDS, changed, stamp);
}
