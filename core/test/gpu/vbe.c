/*
 * KairoX86's VESA modes test (KairoX86#283): every mode the card's VBE BIOS lists that is packed pixel or
 * direct colour, 8 to 32 bits a pixel, at most 1024 x 768, with a linear framebuffer: set, its palette
 * loaded (8 bits), the screen filled with the pattern through the linear framebuffer, held 4 frames.
 * Then text mode 3. A card with no VBE BIOS goes straight to text mode.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

struct vbe_info {
    char signature[4];
    u16 version;
    u32 oem;
    u32 caps;
    u32 modes;      /* far pointer: offset low, segment high */
    u16 memory;
    u8 rest[492];
} __attribute__((packed));

struct mode_info {
    u16 attributes;
    u8 window_a, window_b;
    u16 granularity, window_size, segment_a, segment_b;
    u32 window_func;
    u16 pitch;
    u16 width, height;
    u8 char_w, char_h, planes, bpp, banks, model, bank_size, image_pages, reserved0;
    u8 red_size, red_pos, green_size, green_pos, blue_size, blue_pos, rsv_size, rsv_pos, direct_info;
    u32 framebuffer;
    u8 rest[212];
} __attribute__((packed));

/* At fixed addresses below 64 KB, so ES:DI (ES = 0) reaches them */
#define INFO ((struct vbe_info *) 0x6000)
#define MODE ((struct mode_info *) 0x6200)
#define MODES ((u16 *) 0x6400)

/* Two copies of one row of the pattern, above the program (flat addressing, unreal mode) */
#define ROW ((u8 *) 0x20000)

/* The pattern's row built once, twice over, and each line written from it 13 pixels further on, a
   32-bit store at a time, so even a 486 fills 1024 x 768 at 32 bits within a few frames. A misplaced,
   dropped or doubled pixel or line still shows. */
static void fill(const struct mode_info *m, u32 salt) {
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
    INFO->signature[0] = 'V';
    INFO->signature[1] = 'B';
    INFO->signature[2] = 'E';
    INFO->signature[3] = '2';
    if (int10(0x4f00, 0, 0, 0, 0x6000, 0) == 0x004f) {
        /* The mode list, copied below 64 KB before any other call can change it */
        const u16 *list = (const u16 *) (((INFO->modes >> 16) << 4) + (INFO->modes & 0xffff));
        int count = 0;
        while (count < 255 && list[count] != 0xffff) {
            MODES[count] = list[count];
            count++;
        }
        for (int i = 0; i < count; i++) {
            const u16 mode = MODES[i];
            if (int10(0x4f01, 0, mode, 0, 0x6200, 0) != 0x004f)
                continue;
            const int lfb = (MODE->attributes & 0x81) == 0x81 && MODE->framebuffer;
            const int packed = MODE->model == 4 || MODE->model == 6;
            if (!lfb || !packed || MODE->bpp < 8 || MODE->width > 1024 || MODE->height > 768)
                continue;
            if (int10(0x4f02, mode | 0x4000, 0, 0, 0, 0) != 0x004f)
                continue;
            if (MODE->bpp == 8)
                palette(mode);
            fill(MODE, mode);
            wait_frames(0x3da, 4);
        }
    }
    int10(0x0003, 0, 0, 0, 0, 0);
}
