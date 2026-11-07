/*
 * KairoX86's Western Digital WD90C31 BitBLT test (KairoX86#283, for #267): on a WD90C31 (its index register at 23C0h
 * reads back), the engine through its ports (23C0h index, 23C2h registers, 23C4h host data), every picture drawn by it,
 * in passes each held four ticks of the BIOS clock: in 256 colours (the BIOS's mode 5Fh, packed pixels) fills through
 * all 16 raster operations and the plane mask, host colour data, screen copies in both directions and overlapping,
 * colour expansion from the screen with and without its background, mono host data, the destination compare both
 * ways, the 8 x 8 pattern source; then in 16 colours (mode 12h, planar) fills, copies, host data and mono host data.
 * The engine's busy bit is never read: video-to-video operations end at once. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

enum { CONTROL1, CONTROL2, SRC_LO, SRC_HI, DST_LO, DST_HI, WIDTH, HEIGHT, PITCH, ROP, FG, BG, TRANS_COLOR, TRANS_MASK, MASK };
/* CONTROL1 */
#define START   0x800u
#define REVERSE 0x400u
#define PACKED  0x100u
#define HOST    0x002u
#define F_COLOR (0u << 2) /* the source's colour */
#define F_EXP   (1u << 2) /* colour expanded where it matches the transparency colour */
#define F_FG    (2u << 2) /* the foreground colour */
#define F_MONO  (3u << 2) /* mono host data */
/* CONTROL2 */
#define PATTERN   0x010u
#define MONO_SKIP 0x008u
#define CMP_MATCH 0x004u
#define DST_CMP   0x001u

static u32 packed, pitch;

static void sel(u16 block) { outw(0x23c0, block); }
static void reg(u32 index, u32 v) { outw(0x23c2, (u16) ((index << 12) | (v & 0xfff))); }

/* Everything but the start; the source and destination pixel addresses as x, y */
static void setup(u32 c2, u32 sx, u32 sy, u32 dx, u32 dy, u32 w, u32 h, u32 rop, u32 fg, u32 bg, u32 tc, u32 tm, u32 mask) {
    const u32 src = sy * pitch + sx, dst = dy * pitch + dx;
    sel(1);
    reg(CONTROL2, c2);
    reg(SRC_LO, src & 0xfff);
    reg(SRC_HI, src >> 12);
    reg(DST_LO, dst & 0xfff);
    reg(DST_HI, dst >> 12);
    reg(WIDTH, w);
    reg(HEIGHT, h);
    reg(PITCH, pitch);
    reg(ROP, rop << 8);
    reg(FG, fg);
    reg(BG, bg);
    reg(TRANS_COLOR, tc);
    reg(TRANS_MASK, tm);
    reg(MASK, mask);
}

static void start(u32 c1) { reg(CONTROL1, c1 | (packed ? PACKED : 0) | START); }

static void fill(u32 x, u32 y, u32 w, u32 h, u32 colour, u32 rop, u32 mask) {
    setup(0, 0, 0, x, y, w, h, rop, colour, 0, 0, 0xff, mask);
    start(F_FG);
}

static void clear(u32 salt) {
    fill(0, 0, 640, 480, salt, 0x3 /* source */, 0xff);
    for (u32 i = 0; i < 24; i++)
        fill(pattern(i, 1, salt) % 600, pattern(i, 2, salt) % 440, 8 + pattern(i, 3, salt) % 200, 8 + pattern(i, 4, salt) % 120,
             pattern(i, 5, salt), 0x3, 0xff);
}

static void p_fills(u32 salt) {
    for (u32 rop = 0; rop < 16; rop++)
        fill(20 + (rop % 4) * 150, 20 + (rop / 4) * 110, 130, 90, pattern(rop, 7, salt), rop, packed ? 0xff : 0x0f);
    fill(40, 40, 300, 200, pattern(1, 9, salt), 0x3, packed ? 0x3c : 0x05);
}

/* w x h at (x, y) from the host, its pixels the pattern: four packed or eight planar pixels a pair of words */
static void host(u32 x, u32 y, u32 w, u32 h, u32 rop, u32 salt) {
    setup(0, 0, 0, x, y, w, h, rop, 0, 0, 0, 0xff, 0xff);
    start(HOST | F_COLOR);
    const u32 per = packed ? 4 : 8;
    for (u32 row = 0; row < h; row++)
        for (u32 i = 0; i < (w + per - 1) / per; i++) {
            const u32 v = pattern(i, row, salt);
            outw(0x23c4, (u16) v);
            outw(0x23c4, (u16) (v >> 16));
        }
}

static void p_host(u32 salt) {
    host(30, 30, 200, 120, 0x3, salt);
    host(300, 200, 160, 100, 0x6 /* xor */, salt + 1);
    host(100, 300, 96, 64, 0x9, salt + 2);
}

