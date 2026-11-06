/*
 * KairoX86's ATI Mach64 2D test (KairoX86#283, for #237): on any Mach64 (PCI 1002h: 4758h GX, 4354h CT, 5654h VT,
 * 5655h VT2, 4755h 3D Rage II+; or an ISA/VLB GX found by its registers), 640 x 480 x 16 with its linear frame buffer
 * and the registers in the aperture's top 1K (VESA where the BIOS has it; the GX's BIOS does not, so its CRTC, RAMDAC
 * and aperture are programmed directly), a series of passes through the 2D engine, each over a clear and
 * held four ticks of the BIOS clock: rectangle fills through every mix (the average with its carry chain among them)
 * and write masks; blits screen to screen apart and overlapping both ways; the mono 8x8 and colour 4x2 and 8x1
 * patterns; a source pattern wrapping (with rotation); a linear source, byte aligned; mono expansion from a 1 bpp
 * source and from the host, colour data from the host, byte aligned; lines of every octant, polygon outlines into a
 * 1 bpp boundary and polygon fills from it; the destination colour compare; the scissors; tiled rectangles; packed
 * 24 bpp (8 bpp with rotation); 1 bpp and 4 bpp destinations. The engine's status is never read: each pass waits on
 * the BIOS clock. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    return inl(0xcfc);
}

static volatile u32 *mmio;

static void reg(u32 offset, u32 value) { mmio[offset / 4] = value; }

enum {
    DST_OFF_PITCH = 0x100, DST_Y_X = 0x10c, DST_HEIGHT_WIDTH = 0x118, DST_BRES_LNTH = 0x120, DST_BRES_ERR = 0x124,
    DST_BRES_INC = 0x128, DST_BRES_DEC = 0x12c, DST_CNTL = 0x130, SRC_OFF_PITCH = 0x180, SRC_Y_X = 0x18c,
    SRC_HEIGHT1_WIDTH1 = 0x198, SRC_Y_X_START = 0x1a4, SRC_HEIGHT2_WIDTH2 = 0x1b0, SRC_CNTL = 0x1b4, HOST_DATA0 = 0x200,
    HOST_CNTL = 0x240, PAT_REG0 = 0x280, PAT_REG1 = 0x284, PAT_CNTL = 0x288, SC_LEFT_RIGHT = 0x2a8,
    SC_TOP_BOTTOM = 0x2b4, DP_BKGD_CLR = 0x2c0, DP_FRGD_CLR = 0x2c4, WRITE_MASK = 0x2c8, CHAIN_MASK = 0x2cc,
    DP_PIX_WIDTH = 0x2d0, DP_MIX = 0x2d4, DP_SRC = 0x2d8, CLR_CMP_CLR = 0x300, CLR_CMP_MASK = 0x304,
    CLR_CMP_CNTL = 0x308,
};

/* DST_CNTL */
#define X_DIR    0x01u
#define Y_DIR    0x02u
#define Y_MAJOR  0x04u
#define X_TILE   0x08u
#define Y_TILE   0x10u
#define LAST_PEL 0x20u
#define POLYGON  0x40u
#define ROT24    0x80u
#define BRES_SGN 0x800u
/* SRC_CNTL */
#define PATT_EN    1u
#define PATT_ROT   2u
#define LINEAR     4u
#define BYTE_ALIGN 8u
#define LINE_XDIR  16u
/* DP_SRC: background, foreground, mono */
#define DPSRC(bg, fg, mono) ((u32) (bg) | ((u32) (fg) << 8) | ((u32) (mono) << 16))
enum { S_BG = 0, S_FG = 1, S_HOST = 2, S_BLIT = 3, S_PAT = 4 };
enum { M_1 = 0, M_PAT = 1, M_HOST = 2, M_BLIT = 3 };

static u32 width_px; /* the screen's pitch in pixels of the destination's width */

static void common(u32 dst_bits_code, u32 dst_pitch_px, u32 src_pitch_px) {
    reg(DST_OFF_PITCH, ((dst_pitch_px / 8) << 22) | 0);
    reg(SRC_OFF_PITCH, ((src_pitch_px / 8) << 22) | (0x100000u / 8));
    reg(SC_LEFT_RIGHT, ((u32) 0x0fff << 16) | 0);
    reg(SC_TOP_BOTTOM, ((u32) 0x3fff << 16) | 0);
    reg(WRITE_MASK, 0xffffffffu);
    reg(CLR_CMP_CNTL, 0);
    reg(DP_PIX_WIDTH, dst_bits_code | (dst_bits_code << 8) | (dst_bits_code << 16));
}

