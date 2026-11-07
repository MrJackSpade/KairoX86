/*
 * KairoX86's Western Digital WD90C33 drawing engine test (KairoX86#267): on a WD90C33 (its index register at 23C0h
 * reads back with a block above 3 flagged), the engine through its ports (23C0h index, 23C2h registers, 23C4h host
 * data, 23C8h-23CCh the Bresenham terms), every picture drawn by it, in passes each held four ticks of the BIOS clock:
 * in 256 colours (the BIOS's mode 5Fh) with byte pixels fills through all 16 raster operations and the plane mask,
 * host colour data, screen copies both ways and overlapping, colour expansion from the screen with and without its
 * background, mono host data, the destination compare both ways, the 8 x 8 pattern, clipping, line strips, trapezoids
 * and Bresenham lines; then the same screen with word pixels (fills, copies, host data, mono data and lines); then in
 * 16 colours (mode 12h, planar) fills, copies, host data, mono data and lines. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

/* Block 1 */
enum { CONTROL1, CONTROL2, SRC_X, SRC_Y, DST_X, DST_Y, DIM_X, DIM_Y, ROP, CLIP_L, CLIP_R, CLIP_T, CLIP_B };
/* Block 3 */
enum { MAP_BASE, ROW_PITCH, FG0, FG1, BG0, BG1, TC0, TC1, TM0, TM1, M0, M1 };
/* CONTROL1 */
#define M_BITBLT    (1u << 9)
#define M_STRIP     (2u << 9)
#define M_TRAP      (3u << 9)
#define M_BRESENHAM (4u << 9)
#define X_REV       0x100u
#define Y_REV       0x080u
#define Y_MAJOR     0x040u
#define HOST        0x020u
#define PATTERN     0x004u
#define LAST_SKIP   0x001u
#define F_COLOR     (0u << 3)
#define F_EXP       (1u << 3)
#define F_FG        (2u << 3)
#define F_MONO      (3u << 3)
/* CONTROL2 */
#define DST_CMP   0x200u
#define CMP_MATCH 0x100u
#define MONO_SKIP 0x080u
#define BITS8     0x004u /* mono host data: eight bits a byte */

static u32 depth, width, height, pmask;

static void reg(u32 block, u32 index, u32 v) {
    outw(0x23c0, (u16) block);
    outw(0x23c2, (u16) ((index << 12) | (v & 0xfff)));
}

static void colours(u32 fg, u32 bg, u32 tc, u32 tm, u32 mask) {
    reg(3, MAP_BASE, 0);
    reg(3, ROW_PITCH, width);
    reg(3, FG0, fg & 0xff);
    reg(3, FG1, fg >> 8);
    reg(3, BG0, bg & 0xff);
    reg(3, BG1, bg >> 8);
    reg(3, TC0, tc & 0xff);
    reg(3, TC1, tc >> 8);
    reg(3, TM0, tm & 0xff);
    reg(3, TM1, tm >> 8);
    reg(3, M0, mask & 0xff);
    reg(3, M1, mask >> 8);
}

static void clip(u32 l, u32 t, u32 r, u32 b) {
    reg(1, CLIP_L, l);
    reg(1, CLIP_T, t);
    reg(1, CLIP_R, r);
    reg(1, CLIP_B, b);
}

/* Everything but the start */
static void setup(u32 c2, u32 sx, u32 sy, u32 dx, u32 dy, u32 w, u32 h, u32 rop) {
    reg(1, CONTROL2, c2 | (depth << 10));
    reg(1, SRC_X, sx);
    reg(1, SRC_Y, sy);
    reg(1, DST_X, dx);
    reg(1, DST_Y, dy);
    reg(1, DIM_X, w - 1);
    reg(1, DIM_Y, h - 1);
    reg(1, ROP, rop << 8);
}

static void start(u32 c1) { reg(1, CONTROL1, c1); }

static void fill(u32 x, u32 y, u32 w, u32 h, u32 colour, u32 rop, u32 mask) {
    colours(colour, 0, 0, 0xffff, mask);
    setup(0, 0, 0, x, y, w, h, rop);
    start(M_BITBLT | F_FG);
}

static void clear(u32 salt) {
    clip(0, 0, width - 1, height - 1);
    fill(0, 0, width, height, pattern(0, 0, salt) & pmask, 0x3 /* source */, 0xffff);
    for (u32 i = 0; i < 24; i++)
        fill(pattern(i, 1, salt) % (width - 40), pattern(i, 2, salt) % (height - 40), 8 + pattern(i, 3, salt) % (width / 3),
             8 + pattern(i, 4, salt) % 120, pattern(i, 5, salt) & pmask, 0x3, 0xffff);
}

