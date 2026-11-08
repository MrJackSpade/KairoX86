/*
 * KairoX86's Genius VHR layering test (KairoX86#283, for #255): its MDA text drawn over its other layers, which the
 * card composes per pixel: over the CGA 640 x 200 graphics (control register 3B0h 00h), over its native high-resolution
 * graphics (3B0h 01h: A0000h and B8000h), and over the CGA's own text (3B0h 10h). Every layer filled with a pattern,
 * the MDA text's attributes cycling through underline, intensity, reverse and blink, its cursor on; each held six
 * ticks of the BIOS clock. On a card without an MDA-class text page it returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static void mda_crtc(u8 index, u8 value) {
    outb(0x3b4, index);
    outb(0x3b5, value);
}

static void fill(volatile u8 *at, u32 bytes, u32 salt) {
    for (u32 i = 0; i < bytes; i++)
        at[i] = (u8) ((i * 7u) ^ (i >> 6) ^ salt);
}

/* The MDA text: every character, its attribute cycling */
static void mda_text(void) {
    static const u8 attrs[6] = { 0x07, 0x01, 0x0f, 0x70, 0x87, 0x09 };
    volatile u8    *text     = (volatile u8 *) 0xb0000;
    for (u32 i = 0; i < 2000; i++) {
        text[i * 2]     = (u8) i;
        text[i * 2 + 1] = attrs[i % 6];
    }
}

void test_main(void) {
    if (card_class() != CARD_MDA)
        return;
    outb(0x3b0, 0x00); /* CGA graphics, the B000 segment */
    mda_text();
    mda_crtc(10, 0x0b);
    mda_crtc(11, 0x0c);
    mda_crtc(14, 0x00);
    mda_crtc(15, 0x52); /* the cursor on row 1 */
    outb(0x3b8, 0x28); /* the MDA text on, blinking */

    /* Over the CGA's 640 x 200 graphics */
    fill((volatile u8 *) 0xb8000, 0x4000, 0x5a);
    outb(0x3d8, 0x1a);
    wait_ticks(6);

    /* Over the native high-resolution graphics (A0000h, then B8000h) */
    outb(0x3b0, 0x01);
    fill((volatile u8 *) 0xa0000, 0x10000, 0x33);
    fill((volatile u8 *) 0xb8000, 0x10000, 0xc6);
    mda_text();
    wait_ticks(6);

    /* Over the CGA's 80-column text */
    outb(0x3b0, 0x10);
    fill((volatile u8 *) 0xb8000, 0x4000, 0x21);
    outb(0x3d8, 0x09);
    wait_ticks(6);

    outb(0x3b0, 0x00);
    outb(0x3d8, 0x00);
    outb(0x3b8, 0x08);
    wait_ticks(2);
}
