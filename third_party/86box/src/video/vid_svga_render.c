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
 *          Copyright 2008-2019 Sarah Walker.
 *          Copyright 2016-2019 Miran Grca.
 */
#include <stdbool.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <wchar.h>
#include <86box/86box.h>
#include <86box/device.h>
#include <86box/mem.h>
#include <86box/timer.h>
#include <86box/video.h>
#include <86box/vid_svga.h>
#include <86box/vid_svga_render.h>
#include <stdatomic.h>
#include <86box/thread.h>
#include <86box/plat_unused.h>
#include <86box/vid_svga_render_remap.h>
#include <86box/kairo_gpu.h> /* KairoX86#233 */

uint32_t
svga_lookup_lut_ram(svga_t* svga, uint32_t val)
{
    if (!svga->lut_map)
        return val;

    uint8_t r = getcolr(svga->pallook[getcolr(val)]);
    uint8_t g = getcolg(svga->pallook[getcolg(val)]);
    uint8_t b = getcolb(svga->pallook[getcolb(val)]);
    return makecol32(r, g, b) | (val & 0xFF000000);
}

#define lookup_lut(val) svga_lookup_lut_ram(svga, val)

/* KairoX86#233: the lines the GPU draws with the machine's Hardware acceleration on (86box/kairo_gpu.h).
   A line goes to the GPU only where nothing else draws on it (render_async: no cursor, no overlay)
   and the installed renderer is the core's own: a card's renderer around it (the Rage 128's pixel
   doubler) may read or redraw the line as soon as the core's returns. */
extern uint32_t svga_conv_16to32(struct svga_t *svga, uint16_t color, uint8_t bpp);

static bool
render_gpu_indexed(const svga_t *svga)
{
    return (svga->render == svga_render_2bpp_lowres) || (svga->render == svga_render_2bpp_highres) ||
           (svga->render == svga_render_4bpp_lowres) || (svga->render == svga_render_4bpp_highres) ||
           (svga->render == svga_render_8bpp_lowres) || (svga->render == svga_render_8bpp_highres);
}

/* Queues a line starting at p; returns where its words dwords go, the queue locked until
   kairo_gpu_scan_commit() */
static uint32_t *
render_gpu_line(svga_t *svga, uint32_t *p, uint32_t kind, uint32_t count, uint32_t words, const uint32_t *palette,
                uint32_t colours, uint32_t a, uint32_t flags)
{
    bitmap_t *bitmap = svga->monitor->target_buffer;
    return kairo_gpu_scan(bitmap, bitmap->kairo_gpu, (uint32_t) (p - bitmap->dat), kind, count, words, palette, colours,
                          a, 0, flags);
}

/* The packed 8bpp line's dwords wholly left of hdisp, from *memaddr on (moved as the CPU's drawing
   moves it), to the GPU; returns how many pixels (0: none, the CPU draws them all) */
static int
render_gpu_packed8(svga_t *svga, uint32_t *p, bool highres, uint32_t *memaddr)
{
    const uint32_t mask = svga->vram_display_mask;

    if (!svga->render_async || svga->render_line_offset || ((mask + 1) & mask) || (svga->hdisp < 8) ||
        (svga->hdisp > 2048) || !render_gpu_indexed(svga))
        return 0;
    const uint32_t dwords = (uint32_t) svga->hdisp / (highres ? 4 : 8);
    const uint32_t pixels = dwords * (highres ? 4 : 8);
    uint32_t      *words  = render_gpu_line(svga, p, KAIRO_SCAN_8, pixels, dwords, svga->map8, 256, svga->dac_mask,
                                             highres ? 0 : KAIRO_SCAN_WIDE);
    for (uint32_t c = 0; c < dwords; c++) {
        memcpy(&words[c], &svga->vram[*memaddr & mask], 4);
        *memaddr = (*memaddr + 4) & mask;
    }
    kairo_gpu_scan_commit();
    return (int) pixels;
}

/* The line's pixels left of hdisp (a multiple of 8) in format 15, 16 or 32 to the GPU, from
   svga->memaddr on, when eligible (the installed renderer is this one and converts as 86Box does by
   default); returns how many (0: the CPU draws them all) */
static int
render_gpu_direct(svga_t *svga, uint32_t *p, uint32_t format, bool eligible)
{
    const uint32_t mask   = svga->vram_display_mask;
    const int      pixels = svga->hdisp & ~7;

    if (!kairo_gpu_on || !eligible || !svga->render_async || svga->render_line_offset || (pixels <= 0) ||
        (pixels > 2048) || ((mask + 1) & mask))
        return 0;
    const uint32_t words  = (uint32_t) pixels * ((format == 32) ? 4 : 2) / 4;
    /* 0x1f15: 15 bits mixed with the palette (svga_render_15bpp_mix_*) */
    const bool     mix    = (format == 0x1f15);
    const bool     lut    = ((format == 32) && svga->lut_map) || mix;
    const uint32_t kind   = mix ? KAIRO_SCAN_15MIX : (format == 15) ? KAIRO_SCAN_15 : (format == 16) ? KAIRO_SCAN_16 : KAIRO_SCAN_32;
    uint32_t      *line   = render_gpu_line(svga, p, kind, (uint32_t) pixels, words, lut ? svga->pallook : NULL,
                                            lut ? 256 : 0, 0, 0);
    uint32_t       memaddr = svga->memaddr;
    for (uint32_t w = 0; w < words; w++) {
        memcpy(&line[w], &svga->vram[memaddr & mask], 4);
        memaddr += 4;
    }
    kairo_gpu_scan_commit();
    return pixels;
}

/* A text line (svga_render_text_80, _40: dots 8 or 9 a cell, each drawn twice when wide) to the GPU:
   every cell read and its colours resolved as the CPU's drawing does, svga->memaddr moved as it moves
   it, and *col (text_80's shift register, or NULL) left as its drawing leaves it. Not the 256-colour
   text mode (attribute mode bit 6). Returns whether the GPU draws the line. */
static bool
render_gpu_text(svga_t *svga, uint32_t *p, uint32_t dots, bool wide, uint32_t *col)
{
    const uint32_t step  = dots * (wide ? 2 : 1);
    const int      end   = svga->hdisp + svga->scrollcache;

    /* A plane mask above the low nibble makes a dot's colour depend on the dot before it (text_80's
       shift register), which the cells do not carry */
    if (!kairo_gpu_on || !svga->render_async || (svga->attrregs[0x10] & 0x40) || (end <= 0) ||
        (svga->plane_mask & ~0x0f) || (svga->render != (wide ? svga_render_text_40 : svga_render_text_80)))
        return false;
    const uint32_t cells = ((uint32_t) end + step - 1) / step;
    uint32_t       colours[16];
    for (int i = 0; i < 16; i++)
        colours[i] = svga->pallook[svga->egapal[i & svga->plane_mask] & svga->dac_mask];
    uint32_t *words = render_gpu_line(svga, p, KAIRO_SCAN_TEXT, cells * step, cells, colours, 16, dots,
                                      wide ? KAIRO_SCAN_WIDE : 0);
    for (uint32_t c = 0; c < cells; c++) {
        uint32_t addr = 0;
        uint8_t  chr;
        uint8_t  attr;
        uint32_t fg;
        uint32_t bg;
        if (!svga->force_old_addr)
            addr = svga->remap_func(svga, svga->memaddr) & svga->vram_display_mask;
        const bool drawcursor = ((svga->memaddr == svga->cursoraddr) && svga->cursorvisible && svga->cursoron);
        if (svga->force_old_addr) {
            chr  = svga->vram[(svga->memaddr << 1) & svga->vram_display_mask];
            attr = svga->vram[((svga->memaddr << 1) + 1) & svga->vram_display_mask];
        } else {
            chr  = svga->vram[addr];
            attr = svga->vram[addr + 1];
        }
        const uint32_t charaddr = ((attr & 8) ? svga->charsetb : svga->charseta) + (chr * 128);
        if (drawcursor) {
            bg = attr & 15;
            fg = attr >> 4;
        } else {
            fg = attr & 15;
            bg = attr >> 4;
            if (attr & 0x80 && svga->attrregs[0x10] & 8) {
                bg = (attr >> 4) & 7;
                if (svga->blink & 16)
                    fg = bg;
            }
        }
        const uint8_t dat   = svga->vram[charaddr + (svga->scanline << 2)];
        const bool    ninth = ((chr & ~0x1f) == 0xc0) && (svga->attrregs[0x10] & 4) && (dat & 1);
        words[c]            = dat | (fg << 8) | (bg << 16) | (ninth ? (1u << 24) : 0);
        if (col != NULL) {
            for (uint32_t d = 0; d < dots; d++)
                *col = (*col << 4) | ((d < 8) ? ((dat & (0x80 >> d)) ? fg : bg) : (ninth ? fg : bg));
        }
        svga->memaddr += 4;
    }
    svga->memaddr &= svga->vram_display_mask;
    kairo_gpu_scan_commit();
    return true;
}

/* The low-resolution line's pixels left of hdisp (svga_render_15bpp_lowres, _16bpp_lowres, _32bpp_lowres:
   each pixel drawn twice) in format 15, 16 or 32 to the GPU, from svga->memaddr on, when eligible;
   returns the loop's x after them (0: the CPU draws them all), the line drawn 2x pixels on */
static int
render_gpu_wide(svga_t *svga, uint32_t *p, uint32_t format, bool eligible)
{
    const uint32_t mask = svga->vram_display_mask;
    const int      x    = svga->hdisp & ~7;

    if (!kairo_gpu_on || !eligible || !svga->render_async || svga->render_line_offset || (x <= 0) ||
        (x > 2048) || ((mask + 1) & mask))
        return 0;
    /* 15 and 16 bits: x advances 4 for each 2 dwords; 32 bits: 1 for each dword */
    const uint32_t words  = (format == 32) ? (uint32_t) x : (uint32_t) x / 2;
    const bool     mix    = (format == 0x1f15);
    const bool     lut    = ((format == 32) && svga->lut_map) || mix;
    const uint32_t kind   = mix ? KAIRO_SCAN_15MIX : (format == 15) ? KAIRO_SCAN_15 : (format == 16) ? KAIRO_SCAN_16 : KAIRO_SCAN_32;
    uint32_t      *line   = render_gpu_line(svga, p, kind, (uint32_t) x * 2, words, lut ? svga->pallook : NULL,
                                            lut ? 256 : 0, 0, KAIRO_SCAN_WIDE);
    for (uint32_t w = 0; w < words; w++)
        memcpy(&line[w], &svga->vram[(svga->memaddr + 4 * w) & mask], 4);
    kairo_gpu_scan_commit();
    return x;
}

/* The 24bpp line's groups of 4 pixels left of hdisp (svga_render_24bpp_highres, _lowres: each pixel drawn
   twice when wide) to the GPU, read as the loop reads them (3 dwords a group) and svga->memaddr moved on
   12 a group as it moves it, when eligible; returns the loop's x after them (0: the CPU draws them all) */
static int
render_gpu_24(svga_t *svga, uint32_t *p, bool wide, bool eligible)
{
    const uint32_t mask   = svga->vram_display_mask;
    const int      x      = svga->hdisp & ~7;

    if (!kairo_gpu_on || !eligible || !svga->render_async || svga->render_line_offset || (x <= 0) ||
        (x > 2048) || ((mask + 1) & mask))
        return 0;
    const uint32_t groups = (uint32_t) x / 4;
    uint32_t      *line   = render_gpu_line(svga, p, KAIRO_SCAN_24, (uint32_t) x * (wide ? 2 : 1), groups * 3,
                                            svga->lut_map ? svga->pallook : NULL, svga->lut_map ? 256 : 0, 0,
                                            wide ? KAIRO_SCAN_WIDE : 0);
    for (uint32_t g = 0; g < groups; g++) {
        memcpy(&line[g * 3], &svga->vram[svga->memaddr & mask], 4);
        memcpy(&line[g * 3 + 1], &svga->vram[(svga->memaddr + 4) & mask], 4);
        memcpy(&line[g * 3 + 2], &svga->vram[(svga->memaddr + 8) & mask], 4);
        svga->memaddr += 12;
    }
    kairo_gpu_scan_commit();
    return x;
}

/* The packed 8bpp line's steps of 8 pixels left of hdisp for the renderers that read their dwords in turn
   (svga_render_8bpp_clone_highres; svga_render_8bpp_tseng_highres and _lowres, whose attribute register
   14h nibble the palette takes in) to the GPU, svga->memaddr moved on 4 a dword as they move it, when
   eligible; returns the pixels drawn (the loop's x after them; 0: the CPU draws them all) */
