/*
 * The machine's GPU (KairoX86#232): the device's Vulkan GPU, which the emulated graphics hardware's
 * work runs on when the machine's Hardware acceleration setting (#282, 86box.cfg's [KairoX86]
 * hardware_acceleration) is on. Off, nothing here runs: every card works in software as 86Box has it,
 * the reference the GPU versions match within the graphics batch's margin (core/test/gpu, #283).
 *
 * The machine's library copy owns it: kairo_gpu_open at the machine's start, kairo_gpu_close at its
 * end (after pc_close, whose devices free their GPU objects first). Any Vulkan failure ends the
 * machine (fatal) with what failed: there is no software fallback for a machine set to use the GPU.
 *
 * Work is compute kernels (SPIR-V, compiled from core/kairo/shaders at build time) over buffers the
 * CPU and the GPU share, mapped for the CPU's whole life (coherent: no flushes). kairo_gpu_run waits
 * for the kernel, so what it wrote is there for the caller when it returns.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_H
#define KAIRO_GPU_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Whether the machine runs its graphics hardware on the GPU: its Hardware acceleration setting, read
   at the start (kairo_gpu_open). */
extern bool kairo_gpu_on;

/* At the machine's start, after its configuration is read: opens the GPU if the setting is on. */
void kairo_gpu_open(void);
/* The open GPU's name, as its driver gives it. */
const char *kairo_gpu_name(void);
/* At the machine's end, after every device freed its GPU objects. */
void kairo_gpu_close(void);

typedef struct kairo_gpu_buffer {
    void  *data; /* the CPU's view, for the buffer's whole life */
    size_t size;
    void  *impl;
} kairo_gpu_buffer_t;

/* A buffer of size bytes, zeroed, that kernels and the CPU share. */
kairo_gpu_buffer_t *kairo_gpu_buffer(size_t size);
void                kairo_gpu_buffer_free(kairo_gpu_buffer_t *buffer);

typedef struct kairo_gpu_kernel kairo_gpu_kernel_t;

/* A compute kernel: its SPIR-V (words, its size in bytes), the storage buffers it binds (bindings 0 to
   buffers - 1 of set 0) and the bytes of its push constants (at most 128). name is for errors. */
kairo_gpu_kernel_t *kairo_gpu_kernel(const char *name, const uint32_t *spirv, size_t spirv_bytes, int buffers,
                                     uint32_t push_bytes);
void                kairo_gpu_kernel_free(kairo_gpu_kernel_t *kernel);

/* Runs kernel over groups_x x groups_y x groups_z work groups with its buffers (as many as it binds)
   and push constants, and waits for it. */
void kairo_gpu_run(kairo_gpu_kernel_t *kernel, kairo_gpu_buffer_t *const *buffers, const void *push, uint32_t groups_x,
                   uint32_t groups_y, uint32_t groups_z);

/* ---- The SVGA scanout (KairoX86#233) ---- */

/* One packed 8bpp line, taken as the guest scans it (vid_svga_render.c's render job, KairoX86#38):
   the line's VRAM and the palette it is drawn with. The kernel (shaders/svga_8bpp.comp) reads this
   layout as it is: change both together. */
#define KAIRO_GPU_LINE_BYTES 2048
typedef struct kairo_gpu_line {
    uint32_t  out;    /* the line's first pixel, in pixels from the start of its bitmap */
    uint32_t  dac;    /* the DAC mask */
    int32_t   dwords; /* the line's VRAM dwords: 4 pixels each, 8 when wide */
    int32_t   wide;   /* each pixel drawn twice across */
    uint32_t  map8[256];
    uint8_t   line[KAIRO_GPU_LINE_BYTES];
    uint32_t *p;      /* the line's first pixel, for the CPU's drawing */
} kairo_gpu_line_t;

/* Draws lines first to first + count - 1 (each index masked by mask, a ring of a power of 2 lines) of
   the lines buffer into the bitmap buffer, and waits until they are drawn. */
void kairo_gpu_scanout_8bpp(kairo_gpu_buffer_t *lines, kairo_gpu_buffer_t *bitmap, uint32_t first, uint32_t mask,
                            uint32_t count);

/* One direct-colour line (15, 16 or 32 bits a pixel), taken as the guest scans it: its VRAM bytes in
   the queue's byte ring, and with the RAMDAC's LUT on the palette, in the palette ring. The kernel
   (shaders/svga_direct.comp) reads this layout as it is: change both together. */
typedef struct kairo_gpu_direct {
    uint32_t out;    /* the line's first pixel, in pixels from the start of its bitmap */
    uint32_t format; /* 15, 16 or 32 */
    uint32_t pixels;
    uint32_t src;    /* its first VRAM byte in the byte ring, a multiple of 4 */
    uint32_t lut;    /* 0: no LUT; else its palette's index in the palette ring + 1 */
    uint32_t pad[3];
} kairo_gpu_direct_t;

/* Draws direct lines first to first + count - 1 (masked by mask) into the bitmap buffer, their bytes in
   bytes (a ring of byte_mask + 1 dwords), their palettes in palettes (256 entries each), 15 and 16 bits
   through 86Box's tables (video_15to32, video_16to32: 65536 entries each, copied to the GPU at the
   first call), and waits until they are drawn. */
void kairo_gpu_scanout_direct(kairo_gpu_buffer_t *lines, kairo_gpu_buffer_t *bytes, kairo_gpu_buffer_t *palettes,
                              const uint32_t *table15, const uint32_t *table16, kairo_gpu_buffer_t *bitmap,
                              uint32_t first, uint32_t mask, uint32_t byte_mask, uint32_t count);

#ifdef __cplusplus
}
#endif

#endif
