/*
 * KairoX86's JEGA test (KairoX86#283, for #262): on a JEGA or JVGA (its font status register, index BFh, reads 03h),
 * its Japanese text shown (mode 3, RMOD1 = 88h: display out, master, its own text renderer), each held four ticks of
 * the BIOS clock: Shift JIS double-byte characters between single-byte ones, every attribute, the cursor shown, read as
 * EGA attributes (RMOD2 = 00h), as JEGA attributes (80h: reverse, vertical line, underline, blink) and with the
 * extended attributes (C0h: bold, double width and height). Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static void jreg(u8 index, u8 v) {
    outb(0x3d4, index);
    outb(0x3d5, v);
}

void test_main(void) {
    __asm__ volatile("fninit");
    const int cls = card_class();
    if ((cls != CARD_EGA) && (cls != CARD_VGA))
        return;
    outb(0x3d4, 0xbf);
    if (inb(0x3d5) != 0x03)
        return;
    int10(0x03, 0, 0, 0, 0, 0);
    jreg(0xb9, 0x88);
    /* Double-byte characters (lead 82h, a trail byte from 9Fh on) between runs of single bytes */
    volatile u8 *vram = (volatile u8 *) 0xb8000u;
    for (u32 i = 0; i < 80 * 25; i++) {
        const u32 col = i % 80;
        u8        chr;
        if ((col % 10) < 6)
            chr = (col & 1) ? (u8) (0x9f + (i / 2) % 80) : 0x82;
        else
            chr = (u8) (0x30 + i % 64);
        vram[i * 2]     = chr;
        vram[i * 2 + 1] = (u8) pattern(col, i / 80, 0x80);
    }
    int10(0x0200, 0, 0, 0x0a14, 0, 0); /* the cursor at row 10, column 20 */
    static const u8 modes[3] = { 0x00, 0x80, 0xc0 };
    for (u32 m = 0; m < 3; m++) {
        jreg(0xba, modes[m]);
        wait_ticks(4);
    }
    jreg(0xba, 0x00);
}
