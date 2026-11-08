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

/* Card memory (video memory, a frame buffer, texture caches) where a card would calloc it with the GPU
   on, so kernels work in it in place: zeroed, the CPU's for its whole life as any memory, freed with
   kairo_gpu_free. kairo_gpu_buffer_of gives the buffer an allocation is (data where it starts). */
void               *kairo_gpu_alloc(size_t size);
void                kairo_gpu_free(void *data);
kairo_gpu_buffer_t *kairo_gpu_buffer_of(const void *data);
/* The buffer of the allocation p lies in, and p's byte offset in it (KairoX86#315: a card whose memory is a part of an
   allocation, the MediaGX's frame buffer in main RAM) */
kairo_gpu_buffer_t *kairo_gpu_buffer_containing(const void *p, size_t *offset);

/* KairoX86#239: for a card's own Vulkan backend (the Rage 128's), the core's Vulkan, which it works with instead of its
   own: vkGetInstanceProcAddr, the instance, physical device, device, the queue's family and the queue (as the
   handles, VkInstance and so on), and what the device has turned on (64-bit integers, 16-bit storage access,
   VK_EXT_external_memory_host). Every submit to the queue holds kairo_gpu_queue_lock. kairo_gpu_buffer_handle gives
   a buffer's VkBuffer (as a 64-bit handle). */
typedef struct kairo_gpu_vulkan {
    void    *get_instance_proc_addr;
    void    *instance;
    void    *physical;
    void    *device;
    uint32_t queue_family;
    void    *queue;
    int      int64;
    int      storage16;
    int      host_memory;
    int      android_buffers; /* KairoX86#330: Android's hardware buffers imported (gpu_frame.c) */
} kairo_gpu_vulkan_t;
const kairo_gpu_vulkan_t *kairo_gpu_vulkan(void);

/* KairoX86#330: frame slots the presenter shows the picture from without the processor copying it (core/kairo/gpu_frame.c):
   each an Android hardware buffer (AHardwareBuffer, R8G8B8A8) the GPU copies a card's bitmap into, which the presenter
   samples as a GL texture. kairo_gpu_frames_available: whether this device has them (Android, the device's hardware
   buffer extensions on). kairo_gpu_frame_copy copies width x height pixels of bitmap, from byte offset on, pitch pixels
   from one row to the next, into the slot (made that size first: its buffer then a new one) and waits for the copy;
   it returns the slot's buffer, which the slot holds a reference to until it is remade or freed: a presenter that
   keeps it takes its own (AHardwareBuffer_acquire). Slots are freed before the device (kairo_gpu_close). */
typedef struct kairo_gpu_frame kairo_gpu_frame_t;
int                kairo_gpu_frames_available(void);
kairo_gpu_frame_t *kairo_gpu_frame_new(void);
void               kairo_gpu_frame_free(kairo_gpu_frame_t *frame);
void *kairo_gpu_frame_copy(kairo_gpu_frame_t *frame, const kairo_gpu_buffer_t *bitmap, size_t offset, uint32_t width,
                           uint32_t height, uint32_t pitch);
void                      kairo_gpu_queue_lock(void);
void                      kairo_gpu_queue_unlock(void);
uint64_t                  kairo_gpu_buffer_handle(const kairo_gpu_buffer_t *buffer);

/* The 4 KB pages of card memory a recorded GPU batch draws on (core/kairo/gpu_pages.c): marked as work is
   recorded, checked where the processor touches card memory, cleared once the batch is drawn. hit and
   any are read without the batch's lock: a page marked as the processor touches it races just as the
   card's own threads would. */
typedef struct kairo_gpu_pages {
    uint8_t *pending;
    uint32_t count; /* pages */
    uint32_t mask;  /* the memory's address mask */
    int      any;   /* a page is marked (atomic) */
} kairo_gpu_pages_t;

