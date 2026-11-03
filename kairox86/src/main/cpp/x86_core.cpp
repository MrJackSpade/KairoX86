// The IBM PC compatible (core/x86_machine.h) as the MachineCore the shared frame host runs
// (shared/frontend/src/main/cpp/kairo/machine_core.h).

#include <array>
#include <memory>
#include <string>
#include <vector>

#include "kairo/machine_core.h"
#include "kairo/relative_warp.h"
#include "x86_machine.h"

namespace {

using kairox86::X86Machine;

// The launch's media (MainActivity.startGame): the machine folder, as the app prepared it.
constexpr int kMachineFolder = 0;
// Scan codes (X86Keys): set 1, with 0x100 for the keys after an E0 prefix.
constexpr int kKeyCodes = 0x200;
// The joystick controls in X86Keys.joystick order: the first stick's directions (the joystick
// model's axes 0 and 1), four buttons (its buttons 0 to 3), then the second stick's directions (its
// axes 2 and 3): one model input each (kairo_x86.h).
constexpr int kJoystickControls = 12;
constexpr int kAxisMax = 32767;
// Direct touch goes through the guest's DOS mouse driver while the program asks it for the position
// (INT 33h AX=03h) at least this often, in frames; otherwise by relative motion (KairoX86#44).
constexpr uint64_t kPositionReadFrames = 30;

class X86Core : public kairo::MachineCore {
public:
    explicit X86Core(std::unique_ptr<X86Machine> machine) : machine_(std::move(machine)) {}

    bool run_frame() override {
        // Whether the program asks the mouse driver for the position: direct touch then places the
        // pointer through the driver.
        const uint64_t reads = machine_->guest_input().position_reads;
        if (reads != position_reads_) {
            position_reads_ = reads;
            position_read_frame_ = frames_;
        }
        if (relative_.running()) {
            int dx = 0, dy = 0;
            relative_.step(!machine_->mouse_moving(), dx, dy);
            if (dx != 0 || dy != 0) machine_->mouse_move(dx, dy);
        }
        ++frames_;
        return machine_->run_frame(error_);
    }
    std::string error() override { return error_; }
    const uint8_t *frame(uint32_t &width, uint32_t &height) override { return machine_->frame(width, height); }
    // 86Box's pixels are 0x00RRGGBB words: B, G, R, A in memory; the presenter reorders them.
    bool frame_bgra() override { return true; }
    double frame_seconds() override { return machine_->frame_seconds(); }
    int32_t audio_rate() override { return machine_->sample_rate(); }
    uint32_t read_audio(int16_t *stereo, uint32_t max_frames) override { return machine_->read_audio(stereo, max_frames); }
    // Bit 0 Caps Lock, 1 Num Lock, 2 Scroll Lock, as NativeMachine lists them (MainActivity).
    int locks() override { return machine_->locks(); }
    // A frame a floppy drive worked in: the frame host runs it flat out (KairoX86#41).
    bool loading() override { return machine_->loading(); }
    // The guest's BIOS keyboard calls and mouse driver reads, for the Auto touch mode (KairoX86#43).
    // The core sees the reads themselves, so it never reports the mouse as set up instead.
    bool guest_input(GuestInput &input) override {
        const X86Machine::GuestInput guest = machine_->guest_input();
        input.keyboard_waits = guest.keyboard_waits;
        input.keyboard_polls = guest.keyboard_polls;
        input.mouse_reads = guest.mouse_reads;
        input.keyboard_waiting = guest.keyboard_waiting;
        input.mouse_enabled = false;
        return true;
    }
    // The removable drives (MainActivity.mediaSlots): floppy drives A and B, the first CD-ROM drive.
    int media(int slot, const std::string &path) override {
        return machine_->media(slot, path) ? 0 : kFailed;
    }
    std::vector<std::string> media_paths() override { return machine_->media_paths(); }

