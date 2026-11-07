/*
 * KairoX86's Cirrus Logic GD54xx BitBLT test (KairoX86#283, for #250): on any GD5426 or later (its BIOS's mode 5Fh,
 * 640 x 480 x 8; video memory through the banked window at A000:0000, GR9 its offset), a series of passes through the
 * BitBLT engine, its registers through GR20-GR3F, each over a clear and held four ticks of the BIOS clock: copies
 * forwards and backwards, overlapping, through every raster operation; colour expansion from video memory (opaque,
 * transparent, inverted, with a left skip); pattern copies (colour, colour expanded, solid fill); sources from the
 * host (colour, colour expanded); transparent comparison; at 8, 16, 24 and 32 bits a pixel (the display stays 8: the
 * engine works on bytes). The engine's status is never read: it finishes at once. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

#define WINDOW ((volatile u8 *) 0xa0000)

static u32 pitch;
static u32 bank = 0xffffffffu;

static void gr(u8 index, u8 value) { outw(0x3ce, (u16) (index | (value << 8))); }

/* A byte of video memory through the 64K window, its 4K-granular offset in GR9 */
static volatile u8 *vram_at(u32 addr) {
    const u32 b = addr >> 12;
    if ((b & ~0xfu) != (bank & ~0xfu)) {
        bank = b & ~0xfu;
        gr(0x09, (u8) bank);
    }
    return WINDOW + (addr - (bank << 12));
}

static void clear(u32 salt) {
    for (u32 a = 0; a < 0x80000; a += 4)
        *(volatile u32 *) vram_at(a) = pattern((a >> 2) & 255, a >> 10, salt);
}

/* BitBLT registers */
static void blt(u32 dst, u32 src, u32 w_bytes, u32 h, u32 dpitch, u32 spitch, u8 mode, u8 rop, u8 skip, u8 ext) {
    gr(0x20, (u8) (w_bytes - 1));
    gr(0x21, (u8) ((w_bytes - 1) >> 8));
    gr(0x22, (u8) (h - 1));
    gr(0x23, (u8) ((h - 1) >> 8));
    gr(0x24, (u8) dpitch);
    gr(0x25, (u8) (dpitch >> 8));
    gr(0x26, (u8) spitch);
    gr(0x27, (u8) (spitch >> 8));
    gr(0x28, (u8) dst);
    gr(0x29, (u8) (dst >> 8));
    gr(0x2a, (u8) (dst >> 16));
    gr(0x2c, (u8) src);
    gr(0x2d, (u8) (src >> 8));
    gr(0x2e, (u8) (src >> 16));
    gr(0x2f, skip);
    gr(0x30, mode);
    gr(0x32, rop);
    gr(0x33, ext);
    gr(0x31, 0x02); /* start */
}

static void colours(u32 fg, u32 bg) {
    gr(0x01, (u8) fg);
    gr(0x11, (u8) (fg >> 8));
    gr(0x13, (u8) (fg >> 16));
    gr(0x15, (u8) (fg >> 24));
    gr(0x00, (u8) bg);
    gr(0x10, (u8) (bg >> 8));
    gr(0x12, (u8) (bg >> 16));
    gr(0x14, (u8) (bg >> 24));
}

static const u8 rops[] = { 0x0d, 0x59, 0x6d, 0x05, 0x50, 0x90, 0xda, 0x95, 0xad, 0xd0, 0xd6, 0x09, 0x0b, 0x0e, 0x00, 0x06 };

/* The pixel width code (GR30 bits 5:4) and its bytes */
static u8 pw_code;
static u32 pw;

static void p_copies(u32 salt) {
    for (u32 k = 0; k < 16; k++) {
        const u32 x = 8 + (k % 4) * 150, y = 8 + (k / 4) * 110;
        const u32 w = (100 / pw) * pw, h = 90;
        const u32 src = (300 + k * 3) * pitch + 20 + k * 5 + (salt & 1);
        blt(y * pitch + x, src, w, h, pitch, pitch, pw_code, rops[k], 0, 0);
    }
    /* Overlapping, forwards and backwards (the addresses the last byte's) */
    blt(400 * pitch + 30, 396 * pitch + 20, 200, 60, pitch, pitch, pw_code, 0x0d, 0, 0);
    blt((400 + 59) * pitch + 300 + 199, (404 + 59) * pitch + 310 + 199, 200, 60, pitch, pitch, (u8) (pw_code | 0x01), 0x0d, 0, 0);
}