static int
render_gpu_seq8(svga_t *svga, uint32_t *p, int dwords_per_step, bool wide, bool tseng, bool eligible)
{
    const uint32_t mask  = svga->vram_display_mask;
    const int      x     = svga->hdisp & ~7;

    if (!kairo_gpu_on || !eligible || !svga->render_async || svga->render_line_offset || (x <= 0) ||
        (x > 2048) || ((mask + 1) & mask))
        return 0;
    const uint32_t words = (uint32_t) (x / 8) * (uint32_t) dwords_per_step;
    uint32_t       colours[256];
    for (int v = 0; v < 256; v++) {
        int c = v;
        if (tseng && (svga->attrregs[0x10] & 0x80))
            c = (c & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);
        colours[v] = svga->map8[c & svga->dac_mask & 0xff];
    }
    uint32_t *line = render_gpu_line(svga, p, KAIRO_SCAN_8, (uint32_t) x, words, colours, 256, 0xff, wide ? KAIRO_SCAN_WIDE : 0);
    for (uint32_t w = 0; w < words; w++) {
        memcpy(&line[w], &svga->vram[svga->memaddr & mask], 4);
        svga->memaddr += 4;
    }
    kairo_gpu_scan_commit();
    return x;
}

/* KairoX86#233: a line the renderer's loop reads byte by byte, `pixels` pixels of `bits` bits a pixel,
   most significant first, through `colours` (KAIRO_SCAN_BITS), each drawn twice across when wide, to the
   GPU when eligible (the installed renderer is the one asking): returns where its bytes go, in the order
   the loop reads them (NULL: the CPU draws the line). The caller commits the queue. */
static uint8_t *
render_gpu_bits(svga_t *svga, uint32_t *p, uint32_t bits, uint32_t pixels, bool wide, const uint32_t *colours, uint32_t n,
                bool eligible)
{
    if (!kairo_gpu_on || !eligible || !svga->render_async || (pixels == 0) || (pixels > 4096))
        return NULL;
    const uint32_t words = (pixels * bits + 31) / 32;
    uint32_t      *line  = render_gpu_line(svga, p, KAIRO_SCAN_BITS, pixels * (wide ? 2 : 1), words, colours, n, bits,
                                           wide ? KAIRO_SCAN_WIDE : 0);
    memset(line, 0, words * 4);
    return (uint8_t *) line;
}

void
svga_render_null(svga_t *svga)
{
    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->firstline_draw == 2000)
        svga->firstline_draw = svga->displine;
    svga->lastline_draw = svga->displine;
}

void
svga_render_blank(svga_t *svga)
{
    if (((svga->displine + svga->y_add) < 0) ||
        ((svga->displine + svga->y_add) >= 2048) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->firstline_draw == 2000)
        svga->firstline_draw = svga->displine;
    svga->lastline_draw = svga->displine;

    uint32_t char_width = 0;

    switch (svga->seqregs[1] & 9) {
        case 0:
            char_width = 9;
            break;
        case 1:
            char_width = 8;
            break;
        case 8:
            char_width = 18;
            break;
        case 9:
            char_width = 16;
            break;

        default:
            break;
    }

    uint32_t *line_ptr   = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];
    int32_t   line_width = (uint32_t) (svga->hdisp + svga->scrollcache) * char_width * sizeof(uint32_t);

    if (svga->x_add < 0) {
        line_ptr = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][0];
        line_width -= svga->x_add;
    }

    if ((line_ptr != NULL) && ((svga->hdisp + svga->scrollcache) > 0) && (line_width >= 0))
        memset(line_ptr, 0, line_width);
}

void
svga_render_overscan_left(svga_t *svga)
{
    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->scrblank || (svga->hdisp <= 0))
        return;

    uint32_t *line_ptr = svga->monitor->target_buffer->line[svga->displine + svga->y_add];

    if ((line_ptr != NULL) && (svga->x_add >= 0))  for (int i = 0; i < svga->x_add; i++)
        *line_ptr++ = svga->overscan_color;
}

void
svga_render_overscan_right(svga_t *svga)
{
    int right;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->scrblank || (svga->hdisp <= 0))
        return;

    uint32_t *line_ptr = svga->monitor->target_buffer->line[svga->displine + svga->y_add];
    right              = overscan_x  - svga->left_overscan;

    if (line_ptr != NULL) {
        line_ptr += svga->x_add + svga->hdisp;

        for (int i = 0; i < right; i++)
            *line_ptr++ = svga->overscan_color;
    }
}

void
svga_render_text_40(svga_t *svga)
{
    uint32_t *p;
    int       xx;
    int       drawcursor;
    int       xinc;
    uint8_t   chr;
    uint8_t   attr;
    uint8_t   dat;
    uint32_t  charaddr;
    uint32_t  fg;
    uint32_t  bg;
    uint32_t  addr = 0;

    if (svga->render_override) {
        svga->render_override(svga->priv_parent);
        return;
    }

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->firstline_draw == 2000)
        svga->firstline_draw = svga->displine;
    svga->lastline_draw = svga->displine;

    if (svga->fullchange) {
        p    = &svga->monitor->target_buffer->line[(svga->displine + svga->y_add) & 2047][(svga->x_add) & 2047];
        xinc = (svga->seqregs[1] & 1) ? 16 : 18;

        /* KairoX86#233 */
        if (render_gpu_text(svga, p, (uint32_t) xinc / 2, true, NULL))
            return;

        for (int x = 0; x < (svga->hdisp + svga->scrollcache); x += xinc) {
            if (!svga->force_old_addr)
                addr = svga->remap_func(svga, svga->memaddr) & svga->vram_display_mask;

            drawcursor = ((svga->memaddr == svga->cursoraddr) && svga->cursorvisible && svga->cursoron);

            if (svga->force_old_addr) {
                chr  = svga->vram[(svga->memaddr << 1) & svga->vram_display_mask];
                attr = svga->vram[((svga->memaddr << 1) + 1) & svga->vram_display_mask];
            } else {
                chr  = svga->vram[addr];
                attr = svga->vram[addr + 1];
            }

            if (attr & 8)
                charaddr = svga->charsetb + (chr * 128);
            else
                charaddr = svga->charseta + (chr * 128);

            if (drawcursor) {
                bg = svga->pallook[svga->egapal[(attr & 15) & svga->plane_mask] & svga->dac_mask];
                fg = svga->pallook[svga->egapal[(attr >> 4) & svga->plane_mask] & svga->dac_mask];
            } else {
                fg = svga->pallook[svga->egapal[(attr & 15) & svga->plane_mask] & svga->dac_mask];
                bg = svga->pallook[svga->egapal[(attr >> 4) & svga->plane_mask] & svga->dac_mask];

                if (attr & 0x80 && svga->attrregs[0x10] & 8) {
                    bg = svga->pallook[svga->egapal[((attr >> 4) & 7) & svga->plane_mask] & svga->dac_mask];
                    if (svga->blink & 16)
                        fg = bg;
                }
            }

            dat = svga->vram[charaddr + (svga->scanline << 2)];
            if (svga->seqregs[1] & 1) {
                for (xx = 0; xx < 16; xx += 2)
                    p[xx] = p[xx + 1] = (dat & (0x80 >> (xx >> 1))) ? fg : bg;
            } else {
                for (xx = 0; xx < 16; xx += 2)
                    p[xx] = p[xx + 1] = (dat & (0x80 >> (xx >> 1))) ? fg : bg;
                if ((chr & ~0x1f) != 0xc0 || !(svga->attrregs[0x10] & 4))
                    p[16] = p[17] = bg;
                else
                    p[16] = p[17] = (dat & 1) ? fg : bg;
            }
            svga->memaddr += 4;
            p += xinc;
        }
        svga->memaddr &= svga->vram_display_mask;
    }
}

void
svga_render_text_80(svga_t *svga)
{
    uint32_t *p;
    int       xx;
    int       drawcursor;
    int       xinc;
    uint8_t   chr;
    uint8_t   attr;
    uint8_t   dat;
    uint32_t  charaddr;
    uint32_t  fg;
    uint32_t  bg;
    uint32_t  addr = 0;

    if (svga->render_override) {
        svga->render_override(svga->priv_parent);
        return;
    }

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->firstline_draw == 2000)
        svga->firstline_draw = svga->displine;
    svga->lastline_draw = svga->displine;

    if (svga->fullchange) {
        p    = &svga->monitor->target_buffer->line[(svga->displine + svga->y_add) & 2047][(svga->x_add) & 2047];
        xinc = (svga->seqregs[1] & 1) ? 8 : 9;

        static uint32_t col = 0x00000000;

        /* KairoX86#233 */
        if (render_gpu_text(svga, p, (uint32_t) xinc, false, &col))
            return;

        for (int x = 0; x < (svga->hdisp + svga->scrollcache); x += xinc) {
            if (!svga->force_old_addr)
                addr = svga->remap_func(svga, svga->memaddr) & svga->vram_display_mask;

            drawcursor = ((svga->memaddr == svga->cursoraddr) && svga->cursorvisible && svga->cursoron);

            if (svga->force_old_addr) {
                chr  = svga->vram[(svga->memaddr << 1) & svga->vram_display_mask];
                attr = svga->vram[((svga->memaddr << 1) + 1) & svga->vram_display_mask];
            } else {
                chr  = svga->vram[addr];
                attr = svga->vram[addr + 1];
            }

            if (attr & 8)
                charaddr = svga->charsetb + (chr * 128);
            else
                charaddr = svga->charseta + (chr * 128);

            if (drawcursor) {
                bg = attr & 15;
                fg = attr >> 4;
            } else {
                fg = attr & 15;
                bg = attr >> 4;
                if (attr & 0x80 && svga->attrregs[0x10] & 8) {
                    bg = (attr >> 4) & 7;
                    if (svga->blink & 16)
                        fg = bg;
                }
            }

            dat = svga->vram[charaddr + (svga->scanline << 2)];

            if (svga->attrregs[0x10] & 0x40) {
                if (svga->seqregs[1] & 1) {
                    for (xx = 0; xx < 8; xx++) {
                        uint32_t col16 = (dat & (0x80 >> xx)) ? fg : bg;
                        if ((x + xx - svga->scrollcache) & 1) {
                            col |= col16;
                            if ((x + xx - 1) >= 0)
                                p[xx - 1] = svga->pallook[col & svga->dac_mask];
                            if ((x + xx) >= 0)
                                p[xx] = svga->pallook[col & svga->dac_mask];
                        } else
                           col = col16 << 4;
                    }
                } else {
                    for (xx = 0; xx < 9; xx++) {
                        uint32_t col16;
                        if (xx < 8)
                            col16 = (dat & (0x80 >> xx)) ? fg : bg;
                        else if ((chr & ~0x1F) != 0xC0 || !(svga->attrregs[0x10] & 4))
                            col16 = bg;
                        else
                            col16 = (dat & 1) ? fg : bg;
                        if ((x + xx - svga->scrollcache) & 1) {
                            col |= col16;
                            if ((x + xx - 1) >= 0)
                                p[xx - 1] = svga->pallook[col & svga->dac_mask];
                            if ((x + xx) >= 0)
                                p[xx] = svga->pallook[col & svga->dac_mask];
                        } else
                           col = col16 << 4;
                    }
                }
            } else {
                if (svga->seqregs[1] & 1) {
                    for (xx = 0; xx < 8; xx++) {
                        col = (col << 4) | ((dat & (0x80 >> xx)) ? fg : bg);
                        p[xx] = svga->pallook[svga->egapal[col & svga->plane_mask] & svga->dac_mask];
                    }
                } else {
                    for (xx = 0; xx < 8; xx++) {
                        col = (col << 4) | ((dat & (0x80 >> xx)) ? fg : bg);
                        p[xx] = svga->pallook[svga->egapal[col & svga->plane_mask] & svga->dac_mask];
                    }
                    if ((chr & ~0x1F) != 0xC0 || !(svga->attrregs[0x10] & 4))
                        col = (col << 4) | bg;
                    else
                        col = (col << 4) | ((dat & 1) ? fg : bg);
                    p[8] = svga->pallook[svga->egapal[col & svga->plane_mask] & svga->dac_mask];
                }
            }

            svga->memaddr += 4;
            p += xinc;
        }
        svga->memaddr &= svga->vram_display_mask;
    }
}

