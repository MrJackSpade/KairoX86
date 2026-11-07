/*
 * 86Box    A hypervisor and IBM PC system emulator that specializes in
 *          running old operating systems and software designed for IBM
 *          PC systems and compatibles from 1981 through fairly recent
 *          system designs based on the PCI bus.
 *
 *          This file is part of the 86Box distribution.
 *
 *          3DFX Voodoo emulation.
 *
 * Authors: Sarah Walker, <https://pcem-emulator.co.uk/>
 *
 *          Copyright 2008-2020 Sarah Walker.
 */
#include <stdarg.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <wchar.h>
#include <math.h>
#define HAVE_STDARG_H
#include <86box/86box.h>
#include "cpu.h"
#include <86box/machine.h>
#include <86box/device.h>
#include <86box/mem.h>
#include <86box/pci.h>
#include <86box/timer.h>
#include <86box/device.h>
#include <86box/plat.h>
#include <86box/thread.h>
#include <86box/video.h>
#include <86box/vid_svga.h>
#include <86box/vid_voodoo_common.h>
#include <86box/vid_voodoo_blitter.h>
#include <86box/vid_voodoo_dither.h>
#include <86box/vid_voodoo_regs.h>
#include <86box/vid_voodoo_render.h>
#include <86box/kairo_gpu_banshee2d.h> /* KairoX86#277 */
#include <86box/vid_voodoo_k2d.h>

enum {
    BLIT_COMMAND_SCREEN_TO_SCREEN = 0,
    BLIT_COMMAND_CPU_TO_SCREEN    = 1,
    BLIT_COMMAND_RECT_FILL        = 2,
    BLIT_COMMAND_SGRAM_FILL       = 3
};

enum {
    BLIT_SRC_1BPP             = (0 << 3),
    BLIT_SRC_1BPP_BYTE_PACKED = (1 << 3),
    BLIT_SRC_16BPP            = (2 << 3),
    BLIT_SRC_24BPP            = (3 << 3),
    BLIT_SRC_24BPP_DITHER_2X2 = (4 << 3),
    BLIT_SRC_24BPP_DITHER_4X4 = (5 << 3)
};

enum {
    BLIT_SRC_RGB_ARGB = (0 << 6),
    BLIT_SRC_RGB_ABGR = (1 << 6),
    BLIT_SRC_RGB_RGBA = (2 << 6),
    BLIT_SRC_RGB_BGRA = (3 << 6)
};

enum {
    BLIT_COMMAND_MASK     = 7,
    BLIT_SRC_FORMAT       = (7 << 3),
    BLIT_SRC_RGB_FORMAT   = (3 << 6),
    BLIT_SRC_CHROMA       = (1 << 10),
    BLIT_DST_CHROMA       = (1 << 12),
    BLIT_CLIPPING_ENABLED = (1 << 16)
};

enum {
    BLIT_ROP_DST_PASS = (1 << 0),
    BLIT_ROP_SRC_PASS = (1 << 1)
};

#ifdef ENABLE_VOODOOBLT_LOG
int voodooblt_do_log = ENABLE_VOODOOBLT_LOG;

static void
voodooblt_log(const char *fmt, ...)
{
    va_list ap;

    if (voodooblt_do_log) {
        va_start(ap, fmt);
        pclog_ex(fmt, ap);
        va_end(ap);
    }
}
#else
#    define voodooblt_log(fmt, ...)
#endif

#define MIX(src_dat, dst_dat, rop)          \
    switch (rop) {                          \
        case 0x0:                           \
            dst_dat = 0;                    \
            break;                          \
        case 0x1:                           \
            dst_dat = ~(src_dat | dst_dat); \
            break;                          \
        case 0x2:                           \
            dst_dat = ~src_dat & dst_dat;   \
            break;                          \
        case 0x3:                           \
            dst_dat = ~src_dat;             \
            break;                          \
        case 0x4:                           \
            dst_dat = src_dat & ~dst_dat;   \
            break;                          \
        case 0x5:                           \
            dst_dat = ~dst_dat;             \
            break;                          \
        case 0x6:                           \
            dst_dat = src_dat ^ dst_dat;    \
            break;                          \
        case 0x7:                           \
            dst_dat = ~(src_dat & dst_dat); \
            break;                          \
        case 0x8:                           \
            dst_dat = src_dat & dst_dat;    \
            break;                          \
        case 0x9:                           \
            dst_dat = ~(src_dat ^ dst_dat); \
            break;                          \
        case 0xa:                           \
            dst_dat = dst_dat;              \
            break;                          \
        case 0xb:                           \
            dst_dat = ~src_dat | dst_dat;   \
            break;                          \
        case 0xc:                           \
            dst_dat = src_dat;              \
            break;                          \
        case 0xd:                           \
            dst_dat = src_dat | ~dst_dat;   \
            break;                          \
        case 0xe:                           \
            dst_dat = src_dat | dst_dat;    \
            break;                          \
        case 0xf:                           \
            dst_dat = 0xffff;               \
            break;                          \
    }

