// An IBM PC compatible on 86Box (third_party/86box), run one video frame at a time by its host.
//
// 86Box keeps process-wide state, so each machine runs on a fresh copy of the 86Box library
// (x86_library.h), which starts from 86Box's initial state as a new process would. The machine is
// an 86Box machine folder: its 86box.cfg (the hardware), its disk images and its nvr/ (CMOS).

#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace kairox86 {

class X86Library;

// What a machine starts with.
struct Config {
    // The machine folder: 86box.cfg, the disks it names, and nvr/, which 86Box keeps up to date.
    std::string machine_folder;
    // The firmware: the 86Box ROM set itself (its machines/, video/... folders), which 86Box
    // reads for each of its roms/ paths.
    std::string rom_folder;
    // Other than 0, a repeatable run (KairoX86#36): 86Box's random numbers from this seed and the
    // guest's clock in guest time. The app runs with 0, as a PC does.
    uint32_t seed = 0;
};

class X86Machine {
public:
    // A machine running config's folder; null with error set when it cannot start.
    static std::unique_ptr<X86Machine> create(const Config &config, std::string &error);
    ~X86Machine();

    // Runs one guest video frame; false with error set when the machine stops.
    bool run_frame(std::string &error);
    // The guest time the last frame lasted.
    double frame_seconds() const;
    // The latest picture: rows of width pixels, 0x00RRGGBB words (B, G, R, A bytes); null before
    // the first frame.
    const uint8_t *frame(uint32_t &width, uint32_t &height) const;
    int sample_rate() const;
    // Takes up to max_frames interleaved stereo frames produced so far.
    uint32_t read_audio(int16_t *stereo, uint32_t max_frames);

    // A key by its scan code: set 1, with 0x100 added for the keys sent after an E0 prefix.
    void key(int scancode, bool down);
    // Startup commands (KairoX86#46): whether the guest waits for a command line, a DOS line input
    // asked for since the host last pressed a key; the key (set 1) that types c on a US keyboard, and
    // whether Shift goes with it (false for a character it has none for); and a special key's code.
    bool waits_for_line() const;
    static bool typed_key(char c, int &code, bool &shift);
    enum class Special { Return, Shift, Ctrl, F1, F2, F3, F4, F5 };
    static int special_key(Special key);
    // The mouse: motion in the picture's pixels, and button 1 (left), 2 (right) or 3 (middle).
    void mouse_move(int dx, int dy);
    void mouse_button(int button, bool down);
    // Direct touch through the guest's DOS mouse driver (kairo_x86.h): its next position read puts
    // the pointer on picture point (x, y); placing() until it has.
    void mouse_place(int x, int y);
    bool mouse_placing() const;
    // Whether the guest's mouse has not yet reported all the motion it was given.
    bool mouse_moving() const;
    // One of the joystick model's inputs (kairo_x86.h): axis 0 to 3 (-32767 to 32767), button 0 to 3,
    // counted joystick by joystick in the order 86Box lists the model's inputs.
    void joystick_axis(int axis, int value);
    void joystick_button(int button, bool down);
    // The lock keys' lamps: bit 0 Caps Lock, 1 Num Lock, 2 Scroll Lock, 3 Kana.
    int locks() const;
    // The keyboard the machine runs with (kairo_x86.h keyboard_model), such as "101" or "106".
    std::string keyboard_model() const;
    // What 86Box started with, as "name=value;..." (kairo_x86.h started).
    std::string started() const;
    // Whether the last frame was loading from a floppy disk (kairo_x86.h): the host runs it flat out.
    bool loading() const;
    // The guest's state as one number (kairo_x86.h state), between frames.
    uint64_t state() const;
    // How the guest reads its input since the machine started (kairo_x86.h), for the Auto touch mode.
    struct GuestInput {
        uint64_t keyboard_waits = 0;
        uint64_t keyboard_polls = 0;
        uint64_t mouse_reads = 0;
        uint64_t position_reads = 0; // of them, the position and buttons (INT 33h AX=03h)
        bool keyboard_waiting = false;
        bool mouse_driven = false; // a protected-mode driver turned the mouse on (KairoX86#190)
    };
    GuestInput guest_input() const;
    // The removable drives (kairo_x86.h): slot 0 and 1 floppy drives A and B, 2 the first CD-ROM
    // drive. Puts path in slot ("" empties it): false when the machine has no such drive or the image
    // did not open. An image from outside the machine's folder is for this run only.
    bool media(int slot, const std::string &path);
    // What each slot holds, "" when empty or when the machine has no such drive.
    std::vector<std::string> media_paths() const;
    // Which slots the machine has a drive for.
    std::vector<bool> media_drives() const;

    // A hard reset, as switching the PC off and on does.
    void reset();
    // Ends the machine, saving its CMOS to the machine folder.
    void close();

private:
    struct Impl;
    explicit X86Machine(std::unique_ptr<Impl> impl);
    std::unique_ptr<Impl> impl_;
};

} // namespace kairox86
