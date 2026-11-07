/*
 * The 3dfx Voodoo's triangles on the GPU (KairoX86#277, #278; 86box/kairo_gpu_voodoo.h): the record of
 * each triangle the guest sends (the setup voodoo_triangle and voodoo_half_triangle do before their
 * lines, as words), the card memory the recorded triangles draw on (a page map), and the batch's drain
 * through shaders/voodoo.comp.
 *
 * A batch draws into one set of buffers (colour and auxiliary offsets, strides, tiling): another set
 * drains it first, so every invocation of the kernel owns the same two pixels' memory for the whole
 * batch.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <math.h>
#include <pthread.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#include <86box/86box.h>
#include <86box/device.h>
#include <86box/mem.h>
#include <86box/timer.h>
#include <86box/plat.h>
#include <86box/thread.h>
#include <86box/video.h>
#include <86box/vid_svga.h>
#include <86box/vid_voodoo_common.h>
#include <86box/vid_voodoo_dither.h>
#include <86box/vid_voodoo_regs.h>
#include <86box/vid_voodoo_render.h>
#include <86box/vid_voodoo_texture.h>
#include <86box/kairo_gpu.h>
#include <86box/kairo_gpu_voodoo.h>

#include "gpu_internal.h"

static const uint32_t voodoo_spirv[] = {
#include "voodoo.comp.inc"
};

/* The record, as shaders/voodoo.comp reads it (its T_ offsets) */
enum {
    T_WORDS     = 168,
    T_AX        = 0,
    T_DXAB      = 6,
    T_DXAC      = 7,
    T_DXBC      = 8,
    T_XDIR      = 9,
    T_YSTART    = 10,
    T_YEND      = 11,
    T_Y0        = 12,
    T_AXR       = 13,
    T_YORIGIN   = 14,
    T_ROWLO     = 15,
    T_ROWHI     = 16,
    T_XLO       = 17,
    T_XHI       = 18,
    T_CLIPL     = 19,
    T_CLIPR     = 20,
    T_FLAGS     = 21,
    T_C         = 22,
    T_CDX       = 27,
    T_CDY       = 32,
    T_Q         = 37,
    T_FBZMODE   = 79,
    T_FBZCP     = 80,
    T_FOGMODE   = 81,
    T_ALPHAMODE = 82,
    T_ZACOLOR   = 83,
    T_COLOR0    = 84,
    T_COLOR1    = 85,
    T_FOGCOLOR  = 86,
    T_CHROMA    = 87,
    T_STIPPLE   = 88,
    T_TMUCONFIG = 89,
    T_ODDEVEN   = 90,
    T_TEXMODE   = 91,
    T_TLOD      = 93,
    T_ENTRY     = 95,
    T_LODMIN    = 97,
    T_LODMAX    = 99,
    T_LODTRI    = 101,
    T_LODBASE   = 103,
    T_LODBIAS   = 105,
    T_DMAX      = 107,
    T_DBIAS     = 109,
    T_DSCALE    = 111,
    T_MASKS     = 113,
    T_FOG       = 131,
    T_ENTRY_WORDS = 163,
};
enum {
    F_SPAN_PART      = 1,
    F_DUAL_TMUS      = 2,
    F_BILINEAR       = 4,
    F_DITHERSUB      = 8,
    F_TREX_OVERRIDE  = 16,
};
/* The tables' byte offsets (the kernel's TB_) */
enum {
    TB_DITHER_RB  = 0,
    TB_DITHER_G   = 4096,
    TB_DITHER_RB2 = 8192,
    TB_DITHER_G2  = 9216,
    TB_SUB_RB     = 10240,
    TB_SUB_G      = 14336,
    TB_SUB_RB2    = 18432,
    TB_SUB_G2     = 19456,
    TB_LOGTABLE   = 20480,
    TB_TEXOFFSET  = 20736,
    TB_BYTES      = 20736 + (LOD_MAX + 3) * 4,
};
#define TRIS_MAX     8192
#define ENTRY_WORDS  (256 * 256 + 256 * 256 + 128 * 128 + 64 * 64 + 32 * 32 + 16 * 16 + 8 * 8 + 4 * 4 + 2 * 2)
#define COUNTERS     5

