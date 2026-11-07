/*
 * The Trident TGUI's graphics engine on the GPU (KairoX86#274): its batch on the drawing engines' shared batches
 * (86box/kairo_gpu_seg.h, gpu_seg.c, gpu_seg_run.c) with its kernel, shaders/tgui.comp. vid_tgui9440.c records the
 * pixels its walks draw.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stddef.h>

#include <86box/kairo_gpu_tgui.h>
#include <86box/kairo_gpu_seg.h>

static const uint32_t tgui_spirv[] = {
#include "tgui.comp.inc"
};

struct kairo_seg *
kairo_tgui_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp)
{
    return kairo_seg_open("tgui", tgui_spirv, sizeof(tgui_spirv), vram, vram_mask, TG_WORDS, changed, stamp);
}
