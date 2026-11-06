/*
 * KairoX86's ATI 3D Rage II+ 3D test (KairoX86#283, for #237): on a Rage II+ (PCI 1002h:4755h), VESA 640 x 480 x 16
 * with its linear frame buffer, the registers in the aperture's top 1K, a texture area filled with a pattern
 * through the frame buffer, and a series of passes drawn through the 3D engine (vid_ati_mach64_3d.c), each a set
 * of triangles (two trapezoids each, the second on the edges the first leaves) over a clear, held four ticks of the
 * BIOS clock: shading; the Z tests, with and without writes; each texture format (CI8 and CI4 through the
 * palette, the 16 and 32-bit ones, RGB 332, Y8, YUV 422 and AYUV); nearest and bilinear sampling, magnified and
 * minified, each mip map blend; second-order S and T steps; the lighting functions, colour override and the
 * alpha mask; fog; alpha blending; every destination format; ordered dithering, error diffusion (with and
 * without its scan line reset) and rounding; the destination and texel colour compares; a constant data path
 * source through a partial write mask; the scissors; right to left fills; a texture read from the picture being
 * drawn on; and 3D lines, shaded and textured, X and Y major. The engine's busy bit is never read (as in
 * v3d.c). Any other card returns at once.
 *
 * The destination of every pass is the screen: its pitch (in pixels of the pass's format) keeps one line of it to
 * one line of the screen, which shows its bytes as 16-bit pixels.
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

enum {
    DST_OFF_PITCH = 0x100, DST_Y_X = 0x10c, DST_BRES_LNTH = 0x120, DST_BRES_ERR = 0x124, DST_BRES_INC = 0x128,
    DST_BRES_DEC = 0x12c, DST_CNTL = 0x130, TRAIL_BRES_ERR = 0x138, TRAIL_BRES_INC = 0x13c, TRAIL_BRES_DEC = 0x140,
    Z_OFF_PITCH = 0x148, Z_CNTL = 0x14c, TEX_0_OFF = 0x1c0, SCALE_3D_CNTL = 0x1fc, SC_LEFT_RIGHT = 0x2a8,
    SC_TOP_BOTTOM = 0x2b4, DP_BKGD_CLR = 0x2c0, DP_FRGD_CLR = 0x2c4, WRITE_MASK = 0x2c8, DP_PIX_WIDTH = 0x2d0,
    DP_SRC = 0x2d8, CLR_CMP_CLR = 0x300, CLR_CMP_MASK = 0x304, CLR_CMP_CNTL = 0x308, S_X_INC2 = 0x340,
    S_Y_INC2 = 0x344, S_XY_INC2 = 0x348, S_XINC_START = 0x34c, S_Y_INC = 0x350, S_START = 0x354, T_X_INC2 = 0x358,
    T_Y_INC2 = 0x35c, T_XY_INC2 = 0x360, T_XINC_START = 0x364, T_Y_INC = 0x368, T_START = 0x36c,
    TEX_SIZE_PITCH = 0x370, TEX_PALETTE = 0x37c, RED_X_INC = 0x3c0, RED_Y_INC = 0x3c4, RED_START = 0x3c8,
    GREEN_X_INC = 0x3cc, GREEN_Y_INC = 0x3d0, GREEN_START = 0x3d4, BLUE_X_INC = 0x3d8, BLUE_Y_INC = 0x3dc,
    BLUE_START = 0x3e0, Z_X_INC = 0x3e4, Z_Y_INC = 0x3e8, Z_START = 0x3ec, ALPHA_X_INC = 0x3f0, ALPHA_Y_INC = 0x3f4,
    ALPHA_START = 0x3f8,
};

/* DST_CNTL */
#define X_DIR      0x01u
#define Y_DIR      0x02u
#define Y_MAJOR    0x04u
#define LAST_PEL   0x20u
#define TRAIL_DIR  (1u << 13)
#define FILL_L2R   (1u << 14)
/* DST_BRES_LNTH */
#define DRAW_TRAP  (1u << 15)
#define LOAD_TRAIL (1u << 31)

