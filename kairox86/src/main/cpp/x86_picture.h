// SPDX-License-Identifier: GPL-2.0-or-later
// KairoX86#330: the PC's picture shown from the GPU, never copied by the processor (kairo::GpuPicture). With Hardware
// acceleration on, each frame is copied by the GPU from the video card's bitmap into a frame slot, an Android hardware
// buffer (core/kairo/gpu_frame.c); the presenter samples that buffer as a GL texture, keeping one of each pixel the card
// drew twice and turning 86Box's B, G, R bytes into colours. Android only.
#pragma once

#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
// After gl3.h: the extensions' header takes its types
#include <GLES2/gl2ext.h>
#include <android/hardware_buffer.h>
#include <android/log.h>

#include <array>
#include <cstdint>
#include <memory>
#include <mutex>

#include "kairo/gpu_picture.h"
#include "kairo_x86.h"
#include "x86_machine.h"

namespace kairox86 {

class X86Picture : public kairo::GpuPicture {
public:
    explicit X86Picture(X86Machine &machine) : machine_(machine) {}
    ~X86Picture() override {
        for (Cached &cached : cached_)
            if (cached.buffer) AHardwareBuffer_release(cached.buffer);
    }

    // Emulation thread, before each frame: the slot the frame goes to, a free one (at most three are taken then: the
    // one shown, one drawn and not yet known done, one waiting to be shown).
    void reserve() {
        std::lock_guard<std::mutex> guard(slots_mutex_);
        for (int i = 0; i < kSlots; ++i)
            if (slots_[i] == Slot::Filling) return;
        for (int i = 0; i < kSlots; ++i)
            if (slots_[i] == Slot::Free) {
                slots_[i] = Slot::Filling;
                machine_.gpu_frame_slot(i);
                return;
            }
        __android_log_assert("slots", "KairoX86", "No free frame slot");
    }

    // The screen's signature (MachineCore::screen_signature): FNV-1a 64 over the B, G, R bytes of every picture pixel
    // of the last frame, as the processor's copy of it would give. Emulation thread, between frames.
    uint64_t signature() {
        uint64_t hash = 14695981039346656037ULL;
        if (!last_.buffer) return 0;
        read(last_, [&](const uint8_t *pixel) {
            for (int c = 0; c < 3; ++c) hash = (hash ^ pixel[c]) * 1099511628211ULL;
            return true;
        });
        return hash;
    }

    uint32_t width() const override { return last_.width; }
    uint32_t height() const override { return last_.height; }
    void drawn_size(uint32_t &width_out, uint32_t &height_out) const override {
        width_out = shown_.width;
        height_out = shown_.height;
    }

    std::unique_ptr<Packet> new_packet() override { return std::make_unique<FramePacket>(); }

    bool take(Packet &packet) override {
        const X86Machine::GpuFrame frame = machine_.gpu_frame();
        if (frame.number == taken_number_ || frame.slot < 0 || !frame.buffer) return false;
        taken_number_ = frame.number;
        auto &taken = static_cast<FramePacket &>(packet);
        taken.frame = Frame{frame.slot, static_cast<AHardwareBuffer *>(frame.buffer), frame.width, frame.height, frame.across,
                            frame.down};
        last_ = taken.frame;
        std::lock_guard<std::mutex> guard(slots_mutex_);
        if (slots_[frame.slot] != Slot::Filling)
            __android_log_assert("slots", "KairoX86", "Frame %d in slot %d, which was not being filled", int(frame.number),
                                 frame.slot);
        slots_[frame.slot] = Slot::Pending;
        return true;
    }

    bool pictured(const Packet &packet) override {
        bool black = true;
        read(static_cast<const FramePacket &>(packet).frame, [&](const uint8_t *pixel) {
            if (pixel[0] > 16 || pixel[1] > 16 || pixel[2] > 16) black = false;
            return black;
        });
        return !black;
    }

    void merge(Packet &newer, const Packet &older) override {
        (void) newer;
        // The older frame is never shown: its slot is free again (the GPU never read it)
        std::lock_guard<std::mutex> guard(slots_mutex_);
        slots_[static_cast<const FramePacket &>(older).frame.slot] = Slot::Free;
    }

    void apply(const Packet &packet) override {
        const Frame &frame = static_cast<const FramePacket &>(packet).frame;
        std::lock_guard<std::mutex> guard(slots_mutex_);
        if (shown_.slot >= 0) slots_[shown_.slot] = drawn_ ? Slot::Retiring : Slot::Free;
        slots_[frame.slot] = Slot::Presenting;
        shown_ = frame;
        drawn_ = false;
    }

