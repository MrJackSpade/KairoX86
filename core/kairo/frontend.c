/*
 * KairoX86: 86Box's frontend inside the kairox86_86box library (kairo_x86.h). It replaces the
 * headless program (src/unix/headless_main.c) and its null audio: it starts 86Box on a machine
 * folder, runs it a frame at a time on the host's thread, keeps the last picture, mixes the sound
 * streams to one, and takes the host's keyboard, mouse and joysticks.
 *
 * Copyright 2026 MrJackSpade.
 *
 * This program is free software; you can redistribute it and/or modify it under the terms of the
 * GNU General Public License as published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 */
#include <pthread.h>
#include <setjmp.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#include <86box/86box.h>
#include <86box/keyboard.h>
#include <86box/mouse.h>
#include <86box/plat.h>
#include <86box/plat_unused.h>
#include <86box/thread.h>
#include <86box/timer.h>
#include <86box/nvr.h>
#include <86box/version.h>
#include <86box/video.h>
#include <86box/ui.h>
#include <86box/sound.h>
#include <86box/gameport.h>
#include <86box/random.h>
#include <86box/fdd.h>
#include <86box/cdrom.h>
#include <86box/mem.h>
#include "cpu.h"

#ifdef _WIN32
#    include <process.h>
#endif

#include "kairo_x86.h"
#include "hardware.h"

/* ---- Globals the 86Box frontends define ---- */

int  rctrl_is_lalt;
int  update_icons;
int  kbd_req_capture;
int  hide_status_bar;
int  hide_tool_bar;
bool fast_forward = false;
int  fixed_size_x = 640;
int  fixed_size_y = 480;
int  title_set;
/* The player's pointer is the machine's for its whole run (KairoX86#50): 86Box's mice report only while
   the host holds it captured, as its own UI does after a click in the window. Kairo has no window to
   click and no host pointer to give back, so it is held from the start and never let go. */
int  mouse_capture = 1;

volatile int cpu_thread_run = 1;

plat_joystick_state_t plat_joystick_state[MAX_PLAT_JOYSTICKS];
joystick_state_t      joystick_state[GAMEPORT_MAX][MAX_JOYSTICKS];

/* ---- The machine run ---- */

static struct KairoX86Host host;
static pthread_t           host_thread;
static jmp_buf             stopped;   /* where do_stop() returns to on the host's thread */
static bool                running;   /* a call into 86Box is on the host's stack, with stopped set */
static atomic_bool         dead;      /* the machine stopped: nothing runs it again */
static bool                closed;    /* pc_close ended 86Box's threads */
static int                 frame_ms;  /* the guest time the last frame lasted */
static int                 nvr_ms;    /* guest time since the CMOS was last saved */
static int                 halted_ms; /* guest time the processor has sat on a HLT with interrupts off */
static bool                repeatable; /* a seeded run (start): its clock is the guest's own */
static int                 configured_time_sync; /* the machine's own time_sync, saved back as it was */

/* How long the processor must sit on a HLT with interrupts off before the machine counts as
   stopped: only an NMI or SMI can wake it, and a second rules out a short wait for either. */
#define HALT_STOP_MS 1000

static pthread_mutex_t blit_lock = PTHREAD_MUTEX_INITIALIZER;
static char            title[512] = EMU_NAME;

/* The last picture, copied from the video card's bitmap on 86Box's blit thread. */
static pthread_mutex_t picture_lock = PTHREAD_MUTEX_INITIALIZER;
static uint32_t       *picture;
static int             picture_alloc;
static int             picture_width;
static int             picture_height;

/* The joysticks the host gives, which joystick_process hands to the game port. */
static int input_axes[KAIRO_X86_JOYSTICK_AXES];
static int input_buttons[KAIRO_X86_JOYSTICK_BUTTONS];

static void
report(void (*to)(void *, const char *), const char *message)
{
    if (to != NULL)
        to(host.context, message);
}

/* The machine is over, for the reason given: the host ends the game with it (host->fatal keeps the
   first reason), and run_frame returns false from now on. */
static void
machine_over(const char *reason)
{
    report(host.fatal, reason);
    atomic_store(&dead, true);
}

/* ---- Sound: every stream resampled to OUTPUT_RATE and mixed ---- */

#define OUTPUT_RATE 48000
/* Stereo frames each stream's queue holds: two seconds, far more than a frame's worth. */
#define QUEUE_FRAMES (OUTPUT_RATE * 2)
#define STREAMS      16

typedef struct {
    int16_t queue[QUEUE_FRAMES * 2];
    int     read;
    int     count;
    double  phase;     /* the resampler's position between the last input frame and the next */
    int32_t last[2];   /* the last input frame, for interpolation */
    bool    primed;
} stream_t;

static pthread_mutex_t sound_lock = PTHREAD_MUTEX_INITIALIZER;
static stream_t        streams[STREAMS];

static void
stream_push(stream_t *s, int32_t l, int32_t r)
{
    if (s->count == QUEUE_FRAMES) {
        /* The host stopped taking sound: the oldest frame goes. */
        s->read = (s->read + 1) % QUEUE_FRAMES;
        s->count--;
    }
    int at = (s->read + s->count) % QUEUE_FRAMES;
    s->queue[at * 2]     = (int16_t) (l < -32768 ? -32768 : (l > 32767 ? 32767 : l));
    s->queue[at * 2 + 1] = (int16_t) (r < -32768 ? -32768 : (r > 32767 ? 32767 : r));
    s->count++;
}