/* SCALE_3D_CNTL */
#define PIX_EXPAND  (1u << 0)
#define SDITHER     (1u << 1)
#define DITHER      (1u << 2)
#define DINIT       (1u << 3)
#define ROUND       (1u << 4)
#define TEXTURE     (2u << 6)
#define SHADE       (3u << 6)
#define NEAR_VIS    (1u << 9)
#define APPLE_YUV   (1u << 10)
#define ABLEND      (1u << 11)
#define FOG         (2u << 11)
#define OVERRIDE    (1u << 13)
#define RED_MAX     (1u << 14)
#define BSRC(f)     ((u32) (f) << 16) /* 0 zero, 1 one, 2 dst colour, 3 1 - dst, 4 src alpha, 5 1 - src alpha */
#define BDST(f)     ((u32) (f) << 19)
#define LIGHT(f)    ((u32) (f) << 22) /* 0 replace, 1 modulate, 2 alpha blend */
#define NO_MIP      (1u << 24)
#define BILINEAR    (1u << 25)
#define TBLEND(f)   ((u32) (f) << 26)
#define AMASK       (1u << 28)
#define AMASK_MODE  (1u << 29)
#define TEX_ALPHA   (1u << 30)

/* Z_CNTL */
#define ZT(t) (1u | ((u32) (t) << 4)) /* 0 never, 1 <, 2 <=, 3 ==, 4 >=, 5 >, 6 !=, 7 always */
#define ZW    (1u << 8)

/* A pass's other settings */
#define P_CI4      0x001u
#define P_CONST    0x002u
#define P_DSTCMP   0x004u
#define P_KEY      0x008u
#define P_SCISSOR  0x010u
#define P_INC2     0x020u
#define P_WMASK    0x040u
#define P_FEEDBACK 0x080u
#define P_R2L      0x100u
#define P_LINES    0x200u

typedef struct {
    u32 cntl;
    u32 z;
    u8  dst;     /* DP_DST_PIX_WIDTH */
    u8  tex;     /* DP_SCALE_PIX_WIDTH */
    u8  minify;  /* texels a pixel, as a shift */
    u16 flags;
} pass_t;

