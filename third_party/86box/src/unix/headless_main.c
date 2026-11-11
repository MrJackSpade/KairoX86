/* POC headless frontend: no window, no input devices. Everything goes through
   the automation socket. Prints the emulation speed once a second. */
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <wchar.h>

#include <SDL3/SDL.h>

#include <86box/86box.h>
#include <86box/keyboard.h>
#include <86box/mouse.h>
#include <86box/plat.h>
#include <86box/thread.h>
#include <86box/timer.h>
#include <86box/nvr.h>
#include <86box/version.h>
#include <86box/video.h>
#include <86box/ui.h>
#include <86box/gdbstub.h>
#include <86box/automation.h>
#include <86box/gameport.h>

int  rctrl_is_lalt;
int  update_icons;
int  kbd_req_capture;
int  hide_status_bar;
int  hide_tool_bar;
bool fast_forward = false;
int  fixed_size_x = 640;
int  fixed_size_y = 480;
int  title_set;

static pthread_mutex_t blitmtx = PTHREAD_MUTEX_INITIALIZER;
static char            win_title[512] = EMU_NAME;

volatile int cpu_thread_run = 1;

/* POC instrumentation, reported once a second by ui_emu_status. */
static _Atomic uint64_t stat_run_ns;
static _Atomic uint64_t stat_sleep_ns;
static _Atomic uint64_t stat_runs;
static _Atomic uint64_t stat_spins;
static _Atomic uint64_t stat_resets;
static _Atomic uint64_t stat_reset_ms;
static _Atomic uint64_t stat_max_spin_ns;

static void
main_thread(UNUSED(void *param))
{
    /* Each pc_run() is one quantum of emulated time. Pace against an absolute
       deadline so sleep overshoot is paid back instead of lost. */
    const uint64_t quantum_ns = force_10ms ? 10000000ull : 1000000ull;
    uint64_t       deadline   = SDL_GetPerformanceCounter();
    int            frames     = 0;

    is_cpu_thread = 1;
    framecountx   = 0;

    while (!is_quit && cpu_thread_run) {
        automation_poll();
        const int automation = automation_run_state();
        if (!dopause && (automation != AUTOMATION_HOLD)) {
            const uint64_t t0 = SDL_GetPerformanceCounter();
            pc_run();
            stat_run_ns += SDL_GetPerformanceCounter() - t0;
            stat_runs++;
            automation_quantum();

            if (++frames >= (force_10ms ? 200 : 2000) && nvr_dosave) {
                nvr_save();
                nvr_dosave = 0;
                frames     = 0;
            }

            const uint64_t now = SDL_GetPerformanceCounter();
            if (fast_forward || (automation == AUTOMATION_RUN)) {
                deadline = now;
            } else {
                deadline += quantum_ns;
                if (deadline > now) {
                    /* Spin, don't sleep: an idle gap lets the governor drop
                       the core's clock (POC stand-in for ADPF hints). */
                    while (SDL_GetPerformanceCounter() < deadline)
                        ;
                    const uint64_t spun = SDL_GetPerformanceCounter() - now;
                    stat_sleep_ns += spun;
                    stat_spins++;
                    if (spun > stat_max_spin_ns)
                        stat_max_spin_ns = spun;
                } else if (now - deadline > 50000000ull) {
                    /* More than 50 ms behind: the host can't keep up; don't try to catch up. */
                    stat_resets++;
                    stat_reset_ms += (now - deadline) / 1000000ull;
                    deadline = now;
                }
            }
        } else {
            gdbstub_poll();
            SDL_Delay(1);
            deadline = SDL_GetPerformanceCounter();
        }

        if (atomic_load(&doresize_monitors[0]) && !is_quit) {
            plat_resize(scrnsz_x, scrnsz_y, 0);
            atomic_store(&doresize_monitors[0], 0);
        }
    }

    is_quit = 1;
}

static void
headless_blit(UNUSED(int x), UNUSED(int y), UNUSED(int w), UNUSED(int h), int monitor_index)
{
    /* video.c has already handed the frame to the automation layer. */
    video_blit_complete_monitor(monitor_index);
}

static void *
onesec_thread(UNUSED(void *arg))
{
    while (!is_quit) {
        SDL_Delay(1000);
        pc_onesec();
    }
    return NULL;
}

int
main(int argc, char **argv)
{
    if (!pc_init(argc, argv))
        return 0;
    if (!pc_init_roms()) {
        fprintf(stderr, "No ROMs found.\n");
        return 6;
    }
    pc_init_modules();

    for (uint8_t i = 1; i < GFXCARD_MAX; i++)
        gfxcard[i] = 0;

    video_setblit(headless_blit);

    pc_reset_hard_init();
    plat_pause(0);

    is_quit         = 0;
    timer_freq      = SDL_GetPerformanceFrequency();
    thread_t *thMain = thread_create(main_thread, NULL);

    pthread_t onesec;
    pthread_create(&onesec, NULL, onesec_thread, NULL);

    while (!is_quit)
        SDL_Delay(50);

    pc_close(thMain);
    return 0;
}

