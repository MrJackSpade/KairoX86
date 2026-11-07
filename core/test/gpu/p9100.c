/*
 * KairoX86's Weitek Power 9100 test (KairoX86#283, for #266): on a P9100 (PCI 100Eh:9100h), the native drawing engine
 * in native mode at 640 x 480, 8, 16, 24 and 32 bits a pixel, each over a clear and held four ticks of the BIOS clock:
 * quads (rectangles, triangles, points, oversized lines), through ternary raster operations, the plane mask, the
 * windows and two and four colour patterns, transparent or not; blits apart and overlapping both ways, with and
 * without a pattern; pixel1 and pixel8 runs. Then the W5286 GHA: its blits and moves in planar, packed 8 and packed 16 modes (short and long, rotated, expanded, overlapping both
 * ways, masks) and lines both ways, shown in native mode at 8 bits a pixel. The engines' status is never waited on: they finish at once. Any other card
 * returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_addr(u32 bus, u32 dev, u32 reg_) { return 0x80000000u | (bus << 16) | (dev << 11) | (reg_ & 0xfc); }

static volatile u32 *regs;
static volatile u32 *fb;

static void reg(u32 offset, u32 value) { regs[offset / 4] = value; }

enum { SYSCONFIG = 0x04, VIDEO = 0x100, CMD_BLIT = 0x2004, CMD_QUAD = 0x2008, CMD_PIXEL8 = 0x200c, CMD_NEXT = 0x2014,
       CMD_PIXEL1 = 0x2080, DRAW = 0x2200, COORD_DEV = 0x3000, COORD_META = 0x3200 };
enum { D_COLOR0 = 0, D_COLOR1 = 1, D_PMASK = 2, D_PATX = 4, D_PATY = 5, D_RASTER = 6, D_PWMIN = 8, D_PWMAX = 9, D_COLOR2 = 0x0e,
       D_COLOR3 = 0x0f, D_PATTERN = 0x20, D_BWMIN = 0x28, D_BWMAX = 0x29 };
#define RASTER_TRANSPARENT 0x20000u
#define RASTER_OVERSIZED   0x10000u
#define RASTER_PIX1_TRANSP 0x08000u
#define RASTER_PAT_4COLOR  0x04000u
#define RASTER_PAT_ENABLE  0x02000u
/* Quad types, the meta coordinates' vertex type */
enum { T_POINT = 0, T_LINE = 1, T_TRI = 2, T_QUAD = 3, T_RECT = 4 };

static void draw(u32 idx, u32 value) { reg(DRAW + idx * 4, value); }

static void vertex(u32 type, int x, int y) { reg(COORD_META | (type << 6) | (3u << 3), ((u32) (x & 0xffff) << 16) | (u32) (y & 0xffff)); }

static void device(u32 i, int x, int y) { reg(COORD_DEV | (i << 6) | (3u << 3), ((u32) (x & 0xffff) << 16) | (u32) (y & 0xffff)); }

static u32 quad(void) { return regs[CMD_QUAD / 4]; }
static u32 blit(void) { return regs[CMD_BLIT / 4]; }

static void windows_open(void) {
    draw(D_PWMIN, 0);
    draw(D_PWMAX, (0x1fffu << 16) | 0x1fff);
    draw(D_BWMIN, 0);
    draw(D_BWMAX, (0x1fffu << 16) | 0x1fff);
}

/* Native mode's picture: sysconfig's pixel size and pitch, the timing in 64-bit words of the frame buffer */
static u32 pitch_bytes;

static void native_mode(u32 bytes) {
    /* Pixel size code, and the pitch as its top shift field */
    const u32 code = (bytes == 2) ? 3 : (bytes == 4) ? 5 : (bytes == 3) ? 7 : 2;
    const u32 top  = (bytes == 1) ? 1 : (bytes == 4) ? 3 : 2;
    reg(SYSCONFIG, (top << 29) | (code << 26));
    pitch_bytes = 512u << top;
    const u32 words = (640 * bytes) / 8;
    reg(VIDEO + 0x02 * 4, words + words / 4 - 1);
    reg(VIDEO + 0x04 * 4, 8);
    reg(VIDEO + 0x05 * 4, 8 + words);
    reg(VIDEO + 0x08 * 4, 525);
    reg(VIDEO + 0x0a * 4, 35);
    reg(VIDEO + 0x0b * 4, 515);
    reg(VIDEO + 0x0e * 4, 0x20);
}