static const pass_t passes[] = {
    { SHADE, 0, 4, 0, 0, 0 },
    { SHADE, ZT(1) | ZW, 4, 0, 0, 0 },
    { SHADE, ZT(2) | ZW, 4, 0, 0, 0 },
    { SHADE, ZT(5), 4, 0, 0, 0 },
    { SHADE, ZT(6) | ZW, 4, 0, 0, P_R2L },
    { TEXTURE | NO_MIP | LIGHT(0), 0, 4, 3, 0, 0 },
    { TEXTURE | NO_MIP | LIGHT(1) | BILINEAR, ZT(1) | ZW, 4, 4, 0, 0 },
    { TEXTURE | NO_MIP | LIGHT(2) | TEX_ALPHA | PIX_EXPAND, 0, 4, 15, 0, 0 },
    { TEXTURE | NO_MIP | LIGHT(1) | BILINEAR | TEX_ALPHA, 0, 4, 6, 0, P_INC2 },
    { TEXTURE | LIGHT(0) | TBLEND(0), 0, 4, 6, 2, 0 },
    { TEXTURE | LIGHT(1) | TBLEND(1), 0, 4, 4, 3, 0 },
    { TEXTURE | LIGHT(0) | TBLEND(2) | BILINEAR, 0, 4, 3, 2, P_INC2 },
    { TEXTURE | LIGHT(0) | TBLEND(3) | ABLEND | BSRC(4) | BDST(5), 0, 4, 4, 2, 0 },
    { TEXTURE | NO_MIP | LIGHT(0), 0, 4, 2, 0, 0 },
    { TEXTURE | NO_MIP | LIGHT(1) | BILINEAR, 0, 4, 2, 0, P_CI4 },
    { TEXTURE | NO_MIP | LIGHT(0) | NEAR_VIS | BILINEAR, 0, 4, 2, 0, P_KEY },
    { TEXTURE | NO_MIP | LIGHT(0) | PIX_EXPAND, 0, 4, 7, 0, 0 },
    { TEXTURE | NO_MIP | LIGHT(1), 0, 4, 8, 0, 0 },
    { TEXTURE | NO_MIP | LIGHT(0) | BILINEAR, 0, 4, 11, 0, 0 },
    { TEXTURE | NO_MIP | LIGHT(0) | APPLE_YUV, 0, 4, 14, 0, 0 },
    { TEXTURE | NO_MIP | LIGHT(0) | TEX_ALPHA | AMASK, 0, 4, 3, 0, 0 },
    { TEXTURE | NO_MIP | LIGHT(1) | TEX_ALPHA | AMASK | AMASK_MODE | OVERRIDE, 0, 4, 15, 0, 0 },
    { SHADE | FOG, ZT(1) | ZW, 4, 0, 0, 0 },
    { TEXTURE | NO_MIP | LIGHT(1) | FOG, 0, 4, 4, 0, 0 },
    { SHADE | ABLEND | BSRC(4) | BDST(5), 0, 4, 0, 0, 0 },
    { SHADE | ABLEND | BSRC(2) | BDST(3), 0, 4, 0, 0, 0 },
    { TEXTURE | NO_MIP | LIGHT(1) | ABLEND | BSRC(1) | BDST(1), 0, 4, 4, 0, 0 },
    { SHADE | DITHER | SDITHER, 0, 4, 0, 0, 0 },
    { SHADE | DITHER | SDITHER | ABLEND | BSRC(1) | BDST(1), 0, 3, 0, 0, 0 },
    { SHADE | DITHER, 0, 4, 0, 0, 0 },
    { SHADE | DITHER | DINIT, ZT(1) | ZW, 3, 0, 0, 0 },
    { SHADE | ROUND, 0, 15, 0, 0, 0 },
    { SHADE, 0, 6, 0, 0, 0 },
    { TEXTURE | NO_MIP | LIGHT(0) | DITHER | RED_MAX, 0, 7, 4, 0, 0 },
    { SHADE | DITHER | SDITHER | RED_MAX, 0, 7, 0, 0, 0 },
    { SHADE, 0, 8, 0, 0, 0 },
    { SHADE | ABLEND | BSRC(4) | BDST(5), 0, 2, 0, 0, 0 },
    { SHADE, 0, 4, 0, 0, P_DSTCMP },
    { SHADE, ZT(1) | ZW, 4, 0, 0, P_CONST | P_WMASK },
    { TEXTURE | NO_MIP | LIGHT(0), ZT(2) | ZW, 4, 4, 0, P_SCISSOR },
    { TEXTURE | NO_MIP | LIGHT(1) | BILINEAR, 0, 4, 4, 0, P_FEEDBACK },
    { SHADE, ZT(1) | ZW, 4, 0, 0, P_LINES },
    { TEXTURE | NO_MIP | LIGHT(1), 0, 4, 4, 0, P_LINES },
    { TEXTURE | NO_MIP | LIGHT(0) | DITHER, 0, 4, 4, 0, P_LINES },
};

static u32 bytes_of(u32 format) {
    switch (format) {
        case 2: case 7: case 8: return 1;
        case 6: return 4;
        default: return 2;
    }
}

typedef struct {
    int   x, y;
    float r, g, b, a, z, s, t;
} vertex_t;

