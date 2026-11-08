/*
 * Runs of pixels on the drawing engines' shared batches (86box/kairo_gpu_seg.h; KairoX86#232): for an engine whose
 * walk stays the CPU's and whose every destination pixel (1 to 4 bytes) carries its own inputs (the ET4000/W32's,
 * the Cirrus GD54xx's, the B69000's), the pixels the walk draws one after the other along memory go in as one
 * segment, each with its card's stream words, and the memory each pixel reads is tracked so the run is drawn in order
 * where it reads what it draws or its pixels cross a word, and the batch first where the run reads what the batch
 * draws or draws what it reads.
 *
 * A run is locked (recursively: a drain inside its flush calls the flush again), as an engine may walk on its own
 * thread while the machine's drains the batch. The batch's lock is only ever taken after a run's, never held while
 * taking one: kairo_seg_drain calls the flush before it locks.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <pthread.h>

#include <86box/86box.h>
#include <86box/kairo_gpu_seg.h>

struct kairo_seg_run {
    pthread_mutex_t lock;
    kairo_seg_t *seg;
    uint32_t     words_per, max, reads, vram_mask, pixel_bytes;
    void       (*op)(void *ctx, bool in_order);
    void        *ctx;
    uint32_t     start; /* the run's first pixel's first byte */
    int          dir;
    uint32_t     count;
    uint32_t    *words;
    uint32_t     lo[KAIRO_SEG_RUN_READS], hi[KAIRO_SEG_RUN_READS]; /* each read slot's bytes [lo, hi), lo = hi none */
};

static void
run_flush_cb(void *ctx)
{
    kairo_seg_run_flush((kairo_seg_run_t *) ctx);
}

/* The run freed by its batch's close (kairo_seg_close), after the batch's last drain flushed it */
static void
run_close_cb(void *ctx)
{
    kairo_seg_run_t *r = (kairo_seg_run_t *) ctx;

    pthread_mutex_destroy(&r->lock);
    free(r->words);
    free(r);
}

/* Whether the run's pixels not yet in the batch draw or read any of len bytes at addr */
static bool
run_open_cb(void *ctx, uint32_t addr, uint32_t len)
{
    kairo_seg_run_t *r   = (kairo_seg_run_t *) ctx;
    bool             hit = false;

    /* Between the engine's operations every run is in the batch: the processor's accesses take no lock */
    if (__atomic_load_n(&r->count, __ATOMIC_RELAXED) == 0)
        return false;
    pthread_mutex_lock(&r->lock);
    if (r->count != 0) {
        const uint32_t pb   = r->pixel_bytes;
        const uint32_t d_lo = (r->dir > 0) ? r->start : (r->start - (r->count - 1) * pb);
        hit                 = (addr < d_lo + r->count * pb) && (d_lo < addr + len);
        for (uint32_t k = 0; !hit && (k < r->reads); k++)
            hit = (r->lo[k] != r->hi[k]) && (addr < r->hi[k]) && (r->lo[k] < addr + len);
    }
    pthread_mutex_unlock(&r->lock);
    return hit;
}

kairo_seg_run_t *
kairo_seg_run_open(kairo_seg_t *seg, uint32_t vram_mask, uint32_t pixel_bytes, uint32_t words_per, uint32_t reads,
                   void (*op)(void *ctx, bool in_order), void *ctx)
{
    kairo_seg_run_t *r = calloc(1, sizeof(kairo_seg_run_t));
    if ((r == NULL) || (reads > KAIRO_SEG_RUN_READS) || (pixel_bytes < 1) || (pixel_bytes > 4))
        fatal("A run of pixels on the GPU: no memory, %u read slots or %u bytes a pixel\n", reads, pixel_bytes);
    r->pixel_bytes = pixel_bytes;
    r->seg       = seg;
    r->vram_mask = vram_mask;
    r->words_per = words_per;
    r->max       = 4096;
    r->reads     = reads;
    r->op        = op;
    r->ctx       = ctx;
    r->words     = malloc((size_t) r->max * words_per * 4);
    pthread_mutexattr_t attr;
    pthread_mutexattr_init(&attr);
    pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_RECURSIVE);
    pthread_mutex_init(&r->lock, &attr);
    pthread_mutexattr_destroy(&attr);
    if (r->words == NULL)
        fatal("A run of pixels on the GPU: no memory\n");
    kairo_seg_add_flush(seg, run_flush_cb, run_open_cb, run_close_cb, r);
    return r;
}

void
kairo_seg_run_flush(kairo_seg_run_t *r)
{
    pthread_mutex_lock(&r->lock);
    const uint32_t n = r->count;

    if (n == 0) {
        pthread_mutex_unlock(&r->lock);
        return;
    }
    r->count = 0; /* a drain below calls back here */

    const uint32_t pb       = r->pixel_bytes;
    const uint32_t d_lo     = (r->dir > 0) ? r->start : (r->start - (n - 1) * pb);
    const uint32_t d_hi     = d_lo + n * pb;
    /* In parallel a pixel must lie in one word (seg.glsl) */
    bool           in_order = ((pb & (pb - 1)) != 0) || ((r->start % pb) != 0);

    kairo_seg_draws(r->seg, d_lo, n * pb);
    for (uint32_t k = 0; k < r->reads; k++) {
        const uint32_t lo = r->lo[k], hi = r->hi[k];
        if (lo == hi)
            continue;
        if (kairo_seg_reads_pending(r->seg, lo, hi - lo))
            kairo_seg_drain(r->seg);
        if ((lo < d_hi) && (d_lo < hi))
            in_order = true;
        kairo_seg_reads(r->seg, lo, hi - lo);
    }
    r->op(r->ctx, in_order);
    kairo_seg_add(r->seg, kairo_seg_stream(r->seg, r->words, n * r->words_per), 0, n, r->start * 8, pb * 8, r->dir);
    pthread_mutex_unlock(&r->lock);
}

void
kairo_seg_run_pixel(kairo_seg_run_t *r, uint32_t addr, const uint32_t *words, const uint32_t *reads)
{
    const uint32_t pb = r->pixel_bytes;

    pthread_mutex_lock(&r->lock);
    addr &= r->vram_mask;
    if (r->count != 0) {
        int dir = r->dir;
        if (r->count == 1)
            dir = (addr == r->start + pb) ? 1 : ((addr + pb) == r->start) ? -1 : 0;
        if ((dir != 0) && (r->count < r->max) && ((int64_t) addr == (int64_t) r->start + (int64_t) r->count * dir * pb) &&
            ((int64_t) addr + pb <= (int64_t) r->vram_mask + 1))
            r->dir = dir;
        else
            kairo_seg_run_flush(r);
    }
    if (r->count == 0) {
        r->start = addr;
        r->dir   = 1;
        for (uint32_t k = 0; k < r->reads; k++)
            r->lo[k] = r->hi[k] = 0;
    }
    for (uint32_t i = 0; i < r->words_per; i++)
        r->words[r->count * r->words_per + i] = words[i];
    for (uint32_t k = 0; k < r->reads; k++) {
        if (reads[k] == KAIRO_SEG_RUN_NONE)
            continue;
        /* a slot reads a pixel's bytes */
        const uint32_t a = reads[k] & r->vram_mask;
        if (r->lo[k] == r->hi[k]) {
            r->lo[k] = a;
            r->hi[k] = a + pb;
        } else {
            r->lo[k] = (a < r->lo[k]) ? a : r->lo[k];
            r->hi[k] = (a + pb > r->hi[k]) ? a + pb : r->hi[k];
        }
    }
    r->count++;
    pthread_mutex_unlock(&r->lock);
}
