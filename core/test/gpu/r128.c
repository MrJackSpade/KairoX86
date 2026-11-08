/*
 * KairoX86's Rage 128 2D test (KairoX86#283, for #239): on an ATI Rage 128 (PCI 1002h: 5046h, 5245h), each VESA
 * 640 x 480 mode with a linear frame buffer at 8, 16 and 32 bits a pixel, and the 2D engine's passes through its
 * memory-mapped registers (BAR2), each started by a register write on the processor's thread, over a clear through
 * the linear frame buffer, each held four ticks of the BIOS clock and copied into memory above 1 MB for the end
 * state: rectangle fills through 64 ternary raster operations, solid and with the mono brush (opaque and
 * transparent), and under a partial write mask; copies through operations of the brush, source and destination in
 * every direction, overlapping, a smear, and a source colour key; colour and mono data from the host, opaque and
 * transparent; Bresenham lines in every octant. Then at 16 and 32 bits, 3D through the CCE, its packets written by the
 * processor (PIO): Gouraud triangles through the depth test (16-bit Z, kept in the end state too) under four compare
 * functions, alpha-blended ones and the alpha test; textured ones (the picture's format, bilinear, modulated by the
 * vertex colours) as a fan and a strip, then the same with a texture of datatype 13 (alpha and intensity 8:8). The
 * display waits for the CCE before it draws a line (KairoX86#302), so what a picture shows does not depend on the
 * host's threads. The engine's status is never read. Any other card returns at
 * once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    return inl(0xcfc);
}

enum { DST_OFFSET = 0x1404, DST_PITCH = 0x1408, SRC_PITCH_OFFSET = 0x1428, DST_PITCH_OFFSET = 0x142c,
       SRC_Y_X = 0x1434, DST_Y_X = 0x1438, DST_HEIGHT_WIDTH = 0x143c, GMC = 0x146c, BRUSH_BKGD = 0x1478,
       BRUSH_FRGD = 0x147c, BRUSH_DATA0 = 0x1480, BRUSH_DATA1 = 0x1484, DST_WIDTH_HEIGHT = 0x1598,
       CLR_CMP_CNTL = 0x15c0, CLR_CMP_CLR_SRC = 0x15c4, CLR_CMP_CLR_DST = 0x15c8, CLR_CMP_MASK = 0x15cc,
       SRC_FRGD = 0x15d8, SRC_BKGD = 0x15dc, BRES_ERR = 0x1628, BRES_INC = 0x162c, BRES_DEC = 0x1630,
       BRES_LNTH = 0x1634, DP_CNTL = 0x16c0, WRITE_MASK = 0x16cc, LINE_DIR = 0x16d0, SC_TOP_LEFT = 0x16ec,
       SC_BOTTOM_RIGHT = 0x16f0, SRC_SC_BOTTOM_RIGHT = 0x16f4, HOST_DATA0 = 0x17c0, HOST_DATA_LAST = 0x17e0 };

/* DP_GUI_MASTER_CNTL: the pitches, offsets and clips as written (LEAVE), no auxiliary clip */
#define G_LEAVE        0xfu
#define G_BRUSH(b)     ((u32) (b) << 4)
#define G_DST(d)       ((u32) (d) << 8)
#define G_SRC(s)       ((u32) (s) << 12)
#define G_ROP(r)       ((u32) (r) << 16)
#define G_SOURCE(s)    ((u32) (s) << 24)
#define G_CMP_DIS      (1u << 28)
#define G_AUX_DIS      (1u << 29)
#define G_WRMASK_DIS   (1u << 30)
enum { BR_MONO = 0, BR_MONO_TRANSPARENT = 1, BR_SOLID = 13, BR_NONE = 15 };
enum { SD_MONO = 0, SD_MONO_TRANSPARENT = 1, SD_COLOUR = 3 };
enum { SS_MEMORY = 2, SS_HOST = 3 };

#define W 640
#define H 480

static volatile u32 *mmio;
static volatile u8  *fb;
static u32           bytes, datatype;
static u32           readback = 0x100000;

static void reg(u32 offset, u32 value) { mmio[offset / 4] = value; }
static u32  colour(u32 v) { return (bytes == 4) ? v : (v & ((1u << (bytes * 8)) - 1)); }
static u32  gmc(u32 rest) { return G_LEAVE | G_AUX_DIS | G_DST(datatype) | rest; }

