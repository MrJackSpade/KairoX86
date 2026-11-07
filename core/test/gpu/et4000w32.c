/*
 * KairoX86's Tseng Labs ET4000/W32 accelerator test (KairoX86#283, for #254): on any W32, W32i or W32p (a Tseng BIOS's
 * mode 2Eh, 640 x 480 x 8, its memory through the MMU's apertures at B800:0000), a series of passes through the
 * accelerator, each over a clear and held four ticks of the BIOS clock: blits through raster operations with every
 * pattern and source wrap, in all four directions and overlapping both ways; source data and mix data from the
 * processor; on the W32p (the others ignore those bits) a mix map in video memory and lines. The accelerator's
 * status is never read. A machine whose BIOS has no mode 2Eh returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

#define MMU      ((volatile u8 *) 0xb8000)
#define MMU_REGS ((volatile u8 *) 0xbff00)
#define PITCH    640u

/* Accelerator registers (MMU_REGS + offset) */
enum {
    PAT_ADDR = 0x80, SRC_ADDR = 0x84, PAT_OFF = 0x88, SRC_OFF = 0x8a, DST_OFF = 0x8c, VBUS = 0x8e, XY_DIR = 0x8f,
    PAT_WRAP = 0x90, SRC_WRAP = 0x92, COUNT_X = 0x98, COUNT_Y = 0x9a, ROUTING = 0x9c, RELOAD = 0x9d, ROP_BG = 0x9e,
    ROP_FG = 0x9f, DST_ADDR = 0xa0, MIX_ADDR = 0xa4, MIX_OFF = 0xa8, ERROR = 0xaa, DMIN = 0xac, DMAJ = 0xae
};
/* MMU control registers */
enum { MMU_BASE0 = 0x00, MMU_CTRL = 0x13 };

static void r8(u32 reg, u8 v) { MMU_REGS[reg] = v; }
static void r16(u32 reg, u16 v) {
    MMU_REGS[reg]     = (u8) v;
    MMU_REGS[reg + 1] = (u8) (v >> 8);
}
static void r32(u32 reg, u32 v) {
    for (u32 i = 0; i < 4; i++)
        MMU_REGS[reg + i] = (u8) (v >> (8 * i));
}

/* Aperture 0 at an offset of video memory, plain (accelerated 0) or the accelerator's (1) */
static void aperture(u32 base, int accel) {
    r32(MMU_BASE0, base);
    r8(MMU_CTRL, accel ? 1 : 0);
}

static void clear(u32 salt) {
    for (u32 base = 0; base < PITCH * 480; base += 0x2000) {
        aperture(base, 0);
        for (u32 i = 0; i < 0x2000; i += 4)
            *(volatile u32 *) (MMU + i) = pattern((base + i) / 4 % 160, (base + i) / PITCH, salt);
    }
    /* A pattern block and a mix map apart, at 300 K */
    aperture(300u * 1024u, 0);
    for (u32 i = 0; i < 0x2000; i += 4)
        *(volatile u32 *) (MMU + i) = pattern(i, 77, salt);
}

static u32 at(u32 x, u32 y) { return y * PITCH + x; }

/* An operation's setup: its addresses start it (the destination's top byte) */
static void blit(u32 dst, u32 src, u32 pat, u32 w, u32 h, u8 dir, u8 pwrap, u8 swrap, u8 rop_fg, u8 rop_bg, u8 routing,
                 u16 src_off, u16 pat_off) {
    r32(PAT_ADDR, pat);
    r32(SRC_ADDR, src);
    r16(PAT_OFF, pat_off);
    r16(SRC_OFF, src_off);
    r16(DST_OFF, (u16) (PITCH - 1));
    r8(VBUS, 0);
    r8(XY_DIR, dir);
    r8(PAT_WRAP, pwrap);
    r8(SRC_WRAP, swrap);
    r16(COUNT_X, (u16) (w - 1));
    r16(COUNT_Y, (u16) (h - 1));
    r8(ROUTING, routing);
    r8(RELOAD, 0);
    r8(ROP_BG, rop_bg);
    r8(ROP_FG, rop_fg);
    r32(DST_ADDR, dst);
}

