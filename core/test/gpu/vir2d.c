/*
 * KairoX86's S3 ViRGE 2D test (KairoX86#283, for #272): on an S3 ViRGE or Trio3D (PCI 5333h: 5631h, 883Dh, 8A01h,
 * 8A10h, 8A13h), VESA mode 110h with S3's linear addressing (CR58) and the new MMIO window (CR53 bit 3), as vir3d.c,
 * and the 2D engine's passes at each of its pixel formats (8, 16 and 24 bits, the stride 640 pixels) over a clear
 * through the linear frame buffer, each held four ticks of the BIOS clock and copied into memory above 1 MB for the
 * end state: rectangle fills through 64 ternary raster operations; BitBLTs with the mono pattern through operations
 * of the pattern, source and destination, in every direction, overlapping, and a smear; colour and mono data from
 * the host (the image transfer window), opaque and transparent; lines; polygons. The engine's busy bit is never
 * read. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    return inl(0xcfc);
}

enum { SRC_BASE = 0xa4d4, DEST_BASE = 0xa4d8, CLIP_LR = 0xa4dc, CLIP_TB = 0xa4e0, STR = 0xa4e4, MONO_PAT0 = 0xa4e8,
       MONO_PAT1 = 0xa4ec, PAT_BG = 0xa4f0, PAT_FG = 0xa4f4, SRC_BG = 0xa4f8, SRC_FG = 0xa4fc, CMD = 0xa500,
       RWH = 0xa504, RSRC = 0xa508, RDEST = 0xa50c,
       L_CMD = 0xa900, L_PAT_FG = 0xa8f4, L_XEND = 0xa96c, L_DX = 0xa970, L_XSTART = 0xa974, L_YSTART = 0xa978,
       L_YCNT = 0xa97c,
       P_CMD = 0xad00, P_PAT_FG = 0xacf4, P_RDX = 0xad68, P_RXSTART = 0xad6c, P_LDX = 0xad70, P_LXSTART = 0xad74,
       P_YSTART = 0xad78, P_YCNT = 0xad7c };
/* the command */
#define AE          1u
#define HC          (1u << 1)
#define FMT(f)      ((u32) (f) << 2)
#define MS          (1u << 6)
#define IDS         (1u << 7)
#define MP          (1u << 8)
#define TP          (1u << 9)
#define ITA_DWORD   (2u << 10)
#define ROP(r)      ((u32) (r) << 17)
#define XP          (1u << 25)
#define YP          (1u << 26)
#define C_BITBLT    (0u << 27)
#define C_RECTFILL  (2u << 27)
#define C_LINE      (3u << 27)
#define C_POLY      (5u << 27)

#define W 640
#define H 480

static volatile u32 *mmio;
static volatile u8  *fb;
static u32           fmt, bytes;
static u32           readback = 0x100000;

static void reg(u32 offset, u32 value) { mmio[offset / 4] = value; }
static u32  colour(u32 v) { return (bytes == 4) ? v : (v & ((1u << (bytes * 8)) - 1)); }

static void clear(u32 salt) {
    for (u32 i = 0; i < W * H * bytes / 4; i++)
        ((volatile u32 *) fb)[i] = pattern(i % 160, i / 160, salt);
}

static void copy_out(void) {
    for (u32 i = 0; i < W * H * bytes / 4; i++)
        ((volatile u32 *) readback)[i] = ((volatile u32 *) fb)[i];
    readback += W * H * bytes;
}

/* A rectangle of the BitBLT unit: w x h at (dx, dy), from (sx, sy) */
static void blit(u32 cmd, u32 sx, u32 sy, u32 dx, u32 dy, u32 w, u32 h) {
    reg(CMD, cmd | AE | HC | FMT(fmt));
    reg(RWH, ((w - 1) << 16) | h);
    reg(RSRC, (sx << 16) | sy);
    reg(RDEST, (dx << 16) | dy);
}

