/*
 * The 3dfx Voodoo Banshee and Voodoo3's 2D engine on the GPU (KairoX86#278): its batch on the drawing engines' shared
 * batches (86box/kairo_gpu_seg.h, gpu_seg.c, gpu_seg_run.c) with its kernel, shaders/banshee2d.comp.
 * vid_voodoo_banshee_blitter.c records the pixels its walks draw.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_banshee2d.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t banshee2d_spirv[] = {
#include "banshee2d.comp.inc"
};

struct kairo_seg *
kairo_banshee2d_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp)
{
    return kairo_seg_open("Banshee-2D", banshee2d_spirv, sizeof(banshee2d_spirv), vram, vram_mask, B2_WORDS, changed, stamp);
}
