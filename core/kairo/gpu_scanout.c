/*
 * The scanout on the GPU (KairoX86#233, 86box/kairo_gpu.h): the queue of lines the cards' renderers
 * take as the guest scans them, and the kernel (shaders/scanout.comp) that draws them at the drain.
 *
 * The queue fills from its start after every drain: records, the dwords they captured and their
 * palettes, each a GPU buffer the CPU writes as the guest scans and the kernel reads at the drain.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <pthread.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include <86box/86box.h>
#include <86box/kairo_gpu.h>

#include "gpu_internal.h"

_Static_assert(sizeof(kairo_gpu_scan_t) == 64, "kairo_gpu_scan_t's size changed: shaders/scanout.comp reads it");

static const uint32_t scanout_spirv[] = {
#include "scanout.comp.inc"
};

#define LINES       8192
#define WORDS       (4u << 20) /* 16 MB of captured dwords */
#define PALETTES    1024
#define TABLE_BYTES (65536 * sizeof(uint32_t))

static kairo_gpu_kernel_t *scanout;
static kairo_gpu_buffer_t *lines;
static kairo_gpu_buffer_t *words;
static kairo_gpu_buffer_t *palettes;
static kairo_gpu_buffer_t *table15;
static kairo_gpu_buffer_t *table16;

static uint32_t            line_count;
static uint32_t            words_used;
static uint32_t            palettes_used;
static const void         *queued_bitmap; /* the queued lines' bitmap, and its buffer */
static kairo_gpu_buffer_t *queued_bitmap_gpu;
static uint32_t            queued_out;    /* the last queued line's first pixel */
static uint32_t            queued_end;    /* the end of the queued pixels furthest on (they come in order) */
static unsigned long long  lines_drawn;   /* every line the GPU drew this machine, reported at its end */
/* Held from kairo_gpu_scan to kairo_gpu_scan_commit, and by a drain */
static pthread_mutex_t queue_lock = PTHREAD_MUTEX_INITIALIZER;

void
kairo_gpu_scan_tables(const uint32_t *t15, const uint32_t *t16)
{
    if (table15 != NULL)
        return;
    table15 = kairo_gpu_buffer(TABLE_BYTES);
    table16 = kairo_gpu_buffer(TABLE_BYTES);
    memcpy(table15->data, t15, TABLE_BYTES);
    memcpy(table16->data, t16, TABLE_BYTES);
}

/* The drain, with the queue locked */
static void
drain_locked(void)
{
    if (line_count == 0)
        return;
    if (table15 == NULL)
        fatal("GPU scanout: drawn before 86Box's colour tables were given\n");
    if (scanout == NULL)
        scanout = kairo_gpu_kernel("scanout", scanout_spirv, sizeof(scanout_spirv), 6, 4);
    kairo_gpu_buffer_t *const buffers[6] = { lines, words, palettes, table15, table16, queued_bitmap_gpu };
    const uint32_t            unused     = 0;
    kairo_gpu_run(scanout, buffers, &unused, line_count, 1, 1);
    lines_drawn += line_count;
    line_count    = 0;
    words_used    = 0;
    palettes_used = 0;
}

void
kairo_gpu_scan_drain(void)
{
    pthread_mutex_lock(&queue_lock);
    drain_locked();
    pthread_mutex_unlock(&queue_lock);
}

void
kairo_gpu_scan_forget(const void *bitmap)
{
    pthread_mutex_lock(&queue_lock);
    if ((line_count != 0) && (queued_bitmap == bitmap))
        drain_locked();
    if (queued_bitmap == bitmap)
        queued_bitmap = NULL;
    pthread_mutex_unlock(&queue_lock);
}

void
kairo_gpu_scan_touch(const void *bitmap, uint32_t start, uint32_t count)
{
    pthread_mutex_lock(&queue_lock);
    /* The lines come in order: pixels past the last queued one's end touch none (the usual case, the
       CPU drawing the line about to be queued) */
    if ((line_count != 0) && (queued_bitmap == bitmap) && (start < queued_end)) {
        const kairo_gpu_scan_t *queued = lines->data;
        for (uint32_t i = 0; i < line_count; i++)
            if ((queued[i].out < (start + count)) && (start < (queued[i].out + queued[i].count))) {
                drain_locked();
                break;
            }
    }
    pthread_mutex_unlock(&queue_lock);
}

void
kairo_gpu_scan_cut(const void *bitmap, uint32_t start, uint32_t count)
{
    pthread_mutex_lock(&queue_lock);
    if ((line_count != 0) && (queued_bitmap == bitmap)) {
        kairo_gpu_scan_t *queued = lines->data;
        const uint32_t    end    = start + count;
        for (uint32_t i = 0; i < line_count; i++) {
            const uint32_t from = queued[i].out + queued[i].skip;
            const uint32_t to   = queued[i].out + queued[i].count;
            if ((end <= from) || (start >= to))
                continue;
            if ((start <= from) && (end >= to))
                queued[i].count = queued[i].skip; /* all of it drawn over */
            else if (start <= from)
                queued[i].skip = end - queued[i].out; /* its head */
            else if (end >= to)
                queued[i].count = start - queued[i].out; /* its tail */
            else {
                /* Its middle: the line split in two, its head here and its tail queued after it */
                if (line_count == LINES)
                    fatal("GPU scanout: no room to split a line the CPU drew over\n");
                queued[line_count]      = queued[i];
                queued[line_count].skip = end - queued[i].out;
                queued[i].count         = start - queued[i].out;
                line_count++;
            }
        }
    }
    pthread_mutex_unlock(&queue_lock);
}

