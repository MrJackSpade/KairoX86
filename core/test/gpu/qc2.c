/*
 * KairoX86's Quadcolor II test (KairoX86#283, for #246): the daughter board's second plane (64K at D0000h, its pixels
 * ORed into the card's, turned on through port 3DEh) over the BIOS's 80- and 40-column text and its 320 x 200 x 4 and
 * 640 x 200 x 2 graphics, both planes filled with patterns, each held six ticks of the BIOS clock; then with the
 * plane off again. On any other card than a CGA it returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

void test_main(void) {
    if (card_class() != CARD_CGA)
        return;
    volatile u8 *plane2 = (volatile u8 *) 0xd0000;
    for (u32 i = 0; i < 0x10000; i++)
        plane2[i] = (u8) ((i * 29u) ^ (i >> 5) ^ 0x93u);

    static const u16 modes[4] = { 0x0003, 0x0001, 0x0004, 0x0006 };
    for (int m = 0; m < 4; m++) {
        int10(modes[m], 0, 0, 0, 0, 0);
        volatile u8 *screen = (volatile u8 *) 0xb8000;
        for (u32 i = 0; i < 0x4000; i++)
            screen[i] = (u8) ((i * 11u) ^ (i >> 4) ^ (u32) (m * 0x33));
        outb(0x3de, 0x01); /* the second plane on (its polarity inverted: bit 4 clear) */
        wait_ticks(6);
        outb(0x3de, 0x00);
        wait_ticks(6);
    }
    int10(0x0003, 0, 0, 0, 0, 0);
}
