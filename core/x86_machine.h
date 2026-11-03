// An IBM PC compatible on 86Box (third_party/86box), run one video frame at a time by its host.
//
// 86Box keeps process-wide state, so each machine runs on a fresh copy of the 86Box library
// (x86_library.h), which starts from 86Box's initial state as a new process would. The machine is
// an 86Box machine folder: its 86box.cfg (the hardware), its disk images and its nvr/ (CMOS).

#pragma once

#include <cstdint>
#include <memory>
#include <string>

namespace kairox86 {

class X86Library;

// What a machine starts with.
struct Config {
    // The machine folder: 86box.cfg, the disks it names, and nvr/, which 86Box keeps up to date.
    std::string machine_folder;
    // The firmware, in the 86Box ROM set's layout (roms/machines/..., roms/video/...).
    std::string rom_folder;
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
    // The mouse: motion in host pixels, and button 1 (left), 2 (right) or 3 (middle).
    void mouse_move(int dx, int dy);
    void mouse_button(int button, bool down);
    // A game port joystick's axis (-32767 to 32767) and buttons (0 to 3).
    void joystick_axis(int joystick, int axis, int value);
    void joystick_button(int joystick, int button, bool down);
    // The lock keys' lamps: bit 0 Caps Lock, 1 Num Lock, 2 Scroll Lock.
    int locks() const;

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
