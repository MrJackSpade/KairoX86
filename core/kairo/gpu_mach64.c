/*
 * The ATI 3D Rage II+'s 3D engine on the GPU (KairoX86#237; 86box/kairo_gpu_mach64.h): the batch of recorded rows
 * with their draws' records, the video memory they draw on and read (page maps), and its drain through
 * shaders/mach64.comp.
 *
 * A batch is drawn one of two ways:
 * - in parallel: every invocation owns four pixels of one line of the destination (and their depth), and runs
 *   through the rows on its line in the order they were recorded. Its draws share one destination and one depth
 *   buffer, so the four pixels' memory is the same words for the whole batch; a texture read from what the batch
 *   draws on draws the batch first.
 * - in order: one invocation draws every row pixel by pixel as mach64_3d_draw_row does, for the draws whose pixels
 *   depend on the pixels before them: X error diffusion (its error runs on from pixel to pixel and row to row), or
 *   a draw whose rows, depth buffer or texture share memory with each other.
 * A draw of the other way draws the batch first.
 *
 * The X error diffusion's state lives in a buffer the kernel carries from batch to batch: the card's copy goes to
 * it when a batch starts and comes back when it is drawn, for the scaler and anything else drawing on the CPU.
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
#include <86box/kairo_gpu_mach64.h>

#include "gpu_internal.h"

static const uint32_t mach64_spirv[] = {
#include "mach64.comp.inc"
};

#define DRAWS_MAX    16384
#define ROWS_MAX     65536
#define PALETTES_MAX 256
#define LINES_MAX    32768 /* DST_Y is 15 bits */

/* SCALE_3D_CNTL */
#define DITHER_EN    (1u << 2)
#define SCALE_DITHER (1u << 1)

typedef struct {
    pthread_mutex_t     lock;
    kairo_gpu_buffer_t *draws;
    kairo_gpu_buffer_t *rows;
    kairo_gpu_buffer_t *lists;
    kairo_gpu_buffer_t *palettes;
    kairo_gpu_buffer_t *vram;
    kairo_gpu_buffer_t *state;
    uint32_t            vram_mask;
    int32_t            *dither;
    uint32_t            draw_count;
    uint32_t            row_count;
    uint32_t            palette_count;
    bool                in_order;
    /* A parallel batch's destination and depth buffer, and the bytes its rows draw on in each */
    uint32_t dst_base, dst_pitch, dst_bpp;
    bool     z_set;
    uint32_t z_base, z_pitch;
    uint64_t dst_lo, dst_hi, z_lo, z_hi;
    int      y_lo, y_hi, x_lo, x_hi;
    /* The pages the batch draws on, and those it draws on or reads */
    kairo_gpu_pages_t writes;
    kairo_gpu_pages_t touched;
} mach64_gpu_t;

static kairo_gpu_kernel_t *kernel;
static unsigned long long  draws_drawn;

void *
kairo_mach64_gpu_open(uint8_t *vram, uint32_t vram_mask, int32_t *dither)
{
    mach64_gpu_t *g = calloc(1, sizeof(mach64_gpu_t));
    if (g == NULL)
        fatal("Mach64 3D on the GPU: no memory\n");
    pthread_mutex_init(&g->lock, NULL);
    g->draws     = kairo_gpu_buffer((size_t) DRAWS_MAX * KM_WORDS * 4);
    g->rows      = kairo_gpu_buffer((size_t) ROWS_MAX * KR_WORDS * 4);
    g->lists     = kairo_gpu_buffer((size_t) (LINES_MAX + 1 + ROWS_MAX) * 4);
    g->palettes  = kairo_gpu_buffer((size_t) PALETTES_MAX * KAIRO_M64_PALETTE_WORDS * 4);
    g->state     = kairo_gpu_buffer(8 * 4);
    g->vram      = kairo_gpu_buffer_of(vram);
    g->vram_mask = vram_mask;
    g->dither    = dither;
    kairo_gpu_pages_init(&g->writes, vram_mask);
    kairo_gpu_pages_init(&g->touched, vram_mask);
    return g;
}

/* The rows on each line, in order: the lines' first indices (one past the last line's end too), then the indices */
static void
build_lists(mach64_gpu_t *g)
{
    uint32_t      *lists = g->lists->data;
    const uint32_t lines = (uint32_t) (g->y_hi - g->y_lo + 1);
    const uint32_t *rows = g->rows->data;

    memset(lists, 0, (lines + 1) * 4);
    for (uint32_t i = 0; i < g->row_count; i++)
        lists[(uint32_t) ((int) rows[i * KR_WORDS + KR_Y] - g->y_lo) + 1]++;
    for (uint32_t l = 0; l < lines; l++)
        lists[l + 1] += lists[l];
    uint32_t *next = calloc(lines, 4);
    if (next == NULL)
        fatal("Mach64 3D on the GPU: no memory\n");
    for (uint32_t i = 0; i < g->row_count; i++) {
        const uint32_t l = (uint32_t) ((int) rows[i * KR_WORDS + KR_Y] - g->y_lo);
        lists[lines + 1 + lists[l] + next[l]++] = i;
    }
    free(next);
}