    void release_inputs() override {
        for (int code = 1; code < kKeyCodes; ++code)
            if (keys_[code]) key(code, false);
        for (int control = 0; control < kJoystickControls; ++control)
            if (controls_[control]) joystick(control, false);
        machine_->mouse_button(1, false);
        machine_->mouse_button(2, false);
        machine_->mouse_button(3, false);
    }

    void key(int code, bool down) override {
        if (code <= 0 || code >= kKeyCodes || keys_[code] == down) return;
        keys_[code] = down;
        machine_->key(code, down);
    }

    void joystick(int control, bool down) override {
        if (control < 0 || control >= kJoystickControls) return;
        controls_[control] = down;
        if (control >= 4 && control < 8) {
            machine_->joystick_button(control - 4, down);
            return;
        }
        // Directions: each axis from its pair of controls (up/down, left/right).
        const int stick = control < 4 ? 0 : 1;
        const int base = stick == 0 ? 0 : 8;
        const int y = (controls_[base + 1] ? kAxisMax : 0) - (controls_[base] ? kAxisMax : 0);
        const int x = (controls_[base + 3] ? kAxisMax : 0) - (controls_[base + 2] ? kAxisMax : 0);
        machine_->joystick_axis(stick * 2, x);
        machine_->joystick_axis(stick * 2 + 1, y);
    }

    void mouse_move(int dx, int dy) override {
        if (relative_.hold(dx, dy)) return;
        machine_->mouse_move(dx, dy);
    }
    // Direct touch (KairoX86#44): a program that asks its DOS mouse driver for the position gets the
    // pointer placed by the driver itself, exactly; any other guest gets there by motion, one picture
    // pixel per count, from the corner it is pushed into (RelativeWarp).
    void mouse_warp(int x, int y) override {
        relative_ = kairo::RelativeWarp();
        placing_ = position_reads_ != 0 && frames_ - position_read_frame_ <= kPositionReadFrames;
        if (placing_) {
            machine_->mouse_place(x, y);
            return;
        }
        uint32_t width = 0, height = 0;
        machine_->frame(width, height);
        relative_.start(x, y, int(width), int(height));
    }
    bool mouse_warp_done() override { return placing_ ? !machine_->mouse_placing() : relative_.done(); }
    void mouse_button(int button, bool down) override { machine_->mouse_button(button, down); }
    void reset() override { machine_->reset(); }

    // The machine's CMOS goes back to its folder's nvr/ as it ends (MainActivity writes it back).
    std::string close() override {
        machine_->close();
        return "";
    }

private:
    std::unique_ptr<X86Machine> machine_;
    std::string error_;
    std::array<bool, kKeyCodes> keys_{};
    std::array<bool, kJoystickControls> controls_{};
    uint64_t frames_ = 0;
    uint64_t position_reads_ = 0;
    uint64_t position_read_frame_ = 0;
    bool placing_ = false;
    kairo::RelativeWarp relative_;
};

} // namespace

// The launch's media[0] is the machine folder (86box.cfg, its disks, nvr/), and its firmware folder
// is the player's 86Box ROM set itself (MainActivity.startGame).
std::unique_ptr<kairo::MachineCore> kairo::create_core(const kairo::Launch &launch, std::string &error) {
    if (launch.media.size() <= kMachineFolder || launch.media[kMachineFolder].empty()) {
        error = "No machine folder to start";
        return nullptr;
    }
    kairox86::Config config;
    config.machine_folder = launch.media[kMachineFolder];
    config.rom_folder = launch.firmware;
    auto machine = X86Machine::create(config, error);
    if (!machine) return nullptr;
    return std::make_unique<X86Core>(std::move(machine));
}

// KairoX86's blank disks are written by the app itself (MainActivity.blankDisks).
std::string kairo::create_blank_disk(const std::string &kind, const std::string &) {
    return "KairoX86 makes no blank disk " + kind + " in its core";
}
