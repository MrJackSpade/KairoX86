/*
 * KairoX86's Voodoo Banshee / Voodoo3 3D test (KairoX86#283, for #278): on a 3dfx Banshee or Voodoo3 (PCI
 * vendor 121Ah), VESA mode 640 x 480 x 16 set, the 3D engine pointed at the displayed buffer (a depth
 * buffer after it), and a fixed sequence drawn through the 3D registers: a fast fill; Gouraud
 * triangles; overlapping triangles depth tested against iterated Z; alpha blended ones; each set
 * dithered and not. The engine is waited for after each set, and each picture held four ticks of the BIOS
 * clock. Any other card returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

/* PCI configuration mechanism 1 */
static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg & 0xfc));
    return inl(0xcfc);
}

/* The 3D registers (vid_voodoo_regs.h) */
enum {
    VERTEX_AX = 0x008, VERTEX_AY = 0x00c, VERTEX_BX = 0x010, VERTEX_BY = 0x014, VERTEX_CX = 0x018, VERTEX_CY = 0x01c,
    START_R = 0x020, START_G = 0x024, START_B = 0x028, START_Z = 0x02c, START_A = 0x030,
    DRDX = 0x040, DGDX = 0x044, DBDX = 0x048, DZDX = 0x04c, DADX = 0x050,
    DRDY = 0x060, DGDY = 0x064, DBDY = 0x068, DZDY = 0x06c, DADY = 0x070,
    TRIANGLE_CMD = 0x080, FBZ_COLOR_PATH = 0x104, FOG_MODE = 0x108, ALPHA_MODE = 0x10c, FBZ_MODE = 0x110,
    CLIP_LEFT_RIGHT = 0x118, CLIP_LOW_Y_HIGH_Y = 0x11c, NOP_CMD = 0x120, FASTFILL_CMD = 0x124,
    ZA_COLOR = 0x130, COLOR1 = 0x148, COL_BUFFER_ADDR = 0x1ec, COL_BUFFER_STRIDE = 0x1f0,
    AUX_BUFFER_ADDR = 0x1f4, AUX_BUFFER_STRIDE = 0x1f8, STATUS = 0x000,
};

/* fbzMode bits */
#define FBZ_CLIP       (1u << 0)
#define FBZ_DEPTH      (1u << 4)
#define FBZ_DEPTH_LESS (1u << 5) /* depth function 1: less than */
#define FBZ_DITHER     (1u << 8)
#define FBZ_RGB_WRITE  (1u << 9)
#define FBZ_AUX_WRITE  (1u << 10)

static volatile u32 *regs;

static void reg(u32 offset, u32 value) {
    regs[offset / 4] = value;
}

/* Waits until the engine has drawn everything sent (status bit 9: busy) */
static void idle(void) {
    reg(NOP_CMD, 0);
    for (int stable = 0; stable < 3;) {
        if (regs[STATUS / 4] & (1u << 9))
            stable = 0;
        else
            stable++;
    }
}

typedef struct {
    float x, y, r, g, b, a, z;
} vertex_t;

/* A parameter's gradients across a triangle (its plane), in 12.12 fixed point times scale */
static void gradient(const vertex_t *v, const float *p, float area, float scale, u32 *start, u32 *dx, u32 *dy) {
    const float d1 = p[1] - p[0];
    const float d2 = p[2] - p[0];
    const float gx = (d1 * (v[2].y - v[0].y) - d2 * (v[1].y - v[0].y)) / area;
    const float gy = (d2 * (v[1].x - v[0].x) - d1 * (v[2].x - v[0].x)) / area;
    *start = (u32) (int) (p[0] * scale);
    *dx    = (u32) (int) (gx * scale);
    *dy    = (u32) (int) (gy * scale);
}

/* One triangle, its vertices in order of y */
static void triangle(const vertex_t *v) {
    const float area = (v[1].x - v[0].x) * (v[2].y - v[0].y) - (v[2].x - v[0].x) * (v[1].y - v[0].y);
    if (area == 0)
        return;
    reg(VERTEX_AX, (u32) (int) (v[0].x * 16));
    reg(VERTEX_AY, (u32) (int) (v[0].y * 16));
    reg(VERTEX_BX, (u32) (int) (v[1].x * 16));
    reg(VERTEX_BY, (u32) (int) (v[1].y * 16));
    reg(VERTEX_CX, (u32) (int) (v[2].x * 16));
    reg(VERTEX_CY, (u32) (int) (v[2].y * 16));
    static const u32 starts[5] = { START_R, START_G, START_B, START_A, START_Z };
    static const u32 dxs[5]    = { DRDX, DGDX, DBDX, DADX, DZDX };
    static const u32 dys[5]    = { DRDY, DGDY, DBDY, DADY, DZDY };
    for (int k = 0; k < 5; k++) {
        float p[3];
        for (int i = 0; i < 3; i++)
            p[i] = (k == 0) ? v[i].r : (k == 1) ? v[i].g : (k == 2) ? v[i].b : (k == 3) ? v[i].a : v[i].z;
        u32 s;
        u32 gx;
        u32 gy;
        gradient(v, p, area, 4096.0f, &s, &gx, &gy);
        reg(starts[k], s);
        reg(dxs[k], gx);
        reg(dys[k], gy);
    }
    reg(TRIANGLE_CMD, (area < 0) ? 0x80000000u : 0);
}

