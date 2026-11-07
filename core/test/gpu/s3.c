/*
 * KairoX86's S3 86C801 to Trio64 graphics engine test (KairoX86#283, for #271): on any S3 with the 8514-style engine
 * (CR30 a chip ID; VESA modes 101h and 111h, 640 x 480 x 8 and x 16, through S3's linear window), the engine through its ports
 * (82E8h-E2E8h, CR40 bit 0 on), passes over a clear, each held four ticks of the BIOS clock: rectangle fills through
 * all 16 mixes and write masks; screen copies in every direction, overlapping, and a smear (a copy reading what it
 * has just drawn); pattern fills; lines in every octant
 * and radial lines; short-stroke vectors; colour and mono data from the host (pixel transfer); the colour compare.
 * The engine's status is never read: it finishes at once. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

enum { CUR_Y = 0x82e8, CUR_X = 0x86e8, DESTY_AXSTP = 0x8ae8, DESTX_DISTP = 0x8ee8, ERR_TERM = 0x92e8, MAJ_AXIS = 0x96e8,
       CMD = 0x9ae8, SHORT_STROKE = 0x9ee8, BKGD_COLOR = 0xa2e8, FRGD_COLOR = 0xa6e8, WRT_MASK = 0xaae8, RD_MASK = 0xaee8,
       COLOR_CMP = 0xb2e8, BKGD_MIX = 0xb6e8, FRGD_MIX = 0xbae8, MULTIFUNC = 0xbee8, PIX_TRANS = 0xe2e8 };
/* CMD */
#define DRAW   0x0010u
#define XPOS   0x0020u
#define YPOS   0x0080u
#define CPU    0x0100u
#define BUS16  0x0200u
#define RADIAL 0x0008u
#define LINE   (1u << 13)
#define RECT   (2u << 13)
#define BLIT   (6u << 13)
#define PATT   (7u << 13)
/* the mixes' sources */
#define SRC_BKGD 0x00u
#define SRC_FRGD 0x20u
#define SRC_CPU  0x40u
#define SRC_DISP 0x60u

static volatile u8 *fb;
static u32          pitch, bpp_bytes;

static void reg(u16 port, u16 v) { outw(port, v); }
static void color(u16 port, u32 v) {
    reg(port, (u16) v);
    if (bpp_bytes > 1)
        reg(port, (u16) (v >> 16)); /* the second write, the high word, where the 16-bit colour mode takes it */
}
static void multi(u16 idx, u16 v) { reg(MULTIFUNC, (u16) ((idx << 12) | (v & 0x0fff))); }

static void clear(u32 salt) {
    for (u32 i = 0; i < pitch * 480 / 4; i++)
        ((volatile u32 *) fb)[i] = pattern(i % 160, i / 160, salt);
}

static void rect(u16 cmd, u32 x, u32 y, u32 w, u32 h) {
    reg(CUR_X, (u16) x);
    reg(CUR_Y, (u16) y);
    reg(MAJ_AXIS, (u16) (w - 1));
    multi(0, (u16) (h - 1));
    reg(CMD, cmd);
}

static void p_fills(u32 salt) {
    multi(0xa, 0x000); /* the foreground mix alone */
    for (u32 m = 0; m < 16; m++) {
        color(FRGD_COLOR, pattern(m, 1, salt));
        reg(WRT_MASK, (m & 1) ? 0xf3cf : 0xffff);
        reg(FRGD_MIX, (u16) (SRC_FRGD | m));
        rect((u16) (RECT | DRAW | XPOS | YPOS), 10 + (m % 6) * 100, 10 + (m / 6) * 150, 90, 140);
    }
    reg(WRT_MASK, 0xffff);
}

