/*
 * KairoX86's ATI 3D Rage II+ scaler test (KairoX86#283, for #237): on a Rage II+ (PCI 1002h:4755h), VESA 640 x 480 x 16
 * with its linear frame buffer, the registers in the aperture's top 1K and a source area filled with a pattern, a
 * series of passes through the front-end scaler (SCALE_3D_FCN 1; vid_ati_mach64_3d.c's mach64_scaler_draw), each a
 * set of scaled rectangles over a clear, held four ticks of the BIOS clock: each source format (CI8 through the
 * palette, the 16 and 32-bit ones, RGB 332, Y8, YUV 422 with unsigned and signed chroma, AYUV), filtered and
 * replicated, enlarged and reduced; both X and Y directions; the scissors; alpha blending; ordered dithering and
 * error diffusion; the destination formats; the compares (destination, scaled pixel, source key); DP_MIX's
 * functions through a write mask; and a source read from the picture being drawn on. The engine's busy bit is never
 * read. Any other card returns at once.
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
    DST_OFF_PITCH = 0x100, DST_Y_X = 0x10c, DST_HEIGHT_WIDTH = 0x118, DST_CNTL = 0x130, SCALE_Y_OFF = 0x1c0,
    SCALE_WIDTH = 0x1dc, SCALE_HEIGHT = 0x1e0, SCALE_Y_PITCH = 0x1ec, SCALE_X_INC = 0x1f0, SCALE_Y_INC = 0x1f4,
    SCALE_VACC = 0x1f8, SCALE_3D_CNTL = 0x1fc, SC_LEFT_RIGHT = 0x2a8, SC_TOP_BOTTOM = 0x2b4, WRITE_MASK = 0x2c8,
    DP_PIX_WIDTH = 0x2d0, DP_MIX = 0x2d4, DP_SRC = 0x2d8, CLR_CMP_CLR = 0x300, CLR_CMP_MASK = 0x304,
    CLR_CMP_CNTL = 0x308, TEX_PALETTE = 0x37c, SCALE_HACC = 0x3c8, SCALE_XUV_INC = 0x3d8, SCALE_UV_HACC = 0x3e0,
};

/* SCALE_3D_CNTL */
#define SDITHER   (1u << 1)
#define DITHER    (1u << 2)
#define DINIT     (1u << 3)
#define SCALE     (1u << 6)
#define PIX_REP   (1u << 8)
#define NEAR_VIS  (1u << 9)
#define APPLE_YUV (1u << 10)
#define ABLEND    (1u << 11)
#define BSRC(f)   ((u32) (f) << 16)
#define BDST(f)   ((u32) (f) << 19)

/* A pass's other settings */
#define P_XLEFT    0x01u
#define P_YUP      0x02u
#define P_SCISSOR  0x04u
#define P_KEY      0x08u
#define P_DSTCMP   0x10u
#define P_PIXCMP   0x20u
#define P_WMASK    0x40u
#define P_FEEDBACK 0x80u

typedef struct {
    u32 cntl;
    u8  src; /* DP_SCALE_PIX_WIDTH */
    u8  dst; /* DP_DST_PIX_WIDTH */
    u8  mix; /* DP_MIX's foreground function */
    u8  flags;
} pass_t;

static const pass_t passes[] = {
    { SCALE, 4, 4, 7, 0 },
    { SCALE | PIX_REP, 4, 4, 7, 0 },
    { SCALE, 3, 4, 7, P_XLEFT },
    { SCALE | ABLEND | BSRC(4) | BDST(5), 15, 4, 7, 0 },
    { SCALE, 6, 6, 7, 0 },
    { SCALE | NEAR_VIS, 2, 4, 7, P_KEY },
    { SCALE | PIX_REP, 2, 4, 7, P_KEY },
    { SCALE, 11, 4, 7, 0 },
    { SCALE | PIX_REP | APPLE_YUV, 11, 4, 7, P_YUP },
    { SCALE | APPLE_YUV, 11, 4, 7, P_KEY },
    { SCALE, 14, 4, 7, 0 },
    { SCALE | DITHER, 7, 7, 7, 0 },
    { SCALE | DITHER | DINIT, 4, 4, 7, P_XLEFT | P_YUP },
    { SCALE | DITHER | SDITHER, 8, 3, 7, 0 },
    { SCALE, 4, 4, 0x05, P_WMASK },
    { SCALE, 4, 4, 0x17, 0 },
    { SCALE, 4, 4, 0x0e, 0 },
    { SCALE, 4, 4, 7, P_DSTCMP },
    { SCALE, 4, 4, 7, P_PIXCMP },
    { SCALE, 4, 4, 7, P_SCISSOR | P_YUP },
    { SCALE, 4, 4, 7, P_FEEDBACK },
    { SCALE | ABLEND | BSRC(2) | BDST(1), 4, 2, 7, 0 },
    { SCALE, 6, 15, 7, 0 },
    { SCALE, 4, 8, 7, 0 },
};

static u32 bytes_of(u32 format) {
    switch (format) {
        case 2: case 7: case 8: return 1;
        case 6: return 4;
        default: return 2;
    }
}