static void clear(u32 salt) {
    for (u32 y = 0; y < 480; y++)
        for (u32 x = 0; x < pitch_bytes / 4; x++)
            fb[y * (pitch_bytes / 4) + x] = pattern(x & 255, y, salt) & 0x7f7f7f7fu;
}

static void p_quads(u32 bytes, u32 salt) {
    static const u32 rops[] = { 0xf0, 0xcc, 0xaa, 0x5a, 0x66, 0x88, 0xee, 0x0f, 0x96, 0x00, 0xff, 0xe2 };
    (void) bytes;
    for (u32 k = 0; k < 12; k++) {
        draw(D_COLOR0, pattern(k, 1, salt));
        draw(D_COLOR1, pattern(k, 2, salt));
        draw(D_PMASK, (k & 1) ? 0xf0f0ffffu : 0xffffffffu);
        draw(D_RASTER, rops[k]);
        const int x = 10 + (int) (k % 4) * 150, y = 10 + (int) (k / 4) * 100;
        vertex(T_RECT, x, y);
        vertex(T_RECT, x + 130 + (int) k, y + 80);
        quad();
    }
    draw(D_PMASK, 0xffffffffu);
    /* A triangle, a quad, oversized lines and points */
    draw(D_RASTER, 0xf0);
    draw(D_COLOR0, pattern(20, 1, salt));
    vertex(T_TRI, 40, 330);
    vertex(T_TRI, 200, 345);
    vertex(T_TRI, 90, 460);
    quad();
    draw(D_COLOR0, pattern(21, 1, salt));
    vertex(T_QUAD, 250, 320);
    vertex(T_QUAD, 400, 330);
    vertex(T_QUAD, 420, 450);
    vertex(T_QUAD, 240, 470);
    quad();
    draw(D_RASTER, 0xf0 | RASTER_OVERSIZED);
    for (u32 k = 0; k < 6; k++) {
        draw(D_COLOR0, pattern(k, 22, salt));
        vertex(T_LINE, 440 + (int) k * 30, 320);
        vertex(T_LINE, 620 - (int) k * 25, 470);
        quad();
        vertex(T_POINT, 450 + (int) k * 20, 300);
        quad();
    }
}

static void p_patterns(u32 bytes, u32 salt) {
    (void) bytes;
    for (u32 i = 0; i < 8; i++)
        draw(D_PATTERN + i, pattern(i, 3, salt));
    draw(D_COLOR0, pattern(1, 4, salt));
    draw(D_COLOR1, pattern(2, 4, salt));
    draw(D_COLOR2, pattern(3, 4, salt));
    draw(D_COLOR3, pattern(4, 4, salt));
    static const u32 modes[] = { RASTER_PAT_ENABLE | 0xf0, RASTER_PAT_ENABLE | RASTER_TRANSPARENT | 0xf0, RASTER_PAT_ENABLE | RASTER_PAT_4COLOR | 0xf0,
                                 RASTER_PAT_ENABLE | 0xfc, RASTER_PAT_ENABLE | RASTER_PAT_4COLOR | 0x5a, RASTER_PAT_ENABLE | RASTER_TRANSPARENT | 0xa0 };
    for (u32 k = 0; k < 6; k++) {
        draw(D_PATX, k * 3);
        draw(D_PATY, k * 5);
        draw(D_RASTER, modes[k]);
        vertex(T_RECT, 20 + (int) k * 100, 20);
        vertex(T_RECT, 110 + (int) k * 100, 230);
        quad();
    }
    /* The windows clip a quad */
    draw(D_RASTER, 0xf0);
    draw(D_PWMIN, (100u << 16) | 260);
    draw(D_PWMAX, (500u << 16) | 420);
    draw(D_COLOR0, pattern(5, 4, salt));
    vertex(T_QUAD, 60, 250);
    vertex(T_QUAD, 540, 270);
    vertex(T_QUAD, 520, 440);
    vertex(T_QUAD, 80, 460);
    quad();
    windows_open();
}

