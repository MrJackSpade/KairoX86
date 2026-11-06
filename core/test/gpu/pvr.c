/*
 * KairoX86's PowerVR PCX2 test (KairoX86#283, for #269): with a PowerVR PCX2 (PCI 1033h:0046h) beside an S3 2D card
 * in VESA 640 x 480 x 16 with S3's linear addressing, a series of frames the PCX2 draws into that frame
 * buffer, each over a clear and held four ticks of the BIOS clock. A frame's display list (the ISP parameter store,
 * in system RAM at 2 MB through the TLB) is regions of the screen, each with triangles: a depth plane and three
 * edge planes, a fifth plane starting the translucent pass for some. Their surfaces (TSP parameters in texture
 * memory, which holds a pattern) are flat, smooth shaded, highlighted, textured in each map size and format (8-bit,
 * 555, 4444, mip mapped, mirrored), translucent, fogged and the masking plane. The frames cover each packing (565
 * with and without dither, 555, 24 and 32 bits), the bilinear modes and the X clip. The end of each render is
 * waited for through INTSTATUS (#294 puts it at its emulated time). Any machine without a PCX2 returns at once.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "runtime.h"

static u32 pci_read(u32 bus, u32 dev, u32 fn, u32 reg_) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    return inl(0xcfc);
}

static void pci_write(u32 bus, u32 dev, u32 fn, u32 reg_, u32 v) {
    outl(0xcf8, 0x80000000u | (bus << 16) | (dev << 11) | (fn << 8) | (reg_ & 0xfc));
    outl(0xcfc, v);
}

static volatile u32 *regs;
static volatile u32 *tex;
static volatile u32 *isp;

enum {
    INTSTATUS = 0x003, INTMASK = 0x004, STARTRENDER = 0x005, FOGAMOUNT = 0x006, OBJECT_OFFSET = 0x007,
    PAGE_CTRL = 0x008, FOGCOL = 0x00e, CAMERA = 0x00f, PACKMODE = 0x010, LSTRIDE = 0x012, SOFADDR = 0x013,
    XCLIP = 0x014, BILINEAR = 0x019, TLB = 0x100,
};

/* ISP plane instructions */
#define FORW_PERP     2u
#define FORW_VISIB_FP 8u
#define BEGIN_TRANS   15u

/* TSP control word */
#define T_TEXTURE   0x80000000u
#define T_SMOOTH    0x40000000u
#define T_NOFOG     0x20000000u
#define T_HIGHLIGHT 0x04000000u
#define T_EXP(e)    ((u32) (e) << 18)
#define T_GTRANS(g) ((u32) (g) << 13)
#define T_FLIP(f)   ((u32) (f) << 11)
#define T_TRANS     0x00000400u
/* TSP word 6 */
#define M_MIP      0x80000000u
#define M_16       0x40000000u
#define M_SIZE(s)  ((u32) (s) << 28)
#define M_4444     0x08000000u

#define PLANES_AT 0x8000u  /* the planes' word offset in the ISP store */
#define TSP_AT    0x10000u /* the surfaces' word address in texture memory */

typedef struct {
    u32 packmode, bilinear, xclip, fog;
} frame_t;

static const frame_t frames[] = {
    { 0x02, 0, 0, 0 },
    { 0x12, 0, 0, 0 },
    { 0x03, 1, 0, 0x01406080u },
    { 0x13, 3, 0x10000000u | (500u << 16), 0 },
    { 0x02, 1, 0x00001000u | 80u, 0x01c08040u },
    { 0x00, 0, 0, 0 },
    { 0x01, 3, 0, 0x01204060u },
};

static u32 isp_word;  /* the next region-list word */
static u32 plane_word;
static u32 tsp_word;

static u32 fbits(float f) {
    union {
        float f;
        u32   u;
    } v;
    v.f = f;
    return v.u;
}

static void plane(float a, float b, float c, u32 instr, u32 index) {
    isp[plane_word++] = fbits(a);
    isp[plane_word++] = fbits(b);
    isp[plane_word++] = fbits(c);
    isp[plane_word++] = instr | (index << 4);
}

