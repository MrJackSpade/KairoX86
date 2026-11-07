/*
 * The S3 86C801 to Trio64's graphics engine on the GPU (KairoX86#271): its batch on the drawing engines' shared
 * batches (86box/kairo_gpu_seg.h, gpu_seg.c, gpu_seg_run.c) with its kernel, shaders/s3.comp. vid_s3.c records the
 * pixels its walks draw.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_s3.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t s3_spirv[] = {
#include "s3.comp.inc"
};

struct kairo_seg *
kairo_s3_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp)
{
    return kairo_seg_open("s3", s3_spirv, sizeof(s3_spirv), vram, vram_mask, S3_WORDS, changed, stamp);
}