static void rect(int x, int y, int w, int h, u32 cntl) {
    reg(DST_CNTL, cntl);
    reg(DST_Y_X, ((u32) (x & 0x1fff) << 16) | (u32) (y & 0x7fff));
    reg(DST_HEIGHT_WIDTH, ((u32) w << 16) | (u32) h);
}

static void line(int x0, int y0, int x1, int y1, u32 extra) {
    int dx = x1 - x0, dy = y1 - y0;
    int adx = dx < 0 ? -dx : dx, ady = dy < 0 ? -dy : dy;
    int ymaj = ady > adx;
    int major = ymaj ? ady : adx, minor = ymaj ? adx : ady;
    reg(DST_CNTL, ((dx >= 0) ? X_DIR : 0) | ((dy >= 0) ? Y_DIR : 0) | (ymaj ? Y_MAJOR : 0) | extra);
    reg(DST_Y_X, ((u32) (x0 & 0x1fff) << 16) | (u32) (y0 & 0x7fff));
    reg(DST_BRES_ERR, (u32) (2 * minor - major) & 0x3ffffu);
    reg(DST_BRES_INC, (u32) (2 * minor) & 0x3ffffu);
    reg(DST_BRES_DEC, (u32) (2 * (minor - major)) & 0x3ffffu);
    reg(DST_BRES_LNTH, (u32) (major + 1));
}

static void host_words(u32 n, u32 salt) {
    for (u32 i = 0; i < n; i++)
        reg(HOST_DATA0 + 4 * (i & 15), pattern(i, 5, salt));
}

typedef void (*pass_fn)(u32 p);

/* The GX, whose BIOS has no VESA: its aperture (the BAR on PCI, else CONFIG_CNTL: 4 MB at 12 MB), the 68860 RAMDAC at
   16 bpp 5:6:5 and the CRTC at 640 x 480. The frame buffer's address. */
static u32 gx_mode(u32 bar) {
    enum { CONFIG_CNTL_PORT = 0x6aec, CRTC_H_TOTAL_DISP = 0x00, CRTC_H_SYNC = 0x04, CRTC_V_TOTAL_DISP = 0x08,
           CRTC_V_SYNC = 0x0c, CRTC_OFF_PITCH = 0x14, CRTC_GEN_CNTL = 0x1c, DAC_REGS = 0xc0, DAC_CNTL = 0xc4,
           GEN_TEST_CNTL = 0xd0 };
    const u32 lfb = bar ? bar : 0x00c00000u;
    if (bar) {
        outl(CONFIG_CNTL_PORT, 2);
        mmio = (volatile u32 *) (lfb + 0x7ffc00u);
    } else {
        outl(CONFIG_CNTL_PORT, ((lfb >> 22) << 4) | 1);
        mmio = (volatile u32 *) (lfb + 0x3ffc00u);
    }
    reg(GEN_TEST_CNTL, mmio[GEN_TEST_CNTL / 4] & ~0x100u);
    reg(GEN_TEST_CNTL, mmio[GEN_TEST_CNTL / 4] | 0x100u);
    const u32 dac = mmio[DAC_CNTL / 4];
    reg(DAC_CNTL, (dac & ~3u) | 2);
    ((volatile u8 *) mmio)[DAC_REGS + 3] = 0xa1; /* its register 0Bh, the mode */
    reg(DAC_CNTL, dac & ~3u);
    reg(CRTC_H_TOTAL_DISP, (79u << 16) | 99);
    reg(CRTC_H_SYNC, (12u << 16) | 82);
    reg(CRTC_V_TOTAL_DISP, (479u << 16) | 524);
    reg(CRTC_V_SYNC, (2u << 16) | 489);
    reg(CRTC_OFF_PITCH, 80u << 22);
    reg(CRTC_GEN_CNTL, (1u << 25) | (1u << 24) | (4u << 8));
    return lfb;
}

static void p_fills(u32 p) {
    common(4, width_px, width_px);
    reg(DP_SRC, DPSRC(S_BG, S_FG, M_1));
    reg(CHAIN_MASK, 0x7bef);
    for (u32 m = 0; m < 17; m++) {
        reg(DP_FRGD_CLR, pattern(m, p, 1));
        reg(DP_MIX, ((m == 16) ? 0x17u : m) << 16);
        reg(WRITE_MASK, (m & 1) ? 0x00fff0f0u : 0xffffffffu);
        rect(20 + (int) (m % 6) * 100, 20 + (int) (m / 6) * 140, 90, 120, X_DIR | Y_DIR);
    }
}

