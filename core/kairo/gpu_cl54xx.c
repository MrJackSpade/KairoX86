/*
 * The Cirrus Logic GD54xx BitBLT engine on the GPU (KairoX86#250): its batch on the drawing engines' shared batches
 * (86box/kairo_gpu_seg.h, gpu_seg.c, gpu_seg_run.c) with its kernel, shaders/cl54xx.comp. vid_cl54xx.c records the
 * bytes its walks draw.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_cl54xx.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t cl54xx_spirv[] = {
#include "cl54xx.comp.inc"
};

struct kairo_seg *
kairo_cl54xx_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp)
{
    return kairo_seg_open("cl54xx", cl54xx_spirv, sizeof(cl54xx_spirv), vram, vram_mask, CL_WORDS, changed, stamp);
}