/* A surface's TSP words, from its kind; returns its word address */
static u32 surface(u32 kind, u32 salt) {
    const u32 at = tsp_word;
    u32       w[12];
    for (int i = 0; i < 12; i++)
        w[i] = pattern((u32) i, kind, salt);
    const u32 tex_kind = kind % 7;
    u32       w0       = w[0] & 0xffu;
    if (kind & 1)
        w0 |= T_SMOOTH;
    if (kind & 8)
        w0 |= T_HIGHLIGHT;
    if ((kind % 5) == 4)
        w0 |= T_NOFOG;
    if ((kind % 3) == 0) {
        w0 |= T_TEXTURE | T_EXP(6 + w[1] % 9) | T_FLIP(kind >> 4) | T_GTRANS(w[2] & 3);
        /* words 2-7: pmip, r, q p, addr c, b a, map f, e d; small texture gradients */
        w[2] = (w[2] & 0xfffc0000u) | 0x4000u;
        w[3] = 0;
        w[4] = (w[4] & 0xffff0000u) | (w[4] & 0x00ffu);
        w[5] = ((w[5] & 0x1fffu) << 16) | (w[5] & 0x1fffu);
        w[7] = ((w[7] & 0x1fffu) << 16) | ((w[7] >> 16) & 0x1fffu);
        const u32 map = (tex_kind == 0) ? 0 : (tex_kind == 1) ? (M_16 | M_SIZE(1)) : (tex_kind == 2) ? (M_16 | M_4444 | M_SIZE(2))
                       : (tex_kind == 3) ? (M_16 | M_MIP | M_SIZE(0)) : (tex_kind == 4) ? (M_16 | M_MIP | M_4444 | M_SIZE(3))
                       : (tex_kind == 5) ? M_SIZE(3) : (M_16 | M_SIZE(0));
        w[6] = map | (w[6] & 0x003f0000u) | (w[6] & 0x00ffu);
    }
    if ((kind % 4) == 2)
        w0 |= T_TRANS;
    if (w0 & T_SMOOTH)
        w[1] = ((w[1] & 0x00ffu) << 16) | ((w[1] >> 16) & 0x00ffu); /* the shading's origin */
    tex[at] = w0;
    for (int i = 1; i < 12; i++)
        tex[at + (u32) i] = w[i];
    tsp_word += 12;
    return at;
}

/* A triangle: its depth plane on surface tsp (a TSP word address), its three edges inside where >= 0, and the
   translucent pass's start when asked */
static void triangle(const float *x, const float *y, float d0, float dx, float dy, u32 tsp, int trans) {
    plane(dx, dy, d0, FORW_VISIB_FP, tsp >> 1);
    const float cx = (x[0] + x[1] + x[2]) / 3.0f, cy = (y[0] + y[1] + y[2]) / 3.0f;
    for (int i = 0; i < 3; i++) {
        const int   j = (i + 1) % 3;
        float       a = y[j] - y[i], b = x[i] - x[j];
        float       c = -(a * x[i] + b * y[i]);
        if (a * cx + b * cy + c < 0.0f) {
            a = -a;
            b = -b;
            c = -c;
        }
        plane(a, b, c, FORW_PERP, 0);
    }
    if (trans)
        plane(0.0f, 0.0f, 0.0f, BEGIN_TRANS, 0);
}

static void build(u32 f) {
    isp_word   = 0;
    plane_word = PLANES_AT;
    tsp_word   = TSP_AT;
    /* The masking plane's surface at TSP word 2 */
    tex[2] = 0x00ff00ffu;
    tex[3] = 0x00ff0000u;
    /* Four regions: the screen's quarters, 320 x 240, of 32-pixel columns */
    for (u32 r = 0; r < 4; r++) {
        const u32 x0 = (r & 1) * 320, y0 = (r >> 1) * 240;
        isp[isp_word++] = 0x40000000u | (y0 << 20) | ((x0 / 32) << 15) | (239u << 5) | (320u / 32 - 1);
        const u32 n = 5 + (pattern(r, f, 0x11) % 6);
        for (u32 t = 0; t < n; t++) {
            const u32 g = pattern(t, r * 16 + f, 0x22);
            float     x[3], y[3];
            for (int k = 0; k < 3; k++) {
                const u32 h = pattern((u32) k, t, g);
                x[k] = (float) x0 - 20.0f + (float) (h % 360);
                y[k] = (float) y0 - 20.0f + (float) ((h >> 9) % 280);
            }
            const u32 kind = pattern(t, 9, g) % 64;
            const u32 tsp  = ((kind % 13) == 12) ? 2 : surface(kind, g);
            const u32 first = plane_word;
            const int trans = (kind % 4) == 2;
            triangle(x, y, 0.2f + (float) (g % 600) / 1000.0f, (float) ((int) (g >> 12) % 64 - 32) * 2e-5f,
                     (float) ((int) (g >> 18) % 64 - 32) * 2e-5f, tsp, trans);
            const u32 count = (plane_word - first) / 4;
            isp[isp_word++] = (count << 19) | first | (((r == 3) && (t == n - 1)) ? 0x80000000u : 0u);
        }
    }
}

