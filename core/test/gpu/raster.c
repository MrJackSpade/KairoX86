/*
 * KairoX86's raster test (KairoX86#283): what a card shows when the guest changes it as the beam
 * scans. In mode 13h:
 * - the palette: every line shows colour 1, and colour 1 changes in each horizontal retrace, so
 *   each line has its own colour (the palette a line is drawn with is the one at its scan);
 * - VRAM: the lower half's pattern changes in each line's retrace, one line after the beam;
 * - the CRTC: the start address moves each frame, and the line compare splits the screen at line 100.
 * Each for 3 frames.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

#define STATUS 0x3da

static void wait_retrace_start(void) {
    while (inb(STATUS) & 8) {
    }
    while (!(inb(STATUS) & 8)) {
    }
}

/* Waits for the next horizontal (display) blank to begin */
static void wait_line(void) {
    while (inb(STATUS) & 1) {
    }
    while (!(inb(STATUS) & 1)) {
    }
}

static void palette_lines(void) {
    u8 *screen = (u8 *) 0xa0000;
    for (u32 i = 0; i < 64000; i++)
        screen[i] = 1;
    for (int frame = 0; frame < 3; frame++) {
        wait_retrace_start();
        /* Mode 13h's 200 lines are each scanned twice: 400 retraces a frame */
        for (u32 line = 0; line < 400; line++) {
            wait_line();
            const u32 v = pattern(line, (u32) frame, 0x51);
            outb(0x3c8, 1);
            outb(0x3c9, v & 63);
            outb(0x3c9, (v >> 6) & 63);
            outb(0x3c9, (v >> 12) & 63);
        }
    }
}

static void vram_lines(void) {
    u8 *screen = (u8 *) 0xa0000;
    for (int frame = 0; frame < 3; frame++) {
        wait_retrace_start();
        for (u32 line = 0; line < 400; line++) {
            wait_line();
            const u32 y = 100 + (line >> 2);
            if (y < 200)
                for (u32 x = 0; x < 320; x += 4)
                    *(u32 *) &screen[y * 320 + x] = pattern(x, y, (u32) (frame * 400 + line));
        }
    }
}

static void crtc_scroll_split(void) {
    u8 *screen = (u8 *) 0xa0000;
    for (u32 i = 0; i < 0x10000; i += 4)
        *(u32 *) &screen[i] = pattern(i, 1, 0x52);
    /* Line compare 100 lines (200 scans): bits 0-7 in 18h, bit 8 in 07h bit 4, bit 9 in 09h bit 6 */
    outb(0x3d4, 0x07);
    outb(0x3d5, (u8) ((inb(0x3d5) & ~0x10)));
    outb(0x3d4, 0x09);
    outb(0x3d5, (u8) (inb(0x3d5) & ~0x40));
    outw(0x3d4, (u16) (0x18 | (200 << 8)));
    for (u32 frame = 0; frame < 6; frame++) {
        /* Mode 13h counts the start address in dwords */
        const u32 start = frame * 80 * 3;
        outw(0x3d4, (u16) (0x0c | ((start >> 8) << 8)));
        outw(0x3d4, (u16) (0x0d | ((start & 0xff) << 8)));
        wait_retrace_start();
    }
    outw(0x3d4, 0xff18);
    outb(0x3d4, 0x07);
    outb(0x3d5, (u8) (inb(0x3d5) | 0x10));
    outb(0x3d4, 0x09);
    outb(0x3d5, (u8) (inb(0x3d5) | 0x40));
}

void test_main(void) {
    if (!is_vga())
        return;
    int10(0x0013, 0, 0, 0, 0, 0);
    palette_lines();
    vram_lines();
    crtc_scroll_split();
}
