/*
 * KairoX86's 8514/A drawing engine test (KairoX86#283, for #238): on an 8514/A engine (ERR_TERM reads back; an S3,
 * whose engine has the same ports and its own test, returns at once): the IBM 8514/A, ATI's 8514 Ultra, Graphics
 * Ultra (Mach8) and Mach32. The 8514/A display at 640 x 480 x 8 (ADVFUNC_CNTL), and passes, each over a screen
 * filled from the host, held four ticks of the BIOS clock and read back through PIX_TRANS into memory above 1 MB for
 * the end state: rectangle fills through all 32 mixes, write masks and the colour compares; copies in every
 * direction, overlapping, and a smear (a copy reading what it has just drawn); lines in every octant and short-stroke
 * vectors; mono data from the host. On ATI's cards (SCRATCH0 reads back) the Mach engine too: its blits (DEST_Y_END)
 * as fills through the mixes and DEST_CMP_FN's compares, copies and a smear; its vector and Bresenham lines
 * (BRES_COUNT); its scans (SCAN_TO_X). On the Mach32 every pass again with 16-bit pixels (EXT_GE_CONFIG), the
 * display left as it is. The engine's status is never read: it finishes at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

enum { H_TOTAL = 0x02e8, H_DISP = 0x06e8, H_SYNC_STRT = 0x0ae8, H_SYNC_WID = 0x0ee8, V_TOTAL = 0x12e8, V_DISP = 0x16e8,
       V_SYNC_STRT = 0x1ae8, V_SYNC_WID = 0x1ee8, DISP_CNTL = 0x22e8, ADVFUNC = 0x4ae8, DAC_MASK = 0x02ea,
       DAC_W = 0x02ec, DAC_D = 0x02ed };
enum { CUR_Y = 0x82e8, CUR_X = 0x86e8, DESTY_AXSTP = 0x8ae8, DESTX_DISTP = 0x8ee8, ERR_TERM = 0x92e8, MAJ_AXIS = 0x96e8,
       CMD = 0x9ae8, SHORT_STROKE = 0x9ee8, BKGD_COLOR = 0xa2e8, FRGD_COLOR = 0xa6e8, WRT_MASK = 0xaae8, RD_MASK = 0xaee8,
       COLOR_CMP = 0xb2e8, BKGD_MIX = 0xb6e8, FRGD_MIX = 0xbae8, MULTIFUNC = 0xbee8, PIX_TRANS = 0xe2e8 };
/* The Mach engine's (SRC_X and SRC_Y are DESTX_DISTP and DESTY_AXSTP) */
enum { SCRATCH0 = 0x52ee, BRES_COUNT = 0x96ee, LINEDRAW_OPT = 0xa2ee, DEST_X_START = 0xa6ee, DEST_X_END = 0xaaee,
       DEST_Y_END = 0xaeee, SRC_X_START = 0xb2ee, MACH_BKGD_MIX = 0xb6ee, MACH_FRGD_MIX = 0xbaee, SRC_X_END = 0xbeee,
       SRC_Y_DIR = 0xc2ee, SCAN_TO_X = 0xcaee, DP_CONFIG = 0xceee, DEST_CMP_FN = 0xeeee, EXT_GE_CONFIG = 0x7aee };
/* CMD */
#define WRITE  0x0001u
#define SSV    0x0008u
#define DRAW   0x0010u
#define XPOS   0x0020u
#define YPOS   0x0080u
#define CPU    0x0100u
#define BUS16  0x0200u
#define LINE   (1u << 13)
#define RECT   (2u << 13)
#define BLIT   (6u << 13)
/* the mixes' sources */
#define SRC_BKGD 0x00u
#define SRC_FRGD 0x20u
#define SRC_CPU  0x40u
#define SRC_DISP 0x60u
/* DP_CONFIG: write, draw, the foreground source (1 colour, 3 the blit source) */
#define DP_FILL 0x2011u
#define DP_COPY 0x6011u

#define W 640
#define H 480

static int ati;
static int px16;                /* 16-bit pixels: the Mach32 with EXT_GE_CONFIG at 16 bpp */
static u32 readback = 0x100000; /* where the next pass is read back to */

static void reg(u16 port, u16 v) { outw(port, v); }
static void multi(u16 idx, u16 v) { reg(MULTIFUNC, (u16) ((idx << 12) | (v & 0x0fff))); }

/* A colour of the pixel size */
static u16 colour(u32 v) { return (u16) (px16 ? v : (v & 0xff)); }

