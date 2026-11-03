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

/* The joystick model's inputs (KairoX86#52): four axes and four buttons, counted in the order 86Box
 * lists the model's inputs, joystick by joystick (its axis and button names). A two-joystick
 * 2-axis 2-button model takes axes 2 and 3 and buttons 2 and 3 as its second joystick's; a 4-axis
 * 4-button one as its own Z and zX axes (throttle and rudder) and buttons 3 and 4. An input the
 * model does not have reaches nothing. */
#define KAIRO_X86_JOYSTICK_AXES 4
#define KAIRO_X86_JOYSTICK_BUTTONS 4
#define KAIRO_X86_AXIS_MAX 32767

/* How the guest reads its input since the machine started (KairoX86#43): its BIOS keyboard calls
 * (INT 16h) that waited for a key and that checked for one, its mouse driver's (INT 33h) reads of
 * the mouse, and whether it waits for a key now. */
struct KairoX86GuestInput {
	uint64_t keyboard_waits;
	uint64_t keyboard_polls;
	uint64_t mouse_reads;
	uint64_t position_reads; /* of the mouse reads, the position and buttons (INT 33h AX=03h) */
	bool keyboard_waiting;
};

/* The removable drives a machine's media go in (KairoX86#48), as slots: floppy drives A and B,
 * then the first CD-ROM drive. */
#define KAIRO_X86_MEDIA_SLOTS 3

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
	 * firmware in rom_folder: the 86Box ROM set itself (its machines/, video/... folders), which
	 * 86Box reads for each of its roms/ paths. False after host->fatal when it cannot.
	 * A library copy starts one machine: the host loads a fresh copy for the next.
	 * A seed other than 0 makes the run repeatable (the tests, KairoX86#36): 86Box's random
	 * numbers come from it, and the guest's clock runs from guest time, not the host's. */
	bool (*start)(const char *vm_folder, const char *rom_folder, const struct KairoX86Host *host, uint32_t seed);
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
	/* The mouse: motion in the picture's pixels (86Box's raw input), and its buttons (bit 0 left, 1 right, 2 middle). */
	void (*mouse_move)(int dx, int dy);
	void (*mouse_buttons)(int buttons);
	/* Direct touch through the guest's DOS mouse driver (KairoX86#44): the program's next "get the
	 * position and buttons" call (INT 33h AX=03h) sets the driver's pointer to picture point (x, y)
	 * instead, as the driver's own "set the position" (AX=04h). mouse_placing: whether that call is
	 * still to come. */
	void (*mouse_place)(int x, int y);
	bool (*mouse_placing)(void);
	/* Whether the mouse still has motion the guest's mouse has not reported. */
	bool (*mouse_moving)(void);
	/* How many times DOS has been asked for keyboard input while the console line it last wrote read
	 * as a DOS prompt (X:\...>): a command shell asking for its command (KairoX86#46). */
	uint64_t (*line_inputs)(void);
	/* The hardware 86Box offers, with no machine running (Kairo#143, core/kairo/hardware.h): the answer
	 * to query as JSON, valid until the next call; NULL for a query it does not know. */
	const char *(*hardware)(const char *rom_folder, const char *query);
	/* One of the joystick model's inputs (KAIRO_X86_JOYSTICK_*): an axis, -KAIRO_X86_AXIS_MAX to
	 * KAIRO_X86_AXIS_MAX, or a button. */
	void (*joystick_axis)(int axis, int value);
	void (*joystick_button)(int button, bool down);
	/* The lock keys' lamps (KAIRO_X86_*_LOCK). */
	int (*locks)(void);
	/* Whether the last frame was loading from a floppy disk (a drive worked in it, KairoX86#41):
	 * the host runs such frames flat out. Hard disks and CDs do not count: a game reads them as
	 * it plays. */
	bool (*loading)(void);
	/* How the guest reads its input, for the Auto touch mode (KairoX86#43). */
	void (*guest_input)(struct KairoX86GuestInput *input);
	/* Puts the image at path in slot (KAIRO_X86_MEDIA_SLOTS), or empties it for an empty path: 0
	 * when the drive holds what was asked, -1 when the machine has no such drive or the image did
	 * not open. An image from outside the machine's folder is for this run only: the drive gets
	 * back what the machine had in it before 86Box saves its configuration (stop), so the folder's
	 * 86box.cfg never names a file the folder lacks. */
	int (*media)(int slot, const char *path);
	/* What slot holds, from 86Box's own drive: the image's path into path (size bytes), "" when
	 * empty; false when the machine has no such drive. */
	bool (*media_path)(int slot, char *path, int size);

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