/*Not available on most generic cards.*/
/* KairoX86#233: one cell of a KSC5601 text line: its 8 dots (and the ninth, a line drawing character's
   bit 0 where the attribute controller extends them, else the background) drawn at *p, or its word for
   the GPU at *gpu */
static void
ksc5601_cell(const svga_t *svga, uint32_t **p, uint32_t **gpu, int xinc, uint8_t chr, uint8_t dat, const uint32_t *colours,
             uint32_t fi, uint32_t bi)
{
    const int ninth = (xinc == 9) && ((chr & ~0x1f) == 0xc0) && (svga->attrregs[0x10] & 4) && (dat & 1);

    if (*gpu != NULL) {
        *(*gpu)++ = dat | (fi << 8) | (bi << 16) | (ninth ? (1u << 24) : 0);
        return;
    }
    for (int xx = 0; xx < 8; xx++)
        (*p)[xx] = (dat & (0x80 >> xx)) ? colours[fi] : colours[bi];
    if (xinc == 9)
        (*p)[8] = ninth ? colours[fi] : colours[bi];
    *p += xinc;
}

/* KairoX86#233: a text cell's colour indexes (the dot, the background), as the attribute gives them */
static void
ksc5601_cell_colours(const svga_t *svga, uint8_t attr, int drawcursor, uint32_t *fi, uint32_t *bi)
{
    if (drawcursor) {
        *bi = attr & 15;
        *fi = attr >> 4;
    } else {
        *fi = attr & 15;
        *bi = attr >> 4;
        if (attr & 0x80 && svga->attrregs[0x10] & 8) {
            *bi = (attr >> 4) & 7;
            if (svga->blink & 16)
                *fi = *bi;
        }
    }
}

void
svga_render_text_80_ksc5601(svga_t *svga)
{
    uint32_t *p;
    int       drawcursor;
    int       xinc;
    uint8_t   chr;
    uint8_t   attr;
    uint8_t   dat;
    uint8_t   nextchr;
    uint32_t  charaddr;
    uint32_t  fi;
    uint32_t  bi;
    uint32_t  colours[16];
    uint32_t *gpu = NULL; /* KairoX86#233: the cells' words, when the GPU draws the line */

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->firstline_draw == 2000)
        svga->firstline_draw = svga->displine;
    svga->lastline_draw = svga->displine;

    if (svga->fullchange) {
        p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

        xinc = (svga->seqregs[1] & 1) ? 8 : 9;
        for (int i = 0; i < 16; i++)
            colours[i] = svga->pallook[svga->egapal[i & svga->plane_mask] & svga->dac_mask];

        /* KairoX86#233: one cell every xinc dots up to the line's end (a double-byte character's two
           halves are two cells), each with its font byte and colours resolved here */
        const int end = svga->hdisp + svga->scrollcache;
        if (kairo_gpu_on && svga->render_async && (end > 0) && (svga->render == svga_render_text_80_ksc5601)) {
            const uint32_t cells = (uint32_t) (end + xinc - 1) / (uint32_t) xinc;
            gpu = render_gpu_line(svga, p, KAIRO_SCAN_TEXT, cells * (uint32_t) xinc, cells, colours, 16, (uint32_t) xinc, 0);
        }

        for (int x = 0; x < (svga->hdisp + svga->scrollcache); x += xinc) {
            uint32_t addr = svga->remap_func(svga, svga->memaddr) & svga->vram_display_mask;
            drawcursor    = ((svga->memaddr == svga->cursoraddr) && svga->cursorvisible && svga->cursoron);
            chr           = svga->vram[addr];
            nextchr       = svga->vram[addr + 8];
            attr          = svga->vram[addr + 1];

            ksc5601_cell_colours(svga, attr, drawcursor, &fi, &bi);

            if ((x + xinc) < svga->hdisp && (chr & (nextchr | svga->ksc5601_sbyte_mask) & 0x80)) {
                if ((chr == svga->ksc5601_udc_area_msb[0] || chr == svga->ksc5601_udc_area_msb[1]) && (nextchr > 0xa0 && nextchr < 0xff))
                    dat = fontdatksc5601_user[(chr == svga->ksc5601_udc_area_msb[1] ? 96 : 0) + (nextchr & 0x7F) - 0x20].chr[svga->scanline];
                else if (nextchr & 0x80) {
                    if (svga->ksc5601_swap_mode == 1 && (nextchr > 0xa0 && nextchr < 0xff)) {
                        if (chr >= 0x80 && chr < 0x99)
                            chr += 0x30;
                        else if (chr >= 0xB0 && chr < 0xC9)
                            chr -= 0x30;
                    }
                    dat = fontdatksc5601[((chr & 0x7F) << 7) | (nextchr & 0x7F)].chr[svga->scanline];
                } else
                    dat = 0xff;
            } else {
                if (attr & 8)
                    charaddr = svga->charsetb + (chr * 128);
                else
                    charaddr = svga->charseta + (chr * 128);

                if ((svga->ksc5601_english_font_type >> 8) == 1)
                    dat = fontdatksc5601[((svga->ksc5601_english_font_type & 0x7F) << 7) | (chr >> 1)].chr[((chr & 1) << 4) | svga->scanline];
                else
                    dat = svga->vram[charaddr + (svga->scanline << 2)];
            }

            ksc5601_cell(svga, &p, &gpu, xinc, chr, dat, colours, fi, bi);
            svga->memaddr += 4;

            if ((x + xinc) < svga->hdisp && (chr & (nextchr | svga->ksc5601_sbyte_mask) & 0x80)) {
                attr = svga->vram[((svga->memaddr << 1) + 1) & svga->vram_display_mask];

                ksc5601_cell_colours(svga, attr, drawcursor, &fi, &bi);

                if ((chr == svga->ksc5601_udc_area_msb[0] || chr == svga->ksc5601_udc_area_msb[1]) && (nextchr > 0xa0 && nextchr < 0xff))
                    dat = fontdatksc5601_user[(chr == svga->ksc5601_udc_area_msb[1] ? 96 : 0) + (nextchr & 0x7F) - 0x20].chr[svga->scanline + 16];
                else if (nextchr & 0x80)
                    dat = fontdatksc5601[((chr & 0x7f) << 7) | (nextchr & 0x7F)].chr[svga->scanline + 16];
                else
                    dat = 0xff;

                ksc5601_cell(svga, &p, &gpu, xinc, chr, dat, colours, fi, bi);
                svga->memaddr += 4;
                x += xinc;
            }
        }
        svga->memaddr &= svga->vram_display_mask;
        if (gpu != NULL)
            kairo_gpu_scan_commit();
    }
}

/* KairoX86#233: svga_render_2bpp_s3_lowres and _highres in one: the line's 2-bit pixels, two bytes each 8,
   through the palette, each drawn twice across when wide; or, with the GPU on, the bytes to the GPU */
static void
render_2bpp_s3(svga_t *svga, bool wide)
{
    uint32_t  colours[4];
    bool      changed;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->force_old_addr) {
        const int changed_offset = ((svga->memaddr << 1) + (svga->scanline & ~svga->crtc[0x17] & 3) * 0x8000) >> 12;

        changed = svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1] || svga->fullchange;
    } else {
        const uint32_t changed_addr = svga->remap_func(svga, svga->memaddr);

        changed = svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange;
    }
    if (!changed)
        return;

    uint32_t *p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

    if (svga->firstline_draw == 2000)
        svga->firstline_draw = svga->displine;
    svga->lastline_draw = svga->displine;

    for (int v = 0; v < 4; v++)
        colours[v] = svga->pallook[svga->egapal[v] & svga->dac_mask];
    const int step = wide ? 16 : 8;
    const int end  = svga->hdisp + svga->scrollcache;
    uint8_t  *gpu  = (end >= 0) ? render_gpu_bits(svga, p, 2, (uint32_t) (end / step + 1) * 8, wide, colours, 4,
                                                  svga->render == (wide ? svga_render_2bpp_s3_lowres : svga_render_2bpp_s3_highres))
                                : NULL;

    for (int x = 0; x <= end; x += step) {
        uint32_t addr;

        if (svga->force_old_addr) {
            addr = svga->memaddr;

            if (!(svga->crtc[0x17] & 0x40)) {
                addr = (addr << 1) & svga->vram_mask;
                addr &= ~7;

                if ((svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x20000))
                    addr |= 4;

                if (!(svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x8000))
                    addr |= 4;
            }

            if (!(svga->crtc[0x17] & 0x01))
                addr = (addr & ~0x8000) | ((svga->scanline & 1) ? 0x8000 : 0);

            if (!(svga->crtc[0x17] & 0x02))
                addr = (addr & ~0x10000) | ((svga->scanline & 2) ? 0x10000 : 0);
        } else
            addr = svga->remap_func(svga, svga->memaddr);

        const uint8_t dat[2] = { svga->vram[addr], svga->vram[addr | 0x1] };
        if (svga->seqregs[1] & 4)
            svga->memaddr += 2;
        else
            svga->memaddr += 4;
        svga->memaddr &= svga->vram_mask;

        if (gpu != NULL) {
            *gpu++ = dat[0];
            *gpu++ = dat[1];
            continue;
        }
        for (int i = 0; i < 8; i++) {
            const uint32_t c = colours[(dat[i >> 2] >> (6 - 2 * (i & 3))) & 3];

            if (wide) {
                p[0] = p[1] = c;
                p += 2;
            } else
                *p++ = c;
        }
    }
    if (gpu != NULL)
        kairo_gpu_scan_commit();
}

void
svga_render_2bpp_s3_lowres(svga_t *svga)
{
    render_2bpp_s3(svga, true);
}

void
svga_render_2bpp_s3_highres(svga_t *svga)
{
    render_2bpp_s3(svga, false);
}

/* KairoX86#233: the 8 pixels of four plane bytes (edat), as the plane mask leaves them (the second of each
   pair keeps the high nibble's bits a mask above 0x0f lets through): drawn at *p through the attribute
   palette and the DAC's (its index masked with dac), or packed two a byte (the first in the high nibble)
   at *gpu, which only takes lines whose mask is within 0x0f */
static void
render_edat_pixels(const svga_t *svga, const uint8_t *edat, uint32_t dac, uint32_t **p, uint8_t **gpu)
{
    for (int i = 0; i < 4; i++) {
        const int     s   = 6 - 2 * i;
        const uint8_t dat = edatlookup[(edat[0] >> s) & 3][(edat[1] >> s) & 3] | (edatlookup[(edat[2] >> s) & 3][(edat[3] >> s) & 3] << 2);
        const int     hi  = (dat >> 4) & svga->plane_mask;
        const int     lo  = dat & svga->plane_mask;

        if (*gpu != NULL)
            *(*gpu)++ = (uint8_t) ((hi << 4) | (lo & 0x0f));
        else {
            (*p)[0] = svga->pallook[svga->egapal[hi] & dac];
            (*p)[1] = svga->pallook[svga->egapal[lo] & dac];
            *p += 2;
        }
    }
}

void
svga_render_2bpp_headland_highres(svga_t *svga)
{
    uint32_t  addr;
    uint32_t *p;
    uint8_t   edat[4];
    uint32_t  changed_addr;
    uint32_t  colours[16];

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    changed_addr = svga->remap_func(svga, svga->memaddr);

    if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
        p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

        if (svga->firstline_draw == 2000)
            svga->firstline_draw = svga->displine;
        svga->lastline_draw = svga->displine;

        for (int v = 0; v < 16; v++)
            colours[v] = svga->pallook[svga->egapal[v] & svga->dac_mask];
        const int end = svga->hdisp + svga->scrollcache;
        /* KairoX86#233: each 8 pixels' nibbles to the GPU, when it draws the line (the plane mask within
           4 bits: its pixels index the 16 colours) */
        uint8_t *gpu = ((end >= 0) && !(svga->plane_mask & ~0x0f))
                           ? render_gpu_bits(svga, p, 4, (uint32_t) (end / 8 + 1) * 8, false, colours, 16,
                                             svga->render == svga_render_2bpp_headland_highres)
                           : NULL;

        for (int x = 0; x <= end; x += 8) {
            addr = svga->remap_func(svga, svga->memaddr);

            if (svga->seqregs[1] & 4) {
                const int oddeven = (addr & 4) ? 1 : 0;
                edat[0]           = svga->vram[addr | oddeven];
                edat[2]           = svga->vram[addr | oddeven | 0x2];
                edat[1] = edat[3] = 0;
            } else {
                *(uint32_t *) (&edat[0]) = *(uint32_t *) (&svga->vram[addr]);
            }
            svga->memaddr += 4;
            svga->memaddr &= svga->vram_mask;

            render_edat_pixels(svga, edat, svga->dac_mask, &p, &gpu);
        }
        if (gpu != NULL)
            kairo_gpu_scan_commit();
    }
}

