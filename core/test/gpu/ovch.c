/*
 * KairoX86's Chips & Technologies 69000 video playback test (KairoX86#283, for #233): on a 69000 (PCI 102Ch:00C0h),
 * VESA 640 x 480 x 16 with its linear frame buffer, the picture a pattern with a band of one colour and a source
 * placed 1 MB on, shown through the multimedia registers' playback window (MR1E to MR42, through 3D2h/3D3h) in
 * passes, each held six ticks of the BIOS clock: RGB 565 at 1:1, through the colour key (the band's colour), doubled
 * across and down, YUV 4:2:2, against the right edge, and with the colours' low bit cleared over the whole display.
 * The window's coordinates count from the CRT's blanking and sync as the chip's do; the passes add an approximate
 * offset for them. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    return inl(0xcfc);
}

static void mr(u8 index, u8 value) {
    outb(0x3d2, index);
    outb(0x3d3, value);
}

#define W      640
#define H      480
#define KEY    0xf81fu
#define SRC    0x100000u
#define SRC_W  320
#define SRC_H  240
#define SKEW_X 143
#define SKEW_Y 31

/* The window at (x, y), w x h; rgb (MR1F bit 3: RGB 565, else YUV 4:2:2); scale 1 or 2; flags: 2 keyed, 80h the
   colours' low bit cleared over the whole display (MR3C) */
static void window(u32 x, u32 y, u32 w, u32 h, u32 rgb, u32 scale, u32 flags) {
    const u32 left = x + SKEW_X, right = x + w - 1 + SKEW_X, top = y + SKEW_Y, bottom = y + h - 1 + SKEW_Y;
    mr(0x3c, 0);
    mr(0x1e, (u8) ((scale == 2) ? 0x0c : 0x00));
    mr(0x1f, (u8) (rgb ? 0x08 : 0x00));
    mr(0x20, 0);
    mr(0x22, (u8) SRC);
    mr(0x23, (u8) (SRC >> 8));
    mr(0x24, (u8) (SRC >> 16));
    mr(0x28, (u8) (SRC_W * 2 / 8 - 1));
    mr(0x2a, (u8) left);
    mr(0x2b, (u8) (left >> 8));
    mr(0x2c, (u8) right);
    mr(0x2d, (u8) (right >> 8));
    mr(0x2e, (u8) top);
    mr(0x2f, (u8) (top >> 8));
    mr(0x30, (u8) bottom);
    mr(0x31, (u8) (bottom >> 8));
    mr(0x32, 0x80); /* half steps, when zoomed */
    mr(0x33, 0x80);
    /* The key: the picture's colour (as 8:8:8) equal to KEY's, no bits masked */
    mr(0x3d, 0xf8);
    mr(0x3e, 0x00);
    mr(0x3f, 0xf8);
    mr(0x40, 0);
    mr(0x41, 0);
    mr(0x42, 0);
    mr(0x3c, (u8) (0x01 | flags));
}

void test_main(void) {
    __asm__ volatile("fninit");
    int found = 0;
    for (u32 bus = 0; bus < 2 && !found; bus++)
        for (u32 dev = 0; dev < 32 && !found; dev++)
            if (pci_read(bus, dev, 0, 0) == 0x00c0102cu)
                found = 1;
    if (!found || vbe_modes() < 0)
        return;
    const u16 mode = vbe_find(W, H, 16);
    if (!mode || int10(0x4f02, mode | 0x4000, 0, 0, 0, 0) != 0x004f)
        return;
    const u32 lfb = VBE_MODE->framebuffer;

    volatile u16 *fb = (volatile u16 *) lfb;
    for (u32 y = 0; y < H; y++)
        for (u32 x = 0; x < W; x++)
            fb[y * W + x] = ((y >= 200) && (y < 260) && (x >= 60)) ? (u16) KEY : (u16) pattern(x, y, 0xa1);
    volatile u16 *src = (volatile u16 *) (lfb + SRC);
    for (u32 i = 0; i < SRC_W * SRC_H; i++)
        src[i] = (u16) pattern(i % SRC_W, i / SRC_W, 0xa2);

    static const u32 passes[6][7] = {
        /* x, y, w, h, rgb, scale, flags */
        { 100, 60, 300, 200, 1, 1, 0 },
        { 100, 160, 300, 200, 1, 1, 2 },
        { 40, 40, 560, 400, 1, 2, 0 },
        { 160, 100, 240, 180, 0, 1, 0 },
        { 500, 300, 300, 150, 1, 1, 0 },
        { 100, 60, 300, 200, 1, 1, 0x80 },
    };
    for (u32 p = 0; p < 6; p++) {
        window(passes[p][0], passes[p][1], passes[p][2], passes[p][3], passes[p][4], passes[p][5], passes[p][6]);
        wait_ticks(6);
    }
    mr(0x3c, 0);
}