static void clear(u32 salt) {
    for (u32 i = 0; i < W * H * bytes / 4; i++)
        ((volatile u32 *) fb)[i] = pattern(i % 160, i / 160, salt);
}

static void copy_out(void) {
    for (u32 i = 0; i < W * H * bytes / 4; i++)
        ((volatile u32 *) readback)[i] = ((volatile u32 *) fb)[i];
    readback += W * H * bytes;
}

static void fill(u32 x, u32 y, u32 w, u32 h) {
    reg(DST_Y_X, (y << 16) | x);
    reg(DST_WIDTH_HEIGHT, (w << 16) | h);
}

/* A copy w x h from (sx, sy) to (dx, dy) in the direction given; the start is the corner the walk leaves first */
static void copy(u32 sx, u32 sy, u32 dx, u32 dy, u32 w, u32 h, u32 right, u32 down) {
    reg(DP_CNTL, (right ? 1u : 0) | (down ? 2u : 0));
    const u32 fx = right ? 0 : w - 1, fy = down ? 0 : h - 1;
    reg(SRC_Y_X, ((sy + fy) << 16) | (sx + fx));
    reg(DST_Y_X, ((dy + fy) << 16) | (dx + fx));
    reg(DST_HEIGHT_WIDTH, (h << 16) | w);
}

static const u8 rops[64] = { 0x00, 0x05, 0x0a, 0x0f, 0x11, 0x22, 0x33, 0x44, 0x50, 0x55, 0x5a, 0x5f, 0x66, 0x77, 0x88,
                             0x99, 0xa0, 0xa5, 0xaa, 0xaf, 0xbb, 0xcc, 0xdd, 0xee, 0xf0, 0xf5, 0xfa, 0xff, 0x1a, 0x2d,
                             0x3c, 0x4b, 0x69, 0x78, 0x87, 0x96, 0xa3, 0xb4, 0xb8, 0xc3, 0xca, 0xd2, 0xe1, 0xe2, 0xf6,
                             0x06, 0x12, 0x24, 0x36, 0x48, 0x6c, 0x7e, 0x81, 0x93, 0x9c, 0xac, 0xbe, 0xc5, 0xd8, 0xe4,
                             0x1b, 0x27, 0x39, 0x4e };

static void p_fills(u32 salt) {
    reg(DP_CNTL, 3);
    reg(BRUSH_DATA0, 0x81422418u ^ salt);
    reg(BRUSH_DATA1, 0x18244281u);
    reg(BRUSH_BKGD, colour(pattern(2, 1, salt)));
    for (u32 r = 0; r < 64; r++) {
        /* solid, the mono brush opaque and transparent in turn */
        static const u8 brushes[3] = { BR_SOLID, BR_MONO, BR_MONO_TRANSPARENT };
        reg(GMC, gmc(G_BRUSH(brushes[r % 3]) | G_ROP(rops[r]) | G_CMP_DIS | G_WRMASK_DIS));
        reg(BRUSH_FRGD, colour(pattern(r, 1, salt)));
        fill(8 + (r % 8) * 78, 8 + (r / 8) * 50, 70, 44);
    }
    /* under a partial write mask */
    reg(WRITE_MASK, 0x5a5aa5a5u ^ salt);
    for (u32 r = 0; r < 8; r++) {
        reg(GMC, gmc(G_BRUSH(BR_SOLID) | G_ROP(rops[r * 7]) | G_CMP_DIS));
        reg(BRUSH_FRGD, colour(pattern(r, 2, salt)));
        fill(8 + r * 78, 410, 70, 60);
    }
    reg(WRITE_MASK, 0xffffffffu);
}

