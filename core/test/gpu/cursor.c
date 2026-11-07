/*
 * KairoX86's hardware cursor test (KairoX86#283, for #233): on an S3 (CR45 to CR4F: the 86C801 to Trio64 and Vision
 * family, the ViRGE and Trio3D): 640 x 480 at each pixel width its BIOS sets (VESA 101h, 111h and 112h, its linear
 * window placed as s3.c does), the screen filled with a pattern, a 64 x 64 cursor of two
 * planes (a pattern, so it has transparent, inverting and both colour pixels) put in card memory with its colours,
 * shown inside the picture, past its right edge and near its bottom, then in X11 mode (CR55 bit 4), each held
 * six ticks of the BIOS clock. On a Cirrus (SR6 reads back 12h): the BIOS's mode 5Fh (640 x 480 x 8), the cursor's
 * patterns in the last 16K of video memory, its colours through the extended DAC entries (SR12 bit 1), at 32 x 32 and
 * 64 x 64 (SR12 bit 2) at the same three places. Any other card returns at once.
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

/* ---- The RAMDAC's own cursor on an S3 Vision964 or 968 (its RS2 and RS3 lines from CR55 bits 0 and 1): a Bt485,
   an IBM RGB528 or a TI TVP3026, told apart as drivers do. RS n is port 3C8h, 3C9h, 3C6h or 3C7h (its bits 0-1: 0 to
   3) with CR55 n >> 2. */

enum { DAC_NONE, BT485, RGB528, TVP3026 };

static const u16 rs_ports[4] = { 0x3c8, 0x3c9, 0x3c6, 0x3c7 };

static void rs_out(u32 rs, u8 v) {
    crtc_write(0x55, (u8) ((crtc_read(0x55) & ~0x03) | (rs >> 2)));
    outb(rs_ports[rs & 3], v);
}

static u8 rs_in(u32 rs) {
    crtc_write(0x55, (u8) ((crtc_read(0x55) & ~0x03) | (rs >> 2)));
    return inb(rs_ports[rs & 3]);
}

static int vision(void) {
    s3_unlock();
    const u8 id = crtc_read(0x30);
    return ((id & 0xf0) == 0xd0) || ((id == 0xe1) && (crtc_read(0x2e) == 0xf0));
}

static int dac_kind(void) {
    rs_out(0, 0x3f); /* the TVP3026's index 3Fh, its ID */
    if (rs_in(0x0a) == 0x26)
        return TVP3026;
    if ((rs_in(0x0a) & 0xf0) == 0x60) /* the Bt485's status register, its ID in bits 4-7 */
        return BT485;
    return RGB528;
}

static void rgb528(u32 index, u8 v) {
    rs_out(4, (u8) index);
    rs_out(5, (u8) (index >> 8));
    rs_out(6, v);
}

/* The cursor's 64 x 64 pattern, its three colours, at (x, y) */
static void dac_cursor(int kind, u32 x, u32 y, u32 salt) {
    if (kind == RGB528) {
        rgb528(0x30, 0x00);
        rs_out(7, 0x01); /* the index counts up after each data byte */
        rs_out(4, 0x00);
        rs_out(5, 0x01);
        for (u32 i = 0; i < 1024; i++)
            rs_out(6, (u8) pattern(i, 11, salt));
        rs_out(7, 0x00);
        for (u32 i = 0; i < 9; i++)
            rgb528(0x40 + i, (u8) pattern(i, 12, salt));
        rgb528(0x31, (u8) x);
        rgb528(0x32, (u8) (x >> 8));
        rgb528(0x33, (u8) y);
        rgb528(0x34, (u8) (y >> 8));
        rgb528(0x35, 0);
        rgb528(0x36, 0);
        rgb528(0x30, 0x06); /* 64 x 64, two-colour and inverting */
    } else {
        /* The pattern through the cursor RAM data register (RS 0Bh) from address 0: the TVP3026 takes its two high
           address bits from the indirect cursor control (index 06h), the Bt485 from command register 3 */
        for (u32 k = 0; k < 4; k++) {
            if (kind == TVP3026) {
                rs_out(0, 0x06);
                rs_out(0x0a, (u8) (k << 2));
            } else {
                rs_out(6, (u8) (rs_in(6) | 0x80)); /* command register 3 reachable */
                rs_out(0, 0x01);
                rs_out(0x0a, (u8) (0x04 | k));
            }
            rs_out(0, 0x00);
            for (u32 i = 0; i < 256; i++)
                rs_out(0x0b, (u8) pattern(k * 256 + i, 11, salt));
        }
        rs_out(4, 0x01); /* the cursor colours 1 to 3 */
        for (u32 i = 0; i < 9; i++)
            rs_out(5, (u8) (pattern(i, 12, salt) & 0x3f));
        /* The position counts the cursor's far corner: (x + 64, y + 64) */
        rs_out(0x0c, (u8) (x + 64));
        rs_out(0x0d, (u8) ((x + 64) >> 8));
        rs_out(0x0e, (u8) (y + 64));
        rs_out(0x0f, (u8) ((y + 64) >> 8));
        if (kind == TVP3026) {
            rs_out(0, 0x06);
            rs_out(0x0a, 0x02);
        } else
            rs_out(9, (u8) ((rs_in(9) & ~0x03) | 0x02));
    }
    crtc_write(0x55, (u8) (crtc_read(0x55) & ~0x03));
}