/* vid_voodoo_render.c's logtable, for fastlog() */
static const uint8_t logtable[256] = {
    0x00, 0x01, 0x02, 0x04, 0x05, 0x07, 0x08, 0x09, 0x0b, 0x0c, 0x0e, 0x0f, 0x10, 0x12, 0x13, 0x15,
    0x16, 0x17, 0x19, 0x1a, 0x1b, 0x1d, 0x1e, 0x1f, 0x21, 0x22, 0x23, 0x25, 0x26, 0x27, 0x28, 0x2a,
    0x2b, 0x2c, 0x2e, 0x2f, 0x30, 0x31, 0x33, 0x34, 0x35, 0x36, 0x38, 0x39, 0x3a, 0x3b, 0x3d, 0x3e,
    0x3f, 0x40, 0x41, 0x43, 0x44, 0x45, 0x46, 0x47, 0x49, 0x4a, 0x4b, 0x4c, 0x4d, 0x4e, 0x50, 0x51,
    0x52, 0x53, 0x54, 0x55, 0x57, 0x58, 0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x60, 0x61, 0x62, 0x63,
    0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6a, 0x6c, 0x6d, 0x6e, 0x6f, 0x70, 0x71, 0x72, 0x73, 0x74,
    0x75, 0x76, 0x77, 0x78, 0x79, 0x7a, 0x7b, 0x7c, 0x7d, 0x7e, 0x7f, 0x80, 0x81, 0x83, 0x84, 0x85,
    0x86, 0x87, 0x88, 0x89, 0x8a, 0x8b, 0x8c, 0x8c, 0x8d, 0x8e, 0x8f, 0x90, 0x91, 0x92, 0x93, 0x94,
    0x95, 0x96, 0x97, 0x98, 0x99, 0x9a, 0x9b, 0x9c, 0x9d, 0x9e, 0x9f, 0xa0, 0xa1, 0xa2, 0xa2, 0xa3,
    0xa4, 0xa5, 0xa6, 0xa7, 0xa8, 0xa9, 0xaa, 0xab, 0xac, 0xad, 0xad, 0xae, 0xaf, 0xb0, 0xb1, 0xb2,
    0xb3, 0xb4, 0xb5, 0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0xba, 0xbb, 0xbc, 0xbc, 0xbd, 0xbe, 0xbf, 0xc0,
    0xc1, 0xc2, 0xc2, 0xc3, 0xc4, 0xc5, 0xc6, 0xc7, 0xc8, 0xc8, 0xc9, 0xca, 0xcb, 0xcc, 0xcd, 0xcd,
    0xce, 0xcf, 0xd0, 0xd1, 0xd1, 0xd2, 0xd3, 0xd4, 0xd5, 0xd6, 0xd6, 0xd7, 0xd8, 0xd9, 0xda, 0xda,
    0xdb, 0xdc, 0xdd, 0xde, 0xde, 0xdf, 0xe0, 0xe1, 0xe1, 0xe2, 0xe3, 0xe4, 0xe5, 0xe5, 0xe6, 0xe7,
    0xe8, 0xe8, 0xe9, 0xea, 0xeb, 0xeb, 0xec, 0xed, 0xee, 0xef, 0xef, 0xf0, 0xf1, 0xf2, 0xf2, 0xf3,
    0xf4, 0xf5, 0xf5, 0xf6, 0xf7, 0xf7, 0xf8, 0xf9, 0xfa, 0xfa, 0xfb, 0xfc, 0xfd, 0xfd, 0xfe, 0xff
};

typedef struct {
    pthread_mutex_t     lock;
    kairo_gpu_buffer_t *tris;
    kairo_gpu_buffer_t *counters;
    kairo_gpu_buffer_t *fb;
    kairo_gpu_buffer_t *tex[2];
    uint32_t            count;
    /* The batch's buffers */
    uint32_t draw_offset, aux_offset, row_width, aux_row_width, tiled;
    /* What it covers: rows and pixels, and the pages */
    int               row_lo, row_hi, x_lo, x_hi;
    kairo_gpu_pages_t pages;
    int16_t           entries[TRIS_MAX][2];
} voodoo_gpu_t;

/* Every card's: the kernel and its tables */
static kairo_gpu_kernel_t *kernel;
static kairo_gpu_buffer_t *tables;
static unsigned long long  triangles_drawn;

