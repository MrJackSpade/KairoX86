/*
 * KairoX86's Matrox drawing engine test (KairoX86#283, for #264): on any Matrox Millennium, Millennium II or Mystique
 * (PCI 102Bh; its control aperture the 16 KB BAR), VESA 640 x 480 x 8 with its linear frame buffer, and the engine
 * through the control aperture at each pixel width (MACCESS 8, 16, 24 and 32 bits, the pitch 640 pixels): passes over
 * a clear from the processor, each held four ticks of the BIOS clock (the display waits for the engine, KairoX86#299)
 * and then copied from the frame buffer into memory above 1 MB for the end state. Trapezoid fills through all 16
 * boolean operations, solid and patterned, opaque and transparent, with the screen-door masks; blits (BITBLT) in
 * every direction, overlapping, a smear, the fast blit and mono expansion from video memory (raster and block);
 * lines (AUTOLINE) through the operations and Gouraud lines with a Z buffer; host data (ILOAD) in colour and mono;
 * at 16 and 32 bits, Gouraud trapezoids (with and without the Z buffer) and textured ones (TEXTURE_TRAP, nearest and
 * bilinear, plain and modulated), their edges slanted.
 * The engine's status is never read. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

enum { DWGCTL = 0x1c00, MACCESS = 0x1c04, ZORG = 0x1c0c, PAT0 = 0x1c10, PAT1 = 0x1c14, PLNWT = 0x1c1c, BCOL = 0x1c20,
       FCOL = 0x1c24, XYSTRT = 0x1c40, XYEND = 0x1c44, SHIFT = 0x1c50, SGN = 0x1c58, AR0 = 0x1c60, AR3 = 0x1c6c,
       AR5 = 0x1c74, CXBNDRY = 0x1c80, FXBNDRY = 0x1c84, YDSTLEN = 0x1c88, PITCH = 0x1c8c, YDSTORG = 0x1c94,
       YTOP = 0x1c98, YBOT = 0x1c9c, OPMODE = 0x1e54, DR0 = 0x1cc0, DR2 = 0x1cc8, DR3 = 0x1ccc, DR4 = 0x1cd0, DR6 = 0x1cd8,
       DR7 = 0x1cdc, DR8 = 0x1ce0, DR10 = 0x1ce8, DR11 = 0x1cec, DR12 = 0x1cf0, DR14 = 0x1cf8, DR15 = 0x1cfc,
       GO = 0x100 /* a register written at its address + 100h starts the operation */ };
/* DWGCTL */
#define OP_AUTOLINE 0x1u
#define OP_TRAP     0x4u
#define OP_BITBLT   0x8u
#define OP_ILOAD    0x9u
#define OP_FBITBLT  0xcu
#define AT_RPL      (0u << 4)
#define AT_RSTR     (1u << 4)
#define AT_ZI       (3u << 4)
#define AT_BLK      (4u << 4)
#define AT_I        (7u << 4)
#define ZLT         (4u << 8)
#define SOLID       (1u << 11)
#define ARZERO      (1u << 12)
#define SGNZERO     (1u << 13)
#define SHFTZERO    (1u << 14)
#define BOP(x)      ((u32) (x) << 16)
#define TRANS(x)    ((u32) (x) << 20)
#define BMONOLEF    (0x0u << 25)
#define BFCOL       (0x2u << 25)
#define TRANSC      (1u << 30)
/* SGN */
#define SCANLEFT 1u
#define SDY      4u

#define W     640
#define H     480
#define ZBASE 0x180000u /* the Z buffer's byte address: past a 32-bit screen */

static u32 pci_read(u32 bus, u32 dev, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (reg_ & 0xfc));
    return inl(0xcfc);
}
static void pci_write(u32 bus, u32 dev, u32 reg_, u32 v) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (reg_ & 0xfc));
    outl(0xcfc, v);
}

static volatile u32 *mmio;
static volatile u8  *fb;
static u32           bytes;                 /* a pixel's */
static u32           readback = 0x100000;   /* where the next pass is copied to */

