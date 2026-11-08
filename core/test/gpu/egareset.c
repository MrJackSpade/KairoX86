/*
 * KairoX86's CRTC reset test (KairoX86#283, for #234): on an EGA or VGA, the BIOS's 640 x 350 x 16 (mode 10h) filled
 * with a pattern through the four planes, then its CRTC held in reset (register 17h bit 7 clear: the line black, its
 * memory still walked) and let go again, each held six ticks of the BIOS clock. On any other card it returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static void crtc_write(u8 index, u8 value) {
    outb(0x3d4, index);
    outb(0x3d5, value);
}

static u8 crtc_read(u8 index) {
    outb(0x3d4, index);
    return inb(0x3d5);
}

void test_main(void) {
    const int cls = card_class();
    if ((cls != CARD_EGA) && (cls != CARD_VGA))
        return;
    int10(0x0010, 0, 0, 0, 0, 0);
    volatile u8 *plane = (volatile u8 *) 0xa0000;
    for (u32 p = 0; p < 4; p++) {
        outb(0x3c4, 2);
        outb(0x3c5, (u8) (1u << p)); /* the plane written */
        for (u32 i = 0; i < 28000; i++)
            plane[i] = (u8) ((i * (3u + p)) ^ (i >> 4) ^ (p * 0x55u));
    }
    outb(0x3c4, 2);
    outb(0x3c5, 0x0f);
    wait_ticks(6);
    /* The CRTC's mode control: an EGA's reads back as the BIOS's E3h */
    const u8 mode = (cls == CARD_VGA) ? crtc_read(0x17) : 0xe3;
    crtc_write(0x17, (u8) (mode & 0x7f));
    wait_ticks(6);
    crtc_write(0x17, mode);
    wait_ticks(6);
    int10(0x0003, 0, 0, 0, 0, 0);
}
