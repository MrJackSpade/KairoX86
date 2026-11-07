/*
 * KairoX86's ATI Rage 128 overlay test (KairoX86#283, for #233): on a Rage 128 (PCI 1002h: 5046h, 5245h), VESA
 * 640 x 480 x 16 with its linear frame buffer, the picture a pattern with a band of one colour and a source placed
 * 2 MB on, shown through the scaler OV0 (its registers set as the X driver's R128DisplayVideo422 sets them) in passes,
 * each held six ticks of the BIOS clock: RGB 565 at 1:1, through the graphics key (the band's colour), doubled across
 * and down, VYUY 4:2:2, and against the right edge. Any other card returns at once.
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

enum { Y_X_START = 0x400, Y_X_END = 0x404, REG_LOAD_CNTL = 0x410, SCALE_CNTL = 0x420, V_INC = 0x424,
       P1_V_ACCUM_INIT = 0x428, P23_V_ACCUM_INIT = 0x42c, P1_BLANK = 0x430, P23_BLANK = 0x434, BUF0 = 0x440,
       BUF1 = 0x444, BUF2 = 0x448, PITCH0 = 0x460, AUTO_FLIP = 0x470, H_INC = 0x480, STEP_BY = 0x484,
       P1_H_ACCUM_INIT = 0x488, P23_H_ACCUM_INIT = 0x48c, P1_X = 0x494, P2_X = 0x498, P3_X = 0x49c,
       GRAPHICS_KEY_CLR = 0x4ec, GRAPHICS_KEY_MSK = 0x4f0, KEY_CNTL = 0x4f4 };

#define W     640
#define H     480
#define KEY   0xf81fu
#define SRC   0x200000u
#define SRC_W 320
#define SRC_H 240

/* The overlay at (x, y), w x h; format (4 RGB 565, 0Bh VYUY 4:2:2); scale 1 or 2; keyed */
static void overlay(u32 x, u32 y, u32 w, u32 h, u32 format, u32 scale, u32 keyed) {
    const u32 h_inc = 0x1000u / scale;
    reg(REG_LOAD_CNTL, 1); /* the lock, while the window is set */
    reg(H_INC, h_inc | ((h_inc >> 1) << 16));
    reg(STEP_BY, 1u | (1u << 8));
    reg(Y_X_START, x | (y << 16));
    reg(Y_X_END, (x + w - 1) | ((y + h - 1) << 16));
    reg(V_INC, 0x100000u / scale);
    reg(P1_BLANK, 0xfffu | ((SRC_H - 1u) << 16));
    reg(P23_BLANK, 0xfffu | ((SRC_H / 2 - 1u) << 16));
    reg(PITCH0, SRC_W * 2);
    reg(P1_X, SRC_W - 1u);
    reg(P2_X, SRC_W / 2 - 1u);
    reg(P3_X, SRC_W / 2 - 1u);
    reg(BUF0, SRC);
    reg(BUF1, SRC);
    reg(BUF2, SRC);
    reg(AUTO_FLIP, 0);
    reg(P1_V_ACCUM_INIT, 0x00180001u);
    reg(P23_V_ACCUM_INIT, 0x00180001u);
    reg(P1_H_ACCUM_INIT, 0x00028000u);
    reg(P23_H_ACCUM_INIT, 0x00028000u);
    reg(GRAPHICS_KEY_CLR, KEY);
    reg(GRAPHICS_KEY_MSK, 0xffff);
    /* Keyed: the video where the picture matches the key (graphics key 5, the supplement's "equal"), else always
       (graphics key "true"); the video key "false", the two ORed */
    reg(KEY_CNTL, (keyed ? 5u : 1u) << 4);
    reg(SCALE_CNTL, 0x40008003u | (format << 8));
    reg(REG_LOAD_CNTL, 0);
}

void test_main(void) {
    __asm__ volatile("fninit");
    u32 regs = 0;
    for (u32 bus = 0; bus < 2 && !regs; bus++)
        for (u32 dev = 0; dev < 32 && !regs; dev++) {
            const u32 id = pci_read(bus, dev, 0, 0);
            const u32 d  = id >> 16;
            if (((id & 0xffff) == 0x1002) && ((d == 0x5046) || (d == 0x5245)))
                regs = pci_read(bus, dev, 0, 0x18) & ~0xfu;
        }
    if (!regs || vbe_modes() < 0)
        return;
    mmio = (volatile u32 *) regs;
    const u16 mode = vbe_find(W, H, 16);
    if (!mode || int10(0x4f02, mode | 0x4000, 0, 0, 0, 0) != 0x004f)
        return;
    const u32 lfb = VBE_MODE->framebuffer;

    volatile u16 *fb = (volatile u16 *) lfb;
    for (u32 y = 0; y < H; y++)
        for (u32 x = 0; x < W; x++)
            fb[y * W + x] = ((y >= 200) && (y < 260) && (x >= 60)) ? (u16) KEY : (u16) pattern(x, y, 0x81);
    volatile u16 *src = (volatile u16 *) (lfb + SRC);
    for (u32 i = 0; i < SRC_W * SRC_H; i++)
        src[i] = (u16) pattern(i % SRC_W, i / SRC_W, 0x82);

    static const u32 passes[5][7] = {
        /* x, y, w, h, format, scale, keyed */
        { 100, 60, 300, 200, 4, 1, 0 },
        { 100, 160, 300, 200, 4, 1, 1 },
        { 40, 40, 560, 400, 4, 2, 0 },
        { 160, 100, 240, 180, 0xb, 1, 0 },
        { 500, 300, 300, 150, 4, 1, 0 },
    };
    for (u32 p = 0; p < 5; p++) {
        overlay(passes[p][0], passes[p][1], passes[p][2], passes[p][3], passes[p][4], passes[p][5], passes[p][6]);
        wait_ticks(6);
    }
    reg(SCALE_CNTL, 0);
}
