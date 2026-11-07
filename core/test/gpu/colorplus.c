/*
 * KairoX86's Plantronics ColorPlus test (KairoX86#283, for #242): on a CGA-class card, its two planes (B8000h and
 * BC000h) filled with a pattern and the ColorPlus's own modes chosen through its control port (3DDh), each held four
 * ticks of the BIOS clock: 320 x 200 in 16 colours (from mode 4, 10h), 640 x 200 in 4 colours (from mode 6, 20h) in
 * both CGA palettes and black and white. A plain CGA ignores 3DDh and shows its own
 * modes of the same memory. Any other card class returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static void fill(u32 salt) {
    volatile u8 *vram = (volatile u8 *) 0xb8000u;
    for (u32 i = 0; i < 0x8000; i++)
        vram[i] = (u8) pattern(i % 80, i / 80, salt);
}

void test_main(void) {
    __asm__ volatile("fninit");
    if (card_class() != CARD_CGA)
        return;
    /* 320 x 200 x 16 */
    int10(0x04, 0, 0, 0, 0, 0);
    outb(0x3dd, 0x10);
    fill(0x60);
    wait_ticks(4);
    /* 640 x 200 x 4: the two palettes, intense, then black and white */
    int10(0x06, 0, 0, 0, 0, 0);
    outb(0x3dd, 0x20);
    fill(0x61);
    static const u8 colour[3] = { 0x00, 0x20, 0x31 };
    for (u32 i = 0; i < 3; i++) {
        outb(0x3d9, colour[i]);
        wait_ticks(4);
    }
    outb(0x3d8, 0x1e); /* black and white */
    wait_ticks(4);
    outb(0x3dd, 0x00);
}