static void rect(u16 cmd, u32 x, u32 y, u32 w, u32 h) {
    reg(CUR_X, (u16) x);
    reg(CUR_Y, (u16) y);
    reg(MAJ_AXIS, (u16) (w - 1));
    multi(0, (u16) (h - 1));
    reg(CMD, cmd);
}

/* The whole screen from the host, 16 bits (two 8-bit pixels or one 16-bit one) a transfer */
static void clear(u32 salt) {
    const u32 per_row = px16 ? W : W / 2;
    reg(WRT_MASK, 0xffff);
    reg(FRGD_MIX, SRC_CPU | 7);
    multi(0xa, 0x000);
    rect((u16) (RECT | DRAW | WRITE | XPOS | YPOS | CPU | BUS16), 0, 0, W, H);
    for (u32 i = 0; i < per_row * H; i++)
        reg(PIX_TRANS, (u16) pattern(i % per_row, i / per_row, salt));
}

/* w x h pixels at (x, y) read back from the engine into memory at to */
static void read_rect(volatile u16 *to, u32 x, u32 y, u32 w, u32 h) {
    reg(WRT_MASK, 0xffff);
    reg(RD_MASK, 0xffff);
    multi(0xa, 0x000);
    rect((u16) (RECT | DRAW | XPOS | YPOS | CPU | BUS16), x, y, w, h);
    for (u32 i = 0; i < (px16 ? w * h : w * h / 2); i++)
        to[i] = inw(PIX_TRANS);
}

/* The screen read back into memory, for the end state */
static void read_back(void) {
    read_rect((volatile u16 *) readback, 0, 0, W, H);
    readback += px16 ? W * H * 2 : W * H;
}

static void p_fills(u32 salt) {
    multi(0xa, 0x000);
    for (u32 m = 0; m < 32; m++) {
        reg(FRGD_COLOR, colour(pattern(m, 1, salt)));
        reg(WRT_MASK, (m & 1) ? (px16 ? 0xf3cf : 0xf3) : 0xffff);
        reg(FRGD_MIX, (u16) (SRC_FRGD | m));
        rect((u16) (RECT | DRAW | WRITE | XPOS | YPOS), 8 + (m % 8) * 78, 8 + (m / 8) * 60, 70, 52);
    }
    reg(WRT_MASK, 0xffff);
    /* The colour compares (PIX_CNTL bits 5:3): each keeps some of the pixels under it */
    reg(FRGD_MIX, SRC_FRGD | 7);
    reg(COLOR_CMP, colour(pattern(3, 2, salt)));
    for (u32 c = 1; c < 8; c++) {
        multi(0xa, (u16) (c << 3));
        reg(FRGD_COLOR, colour(pattern(c, 3, salt)));
        rect((u16) (RECT | DRAW | WRITE | XPOS | YPOS), 8 + (c - 1) * 90, 260, 84, 200);
    }
    multi(0xa, 0x000);
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
        reg(CUR_X, (u16) (sx + fx));
        reg(CUR_Y, (u16) (sy + fy));
        reg(DESTX_DISTP, (u16) (sx + (u32) ox + fx));
        reg(DESTY_AXSTP, (u16) (sy + (u32) oy + fy));
        reg(MAJ_AXIS, (u16) (w - 1));
        multi(0, (u16) (h - 1));
        reg(FRGD_MIX, (u16) (SRC_DISP | ((k == 6) ? 5 : 7)));
        reg(CMD, (u16) (BLIT | DRAW | WRITE | xp | yp));
    }
    /* A smear: a copy 3 pixels right, left to right along each row, reading what it has just drawn */
    reg(FRGD_MIX, SRC_DISP | 7);
    reg(CUR_X, 20);
    reg(CUR_Y, 440);
    reg(DESTX_DISTP, 23);
    reg(DESTY_AXSTP, 440);
    reg(MAJ_AXIS, 199);
    multi(0, 19);
    reg(CMD, (u16) (BLIT | DRAW | WRITE | XPOS | YPOS));
}

