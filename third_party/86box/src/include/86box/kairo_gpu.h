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

/* ---- The scanout (KairoX86#233 and the cards' own displays) ---- */

/* What a card's line renderer would draw, taken as the guest scans the line: its kind, what it read
   (VRAM, resolved per kind into dwords in the queue's byte ring) and the colours it draws with (a
   palette, kept once while it stays the same). The drain draws every queued line with one kernel
   (shaders/scanout.comp), which reads this layout as it is: change both together. */
typedef struct kairo_gpu_scan {
    uint32_t out;     /* the line's first pixel, in pixels from the start of its bitmap */
    uint32_t kind;    /* KAIRO_SCAN_* */
    uint32_t count;   /* the pixels it draws */
    uint32_t src;     /* its first dword in the byte ring */
    uint32_t palette; /* 0: none; else its palette's index in the palette ring + 1 */
    uint32_t a;       /* the kind's own parameter */
    uint32_t skip;    /* the first pixels not drawn: the CPU drew over them after the line was queued */
    uint32_t flags;   /* KAIRO_SCAN_WIDE */
} kairo_gpu_scan_t;

enum {
    /* Packed 8 bits a pixel, 4 a dword; a: the DAC mask; palette: 256 colours */
    KAIRO_SCAN_8 = 1,
    /* 15 or 16 bits a pixel, 2 a dword, through 86Box's tables (video_15to32, video_16to32) */
    KAIRO_SCAN_15,
    KAIRO_SCAN_16,
    /* 32 bits a pixel (the low 24 used), with the RAMDAC's LUT through the palette when it has one */
    KAIRO_SCAN_32,
    /* Text cells, one a dword: the font's byte (bits 0-7), the foreground (8-15) and background
       (16-23) colour indexes, bit 24 the ninth column's dot (a line drawing character, the font's
       bit 0) and bit 25 a 9-dot cell; a: unused; palette: the colour of each index */
    KAIRO_SCAN_TEXT,
    /* Pixels of a bits a pixel (1, 2, 4 or 8), most significant first, over the bytes in the order the
       card scans them (byte k at bits 8(k % 4) of dword k / 4); palette: the colour of each value */
    KAIRO_SCAN_BITS,
    /* Planar pixels, a dword each 8: byte p plane p's bits, most significant first; a pixel's value is
       its bit of each plane (plane p bit p); palette: the colour of each value (16) */
    KAIRO_SCAN_PLANES,
    /* Text cells of four planes, two dwords each: the planes' 8-dot bytes (byte p plane p), then the
       foreground mask F (bits 0-3), the background mask B (4-7) and each plane's ninth dot (8-11); a
       dot's value takes plane p's bit from F where that plane's dot is set, else from B; a: the cell's
       width; palette: the colour of each value (16) */
    KAIRO_SCAN_TEXT4,
    /* 24 bits a pixel, 3 bytes each over the bytes in order (byte k at bits 8(k % 4) of dword k / 4), with
       the RAMDAC's LUT through the palette when it has one, as KAIRO_SCAN_32 */
    KAIRO_SCAN_24,
    /* svga_render_indexed_gfx's character clocks, a dword each: eight 4-bit pixels taken in the order a
       gives (svga's shift_values: each pixel's shift in 3 bits, masked 0x1c), each a palette colour (16) */
    KAIRO_SCAN_NIBBLES,
    /* The same clocks combined into four 8-bit pixels, each pair of nibbles one (palette: 256) */
    KAIRO_SCAN_NIBBLES8,
    /* 15 bits a pixel, 2 a dword, each through the palette (its low byte) when its top bit is set, else
       through 86Box's 15-bit table (svga_render_15bpp_mix_*) */
    KAIRO_SCAN_15MIX,
};

/* Each pixel drawn twice across */
#define KAIRO_SCAN_WIDE 1u
/* Each pixel drawn four times across (with KAIRO_SCAN_WIDE, eight) */
#define KAIRO_SCAN_WIDE4 2u

/* Queues a line of bitmap (its CPU pointer, to tell bitmaps apart; bitmap_gpu its buffer) starting at
   pixel out, drawing count pixels; returns where its words dwords go. palette (palette_count colours,
   at most 256) is kept with it, or none when NULL. A line out of the queue's order (a new frame,
   another bitmap) drains the queue first, as does a full one. The queue stays locked until
   kairo_gpu_scan_commit, after the caller wrote the dwords: a drain on another thread (a card handing
   its frame over from its own) waits for it. */
uint32_t *kairo_gpu_scan(const void *bitmap, kairo_gpu_buffer_t *bitmap_gpu, uint32_t out, uint32_t kind,
                         uint32_t count, uint32_t words, const uint32_t *palette, uint32_t palette_count, uint32_t a,
                         uint32_t b, uint32_t flags);
/* The line kairo_gpu_scan gave is written: the queue unlocks. */
void kairo_gpu_scan_commit(void);
/* Draws every queued line and waits until they are drawn. */
void kairo_gpu_scan_drain(void);
/* The CPU is about to draw pixels start to start + count - 1 of bitmap: a queued line that draws any of
   them is drawn first, so the CPU's drawing, the later one, stays. */
void kairo_gpu_scan_touch(const void *bitmap, uint32_t start, uint32_t count);
/* The CPU has just drawn pixels start to start + count - 1 of bitmap, after lines that draw them were
   queued (a border over a line's first or last pixels): the queued lines leave those pixels as the CPU
   drew them; one they fall in the middle of is drawn first. */
void kairo_gpu_scan_cut(const void *bitmap, uint32_t start, uint32_t count);
/* bitmap is about to be freed: the lines queued for it are drawn first. */
void kairo_gpu_scan_forget(const void *bitmap);
/* 86Box's 15 and 16-bit colour tables (65536 entries each), copied to the GPU at the first call. */
void kairo_gpu_scan_tables(const uint32_t *table15, const uint32_t *table16);

#ifdef __cplusplus
}
#endif

#endif