static void p_blits(u32 salt) {
    (void) salt;
    reg(FRGD_MIX, SRC_DISP | 7);
    multi(0xa, 0x000);
    for (u32 k = 0; k < 8; k++) {
        const u32 sx = 20 + (k % 4) * 150, sy = 20 + (k / 4) * 220, w = 100, h = 90;
        const int ox = (k & 4) ? 9 : 40, oy = (k & 4) ? 5 : 100;
        const u32 xp = (k & 1) ? 0 : XPOS, yp = (k & 2) ? 0 : YPOS;
        /* the walk starts at the corner it leaves first */
        const u32 fx = xp ? 0 : w - 1, fy = yp ? 0 : h - 1;
        reg(MULTIFUNC, 0xa000);
        reg(CUR_X, (u16) (sx + fx));
        reg(CUR_Y, (u16) (sy + fy));
        reg(DESTX_DISTP, (u16) (sx + (u32) ox + fx));
        reg(DESTY_AXSTP, (u16) (sy + (u32) oy + fy));
        reg(MAJ_AXIS, (u16) (w - 1));
        multi(0, (u16) (h - 1));
        reg(FRGD_MIX, (u16) (SRC_DISP | ((k == 6) ? 5 : 7)));
        reg(CMD, (u16) (BLIT | DRAW | xp | yp));
    }
    /* A smear: a copy 3 pixels right, left to right along each row, reading what it has just drawn */
    reg(FRGD_MIX, SRC_DISP | 7);
    reg(CUR_X, 20);
    reg(CUR_Y, 440);
    reg(DESTX_DISTP, 23);
    reg(DESTY_AXSTP, 440);
    reg(MAJ_AXIS, 199);
    multi(0, 19);
    reg(CMD, (u16) (BLIT | DRAW | XPOS | YPOS));
    /* A pattern fill: the 8 x 8 at (300, 400) over (400, 300) */
    reg(CUR_X, 300);
    reg(CUR_Y, 400);
    reg(DESTX_DISTP, 400);
    reg(DESTY_AXSTP, 300);
    reg(MAJ_AXIS, 199);
    multi(0, 149);
    reg(FRGD_MIX, SRC_DISP | 7);
    reg(CMD, (u16) (PATT | DRAW | XPOS | YPOS));
}

static void p_lines(u32 salt) {
    color(FRGD_COLOR, pattern(2, 1, salt));
    reg(FRGD_MIX, SRC_FRGD | 7);
    multi(0xa, 0x000);
    for (u32 o = 0; o < 8; o++) {
        const int major = 120, minor = 25 + (int) o * 11;
        reg(CUR_X, (u16) (160 + (o % 4) * 100));
        reg(CUR_Y, (u16) (140 + (o / 4) * 200));
        reg(MAJ_AXIS, (u16) major);
        reg(DESTY_AXSTP, (u16) (2 * minor));
        reg(DESTX_DISTP, (u16) (2 * (minor - major)));
        reg(ERR_TERM, (u16) (2 * minor - major));
        reg(CMD, (u16) (LINE | DRAW | ((o & 1) ? XPOS : 0) | ((o & 2) ? YPOS : 0) | ((o & 4) ? 0x40 : 0)));
        /* a radial line, direction o times 45 degrees */
        reg(FRGD_MIX, (u16) (SRC_FRGD | (5 + (o & 1))));
        reg(CUR_X, (u16) (320 + o * 3));
        reg(CUR_Y, 240);
        reg(MAJ_AXIS, (u16) (60 + o * 5));
        reg(CMD, (u16) (LINE | DRAW | RADIAL | (o << 5)));
        reg(FRGD_MIX, SRC_FRGD | 7);
    }
    /* Short-stroke vectors: two a write */
    reg(CUR_X, 50);
    reg(CUR_Y, 450);
    reg(CMD, (u16) (DRAW | XPOS | YPOS));
    for (u32 i = 0; i < 8; i++)
        reg(SHORT_STROKE, (u16) (0x1010 | ((i & 7) << 5) | (((i + 3) & 7) << 13) | 0x0f0f));
}