static void p_wraps(u32 salt) {
    static const u8 wraps[] = { 0x22, 0x33, 0x12, 0x03, 0x44, 0x77, 0x31, 0x24, 0x05, 0x16 };
    static const u8 rops[]  = { 0xf0, 0xcc, 0x5a, 0x66, 0xe2, 0x96, 0x0f, 0xb8, 0xa0, 0x3c };
    const u32 pat = 300u * 1024u;
    for (u32 k = 0; k < 10; k++) {
        const u32 x = 10 + (k % 5) * 125, y = 10 + (k / 5) * 120;
        blit(at(x, y), at(400 + k * 7, 300 + k * 3) + (salt & 3), pat + k * 13, 110, 100, 0, wraps[k], wraps[9 - k], rops[k], rops[k],
             0, (u16) (PITCH - 1), (u16) (k * 3));
    }
}

static void p_dirs(u32 salt) {
    (void) salt;
    /* Every direction, apart and overlapping */
    for (u32 k = 0; k < 8; k++) {
        const u32 sx = 40 + (k % 4) * 150, sy = 40 + (k / 4) * 200;
        const u32 w = 90, h = 80;
        const u8  dir = (u8) (k & 3);
        const int ox = (k & 4) ? 9 : 60, oy = (k & 4) ? 5 : 90;
        /* The walk starts at the corner its direction leaves first */
        const u32 dx = sx + (u32) ox, dy = sy + (u32) oy;
        const u32 fx = (dir & 1) ? w - 1 : 0, fy = (dir & 2) ? h - 1 : 0;
        blit(at(dx + fx, dy + fy), at(sx + fx, sy + fy), 0, w, h, dir, 0x77, 0x77, 0xcc, 0xcc, 0, (u16) (PITCH - 1), 0);
    }
}

/* Source or mix data from the processor through aperture 0 */
static void p_host(u32 salt) {
    const u32 w = 77, h = 40;
    blit(at(20, 20), 0, 300u * 1024u, w, h, 0, 0x22, 0x77, 0xcc, 0xcc, 1, 0, 0);
    aperture(at(20, 20), 1);
    for (u32 i = 0; i < w * h; i++)
        MMU[i & 0x1fff] = (u8) pattern(i, 1, salt);
    blit(at(200, 20), 0, 300u * 1024u, 120, 60, 0, 0x33, 0x77, 0xf0, 0x5a, 2, 0, 0);
    aperture(at(200, 20), 1);
    for (u32 i = 0; i < 120 * 60 / 8 + 60; i++)
        MMU[i & 0x1fff] = (u8) pattern(i, 2, salt);
    blit(at(400, 20), at(30, 300), 300u * 1024u, 120, 60, 2, 0x22, 0x77, 0xcc, 0x0f, 2, (u16) (PITCH - 1), 0);
    aperture(at(400, 20), 1);
    for (u32 i = 0; i < 120 * 60 / 8 + 60; i++)
        MMU[i & 0x1fff] = (u8) pattern(i, 3, salt);
}

/* The W32p's mix map in video memory and its lines */
static void p_w32p(u32 salt) {
    (void) salt;
    r32(MIX_ADDR, 300u * 1024u * 8u);
    r16(MIX_OFF, 15);
    blit(at(20, 200), at(300, 10), 300u * 1024u + 512, 200, 120, 0, 0x33, 0x77, 0xcc, 0x00, 0x08, (u16) (PITCH - 1), 0);
    for (u32 k = 0; k < 8; k++) {
        r16(ERROR, 0);
        r16(DMIN, (u16) (20 + k * 9));
        r16(DMAJ, 100);
        r32(MIX_ADDR, 0);
        blit(at(300 + k * 30, 200 + (k & 1) * 120), 0, 300u * 1024u + k, 100, 100, (u8) (0x80 | (k & 7)), 0x22, 0x77, 0xf0, 0xf0, 0, 0, 0);
    }
}

void test_main(void) {
    __asm__ volatile("fninit");
    if (int10(0x002e, 0, 0, 0, 0, 0) & 0) /* AL is the BIOS's; the mode is checked below */
        return;
    /* Mode 2Eh is 640 wide: CRTC 01h (horizontal display end) 4Fh */
    outb(0x3d4, 0x01);
    if (inb(0x3d5) != 0x4f)
        return;
    /* 64K at A000:0000 and the MMU at B800:0000 (CRTC 36h bit 5) */
    outb(0x3ce, 0x06);
    outb(0x3cf, (u8) ((inb(0x3cf) & ~0x0c) | 0x04));
    outb(0x3d4, 0x36);
    outb(0x3d5, (u8) ((inb(0x3d5) & ~0x18) | 0x20));

    static void (*const passes[])(u32) = { p_wraps, p_dirs, p_host, p_w32p, p_wraps, p_dirs };
    for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
        clear(0x30 + p);
        passes[p](p);
        aperture(0, 0);
        wait_ticks(4);
    }
}