/* The data sheet's truth table: 0x3 the source, 0x6 xor, 0x9 xnor, 0xc not the source */
static void p_fills(u32 salt) {
    for (u32 rop = 0; rop < 16; rop++)
        fill(10 + (rop % 4) * (width / 4), 20 + (rop / 4) * 110, width / 5, 90, pattern(rop, 7, salt) & pmask, rop, 0xffff);
    fill(30, 40, width / 2, 200, pattern(1, 9, salt) & pmask, 0x3, depth ? 0x3c3c : 0x05);
}

static void host(u32 x, u32 y, u32 w, u32 h, u32 rop, u32 salt) {
    colours(0, 0, 0, 0xffff, 0xffff);
    setup(0, 0, 0, x, y, w, h, rop);
    start(M_BITBLT | HOST | F_COLOR);
    const u32 per = (depth == 2) ? 2 : (depth ? 4 : 8);
    for (u32 row = 0; row < h; row++)
        for (u32 i = 0; i < (w + per - 1) / per; i++) {
            const u32 v = pattern(i, row, salt);
            outw(0x23c4, (u16) v);
            outw(0x23c6, (u16) (v >> 16));
        }
}

static void p_host(u32 salt) {
    host(20, 30, width / 3, 120, 0x3, salt);
    host(width / 2, 200, width / 4, 100, 0x6, salt + 1);
    host(60, 300, 96, 64, 0x9, salt + 2);
}

static void copy(u32 sx, u32 sy, u32 dx, u32 dy, u32 w, u32 h, u32 rop, int reverse) {
    colours(0, 0, 0, 0xffff, 0xffff);
    if (reverse) {
        setup(0, sx + w - 1, sy + h - 1, dx + w - 1, dy + h - 1, w, h, rop);
        start(M_BITBLT | F_COLOR | X_REV | Y_REV);
    } else {
        setup(0, sx, sy, dx, dy, w, h, rop);
        start(M_BITBLT | F_COLOR);
    }
}

static void p_copies(u32 salt) {
    const u32 w = width / 4;
    host(0, 0, w, 100, 0x3, salt);
    copy(0, 0, w + 20, 0, w, 100, 0x3, 0);
    copy(0, 0, 2 * w + 40, 120, w, 100, 0x6, 0);
    copy(5, 10, 25, 20, w - 10, 80, 0x3, 1); /* overlapping, down and right: from the far corner */
    copy(w + 20, 0, w + 10, 5, w - 10, 90, 0x3, 0);
    copy(0, 0, 0, 250, w, 100, 0x9, 0);
    for (u32 i = 0; i < 20; i++)
        copy(i * 4, 250, width / 2 + i * 3, 250 + i * 4, w / 2, 48, 0x3, i & 1);
}

static void p_expand(u32 salt) {
    const u32 w = width / 4;
    host(0, 0, w, 100, 0x3, salt);
    fill(0, 120, w, 60, pattern(0, 0, salt) & pmask, 0x3, 0xffff);
    const u32 tm = depth ? 0xf0f0 : 0x0c;
    colours(0x1111 & pmask, 0x2222 & pmask, salt & pmask, tm, 0xffff);
    setup(0, 0, 0, w + 20, 0, w, 180, 0x3);
    start(M_BITBLT | F_EXP);
    colours(0x3333 & pmask, 0x4444 & pmask, salt & pmask, tm, 0xffff);
    setup(MONO_SKIP, 0, 0, 2 * w + 40, 0, w, 180, 0x6);
    start(M_BITBLT | F_EXP);
}

static void p_mono(u32 salt) {
    for (u32 k = 0; k < 2; k++) {
        const u32 w = width / 3;
        colours((0x5a5a + k) & pmask, (0xa5a5 - k) & pmask, 0, 0xffff, 0xffff);
        setup(BITS8 | (k ? MONO_SKIP : 0), 0, 0, 20 + k * (width / 2), 60, w, 150, 0x3);
        start(M_BITBLT | HOST | F_MONO);
        for (u32 row = 0; row < 150; row++)
            for (u32 i = 0; i < (w + 7) / 8; i++)
                outb(0x23c4, (u8) pattern(i, row, salt + k));
    }
}

static void p_compare(u32 salt) {
    const u32 w = width / 2;
    host(0, 0, w, 240, 0x3, salt);
    colours(0x7777 & pmask, 0, salt & pmask, depth ? 0xc0c0 : 0x08, 0xffff);
    setup(DST_CMP, 0, 0, 0, 0, w, 240, 0x3);
    start(M_BITBLT | F_FG);
    host(w, 240, w, 240, 0x3, salt + 1);
    colours(0x8888 & pmask, 0, salt & pmask, depth ? 0xc0c0 : 0x08, 0xffff);
    setup(DST_CMP | CMP_MATCH, 0, 0, w, 240, w, 240, 0x6);
    start(M_BITBLT | F_FG);
}

