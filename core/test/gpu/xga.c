/*
 * KairoX86's IBM XGA drawing engine test (KairoX86#283, for #280): on the INMOS XGA (ISA), set up as instance 1 through
 * its ISA POS ports, its memory through a 1 MB aperture at 12 MB and its coprocessor in the ROM window (C800:7C80), a
 * series of passes through the engine over a cleared memory: fills and copies through every mix (the arithmetic
 * ones among them), colour compares and plane masks; blits through 1 bpp pattern maps; area fill; copies between maps
 * of 1, 4, 8 and 16 bits a pixel; Bresenham lines in every octant; short-stroke vectors. After each pass the XGA's
 * whole memory is copied into the guest's RAM (2 MB on, 1 MB a pass), which the batch's end state covers: the XGA's
 * own picture is not set up. The engine's status is never read: it finishes at once. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

#define IO       0x2110u                          /* instance 1 */
#define APERTURE ((volatile u32 *) 0x00c00000u)   /* 1 MB at 12 MB */
#define COP      ((volatile u32 *) (0xc8000u + 0x7c00u + 0x80u))
#define MAPS     0x00400000u                      /* the maps' addresses: instance 1's 4 MB window */

static void cop(u32 off, u32 v) { COP[off / 4] = v; }
static void cop8(u32 off, u8 v) { ((volatile u8 *) COP)[off] = v; }

enum { CONTROL = 0x11, MAP_IDX = 0x12, MAP_BASE = 0x14, MAP_WH = 0x18, MAP_FMT = 0x1c, BRES_ERR = 0x20, BRES_K1 = 0x24,
       BRES_K2 = 0x28, SHORT_STROKE = 0x2c, MIX = 0x48, COLOR_CMP = 0x4c, PLANE_MASK = 0x50, FG = 0x58, BG = 0x5c, BLT_WH = 0x60,
       SRC_XY = 0x70, PAT_XY = 0x74, DST_XY = 0x78, COMMAND = 0x7c };
/* COMMAND */
#define OCTANT(o)  ((u32) (o))
#define PAT(m)     ((u32) (m) << 12)
#define DST(m)     ((u32) (m) << 16)
#define SRC(m)     ((u32) (m) << 20)
#define OP(o)      ((u32) (o) << 24)
#define FG_SRC     (2u << 28)
#define BG_SRC     (2u << 30)
#define PAT_FG     8u
enum { OP_SHORT_STROKE = 4, OP_LINE = 5, OP_BITBLT = 8, OP_AREA_FILL = 0x0a };

static void map(u32 idx, u32 offset, u32 w, u32 h, u32 fmt) {
    cop8(MAP_IDX, (u8) idx);
    cop(MAP_BASE, MAPS + offset);
    cop(MAP_WH, (w - 1) | ((h - 1) << 16));
    cop(MAP_FMT, fmt);
}

static void mixes(u32 fg, u32 bg, u32 cc) { cop(MIX, fg | (bg << 8) | (cc << 16)); }

static void blt(u32 cmd, u32 dx, u32 dy, u32 sx, u32 sy, u32 px, u32 py, u32 w, u32 h) {
    cop(SRC_XY, sx | (sy << 16));
    cop(PAT_XY, px | (py << 16));
    cop(DST_XY, dx | (dy << 16));
    cop(BLT_WH, (w - 1) | ((h - 1) << 16));
    cop(COMMAND, cmd);
}

static void clear(u32 salt) {
    for (u32 i = 0; i < 0x100000 / 4; i++)
        APERTURE[i] = pattern(i & 255, i >> 8, salt);
}

/* The XGA's memory into RAM, where the end state covers it */
static void keep(u32 pass) {
    volatile u32 *to = (volatile u32 *) (0x200000u + pass * 0x100000u);
    for (u32 i = 0; i < 0x100000 / 4; i++)
        to[i] = APERTURE[i];
}

static void p_fills(u32 salt) {
    for (u32 m = 0; m < 22; m++) {
        cop(FG, pattern(m, 1, salt));
        cop(COLOR_CMP, pattern(m, 2, salt) & 0xff);
        cop(PLANE_MASK, (m & 1) ? 0xf3 : 0xff);
        mixes(m, 5, (m % 8));
        blt(OP(OP_BITBLT) | PAT(PAT_FG) | DST(1) | SRC(1), 10 + (m % 6) * 100, 10 + (m / 6) * 110, 0, 0, 0, 0, 90, 100);
    }
}

static void p_copies(u32 salt) {
    (void) salt;
    cop(PLANE_MASK, 0xff);
    for (u32 m = 0; m < 22; m++) {
        mixes(m, 5, 4);
        blt(OP(OP_BITBLT) | PAT(PAT_FG) | DST(1) | SRC(1) | FG_SRC | OCTANT((m & 3) << 1), 10 + (m % 6) * 100 + ((m & 4) ? 89 : 0),
            10 + (m / 6) * 110 + ((m & 2) ? 99 : 0), 300 + m * 3, 200 + m * 5, 0, 0, 90, 100);
    }
    /* Overlapping, the walk starting at the corner it leaves first */
    mixes(3, 5, 4);
    blt(OP(OP_BITBLT) | PAT(PAT_FG) | DST(1) | SRC(1) | FG_SRC, 40, 300, 30, 290, 0, 0, 120, 100);
    blt(OP(OP_BITBLT) | PAT(PAT_FG) | DST(1) | SRC(1) | FG_SRC | OCTANT(6), 400 + 119, 300 + 99, 410 + 119, 310 + 99, 0, 0, 120, 100);
}

