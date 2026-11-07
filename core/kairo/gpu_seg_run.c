/*
 * Runs of bytes on the drawing engines' shared batches (86box/kairo_gpu_seg.h; KairoX86#232): for an engine whose
 * walk stays the CPU's and whose every destination byte carries its own inputs (the ET4000/W32's, the Cirrus
 * GD54xx's), the bytes the walk draws one after the other along memory go in as one segment, each with its card's
 * stream words, and the memory each byte reads is tracked so the run is drawn in order where it reads what it draws,
 * and the batch first where the run reads what the batch draws or draws what it reads.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

#include <86box/86box.h>
#include <86box/kairo_gpu_seg.h>

struct kairo_seg_run {
    kairo_seg_t *seg;
    uint32_t     words_per, max, reads, vram_mask;
    void       (*op)(void *ctx, bool in_order);
    void        *ctx;
    uint32_t     start; /* the run's first byte */
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

kairo_seg_run_t *
kairo_seg_run_open(kairo_seg_t *seg, uint32_t vram_mask, uint32_t words_per, uint32_t reads, void (*op)(void *ctx, bool in_order),
                   void *ctx)
{
    kairo_seg_run_t *r = calloc(1, sizeof(kairo_seg_run_t));
    if ((r == NULL) || (reads > KAIRO_SEG_RUN_READS))
        fatal("A run of bytes on the GPU: no memory, or %u read slots\n", reads);
    r->seg       = seg;
    r->vram_mask = vram_mask;
    r->words_per = words_per;
    r->max       = 4096;
    r->reads     = reads;
    r->op        = op;
    r->ctx       = ctx;
    r->words     = malloc((size_t) r->max * words_per * 4);
    if (r->words == NULL)
        fatal("A run of bytes on the GPU: no memory\n");
    kairo_seg_set_flush(seg, run_flush_cb, r);
    return r;
}

void
kairo_seg_run_close(kairo_seg_run_t *r)
{
    if (r == NULL)
        return;
    free(r->words);
    free(r);
}

void
kairo_seg_run_flush(kairo_seg_run_t *r)
{
    const uint32_t n = r->count;

    if (n == 0)
        return;
    r->count = 0; /* a drain below calls back here */

    const uint32_t d_lo     = (r->dir > 0) ? r->start : (r->start - (n - 1));
    const uint32_t d_hi     = d_lo + n;
    bool           in_order = false;

    kairo_seg_draws(r->seg, d_lo, n);
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
    kairo_seg_add(r->seg, kairo_seg_stream(r->seg, r->words, n * r->words_per), 0, n, r->start * 8, 8, r->dir);
}

void
kairo_seg_run_byte(kairo_seg_run_t *r, uint32_t addr, const uint32_t *words, const uint32_t *reads)
{
    addr &= r->vram_mask;
    if (r->count != 0) {
        int dir = r->dir;
        if (r->count == 1)
            dir = (addr == r->start + 1) ? 1 : ((addr + 1) == r->start) ? -1 : 0;
        if ((dir != 0) && (r->count < r->max) && ((int64_t) addr == (int64_t) r->start + (int64_t) r->count * dir))
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
        const uint32_t a = reads[k] & r->vram_mask;
        if (r->lo[k] == r->hi[k]) {
            r->lo[k] = a;
            r->hi[k] = a + 1;
        } else {
            r->lo[k] = (a < r->lo[k]) ? a : r->lo[k];
            r->hi[k] = (a + 1 > r->hi[k]) ? a + 1 : r->hi[k];
        }
    }
    r->count++;
}
