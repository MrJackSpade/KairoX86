/*
 * KairoX86's Cirrus video window test (KairoX86#283, for #233): on a Cirrus GD5426 or later (CR27 90h and up), the
 * Cirrus BIOS's mode 5Fh (640 x 480 x 8, through the 64K window at A0000h), the picture a pattern with a band of one
 * colour and an RGB 565 source placed 640K on, shown in the video window (CR31 to CR3E) in passes, each held six ticks
 * of the BIOS clock: at 1:1, through the colour key (the band's colour: CR3E bit 7, GR0C), doubled across and down,
 * as YUV 4:2:2, and placed past the picture's right edge. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static void crtc(u8 index, u8 value) {
    outb(0x3d4, index);
    outb(0x3d5, value);
}

static u8 crtc_read(u8 index) {
    outb(0x3d4, index);
    return inb(0x3d5);
}

static void gr(u8 index, u8 value) {
    outb(0x3ce, index);
    outb(0x3cf, value);
}

#define W     640
#define H     480
#define KEY   0xe3u     /* the band's colour index */
#define SRC   0xa0000u  /* the source, 640K on */
#define SRC_W 320
#define SRC_H 240

/* A byte of video memory through the 64K window, its 4K page in GR9 */
static u32 page = 0xffffffffu;
static void vram8(u32 addr, u8 v) {
    if ((addr >> 12) != page) {
        page = addr >> 12;
        gr(0x09, (u8) page);
    }
    *(volatile u8 *) (0xa0000u + (addr & 0xfffu)) = v;
}

static u32 dwords; /* source addresses in dwords (the GD5446 on) or bytes */

/* The window: left edge x (a multiple of 4), w wide (a multiple of 8), lines y to y + h - 1; format (CR3E bits 1-3:
   0 YUV 4:2:2, 5 RGB 565); zoom 256 (1:1) or 128 (2x); keyed */
static void window(u32 x, u32 w, u32 y, u32 h, u32 format, u32 zoom, u32 keyed) {
    /* At 8 bits a pixel a region's size counts 4 pixels a unit */
    const u32 r1 = x / 4;
    const u32 r2 = w / 4;
    const u32 end = y + h - 1;
    const u32 addr = dwords ? (SRC / 4) : SRC;
    const u32 pitch = dwords ? (SRC_W * 2 / 8) : (SRC_W * 2 / 2);
    crtc(0x3e, 0); /* off while it is set up */
    crtc(0x31, (u8) zoom);
    crtc(0x32, (u8) zoom);
    crtc(0x33, (u8) r1);
    crtc(0x34, (u8) r2);
    crtc(0x35, 0);
    crtc(0x36, (u8) (((r1 >> 8) & 3) | (((r2 >> 8) & 3) << 2)));
    crtc(0x37, (u8) y);
    crtc(0x38, (u8) end);
    crtc(0x39, (u8) (((y >> 8) & 3) | (((end >> 8) & 3) << 2)));
    crtc(0x3a, (u8) addr);
    crtc(0x3b, (u8) (addr >> 8));
    crtc(0x3c, (u8) (((addr >> 16) & 0x0f) | ((pitch >> 3) & 0x20)));
    crtc(0x3d, (u8) pitch);
    /* The key: colour key mode 0 (CR1D bits 3-5), the compare value in GR0C */
    crtc(0x1d, (u8) (crtc_read(0x1d) & ~0x38));
    gr(0x0c, KEY);
    crtc(0x3e, (u8) (1u | (format << 1) | (keyed ? 0x80u : 0)));
}

void test_main(void) {
    __asm__ volatile("fninit");
    /* A Cirrus: SR6 unlocks the extensions and reads back 12h */
    outw(0x3c4, 0x1206);
    outb(0x3c4, 0x06);
    if (inb(0x3c5) != 0x12)
        return;
    int10(0x005f, 0, 0, 0, 0, 0);
    outb(0x3d4, 0x01);
    if (inb(0x3d5) != 0x4f)
        return;
    outw(0x3c4, 0x1206);
    const u8 id = crtc_read(0x27) & 0xfc;
    if (id < 0x90)
        return;
    dwords = (id >= 0xb8);
    gr(0x0b, 0x00); /* one 64K window, 4K offsets */

    for (u32 y = 0; y < H; y++)
        for (u32 x = 0; x < W; x++)
            vram8(y * W + x, ((y >= 200) && (y < 260) && (x >= 60)) ? (u8) KEY : (u8) pattern(x, y, 0x61));
    for (u32 i = 0; i < SRC_W * SRC_H * 2; i++)
        vram8(SRC + i, (u8) pattern(i % (SRC_W * 2), i / (SRC_W * 2), 0x62));

    static const u32 passes[5][7] = {
        /* x, w, y, h, format, zoom, keyed */
        { 100, 304, 60, 200, 5, 256, 0 },
        { 100, 304, 160, 200, 5, 256, 1 },
        { 40, 560, 40, 400, 5, 128, 0 },
        { 160, 240, 100, 180, 0, 256, 0 },
        { 500, 304, 300, 150, 5, 256, 0 },
    };
    for (u32 p = 0; p < 5; p++) {
        window(passes[p][0], passes[p][1], passes[p][2], passes[p][3], passes[p][4], passes[p][5], passes[p][6]);
        wait_ticks(6);
    }
    crtc(0x3e, 0);
}