static void plane(const vertex_t *v, float a0, float a1, float a2, float *gx, float *gy) {
    const float area = (float) ((v[1].x - v[0].x) * (v[2].y - v[0].y) - (v[2].x - v[0].x) * (v[1].y - v[0].y));
    const float d1   = a1 - a0;
    const float d2   = a2 - a0;
    *gx = (d1 * (float) (v[2].y - v[0].y) - d2 * (float) (v[1].y - v[0].y)) / area;
    *gy = (d2 * (float) (v[1].x - v[0].x) - d1 * (float) (v[2].x - v[0].x)) / area;
}

/* An edge's Bresenham terms, one scan line down at a time, X moving the edge's way */
static void edge(int xa, int ya, int xb, int yb, u32 *err, u32 *inc, u32 *dec) {
    const int dx = (xb > xa) ? (xb - xa) : (xa - xb);
    const int dy = yb - ya;
    *err = (u32) -dy;
    *inc = (u32) (2 * dx);
    *dec = (u32) (-2 * dy);
}

static u32 c16(float v) { return ((u32) (int) (v * 65536.0f)) & 0x01fffff0u; }
static u32 z12(float v) { return ((u32) (int) (v * 4096.0f)) & 0x1fffffffu; }

static u32 inc2_on;

/* The interpolators at v[0], stepping lead_dir across and down */
static void interpolators(const vertex_t *v, int lead_dir) {
    float gx, gy;
#define ATTR(f, enc, start, xinc, yinc)                       \
    plane(v, v[0].f, v[1].f, v[2].f, &gx, &gy);              \
    reg(start, enc(v[0].f));                                  \
    reg(xinc, enc(gx * (float) lead_dir));                    \
    reg(yinc, enc(gy))
    ATTR(r, c16, RED_START, RED_X_INC, RED_Y_INC);
    ATTR(g, c16, GREEN_START, GREEN_X_INC, GREEN_Y_INC);
    ATTR(b, c16, BLUE_START, BLUE_X_INC, BLUE_Y_INC);
    ATTR(a, c16, ALPHA_START, ALPHA_X_INC, ALPHA_Y_INC);
    ATTR(z, z12, Z_START, Z_X_INC, Z_Y_INC);
#undef ATTR
    plane(v, v[0].s, v[1].s, v[2].s, &gx, &gy);
    reg(S_START, ((u32) (int) v[0].s) & 0x03ffffe0u);
    reg(S_XINC_START, ((u32) (int) (gx * (float) lead_dir)) & 0x0fffffffu);
    reg(S_Y_INC, ((u32) (int) gy) & 0x0fffffffu);
    plane(v, v[0].t, v[1].t, v[2].t, &gx, &gy);
    reg(T_START, ((u32) (int) v[0].t) & 0x03ffffe0u);
    reg(T_XINC_START, ((u32) (int) (gx * (float) lead_dir)) & 0x0fffffffu);
    reg(T_Y_INC, ((u32) (int) gy) & 0x0fffffffu);
    reg(S_X_INC2, inc2_on ? 0x00000400u : 0);
    reg(S_Y_INC2, inc2_on ? 0x07fffc00u : 0);
    reg(S_XY_INC2, inc2_on ? 0x00000200u : 0);
    reg(T_X_INC2, inc2_on ? 0x07fffe00u : 0);
    reg(T_Y_INC2, inc2_on ? 0x00000300u : 0);
    reg(T_XY_INC2, inc2_on ? 0x07ffff00u : 0);
}

/* A triangle as two trapezoids: the leading edge v0 to v2 (the long one), the trailing edges v0 to v1, then v1
   to v2 */
