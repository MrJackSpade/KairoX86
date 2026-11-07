/*
 * KairoX86's Voodoo Banshee / Voodoo3 2D test (KairoX86#283, for #278): on a 3dfx Banshee or Voodoo3 (PCI 121Ah:
 * 0003h, 0004h, 0005h), VESA 640 x 480 x 16 with its linear frame buffer (as v3d.c), and the 2D engine's passes at
 * each destination format (8, 16, 24 and 32 bits, the stride 640 pixels, from the frame buffer's start) over a clear
 * through the linear frame buffer, each held four ticks of the BIOS clock and copied into memory above 1 MB for the
 * end state: rectangle fills through raster operations with the mono pattern, and with the destination colour key
 * choosing between operations; screen-to-screen blits in every direction, overlapping, a smear, and through the
 * source colour key; host colour and mono data; lines. The engine's status is never read. Any other card returns at
 * once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    return inl(0xcfc);
}

/* The 2D registers (BAR 0 + 1 MB) */
enum { CLIP0_MIN = 0x08, CLIP0_MAX = 0x0c, DST_BASE = 0x10, DST_FORMAT = 0x14, SRC_KEY_MIN = 0x18, SRC_KEY_MAX = 0x1c,
       DST_KEY_MIN = 0x20, DST_KEY_MAX = 0x24, ROP = 0x30, SRC_BASE = 0x34, COMMAND_EXTRA = 0x38, PATTERN0 = 0x44,
       PATTERN1 = 0x48, SRC_FORMAT = 0x54, SRC_XY = 0x5c, COLOR_BACK = 0x60, COLOR_FORE = 0x64, DST_SIZE = 0x68,
       DST_XY = 0x6c, COMMAND = 0x70, LAUNCH = 0x80 };
/* COMMAND */
#define C_S2S       1u
#define C_H2S       3u
#define C_RECTFILL  5u
#define C_LINE      6u
#define INITIATE    (1u << 8)
#define PAT_MONO    (1u << 13)
#define DX          (1u << 14)
#define DY          (1u << 15)
#define ROP0(r)     ((u32) (r) << 24)
/* COMMAND_EXTRA */
#define SRC_KEYED 1u
#define DST_KEYED 2u
/* formats: the colour in bits 19:16 */
#define COL_MONO 0u
#define PACK_DWORD (2u << 22)

#define W 640
#define H 480

static volatile u32 *r2d;
static volatile u8  *fb;
static u32           col, bytes;
static u32           readback = 0x100000;

static void reg(u32 offset, u32 value) { r2d[offset / 4] = value; }
static u32  colour(u32 v) { return (bytes == 4) ? v : (v & ((1u << (bytes * 8)) - 1)); }
static u32  xy(u32 x, u32 y) { return (y << 16) | x; }

static void clear(u32 salt) {
    for (u32 i = 0; i < W * H * bytes / 4; i++)
        ((volatile u32 *) fb)[i] = pattern(i % 160, i / 160, salt);
}

static void copy_out(void) {
    for (u32 i = 0; i < W * H * bytes / 4; i++)
        ((volatile u32 *) readback)[i] = ((volatile u32 *) fb)[i];
    readback += W * H * bytes;
}

static void fill(u32 rop, u32 x, u32 y, u32 w, u32 h) {
    reg(DST_SIZE, xy(w, h));
    reg(DST_XY, xy(x, y));
    reg(COMMAND, C_RECTFILL | INITIATE | PAT_MONO | ROP0(rop));
}

static const u8 rops[32] = { 0x00, 0x05, 0x0a, 0x0f, 0x33, 0x50, 0x55, 0x5a, 0x5f, 0x66, 0x88, 0x99, 0xa0, 0xa5,
                             0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xf0, 0xf5, 0xfa, 0xff, 0x1a, 0x3c, 0x69, 0x96, 0xb8,
                             0xc3, 0xe2, 0x2d, 0x87 };

static void p_fills(u32 salt) {
    reg(PATTERN0, 0x81422418u ^ salt);
    reg(PATTERN1, 0x18244281u);
    reg(COLOR_BACK, colour(pattern(1, 1, salt)));
    for (u32 r = 0; r < 32; r++) {
        reg(COLOR_FORE, colour(pattern(r, 2, salt)));
        fill(rops[r], 8 + (r % 8) * 78, 8 + (r / 8) * 58, 70, 50);
    }
    /* The destination key: rops[1] (in ROP) where the destination lies in the range, rops[0] elsewhere */
    reg(COMMAND_EXTRA, DST_KEYED);
    reg(DST_KEY_MIN, 0);
    reg(DST_KEY_MAX, colour(0x7f7f7f7fu));
    reg(ROP, 0x00f0f055u); /* rops[1] 55h (bits 7:0), rops[2] and rops[3] F0h */
    reg(COLOR_FORE, colour(pattern(3, 3, salt)));
    fill(0xf0, 20, 260, 600, 100);
    reg(COMMAND_EXTRA, 0);
}

static void blit(u32 cmd, u32 sx, u32 sy, u32 dx, u32 dy, u32 w, u32 h) {
    reg(SRC_XY, xy(sx, sy));
    reg(DST_SIZE, xy(w, h));
    reg(DST_XY, xy(dx, dy));
    reg(COMMAND, C_S2S | INITIATE | cmd);
}

