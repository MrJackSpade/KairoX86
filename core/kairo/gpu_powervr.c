/*
 * The PowerVR PCX2's tiles on the GPU (KairoX86#269; 86box/kairo_gpu_powervr.h): a prepared frame's lists copied to
 * GPU buffers and drawn by shaders/powervr.comp, one work group a span.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <86box/86box.h>
#include <86box/kairo_gpu.h>
#include <86box/kairo_gpu_powervr.h>

#include "gpu_internal.h"

static const uint32_t powervr_spirv[] = {
#include "powervr.comp.inc"
};

/* The most work groups a dispatch has across */
#define GROUPS_X 32768

typedef struct {
    kairo_gpu_buffer_t *planes, *objects, *spans, *sched, *frame;
    kairo_gpu_buffer_t *tex, *rgb;
    uint32_t            tex_words;
} pvr_gpu_t;

static kairo_gpu_kernel_t *kernel;
static unsigned long long  spans_drawn;

void *
kairo_pvr_gpu_open(uint32_t *tex, uint32_t tex_words, uint32_t *rgb)
{
    pvr_gpu_t *g = calloc(1, sizeof(pvr_gpu_t));
    if (g == NULL)
        fatal("PowerVR on the GPU: no memory\n");
    g->tex       = kairo_gpu_buffer_of(tex);
    g->rgb       = kairo_gpu_buffer_of(rgb);
    g->tex_words = tex_words;
    g->frame     = kairo_gpu_buffer(KF_WORDS * 4);
    return g;
}

/* *buffer, at least bytes long (its contents not kept) */
static void
fit(kairo_gpu_buffer_t **buffer, size_t bytes)
{
    if (bytes == 0)
        bytes = 4;
    if ((*buffer != NULL) && ((*buffer)->size >= bytes))
        return;
    size_t size = (*buffer != NULL) ? (*buffer)->size : 4096;
    while (size < bytes)
        size *= 2;
    kairo_gpu_buffer_free(*buffer);
    *buffer = kairo_gpu_buffer(size);
}

void
kairo_pvr_gpu_render(void *gpu, const kairo_pvr_lists_t *lists)
{
    pvr_gpu_t *g = gpu;

    if (lists->n_spans == 0)
        return;
    if (kernel == NULL)
        kernel = kairo_gpu_kernel("powervr", powervr_spirv, sizeof(powervr_spirv), 7, 4 * 4);

    fit(&g->planes, (size_t) lists->n_planes * KP_WORDS * 4);
    fit(&g->objects, (size_t) lists->n_objects * KO_WORDS * 4);
    fit(&g->spans, (size_t) lists->n_spans * KN_WORDS * 4);
    fit(&g->sched, (size_t) lists->n_sched * 4);
    memcpy(g->planes->data, lists->planes, (size_t) lists->n_planes * KP_WORDS * 4);
    memcpy(g->objects->data, lists->objects, (size_t) lists->n_objects * KO_WORDS * 4);
    memcpy(g->spans->data, lists->spans, (size_t) lists->n_spans * KN_WORDS * 4);
    memcpy(g->sched->data, lists->sched, (size_t) lists->n_sched * 4);
    memcpy(g->frame->data, lists->frame, KF_WORDS * 4);

    /* The texture memory's word mask when its size is a power of two, as tsp_word takes it */
    const uint32_t tex_mask = (g->tex_words && !(g->tex_words & (g->tex_words - 1))) ? g->tex_words - 1 : 0;
    if (tex_mask == 0)
        fatal("PowerVR on the GPU: texture memory of %u words\n", g->tex_words);
    const uint32_t            push[4]    = { lists->n_spans, tex_mask, 0, 0 };
    kairo_gpu_buffer_t *const buffers[7] = { g->planes, g->objects, g->spans, g->sched, g->frame, g->tex, g->rgb };
    const uint32_t            groups_x   = (lists->n_spans < GROUPS_X) ? lists->n_spans : GROUPS_X;
    kairo_gpu_run(kernel, buffers, push, groups_x, (lists->n_spans + GROUPS_X - 1) / GROUPS_X, 1);
    spans_drawn += lists->n_spans;
}

void
kairo_pvr_gpu_close(void *gpu)
{
    pvr_gpu_t *g = gpu;
    if (g == NULL)
        return;
    kairo_gpu_buffer_free(g->planes);
    kairo_gpu_buffer_free(g->objects);
    kairo_gpu_buffer_free(g->spans);
    kairo_gpu_buffer_free(g->sched);
    kairo_gpu_buffer_free(g->frame);
    free(g);
}

void
kairo_gpu_powervr_close(void)
{
    /* How many spans the GPU drew, for the graphics batch (core/test/gpu/compare.py) */
    fprintf(stderr, "kairo-gpu-powervr: %llu spans drawn\n", spans_drawn);
    spans_drawn = 0;
    kairo_gpu_kernel_free(kernel);
    kernel = NULL;
}
