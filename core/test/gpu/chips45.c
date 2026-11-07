/*
 * KairoX86's Chips & Technologies 82C45x test (KairoX86#283, for #248): on an 82C450, 82C451 or 82C452 (A5h from
 * setup port 104h), its extension registers enabled (103h bit 7) and its CGA emulation's 640 x 200 mode shown (from
 * mode 6: XR14 = 1, 3D8h = 1Eh, 3D9h = 0Fh), the chip's own 1bpp renderer, every row a different pattern in the two
 * interleaved banks, the alternate horizontal registers XR18-XR1E set up for it, held four ticks of the BIOS clock.
 * Hercules graphics, the renderer's other user, is not driven. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static void xr(u8 index, u8 v) {
    outb(0x3d6, index);
    outb(0x3d7, v);
}

void test_main(void) {
    __asm__ volatile("fninit");
    /* Setup mode: the chip answers A5h at 104h */
    outb(0x46e8, 0x18);
    const u8 id = inb(0x104);
    if (id != 0xa5) {
        outb(0x46e8, 0x08);
        return;
    }
    outb(0x103, 0x80); /* the extension registers at 3D6h/3D7h */
    outb(0x46e8, 0x08);

    /* CGA 640 x 200: two banks of 100 rows, 80 bytes a row */
    int10(0x06, 0, 0, 0, 0, 0);
    outb(0x3d6, 0x14);
    const u8 xr14 = inb(0x3d7);
    /* The alternate horizontal registers the emulated mode times its lines by, as an emulation utility sets them:
       16 dots a clock, 40 shown of 50, 80 bytes a row (XR15's write protection off first) */
    outb(0x3d6, 0x15);
    const u8 xr15 = inb(0x3d7);
    xr(0x15, 0);
    xr(0x18, 39);
    xr(0x1b, 45);
    xr(0x1c, 40);
    xr(0x1d, 17);
    xr(0x1e, 20);
    xr(0x14, (u8) ((xr14 & ~3u) | 1));
    outb(0x3d8, 0x1e);
    outb(0x3d9, 0x0f); /* the foreground: white */
    for (u32 y = 0; y < 200; y++) {
        volatile u8 *row = (volatile u8 *) (0xb8000u + (y & 1) * 0x2000u + (y >> 1) * 80u);
        for (u32 x = 0; x < 80; x++)
            row[x] = (u8) pattern(x, y, 0x45);
    }
    wait_ticks(4);

    xr(0x14, xr14);
    xr(0x15, xr15);
}