static void p_lines(u32 salt) {
    reg(FRGD_COLOR, colour(pattern(2, 1, salt)));
    multi(0xa, 0x000);
    for (u32 o = 0; o < 8; o++) {
        const int major = 120, minor = 25 + (int) o * 11;
        reg(FRGD_MIX, (u16) (SRC_FRGD | ((o & 1) ? 5 : 7)));
        reg(CUR_X, (u16) (160 + (o % 4) * 100));
        reg(CUR_Y, (u16) (140 + (o / 4) * 200));
        reg(MAJ_AXIS, (u16) major);
        reg(DESTY_AXSTP, (u16) (2 * minor));
        reg(DESTX_DISTP, (u16) (2 * (minor - major)));
        reg(ERR_TERM, (u16) (2 * minor - major));
        reg(CMD, (u16) (LINE | DRAW | WRITE | ((o & 1) ? XPOS : 0) | ((o & 2) ? YPOS : 0) | ((o & 4) ? 0x40 : 0)));
    }
    /* Short-stroke vectors: two a write */
    reg(FRGD_MIX, SRC_FRGD | 7);
    reg(CUR_X, 50);
    reg(CUR_Y, 450);
    reg(CMD, (u16) (SSV | DRAW | WRITE | XPOS | YPOS));
    for (u32 i = 0; i < 8; i++)
        reg(SHORT_STROKE, (u16) (0x1010 | ((i & 7) << 5) | (((i + 3) & 7) << 13) | 0x0f0f));
}

static void p_host(u32 salt) {
    /* Mono from the host: the pixel control's CPU data selecting the foreground and background mixes */
    reg(FRGD_COLOR, colour(pattern(1, 4, salt)));
    reg(BKGD_COLOR, colour(pattern(2, 4, salt)));
    reg(FRGD_MIX, SRC_FRGD | 7);
    reg(BKGD_MIX, SRC_BKGD | 5);
    multi(0xa, 0x080);
    rect((u16) (RECT | DRAW | WRITE | XPOS | YPOS | CPU | BUS16), 200, 20, 96, 50);
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
    reg(CMD, (u16) (BLIT | DRAW | WRITE | XPOS | YPOS));
    multi(0xa, 0x000);
}

/* The Mach engine's blit over [x0, x1) x [y, y_end) (reversed bounds walk the other way) */
static void mach_blit(u16 dp, u32 x, u32 x0, u32 x1, u32 y, u32 y_end) {
    reg(DP_CONFIG, dp);
    reg(CUR_X, (u16) x);
    reg(CUR_Y, (u16) y);
    reg(DEST_X_START, (u16) x0);
    reg(DEST_X_END, (u16) x1);
    reg(DEST_Y_END, (u16) y_end);
}

static void mach_source(u32 x, u32 x0, u32 x1, u32 y, int down) {
    reg(DESTX_DISTP, (u16) x);
    reg(DESTY_AXSTP, (u16) y);
    reg(SRC_X_START, (u16) x0);
    reg(SRC_X_END, (u16) x1);
    reg(SRC_Y_DIR, (u16) down);
}

static void p_mach(u32 salt) {
    reg(WRT_MASK, 0xffff);
    reg(DEST_CMP_FN, 0);
    /* Fills through the mixes */
    for (u32 m = 0; m < 32; m++) {
        reg(FRGD_COLOR, colour(pattern(m, 7, salt)));
        reg(WRT_MASK, (m & 2) ? (px16 ? 0x3cc3 : 0x3c) : 0xffff);
        reg(MACH_FRGD_MIX, (u16) m);
        const u32 x = 8 + (m % 8) * 78, y = 8 + (m / 8) * 50;
        mach_blit(DP_FILL, x, x, x + 70, y, y + 42);
    }
    reg(WRT_MASK, 0xffff);
    /* DEST_CMP_FN's compares (bits 5:3) */
    reg(MACH_FRGD_MIX, 7);
    reg(COLOR_CMP, colour(pattern(5, 2, salt)));
    for (u32 c = 1; c < 8; c++) {
        reg(DEST_CMP_FN, (u16) (c << 3));
        reg(FRGD_COLOR, colour(pattern(c, 8, salt)));
        const u32 x = 8 + (c - 1) * 90;
        mach_blit(DP_FILL, x, x, x + 84, 210, 260);
    }
    reg(DEST_CMP_FN, 0);
    /* Copies down and right, up and left (reversed bounds), and a smear 3 pixels right */
    mach_source(20, 20, 140, 270, 1);
    mach_blit(DP_COPY, 60, 60, 180, 300, 360);
    mach_source(339, 339, 219, 329, 0);
    mach_blit(DP_COPY, 379, 379, 259, 359, 299);
    mach_source(400, 400, 600, 280, 1);
    mach_blit(DP_COPY, 403, 403, 603, 280, 300);
    /* Lines: vectors in all 8 directions (LINEDRAW_OPT bit 3), Bresenham in all 8 octants */
    reg(DP_CONFIG, DP_FILL);
    reg(FRGD_COLOR, colour(pattern(4, 9, salt)));
    for (u32 d = 0; d < 8; d++) {
        reg(MACH_FRGD_MIX, (u16) ((d & 1) ? 5 : 7));
        reg(CUR_X, (u16) (320 + d * 3));
        reg(CUR_Y, 400);
        reg(LINEDRAW_OPT, (u16) (0x08 | (d << 5)));
        reg(BRES_COUNT, (u16) (40 + d * 5));
    }
    for (u32 o = 0; o < 8; o++) {
        const int major = 60, minor = 10 + (int) o * 6;
        reg(CUR_X, (u16) (60 + (o % 4) * 70));
        reg(CUR_Y, (u16) (400 + (o / 4) * 40));
        reg(DESTY_AXSTP, (u16) (2 * minor));
        reg(DESTX_DISTP, (u16) (2 * (minor - major)));
        reg(ERR_TERM, (u16) (2 * minor - major));
        reg(LINEDRAW_OPT, (u16) (((o & 1) ? 0x20 : 0) | ((o & 2) ? 0x80 : 0) | ((o & 4) ? 0x40 : 0)));
        reg(BRES_COUNT, (u16) major);
    }
    /* Scans: a span to SCAN_TO_X per row */
    reg(MACH_FRGD_MIX, 6);
    for (u32 y = 440; y < 470; y++) {
        reg(CUR_X, (u16) (450 + (y & 7)));
        reg(CUR_Y, (u16) y);
        reg(SCAN_TO_X, (u16) (600 - (y & 15)));
    }
    reg(MACH_FRGD_MIX, 7);
}

