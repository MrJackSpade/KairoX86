/*
 * The Voodoo 3D pipeline passes KairoX86's 3D tests share (KairoX86#283, for #277 and #278): the 3D
 * registers, triangles from the pattern, the passes, and run_passes(), which draws them once the card is
 * set up (its buffers, its textures' memory filled): v3dtex.c on the Banshee family, v12tex.c on the
 * Voodoo Graphics and Voodoo2. regs points at the 3D registers.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#pragma once
#include "runtime.h"

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg & 0xfc));
    return inl(0xcfc);
}

/* The 3D registers (vid_voodoo_regs.h), with the chip select of bits 10 to 13: 0 every chip */
enum {
    STATUS = 0x000, VERTEX_AX = 0x008, TRIANGLE_CMD = 0x080, FBZ_COLOR_PATH = 0x104, FOG_MODE = 0x108,
    ALPHA_MODE = 0x10c, FBZ_MODE = 0x110, CLIP_LEFT_RIGHT = 0x118, CLIP_LOW_Y_HIGH_Y = 0x11c, NOP_CMD = 0x120,
    FASTFILL_CMD = 0x124, FOG_COLOR = 0x12c, ZA_COLOR = 0x130, CHROMA_KEY = 0x134, STIPPLE = 0x140,
    COLOR0 = 0x144, COLOR1 = 0x148, FOG_TABLE = 0x160, COL_BUFFER_ADDR = 0x1ec, COL_BUFFER_STRIDE = 0x1f0,
    AUX_BUFFER_ADDR = 0x1f4, AUX_BUFFER_STRIDE = 0x1f8, TEXTURE_MODE = 0x300, TLOD = 0x304, TDETAIL = 0x308,
    TEX_BASE_ADDR = 0x30c,
};
enum { CHIP_TMU0 = 0x800, CHIP_TMU1 = 0x1000 };
/* The parameters' start, X and Y gradient registers: R G B Z A S T W */
static const u16 starts[8] = { 0x020, 0x024, 0x028, 0x02c, 0x030, 0x034, 0x038, 0x03c };

static volatile u32 *regs;

static void reg(u32 offset, u32 value) { regs[offset / 4] = value; }

/* A vertex: position, colour, alpha, Z, and each TMU's S, T, W (texels of LOD 0 and W, both before the
   division the perspective correction does) */
typedef struct {
    float x, y;
    float p[8];  /* r g b z a s t w: the FBI's and TMU0's */
    float q[3];  /* TMU1's s t w */
} vertex_t;

/* Fixed-point scales of the registers: colours and alpha 12.12, Z 20.12, S and T 14.18, W 2.30 */
static const float scale[8] = { 4096.0f, 4096.0f, 4096.0f, 4096.0f, 4096.0f, 262144.0f, 262144.0f, 1073741824.0f };

static void plane(const vertex_t *v, const float *a, float area, float k, u32 *s, u32 *gx, u32 *gy) {
    const float d1 = a[1] - a[0];
    const float d2 = a[2] - a[0];
    *s  = (u32) (int) (a[0] * k);
    *gx = (u32) (int) ((d1 * (v[2].y - v[0].y) - d2 * (v[1].y - v[0].y)) / area * k);
    *gy = (u32) (int) ((d2 * (v[1].x - v[0].x) - d1 * (v[2].x - v[0].x)) / area * k);
}

static int dual;

static void triangle(const vertex_t *v) {
    const float area = (v[1].x - v[0].x) * (v[2].y - v[0].y) - (v[2].x - v[0].x) * (v[1].y - v[0].y);
    if (area == 0)
        return;
    for (int i = 0; i < 3; i++) {
        reg(VERTEX_AX + i * 8, (u32) (int) (v[i].x * 16));
        reg(VERTEX_AX + i * 8 + 4, (u32) (int) (v[i].y * 16));
    }
    for (int k = 0; k < 8; k++) {
        float a[3];
        u32   s, gx, gy;
        for (int i = 0; i < 3; i++)
            a[i] = v[i].p[k];
        plane(v, a, area, scale[k], &s, &gx, &gy);
        reg(starts[k], s);
        reg(starts[k] + 0x20, gx);
        reg(starts[k] + 0x40, gy);
    }
    if (dual) {
        for (int k = 0; k < 3; k++) {
            float a[3];
            u32   s, gx, gy;
            for (int i = 0; i < 3; i++)
                a[i] = v[i].q[k];
            plane(v, a, area, scale[5 + k], &s, &gx, &gy);
            reg(CHIP_TMU1 | starts[5 + k], s);
            reg(CHIP_TMU1 | (starts[5 + k] + 0x20), gx);
            reg(CHIP_TMU1 | (starts[5 + k] + 0x40), gy);
        }
    }
    reg(TRIANGLE_CMD, (area < 0) ? 0x80000000u : 0);
}

