/*
 * KairoX86's S3 ViRGE 3D test (KairoX86#283, for #272): on an S3 ViRGE or Trio3D (PCI 5333h: 5631h, 883Dh,
 * 8A01h, 8A10h, 8A13h), VESA mode 110h (640 x 480 x 15) set with S3's linear addressing (CR58), the new
 * MMIO window on (CR53 bit 3), a texture area
 * filled with a pattern through the linear frame buffer, and a series of passes drawn through the 3D
 * triangle registers (B4D4h on), each a fan of triangles of both directions over a clear, held four ticks
 * of the BIOS clock: Gouraud; each Z function, with and without updates; the three texture formats,
 * wrapped and bordered; plain, mipmapped, filtered and perspective-corrected sampling; the lit modes
 * (reflection, modulate, decal) and unlit; fog; alpha blending from the texture and from the iterated
 * alpha; the hard clip rectangle, a triangle across its bottom edge among them (#292). The engine's
 * busy bit is never read (as in v3d.c). Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    return inl(0xcfc);
}

static volatile u32 *mmio;

static void reg(u32 offset, u32 value) { mmio[offset / 4] = value; }

/* The 3D triangle registers */
enum {
    Z_BASE = 0xb4d4, DEST_BASE = 0xb4d8, CLIP_LR = 0xb4dc, CLIP_TB = 0xb4e0, DEST_SRC_STR = 0xb4e4, Z_STR = 0xb4e8,
    TEX_BASE = 0xb4ec, TEX_BDR = 0xb4f0, FOG_CLR = 0xb4f4, CMD_SET = 0xb500, TBV = 0xb504, TBU = 0xb508,
    WDX = 0xb50c, WDY = 0xb510, WS = 0xb514, DDX = 0xb518, VDX = 0xb51c, UDX = 0xb520, DDY = 0xb524, VDY = 0xb528,
    UDY = 0xb52c, DS = 0xb530, VS = 0xb534, US = 0xb538, GBX = 0xb53c, ARX = 0xb540, GBY = 0xb544, ARY = 0xb548,
    GBS = 0xb54c, ARS = 0xb550, ZDX = 0xb554, ZDY = 0xb558, ZS = 0xb55c, XDY12 = 0xb560, XEND12 = 0xb564,
    XDY01 = 0xb568, XEND01 = 0xb56c, XDY02 = 0xb570, XS = 0xb574, YS = 0xb578, Y01_Y12_LR = 0xb57c,
};

/* cmd_set */
#define AE (1u << 0)
#define HC (1u << 1)
#define FMT16 (1u << 2)
#define TEX8888 (0u << 5)
#define TEX4444 (1u << 5)
#define TEX1555 (2u << 5)
#define MAXD(d) ((u32) (d) << 8)
#define FILT(f) ((u32) (f) << 12) /* 0-1 mipmap, 2-3 mipmap filtered, 4-5 plain, 6-7 plain filtered */
#define LIT(m) ((u32) (m) << 15)  /* 0 reflection, 1 modulate, 2 decal */
#define FE (1u << 17)
#define ABC_SRC (1u << 18)
#define ABC (1u << 19)
#define ZFUNC(f) ((u32) (f) << 20)
#define ZUP (1u << 23)
#define NOZ (3u << 24)
#define TWE (1u << 26)
#define CMD(c) ((u32) (c) << 27) /* 0 Gouraud, 1 lit texture, 2 unlit, 5 lit perspective, 6 unlit perspective */

typedef struct {
    float x, y;
    float r, g, b, a, z, u, v, w, d;
} vertex_t;

/* An attribute's plane: its gradients across x and y */
static void plane(const vertex_t *v, float a0, float a1, float a2, float *gx, float *gy) {
    const float area = (v[1].x - v[0].x) * (v[2].y - v[0].y) - (v[2].x - v[0].x) * (v[1].y - v[0].y);
    const float d1   = a1 - a0;
    const float d2   = a2 - a0;
    *gx = (d1 * (v[2].y - v[0].y) - d2 * (v[1].y - v[0].y)) / area;
    *gy = (d2 * (v[1].x - v[0].x) - d1 * (v[2].x - v[0].x)) / area;
}

