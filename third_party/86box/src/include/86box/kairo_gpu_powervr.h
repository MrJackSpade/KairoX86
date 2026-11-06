/*
 * The PowerVR PCX2's tiles on the GPU (KairoX86#269; core/kairo/gpu_powervr.c, core/kairo/shaders/powervr.comp):
 * with the machine's Hardware acceleration on, a prepared frame (pcxr_prepare, vid_powervr_pcx_render.c) is drawn
 * by one kernel instead of pcxr_render_tiles: every span of 32 cells (one work group, an invocation a cell) runs
 * the tile's planes through its cells and shades them, as the render threads do, into the frame's RGB buffer. The
 * planes are decoded and each span's instruction-decoder schedule worked out on the CPU (pcxr_gpu_lists), in the
 * order pcxr_render_tiles walks them.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_POWERVR_H
#define KAIRO_GPU_POWERVR_H

#include <stdint.h>

/* A plane, as words: A and B 64-bit (low word first), C, the TSP index, the instruction */
enum { KP_A = 0, KP_B = 2, KP_C = 4, KP_INDEX = 5, KP_INSTR = 6, KP_WORDS = 8 };
/* An object: its first plane, its planes, whether it ends its region */
enum { KO_FIRST = 0, KO_COUNT = 1, KO_LAST_IN_REGION = 2, KO_WORDS = 4 };
/* A span: its tile's first object and objects, its first cell's X, its line, its schedule (a word for each of the
   tile's planes from its first object's first plane on) */
enum { KN_FIRST_OBJECT = 0, KN_N_OBJECTS = 1, KN_X = 2, KN_Y = 3, KN_SCHED = 4, KN_P0 = 5, KN_WORDS = 8 };
/* A schedule word: a plane's cell control (cell_control), and whether it runs */
#define KAIRO_PVR_RUN(w)    ((w) & 1u)
#define KAIRO_PVR_I_LOAD(w) (((w) >> 1) & 15u)
#define KAIRO_PVR_U_LOAD(w) (((w) >> 5) & 3u)
#define KAIRO_PVR_SHAD(w)   (((w) >> 7) & 3u)
#define KAIRO_PVR_VISIB(w)  (((w) >> 9) & 1u)
#define KAIRO_PVR_CLEAR(w)  (((w) >> 10) & 1u)
#define KAIRO_PVR_PERP(w)   (((w) >> 11) & 1u)
#define KAIRO_PVR_MUX(w)    (((w) >> 12) & 1u)

/* The frame's registers the shading reads, as words, then the fog table (128 words) */
enum { KF_FOG_SHIFT = 0, KF_FOG_COLOUR = 1, KF_CAMERA = 2, KF_XCLIP = 3, KF_BILINEAR = 4, KF_TEX_WORDS = 5,
       KF_FOG_TABLE = 8, KF_WORDS = 136 };

/* A prepared frame's lists (vid_powervr_pcx_render.c owns the memory) */
typedef struct kairo_pvr_lists {
    const uint32_t *planes, *objects, *spans, *sched, *frame;
    uint32_t        n_planes, n_objects, n_spans, n_sched;
} kairo_pvr_lists_t;

/* The card's GPU state: its texture memory and RGB buffer shared with the GPU (kairo_gpu_alloc) */
void *kairo_pvr_gpu_open(uint32_t *tex, uint32_t tex_words, uint32_t *rgb);
void  kairo_pvr_gpu_close(void *gpu);
/* Draws a prepared frame's spans into the RGB buffer; returns once they are drawn */
void kairo_pvr_gpu_render(void *gpu, const kairo_pvr_lists_t *lists);

#endif
