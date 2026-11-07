/*
 * KairoX86's Voodoo2 blitter test (KairoX86#283, for #277): on the add-on 3dfx Voodoo2 (PCI 121Ah:0002, beside the
 * machine's VGA), its output set up as v12tex.c does (640 x 480, its picture instead of the VGA's), and passes of its
 * blitter into the back buffer (linear rows of 1280 bytes), each shown by a buffer swap and held eight ticks of the
 * BIOS clock: a picture from the host (16 bits) with rectangle fills over it, clipped and not; screen-to-screen copies
 * through all 16 raster operations, overlapping in every direction, and through the source and destination chroma
 * keys choosing among four operations; host pictures of 1 bit (opaque colours) and 24 bits (plain and dithered 2 x 2
 * and 4 x 4) through operations. Any other machine returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    return inl(0xcfc);
}

static void pci_write(u32 bus, u32 dev, u32 fn, u32 reg_, u32 value) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    outl(0xcfc, value);
}

enum {
    SWAP = 0x128, BACK_PORCH = 0x208, VIDEO_DIMENSIONS = 0x20c, FBI_INIT0 = 0x210, FBI_INIT1 = 0x214, FBI_INIT2 = 0x218,
    H_SYNC = 0x220, V_SYNC = 0x224, CLUT_DATA = 0x228,
    SRC_BASE = 0x2c0, DST_BASE = 0x2c4, STRIDES = 0x2c8, SRC_CHROMA = 0x2cc, DST_CHROMA = 0x2d0, CLIP_X = 0x2d4,
    CLIP_Y = 0x2d8, SRC_XY = 0x2e0, DST_XY = 0x2e4, SIZE = 0x2e8, ROP = 0x2ec, COLOR = 0x2f0, COMMAND = 0x2f8,
    DATA = 0x2fc
};
/* bltCommand */
#define SCREEN_TO_SCREEN 0u
#define CPU_TO_SCREEN    1u
#define RECT_FILL        2u
#define SRC_1BPP         (0u << 3)
#define SRC_16BPP        (2u << 3)
#define SRC_24BPP        (3u << 3)
#define SRC_DITHER2      (4u << 3)
#define SRC_DITHER4      (5u << 3)
#define SRC_CHROMA_ON    (1u << 10)
#define DST_CHROMA_ON    (1u << 12)
#define CLIP_ON          (1u << 16)
#define LAUNCH           (1u << 31)

#define W      640
#define H      480
#define BUFFER 0x96000u /* 150 pages of 4 KB a buffer */

static volatile u32 *regs;
static u32           back = BUFFER; /* buffer 1 drawn first */

static void reg(u32 offset, u32 value) { regs[offset / 4] = value; }

static void swap(void) {
    reg(SWAP, 0);
    back = back ? 0 : BUFFER;
    wait_ticks(8);
}

static u32 range(u32 rlo, u32 glo, u32 blo, u32 rhi, u32 ghi, u32 bhi) {
    return (rlo << 11) | (glo << 5) | blo | (((rhi << 11) | (ghi << 5) | bhi) << 16);
}

/* A host picture of w x h at (x, y): the data words of a source format, pixels per word given */
static void host(u32 format, u32 rop, u32 x, u32 y, u32 w, u32 h, u32 per_word, u32 salt) {
    reg(DST_BASE, back);
    reg(ROP, rop * 0x1111u);
    reg(DST_XY, (y << 16) | x);
    reg(SIZE, ((h - 1) << 16) | (w - 1));
    reg(COMMAND, CPU_TO_SCREEN | format | LAUNCH);
    const u32 words = (w + per_word - 1) / per_word;
    for (u32 r = 0; r < h; r++)
        for (u32 i = 0; i < words; i++)
            reg(DATA, pattern(i, r, salt));
}

static void fill(u32 colour, u32 x, u32 y, u32 w, u32 h, u32 extra) {
    reg(DST_BASE, back);
    reg(COLOR, colour);
    reg(DST_XY, (y << 16) | x);
    reg(SIZE, (h << 16) | w);
    reg(COMMAND, RECT_FILL | extra | LAUNCH);
}