static void p_blits(u32 bytes, u32 salt) {
    /* Coordinates in bytes */
    for (u32 k = 0; k < 8; k++) {
        const u32 g = pattern(k, 5, salt);
        const int sx = (int) (10 + g % 200) * (int) bytes, sy = 10 + (int) ((g >> 9) % 150);
        const int w = (40 + (int) ((g >> 17) % 200)) * (int) bytes, h = 30 + (int) ((g >> 23) % 150);
        const int dx = sx + ((k & 1) ? 13 : -9) * (int) bytes * ((k & 4) ? 30 : 1), dy = sy + ((k & 2) ? 7 : -5) * ((k & 4) ? 40 : 1);
        draw(D_RASTER, (k == 6) ? 0x66 : (k == 7) ? 0xc0 : 0xcc);
        device(0, sx, sy);
        device(1, sx + w - 1, sy + h - 1);
        device(2, dx, dy);
        device(3, dx + w - 1, dy + h - 1);
        blit();
    }
    /* With a pattern, clipped by the byte window */
    for (u32 i = 0; i < 8; i++)
        draw(D_PATTERN + i, pattern(i, 6, salt));
    draw(D_COLOR0, pattern(1, 7, salt));
    draw(D_COLOR1, pattern(2, 7, salt));
    draw(D_RASTER, RASTER_PAT_ENABLE | RASTER_TRANSPARENT | 0xc0);
    draw(D_BWMIN, ((80u * bytes) << 16) | 300);
    draw(D_BWMAX, ((400u * bytes) << 16) | 440);
    device(0, 0, 0);
    device(1, 500 * (int) bytes - 1, 170);
    device(2, 40 * (int) bytes, 280);
    device(3, 540 * (int) bytes - 1, 450);
    blit();
    windows_open();
}

static void p_pixels(u32 bytes, u32 salt) {
    draw(D_RASTER, 0xf0);
    draw(D_COLOR0, pattern(1, 8, salt));
    draw(D_COLOR1, pattern(2, 8, salt));
    /* Pixel1: x[0] and x[1] the start, x[2] the right edge, y[1] the line, y[3] its step */
    device(0, 30, 0);
    device(1, 30, 40);
    device(2, 30 + 77, 0);
    device(3, 0, 1);
    for (u32 i = 0; i < 80; i++)
        reg(CMD_PIXEL1 + ((i % 32) * 4), pattern(i, 9, salt));
    draw(D_RASTER, 0xf0 | RASTER_PIX1_TRANSP);
    device(0, 200, 0);
    device(1, 200, 40);
    device(2, 200 + 91, 0);
    device(3, 0, 2);
    for (u32 i = 0; i < 80; i++)
        reg(CMD_PIXEL1 + (31 * 4), pattern(i, 10, salt));
    /* Pixel8: bytes */
    draw(D_RASTER, 0xcc);
    device(0, 30 * (int) bytes, 0);
    device(1, 30 * (int) bytes, 200);
    device(2, (30 + 90) * (int) bytes, 0);
    device(3, 0, 1);
    for (u32 i = 0; i < 90 * bytes * 80 / 4; i++)
        reg(CMD_PIXEL8, pattern(i & 255, i >> 8, salt));
    /* Next pixels: the block beside it */
    draw(D_RASTER, RASTER_PAT_ENABLE | 0xc0);
    for (u32 i = 0; i < 8; i++)
        draw(D_PATTERN + i, pattern(i, 11, salt));
    reg(CMD_NEXT, 60 * bytes);
    device(1, (30 + 90) * (int) bytes, 300);
    for (u32 i = 0; i < 60 * bytes * 60 / 4; i++)
        reg(CMD_PIXEL8, pattern(i & 255, i >> 8, salt + 1));
}

/* ---- the GHA: its registers are VGA's: instructions go in the queue in video memory ---- */

static void gdc(u8 index, u8 value) {
    outb(0x3ce, index);
    outb(0x3cf, value);
}

static u8 *vga_bytes; /* the frame buffer's bytes as the display shows them */
static u32 queue_at;  /* the queue's base (longwords) */
static u8  queue_tail;

/* An instruction: 16 bytes, four longwords in the queue */
static void gha(const u8 *ins) {
    volatile u32 *q = (volatile u32 *) (vga_bytes + ((queue_at + ((u32) queue_tail << 2)) << 2));
    for (u32 w = 0; w < 4; w++)
        q[w] = ((u32) ins[w * 4] << 24) | ((u32) ins[w * 4 + 1] << 16) | ((u32) ins[w * 4 + 2] << 8) | (u32) ins[w * 4 + 3]; /* the frame buffer is big-endian */
    queue_tail++;
    gdc(0x0a, queue_tail);
}