static void p_blits(u32 salt) {
    for (u32 k = 0; k < 8; k++) {
        const u32 sx = 20 + (k % 4) * 150, sy = 20 + (k / 4) * 220, w = 100, h = 90;
        const u32 ox = (k & 4) ? 9 : 40, oy = (k & 4) ? 5 : 100;
        /* walking from the right (DX) and/or the bottom (DY): the start is that corner */
        const u32 dxm = (k & 1) ? DX : 0, dym = (k & 2) ? DY : 0;
        const u32 fx = dxm ? w - 1 : 0, fy = dym ? h - 1 : 0;
        static const u8 brops[8] = { 0xcc, 0x66, 0x88, 0xee, 0x33, 0xcc, 0x99, 0xcc };
        blit(dxm | dym | ROP0(brops[k]), sx + fx, sy + fy, sx + ox + fx, sy + oy + fy, w, h);
    }
    /* A smear: a copy 3 pixels right, left to right, reading what it has just drawn */
    blit(ROP0(0xcc), 20, 440, 23, 440, 200, 20);
    /* Through the source key: rops[2] where the source lies in the range */
    reg(COMMAND_EXTRA, SRC_KEYED);
    reg(SRC_KEY_MIN, 0);
    reg(SRC_KEY_MAX, colour(0x80808080u));
    reg(ROP, 0x0000aa00u); /* rops[2] AAh (bits 15:8) */
    blit(ROP0(0xcc), 300, 300, 340, 330, 160, 100);
    reg(COMMAND_EXTRA, 0);
    (void) salt;
}

static void p_host(u32 salt) {
    /* Colour, a row a whole number of words (64 pixels) */
    reg(SRC_FORMAT, (64 * bytes) | (col << 16) | PACK_DWORD);
    reg(SRC_XY, 0);
    reg(DST_SIZE, xy(64, 60));
    reg(DST_XY, xy(20, 20));
    reg(COMMAND, C_H2S | ROP0(0xcc));
    for (u32 i = 0; i < 64 * bytes / 4 * 60; i++)
        reg(LAUNCH + (i & 0x1f) * 4, pattern(i, 4, salt));
    /* Mono: two words a row, the foreground and background colours */
    reg(COLOR_FORE, colour(pattern(1, 5, salt)));
    reg(COLOR_BACK, colour(pattern(2, 5, salt)));
    reg(SRC_FORMAT, 8 | (COL_MONO << 16) | PACK_DWORD);
    reg(DST_SIZE, xy(64, 60));
    reg(DST_XY, xy(100, 20));
    reg(COMMAND, C_H2S | ROP0(0x66));
    for (u32 i = 0; i < 2 * 60; i++)
        reg(LAUNCH + (i & 0x1f) * 4, pattern(i, 6, salt));
    reg(SRC_FORMAT, (W * bytes) | (col << 16));
}

static void p_lines(u32 salt) {
    for (u32 l = 0; l < 16; l++) {
        const u32 x0 = 160 + (l % 4) * 100, y0 = 120 + (l / 4) * 90;
        const int dx = ((l & 1) ? 1 : -1) * (int) (30 + l * 5), dy = ((l & 2) ? 1 : -1) * (int) (60 - l * 3);
        reg(COLOR_FORE, colour(pattern(l, 7, salt)));
        reg(COMMAND, C_LINE | ROP0((l & 4) ? 0x66 : 0xcc));
        reg(SRC_XY, xy(x0, y0));
        reg(LAUNCH, xy((u32) ((int) x0 + dx), (u32) ((int) y0 + dy)));
    }
}

void test_main(void) {
    __asm__ volatile("fninit");
    u32 mmio = 0, lfb = 0;
    for (u32 bus = 0; bus < 2 && !mmio; bus++)
        for (u32 dev = 0; dev < 32 && !mmio; dev++) {
            const u32 id = pci_read(bus, dev, 0, 0);
            if ((id & 0xffff) == 0x121a && ((id >> 16) == 0x0003 || (id >> 16) == 0x0005 || (id >> 16) == 0x0004)) {
                mmio = pci_read(bus, dev, 0, 0x10) & ~0xfu;
                lfb  = pci_read(bus, dev, 0, 0x14) & ~0xfu;
            }
        }
    if (!mmio)
        return;
    if (int10(0x4f02, 0x4111, 0, 0, 0, 0) != 0x004f)
        return;
    r2d = (volatile u32 *) (mmio + 0x100000);
    fb  = (volatile u8 *) lfb;

    static const u32 cols[4] = { 1, 3, 4, 5 }; /* 8, 16, 24 and 32 bits */
    static void (*const passes[])(u32) = { p_fills, p_blits, p_host, p_lines };
    for (u32 f = 0; f < 4; f++) {
        col   = cols[f];
        bytes = f + 1;
        reg(CLIP0_MIN, 0);
        reg(CLIP0_MAX, xy(W, H));
        reg(DST_BASE, 0);
        reg(DST_FORMAT, (W * bytes) | (col << 16));
        reg(SRC_BASE, 0);
        reg(SRC_FORMAT, (W * bytes) | (col << 16));
        reg(COMMAND_EXTRA, 0);
        for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
            clear(0x50 + p + f * 8);
            passes[p](p + f * 8);
            wait_ticks(4);
            copy_out();
        }
    }
}