static void
drain_locked(mach64_gpu_t *g)
{
    if (g->draw_count == 0)
        return;
    if (kernel == NULL)
        kernel = kairo_gpu_kernel("mach64", mach64_spirv, sizeof(mach64_spirv), 6, 8 * 4);

    uint32_t groups_x = 1;
    uint32_t groups_y = 1;
    uint32_t columns  = 0;
    uint32_t lines    = 0;
    if (!g->in_order) {
        build_lists(g);
        columns  = (uint32_t) ((g->x_hi >> 2) - (g->x_lo >> 2) + 1);
        lines    = (uint32_t) (g->y_hi - g->y_lo + 1);
        groups_x = (columns + 15) / 16;
        groups_y = (lines + 3) / 4;
    }
    const uint32_t push[8] = { g->row_count, g->vram_mask, (uint32_t) (g->x_lo >> 2), (uint32_t) g->y_lo, lines, columns,
                               g->in_order ? 1u : 0u, 0 };
    kairo_gpu_buffer_t *const buffers[6] = { g->draws, g->rows, g->lists, g->palettes, g->vram, g->state };
    kairo_gpu_run(kernel, buffers, push, groups_x, groups_y, 1);
    memcpy(g->dither, g->state->data, 5 * 4);

    draws_drawn += g->draw_count;
    g->draw_count    = 0;
    g->row_count     = 0;
    g->palette_count = 0;
    kairo_gpu_pages_clear(&g->writes);
    kairo_gpu_pages_clear(&g->touched);
}

void
kairo_mach64_gpu_drain(void *gpu)
{
    mach64_gpu_t *g = gpu;
    if (!kairo_gpu_pages_any(&g->touched))
        return;
    pthread_mutex_lock(&g->lock);
    drain_locked(g);
    pthread_mutex_unlock(&g->lock);
}

void
kairo_mach64_gpu_touch(void *gpu, uint32_t addr, uint32_t len)
{
    mach64_gpu_t *g = gpu;
    if (kairo_gpu_pages_hit(&g->touched, addr, len))
        kairo_mach64_gpu_drain(gpu);
}

void
kairo_mach64_gpu_close(void *gpu)
{
    mach64_gpu_t *g = gpu;
    if (g == NULL)
        return;
    pthread_mutex_lock(&g->lock);
    drain_locked(g);
    pthread_mutex_unlock(&g->lock);
    kairo_gpu_buffer_free(g->draws);
    kairo_gpu_buffer_free(g->rows);
    kairo_gpu_buffer_free(g->lists);
    kairo_gpu_buffer_free(g->palettes);
    kairo_gpu_buffer_free(g->state);
    kairo_gpu_pages_free(&g->writes);
    kairo_gpu_pages_free(&g->touched);
    pthread_mutex_destroy(&g->lock);
    free(g);
}

void
kairo_gpu_mach64_close(void)
{
    /* How many draws the GPU drew, for the graphics batch (core/test/gpu/compare.py) */
    fprintf(stderr, "kairo-gpu-mach64: %llu draws drawn\n", draws_drawn);
    draws_drawn = 0;
    kairo_gpu_kernel_free(kernel);
    kernel = NULL;
}

/* Whether two runs of video memory share a byte, each wrapping at its end (mach64_3d_ranges_overlap) */
static bool
ranges_overlap(uint64_t a, uint64_t a_len, uint64_t b, uint64_t b_len, uint64_t size)
{
    a %= size;
    b %= size;
    const uint64_t a_to_b = (b >= a) ? (b - a) : (b + size - a);
    const uint64_t b_to_a = (a >= b) ? (a - b) : (a + size - b);
    return (a_to_b < a_len) || (b_to_a < b_len);
}

/* The memory a record's pixels read besides their own: its texture maps (each as mach64_3d_rows_shared counts its
   bytes), or a scaled rectangle's source; how many runs */