static void gha_blit(u8 opcode, u8 low, u8 start, u8 end, u8 rmask, u8 fg0, u8 fg1, u32 w, u32 h, u32 dst, u32 src, u32 pitch, u8 rot, u8 flags, int down) {
    u8 ins[16];
    ins[0] = (u8) ((opcode << 5) | low);
    ins[1] = start;
    ins[2] = (u8) w;
    ins[3] = rmask;
    ins[4] = fg0;
    ins[5] = fg1;
    ins[6] = end;
    ins[7] = (u8) h;
    ins[8] = (u8) dst;
    ins[9] = (u8) (dst >> 8);
    ins[10] = (u8) src;
    ins[11] = (u8) (src >> 8);
    ins[12] = (u8) pitch;
    ins[13] = (u8) (((pitch >> 8) & 1) | (((dst >> 16) & 3) << 1) | ((rot & 7) << 3) | (((h >> 8) & 3) << 6));
    ins[14] = (u8) pitch;
    ins[15] = (u8) (((pitch >> 8) & 1) | (((src >> 16) & 3) << 1) | flags | (down ? 0x80 : 0));
    gha(ins);
}

static void gha_line(u8 opcode, u8 low, u8 mask, u8 end, u32 count, u32 addr, u32 pitch, u8 rot, int err, u32 inc, int dec, u8 fg0, u8 fg1) {
    u8 ins[16];
    ins[0] = (u8) ((opcode << 5) | low);
    ins[1] = mask;
    ins[2] = (u8) dec;
    ins[3] = (u8) (dec >> 8);
    ins[4] = fg0;
    ins[5] = fg1;
    ins[6] = end;
    ins[7] = (u8) count;
    ins[8] = (u8) addr;
    ins[9] = (u8) (addr >> 8);
    ins[10] = (u8) err;
    ins[11] = (u8) (err >> 8);
    ins[12] = (u8) pitch;
    ins[13] = (u8) (((pitch >> 8) & 1) | (((addr >> 16) & 3) << 1) | ((rot & 7) << 3) | (((count >> 8) & 3) << 6));
    ins[14] = (u8) inc;
    ins[15] = (u8) ((inc >> 8) & 0x3f);
    gha(ins);
}

/* The screen's lines of 1024 bytes (native 8 bits a pixel), all the GHA draws on */
#define GHA_ROW 256u /* longwords a line */
static void gha_clear(u32 salt) {
    volatile u32 *p = (volatile u32 *) vga_bytes;
    for (u32 i = 0; i < GHA_ROW * 470; i++)
        p[i] = pattern(i % GHA_ROW, i / GHA_ROW, salt);
}