/* KairoX86#277: whether a 565 colour lies in the source (or destination) chroma range, in each channel */
static int
voodoo_v2_keyed(voodoo_t *voodoo, uint16_t c, int dst)
{
    const int r = c >> 11;
    const int g = (c >> 5) & 0x3f;
    const int b = c & 0x1f;

    if (dst)
        return r >= voodoo->bltDstChromaMinR && r <= voodoo->bltDstChromaMaxR && g >= voodoo->bltDstChromaMinG &&
               g <= voodoo->bltDstChromaMaxG && b >= voodoo->bltDstChromaMinB && b <= voodoo->bltDstChromaMaxB;
    return r >= voodoo->bltSrcChromaMinR && r <= voodoo->bltSrcChromaMaxR && g >= voodoo->bltSrcChromaMinG &&
           g <= voodoo->bltSrcChromaMaxG && b >= voodoo->bltSrcChromaMinB && b <= voodoo->bltSrcChromaMaxB;
}

/* KairoX86#277: one pixel of a walk at p: with mix, MIX with src through the raster operation the command's chroma
   keys choose; without, src stored (a fill). With Hardware acceleration on, recorded for the GPU: the Banshee 2D
   kernel's raster operation of the pattern, source and destination with the pattern left out (bltRop[n] in both
   halves), its 16-bit destination key the chroma range. */
static void
voodoo_v2_px(voodoo_t *voodoo, uint16_t *p, uint16_t src, int mix)
{
    if (voodoo->k2d != NULL) {
        uint32_t rec[B2_WORDS] = { 0 };

        if (mix) {
            for (int n = 0; n < 4; n++)
                rec[B2_ROPS] |= (uint32_t) (voodoo->bltRop[n] * 0x11) << (8 * n);
            if (voodoo->bltCommand & BLIT_DST_CHROMA) {
                rec[B2_DKEY]     = B2_KEY_16;
                rec[B2_DKEY_MIN] = (voodoo->bltDstChromaMinR << 11) | (voodoo->bltDstChromaMinG << 5) | voodoo->bltDstChromaMinB;
                rec[B2_DKEY_MAX] = (voodoo->bltDstChromaMaxR << 11) | (voodoo->bltDstChromaMaxG << 5) | voodoo->bltDstChromaMaxB;
            }
        } else
            rec[B2_ROPS] = 0xccccccccu;
        rec[B2_BYTES] = 2;
        voodoo_k2d_pixel(voodoo, (uint32_t) ((uint8_t *) p - voodoo->fb_mem), 2, rec, src, 0,
                         mix && (voodoo->bltCommand & BLIT_SRC_CHROMA) && voodoo_v2_keyed(voodoo, src, 0));
        return;
    }
    if (!mix) {
        *p = src;
        return;
    }
    uint16_t dst_dat = *p;
    int      rop     = 0;

    if ((voodoo->bltCommand & BLIT_SRC_CHROMA) && voodoo_v2_keyed(voodoo, src, 0))
        rop |= BLIT_ROP_SRC_PASS;
    if ((voodoo->bltCommand & BLIT_DST_CHROMA) && voodoo_v2_keyed(voodoo, dst_dat, 1))
        rop |= BLIT_ROP_DST_PASS;
    MIX(src, dst_dat, voodoo->bltRop[rop]);
    *p = dst_dat;
}

static void voodoo_v2_blit_start_walk(voodoo_t *voodoo);
static void voodoo_v2_blit_data_walk(voodoo_t *voodoo, uint32_t data);

/* KairoX86#277: the blitter's walks hold the 2D batch's lock (the machine's thread touches the frame buffer) */
void
voodoo_v2_blit_start(voodoo_t *voodoo)
{
    voodoo_k2d_lock(voodoo);
    voodoo_v2_blit_start_walk(voodoo);
    voodoo_k2d_unlock(voodoo);
}