static void p_blits(u32 p) {
    common(4, width_px, width_px);
    reg(SRC_OFF_PITCH, ((width_px / 8) << 22) | 0);
    reg(DP_SRC, DPSRC(S_BLIT, S_BLIT, M_1));
    reg(DP_MIX, 0x00070000u | ((p & 1) ? 0x00050000u : 0));
    reg(SRC_CNTL, 0);
    for (u32 k = 0; k < 8; k++) {
        const u32 g = pattern(k, p, 2);
        int       sx = 10 + (int) (g % 300), sy = 10 + (int) ((g >> 9) % 200), w = 40 + (int) ((g >> 17) % 200),
            h  = 30 + (int) ((g >> 23) % 150);
        int dx = sx + ((k & 1) ? 13 : -9), dy = sy + ((k & 2) ? 7 : -11);
        /* overlapping copies, in the direction that keeps the source (and once the other way) */
        u32 cntl = ((dx > sx) ? 0 : X_DIR) | ((dy > sy) ? 0 : Y_DIR);
        if (k == 7)
            cntl ^= X_DIR | Y_DIR;
        int xs = (cntl & X_DIR) ? sx : sx + w - 1, ys = (cntl & Y_DIR) ? sy : sy + h - 1;
        int xd = (cntl & X_DIR) ? dx : dx + w - 1, yd = (cntl & Y_DIR) ? dy : dy + h - 1;
        reg(SRC_Y_X, ((u32) xs << 16) | (u32) ys);
        reg(SRC_HEIGHT1_WIDTH1, ((u32) w << 16) | (u32) h);
        rect(xd, yd, w, h, cntl);
    }
}

static void p_patterns(u32 p) {
    common(4, width_px, width_px);
    reg(PAT_REG0, pattern(1, p, 3));
    reg(PAT_REG1, pattern(2, p, 3));
    reg(DP_BKGD_CLR, 0x1234);
    reg(DP_FRGD_CLR, 0xfedc);
    reg(DP_MIX, 0x00070003u | ((p & 1) ? 0x0005000cu : 0));
    for (u32 k = 0; k < 6; k++) {
        reg(PAT_CNTL, (k < 2) ? 1u : (k < 4) ? 2u : 4u);
        reg(DP_SRC, (k < 2) ? DPSRC(S_BG, S_FG, M_PAT) : DPSRC(S_PAT, S_PAT, M_1));
        rect(30 + (int) k * 100, 30 + (int) (k & 1) * 200, 90, 180, X_DIR | Y_DIR | ((k == 5) ? 0 : 0));
    }
}

static void p_srcpattern(u32 p) {
    common(4, width_px, width_px);
    reg(SRC_OFF_PITCH, ((width_px / 8) << 22) | 0);
    reg(DP_SRC, DPSRC(S_BLIT, S_BLIT, M_1));
    reg(DP_MIX, 0x00070000u);
    for (u32 k = 0; k < 4; k++) {
        reg(SRC_CNTL, PATT_EN | ((k & 1) ? PATT_ROT : 0));
        reg(SRC_Y_X, ((u32) (300 + k * 20) << 16) | (u32) (300 + k * 10));
        reg(SRC_HEIGHT1_WIDTH1, (17u << 16) | 13u);
        reg(SRC_Y_X_START, ((u32) (305 + k * 20) << 16) | (u32) (304 + k * 10));
        reg(SRC_HEIGHT2_WIDTH2, (9u << 16) | 7u);
        rect(20 + (int) k * 150, 20, 140, 260, X_DIR | Y_DIR | ((k == 3) ? 0 : 0));
    }
    /* a linear source, byte aligned, mono expanded */
    reg(SRC_OFF_PITCH, (8u << 22) | (0x100000u / 8) | 1u);
    reg(SRC_CNTL, LINEAR | BYTE_ALIGN);
    reg(DP_SRC, DPSRC(S_BG, S_FG, M_BLIT));
    reg(DP_FRGD_CLR, 0xf800);
    reg(DP_BKGD_CLR, 0x001f);
    reg(SRC_Y_X, 0);
    rect(40, 300, 211, 150, X_DIR | Y_DIR);
    reg(SRC_CNTL, LINEAR);
    rect(300, 300, 133, 150, X_DIR | Y_DIR);
}