/* voodoo_lod_from_gradients(), voodoo_triangle_lod_base() and voodoo_lod_bias() (vid_voodoo_render.c) */
static int
lod_from_gradients(double dsdx, double dtdx, double dsdy, double dtdy)
{
    double gx = dsdx * dsdx + dtdx * dtdx;
    double gy = dsdy * dsdy + dtdy * dtdy;
    double g  = (gx > gy) ? gx : gy;
    if (g <= 0.0)
        return -(64 << 8);
    return (int) ((log2(g) / 2.0) * 256.0);
}

static int
triangle_lod_base(const voodoo_params_t *params, int tmu)
{
    const double one = 4294967296.0;
    return lod_from_gradients((double) params->tmu[tmu].dSdX / one, (double) params->tmu[tmu].dTdX / one,
                              (double) params->tmu[tmu].dSdY / one, (double) params->tmu[tmu].dTdY / one);
}

static int
lod_bias(const voodoo_params_t *params, int tmu)
{
    int bias = (params->tLOD[tmu] >> 12) & 0x3f;
    if (bias & 0x20)
        bias -= 0x40;
    return bias * (1 << 6);
}

static int32_t
sext16(int32_t v)
{
    v &= 0xffff;
    return (v & 0x8000) ? (v | (int32_t) 0xffff0000) : v;
}

static void
put64(uint32_t *r, int i, int part, int64_t v)
{
    r[T_Q + (i * 3 + part) * 2]     = (uint32_t) (uint64_t) v;
    r[T_Q + (i * 3 + part) * 2 + 1] = (uint32_t) ((uint64_t) v >> 32);
}

static void
put_tables(void)
{
    uint8_t *t = tables->data;
    memcpy(t + TB_DITHER_RB, dither_rb, 4096);
    memcpy(t + TB_DITHER_G, dither_g, 4096);
    memcpy(t + TB_DITHER_RB2, dither_rb2x2, 1024);
    memcpy(t + TB_DITHER_G2, dither_g2x2, 1024);
    memcpy(t + TB_SUB_RB, dithersub_rb, 4096);
    memcpy(t + TB_SUB_G, dithersub_g, 4096);
    memcpy(t + TB_SUB_RB2, dithersub_rb2x2, 1024);
    memcpy(t + TB_SUB_G2, dithersub_g2x2, 1024);
    memcpy(t + TB_LOGTABLE, logtable, 256);
    memcpy(t + TB_TEXOFFSET, texture_offset, (LOD_MAX + 3) * 4);
}

void *
kairo_voodoo_gpu_open(voodoo_t *voodoo)
{
    voodoo_gpu_t *g = calloc(1, sizeof(voodoo_gpu_t));
    if (g == NULL)
        fatal("Voodoo on the GPU: no memory\n");
    pthread_mutex_init(&g->lock, NULL);
    g->tris     = kairo_gpu_buffer((size_t) TRIS_MAX * T_WORDS * 4);
    g->counters = kairo_gpu_buffer(COUNTERS * 4);
    g->fb       = kairo_gpu_buffer_of(voodoo->fb_mem);
    g->tex[0]   = kairo_gpu_buffer_of(voodoo->texture_cache[0][0].data);
    g->tex[1]   = voodoo->dual_tmus ? kairo_gpu_buffer_of(voodoo->texture_cache[1][0].data) : g->tex[0];
    kairo_gpu_pages_init(&g->pages, voodoo->fb_mask);
    if (tables == NULL) {
        tables = kairo_gpu_buffer(TB_BYTES);
        put_tables();
    }
    return g;
}

/* Marks the pages under pixels x0 to x1 of a row of 16-bit pixels at byte offset row (tiled: 64 pixels
   across, 32 rows down, each tile column a page) */
static void
mark_pages(voodoo_gpu_t *g, uint32_t row, int tiled, int x0, int x1)
{
    if (tiled) {
        for (int tile = x0 >> 6; tile <= (x1 >> 6); tile++)
            kairo_gpu_pages_mark(&g->pages, row + (uint32_t) tile * 4096, 1);
    } else
        kairo_gpu_pages_mark(&g->pages, row + (uint32_t) x0 * 2, (uint32_t) (x1 - x0 + 1) * 2);
}

