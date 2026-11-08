/*
 * Drawing engines' operations on the GPU, batched by video memory (core/kairo/gpu_seg.c, core/kairo/shaders/seg.glsl;
 * KairoX86#232): a card's engine records each operation (a record of the card's own layout) and the rows it draws,
 * each a run of pixels in video memory (a segment), instead of drawing them; the batch is drawn by the card's kernel
 * wherever the processor, the display or another engine is about to read or write video memory it draws on or reads.
 *
 * In parallel, an invocation owns one 32-bit word of video memory and draws every pixel any segment has in that word,
 * in the order the segments were recorded, so operations overlapping in memory land as the CPU draws them. An
 * operation that reads memory the batch draws on draws the batch first; one that reads memory it draws on itself,
 * or whose pixels depend on the ones before them, runs in order: one invocation draws the batch's segments pixel by
 * pixel as the CPU would.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_SEG_H
#define KAIRO_GPU_SEG_H

#include <stdbool.h>
#include <stdint.h>

/* A segment, as words (the kernel's view): its operation, its row, the first and count of its pixels (the card's
   pixel numbers along the row), the bit address of its first pixel, the bits a pixel takes, the direction (1 or
   -1) its pixels go in memory */
enum { KG_OP = 0, KG_ROW = 1, KG_FIRST = 2, KG_COUNT = 3, KG_BIT = 4, KG_BITS = 5, KG_DIR = 6, KG_WORDS = 8 };

typedef struct kairo_seg kairo_seg_t;

/* A card's batch: its kernel (SPIR-V of a shader including seg.glsl), its operation records' words, its video
   memory (shared with the GPU, kairo_gpu_alloc), and the display's changed pages (a byte per 4K, set to *stamp for
   every page a recorded segment draws on, as the CPU's writes set them; NULL for a card whose display keeps no such
   map, the 3dfx Voodoo Graphics and Voodoo2's) */
kairo_seg_t *kairo_seg_open(const char *name, const uint32_t *spirv, size_t spirv_bytes, uint8_t *vram, uint32_t vram_mask,
                            uint32_t op_words, uint8_t *changed, const int *stamp);
void         kairo_seg_close(kairo_seg_t *s);

/* Memory the next operation reads (len bytes at addr): a batch that draws there is drawn first; if the operation
   itself draws there too, it must run in order (say so to kairo_seg_op) */
bool kairo_seg_reads_pending(kairo_seg_t *s, uint32_t addr, uint32_t len);
void kairo_seg_reads(kairo_seg_t *s, uint32_t addr, uint32_t len);
/* Memory the next operation draws on: a parallel batch with an operation reading there is drawn first */
void kairo_seg_draws(kairo_seg_t *s, uint32_t addr, uint32_t len);
/* A card that goes on adding to an operation already in the batch, its segments unbounded, calls this first: a full
   batch is drawn (its generation changes, so the card starts the operation again) */
void kairo_seg_make_room(kairo_seg_t *s);
/* Starts an operation: the words of its record to fill (op_words), valid until the next call. A batch of the other
   way (parallel, in order), or a full one, is drawn first. */
uint32_t *kairo_seg_op(kairo_seg_t *s, bool in_order);
/* A segment of the operation started last */
void kairo_seg_add(kairo_seg_t *s, uint32_t row, uint32_t first, uint32_t count, uint32_t bit, uint32_t bits, int dir);
/* Words the operations read beside video memory (host data, patterns), appended to the batch's stream: where
   they start in it */
uint32_t kairo_seg_stream(kairo_seg_t *s, const uint32_t *words, uint32_t count);

/* A card's own work in progress (a row partly drawn) recorded before every drain, so a drain draws everything the
   card has done: fn(ctx) is called first, outside the batch's lock. open(ctx, addr, len), if not NULL, says whether
   that work draws or reads any of len bytes at addr: kairo_seg_touch there records it first. close(ctx), if not
   NULL, makes ctx the batch's: kairo_seg_close calls it after the batch's last drain, so nothing flushes ctx once it
   is closed. A batch takes up to KAIRO_SEG_FLUSHES of them (a card's runs each add one). */
#define KAIRO_SEG_FLUSHES 8
void kairo_seg_add_flush(kairo_seg_t *s, void (*fn)(void *ctx), bool (*open)(void *ctx, uint32_t addr, uint32_t len),
                         void (*close)(void *ctx), void *ctx);
/* How many times the batch has been drawn: a card's operation started before a drain is not in the batch after it */
uint64_t kairo_seg_generation(const kairo_seg_t *s);

/* Draws every recorded segment */
void kairo_seg_drain(kairo_seg_t *s);
/* The processor, the display or another engine reads or writes len bytes at addr: draws first if a segment draws
   there, or an operation reads there */
void kairo_seg_touch(kairo_seg_t *s, uint32_t addr, uint32_t len);

/* Runs of pixels (core/kairo/gpu_seg_run.c), for an engine whose walk stays the CPU's and whose every pixel
   (pixel_bytes, 1 to 4) carries its own inputs: the pixels drawn one after the other along memory go in as one segment
   (its row the place of its pixels' words in the stream, words_per each), and the memory each pixel reads (up to
   KAIRO_SEG_RUN_READS slots of a pixel's bytes, KAIRO_SEG_RUN_NONE for none) decides how: in order where the run
   reads what it draws or its pixels cross a word, and the batch drawn first where the run reads what the batch draws
   or draws what it reads. op(ctx, in_order) puts the card's operation
   record in the batch (kairo_seg_op) before the run's segment. Each run is one of the batch's flushes (kairo_seg_add_flush),
   and the batch's: kairo_seg_close draws it and frees it (KairoX86#329). */
#define KAIRO_SEG_RUN_READS 4
#define KAIRO_SEG_RUN_NONE  0xffffffffu
typedef struct kairo_seg_run kairo_seg_run_t;
kairo_seg_run_t *kairo_seg_run_open(kairo_seg_t *seg, uint32_t vram_mask, uint32_t pixel_bytes, uint32_t words_per,
                                    uint32_t reads, void (*op)(void *ctx, bool in_order), void *ctx);
/* A pixel drawn at addr: its words and where the pixels it reads lie, one per slot */
void kairo_seg_run_pixel(kairo_seg_run_t *r, uint32_t addr, const uint32_t *words, const uint32_t *reads);
/* The run so far into the batch */
void kairo_seg_run_flush(kairo_seg_run_t *r);

#endif
