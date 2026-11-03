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

void X86Machine::key(int scancode, bool down) { impl_->api->key(scancode, down); }
void X86Machine::mouse_move(int dx, int dy) { impl_->api->mouse_move(dx, dy); }

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
void X86Machine::reset() { impl_->api->reset(); }

void X86Machine::close() {
    if (impl_->closed) return;
    impl_->closed = true;
    impl_->api->stop();
}

} // namespace kairox86
