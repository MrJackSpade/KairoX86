/*
 * The drawing engines' kernels' shared part (KairoX86#232; 86box/kairo_gpu_seg.h, core/kairo/gpu_seg.c): the batch's
 * buffers, video memory's access, and main(), which hands each invocation's pixels to the card's
 *     void card_pixels(uint seg, uint op, uint row, uint first, int i0, int i1);
 * pixels i0 to i1 - 1 of the segment seg (the card's pixel numbers first + i), in order.
 *
 * In parallel a work group is one listed block of video memory (256 bytes) and an invocation one word of it: it
 * draws, of every segment listed for its block in recorded order, the pixels that lie in its word. In order,
 * invocation 0 draws every segment whole, in recorded order.
 *
 * A card's pixels must not cross a word (a pixel's bits aligned to its size, 32 at most); an operation whose pixels
 * do runs in order.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
layout(local_size_x = 64) in;

layout(std430, binding = 0) readonly buffer Ops { uint ops[]; };
layout(std430, binding = 1) readonly buffer Segs { uint segs[]; };
layout(std430, binding = 2) readonly buffer Lists { uint lists[]; };
layout(std430, binding = 3) readonly buffer Stream { uint stream[]; };
layout(std430, binding = 4) buffer Vram { uint vram[]; };

layout(push_constant) uniform Push {
    uint n_segs;
    uint vram_mask;
    uint in_order;
    uint n_blocks;
    uint entries; /* where the block entries start in lists */
} pc;

const uint KG_OP = 0u, KG_ROW = 1u, KG_FIRST = 2u, KG_COUNT = 3u, KG_BIT = 4u, KG_BITS = 5u, KG_DIR = 6u, KG_WORDS = 8u;

/* ---- video memory, little endian, wrapping at its end ---- */

uint rd8(uint addr)
{
    uint a = addr & pc.vram_mask;
    return (vram[a >> 2] >> ((a & 3u) * 8u)) & 0xffu;
}

uint rd16(uint addr)
{
    uint a = addr & pc.vram_mask;
    if ((a & 3u) <= 2u)
        return (vram[a >> 2] >> ((a & 3u) * 8u)) & 0xffffu;
    return rd8(a) | (rd8(a + 1u) << 8);
}

uint rd32(uint addr)
{
    uint a = addr & pc.vram_mask;
    if ((a & 3u) == 0u)
        return vram[a >> 2];
    return rd8(a) | (rd8(a + 1u) << 8) | (rd8(a + 2u) << 16) | (rd8(a + 3u) << 24);
}

void wr8(uint addr, uint v)
{
    uint a     = addr & pc.vram_mask;
    uint shift = (a & 3u) * 8u;
    vram[a >> 2] = (vram[a >> 2] & ~(0xffu << shift)) | ((v & 0xffu) << shift);
}

void wr16(uint addr, uint v)
{
    uint a = addr & pc.vram_mask;
    if ((a & 1u) == 0u) {
        uint shift   = (a & 3u) * 8u;
        vram[a >> 2] = (vram[a >> 2] & ~(0xffffu << shift)) | ((v & 0xffffu) << shift);
        return;
    }
    wr8(a, v);
    wr8(a + 1u, v >> 8);
}

void wr32(uint addr, uint v)
{
    uint a = addr & pc.vram_mask;
    if ((a & 3u) == 0u) {
        vram[a >> 2] = v;
        return;
    }
    wr8(a, v);
    wr8(a + 1u, v >> 8);
    wr8(a + 2u, v >> 16);
    wr8(a + 3u, v >> 24);
}

void card_pixels(uint seg, uint op, uint row, uint first, int i0, int i1);

void seg_draw(uint s, int i0, int i1)
{
    uint g = s * KG_WORDS;
    card_pixels(s, segs[g + KG_OP], segs[g + KG_ROW], segs[g + KG_FIRST], i0, i1);
}

void main()
{
    if (pc.in_order != 0u) {
        if (gl_GlobalInvocationID.x != 0u)
            return;
        for (uint s = 0u; s < pc.n_segs; s++)
            seg_draw(s, 0, int(segs[s * KG_WORDS + KG_COUNT]));
        return;
    }
    uint k = gl_WorkGroupID.x;
    if (k >= pc.n_blocks)
        return;
    uint block = lists[k * 3u];
    uint start = lists[k * 3u + 1u];
    uint n     = lists[k * 3u + 2u];
    int  wlo   = int((block * 64u + gl_LocalInvocationID.x) * 32u);
    int  whi   = wlo + 32;
    for (uint j = 0u; j < n; j++) {
        uint s     = lists[pc.entries + start + j];
        uint g     = s * KG_WORDS;
        int  count = int(segs[g + KG_COUNT]);
        int  bits  = int(segs[g + KG_BITS]);
        int  bit   = int(segs[g + KG_BIT]) & int((pc.vram_mask << 3) | 7u);
        int  i0, i1;
        if (int(segs[g + KG_DIR]) > 0) {
            /* pixel i at [bit + i * bits, + bits) */
            i0 = (wlo > bit) ? (wlo - bit) / bits : 0;
            i1 = (whi > bit) ? (whi - bit + bits - 1) / bits : 0;
        } else {
            /* pixel i at [bit - i * bits, + bits) */
            i0 = (bit >= whi) ? (bit - whi) / bits + 1 : 0;
            i1 = (bit + bits > wlo) ? (bit + bits - wlo + bits - 1) / bits : 0;
        }
        i1 = min(i1, count);
        if (i0 < i1)
            seg_draw(s, i0, i1);
    }
}
