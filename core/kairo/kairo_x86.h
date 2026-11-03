/*
 * KairoX86: the seam between 86Box and the frame-driven machine (x86_machine.h) that runs it one
 * video frame at a time.
 *
 * 86Box keeps its whole state in process-wide variables and was written to run once per process.
 * So that every machine starts from 86Box's initial state, as a new 86Box process would, it is
 * built as a library of its own (kairox86_86box) and the machine loads a fresh copy of it for each
 * run (x86_library.h), discarding it afterwards: nothing one machine leaves behind can reach the
 * next. The library's only entry point is KairoX86_Api, which returns its functions.
 *
 * 86Box runs in blocks of one millisecond of guest time (pc_run). The host calls run_frame on its
 * emulation thread, which runs blocks until the guest's video card has finished a frame; every
 * other function is called on that thread between frames, so the host and 86Box never touch its
 * state at once. 86Box's own threads (the blitter, sound synthesis) keep running in between.
 *
 * KairoX86 is free software under the GNU General Public License, version 2 or (at your option)
 * any later version. See LICENSE.md.
 */

#ifndef KAIRO_X86_H
#define KAIRO_X86_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* The longest frame: a frame ends when the video card finishes one, or after this much guest time
 * without one (a guest whose display is off, or a machine without a video card), so the host still
 * gets its frames. Guest time, not the host's: two runs end their frames at the same points. */
#define KAIRO_X86_MAX_FRAME_MS 50

/* The game port's joysticks and their controls. */
#define KAIRO_X86_JOYSTICKS 2
#define KAIRO_X86_JOYSTICK_AXES 2
#define KAIRO_X86_JOYSTICK_BUTTONS 4
#define KAIRO_X86_AXIS_MAX 32767

/* The lock keys, as the guest last set the keyboard's lamps. */
#define KAIRO_X86_CAPS_LOCK 1
#define KAIRO_X86_NUM_LOCK 2
#define KAIRO_X86_SCROLL_LOCK 4

/* The machine's side, called on the host's thread with its context. */
struct KairoX86Host {
	void *context;
	/* 86Box hit an error it cannot continue past (fatal()). run_frame returns false after it. */
	void (*fatal)(void *context, const char *message);
	/* A message 86Box would show in a message box and carry on. */
	void (*notice)(void *context, const char *message);
};

struct KairoX86Api {
	/* Starts the machine 86Box finds in vm_folder (its 86box.cfg, its disks and nvr/), with the
	 * firmware under rom_folder (86Box's roms/ layout). False after host->fatal when it cannot.
	 * A library copy starts one machine: the host loads a fresh copy for the next. */
	bool (*start)(const char *vm_folder, const char *rom_folder, const struct KairoX86Host *host);
	/* Runs the guest to the end of its next video frame (or KAIRO_X86_MAX_FRAME_MS); false after
	 * host->fatal when the machine stopped. */
	bool (*run_frame)(void);
	/* The guest time the last frame lasted, in seconds. */
	double (*frame_seconds)(void);
	/* The last picture: rows of 0x00RRGGBB pixels, pitch pixels apart. */
	const uint32_t *(*screen)(int *width, int *height, int *pitch);
	/* The sound sample rate every stream is mixed to. */
	int (*sample_rate)(void);
	/* Takes up to max_frames interleaved stereo frames mixed so far. */
	uint32_t (*read_audio)(int16_t *stereo, uint32_t max_frames);

	/* A key by its scan code: set 1, with 0x100 added for the keys sent after an E0 prefix. */
	void (*key)(int scancode, bool down);
	/* The mouse: motion in host pixels, and its buttons (bit 0 left, 1 right, 2 middle). */
	void (*mouse_move)(int dx, int dy);
	void (*mouse_buttons)(int buttons);
	/* A game port joystick's axis (-KAIRO_X86_AXIS_MAX to KAIRO_X86_AXIS_MAX) and buttons. */
	void (*joystick_axis)(int joystick, int axis, int value);
	void (*joystick_button)(int joystick, int button, bool down);
	/* The lock keys' lamps (KAIRO_X86_*_LOCK). */
	int (*locks)(void);

	/* Resets the machine: a hard reset, as switching it off and on does. */
	void (*reset)(void);
	/* Stops the machine, saving its CMOS: the copy is then done and the host unloads it. */
	void (*stop)(void);
};

#if defined(_WIN32)
#define KAIRO_X86_EXPORT __declspec(dllexport)
#else
#define KAIRO_X86_EXPORT __attribute__((visibility("default")))
#endif

/* The library's one exported symbol. */
#define KAIRO_X86_API_SYMBOL "KairoX86_Api"
KAIRO_X86_EXPORT const struct KairoX86Api *KairoX86_Api(void);

#ifdef __cplusplus
}
#endif

#endif /* KAIRO_X86_H */
