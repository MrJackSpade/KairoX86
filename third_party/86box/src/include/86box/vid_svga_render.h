/*
 * 86Box    A hypervisor and IBM PC system emulator that specializes in
 *          running old operating systems and software designed for IBM
 *          PC systems and compatibles from 1981 through fairly recent
 *          system designs based on the PCI bus.
 *
 *          This file is part of the 86Box distribution.
 *
 *          SVGA renderers.
 *
 * Authors: Sarah Walker, <https://pcem-emulator.co.uk/>
 *          Miran Grca, <mgrca8@gmail.com>
 *
 *          Copyright 2008-2018 Sarah Walker.
 *          Copyright 2016-2018 Miran Grca.
 */
#ifndef VIDEO_SVGA_RENDER_H
#define VIDEO_SVGA_RENDER_H

#include <stdbool.h> /* KairoX86#248: svga_render_gpu_bits */

extern int firstline_draw;
extern int lastline_draw;
extern int displine;
extern int scanline;

extern uint32_t memaddr;
extern uint32_t cursoraddr;
extern int      cursorvisible;
extern int      cursoron;
extern int      cgablink;

extern int scrollcache;

extern uint8_t edatlookup[4][4];
extern uint8_t egaremap2bpp[256];

extern void svga_recalc_remap_func(svga_t *svga);

extern void svga_render_null(svga_t *svga);
/* Wait until every queued line is drawn (vid_svga_render.c) */
extern void svga_render_drain(void);
extern void svga_render_close(void); /* KairoX86: ends the drawing thread */
extern void svga_render_blank(svga_t *svga);
/* KairoX86#233, #248: a line of pixels of bits bits each (most significant first, over the bytes in the order the card
   scans them) to the GPU's scanout queue at p through colours (n of them), for the shared renderers and a card's
   own; NULL (the CPU draws it) when the GPU is off, the line is not eligible (the installed renderer is not the
   caller) or something else draws on it. The caller writes the line's bytes there, then kairo_gpu_scan_commit(). */
extern uint8_t *svga_render_gpu_bits(svga_t *svga, uint32_t *p, uint32_t bits, uint32_t pixels, bool wide,
                                     const uint32_t *colours, uint32_t n, bool eligible);
extern void svga_render_overscan_left(svga_t *svga);
extern void svga_render_overscan_right(svga_t *svga);
extern void svga_render_text_40(svga_t *svga);
extern void svga_render_text_80(svga_t *svga);
extern void svga_render_text_80_ksc5601(svga_t *svga);

extern void svga_render_2bpp_lowres(svga_t *svga);
extern void svga_render_2bpp_highres(svga_t *svga);
extern void svga_render_2bpp_s3_lowres(svga_t *svga);
extern void svga_render_2bpp_s3_highres(svga_t *svga);
extern void svga_render_2bpp_headland_highres(svga_t *svga);
extern void svga_render_4bpp_lowres(svga_t *svga);
extern void svga_render_4bpp_highres(svga_t *svga);
extern void svga_render_8bpp_lowres(svga_t *svga);
extern void svga_render_8bpp_highres(svga_t *svga);
extern void svga_render_4bpp_tseng_highres(svga_t *svga);
extern void svga_render_8bpp_clone_highres(svga_t *svga);
extern void svga_render_8bpp_tseng_lowres(svga_t *svga);
extern void svga_render_8bpp_tseng_highres(svga_t *svga);
extern void svga_render_15bpp_lowres(svga_t *svga);
extern void svga_render_15bpp_highres(svga_t *svga);
extern void svga_render_15bpp_mix_lowres(svga_t *svga);
extern void svga_render_15bpp_mix_highres(svga_t *svga);
extern void svga_render_16bpp_lowres(svga_t *svga);
extern void svga_render_16bpp_highres(svga_t *svga);
extern void svga_render_24bpp_lowres(svga_t *svga);
extern void svga_render_24bpp_highres(svga_t *svga);
extern void svga_render_32bpp_lowres(svga_t *svga);
extern void svga_render_32bpp_highres(svga_t *svga);
extern void svga_render_ABGR8888_lowres(svga_t *svga);
extern void svga_render_ABGR8888_highres(svga_t *svga);
extern void svga_render_RGBA8888_lowres(svga_t *svga);
extern void svga_render_RGBA8888_highres(svga_t *svga);

extern void ibm8514_render_blank(svga_t *svga);
extern void ibm8514_render_8bpp(svga_t *svga);
extern void ibm8514_render_15bpp(svga_t *svga);
extern void ibm8514_render_16bpp(svga_t *svga);
extern void ibm8514_render_24bpp(svga_t *svga);
extern void ibm8514_render_BGR(svga_t *svga);
extern void ibm8514_render_32bpp(svga_t *svga);
extern void ibm8514_render_ABGR8888(svga_t *svga);
extern void ibm8514_render_RGBA8888(svga_t *svga);

extern void (*svga_render)(svga_t *svga);

#endif /*VID_SVGA_RENDER_H*/
