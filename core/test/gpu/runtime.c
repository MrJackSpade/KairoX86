/*
 * The graphics tests' entry and helpers (KairoX86#283, runtime.h).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

void end_screen(void);

/* The test's end at a fixed address, 0000:8002: a HLT with interrupts off, after which the machine
   stops ("The PC halted ... (at 0000:8003)", the HLT's next instruction), so the batch (compare.py,
   TEST_END) knows the program ran to its end on any card, whatever its last picture. */
__asm__(".section .text.entry\n"
        ".globl _start\n"
        "_start:\n"
        "    jmp 2f\n"
        "1:  cli\n"
        "    hlt\n"
        "    jmp 1b\n"
        "2:  cld\n"
        "    calll test_main\n"
        "    calll end_screen\n"
        "    jmp 1b\n");

int card_class(void) {
    /* VGA: the display combination call (INT 10h 1A00h), which only a VGA's BIOS has */
    u16 bx = 0;
    const u16 al = int10(0x1a00, 0, 0, 0, 0, &bx) & 0xff;
    if (al == 0x1a && ((u8) bx == 7 || (u8) bx == 8))
        return CARD_VGA;
    /* EGA: its information call (INT 10h 12h, BL 10h) changes BL; BH 1 is a mono display */
    bx = 0;
    int10(0x1200, 0x0010, 0, 0, 0, &bx);
    if ((u8) bx != 0x10)
        return (bx >> 8) ? CARD_EGA_MONO : CARD_EGA;
    /* MDA (Hercules too) or CGA: the BIOS's initial video mode in the equipment word, 3 for mono */
    return ((*(volatile u16 *) 0x410 >> 4) & 3) == 3 ? CARD_MDA : CARD_CGA;
}

int is_vga(void) {
    return card_class() == CARD_VGA;
}

/* The end screen every test finishes on: a mode of the card's class drawn with (x + 3y) modulo its
   colours. VGA: mode 13h with 256 distinct palette entries. Colour EGA: mode 0Dh. CGA: mode 4. Mono
   cards: mode 7, every cell's character and attribute from the cell's place. */
void end_screen(void) {
    const int card = card_class();
    if (card == CARD_VGA) {
        int10(0x0013, 0, 0, 0, 0, 0);
        outb(0x3c8, 0);
        for (u32 i = 0; i < 256; i++) {
            /* 256 distinct 6-bit colours: i's bits spread over red, green and blue */
            outb(0x3c9, (u8) ((i & 7) << 3));
            outb(0x3c9, (u8) (((i >> 3) & 7) << 3));
            outb(0x3c9, (u8) (((i >> 6) & 3) << 4));
        }
        u8 *screen = (u8 *) 0xa0000;
        for (u32 y = 0; y < 200; y++)
            for (u32 x = 0; x < 320; x++)
                screen[y * 320 + x] = (u8) (x + 3 * y);
    } else if (card == CARD_EGA) {
        int10(0x000d, 0, 0, 0, 0, 0);
        /* Planar: plane p of a pixel is bit p of its colour */
        u8 *screen = (u8 *) 0xa0000;
        for (u32 plane = 0; plane < 4; plane++) {
            outw(0x3c4, (u16) (0x0002 | ((1u << plane) << 8)));
            for (u32 y = 0; y < 200; y++)
                for (u32 bx8 = 0; bx8 < 40; bx8++) {
                    u8 v = 0;
                    for (u32 b = 0; b < 8; b++)
                        v |= (u8) (((((bx8 * 8 + b) + 3 * y) >> plane) & 1) << (7 - b));
                    screen[y * 40 + bx8] = v;
                }
        }
        outw(0x3c4, 0x0f02);
    } else if (card == CARD_CGA) {
        int10(0x0004, 0, 0, 0, 0, 0);
        /* Two bits a pixel, even lines at B8000h, odd ones 8 KB on */
        u8 *screen = (u8 *) 0xb8000;
        for (u32 y = 0; y < 200; y++)
            for (u32 bx4 = 0; bx4 < 80; bx4++) {
                u8 v = 0;
                for (u32 p = 0; p < 4; p++)
                    v |= (u8) ((((bx4 * 4 + p) + 3 * y) & 3) << (6 - 2 * p));
                screen[(y & 1) * 0x2000 + (y >> 1) * 80 + bx4] = v;
            }
    } else {
        int10(0x0007, 0, 0, 0, 0, 0);
        u8 *screen = (u8 *) 0xb0000;
        for (u32 y = 0; y < 25; y++)
            for (u32 x = 0; x < 80; x++) {
                screen[(y * 80 + x) * 2]     = (u8) (x + 3 * y);
                screen[(y * 80 + x) * 2 + 1] = (u8) ((x + 3 * y) & 0x7f);
            }
    }
}

void wait_frames(u16 status_port, int n) {
    for (int i = 0; i < n; i++) {
        while (inb(status_port) & 8) {
        }
        while (!(inb(status_port) & 8)) {
        }
    }
}