/* A block of a stream (src) in interleaved stereo, size values (frames * 2), as 16-bit or float. */
void
givealbuffer_common(const void *buf, const uint8_t src, const int size)
{
    const int rate = sound_stream_rate(src);

    if ((src >= STREAMS) || (rate <= 0) || (size <= 0))
        return;
    pthread_mutex_lock(&sound_lock);
    stream_t    *s    = &streams[src];
    const double step = (double) rate / OUTPUT_RATE;
    for (int i = 0; i < size / 2; i++) {
        int32_t l;
        int32_t r;
        if (sound_is_float) {
            l = (int32_t) (((const float *) buf)[i * 2] * 32767.0f);
            r = (int32_t) (((const float *) buf)[i * 2 + 1] * 32767.0f);
        } else {
            l = ((const int16_t *) buf)[i * 2];
            r = ((const int16_t *) buf)[i * 2 + 1];
        }
        if (!s->primed) {
            s->last[0] = l;
            s->last[1] = r;
            s->primed  = true;
            continue;
        }
        /* Linear interpolation from the last input frame to this one, at the output rate. */
        while (s->phase < 1.0) {
            stream_push(s, (int32_t) (s->last[0] + (l - s->last[0]) * s->phase),
                        (int32_t) (s->last[1] + (r - s->last[1]) * s->phase));
            s->phase += step;
        }
        s->phase -= 1.0;
        s->last[0] = l;
        s->last[1] = r;
    }
    pthread_mutex_unlock(&sound_lock);
}

static uint32_t
api_read_audio(int16_t *stereo, uint32_t max_frames)
{
    pthread_mutex_lock(&sound_lock);
    /* The main stream (the sound cards and the speaker) sets how much there is; the others (CD
       audio, MIDI synthesis, drive noises) add what they have to it. */
    uint32_t frames = (uint32_t) streams[I_NORMAL].count;
    if (frames > max_frames)
        frames = max_frames;
    for (uint32_t f = 0; f < frames; f++) {
        int32_t mix[2] = { 0, 0 };
        for (int i = 0; i < STREAMS; i++) {
            stream_t *s = &streams[i];
            if (s->count == 0)
                continue;
            mix[0] += s->queue[s->read * 2];
            mix[1] += s->queue[s->read * 2 + 1];
            s->read = (s->read + 1) % QUEUE_FRAMES;
            s->count--;
        }
        stereo[f * 2]     = (int16_t) (mix[0] < -32768 ? -32768 : (mix[0] > 32767 ? 32767 : mix[0]));
        stereo[f * 2 + 1] = (int16_t) (mix[1] < -32768 ? -32768 : (mix[1] > 32767 ? 32767 : mix[1]));
    }
    pthread_mutex_unlock(&sound_lock);
    return frames;
}

static int
api_sample_rate(void)
{
    return OUTPUT_RATE;
}

/* The rest of 86Box's audio backend: no host devices, no capture. */
const char *sound_get_output_devices(void) { return NULL; }
const char *sound_get_input_devices(void) { return NULL; }
void al_capture_open(void) { }
void al_capture_close(void) { }
int  al_capture_get_rate(void) { return OUTPUT_RATE; }
int  sound_get_device_sample_rate(UNUSED(const char *device_name)) { return 0; }
int  sound_get_device_supported_rates(UNUSED(const char *device_name), UNUSED(int *rates_out), UNUSED(int max_rates)) { return 0; }
void closeal(void) { }
void inital(void) { }
int  al_capture_available(void) { return 0; }
void al_capture_start(void) { }
void al_capture_stop(void) { }
void al_capture_get_data(UNUSED(int16_t *buf), size_t *len) { *len = 0; }
void al_set_midi(UNUSED(const int freq), UNUSED(const int buf_size)) { }

/* ---- Memory the machine allocates (KairoX86#186) ---- */

/* The library's malloc, calloc, realloc and free (the linker's --wrap, core/CMakeLists.txt) record
   every block 86Box and this frontend allocate, until it is freed: what is left when the machine
   closes is freed then. A block the record does not hold (one the C library allocated itself, as
   strdup's) is the C library's to free. The record is an open-addressing table of block addresses. */
extern void *__real_malloc(size_t size);
extern void *__real_calloc(size_t count, size_t size);
extern void *__real_realloc(void *ptr, size_t size);
extern void  __real_free(void *ptr);

#define BLOCK_FREE ((void *) 0)
#define BLOCK_GONE ((void *) 1)
/* A lock that never allocates: winpthreads allocates a static mutex on its first lock, through malloc. */
static atomic_flag blocks_busy = ATOMIC_FLAG_INIT;

static void
blocks_lock(void)
{
    while (atomic_flag_test_and_set_explicit(&blocks_busy, memory_order_acquire))
        ;
}

static void
blocks_unlock(void)
{
    atomic_flag_clear_explicit(&blocks_busy, memory_order_release);
}
static void          **blocks;      /* the table: a block's address, BLOCK_FREE or BLOCK_GONE */
static size_t          block_slots; /* a power of two */
static size_t          block_count; /* addresses in the table */
static size_t          block_used;  /* addresses and BLOCK_GONE marks */

static size_t
block_slot(const void *at)
{
    uintptr_t key = (uintptr_t) at;
    key ^= key >> 33;
    key *= UINT64_C(0xff51afd7ed558ccd);
    key ^= key >> 33;
    return (size_t) key & (block_slots - 1);
}

static void block_add(void *at);

/* Room for one more address: a table at most half used, rebuilt without its BLOCK_GONE marks. */
static void
blocks_make_room(void)
{
    if (((block_used + 1) * 2) <= block_slots)
        return;
    void       **old   = blocks;
    const size_t slots = block_slots;
    block_slots = ((block_count + 1) * 4 > 1024) ? (size_t) 1 << (64 - __builtin_clzll((block_count + 1) * 4 - 1)) : 1024;
    blocks      = __real_calloc(block_slots, sizeof(void *));
    if (blocks == NULL)
        fatal("The PC stopped: no memory to record its memory\n");
    block_count = block_used = 0;
    for (size_t i = 0; i < slots; i++)
        if ((old[i] != BLOCK_FREE) && (old[i] != BLOCK_GONE))
            block_add(old[i]);
    __real_free(old);
}