static void dac_cursor_off(int kind) {
    if (kind == RGB528)
        rgb528(0x30, 0x00);
    else if (kind == TVP3026) {
        rs_out(0, 0x06);
        rs_out(0x0a, 0x00);
    } else
        rs_out(9, (u8) (rs_in(9) & ~0x03));
    crtc_write(0x55, (u8) (crtc_read(0x55) & ~0x03));
}

static void dac_run(void) {
    if (!vision() || (int10(0x4f02, 0x101, 0, 0, 0, 0) != 0x004f))
        return;
    volatile u8 *fb = s3_window();
    for (u32 i = 0; i < 640 * 480 / 4; i++)
        ((volatile u32 *) fb)[i] = pattern(i % 160, i / 160, 0x3a);
    const int kind = dac_kind();
    for (u32 p = 0; p < 3; p++) {
        dac_cursor(kind, places[p][0], places[p][1], 0x60 + p);
        wait_ticks(6);
    }
    dac_cursor_off(kind);
}

/* ---- Cirrus (SR6 reads back 12h once unlocked): mode 5Fh, its cursor in the last 16K of video memory */

static void seq(u8 index, u8 value) {
    outb(0x3c4, index);
    outb(0x3c5, value);
}

static void gr(u8 index, u8 value) {
    outb(0x3ce, index);
    outb(0x3cf, value);
}

static int is_cirrus(void) {
    seq(0x06, 0x12);
    outb(0x3c4, 0x06);
    return inb(0x3c5) == 0x12;
}

/* The cursor's patterns at 4 MB - 16K through the 64K window in 16K steps (GR0Bh bit 5, GR9 FFh): the card's
   addresses wrap at its memory's size, so this is its last 16K whatever it has. Pattern n is at n * 256 (32 x 32,
   SR12 bit 2 clear: 128 bytes of each plane) or n * 1024 (64 x 64). */
static void cirrus_patterns(u32 salt) {
    gr(0x0b, 0x20);
    gr(0x09, 0xff);
    for (u32 i = 0; i < 0x4000; i++)
        *(volatile u8 *) (0xa0000u + i) = (u8) pattern(i, 9, salt);
    gr(0x09, 0x00);
    gr(0x0b, 0x00);
}

static void cirrus_cursor(u32 x, u32 y, u32 large, u32 salt) {
    /* Its colours: DAC entries 00h (background) and 0Fh (foreground) while SR12 bit 1 is set */
    seq(0x12, 0x02);
    outb(0x3c8, 0x00);
    for (u32 i = 0; i < 3; i++)
        outb(0x3c9, (u8) (pattern(i, 1, salt) & 0x3f));
    outb(0x3c8, 0x0f);
    for (u32 i = 0; i < 3; i++)
        outb(0x3c9, (u8) (pattern(i, 2, salt) & 0x3f));
    seq(0x13, (u8) (salt & 0x0c));
    /* The position: the high bits in SR10/SR11, the low three in the index's bits 5-7 */
    outb(0x3c4, (u8) (0x10 | ((x & 7) << 5)));
    outb(0x3c5, (u8) (x >> 3));
    outb(0x3c4, (u8) (0x11 | ((y & 7) << 5)));
    outb(0x3c5, (u8) (y >> 3));
    seq(0x12, (u8) (0x01 | (large ? 0x04 : 0x00)));
}

static void cirrus_run(void) {
    int10(0x005f, 0, 0, 0, 0, 0);
    seq(0x06, 0x12);
    gr(0x0b, 0x00);
    for (u32 i = 0; i < 640 * 480; i++) {
        if ((i & 0xfff) == 0)
            gr(0x09, (u8) (i >> 12));
        *(volatile u8 *) (0xa0000u + (i & 0xfff)) = (u8) pattern(i % 640, i / 640, 0x35);
    }
    gr(0x09, 0x00);
    cirrus_patterns(0x36);
    for (u32 large = 0; large < 2; large++)
        for (u32 p = 0; p < 3; p++) {
            cirrus_cursor(places[p][0], places[p][1], large, 0x50 + large * 4 + p);
            wait_ticks(6);
        }
    seq(0x12, 0x00);
}

void test_main(void) {
    __asm__ volatile("fninit");
    if (is_cirrus())
        cirrus_run();
    else if (detect() == S3) {
        s3_run();
        dac_run();
    }
}