static void p_copies(u32 salt) {
    reg(BRUSH_DATA0, 0x81422418u ^ salt);
    reg(BRUSH_DATA1, 0x18244281u);
    reg(BRUSH_FRGD, colour(pattern(1, 2, salt)));
    reg(BRUSH_BKGD, colour(pattern(2, 2, salt)));
    for (u32 k = 0; k < 8; k++) {
        static const u8 brops[8] = { 0xcc, 0xf0, 0xb8, 0xe2, 0x96, 0x5a, 0x66, 0xca };
        const u32 sx = 20 + (k % 4) * 150, sy = 20 + (k / 4) * 200, w = 100, h = 90;
        const u32 ox = (k & 4) ? 9 : 40, oy = (k & 4) ? 5 : 80;
        reg(GMC, gmc(G_BRUSH(BR_MONO) | G_SRC(SD_COLOUR) | G_ROP(brops[k]) | G_SOURCE(SS_MEMORY) | G_CMP_DIS
                     | G_WRMASK_DIS));
        copy(sx, sy, sx + ox, sy + oy, w, h, k & 1, k & 2);
    }
    /* a smear: 3 pixels right, left to right, reading what it has just drawn */
    reg(GMC, gmc(G_BRUSH(BR_NONE) | G_SRC(SD_COLOUR) | G_ROP(0xcc) | G_SOURCE(SS_MEMORY) | G_CMP_DIS | G_WRMASK_DIS));
    copy(20, 420, 23, 420, 200, 20, 1, 1);
    /* a source colour key: pixels of the key's colour (under its mask) are not drawn */
    reg(CLR_CMP_CNTL, (1u << 24) | 5u);
    reg(CLR_CMP_MASK, 0xffffff0fu);
    reg(CLR_CMP_CLR_SRC, colour(pattern(3, 0, 0x40 + salt)) & 0xffffff0fu);
    reg(GMC, gmc(G_BRUSH(BR_NONE) | G_SRC(SD_COLOUR) | G_ROP(0xcc) | G_SOURCE(SS_MEMORY) | G_WRMASK_DIS));
    copy(300, 400, 340, 410, 250, 60, 1, 1);
}

static void p_host(u32 salt) {
    reg(DP_CNTL, 3);
    /* colour: 32 pixels a row, 24 rows */
    for (u32 t = 0; t < 2; t++) {
        reg(GMC, gmc(G_BRUSH(BR_NONE) | G_SRC(SD_COLOUR) | G_ROP(t ? 0x66 : 0xcc) | G_SOURCE(SS_HOST) | G_CMP_DIS
                     | G_WRMASK_DIS));
        fill(20 + t * 60, 20, 32, 24);
        const u32 n = 32 * bytes / 4 * 24;
        for (u32 i = 0; i < n; i++)
            reg(i + 1 == n ? HOST_DATA_LAST : HOST_DATA0 + (i % 8) * 4, pattern(i, 3 + t, salt));
    }
    /* mono, opaque and transparent: 40 pixels a row (two dwords), 30 rows */
    reg(SRC_FRGD, colour(pattern(1, 5, salt)));
    reg(SRC_BKGD, colour(pattern(2, 5, salt)));
    for (u32 t = 0; t < 2; t++) {
        reg(GMC, gmc(G_BRUSH(BR_NONE) | G_SRC(t ? SD_MONO_TRANSPARENT : SD_MONO) | G_ROP(0xcc) | G_SOURCE(SS_HOST)
                     | G_CMP_DIS | G_WRMASK_DIS));
        fill(200 + t * 80, 20, 40, 30);
        for (u32 i = 0; i < 2 * 30; i++)
            reg(i + 1 == 60 ? HOST_DATA_LAST : HOST_DATA0 + (i % 8) * 4, pattern(i, 6 + t, salt));
    }
}

static void p_lines(u32 salt) {
    reg(DP_CNTL, 3 | (1u << 5)); /* the last pixel drawn */
    for (u32 l = 0; l < 16; l++) {
        /* an octant each: x and y directions, the major axis */
        const int dx = 30 + (int) l * 13, dy = 10 + (int) l * 7;
        const int major = (l & 4) ? dy : dx, minor = (l & 4) ? dx : dy;
        reg(GMC, gmc(G_BRUSH(BR_SOLID) | G_ROP((l & 1) ? 0x5a : 0xf0) | G_CMP_DIS | G_WRMASK_DIS));
        reg(BRUSH_FRGD, colour(pattern(l, 8, salt)));
        reg(LINE_DIR, ((l & 1) ? 0 : 0x80000000u) | ((l & 2) ? 0 : 0x8000u) | ((l & 4) ? 4u : 0));
        reg(DST_Y_X, ((u32) (240 + (int) (l % 4) * 20) << 16) | (u32) (320 - 40 + (int) (l / 4) * 20));
        reg(BRES_ERR, (u32) (2 * minor - major) & 0xfffff);
        reg(BRES_INC, (u32) (2 * minor) & 0xfffff);
        reg(BRES_DEC, (u32) (2 * minor - 2 * major) & 0xfffff);
        reg(BRES_LNTH, (u32) major + 1);
    }
}