static void triangle(const vertex_t *in, int r2l) {
    vertex_t v[3] = { in[0], in[1], in[2] };
    for (int a = 0; a < 2; a++)
        for (int b = 0; b < 2 - a; b++)
            if (v[b].y > v[b + 1].y) {
                const vertex_t t = v[b];
                v[b]             = v[b + 1];
                v[b + 1]         = t;
            }
    if ((v[0].y == v[1].y) || (v[1].y == v[2].y))
        return;
    const int lead_dir = (v[2].x >= v[0].x) ? 1 : -1;
    /* The leading edge left of v1: filled left to right from it; or the other way, as asked */
    const int lead_left = ((v[2].x - v[0].x) * (v[1].y - v[0].y)) < ((v[1].x - v[0].x) * (v[2].y - v[0].y));
    if (r2l && lead_left)
        return;
    u32 err, inc, dec;
    interpolators(v, lead_dir);
    reg(DST_Y_X, ((u32) (v[0].x & 0x1fff) << 16) | (u32) (v[0].y & 0x7fff));
    edge(v[0].x, v[0].y, v[2].x, v[2].y, &err, &inc, &dec);
    reg(DST_BRES_ERR, err);
    reg(DST_BRES_INC, inc);
    reg(DST_BRES_DEC, dec);
    for (int half = 0; half < 2; half++) {
        const vertex_t *a = &v[half];
        const vertex_t *b = &v[half + 1];
        edge(a->x, a->y, b->x, b->y, &err, &inc, &dec);
        reg(DST_CNTL, ((lead_dir > 0) ? X_DIR : 0) | Y_DIR | ((b->x >= a->x) ? TRAIL_DIR : 0) | (lead_left ? FILL_L2R : 0));
        reg(TRAIL_BRES_ERR, err);
        reg(TRAIL_BRES_INC, inc);
        reg(TRAIL_BRES_DEC, dec);
        reg(DST_BRES_LNTH, LOAD_TRAIL | ((u32) (a->x & 0x1fff) << 16) | DRAW_TRAP | (u32) (b->y - a->y));
    }
}

/* A 3D line from v[0] to v[1], its last pixel drawn */
static void line3d(const vertex_t *v) {
    const int dx  = v[1].x - v[0].x, dy = v[1].y - v[0].y;
    const int adx = (dx < 0) ? -dx : dx, ady = (dy < 0) ? -dy : dy;
    const int ymaj = ady > adx;
    const int major = ymaj ? ady : adx, minor = ymaj ? adx : ady;
    if (major == 0)
        return;
    const float steps = (float) major;
    reg(RED_START, c16(v[0].r));
    reg(GREEN_START, c16(v[0].g));
    reg(BLUE_START, c16(v[0].b));
    reg(ALPHA_START, c16(v[0].a));
    reg(Z_START, z12(v[0].z));
    reg(S_START, ((u32) (int) v[0].s) & 0x03ffffe0u);
    reg(T_START, ((u32) (int) v[0].t) & 0x03ffffe0u);
    /* The steps along the major axis carry the whole change, the minor axis none */
    const u32 rx = c16((v[1].r - v[0].r) / steps), gx = c16((v[1].g - v[0].g) / steps), bx = c16((v[1].b - v[0].b) / steps);
    const u32 ax = c16((v[1].a - v[0].a) / steps), zx = z12((v[1].z - v[0].z) / steps);
    const u32 sx = ((u32) (int) ((v[1].s - v[0].s) / steps)) & 0x0fffffffu, tx = ((u32) (int) ((v[1].t - v[0].t) / steps)) & 0x0fffffffu;
    reg(ymaj ? RED_Y_INC : RED_X_INC, rx);
    reg(ymaj ? RED_X_INC : RED_Y_INC, 0);
    reg(ymaj ? GREEN_Y_INC : GREEN_X_INC, gx);
    reg(ymaj ? GREEN_X_INC : GREEN_Y_INC, 0);
    reg(ymaj ? BLUE_Y_INC : BLUE_X_INC, bx);
    reg(ymaj ? BLUE_X_INC : BLUE_Y_INC, 0);
    reg(ymaj ? ALPHA_Y_INC : ALPHA_X_INC, ax);
    reg(ymaj ? ALPHA_X_INC : ALPHA_Y_INC, 0);
    reg(ymaj ? Z_Y_INC : Z_X_INC, zx);
    reg(ymaj ? Z_X_INC : Z_Y_INC, 0);
    reg(ymaj ? S_Y_INC : S_XINC_START, sx);
    reg(ymaj ? S_XINC_START : S_Y_INC, 0x00010000u);
    reg(ymaj ? T_Y_INC : T_XINC_START, tx);
    reg(ymaj ? T_XINC_START : T_Y_INC, 0x0fff8000u);
    reg(S_X_INC2, 0);
    reg(S_Y_INC2, 0);
    reg(S_XY_INC2, 0);
    reg(T_X_INC2, 0);
    reg(T_Y_INC2, 0);
    reg(T_XY_INC2, 0);
    reg(DST_Y_X, ((u32) (v[0].x & 0x1fff) << 16) | (u32) (v[0].y & 0x7fff));
    reg(DST_CNTL, ((dx >= 0) ? X_DIR : 0) | ((dy >= 0) ? Y_DIR : 0) | (ymaj ? Y_MAJOR : 0) | LAST_PEL);
    reg(DST_BRES_ERR, (u32) -major & 0x3ffffu);
    reg(DST_BRES_INC, (u32) (2 * minor) & 0x3ffffu);
    reg(DST_BRES_DEC, (u32) (-2 * major) & 0x3ffffu);
    reg(DST_BRES_LNTH, (u32) (major + 1));
}