/* The 8514/A display at 640 x 480 (IBM's timings), its palette a fixed ramp */
static void display(void) {
    reg(H_TOTAL, 0x63);
    reg(H_DISP, 0x4f);
    reg(H_SYNC_STRT, 0x52);
    reg(H_SYNC_WID, 0x2c);
    reg(V_TOTAL, 0x418);
    reg(V_DISP, 0x3bb);
    reg(V_SYNC_STRT, 0x3d2);
    reg(V_SYNC_WID, 0x22);
    reg(DISP_CNTL, 0x23);
    reg(ADVFUNC, 0x03);
    outb(DAC_MASK, 0xff);
    outb(DAC_W, 0);
    for (u32 i = 0; i < 256; i++) {
        outb(DAC_D, (u8) ((i & 7) * 9));
        outb(DAC_D, (u8) (((i >> 3) & 7) * 9));
        outb(DAC_D, (u8) ((i >> 6) * 21));
    }
    reg(RD_MASK, 0xffff);
    reg(WRT_MASK, 0xffff);
    multi(1, 0); /* the scissors: all */
    multi(2, 0);
    multi(3, 0x7ff);
    multi(4, 0x7ff);
    multi(0xa, 0x000);
}

static void run_passes(void) {
    static void (*const passes[])(u32) = { p_fills, p_blits, p_lines, p_host, p_mach };
    for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
        if ((passes[p] == p_mach) && !ati)
            break;
        clear(0x60 + p + px16 * 8);
        passes[p](p + px16 * 8);
        wait_ticks(4);
        read_back();
    }
}

void test_main(void) {
    __asm__ volatile("fninit");
    /* An S3 (CR30 its chip ID once CR38 is unlocked) has its own test */
    outw(0x3d4, 0x4838);
    outb(0x3d4, 0x30);
    const u8 id = inb(0x3d5);
    if ((id >= 0x81) && (id != 0xff))
        return;
    /* An 8514/A engine: ERR_TERM reads back */
    reg(ERR_TERM, 0x5a5);
    if ((inw(ERR_TERM) & 0x3fff) != 0x5a5)
        return;
    reg(SCRATCH0, 0x5aa5); /* not 1234h, which reads back as 0 (vid_ati_mach8.c) */
    ati = (inw(SCRATCH0) == 0x5aa5);
    display();
    run_passes();
    if (!ati)
        return;
    /* The Mach32 again at 16 bpp (EXT_GE_CONFIG): a two-pixel fill reads back as one 16-bit pixel there, as two
       8-bit ones on the others */
    reg(EXT_GE_CONFIG, 0x0060);
    px16 = 1;
    reg(WRT_MASK, 0xffff);
    reg(FRGD_COLOR, 0x1234);
    reg(FRGD_MIX, SRC_FRGD | 7);
    multi(0xa, 0x000);
    rect((u16) (RECT | DRAW | WRITE | XPOS | YPOS), 0, 0, 2, 1);
    volatile u16 *probe = (volatile u16 *) readback;
    read_rect(probe, 0, 0, 1, 1);
    if (probe[0] != 0x1234) {
        px16 = 0;
        return;
    }
    run_passes();
}