static void p_patterns(u32 salt) {
    cop(FG, pattern(1, 3, salt));
    cop(BG, pattern(2, 3, salt));
    for (u32 k = 0; k < 6; k++) {
        mixes(3 + (k & 1) * 3, (k & 2) ? 5 : 3, 4);
        blt(OP(OP_BITBLT) | PAT(2) | DST(1) | SRC(1) | ((k & 4) ? (FG_SRC | BG_SRC) : 0), 20 + (k % 3) * 200, 20 + (k / 3) * 200,
            100 + k * 9, 250, k * 3, k, 180, 170);
    }
    /* Area fill: the pattern map's bits toggle filling along each line */
    mixes(3, 5, 4);
    blt(OP(OP_AREA_FILL) | PAT(2) | DST(1) | SRC(1), 300, 420, 0, 0, 0, 0, 16, 16);
}

static void p_formats(u32 salt) {
    (void) salt;
    mixes(3, 5, 4);
    /* 8 bpp into 1, 4 and 16 bpp maps, and back */
    blt(OP(OP_BITBLT) | PAT(PAT_FG) | DST(2) | SRC(1) | FG_SRC, 0, 0, 10, 10, 0, 0, 16, 16);
    blt(OP(OP_BITBLT) | PAT(PAT_FG) | DST(3) | SRC(1) | FG_SRC, 3, 5, 50, 60, 0, 0, 100, 80);
    map(0, 0xa0000, 200, 100, 4); /* map A as 16 bpp */
    blt(OP(OP_BITBLT) | PAT(PAT_FG) | DST(0) | SRC(1) | FG_SRC, 1, 1, 200, 100, 0, 0, 150, 90);
    mixes(6, 5, 4);
    blt(OP(OP_BITBLT) | PAT(PAT_FG) | DST(1) | SRC(3) | FG_SRC, 300, 10, 0, 0, 0, 0, 100, 80);
    blt(OP(OP_BITBLT) | PAT(PAT_FG) | DST(1) | SRC(2) | FG_SRC, 500, 10, 0, 0, 0, 0, 16, 16);
}

static void p_lines(u32 salt) {
    cop(FG, pattern(4, 3, salt));
    mixes(3, 5, 4);
    for (u32 o = 0; o < 8; o++) {
        const int major = 120, minor = 25 + (int) o * 11;
        cop(BRES_K1, (u32) (2 * minor) & 0x3fff);
        cop(BRES_K2, (u32) (2 * (minor - major)) & 0x3fff);
        cop(BRES_ERR, (u32) (2 * minor - major) & 0x3fff);
        cop(DST_XY, (160 + (o % 4) * 100) | ((140 + (o / 4) * 200) << 16));
        cop(BLT_WH, (u32) major);
        cop(COMMAND, OP(OP_LINE) | PAT(PAT_FG) | DST(1) | SRC(1) | OCTANT(o) | ((o & 1) ? 0x10u : 0));
    }
    /* Short strokes: the command first, then four vectors a write */
    cop(DST_XY, 300 | (400 << 16));
    cop(COMMAND, OP(OP_SHORT_STROKE) | PAT(PAT_FG) | DST(1) | SRC(1));
    for (u32 i = 0; i < 8; i++)
        cop(SHORT_STROKE, 0x1f1f1f1fu | ((i & 7) << 5) | (((i + 2) & 7) << 13) | (((i + 4) & 7) << 21) | (((i + 6) & 7) << 29));
}

void test_main(void) {
    __asm__ volatile("fninit");
    /* The INMOS XGA: its ISA POS, instance 1, the 1 MB aperture at 12 MB, the coprocessor at C800:7C80 */
    outb(0x96, 0x09);
    outb(0x105, 0x0c);
    outb(0x104, 0x00);
    outb(0x102, 0x41);
    if (inb(0x102) == 0xff)
        return;
    outb(IO + 0, 0x04); /* extended graphics */
    outb(IO + 1, 0x00); /* no 64K aperture */
    outb(IO + 0x0a, 0x51);
    outb(IO + 0x0b, 0x03); /* the XGA on */
    outb(IO + 0x09, 0x03); /* access mode: 8 bpp, Intel order */
    /* The memory answers through the aperture */
    APERTURE[0] = 0x5a3c96e1u;
    if (APERTURE[0] != 0x5a3c96e1u)
        return;

    cop8(CONTROL, 0);
    map(1, 0x00000, 640, 480, 3);    /* map A: the 8 bpp page */
    map(2, 0x80000, 16, 16, 0);      /* map B: a 1 bpp pattern */
    map(3, 0x90000, 128, 96, 2);     /* map C: 4 bpp */
    map(0, 0xa0000, 200, 100, 4);    /* map A' (mask map's slot): 16 bpp */

    static void (*const passes[])(u32) = { p_fills, p_copies, p_patterns, p_formats, p_lines };
    for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
        clear(0x60 + p);
        passes[p](p);
        keep(p);
    }
}
