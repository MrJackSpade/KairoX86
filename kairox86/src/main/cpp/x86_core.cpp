// The IBM PC compatible (core/x86_machine.h) as the MachineCore the shared frame host runs
// (shared/frontend/src/main/cpp/kairo/machine_core.h).

#include <array>
#include <memory>
#include <string>

#include "kairo/machine_core.h"
#include "x86_machine.h"

namespace {

using kairox86::X86Machine;

// The launch's media (MainActivity.startGame): the machine folder, as the app prepared it.
constexpr int kMachineFolder = 0;
// Scan codes (X86Keys): set 1, with 0x100 for the keys after an E0 prefix.
constexpr int kKeyCodes = 0x200;
// The joystick controls in X86Keys.joystick order: the first joystick's directions and its four
// buttons, then the second joystick's directions.
constexpr int kJoystickControls = 12;
constexpr int kAxisMax = 32767;

class X86Core : public kairo::MachineCore {
public:
    explicit X86Core(std::unique_ptr<X86Machine> machine) : machine_(std::move(machine)) {}

    bool run_frame() override { return machine_->run_frame(error_); }
    std::string error() override { return error_; }
    const uint8_t *frame(uint32_t &width, uint32_t &height) override { return machine_->frame(width, height); }
    // 86Box's pixels are 0x00RRGGBB words: B, G, R, A in memory; the presenter reorders them.
    bool frame_bgra() override { return true; }
    double frame_seconds() override { return machine_->frame_seconds(); }
    int32_t audio_rate() override { return machine_->sample_rate(); }
    uint32_t read_audio(int16_t *stereo, uint32_t max_frames) override { return machine_->read_audio(stereo, max_frames); }
    // Bit 0 Caps Lock, 1 Num Lock, 2 Scroll Lock, as NativeMachine lists them (MainActivity).
    int locks() override { return machine_->locks(); }

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
            machine_->joystick_button(0, control - 4, down);
            return;
        }
        // Directions: each axis from its pair of controls (up/down, left/right).
        const int stick = control < 4 ? 0 : 1;
        const int base = stick == 0 ? 0 : 8;
        const int y = (controls_[base + 1] ? kAxisMax : 0) - (controls_[base] ? kAxisMax : 0);
        const int x = (controls_[base + 3] ? kAxisMax : 0) - (controls_[base + 2] ? kAxisMax : 0);
        machine_->joystick_axis(stick, 0, x);
        machine_->joystick_axis(stick, 1, y);
    }

    void mouse_move(int dx, int dy) override { machine_->mouse_move(dx, dy); }
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
};

} // namespace

// The launch's media[0] is the machine folder (86box.cfg, its disks, nvr/), and its firmware folder
// holds the player's 86Box ROM set under roms/ (MainActivity.startGame).
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
