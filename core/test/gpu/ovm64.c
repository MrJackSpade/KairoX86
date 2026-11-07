/*
 * KairoX86's ATI Mach64 overlay test (KairoX86#283, for #233): on a Mach64 VT or 3D Rage II+ (PCI 1002h: 5654h,
 * 5655h, 4755h), VESA 640 x 480 x 16 with its linear frame buffer, the picture a pattern with a band of one colour
 * and a source placed 2 MB on, shown through the overlay (MMIO block 1, 1K below block 0 at the aperture's top) in
 * passes, each held six ticks of the BIOS clock: RGB 565 at 1:1, through the graphics key (the band's colour),
 * doubled across and down, VYUY 4:2:2, and against the right edge. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    return inl(0xcfc);
}

static volatile u32 *blk1;
static void reg(u32 offset, u32 value) { blk1[offset / 4] = value; }

enum { Y_X_START = 0x00, Y_X_END = 0x04, GRAPHICS_KEY_CLR = 0x10, GRAPHICS_KEY_MSK = 0x14, KEY_CNTL = 0x18,
       SCALE_INC = 0x20, SCALE_CNTL = 0x24, HEIGHT_WIDTH = 0x28, SCALER_BUF0 = 0x34, SCALER_PITCH = 0x3c,
       BUF0 = 0x80, BUF0_PITCH = 0x8c };

#define W     640
#define H     480
#define KEY   0xf81fu
#define SRC   0x200000u
#define SRC_W 320
#define SRC_H 240

/* The overlay at (x, y), w x h; format (4 RGB 565, 0Bh VYUY 4:2:2); inc 1000h (1:1) or 800h (2x); keyed */
static void overlay(u32 x, u32 y, u32 w, u32 h, u32 format, u32 inc, u32 keyed) {
    reg(SCALE_CNTL, 0);
    reg(Y_X_START, (x << 16) | y);
    reg(Y_X_END, ((x + w - 1) << 16) | (y + h - 1));
    reg(HEIGHT_WIDTH, ((u32) SRC_W << 16) | SRC_H);
    reg(SCALE_INC, (inc << 16) | inc);
    reg(SCALER_BUF0, SRC);
    reg(SCALER_PITCH, SRC_W);
    reg(BUF0, SRC);
    reg(BUF0_PITCH, SRC_W);
    *(volatile u8 *) ((volatile u8 *) blk1 + 0x4a) = (u8) format;
    reg(GRAPHICS_KEY_CLR, KEY);
    reg(GRAPHICS_KEY_MSK, 0xffff);
    /* Keyed: the video where the picture's pixel is the key (graphics key "equal", mix 0); else always (mix 2) */
    reg(KEY_CNTL, keyed ? (5u << 4) : (2u << 8));
    reg(SCALE_CNTL, (1u << 30) | (1u << 31));
}

void test_main(void) {
    __asm__ volatile("fninit");
    int found = 0;
    for (u32 bus = 0; bus < 2 && !found; bus++)
        for (u32 dev = 0; dev < 32 && !found; dev++) {
            const u32 id = pci_read(bus, dev, 0, 0);
            if ((id == 0x56541002u) || (id == 0x56551002u) || (id == 0x47551002u))
                found = 1;
        }
    if (!found)
        return;
    const u16 mode = vbe_find(640, 480, 16);
    if (!mode || (int10(0x4f02, mode | 0x4000, 0, 0, 0, 0) != 0x004f))
        return;
    const u32 lfb = VBE_MODE->framebuffer;
    blk1          = (volatile u32 *) ((lfb & ~0x7fffffu) + 0x7ff800u);

    volatile u16 *fb = (volatile u16 *) lfb;
    for (u32 y = 0; y < H; y++)
        for (u32 x = 0; x < W; x++)
            fb[y * W + x] = ((y >= 200) && (y < 260) && (x >= 60)) ? (u16) KEY : (u16) pattern(x, y, 0x71);
    volatile u16 *src = (volatile u16 *) (lfb + SRC);
    for (u32 i = 0; i < SRC_W * SRC_H; i++)
        src[i] = (u16) pattern(i % SRC_W, i / SRC_W, 0x72);

    static const u32 passes[5][7] = {
        /* x, y, w, h, format, inc, keyed */
        { 100, 60, 300, 200, 4, 0x1000, 0 },
        { 100, 160, 300, 200, 4, 0x1000, 1 },
        { 40, 40, 560, 400, 4, 0x800, 0 },
        { 160, 100, 240, 180, 0xb, 0x1000, 0 },
        { 500, 300, 300, 150, 4, 0x1000, 0 },
    };
    for (u32 p = 0; p < 5; p++) {
        overlay(passes[p][0], passes[p][1], passes[p][2], passes[p][3], passes[p][4], passes[p][5], passes[p][6]);
        wait_ticks(6);
    }
    reg(SCALE_CNTL, 0);
}
