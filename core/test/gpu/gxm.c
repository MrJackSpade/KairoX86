/*
 * KairoX86's Cyrix MediaGX display test (KairoX86#283, for #315): its own display controller (GX_BASE+8300h) and the
 * CS5530's video overlay (its F4 BAR), over SoftVGA's 640 x 480 x 16 (its VESA mode), its frame buffer filled through the
 * graphics memory window (GX_BASE+800000h) with a pattern and keyed stripes. Each held six ticks of the BIOS clock:
 * the picture as 5-6-5, then as 5-5-5 (DC_OUTPUT_CFG bit 1); the hardware cursor (its AND and XOR planes a pattern:
 * colour, inverting and transparent pixels) inside the picture and at its edge; the video window (YUV 4:2:2 scaled
 * up twice, X filtered) keyed by the graphics colour, then by the video's; then the cursor and the graphics-keyed
 * window again through a gamma RAM that is not the identity. Any other machine returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

enum { DC_UNLOCK = 0, DC_GENERAL_CFG, DC_TIMING_CFG, DC_OUTPUT_CFG, DC_FB_ST_OFFSET, DC_CB_ST_OFFSET, DC_CURS_ST_OFFSET,
       DC_RSVD_1C, DC_VID_ST_OFFSET, DC_LINE_DELTA, DC_BUF_SIZE, DC_RSVD_2C, DC_H_TIMING_1, DC_H_TIMING_2, DC_H_TIMING_3,
       DC_FP_H_TIMING, DC_V_TIMING_1, DC_V_TIMING_2, DC_V_TIMING_3, DC_FP_V_TIMING, DC_CURSOR_X, DC_V_LINE_CNT,
       DC_CURSOR_Y, DC_SS_LINE_CMP, DC_CURSOR_COLOR, DC_RSVD_64, DC_BORDER_COLOR, DC_RSVD_6C, DC_PAL_ADDRESS,
       DC_PAL_DATA };
enum { VID_CONFIG = 0, VID_DISPLAY = 1, VID_X = 2, VID_Y, VID_SCALE, VID_KEY, VID_MASK, VID_GAMMA_ADDR = 7, VID_GAMMA = 8 };

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    return inl(0xcfc);
}

static volatile u32 *dc;
static volatile u32 *f4;
static volatile u8  *gmem;

static void pci_write(u32 bus, u32 dev, u32 fn, u32 reg_, u32 v) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    outl(0xcfc, v);
}

/* The CS5530's video function (1078h:0104h), its F4 BAR moved to 48000000h (the BIOS leaves it over the graphics
   memory window's first 4K): first its configuration's trap to the SMI handler off (F0 42h bit 1), so the writes
   reach it; 0 when there is none */
static u32 cs5530_f4(void) {
    for (u32 d = 0; d < 32; d++)
        if (pci_read(0, d, 4, 0) == 0x01041078u) {
            pci_write(0, d, 0, 0x40, pci_read(0, d, 0, 0x40) & ~(2u << 16));
            pci_write(0, d, 4, 0x10, 0x48000000u);
            pci_write(0, d, 4, 0x04, pci_read(0, d, 4, 0x04) | 2u); /* its memory decoded */
            return pci_read(0, d, 4, 0x10) & 0xfffff000u;
        }
    return 0;
}

static void gamma_load(int identity) {
    f4[VID_GAMMA_ADDR] = 0;
    for (u32 i = 0; i < 256; i++) {
        const u32 g = identity ? i : ((i * 3u) >> 2) + 0x20u;
        f4[VID_GAMMA] = (g << 16) | (g << 8) | g;
    }
}

