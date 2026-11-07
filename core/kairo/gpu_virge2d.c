/*
 * The S3 ViRGE and Trio3D's 2D engine on the GPU (KairoX86#272): its batch on the drawing engines' shared batches
 * (86box/kairo_gpu_seg.h, gpu_seg.c, gpu_seg_run.c) with its kernel, shaders/virge2d.comp. vid_s3_virge.c records the
 * pixels s3_virge_bitblt draws.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_virge2d.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t virge2d_spirv[] = {
#include "virge2d.comp.inc"
};

struct kairo_seg *
kairo_virge2d_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp)
{
    return kairo_seg_open("ViRGE-2D", virge2d_spirv, sizeof(virge2d_spirv), vram, vram_mask, V2_WORDS, changed, stamp);
}