static const u8 rops[64] = { 0x00, 0x05, 0x0a, 0x0f, 0x11, 0x22, 0x33, 0x44, 0x50, 0x55, 0x5a, 0x5f, 0x66, 0x77, 0x88,
                             0x99, 0xa0, 0xa5, 0xaa, 0xaf, 0xbb, 0xcc, 0xdd, 0xee, 0xf0, 0xf5, 0xfa, 0xff, 0x1a, 0x2d,
                             0x3c, 0x4b, 0x69, 0x78, 0x87, 0x96, 0xa3, 0xb4, 0xb8, 0xc3, 0xca, 0xd2, 0xe1, 0xe2, 0xf6,
                             0x06, 0x12, 0x24, 0x36, 0x48, 0x6c, 0x7e, 0x81, 0x93, 0x9c, 0xac, 0xbe, 0xc5, 0xd8, 0xe4,
                             0x1b, 0x27, 0x39, 0x4e };

static void p_fills(u32 salt) {
    for (u32 r = 0; r < 64; r++) {
        reg(PAT_FG, colour(pattern(r, 1, salt)));
        blit(C_RECTFILL | ROP(rops[r]), 0, 0, 8 + (r % 8) * 78, 8 + (r / 8) * 58, 70, 50);
    }
}

static void p_blits(u32 salt) {
    /* through the mono pattern: operations of pattern, source and destination */
    reg(MONO_PAT0, 0x81422418u ^ salt);
    reg(MONO_PAT1, 0x18244281u);
    reg(PAT_FG, colour(pattern(1, 2, salt)));
    reg(PAT_BG, colour(pattern(2, 2, salt)));
    for (u32 k = 0; k < 8; k++) {
        const u32 sx = 20 + (k % 4) * 150, sy = 20 + (k / 4) * 220, w = 100, h = 90;
        const u32 ox = (k & 4) ? 9 : 40, oy = (k & 4) ? 5 : 100;
        const u32 xp = (k & 1) ? 0 : XP, yp = (k & 2) ? 0 : YP;
        /* the walk starts at the corner it leaves first */
        const u32 fx = xp ? 0 : w - 1, fy = yp ? 0 : h - 1;
        static const u8 brops[8] = { 0xcc, 0xf0, 0xb8, 0xe2, 0x96, 0x5a, 0x66, 0xca };
        blit(C_BITBLT | MP | ROP(brops[k]) | xp | yp, sx + fx, sy + fy, sx + ox + fx, sy + oy + fy, w, h);
    }
    /* A smear: a copy 3 pixels right, left to right, reading what it has just drawn */
    blit(C_BITBLT | ROP(0xcc) | XP | YP, 20, 440, 23, 440, 200, 20);
}

static void p_host(u32 salt) {
    /* Colour, a row a whole number of words (64 pixels) */
    blit(C_BITBLT | IDS | ITA_DWORD | ROP(0xcc) | XP | YP, 0, 0, 20, 20, 64, 60);
    for (u32 i = 0; i < 64 * bytes / 4 * 60; i++)
        mmio[i & 0x1fff] = pattern(i, 3, salt);
    blit(C_BITBLT | IDS | ITA_DWORD | ROP(0x66) | XP | YP, 0, 0, 100, 20, 64, 60);
    for (u32 i = 0; i < 64 * bytes / 4 * 60; i++)
        mmio[i & 0x1fff] = pattern(i, 4, salt);
    /* Mono, opaque and transparent: two words a row */
    reg(SRC_FG, colour(pattern(1, 5, salt)));
    reg(SRC_BG, colour(pattern(2, 5, salt)));
    for (u32 t = 0; t < 2; t++) {
        blit(C_BITBLT | IDS | MS | ITA_DWORD | ROP(0xcc) | XP | YP | (t ? TP : 0), 0, 0, 200 + t * 80, 20, 64, 60);
        for (u32 i = 0; i < 2 * 60; i++)
            mmio[i & 0x1fff] = pattern(i, 6 + t, salt);
    }
}