static void reg(u32 offset, u32 value) { mmio[offset / 4] = value; }

/* A colour of the pixel width */
static u32 colour(u32 v) { return (bytes == 4) ? v : (v & ((1u << (bytes * 8)) - 1)); }

static void clear(u32 salt) {
    for (u32 i = 0; i < W * H * bytes / 4; i++)
        ((volatile u32 *) fb)[i] = pattern(i % 160, i / 160, salt);
}

static void copy_out(void) {
    for (u32 i = 0; i < W * H * bytes / 4; i++)
        ((volatile u32 *) readback)[i] = ((volatile u32 *) fb)[i];
    readback += W * H * bytes;
}

/* A trapezoid fill as a rectangle: [x, x + w) x [y, y + h) */
static void rect(u32 ctl, u32 x, u32 y, u32 w, u32 h) {
    reg(DWGCTL, OP_TRAP | ARZERO | SGNZERO | SHFTZERO | ctl);
    reg(FXBNDRY, ((x + w) << 16) | x);
    reg(YDSTLEN + GO, (y << 16) | h);
}

static void p_fills(u32 salt) {
    for (u32 b = 0; b < 16; b++) {
        reg(FCOL, colour(pattern(b, 1, salt)));
        rect(SOLID | AT_RSTR | BOP(b), 10 + (b % 8) * 78, 10 + (b / 8) * 70, 70, 60);
    }
    /* Patterned (PAT0, PAT1), opaque and transparent, block and raster, with the screen-door masks */
    reg(PAT0, 0x81422418u ^ salt);
    reg(PAT1, 0x18244281u);
    reg(FCOL, colour(pattern(3, 2, salt)));
    reg(BCOL, colour(pattern(4, 2, salt)));
    rect(AT_BLK | BOP(0xc), 10, 160, 150, 100);
    rect(AT_BLK | BOP(0xc) | TRANSC, 170, 160, 150, 100);
    rect(AT_RSTR | BOP(0x6), 330, 160, 150, 100);
    rect(AT_RSTR | BOP(0xc) | TRANSC, 490, 160, 140, 100);
    reg(PAT0, 0xffffffffu);
    reg(PAT1, 0xffffffffu);
    for (u32 t = 1; t < 8; t++) {
        reg(FCOL, colour(pattern(t, 5, salt)));
        rect(SOLID | ((t & 1) ? AT_BLK : AT_RSTR) | BOP(0xc) | TRANS(t), 10 + (t - 1) * 88, 280, 80, 180);
    }
}

/* A screen-to-screen blit of w x h from (sx, sy) to (dx, dy), walking from the right and/or the bottom first */
static void blit(u32 ctl, u32 sx, u32 sy, u32 dx, u32 dy, u32 w, u32 h, int left, int up) {
    const u32 row   = up ? sy + h - 1 : sy;
    const u32 start = row * W + (left ? sx + w - 1 : sx);
    const u32 end   = left ? start - (w - 1) : start + (w - 1);
    reg(DWGCTL, OP_BITBLT | SHFTZERO | ctl);
    reg(SGN, (left ? SCANLEFT : 0) | (up ? SDY : 0));
    reg(AR5, up ? (u32) -(int) W : W);
    reg(AR0, end);
    reg(AR3, start);
    reg(FXBNDRY, ((dx + w - 1) << 16) | dx);
    reg(YDSTLEN + GO, ((up ? dy + h - 1 : dy) << 16) | h);
}

