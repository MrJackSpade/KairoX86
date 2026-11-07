/*
 * KairoX86's CGA-clone test (KairoX86#283, for #243, #244 and #245): on a CGA-class card, the clones' own text and
 * graphics, each held four ticks of the BIOS clock: 80- and 40-column text of every character and attribute, the
 * cursor shown, with blinking and then intensity backgrounds; the Olivetti OGC's underline (3DEh/3DBh bit 6); the
 * Compaq's 350-line text (character height 14, CRTC R9 = 13); 640 x 400 graphics, the OGC's (3DEh bit 0) and the
 * NCR NGA's two (3D8h bit 6: 1 bit a pixel, then 2 bits from its second 32K at A8000h). A plain CGA ignores the
 * clones' bits and shows its own modes of the same registers. Any other card class returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static void text(u32 columns, u32 salt) {
    volatile u8 *vram = (volatile u8 *) 0xb8000u;
    for (u32 i = 0; i < columns * 25; i++) {
        vram[i * 2]     = (u8) (i + salt);
        vram[i * 2 + 1] = (u8) pattern(i % columns, i / columns, salt);
    }
    int10(0x0200, 0, 0, 0x0c05, 0, 0); /* the cursor at row 12, column 5 */
}

static void crtc(u8 index, u8 v) {
    outb(0x3d4, index);
    outb(0x3d5, v);
}

void test_main(void) {
    __asm__ volatile("fninit");
    if (card_class() != CARD_CGA)
        return;
    /* 80 columns: blinking backgrounds, then intensity */
    int10(0x03, 0, 0, 0, 0, 0);
    text(80, 0x70);
    wait_ticks(4);
    outb(0x3d8, 0x09);
    wait_ticks(4);
    /* The OGC's underline */
    outb(0x3de, 0x40);
    outb(0x3db, 0x40);
    wait_ticks(4);
    outb(0x3de, 0x00);
    outb(0x3db, 0x00);
    /* The Compaq's 350 lines: characters 14 lines high */
    crtc(0x09, 13);
    wait_ticks(4);
    /* 40 columns */
    int10(0x01, 0, 0, 0, 0, 0);
    text(40, 0x71);
    wait_ticks(4);

    /* 640 x 400 graphics: all 64K the clones may show */
    int10(0x06, 0, 0, 0, 0, 0);
    for (u32 i = 0; i < 0x8000; i++) {
        ((volatile u8 *) 0xb8000u)[i] = (u8) pattern(i % 80, i / 80, 0x72);
        ((volatile u8 *) 0xa8000u)[i] = (u8) pattern(i % 80, i / 80, 0x73);
    }
    outb(0x3de, 0x01); /* the OGC's */
    outb(0x3db, 0x01);
    wait_ticks(4);
    outb(0x3de, 0x00);
    outb(0x3db, 0x00);
    outb(0x3d8, 0x5a); /* the NGA's, 1 bit a pixel */
    wait_ticks(4);
    outb(0x3d9, 0x20);
    outb(0x3d8, 0x4a); /* the NGA's, 2 bits */
    wait_ticks(4);
    int10(0x03, 0, 0, 0, 0, 0);
}