static void p_host(u32 salt) {
    /* Colour from the host, 16 bits a transfer */
    reg(FRGD_MIX, SRC_CPU | 7);
    multi(0xa, 0x000);
    rect((u16) (RECT | DRAW | XPOS | YPOS | CPU | BUS16), 20, 20, 64, 40);
    for (u32 i = 0; i < 64 * 40 * bpp_bytes / 2; i++)
        reg(PIX_TRANS, (u16) pattern(i, 3, salt));
    /* Mono from the host: the pixel control's CPU data selecting foreground and background */
    color(FRGD_COLOR, pattern(1, 4, salt));
    color(BKGD_COLOR, pattern(2, 4, salt));
    reg(FRGD_MIX, SRC_FRGD | 7);
    reg(BKGD_MIX, SRC_BKGD | 5);
    multi(0xa, 0x080);
    rect((u16) (RECT | DRAW | XPOS | YPOS | CPU | BUS16), 200, 20, 96, 50);
    for (u32 i = 0; i < 96 * 50 / 16 + 50; i++)
        reg(PIX_TRANS, (u16) pattern(i, 5, salt));
    /* Mono from display memory */
    multi(0xa, 0x0c0);
    reg(CUR_X, 0);
    reg(CUR_Y, 300);
    reg(DESTX_DISTP, 400);
    reg(DESTY_AXSTP, 20);
    reg(MAJ_AXIS, 150);
    multi(0, 90);
    reg(CMD, (u16) (BLIT | DRAW | XPOS | YPOS));
    multi(0xa, 0x000);
    /* The colour compare: draw where the source is not the compare colour */
    color(COLOR_CMP, pattern(0, 6, salt) & 0xff);
    multi(0xe, 0x100);
    reg(FRGD_MIX, SRC_DISP | 7);
    reg(CUR_X, 20);
    reg(CUR_Y, 200);
    reg(DESTX_DISTP, 300);
    reg(DESTY_AXSTP, 300);
    reg(MAJ_AXIS, 150);
    multi(0, 90);
    reg(CMD, (u16) (BLIT | DRAW | XPOS | YPOS));
    multi(0xe, 0x000);
}

static u32 pci_read(u32 bus, u32 dev, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (reg_ & 0xfc));
    return inl(0xcfc);
}

static void pci_write(u32 bus, u32 dev, u32 reg_, u32 v) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (reg_ & 0xfc));
    outl(0xcfc, v);
}

/* The S3's PCI address (bus << 8 | device), or -1 on ISA and VLB */
static int pci_at(void) {
    for (u32 b = 0; b < 2; b++)
        for (u32 d = 0; d < 32; d++)
            if ((pci_read(b, d, 0) & 0xffff) == 0x5333)
                return (int) ((b << 8) | d);
    return -1;
}

/* The linear window, placed after the mode set: a PCI S3's BAR 0 at E0000000h, the others at 12 MB (CR59/CR5A, which
   BAR 0 reads). The 86C928 PCI's BIOS leaves them at 000Ah (A0000h), its VESA modes too. Returns its base. */
static u32 lfb_place(void) {
    const int pci = pci_at();
    if (pci >= 0) {
        pci_write((u32) pci >> 8, (u32) pci & 0xff, 0x10, 0xe0000000u);
        return 0xe0000000u;
    }
    outw(0x3d4, 0x4838);
    outw(0x3d4, 0xa539);
    outw(0x3d4, 0x0059);
    outw(0x3d4, 0xc05a);
    return 0x00c00000u;
}

static void run_mode(u32 bpp) {
    /* VESA 640 x 480 (101h, 111h); the BIOS gives no linear frame buffer, so S3's own linear addressing is turned on
       (CR58 bit 4, a 4 MB window), as pvr.c does */
    if (int10(0x4f02, (bpp == 8) ? 0x101 : 0x111, 0, 0, 0, 0) != 0x004f)
        return;
    const u32 base = lfb_place();
    outw(0x3d4, 0x4838);
    outw(0x3d4, 0xa539);
    outb(0x3d4, 0x58);
    outb(0x3d5, (u8) ((inb(0x3d5) & ~0x03) | 0x13));
    pitch     = 640 * (bpp / 8);
    fb        = (volatile u8 *) base;
    bpp_bytes = bpp / 8;
    /* The extended registers unlocked and the enhanced engine on */
    outw(0x3d4, 0x4838);
    outw(0x3d4, 0xa539);
    outb(0x3d4, 0x40);
    outb(0x3d5, (u8) (inb(0x3d5) | 0x01));
    reg(RD_MASK, 0xffff);
    reg(WRT_MASK, 0xffff);
    multi(1, 0);      /* the scissors: all */
    multi(2, 0);
    multi(3, 0xfff);
    multi(4, 0xfff);
    multi(0xe, 0x000);
    static void (*const passes[])(u32) = { p_fills, p_blits, p_lines, p_host };
    for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
        clear(0x30 + p + bpp);
        passes[p](p + bpp);
        wait_ticks(4);
    }
}

void test_main(void) {
    __asm__ volatile("fninit");
    /* An S3: CR30 its chip ID once CR38 is unlocked */
    outw(0x3d4, 0x4838);
    outb(0x3d4, 0x30);
    const u8 id = inb(0x3d5);
    if ((id < 0x81) || (id == 0xff))
        return;
    run_mode(8);
    run_mode(16);
}
