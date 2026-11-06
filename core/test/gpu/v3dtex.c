/*
 * KairoX86's Voodoo Banshee / Voodoo3 3D pipeline test (KairoX86#283, for #278): on a 3dfx Banshee or
 * Voodoo3, VESA 640 x 480 x 16 set, two textures' memory filled with a pattern through the linear frame
 * buffer, and a fixed series of passes drawn through the 3D registers, each a fan of triangles of both
 * windings over a fast fill, held four ticks of the BIOS clock: point sampled, bilinear, clamped and
 * mirrored textures; perspective corrected, mipmapped, trilinear ones; both TMUs combined; alpha tested
 * and chroma keyed ones; table, Z, alpha, W and constant fog; patterned and rotating stipple; W buffering,
 * depth bias and source; the Y origin swapped; the colour combine's selects and the blend's factors,
 * with destination alpha; 2x2 and subtractive dithering; a clip rectangle. As in v3d.c, the engine's
 * busy bit is never read. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "voodoo_passes.h"

/* The Banshee's I/O registers (miscInit0) */
static volatile u32 *io;

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
    dual = 0;

    /* The textures' memory, 2 MB to 4 MB: the pattern */
    volatile u32 *tex = (volatile u32 *) (lfb + 0x200000);
    for (u32 i = 0; i < 0x80000; i++)
        tex[i] = pattern(i & 1023, i >> 10, 0x77);

    /* The Y origin swap (miscInit0 bits 18 to 29): row 479 at the top */
    io[0x10 / 4] = (io[0x10 / 4] & ~(0xfffu << 18)) | (479u << 18);

    reg(COL_BUFFER_ADDR, 0);
    reg(COL_BUFFER_STRIDE, 1280);
    reg(AUX_BUFFER_ADDR, 0x100000);
    reg(AUX_BUFFER_STRIDE, 1280);
    reg(TEX_BASE_ADDR | CHIP_TMU0, 0x200000);
    reg(TEX_BASE_ADDR | CHIP_TMU1, 0x300000);
    run_passes();
}