static void p_host(u32 p) {
    common(4, width_px, width_px);
    reg(SRC_CNTL, 0);
    reg(DP_FRGD_CLR, 0x07e0);
    reg(DP_BKGD_CLR, 0x7800);
    reg(DP_MIX, 0x00070003u);
    for (u32 k = 0; k < 4; k++) {
        reg(HOST_CNTL, (k & 1) ? 1u : 0u);
        reg(DP_SRC, DPSRC(S_BG, S_FG, M_HOST));
        const int w = 37 + (int) k * 11, h = 40;
        rect(20 + (int) k * 150, 20, w, h, X_DIR | Y_DIR);
        host_words((u32) ((w * h + 31) / 32 + ((k & 1) ? (u32) h : 0)), p * 8 + k);
    }
    /* colour data from the host */
    reg(HOST_CNTL, 0);
    reg(DP_SRC, DPSRC(S_HOST, S_HOST, M_1));
    for (u32 k = 0; k < 3; k++) {
        const int w = 31 + (int) k * 20, h = 50;
        rect(30 + (int) k * 180, 200, w, h, ((k == 2) ? 0 : X_DIR) | Y_DIR);
        host_words((u32) ((w * h + 1) / 2), p * 8 + 4 + k);
    }
}

static void p_lines(u32 p) {
    common(4, width_px, width_px);
    reg(DP_SRC, DPSRC(S_BG, S_FG, M_1));
    reg(DP_MIX, 0x00070000u | ((p & 1) ? 0x000f0000u : 0));
    for (u32 k = 0; k < 40; k++) {
        const u32 g = pattern(k, p, 6);
        reg(DP_FRGD_CLR, g);
        line(320, 240, (int) (g % 640), (int) ((g >> 10) % 480), (k & 1) ? LAST_PEL : 0);
    }
}

static void p_polygon(u32 p) {
    /* The outline into a 1 bpp boundary at 1 MB (pitch 640), then the fill from it */
    common(0, 640, 640);
    reg(DST_OFF_PITCH, ((640u / 8) << 22) | (0x100000u / 8));
    reg(DP_SRC, DPSRC(S_BG, S_FG, M_1));
    reg(DP_FRGD_CLR, 1);
    reg(DP_BKGD_CLR, 0);
    reg(DP_MIX, 0x00010000u);
    rect(0, 0, 640, 480, X_DIR | Y_DIR);
    reg(DP_MIX, 0x00070000u);
    const int vx[5] = { 100, 500, 560, 320, 60 }, vy[5] = { 60, 90, 400, 300, 420 };
    for (int i = 0; i < 5; i++)
        line(vx[i], vy[i], vx[(i + 1) % 5], vy[(i + 1) % 5], POLYGON);
    common(4, width_px, 640);
    reg(SRC_CNTL, 0);
    reg(SRC_Y_X, 0);
    reg(DP_SRC, DPSRC(S_BG, S_FG, M_1));
    reg(DP_FRGD_CLR, pattern(p, 7, 7));
    reg(DP_MIX, 0x00070000u);
    rect(0, 0, 640, 480, X_DIR | Y_DIR | POLYGON);
}

static void p_misc(u32 p) {
    common(4, width_px, width_px);
    /* the destination compare, the scissors, tiles */
    reg(DP_SRC, DPSRC(S_BG, S_FG, M_1));
    reg(DP_MIX, 0x00070000u);
    reg(CLR_CMP_CLR, 0x0000);
    reg(CLR_CMP_MASK, 0x0003);
    reg(CLR_CMP_CNTL, 4u);
    reg(DP_FRGD_CLR, 0xffff);
    rect(20, 20, 200, 200, X_DIR | Y_DIR);
    reg(CLR_CMP_CNTL, 0);
    reg(SC_LEFT_RIGHT, (400u << 16) | 260u);
    reg(SC_TOP_BOTTOM, (300u << 16) | 40u);
    reg(DP_FRGD_CLR, pattern(p, 8, 8));
    rect(240, 20, 220, 300, X_DIR | Y_DIR);
    reg(SC_LEFT_RIGHT, (0x0fffu << 16));
    reg(SC_TOP_BOTTOM, (0x3fffu << 16));
    for (u32 k = 0; k < 5; k++) {
        reg(DP_FRGD_CLR, pattern(k, p, 9));
        rect((k == 0) ? 480 : -1, 20, 30, 25, X_DIR | Y_DIR | X_TILE | Y_TILE);
    }
}

