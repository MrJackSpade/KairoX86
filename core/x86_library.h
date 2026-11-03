// A fresh copy of the 86Box library (kairox86_86box, core/kairo/kairo_x86.h) for one machine.
//
// 86Box keeps its state in process-wide variables that only a new process resets. Loading a new
// copy of the library gives each machine those variables as a new 86Box process has them, and
// unloading it discards whatever the machine left behind. On Android the library is loaded again
// even though a copy of it is already loaded (ANDROID_DLEXT_FORCE_LOAD); on Windows, where a
// module loads once per path, from a copy of the file made for this machine.

#pragma once

#include <memory>
#include <string>

#include "kairo_x86.h"

namespace kairox86 {

class X86Library {
public:
    // A new copy of the library; null with error set when it cannot be loaded.
    static std::unique_ptr<X86Library> load(std::string &error);
    // Unloads the copy: its machine's thread must have ended.
    ~X86Library();

    X86Library(const X86Library &) = delete;
    X86Library &operator=(const X86Library &) = delete;

    const KairoX86Api &api() const { return *api_; }

private:
    X86Library(void *handle, const KairoX86Api *api, std::string copy)
        : handle_(handle), api_(api), copy_(std::move(copy)) {}

    void *handle_;
    const KairoX86Api *api_;
    // The file this copy was loaded from, when it was made for it (Windows); "" otherwise.
    std::string copy_;
};

} // namespace kairox86
