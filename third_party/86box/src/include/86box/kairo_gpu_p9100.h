/*
 * The Weitek Power 9100's drawing engines on the GPU (KairoX86#266): the operation record of its batch
 * (kairo_gpu_seg.h), as words, and the batch's opening (core/kairo/gpu_p9100.c, core/kairo/shaders/p9100.comp).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_P9100_H
#define KAIRO_GPU_P9100_H

#include <stdint.h>

enum {
    P9_KIND = 0, P9_RASTER = 1, P9_PMASK = 2, P9_BPP = 3, P9_PITCH = 4, P9_SX = 5, P9_SY = 6, P9_DX = 7, P9_DY = 8,
    P9_COLOR = 9, P9_PAT_X = 13, P9_PAT_Y = 14, P9_PATTERN = 15, P9_USES_PAT = 23,
    P9_INS = 24, P9_MODE = 28, P9_BG = 29, P9_HT = 30, P9_STEP = 31, P9_ROT = 32, P9_RMASK = 33, P9_GPMASK = 34,
    P9_BITMASK = 35, P9_EXPAND = 36, P9_PPL = 37, P9_WORDS = 40
};
/* P9_KIND */
enum { P9K_COLOR = 0, P9K_BLIT = 1, P9K_PIXEL8 = 2, P9K_GHA_BLIT = 3, P9K_GHA_LINE = 4 };

struct kairo_seg;
struct kairo_seg *kairo_p9100_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp);

#endif
