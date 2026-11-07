/*
 * The IBM 8514/A's drawing engine and the ATI Mach8 and Mach32's on the GPU (KairoX86#238): their batch on the drawing
 * engines' shared batches (86box/kairo_gpu_seg.h, gpu_seg.c, gpu_seg_run.c) with its kernel, shaders/ibm8514.comp.
 * vid_8514a.c and vid_ati_mach8.c record the pixels their walks draw.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_ibm8514.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t ibm8514_spirv[] = {
#include "ibm8514.comp.inc"
};

struct kairo_seg *
kairo_ibm8514_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp)
{
    return kairo_seg_open("8514/A", ibm8514_spirv, sizeof(ibm8514_spirv), vram, vram_mask, I8_WORDS, changed, stamp);
}
