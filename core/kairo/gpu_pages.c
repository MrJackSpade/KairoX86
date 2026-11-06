/*
 * The card memory pages a recorded GPU batch draws on (86box/kairo_gpu.h, kairo_gpu_pages_t): the Voodoo's
 * and the ViRGE's batches (gpu_voodoo.c, gpu_virge.c) mark them as they record, and the processor's own
 * reads and writes of card memory check them, drawing the batch first where they meet.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <86box/86box.h>
#include <86box/kairo_gpu.h>

void
kairo_gpu_pages_init(kairo_gpu_pages_t *pages, uint32_t mask)
{
    pages->mask    = mask;
    pages->count   = (mask >> 12) + 1;
    pages->pending = calloc(pages->count, 1);
    if (pages->pending == NULL)
        fatal("The PC stopped: no memory for its GPU's page map\n");
    __atomic_store_n(&pages->any, 0, __ATOMIC_RELEASE);
}

void
kairo_gpu_pages_free(kairo_gpu_pages_t *pages)
{
    free(pages->pending);
    pages->pending = NULL;
}

void
kairo_gpu_pages_mark(kairo_gpu_pages_t *pages, uint32_t addr, uint32_t len)
{
    if (len == 0)
        return;
    if (len > pages->mask)
        len = pages->mask + 1;
    const uint32_t first = addr >> 12;
    const uint32_t last  = (addr + len - 1) >> 12;
    for (uint32_t page = first; page <= last; page++)
        pages->pending[((page << 12) & pages->mask) >> 12] = 1;
    __atomic_store_n(&pages->any, 1, __ATOMIC_RELEASE);
}

bool
kairo_gpu_pages_any(const kairo_gpu_pages_t *pages)
{
    return __atomic_load_n(&pages->any, __ATOMIC_ACQUIRE) != 0;
}

bool
kairo_gpu_pages_hit(const kairo_gpu_pages_t *pages, uint32_t addr, uint32_t len)
{
    if ((len == 0) || !kairo_gpu_pages_any(pages))
        return false;
    if (len > pages->mask)
        len = pages->mask + 1;
    const uint32_t first = addr >> 12;
    const uint32_t last  = (addr + len - 1) >> 12;
    for (uint32_t page = first; page <= last; page++)
        if (pages->pending[((page << 12) & pages->mask) >> 12])
            return true;
    return false;
}

void
kairo_gpu_pages_clear(kairo_gpu_pages_t *pages)
{
    memset(pages->pending, 0, pages->count);
    __atomic_store_n(&pages->any, 0, __ATOMIC_RELEASE);
}
