/*
 * KairoX86's Voodoo Graphics / Voodoo2 3D pipeline test (KairoX86#283, for #277): on the add-on 3dfx card
 * (PCI 121Ah:0001 or 0002, beside the machine's VGA), its output set up as Glide's does it (640 x 480:
 * the frame buffer's tiles, two colour buffers and the depth buffer after them, the video timing, the
 * card's picture instead of the VGA's), its texture memory (each TMU's) filled with a pattern through
 * the texture download space, and the passes of voodoo_passes.h drawn into the front buffer. Any other
 * machine returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "voodoo_passes.h"

static void pci_write(u32 bus, u32 dev, u32 fn, u32 reg_, u32 value) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    outl(0xcfc, value);
}

enum {
    TEXTURE_MODE_ALL = 0x300, BACK_PORCH = 0x208, VIDEO_DIMENSIONS = 0x20c, FBI_INIT0 = 0x210, FBI_INIT1 = 0x214,
    FBI_INIT2 = 0x218, H_SYNC = 0x220, V_SYNC = 0x224, CLUT_DATA = 0x228,
};

void test_main(void) {
    __asm__ volatile("fninit");
    u32 base = 0;
    u32 bus_ = 0, dev_ = 0, model = 0;
    for (u32 bus = 0; bus < 2 && !base; bus++)
        for (u32 dev = 0; dev < 32 && !base; dev++) {
            const u32 id = pci_read(bus, dev, 0, 0);
            if ((id & 0xffff) == 0x121a && ((id >> 16) == 0x0001 || (id >> 16) == 0x0002)) {
                base  = pci_read(bus, dev, 0, 0x10) & ~0xfu;
                bus_  = bus;
                dev_  = dev;
                model = id >> 16;
            }
        }
    if (!base)
        return;
    regs = (volatile u32 *) base;
    dual = 0;

    /* initEnable: the init registers writable */
    pci_write(bus_, dev_, 0, 0x40, 1);
    /* 640 pixels a row: ten 64-pixel tiles (fbiInit1 bits 4 to 7, in pairs of 32); video reset off */
    reg(FBI_INIT1, 10u << 4);
    /* Each buffer 150 pages of 4 KB (614,400 bytes): front, back, then depth */
    reg(FBI_INIT2, 0x80000040u | (150u << 11));
    /* 640 x 480, an 800 x 525 frame */
    reg(VIDEO_DIMENSIONS, (480u << 16) | (640u - 1));
    reg(H_SYNC, (704u << 16) | 96u);
    reg(V_SYNC, (523u << 16) | 2u);
    reg(BACK_PORCH, (33u << 16) | 48u);
    /* The gamma table, its 33 entries a straight ramp (as Glide sets it: zeroed, every colour is black) */
    for (u32 i = 0; i <= 32; i++) {
        const u32 v = (i * 8 > 255) ? 255 : i * 8;
        reg(CLUT_DATA, (i << 24) | (v << 16) | (v << 8) | v);
    }
    /* The card's picture instead of the VGA's, after a graphics reset (bit 1: buffer 0 shown, 1 drawn) */
    reg(FBI_INIT0, 3u);
    reg(FBI_INIT0, 1u);

    /* Each TMU's texture memory, levels 0 to 8 of a 256 x 256 16-bit texture: the pattern */
    for (u32 tmu = 0; tmu < ((model == 2) ? 2u : 1u); tmu++) {
        reg(TEXTURE_MODE | (tmu ? CHIP_TMU1 : CHIP_TMU0), FMT_565);
        reg(TLOD | (tmu ? CHIP_TMU1 : CHIP_TMU0), LOD(0, 8));
        reg(TEX_BASE_ADDR | (tmu ? CHIP_TMU1 : CHIP_TMU0), 0);
        volatile u32 *tex = (volatile u32 *) (base + 0x800000 + (tmu ? 0x200000 : 0));
        for (u32 i = 0; i < (9u << 17) / 4; i++)
            tex[i] = pattern(i & 1023, i >> 10, 0x77 + tmu);
    }
    run_passes();
}
