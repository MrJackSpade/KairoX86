/*
 * The S3 ViRGE's triangles on the GPU (KairoX86#272; 86box/kairo_gpu_virge.h): the batch of recorded
 * triangles, the video memory it draws on (a page map), and its drain through shaders/virge.comp.
 *
 * A batch draws into one set of buffers (colour and depth bases and strides, the pixel format) with one
 * set of flags: another drains it first, so every invocation of the kernel owns the same four pixels'
 * memory for the whole batch.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <pthread.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <86box/86box.h>
#include <86box/kairo_gpu.h>
#include <86box/kairo_gpu_virge.h>

#include "gpu_internal.h"

static const uint32_t virge_spirv[] = {
#include "virge.comp.inc"
};

#define TRIS_MAX 8192

typedef struct {
    pthread_mutex_t     lock;
    kairo_gpu_buffer_t *tris;
    kairo_gpu_buffer_t *vram;
    uint32_t            vram_mask;
    uint32_t            count;
    /* The batch's buffers and flags */
    uint32_t dest_base, dest_str, z_base, z_str, format, flags;
    int      row_lo, row_hi, x_lo, x_hi;
    kairo_gpu_pages_t pages;
} virge_gpu_t;

static kairo_gpu_kernel_t *kernel;
static unsigned long long  triangles_drawn;

void *
kairo_virge_gpu_open(uint8_t *vram, uint32_t vram_mask)
{
    virge_gpu_t *g = calloc(1, sizeof(virge_gpu_t));
    if (g == NULL)
        fatal("ViRGE on the GPU: no memory\n");
    pthread_mutex_init(&g->lock, NULL);
    g->tris      = kairo_gpu_buffer((size_t) TRIS_MAX * KV_WORDS * 4);
    g->vram      = kairo_gpu_buffer_of(vram);
    g->vram_mask = vram_mask;
    kairo_gpu_pages_init(&g->pages, vram_mask);
    return g;
}

static void
drain_locked(virge_gpu_t *g)
{
    if (g->count == 0)
        return;
    if (kernel == NULL)
        kernel = kairo_gpu_kernel("virge", virge_spirv, sizeof(virge_spirv), 2, 5 * 4);
    const uint32_t push[5] = { g->count, g->vram_mask, (uint32_t) g->x_lo, (uint32_t) g->row_lo, g->flags };
    kairo_gpu_buffer_t *const buffers[2] = { g->tris, g->vram };
    kairo_gpu_run(kernel, buffers, push, (uint32_t) (g->x_hi - g->x_lo) / 64 + 1, (uint32_t) (g->row_hi - g->row_lo) / 4 + 1, 1);
    triangles_drawn += g->count;
    g->count = 0;
    kairo_gpu_pages_clear(&g->pages);
}

void
kairo_virge_gpu_drain(void *gpu)
{
    virge_gpu_t *g = gpu;
    if (!kairo_gpu_pages_any(&g->pages))
        return;
    pthread_mutex_lock(&g->lock);
    drain_locked(g);
    pthread_mutex_unlock(&g->lock);
}

void
kairo_virge_gpu_touch(void *gpu, uint32_t addr, uint32_t len)
{
    virge_gpu_t *g = gpu;
    if (kairo_gpu_pages_hit(&g->pages, addr, len))
        kairo_virge_gpu_drain(gpu);
}

void
kairo_virge_gpu_close(void *gpu)
{
    virge_gpu_t *g = gpu;
    if (g == NULL)
        return;
    kairo_virge_gpu_drain(gpu);
    kairo_gpu_buffer_free(g->tris);
    kairo_gpu_pages_free(&g->pages);
    pthread_mutex_destroy(&g->lock);
    free(g);
}

void
kairo_gpu_virge_close(void)
{
    /* How many triangles the GPU drew, for the graphics batch (core/test/gpu/compare.py) */
    fprintf(stderr, "kairo-gpu-virge: %llu triangles drawn\n", triangles_drawn);
    triangles_drawn = 0;
    kairo_gpu_kernel_free(kernel);
    kernel = NULL;
}

/* A line's span ends, as tri() rounds them: its first pixel and one past its last */
static int
span_x(int32_t edge, int x_dir)
{
    return ((edge + ((1 << 20) - 1)) >> 20) - ((x_dir < 0) ? 1 : 0);
}

static bool
ranges_overlap(uint64_t a, uint64_t a_end, uint64_t b, uint64_t b_end)
{
    return (a < b_end) && (b < a_end);
}