/* ---- 3D, through the CCE: packets written by the processor (PIO mode 1), each pair to PM4_FIFO_DATA_EVEN and ODD */

enum { PM4_BUFFER_CNTL = 0x0704, PM4_VC_FPU_SETUP = 0x071c, PM4_FIFO_EVEN = 0x1000, PM4_FIFO_ODD = 0x1004,
       SCALE_3D_CNTL = 0x1a00, SETUP_CNTL = 0x1bc4, CONTEXT_C = 0x1c80, CONSTANT_COLOR_C = 0x1d34,
       STEN_REF_MASK_C = 0x1d40, PLANE_3D_MASK_C = 0x1d44 };
/* The card memory the 3D passes use besides the picture: the depth buffer (16 bits a pixel) and the texture */
#define Z_OFF   0x140000u
#define TEX_OFF 0x200000u
#define TEX_LOG 6 /* 64 x 64 */

static u32 pm4_odd;

static void pm4(u32 v) {
    reg(pm4_odd ? PM4_FIFO_ODD : PM4_FIFO_EVEN, v);
    pm4_odd ^= 1;
}

/* The last packet's pair completed with a type-2 (filler) packet */
static void pm4_end(void) {
    if (pm4_odd)
        pm4(0x80000000u);
}

/* Type 0: n registers from first, in order */
static void pm4_regs(u32 first, u32 n, const u32 *v) {
    pm4(((n - 1) << 16) | (first >> 2));
    for (u32 i = 0; i < n; i++)
        pm4(v[i]);
}

static u32 fbits(float f) {
    union { float f; u32 u; } v = { f };
    return v.u;
}

/* The 3D context block (DST_PITCH_OFFSET_C to PRIM_TEX_OFFSET_C(10)) for a draw state */
static void context(u32 tex_cntl, u32 z_fn, u32 misc, u32 tex_dt) {
    u32 c[26];
    c[0]  = (W / 8) << 21;                                                          /* DST_PITCH_OFFSET_C */
    c[1]  = G_LEAVE | G_BRUSH(BR_NONE) | G_DST(datatype) | G_SRC(SD_COLOUR) | G_ROP(0xcc) | G_SOURCE(SS_MEMORY)
         | (1u << 27) | G_CMP_DIS | G_AUX_DIS | G_WRMASK_DIS;                      /* DP_GUI_MASTER_CNTL_C, 3D */
    c[2]  = 0;                                                                      /* SC_TOP_LEFT_C */
    c[3]  = ((H - 1) << 16) | (W - 1);                                              /* SC_BOTTOM_RIGHT_C */
    c[4]  = Z_OFF;                                                                  /* Z_OFFSET_C */
    c[5]  = W / 8;                                                                  /* Z_PITCH_C */
    c[6]  = z_fn << 4;                                                              /* Z_STEN_CNTL_C: 16-bit Z */
    c[7]  = tex_cntl;                                                               /* TEX_CNTL_C */
    c[8]  = misc;                                                                   /* MISC_3D_STATE_CNTL */
    c[9]  = 0;                                                                      /* TEX_CLR_CMP_CLR_C */
    c[10] = 0;                                                                      /* TEX_CLR_CMP_MSK_C */
    c[11] = 0;                                                                      /* FOG_COLOR_C */
    c[12] = (tex_dt << 16) | (1u << 4) | (1u << 1);                                 /* PRIM_TEX_CNTL_C: bilinear */
    c[13] = 3u | (4u << 4) | (4u << 10) | (3u << 14) | (6u << 18) | (2u << 25);    /* modulate, colour and alpha */
    c[14] = TEX_LOG | (TEX_LOG << 4) | (TEX_LOG << 8) | (TEX_LOG << 12);            /* TEX_SIZE_PITCH_C */
    for (u32 i = 15; i < 26; i++)
        c[i] = TEX_OFF;                                                             /* PRIM_TEX_OFFSET_C(0-10) */
    pm4_regs(CONTEXT_C, 26, c);
    const u32 mask = 0xffffffffu, sten = 0;
    pm4_regs(PLANE_3D_MASK_C, 1, &mask);
    pm4_regs(STEN_REF_MASK_C, 1, &sten);
}

