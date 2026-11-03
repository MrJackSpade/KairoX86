#include "x86_machine.h"

#include <utility>

#include "kairo_x86.h"
#include "x86_library.h"

namespace kairox86 {

struct X86Machine::Impl {
    std::unique_ptr<X86Library> library;
    const KairoX86Api *api = nullptr;
    // What 86Box reported through the host: the reason a fatal error stopped it.
    std::string fatal;
    int buttons = 0;
    // DOS's line inputs when the host last pressed a key (waits_for_line).
    uint64_t line_inputs_at_key = 0;
    bool closed = false;

    static void on_fatal(void *context, const char *message) {
        auto *self = static_cast<Impl *>(context);
        if (self->fatal.empty()) self->fatal = message;
    }
    static void on_notice(void *, const char *) {}
};

X86Machine::X86Machine(std::unique_ptr<Impl> impl) : impl_(std::move(impl)) {}

std::unique_ptr<X86Machine> X86Machine::create(const Config &config, std::string &error) {
    auto impl = std::make_unique<Impl>();
    impl->library = X86Library::load(error);
    if (!impl->library) return nullptr;
    impl->api = &impl->library->api();
    KairoX86Host host{impl.get(), &Impl::on_fatal, &Impl::on_notice};
    if (!impl->api->start(config.machine_folder.c_str(), config.rom_folder.c_str(), &host, config.seed)) {
        error = impl->fatal.empty() ? "86Box could not start the machine" : impl->fatal;
        return nullptr;
    }
    return std::unique_ptr<X86Machine>(new X86Machine(std::move(impl)));
}

X86Machine::~X86Machine() { close(); }

bool X86Machine::run_frame(std::string &error) {
    if (impl_->api->run_frame()) return true;
    error = impl_->fatal.empty() ? "The machine stopped" : impl_->fatal;
    return false;
}

double X86Machine::frame_seconds() const { return impl_->api->frame_seconds(); }

const uint8_t *X86Machine::frame(uint32_t &width, uint32_t &height) const {
    int w = 0, h = 0, pitch = 0;
    const uint32_t *pixels = impl_->api->screen(&w, &h, &pitch);
    width = uint32_t(w);
    height = uint32_t(h);
    return reinterpret_cast<const uint8_t *>(pixels);
}

int X86Machine::sample_rate() const { return impl_->api->sample_rate(); }

uint32_t X86Machine::read_audio(int16_t *stereo, uint32_t max_frames) {
    return impl_->api->read_audio(stereo, max_frames);
}

void X86Machine::key(int scancode, bool down) {
    if (down) impl_->line_inputs_at_key = impl_->api->line_inputs();
    impl_->api->key(scancode, down);
}

bool X86Machine::waits_for_line() const { return impl_->api->line_inputs() > impl_->line_inputs_at_key; }

bool X86Machine::typed_key(char c, int &code, bool &shift) {
    // A US keyboard's printable characters: each key's character, then with Shift (set 1 scan codes).
    struct Key {
        char plain, shifted;
        int code;
    };
    static constexpr Key kKeys[] = {
        {'1', '!', 0x02}, {'2', '@', 0x03}, {'3', '#', 0x04}, {'4', '$', 0x05}, {'5', '%', 0x06},
        {'6', '^', 0x07}, {'7', '&', 0x08}, {'8', '*', 0x09}, {'9', '(', 0x0a}, {'0', ')', 0x0b},
        {'-', '_', 0x0c}, {'=', '+', 0x0d}, {'q', 'Q', 0x10}, {'w', 'W', 0x11}, {'e', 'E', 0x12},
        {'r', 'R', 0x13}, {'t', 'T', 0x14}, {'y', 'Y', 0x15}, {'u', 'U', 0x16}, {'i', 'I', 0x17},
        {'o', 'O', 0x18}, {'p', 'P', 0x19}, {'[', '{', 0x1a}, {']', '}', 0x1b}, {'a', 'A', 0x1e},
        {'s', 'S', 0x1f}, {'d', 'D', 0x20}, {'f', 'F', 0x21}, {'g', 'G', 0x22}, {'h', 'H', 0x23},
        {'j', 'J', 0x24}, {'k', 'K', 0x25}, {'l', 'L', 0x26}, {';', ':', 0x27}, {'\'', '"', 0x28},
        {'`', '~', 0x29}, {'\\', '|', 0x2b}, {'z', 'Z', 0x2c}, {'x', 'X', 0x2d}, {'c', 'C', 0x2e},
        {'v', 'V', 0x2f}, {'b', 'B', 0x30}, {'n', 'N', 0x31}, {'m', 'M', 0x32}, {',', '<', 0x33},
        {'.', '>', 0x34}, {'/', '?', 0x35}, {' ', ' ', 0x39},
    };
    for (const Key &key : kKeys) {
        if (c != key.plain && c != key.shifted) continue;
        code = key.code;
        shift = c != key.plain;
        return true;
    }
    return false;
}

int X86Machine::special_key(Special key) {
    switch (key) {
    case Special::Return: return 0x1c;
    case Special::Shift: return 0x2a;
    case Special::Ctrl: return 0x1d;
    case Special::F1: return 0x3b;
    case Special::F2: return 0x3c;
    case Special::F3: return 0x3d;
    case Special::F4: return 0x3e;
    case Special::F5: return 0x3f;
    }
    return -1;
}
void X86Machine::mouse_move(int dx, int dy) { impl_->api->mouse_move(dx, dy); }

void X86Machine::mouse_place(int x, int y) { impl_->api->mouse_place(x, y); }

bool X86Machine::mouse_placing() const { return impl_->api->mouse_placing(); }

bool X86Machine::mouse_moving() const { return impl_->api->mouse_moving(); }

void X86Machine::mouse_button(int button, bool down) {
    if (button < 1 || button > 3) return;
    const int bit = 1 << (button - 1);
    impl_->buttons = down ? (impl_->buttons | bit) : (impl_->buttons & ~bit);
    impl_->api->mouse_buttons(impl_->buttons);
}

void X86Machine::joystick_axis(int axis, int value) { impl_->api->joystick_axis(axis, value); }
void X86Machine::joystick_button(int button, bool down) { impl_->api->joystick_button(button, down); }
int X86Machine::locks() const { return impl_->api->locks(); }
bool X86Machine::loading() const { return impl_->api->loading(); }

X86Machine::GuestInput X86Machine::guest_input() const {
    KairoX86GuestInput input{};
    impl_->api->guest_input(&input);
    return {input.keyboard_waits, input.keyboard_polls, input.mouse_reads, input.position_reads, input.keyboard_waiting};
}

bool X86Machine::media(int slot, const std::string &path) { return impl_->api->media(slot, path.c_str()) == 0; }

std::vector<std::string> X86Machine::media_paths() const {
    std::vector<std::string> paths;
    for (int slot = 0; slot < KAIRO_X86_MEDIA_SLOTS; ++slot) {
        char path[1024] = "";
        paths.emplace_back(impl_->api->media_path(slot, path, int(sizeof(path))) ? path : "");
    }
    return paths;
}
void X86Machine::reset() { impl_->api->reset(); }

void X86Machine::close() {
    if (impl_->closed) return;
    impl_->closed = true;
    impl_->api->stop();
}

} // namespace kairox86