    void context_created() override {
        const char *const vertex = "#version 300 es\n"
                                   "void main() {\n"
                                   "    vec2 corner = vec2(float(gl_VertexID & 1), float(gl_VertexID >> 1));\n"
                                   "    gl_Position = vec4(corner * 4.0 - 1.0, 0.0, 1.0);\n"
                                   "}\n";
        // One texel a picture pixel: the first of the across x down the card drew for it; B, G, R in the R, G, B bytes
        const char *const fragment = "#version 300 es\n"
                                     "#extension GL_OES_EGL_image_external_essl3 : require\n"
                                     "precision highp float;\n"
                                     "uniform samplerExternalOES frame;\n"
                                     "uniform ivec2 size;\n"
                                     "uniform ivec2 step_;\n"
                                     "uniform ivec2 texels;\n"
                                     "uniform int flip;\n"
                                     "out vec4 colour;\n"
                                     "void main() {\n"
                                     "    ivec2 p = ivec2(gl_FragCoord.xy);\n"
                                     "    if (flip != 0) p.y = size.y - 1 - p.y;\n"
                                     "    vec2 at = (vec2(p * step_) + 0.5) / vec2(texels);\n"
                                     "    vec4 c = texture(frame, at);\n"
                                     "    colour = vec4(c.b, c.g, c.r, 1.0);\n"
                                     "}\n";
        program_ = link(vertex, fragment);
        glGenVertexArrays(1, &vertex_array_);
        get_ = reinterpret_cast<PFNEGLGETNATIVECLIENTBUFFERANDROIDPROC>(eglGetProcAddress("eglGetNativeClientBufferANDROID"));
        create_image_ = reinterpret_cast<PFNEGLCREATEIMAGEKHRPROC>(eglGetProcAddress("eglCreateImageKHR"));
        destroy_image_ = reinterpret_cast<PFNEGLDESTROYIMAGEKHRPROC>(eglGetProcAddress("eglDestroyImageKHR"));
        target_ = reinterpret_cast<PFNGLEGLIMAGETARGETTEXTURE2DOESPROC>(eglGetProcAddress("glEGLImageTargetTexture2DOES"));
        if (!get_ || !create_image_ || !destroy_image_ || !target_)
            __android_log_assert("egl", "KairoX86", "This device's EGL cannot show a hardware buffer");
    }

    void context_ending() override {
        // Whatever the GPU still reads is read, so the slots it held are free
        glFinish();
        release_retiring();
        for (Cached &cached : cached_) forget(cached);
        if (program_) glDeleteProgram(program_);
        if (vertex_array_) glDeleteVertexArrays(1, &vertex_array_);
        program_ = vertex_array_ = 0;
    }

    void draw(unsigned int framebuffer, bool top_row_first) override {
        if (shown_.slot < 0) return;
        Cached &cached = cached_[shown_.slot];
        if (cached.buffer != shown_.buffer) bind(cached, shown_.buffer);
        glBindFramebuffer(GL_FRAMEBUFFER, framebuffer);
        glViewport(0, 0, GLsizei(shown_.width), GLsizei(shown_.height));
        glDisable(GL_BLEND);
        glDisable(GL_SCISSOR_TEST);
        glDisable(GL_DEPTH_TEST);
        glUseProgram(program_);
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_EXTERNAL_OES, cached.texture);
        glUniform1i(glGetUniformLocation(program_, "frame"), 0);
        glUniform2i(glGetUniformLocation(program_, "size"), GLint(shown_.width), GLint(shown_.height));
        glUniform2i(glGetUniformLocation(program_, "step_"), GLint(shown_.across), GLint(shown_.down));
        glUniform2i(glGetUniformLocation(program_, "texels"), GLint(shown_.width * shown_.across),
                    GLint(shown_.height * shown_.down));
        // The framebuffer's first row is gl_FragCoord.y 0: the picture's top when top_row_first
        glUniform1i(glGetUniformLocation(program_, "flip"), top_row_first ? 0 : 1);
        glBindVertexArray(vertex_array_);
        glDrawArrays(GL_TRIANGLES, 0, 3);
        glBindVertexArray(0);
        glBindTexture(GL_TEXTURE_EXTERNAL_OES, 0);
        // The frame is read once this is done: a slot retired before it is free again, and this one once replaced
        glFinish();
        release_retiring();
        std::lock_guard<std::mutex> guard(slots_mutex_);
        drawn_ = true;
    }

private:
    static constexpr int kSlots = KAIRO_X86_FRAME_SLOTS;
    enum class Slot { Free, Filling, Pending, Presenting, Retiring };
    struct Frame {
        int slot = -1;
        AHardwareBuffer *buffer = nullptr;
        uint32_t width = 0, height = 0, across = 1, down = 1;
    };
    struct FramePacket : Packet {
        Frame frame;
    };
    // A slot's buffer as a GL texture, with the presenter's own reference to the buffer
    struct Cached {
        AHardwareBuffer *buffer = nullptr;
        EGLImageKHR image = EGL_NO_IMAGE_KHR;
        GLuint texture = 0;
    };