static int fx20(float x) { return (int) (x * 1048576.0f); }

/* One triangle: v[0] the lowest on screen (the largest y), drawn upward line by line */
static void triangle(const vertex_t *in, u32 cmd) {
    vertex_t v[3] = { in[0], in[1], in[2] };
    for (int a = 0; a < 2; a++)
        for (int b = 0; b < 2 - a; b++)
            if (v[b].y < v[b + 1].y) {
                const vertex_t t = v[b];
                v[b]             = v[b + 1];
                v[b + 1]         = t;
            }
    const int y0 = (int) v[0].y, y1 = (int) v[1].y, y2 = (int) v[2].y;
    if (y0 == y2)
        return;
    /* Edges' x at the start line, and per line upward */
    const float d02 = (v[2].x - v[0].x) / (v[0].y - v[2].y);
    const float d01 = (y0 != y1) ? (v[1].x - v[0].x) / (v[0].y - v[1].y) : 0.0f;
    const float d12 = (y1 != y2) ? (v[2].x - v[1].x) / (v[1].y - v[2].y) : 0.0f;
    const float xs  = v[0].x + d02 * (v[0].y - (float) y0);
    const float xe1 = v[0].x + d01 * (v[0].y - (float) y0);
    const float xe2 = v[1].x + d12 * (v[1].y - (float) y1);
    /* The long edge left of the short ones: drawn left to right */
    const float xmid = v[0].x + d02 * (v[0].y - v[1].y);
    const u32   lr   = (xmid < v[1].x) ? 1u : 0u;

    float gx, gy;
    const float  dyv = (float) y0 - v[0].y;
    const float  dxv = xs - v[0].x;
#define ATTR(field, scale, start_reg, dx_reg, dy_reg, mask)                                       \
    plane(v, v[0].field, v[1].field, v[2].field, &gx, &gy);                                       \
    reg(start_reg, ((u32) (int) ((v[0].field + gx * dxv + gy * dyv) * (scale))) & (mask));       \
    reg(dx_reg, (u32) (int) (gx * (scale)));                                                      \
    reg(dy_reg, (u32) (int) (-gy * (scale)))
    ATTR(u, 1.0f, US, UDX, UDY, 0xffffffffu);
    ATTR(v, 1.0f, VS, VDX, VDY, 0xffffffffu);
    ATTR(w, 1.0f, WS, WDX, WDY, 0xffffffffu);
    ATTR(d, 1.0f, DS, DDX, DDY, 0xffffffffu);
    ATTR(z, 32768.0f, ZS, ZDX, ZDY, 0xffffffffu);
#undef ATTR
    /* Colours and alpha: 8.7, the X and Y gradients two to a register */
    float rx, ry, gxx, gyy, bx, by, ax, ay;
    plane(v, v[0].r, v[1].r, v[2].r, &rx, &ry);
    plane(v, v[0].g, v[1].g, v[2].g, &gxx, &gyy);
    plane(v, v[0].b, v[1].b, v[2].b, &bx, &by);
    plane(v, v[0].a, v[1].a, v[2].a, &ax, &ay);
#define C16(x) (((u32) (int) ((x) * 128.0f)) & 0xffffu)
    reg(GBX, (C16(gxx) << 16) | C16(bx));
    reg(ARX, (C16(ax) << 16) | C16(rx));
    reg(GBY, (C16(-gyy) << 16) | C16(-by));
    reg(ARY, (C16(-ay) << 16) | C16(-ry));
    reg(GBS, (C16(v[0].g + gxx * dxv + gyy * dyv) << 16) | C16(v[0].b + bx * dxv + by * dyv));
    reg(ARS, (C16(v[0].a + ax * dxv + ay * dyv) << 16) | C16(v[0].r + rx * dxv + ry * dyv));
#undef C16
    reg(XDY12, (u32) fx20(d12));
    reg(XEND12, (u32) fx20(xe2));
    reg(XDY01, (u32) fx20(d01));
    reg(XEND01, (u32) fx20(xe1));
    reg(XDY02, (u32) fx20(d02));
    reg(XS, (u32) fx20(xs));
    reg(YS, (u32) y0);
    reg(CMD_SET, cmd | AE);
    reg(Y01_Y12_LR, (lr << 31) | ((u32) (y0 - y1) << 16) | (u32) (y1 - y2));
}

