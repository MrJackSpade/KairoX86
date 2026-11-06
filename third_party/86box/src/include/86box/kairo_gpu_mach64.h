/*
 * The ATI 3D Rage II+'s 3D engine on the GPU (KairoX86#237; core/kairo/gpu_mach64.c, core/kairo/shaders/mach64.comp):
 * with the machine's Hardware acceleration on, the rows a trapezoid or a 3D line walks (vid_ati_mach64_3d.c, as it
 * hands them to mach64_3d_draw_row), and the lines of a scaled rectangle (the front-end scaler), are recorded with
 * their draw's state instead of drawn, and the recorded rows are
 * drawn by one kernel wherever the processor, the display, the 2D engine or the scaler is about to read or write
 * video memory they draw on (the touch).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_MACH64_H
#define KAIRO_GPU_MACH64_H

#include <stdint.h>

/* A draw's record (one call of mach64_3d_draw_rows: its job and the registers its pixels read), as words */
enum {
    KM_FLAGS        = 0, /* KAIRO_M64_* | alpha_fog << 8 */
    KM_CNTL         = 1, /* SCALE_3D_CNTL */
    KM_Z_CNTL       = 2,
    KM_DST_BASE     = 3,
    KM_DST_PITCH    = 4, /* pixels */
    KM_DST_FORMAT   = 5,
    KM_DST_BPP      = 6, /* bytes */
    KM_Z_BASE       = 7,
    KM_Z_PITCH      = 8,
    KM_FOG          = 9, /* DP_FRGD_CLR */
    KM_CLR_CMP_CNTL = 10,
    KM_CLR_CMP_CLR  = 11,
    KM_CLR_CMP_MASK = 12,
    KM_WRITE_MASK   = 13,
    KM_DP_SRC       = 14,
    KM_DP_BKGD_CLR  = 15,
    KM_DP_FRGD_CLR  = 16,
    KM_DP_PIX_WIDTH = 17,
    KM_PALETTE      = 18, /* the draw's palettes in the palette pool (core/kairo/gpu_mach64.c fills it) */
    KM_RX           = 19, /* rx gx bx ax zx: the low words (the pixels read only the fields' low bits) */
    KM_SX2          = 24, /* sx2 tx2 sxy2 txy2: 32-bit values */
    KM_TEX_FORMAT   = 28,
    KM_TEX_BPP      = 29,
    KM_TEX_DYNAMIC  = 30,
    KM_KEY_FCN      = 31,
    KM_KEY          = 32,
    KM_KEY_MASK     = 33,
    KM_MAX_LOD      = 34,
    KM_LEVELS       = 35, /* the maps the pixels read: max_lod + 1 with mip mapping, else 1 (0 untextured) */
    KM_MAPS         = 36, /* [11][KM_MAP_WORDS] */
    KM_WORDS        = 104,
};

/* A texture map in the record, as words */
enum {
    KM_MAP_BASE        = 0,
    KM_MAP_PITCH_LOG2  = 1,
    KM_MAP_WIDTH_MASK  = 2,
    KM_MAP_HEIGHT_MASK = 3,
    KM_MAP_COORD_SHIFT = 4,
    KM_MAP_HEIGHT_LOG2 = 5,
    KM_MAP_WORDS       = 6,
};

/* A scaled rectangle's record (mach64_scaler_draw; KAIRO_M64_SCALER): KM_FLAGS, KM_CNTL, the destination (KM_DST_*),
   the compare, KM_WRITE_MASK, KM_DP_PIX_WIDTH and KM_PALETTE as a draw's, then these. Its rows are its destination
   lines, each from its first pixel to one past its last, left to right. */
enum {
    KS_SRC_BASE   = 36,
    KS_SRC_WIDTH  = 37,
    KS_SRC_HEIGHT = 38,
    KS_SRC_PITCH  = 39,
    KS_SRC_FORMAT = 40,
    KS_X_INC      = 41,
    KS_XUV_INC    = 42,
    KS_Y_INC      = 43,
    KS_H_START    = 44,
    KS_UV_START   = 45,
    KS_V_START    = 46,
    KS_DST_X      = 47,
    KS_DST_Y      = 48,
    KS_DP_MIX     = 49,
};

/* KM_FLAGS */
#define KAIRO_M64_TEXTURED    0x01u
#define KAIRO_M64_Z_ENABLED   0x02u
#define KAIRO_M64_Z_WRITE     0x04u
#define KAIRO_M64_DST_COMPARE 0x08u
#define KAIRO_M64_DP_CONSTANT 0x10u
#define KAIRO_M64_LINE        0x20u /* a 3D line's pixels: a pixel outside the depth buffer is not drawn */
#define KAIRO_M64_LEAD_LEFT   0x40u /* DST_X_DIR right to left (a scaled rectangle's too: its pixels go that way) */
#define KAIRO_M64_SCALER      0x80u /* a scaled rectangle's record */
/* bits 8 and 9: alpha_fog */
#define KAIRO_M64_Y_UP        0x400u /* a scaled rectangle's lines going up (DST_Y_DIR 0) */
#define KAIRO_M64_REPLICATE   0x800u /* SCALE_PIX_REP */

