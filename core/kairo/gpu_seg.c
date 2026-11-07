/*
 * Drawing engines' operations on the GPU, batched by video memory (86box/kairo_gpu_seg.h; KairoX86#232): a card's
 * recorded operations and segments, the memory they draw on and read (page maps), the per-block lists the parallel
 * kernel walks, and the drain through the card's kernel (shaders/seg.glsl and the card's pixels).
 *
 * Video memory is cut into blocks of 256 bytes, a work group of the kernel each (64 invocations, a word each). A
 * drain lists, for each block any segment draws on, the segments that do, in the order they were recorded.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <pthread.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <86box/86box.h>
#include <86box/kairo_gpu.h>
#include <86box/kairo_gpu_seg.h>

#define OPS_MAX     16384
#define SEGS_MAX    262144
#define STREAM_MAX  (1u << 20)
#define BLOCK_SHIFT 8
/* Room left for an operation's rows, every operation's rows being fewer than a card's 32K lines (and their entries,
   each a block a row meets) */
#define SEGS_ROOM    65536
#define ENTRIES_MAX  (SEGS_MAX * 8)
#define ENTRIES_ROOM (ENTRIES_MAX / 2)

struct kairo_seg {
    pthread_mutex_t     lock;
    const char         *name;
    kairo_gpu_kernel_t *kernel;
    const uint32_t     *spirv;
    size_t              spirv_bytes;
    kairo_gpu_buffer_t *ops, *segs, *lists, *stream, *vram;
    uint32_t            vram_mask, op_words;
    uint32_t            n_ops, n_segs, n_stream, n_entries;
    bool                in_order;
    int32_t            *block_slot; /* each block's place in the drain's list, -1 none */
    uint32_t           *block_ids;  /* the blocks listed */
    uint32_t           *block_count;
    kairo_gpu_pages_t   writes, reads, touched;
    uint8_t            *changed;
    const int          *stamp;
    unsigned long long  drawn;
    void              (*flush)(void *ctx);
    void               *flush_ctx;
    uint64_t            generation;
};

kairo_seg_t *
kairo_seg_open(const char *name, const uint32_t *spirv, size_t spirv_bytes, uint8_t *vram, uint32_t vram_mask, uint32_t op_words,
               uint8_t *changed, const int *stamp)
{
    kairo_seg_t *s = calloc(1, sizeof(kairo_seg_t));
    if (s == NULL)
        fatal("%s on the GPU: no memory\n", name);
    pthread_mutex_init(&s->lock, NULL);
    s->name        = name;
    s->spirv       = spirv;
    s->spirv_bytes = spirv_bytes;
    s->vram_mask   = vram_mask;
    s->op_words    = op_words;
    s->changed     = changed;
    s->stamp       = stamp;
    s->ops         = kairo_gpu_buffer((size_t) OPS_MAX * op_words * 4);
    s->segs        = kairo_gpu_buffer((size_t) SEGS_MAX * KG_WORDS * 4);
    s->stream      = kairo_gpu_buffer((size_t) STREAM_MAX * 4);
    s->vram        = kairo_gpu_buffer_of(vram);
    const uint32_t blocks = (vram_mask >> BLOCK_SHIFT) + 1;
    /* The lists: three words a listed block (its id, its first entry, its entries), then the entries; a segment
       spans at most a few blocks of a row, so the entries are bounded by the segments' blocks */
    s->lists       = kairo_gpu_buffer(((size_t) blocks * 3 + (size_t) ENTRIES_MAX) * 4);
    s->block_slot  = malloc((size_t) blocks * sizeof(int32_t));
    s->block_ids   = malloc((size_t) blocks * sizeof(uint32_t));
    s->block_count = malloc((size_t) blocks * sizeof(uint32_t));
    if ((s->block_slot == NULL) || (s->block_ids == NULL) || (s->block_count == NULL))
        fatal("%s on the GPU: no memory\n", name);
    memset(s->block_slot, -1, (size_t) blocks * sizeof(int32_t));
    kairo_gpu_pages_init(&s->writes, vram_mask);
    kairo_gpu_pages_init(&s->reads, vram_mask);
    kairo_gpu_pages_init(&s->touched, vram_mask);
    return s;
}

/* A segment's bytes: its first, and one past its last */
static void
seg_bytes(const uint32_t *g, uint32_t *lo, uint32_t *hi)
{
    const uint32_t count = g[KG_COUNT], bits = g[KG_BITS], bit = g[KG_BIT];
    const uint32_t first = ((int32_t) g[KG_DIR] > 0) ? bit : bit - (count - 1) * bits;
    *lo = first >> 3;
    *hi = (first + count * bits + 7) >> 3;
}