static void copy(u32 sx, u32 sy, u32 dx, u32 dy, u32 w, u32 h, u32 rop, int reverse) {
    if (reverse) {
        setup(0, sx + w - 1, sy + h - 1, dx + w - 1, dy + h - 1, w, h, rop, 0, 0, 0, 0xff, 0xff);
        start(F_COLOR | REVERSE);
    } else {
        setup(0, sx, sy, dx, dy, w, h, rop, 0, 0, 0, 0xff, 0xff);
        start(F_COLOR);
    }
}

static void p_copies(u32 salt) {
    host(0, 0, 160, 100, 0x3, salt);
    copy(0, 0, 200, 0, 160, 100, 0x3, 0);
    copy(0, 0, 400, 120, 160, 100, 0x6, 0);
    copy(10, 10, 30, 20, 140, 80, 0x3, 0);  /* overlapping, down and right: from the far corner */
    copy(200, 0, 190, 5, 150, 90, 0x3, 1);
    copy(0, 0, 0, 250, 160, 100, 0x9, 0);
    for (u32 i = 0; i < 20; i++)
        copy(i * 8, 250, 320 + i * 6, 250 + i * 4, 64, 48, 0x3, i & 1);
}

static void p_expand(u32 salt) {
    host(0, 0, 160, 100, 0x3, salt);
    fill(0, 120, 160, 60, salt, 0x3, 0xff);
    /* Each pixel matching the transparency colour (in the compare mask) the foreground, the rest the background or
       left (MONO_SKIP) */
    setup(0, 0, 0, 200, 0, 160, 180, 0x3, 0x11, 0x22, salt & 0xff, packed ? 0xf0 : 0x0c, 0xff);
    start(F_EXP);
    setup(MONO_SKIP, 0, 0, 400, 0, 160, 180, 0x3, 0x33, 0x44, salt & 0xff, packed ? 0xf0 : 0x0c, 0xff);
    start(F_EXP);
}

static void p_mono(u32 salt) {
    const u32 per = packed ? 4 : 8;
    for (u32 k = 0; k < 2; k++) {
        setup(k ? MONO_SKIP : 0, 0, 0, 40 + k * 300, 60, 200, 150, 0x3, 0x5a + k, 0xa5 - k, 0, 0xff, 0xff);
        start(HOST | F_MONO);
        for (u32 row = 0; row < 150; row++)
            for (u32 i = 0; i < (200 + per - 1) / per; i++)
                outb(0x23c4, (u8) pattern(i, row, salt + k));
    }
}

static void p_compare(u32 salt) {
    host(0, 0, 320, 240, 0x3, salt);
    /* The destination compared with the transparency colour: drawn where it differs, then where it matches */
    setup(DST_CMP, 0, 0, 0, 0, 320, 240, 0x3, 0x77, 0, salt & 0xff, packed ? 0xc0 : 0x08, 0xff);
    start(F_FG);
    setup(DST_CMP | CMP_MATCH, 0, 0, 320, 240, 320, 240, 0x3, 0x88, 0, salt & 0xff, packed ? 0xc0 : 0x08, 0xff);
    host(320, 240, 320, 240, 0x3, salt + 1);
    setup(DST_CMP | CMP_MATCH, 0, 0, 320, 240, 320, 240, 0x3, 0x88, 0, salt & 0xff, packed ? 0xc0 : 0x08, 0xff);
    start(F_FG);
}

static void p_pattern(u32 salt) {
    host(0, 0, 8, 8, 0x3, salt); /* the pattern: 8 x 8 at (0, 0), its address aligned to 64 pixels */
    for (u32 i = 0; i < 6; i++) {
        setup(PATTERN, 0, 0, 20 + i * 100, 40 + i * 60, 90, 70, (i & 1) ? 0x6 : 0x3, 0, 0, 0, 0xff, 0xff);
        start(F_COLOR);
    }
}

void test_main(void) {
    __asm__ volatile("fninit");
    /* A WD90C31: its index register reads back */
    outw(0x23c0, 0x0101);
    if (inw(0x23c0) != 0x0101)
        return;
    static const u16 modes[2] = { 0x5f, 0x12 };
    for (u32 m = 0; m < 2; m++) {
        int10(modes[m], 0, 0, 0, 0, 0);
        packed = (m == 0);
        pitch  = 640;
        static void (*const passes[])(u32) = { p_fills, p_host, p_copies, p_expand, p_mono, p_compare, p_pattern };
        const u32 n = packed ? 7 : 5;
        for (u32 p = 0; p < n; p++) {
            const u32 salt = 0x30 + m * 8 + p;
            clear(salt);
            passes[p](salt);
            wait_ticks(4);
        }
    }
}