static void p_expand(u32 salt) {
    colours(pattern(1, 1, salt), pattern(2, 1, salt));
    /* The bits at 470 K, 8 bytes a line */
    for (u32 k = 0; k < 8; k++) {
        const u32 x = 8 + (k % 4) * 150, y = 8 + (k / 4) * 200;
        const u8 mode = (u8) (0x80 | pw_code | ((k & 1) ? 0x08 : 0));
        const u8 ext = (u8) ((k & 2) ? 0x02 : 0);
        blt(y * pitch + x, 470u * 1024u + k * 64, 64 * pw, 120, pitch, 8, mode, rops[k], (u8) (k * 3), ext);
    }
}

static void p_patterns(u32 salt) {
    colours(pattern(3, 1, salt), pattern(4, 1, salt));
    for (u32 k = 0; k < 9; k++) {
        const u32 x = 8 + (k % 3) * 200, y = 8 + (k / 3) * 150;
        u8 mode = (u8) (0x40 | pw_code);
        u8 ext  = 0;
        u32 src = 480u * 1024u + k * 256;
        if (k % 3 == 1)
            mode |= 0x80;
        if (k % 3 == 2) {
            mode |= 0x80;
            ext = 0x04; /* solid fill */
        }
        if (k >= 6)
            mode |= 0x08;
        blt(y * pitch + x, src | (k & 7), (180 / pw) * pw, 130, pitch, 0, mode, rops[k], (u8) (k & 7), ext);
    }
}

static void p_host(u32 salt) {
    colours(pattern(5, 1, salt), pattern(6, 1, salt));
    const u32 w = (90 / pw) * pw, h = 40;
    blt(20 * pitch + 20, 0, w, h, pitch, 0, (u8) (0x04 | pw_code), 0x0d, 0, 0);
    for (u32 i = 0; i < (w * h + 3) / 4; i++)
        *(volatile u32 *) WINDOW = pattern(i, 3, salt);
    blt(20 * pitch + 300, 0, 120 * pw, 60, pitch, 0, (u8) (0x84 | pw_code), 0x59, 2, 0);
    for (u32 i = 0; i < 60 * 4; i++)
        *(volatile u32 *) WINDOW = pattern(i, 4, salt);
    bank = 0xffffffffu;
}

static void p_transparent(u32 salt) {
    gr(0x34, (u8) pattern(7, 1, salt));
    gr(0x35, (u8) pattern(8, 1, salt));
    gr(0x38, 0x0f);
    gr(0x39, 0xf0);
    for (u32 k = 0; k < 4; k++)
        blt((20 + k * 110) * pitch + 20, (300 + k * 20) * pitch + 40, (200 / pw) * pw, 100, pitch, pitch, (u8) (0x08 | pw_code),
            0x0d, 0, 0);
    for (u32 k = 0; k < 4; k++)
        blt((20 + k * 110) * pitch + 300, 480u * 1024u + k * 256, (200 / pw) * pw, 100, pitch, 0, (u8) (0x48 | pw_code), 0x0d,
            0, 0);
}

void test_main(void) {
    __asm__ volatile("fninit");
    /* A Cirrus: SR6 unlocks the extensions and reads back 12h */
    outw(0x3c4, 0x1206);
    outb(0x3c4, 0x06);
    if (inb(0x3c5) != 0x12)
        return;
    /* The Cirrus BIOS's mode 5Fh, 640 wide: CRTC 01h (horizontal display end) 4Fh */
    int10(0x005f, 0, 0, 0, 0, 0);
    outb(0x3d4, 0x01);
    if (inb(0x3d5) != 0x4f)
        return;
    pitch = 640;
    outw(0x3c4, 0x1206);
    gr(0x0b, 0x00); /* one 64K window, 4K offsets */

    static const u8 codes[] = { 0x00, 0x10, 0x20, 0x30 };
    for (u32 c = 0; c < 4; c++) {
        pw_code = codes[c];
        pw      = c + 1;
        static void (*const passes[])(u32) = { p_copies, p_expand, p_patterns, p_host, p_transparent };
        for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
            const u32 salt = 0x20 + c * 8 + p;
            clear(salt);
            passes[p](salt);
            wait_ticks(4);
        }
    }
}
