/*
 * KairoX86's Trident TGUI9680 overlay test (KairoX86#283, for #233): on a TGUI96x0 (PCI 1023h:9660h; the 9680 has the
 * overlay, the 9660 none), VESA 640 x 480 x 8 through the linear aperture (BAR 0 at E0000000h, CRTC 21h bit 5), the
 * picture a pattern with a band of one colour and a source placed 384K on, shown through the overlay window (CRTC
 * 80h to 94h, its colour key in the extended registers 30h to 37h at 83C8h/83C6h) in passes, each held six ticks of
 * the BIOS clock: RGB 565 at 1:1, through the colour key (the band's colour, compared with the drawn picture), doubled
 * across and down, YUV 4:2:2, and against the right edge. The window counts from the end of sync, so each pass adds
 * the offsets the driver adds. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_addr(u32 bus, u32 dev, u32 reg_) { return 0x80000000u | (bus << 16) | (dev << 11) | (reg_ & 0xfc); }

static void crtc(u8 index, u8 value) {
    outb(0x3d4, index);
    outb(0x3d5, value);
}

static u8 crtc_read(u8 index) {
    outb(0x3d4, index);
    return inb(0x3d5);
}

static void ext(u8 index, u8 value) {
    outb(0x83c8, index);
    outb(0x83c6, value);
}

#define W     640
#define H     480
#define KEY   0xe3u
#define SRC   0x60000u
#define SRC_W 320
#define SRC_H 240

/* The offsets from screen coordinates to the window's, from the end of horizontal and vertical sync */
static int hoff, voff;
static void offsets(void) {
    const int hss = crtc_read(0x04);
    int       hse = (hss & ~0x1f) | (crtc_read(0x05) & 0x1f);
    const u8  c7  = crtc_read(0x07);
    const int vt  = (crtc_read(0x06) | ((c7 & 0x01) << 8) | ((c7 & 0x20) << 4)) + 2;
    const int vss = crtc_read(0x10) | ((c7 & 0x04) << 6) | ((c7 & 0x80) << 2);
    int       vse = (vss & ~0x0f) | (crtc_read(0x11) & 0x0f);
    if ((hss & 0x1f) > (crtc_read(0x05) & 0x1f))
        hse += 0x20;
    hoff = (((crtc_read(0x00) + 5) - hse) << 3) - 6;
    if ((vss & 0x0f) > (crtc_read(0x11) & 0x0f))
        vse += 0x10;
    voff = vt - vse - 1;
}

/* The window at (x, y), w x h; rgb (CRTC 8Fh bit 0); zoom (0: 1:1, 400h: 2x); keyed */
static void window(u32 x, u32 y, u32 w, u32 h, u32 rgb, u32 zoom, u32 keyed) {
    const u32 x1 = x + (u32) hoff, y1 = y + (u32) voff, x2 = x1 + w, y2 = y1 + h;
    crtc(0x8e, 0);
    crtc(0x80, (u8) zoom);
    crtc(0x81, (u8) (zoom >> 8));
    crtc(0x82, (u8) zoom);
    crtc(0x83, (u8) (zoom >> 8));
    crtc(0x86, (u8) x1);
    crtc(0x87, (u8) (x1 >> 8));
    crtc(0x88, (u8) y1);
    crtc(0x89, (u8) (y1 >> 8));
    crtc(0x8a, (u8) x2);
    crtc(0x8b, (u8) (x2 >> 8));
    crtc(0x8c, (u8) y2);
    crtc(0x8d, (u8) (y2 >> 8));
    crtc(0x8f, (u8) (rgb ? 0x01 : 0x00));
    crtc(0x90, (u8) (SRC_W * 2));
    crtc(0x91, (u8) ((SRC_W * 2) >> 8));
    crtc(0x92, (u8) (SRC >> 3));
    crtc(0x93, (u8) (SRC >> 11));
    crtc(0x94, (u8) ((SRC >> 19) & 7));
    /* The key: the band's index (8 bits a pixel compares the drawn colour with its palette entry's) */
    ext(0x30, KEY);
    ext(0x31, 0);
    ext(0x32, 0);
    ext(0x37, (u8) (keyed ? 0x01 : 0x00));
    crtc(0x8e, 0x10);
}

void test_main(void) {
    __asm__ volatile("fninit");
    u32 bus, dev;
    int found = 0;
    for (bus = 0; bus < 2 && !found; bus++)
        for (dev = 0; dev < 32 && !found; dev++) {
            outl(0xcf8, pci_addr(bus, dev, 0));
            if (inl(0xcfc) == 0x96601023u) {
                found = 1;
                break;
            }
        }
    if (!found)
        return;
    bus--; /* the outer loop stepped past it */
    outl(0xcf8, pci_addr(bus, dev, 0x10));
    outl(0xcfc, 0xe0000000u);
    outl(0xcf8, pci_addr(bus, dev, 0x10));
    const u32 base = inl(0xcfc) & 0xfff00000u;
    if (base != 0xe0000000u)
        return;
    outl(0xcf8, pci_addr(bus, dev, 0x04));
    outw(0xcfc, (u16) (inw(0xcfc) | 0x0003));
    u16       mode  = 0;
    const int count = vbe_modes();
    for (int i = 0; (i < count) && !mode; i++)
        if ((int10(0x4f01, 0, VBE_MODES[i], 0, 0x6200, 0) == 0x004f) && (VBE_MODE->attributes & 1) && (VBE_MODE->width == 640) &&
            (VBE_MODE->height == 480) && (VBE_MODE->bpp == 8))
            mode = VBE_MODES[i];
    if (!mode || (int10(0x4f02, mode, 0, 0, 0, 0) != 0x004f))
        return;
    /* CRTC 21h takes writes with SR0Eh bit 7 set (new mode: SR0Bh read first): the linear aperture on */
    outb(0x3c4, 0x0b);
    (void) inb(0x3c5);
    outb(0x3c4, 0x0e);
    outb(0x3c5, (u8) (inb(0x3c5) | 0x80));
    crtc(0x21, (u8) (crtc_read(0x21) | 0x20));
    offsets();

    volatile u8 *fb = (volatile u8 *) base;
    for (u32 y = 0; y < H; y++)
        for (u32 x = 0; x < W; x++)
            fb[y * W + x] = ((y >= 200) && (y < 260) && (x >= 60)) ? (u8) KEY : (u8) pattern(x, y, 0xb1);
    volatile u16 *src = (volatile u16 *) (base + SRC);
    for (u32 i = 0; i < SRC_W * SRC_H; i++)
        src[i] = (u16) pattern(i % SRC_W, i / SRC_W, 0xb2);

    static const u32 passes[5][7] = {
        /* x, y, w, h, rgb, zoom, keyed */
        { 100, 60, 300, 200, 1, 0, 0 },
        { 100, 160, 300, 200, 1, 0, 1 },
        { 40, 40, 560, 400, 1, 0x400, 0 },
        { 160, 100, 240, 180, 0, 0, 0 },
        { 500, 300, 300, 150, 1, 0, 0 },
    };
    for (u32 p = 0; p < 5; p++) {
        window(passes[p][0], passes[p][1], passes[p][2], passes[p][3], passes[p][4], passes[p][5], passes[p][6]);
        wait_ticks(6);
    }
    crtc(0x8e, 0);
}