void test_main(void) {
    const u32 bar = cs5530_f4();
    if (!bar)
        return;
    /* SoftVGA's 640 x 480 x 16 with its linear frame buffer, the graphics memory window at GX_BASE+800000h */
    u32 lfb = 0;
    const int count = vbe_modes();
    for (int i = 0; (i < count) && !lfb; i++) {
        const u16 mode = VBE_MODES[i];
        if ((int10(0x4f01, 0, mode, 0, 0x6200, 0) == 0x004f) && (VBE_MODE->width == 640) && (VBE_MODE->height == 480) &&
            (VBE_MODE->bpp == 16) && VBE_MODE->framebuffer && (int10(0x4f02, mode | 0x4000, 0, 0, 0, 0) == 0x004f))
            lfb = VBE_MODE->framebuffer;
    }
    if (!lfb)
        return;
    const u32 gx = lfb - 0x800000u;
    dc   = (volatile u32 *) (gx + 0x8300);
    f4   = (volatile u32 *) bar;
    gmem = (volatile u8 *) (gx + 0x800000);
    dc[DC_UNLOCK] = 0x4758;

    /* The picture: a pattern, every 16th column pair of 16 the key colour (pure blue) */
    const u32 fb    = dc[DC_FB_ST_OFFSET] & 0x3ffff0u;
    const u32 delta = (dc[DC_LINE_DELTA] & 0x3ffu) << 2;
    for (u32 y = 0; y < 480; y++) {
        volatile u16 *row = (volatile u16 *) (gmem + fb + y * delta);
        for (u32 x = 0; x < 640; x++)
            row[x] = ((x >> 4) & 1) ? 0x001fu : (u16) ((x * 37u) ^ (y * 101u) ^ (x << 7));
    }
    wait_ticks(6);
    dc[DC_OUTPUT_CFG] |= 2u; /* 5-5-5 */
    wait_ticks(6);
    dc[DC_OUTPUT_CFG] &= ~2u;

    /* The cursor: 32 lines of an AND and an XOR word per 16 pixels, past the frame buffer */
    const u32 curs = (fb + delta * 480u + 0x1000u) & ~0xfffu;
    for (u32 r = 0; r < 32; r++)
        for (u32 h = 0; h < 2; h++) {
            const u32 and_ = (0x0ff0u ^ (r * 0x1111u)) & 0xffffu;
            const u32 xor_ = (0x3c3cu + (r * 0x0101u) + h) & 0xffffu;
            *(volatile u32 *) (gmem + curs + r * 8u + h * 4u) = (and_ << 16) | xor_;
        }
    dc[DC_PAL_ADDRESS]    = 0x100;
    dc[DC_PAL_DATA]       = 0x3f000u; /* red */
    dc[DC_PAL_ADDRESS]    = 0x101;
    dc[DC_PAL_DATA]       = 0x00fc0u; /* green */
    dc[DC_CURS_ST_OFFSET] = curs;
    dc[DC_CURSOR_X]       = 100;
    dc[DC_CURSOR_Y]       = 80;
    dc[DC_GENERAL_CFG] |= 2u;
    wait_ticks(6);
    dc[DC_CURSOR_X] = 620 | (3u << 11);
    dc[DC_CURSOR_Y] = 470 | (5u << 11);
    wait_ticks(6);
    dc[DC_GENERAL_CFG] &= ~2u;

    /* The video: 64 x 64 YUV 4:2:2 (128 bytes a line) past the cursor, shown 128 x 128 */
    const u32 vbuf = curs + 0x1000u;
    for (u32 i = 0; i < 64u * 128u; i++)
        gmem[vbuf + i] = (u8) ((i * 7u) ^ (i >> 7) ^ ((i & 1) ? 0x80u : 0x10u));
    const u32 htotal   = ((((dc[DC_H_TIMING_1] >> 19) & 0xffu) + 1u) << 3);
    const u32 hsyncend = ((((dc[DC_H_TIMING_3] >> 19) & 0xffu) + 1u) << 3);
    const u32 vtotal   = ((dc[DC_V_TIMING_1] >> 16) & 0x7ffu) + 1u;
    const u32 vsyncend = ((dc[DC_V_TIMING_3] >> 16) & 0x7ffu) + 1u;
    const u32 hadj     = htotal - hsyncend - 13u;
    const u32 vadj     = vtotal - vsyncend + 1u;
    dc[DC_VID_ST_OFFSET] = vbuf;
    dc[DC_BUF_SIZE]      = (dc[DC_BUF_SIZE] & 0xffffu) | ((64u * 128u / 64u) << 16);
    f4[VID_X]            = (200u + hadj) | ((328u + hadj) << 16);
    f4[VID_Y]            = (150u + vadj) | ((278u + vadj) << 16);
    f4[VID_SCALE]        = 0x1000u | (0x1000u << 16);
    f4[VID_KEY]          = 0x0000f8u; /* the graphics' blue, as the key compares it */
    f4[VID_MASK]         = 0xffffffu;
    f4[VID_CONFIG]       = 1u | 2u | (32u << 8) | (1u << 7);
    dc[DC_GENERAL_CFG] |= 1u << 28;
    const u32 display = f4[VID_DISPLAY];
    f4[VID_DISPLAY] = display & ~(1u << 20);
    wait_ticks(6);
    f4[VID_KEY]     = 0x400000u; /* by the video: shown where its red's bit 6 differs */
    f4[VID_MASK]    = 0x400000u;
    f4[VID_DISPLAY] = display | (1u << 20);
    wait_ticks(6);

    /* Through a gamma RAM that is not the identity: the graphics-keyed window, then the cursor */
    gamma_load(0);
    f4[VID_DISPLAY] = display & ~((1u << 20) | (1u << 21));
    f4[VID_KEY]     = 0x0000f8u;
    f4[VID_MASK]    = 0xffffffu;
    wait_ticks(6);
    dc[DC_GENERAL_CFG] &= ~(1u << 28);
    dc[DC_CURSOR_X] = 300;
    dc[DC_CURSOR_Y] = 200;
    dc[DC_GENERAL_CFG] |= 2u;
    wait_ticks(6);
    dc[DC_GENERAL_CFG] &= ~2u;
    gamma_load(1);
    f4[VID_DISPLAY] = display;
    wait_ticks(6);
}