void test_main(void) {
    __asm__ volatile("fninit");
    u32 bus = 0, dev = 0;
    int found = 0;
    for (bus = 0; bus < 2 && !found; bus++)
        for (dev = 0; dev < 32 && !found; dev++)
            if (pci_read(bus, dev, 0, 0) == 0x00461033u)
                found = 1;
    if (!found)
        return;
    bus--;
    dev--;
    regs = (volatile u32 *) (pci_read(bus, dev, 0, 0x10) & ~0xfu);
    tex  = (volatile u32 *) (pci_read(bus, dev, 0, 0x14) & ~0xfu);
    /* Memory and bus mastering on */
    pci_write(bus, dev, 0, 0x04, pci_read(bus, dev, 0, 0x04) | 0x06u);

    /* The 2D card (the batch's S3 Trio64): VESA 640 x 480 x 16 (mode 111h); its BIOS gives no linear frame buffer,
       so S3's own linear addressing is turned on (CR58 bit 4, a 4 MB window at its BAR0), as vir3d.c does */
    u32 lfb = 0;
    for (u32 b = 0; b < 2 && !lfb; b++)
        for (u32 d = 0; d < 32 && !lfb; d++)
            if ((pci_read(b, d, 0, 0) & 0xffff) == 0x5333)
                lfb = pci_read(b, d, 0, 0x10) & ~0xfu;
    if (!lfb || (int10(0x4f02, 0x111, 0, 0, 0, 0) != 0x004f)) {
        *(volatile u16 *) 0xb8000 = 0x4f56;
        wait_ticks(40);
        return;
    }
    outb(0x3d4, 0x38);
    outb(0x3d5, 0x48);
    outb(0x3d4, 0x39);
    outb(0x3d5, 0xa5);
    outb(0x3d4, 0x58);
    const u8 cr58 = inb(0x3d5);
    outb(0x3d5, (cr58 & ~0x03) | 0x13);

    /* Texture memory: the pattern */
    for (u32 i = 0; i < 0x100000; i++)
        tex[i] = pattern(i & 1023, i >> 10, 0x95);
    /* The ISP store: 128 pages of 4 KB from 2 MB */
    isp = (volatile u32 *) 0x200000;
    regs[PAGE_CTRL] = 0;
    for (u32 i = 0; i < 128; i++)
        regs[TLB + i] = (0x200000u >> 12) + i;
    regs[OBJECT_OFFSET] = 0;
    regs[INTMASK]       = 0;
    regs[SOFADDR]       = lfb;
    regs[FOGAMOUNT]     = 22;
    regs[CAMERA]        = 0x0100;

    for (u32 f = 0; f < sizeof(frames) / sizeof(frames[0]); f++) {
        const frame_t *fr = &frames[f];
        volatile u32  *fb = (volatile u32 *) lfb;
        for (u32 i = 0; i < 640 * 480 / 2; i++)
            fb[i] = pattern(i % 320, i / 320, 0x30 + f) & 0x7bef7befu;
        build(f);
        const u32 bpp = ((fr->packmode & 3) == 0) ? 4 : ((fr->packmode & 3) == 1) ? 3 : 2;
        regs[PACKMODE] = fr->packmode;
        regs[LSTRIDE]  = (bpp == 2) ? 1280 : 1280 / bpp * bpp;
        regs[BILINEAR] = fr->bilinear;
        regs[XCLIP]    = fr->xclip;
        regs[FOGCOL]   = fr->fog;
        (void) regs[INTSTATUS];
        regs[STARTRENDER] = 1;
        while (!(regs[INTSTATUS] & 2))
            ;
        wait_ticks(4);
    }
}