static void p_pattern(u32 salt) {
    host(0, 0, 8, 8, 0x3, salt); /* the pattern: 64 pixels at (0, 0) */
    for (u32 i = 0; i < 6; i++) {
        colours(0, 0, 0, 0xffff, 0xffff);
        setup(0, i, 0, 20 + i * (width / 7), 40 + i * 60, 90, 70, (i & 1) ? 0x6 : 0x3);
        start(M_BITBLT | F_COLOR | PATTERN);
    }
}

static void p_clip(u32 salt) {
    clip(width / 8, 60, width - width / 8, 400);
    for (u32 i = 0; i < 12; i++)
        fill(pattern(i, 1, salt) % width, pattern(i, 2, salt) % height, 40 + pattern(i, 3, salt) % (width / 2),
             40 + pattern(i, 4, salt) % 200, pattern(i, 5, salt) & pmask, (i & 1) ? 0x6 : 0x3, 0xffff);
    host(0, 30, width / 2, 100, 0x3, salt);
    clip(0, 0, width - 1, height - 1);
}

static void p_lines(u32 salt) {
    /* Line strips: x-major and y-major, every direction */
    for (u32 i = 0; i < 8; i++) {
        colours(pattern(i, 1, salt) & pmask, 0, 0, 0xffff, 0xffff);
        setup(0, 0, 0, width / 2, 240, 6 + i, 12, (i & 1) ? 0x6 : 0x3);
        start(M_STRIP | ((i & 1) ? X_REV : 0) | ((i & 2) ? Y_REV : 0) | ((i & 4) ? Y_MAJOR : 0));
    }
    /* Trapezoids: a strip a row, its width rewritten each row */
    colours(pattern(2, 2, salt) & pmask, 0, 0, 0xffff, 0xffff);
    setup(0, 0, 0, 30, 20, 10, 1, 0x3);
    start(M_TRAP);
    for (u32 row = 1; row < 100; row++) {
        reg(1, DST_X, 30 + row / 3);
        reg(1, DIM_X, 10 + row);
    }
    /* Bresenham lines from the centre, the last pixel left on odd ones */
    for (u32 i = 0; i < 16; i++) {
        const int dx = (int) (pattern(i, 3, salt) % (width / 2)), dy = (int) (pattern(i, 4, salt) % 220);
        const int ymajor = dy > dx, maj = ymajor ? dy : dx, mnr = ymajor ? dx : dy;
        outw(0x23c8, (u16) ((2 * mnr) & 0x3fff));
        outw(0x23ca, (u16) ((2 * (mnr - maj)) & 0x3fff));
        outw(0x23cc, (u16) ((2 * mnr - maj) & 0x3fff));
        colours(pattern(i, 5, salt) & pmask, 0, 0, 0xffff, 0xffff);
        setup(0, 0, 0, width / 2, 240, maj + 1, 1, (i & 4) ? 0x6 : 0x3);
        start(M_BRESENHAM | ((i & 1) ? X_REV : 0) | ((i & 2) ? Y_REV : 0) | (ymajor ? Y_MAJOR : 0) | ((i & 8) ? LAST_SKIP : 0));
    }
}

void test_main(void) {
    __asm__ volatile("fninit");
    /* A WD90C33: its index register reads back, a block above 3 flagged */
    outw(0x23c0, 0x0104);
    if (inw(0x23c0) != 0x2104)
        return;
    static void (*const all[])(u32) = { p_fills, p_host, p_copies, p_expand, p_mono, p_compare, p_pattern, p_clip, p_lines };
    static void (*const word[])(u32) = { p_fills, p_host, p_copies, p_mono, p_lines };
    static void (*const planar[])(u32) = { p_fills, p_host, p_copies, p_mono, p_lines };
    for (u32 m = 0; m < 3; m++) {
        int10(m == 2 ? 0x12 : 0x5f, 0, 0, 0, 0, 0);
        depth  = (m == 0) ? 1 : (m == 1) ? 2 : 0;
        width  = (m == 1) ? 320 : 640;
        height = 480;
        pmask  = (depth == 2) ? 0xffff : (depth ? 0xff : 0x0f);
        void (*const *passes)(u32) = (m == 0) ? all : (m == 1) ? word : planar;
        const u32 n = (m == 0) ? 9 : 5;
        for (u32 p = 0; p < n; p++) {
            const u32 salt = 0x50 + m * 16 + p;
            clear(salt);
            passes[p](salt);
            wait_ticks(4);
        }
    }
}
