/*
 * KairoX86's hardware cursor test (KairoX86#283, for #233): on an S3 (CR45 to CR4F: the 86C801 to Trio64 and Vision
 * family, the ViRGE and Trio3D): 640 x 480 at each pixel width its BIOS sets (VESA 101h, 111h and 112h, its linear
 * window placed as s3.c does), the screen filled with a pattern, a 64 x 64 cursor of two
 * planes (a pattern, so it has transparent, inverting and both colour pixels) put in card memory with its colours,
 * shown inside the picture, past its right edge and near its bottom, then in X11 mode (CR55 bit 4), each held
 * six ticks of the BIOS clock. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

enum { NONE, S3 };

static u8 crtc_read(u8 index) {
    outb(0x3d4, index);
    return inb(0x3d5);
}

static void crtc_write(u8 index, u8 value) {
    outb(0x3d4, index);
    outb(0x3d5, value);
}

static u32 pci_read(u32 bus, u32 dev, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (reg_ & 0xfc));
    return inl(0xcfc);
}

static void pci_write(u32 bus, u32 dev, u32 reg_, u32 v) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (reg_ & 0xfc));
    outl(0xcfc, v);
}

static void s3_unlock(void) {
    crtc_write(0x38, 0x48);
    crtc_write(0x39, 0xa5);
}

static int detect(void) {
    /* S3: CR38 48h and CR39 A5h unlock, then CR30 holds the chip's ID */
    s3_unlock();
    const u8 id = crtc_read(0x30);
    if ((id >= 0x81) && (id != 0xff))
        return S3;
    return NONE;
}

/* ---- S3: the linear window, as s3.c places it */

static volatile u8 *s3_window(void) {
    for (u32 b = 0; b < 2; b++)
        for (u32 d = 0; d < 32; d++)
            if ((pci_read(b, d, 0) & 0xffff) == 0x5333) {
                pci_write(b, d, 0x10, 0xe0000000u);
                s3_unlock();
                crtc_write(0x58, (u8) ((crtc_read(0x58) & ~0x03) | 0x13));
                return (volatile u8 *) 0xe0000000u;
            }
    s3_unlock();
    crtc_write(0x59, 0x00);
    crtc_write(0x5a, 0xc0);
    crtc_write(0x58, (u8) ((crtc_read(0x58) & ~0x03) | 0x13));
    return (volatile u8 *) 0x00c00000u;
}

static void s3_cursor(volatile u8 *fb, u32 at, u32 x, u32 y, u32 salt) {
    for (u32 i = 0; i < 1024 / 4; i++)
        ((volatile u32 *) (fb + at))[i] = pattern(i, 7, salt);
    crtc_write(0x4c, (u8) (at >> 18));
    crtc_write(0x4d, (u8) (at >> 10));
    crtc_write(0x4e, 0);
    crtc_write(0x4f, 0);
    (void) crtc_read(0x45); /* the colour stacks back to their first byte */
    for (u32 i = 0; i < 3; i++)
        crtc_write(0x4a, (u8) pattern(i, 1, salt));
    for (u32 i = 0; i < 3; i++)
        crtc_write(0x4b, (u8) pattern(i, 2, salt));
    crtc_write(0x46, (u8) (x >> 8));
    crtc_write(0x47, (u8) x);
    crtc_write(0x48, (u8) (y >> 8));
    crtc_write(0x49, (u8) y);
    crtc_write(0x45, (u8) (crtc_read(0x45) | 0x01));
}

static const u32 places[3][2] = { { 200, 150 }, { 600, 300 }, { 100, 440 } };

static void s3_run(void) {
    static const u16 modes[3] = { 0x101, 0x111, 0x112 };
    for (u32 f = 0; f < 3; f++) {
        if (int10(0x4f02, modes[f], 0, 0, 0, 0) != 0x004f)
            continue;
        volatile u8 *fb    = s3_window();
        const u32    bytes = (f == 0) ? 1 : (f == 1) ? 2 : 4;
        for (u32 i = 0; i < 640 * 480 * bytes / 4; i++)
            ((volatile u32 *) fb)[i] = pattern(i % 160, i / 160, 0x30 + f);
        for (u32 p = 0; p < 3; p++) {
            s3_cursor(fb, 0x100000u, places[p][0], places[p][1], 0x40 + f * 4 + p);
            wait_ticks(6);
        }
        crtc_write(0x55, (u8) (crtc_read(0x55) | 0x10)); /* X11 mode */
        wait_ticks(6);
        crtc_write(0x55, (u8) (crtc_read(0x55) & ~0x10));
        crtc_write(0x45, (u8) (crtc_read(0x45) & ~0x01));
    }
}

void test_main(void) {
    __asm__ volatile("fninit");
    if (detect() == S3)
        s3_run();
}