/* The textures' refcount_r, as the render threads raise them once each per triangle drawn */
static void
textures_done(voodoo_t *voodoo, int e0, int e1)
{
    for (int i = 0; i < voodoo->render_threads; i++) {
        ATOMIC_INC(voodoo->texture_cache[0][e0].refcount_r[i]);
        ATOMIC_INC(voodoo->texture_cache[1][e1].refcount_r[i]);
    }
}

static void
drain_locked(voodoo_t *voodoo, voodoo_gpu_t *g)
{
    if (g->count == 0)
        return;
    if (kernel == NULL)
        kernel = kairo_gpu_kernel("voodoo", voodoo_spirv, sizeof(voodoo_spirv), 6, 9 * 4);
    const uint32_t push[9] = { g->draw_offset, g->aux_offset, g->row_width, g->aux_row_width, g->tiled,
                               voodoo->fb_mask, g->count, (uint32_t) g->x_lo, (uint32_t) g->row_lo };
    uint32_t *counts = g->counters->data;
    memset(counts, 0, COUNTERS * 4);
    kairo_gpu_buffer_t *const buffers[6] = { g->tris, g->fb, g->tex[0], g->tex[1], tables, g->counters };
    kairo_gpu_run(kernel, buffers, push, (uint32_t) (g->x_hi - g->x_lo + 16) / 16, (uint32_t) (g->row_hi - g->row_lo + 8) / 8, 1);
    voodoo->fbiPixelsIn += counts[0];
    voodoo->fbiChromaFail += counts[1];
    voodoo->fbiZFuncFail += counts[2];
    voodoo->fbiAFuncFail += counts[3];
    voodoo->fbiPixelsOut += counts[4];
    for (uint32_t i = 0; i < g->count; i++)
        textures_done(voodoo, g->entries[i][0], g->entries[i][1]);
    triangles_drawn += g->count;
    g->count = 0;
    kairo_gpu_pages_clear(&g->pages);
}

void
kairo_voodoo_gpu_drain(voodoo_t *voodoo)
{
    voodoo_gpu_t *g = voodoo->k_gpu;
    if (!kairo_gpu_pages_any(&g->pages))
        return;
    pthread_mutex_lock(&g->lock);
    drain_locked(voodoo, g);
    pthread_mutex_unlock(&g->lock);
}

void
kairo_voodoo_gpu_touch(voodoo_t *voodoo, uint32_t addr, uint32_t len)
{
    voodoo_gpu_t *g = voodoo->k_gpu;
    /* The Banshee's 2D engine's batch too: at most one of the two has work, each drawing the other's first */
    if (voodoo->k2d_touch != NULL)
        voodoo->k2d_touch(voodoo, addr, len);
    if (kairo_gpu_pages_hit(&g->pages, addr, len))
        kairo_voodoo_gpu_drain(voodoo);
}

void
kairo_voodoo_gpu_close(voodoo_t *voodoo)
{
    voodoo_gpu_t *g = voodoo->k_gpu;
    if (g == NULL)
        return;
    kairo_voodoo_gpu_drain(voodoo);
    kairo_gpu_buffer_free(g->tris);
    kairo_gpu_buffer_free(g->counters);
    kairo_gpu_pages_free(&g->pages);
    pthread_mutex_destroy(&g->lock);
    free(g);
    voodoo->k_gpu = NULL;
}

void
kairo_gpu_voodoo_close(void)
{
    /* How many triangles the GPU drew, for the graphics batch (core/test/gpu/compare.py) */
    fprintf(stderr, "kairo-gpu-voodoo: %llu triangles drawn\n", triangles_drawn);
    triangles_drawn = 0;
    kairo_gpu_kernel_free(kernel);
    kairo_gpu_buffer_free(tables);
    kernel = NULL;
    tables = NULL;
}