void kairo_gpu_pages_init(kairo_gpu_pages_t *pages, uint32_t mask);
void kairo_gpu_pages_free(kairo_gpu_pages_t *pages);
void kairo_gpu_pages_mark(kairo_gpu_pages_t *pages, uint32_t addr, uint32_t len);
bool kairo_gpu_pages_hit(const kairo_gpu_pages_t *pages, uint32_t addr, uint32_t len);
bool kairo_gpu_pages_any(const kairo_gpu_pages_t *pages);
void kairo_gpu_pages_clear(kairo_gpu_pages_t *pages);

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
    /* A patch over the drawn pixels (hardware cursors and overlays, kairo_gpu_scan_patch): pixels patch_from to
       patch_from + patch_count - 1 of the line (0: none), four dwords each from dword patch_src on (A, X, K, V): a
       pixel with K set whose drawn value v matches the line's key ((v & patch_key_mask) == patch_key) becomes V,
       any other (v & A) ^ X */
    uint32_t patch_from;
    uint32_t patch_count;
    uint32_t patch_src;
    uint32_t patch_key;
    uint32_t patch_key_mask;
    uint32_t reserved[3];
} kairo_gpu_scan_t;

/* The dwords of each pixel of a patch: A, X, K, V */
#define KAIRO_PATCH_WORDS 4

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
    /* 16 bits a pixel (565), 2 a dword, each channel through its own column of the palette (256 colours): red from
       palette[(c >> 8) & F8h], green from palette[(c >> 3) & FCh], blue from palette[(c << 3) & F8h], no alpha (the
       3dfx Voodoo's display table, vid_voodoo_display.c voodoo_calc_clutData) */
    KAIRO_SCAN_16CLUT,
    /* KairoX86#241: the CGA's composite output decoded (vid_cga_comp.c Composite_Process): the words are the line's
       composite signal, count + 10 values (signed) from 5 before its first pixel; a: 1 for the luma-only decode;
       palette: the sharpness, then the I and Q weights of red, green and blue (signed) */
    KAIRO_SCAN_COMPOSITE,
    /* KairoX86#315: 15 bits a pixel (555), 2 a dword, each channel through its own column of the palette (256 colours):
       red from palette[(c >> 7) & F8h], green from palette[(c >> 2) & F8h], blue from palette[(c << 3) & F8h] (the
       Cyrix MediaGX's 5-5-5 format through its gamma RAM) */
    KAIRO_SCAN_15CLUT,
};

/* Each pixel drawn twice across */
#define KAIRO_SCAN_WIDE 1u
/* Each pixel drawn four times across (with KAIRO_SCAN_WIDE, eight) */
#define KAIRO_SCAN_WIDE4 2u

/* Queues a line of bitmap (its CPU pointer, to tell bitmaps apart; bitmap_gpu its buffer) starting at
   pixel out, drawing count pixels, the first b of them not (a line clipped at its start); returns where its words
   dwords go. palette (palette_count colours,
   at most 256) is kept with it, or none when NULL. A line out of the queue's order (a new frame,
   another bitmap) drains the queue first, as does a full one. The queue stays locked until
   kairo_gpu_scan_commit, after the caller wrote the dwords: a drain on another thread (a card handing
   its frame over from its own) waits for it. */
uint32_t *kairo_gpu_scan(const void *bitmap, kairo_gpu_buffer_t *bitmap_gpu, uint32_t out, uint32_t kind,
                         uint32_t count, uint32_t words, const uint32_t *palette, uint32_t palette_count, uint32_t a,
                         uint32_t b, uint32_t flags);
/* The line kairo_gpu_scan gave is written: the queue unlocks. */
void kairo_gpu_scan_commit(void);
/* Pixels start to start + count - 1 of bitmap, of the line queued last for them, take the patch when it is drawn
   (hardware cursors and overlays over it: KairoX86#233): pixel k's dwords ax[4k] to ax[4k + 3] (A, X, K, V), with
   the line's key and key_mask (kairo_gpu_scan_t). Returns the pixels the patch took ([*from, *to); none when no
   queued line draws them): the caller applies the rest to the pixels the CPU drew. One patch a line. */
void kairo_gpu_scan_patch(const void *bitmap, uint32_t start, uint32_t count, const uint32_t *ax, uint32_t key,
                          uint32_t key_mask, uint32_t *from, uint32_t *to);
/* One pixel as a patch takes it (the CPU's half of kairo_gpu_scan_patch) */
static inline uint32_t
kairo_gpu_patch_pixel(uint32_t v, const uint32_t *axkv, uint32_t key, uint32_t key_mask)
{
    if (axkv[2] && ((v & key_mask) == key))
        return axkv[3];
    return (v & axkv[0]) ^ axkv[1];
}
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