static void
block_add(void *at)
{
    blocks_make_room();
    size_t slot = block_slot(at);
    while ((blocks[slot] != BLOCK_FREE) && (blocks[slot] != BLOCK_GONE))
        slot = (slot + 1) & (block_slots - 1);
    if (blocks[slot] == BLOCK_FREE)
        block_used++;
    blocks[slot] = at;
    block_count++;
}

/* Takes at out of the table: false when it was not there. */
static bool
block_remove(const void *at)
{
    if (block_slots == 0)
        return false;
    for (size_t slot = block_slot(at); blocks[slot] != BLOCK_FREE; slot = (slot + 1) & (block_slots - 1))
        if (blocks[slot] == at) {
            blocks[slot] = BLOCK_GONE;
            block_count--;
            return true;
        }
    return false;
}

void *
__wrap_malloc(size_t size)
{
    void *at = __real_malloc(size);
    if (at != NULL) {
        blocks_lock();
        block_add(at);
        blocks_unlock();
    }
    return at;
}

void *
__wrap_calloc(size_t count, size_t size)
{
    void *at = __real_calloc(count, size);
    if (at != NULL) {
        blocks_lock();
        block_add(at);
        blocks_unlock();
    }
    return at;
}

void *
__wrap_realloc(void *ptr, size_t size)
{
    if (ptr == NULL)
        return __wrap_malloc(size);
    blocks_lock();
    const bool ours = block_remove(ptr);
    blocks_unlock();
    void *at = __real_realloc(ptr, size);
    if (ours) {
        blocks_lock();
        /* A failed realloc leaves the block where it was. */
        block_add((at != NULL) ? at : ptr);
        blocks_unlock();
    }
    return at;
}

void
__wrap_free(void *ptr)
{
    if (ptr == NULL)
        return;
    blocks_lock();
    block_remove(ptr);
    blocks_unlock();
    __real_free(ptr);
}

/* After pc_close: every block 86Box left goes back. */
static void
release_blocks(void)
{
    blocks_lock();
    for (size_t i = 0; i < block_slots; i++)
        if ((blocks[i] != BLOCK_FREE) && (blocks[i] != BLOCK_GONE))
            __real_free(blocks[i]);
    __real_free(blocks);
    blocks      = NULL;
    block_slots = block_count = block_used = 0;
    blocks_unlock();
}

/* ---- Memory the machine maps (KairoX86#186) ---- */

/* 86Box's own mappings (the platform files' plat_mmap_os, kairox86-own-memory), each recorded until
   86Box unmaps it: what is left when the machine closes (the recompiler's pool and tables) is
   released then, so a closed machine gives its memory back. */
extern void *plat_mmap_os(size_t size, uint8_t executable, uint8_t *large);
extern void  plat_munmap_os(void *ptr, size_t size);

struct mapping {
    void  *at;
    size_t size;
};
static pthread_mutex_t mappings_lock = PTHREAD_MUTEX_INITIALIZER;
static struct mapping *mappings;
static int             mapping_count;
static int             mapping_room;

void *
plat_mmap(size_t size, uint8_t executable, uint8_t *large)
{
    void *at = plat_mmap_os(size, executable, large);

    if (at == NULL)
        return NULL;
    pthread_mutex_lock(&mappings_lock);
    if (mapping_count == mapping_room) {
        const int       room  = mapping_room ? (mapping_room * 2) : 16;
        struct mapping *grown = realloc(mappings, (size_t) room * sizeof(struct mapping));
        if (grown == NULL) {
            pthread_mutex_unlock(&mappings_lock);
            fatal("plat_mmap: no memory to record a mapping\n");
        }
        mappings     = grown;
        mapping_room = room;
    }
    mappings[mapping_count++] = (struct mapping) { at, size };
    pthread_mutex_unlock(&mappings_lock);
    return at;
}

void
plat_munmap(void *ptr, size_t size)
{
    pthread_mutex_lock(&mappings_lock);
    for (int i = 0; i < mapping_count; i++)
        if (mappings[i].at == ptr) {
            mappings[i] = mappings[--mapping_count];
            break;
        }
    pthread_mutex_unlock(&mappings_lock);
    plat_munmap_os(ptr, size);
}

/* After pc_close: every mapping 86Box left goes back. */
static void
release_mappings(void)
{
    pthread_mutex_lock(&mappings_lock);
    for (int i = 0; i < mapping_count; i++)
        plat_munmap_os(mappings[i].at, mappings[i].size);
    mapping_count = 0;
    free(mappings);
    mappings     = NULL;
    mapping_room = 0;
    pthread_mutex_unlock(&mappings_lock);
}

/* ---- Video ---- */