static int
reads_of(const uint32_t *record, uint64_t base[11], uint64_t len[11])
{
    if (record[KM_FLAGS] & KAIRO_M64_SCALER) {
        const uint32_t format = record[KS_SRC_FORMAT];
        const uint64_t bpp    = ((format == 2) || (format == 7) || (format == 8)) ? 1
                                : ((format == 6) || (format == 14))             ? 4
                                                                                : 2;
        base[0] = record[KS_SRC_BASE];
        len[0]  = ((uint64_t) (record[KS_SRC_HEIGHT] - 1) * record[KS_SRC_PITCH] + record[KS_SRC_WIDTH]) * bpp + 4;
        return 1;
    }
    const int levels = (int) record[KM_LEVELS];
    for (int level = 0; level < levels; level++) {
        const uint32_t *map = record + KM_MAPS + level * KM_MAP_WORDS;
        base[level]         = map[KM_MAP_BASE];
        len[level]          = ((uint64_t) 1 << (map[KM_MAP_PITCH_LOG2] + map[KM_MAP_HEIGHT_LOG2])) * record[KM_TEX_BPP] + 4;
    }
    return levels;
}

void
kairo_mach64_gpu_draw(void *gpu, const uint32_t *record, const uint32_t *palettes, const uint32_t *rows, int count)
{
    mach64_gpu_t  *g      = gpu;
    const uint32_t flags  = record[KM_FLAGS];
    const uint32_t cntl   = record[KM_CNTL];
    const uint64_t size   = (uint64_t) g->vram_mask + 1;
    const uint32_t bpp    = record[KM_DST_BPP];
    const uint32_t pitch  = record[KM_DST_PITCH];
    const bool     z_on   = (flags & KAIRO_M64_Z_ENABLED) != 0;
    uint64_t       read_base[11];
    uint64_t       read_len[11];
    const int      reads  = reads_of(record, read_base, read_len);

    if (count <= 0)
        return;

    int y_min = (int) rows[KR_Y];
    int y_max = y_min;
    int x_min = (int) rows[KR_FIRST];
    int x_max = (int) rows[KR_END];
    for (int i = 1; i < count; i++) {
        const uint32_t *row = rows + (size_t) i * KR_WORDS;
        if ((int) row[KR_Y] < y_min)
            y_min = (int) row[KR_Y];
        if ((int) row[KR_Y] > y_max)
            y_max = (int) row[KR_Y];
        if ((int) row[KR_FIRST] < x_min)
            x_min = (int) row[KR_FIRST];
        if ((int) row[KR_END] > x_max)
            x_max = (int) row[KR_END];
    }
    if ((y_min < 0) || (x_min < 0) || (y_max >= LINES_MAX))
        fatal("Mach64 3D on the GPU: a row at %d, %d\n", x_min, y_min);

    /* The bytes it draws on, as mach64_3d_rows_shared counts them */
    const uint64_t dst_start = record[KM_DST_BASE] + ((uint64_t) y_min * pitch + (uint64_t) x_min) * bpp;
    const uint64_t dst_len   = ((uint64_t) (y_max - y_min) * pitch + (uint64_t) (x_max - x_min)) * bpp;
    const uint64_t z_start   = record[KM_Z_BASE] + ((uint64_t) y_min * record[KM_Z_PITCH] + (uint64_t) x_min) * 2;
    const uint64_t z_len     = ((uint64_t) (y_max - y_min) * record[KM_Z_PITCH] + (uint64_t) (x_max - x_min)) * 2;

    /* In order: X error diffusion, or memory that would make one invocation's pixels another's */
    bool in_order = ((cntl & DITHER_EN) && !(cntl & SCALE_DITHER)) || (dst_start + dst_len > size);
    if (z_on && (((uint64_t) x_max > record[KM_Z_PITCH]) || (z_start + z_len > size)
                 || ranges_overlap(dst_start, dst_len, z_start, z_len, size)))
        in_order = true;
    for (int i = 0; i < reads; i++)
        if ((read_len[i] >= size) || ranges_overlap(read_base[i], read_len[i], dst_start, dst_len, size)
            || ((flags & KAIRO_M64_Z_WRITE) && ranges_overlap(read_base[i], read_len[i], z_start, z_len, size)))
            in_order = true;

    pthread_mutex_lock(&g->lock);
    uint32_t  *pool        = g->palettes->data;
    const bool new_palette = (g->palette_count == 0)
                             || memcmp(pool + (size_t) (g->palette_count - 1) * KAIRO_M64_PALETTE_WORDS, palettes,
                                       KAIRO_M64_PALETTE_WORDS * 4);
    if (g->draw_count != 0) {
        bool first = (g->in_order != in_order) || (g->draw_count == DRAWS_MAX) || (g->row_count + (uint32_t) count > ROWS_MAX)
                     || (new_palette && (g->palette_count == PALETTES_MAX));
        if (!first && !in_order) {
            /* One destination and depth buffer, apart from each other across the batch, and no texture read
               from what it draws on */
            first = (record[KM_DST_BASE] != g->dst_base) || (pitch != g->dst_pitch) || (bpp != g->dst_bpp)
                    || (z_on && g->z_set && ((record[KM_Z_BASE] != g->z_base) || (record[KM_Z_PITCH] != g->z_pitch)));
            if (!first && z_on && g->z_set) {
                const uint64_t d_lo = (dst_start < g->dst_lo) ? dst_start : g->dst_lo;
                const uint64_t d_hi = ((dst_start + dst_len) > g->dst_hi) ? (dst_start + dst_len) : g->dst_hi;
                const uint64_t z_lo = (z_start < g->z_lo) ? z_start : g->z_lo;
                const uint64_t z_hi = ((z_start + z_len) > g->z_hi) ? (z_start + z_len) : g->z_hi;
                first = (d_lo < z_hi) && (z_lo < d_hi);
            } else if (!first && z_on) {
                first = (z_start < g->dst_hi) && (g->dst_lo < z_start + z_len);
            } else if (!first && g->z_set) {
                first = (dst_start < g->z_hi) && (g->z_lo < dst_start + dst_len);
            }
            for (int i = 0; !first && (i < reads); i++)
                first = kairo_gpu_pages_hit(&g->writes, (uint32_t) read_base[i] & g->vram_mask, (uint32_t) read_len[i]);
        }
        if (first)
            drain_locked(g);
    }

    if (g->draw_count == 0) {
        g->in_order  = in_order;
        g->dst_base  = record[KM_DST_BASE];
        g->dst_pitch = pitch;
        g->dst_bpp   = bpp;
        g->z_set     = false;
        g->dst_lo    = dst_start;
        g->dst_hi    = dst_start + dst_len;
        g->y_lo      = y_min;
        g->y_hi      = y_max;
        g->x_lo      = x_min;
        g->x_hi      = x_max - 1;
        memcpy(g->state->data, g->dither, 5 * 4);
    } else {
        if (dst_start < g->dst_lo)
            g->dst_lo = dst_start;
        if (dst_start + dst_len > g->dst_hi)
            g->dst_hi = dst_start + dst_len;
        if (y_min < g->y_lo)
            g->y_lo = y_min;
        if (y_max > g->y_hi)
            g->y_hi = y_max;
        if (x_min < g->x_lo)
            g->x_lo = x_min;
        if (x_max - 1 > g->x_hi)
            g->x_hi = x_max - 1;
    }
    if (z_on) {
        if (!g->z_set) {
            g->z_set   = true;
            g->z_base  = record[KM_Z_BASE];
            g->z_pitch = record[KM_Z_PITCH];
            g->z_lo    = z_start;
            g->z_hi    = z_start + z_len;
        } else {
            if (z_start < g->z_lo)
                g->z_lo = z_start;
            if (z_start + z_len > g->z_hi)
                g->z_hi = z_start + z_len;
        }
    }

    /* Its palettes: the last ones again where they are the same (a drain empties the pool) */
    if (new_palette || (g->palette_count == 0)) {
        memcpy(pool + (size_t) g->palette_count * KAIRO_M64_PALETTE_WORDS, palettes, KAIRO_M64_PALETTE_WORDS * 4);
        g->palette_count++;
    }

    uint32_t *draw = (uint32_t *) g->draws->data + (size_t) g->draw_count * KM_WORDS;
    memcpy(draw, record, KM_WORDS * 4);
    draw[KM_PALETTE] = g->palette_count - 1;
    uint32_t *out = (uint32_t *) g->rows->data + (size_t) g->row_count * KR_WORDS;
    memcpy(out, rows, (size_t) count * KR_WORDS * 4);
    for (int i = 0; i < count; i++) {
        uint32_t *row = out + (size_t) i * KR_WORDS;
        row[KR_DRAW]  = g->draw_count;
        const uint32_t y     = row[KR_Y];
        const uint32_t first = row[KR_FIRST];
        const uint32_t n     = row[KR_END] - first;
        const uint32_t d     = record[KM_DST_BASE] + (y * pitch + first) * bpp;
        kairo_gpu_pages_mark(&g->writes, d & g->vram_mask, n * bpp);
        kairo_gpu_pages_mark(&g->touched, d & g->vram_mask, n * bpp);
        if (z_on) {
            const uint32_t z = record[KM_Z_BASE] + (y * record[KM_Z_PITCH] + first) * 2;
            if (flags & KAIRO_M64_Z_WRITE)
                kairo_gpu_pages_mark(&g->writes, z & g->vram_mask, n * 2);
            kairo_gpu_pages_mark(&g->touched, z & g->vram_mask, n * 2);
        }
    }
    for (int i = 0; i < reads; i++)
        kairo_gpu_pages_mark(&g->touched, (uint32_t) read_base[i] & g->vram_mask, (uint32_t) read_len[i]);
    g->draw_count++;
    g->row_count += (uint32_t) count;
    pthread_mutex_unlock(&g->lock);
}
