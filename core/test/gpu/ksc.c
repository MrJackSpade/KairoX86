/*
 * KairoX86's KSC5601 text test (KairoX86#283, for #236): on an ATI 28800 (its BIOS's signature at C000:0031),
 * text mode 3 with the card's Korean mode on (extended register BFh bit 5: the ATI 28800K draws double-byte
 * characters from its Hangul font), the screen filled from the pattern with ASCII, Hangul pairs (lead bytes
 * B0h to C8h, trail bytes A1h to FEh), user-defined pairs (lead C9h and FEh) and line drawing characters,
 * their attributes from the pattern (blinking ones among them), the cursor shown; held in 9-dot and 8-dot
 * cells, the line graphics extension on and off. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static int is_ati(void) {
    const char *signature = "761295520";
    const volatile char *bios = (const volatile char *) 0xc0031;
    for (int i = 0; signature[i]; i++)
        if (bios[i] != signature[i])
            return 0;
    return 1;
}

static void fill(u32 salt) {
    volatile u8 *text = (volatile u8 *) 0xb8000;
    for (u32 cell = 0; cell < 80 * 25; cell++) {
        const u32 h = pattern(cell % 80, cell / 80, salt);
        u8        c;
        switch (h & 3) {
            case 0: c = (u8) (0x20 + ((h >> 4) % 0x5f)); break;
            case 1: c = (u8) (0xb0 + ((h >> 4) % 0x19)); break;
            case 2: c = ((h >> 4) & 1) ? 0xc9 : 0xfe; break;
            default: c = (u8) (0xc0 + ((h >> 4) % 0x20)); break;
        }
        /* A lead byte's cell: the next one its trail */
        if ((c & 0x80) && (cell + 1 < 80 * 25) && ((h >> 9) & 1)) {
            text[cell * 2]     = c;
            text[cell * 2 + 1] = (u8) (h >> 16);
            cell++;
            c = (u8) (0xa1 + ((h >> 12) % 0x5e));
        }
        text[cell * 2]     = c;
        text[cell * 2 + 1] = (u8) (h >> 24);
    }
}

void test_main(void) {
    if (!is_ati())
        return;
    int10(0x0003, 0, 0, 0, 0, 0);
    /* Korean mode: extended register BFh bit 5 */
    outb(0x1ce, 0xbf);
    const u8 bf = inb(0x1cf);
    outb(0x1ce, 0xbf);
    outb(0x1cf, bf | 0x20);
    /* The cursor at row 5, column 12, shown */
    int10(0x0200, 0, 0, (5 << 8) | 12, 0, 0);
    int10(0x0100, 0, 0x0607, 0, 0, 0);

    for (int pass = 0; pass < 4; pass++) {
        fill(0x300 + (u32) pass);
        /* 9-dot cells in passes 0 and 2, 8-dot in 1 and 3 (sequencer register 1 bit 0) */
        outb(0x3c4, 1);
        const u8 seq1 = inb(0x3c5);
        outb(0x3c5, (pass & 1) ? (seq1 | 1) : (seq1 & ~1));
        /* The line graphics extension (attribute mode bit 2) off in passes 2 and 3 */
        (void) inb(0x3da);
        outb(0x3c0, 0x30);
        const u8 mode = inb(0x3c1);
        outb(0x3c0, (pass & 2) ? (mode & ~4) : (mode | 4));
        outb(0x3c0, 0x20);
        wait_ticks(4);
    }
}