/* On 86Box's blit thread: the video card finished a frame in its bitmap. */
static void
blit(int x, int y, int w, int h, int monitor_index)
{
    const bitmap_t *target = monitors[monitor_index].target_buffer;

    if ((monitor_index == 0) && (target != NULL) && (x >= 0) && (y >= 0) && (x < target->w) && (y < target->h)) {
        if ((x + w) > target->w)
            w = target->w - x;
        if ((y + h) > target->h)
            h = target->h - y;
        /* The machine's own pixels (KairoX86#37): one of each pixel and line the card drew twice. */
        const int across = (monitors[monitor_index].mon_kairo_x_div > 1) ? monitors[monitor_index].mon_kairo_x_div : 1;
        const int down   = (monitors[monitor_index].mon_kairo_y_div > 1) ? monitors[monitor_index].mon_kairo_y_div : 1;
        w /= across;
        h /= down;
        pthread_mutex_lock(&picture_lock);
        bool room = true;
        if ((w * h) > picture_alloc) {
            uint32_t *grown = realloc(picture, (size_t) w * (size_t) h * sizeof(uint32_t));
            if (grown == NULL) {
                /* The last picture stays as it was; the machine ends with why. */
                room = false;
                machine_over("The PC stopped: no memory for its picture");
            } else {
                picture       = grown;
                picture_alloc = w * h;
            }
        }
        if (room) {
#ifdef KAIROX86_CHECK_NATIVE_SIZE
            /* A test build (KairoX86#37): every line's pixels come in runs of [across] alike, whatever the
               runs' phase, so keeping one of each loses nothing; a frame where they do not is reported. */
            if (across > 1) {
                static unsigned frames_checked;
                frames_checked++;
                for (int row = 0; row < (h * down); row++) {
                    const uint32_t *line = &target->line[y + row][x];
                    bool            alike[2] = { true, true };
                    for (int phase = 0; phase < 2; phase++)
                        for (int column = phase; (column + 1) < (w * across); column += across)
                            if (line[column] != line[column + 1])
                                alike[phase] = false;
                    if (!alike[0] && !alike[1]) {
                        fprintf(stderr, "KAIROX86_CHECK_NATIVE_SIZE: frame %u, line %d of %dx%d: pixels not in pairs\n",
                                frames_checked, row, w * across, h * down);
                        break;
                    }
                }
            }
#endif
            for (int row = 0; room && (row < h); row++) {
                const uint32_t *line = &target->line[y + (row * down)][x];
                if (across == 1)
                    memcpy(&picture[row * w], line, (size_t) w * sizeof(uint32_t));
                else
                    for (int column = 0; column < w; column++)
                        picture[(row * w) + column] = line[column * across];
            }
            picture_width  = w;
            picture_height = h;
        }
        pthread_mutex_unlock(&picture_lock);
    }
    video_blit_complete_monitor(monitor_index);
}

static const uint32_t *
api_screen(int *width, int *height, int *pitch)
{
    /* Called between frames, after run_frame waited for the blit: the picture is not changing. */
    *width  = picture_width;
    *height = picture_height;
    *pitch  = picture_width;
    return picture;
}

/* The host's thread holds blit_lock (pc_run takes it around the CPU's block): a fatal() inside the
   block unwinds past endblit(), so do_stop() releases it. */
static bool blit_held_by_host;

void
startblit(void)
{
    pthread_mutex_lock(&blit_lock);
    if (pthread_equal(pthread_self(), host_thread))
        blit_held_by_host = true;
}

void
endblit(void)
{
    if (pthread_equal(pthread_self(), host_thread))
        blit_held_by_host = false;
    pthread_mutex_unlock(&blit_lock);
}

int
plat_vidapi(UNUSED(const char *api))
{
    return 0;
}

/* 86Box lets the pointer go on close and when a tablet changes mode; Kairo keeps it (mouse_capture). */
void
plat_mouse_capture(UNUSED(int on))
{
}

void
plat_resize(UNUSED(int w), UNUSED(int h), UNUSED(int monitor_index))
{
}

void
plat_resize_request(UNUSED(int w), UNUSED(int h), int monitor_index)
{
    atomic_store(&doresize_monitors[monitor_index], 0);
}

void
sdl_close(void)
{
}

/* ---- UI: messages go to the host ---- */

void
ui_window_title_real(void)
{
    title_set = 0;
}

char *
ui_window_title(char *str)
{
    if (!str)
        return title;
    strncpy(title, str, sizeof(title) - 1);
    return str;
}

void ui_emu_status(UNUSED(int speed_percent)) { }
void ui_init_monitor(UNUSED(int monitor_index)) { }
void ui_deinit_monitor(UNUSED(int monitor_index)) { }

int
ui_msgbox_header(int flags, char *header, char *message)
{
    char text[1024];

    snprintf(text, sizeof(text), "%s%s%s", header ? header : "", (header && message) ? ": " : "", message ? message : "");
    if (flags & MBX_FATAL) {
        char reason[1100];
        snprintf(reason, sizeof(reason), "The PC stopped: %s", text);
        machine_over(reason);
        /* fatal() then calls do_stop(), which ends the machine run. */
    } else
        report(host.notice, text);
    return 1;
}

int
ui_msgbox(int flags, char *message)
{
    return ui_msgbox_header(flags, NULL, message);
}

void
ui_progress_wait(UNUSED(const char *message), int total, int (*poll)(void *arg), void *arg)
{
    while (poll(arg) < total)
        plat_delay_ms(10);
}

int
ui_confirm_unsupported_hardware(UNUSED(const ui_unsupported_hardware_t *items), UNUSED(int count), UNUSED(int machine_missing))
{
    return 1;
}

void ui_sb_update_icon_state(UNUSED(int tag), UNUSED(int state)) { }
/* The floppy drives' activity lamps (KairoX86#41): a bit per drive while it works, and how often
   a lamp changed, so a frame in which a drive worked at all counts as loading. Called on the
   emulation thread, by the floppy controller. */
static unsigned floppy_busy;
static unsigned floppy_changes;
static bool     loading_frame;

static void
floppy_lamp(int tag, int active)
{
    if ((tag & 0xf0) != SB_FLOPPY)
        return;
    const unsigned bit = 1u << (tag & 0x0f);
    floppy_busy        = active ? (floppy_busy | bit) : (floppy_busy & ~bit);
    floppy_changes++;
}

void ui_sb_update_icon(int tag, int active) { floppy_lamp(tag, active); }
void ui_sb_update_icon_write(int tag, int active) { floppy_lamp(tag, active); }
void ui_sb_update_icon_wp(UNUSED(int tag), UNUSED(int state)) { }
void ui_sb_update_tip(UNUSED(int arg)) { }
void ui_sb_update_panes(void) { }
void ui_sb_update_text(void) { }
void ui_sb_set_text(UNUSED(char *wstr)) { }
void ui_sb_bugui(UNUSED(char *str)) { }
void ui_sb_set_ready(UNUSED(int ready)) { }
void ui_sb_mt32lcd(UNUSED(char *str)) { }
void ui_hard_reset_completed(void) { }
void ui_update_force_interpreter(void) { }