void
voodoo_v2_blit_data(voodoo_t *voodoo, uint32_t data)
{
    voodoo_k2d_lock(voodoo);
    voodoo_v2_blit_data_walk(voodoo, data);
    voodoo_k2d_unlock(voodoo);
}

static void
voodoo_v2_blit_start_walk(voodoo_t *voodoo)
{
    uint64_t dat64;
    int      size_x = ABS(voodoo->bltSizeX);
    int      size_y = ABS(voodoo->bltSizeY);
    int      x_dir = (voodoo->bltSizeX > 0) ? 1 : -1;
    int      y_dir = (voodoo->bltSizeY > 0) ? 1 : -1;
    int      src_y = voodoo->bltSrcY & 0x7ff;
    int      dst_y = voodoo->bltDstY & 0x7ff;
    int      src_stride    = (voodoo->bltCommand & BLTCMD_SRC_TILED) ? ((voodoo->bltSrcXYStride & 0x3f) * 32 * 2) : (voodoo->bltSrcXYStride & 0xff8);
    int      dst_stride    = (voodoo->bltCommand & BLTCMD_DST_TILED) ? ((voodoo->bltDstXYStride & 0x3f) * 32 * 2) : (voodoo->bltDstXYStride & 0xff8);
    uint32_t src_base_addr = (voodoo->bltCommand & BLTCMD_SRC_TILED) ? ((voodoo->bltSrcBaseAddr & 0x3ff) << 12) : (voodoo->bltSrcBaseAddr & 0x3ffff8);
    uint32_t dst_base_addr = (voodoo->bltCommand & BLTCMD_DST_TILED) ? ((voodoo->bltDstBaseAddr & 0x3ff) << 12) : (voodoo->bltDstBaseAddr & 0x3ffff8);

#if 0
    voodooblt_log("blit_start: command=%08x srcX=%i srcY=%i dstX=%i dstY=%i sizeX=%i sizeY=%i color=%04x,%04x\n",
                  voodoo->bltCommand, voodoo->bltSrcX, voodoo->bltSrcY, voodoo->bltDstX, voodoo->bltDstY, voodoo->bltSizeX, voodoo->bltSizeY, voodoo->bltColorFg, voodoo->bltColorBg);
#endif

    voodoo_wait_for_render_thread_idle(voodoo);

    switch (voodoo->bltCommand & BLIT_COMMAND_MASK) {
        case BLIT_COMMAND_SCREEN_TO_SCREEN:
            for (int y = 0; y <= size_y; y++) {
                const uint16_t *src   = (uint16_t *) &voodoo->fb_mem[src_base_addr + src_y * src_stride];
                uint16_t       *dst   = (uint16_t *) &voodoo->fb_mem[dst_base_addr + dst_y * dst_stride];
                int             src_x = voodoo->bltSrcX;
                int             dst_x = voodoo->bltDstX;

                for (int x = 0; x <= size_x; x++) {
                    voodoo_k2d_read(voodoo, (const uint8_t *) &src[src_x], 2); /* KairoX86#277 */
                    uint16_t src_dat = src[src_x];

                    if (voodoo->bltCommand & BLIT_CLIPPING_ENABLED) {
                        if (dst_x < voodoo->bltClipLeft || dst_x >= voodoo->bltClipRight || dst_y < voodoo->bltClipLowY || dst_y >= voodoo->bltClipHighY)
                            goto skip_pixel_blit;
                    }

                    voodoo_v2_px(voodoo, &dst[dst_x], src_dat, 1); /* KairoX86#277 */
skip_pixel_blit:
                    src_x += x_dir;
                    dst_x += x_dir;
                }

                src_y += y_dir;
                dst_y += y_dir;
            }
            break;

        case BLIT_COMMAND_CPU_TO_SCREEN:
            voodoo->launch_pending = 1;
            break;

        case BLIT_COMMAND_RECT_FILL:
            for (int y = 0; y <= size_y; y++) {
                uint16_t *dst;
                int       dst_x = voodoo->bltDstX;

                if (SLI_ENABLED) {
                    if ((!(voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && (dst_y & 1)) || ((voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && !(dst_y & 1)))
                        goto skip_line_fill;
                    dst = (uint16_t *) &voodoo->fb_mem[dst_base_addr + (dst_y >> 1) * dst_stride];
                } else
                    dst = (uint16_t *) &voodoo->fb_mem[dst_base_addr + dst_y * dst_stride];

                for (int x = 0; x < size_x; x++) {
                    if (voodoo->bltCommand & BLIT_CLIPPING_ENABLED) {
                        if (dst_x < voodoo->bltClipLeft || dst_x >= voodoo->bltClipRight || dst_y < voodoo->bltClipLowY || dst_y >= voodoo->bltClipHighY)
                            goto skip_pixel_fill;
                    }

                    voodoo_v2_px(voodoo, &dst[dst_x], voodoo->bltColorFg, 0); /* KairoX86#277 */
skip_pixel_fill:
                    dst_x += x_dir;
                }
skip_line_fill:
                dst_y += y_dir;
            }
            break;

        case BLIT_COMMAND_SGRAM_FILL: {
            const int sgram_page_words = 512;

            /* Glide uses SGRAM fill for whole pages, with 512 64-bit words in X. */
            dst_y  = voodoo->bltDstY & 0x3ff;
            size_y = voodoo->bltSizeY & 0x3ff;

            /* Replicate the 16-bit fill color across one 64-bit write. */
            dat64 = voodoo->bltColorFg | ((uint64_t) voodoo->bltColorFg << 16) | ((uint64_t) voodoo->bltColorFg << 32) | ((uint64_t) voodoo->bltColorFg << 48);

            for (int y = 0; y <= size_y; y++) {
                uint64_t *dst = (uint64_t *) &voodoo->fb_mem[(dst_y * sgram_page_words * 8) & voodoo->fb_mask];

                voodoo_k2d_read(voodoo, (const uint8_t *) dst, sgram_page_words * 8); /* KairoX86#277 */
                for (int x = 0; x < sgram_page_words; x++)
                    dst[x] = dat64;

                dst_y++;
            }
            break;
        }

        default:
            fatal("bad blit command %08x\n", voodoo->bltCommand);
    }
}

static void
voodoo_v2_blit_data_walk(voodoo_t *voodoo, uint32_t data)
{
    int       src_bits  = 32;
    uint32_t  base_addr = (voodoo->bltCommand & BLTCMD_DST_TILED) ? ((voodoo->bltDstBaseAddr & 0x3ff) << 12) : (voodoo->bltDstBaseAddr & 0x3ffff8);
    uint32_t  addr;
    uint16_t *dst;

    if ((voodoo->bltCommand & BLIT_COMMAND_MASK) != BLIT_COMMAND_CPU_TO_SCREEN)
        return;

    if (voodoo->launch_pending) {
        voodoo->blt.dst_x      = voodoo->bltDstX;
        voodoo->blt.dst_y      = voodoo->bltDstY;
        voodoo->blt.cur_x      = 0;
        voodoo->blt.size_x     = voodoo->bltSizeX;
        voodoo->blt.size_y     = voodoo->bltSizeY;
        voodoo->blt.x_dir      = (voodoo->bltSizeX > 0) ? 1 : -1;
        voodoo->blt.y_dir      = (voodoo->bltSizeY > 0) ? 1 : -1;
        voodoo->blt.dst_stride = (voodoo->bltCommand & BLTCMD_DST_TILED) ? ((voodoo->bltDstXYStride & 0x3f) * 32 * 2) : (voodoo->bltDstXYStride & 0xff8);
        voodoo->launch_pending = 0;
    }

    if (SLI_ENABLED) {
        addr = base_addr + (voodoo->blt.dst_y >> 1) * voodoo->blt.dst_stride;
        dst  = (uint16_t *) &voodoo->fb_mem[addr];
    } else {
        addr = base_addr + voodoo->blt.dst_y * voodoo->blt.dst_stride;
        dst  = (uint16_t *) &voodoo->fb_mem[addr];
    }

    if (addr >= voodoo->front_offset && voodoo->row_width) {
        int y = (addr - voodoo->front_offset) / voodoo->row_width;
        if (y < voodoo->v_disp)
            voodoo->dirty_line[y] = 2;
    }

    while (src_bits && voodoo->blt.cur_x <= voodoo->blt.size_x) {
        int      r       = 0;
        int      g       = 0;
        int      b       = 0;
        uint16_t src_dat = 0;
        int      x       = (voodoo->blt.x_dir > 0) ? (voodoo->blt.dst_x + voodoo->blt.cur_x) : (voodoo->blt.dst_x - voodoo->blt.cur_x);

        switch (voodoo->bltCommand & BLIT_SRC_FORMAT) {
            case BLIT_SRC_1BPP:
            case BLIT_SRC_1BPP_BYTE_PACKED:
                src_dat = (data & 1) ? voodoo->bltColorFg : voodoo->bltColorBg;
                data >>= 1;
                src_bits--;
                break;
            case BLIT_SRC_16BPP:
                switch (voodoo->bltCommand & BLIT_SRC_RGB_FORMAT) {
                    case BLIT_SRC_RGB_ARGB:
                    case BLIT_SRC_RGB_RGBA:
                        src_dat = data & 0xffff;
                        break;
                    case BLIT_SRC_RGB_ABGR:
                    case BLIT_SRC_RGB_BGRA:
                        src_dat = ((data & 0xf800) >> 11) | (data & 0x07c0) | ((data & 0x0038) << 11);
                        break;

                    default:
                        break;
                }
                data >>= 16;
                src_bits -= 16;
                break;
            case BLIT_SRC_24BPP:
            case BLIT_SRC_24BPP_DITHER_2X2:
            case BLIT_SRC_24BPP_DITHER_4X4:
                switch (voodoo->bltCommand & BLIT_SRC_RGB_FORMAT) {
                    case BLIT_SRC_RGB_ARGB:
                        r = (data >> 16) & 0xff;
                        g = (data >> 8) & 0xff;
                        b = data & 0xff;
                        break;
                    case BLIT_SRC_RGB_ABGR:
                        r = data & 0xff;
                        g = (data >> 8) & 0xff;
                        b = (data >> 16) & 0xff;
                        break;
                    case BLIT_SRC_RGB_RGBA:
                        r = (data >> 24) & 0xff;
                        g = (data >> 16) & 0xff;
                        b = (data >> 8) & 0xff;
                        break;
                    case BLIT_SRC_RGB_BGRA:
                        r = (data >> 8) & 0xff;
                        g = (data >> 16) & 0xff;
                        b = (data >> 24) & 0xff;
                        break;

                    default:
                        break;
                }
                switch (voodoo->bltCommand & BLIT_SRC_FORMAT) {
                    case BLIT_SRC_24BPP:
                        src_dat = (b >> 3) | ((g & 0xfc) << 3) | ((r & 0xf8) << 8);
                        break;
                    case BLIT_SRC_24BPP_DITHER_2X2:
                        r       = dither_rb2x2[r][voodoo->blt.dst_y & 1][x & 1];
                        g       = dither_g2x2[g][voodoo->blt.dst_y & 1][x & 1];
                        b       = dither_rb2x2[b][voodoo->blt.dst_y & 1][x & 1];
                        src_dat = (b >> 3) | ((g & 0xfc) << 3) | ((r & 0xf8) << 8);
                        break;
                    case BLIT_SRC_24BPP_DITHER_4X4:
                        r       = dither_rb[r][voodoo->blt.dst_y & 3][x & 3];
                        g       = dither_g[g][voodoo->blt.dst_y & 3][x & 3];
                        b       = dither_rb[b][voodoo->blt.dst_y & 3][x & 3];
                        src_dat = (b >> 3) | ((g & 0xfc) << 3) | ((r & 0xf8) << 8);
                        break;

                    default:
                        break;
                }
                src_bits = 0;
                break;

            default:
                break;
        }

        if (SLI_ENABLED) {
            if ((!(voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && (voodoo->blt.dst_y & 1)) || ((voodoo->initEnable & INITENABLE_SLI_MASTER_SLAVE) && !(voodoo->blt.dst_y & 1)))
                goto skip_pixel;
        }

        if (voodoo->bltCommand & BLIT_CLIPPING_ENABLED) {
            if (x < voodoo->bltClipLeft || x >= voodoo->bltClipRight || voodoo->blt.dst_y < voodoo->bltClipLowY || voodoo->blt.dst_y >= voodoo->bltClipHighY)
                goto skip_pixel;
        }

        voodoo_v2_px(voodoo, &dst[x], src_dat, 1); /* KairoX86#277 */

skip_pixel:
        voodoo->blt.cur_x++;
    }

    if (voodoo->blt.cur_x > voodoo->blt.size_x) {
        voodoo->blt.size_y--;
        if (voodoo->blt.size_y >= 0) {
            voodoo->blt.cur_x = 0;
            voodoo->blt.dst_y += voodoo->blt.y_dir;
        }
    }
}

void
voodoo_fastfill(voodoo_t *voodoo, voodoo_params_t *params)
{
    int y;
    int low_y;
    int high_y;

    if (params->fbzMode & (1 << 17)) {
        int y_origin = (voodoo->type >= VOODOO_BANSHEE) ? (voodoo->y_origin_swap + 1) : voodoo->v_disp;

        high_y = y_origin - params->clipLowY;
        low_y  = y_origin - params->clipHighY;
    } else {
        low_y  = params->clipLowY;
        high_y = params->clipHighY;
    }

    if (params->fbzMode & FBZ_RGB_WMASK) {
        int      r;
        int      g;
        int      b;
        uint16_t col;

        r   = ((params->color1 >> 16) >> 3) & 0x1f;
        g   = ((params->color1 >> 8) >> 2) & 0x3f;
        b   = (params->color1 >> 3) & 0x1f;
        col = b | (g << 5) | (r << 11);

        if (SLI_ENABLED) {
            for (y = low_y; y < high_y; y += 2) {
                uint16_t *cbuf = (uint16_t *) &voodoo->fb_mem[(params->draw_offset + (y >> 1) * voodoo->row_width) & voodoo->fb_mask];

                for (int x = params->clipLeft; x < params->clipRight; x++)
                    cbuf[x] = col;
            }
        } else {
            for (y = low_y; y < high_y; y++) {
                if (voodoo->col_tiled) {
                    uint16_t *cbuf = (uint16_t *) &voodoo->fb_mem[(params->draw_offset + (y >> 5) * voodoo->row_width + (y & 31) * 128) & voodoo->fb_mask];

                    for (int x = params->clipLeft; x < params->clipRight; x++) {
                        int x2   = (x & 63) | ((x >> 6) * 128 * 32 / 2);
                        cbuf[x2] = col;
                    }
                } else {
                    uint16_t *cbuf = (uint16_t *) &voodoo->fb_mem[(params->draw_offset + y * voodoo->row_width) & voodoo->fb_mask];

                    for (int x = params->clipLeft; x < params->clipRight; x++)
                        cbuf[x] = col;
                }
                /* Mark line dirty for single buffer mode */
                if (params->draw_offset == params->front_offset && y < 2048)
                    voodoo->dirty_line[y] = 1;
                /* KairoX86#287: the row's pages on the desktop */
                if (params->clipRight > params->clipLeft)
                    voodoo_mark_changed(voodoo, params->draw_offset + (voodoo->col_tiled ? ((y >> 5) * voodoo->row_width + (y & 31) * 128) : (y * voodoo->row_width)),
                                        voodoo->col_tiled, params->clipLeft, params->clipRight - 1);
            }
        }
    }
    if (params->fbzMode & FBZ_DEPTH_WMASK) {
        if (SLI_ENABLED) {
            for (y = low_y; y < high_y; y += 2) {
                uint16_t *abuf = (uint16_t *) &voodoo->fb_mem[(params->aux_offset + (y >> 1) * voodoo->row_width) & voodoo->fb_mask];

                for (int x = params->clipLeft; x < params->clipRight; x++)
                    abuf[x] = params->zaColor & 0xffff;
            }
        } else {
            for (y = low_y; y < high_y; y++) {
                if (voodoo->aux_tiled) {
                    uint16_t *abuf = (uint16_t *) &voodoo->fb_mem[(params->aux_offset + (y >> 5) * voodoo->aux_row_width + (y & 31) * 128) & voodoo->fb_mask];

                    for (int x = params->clipLeft; x < params->clipRight; x++) {
                        int x2   = (x & 63) | ((x >> 6) * 128 * 32 / 2);
                        abuf[x2] = params->zaColor & 0xffff;
                    }
                } else {
                    uint16_t *abuf = (uint16_t *) &voodoo->fb_mem[(params->aux_offset + y * voodoo->aux_row_width) & voodoo->fb_mask];

                    for (int x = params->clipLeft; x < params->clipRight; x++)
                        abuf[x] = params->zaColor & 0xffff;
                }
            }
        }
    }
}
