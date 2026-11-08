/*
 * KairoX86's Yamaha V6355 pointer test (KairoX86#283, for #247): its hardware mouse pointer (registers 00h-3Fh its AND
 * and XOR masks, 60h-63h its place, 64h its AND and XOR on, 68h its colours, through ports 3DDh and 3DEh) over the
 * BIOS's 80- and 40-column text (the text cursor under the pointer), its 320 x 200 x 4 and its 640 x 200 x 2 graphics,
 * each filled with a pattern; the pointer inside the picture, then over its left and right edges. Each held six ticks
 * of the BIOS clock. On any other card than a CGA it returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static void v6355_reg(u8 index, u8 value) {
    outb(0x3dd, index);
    outb(0x3de, value);
}

static void pointer_at(u16 x, u8 y) {
    v6355_reg(0x60, (u8) (x >> 8));
    v6355_reg(0x61, (u8) x);
    v6355_reg(0x63, y);
}

/* The pointer at three places: inside, across the left edge, across the right */
static void pointer_walk(void) {
    pointer_at(120, 60);
    wait_ticks(6);
    pointer_at(8, 100);
    wait_ticks(6);
    pointer_at(330, 140);
    wait_ticks(6);
}

void test_main(void) {
    if (card_class() != CARD_CGA)
        return;
    /* The masks: an arrow's outline in AND, a pattern in XOR */
    for (u8 r = 0; r < 16; r++) {
        v6355_reg((u8) (r * 2), (u8) (0xff >> (r >> 1)));
        v6355_reg((u8) (r * 2 + 1), (u8) (0xf0 ^ (r * 0x11)));
        v6355_reg((u8) (0x20 + r * 2), (u8) (0x3c ^ (r * 7)));
        v6355_reg((u8) (0x21 + r * 2), (u8) (0x81 | (r << 2)));
    }
    v6355_reg(0x68, 0xa5);
    v6355_reg(0x64, 0x06);

    static const u16 modes[4] = { 0x0003, 0x0001, 0x0004, 0x0006 };
    for (int m = 0; m < 4; m++) {
        int10(modes[m], 0, 0, 0, 0, 0);
        volatile u8 *screen = (volatile u8 *) 0xb8000;
        for (u32 i = 0; i < 0x4000; i++)
            screen[i] = (u8) ((i * 13u) ^ (i >> 3) ^ (u32) (m * 0x55));
        /* The text cursor under the pointer's first place */
        if (m < 2)
            int10(0x0200, 0, 0, (u16) ((((60 - 16) / 8) << 8) | ((120 - 16) / (m ? 8 : 4))), 0, 0);
        pointer_walk();
    }
    v6355_reg(0x64, 0x00);
    int10(0x0003, 0, 0, 0, 0, 0);
}