/* fatal() ends here after reporting (ui_msgbox), never reaching its exit(). */
void
do_stop(void)
{
    is_quit = 1;
    atomic_store(&dead, true);
    /* On the host's thread, the call into 86Box unwinds to the host, whose machine is then over. */
    if (running && pthread_equal(pthread_self(), host_thread)) {
        if (blit_held_by_host) {
            blit_held_by_host = false;
            pthread_mutex_unlock(&blit_lock);
        }
        longjmp(stopped, 1);
    }
    /* Every call into 86Box comes from the host's thread inside a setjmp (start, run_frame,
       reset, stop), so this is one of 86Box's own threads (the blit, a renderer, a sound thread):
       it ends here, and the host sees the machine over at its next frame. pc_close then joins it
       with the rest. */
#ifdef _WIN32
    _endthreadex(1);
#else
    pthread_exit(NULL);
#endif
}

/* ---- Media (KairoX86#48) ---- */

/* 86Box's own insert and eject (unix/sdl_cdrom.c), which also update its configuration. */
extern void floppy_mount(uint8_t id, char *fn, uint8_t wp);
extern void floppy_eject(uint8_t id);
extern void cdrom_mount(uint8_t id, char *fn);

/* A slot holding an image from outside the machine's folder for this run, and what the slot held
   before it, which goes back in before 86Box saves its configuration (media_restore). */
static bool media_borrowed[KAIRO_X86_MEDIA_SLOTS];
static char media_own[KAIRO_X86_MEDIA_SLOTS][MAX_IMAGE_PATH_LEN];

static bool
media_drive(int slot)
{
    if ((slot == 0) || (slot == 1))
        return drives[slot].type != 0;
    return (slot == 2) && (cdrom[0].bus_type != CDROM_BUS_DISABLED);
}

static const char *
media_held(int slot)
{
    return (slot < 2) ? drives[slot].image_path : cdrom[0].image_path;
}

static bool
media_separator(char c)
{
    return (c == '/') || (c == '\\');
}

/* Whether path is in the machine's folder (86Box's usr_path): a disk of the machine itself. Either
   separator matches the other (a Windows host's paths mix them). */
static bool
media_in_machine(const char *path)
{
    size_t i = 0;

    for (; usr_path[i] != 0; i++)
        if ((path[i] != usr_path[i]) && !(media_separator(path[i]) && media_separator(usr_path[i])))
            return false;
    return (i > 0) && (media_separator(usr_path[i - 1]) || media_separator(path[i]));
}

/* Puts path in slot through 86Box's own insert or eject. */
static void
media_put(int slot, const char *path)
{
    char name[MAX_IMAGE_PATH_LEN];

    snprintf(name, sizeof(name), "%s", path);
    if (slot < 2) {
        if (name[0])
            floppy_mount((uint8_t) slot, name, 0);
        else
            floppy_eject((uint8_t) slot);
    } else if (name[0])
        cdrom_mount(0, name);
    else
        cdrom_eject(0);
}

/* Before 86Box saves its configuration: each slot holding an image of this run only gets back what
   the machine had in it. */
static void
media_restore(void)
{
    for (int slot = 0; slot < KAIRO_X86_MEDIA_SLOTS; slot++)
        if (media_borrowed[slot]) {
            media_borrowed[slot] = false;
            media_put(slot, media_own[slot]);
        }
}

/* ---- Guest input (KairoX86#43) and the pointer's place (KairoX86#44) ---- */

/* How the guest reads its input, for the Auto touch mode, counted as KairoDos counts DOSBox's: the
   BIOS keyboard calls (INT 16h) that wait for a key or check for one, and the mouse driver's
   (INT 33h) reads of the mouse. A real BIOS waits inside one INT 16h call, so a wait lasts until
   the program runs on: until its own code (outside the ROMs, which the BIOS's own calls come from)
   runs its next INT. */
static atomic_uint_fast64_t keyboard_waits;
static atomic_uint_fast64_t keyboard_polls;
static atomic_uint_fast64_t mouse_reads;
static atomic_uint_fast64_t position_reads; /* of them, the position and buttons (AX=03h) */
static atomic_bool          keyboard_wait; /* the last wait has not returned to its program yet */
/* DOS's command prompt (KairoX86#46): the console line the guest wrote through DOS since its last
   line break, and how many times DOS was asked for keyboard input while that line read as a DOS
   prompt (a drive, ":\" and a path, ending in ">", as PROMPT $P$G shows). A command shell asks for
   its command there: MS-DOS's COMMAND.COM by buffered input (INT 21h AH=0Ah), FreeDOS's FreeCOM a key
   at a time (AH=07h), each echoed key leaving the prompt behind. */
static atomic_uint_fast64_t line_inputs;
#define CONSOLE_LINE 160
static char console_line[CONSOLE_LINE];
static int  console_length;
/* The most a DOS write is read of, and conventional memory, where DOS programs keep what they write. */
#define CONSOLE_WRITE   512
#define CONVENTIONAL_END 0xa0000

static void
console_put(char c)
{
    if ((c == '\r') || (c == '\n')) {
        console_length = 0;
        return;
    }
    if (c == '\b') {
        if (console_length > 0)
            console_length--;
        return;
    }
    if (console_length == CONSOLE_LINE) {
        memmove(console_line, console_line + 1, CONSOLE_LINE - 1);
        console_length--;
    }
    console_line[console_length++] = c;
}

/* Whether the console line reads as a DOS prompt: X:\...> */
static bool
console_prompt(void)
{
    if ((console_length < 4) || (console_line[console_length - 1] != '>'))
        return false;
    for (int at = 0; at + 2 < console_length - 1; at++) {
        const char drive = console_line[at];
        if ((((drive >= 'A') && (drive <= 'Z')) || ((drive >= 'a') && (drive <= 'z'))) && (console_line[at + 1] == ':')
            && (console_line[at + 2] == '\\'))
            return true;
    }
    return false;
}