static void
drain_locked(kairo_seg_t *s)
{
    if (s->n_ops == 0)
        return;
    if (s->kernel == NULL)
        s->kernel = kairo_gpu_kernel(s->name, s->spirv, s->spirv_bytes, 5, 8 * 4);

    uint32_t       n_blocks = 0;
    uint32_t      *lists    = s->lists->data;
    const uint32_t *segs    = s->segs->data;
    if (!s->in_order) {
        /* Each block's segments: counted, placed, then filled in order */
        for (uint32_t i = 0; i < s->n_segs; i++) {
            uint32_t lo, hi;
            seg_bytes(&segs[i * KG_WORDS], &lo, &hi);
            for (uint32_t b = lo >> BLOCK_SHIFT; b <= ((hi - 1) >> BLOCK_SHIFT); b++) {
                const uint32_t id = b & (s->vram_mask >> BLOCK_SHIFT);
                if (s->block_slot[id] < 0) {
                    s->block_slot[id]       = (int32_t) n_blocks;
                    s->block_ids[n_blocks]  = id;
                    s->block_count[n_blocks] = 0;
                    n_blocks++;
                }
                s->block_count[s->block_slot[id]]++;
            }
        }
        uint32_t entry = 0;
        for (uint32_t k = 0; k < n_blocks; k++) {
            lists[k * 3]     = s->block_ids[k];
            lists[k * 3 + 1] = entry;
            lists[k * 3 + 2] = 0;
            entry += s->block_count[k];
        }
        if (entry > ENTRIES_MAX)
            fatal("%s on the GPU: %u block entries\n", s->name, entry);
        uint32_t *entries = lists + n_blocks * 3;
        for (uint32_t i = 0; i < s->n_segs; i++) {
            uint32_t lo, hi;
            seg_bytes(&segs[i * KG_WORDS], &lo, &hi);
            for (uint32_t b = lo >> BLOCK_SHIFT; b <= ((hi - 1) >> BLOCK_SHIFT); b++) {
                const uint32_t k = (uint32_t) s->block_slot[b & (s->vram_mask >> BLOCK_SHIFT)];
                entries[lists[k * 3 + 1] + lists[k * 3 + 2]++] = i;
            }
        }
        for (uint32_t k = 0; k < n_blocks; k++)
            s->block_slot[s->block_ids[k]] = -1;
    }

    const uint32_t push[8] = { s->n_segs, s->vram_mask, s->in_order ? 1u : 0u, n_blocks, n_blocks * 3, 0, 0, 0 };
    kairo_gpu_buffer_t *const buffers[5] = { s->ops, s->segs, s->lists, s->stream, s->vram };
    kairo_gpu_run(s->kernel, buffers, push, s->in_order ? 1 : (n_blocks ? n_blocks : 1), 1, 1);

    s->drawn += s->n_ops;
    __atomic_add_fetch(&s->generation, 1, __ATOMIC_RELEASE);
    s->n_ops    = 0;
    s->n_segs   = 0;
    s->n_stream = 0;
    s->n_entries = 0;
    kairo_gpu_pages_clear(&s->writes);
    kairo_gpu_pages_clear(&s->reads);
    kairo_gpu_pages_clear(&s->touched);
}

void
kairo_seg_set_flush(kairo_seg_t *s, void (*fn)(void *ctx), void *ctx)
{
    s->flush     = fn;
    s->flush_ctx = ctx;
}

uint64_t
kairo_seg_generation(const kairo_seg_t *s)
{
    return __atomic_load_n(&s->generation, __ATOMIC_ACQUIRE);
}

void
kairo_seg_drain(kairo_seg_t *s)
{
    if (s->flush != NULL)
        s->flush(s->flush_ctx);
    if (!kairo_gpu_pages_any(&s->touched) && (s->n_ops == 0))
        return;
    pthread_mutex_lock(&s->lock);
    drain_locked(s);
    pthread_mutex_unlock(&s->lock);
}

void
kairo_seg_touch(kairo_seg_t *s, uint32_t addr, uint32_t len)
{
    if (kairo_gpu_pages_hit(&s->touched, addr & s->vram_mask, len))
        kairo_seg_drain(s);
}

bool
kairo_seg_reads_pending(kairo_seg_t *s, uint32_t addr, uint32_t len)
{
    return kairo_gpu_pages_hit(&s->writes, addr & s->vram_mask, len);
}

void
kairo_seg_reads(kairo_seg_t *s, uint32_t addr, uint32_t len)
{
    pthread_mutex_lock(&s->lock);
    kairo_gpu_pages_mark(&s->reads, addr & s->vram_mask, len);
    kairo_gpu_pages_mark(&s->touched, addr & s->vram_mask, len);
    pthread_mutex_unlock(&s->lock);
}