    void release_retiring() {
        std::lock_guard<std::mutex> guard(slots_mutex_);
        for (Slot &slot : slots_)
            if (slot == Slot::Retiring) slot = Slot::Free;
    }

    void forget(Cached &cached) {
        if (cached.texture) glDeleteTextures(1, &cached.texture);
        if (cached.image != EGL_NO_IMAGE_KHR) destroy_image_(eglGetCurrentDisplay(), cached.image);
        if (cached.buffer) AHardwareBuffer_release(cached.buffer);
        cached = Cached{};
    }

    void bind(Cached &cached, AHardwareBuffer *buffer) {
        forget(cached);
        AHardwareBuffer_acquire(buffer);
        cached.buffer = buffer;
        const EGLint attributes[] = {EGL_IMAGE_PRESERVED_KHR, EGL_TRUE, EGL_NONE};
        cached.image = create_image_(eglGetCurrentDisplay(), EGL_NO_CONTEXT, EGL_NATIVE_BUFFER_ANDROID, get_(buffer), attributes);
        if (cached.image == EGL_NO_IMAGE_KHR)
            __android_log_assert("egl", "KairoX86", "Could not show a frame's hardware buffer (EGL 0x%x)", eglGetError());
        glGenTextures(1, &cached.texture);
        glBindTexture(GL_TEXTURE_EXTERNAL_OES, cached.texture);
        glTexParameteri(GL_TEXTURE_EXTERNAL_OES, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri(GL_TEXTURE_EXTERNAL_OES, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        glTexParameteri(GL_TEXTURE_EXTERNAL_OES, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_EXTERNAL_OES, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        target_(GL_TEXTURE_EXTERNAL_OES, static_cast<GLeglImageOES>(cached.image));
    }

    // Each picture pixel of frame (its B, G, R, A bytes), read by the processor through the buffer, while each(pixel)
    // gives true. Emulation thread: only the screen's signature and the first picture's check read it.
    template <typename Each> void read(const Frame &frame, Each each) {
        AHardwareBuffer_Desc desc{};
        AHardwareBuffer_describe(frame.buffer, &desc);
        void *bytes = nullptr;
        if (AHardwareBuffer_lock(frame.buffer, AHARDWAREBUFFER_USAGE_CPU_READ_RARELY, -1, nullptr, &bytes) != 0)
            __android_log_assert("lock", "KairoX86", "Could not read a frame's hardware buffer");
        const auto *base = static_cast<const uint8_t *>(bytes);
        bool more = true;
        for (uint32_t y = 0; more && y < frame.height; ++y)
            for (uint32_t x = 0; more && x < frame.width; ++x)
                more = each(base + (size_t(y) * frame.down * desc.stride + size_t(x) * frame.across) * 4);
        AHardwareBuffer_unlock(frame.buffer, nullptr);
    }

    static GLuint compile(GLenum kind, const char *source) {
        const GLuint shader = glCreateShader(kind);
        glShaderSource(shader, 1, &source, nullptr);
        glCompileShader(shader);
        GLint ok = 0;
        glGetShaderiv(shader, GL_COMPILE_STATUS, &ok);
        if (!ok) {
            char log[1024] = {};
            glGetShaderInfoLog(shader, sizeof(log), nullptr, log);
            __android_log_assert("shader", "KairoX86", "The frame's shader did not compile: %s", log);
        }
        return shader;
    }

    static GLuint link(const char *vertex, const char *fragment) {
        const GLuint program = glCreateProgram();
        const GLuint v = compile(GL_VERTEX_SHADER, vertex), f = compile(GL_FRAGMENT_SHADER, fragment);
        glAttachShader(program, v);
        glAttachShader(program, f);
        glLinkProgram(program);
        glDeleteShader(v);
        glDeleteShader(f);
        GLint ok = 0;
        glGetProgramiv(program, GL_LINK_STATUS, &ok);
        if (!ok) {
            char log[1024] = {};
            glGetProgramInfoLog(program, sizeof(log), nullptr, log);
            __android_log_assert("shader", "KairoX86", "The frame's shader did not link: %s", log);
        }
        return program;
    }

    X86Machine &machine_;
    std::mutex slots_mutex_;
    std::array<Slot, kSlots> slots_{};
    uint64_t taken_number_ = 0;
    Frame last_;           // emulation thread: the last frame taken
    Frame shown_;          // presenter thread: the frame applied
    bool drawn_ = false;   // the frame applied has been drawn since (slots_mutex_)
    std::array<Cached, kSlots> cached_{};
    GLuint program_ = 0, vertex_array_ = 0;
    PFNEGLGETNATIVECLIENTBUFFERANDROIDPROC get_ = nullptr;
    PFNEGLCREATEIMAGEKHRPROC create_image_ = nullptr;
    PFNEGLDESTROYIMAGEKHRPROC destroy_image_ = nullptr;
    PFNGLEGLIMAGETARGETTEXTURE2DOESPROC target_ = nullptr;
};

} // namespace kairox86