#include <inttypes.h>

/* Lines of packed 8bpp drawn on a thread of their own. The emulation thread
   works out each line (svga->memaddr moves on just as drawing would move it)
   and queues the part of it left of hdisp; the rest, which the right overscan
   then partly covers, it draws itself, so the frame comes out the same.
   Drawing writes nothing but the frame buffer, so the guest sees nothing of
   it; a queued line shows the VRAM of a moment later. svga_render_drain()
   waits for the queue to empty: before a frame is shown, before the buffer
   can change size, and on close. A line something else draws on (cursors,
   overlay) is drawn in place (svga->render_async). */
/* KairoX86#38: a job holds what its line reads, taken as the guest scans the line: the line's
   VRAM and the palette. Wider lines than RENDER_LINE_BYTES are drawn in place. */
#define RENDER_LINE_BYTES 2048

typedef struct render_job_t {
    uint32_t *p;
    uint32_t  dac;
    int       dwords;
    int       wide; /* KairoX86#214: each pixel drawn twice across */
    uint32_t  map8[256];
    uint8_t   line[RENDER_LINE_BYTES];
} render_job_t;

#define RENDER_JOBS 2048 /* a power of 2, more lines than a frame has */
#define RENDER_BATCH 32 /* KairoX86#214: lines queued before a sleeping drawing thread is woken */

static render_job_t render_jobs[RENDER_JOBS];
static atomic_uint  render_head; /* next job queued, emulation thread */
static atomic_uint  render_tail; /* next job drawn, drawing thread */
static thread_t    *render_thread;
static event_t     *render_wake;
static event_t     *render_idle;
static atomic_int   render_quit; /* KairoX86: svga_render_close ends the drawing thread */

static void
render_8bpp_dwords(const render_job_t *job)
{
    uint32_t *p = job->p;

    for (int c = 0; c < job->dwords; c++) {
        uint32_t dat;

        memcpy(&dat, &job->line[4 * c], 4);
        if (job->wide) {
            p[0] = p[1] = job->map8[dat & job->dac];
            p[2] = p[3] = job->map8[(dat >> 8) & job->dac];
            p[4] = p[5] = job->map8[(dat >> 16) & job->dac];
            p[6] = p[7] = job->map8[(dat >> 24) & job->dac];
            p += 8;
            continue;
        }
        p[0]    = job->map8[dat & job->dac];
        p[1]    = job->map8[(dat >> 8) & job->dac];
        p[2]    = job->map8[(dat >> 16) & job->dac];
        p[3]    = job->map8[(dat >> 24) & job->dac];
        p += 4;
    }
}

static void
render_thread_func(UNUSED(void *priv))
{
    for (;;) {
        thread_wait_event(render_wake, -1);
        thread_reset_event(render_wake);
        if (atomic_load_explicit(&render_quit, memory_order_acquire))
            return; /* KairoX86: svga_render_close, after the queue was drained */
        for (;;) {
            const unsigned tail = atomic_load_explicit(&render_tail, memory_order_relaxed);

            if (tail == atomic_load_explicit(&render_head, memory_order_acquire))
                break;
            render_8bpp_dwords(&render_jobs[tail & (RENDER_JOBS - 1)]);
            atomic_store_explicit(&render_tail, tail + 1, memory_order_release);
        }
        thread_set_event(render_idle);
    }
}

void
svga_render_drain(void)
{
    if (kairo_gpu_on) {
        /* KairoX86#233: the lines queued for the GPU, drawn */
        kairo_gpu_scan_drain();
        return;
    }
    if (render_thread == NULL)
        return;
    while (atomic_load_explicit(&render_tail, memory_order_acquire) != atomic_load_explicit(&render_head, memory_order_relaxed)) {
        thread_reset_event(render_idle);
        if (atomic_load_explicit(&render_tail, memory_order_acquire) == atomic_load_explicit(&render_head, memory_order_relaxed))
            break;
        thread_set_event(render_wake);
        thread_wait_event(render_idle, -1);
    }
}

/* KairoX86: ends the drawing thread, its queue drawn, so nothing of it outlives the machine. */
void
svga_render_close(void)
{
    if (render_thread == NULL)
        return;
    svga_render_drain();
    atomic_store_explicit(&render_quit, 1, memory_order_release);
    thread_set_event(render_wake);
    thread_wait(render_thread);
    thread_destroy_event(render_wake);
    thread_destroy_event(render_idle);
    render_thread = NULL;
    render_wake   = NULL;
    render_idle   = NULL;
    atomic_store_explicit(&render_quit, 0, memory_order_relaxed);
}

/* The next job's slot, which the emulation thread fills before render_commit(). */
static render_job_t *
render_slot(void)
{
    const unsigned head = atomic_load_explicit(&render_head, memory_order_relaxed);

    if (render_thread == NULL) {
        render_wake   = thread_create_event();
        render_idle   = thread_create_event();
        render_thread = thread_create(render_thread_func, NULL);
    }
    if ((head - atomic_load_explicit(&render_tail, memory_order_acquire)) == RENDER_JOBS)
        svga_render_drain();
    return &render_jobs[head & (RENDER_JOBS - 1)];
}

/* Queues the job render_slot() gave. */
static void
render_commit(void)
{
    const unsigned head = atomic_load_explicit(&render_head, memory_order_relaxed);
    /* KairoX86#214: a thread still drawing finds the job itself; a sleeping one is woken once
       RENDER_BATCH lines wait (while it sleeps nothing is drawn, so the count reaches it), and
       svga_render_drain() wakes it for the rest */
    const unsigned waiting = head + 1 - atomic_load_explicit(&render_tail, memory_order_acquire);
    atomic_store_explicit(&render_head, head + 1, memory_order_release);
    if (waiting == RENDER_BATCH)
        thread_set_event(render_wake);
}


static void
svga_render_indexed_gfx(svga_t *svga, bool highres, bool combine8bits)
{
    int       x;
    uint32_t  addr;
    uint32_t *p;
    uint32_t  changed_offset;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    const bool blinked   = !!(svga->blink & 0x10);
    const bool attrblink = (!svga->disable_blink) && ((svga->attrregs[0x10] & 0x08) != 0);

    /*
       The following is likely how it works on an IBM VGA - that is, it works with its BIOS.
       But on some cards, certain modes are broken.
       - S3 Trio: mode 13h (320x200x8), incbypow2 given as 2 treated as 0
       - ET4000/W32i: mode 2Eh (640x480x8), incevery given as 2 treated as 1
     */
    const bool forcepacked = combine8bits && (svga->force_old_addr || svga->packed_chain4);

    /*
       SVGA cards with a high-resolution 8bpp mode may actually bypass the VGA shifter logic.
       - HT-216 (+ other Video7 chipsets?) has 0x3C4.0xC8 bit 4 which, when set to 1, loads
         bytes directly, bypassing the shifters.
     */
    const bool highres8bpp = (combine8bits && highres) || svga->force_shifter_bypass;

    const bool     dwordload  = ((svga->seqregs[0x01] & 0x10) != 0);
    const bool     wordload   = ((svga->seqregs[0x01] & 0x04) != 0) && !dwordload;
    const bool     wordincr   = ((svga->crtc[0x17] & 0x08) != 0);
    const bool     dwordincr  = ((svga->crtc[0x14] & 0x20) != 0) && !wordincr;
    const bool     dwordshift = ((svga->crtc[0x14] & 0x40) != 0);
    const bool     wordshift  = ((svga->crtc[0x17] & 0x40) == 0) && !dwordshift;
    const uint32_t incbypow2  = forcepacked ? 0 : (dwordshift ? 2 : wordshift ? 1 : 0);
    const uint32_t incevery   = forcepacked ? 1 : (dwordincr ? 4 : wordincr ? 2 : 1);
    const uint32_t loadevery  = forcepacked ? 1 : (dwordload ? 4 : wordload ? 2 : 1);

    const bool shift4bit = ((svga->gdcreg[0x05] & 0x40) == 0x40) || highres8bpp;
    const bool shift2bit = (((svga->gdcreg[0x05] & 0x60) == 0x20) && !shift4bit);

    const int      dwshift   = highres ? 0 : 1;
    const int      dotwidth  = 1 << dwshift;
    const int      charwidth = dotwidth * ((combine8bits && !svga->packed_4bpp) ? 4 : 8);
    const uint32_t planemask = 0x11111111 * (uint32_t) (svga->plane_mask);
    const uint32_t blinkmask = (attrblink ? 0x88888888 : 0x0);
    const uint32_t blinkval  = (attrblink && blinked ? 0x88888888 : 0x0);

    /*
       This is actually a 8x 3-bit lookup table,
       preshifted by 2 bits to allow shifting by multiples of 4 bits.

       Anyway, when we perform a planar-to-chunky conversion,
       we keep the pixel values in a scrambled order.
       This lookup table unscrambles them.

       WARNING: Octal values are used here!
     */
    const uint32_t shift_values = (shift4bit
                                       ? ((067452301) << 2)
                                       : shift2bit
                                       ? ((026370415) << 2)
                                       : ((002461357) << 2));

    if ((svga->displine + svga->y_add) < 0)
        return;

    if (svga->force_old_addr)
        changed_offset = (svga->memaddr + (svga->scanline & ~svga->crtc[0x17] & 3) * 0x8000) >> 12;
    else
        changed_offset = svga->remap_func(svga, svga->memaddr) >> 12;

#ifdef K9X_DIAG
    {
        extern uint64_t k9x_lines_skip, k9x_lines_vram, k9x_lines_full;
        if (!(svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1] || svga->fullchange))
            k9x_lines_skip++;
        else if (svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1])
            k9x_lines_vram++;
        else
            k9x_lines_full++;
    }