void
kairo_voodoo_gpu_queue(voodoo_t *voodoo, const voodoo_params_t *params)
{
    voodoo_gpu_t *g = voodoo->k_gpu;

    /* What the CPU's rasteriser stops the PC for, stopped for here as it is queued */
    if (((params->fbzColorPath >> 5) & 3) == 3)
        fatal("Bad cca_localselect %i\n", 3);
    if (((params->fbzColorPath >> 2) & 3) == 3)
        fatal("Bad a_sel %i\n", 3);
    if (((params->fbzColorPath >> 10) & 7) > 5)
        fatal("Bad cc_mselect %i\n", (params->fbzColorPath >> 10) & 7);
    if (((params->fbzColorPath >> 19) & 7) > 4)
        fatal("Bad cca_mselect %i\n", (params->fbzColorPath >> 19) & 7);
    if (((params->fbzColorPath >> 14) & 3) == 3)
        fatal("Bad cc_add %i\n", 3);
    if (SLI_ENABLED)
        fatal("Voodoo on the GPU: SLI is not drawn on the GPU\n");
    if ((params->draw_offset | params->aux_offset | (uint32_t) params->row_width | (uint32_t) params->aux_row_width) & 3)
        fatal("Voodoo on the GPU: buffers not word aligned (draw %08x aux %08x strides %d %d)\n", params->draw_offset,
              params->aux_offset, params->row_width, params->aux_row_width);

    voodoo->tri_count++;

    /* voodoo_triangle()'s setup */
    const int32_t ax = sext16(params->vertexAx), ay = sext16(params->vertexAy);
    const int32_t bx = sext16(params->vertexBx), by = sext16(params->vertexBy);
    const int32_t cx = sext16(params->vertexCx), cy = sext16(params->vertexCy);
    int dx = 8 - (params->vertexAx & 0xf);
    if ((params->vertexAx & 0xf) > 8)
        dx += 16;
    int dy = 8 - (params->vertexAy & 0xf);
    if ((params->vertexAy & 0xf) > 8)
        dy += 16;
    int32_t c[5]   = { (int32_t) params->startR, (int32_t) params->startG, (int32_t) params->startB, (int32_t) params->startA,
                       (int32_t) params->startZ };
    int32_t cdx[5] = { params->dRdX, params->dGdX, params->dBdX, params->dAdX, params->dZdX };
    int32_t cdy[5] = { params->dRdY, params->dGdY, params->dBdY, params->dAdY, params->dZdY };
    int64_t q[7][3] = {
        { params->startW, params->dWdX, params->dWdY },
        { params->tmu[0].startS, params->tmu[0].dSdX, params->tmu[0].dSdY },
        { params->tmu[0].startT, params->tmu[0].dTdX, params->tmu[0].dTdY },
        { params->tmu[0].startW, params->tmu[0].dWdX, params->tmu[0].dWdY },
        { params->tmu[1].startS, params->tmu[1].dSdX, params->tmu[1].dSdY },
        { params->tmu[1].startT, params->tmu[1].dTdX, params->tmu[1].dTdY },
        { params->tmu[1].startW, params->tmu[1].dWdX, params->tmu[1].dWdY },
    };
    if (params->fbzColorPath & FBZ_PARAM_ADJUST) {
        for (int i = 0; i < 5; i++)
            c[i] += (dx * cdx[i] + dy * cdy[i]) >> 4;
        for (int i = 0; i < 7; i++)
            q[i][0] += (dx * q[i][1] + dy * q[i][2]) >> 4;
    }
    int dxAB = 0, dxAC = 0, dxBC = 0;
    if (by - ay)
        dxAB = (int) ((((int64_t) bx << 12) - ((int64_t) ax << 12)) << 4) / (by - ay);
    if (cy - ay)
        dxAC = (int) ((((int64_t) cx << 12) - ((int64_t) ax << 12)) << 4) / (cy - ay);
    if (cy - by)
        dxBC = (int) ((((int64_t) cx << 12) - ((int64_t) bx << 12)) << 4) / (cy - by);

    /* voodoo_half_triangle()'s lines */
    const int y0     = (ay + 7) >> 4;
    int       ystart = y0;
    int       yend   = (cy + 7) >> 4;
    if ((params->fbzMode & 1) && (ystart < params->clipLowY))
        ystart = params->clipLowY;
    if ((params->fbzMode & 1) && (yend >= params->clipHighY))
        yend = params->clipHighY;
    const int y_origin = (voodoo->type >= VOODOO_BANSHEE) ? voodoo->y_origin_swap : (voodoo->v_disp - 1);
    const int flip     = (params->fbzMode & (1 << 17)) != 0;
    int       row_lo   = flip ? (y_origin - (yend - 1)) : ystart;
    int       row_hi   = flip ? (y_origin - ystart) : (yend - 1);
    int       x_lo     = ax, x_hi = ax;
    if (bx < x_lo)
        x_lo = bx;
    if (cx < x_lo)
        x_lo = cx;
    if (bx > x_hi)
        x_hi = bx;
    if (cx > x_hi)
        x_hi = cx;
    x_lo = (x_lo >> 4) - 2;
    x_hi = ((x_hi + 15) >> 4) + 2;
    if (params->fbzMode & 1) {
        if (x_lo < params->clipLeft)
            x_lo = params->clipLeft;
        if (x_hi > params->clipRight - 1)
            x_hi = params->clipRight - 1;
    }
    if (x_lo < 0)
        x_lo = 0;
    if (row_lo < 0)
        row_lo = 0;
    x_lo &= ~1;
    if ((ystart >= yend) || (x_hi < x_lo) || (row_hi < row_lo)) {
        /* No line: drawn at once, as far as the textures go */
        textures_done(voodoo, params->tex_entry[0], params->tex_entry[1]);
        return;
    }

    pthread_mutex_lock(&g->lock);
    const uint32_t tiled = (params->col_tiled ? 1 : 0) | (params->aux_tiled ? 2 : 0);
    if ((g->count != 0)
        && ((g->count == TRIS_MAX) || (params->draw_offset != g->draw_offset) || (params->aux_offset != g->aux_offset)
            || ((uint32_t) params->row_width != g->row_width) || ((uint32_t) params->aux_row_width != g->aux_row_width)
            || (tiled != g->tiled)))
        drain_locked(voodoo, g);
    if (g->count == 0) {
        g->draw_offset   = params->draw_offset;
        g->aux_offset    = params->aux_offset;
        g->row_width     = params->row_width;
        g->aux_row_width = params->aux_row_width;
        g->tiled         = tiled;
        g->row_lo        = row_lo;
        g->row_hi        = row_hi;
        g->x_lo          = x_lo;
        g->x_hi          = x_hi;
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

    uint32_t *r = (uint32_t *) g->tris->data + (size_t) g->count * T_WORDS;
    memset(r, 0, T_WORDS * 4);
    r[T_AX]         = (uint32_t) ax;
    r[T_AX + 1]     = (uint32_t) ay;
    r[T_AX + 2]     = (uint32_t) bx;
    r[T_AX + 3]     = (uint32_t) by;
    r[T_AX + 4]     = (uint32_t) cx;
    r[T_AX + 5]     = (uint32_t) cy;
    r[T_DXAB]       = (uint32_t) dxAB;
    r[T_DXAC]       = (uint32_t) dxAC;
    r[T_DXBC]       = (uint32_t) dxBC;
    r[T_XDIR]       = (uint32_t) (params->sign ? -1 : 1);
    r[T_YSTART]     = (uint32_t) ystart;
    r[T_YEND]       = (uint32_t) yend;
    r[T_Y0]         = (uint32_t) y0;
    r[T_AXR]        = (uint32_t) (((ax << 12) + 0x7000) >> 16);
    r[T_YORIGIN]    = (uint32_t) y_origin;
    r[T_ROWLO]      = (uint32_t) row_lo;
    r[T_ROWHI]      = (uint32_t) row_hi;
    r[T_XLO]        = (uint32_t) x_lo;
    r[T_XHI]        = (uint32_t) x_hi;
    r[T_CLIPL]      = (uint32_t) params->clipLeft;
    r[T_CLIPR]      = (uint32_t) params->clipRight;
    for (int i = 0; i < 5; i++) {
        r[T_C + i]   = (uint32_t) c[i];
        r[T_CDX + i] = (uint32_t) cdx[i];
        r[T_CDY + i] = (uint32_t) cdy[i];
    }
    for (int i = 0; i < 7; i++)
        for (int part = 0; part < 3; part++)
            put64(r, i, part, q[i][part]);
    r[T_FBZMODE]   = params->fbzMode;
    r[T_FBZCP]     = params->fbzColorPath;
    r[T_FOGMODE]   = params->fogMode;
    r[T_ALPHAMODE] = params->alphaMode;
    r[T_ZACOLOR]   = params->zaColor;
    r[T_COLOR0]    = params->color0;
    r[T_COLOR1]    = params->color1;
    r[T_FOGCOLOR]  = params->fogColor.b | (params->fogColor.g << 8) | (params->fogColor.r << 16);
    r[T_CHROMA]    = (params->chromaKey_b & 0xff) | ((params->chromaKey_g & 0xff) << 8) | ((params->chromaKey_r & 0xff) << 16);
    r[T_STIPPLE]   = params->stipple;
    r[T_TMUCONFIG] = voodoo->tmuConfig;
    r[T_ODDEVEN]   = (uint32_t) (voodoo->odd_even_mask & 0xff) | ((uint32_t) voodoo->render_threads << 8);
    for (int tmu = 0; tmu < 2; tmu++) {
        r[T_TEXMODE + tmu] = params->textureMode[tmu];
        r[T_TLOD + tmu]    = params->tLOD[tmu];
        r[T_ENTRY + tmu]   = (uint32_t) params->tex_entry[tmu];
        int lod_max        = ((params->tLOD[tmu] >> 6) & 0x3f) << 6;
        r[T_LODMIN + tmu]  = (uint32_t) ((params->tLOD[tmu] & 0x3f) << 6);
        r[T_LODMAX + tmu]  = (uint32_t) ((lod_max > 0x800) ? 0x800 : lod_max);
        const int base     = triangle_lod_base(params, tmu);
        const int bias     = lod_bias(params, tmu);
        r[T_LODTRI + tmu]  = (uint32_t) (base + bias);
        r[T_LODBASE + tmu] = (uint32_t) base;
        r[T_LODBIAS + tmu] = (uint32_t) bias;
        r[T_DMAX + tmu]    = (uint32_t) params->detail_max[tmu];
        r[T_DBIAS + tmu]   = (uint32_t) params->detail_bias[tmu];
        r[T_DSCALE + tmu]  = (uint32_t) params->detail_scale[tmu];
        for (int lod = 0; lod <= LOD_MAX; lod++)
            r[T_MASKS + tmu * 9 + lod] = ((uint32_t) params->tex_w_mask[tmu][lod] & 0x3ff) | (((uint32_t) params->tex_h_mask[tmu][lod] & 0x3ff) << 10)
                                         | ((uint32_t) params->tex_lod[tmu][lod] << 20);
    }
    for (int i = 0; i < 32; i++)
        r[T_FOG + i] = params->fogTable[i * 2].fog | (params->fogTable[i * 2].dfog << 8) | (params->fogTable[i * 2 + 1].fog << 16)
                       | (params->fogTable[i * 2 + 1].dfog << 24);
    r[T_ENTRY_WORDS] = ENTRY_WORDS;
    uint32_t flags   = 0;
    if ((params->fbzColorPath & FBZCP_TEXTURE_ENABLED)
        && ((params->textureMode[0] & TEXTUREMODE_TPERSP_ST) || (voodoo->dual_tmus && (params->textureMode[1] & TEXTUREMODE_TPERSP_ST))))
        flags |= F_SPAN_PART;
    if (voodoo->dual_tmus)
        flags |= F_DUAL_TMUS;
    if (voodoo->bilinear_enabled)
        flags |= F_BILINEAR;
    if (voodoo->dithersub_enabled)
        flags |= F_DITHERSUB;
    if (voodoo->trexInit1[0] & (1 << 18))
        flags |= F_TREX_OVERRIDE;
    r[T_FLAGS] = flags;
    g->entries[g->count][0] = (int16_t) params->tex_entry[0];
    g->entries[g->count][1] = (int16_t) params->tex_entry[1];
    g->count++;

    /* The memory it draws on, the display's line marks (voodoo_half_triangle's, at its lines) */
    for (int row = row_lo; row <= row_hi; row++) {
        const uint32_t crow = params->col_tiled ? (params->draw_offset + (row >> 5) * params->row_width + (row & 31) * 128)
                                                : (params->draw_offset + row * params->row_width);
        const uint32_t arow = params->aux_tiled ? (params->aux_offset + (row >> 5) * params->aux_row_width + (row & 31) * 128)
                                                : (params->aux_offset + row * params->row_width);
        mark_pages(g, crow, params->col_tiled, x_lo, x_hi);
        mark_pages(g, arow, params->aux_tiled, x_lo, x_hi);
        if ((voodoo->params.draw_offset == voodoo->params.front_offset) && (row < 2048))
            voodoo->dirty_line[row] = 1;
        if (params->fbzMode & FBZ_RGB_WMASK)
            voodoo_mark_changed(voodoo, crow, params->col_tiled, x_lo, x_hi);
    }
    pthread_mutex_unlock(&g->lock);
}