static void p_lines(u32 salt) {
    /* lines: 12.20 x start and slope, x end clipping both ends */
    for (u32 l = 0; l < 12; l++) {
        const int dx = ((int) l - 6) * 0x40000;
        reg(L_PAT_FG, colour(pattern(l, 8, salt)));
        reg(L_CMD, C_LINE | AE | HC | FMT(fmt) | ROP((l & 1) ? 0x66 : 0xf0));
        reg(L_XEND, ((u32) (50 + l * 40) << 16) | (u32) (10 + l * 40));
        reg(L_DX, (u32) dx);
        reg(L_XSTART, (u32) (30 + l * 40) << 20);
        reg(L_YSTART, 100 + l * 10);
        reg(L_YCNT, 80u | ((l & 2) ? 0x80000000u : 0));
    }
    /* polygons: a trapezoid per call, its sides 12.20 */
    for (u32 p = 0; p < 6; p++) {
        reg(P_PAT_FG, colour(pattern(p, 9, salt)));
        reg(P_CMD, C_POLY | AE | HC | FMT(fmt) | ROP((p & 1) ? 0x5a : 0xf0));
        reg(P_RDX, (u32) (-(int) (p * 0x8000)));
        reg(P_RXSTART, (u32) (200 + p * 70) << 20);
        reg(P_LDX, p * 0x10000);
        reg(P_LXSTART, (u32) (150 + p * 70) << 20);
        reg(P_YSTART, 300 + p * 20);
        reg(P_YCNT, 60u | (3u << 28));
    }
}

void test_main(void) {
    __asm__ volatile("fninit");
    u32 lfb = 0;
    for (u32 bus = 0; bus < 2 && !lfb; bus++)
        for (u32 dev = 0; dev < 32 && !lfb; dev++) {
            const u32 id = pci_read(bus, dev, 0, 0);
            const u32 d  = id >> 16;
            if (((id & 0xffff) == 0x5333) && ((d == 0x5631) || (d == 0x883d) || (d == 0x8a01) || (d == 0x8a10) || (d == 0x8a13)))
                lfb = pci_read(bus, dev, 0, 0x10) & ~0xfu;
        }
    if (!lfb)
        return;
    /* VESA 640 x 480 x 15, S3's linear addressing (CR58) and the new MMIO window (CR53 bit 3), as vir3d.c */
    if (int10(0x4f02, 0x110, 0, 0, 0, 0) != 0x004f)
        return;
    outb(0x3d4, 0x38);
    outb(0x3d5, 0x48);
    outb(0x3d4, 0x39);
    outb(0x3d5, 0xa5);
    outb(0x3d4, 0x58);
    const u8 cr58 = inb(0x3d5);
    outb(0x3d5, (cr58 & ~0x03) | 0x13);
    outb(0x3d4, 0x53);
    const u8 cr53 = inb(0x3d5);
    outb(0x3d5, cr53 | 0x08);
    mmio = (volatile u32 *) (lfb + 0x1000000);
    fb   = (volatile u8 *) lfb;

    static void (*const passes[])(u32) = { p_fills, p_blits, p_host, p_lines };
    for (fmt = 0; fmt < 3; fmt++) {
        bytes = fmt + 1;
        reg(SRC_BASE, 0);
        reg(DEST_BASE, 0);
        reg(CLIP_LR, (0u << 16) | (W - 1));
        reg(CLIP_TB, (0u << 16) | (H - 1));
        reg(STR, ((W * bytes) << 16) | (W * bytes));
        reg(0xa8d8, 0);           /* the line unit's destination base */
        reg(0xa8dc, W - 1);       /* and its clip */
        reg(0xa8e0, H - 1);
        reg(0xa8e4, ((W * bytes) << 16) | (W * bytes));
        reg(0xacd8, 0);           /* the polygon unit's */
        reg(0xacdc, W - 1);
        reg(0xace0, H - 1);
        reg(0xace4, ((W * bytes) << 16) | (W * bytes));
        for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
            clear(0x40 + p + fmt * 8);
            passes[p](p + fmt * 8);
            wait_ticks(4);
            copy_out();
        }
    }
}