#endif
    if (!(svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1] || svga->fullchange))
        return;
    p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];
    if (p < svga->monitor->target_buffer->line[0])
        return;

    if (svga->render_line_offset) {
        if (svga->render_line_offset > 0) {
            memset(p, svga->overscan_color, (size_t) charwidth * svga->render_line_offset * sizeof(uint32_t));
            p += charwidth * svga->render_line_offset;
        }
    }

    if (svga->firstline_draw == 2000)
        svga->firstline_draw = svga->displine;
    svga->lastline_draw = svga->displine;

    uint32_t incr_counter = 0;
    uint32_t load_counter = 0;
    uint32_t edat         = 0;
    static uint32_t col          = 0;
    static uint32_t col2         = 0;

    /* Packed 8bpp, a dot per pixel, nothing remapped, masked or blinking:
       what the loop below comes to (each VRAM byte in order through map8),
       with the fields it reads held here, as the pixel stores could alias
       them as far as the compiler knows (-fno-strict-aliasing). With
       force_old_addr the address is memaddr & ~3 (forcepacked makes
       incbypow2 0) unless CRTC 17h bits 0/1 bring in scanline bits, so it is
       the same for a dword-aligned memaddr with both bits set. */
    /* KairoX86#214: lowres too, each pixel twice across (dotwidth 2, a dword to eight pixels) */
    if (combine8bits && !svga->packed_4bpp && !svga->half_pixel && !svga->ati_4color &&
        (!svga->force_old_addr || (((svga->crtc[0x17] & 3) == 3) && !(svga->memaddr & 3) && !incbypow2)) &&
        !svga->remap_required && (loadevery == 1) && (incevery == 1) &&
        (planemask == 0xffffffff) && !blinkmask && shift4bit) {
        const uint8_t  *vram    = svga->vram;
        const uint32_t *map8    = svga->map8;
        const uint32_t  mask    = svga->vram_display_mask;
        const uint32_t  dac     = svga->dac_mask;
        const int       end     = svga->hdisp + svga->scrollcache;
        uint32_t        memaddr = svga->memaddr;

#ifdef K9X_DIAG
        {
            extern uint64_t k9x_lines_fast;
            k9x_lines_fast++;
        }
#endif
        /* The dwords wholly left of hdisp to the drawing thread */
        x = 0;
        if (kairo_gpu_on) {
            /* KairoX86#233: the dwords wholly left of hdisp to the GPU */
            x = render_gpu_packed8(svga, p, highres, &memaddr);
            p += x;
        } else if (svga->render_async && !svga->render_line_offset && !((mask + 1) & mask) && (svga->hdisp >= 8) &&
                   (svga->hdisp <= RENDER_LINE_BYTES)) {
            render_job_t *job    = render_slot();
            const int     dwords = svga->hdisp / (highres ? 4 : 8);

            job->p      = p;
            job->dac    = dac;
            job->dwords = dwords;
            job->wide   = !highres;
            memcpy(job->map8, map8, sizeof(job->map8));
            for (int c = 0; c < dwords; c++) {
                memcpy(&job->line[4 * c], &vram[memaddr & mask], 4);
                memaddr = (memaddr + 4) & mask;
            }
            render_commit();
            p += (highres ? 4 : 8) * dwords;
            x = (highres ? 4 : 8) * dwords;
        }

        for (; !highres && (x <= end); x += 8) {
            const uint32_t dat = *(const uint32_t *) &vram[memaddr & mask];

            memaddr = (memaddr + 4) & mask;
            p[0] = p[1] = map8[dat & dac];
            p[2] = p[3] = map8[(dat >> 8) & dac];
            p[4] = p[5] = map8[(dat >> 16) & dac];
            p[6] = p[7] = map8[(dat >> 24) & dac];
            col = p[7];
            p += 8;
        }
        for (; highres && (x <= end); x += 4) {
            const uint32_t dat = *(const uint32_t *) &vram[memaddr & mask];

            memaddr = (memaddr + 4) & mask;
            p[0]    = map8[dat & dac];
            p[1]    = map8[(dat >> 8) & dac];
            p[2]    = map8[(dat >> 16) & dac];
            p[3]    = map8[(dat >> 24) & dac];
            col     = p[3];
            p += 4;
        }
        svga->memaddr = memaddr;
    } else {
#ifdef K9X_DIAG
    {
        extern uint64_t k9x_lines_slow, k9x_slow_why[8];
        k9x_lines_slow++;
        k9x_slow_why[0] += !(combine8bits && highres);
        k9x_slow_why[1] += !!(svga->packed_4bpp || svga->half_pixel || svga->ati_4color);
        k9x_slow_why[2] += !!svga->force_old_addr;
        k9x_slow_why[3] += !!svga->remap_required;
        k9x_slow_why[4] += (loadevery != 1) || (incevery != 1);
        k9x_slow_why[5] += (planemask != 0xffffffff);
        k9x_slow_why[6] += !!blinkmask;
        k9x_slow_why[7] += !shift4bit;
    }
#endif
    /* KairoX86#233: the character clocks to the GPU, which draws their pixels (not ATI's 4-colour mode,
       half pixels, packed 4bpp or a line offset, whose drawing reads or moves what it drew) */
    uint32_t *gpu_clocks = NULL;
    uint32_t  gpu_count  = 0;
    if (kairo_gpu_on && svga->render_async && !svga->render_line_offset && !svga->ati_4color && !svga->half_pixel &&
        !(combine8bits && svga->packed_4bpp) && render_gpu_indexed(svga) && ((svga->hdisp + svga->scrollcache) >= 0)) {
        const uint32_t clocks = (uint32_t) ((svga->hdisp + svga->scrollcache) / charwidth) + 1;
        uint32_t       colours[256];
        if (combine8bits) {
            for (int c = 0; c < 256; c++)
                colours[c] = svga->map8[c & svga->dac_mask];
        } else {
            for (int c = 0; c < 16; c++)
                colours[c] = svga->pallook[svga->egapal[c] & svga->dac_mask];
        }
        gpu_clocks = render_gpu_line(svga, p, combine8bits ? KAIRO_SCAN_NIBBLES8 : KAIRO_SCAN_NIBBLES,
                                     clocks * (uint32_t) charwidth, clocks, colours, combine8bits ? 256 : 16, shift_values,
                                     (dotwidth == 2) ? KAIRO_SCAN_WIDE : 0);
    }
    for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += charwidth) {
        if (load_counter == 0) {
            /* Find our address */
            if (svga->force_old_addr) {
                addr = ((svga->memaddr & ~0x3) << incbypow2);

                if (incbypow2 == 2) {
                    if (svga->memaddr & (4 << 15))
                        addr |= 0x8;
                    if (svga->memaddr & (4 << 14))
                        addr |= 0x4;
                } else if (incbypow2 == 1) {
                    if ((svga->crtc[0x17] & 0x20)) {
                        if (svga->memaddr & (4 << 15))
                            addr |= 0x4;
                    } else {
                        if (svga->memaddr & (4 << 13))
                            addr |= 0x4;
                    }
                } else {
                    /* Nothing */
                }

                if (!(svga->crtc[0x17] & 0x01))
                    addr = (addr & ~0x8000) | ((svga->scanline & 1) ? 0x8000 : 0);
                if (!(svga->crtc[0x17] & 0x02))
                    addr = (addr & ~0x10000) | ((svga->scanline & 2) ? 0x10000 : 0);
            } else if (svga->remap_required)
                addr = svga->remap_func(svga, svga->memaddr);
            else
                addr = svga->memaddr;

            addr &= svga->vram_display_mask;

            /* Load VRAM */
            edat = *(uint32_t *) &svga->vram[addr];

            /*
               EGA and VGA actually use 4bpp planar as its native format.
               But 4bpp chunky is generally easier to deal with on a modern CPU.
               shift4bit is the native format for this renderer (4bpp chunky).
             */
            if (svga->ati_4color || !shift4bit) {
                if (shift2bit && !svga->ati_4color) {
                    /* Group 2x 2bpp values into 4bpp values */
                    edat = (edat & 0xCCCC3333) | ((edat << 14) & 0x33330000) | ((edat >> 14) & 0x0000CCCC);
                } else {
                    /* Group 4x 1bpp values into 4bpp values */
                    edat = (edat & 0xAA55AA55) | ((edat << 7) & 0x55005500) | ((edat >> 7) & 0x00AA00AA);
                    edat = (edat & 0xCCCC3333) | ((edat << 14) & 0x33330000) | ((edat >> 14) & 0x0000CCCC);
                }
            }
        } else {
            /*
               According to the 82C451 VGA clone chipset datasheet, all 4 planes chain in a ring.
               So, rotate them all around.
               Planar version: edat = (edat >> 8) | (edat << 24);
               Here's the chunky version...
             */
            edat = ((edat >> 1) & 0x77777777) | ((edat << 3) & 0x88888888);
        }
        load_counter += 1;
        if (load_counter >= loadevery)
            load_counter = 0;

        incr_counter += 1;
        if (incr_counter >= incevery) {
            incr_counter = 0;
            svga->memaddr += 4;
            /* DISCREPANCY TODO FIXME 2/4bpp used vram_mask, 8bpp used vram_display_mask --GM */
            svga->memaddr &= svga->vram_display_mask;
        }

        uint32_t current_shift = shift_values;
        uint32_t out_edat      = edat;
        /*
           Apply blink
           FIXME: Confirm blink behaviour on real hardware

           The VGA 4bpp graphics blink logic was a pain to work out.

           If plane 3 is enabled in the attribute controller, then:
           - if bit 3 is 0, then we force the output of it to be 1.
           - if bit 3 is 1, then the output blinks.
           This can be tested with Lotus 1-2-3 release 2.3 with the WYSIWYG addon.

           If plane 3 is disabled in the attribute controller, then the output blinks.
           This can be tested with QBASIC SCREEN 10 - anything using color #2 should
           blink and nothing else.

           If you can simplify the following and have it still work, give yourself a medal.
         */
        out_edat = ((out_edat & planemask & ~blinkmask) | ((out_edat | ~planemask) & blinkmask & blinkval)) ^ blinkmask;

        if (gpu_clocks != NULL) {
            /* KairoX86#233: the clock to the GPU; col left as the pixel loop's last pair leaves it */
            gpu_clocks[gpu_count++] = out_edat;
            const uint32_t last_c0  = (out_edat >> ((shift_values >> 18) & 0x1C)) & 0xF;
            const uint32_t last_c1  = (out_edat >> ((shift_values >> 21) & 0x1C)) & 0xF;
            if (combine8bits)
                col = svga->map8[((last_c0 << 4) | last_c1) & svga->dac_mask];
            else if ((x + 6 - svga->scrollcache) & 0x01)
                col = last_c1 << 4;
            else
                col = (last_c0 << 4) | last_c1;
            p += charwidth;
            continue;
        }

        for (int i = 0; i < (8 + (svga->ati_4color ? 8 : 0)); i += (svga->ati_4color ? 4 : 2)) {
            /*
               c0 denotes the first 4bpp pixel shifted, while c1 denotes the second.
               For 8bpp modes, the first 4bpp pixel is the upper 4 bits.
             */
            uint32_t c0 = (out_edat >> (current_shift & 0x1C)) & 0xF;
            current_shift >>= 3;
            uint32_t c1 = (out_edat >> (current_shift & 0x1C)) & 0xF;
            current_shift >>= 3;

            if (svga->ati_4color) {
                uint32_t  q[4];
                q[0]      = svga->pallook[svga->egapal[(c0 & 0x0c) >> 2]];
                q[1]      = svga->pallook[svga->egapal[c0 & 0x03]];
                q[2]      = svga->pallook[svga->egapal[(c1 & 0x0c) >> 2]];
                q[3]      = svga->pallook[svga->egapal[c1 & 0x03]];

                const int outoffs = i << dwshift;
                for (int ch = 0; ch < 4; ch++) {
                    for (int subx = 0; subx < dotwidth; subx++)
                        p[outoffs + subx + (dotwidth * ch)] = q[ch];
                }
            } else if (combine8bits) {
                if (svga->packed_4bpp) {
                    uint32_t  p0;
                    uint32_t  p1;
                    if (svga->half_pixel) {
                        col                 &= 0xf0;
                        col                 |= (c0 >> 4) & 0xff;
                        col2                 = (c0 << 4) & 0xff;
                        col2                |= (c1 >> 4) & 0xff;
                        p0                  = svga->map8[col & svga->dac_mask];
                        p1                  = svga->map8[col2 & svga->dac_mask];
                        col                 = (c1 << 4) & 0xff;
                    } else {
                        p0                = svga->map8[c0 & svga->dac_mask];
                        p1                = svga->map8[c1 & svga->dac_mask];
                        col                 = p1;
                    }
                    const int outoffs = i << dwshift;
                    for (int subx = 0; subx < dotwidth; subx++)
                        p[outoffs + subx] = p0;
                    for (int subx = 0; subx < dotwidth; subx++)
                        p[outoffs + subx + dotwidth] = p1;
                } else {
                    uint32_t  ccombined = (c0 << 4) | c1;
                    uint32_t  p0;
                    if (svga->half_pixel) {
                        col                 &= 0xf0;
                        col                 |= (ccombined >> 4) & 0xff;
                        p0                  = svga->map8[col & svga->dac_mask];
                        col                 = (ccombined << 4) & 0xff;
                    } else {
                        p0                  = svga->map8[ccombined & svga->dac_mask];
                        col                 = p0;
                    }
                    const int outoffs   = (i >> 1) << dwshift;
                    for (int subx = 0; subx < dotwidth; subx++)
                        p[outoffs + subx] = p0;
                }
            } else {
                uint32_t  p0      = svga->pallook[svga->egapal[c0] & svga->dac_mask];
                uint32_t  p1      = svga->pallook[svga->egapal[c1] & svga->dac_mask];
                const int outoffs = i << dwshift;
                for (int subx = 0; subx < dotwidth; subx++)
                    p[outoffs + subx] = p0;
                for (int subx = 0; subx < dotwidth; subx++)
                    p[outoffs + subx + dotwidth] = p1;
                if ((x + i - svga->scrollcache) & 0x01)
                    /* The lower 4 bits are undefined at this point. */
                    col = c1 << 4;
                else
                    col = (c0 << 4) | c1;
            }
        }

        if (svga->ati_4color)
            p += (charwidth << 1);
            // p += charwidth;
        else
            p += charwidth;
    }
    if (gpu_clocks != NULL)
        kairo_gpu_scan_commit(); /* KairoX86#233 */
    }

    if (svga->render_line_offset < 0) {
        uint32_t *orig_line = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];
        memmove(orig_line, orig_line + (charwidth * -svga->render_line_offset), (svga->hdisp) * 4);
        memset((orig_line + svga->hdisp) - (charwidth * -svga->render_line_offset), svga->overscan_color, (size_t) charwidth * -svga->render_line_offset * 4);
    }
}