void
kairo_seg_draws(kairo_seg_t *s, uint32_t addr, uint32_t len)
{
    /* In parallel a block's invocations read other blocks while those draw: what an operation reads must not change
       under it. In order every pixel is drawn in turn. */
    if (!s->in_order && kairo_gpu_pages_hit(&s->reads, addr & s->vram_mask, len))
        kairo_seg_drain(s);
}

static bool
no_room(const kairo_seg_t *s)
{
    return (s->n_ops != 0) && ((s->n_ops == OPS_MAX) || (s->n_segs + SEGS_ROOM > SEGS_MAX) || (s->n_entries > ENTRIES_ROOM)
                               || (s->n_stream > STREAM_MAX / 2));
}

void
kairo_seg_make_room(kairo_seg_t *s)
{
    pthread_mutex_lock(&s->lock);
    if (no_room(s))
        drain_locked(s);
    pthread_mutex_unlock(&s->lock);
}

uint32_t *
kairo_seg_op(kairo_seg_t *s, bool in_order)
{
    pthread_mutex_lock(&s->lock);
    if ((s->n_ops != 0) && ((s->in_order != in_order) || no_room(s)))
        drain_locked(s);
    s->in_order   = in_order;
    uint32_t *op = (uint32_t *) s->ops->data + (size_t) s->n_ops * s->op_words;
    memset(op, 0, s->op_words * 4);
    s->n_ops++;
    pthread_mutex_unlock(&s->lock);
    return op;
}

void
kairo_seg_add(kairo_seg_t *s, uint32_t row, uint32_t first, uint32_t count, uint32_t bit, uint32_t bits, int dir)
{
    if (count == 0)
        return;
    pthread_mutex_lock(&s->lock);
    if (s->n_segs == SEGS_MAX)
        fatal("%s on the GPU: more than %u segments in an operation\n", s->name, SEGS_MAX);
    uint32_t *g = (uint32_t *) s->segs->data + (size_t) s->n_segs * KG_WORDS;
    g[KG_OP]    = s->n_ops - 1;
    g[KG_ROW]   = row;
    g[KG_FIRST] = first;
    g[KG_COUNT] = count;
    g[KG_BIT]   = bit;
    g[KG_BITS]  = bits;
    g[KG_DIR]   = (uint32_t) dir;
    g[KG_DIR + 1] = 0;
    s->n_segs++;
    uint32_t lo, hi;
    seg_bytes(g, &lo, &hi);
    /* In parallel a block's words are video memory's own: a segment running past its end must run in order */
    if (!s->in_order && (hi > s->vram_mask + 1))
        fatal("%s on the GPU: a segment past the end of video memory in a parallel operation\n", s->name);
    s->n_entries += ((hi - 1) >> BLOCK_SHIFT) - (lo >> BLOCK_SHIFT) + 1;
    kairo_gpu_pages_mark(&s->writes, lo & s->vram_mask, hi - lo);
    kairo_gpu_pages_mark(&s->touched, lo & s->vram_mask, hi - lo);
    pthread_mutex_unlock(&s->lock);
    /* The display redraws the lines it shows from these pages (the CPU's writes mark them as they go) */
    const uint8_t stamp = (uint8_t) *s->stamp;
    for (uint32_t pg = lo >> 12; pg <= ((hi - 1) >> 12); pg++)
        s->changed[(pg << 12 & s->vram_mask) >> 12] = stamp;
}

uint32_t
kairo_seg_stream(kairo_seg_t *s, const uint32_t *words, uint32_t count)
{
    pthread_mutex_lock(&s->lock);
    if (s->n_stream + count > STREAM_MAX)
        fatal("%s on the GPU: more than %u stream words in a batch\n", s->name, STREAM_MAX);
    const uint32_t at = s->n_stream;
    if (count != 0)
        memcpy((uint32_t *) s->stream->data + at, words, (size_t) count * 4);
    s->n_stream += count;
    pthread_mutex_unlock(&s->lock);
    return at;
}

void
kairo_seg_close(kairo_seg_t *s)
{
    if (s == NULL)
        return;
    kairo_seg_drain(s);
    fprintf(stderr, "kairo-gpu-%s: %llu operations drawn\n", s->name, s->drawn);
    kairo_gpu_kernel_free(s->kernel);
    kairo_gpu_buffer_free(s->ops);
    kairo_gpu_buffer_free(s->segs);
    kairo_gpu_buffer_free(s->lists);
    kairo_gpu_buffer_free(s->stream);
    kairo_gpu_pages_free(&s->writes);
    kairo_gpu_pages_free(&s->reads);
    kairo_gpu_pages_free(&s->touched);
    free(s->block_slot);
    free(s->block_ids);
    free(s->block_count);
    pthread_mutex_destroy(&s->lock);
    free(s);
}
