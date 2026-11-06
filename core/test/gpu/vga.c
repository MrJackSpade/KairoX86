/*
 * KairoX86's standard modes test (KairoX86#283): every BIOS mode of the IBM PC's cards, 0 to 13h, and
 * VGA's unchained 256-colour mode (mode X, 320 x 240), each set, its memory filled with the pattern,
 * and held one tick of the BIOS clock. Each card gets only the modes of its class (runtime.h CARD_*).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

/* Every byte of [at, at + bytes) from the pattern */
static void fill_bytes(u8 *at, u32 bytes, u32 salt) {
    for (u32 i = 0; i < bytes; i += 4) {
        const u32 v = pattern(i, 0, salt);
        for (u32 b = 0; (b < 4) && (i + b < bytes); b++)
            at[i + b] = (u8) (v >> (8 * b));
    }
}

/* The four planes of A0000h, each its own pattern, through the sequencer's map mask */
static void fill_planes(u32 bytes, u32 salt) {
    for (u32 plane = 0; plane < 4; plane++) {
        outw(0x3c4, (u16) (0x0002 | ((1u << plane) << 8)));
        fill_bytes((u8 *) 0xa0000, bytes, salt * 4 + plane);
    }
    outw(0x3c4, 0x0f02);
}

static void show(u32 mode) {
    int10((u16) mode, 0, 0, 0, 0, 0);
    switch (mode) {
    case 0x00: case 0x01: case 0x02: case 0x03:
        fill_bytes((u8 *) 0xb8000, 0x4000, mode);
        break;
    case 0x07:
        fill_bytes((u8 *) 0xb0000, 0x1000, mode);
        break;
    case 0x04: case 0x05: case 0x06:
        fill_bytes((u8 *) 0xb8000, 0x4000, mode);
        break;
    case 0x0d: case 0x0e: case 0x0f: case 0x10: case 0x11: case 0x12:
        fill_planes(0x10000, mode);
        break;
    case 0x13:
        fill_bytes((u8 *) 0xa0000, 64000, mode);
        break;
    }
    wait_ticks(1);
}

/* Mode X: mode 13h unchained (sequencer memory mode 06h, CRTC underline 00h, mode control E3h), 240
   lines (vertical timing of 480 lines, doubled), filled through the planes */
static void mode_x(void) {
    int10(0x0013, 0, 0, 0, 0, 0);
    outw(0x3c4, 0x0604);
    outb(0x3c2, 0xe3);
    outw(0x3d4, 0x0011); /* unlock CRTC 0-7 */
    static const u16 crtc[] = { 0x0d06, 0x3e07, 0x4109, 0xea10, 0xac11, 0xdf12, 0x0014, 0xe715, 0x0616, 0xe317 };
    for (u32 i = 0; i < sizeof(crtc) / sizeof(crtc[0]); i++)
        outw(0x3d4, crtc[i]);
    fill_planes(0x10000, 0x58);
    wait_frames(0x3da, 3);
}

/* The BIOS modes of each card class (runtime.h's CARD_*): a card is never asked for a mode its
   class lacks, which leaves its CRTC in no defined state */
static const u8 vga_modes[] = { 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x0d, 0x0e, 0x0f, 0x10, 0x11, 0x12, 0x13, 0 };
static const u8 ega_modes[] = { 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x0d, 0x0e, 0x10, 0 };
static const u8 ega_mono_modes[] = { 0x07, 0x0f, 0 };
static const u8 cga_modes[] = { 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0 };
static const u8 mda_modes[] = { 0x07, 0 };

void test_main(void) {
    const int card = card_class();
    const u8 *modes = card == CARD_VGA ? vga_modes : card == CARD_EGA ? ega_modes : card == CARD_EGA_MONO ? ega_mono_modes
                    : card == CARD_CGA ? cga_modes : mda_modes;
    /* Mode 0 is the end of each list but VGA's, EGA's and CGA's first */
    for (u32 i = 0; (i == 0) || modes[i]; i++)
        show(modes[i]);
    if (card == CARD_VGA)
        mode_x();
}
