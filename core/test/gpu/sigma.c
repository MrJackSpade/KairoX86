/*
 * KairoX86's Sigma Color 400 test (KairoX86#283, for #273): on a Sigma Color 400 (its ROM's "COLOR 400" at C000:000F),
 * each mode its BIOS sets (INT 10h: 1 and 3, text of 40 and 80 columns; 4, 320 x 200; 6, 640 x 200; 40h, 41h and 42h,
 * its own 80-column text, 80 x 50 text and 640 x 400), its memory filled with a pattern through the B800h window, plane
 * by plane (2DEh) in the graphics modes, text with blinking and plain attributes and the BIOS's cursor; then the
 * palette (2DEh with 2D9h bit 0) changed and the blink turned off (2D8h bit 2). Each picture held eight ticks of the
 * BIOS clock. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

#define WINDOW ((volatile u8 *) 0xb8000u)

static int sigma_present(void) {
    static const char sig[] = "COLOR 400";
    for (u32 i = 0; i < sizeof(sig) - 1; i++)
        if (((volatile u8 *) 0xc000fu)[i] != (u8) sig[i])
            return 0;
    return 1;
}

static void fill_planes(u32 salt) {
    for (u32 p = 0; p < 4; p++) {
        outb(0x2de, (u8) p);
        for (u32 i = 0; i < 0x8000; i++)
            WINDOW[i] = (u8) pattern(i & 127, i >> 7, salt + p);
    }
}

static void fill_text(u32 salt) {
    for (u32 i = 0; i < 0x4000; i++) {
        const u32 v = pattern(i & 63, i >> 6, salt);
        WINDOW[i * 2]     = (u8) (v & 0xff);
        WINDOW[i * 2 + 1] = (u8) (v >> 8);
    }
}

void test_main(void) {
    if (!sigma_present())
        return;
    static const u8 text_modes[3] = { 0x01, 0x03, 0x40 };
    for (u32 m = 0; m < 3; m++) {
        int10(text_modes[m], 0, 0, 0, 0, 0);
        int10(0x0200, 0, 0, 0x0a14, 0, 0); /* the cursor at row 10, column 20 */
        outb(0x2de, 0);
        fill_text(0x90 + m);
        wait_ticks(8);
    }
    int10(0x41, 0, 0, 0, 0, 0);
    outb(0x2de, 0);
    fill_text(0x93);
    wait_ticks(8);
    static const u8 gfx_modes[3] = { 0x04, 0x06, 0x42 };
    for (u32 m = 0; m < 3; m++) {
        int10(gfx_modes[m], 0, 0, 0, 0, 0);
        fill_planes(0xa0 + m * 4);
        wait_ticks(8);
        /* The palette: each ink a different colour */
        const u8 ctl = inb(0x2da) & 0xe0;
        outb(0x2d9, (u8) (ctl | 0x01));
        for (u32 i = 0; i < 16; i++)
            outb(0x2de, (u8) ((i << 4) | ((i * 7 + m) & 15)));
        outb(0x2d9, ctl);
        wait_ticks(8);
    }
    /* 80-column text without blink */
    int10(0x03, 0, 0, 0, 0, 0);
    fill_text(0x95);
    const u8 mode = 0x08 | 0x01 | 0x04 | 0x20 | 0x10 | 0x80; /* as the BIOS's 80-column text (B9h), blink off */
    outb(0x2d8, mode);
    wait_ticks(8);
}