void
kairo_virge_gpu_queue(void *gpu, uint32_t *r, uint32_t flags, uint32_t tex_start, uint32_t tex_len)
{
    virge_gpu_t   *g      = gpu;
    const uint32_t cmd    = r[KV_CMD];
    const int      bpp    = (int) ((cmd >> 2) & 7);
    const bool     hc     = (cmd & 2) != 0;
    const bool     use_z  = !(cmd & (3u << 24));
    const int      x_dir  = r[KV_TLR] ? 1 : -1;
    const int      ty01   = (int) r[KV_TY01];
    const int      lines  = ty01 + (int) r[KV_TY12];
    const int      tys    = (int) r[KV_TYS];

    if (bpp > 2)
        fatal("ViRGE on the GPU: pixel format %d\n", bpp);
    if (lines <= 0)
        return;

    /* The rows: tys up to lines - 1 above it, inside the clip rectangle */
    int row_lo = tys - (lines - 1);
    int row_hi = tys;
    if (hc) {
        if (row_lo < (int) r[KV_CLIP_T])
            row_lo = (int) r[KV_CLIP_T];
        if (row_hi > (int) r[KV_CLIP_B])
            row_hi = (int) r[KV_CLIP_B];
    }
    if (row_lo < 0)
        row_lo = 0;
    if (row_hi > 4095)
        row_hi = 4095;
    if (row_lo > row_hi)
        return;

    /* The pixels: each line's span as tri() finds it (its edges wrap as the CPU's int32 sums do, so only
       the lines themselves bound it) */
    int x_lo = 4096;
    int x_hi = -1;
    for (int row = row_lo; row <= row_hi; row++) {
        const int     i  = tys - row;
        const int32_t x1 = (int32_t) (r[KV_TXS] + (uint32_t) i * r[KV_DX02]);
        const int32_t x2 = (i < ty01) ? (int32_t) (r[KV_TXEND01] + (uint32_t) i * r[KV_DX01])
                                      : (int32_t) (r[KV_TXEND12] + (uint32_t) (i - ty01) * r[KV_DX12]);
        int           x  = span_x(x1, x_dir);
        int           xe = span_x(x2, x_dir);
        if ((x == xe) || ((x_dir > 0) ? (x > xe) : (x < xe)))
            continue;
        /* The pixels drawn: x up to xe (exclusive) in x_dir */
        int first = (x_dir > 0) ? x : xe + 1;
        int last  = (x_dir > 0) ? xe - 1 : x;
        if (hc) {
            if (first < (int) r[KV_CLIP_L])
                first = (int) r[KV_CLIP_L];
            if (last > (int) r[KV_CLIP_R])
                last = (int) r[KV_CLIP_R];
        }
        if (first < 0)
            first = 0;
        if (last > 4095)
            last = 4095;
        if (first > last)
            continue;
        if (first < x_lo)
            x_lo = first;
        if (last > x_hi)
            x_hi = last;
    }
    if (x_lo > x_hi)
        return;
    x_lo &= ~3;

    /* Its own memory: the colour and depth rows apart, the texture apart from both (the CPU draws such a
       triangle pixel by pixel in order, which the kernel does not) */
    const uint64_t pixel  = (uint64_t) bpp + 1;
    const uint64_t d_lo   = (uint64_t) r[KV_DEST_BASE] + (uint64_t) row_lo * r[KV_DEST_STR] + (uint64_t) x_lo * pixel;
    const uint64_t d_hi   = (uint64_t) r[KV_DEST_BASE] + (uint64_t) row_hi * r[KV_DEST_STR] + (uint64_t) (x_hi + 4) * pixel;
    const uint64_t z_lo   = (uint64_t) r[KV_Z_BASE] + (uint64_t) row_lo * r[KV_Z_STR] + (uint64_t) x_lo * 2;
    const uint64_t z_hi   = (uint64_t) r[KV_Z_BASE] + (uint64_t) row_hi * r[KV_Z_STR] + (uint64_t) (x_hi + 4) * 2;
    if (use_z && ranges_overlap(d_lo, d_hi, z_lo, z_hi))
        fatal("ViRGE on the GPU: a triangle whose depth buffer overlaps its colour buffer\n");
    if (tex_len && (ranges_overlap(tex_start, (uint64_t) tex_start + tex_len, d_lo, d_hi)
                    || (use_z && ranges_overlap(tex_start, (uint64_t) tex_start + tex_len, z_lo, z_hi))))
        fatal("ViRGE on the GPU: a triangle textured from its own colour or depth buffer\n");

    pthread_mutex_lock(&g->lock);
    /* Its texture drawn on by the batch: the batch first */
    if (tex_len && kairo_gpu_pages_hit(&g->pages, tex_start, tex_len))
        drain_locked(g);
    const uint32_t format = cmd & (7u << 2);
    if ((g->count != 0)
        && ((g->count == TRIS_MAX) || (r[KV_DEST_BASE] != g->dest_base) || (r[KV_DEST_STR] != g->dest_str)
            || (r[KV_Z_BASE] != g->z_base) || (r[KV_Z_STR] != g->z_str) || (format != g->format) || (flags != g->flags)))
        drain_locked(g);
    if (g->count == 0) {
        g->dest_base = r[KV_DEST_BASE];
        g->dest_str  = r[KV_DEST_STR];
        g->z_base    = r[KV_Z_BASE];
        g->z_str     = r[KV_Z_STR];
        g->format    = format;
        g->flags     = flags;
        g->row_lo    = row_lo;
        g->row_hi    = row_hi;
        g->x_lo      = x_lo;
        g->x_hi      = x_hi;
    } else {
        if (row_lo < g->row_lo)
            g->row_lo = row_lo;
        if (row_hi > g->row_hi)
            g->row_hi = row_hi;
        if (x_lo < g->x_lo)
            g->x_lo = x_lo;
        if (x_hi > g->x_hi)
            g->x_hi = x_hi;
    }
    r[KV_ROW_LO] = (uint32_t) row_lo;
    r[KV_ROW_HI] = (uint32_t) row_hi;
    r[KV_X_LO]   = (uint32_t) x_lo;
    r[KV_X_HI]   = (uint32_t) x_hi;
    memcpy((uint32_t *) g->tris->data + (size_t) g->count * KV_WORDS, r, KV_WORDS * 4);
    g->count++;
    for (int row = row_lo; row <= row_hi; row++) {
        kairo_gpu_pages_mark(&g->pages, r[KV_DEST_BASE] + (uint32_t) row * r[KV_DEST_STR] + (uint32_t) x_lo * (uint32_t) pixel,
                             (uint32_t) (x_hi - x_lo + 4) * (uint32_t) pixel);
        if (use_z)
            kairo_gpu_pages_mark(&g->pages, r[KV_Z_BASE] + (uint32_t) row * r[KV_Z_STR] + (uint32_t) x_lo * 2,
                                 (uint32_t) (x_hi - x_lo + 4) * 2);
    }
    pthread_mutex_unlock(&g->lock);
}