static void p_blits(u32 salt) {
    for (u32 k = 0; k < 8; k++) {
        const u32 sx = 20 + (k % 4) * 150, sy = 20 + (k / 4) * 220;
        const int ox = (k & 4) ? 9 : 40, oy = (k & 4) ? 5 : 100;
        /* overlapping copies walk away from the overlap, as a driver does */
        blit(AT_RSTR | BFCOL | BOP((k == 6) ? 0x6 : 0xc), sx, sy, sx + (u32) ox, sy + (u32) oy, 100, 90, (k & 1) != 0,
             (k & 2) != 0);
    }
    /* A smear: a copy 3 pixels right, left to right, reading what it has just drawn */
    blit(AT_RSTR | BFCOL | BOP(0xc), 20, 440, 23, 440, 200, 20, 0, 0);
    /* The fast blit */
    blit(AT_RPL | BFCOL | BOP(0xc), 300, 300, 330, 420, 120, 40, 0, 0);
    /* Mono expansion from video memory (a bit address), opaque and transparent */
    reg(FCOL, colour(pattern(7, 3, salt)));
    reg(BCOL, colour(pattern(8, 3, salt)));
    for (u32 t = 0; t < 4; t++) {
        const u32 start = 8u * (200 * W * bytes), w = 64, h = 40;
        reg(DWGCTL, OP_BITBLT | SHFTZERO | SGNZERO | ((t & 2) ? AT_BLK : AT_RSTR) | BMONOLEF | BOP(0xc) | ((t & 1) ? TRANSC : 0));
        reg(AR5, w);
        reg(AR0, start + w - 1);
        reg(AR3, start);
        reg(FXBNDRY, ((300 + t * 80 + w - 1) << 16) | (300 + t * 80));
        reg(YDSTLEN + GO, (20u << 16) | h);
    }
    (void) salt;
}

static void p_lines(u32 salt) {
    for (u32 o = 0; o < 16; o++) {
        const u32 x0 = 160 + (o % 4) * 100, y0 = 120 + (o / 4) * 90;
        const int dx = ((o & 1) ? 1 : -1) * (int) (30 + o * 5), dy = ((o & 2) ? 1 : -1) * (int) (60 - o * 3);
        reg(FCOL, colour(pattern(o, 4, salt)));
        reg(DWGCTL, OP_AUTOLINE | SOLID | SHFTZERO | AT_RSTR | BOP((o & 4) ? 0x6 : 0xc));
        reg(XYSTRT, (y0 << 16) | x0);
        reg(XYEND + GO, (((u32) ((int) y0 + dy)) << 16) | (u32) ((int) x0 + dx));
    }
    /* Gouraud lines, the second and third through a 16-bit Z buffer (cleared first, then less-than) */
    reg(ZORG, ZBASE);
    for (u32 i = 0; i < W * 50 / 2; i++)
        ((volatile u32 *) (fb + ZBASE))[i] = 0xffffffffu;
    for (u32 l = 0; l < 3; l++) {
        reg(DR0, (0x4000u + l * 0x1000u) << 15);
        reg(DR2, 0x40u << 15);
        reg(DR3, 0x40u << 15);
        reg(DR4, (0x20u + l * 0x30u) << 15);
        reg(DR6, 0x1u << 14);
        reg(DR7, 0x1u << 14);
        reg(DR8, (0x80u + l * 0x10u) << 15);
        reg(DR10, 0x2u << 13);
        reg(DR11, 0x2u << 13);
        reg(DR12, (0xc0u - l * 0x20u) << 15);
        reg(DR14, (u32) -(0x1 << 13));
        reg(DR15, (u32) -(0x1 << 13));
        reg(DWGCTL, OP_AUTOLINE | SHFTZERO | (l ? (AT_ZI | ZLT) : AT_I) | BOP(0xc));
        reg(XYSTRT, ((10u + l * 6) << 16) | 20);
        reg(XYEND + GO, ((30u + l * 4) << 16) | 600);
    }
}

/* Host data into [x, x + w) x [y, y + h): n words through the control aperture's window */
static void iload(u32 ctl, u32 x, u32 y, u32 w, u32 h, u32 n, u32 salt) {
    reg(DWGCTL, OP_ILOAD | SGNZERO | SHFTZERO | ctl);
    reg(AR0, w - 1);
    reg(AR3, 0);
    reg(AR5, 0);
    reg(FXBNDRY, ((x + w - 1) << 16) | x);
    reg(YDSTLEN + GO, (y << 16) | h);
    for (u32 i = 0; i < n; i++)
        mmio[i & 0x3ff] = pattern(i, 6, salt);
}

