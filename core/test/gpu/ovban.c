/*
 * KairoX86's 3dfx Banshee / Voodoo3 overlay test (KairoX86#283, for #233): on a Banshee or Voodoo3, VESA 640 x 480 x 16
 * with its linear frame buffer, the picture a pattern with a band of one colour and a source placed 2 MB on (the 3D
 * leftOverlayBuf, taken at a swap), shown through the video processor's overlay (vidProcCfg bit 8 and its window,
 * scale and stride registers) in passes, each held six ticks of the BIOS clock: RGB 565 at 1:1, through the chroma
 * key (the band's colour), doubled across and down, YUYV 4:2:2, and against the right edge. Any other card returns at
 * once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    return inl(0xcfc);
}

static volatile u32 *io;   /* the I/O registers (BAR 0) */
static volatile u32 *regs; /* the 3D registers (BAR 0 + 2 MB) */

enum { VID_PROC_CFG = 0x5c, CHROMA_MIN = 0x8c, CHROMA_MAX = 0x90, OV_START = 0x9c, OV_END = 0xa0, OV_DUDX = 0xa4,
       OV_DUDX_OFFSET_SRC_WIDTH = 0xa8, OV_DVDY = 0xac, OV_DVDY_OFFSET = 0xe0, DESKTOP_OVERLAY_STRIDE = 0xe8,
       SWAPBUFFER_CMD = 0x128, LEFT_OVERLAY_BUF = 0x250 };

#define W     640
#define H     480
#define KEY   0xf81fu
#define SRC   0x200000u
#define SRC_W 320
#define SRC_H 240

static void io_reg(u32 offset, u32 value) { io[offset / 4] = value; }

/* The overlay at (x, y), w x h; format (1 RGB 565, 5 YUYV 4:2:2); scale 1 or 2; keyed */
static void overlay(u32 x, u32 y, u32 w, u32 h, u32 format, u32 scale, u32 keyed) {
    u32 cfg = io[VID_PROC_CFG / 4];
    cfg &= ~((1u << 5) | (1u << 6) | (1u << 8) | (1u << 14) | (1u << 15) | (3u << 16) | (7u << 21) | (1u << 25));
    io_reg(VID_PROC_CFG, cfg);
    io_reg(OV_START, (y << 12) | x);
    io_reg(OV_END, ((y + h - 1) << 12) | (x + w - 1));
    io_reg(OV_DUDX, 0x100000u / scale);
    io_reg(OV_DUDX_OFFSET_SRC_WIDTH, (SRC_W * 2u) << 19);
    io_reg(OV_DVDY, 0x100000u / scale);
    io_reg(OV_DVDY_OFFSET, 0);
    io_reg(DESKTOP_OVERLAY_STRIDE, (io[DESKTOP_OVERLAY_STRIDE / 4] & 0x7fffu) | ((SRC_W * 2u) << 16));
    io_reg(CHROMA_MIN, KEY);
    io_reg(CHROMA_MAX, KEY);
    regs[LEFT_OVERLAY_BUF / 4] = SRC;
    regs[SWAPBUFFER_CMD / 4]   = 0; /* the overlay's address taken now */
    cfg |= (1u << 8) | (format << 21);
    if (scale == 2)
        cfg |= (1u << 14) | (1u << 15);
    if (keyed)
        cfg |= 1u << 5;
    io_reg(VID_PROC_CFG, cfg);
}

void test_main(void) {
    __asm__ volatile("fninit");
    u32 mmio = 0;
    u32 lfb  = 0;
    for (u32 bus = 0; bus < 2 && !mmio; bus++)
        for (u32 dev = 0; dev < 32 && !mmio; dev++) {
            const u32 id = pci_read(bus, dev, 0, 0);
            if ((id & 0xffff) == 0x121a && ((id >> 16) == 0x0003 || (id >> 16) == 0x0005 || (id >> 16) == 0x0004)) {
                mmio = pci_read(bus, dev, 0, 0x10) & ~0xfu;
                lfb  = pci_read(bus, dev, 0, 0x14) & ~0xfu;
            }
        }
    if (!mmio)
        return;
    if (int10(0x4f02, 0x4111, 0, 0, 0, 0) != 0x004f)
        return;
    io   = (volatile u32 *) mmio;
    regs = (volatile u32 *) (mmio + 0x200000);

    volatile u16 *fb = (volatile u16 *) lfb;
    for (u32 y = 0; y < H; y++)
        for (u32 x = 0; x < W; x++)
            fb[y * W + x] = ((y >= 200) && (y < 260) && (x >= 60)) ? (u16) KEY : (u16) pattern(x, y, 0x91);
    volatile u16 *src = (volatile u16 *) (lfb + SRC);
    for (u32 i = 0; i < SRC_W * SRC_H; i++)
        src[i] = (u16) pattern(i % SRC_W, i / SRC_W, 0x92);

    static const u32 passes[5][7] = {
        /* x, y, w, h, format, scale, keyed */
        { 100, 60, 300, 200, 1, 1, 0 },
        { 100, 160, 300, 200, 1, 1, 1 },
        { 40, 40, 560, 400, 1, 2, 0 },
        { 160, 100, 240, 180, 5, 1, 0 },
        { 500, 300, 300, 150, 1, 1, 0 },
    };
    for (u32 p = 0; p < 5; p++) {
        overlay(passes[p][0], passes[p][1], passes[p][2], passes[p][3], passes[p][4], passes[p][5], passes[p][6]);
        wait_ticks(6);
    }
    io_reg(VID_PROC_CFG, io[VID_PROC_CFG / 4] & ~(1u << 8));
}