/* A row (mach64_3d_row_t), as words; 64-bit values low word first */
enum {
    KR_Y     = 0,
    KR_FIRST = 1,
    KR_END   = 2,
    KR_LEAD  = 3,
    KR_DRAW  = 4, /* its draw's record (core/kairo/gpu_mach64.c fills it) */
    KR_R     = 5, /* r g b a z: the low words */
    KR_S     = 10, /* s sxi syi t txi tyi: 64-bit */
    KR_WORDS = 22,
};

/* The palettes a draw reads: the texture palette, then the RAMDAC's (svga pallook) */
#define KAIRO_M64_PALETTE_WORDS 512

/* The 2D engine's operation record (vid_ati_mach64_accel.c, core/kairo/shaders/mach64_2d.comp), as words */
enum {
    M2_FLAGS = 0, M2_DST_SIZE = 1, M2_SRC_SIZE = 2, M2_DST_OFFSET = 3, M2_DST_PITCH = 4, M2_SRC_OFFSET = 5, M2_SRC_PITCH = 6,
    M2_POLY_OFFSET = 7, M2_MIX_FG = 8, M2_MIX_BG = 9, M2_SOURCE_FG = 10, M2_SOURCE_BG = 11, M2_SOURCE_MIX = 12,
    M2_PAT_CNTL = 13, M2_PATTERN = 14 /* [2]: bit y * 8 + x */, M2_CLR4X2 = 16 /* [2] */, M2_CLR8X1 = 18 /* [2] */,
    M2_CLR8X8 = 20 /* [16] */, M2_SC_LEFT = 36, M2_SC_RIGHT = 37, M2_SC_TOP = 38, M2_SC_BOTTOM = 39, M2_FG = 40,
    M2_BG = 41, M2_WRITE_MASK = 42, M2_CMP_CLR = 43, M2_CMP_MASK = 44, M2_CMP_FN = 45, M2_CMP_SRC = 46, M2_XINC = 47,
    M2_YINC = 48, M2_ROT0 = 49, M2_DST_X = 50, M2_DST_Y = 51, M2_WIDTH = 52, M2_SX1 = 53, M2_SY1 = 54, M2_SX2 = 55,
    M2_SY2 = 56, M2_W1 = 57, M2_H1 = 58, M2_W2 = 59, M2_H2 = 60, M2_CHAIN = 61, M2_BNDRY = 62,
    M2_HOST = 63 /* host data: row r's pixel p at stream[M2_HOST + r * M2_WIDTH + p] */, M2_LIN_L1 = 64,
    M2_LIN_STEP = 65, M2_LINE_SRC_Y = 66, M2_WORDS = 72
};
/* M2_FLAGS */
#define M2F_LINE      0x001u
#define M2F_ROT       0x002u /* DST_24_ROT_EN */
#define M2F_PIX_ORDER 0x004u /* DP_BYTE_PIX_ORDER */
#define M2F_LINEAR    0x008u /* SRC_LINEAR_EN */
#define M2F_POLYGON   0x010u /* a rectangle's DST_POLYGON_EN */
#define M2F_RTEDGE    0x020u /* DST_POLYGON_RTEDGE_DIS, on the CT and later */
#define M2F_BRUSH     0x040u /* the VT3's 8x8x8 brush */
#define M2F_PATT_ROT  0x080u /* SRC_PATT_EN and SRC_PATT_ROT_EN */
#define M2F_PATT_EN   0x100u
#define M2F_BNDRY     0x400u /* MEM_BNDRY_EN */
/* A line pixel's stream words: dst_x, its drawn X, dst_y, src_x, the host pixel */
#define M2_LINE_PIXEL_WORDS 5

/* The 2D engine's batch on the GPU (kairo_gpu_seg.h) */
struct kairo_seg;
struct kairo_seg *kairo_mach64_2d_open(uint8_t *vram, uint32_t vram_mask, uint8_t *changed, const int *stamp);

/* The card's GPU state, its video memory shared with the GPU (kairo_gpu_alloc); dither is the 3D engine's X error
   diffusion state (valid, y, three errors), which the GPU carries while it draws */
void *kairo_mach64_gpu_open(uint8_t *vram, uint32_t vram_mask, int32_t *dither);
void  kairo_mach64_gpu_close(void *gpu);
/* A draw: its record (KM_WORDS words), palettes (KAIRO_M64_PALETTE_WORDS words) and count rows (KR_WORDS words
   each) */
void kairo_mach64_gpu_draw(void *gpu, const uint32_t *record, const uint32_t *palettes, const uint32_t *rows, int count);
/* Draws every recorded row */
void kairo_mach64_gpu_drain(void *gpu);
/* The processor, the display or another engine reads or writes len bytes at addr: draws first if a recorded row
   draws there or reads a texture there */
void kairo_mach64_gpu_touch(void *gpu, uint32_t addr, uint32_t len);

#endif