static void p_host(u32 salt) {
    /* Colour, a row a whole number of words (64 pixels) */
    iload(AT_RSTR | BFCOL | BOP(0xc), 20, 20, 64, 60, 64 * bytes / 4 * 60, salt);
    iload(AT_RSTR | BFCOL | BOP(0x6), 100, 20, 64, 60, 64 * bytes / 4 * 60, salt + 1);
    /* Mono, opaque and transparent: two words a row */
    reg(FCOL, colour(pattern(1, 7, salt)));
    reg(BCOL, colour(pattern(2, 7, salt)));
    iload(AT_RSTR | BMONOLEF | BOP(0xc), 200, 20, 64, 60, 2 * 60, salt + 2);
    iload(AT_BLK | BMONOLEF | BOP(0xc) | TRANSC, 280, 20, 64, 60, 2 * 60, salt + 3);
}

enum { AR1 = 0x1c64, AR2 = 0x1c68, AR4 = 0x1c70, AR6 = 0x1c78, TMR0 = 0x2c00, TEXORG = 0x2c24, TEXWIDTH = 0x2c28,
       TEXHEIGHT = 0x2c2c, TEXCTL = 0x2c30, TEXTRANS = 0x2c34, TEXFILTER = 0x2c58 };
#define OP_TEXTURE_TRAP 0x6u
#define SDXR            0x20u
#define TEXBASE         0x1e0000u /* the texture: past the Z buffer's first 300 rows */

/* A trapezoid from [xl, xr) at row y, h rows: its left edge moving right a pixel every 2 rows and its right edge
   left one every 3 */
static void trap(u32 ctl, u32 xl, u32 xr, u32 y, u32 h) {
    reg(DWGCTL, ctl | SHFTZERO);
    reg(AR0, 2);
    reg(AR1, 0);
    reg(AR2, (u32) -1);
    reg(AR6, 3);
    reg(AR4, 0);
    reg(AR5, (u32) -1);
    reg(SGN, SDXR);
    reg(FXBNDRY, (xr << 16) | xl);
    reg(YDSTLEN + GO, (y << 16) | h);
}

/* Shaded trapezoids (16 and 32 bits): Gouraud, without and through a 16-bit Z buffer (less-than), and textured
   (64 x 64 RGB565, nearest and bilinear, with and without modulation by the shading) */
static void p_shaded(u32 salt) {
    reg(ZORG, ZBASE);
    for (u32 i = 0; i < W * 300 / 2; i++)
        ((volatile u32 *) (fb + ZBASE))[i] = 0xffffffffu;
    for (u32 i = 0; i < 64 * 64 / 2; i++)
        ((volatile u32 *) (fb + TEXBASE))[i] = pattern(i % 32, i / 32, salt);
    for (u32 k = 0; k < 6; k++) {
        reg(DR0, (0x2000u + k * 0x1800u) << 15);
        reg(DR2, (u32) (((int) k - 3) * 0x40) << 15);
        reg(DR3, 0x20u << 15);
        reg(DR4, (0x20u + k * 0x20u) << 15);
        reg(DR6, 0x1u << 14);
        reg(DR7, (u32) -(0x1 << 13));
        reg(DR8, (0x40u + k * 0x10u) << 15);
        reg(DR10, (u32) -(0x1 << 14));
        reg(DR11, 0x1u << 14);
        reg(DR12, (0xe0u - k * 0x18u) << 15);
        reg(DR14, 0x1u << 13);
        reg(DR15, 0x1u << 13);
        trap(OP_TRAP | ((k < 2) ? AT_I : (AT_ZI | ZLT)) | BOP(0xc), 20 + (k % 3) * 200, 200 + (k % 3) * 200,
             10 + (k / 3) * 60, 120);
    }
    reg(TEXORG, TEXBASE);
    reg(TEXWIDTH, 6u | (63u << 18));
    reg(TEXHEIGHT, 6u | (63u << 18));
    reg(TEXTRANS, 0);
    for (u32 k = 0; k < 4; k++) {
        reg(TEXCTL, 3u | (3u << 16) | (1u << 21) | ((k & 2) ? (1u << 29) : 0)); /* RGB565, pitch 64, NPCEN */
        reg(TEXFILTER, k & 1);
        reg(TMR0 + 6 * 4, (k * 5u) << 14);                    /* s */
        reg(TMR0 + 7 * 4, (k * 3u) << 14);                    /* t */
        reg(TMR0 + 0 * 4, (u32) (0x5000 + k * 0x1000));       /* ds/dx */
        reg(TMR0 + 1 * 4, (u32) (0x1800 - k * 0x400));        /* ds/dy */
        reg(TMR0 + 2 * 4, (u32) (0x1000 + k * 0x800));        /* dt/dx */
        reg(TMR0 + 3 * 4, (u32) (0x4000 + k * 0x800));        /* dt/dy */
        reg(TMR0 + 4 * 4, 0);
        reg(TMR0 + 5 * 4, 0);
        reg(TMR0 + 8 * 4, 0);
        reg(DR0, (0x1000u + k * 0x2000u) << 15);
        reg(DR2, 0);
        reg(DR3, 0x10u << 15);
        reg(DR4, 0xc0u << 15);
        reg(DR8, (0x60u + k * 0x20u) << 15);
        reg(DR12, 0xffu << 15);
        trap(OP_TEXTURE_TRAP | ((k & 1) ? (AT_ZI | ZLT) : AT_I) | BOP(0xc), 20 + k * 150, 160 + k * 150, 200, 90);
    }
}