/* 3D_RNDR_GEN_PRIM: a triangle list (or fan, strip) of n vertices, x y z, ARGB, and s t when textured */
static void prim(u32 type, u32 n, const float *xyz, const u32 *argb, const float *st) {
    const u32 fmt = st ? 0x088u : 0x008u, stride = st ? 6 : 4;
    pm4(0xc0000000u | ((n * stride + 2 - 1) << 16) | (0x25u << 8));
    pm4(fmt);
    pm4(type | (3u << 4) | (n << 16));
    for (u32 i = 0; i < n; i++) {
        pm4(fbits(xyz[i * 3]));
        pm4(fbits(xyz[i * 3 + 1]));
        pm4(fbits(xyz[i * 3 + 2]));
        pm4(argb[i]);
        if (st) {
            pm4(fbits(st[i * 2]));
            pm4(fbits(st[i * 2 + 1]));
        }
    }
}

static void clear_z(void) {
    for (u32 i = 0; i < W * H * 2 / 4; i++)
        ((volatile u32 *) (fb + Z_OFF))[i] = 0xffffffffu;
}

static void copy_z(void) {
    for (u32 i = 0; i < W * H * 2 / 4; i++)
        ((volatile u32 *) readback)[i] = ((volatile u32 *) (fb + Z_OFF))[i];
    readback += W * H * 2;
}

static float fr(u32 v, float lo, float span) { return lo + (float) (v & 0xffff) * span / 65536.0f; }

/* Gouraud triangles through the depth test, then alpha-blended ones over them */
static void p_3d(u32 salt) {
    clear_z();
    reg(PM4_BUFFER_CNTL, 0x10000000u);
    reg(PM4_VC_FPU_SETUP, 0x1eu | (2u << 5)); /* both faces drawn, Gouraud */
    reg(SCALE_3D_CNTL, 2u << 6);
    reg(SETUP_CNTL, 0x00080200u);
    static const u8 zfns[4] = { 1, 2, 4, 7 }; /* less, less or equal, greater or equal, always */
    for (u32 k = 0; k < 4; k++) {
        context((1u << 0) | (1u << 1), zfns[k], 0, 0);
        float xyz[18];
        u32   argb[6];
        for (u32 v = 0; v < 6; v++) {
            xyz[v * 3]     = fr(pattern(v, k, salt), 10.0f, 620.0f);
            xyz[v * 3 + 1] = fr(pattern(v, k + 10, salt), 10.0f, 460.0f);
            xyz[v * 3 + 2] = fr(pattern(v, k + 20, salt), 0.0f, 1.0f);
            argb[v]        = pattern(v, k + 30, salt);
        }
        prim(4, 6, xyz, argb, 0);
    }
    /* blended: source alpha and its inverse, add and subtract; then the alpha test */
    static const u32 blends[4] = { (4u << 16) | (5u << 20), (1u << 16) | (1u << 20), (2u << 16) | (9u << 20) | (2u << 12),
                                   (8u << 16) | (0u << 20) };
    for (u32 k = 0; k < 4; k++) {
        context((1u << 0) | (1u << 9) | ((k == 3) ? (1u << 10) : 0), 1, blends[k] | ((k == 3) ? (5u << 24) | 0x80u : 0), 0);
        float xyz[9];
        u32   argb[3];
        for (u32 v = 0; v < 3; v++) {
            xyz[v * 3]     = fr(pattern(v, k + 40, salt), 0.0f, 640.0f);
            xyz[v * 3 + 1] = fr(pattern(v, k + 50, salt), 0.0f, 480.0f);
            xyz[v * 3 + 2] = fr(pattern(v, k + 60, salt), 0.0f, 1.0f);
            argb[v]        = pattern(v, k + 70, salt);
        }
        prim(4, 3, xyz, argb, 0);
    }
    pm4_end();
}