/* A fan of triangles across the screen, each its own colours, depth and alpha from the pattern */
static void triangles(u32 salt, int count) {
    for (int i = 0; i < count; i++) {
        const u32 h  = pattern((u32) i, 7, salt);
        const float cx = (float) (40 + (h % 560));
        const float cy = (float) (40 + ((h >> 10) % 400));
        const float s  = (float) (30 + ((h >> 20) % 90));
        vertex_t    v[3] = {
            { cx, cy - s, (float) (h & 255), (float) ((h >> 8) & 255), (float) ((h >> 16) & 255), 255.0f, 1000.0f },
            { cx - s, cy + s * 0.5f, (float) ((h >> 24) & 255), 40.0f, 200.0f, 128.0f, 30000.0f + (float) (h & 4095) },
            { cx + s * 0.8f, cy + s, 250.0f, (float) ((h >> 4) & 255), 10.0f, 30.0f, 60000.0f },
        };
        triangle(v);
    }
}

void test_main(void) {
    __asm__ volatile("fninit");
    /* The card: on bus 0 (PCI) or behind the AGP bridge (bus 1) */
    u32 mmio = 0;
    for (u32 bus = 0; bus < 2 && !mmio; bus++)
        for (u32 dev = 0; dev < 32 && !mmio; dev++) {
            const u32 id = pci_read(bus, dev, 0, 0);
            if ((id & 0xffff) == 0x121a && ((id >> 16) == 0x0003 || (id >> 16) == 0x0005 || (id >> 16) == 0x0004))
                mmio = pci_read(bus, dev, 0, 0x10) & ~0xfu;
        }
    if (!mmio)
        return;
    /* 640 x 480 x 16 with its linear framebuffer, the displayed buffer at the framebuffer's start */
    if (int10(0x4f02, 0x4111, 0, 0, 0, 0) != 0x004f)
        return;
    regs = (volatile u32 *) (mmio + 0x200000);
    reg(COL_BUFFER_ADDR, 0);
    reg(COL_BUFFER_STRIDE, 1280);
    reg(AUX_BUFFER_ADDR, 0x100000);
    reg(AUX_BUFFER_STRIDE, 1280);
    reg(CLIP_LEFT_RIGHT, (0u << 16) | 640);
    reg(CLIP_LOW_Y_HIGH_Y, (0u << 16) | 480);
    reg(FOG_MODE, 0);

    for (int dither = 0; dither < 2; dither++) {
        const u32 d = dither ? FBZ_DITHER : 0;
        /* A fast fill: colour and depth */
        reg(COLOR1, 0x00203040);
        reg(ZA_COLOR, 0xffff);
        reg(FBZ_MODE, FBZ_CLIP | FBZ_RGB_WRITE | FBZ_AUX_WRITE | d);
        reg(FASTFILL_CMD, 0);
        idle();
        wait_ticks(4);

        /* Gouraud: iterated colour straight through the colour combine unit */
        reg(FBZ_COLOR_PATH, 0);
        reg(ALPHA_MODE, 0);
        reg(FBZ_MODE, FBZ_CLIP | FBZ_RGB_WRITE | d);
        triangles(0x31 + (u32) dither, 24);
        idle();
        wait_ticks(4);

        /* Depth: iterated Z tested less-than and written */
        reg(FBZ_MODE, FBZ_CLIP | FBZ_RGB_WRITE | FBZ_AUX_WRITE | FBZ_DEPTH | FBZ_DEPTH_LESS | d);
        triangles(0x47 + (u32) dither, 24);
        idle();
        wait_ticks(4);

        /* Alpha blending: source alpha over the destination (alphaMode: blend on, src factor 1 = source
           alpha, destination factor 5 = one minus source alpha) */
        reg(ALPHA_MODE, (1u << 4) | (1u << 8) | (5u << 12));
        reg(FBZ_MODE, FBZ_CLIP | FBZ_RGB_WRITE | d);
        triangles(0x59 + (u32) dither, 24);
        idle();
        wait_ticks(4);
    }
    reg(ALPHA_MODE, 0);
}