/* Writes count bytes at linear address (DOS's DS:DX) to the console line, up to stop when it is not -1. */
static void
console_write(uint32_t address, int count, int stop)
{
    for (int i = 0; (i < count) && (i < CONSOLE_WRITE) && ((address + i) < CONVENTIONAL_END); i++) {
        const char c = (char) mem_readb_phys(address + i);
        if (c == stop)
            return;
        console_put(c);
    }
}

/* An INT 21h call: what it writes to the console, and a keyboard read at a prompt. */
static void
console_call(uint8_t ah, uint16_t bx, uint16_t cx, uint16_t dx, uint32_t data_base)
{
    switch (ah) {
        case 0x02: /* a character */
            console_put((char) dx);
            break;
        case 0x06: /* direct console output, unless DL=FFh (input) */
            if ((dx & 0xff) != 0xff)
                console_put((char) dx);
            break;
        case 0x09: /* a string ending in $ */
            console_write(data_base + dx, CONSOLE_WRITE, '$');
            break;
        case 0x40: /* a write to standard output or standard error */
            if ((bx == 1) || (bx == 2))
                console_write(data_base + dx, cx, -1);
            break;
        case 0x01: case 0x07: case 0x08: case 0x0a: case 0x0c: /* keyboard input */
            if (console_prompt())
                atomic_fetch_add_explicit(&line_inputs, 1, memory_order_relaxed);
            break;
        case 0x3f: /* a read of standard input */
            if ((bx == 0) && console_prompt())
                atomic_fetch_add_explicit(&line_inputs, 1, memory_order_relaxed);
            break;
        default:
            break;
    }
}

#define BDA_VIDEO_MODE    0x449
#define BDA_COLUMNS       0x44a
#define BDA_KEYBOARD_HEAD 0x41a
#define BDA_KEYBOARD_TAIL 0x41c
#define BDA_LAST_ROW      0x484
/* The adapter and system ROMs, C0000h to FFFFFh. */
#define ROM_START 0xc0000
#define ROM_END   0x100000

/* Direct touch through the guest's mouse driver: a DOS mouse driver keeps the pointer itself, in its
   own coordinates, so the pointer goes where the player tapped by the driver's own "set the
   pointer's position" (INT 33h AX=04h). The program's next "get the position and buttons" call
   (AX=03h) becomes that call, to the tapped point; the program gets back what AX=03h would then
   give: the point, and the buttons the host holds. The driver's coordinates span what the program
   set (AX=07h and 08h) or, until it does, the driver's default for the video mode. */
static atomic_bool placing;                   /* a place waits for the program's next AX=03h */
static atomic_int  place_x, place_y;          /* the tapped point, in the picture's pixels */
static atomic_int  place_width, place_height; /* the picture's size then */
static atomic_int  host_buttons;              /* the buttons the host holds (bit 0 left, 1 right, 2 middle) */
static bool        range_x_set, range_y_set;
static int         range_x_min, range_x_max, range_y_min, range_y_max;

/* The driver's default span on one axis for the video mode (Microsoft's mouse driver's): text by its
   8-pixel cells, the 320-pixel-wide modes doubled to 640, every other standard mode its own pixels,
   and any other mode the picture's. */
static int
driver_span(bool across)
{
    const uint8_t mode = mem_readb_phys(BDA_VIDEO_MODE) & 0x7f;

    if ((mode <= 0x03) || (mode == 0x07)) {
        if (across)
            return mem_readw_phys(BDA_COLUMNS) * 8;
        const uint8_t last_row = mem_readb_phys(BDA_LAST_ROW);
        return ((last_row != 0) ? (last_row + 1) : 25) * 8;
    }
    switch (mode) {
        case 0x04: case 0x05: case 0x06: case 0x0d: case 0x0e: case 0x13:
            return across ? 640 : 200;
        case 0x0f: case 0x10:
            return across ? 640 : 350;
        case 0x11: case 0x12:
            return across ? 640 : 480;
        default:
            return across ? atomic_load(&place_width) : atomic_load(&place_height);
    }
}

/* A picture coordinate as the driver's: proportionally across the driver's span. */
static uint16_t
driver_coordinate(int value, int size, bool set, int min, int max, bool across)
{
    if (!set) {
        min = 0;
        max = driver_span(across) - 1;
    }
    if (size <= 0)
        return (uint16_t) min;
    int coordinate = min + (int) (((int64_t) value * (max - min + 1)) / size);
    if (coordinate > max)
        coordinate = max;
    if (coordinate < min)
        coordinate = min;
    return (uint16_t) coordinate;
}

/* Every INT n the guest runs, from code at linear code_base with DS at data_base (the processors' INT
   decoders, kairox86-guest-input); the registers are the call's, which a place may change. */