static void triangles(u32 salt, int count, u32 cmd, int across_bottom) {
    for (int i = 0; i < count; i++) {
        const u32   h  = pattern((u32) i, 13, salt);
        const float cx = (float) (30 + (h % 580));
        const float cy = (across_bottom && i == 0) ? 430.0f : (float) (30 + ((h >> 10) % 420));
        const float s  = (float) (24 + ((h >> 20) % 110));
        vertex_t    v[3];
        const float px[3] = { cx, cx - s, cx + s * 0.8f };
        const float py[3] = { cy - s, cy + s * 0.5f, cy + s };
        for (int j = 0; j < 3; j++) {
            const u32 g = pattern((u32) i, (u32) j, salt ^ 0x3c3c);
            v[j].x = px[j];
            v[j].y = py[j];
            v[j].r = (float) ((g >> 3) & 255);
            v[j].g = (float) ((g >> 11) & 255);
            v[j].b = (float) ((g >> 19) & 255);
            v[j].a = (float) ((g >> 7) & 255);
            v[j].z = (float) (1000 + (g % 60000));
            v[j].u = (float) (g & 0xffff) * 4096.0f;
            v[j].v = (float) ((g >> 16) & 0xffff) * 4096.0f;
            v[j].w = (float) (0x100000 + (g % 0x300000));
            v[j].d = (float) ((g >> 5) % 4) * 134217728.0f;
        }
        if (h & 1) {
            const vertex_t t = v[1];
            v[1]             = v[2];
            v[2]             = t;
        }
        triangle(v, cmd);
    }
}

static const u32 passes[] = {
    CMD(0) | FMT16 | NOZ,
    CMD(0) | FMT16 | ZFUNC(1) | ZUP,
    CMD(0) | FMT16 | ZFUNC(4) | ZUP,
    CMD(0) | FMT16 | ZFUNC(3),
    CMD(0) | FMT16 | ZFUNC(6) | ZUP | FE,
    CMD(2) | FMT16 | NOZ | TEX1555 | MAXD(8) | FILT(4) | TWE,
    CMD(2) | FMT16 | NOZ | TEX4444 | MAXD(7) | FILT(6) | TWE,
    CMD(2) | FMT16 | NOZ | TEX8888 | MAXD(6) | FILT(4),
    CMD(2) | FMT16 | NOZ | TEX1555 | MAXD(8) | FILT(0) | TWE,
    CMD(2) | FMT16 | NOZ | TEX1555 | MAXD(8) | FILT(2) | TWE,
    CMD(1) | FMT16 | NOZ | TEX1555 | MAXD(8) | FILT(4) | LIT(0) | TWE,
    CMD(1) | FMT16 | NOZ | TEX4444 | MAXD(8) | FILT(6) | LIT(1) | TWE,
    CMD(1) | FMT16 | ZFUNC(1) | ZUP | TEX1555 | MAXD(8) | FILT(4) | LIT(2),
    CMD(6) | FMT16 | NOZ | TEX1555 | MAXD(8) | FILT(4) | TWE,
    CMD(6) | FMT16 | NOZ | TEX4444 | MAXD(8) | FILT(2) | TWE,
    CMD(5) | FMT16 | NOZ | TEX1555 | MAXD(8) | FILT(6) | LIT(1) | TWE | FE,
    CMD(2) | FMT16 | NOZ | TEX4444 | MAXD(8) | FILT(4) | TWE | ABC,
    CMD(0) | FMT16 | NOZ | ABC | ABC_SRC,
    CMD(1) | FMT16 | NOZ | TEX4444 | MAXD(8) | FILT(4) | LIT(1) | TWE | ABC | ABC_SRC | FE,
    CMD(0) | FMT16 | NOZ | HC,
    CMD(2) | FMT16 | ZFUNC(1) | ZUP | TEX1555 | MAXD(8) | FILT(6) | TWE | HC,
};