/* A fan of triangles from the pattern, half of them wound the other way; perspective varies W from
   near to far across each */
static void triangles(u32 salt, int count, int perspective) {
    for (int i = 0; i < count; i++) {
        const u32   h  = pattern((u32) i, 11, salt);
        const float cx = (float) (30 + (h % 580));
        const float cy = (float) (30 + ((h >> 10) % 420));
        const float s  = (float) (24 + ((h >> 20) % 110));
        vertex_t    v[3];
        const float px[3] = { cx, cx - s, cx + s * 0.8f };
        const float py[3] = { cy - s, cy + s * 0.5f, cy + s };
        for (int j = 0; j < 3; j++) {
            const u32 g = pattern((u32) i, (u32) j, salt ^ 0x5a5a);
            const float w = perspective ? (0.25f + (float) (g % 1500) / 1000.0f) : 1.0f;
            const float ts = (float) (g & 1023) - 256.0f;
            const float tt = (float) ((g >> 10) & 1023) - 256.0f;
            v[j].x    = px[j];
            v[j].y    = py[j];
            v[j].p[0] = (float) ((g >> 3) & 255);
            v[j].p[1] = (float) ((g >> 11) & 255);
            v[j].p[2] = (float) ((g >> 19) & 255);
            v[j].p[3] = (float) (1000 + (g % 60000));
            v[j].p[4] = (float) ((g >> 7) & 255);
            v[j].p[5] = ts * w;
            v[j].p[6] = tt * w;
            v[j].p[7] = w;
            v[j].q[0] = tt * 0.5f * w;
            v[j].q[1] = ts * 1.5f * w;
            v[j].q[2] = w;
        }
        /* The other winding: B and C swapped keep A on top */
        if (h & 1) {
            const vertex_t t = v[1];
            v[1]             = v[2];
            v[2]             = t;
        }
        /* In order of y */
        for (int a = 0; a < 2; a++)
            for (int b = 0; b < 2 - a; b++)
                if (v[b].y > v[b + 1].y) {
                    const vertex_t t = v[b];
                    v[b]             = v[b + 1];
                    v[b + 1]         = t;
                }
        triangle(v);
    }
}

/* fbzMode bits */
#define CLIP (1u << 0)
#define CHROMA (1u << 1)
#define STIP (1u << 2)
#define WBUF (1u << 3)
#define DEPTH (1u << 4)
#define DLESS (1u << 5)
#define DITHER (1u << 8)
#define RGB_W (1u << 9)
#define AUX_W (1u << 10)
#define DITHER2 (1u << 11)
#define STIP_PATT (1u << 12)
#define DBIAS (1u << 16)
#define YFLIP (1u << 17)
#define ALPHA_BUF (1u << 18)
#define DSUB (1u << 19)
#define DSRC (1u << 20)

/* fbzColorPath: rgb and alpha from the texture, texturing on */
#define CP_TEX ((1u << 27) | 1u | (1u << 2))
/* textureMode: the formats, and TMU0's combine "local" (its texel as it is) */
#define FMT_565 (0xau << 8)
#define FMT_4444 (0xcu << 8)
#define TC_LOCAL 0x00241000u
#define PERSP 1u
#define BILINEAR 6u
#define CLAMP_ST (3u << 6)
#define TRILINEAR (1u << 30)

typedef struct {
    u32 fbz, cp, alpha, fog, tex0, lod0, tex1, lod1, detail;
    u8  perspective, dual;
} pass_t;

#define LOD(min, max) ((u32) ((min) * 4) | ((u32) ((max) * 4) << 6))
#define MIRROR ((1u << 28) | (1u << 29))