/*
   Remap these to the paletted renderer
   (*, highres, combine8bits)
 */
void svga_render_2bpp_lowres(svga_t *svga) { svga_render_indexed_gfx(svga, false, false); }
void svga_render_2bpp_highres(svga_t *svga) { svga_render_indexed_gfx(svga, true, false); }
void svga_render_4bpp_lowres(svga_t *svga) { svga_render_indexed_gfx(svga, false, false); }
void svga_render_4bpp_highres(svga_t *svga) { svga_render_indexed_gfx(svga, true, false); }
void svga_render_8bpp_lowres(svga_t *svga) { svga_render_indexed_gfx(svga, false, true); }
void svga_render_8bpp_highres(svga_t *svga) { svga_render_indexed_gfx(svga, true, true); }

void
svga_render_4bpp_tseng_highres(svga_t *svga)
{
    uint32_t  addr;
    uint8_t   edat[4];
    uint32_t  colours[16];
    bool      changed;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->force_old_addr) {
        const int changed_offset = (svga->memaddr + (svga->scanline & ~svga->crtc[0x17] & 3) * 0x8000) >> 12;

        changed = svga->changedvram[changed_offset] || svga->changedvram[changed_offset + 1] || svga->fullchange;
    } else {
        const uint32_t changed_addr = svga->remap_func(svga, svga->memaddr);

        changed = svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange;
    }
    if (!changed)
        return;

    uint32_t *p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

    if (svga->firstline_draw == 2000)
        svga->firstline_draw = svga->displine;
    svga->lastline_draw = svga->displine;

    for (int v = 0; v < 16; v++)
        colours[v] = svga->pallook[svga->egapal[v]];
    const int end = svga->hdisp + svga->scrollcache;
    /* KairoX86#233: each 8 pixels' nibbles to the GPU, when it draws the line (the plane mask within 4 bits) */
    uint8_t *gpu = ((end >= 0) && !(svga->plane_mask & ~0x0f))
                       ? render_gpu_bits(svga, p, 4, (uint32_t) (end / 8 + 1) * 8, false, colours, 16,
                                         svga->render == svga_render_4bpp_tseng_highres)
                       : NULL;

    for (int x = 0; x <= end; x += 8) {
        int oddeven = 0;

        if (svga->force_old_addr) {
            addr = svga->memaddr;

            if (!(svga->crtc[0x17] & 0x40)) {
                addr = (addr << 1) & svga->vram_mask;

                if (svga->seqregs[1] & 4)
                    oddeven = (addr & 4) ? 1 : 0;

                addr &= ~7;

                if ((svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x20000))
                    addr |= 4;
                if (!(svga->crtc[0x17] & 0x20) && (svga->memaddr & 0x8000))
                    addr |= 4;
            }

            if (!(svga->crtc[0x17] & 0x01))
                addr = (addr & ~0x8000) | ((svga->scanline & 1) ? 0x8000 : 0);
            if (!(svga->crtc[0x17] & 0x02))
                addr = (addr & ~0x10000) | ((svga->scanline & 2) ? 0x10000 : 0);
        } else {
            addr = svga->remap_func(svga, svga->memaddr);
            if (svga->seqregs[1] & 4)
                oddeven = (addr & 4) ? 1 : 0;
        }

        if (svga->seqregs[1] & 4) {
            edat[0] = svga->vram[addr | oddeven];
            edat[2] = svga->vram[addr | oddeven | 0x2];
            edat[1] = edat[3] = 0;
            svga->memaddr += 2;
        } else {
            *(uint32_t *) (&edat[0]) = *(uint32_t *) (&svga->vram[addr]);
            svga->memaddr += 4;
        }
        svga->memaddr &= svga->vram_mask;

        render_edat_pixels(svga, edat, 0xff, &p, &gpu);
    }
    if (gpu != NULL)
        kairo_gpu_scan_commit();
}

void
svga_render_8bpp_clone_highres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  dat;
    uint32_t  changed_addr;
    uint32_t  addr;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->force_old_addr) {
        if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            /* KairoX86#233: the pixels left of hdisp to the GPU */
            const int gpu_x = render_gpu_seq8(svga, p, 2, false, false, svga->render == svga_render_8bpp_clone_highres);
            p += gpu_x;
            for (x = gpu_x; x <= (svga->hdisp /* + svga->scrollcache*/); x += 8) {
                dat  = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);
                p[0] = svga->map8[dat & svga->dac_mask & 0xff];
                p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];
                p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];
                p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];

                dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);
                p[4] = svga->map8[dat & svga->dac_mask & 0xff];
                p[5] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];
                p[6] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];
                p[7] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];

                svga->memaddr += 8;
                p += 8;
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    } else {
        changed_addr = svga->remap_func(svga, svga->memaddr);

        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            if (!svga->remap_required) {
                /* KairoX86#233: the pixels left of hdisp to the GPU */
                const int gpu_x = render_gpu_seq8(svga, p, 2, false, false, svga->render == svga_render_8bpp_clone_highres);
                p += gpu_x;
                for (x = gpu_x; x <= (svga->hdisp /* + svga->scrollcache*/); x += 8) {
                    dat  = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);
                    p[0] = svga->map8[dat & svga->dac_mask & 0xff];
                    p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];
                    p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];
                    p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];

                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);
                    p[4] = svga->map8[dat & svga->dac_mask & 0xff];
                    p[5] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];
                    p[6] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];
                    p[7] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];

                    svga->memaddr += 8;
                    p += 8;
                }
            } else {
                for (x = 0; x <= (svga->hdisp /* + svga->scrollcache*/); x += 4) {
                    addr = svga->remap_func(svga, svga->memaddr);
                    dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);
                    p[0] = svga->map8[dat & svga->dac_mask & 0xff];
                    p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];
                    p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];
                    p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];

                    svga->memaddr += 4;
                    p += 4;
                }
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    }
}

// TODO: Integrate more of this into the generic paletted renderer --GM
#if 0
void
svga_render_8bpp_lowres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  dat;
    uint32_t  changed_addr;
    uint32_t  addr;

    if ((svga->displine + svga->y_add) < 0)
        return;

    if (svga->force_old_addr) {
        if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {
                dat = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);

                p[0] = p[1] = svga->map8[dat & 0xff];
                p[2] = p[3] = svga->map8[(dat >> 8) & 0xff];
                p[4] = p[5] = svga->map8[(dat >> 16) & 0xff];
                p[6] = p[7] = svga->map8[(dat >> 24) & 0xff];

                svga->memaddr += 4;
                p += 8;
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    } else {
        changed_addr = svga->remap_func(svga, svga->memaddr);

        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            if (!svga->remap_required) {
                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {
                    dat  = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);
                    p[0] = p[1] = svga->map8[dat & svga->dac_mask & 0xff];
                    p[2] = p[3] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];
                    p[4] = p[5] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];
                    p[6] = p[7] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];

                    svga->memaddr += 4;
                    p += 8;
                }
            } else {
                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 8) {
                    addr = svga->remap_func(svga, svga->memaddr);
                    dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);
                    p[0] = p[1] = svga->map8[dat & svga->dac_mask & 0xff];
                    p[2] = p[3] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];
                    p[4] = p[5] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];
                    p[6] = p[7] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];

                    svga->memaddr += 4;
                    p += 8;
                }
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    }
}

void
svga_render_8bpp_highres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  dat;
    uint32_t  changed_addr;
    uint32_t  addr;

    if ((svga->displine + svga->y_add) < 0)
        return;

    if (svga->force_old_addr) {
        if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            for (x = 0; x <= (svga->hdisp /* + svga->scrollcache*/); x += 8) {
                dat  = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);
                p[0] = svga->map8[dat & svga->dac_mask & 0xff];
                p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];
                p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];
                p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];

                dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);
                p[4] = svga->map8[dat & svga->dac_mask & 0xff];
                p[5] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];
                p[6] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];
                p[7] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];

                svga->memaddr += 8;
                p += 8;
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    } else {
        changed_addr = svga->remap_func(svga, svga->memaddr);

        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            if (!svga->remap_required) {
                for (x = 0; x <= (svga->hdisp /* + svga->scrollcache*/); x += 8) {
                    dat  = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);
                    p[0] = svga->map8[dat & svga->dac_mask & 0xff];
                    p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];
                    p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];
                    p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];

                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);
                    p[4] = svga->map8[dat & svga->dac_mask & 0xff];
                    p[5] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];
                    p[6] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];
                    p[7] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];

                    svga->memaddr += 8;
                    p += 8;
                }
            } else {
                for (x = 0; x <= (svga->hdisp /* + svga->scrollcache*/); x += 4) {
                    addr = svga->remap_func(svga, svga->memaddr);
                    dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);
                    p[0] = svga->map8[dat & svga->dac_mask & 0xff];
                    p[1] = svga->map8[(dat >> 8) & svga->dac_mask & 0xff];
                    p[2] = svga->map8[(dat >> 16) & svga->dac_mask & 0xff];
                    p[3] = svga->map8[(dat >> 24) & svga->dac_mask & 0xff];

                    svga->memaddr += 4;
                    p += 4;
                }
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    }
}
#endif

void
svga_render_8bpp_tseng_lowres(svga_t *svga)
{
    uint32_t *p;
    uint32_t  dat;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange || svga->render_line_offset) {
        p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

        if (svga->firstline_draw == 2000)
            svga->firstline_draw = svga->displine;
        svga->lastline_draw = svga->displine;

        if (svga->render_line_offset) {
            if (svga->render_line_offset > 0) {
                memset(p, svga->overscan_color, 8 * svga->render_line_offset * sizeof(uint32_t));
                p += 8 * svga->render_line_offset;
            }
        }

        /* KairoX86#233: the pixels left of hdisp to the GPU */
        const int gpu_x = render_gpu_seq8(svga, p, 1, true, true, svga->render == svga_render_8bpp_tseng_lowres);
        p += gpu_x;
        for (int x = gpu_x; x <= (svga->hdisp + svga->scrollcache); x += 8) {
            dat = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);
            if (svga->attrregs[0x10] & 0x80)
                dat = (dat & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);
            p[0] = p[1] = svga->map8[dat & svga->dac_mask & 0xff];
            dat >>= 8;
            if (svga->attrregs[0x10] & 0x80)
                dat = (dat & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);
            p[2] = p[3] = svga->map8[dat & svga->dac_mask & 0xff];
            dat >>= 8;
            if (svga->attrregs[0x10] & 0x80)
                dat = (dat & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);
            p[4] = p[5] = svga->map8[dat & svga->dac_mask & 0xff];
            dat >>= 8;
            if (svga->attrregs[0x10] & 0x80)
                dat = (dat & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);
            p[6] = p[7] = svga->map8[dat & svga->dac_mask & 0xff];

            svga->memaddr += 4;
            p += 8;
        }
        if (svga->render_line_offset < 0) {
            uint32_t *orig_line = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];
            memmove(orig_line, orig_line + (8 * -svga->render_line_offset), (svga->hdisp) * 4);
            memset((orig_line + svga->hdisp) - (8 * -svga->render_line_offset), svga->overscan_color, 8 * -svga->render_line_offset * 4);
        }
        svga->memaddr &= svga->vram_display_mask;
    }
}

