/*
 * The Matrox Millennium and Mystique's drawing engine on the GPU (KairoX86#264): its batch on the drawing engines'
 * shared batches (86box/kairo_gpu_seg.h, gpu_seg.c, gpu_seg_run.c) with its kernel, shaders/mga.comp. vid_mga.c
 * records the pixels its walks store.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_mga.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t mga_spirv[] = {
#include "mga.comp.inc"
};

struct kairo_seg *
kairo_mga_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp)
{
    return kairo_seg_open("Matrox", mga_spirv, sizeof(mga_spirv), vram, vram_mask, MG_WORDS, changed, stamp);
}
