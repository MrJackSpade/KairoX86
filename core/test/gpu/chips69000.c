/*
 * KairoX86's Chips & Technologies B69000 BitBLT test (KairoX86#283, for #249): on a B69000 (PCI 102Ch:00C0h), VESA
 * 640 x 480 x 8 with its linear frame buffer, the BitBLT registers in the aperture's MMIO window (+4 MB) and its data
 * port (+4 MB + 64K), a series of passes through the engine, each over a clear and held four ticks of the BIOS
 * clock: copies in every direction and overlapping through raster operations; colour and mono patterns (transparent,
 * solid, every vertical alignment); colour keying both ways; sources from the data port (colour and mono, every
 * alignment) and mono sources from video memory; at 8, 16 and 24 bits a pixel. The engine's status is never read: it
 * finishes at once. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_addr(u32 bus, u32 dev, u32 reg_) { return 0x80000000u | (bus << 16) | (dev << 11) | (reg_ & 0xfc); }

static volatile u32 *br;   /* BR00-BR0A */
static volatile u32 *port; /* the data port */
static volatile u8  *fb;
static u32           pitch;

/* BR04 */
#define DIR(d)      ((u32) (d) << 8)
#define SRC_PORT    (1u << 10)
#define MONO_SRC    (1u << 12)
#define MONO_TRANSP (1u << 13)
#define KEY         (1u << 14)
#define KEY_MODE(m) ((u32) (m) << 15)
#define PAT_TRANSP  (1u << 17)
#define MONO_PAT    (1u << 18)
#define SOLID       (1u << 19)
#define VALIGN(v)   ((u32) (v) << 20)
#define DEPTH(b)    ((1u << 23) | ((u32) ((b) - 1) << 24))

static u32 depth;

static void clear(u32 salt) {
    for (u32 i = 0; i < pitch * 480 / 4; i++)
        ((volatile u32 *) fb)[i] = pattern(i % 160, i / 160, salt);
    /* Patterns and mono bits at 400 K */
    for (u32 i = 0; i < 8192 / 4; i++)
        ((volatile u32 *) (fb + 400u * 1024u))[i] = pattern(i, 99, salt);
}

static void blit(u32 ctrl, u32 dst, u32 src, u32 pat, u32 w_px, u32 h, u32 sspan, u32 mono) {
    br[0] = (pitch << 16) | sspan;
    br[3] = mono;
    br[4] = ctrl | DEPTH(depth);
    br[5] = pat;
    br[6] = src;
    br[7] = dst;
    br[8] = (h << 16) | (w_px * depth); /* the top byte starts it */
}

static const u8 rops[] = { 0xcc, 0x66, 0x88, 0xee, 0xf0, 0x5a, 0xa0, 0x33, 0x99, 0x0f, 0x55, 0xbb };

static u32 at(u32 x, u32 y) { return y * pitch + x * depth; }

static void p_copies(u32 salt) {
    (void) salt;
    for (u32 k = 0; k < 8; k++) {
        const u32 x = 10 + (k % 4) * 150, y = 10 + (k / 4) * 110;
        blit(rops[k], at(x, y), at(x + 7, 300 + k * 9), 400u * 1024u, 90, 80, pitch, 0);
    }
    /* Every direction, overlapping: the addresses are the corner the walk starts at */
    for (u32 d = 0; d < 4; d++) {
        const u32 x = 20 + d * 150, y = 260;
        const u32 w = 80, h = 70;
        const u32 fx = (d & 1) ? w - 1 : 0, fy = (d & 2) ? h - 1 : 0;
        blit(DIR(d) | 0xcc, at(x + 6 + fx, y + 4 + fy) + ((d & 1) ? depth - 1 : 0), at(x + fx, y + fy) + ((d & 1) ? depth - 1 : 0),
             0, w, h, (d & 2) ? (u32) -pitch : pitch, 0);
    }
}

