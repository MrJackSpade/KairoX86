/*
 * The Cyrix MediaGX's BitBLT and vector engine on the GPU (KairoX86#315): its batch on the drawing engines' shared
 * batches (86box/kairo_gpu_seg.h, gpu_seg.c, gpu_seg_run.c) with its kernel, shaders/gxm.comp. vid_cyrix_gxm.c records
 * the pixels its walks draw. Its video memory is the graphics memory at the top of main RAM, which mem.c makes memory
 * the GPU shares on the MediaGX machines; the display keeps no changed pages (it draws every line every frame).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_gxm.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t gxm_spirv[] = {
#include "gxm.comp.inc"
};

struct kairo_seg *
kairo_gxm_open(uint8_t *gmem, uint32_t gmem_mask)
{
    return kairo_seg_open("gxm", gxm_spirv, sizeof(gxm_spirv), gmem, gmem_mask, GX_WORDS, NULL, NULL);
}