static void p_rot24(u32 p) {
    /* 8 bpp with 24 bpp rotation: three bytes a pixel along a line of 1280 bytes */
    common(2, 1280, 1280);
    reg(DP_SRC, DPSRC(S_BG, S_FG, M_PAT));
    reg(PAT_CNTL, 1);
    reg(PAT_REG0, pattern(3, p, 10));
    reg(PAT_REG1, pattern(4, p, 10));
    reg(DP_FRGD_CLR, 0x00c08040);
    reg(DP_BKGD_CLR, 0x00204060);
    reg(WRITE_MASK, 0x00ff00ffu);
    reg(DP_MIX, 0x00070007u);
    for (u32 k = 0; k < 4; k++)
        rect(30 + (int) k * 300, 20 + (int) k * 100, 3 * (50 + (int) k * 20), 80, X_DIR | Y_DIR | ROT24 | ((k & 1) << 8));
}

static void p_narrow(u32 p) {
    /* 1 bpp and 4 bpp destinations, lines of 5120 and 2560 pixels: fills and a mono expansion */
    for (u32 k = 0; k < 2; k++) {
        const u32 code = k ? 0u : 1u, pitch = k ? 10240u : 2560u;
        common(code, pitch, pitch);
        reg(DP_SRC, DPSRC(S_BG, S_FG, M_PAT));
        reg(PAT_CNTL, 1);
        reg(PAT_REG0, pattern(k, p, 11));
        reg(PAT_REG1, pattern(k + 2, p, 11));
        reg(DP_FRGD_CLR, 0xb);
        reg(DP_BKGD_CLR, 0x4);
        reg(DP_MIX, 0x00070005u);
        rect(3 + (int) k * 7, 10 + (int) k * 120, 333, 100, X_DIR | Y_DIR);
    }
}

static const pass_fn passes[] = { p_fills, p_blits, p_patterns, p_srcpattern, p_host, p_lines, p_polygon, p_misc,
                                  p_rot24, p_narrow, p_fills, p_blits };

void test_main(void) {
    __asm__ volatile("fninit");
    int found = 0;
    u32 gx_bar = 0;
    for (u32 bus = 0; bus < 2 && !found; bus++)
        for (u32 dev = 0; dev < 32 && !found; dev++) {
            const u32 id = pci_read(bus, dev, 0, 0);
            const u32 d  = id >> 16;
            if (((id & 0xffff) == 0x1002) && ((d == 0x4758) || (d == 0x4354) || (d == 0x5654) || (d == 0x5655) || (d == 0x4755)))
                found = 1;
            if (found && (d == 0x4758))
                gx_bar = pci_read(bus, dev, 0, 0x10) & 0xff800000u;
        }
    const u16 mode = vbe_find(640, 480, 16);
    u32       lfb;
    if (mode) {
        if (int10(0x4f02, mode | 0x4000, 0, 0, 0, 0) != 0x004f)
            return;
        lfb = VBE_MODE->framebuffer;
        /* The registers: the top 1K of an 8 MB aperture, or of a 4 MB one when the 8 MB place reads nothing */
        mmio = (volatile u32 *) ((lfb & ~0x7fffffu) + 0x7ffc00u);
        if (mmio[0xe0 / 4] == 0xffffffffu)
            mmio = (volatile u32 *) ((lfb & ~0x3fffffu) + 0x3ffc00u);
        if (!found && (mmio[0xe0 / 4] == 0xffffffffu))
            return;
    } else if ((inl(0x6eec) & 0xffff) == 0x00d7) /* CONFIG_CHIP_ID: a GX, on any bus */
        lfb = gx_mode(gx_bar);
    else
        return;
    width_px = 640;

    /* The source area at 1 MB: the pattern */
    volatile u32 *src = (volatile u32 *) (lfb + 0x100000);
    for (u32 i = 0; i < 0x20000; i++)
        src[i] = pattern(i & 511, i >> 9, 0x2d);

    for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
        volatile u32 *fb = (volatile u32 *) lfb;
        for (u32 i = 0; i < 640 * 480 / 2; i++)
            fb[i] = pattern(i % 320, i / 320, 0x50 + p) & 0x7bef7befu;
        passes[p](p);
        wait_ticks(4);
    }
}