void test_main(void) {
    __asm__ volatile("fninit");
    u32 lfb = 0;
    for (u32 bus = 0; bus < 2 && !lfb; bus++)
        for (u32 dev = 0; dev < 32 && !lfb; dev++) {
            const u32 id = pci_read(bus, dev, 0, 0);
            const u32 d  = id >> 16;
            if (((id & 0xffff) == 0x5333) && ((d == 0x5631) || (d == 0x883d) || (d == 0x8a01) || (d == 0x8a10) || (d == 0x8a13)))
                lfb = pci_read(bus, dev, 0, 0x10) & ~0xfu;
        }
    if (!lfb)
        return;
    /* VESA 640 x 480, 15 bits a pixel (the 3D engine's 16-bit format); the S3 BIOS's VBE gives no linear
       frame buffer, so S3's own linear addressing is turned on (CR58 bit 4, a 4 MB window) */
    if (int10(0x4f02, 0x110, 0, 0, 0, 0) != 0x004f) {
        *(volatile u16 *) 0xb8000 = 0x4f56;
        wait_ticks(40);
        return;
    }
    /* The S3 extensions unlocked, the new MMIO window on (CR53 bit 3: linear base + 16 MB) */
    outb(0x3d4, 0x38);
    outb(0x3d5, 0x48);
    outb(0x3d4, 0x39);
    outb(0x3d5, 0xa5);
    outb(0x3d4, 0x58);
    const u8 cr58 = inb(0x3d5);
    outb(0x3d5, (cr58 & ~0x03) | 0x13);
    outb(0x3d4, 0x53);
    const u8 cr53 = inb(0x3d5);
    outb(0x3d5, cr53 | 0x08);
    mmio = (volatile u32 *) (lfb + 0x1000000);

    /* The texture area, 2 MB to 3 MB: the pattern */
    volatile u32 *tex = (volatile u32 *) (lfb + 0x200000);
    for (u32 i = 0; i < 0x40000; i++)
        tex[i] = pattern(i & 1023, i >> 10, 0x51);

    reg(DEST_BASE, 0);
    reg(Z_BASE, 0x100000);
    reg(DEST_SRC_STR, (1280u << 16) | 1280u);
    reg(Z_STR, 1280);
    reg(TEX_BASE, 0x200000);
    reg(TEX_BDR, 0x00406080);
    reg(FOG_CLR, 0x00c08040);
    reg(TBU, 0x123);
    reg(TBV, 0x456);

    for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
        /* The clear: the frame and the Z buffer through the linear frame buffer */
        volatile u32 *fb = (volatile u32 *) lfb;
        const u32     c  = pattern(p, 0, 0x99) & 0x7fff7fffu;
        for (u32 i = 0; i < 640 * 480 / 2; i++)
            fb[i] = c;
        volatile u32 *zb = (volatile u32 *) (lfb + 0x100000);
        const u32     zc = (p & 1) ? 0x80008000u : 0x40004000u;
        for (u32 i = 0; i < 640 * 480 / 2; i++)
            zb[i] = zc;
        const int hc = (passes[p] & HC) != 0;
        reg(CLIP_LR, hc ? ((60u << 16) | 580u) : ((0u << 16) | 639u));
        reg(CLIP_TB, hc ? ((40u << 16) | 440u) : ((0u << 16) | 479u));
        triangles(0x700 + p, 20, passes[p] | HC, hc);
        wait_ticks(4);
    }
}