static void p_patterns(u32 salt) {
    br[1] = pattern(1, 2, salt);
    br[2] = pattern(2, 2, salt);
    for (u32 k = 0; k < 12; k++) {
        const u32 x = 10 + (k % 4) * 155, y = 10 + (k / 4) * 155;
        u32 ctrl = VALIGN(k & 7) | rops[k];
        if (k >= 4)
            ctrl |= MONO_PAT;
        if (k >= 8)
            ctrl |= (k & 1) ? PAT_TRANSP : SOLID;
        blit(ctrl, at(x, y), at(x + 3, y + 1), 400u * 1024u + k * 64, 140, 140, pitch, 0);
    }
}

static void p_keys(u32 salt) {
    br[1] = pattern(3, 2, salt) & 0xffff00ffu;
    for (u32 k = 0; k < 8; k++) {
        const u32 x = 10 + (k % 4) * 155, y = 10 + (k / 4) * 200;
        blit(KEY | KEY_MODE(k & 3) | rops[k], at(x, y), at(x + 40, 300), 400u * 1024u, 140, 180, pitch, 0);
    }
}

static void p_host(u32 salt) {
    br[1] = pattern(4, 2, salt);
    br[2] = pattern(5, 2, salt);
    /* Colour from the port: quadword-aligned rows */
    const u32 w = 37, h = 30;
    blit(SRC_PORT | 0xcc, at(20, 20), 0, 0, w, h, 0, 0);
    for (u32 i = 0; i < ((w * depth + 7) & ~7u) * h / 4 + 8; i++)
        *port = pattern(i, 6, salt);
    /* Mono from the port, byte- and doubleword-aligned, colours from BR01/BR02 or BR09/BR0A */
    for (u32 a = 1; a <= 4; a++) {
        br[9]  = pattern(a, 7, salt);
        br[10] = pattern(a, 8, salt);
        blit(SRC_PORT | MONO_SRC | ((a & 1) ? MONO_TRANSP : 0) | rops[a], at(100 + a * 120, 20), 0, 0, 100, 40, 0,
             (u32) a << 24 | ((a == 2) ? (1u << 27) : 0) | (a & 3));
        for (u32 i = 0; i < 100 * 40 / 32 + 64; i++)
            *port = pattern(i, 9 + a, salt);
    }
    /* Mono from video memory, source-span aligned */
    blit(MONO_SRC | 0xcc, at(20, 200), 400u * 1024u, 0, 160, 100, 24, 0);
    blit(MONO_SRC | MONO_TRANSP | 0x66, at(300, 200), 400u * 1024u + 333, 0, 160, 100, 24, 2);
}

void test_main(void) {
    __asm__ volatile("fninit");
    u32 bus, dev;
    int found = 0;
    for (bus = 0; bus < 2 && !found; bus++)
        for (dev = 0; dev < 32 && !found; dev++) {
            outl(0xcf8, pci_addr(bus, dev, 0));
            if (inl(0xcfc) == 0x00c0102cu) {
                found = 1;
                break;
            }
        }
    if (!found)
        return;
    bus--;
    outl(0xcf8, pci_addr(bus, dev, 0x10));
    const u32 base = inl(0xcfc) & 0xff000000u;
    const u16 mode = vbe_find(640, 480, 8);
    if (!mode || (int10(0x4f02, mode | 0x4000, 0, 0, 0, 0) != 0x004f))
        return;
    pitch = VBE_MODE->pitch;
    fb    = (volatile u8 *) VBE_MODE->framebuffer;
    br    = (volatile u32 *) (base + 0x400000u);
    port  = (volatile u32 *) (base + 0x410000u);

    static void (*const passes[])(u32) = { p_copies, p_patterns, p_keys, p_host };
    for (u32 d = 1; d <= 3; d++) {
        depth = d;
        for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
            clear(0x30 + d * 8 + p);
            passes[p](d * 8 + p);
            wait_ticks(4);
        }
    }
}