void test_main(void) {
    __asm__ volatile("fninit");
    int found = 0;
    for (u32 bus = 0; bus < 2 && !found; bus++)
        for (u32 dev = 0; dev < 32 && !found; dev++)
            if (pci_read(bus, dev, 0, 0) == 0x47551002u)
                found = 1;
    if (!found)
        return;
    const u16 mode = vbe_find(640, 480, 16);
    if (!mode || (int10(0x4f02, mode | 0x4000, 0, 0, 0, 0) != 0x004f)) {
        *(volatile u16 *) 0xb8000 = 0x4f56;
        wait_ticks(40);
        return;
    }
    const u32 lfb = VBE_MODE->framebuffer;
    mmio          = (volatile u32 *) ((lfb & ~0x7fffffu) + 0x7ffc00u);

    /* The source area, 2 MB to 3 MB: the pattern */
    volatile u32 *src = (volatile u32 *) (lfb + 0x200000);
    for (u32 i = 0; i < 0x40000; i++)
        src[i] = pattern(i & 511, i >> 9, 0x5c);
    for (u32 i = 0; i < 256; i++)
        reg(TEX_PALETTE, (i << 24) | (pattern(i, 3, 0x78) & 0xffffff));
    reg(DP_SRC, 5u << 8);

    for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
        const pass_t *ps    = &passes[p];
        const u32     width = 1280 / bytes_of(ps->dst);
        volatile u32 *fb    = (volatile u32 *) lfb;
        for (u32 i = 0; i < 640 * 480 / 2; i++)
            fb[i] = pattern(i % 320, i / 320, 0x80 + p) & 0x7bef7befu;

        reg(DST_OFF_PITCH, (width / 8) << 22);
        reg(SC_LEFT_RIGHT, (ps->flags & P_SCISSOR) ? (((width * 3 / 4) << 16) | 40u) : ((width - 1) << 16));
        reg(SC_TOP_BOTTOM, (ps->flags & P_SCISSOR) ? ((400u << 16) | 60u) : (479u << 16));
        reg(DP_PIX_WIDTH, ((u32) ps->src << 28) | ((u32) ps->dst << 8) | ps->dst);
        reg(DP_MIX, ((u32) ps->mix << 16) | 3u);
        reg(WRITE_MASK, (ps->flags & P_WMASK) ? 0x0000c3c3u : 0xffffffffu);
        reg(CLR_CMP_CLR, (ps->flags & P_KEY) ? 0x00000040u : 0x00000400u);
        reg(CLR_CMP_MASK, (ps->flags & P_KEY) ? 0x000000c0u : 0x00000700u);
        reg(CLR_CMP_CNTL, (ps->flags & P_KEY) ? ((2u << 24) | 5u) : (ps->flags & P_DSTCMP) ? 4u : (ps->flags & P_PIXCMP) ? ((1u << 24) | 5u) : 0u);
        reg(DST_CNTL, ((ps->flags & P_XLEFT) ? 0u : 1u) | ((ps->flags & P_YUP) ? 0u : 2u));
        reg(SCALE_3D_CNTL, ps->cntl);

        for (u32 k = 0; k < 6; k++) {
            const u32 g     = pattern(k, p, 0x3a3a);
            const u32 sw    = 16 + (g % 200), sh = 16 + ((g >> 8) % 150);
            const u32 dw    = 24 + ((g >> 4) % 260), dh = 24 + ((g >> 12) % 200);
            const u32 sbpp  = (ps->src == 11) ? 2 : bytes_of(ps->src);
            const u32 pitch = 512 + ((g >> 20) & 3) * 8;
            const u32 x     = (ps->flags & P_XLEFT) ? (dw + (g % 30)) : (4 + ((g >> 3) % 40));
            const u32 y     = (ps->flags & P_YUP) ? (dh + ((g >> 9) % 40)) : (4 + ((g >> 11) % 40));
            reg(SCALE_Y_OFF, (ps->flags & P_FEEDBACK) ? (0x10000u + k * 0x800u) : (0x200000u + (k * 0x1000u) * sbpp));
            reg(SCALE_WIDTH, sw);
            reg(SCALE_HEIGHT, sh);
            reg(SCALE_Y_PITCH, pitch);
            /* The steps: 16-bit fractions, source pixels a destination pixel */
            reg(SCALE_X_INC, ((sw << 16) / dw) & 0x001ffff0u);
            reg(SCALE_Y_INC, ((sh << 16) / dh) & 0x001ffff0u);
            reg(SCALE_XUV_INC, ((sw << 15) / dw) & 0x001ffff0u);
            reg(SCALE_HACC, (g >> 6) & 0x0000fff0u);
            reg(SCALE_UV_HACC, (g >> 10) & 0x0000fff0u);
            reg(SCALE_VACC, (g >> 14) & 0x0000fff0u);
            reg(DST_Y_X, (x << 16) | y);
            reg(DST_HEIGHT_WIDTH, (dw << 16) | dh);
        }
        wait_ticks(4);
    }
}