void
kairo_gpu_scan_patch(const void *bitmap, uint32_t start, uint32_t count, const uint32_t *ax, uint32_t key, uint32_t key_mask,
                     uint32_t *from, uint32_t *to)
{
    *from = *to = start;
    pthread_mutex_lock(&queue_lock);
    if ((line_count != 0) && (queued_bitmap == bitmap)) {
        kairo_gpu_scan_t *queued = lines->data;
        /* The last queued line over these pixels: the one drawn last */
        for (uint32_t i = line_count; i-- > 0;) {
            kairo_gpu_scan_t *line = &queued[i];
            const uint32_t    lo   = (start > line->out + line->skip) ? start : line->out + line->skip;
            const uint32_t    hi   = ((start + count) < (line->out + line->count)) ? (start + count) : (line->out + line->count);
            if (lo >= hi)
                continue;
            if (line->patch_count != 0)
                fatal("GPU scanout: a second patch over one line\n");
            if ((words_used + KAIRO_PATCH_WORDS * (hi - lo)) > WORDS)
                fatal("GPU scanout: no room for a patch of %u pixels\n", (unsigned) (hi - lo));
            memcpy((uint32_t *) words->data + words_used, &ax[KAIRO_PATCH_WORDS * (lo - start)], KAIRO_PATCH_WORDS * (hi - lo) * 4);
            line->patch_from  = lo - line->out;
            line->patch_count = hi - lo;
            line->patch_src      = words_used;
            line->patch_key      = key;
            line->patch_key_mask = key_mask;
            words_used += KAIRO_PATCH_WORDS * (hi - lo);
            *from = lo;
            *to   = hi;
            break;
        }
    }
    pthread_mutex_unlock(&queue_lock);
}

void
kairo_gpu_scan_commit(void)
{
    pthread_mutex_unlock(&queue_lock);
}

uint32_t *
kairo_gpu_scan(const void *bitmap, kairo_gpu_buffer_t *bitmap_gpu, uint32_t out, uint32_t kind, uint32_t count,
               uint32_t word_count, const uint32_t *palette, uint32_t palette_count, uint32_t a, uint32_t b,
               uint32_t flags)
{
    if (bitmap_gpu == NULL)
        fatal("GPU scanout: a line for a bitmap the GPU does not share\n");
    if ((word_count > WORDS) || (palette_count > 256))
        fatal("GPU scanout: a line of %u dwords and %u colours\n", (unsigned) word_count, (unsigned) palette_count);
    pthread_mutex_lock(&queue_lock);
    if (lines == NULL) {
        lines    = kairo_gpu_buffer(sizeof(kairo_gpu_scan_t) * LINES);
        words    = kairo_gpu_buffer(WORDS * 4);
        palettes = kairo_gpu_buffer(PALETTES * 256 * 4);
    }
    /* Out of order (a new frame, another bitmap), or no room: the queued lines first */
    if ((line_count != 0)
        && ((bitmap != queued_bitmap) || (out <= queued_out) || (line_count == LINES)
            || ((words_used + word_count) > WORDS) || ((palette != NULL) && (palettes_used == PALETTES))))
        drain_locked();
    if ((line_count == 0) || (bitmap != queued_bitmap) || ((out + count) > queued_end))
        queued_end = out + count;
    queued_bitmap     = bitmap;
    queued_bitmap_gpu = bitmap_gpu;
    queued_out        = out;

    uint32_t index = 0;
    if (palette != NULL) {
        uint32_t *kept = palettes->data;
        /* Kept once while it stays the same */
        if ((palettes_used == 0) || memcmp(&kept[(palettes_used - 1) * 256], palette, palette_count * 4)) {
            memcpy(&kept[palettes_used * 256], palette, palette_count * 4);
            palettes_used++;
        }
        index = palettes_used;
    }
    kairo_gpu_scan_t *line = (kairo_gpu_scan_t *) lines->data + line_count++;
    line->out              = out;
    line->kind             = kind;
    line->count            = count;
    line->src              = words_used;
    line->palette          = index;
    line->a                = a;
    line->skip             = b;
    line->flags            = flags;
    line->patch_from       = 0;
    line->patch_count      = 0;
    line->patch_src        = 0;
    line->patch_key        = 0;
    line->patch_key_mask   = 0;
    memset(line->reserved, 0, sizeof(line->reserved));
    uint32_t *at           = (uint32_t *) words->data + words_used;
    words_used += word_count;
    return at;
}

void
kairo_gpu_scanout_close(void)
{
    /* How much the GPU drew, for the graphics batch (core/test/gpu/compare.py reports it per card) */
    fprintf(stderr, "kairo-gpu: %llu lines drawn\n", lines_drawn);
    lines_drawn = 0;
    kairo_gpu_kernel_free(scanout);
    kairo_gpu_buffer_free(lines);
    kairo_gpu_buffer_free(words);
    kairo_gpu_buffer_free(palettes);
    kairo_gpu_buffer_free(table15);
    kairo_gpu_buffer_free(table16);
    scanout = NULL;
    lines = words = palettes = table15 = table16 = NULL;
    line_count = words_used = palettes_used = 0;
    queued_bitmap     = NULL;
    queued_bitmap_gpu = NULL;
    queued_out        = 0;
}
