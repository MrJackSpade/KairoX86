/*
 * The 3dfx cards' 2D drawing on the GPU (KairoX86#278, #277): 86box/vid_voodoo_k2d.h.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#include <86box/86box.h>
#include <86box/device.h>
#include <86box/mem.h>
#include <86box/thread.h>
#include <86box/timer.h>
#include <86box/video.h>
#include <86box/vid_svga.h>
#include <86box/vid_voodoo_common.h>
#include <86box/kairo_gpu.h>
#include <86box/kairo_gpu_seg.h>
#include <86box/kairo_gpu_voodoo.h>
#include <86box/vid_voodoo_k2d.h>

typedef struct voodoo_k2d_t {
    kairo_seg_t     *seg;
    kairo_seg_run_t *run[4];           /* 1 to 4-byte pixels */
    mutex_t         *lock;
    uint32_t         record[B2_WORDS]; /* the operation last put in the batch */
    uint32_t         next[B2_WORDS];   /* the operation of the pixels being recorded */
    uint64_t         generation;
    int              issued;
    int              in_order;
} voodoo_k2d_t;

static void
voodoo_k2d_op(void *priv, bool in_order)
{
    voodoo_k2d_t *g = (voodoo_k2d_t *) priv;

    kairo_seg_make_room(g->seg);
    if (g->issued && (g->in_order == in_order) && (g->generation == kairo_seg_generation(g->seg)) &&
        !memcmp(g->record, g->next, sizeof(g->record)))
        return;
    memcpy(kairo_seg_op(g->seg, in_order), g->next, sizeof(g->next));
    memcpy(g->record, g->next, sizeof(g->record));
    g->generation = kairo_seg_generation(g->seg);
    g->in_order   = in_order;
    g->issued     = 1;
}

static void
voodoo_k2d_flush(voodoo_k2d_t *g)
{
    for (int i = 0; i < 4; i++)
        kairo_seg_run_flush(g->run[i]);
}

/* voodoo->k2d_touch: the processor's, the display's or the 3D engine's access */
static void
voodoo_k2d_touch(voodoo_t *voodoo, uint32_t addr, uint32_t len)
{
    voodoo_k2d_t *g = (voodoo_k2d_t *) voodoo->k2d;

    thread_wait_mutex(g->lock);
    kairo_seg_touch(g->seg, addr & voodoo->fb_mask, len);
    thread_release_mutex(g->lock);
}

/* voodoo->k2d_drain: the batch drawn before the 3D engine draws */
static void
voodoo_k2d_drain(voodoo_t *voodoo)
{
    voodoo_k2d_t *g = (voodoo_k2d_t *) voodoo->k2d;

    thread_wait_mutex(g->lock);
    voodoo_k2d_flush(g);
    kairo_seg_drain(g->seg);
    thread_release_mutex(g->lock);
}

void
voodoo_k2d_lock(voodoo_t *voodoo)
{
    if (voodoo->k2d == NULL)
        return;
    thread_wait_mutex(((voodoo_k2d_t *) voodoo->k2d)->lock);
    if (voodoo->k_gpu != NULL)
        kairo_voodoo_gpu_drain(voodoo);
}

void
voodoo_k2d_unlock(voodoo_t *voodoo)
{
    if (voodoo->k2d != NULL)
        thread_release_mutex(((voodoo_k2d_t *) voodoo->k2d)->lock);
}

void
voodoo_k2d_read(voodoo_t *voodoo, const uint8_t *p, uint32_t len)
{
    if (voodoo->k2d != NULL)
        kairo_seg_touch(((voodoo_k2d_t *) voodoo->k2d)->seg, (uint32_t) (p - voodoo->fb_mem) & voodoo->fb_mask, len);
}

void
voodoo_k2d_pixel(voodoo_t *voodoo, uint32_t addr, int pb, const uint32_t *rec, uint32_t src, uint32_t pattern, int src_key)
{
    voodoo_k2d_t *g = (voodoo_k2d_t *) voodoo->k2d;

    /* A run is of one operation */
    if (memcmp(rec, g->next, sizeof(g->next))) {
        voodoo_k2d_flush(g);
        memcpy(g->next, rec, sizeof(g->next));
    }
    const uint32_t words[B2_PIXEL_WORDS] = { src, pattern, src_key ? B2K_SRC_KEY : 0 };

    kairo_seg_run_pixel(g->run[pb - 1], addr, words, NULL);
}

void
voodoo_k2d_open(voodoo_t *voodoo)
{
    voodoo_k2d_t *g;

    if (!kairo_gpu_on)
        return;
    g = calloc(1, sizeof(*g));
    if (g == NULL)
        fatal("The 3dfx 2D drawing on the GPU: no memory\n");
    g->seg  = kairo_banshee2d_open(voodoo->fb_mem, voodoo->fb_mask, voodoo->changedvram, &changeframecount);
    g->lock = thread_create_mutex();
    for (int i = 0; i < 4; i++)
        g->run[i] = kairo_seg_run_open(g->seg, voodoo->fb_mask, i + 1, B2_PIXEL_WORDS, 0, voodoo_k2d_op, g);
    voodoo->k2d       = g;
    voodoo->k2d_touch = voodoo_k2d_touch;
    voodoo->k2d_drain = voodoo_k2d_drain;
}

void
voodoo_k2d_close(voodoo_t *voodoo)
{
    voodoo_k2d_t *g = (voodoo_k2d_t *) voodoo->k2d;

    if (g == NULL)
        return;
    kairo_seg_close(g->seg);
    thread_close_mutex(g->lock);
    free(g);
    voodoo->k2d = NULL;
}