static void vertices(vertex_t *v, int count, u32 salt, u32 minify, int width) {
    for (int j = 0; j < count; j++) {
        const u32 g = pattern((u32) j, 7, salt);
        v[j].x = 4 + (int) (g % (u32) (width - 8));
        v[j].y = 4 + (int) ((g >> 12) % 472u);
        v[j].r = (float) ((g >> 3) & 255);
        v[j].g = (float) ((g >> 11) & 255);
        v[j].b = (float) ((g >> 19) & 255);
        v[j].a = (float) ((g >> 5) & 255);
        v[j].z = (float) (500 + (g % 64000));
        /* S and T: a 256-texel map is 1 << 26; a texel 1 << 18, magnified about half a texel a pixel, minified
           1 << minify texels a pixel */
        const float per_pixel = (minify == 0) ? 131072.0f : (float) (262144u << minify);
        v[j].s = (float) v[j].x * per_pixel + (float) ((g >> 9) & 0xffff) * 64.0f;
        v[j].t = (float) v[j].y * per_pixel + (float) ((g >> 17) & 0x7fff) * 128.0f;
    }
}

void test_main(void) {
    __asm__ volatile("fninit");
    int found = 0;
    for (u32 bus = 0; bus < 2 && !found; bus++)
        for (u32 dev = 0; dev < 32 && !found; dev++)
            if (pci_read(bus, dev, 0, 0) == 0x47551002u)
                found = 1;
    if (!found)
        return;
    const u16 mode = vbe_find(640, 480, 16);
    if (!mode || (int10(0x4f02, mode | 0x4000, 0, 0, 0, 0) != 0x004f)) {
        *(volatile u16 *) 0xb8000 = 0x4f56;
        wait_ticks(40);
        return;
    }
    const u32 lfb = VBE_MODE->framebuffer;
    mmio          = (volatile u32 *) ((lfb & ~0x7fffffu) + 0x7ffc00u);

    /* The texture area, 2 MB to 3 MB: the pattern; the maps of a 256 x 256 chain, each level after the last */
    volatile u32 *tex = (volatile u32 *) (lfb + 0x200000);
    for (u32 i = 0; i < 0x40000; i++)
        tex[i] = pattern(i & 1023, i >> 10, 0x64);
    u32 off = 0x200000;
    for (int level = 8; level >= 0; level--) {
        reg(TEX_0_OFF + 4 * (u32) level, off);
        off += (1u << (2 * level)) * 4;
    }
    for (int k = 9; k <= 10; k++)
        reg(TEX_0_OFF + 4 * (u32) k, 0x200000);
    reg(TEX_SIZE_PITCH, 0x888);
    for (u32 i = 0; i < 256; i++)
        reg(TEX_PALETTE, (i << 24) | (pattern(i, 1, 0x77) & 0xffffff));
    reg(Z_OFF_PITCH, ((640u / 8) << 22) | (0x100000u / 8));
    reg(DP_BKGD_CLR, 0x00305070);
    reg(CLR_CMP_CLR, 0x00000000);

    for (u32 p = 0; p < sizeof(passes) / sizeof(passes[0]); p++) {
        const pass_t *ps    = &passes[p];
        const u32     bpp   = bytes_of(ps->dst);
        const int     width = (int) (1280 / bpp);
        /* The clear: the frame and the Z buffer through the linear frame buffer */
        volatile u32 *fb = (volatile u32 *) lfb;
        for (u32 i = 0; i < 640 * 480 / 2; i++)
            fb[i] = pattern(i % 320, i / 320, 0x40 + p) & 0x7bef7befu;
        volatile u32 *zb = (volatile u32 *) (lfb + 0x100000);
        const u32     zc = (p & 1) ? 0x80008000u : 0x40004000u;
        for (u32 i = 0; i < 640 * 480 / 2; i++)
            zb[i] = zc;

        reg(DST_OFF_PITCH, ((u32) (width / 8) << 22) | 0);
        reg(SC_LEFT_RIGHT, (ps->flags & P_SCISSOR) ? ((((u32) width * 3 / 4) << 16) | 40u) : (((u32) (width - 1) << 16) | 0u));
        reg(SC_TOP_BOTTOM, (ps->flags & P_SCISSOR) ? ((400u << 16) | 60u) : ((479u << 16) | 0u));
        reg(DP_PIX_WIDTH, ((u32) ps->tex << 28) | ((ps->flags & P_CI4) ? ((1u << 26) | (5u << 20)) : 0) | ((u32) ps->dst << 8) | ps->dst);
        reg(DP_SRC, (ps->flags & P_CONST) ? (1u << 8) : (5u << 8));
        reg(DP_FRGD_CLR, (ps->flags & P_CONST) ? 0x0000a5c3u : 0x00c08040u);
        reg(WRITE_MASK, (ps->flags & P_WMASK) ? 0x0000f0f0u : 0xffffffffu);
        reg(CLR_CMP_MASK, (ps->flags & P_KEY) ? 0x000000f0u : 0x00000f00u);
        reg(CLR_CMP_CNTL, (ps->flags & P_DSTCMP) ? 4u : (ps->flags & P_KEY) ? ((2u << 24) | 5u) : 0u);
        reg(CLR_CMP_CLR, (ps->flags & P_KEY) ? 0x00000050u : 0x00000300u);
        if (ps->flags & P_FEEDBACK) {
            /* The texture is the picture being drawn on */
            for (int level = 0; level <= 10; level++)
                reg(TEX_0_OFF + 4 * (u32) level, 0x2000);
        }
        reg(SCALE_3D_CNTL, ps->cntl);
        reg(Z_CNTL, ps->z);
        inc2_on = (ps->flags & P_INC2) != 0;

        vertex_t v[36];
        vertices(v, 36, 0x900 + p, ps->minify, width);
        if (ps->flags & P_LINES) {
            for (int i = 0; i + 1 < 36; i += 2)
                line3d(&v[i]);
        } else {
            for (int i = 0; i + 2 < 36; i += 3)
                triangle(&v[i], (ps->flags & P_R2L) != 0);
        }
        if (ps->flags & P_FEEDBACK) {
            u32 o = 0x200000;
            for (int level = 8; level >= 0; level--) {
                reg(TEX_0_OFF + 4 * (u32) level, o);
                o += (1u << (2 * level)) * 4;
            }
            for (int k = 9; k <= 10; k++)
                reg(TEX_0_OFF + 4 * (u32) k, 0x200000);
        }
        wait_ticks(4);
    }
}