void
startblit(void)
{
    pthread_mutex_lock(&blitmtx);
}

void
endblit(void)
{
    pthread_mutex_unlock(&blitmtx);
}

/* Renderer hooks. */
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
    atomic_store((&doresize_monitors[monitor_index]), 1);
}

void
sdl_close(void)
{
}

void
ui_window_title_real(void)
{
    title_set = 0;
}

char *
ui_window_title(char *str)
{
    if (!str)
        return win_title;
    strncpy(win_title, str, sizeof(win_title) - 1);
    return str;
}

void
ui_emu_status(int speed_percent)
{
#ifdef K9X_DIAG
    extern uint64_t k9x_c_dispatch, k9x_c_interp, k9x_link_patches, k9x_patch_first, k9x_patch_same, k9x_patch_retarget, k9x_c_dispatch_nofrom;
    static uint64_t last[7];
    const uint64_t  now[7] = { k9x_c_dispatch, k9x_c_dispatch_nofrom, k9x_c_interp, k9x_link_patches, k9x_patch_first, k9x_patch_same, k9x_patch_retarget };
    fprintf(stderr, "[diag] c_dispatch=%llu nofrom=%llu c_interp=%llu patches=%llu first=%llu same=%llu retarget=%llu\n",
            (unsigned long long) (now[0] - last[0]), (unsigned long long) (now[1] - last[1]), (unsigned long long) (now[2] - last[2]),
            (unsigned long long) (now[3] - last[3]), (unsigned long long) (now[4] - last[4]), (unsigned long long) (now[5] - last[5]),
            (unsigned long long) (now[6] - last[6]));
    for (int i = 0; i < 7; i++)
        last[i] = now[i];
    extern uint64_t k9x_miss[8];
    static uint64_t last_miss[8];
    fprintf(stderr, "[miss] target=%llu gen=%llu tsc=%llu slice=%llu timer=%llu irq=%llu status=%llu other=%llu\n",
            (unsigned long long) (k9x_miss[0] - last_miss[0]), (unsigned long long) (k9x_miss[1] - last_miss[1]),
            (unsigned long long) (k9x_miss[2] - last_miss[2]), (unsigned long long) (k9x_miss[3] - last_miss[3]),
            (unsigned long long) (k9x_miss[4] - last_miss[4]), (unsigned long long) (k9x_miss[5] - last_miss[5]),
            (unsigned long long) (k9x_miss[6] - last_miss[6]), (unsigned long long) (k9x_miss[7] - last_miss[7]));
    for (int i = 0; i < 8; i++)
        last_miss[i] = k9x_miss[i];
    extern uint64_t k9x_cnt_changed;
    static uint64_t last_changed;
    fprintf(stderr, "[changed] %llu\n", (unsigned long long) (k9x_cnt_changed - last_changed));
    last_changed = k9x_cnt_changed;
    extern uint64_t k9x_cnt_ins, k9x_cnt_ins_c, k9x_cnt_exits, k9x_cnt_mem, k9x_cnt_walk;
    static uint64_t last_ins, last_ins_c, last_exits, last_mem, last_walk;
    fprintf(stderr, "[count] ins=%llu ins_c=%llu exits=%llu mem=%llu walk=%llu\n", (unsigned long long) (k9x_cnt_ins - last_ins),
            (unsigned long long) (k9x_cnt_ins_c - last_ins_c), (unsigned long long) (k9x_cnt_exits - last_exits),
            (unsigned long long) (k9x_cnt_mem - last_mem), (unsigned long long) (k9x_cnt_walk - last_walk));
    last_ins = k9x_cnt_ins; last_ins_c = k9x_cnt_ins_c; last_exits = k9x_cnt_exits; last_mem = k9x_cnt_mem; last_walk = k9x_cnt_walk;
    extern uint64_t k9x_miss2[12];
    static uint64_t last_miss2[12];
    fprintf(stderr, "[other] flags=%llu status=%llu npxc=%llu cr0=%llu xlat=%llu mem_exec=%llu hash=%llu dirty=%llu top=%llu two_page=%llu none=%llu\n",
            (unsigned long long) (k9x_miss2[0] - last_miss2[0]), (unsigned long long) (k9x_miss2[1] - last_miss2[1]),
            (unsigned long long) (k9x_miss2[2] - last_miss2[2]), (unsigned long long) (k9x_miss2[3] - last_miss2[3]),
            (unsigned long long) (k9x_miss2[4] - last_miss2[4]), (unsigned long long) (k9x_miss2[5] - last_miss2[5]),
            (unsigned long long) (k9x_miss2[6] - last_miss2[6]), (unsigned long long) (k9x_miss2[7] - last_miss2[7]),
            (unsigned long long) (k9x_miss2[8] - last_miss2[8]), (unsigned long long) (k9x_miss2[9] - last_miss2[9]),
            (unsigned long long) (k9x_miss2[10] - last_miss2[10]));
    for (int i = 0; i < 12; i++)
        last_miss2[i] = k9x_miss2[i];
    {
        extern uint64_t k9x_cmem[24];
        static uint64_t last_cmem[24];
        fprintf(stderr, "[cmem]");
        for (int c = 0; c < 20; c++) {
            fprintf(stderr, " %llu", (unsigned long long) (k9x_cmem[c] - last_cmem[c]));
            last_cmem[c] = k9x_cmem[c];
        }
        fprintf(stderr, "%c", 10);
    }
    {
        extern uint64_t k9x_lines_fast, k9x_lines_slow, k9x_slow_why[8];
        fprintf(stderr, "[render] fast=%llu slow=%llu why=%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu\n",
                (unsigned long long) k9x_lines_fast, (unsigned long long) k9x_lines_slow,
                (unsigned long long) k9x_slow_why[0], (unsigned long long) k9x_slow_why[1], (unsigned long long) k9x_slow_why[2],
                (unsigned long long) k9x_slow_why[3], (unsigned long long) k9x_slow_why[4], (unsigned long long) k9x_slow_why[5],
                (unsigned long long) k9x_slow_why[6], (unsigned long long) k9x_slow_why[7]);
    }
    extern uint64_t k9x_lines_skip, k9x_lines_vram, k9x_lines_full;
    static uint64_t last_ls, last_lv, last_lf;
    fprintf(stderr, "[lines] skip=%llu vram=%llu full=%llu\n", (unsigned long long) (k9x_lines_skip - last_ls),
            (unsigned long long) (k9x_lines_vram - last_lv), (unsigned long long) (k9x_lines_full - last_lf));
    last_ls = k9x_lines_skip; last_lv = k9x_lines_vram; last_lf = k9x_lines_full;
    extern void    *k9x_timer_cb[32];
    extern uint64_t k9x_timer_n[32];
    static uint64_t last_tn[32];
    extern char     __executable_start;
    fprintf(stderr, "[timers]");
    for (int i = 0; (i < 32) && k9x_timer_cb[i]; i++) {
        fprintf(stderr, " %lx=%llu", (unsigned long) ((char *) k9x_timer_cb[i] - &__executable_start),
                (unsigned long long) (k9x_timer_n[i] - last_tn[i]));
        last_tn[i] = k9x_timer_n[i];
    }
    fprintf(stderr, "\n");
#endif
    fprintf(stderr, "[speed] %d%% runs=%llu run_ms=%llu spin_ms=%llu spins=%llu max_spin_us=%llu resets=%llu reset_ms=%llu\n", speed_percent,
            (unsigned long long) atomic_exchange(&stat_runs, 0),
            (unsigned long long) (atomic_exchange(&stat_run_ns, 0) / 1000000ull),
            (unsigned long long) (atomic_exchange(&stat_sleep_ns, 0) / 1000000ull),
            (unsigned long long) atomic_exchange(&stat_spins, 0),
            (unsigned long long) (atomic_exchange(&stat_max_spin_ns, 0) / 1000ull),
            (unsigned long long) atomic_exchange(&stat_resets, 0),
            (unsigned long long) atomic_exchange(&stat_reset_ms, 0));
}

void
ui_init_monitor(UNUSED(int monitor_index))
{
}

void
ui_deinit_monitor(UNUSED(int monitor_index))
{
}

/* Message boxes go to stderr. */
int
ui_msgbox_header(int flags, char *header, char *message)
{
    fprintf(stderr, "[msgbox %d] %s: %s\n", flags, header ? header : "", message ? message : "");
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
        SDL_Delay(50);
}

int
ui_confirm_unsupported_hardware(UNUSED(const ui_unsupported_hardware_t *items), UNUSED(int count), UNUSED(int machine_missing))
{
    return 1;
}

void ui_sb_update_icon_state(UNUSED(int tag), UNUSED(int state)) { }
void ui_sb_update_icon(UNUSED(int tag), UNUSED(int active)) { }
void ui_sb_update_icon_write(UNUSED(int tag), UNUSED(int active)) { }
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

/* No host input devices. */
int mouse_capture;

plat_joystick_state_t plat_joystick_state[MAX_PLAT_JOYSTICKS];
joystick_state_t      joystick_state[GAMEPORT_MAX][MAX_JOYSTICKS];

void
joystick_init(void)
{
}

void
joystick_process(UNUSED(uint8_t gp))
{
}

void
do_stop(void)
{
    is_quit = 1;
}
