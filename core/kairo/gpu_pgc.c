/*
 * The IBM Professional Graphics Controller's (and the ImageManager 1024's) drawing processor on the GPU
 * (KairoX86#268, #261): its batch on the drawing engines' shared batches (86box/kairo_gpu_seg.h, gpu_seg.c,
 * gpu_seg_run.c) with its kernel, shaders/pgc.comp. vid_pgc.c records the pixels its walks draw. The card's display
 * keeps no changed-page map: it reads every line.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_pgc.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t pgc_spirv[] = {
#include "pgc.comp.inc"
};

struct kairo_seg *
kairo_pgc_open(uint8_t *vram, uint32_t vram_mask)
{
    return kairo_seg_open("PGC", pgc_spirv, sizeof(pgc_spirv), vram, vram_mask, PGC_K_WORDS, NULL, NULL);
}
