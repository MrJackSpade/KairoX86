/*
 * KairoX86's Hercules graphics test (KairoX86#283): on an MDA-class card, the Hercules 720 x 348 graphics
 * mode (configuration switch 3BFh, the CRTC programmed for it, mode control 3B8h), both pages filled
 * with the pattern and each shown for two ticks of the BIOS clock, then text mode 7 again. The BIOS
 * cannot set the mode. A plain MDA has no graphics mode: it shows whatever its text mode makes of it.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

/* The CRTC for 720 x 348: 45 characters of 16 dots across, 87 rows of 4 lines */
static const u8 crtc[12] = { 0x35, 0x2d, 0x2e, 0x07, 0x5b, 0x02, 0x57, 0x57, 0x02, 0x03, 0x00, 0x00 };

void test_main(void) {
    if (card_class() != CARD_MDA)
        return;
    outb(0x3bf, 0x03); /* graphics allowed, page 1 mapped */
    outb(0x3b8, 0x02); /* graphics, display off while the CRTC changes */
    for (u32 i = 0; i < 12; i++) {
        outb(0x3b4, (u8) i);
        outb(0x3b5, crtc[i]);
    }
    /* Both 32 KB pages: four banks of 90-byte lines (line y at bank y % 4, row y / 4) */
    u8 *vram = (u8 *) 0xb0000;
    for (u32 i = 0; i < 0x10000; i += 4) {
        const u32 v = pattern(i, 2, 0x48);
        for (u32 b = 0; b < 4; b++)
            vram[i + b] = (u8) (v >> (8 * b));
    }
    outb(0x3b8, 0x0a); /* graphics, display on, page 0 */
    wait_ticks(2);
    outb(0x3b8, 0x8a); /* page 1 */
    wait_ticks(2);
    outb(0x3b8, 0x00);
    outb(0x3bf, 0x00);
    int10(0x0007, 0, 0, 0, 0, 0);
}
