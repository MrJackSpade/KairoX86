/*
 * The 3dfx Voodoo's triangles on the GPU (KairoX86#277, #278; core/kairo/gpu_voodoo.c): with the
 * machine's Hardware acceleration on (86box/kairo_gpu.h), a Voodoo's triangles are recorded in order
 * instead of going to its render threads, and drawn by one kernel (core/kairo/shaders/voodoo.comp) at the
 * points where 86Box waits for its render threads (voodoo_wait_for_render_thread_idle), and wherever the
 * processor is about to read or write card memory a recorded triangle draws on (the touch). Its frame
 * buffer and texture caches are memory the GPU shares (kairo_gpu_alloc).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_VOODOO_H
#define KAIRO_GPU_VOODOO_H

#include <stdint.h>

struct voodoo_t;
struct voodoo_params_t;

/* At the card's start, its frame buffer and texture caches allocated: its GPU state (voodoo->k_gpu) */
void *kairo_voodoo_gpu_open(struct voodoo_t *voodoo);
/* At its end, before its memory goes */
void kairo_voodoo_gpu_close(struct voodoo_t *voodoo);
/* A triangle (its textures in the caches: voodoo_use_texture), recorded */
void kairo_voodoo_gpu_queue(struct voodoo_t *voodoo, const struct voodoo_params_t *params);
/* Draws every recorded triangle */
void kairo_voodoo_gpu_drain(struct voodoo_t *voodoo);
/* The processor reads or writes len bytes at addr in the frame buffer: draws first if a recorded
   triangle draws there */
void kairo_voodoo_gpu_touch(struct voodoo_t *voodoo, uint32_t addr, uint32_t len);

#endif
