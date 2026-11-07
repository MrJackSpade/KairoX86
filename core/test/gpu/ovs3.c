/*
 * KairoX86's S3 streams overlay test (KairoX86#283, for #233): on an S3 with the streams processor (PCI 5333h: the
 * Trio64V+ 8811h at revision 40h, the Trio64V2 8901h, the ViRGE family 5631h, 883Dh, 8A01h, 8A10h, 8A13h), VESA
 * 640 x 480 x 16 with S3's linear addressing (CR58) and the new MMIO window (CR53 bit 3), streams mode on (CR67 bits 2
 * and 3), the primary stream the picture (a pattern with a band of one colour) and the secondary stream a pattern
 * placed 1 MB on, shown over it in passes, each held six ticks of the BIOS clock: RGB 565 at 1:1, the same through the
 * colour key (the band's colour), doubled across and down, YCbCr 4:2:2, and placed against the right edge. Any other
 * card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    return inl(0xcfc);
}

static void pci_write(u32 bus, u32 dev, u32 reg_, u32 v) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (reg_ & 0xfc));
    outl(0xcfc, v);
}

static u8 crtc_read(u8 index) {
    outb(0x3d4, index);
    return inb(0x3d5);
}

static void crtc_write(u8 index, u8 value) {
    outb(0x3d4, index);
    outb(0x3d5, value);
}

static volatile u32 *mmio;
static void reg(u32 offset, u32 value) { mmio[offset / 4] = value; }

enum { PRI_CTRL = 0x8180, CHROMA_CTRL = 0x8184, SEC_CTRL = 0x8190, SEC_FILTER = 0x8198, BLEND_CTRL = 0x81a0,
       PRI_FB0 = 0x81c0, PRI_STRIDE = 0x81c8, BUFFER_CTRL = 0x81cc, SEC_FB0 = 0x81d0, SEC_STRIDE = 0x81d8,
       K1_VERT = 0x81e0, K2_VERT = 0x81e4, DDA_VERT = 0x81e8, PRI_START = 0x81f0, PRI_SIZE = 0x81f4, SEC_START = 0x81f8,
       SEC_SIZE = 0x81fc };

#define W         640
#define H         480
#define KEY       0xf81fu /* the band's colour, magenta */
#define SRC       0x100000u
#define SRC_W     320
#define SRC_H     240

/* The secondary stream at (x, y), w x h on screen, its format (1 YCbCr 4:2:2, 5 RGB 565) and scale (1 or 2), keyed */
static void secondary(u32 x, u32 y, u32 w, u32 h, u32 format, u32 scale, u32 keyed) {
    /* Each output pixel advances the DDA by k1; at 0 or above the source moves on and it takes k2 - k1: k1 1 and
       k2 0 move on every pixel, k2 -1 every other */
    const u32 k2 = (scale == 2) ? 0xfffu : 0;
    reg(SEC_CTRL, (format << 24) | 0x1fffu);
    reg(SEC_FILTER, 1u | (k2 << 16));
    reg(K1_VERT, 1);
    reg(K2_VERT, k2);
    reg(DDA_VERT, 0x1fff);
    reg(SEC_FB0, SRC);
    reg(SEC_STRIDE, SRC_W * 2);
    reg(SEC_START, (x << 16) | y);
    reg(SEC_SIZE, ((w - 1) << 16) | h);
    /* The key: the primary's colour at each pixel against KEY, all 8 bits of each channel compared */
    reg(CHROMA_CTRL, keyed ? ((1u << 28) | (7u << 24) | 0xf800f8u) : 0);
    reg(BLEND_CTRL, 0x20); /* the secondary over the primary (bits 24-26 0; the GX2's bit 5) */
}

void test_main(void) {
    __asm__ volatile("fninit");
    u32 lfb = 0;
    u32 at  = 0;
    for (u32 bus = 0; bus < 2 && !lfb; bus++)
        for (u32 dev = 0; dev < 32 && !lfb; dev++) {
            const u32 id = pci_read(bus, dev, 0, 0);
            const u32 d  = id >> 16;
            if (((id & 0xffff) == 0x5333) &&
                ((d == 0x8811) || (d == 0x8901) || (d == 0x5631) || (d == 0x883d) || (d == 0x8a01) || (d == 0x8a10) ||
                 (d == 0x8a13))) {
                at  = (bus << 8) | dev;
                lfb = pci_read(bus, dev, 0, 0x10) & ~0xfu;
                if (!lfb) {
                    pci_write(bus, dev, 0x10, 0xe0000000u);
                    lfb = 0xe0000000u;
                }
            }
        }
    if (!lfb)
        return;
    if (int10(0x4f02, 0x111, 0, 0, 0, 0) != 0x004f)
        return;
    crtc_write(0x38, 0x48);
    crtc_write(0x39, 0xa5);
    /* A Trio64 (8811h) has streams only from revision 40h, the Trio64V+ */
    if (((pci_read(at >> 8, at & 0xff, 0, 0) >> 16) == 0x8811) && (crtc_read(0x2f) != 0x40))
        return;
    crtc_write(0x58, (u8) ((crtc_read(0x58) & ~0x03) | 0x13));
    crtc_write(0x40, (u8) (crtc_read(0x40) | 0x01));
    crtc_write(0x53, (u8) (crtc_read(0x53) | 0x08));
    mmio = (volatile u32 *) (lfb + 0x1000000);

    /* The picture and the secondary's source */
    volatile u16 *fb = (volatile u16 *) lfb;
    for (u32 y = 0; y < H; y++)
        for (u32 x = 0; x < W; x++)
            fb[y * W + x] = ((y >= 200) && (y < 260) && (x >= 60)) ? (u16) KEY : (u16) pattern(x, y, 0x51);
    volatile u16 *src = (volatile u16 *) (lfb + SRC);
    for (u32 i = 0; i < SRC_W * SRC_H; i++)
        src[i] = (u16) pattern(i % SRC_W, i / SRC_W, 0x52);

    /* Streams mode, the primary the whole 640 x 480 x 16 picture */
    crtc_write(0x67, (u8) (crtc_read(0x67) | 0x0c));
    reg(PRI_CTRL, 5u << 24);
    reg(PRI_FB0, 0);
    reg(PRI_STRIDE, W * 2);
    reg(BUFFER_CTRL, 0);
    reg(PRI_START, (1u << 16) | 1u);
    reg(PRI_SIZE, ((W - 1u) << 16) | H);

    static const u32 passes[5][7] = {
        /* x, y, w, h, format, scale, keyed */
        { 101, 61, 300, 200, 5, 1, 0 },
        { 101, 161, 300, 200, 5, 1, 1 },
        { 51, 41, 500, 400, 5, 2, 0 },
        { 151, 101, 240, 180, 1, 1, 0 },
        { 501, 301, 300, 150, 5, 1, 0 },
    };
    for (u32 p = 0; p < 5; p++) {
        secondary(passes[p][0], passes[p][1], passes[p][2], passes[p][3], passes[p][4], passes[p][5], passes[p][6]);
        wait_ticks(6);
    }
    /* Back to plain VGA mode */
    reg(BLEND_CTRL, 0);
    crtc_write(0x67, (u8) (crtc_read(0x67) & ~0x0c));
}
