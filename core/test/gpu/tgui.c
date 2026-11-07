/*
 * KairoX86's Trident TGUI graphics engine test (KairoX86#283, for #274): on a TGUI 9440, 9660 or 9680 (PCI 1023h:
 * 9440h, 9660h), VESA 640 x 480 x 8 through its linear aperture (BAR 0, CRTC 21h bit 5), the engine through its ports (2120h-21FFh), a
 * series of passes, each over a clear and held four ticks of the BIOS clock: screen copies through raster operations
 * both ways, overlapping, transparent; colour, mono and solid pattern fills; Bresenham lines in every octant, short
 * vectors and (9660 and later) fast lines; sources from the host (colour and mono, through the linear frame buffer).
 * The engine's status is never read: it finishes at once. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_addr(u32 bus, u32 dev, u32 reg_) { return 0x80000000u | (bus << 16) | (dev << 11) | (reg_ & 0xfc); }

static volatile u8 *fb;
static u32          pitch;
static u32          is_9660;

enum { CMD = 0x2124, ROP = 0x2127, FLAGS = 0x2128, FG = 0x212c, BG = 0x2130, DST_X = 0x2138, DST_Y = 0x213a, SRC_X = 0x213c,
       SRC_Y = 0x213e, SIZE_X = 0x2140, SIZE_Y = 0x2142, CLIP_SX = 0x2148, CLIP_SY = 0x214a, CLIP_DX = 0x214c, CLIP_DY = 0x214e,
       PATTERN = 0x2180 };
enum { BITBLT = 1, SCANLINE = 3, BRESENHAM = 4, SHORTVECTOR = 5, FASTLINE = 6 };
#define SRCDISP  0x04u
#define PATMONO  0x20u
#define SRCMONO  0x40u
#define YDEC     0x100u
#define XDEC     0x200u
#define TRANSENA 0x1000u
#define TRANSREV 0x2000u
#define SOLID    0x4000u

static void w16(u16 port, u16 v) { outw(port, v); }
static void w32(u16 port, u32 v) { outl(port, v); }

static void clear(u32 salt) {
    for (u32 i = 0; i < pitch * 480 / 4; i++)
        ((volatile u32 *) fb)[i] = pattern(i % 160, i / 160, salt);
}

static void op(u8 cmd, u8 rop, u32 flags, u32 dx, u32 dy, u32 sx, u32 sy, u32 w, u32 h) {
    outb(ROP, rop);
    w32(FLAGS, flags);
    w16(DST_X, (u16) dx);
    w16(DST_Y, (u16) dy);
    w16(SRC_X, (u16) sx);
    w16(SRC_Y, (u16) sy);
    w16(SIZE_X, (u16) (w - 1));
    w16(SIZE_Y, (u16) (h - 1));
    outb(CMD, cmd);
}

static const u8 rops[] = { 0xcc, 0x66, 0x88, 0xee, 0xf0, 0x5a, 0xa0, 0x33, 0x99, 0x0f, 0x55, 0xbb };

static void p_copies(u32 salt) {
    w32(BG, pattern(1, 3, salt) & 0xff);
    for (u32 k = 0; k < 8; k++)
        op(BITBLT, rops[k], SRCDISP | ((k & 1) ? TRANSENA : 0), 10 + (k % 4) * 155, 10 + (k / 4) * 110, 300 + k * 7, 260 + k * 3, 140, 100);
    /* Overlapping both ways: the walk starts at the corner its direction leaves first */
    op(BITBLT, 0xcc, SRCDISP, 30 + 9, 260 + 5, 30, 260, 120, 90);
    op(BITBLT, 0xcc, SRCDISP | XDEC | YDEC, 300 + 119, 260 + 89, 300 + 119 + 9, 260 + 89 + 5, 120, 90);
}

static void p_patterns(u32 salt) {
    for (u32 i = 0; i < 0x80; i += 4)
        w32((u16) (PATTERN + i), pattern(i, 4, salt));
    w32(FG, pattern(5, 4, salt));
    w32(BG, pattern(6, 4, salt));
    for (u32 k = 0; k < 9; k++) {
        const u32 flags = (k % 3 == 1) ? PATMONO : (k % 3 == 2) ? SOLID : 0;
        op(BITBLT, (u8) ((k < 6) ? 0xf0 : 0x5a), flags | SRCDISP, 10 + (k % 3) * 210, 10 + (k / 3) * 155, 0, 0, 190, 140);
    }
    /* A scanline, a copy of one line */
    op(SCANLINE, 0xcc, SRCDISP, 20, 470, 100, 3, 400, 1);
}