void
kairo_observe_int(uint8_t num, uint16_t *ax, uint16_t *bx, uint16_t *cx, uint16_t *dx, uint32_t code_base,
                  uint32_t data_base)
{
    const uint8_t ah = *ax >> 8;

    if ((code_base < ROM_START) || (code_base >= ROM_END))
        atomic_store(&keyboard_wait, false);
    if (num == 0x16) {
        /* Get a keystroke: a wait when the buffer is empty, else a key read at once. */
        if (((ah == 0x00) || (ah == 0x10)) && (mem_readw_phys(BDA_KEYBOARD_HEAD) == mem_readw_phys(BDA_KEYBOARD_TAIL))) {
            atomic_fetch_add_explicit(&keyboard_waits, 1, memory_order_relaxed);
            atomic_store(&keyboard_wait, true);
        } else if ((ah == 0x01) || (ah == 0x11))
            atomic_fetch_add_explicit(&keyboard_polls, 1, memory_order_relaxed); /* check for a keystroke */
    } else if (num == 0x21)
        console_call(ah, *bx, *cx, *dx, data_base);
    else if ((num == 0x10) && (ah == 0x00))
        /* A video mode set: the driver goes back to the mode's span. */
        range_x_set = range_y_set = false;
    else if (num == 0x33) {
        switch (*ax) {
            case 0x00: case 0x21: /* a reset: the default span */
                range_x_set = range_y_set = false;
                break;
            case 0x07: /* the horizontal span */
                range_x_min = (*cx < *dx) ? *cx : *dx;
                range_x_max = (*cx < *dx) ? *dx : *cx;
                range_x_set = true;
                break;
            case 0x08: /* the vertical span */
                range_y_min = (*cx < *dx) ? *cx : *dx;
                range_y_max = (*cx < *dx) ? *dx : *cx;
                range_y_set = true;
                break;
            case 0x03: /* the position and buttons */
                atomic_fetch_add_explicit(&mouse_reads, 1, memory_order_relaxed);
                atomic_fetch_add_explicit(&position_reads, 1, memory_order_relaxed);
                if (atomic_exchange(&placing, false)) {
                    *ax = 0x04;
                    *bx = (uint16_t) atomic_load(&host_buttons);
                    *cx = driver_coordinate(atomic_load(&place_x), atomic_load(&place_width), range_x_set,
                                            range_x_min, range_x_max, true);
                    *dx = driver_coordinate(atomic_load(&place_y), atomic_load(&place_height), range_y_set,
                                            range_y_min, range_y_max, false);
                }
                break;
            case 0x05: case 0x06: case 0x0b: /* a button's presses or releases, the motion counters */
                atomic_fetch_add_explicit(&mouse_reads, 1, memory_order_relaxed);
                break;
            default:
                break;
        }
    }
}

/* ---- Input ---- */

void
joystick_init(void)
{
}

/* Each block, on the host's thread: the host's inputs to the joystick model the machine has (its
   86box.cfg's joystick_type). Axis or button i is input i % n of joystick i / n, n being the model's
   axes or buttons a joystick: the order 86Box lists a model's inputs in, joystick by joystick
   (KairoX86#52). Each joystick the model has is present (86Box reads a joystick without a host
   joystick number as unplugged). */
void
joystick_process(uint8_t gp)
{
    const int type = joystick_type[gp];

    if ((gp != 0) || (type == JS_TYPE_NONE))
        return;
    const int sticks  = joystick_get_max_joysticks(type);
    const int axes    = joystick_get_axis_count(type);
    const int buttons = joystick_get_button_count(type);

    for (int j = 0; (j < sticks) && (j < MAX_JOYSTICKS); j++) {
        joystick_state[gp][j].plat_joystick_nr = j + 1;
        for (int a = 0; a < MAX_JOY_AXES; a++)
            joystick_state[gp][j].axis[a] = 0;
        for (int b = 0; b < MAX_JOY_BUTTONS; b++)
            joystick_state[gp][j].button[b] = 0;
    }
    if (axes > 0)
        for (int i = 0; i < KAIRO_X86_JOYSTICK_AXES; i++)
            if ((i / axes) < sticks)
                joystick_state[gp][i / axes].axis[i % axes] = input_axes[i];
    if (buttons > 0)
        for (int i = 0; i < KAIRO_X86_JOYSTICK_BUTTONS; i++)
            if ((i / buttons) < sticks)
                joystick_state[gp][i / buttons].button[i % buttons] = input_buttons[i];
}

static void
api_key(int scancode, bool down)
{
    keyboard_input(down, (uint16_t) scancode);
}

static void
api_mouse_move(int dx, int dy)
{
    mouse_scale(dx, dy);
}

static void
api_mouse_buttons(int buttons)
{
    atomic_store(&host_buttons, buttons);
    mouse_set_buttons_ex(buttons);
}

static void
api_mouse_place(int x, int y)
{
    /* Called between frames: the picture is not changing. */
    atomic_store(&place_x, x);
    atomic_store(&place_y, y);
    atomic_store(&place_width, picture_width);
    atomic_store(&place_height, picture_height);
    atomic_store(&placing, true);
}

static uint64_t
api_line_inputs(void)
{
    return atomic_load(&line_inputs);
}

static bool
api_mouse_placing(void)
{
    return atomic_load(&placing);
}

static bool
api_mouse_moving(void)
{
    return mouse_moved() != 0;
}

static void
api_joystick_axis(int axis, int value)
{
    if ((axis < 0) || (axis >= KAIRO_X86_JOYSTICK_AXES))
        return;
    input_axes[axis] = value;
}

static void
api_joystick_button(int button, bool down)
{
    if ((button < 0) || (button >= KAIRO_X86_JOYSTICK_BUTTONS))
        return;
    input_buttons[button] = down ? 128 : 0;
}

static int
api_media(int slot, const char *path)
{
    if (atomic_load(&dead) || (slot < 0) || (slot >= KAIRO_X86_MEDIA_SLOTS) || !media_drive(slot))
        return -1;
    if (path == NULL)
        path = "";
    if (setjmp(stopped)) {
        running = false;
        return -1;
    }
    running              = true;
    const bool borrowed  = (path[0] != 0) && !media_in_machine(path);
    if (borrowed && !media_borrowed[slot])
        snprintf(media_own[slot], sizeof(media_own[slot]), "%s", media_held(slot));
    if (!borrowed)
        media_borrowed[slot] = false;
    else
        media_borrowed[slot] = true;
    media_put(slot, path);
    running = false;
    /* An image that did not open leaves the drive empty. */
    return (path[0] == 0) == (media_held(slot)[0] == 0) ? 0 : -1;
}

static bool
api_media_path(int slot, char *path, int size)
{
    if ((slot < 0) || (slot >= KAIRO_X86_MEDIA_SLOTS) || (size <= 0) || !media_drive(slot))
        return false;
    snprintf(path, (size_t) size, "%s", media_held(slot));
    return true;
}

static void
api_guest_input(struct KairoX86GuestInput *input)
{
    input->keyboard_waits = atomic_load(&keyboard_waits);
    input->keyboard_polls = atomic_load(&keyboard_polls);
    input->mouse_reads    = atomic_load(&mouse_reads);
    input->position_reads = atomic_load(&position_reads);
    input->keyboard_waiting = atomic_load(&keyboard_wait);
}