/* A screen-to-screen copy of w x h from (sx, sy) to (dx, dy), walking from the bottom right when back is set */
static void copy(u32 extra, u32 rops, u32 sx, u32 sy, u32 dx, u32 dy, u32 w, u32 h, int backwards) {
    reg(SRC_BASE, back);
    reg(DST_BASE, back);
    reg(ROP, rops);
    reg(SRC_XY, ((backwards ? sy + h - 1 : sy) << 16) | (backwards ? sx + w - 1 : sx));
    reg(DST_XY, ((backwards ? dy + h - 1 : dy) << 16) | (backwards ? dx + w - 1 : dx));
    reg(SIZE, backwards ? ((((u32) -(int) (h - 1)) & 0xfffu) << 16) | (((u32) -(int) (w - 1)) & 0xfffu)
                        : ((h - 1) << 16) | (w - 1));
    reg(COMMAND, SCREEN_TO_SCREEN | extra | LAUNCH);
}

void test_main(void) {
    u32 base = 0, bus_ = 0, dev_ = 0;
    for (u32 bus = 0; bus < 2 && !base; bus++)
        for (u32 dev = 0; dev < 32 && !base; dev++) {
            const u32 id = pci_read(bus, dev, 0, 0);
            if (id == 0x0002121au) {
                base = pci_read(bus, dev, 0, 0x10) & ~0xfu;
                bus_ = bus;
                dev_ = dev;
            }
        }
    if (!base)
        return;
    regs = (volatile u32 *) base;

    /* The output as v12tex.c sets it up */
    pci_write(bus_, dev_, 0, 0x40, 1);
    reg(FBI_INIT1, 10u << 4);
    reg(FBI_INIT2, 0x80000040u | (150u << 11));
    reg(VIDEO_DIMENSIONS, (480u << 16) | (640u - 1));
    reg(H_SYNC, (704u << 16) | 96u);
    reg(V_SYNC, (523u << 16) | 2u);
    reg(BACK_PORCH, (33u << 16) | 48u);
    for (u32 i = 0; i <= 32; i++) {
        const u32 v = (i * 8 > 255) ? 255 : i * 8;
        reg(CLUT_DATA, (i << 24) | (v << 16) | (v << 8) | v);
    }
    reg(FBI_INIT0, 3u);
    reg(FBI_INIT0, 1u);
    reg(STRIDES, ((W * 2u) << 16) | (W * 2u));
    reg(CLIP_X, (40u << 16) | 600u);
    reg(CLIP_Y, (30u << 16) | 450u);

    /* A host picture, then fills over it, clipped and not */
    host(SRC_16BPP, 0xc, 0, 0, W, H, 2, 0x81);
    for (u32 k = 0; k < 8; k++)
        fill(pattern(k, 1, 0x82) & 0xffffu, 10 + k * 70, 10 + (k & 3) * 110, 120, 90, (k & 1) ? CLIP_ON : 0);
    swap();

    /* Copies through all 16 operations, overlapping both ways, then through the chroma keys */
    host(SRC_16BPP, 0xc, 0, 0, W, H, 2, 0x83);
    for (u32 r = 0; r < 16; r++)
        copy(0, r * 0x1111u, 10 + (r % 8) * 75, 10 + (r / 8) * 120, 14 + (r % 8) * 75, 16 + (r / 8) * 120, 60, 100, (r & 1));
    reg(SRC_CHROMA, range(4, 8, 4, 24, 48, 24));
    reg(DST_CHROMA, range(0, 0, 8, 31, 40, 31));
    copy(SRC_CHROMA_ON, 0x6ac0u | 0xcu, 0, 250, 30, 260, 200, 100, 0);
    copy(DST_CHROMA_ON, 0x9e5cu, 220, 250, 250, 270, 200, 100, 1);
    copy(SRC_CHROMA_ON | DST_CHROMA_ON | CLIP_ON, 0x36c9u, 420, 240, 400, 280, 220, 190, 0);
    swap();

    /* Host pictures of 1 bit and 24 bits, plain and dithered */
    host(SRC_16BPP, 0xc, 0, 0, W, H, 2, 0x84);
    reg(COLOR, (0x07e0u << 16) | 0xf81fu);
    host(SRC_1BPP, 0x6, 20, 20, 200, 120, 32, 0x85);
    host(SRC_24BPP, 0xc, 240, 20, 120, 100, 1, 0x86);
    host(SRC_DITHER2, 0xe, 380, 20, 120, 100, 1, 0x87);
    host(SRC_DITHER4, 0x8, 20, 200, 160, 120, 1, 0x88);
    swap();
}
