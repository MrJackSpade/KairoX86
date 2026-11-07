/*
 * The Tseng Labs ET4000/W32's accelerator on the GPU (KairoX86#254): its batch on the drawing engines' shared batches
 * (86box/kairo_gpu_seg.h, gpu_seg.c) with its kernel, shaders/et4000w32.comp. vid_et4000w32.c records the bytes its
 * walk draws.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_et4000w32.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t et4000w32_spirv[] = {
#include "et4000w32.comp.inc"
};

struct kairo_seg *
kairo_et4000w32_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp)
{
    return kairo_seg_open("et4000w32", et4000w32_spirv, sizeof(et4000w32_spirv), vram, vram_mask, ET_WORDS, changed, stamp);
}
