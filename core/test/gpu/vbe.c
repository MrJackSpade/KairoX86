/*
 * KairoX86's VESA modes test (KairoX86#283): every mode the card's VBE BIOS lists that is packed pixel or
 * direct colour, 8 to 32 bits a pixel, at most 1024 x 768, with a linear framebuffer: set, its palette
 * loaded (8 bits), the screen filled with the pattern through the linear framebuffer, held 4 frames.
 * Then text mode 3. A card with no VBE BIOS goes straight to text mode.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

/* Two copies of one row of the pattern, above the program (flat addressing, unreal mode) */
#define ROW ((u8 *) 0x20000)

/* The pattern's row built once, twice over, and each line written from it 13 pixels further on, a
   32-bit store at a time, so even a 486 fills 1024 x 768 at 32 bits within a few frames. A misplaced,
   dropped or doubled pixel or line still shows. */
static void fill(const struct vbe_mode_info *m, u32 salt) {
    const u32 bytes = (m->bpp + 7) / 8;
    const u32 row = m->width * bytes;
    for (u32 x = 0; x < m->width; x++) {
        const u32 v = pattern(x, 0, salt);
        for (u32 b = 0; b < bytes; b++)
            ROW[x * bytes + b] = ROW[row + x * bytes + b] = (u8) (v >> (8 * b));
    }
    u8 *fb = (u8 *) m->framebuffer;
    u32 shift = 0;
    for (u32 y = 0; y < m->height; y++) {
        const u32 *from = (const u32 *) (ROW + shift);
        u32 *to = (u32 *) (fb + y * m->pitch);
        for (u32 i = 0; i < row / 4; i++)
            to[i] = from[i];
        for (u32 i = row & ~3u; i < row; i++)
            ((u8 *) to)[i] = ((const u8 *) from)[i];
        shift += 13 * bytes;
        if (shift >= row)
            shift -= row;
    }
}

static void palette(u32 salt) {
    outb(0x3c8, 0);
    for (u32 i = 0; i < 256; i++) {
        const u32 v = pattern(i, 0, salt);
        outb(0x3c9, v & 63);
        outb(0x3c9, (v >> 6) & 63);
        outb(0x3c9, (v >> 12) & 63);
    }
}

void test_main(void) {
    const int count = vbe_modes();
    for (int i = 0; i < count; i++) {
        const u16 mode = VBE_MODES[i];
        if (int10(0x4f01, 0, mode, 0, 0x6200, 0) != 0x004f)
            continue;
        const int lfb = (VBE_MODE->attributes & 0x81) == 0x81 && VBE_MODE->framebuffer;
        const int packed = VBE_MODE->model == 4 || VBE_MODE->model == 6;
        if (!lfb || !packed || VBE_MODE->bpp < 8 || VBE_MODE->width > 1024 || VBE_MODE->height > 768)
            continue;
        if (int10(0x4f02, mode | 0x4000, 0, 0, 0, 0) != 0x004f)
            continue;
        if (VBE_MODE->bpp == 8)
            palette(mode);
        fill(VBE_MODE, mode);
        wait_frames(0x3da, 4);
    }
    int10(0x0003, 0, 0, 0, 0, 0);
}
