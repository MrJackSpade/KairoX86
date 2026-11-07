/*
 * The 3dfx cards' 2D drawing on the GPU (KairoX86#278, #277): the Voodoo Banshee and Voodoo3's 2D engine and the
 * Voodoo2's blitter record the pixels their walks draw, with the machine's Hardware acceleration on, in one batch over
 * the card's frame buffer (fb_mem) on the drawing engines' shared batches, drawn by the Banshee 2D kernel
 * (86box/kairo_gpu_banshee2d.h: the destination read, the raster operation the colour keys choose, the write). The
 * walks run on the card's FIFO thread holding the batch's lock (voodoo_k2d_lock); the machine's thread, the display
 * and the 3D engine reach the batch through the card's k2d_touch and k2d_drain hooks, which take it too.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef VIDEO_VOODOO_K2D_H
#define VIDEO_VOODOO_K2D_H

#include <stdint.h>

#include <86box/kairo_gpu_banshee2d.h>

/* At the card's start, its frame buffer allocated (fb_mem, fb_mask; changedvram where its display keeps one): the
   batch (voodoo->k2d and its hooks), with Hardware acceleration on; else nothing */
void voodoo_k2d_open(voodoo_t *voodoo);
/* At its end */
void voodoo_k2d_close(voodoo_t *voodoo);

/* Around a walk: the batch's lock, the 3D engine's recorded work drawn first (nothing without the batch) */
void voodoo_k2d_lock(voodoo_t *voodoo);
void voodoo_k2d_unlock(voodoo_t *voodoo);

/* The walk reads len bytes at p, in the frame buffer: what the batch draws there is drawn first (the lock held) */
void voodoo_k2d_read(voodoo_t *voodoo, const uint8_t *p, uint32_t len);

/* One pixel of pb bytes at addr: its operation record (B2_WORDS words: the raster operations, the destination key,
   the bytes), its source, pattern and whether the source is in the source key (the lock held) */
void voodoo_k2d_pixel(voodoo_t *voodoo, uint32_t addr, int pb, const uint32_t *rec, uint32_t src, uint32_t pattern,
                      int src_key);

#endif /*VIDEO_VOODOO_K2D_H*/
