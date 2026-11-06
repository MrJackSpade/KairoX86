/*
 * The SVGA scanout on the GPU (KairoX86#233, 86box/kairo_gpu.h): the kernels that draw the lines
 * vid_svga_render.c takes as the guest scans them.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include <86box/kairo_gpu.h>

#include "gpu_internal.h"

/* The kernel reads kairo_gpu_line_t as shaders/svga_8bpp.comp lays it out (std430) */
_Static_assert(offsetof(kairo_gpu_line_t, map8) == 16, "kairo_gpu_line_t.map8 moved");
_Static_assert(offsetof(kairo_gpu_line_t, line) == 1040, "kairo_gpu_line_t.line moved");
_Static_assert(offsetof(kairo_gpu_line_t, p) == 3088, "kairo_gpu_line_t.p moved");
_Static_assert(sizeof(kairo_gpu_line_t) == 3096, "kairo_gpu_line_t's size changed");

static const uint32_t svga_8bpp_spirv[] = {
#include "svga_8bpp.comp.inc"
};

_Static_assert(sizeof(kairo_gpu_direct_t) == 32, "kairo_gpu_direct_t's size changed");

static const uint32_t svga_direct_spirv[] = {
#include "svga_direct.comp.inc"
};

static kairo_gpu_kernel_t *svga_8bpp;
static kairo_gpu_kernel_t *svga_direct;
/* 86Box's 15 and 16-bit colour tables, on the GPU (they never change) */
static kairo_gpu_buffer_t *table15;
static kairo_gpu_buffer_t *table16;
#define TABLE_BYTES (65536 * sizeof(uint32_t))

void
kairo_gpu_scanout_8bpp(kairo_gpu_buffer_t *lines, kairo_gpu_buffer_t *bitmap, uint32_t first, uint32_t mask,
                       uint32_t count)
{
    if (svga_8bpp == NULL)
        svga_8bpp = kairo_gpu_kernel("svga_8bpp", svga_8bpp_spirv, sizeof(svga_8bpp_spirv), 2, 8);
    kairo_gpu_buffer_t *const buffers[2] = { lines, bitmap };
    const uint32_t            range[2]   = { first, mask };
    kairo_gpu_run(svga_8bpp, buffers, range, count, 1, 1);
}

void
kairo_gpu_scanout_direct(kairo_gpu_buffer_t *lines, kairo_gpu_buffer_t *bytes, kairo_gpu_buffer_t *palettes,
                         const uint32_t *table15_cpu, const uint32_t *table16_cpu, kairo_gpu_buffer_t *bitmap,
                         uint32_t first, uint32_t mask, uint32_t byte_mask, uint32_t count)
{
    if (svga_direct == NULL) {
        svga_direct = kairo_gpu_kernel("svga_direct", svga_direct_spirv, sizeof(svga_direct_spirv), 6, 12);
        table15     = kairo_gpu_buffer(TABLE_BYTES);
        table16     = kairo_gpu_buffer(TABLE_BYTES);
        memcpy(table15->data, table15_cpu, TABLE_BYTES);
        memcpy(table16->data, table16_cpu, TABLE_BYTES);
    }
    kairo_gpu_buffer_t *const buffers[6] = { lines, bytes, palettes, table15, table16, bitmap };
    const uint32_t            range[3]   = { first, mask, byte_mask };
    kairo_gpu_run(svga_direct, buffers, range, count, 1, 1);
}

void
kairo_gpu_scanout_close(void)
{
    kairo_gpu_kernel_free(svga_8bpp);
    kairo_gpu_kernel_free(svga_direct);
    kairo_gpu_buffer_free(table15);
    kairo_gpu_buffer_free(table16);
    svga_8bpp   = NULL;
    svga_direct = NULL;
    table15     = NULL;
    table16     = NULL;
}