/* The control aperture: the 16 KB BAR (BAR 0 on the Millennium and Mystique, BAR 1 on the Mystique 220 and
   Millennium II) */
static int find(void) {
    for (u32 b = 0; b < 2; b++)
        for (u32 d = 0; d < 32; d++) {
            if ((pci_read(b, d, 0) & 0xffff) != 0x102b)
                continue;
            for (u32 bar = 0x10; bar <= 0x14; bar += 4) {
                const u32 at = pci_read(b, d, bar);
                pci_write(b, d, bar, 0xffffffffu);
                const u32 size = ~(pci_read(b, d, bar) & ~0xfu) + 1;
                pci_write(b, d, bar, at);
                if (size == 0x4000) {
                    mmio = (volatile u32 *) (at & ~0xfu);
                    return 1;
                }
            }
        }
    return 0;
}

void test_main(void) {
    __asm__ volatile("fninit");
    if (!find() || (vbe_modes() < 0))
        return;
    const u16 mode = vbe_find(W, H, 8);
    if (!mode || (int10(0x4f02, (u16) (mode | 0x4000), 0, 0, 0, 0) != 0x004f))
        return;
    fb = (volatile u8 *) VBE_MODE->framebuffer;
    static const u32 widths[4] = { 0, 1, 3, 2 }; /* MACCESS: 8, 16, 24 and 32 bits */
    static void (*const passes[])(u32) = { p_fills, p_blits, p_lines, p_host };
    for (u32 wi = 0; wi < 4; wi++) {
        bytes = (wi == 0) ? 1 : (wi == 1) ? 2 : (wi == 2) ? 3 : 4;
        reg(MACCESS, widths[wi] | (1u << 30)); /* no dithering */
        reg(PITCH, W);
        reg(YDSTORG, 0);
        reg(PLNWT, 0xffffffffu);
        reg(CXBNDRY, ((W - 1) << 16) | 0);
        reg(YTOP, 0);
        reg(YBOT, 0x7fffff);
        reg(SHIFT, 0);
        reg(OPMODE, 1u << 2); /* DMAMOD 1: the window takes ILOAD data, not register writes */
        for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
            clear(0x20 + p + wi * 8);
            passes[p](p + wi * 8);
            wait_ticks(4);
            copy_out();
        }
        if ((bytes == 2) || (bytes == 4)) { /* the shaded trapezoids draw 16 and 32-bit pixels */
            clear(0x30 + wi);
            p_shaded(0x38 + wi);
            wait_ticks(4);
            copy_out();
        }
    }
}