void
svga_render_8bpp_tseng_highres(svga_t *svga)
{
    uint32_t *p;
    uint32_t  dat;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange || svga->render_line_offset) {
        p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

        if (svga->firstline_draw == 2000)
            svga->firstline_draw = svga->displine;
        svga->lastline_draw = svga->displine;

        if (svga->render_line_offset) {
            if (svga->render_line_offset > 0) {
                memset(p, svga->overscan_color, 8 * svga->render_line_offset * sizeof(uint32_t));
                p += 8 * svga->render_line_offset;
            }
        }

        /* KairoX86#233: the pixels left of hdisp to the GPU */
        const int gpu_x = render_gpu_seq8(svga, p, 2, false, true, svga->render == svga_render_8bpp_tseng_highres);
        p += gpu_x;
        for (int x = gpu_x; x <= (svga->hdisp /* + svga->scrollcache*/); x += 8) {
            dat = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);
            if (svga->attrregs[0x10] & 0x80)
                dat = (dat & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);
            p[0] = svga->map8[dat & svga->dac_mask & 0xff];
            dat >>= 8;
            if (svga->attrregs[0x10] & 0x80)
                dat = (dat & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);
            p[1] = svga->map8[dat & svga->dac_mask & 0xff];
            dat >>= 8;
            if (svga->attrregs[0x10] & 0x80)
                dat = (dat & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);
            p[2] = svga->map8[dat & svga->dac_mask & 0xff];
            dat >>= 8;
            if (svga->attrregs[0x10] & 0x80)
                dat = (dat & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);
            p[3] = svga->map8[dat & svga->dac_mask & 0xff];

            dat = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);
            if (svga->attrregs[0x10] & 0x80)
                dat = (dat & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);
            p[4] = svga->map8[dat & svga->dac_mask & 0xff];
            dat >>= 8;
            if (svga->attrregs[0x10] & 0x80)
                dat = (dat & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);
            p[5] = svga->map8[dat & svga->dac_mask & 0xff];
            dat >>= 8;
            if (svga->attrregs[0x10] & 0x80)
                dat = (dat & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);
            p[6] = svga->map8[dat & svga->dac_mask & 0xff];
            dat >>= 8;
            if (svga->attrregs[0x10] & 0x80)
                dat = (dat & ~0xf0) | ((svga->attrregs[0x14] & 0x0f) << 4);
            p[7] = svga->map8[dat & svga->dac_mask & 0xff];

            svga->memaddr += 8;
            p += 8;
        }

        if (svga->render_line_offset < 0) {
            uint32_t *orig_line = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];
            memmove(orig_line, orig_line + (8 * -svga->render_line_offset), (svga->hdisp) * 4);
            memset((orig_line + svga->hdisp) - (8 * -svga->render_line_offset), svga->overscan_color, 8 * -svga->render_line_offset * 4);
        }

        svga->memaddr &= svga->vram_display_mask;
    }
}

void
svga_render_15bpp_lowres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  dat;
    uint32_t  changed_addr;
    uint32_t  addr;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->force_old_addr) {
        if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            /* KairoX86#233: the pixels left of hdisp to the GPU */
            x = render_gpu_wide(svga, p, 15, (svga->render == svga_render_15bpp_lowres) && (svga->conv_16to32 == svga_conv_16to32));
            for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {
                dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);

                p[x << 1] = p[(x << 1) + 1] = svga->conv_16to32(svga, dat & 0xffff, 15);
                p[(x << 1) + 2] = p[(x << 1) + 3] = svga->conv_16to32(svga, dat >> 16, 15);

                dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 4) & svga->vram_display_mask]);

                p[(x << 1) + 4] = p[(x << 1) + 5] = svga->conv_16to32(svga, dat & 0xffff, 15);
                p[(x << 1) + 6] = p[(x << 1) + 7] = svga->conv_16to32(svga, dat >> 16, 15);
            }
            svga->memaddr += x << 1;
            svga->memaddr &= svga->vram_display_mask;
        }
    } else {
        changed_addr = svga->remap_func(svga, svga->memaddr);

        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            if (!svga->remap_required) {
                /* KairoX86#233: the pixels left of hdisp to the GPU */
                x = render_gpu_wide(svga, p, 15, (svga->render == svga_render_15bpp_lowres) && (svga->conv_16to32 == svga_conv_16to32));
                p += 2 * x;
                for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {
                    dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);

                    p[0] = p[1] = svga->conv_16to32(svga, dat & 0xffff, 15);
                    p[2] = p[3] = svga->conv_16to32(svga, dat >> 16, 15);

                    dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 4) & svga->vram_display_mask]);

                    p[4] = p[5] = svga->conv_16to32(svga, dat & 0xffff, 15);
                    p[6] = p[7] = svga->conv_16to32(svga, dat >> 16, 15);
                    p += 8;
                }
                svga->memaddr += x << 1;
            } else {
                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 2) {
                    addr = svga->remap_func(svga, svga->memaddr);
                    dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);

                    p[0] = p[1] = svga->conv_16to32(svga, dat & 0xffff, 15);
                    p[2] = p[3] = svga->conv_16to32(svga, dat >> 16, 15);
                    p += 4;
                    svga->memaddr += 4;
                }
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    }
}

void
svga_render_15bpp_highres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  dat;
    uint32_t  changed_addr;
    uint32_t  addr;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->force_old_addr) {
        if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            /* KairoX86#233: the pixels left of hdisp to the GPU */
            x = render_gpu_direct(svga, p, 15, (svga->render == svga_render_15bpp_highres) && (svga->conv_16to32 == svga_conv_16to32));
            for (; x <= (svga->hdisp + svga->scrollcache); x += 8) {
                dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);
                p[x]     = svga->conv_16to32(svga, dat & 0xffff, 15);
                p[x + 1] = svga->conv_16to32(svga, dat >> 16, 15);

                dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 4) & svga->vram_display_mask]);
                p[x + 2] = svga->conv_16to32(svga, dat & 0xffff, 15);
                p[x + 3] = svga->conv_16to32(svga, dat >> 16, 15);

                dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 8) & svga->vram_display_mask]);
                p[x + 4] = svga->conv_16to32(svga, dat & 0xffff, 15);
                p[x + 5] = svga->conv_16to32(svga, dat >> 16, 15);

                dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 12) & svga->vram_display_mask]);
                p[x + 6] = svga->conv_16to32(svga, dat & 0xffff, 15);
                p[x + 7] = svga->conv_16to32(svga, dat >> 16, 15);
            }
            svga->memaddr += x << 1;
            svga->memaddr &= svga->vram_display_mask;
        }
    } else {
        changed_addr = svga->remap_func(svga, svga->memaddr);

        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            if (!svga->remap_required) {
                /* KairoX86#233: the pixels left of hdisp to the GPU */
                x = render_gpu_direct(svga, p, 15, (svga->render == svga_render_15bpp_highres) && (svga->conv_16to32 == svga_conv_16to32));
                p += x;
                for (; x <= (svga->hdisp + svga->scrollcache); x += 8) {
                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);
                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 15);
                    *p++ = svga->conv_16to32(svga, dat >> 16, 15);

                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 4) & svga->vram_display_mask]);
                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 15);
                    *p++ = svga->conv_16to32(svga, dat >> 16, 15);

                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 8) & svga->vram_display_mask]);
                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 15);
                    *p++ = svga->conv_16to32(svga, dat >> 16, 15);

                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 12) & svga->vram_display_mask]);
                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 15);
                    *p++ = svga->conv_16to32(svga, dat >> 16, 15);
                }
                svga->memaddr += x << 1;
            } else {
                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 2) {
                    addr = svga->remap_func(svga, svga->memaddr);
                    dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);

                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 15);
                    *p++ = svga->conv_16to32(svga, dat >> 16, 15);
                    svga->memaddr += 4;
                }
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    }
}

void
svga_render_15bpp_mix_lowres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  dat;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange) {
        p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

        if (svga->firstline_draw == 2000)
            svga->firstline_draw = svga->displine;
        svga->lastline_draw = svga->displine;

        /* KairoX86#233: the pixels left of hdisp to the GPU */
        x = render_gpu_wide(svga, p, 0x1f15, (svga->render == svga_render_15bpp_mix_lowres) && (svga->conv_16to32 == svga_conv_16to32));
        for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {
            dat       = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);
            p[x << 1] = p[(x << 1) + 1] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);

            dat >>= 16;
            p[(x << 1) + 2] = p[(x << 1) + 3] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);

            dat             = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 4) & svga->vram_display_mask]);
            p[(x << 1) + 4] = p[(x << 1) + 5] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);

            dat >>= 16;
            p[(x << 1) + 6] = p[(x << 1) + 7] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);
        }
        svga->memaddr += x << 1;
        svga->memaddr &= svga->vram_display_mask;
    }
}

void
svga_render_15bpp_mix_highres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  dat;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange) {
        p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

        if (svga->firstline_draw == 2000)
            svga->firstline_draw = svga->displine;
        svga->lastline_draw = svga->displine;

        /* KairoX86#233: the pixels left of hdisp to the GPU */
        x = render_gpu_direct(svga, p, 0x1f15, (svga->render == svga_render_15bpp_mix_highres) && (svga->conv_16to32 == svga_conv_16to32));
        for (; x <= (svga->hdisp + svga->scrollcache); x += 8) {
            dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);
            p[x] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);
            dat >>= 16;
            p[x + 1] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);

            dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 4) & svga->vram_display_mask]);
            p[x + 2] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);
            dat >>= 16;
            p[x + 3] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);

            dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 8) & svga->vram_display_mask]);
            p[x + 4] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);
            dat >>= 16;
            p[x + 5] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);

            dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 12) & svga->vram_display_mask]);
            p[x + 6] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);
            dat >>= 16;
            p[x + 7] = (dat & 0x00008000) ? svga->pallook[dat & 0xff] : svga->conv_16to32(svga, dat & 0xffff, 15);
        }
        svga->memaddr += x << 1;
        svga->memaddr &= svga->vram_display_mask;
    }
}

void
svga_render_16bpp_lowres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  dat;
    uint32_t  changed_addr;
    uint32_t  addr;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->force_old_addr) {
        if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            /* KairoX86#233: the pixels left of hdisp to the GPU */
            x = render_gpu_wide(svga, p, 16, (svga->render == svga_render_16bpp_lowres) && (svga->conv_16to32 == svga_conv_16to32));
            for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {
                dat       = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);
                p[x << 1] = p[(x << 1) + 1] = svga->conv_16to32(svga, dat & 0xffff, 16);
                p[(x << 1) + 2] = p[(x << 1) + 3] = svga->conv_16to32(svga, dat >> 16, 16);

                dat             = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 4) & svga->vram_display_mask]);
                p[(x << 1) + 4] = p[(x << 1) + 5] = svga->conv_16to32(svga, dat & 0xffff, 16);
                p[(x << 1) + 6] = p[(x << 1) + 7] = svga->conv_16to32(svga, dat >> 16, 16);
            }
            svga->memaddr += x << 1;
            svga->memaddr &= svga->vram_display_mask;
        }
    } else {
        changed_addr = svga->remap_func(svga, svga->memaddr);

        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            if (!svga->remap_required) {
                /* KairoX86#233: the pixels left of hdisp to the GPU */
                x = render_gpu_wide(svga, p, 16, (svga->render == svga_render_16bpp_lowres) && (svga->conv_16to32 == svga_conv_16to32));
                p += 2 * x;
                for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {
                    dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);

                    p[0] = p[1] = svga->conv_16to32(svga, dat & 0xffff, 16);
                    p[2] = p[3] = svga->conv_16to32(svga, dat >> 16, 16);

                    dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 4) & svga->vram_display_mask]);

                    p[4] = p[5] = svga->conv_16to32(svga, dat & 0xffff, 16);
                    p[6] = p[7] = svga->conv_16to32(svga, dat >> 16, 16);
                    p += 8;
                }
                svga->memaddr += x << 1;
            } else {
                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 2) {
                    addr = svga->remap_func(svga, svga->memaddr);
                    dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);

                    p[0] = p[1] = svga->conv_16to32(svga, dat & 0xffff, 16);
                    p[2] = p[3] = svga->conv_16to32(svga, dat >> 16, 16);
                    p += 4;
                    svga->memaddr += 4;
                }
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    }
}

void
svga_render_16bpp_highres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  dat;
    uint32_t  changed_addr;
    uint32_t  addr;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->force_old_addr) {
        if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            /* KairoX86#233: the pixels left of hdisp to the GPU */
            x = render_gpu_direct(svga, p, 16, (svga->render == svga_render_16bpp_highres) && (svga->conv_16to32 == svga_conv_16to32));
            for (; x <= (svga->hdisp + svga->scrollcache); x += 8) {
                uint32_t dat = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);
                p[x]         = svga->conv_16to32(svga, dat & 0xffff, 16);
                p[x + 1]     = svga->conv_16to32(svga, dat >> 16, 16);

                dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 4) & svga->vram_display_mask]);
                p[x + 2] = svga->conv_16to32(svga, dat & 0xffff, 16);
                p[x + 3] = svga->conv_16to32(svga, dat >> 16, 16);

                dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 8) & svga->vram_display_mask]);
                p[x + 4] = svga->conv_16to32(svga, dat & 0xffff, 16);
                p[x + 5] = svga->conv_16to32(svga, dat >> 16, 16);

                dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 12) & svga->vram_display_mask]);
                p[x + 6] = svga->conv_16to32(svga, dat & 0xffff, 16);
                p[x + 7] = svga->conv_16to32(svga, dat >> 16, 16);
            }
            svga->memaddr += x << 1;
            svga->memaddr &= svga->vram_display_mask;
        }
    } else {
        changed_addr = svga->remap_func(svga, svga->memaddr);

        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            if (!svga->remap_required) {
                /* KairoX86#233: the pixels left of hdisp to the GPU */
                x = render_gpu_direct(svga, p, 16, (svga->render == svga_render_16bpp_highres) && (svga->conv_16to32 == svga_conv_16to32));
                p += x;
                for (; x <= (svga->hdisp + svga->scrollcache); x += 8) {
                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1)) & svga->vram_display_mask]);
                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 16);
                    *p++ = svga->conv_16to32(svga, dat >> 16, 16);

                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 4) & svga->vram_display_mask]);
                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 16);
                    *p++ = svga->conv_16to32(svga, dat >> 16, 16);

                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 8) & svga->vram_display_mask]);
                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 16);
                    *p++ = svga->conv_16to32(svga, dat >> 16, 16);

                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 1) + 12) & svga->vram_display_mask]);
                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 16);
                    *p++ = svga->conv_16to32(svga, dat >> 16, 16);
                }
                svga->memaddr += x << 1;
            } else {
                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 2) {
                    addr = svga->remap_func(svga, svga->memaddr);
                    dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);

                    *p++ = svga->conv_16to32(svga, dat & 0xffff, 16);
                    *p++ = svga->conv_16to32(svga, dat >> 16, 16);

                    svga->memaddr += 4;
                }
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    }
}

