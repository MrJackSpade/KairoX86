/*
 * KairoX86's Voodoo Banshee / Voodoo3 tiled desktop test (KairoX86#283, for #278): on a 3dfx Banshee or Voodoo3 (PCI
 * 121Ah: 0003h, 0004h, 0005h), VESA 640 x 480 x 16 (as v3d.c), then the desktop switched to tiles (vidProcCfg
 * DESKTOP_TILE, the stride 10 tiles of 128 bytes), so the picture is the card's tiled renderer's. Passes over the frame
 * buffer, written through the linear frame buffer, each held eight ticks of the BIOS clock: every pixel; a few tiles
 * changed (the renderer redraws only changed tiles); the same with the hardware cursor on (its lines drawn whole by
 * the processor, the rest by the GPU) and moved; the desktop started a tile row down. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    return inl(0xcfc);
}

/* The video registers (BAR 0) */
enum { VIDPROCCFG = 0x5c, HWCURPATADDR = 0x60, HWCURLOC = 0x64, HWCURC0 = 0x68, HWCURC1 = 0x6c,
       DESKTOP_START = 0xe4, DESKTOP_STRIDE = 0xe8 };
#define DESKTOP_TILE  (1u << 24)
#define HWCURSOR_ENA  (1u << 27)
#define TILES_ACROSS  10u          /* 640 pixels of 16 bits, 128 bytes a tile row */
#define TILE_BYTES    (128u * 32u) /* a tile: 32 rows of 128 bytes */
#define DESKTOP_BYTES (TILES_ACROSS * TILE_BYTES * 16u)
#define CURSOR        0x180000u    /* the cursor's pattern: past the desktop */

static volatile u32 *regs;
static volatile u32 *fb;

static void reg(u32 offset, u32 value) { regs[offset / 4] = value; }

static void fill(u32 from, u32 to, u32 salt) {
    for (u32 i = from / 4; i < to / 4; i++)
        fb[i] = pattern(i % 32, i / 32, salt);
}

void test_main(void) {
    u32 mmio = 0, lfb = 0;
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
    regs = (volatile u32 *) mmio;
    fb   = (volatile u32 *) lfb;

    /* Every pixel, then the desktop switched to tiles */
    fill(0, DESKTOP_BYTES, 0x71);
    reg(DESKTOP_START, 0);
    reg(DESKTOP_STRIDE, (regs[DESKTOP_STRIDE / 4] & 0xffff0000u) | TILES_ACROSS);
    const u32 cfg = regs[VIDPROCCFG / 4] | DESKTOP_TILE;
    reg(VIDPROCCFG, cfg);
    wait_ticks(8);

    /* A few tiles changed */
    for (u32 t = 0; t < 12; t++) {
        const u32 tile = (t * 37u) % (TILES_ACROSS * 15u);
        fill(tile * TILE_BYTES, tile * TILE_BYTES + TILE_BYTES, 0x72 + t);
    }
    wait_ticks(8);

    /* The hardware cursor on, its pattern two planes of 64 x 64, at two places */
    for (u32 i = 0; i < 1024 / 4; i++)
        fb[(CURSOR / 4) + i] = pattern(i, 9, 0x73);
    reg(HWCURPATADDR, CURSOR);
    reg(HWCURC0, 0x00ff8040u);
    reg(HWCURC1, 0x0020c0ffu);
    reg(HWCURLOC, (200u << 16) | 300u);
    reg(VIDPROCCFG, cfg | HWCURSOR_ENA);
    fill(TILE_BYTES * 3, TILE_BYTES * 5, 0x74);
    wait_ticks(8);
    reg(HWCURLOC, (390u << 16) | 37u);
    wait_ticks(8);

    /* The desktop started a tile row down, the cursor off */
    reg(VIDPROCCFG, cfg);
    reg(DESKTOP_START, TILES_ACROSS * TILE_BYTES);
    fill(DESKTOP_BYTES, DESKTOP_BYTES + TILES_ACROSS * TILE_BYTES, 0x75);
    wait_ticks(8);
}