static bool
api_loading(void)
{
    return loading_frame;
}

static int
api_locks(void)
{
    uint8_t caps = 0, num = 0, scroll = 0, kana = 0;

    keyboard_get_states(&caps, &num, &scroll, &kana);
    return (caps ? KAIRO_X86_CAPS_LOCK : 0) | (num ? KAIRO_X86_NUM_LOCK : 0) | (scroll ? KAIRO_X86_SCROLL_LOCK : 0);
}

/* ---- Lifecycle ---- */

static bool
api_start(const char *vm_folder, const char *rom_folder, const struct KairoX86Host *given, uint32_t seed)
{
    char *argv[] = { "kairox86", "-P", (char *) vm_folder, "-R", (char *) rom_folder, "-N", NULL };

    host        = *given;
    host_thread = pthread_self();
    if (setjmp(stopped)) {
        running = false;
        return false;
    }
    running = true;
    if (!pc_init(6, argv)) {
        machine_over("86Box could not read its command line");
        running = false;
        return false;
    }
    if (!pc_init_roms()) {
        machine_over("86Box found no firmware");
        running = false;
        return false;
    }
    /* A repeatable run: the guest's clock counts from its CMOS in guest time, never the host's
       (the machine's own setting goes back before 86Box saves its configuration, api_stop). */
    repeatable           = seed != 0;
    configured_time_sync = time_sync;
    if (repeatable)
        time_sync = 0;
    pc_init_modules();
    /* pc_init_modules seeded 86Box's random numbers from the host (random_init). */
    if (repeatable)
        random_seed(seed);
    for (uint8_t i = 1; i < GFXCARD_MAX; i++)
        gfxcard[i] = 0;
    /* The host's motion is in the machine's picture pixels already (KairoX86#50): 86Box's raw
       input takes it as it is, without scaling it from a 640x480 window it would think it has. */
    mouse_set_raw(1);
    video_setblit(blit);
    pc_reset_hard_init();
    plat_pause(0);
    is_cpu_thread = 1;
    is_quit       = 0;
    running       = false;
    return true;
}

/* At a frame's end: whether the processor sits on the HLT it last stayed halted on (CPU_NOTE_HALT,
   KairoX86's patch to every CPU core) with interrupts off, where only an NMI or SMI can wake it. */
static bool
halted_with_interrupts_off(void)
{
    return cpu_halt_seen && !(cpu_state.flags & I_FLAG) && (CS == cpu_halt_cs) && (cpu_state.pc == cpu_halt_pc);
}

static bool
api_run_frame(void)
{
    if (atomic_load(&dead))
        return false;
    if (setjmp(stopped)) {
        running = false;
        return false;
    }
    running = true;
    const uint64_t frames  = monitors[0].mon_renderedframes;
    const unsigned changes = floppy_changes;
    frame_ms               = 0;
    while ((monitors[0].mon_renderedframes == frames) && (frame_ms < KAIRO_X86_MAX_FRAME_MS)) {
        pc_run();
        frame_ms++;
        /* The guest turned the PC off (ACPI, APM or a soft power switch: plat_power_off, which
           saved its disks, CMOS and configuration). */
        if (!cpu_thread_run) {
            machine_over("The PC turned itself off");
            break;
        }
        if (++nvr_ms >= 2000) {
            nvr_ms = 0;
            if (nvr_dosave) {
                nvr_save();
                nvr_dosave = 0;
            }
        }
    }
    /* The blit thread copies the frame: wait until it has, so screen() reads it whole. */
    video_wait_for_blit_monitor(0);
    loading_frame = (floppy_busy != 0) || (floppy_changes != changes);
    if (halted_with_interrupts_off()) {
        halted_ms += frame_ms;
        if (halted_ms >= HALT_STOP_MS)
            machine_over("The PC halted: its processor stopped with interrupts off");
    } else
        halted_ms = 0;
    running = false;
    return !atomic_load(&dead);
}

static double
api_frame_seconds(void)
{
    return frame_ms / 1000.0;
}

static void
api_reset(void)
{
    if (atomic_load(&dead))
        return;
    if (setjmp(stopped)) {
        running = false;
        return;
    }
    running = true;
    pc_reset_hard();
    halted_ms = 0;
    running   = false;
}

/* Ends 86Box's threads and saves its CMOS, also after it stopped (a fatal error, the guest turning
   the PC off, a halt), so its library copy can go. */
static void
api_stop(void)
{
    if (closed)
        return;
    closed = true;
    atomic_store(&dead, true);
    if (setjmp(stopped)) {
        running = false;
        release_mappings();
        release_blocks();
        return;
    }
    running = true;
    /* pc_close saves the configuration: with the machine's own clock setting and its own media. */
    time_sync = configured_time_sync;
    media_restore();
    pc_close(NULL);
    running = false;
    release_mappings();
    release_blocks();
}

static const struct KairoX86Api api = {
    .start           = api_start,
    .run_frame       = api_run_frame,
    .frame_seconds   = api_frame_seconds,
    .screen          = api_screen,
    .sample_rate     = api_sample_rate,
    .read_audio      = api_read_audio,
    .key             = api_key,
    .mouse_move      = api_mouse_move,
    .mouse_buttons   = api_mouse_buttons,
    .mouse_place     = api_mouse_place,
    .mouse_placing   = api_mouse_placing,
    .mouse_moving    = api_mouse_moving,
    .line_inputs     = api_line_inputs,
    .hardware        = hardware_query,
    .joystick_axis   = api_joystick_axis,
    .joystick_button = api_joystick_button,
    .locks           = api_locks,
    .loading         = api_loading,
    .guest_input     = api_guest_input,
    .media           = api_media,
    .media_path      = api_media_path,
    .reset           = api_reset,
    .stop            = api_stop,
};

KAIRO_X86_EXPORT const struct KairoX86Api *
KairoX86_Api(void)
{
    return &api;
}
