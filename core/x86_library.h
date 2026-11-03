// A fresh copy of the 86Box library (kairox86_86box, core/kairo/kairo_x86.h) for one machine.
//
// 86Box keeps its state in process-wide variables that only a new process resets. Loading a new
// copy of the library gives each machine those variables as a new 86Box process has them, and
// unloading it discards whatever the machine left behind (the shared kairo/fresh_library.h).

#pragma once

#include <memory>
#include <string>

#include "kairo/fresh_library.h"
#include "kairo_x86.h"

namespace kairox86 {

class X86Library {
public:
    // A new copy of the library; null with error set when it cannot be loaded.
    static std::unique_ptr<X86Library> load(std::string &error);

    X86Library(const X86Library &) = delete;
    X86Library &operator=(const X86Library &) = delete;

    const KairoX86Api &api() const { return *api_; }

private:
    X86Library(std::unique_ptr<kairo::FreshLibrary> library, const KairoX86Api *api)
        : library_(std::move(library)), api_(api) {}

    // Unloaded with this object: its machine's thread must have ended.
    std::unique_ptr<kairo::FreshLibrary> library_;
    const KairoX86Api *api_;
};

} // namespace kairox86