void
svga_render_24bpp_lowres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  changed_addr;
    uint32_t  addr;
    uint32_t  dat0;
    uint32_t  dat1;
    uint32_t  dat2;
    uint32_t  fg;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->force_old_addr) {
        if ((svga->displine + svga->y_add) < 0)
            return;

        if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange) {
            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x++) {
                fg = svga->vram[svga->memaddr] | (svga->vram[svga->memaddr + 1] << 8) | (svga->vram[svga->memaddr + 2] << 16);
                svga->memaddr += 3;
                svga->memaddr &= svga->vram_display_mask;
                svga->monitor->target_buffer->line[svga->displine + svga->y_add][(x << 1) + svga->x_add] = svga->monitor->target_buffer->line[svga->displine + svga->y_add][(x << 1) + 1 + svga->x_add] = lookup_lut(fg);
            }
        }
    } else {
        changed_addr = svga->remap_func(svga, svga->memaddr);

        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            if (!svga->remap_required) {
                /* KairoX86#233: the pixels left of hdisp to the GPU */
                x = render_gpu_24(svga, p, true, svga->render == svga_render_24bpp_lowres);
                p += 2 * x;
                for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {
                    dat0 = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);
                    dat1 = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);
                    dat2 = *(uint32_t *) (&svga->vram[(svga->memaddr + 8) & svga->vram_display_mask]);

                    p[0] = p[1] = lookup_lut(dat0 & 0xffffff);
                    p[2] = p[3] = lookup_lut((dat0 >> 24) | ((dat1 & 0xffff) << 8));
                    p[4] = p[5] = lookup_lut((dat1 >> 16) | ((dat2 & 0xff) << 16));
                    p[6] = p[7] = lookup_lut(dat2 >> 8);
                    p += 8;

                    svga->memaddr += 12;
                }
            } else {
                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 4) {
                    addr = svga->remap_func(svga, svga->memaddr);
                    dat0 = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);
                    addr = svga->remap_func(svga, svga->memaddr + 4);
                    dat1 = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);
                    addr = svga->remap_func(svga, svga->memaddr + 8);
                    dat2 = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);

                    p[0] = p[1] = lookup_lut(dat0 & 0xffffff);
                    p[2] = p[3] = lookup_lut((dat0 >> 24) | ((dat1 & 0xffff) << 8));
                    p[4] = p[5] = lookup_lut((dat1 >> 16) | ((dat2 & 0xff) << 16));
                    p[6] = p[7] = lookup_lut(dat2 >> 8);
                    p += 8;

                    svga->memaddr += 12;
                }
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    }
}

void
svga_render_24bpp_highres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  changed_addr;
    uint8_t   addr;
    uint32_t  dat0;
    uint32_t  dat1;
    uint32_t  dat2;
    uint32_t  dat;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->force_old_addr) {
        if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 4) {
                dat  = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);
                p[x] = lookup_lut(dat & 0xffffff);

                dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + 3) & svga->vram_display_mask]);
                p[x + 1] = lookup_lut(dat & 0xffffff);

                dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + 6) & svga->vram_display_mask]);
                p[x + 2] = lookup_lut(dat & 0xffffff);

                dat      = *(uint32_t *) (&svga->vram[(svga->memaddr + 9) & svga->vram_display_mask]);
                p[x + 3] = lookup_lut(dat & 0xffffff);

                svga->memaddr += 12;
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    } else {
        changed_addr = svga->remap_func(svga, svga->memaddr);

        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            if (!svga->remap_required) {
                /* KairoX86#233: the pixels left of hdisp to the GPU */
                x = render_gpu_24(svga, p, false, svga->render == svga_render_24bpp_highres);
                p += x;
                for (; x <= (svga->hdisp + svga->scrollcache); x += 4) {
                    dat0 = *(uint32_t *) (&svga->vram[svga->memaddr & svga->vram_display_mask]);
                    dat1 = *(uint32_t *) (&svga->vram[(svga->memaddr + 4) & svga->vram_display_mask]);
                    dat2 = *(uint32_t *) (&svga->vram[(svga->memaddr + 8) & svga->vram_display_mask]);

                    *p++ = lookup_lut(dat0 & 0xffffff);
                    *p++ = lookup_lut((dat0 >> 24) | ((dat1 & 0xffff) << 8));
                    *p++ = lookup_lut((dat1 >> 16) | ((dat2 & 0xff) << 16));
                    *p++ = lookup_lut(dat2 >> 8);

                    svga->memaddr += 12;
                }
            } else {
                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x += 4) {
                    addr = svga->remap_func(svga, svga->memaddr);
                    dat0 = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);
                    addr = svga->remap_func(svga, svga->memaddr + 4);
                    dat1 = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);
                    addr = svga->remap_func(svga, svga->memaddr + 8);
                    dat2 = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);

                    *p++ = lookup_lut(dat0 & 0xffffff);
                    *p++ = lookup_lut((dat0 >> 24) | ((dat1 & 0xffff) << 8));
                    *p++ = lookup_lut((dat1 >> 16) | ((dat2 & 0xff) << 16));
                    *p++ = lookup_lut(dat2 >> 8);

                    svga->memaddr += 12;
                }
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    }
}

void
svga_render_32bpp_lowres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  dat;
    uint32_t  changed_addr;
    uint32_t  addr;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->force_old_addr) {
        if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->fullchange) {
            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x++) {
                dat = svga->vram[svga->memaddr] | (svga->vram[svga->memaddr + 1] << 8) | (svga->vram[svga->memaddr + 2] << 16);
                svga->memaddr += 4;
                svga->memaddr &= svga->vram_display_mask;
                svga->monitor->target_buffer->line[svga->displine + svga->y_add][(x << 1) + svga->x_add] = svga->monitor->target_buffer->line[svga->displine + svga->y_add][(x << 1) + 1 + svga->x_add] = lookup_lut(dat);
            }
        }
    } else {
        changed_addr = svga->remap_func(svga, svga->memaddr);

        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            if (!svga->remap_required) {
                /* KairoX86#233: the pixels left of hdisp to the GPU */
                x = render_gpu_wide(svga, p, 32, svga->render == svga_render_32bpp_lowres);
                p += 2 * x;
                for (; x <= (svga->hdisp + svga->scrollcache); x++) {
                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 2)) & svga->vram_display_mask]);
                    *p++ = lookup_lut(dat & 0xffffff);
                    *p++ = lookup_lut(dat & 0xffffff);
                }
                svga->memaddr += (x * 4);
            } else {
                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x++) {
                    addr = svga->remap_func(svga, svga->memaddr);
                    dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);
                    *p++ = lookup_lut(dat & 0xffffff);
                    *p++ = lookup_lut(dat & 0xffffff);
                    svga->memaddr += 4;
                }
                svga->memaddr &= svga->vram_display_mask;
            }
        }
    }
}

void
svga_render_32bpp_highres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  dat;
    uint32_t  changed_addr;
    uint32_t  addr;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    if (svga->force_old_addr) {
        if (svga->changedvram[svga->memaddr >> 12] || svga->changedvram[(svga->memaddr >> 12) + 1] || svga->changedvram[(svga->memaddr >> 12) + 2] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            /* KairoX86#233: the pixels left of hdisp to the GPU */
            x = render_gpu_direct(svga, p, 32, svga->render == svga_render_32bpp_highres);
            for (; x <= (svga->hdisp + svga->scrollcache); x++) {
                dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 2)) & svga->vram_display_mask]);
                p[x] = lookup_lut(dat & 0xffffff);
            }
            svga->memaddr += 4;
            svga->memaddr &= svga->vram_display_mask;
        }
    } else {
        changed_addr = svga->remap_func(svga, svga->memaddr);

        if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
            p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

            if (svga->firstline_draw == 2000)
                svga->firstline_draw = svga->displine;
            svga->lastline_draw = svga->displine;

            if (!svga->remap_required) {
                /* KairoX86#233: the pixels left of hdisp to the GPU */
                x = render_gpu_direct(svga, p, 32, svga->render == svga_render_32bpp_highres);
                p += x;
                for (; x <= (svga->hdisp + svga->scrollcache); x++) {
                    dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 2)) & svga->vram_display_mask]);
                    *p++ = lookup_lut(dat & 0xffffff);
                }
                svga->memaddr += (x * 4);
            } else {
                for (x = 0; x <= (svga->hdisp + svga->scrollcache); x++) {
                    addr = svga->remap_func(svga, svga->memaddr);
                    dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);
                    *p++ = lookup_lut(dat & 0xffffff);

                    svga->memaddr += 4;
                }
            }
            svga->memaddr &= svga->vram_display_mask;
        }
    }
}

void
svga_render_ABGR8888_highres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  dat;
    uint32_t  changed_addr;
    uint32_t  addr;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    changed_addr = svga->remap_func(svga, svga->memaddr);

    if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
        p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

        if (svga->firstline_draw == 2000)
            svga->firstline_draw = svga->displine;
        svga->lastline_draw = svga->displine;

        if (!svga->remap_required) {
            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x++) {
                dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 2)) & svga->vram_display_mask]);
                *p++ = lookup_lut(((dat & 0xff0000) >> 16) | (dat & 0x00ff00) | ((dat & 0x0000ff) << 16));
            }
            svga->memaddr += x * 4;
        } else {
            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x++) {
                addr = svga->remap_func(svga, svga->memaddr);
                dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);
                *p++ = lookup_lut(((dat & 0xff0000) >> 16) | (dat & 0x00ff00) | ((dat & 0x0000ff) << 16));

                svga->memaddr += 4;
            }
        }
        svga->memaddr &= svga->vram_display_mask;
    }
}

void
svga_render_RGBA8888_highres(svga_t *svga)
{
    int       x;
    uint32_t *p;
    uint32_t  dat;
    uint32_t  changed_addr;
    uint32_t  addr;

    if (((svga->displine + svga->y_add) < 0) ||
        (svga->monitor->target_buffer == NULL) ||
        (svga->monitor->target_buffer->line[svga->displine + svga->y_add] == NULL))
        return;

    changed_addr = svga->remap_func(svga, svga->memaddr);

    if (svga->changedvram[changed_addr >> 12] || svga->changedvram[(changed_addr >> 12) + 1] || svga->fullchange) {
        p = &svga->monitor->target_buffer->line[svga->displine + svga->y_add][svga->x_add];

        if (svga->firstline_draw == 2000)
            svga->firstline_draw = svga->displine;
        svga->lastline_draw = svga->displine;

        if (!svga->remap_required) {
            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x++) {
                dat  = *(uint32_t *) (&svga->vram[(svga->memaddr + (x << 2)) & svga->vram_display_mask]);
                *p++ = lookup_lut(dat >> 8);
            }
            svga->memaddr += (x * 4);
        } else {
            for (x = 0; x <= (svga->hdisp + svga->scrollcache); x++) {
                addr = svga->remap_func(svga, svga->memaddr);
                dat  = *(uint32_t *) (&svga->vram[addr & svga->vram_display_mask]);
                *p++ = lookup_lut(dat >> 8);

                svga->memaddr += 4;
            }
        }
        svga->memaddr &= svga->vram_display_mask;
    }
}