static void p_lines(u32 salt) {
    w32(FG, pattern(7, 4, salt));
    for (u32 o = 0; o < 8; o++) {
        /* Bresenham: diagonal step 2(minor - major), axial step 2 minor, error 2 minor - major */
        const int major = 120, minor = 30 + (int) o * 9;
        outb(ROP, rops[o]);
        w32(FLAGS, o << 8);
        w16(DST_X, (u16) (160 + (o % 4) * 100));
        w16(DST_Y, (u16) (140 + (o / 4) * 200));
        w16(SRC_X, (u16) ((2 * (minor - major)) & 0x3fff));
        w16(SRC_Y, (u16) ((2 * minor) & 0x3fff));
        w16(SIZE_X, (u16) ((2 * minor - major) & 0x3fff));
        w16(SIZE_Y, (u16) major);
        outb(CMD, BRESENHAM);
        /* A short vector of every direction */
        outb(ROP, 0xf0);
        w16(DST_X, (u16) (40 + o * 70));
        w16(DST_Y, 450);
        w16(SIZE_Y, (u16) ((o << 13) | 25));
        outb(CMD, SHORTVECTOR);
    }
    if (is_9660) {
        w16(CLIP_SX, 0);
        w16(CLIP_SY, 0);
        w16(CLIP_DX, 639);
        w16(CLIP_DY, 479);
        for (u32 o = 0; o < 4; o++)
            op(FASTLINE, 0xf0, o << 8, 300, 240, (u32) (2 * (20 - 100)) & 0x3fff, 40, 100, (u32) (2 * 20 - 100 + 1) & 0x3fff);
    }
}

static void p_host(u32 salt) {
    /* The host's pixels through the linear frame buffer, which CRTC 21h bit 5 opens and routes to the engine */
    w32(FG, pattern(8, 4, salt));
    w32(BG, pattern(9, 4, salt));
    op(BITBLT, 0xcc, 0, 20, 20, 0, 0, 64, 40);
    for (u32 i = 0; i < 64 * 40 / 4; i++)
        *(volatile u32 *) fb = pattern(i, 10, salt);
    op(BITBLT, 0x66, SRCMONO | TRANSENA, 200, 20, 0, 0, 96, 50);
    for (u32 i = 0; i < 96 * 50 / 32 + 2; i++)
        *(volatile u32 *) fb = pattern(i, 11, salt);
    op(BITBLT, 0xcc, SRCMONO | PATMONO | TRANSREV, 400, 20, 0, 0, 96, 50);
    for (u32 i = 0; i < 96 * 50 / 32 + 2; i++)
        *(volatile u32 *) fb = pattern(i, 12, salt);
}

void test_main(void) {
    __asm__ volatile("fninit");
    u32 bus, dev, id = 0;
    int found = 0;
    for (bus = 0; bus < 2 && !found; bus++)
        for (dev = 0; dev < 32 && !found; dev++) {
            outl(0xcf8, pci_addr(bus, dev, 0));
            id = inl(0xcfc);
            if ((id == 0x94401023u) || (id == 0x96601023u)) {
                found = 1;
                break;
            }
        }
    if (!found)
        return;
    bus--; /* the outer loop stepped past it */
    is_9660 = (id == 0x96601023u);
    /* The linear aperture at E000:0000:0000 (BAR 0): the BIOS leaves it as its sizing left it */
    outl(0xcf8, pci_addr(bus, dev, 0x10));
    outl(0xcfc, 0xe0000000u);
    outl(0xcf8, pci_addr(bus, dev, 0x10));
    const u32 base = inl(0xcfc) & 0xfff00000u;
    if (base != 0xe0000000u)
        return;
    /* Its memory and I/O decoded */
    outl(0xcf8, pci_addr(bus, dev, 0x04));
    outw(0xcfc, (u16) (inw(0xcfc) | 0x0003));
    /* VESA 640 x 480 x 8, its frame buffer the card's linear aperture (BAR 0, CRTC 21h bit 5): the BIOS lists none */
    u16 mode = 0;
    const int count = vbe_modes();
    for (int i = 0; (i < count) && !mode; i++)
        if ((int10(0x4f01, 0, VBE_MODES[i], 0, 0x6200, 0) == 0x004f) && (VBE_MODE->attributes & 1) && (VBE_MODE->width == 640) &&
            (VBE_MODE->height == 480) && (VBE_MODE->bpp == 8))
            mode = VBE_MODES[i];
    if (!mode || (int10(0x4f02, mode, 0, 0, 0, 0) != 0x004f))
        return;
    /* VBE 1.0 BIOSes leave the line length 0 */
    pitch = VBE_MODE->pitch ? VBE_MODE->pitch : 640;
    /* CRTC 21h takes writes with SR0Eh bit 7 set (new mode: SR0Bh read first) */
    outb(0x3c4, 0x0b);
    (void) inb(0x3c5);
    outb(0x3c4, 0x0e);
    outb(0x3c5, (u8) (inb(0x3c5) | 0x80));
    outb(0x3d4, 0x21);
    outb(0x3d5, (u8) (inb(0x3d5) | 0x20));
    fb = (volatile u8 *) base;
    /* The engine's ports on (extended registers: SR0Bh read for new mode, CRTC 36h) */
    outb(0x3c4, 0x0b);
    (void) inb(0x3c5);

    static void (*const passes[])(u32) = { p_copies, p_patterns, p_lines, p_host, p_copies, p_lines };
    for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
        clear(0x40 + p);
        passes[p](p);
        wait_ticks(4);
    }
}