static const pass_t passes[] = {
    /* Point sampled 64 x 64, wrapped */
    { RGB_W, CP_TEX, 0, 0, FMT_565 | TC_LOCAL, LOD(2, 2), 0, 0, 0, 0, 0 },
    /* Bilinear, clamped; mirrored */
    { RGB_W, CP_TEX, 0, 0, FMT_565 | TC_LOCAL | BILINEAR | CLAMP_ST, LOD(1, 1), 0, 0, 0, 0, 0 },
    { RGB_W | DITHER, CP_TEX, 0, 0, FMT_565 | TC_LOCAL | BILINEAR, LOD(3, 3) | MIRROR, 0, 0, 0, 0, 0 },
    /* Perspective corrected, mipmapped 256 to 1, point and bilinear, a LOD bias */
    { RGB_W | DEPTH | DLESS | AUX_W, CP_TEX, 0, 0, FMT_565 | TC_LOCAL | PERSP, LOD(0, 8), 0, 0, 0, 1, 0 },
    { RGB_W | DITHER, CP_TEX, 0, 0, FMT_565 | TC_LOCAL | PERSP | BILINEAR, LOD(0, 8) | (0x3cu << 12), 0, 0, 0, 1, 0 },
    /* Both TMUs: TMU1's texel times TMU0's (TMU0: other times local, plus nothing), trilinear, the LOD
       fraction and detail factors */
    { RGB_W, CP_TEX, 0, 0, FMT_565 | PERSP | BILINEAR | (1u << 14) | (1u << 23), LOD(0, 8), FMT_565 | TC_LOCAL | PERSP | BILINEAR, LOD(1, 8), 0, 1, 1 },
    { RGB_W, CP_TEX, 0, 0, FMT_565 | PERSP | BILINEAR | TRILINEAR | (5u << 14) | (1u << 13) | (1u << 18), LOD(0, 8), FMT_4444 | TC_LOCAL | PERSP, LOD(0, 8), 0, 1, 1 },
    { RGB_W, CP_TEX, 0, 0, FMT_565 | BILINEAR | (4u << 14) | (1u << 19), LOD(0, 8), FMT_565 | PERSP | BILINEAR | (1u << 13) | (3u << 14) | (1u << 18), LOD(0, 8), 0x40 | (10u << 8) | (2u << 14), 0, 1 },
    /* Alpha tested (greater than 0x60), chroma keyed (one of the texture's colours) */
    { RGB_W, CP_TEX, 1u | (4u << 1) | (0x60u << 24), 0, FMT_4444 | TC_LOCAL | BILINEAR, LOD(2, 2), 0, 0, 0, 0, 0 },
    { RGB_W | CHROMA, CP_TEX, 0, 0, FMT_4444 | TC_LOCAL, LOD(3, 3), 0, 0, 0, 0, 0 },
    /* Fog: the table by W, Z, alpha, W itself; added, multiplied, constant */
    { RGB_W, 0, 0, 1u, 0, 0, 0, 0, 0, 1, 0 },
    { RGB_W, 0, 0, 1u | 0x10u | 0x02u, 0, 0, 0, 0, 0, 1, 0 },
    { RGB_W, 0, 0, 1u | 0x08u | 0x04u, 0, 0, 0, 0, 0, 1, 0 },
    { RGB_W, 0, 0, 1u | 0x18u, 0, 0, 0, 0, 0, 1, 0 },
    { RGB_W | DITHER, 0, 0, 1u | 0x20u, 0, 0, 0, 0, 0, 0, 0 },
    /* Stipple: the pattern; rotating */
    { RGB_W | STIP | STIP_PATT, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
    { RGB_W | STIP, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
    /* Depth: W buffered; biased; from zaColor */
    { RGB_W | AUX_W | DEPTH | DLESS | WBUF, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0 },
    { RGB_W | AUX_W | DEPTH | (3u << 5) | DBIAS, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
    { RGB_W | AUX_W | DEPTH | (6u << 5) | DSRC, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
    /* The Y origin at the bottom */
    { RGB_W | YFLIP | DITHER, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
    /* The colour combine: color1 minus local times alocal plus local; inverted; local from color0 by the
       texture's alpha; alocal the iterated Z */
    { RGB_W, 2u | (1u << 9) | (3u << 10) | (1u << 14) | (2u << 5), 0, 0, 0, 0, 0, 0, 0, 0, 0 },
    { RGB_W, 0u | (1u << 4) | (1u << 10) | (1u << 13) | (1u << 16) | (1u << 25) | (1u << 18) | (1u << 19), 0, 0, 0, 0, 0, 0, 0, 0, 0 },
    { RGB_W, CP_TEX | (1u << 7) | (5u << 10) | (2u << 14) | (4u << 19) | (1u << 23), 0, 0, FMT_4444 | TC_LOCAL | BILINEAR, LOD(2, 2), 0, 0, 0, 0, 0 },
    /* Blending: each factor pair, with destination alpha in the auxiliary buffer */
    { RGB_W | AUX_W | ALPHA_BUF, 0, (1u << 4) | (1u << 8) | (5u << 12) | (4u << 16), 0, 0, 0, 0, 0, 0, 0, 0 },
    { RGB_W | ALPHA_BUF, 0, (1u << 4) | (3u << 8) | (7u << 12), 0, 0, 0, 0, 0, 0, 0, 0 },
    { RGB_W | DITHER, 0, (1u << 4) | (2u << 8) | (6u << 12), 0, 0, 0, 0, 0, 0, 0, 0 },
    { RGB_W | ALPHA_BUF, 0, (1u << 4) | (0xfu << 8) | (4u << 12), 0, 0, 0, 0, 0, 0, 0, 0 },
    { RGB_W, 0, (1u << 4) | (6u << 8) | (0xfu << 12), 1u, 0, 0, 0, 0, 0, 1, 0 },
    /* Dithering: 2 x 2; subtractive (over a blend) */
    { RGB_W | DITHER | DITHER2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
    { RGB_W | DITHER | DSUB, 0, (1u << 4) | (1u << 8) | (5u << 12), 0, 0, 0, 0, 0, 0, 0, 0 },
    { RGB_W | DITHER | DITHER2 | DSUB, 0, (1u << 4) | (4u << 8) | (4u << 12), 0, 0, 0, 0, 0, 0, 0, 0 },
};

/* Draws every pass, each over its fast fill, held four ticks of the BIOS clock */
static void run_passes(void) {
    reg(FOG_COLOR, 0x00a05030);
    reg(CHROMA_KEY, 0x00ff00ff);
    reg(STIPPLE, 0xa5c3966fu);
    reg(COLOR0, 0x80c04020u);
    reg(COLOR1, 0x4020c0e0u);
    for (u32 i = 0; i < 32; i++) {
        const u32 f0 = i * 8;
        const u32 f1 = i * 8 + 4;
        reg(FOG_TABLE + i * 4, (4u) | (f0 << 8) | (4u << 16) | (f1 << 24));
    }
    reg(TDETAIL, 0);
    reg(FOG_MODE, 0);
    reg(ALPHA_MODE, 0);

    for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
        const pass_t *ps = &passes[p];
        /* Its fill and its triangles clipped to the screen, or every seventh pass to a smaller rectangle */
        const int clipped = (p % 7) == 6;
        reg(CLIP_LEFT_RIGHT, clipped ? ((64u << 16) | 560u) : 640u);
        reg(CLIP_LOW_Y_HIGH_Y, clipped ? ((40u << 16) | 420u) : 480u);
        reg(FOG_MODE, 0);
        reg(ALPHA_MODE, 0);
        reg(COLOR1, 0x00203040 + p * 0x00040302u);
        reg(ZA_COLOR, (p & 1) ? 0x7fffu : 0xffffu);
        reg(FBZ_MODE, RGB_W | AUX_W | (ps->fbz & (YFLIP)));
        reg(FASTFILL_CMD, 0);
        reg(COLOR1, 0x4020c0e0u);
        reg(ZA_COLOR, (p & 1) ? 0x00c03000u : 0x0000ff40u);

        dual = ps->dual;
        reg(TEXTURE_MODE | CHIP_TMU0, ps->tex0);
        reg(TLOD | CHIP_TMU0, ps->lod0);
        reg(TDETAIL | CHIP_TMU0, ps->detail);
        reg(TEXTURE_MODE | CHIP_TMU1, ps->tex1);
        reg(TLOD | CHIP_TMU1, ps->lod1);
        reg(TDETAIL | CHIP_TMU1, ps->detail);
        reg(FBZ_COLOR_PATH, ps->cp);
        reg(ALPHA_MODE, ps->alpha);
        reg(FOG_MODE, ps->fog);
        reg(FBZ_MODE, ps->fbz | CLIP);
        triangles(0x100 + p, 20, ps->perspective);
        wait_ticks(4);
    }
    reg(FOG_MODE, 0);
    reg(ALPHA_MODE, 0);
    reg(FBZ_COLOR_PATH, 0);
}
