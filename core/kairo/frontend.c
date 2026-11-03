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
#include "cpu.h"

#ifdef _WIN32
#    include <process.h>
#endif

#include "kairo_x86.h"

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
int  mouse_capture;

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
            for (int row = 0; row < h; row++)
                memcpy(&picture[row * w], &target->line[y + row][x], (size_t) w * sizeof(uint32_t));
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

void
plat_mouse_capture(int on)
{
    mouse_capture = on;
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
    mouse_set_buttons_ex(buttons);
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
        return;
    }
    running = true;
    /* pc_close saves the configuration: with the machine's own clock setting and its own media. */
    time_sync = configured_time_sync;
    media_restore();
    pc_close(NULL);
    running = false;
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
    .joystick_axis   = api_joystick_axis,
    .joystick_button = api_joystick_button,
    .locks           = api_locks,
    .loading         = api_loading,
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