/* Textured: the texture (64 x 64 of tex_dt, tex_bytes a texel) modulated by the vertex colours, a fan and a strip */
static void p_tex_of(u32 salt, u32 tex_dt, u32 tex_bytes) {
    for (u32 i = 0; i < 64 * 64 * tex_bytes / 4; i++)
        ((volatile u32 *) (fb + TEX_OFF))[i] = pattern(i % 32, i / 32, salt);
    clear_z();
    reg(PM4_BUFFER_CNTL, 0x10000000u);
    reg(PM4_VC_FPU_SETUP, 0x1eu | (2u << 5));
    reg(SCALE_3D_CNTL, (2u << 6) | (1u << 30));
    reg(SETUP_CNTL, 0x00080200u);
    context((1u << 0) | (1u << 1) | (1u << 4), 2, 0, tex_dt);
    for (u32 k = 0; k < 2; k++) {
        float xyz[18], st[12];
        u32   argb[6];
        for (u32 v = 0; v < 6; v++) {
            xyz[v * 3]     = fr(pattern(v, k, salt), 0.0f, 640.0f);
            xyz[v * 3 + 1] = fr(pattern(v, k + 10, salt), 0.0f, 480.0f);
            xyz[v * 3 + 2] = fr(pattern(v, k + 20, salt), 0.0f, 1.0f);
            argb[v]        = pattern(v, k + 30, salt) | 0xff000000u;
            st[v * 2]      = fr(pattern(v, k + 40, salt), -0.5f, 3.0f);
            st[v * 2 + 1]  = fr(pattern(v, k + 50, salt), -0.5f, 3.0f);
        }
        prim(k ? 6 : 5, 6, xyz, argb, st);
    }
    pm4_end();
}

/* The picture's format */
static void p_tex(u32 salt) { p_tex_of(salt, datatype, bytes); }

/* Datatype 13: alpha and intensity 8:8 (KairoX86#325) */
static void p_tex_ai88(u32 salt) { p_tex_of(salt, 13, 2); }

void test_main(void) {
    __asm__ volatile("fninit");
    u32 regs = 0;
    for (u32 bus = 0; bus < 2 && !regs; bus++)
        for (u32 dev = 0; dev < 32 && !regs; dev++) {
            const u32 id = pci_read(bus, dev, 0, 0);
            const u32 d  = id >> 16;
            if (((id & 0xffff) == 0x1002) && ((d == 0x5046) || (d == 0x5245)))
                regs = pci_read(bus, dev, 0, 0x18) & ~0xfu;
        }
    if (!regs || vbe_modes() < 0)
        return;
    mmio = (volatile u32 *) regs;

    static const u8 bpps[3] = { 8, 16, 32 }, types[3] = { 2, 4, 6 };
    static void (*const passes[])(u32) = { p_fills, p_copies, p_host, p_lines };
    for (u32 f = 0; f < 3; f++) {
        const u16 mode = vbe_find(W, H, bpps[f]);
        if (!mode || int10(0x4f02, mode | 0x4000, 0, 0, 0, 0) != 0x004f)
            continue;
        fb       = (volatile u8 *) VBE_MODE->framebuffer;
        bytes    = bpps[f] / 8;
        datatype = types[f];
        reg(DST_PITCH_OFFSET, ((W / 8) << 21) | 0);
        reg(SRC_PITCH_OFFSET, ((W / 8) << 21) | 0);
        reg(SC_TOP_LEFT, 0);
        reg(SC_BOTTOM_RIGHT, ((H - 1) << 16) | (W - 1));
        reg(SRC_SC_BOTTOM_RIGHT, ((H - 1) << 16) | (W - 1));
        reg(WRITE_MASK, 0xffffffffu);
        for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
            clear(0x40 + p + f * 8);
            passes[p](p + f * 8);
            wait_ticks(4);
            copy_out();
        }
        if (bytes == 1)
            continue; /* the 3D engine draws at 15, 16 and 32 bits a pixel */
        clear(0x60 + f);
        p_3d(0x20 + f);
        wait_ticks(4);
        copy_out();
        copy_z();
        clear(0x68 + f);
        p_tex(0x28 + f);
        wait_ticks(4);
        copy_out();
        clear(0x70 + f);
        p_tex_ai88(0x30 + f);
        wait_ticks(4);
        copy_out();
    }
    int10(0x0003, 0, 0, 0, 0, 0);
}
