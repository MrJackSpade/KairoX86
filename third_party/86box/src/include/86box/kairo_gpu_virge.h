/*
 * The S3 ViRGE's triangles on the GPU (KairoX86#272; core/kairo/gpu_virge.c, core/kairo/shaders/virge.comp):
 * with the machine's Hardware acceleration on, each triangle the guest queues is recorded (its setup, as
 * s3_virge_triangle and tri() would start it) instead of going to the render threads, and a batch is drawn
 * by one kernel where 86Box waits for its 3D engine, and wherever the processor or the display is about
 * to read or write video memory the batch draws on (the touch).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_VIRGE_H
#define KAIRO_GPU_VIRGE_H

#include <stdint.h>

/* A triangle's record, as words (the kernel's T_ offsets) */
enum {
    KV_CMD       = 0,
    KV_CLIP_L    = 1,
    KV_CLIP_R    = 2,
    KV_CLIP_T    = 3,
    KV_CLIP_B    = 4,
    KV_DEST_BASE = 5,
    KV_DEST_STR  = 6,
    KV_Z_BASE    = 7,
    KV_Z_STR     = 8,
    KV_TEX_LEVEL = 9, /* [10]: each texture level's byte address */
    KV_TEX_BDR   = 19,
    KV_TBU       = 20, /* << 11 */
    KV_TBV       = 21,
    KV_FOG       = 22, /* b | g << 8 | r << 16 */
    KV_TYS       = 23,
    KV_TY01      = 24,
    KV_TY12      = 25,
    KV_TLR       = 26,
    KV_TXS       = 27,
    KV_TXEND01   = 28,
    KV_TXEND12   = 29,
    KV_DX02      = 30,
    KV_DX01      = 31,
    KV_DX12      = 32,
    KV_START     = 33, /* [9]: u v z r g b a d w */
    KV_DX        = 42, /* [9]: per pixel */
    KV_DY        = 51, /* [9]: per line */
    KV_ROW_LO    = 60, /* the rows and pixels it may draw (core/kairo/gpu_virge.c fills these) */
    KV_ROW_HI    = 61,
    KV_X_LO      = 62,
    KV_X_HI      = 63,
    KV_WORDS     = 64,
};

/* The kernel's flags */
#define KAIRO_VIRGE_BILINEAR  1u
#define KAIRO_VIRGE_DITHER    2u
#define KAIRO_VIRGE_PERSP_375 4u

/* The card's GPU state, its video memory shared with the GPU (kairo_gpu_alloc) */
void *kairo_virge_gpu_open(uint8_t *vram, uint32_t vram_mask);
void  kairo_virge_gpu_close(void *gpu);
/* A triangle (record: KV_WORDS words, its rows and pixels left to fill), drawn with flags; the bytes its
   texture reads (tex_start, tex_len; 0 for none). A batch draws into one set of buffers: another set,
   other flags or a full batch draws it first, as does a texture read from what it draws on. */
void kairo_virge_gpu_queue(void *gpu, uint32_t *record, uint32_t flags, uint32_t tex_start, uint32_t tex_len);
/* Draws every recorded triangle */
void kairo_virge_gpu_drain(void *gpu);
/* The processor or the display reads or writes len bytes at addr: draws first if a recorded triangle
   draws there */
void kairo_virge_gpu_touch(void *gpu, uint32_t addr, uint32_t len);

#endif