static void gha_passes(void) {
    static const u8 modes[3] = { 0x00, 0x10, 0x30 }; /* GDC 0Ch: planar, packed 8, packed 16 */
    for (u32 m = 0; m < 3; m++) {
        for (u32 pass = 0; pass < 2; pass++) {
            gha_clear(0x70 + m * 2 + pass);
            /* The queue on the screen's last lines */
            queue_at = 118u << 10;
            queue_tail = 0;
            gdc(0x09, (u8) (queue_at >> 10));
            gdc(0x0b, 0);
            gdc(0x0a, 0);
            outb(0x3c4, 0x06);
            outb(0x3c5, inb(0x3c5) | 0x40); /* the GHA on */
            gdc(0x0c, modes[m]);
            gdc(0x0d, (u8) (pass ? 0xf3 : 0xff));
            gdc(0x0e, 0x12);
            gdc(0x0f, 0x34);
            /* Short and long copies, rotated, apart */
            const u32 row = GHA_ROW;
            for (u32 k = 0; k < 8; k++) {
                const u32 dst = (10 + k * 22) * row + 2 + (k & 3) * 19;
                const u32 src = (100 + k * 11) * row + 4 + k;
                const u8  low = (u8) ((pass ? k : (k & 3)) | ((m == 0) ? 0x0f : 0));
                gha_blit((u8) (k & 1), low, 0xff, 0xff, (u8) ((k & 2) ? 0xf0 : 0xff), (u8) ((m == 0) ? 0x30 : 0x5a), 0x21,
                         12, 18, dst, src, row - 13, (u8) (k & 3), 0, 0);
            }
            /* Moves, partial start and end masks */
            for (u32 k = 0; k < 4; k++) {
                const u32 dst = 110 * row + 30 + k * 12;
                gha_blit((u8) (2 + (k & 1)), 0x0f, (u8) (0xf0 >> (k & 3)), (u8) (0xf0 << (k & 3)), 0xff, 0xc0, 0x00,
                         9, 40, dst, 3 * row + k, row - 10, (u8) k, 0, 0);
            }
            /* Overlapping: down, and up with the DIR bit */
            gha_blit(3, 0x0f, 0xff, 0xff, 0xff, 0, 0, 20, 30, 40 * row + 34, 44 * row + 30, row - 21, 0, 0, 0);
            gha_blit(3, 0x0f, 0xff, 0xff, 0xff, 0, 0, 20, 30, 190 * row + 70, 186 * row + 66, 512u + 21u - row, 0, 0, 1);
            /* Expansions: a planar plane's byte; packed colour from bits, and the pattern fill */
            if (m == 0)
                gha_blit(3, 0x0f, 0xff, 0xff, 0xff, 0, 0, 10, 16, 150 * row + 2, 20 * row + 2, row - 11, 0, 0x20 | 0x08, 0);
            else {
                gha_blit(2, 0x00, 0xff, 0xff, 0xff, 0x5a, 0xa5, 10, 16, 150 * row + 2, 20 * row + 2, row - 11, 0, 0x20, 0);
                gha_blit(0, 0x03, 0xff, 0xff, 0xff, 0x77, 0x11, 10, 16, 150 * row + 22, 20 * row + 2, row - 11, 0, 0x30, 0);
            }
            /* Lines: flat, steep */
            for (u32 k = 0; k < 4; k++) {
                const u32 addr = (5 + k * 15) * row + 40;
                gha_line(4, (m == 0) ? 0x0f : 0x00, (m == 0) ? 0x80 : 0xc0, 0xff, 8 + k, addr, row, (m == 0) ? 1 : (m == 1) ? 2 : 4, -41, 12, -82, 0x7e, 0x3c);
                gha_line(5, (m == 0) ? 0x05 : 0x00, (m == 0) ? 0x10 : 0x30, 0xff, 30 + k * 4, addr + 20, row, 0, -31, 20, -62, 0x55, 0xaa);
            }
            wait_ticks(4);
            outb(0x3c4, 0x06);
            outb(0x3c5, inb(0x3c5) & ~0x40);
        }
    }
    gdc(0x0c, 0);
}

void test_main(void) {
    __asm__ volatile("fninit");
    u32 bus = 0, dev = 0;
    int found = 0;
    for (bus = 0; bus < 2 && !found; bus++)
        for (dev = 0; dev < 32 && !found; dev++) {
            outl(0xcf8, pci_addr(bus, dev, 0));
            if (inl(0xcfc) == 0x9100100eu) {
                found = 1;
                break;
            }
        }
    if (!found)
        return;
    bus--;
    outl(0xcf8, pci_addr(bus, dev, 0x10));
    const u32 base = inl(0xcfc) & 0xff000000u;
    regs = (volatile u32 *) base;
    fb   = (volatile u32 *) (base + 0x800000u);

    /* Native mode: CONFIG 65's mode select clear */
    outl(0xcf8, pci_addr(bus, dev, 0x40));
    outb(0xcfd, 0x00);
    static const u32 sizes[] = { 1, 2, 4, 3 };
    for (u32 s = 0; s < 4; s++) {
        native_mode(sizes[s]);
        windows_open();
        const u32 salt = 0x40 + s * 8;
        clear(salt);
        p_quads(sizes[s], salt);
        wait_ticks(4);
        clear(salt + 1);
        p_patterns(sizes[s], salt + 1);
        wait_ticks(4);
        clear(salt + 2);
        p_blits(sizes[s], salt + 2);
        wait_ticks(4);
        clear(salt + 3);
        p_pixels(sizes[s], salt + 3);
        wait_ticks(4);
    }
    /* The GHA, its work shown by native mode at 8 bits a pixel, which scans memory as it lies */
    native_mode(1);
    vga_bytes = (u8 *) (base + 0x800000u);
    /* The extended registers unlocked: two writes, then the real one */
    outb(0x3c4, 0x11);
    const u8 misc = inb(0x3c5) & (u8) ~0x20u;
    outb(0x3c5, misc);
    outb(0x3c5, misc);
    outb(0x3c5, misc);
    gha_passes();
}
