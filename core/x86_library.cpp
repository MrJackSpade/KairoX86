#include "x86_library.h"

namespace kairox86 {

std::unique_ptr<X86Library> X86Library::load(std::string &error) {
    auto library = kairo::FreshLibrary::load(KAIROX86_86BOX_FILE, error);
    if (!library) return nullptr;
    auto entry = reinterpret_cast<const KairoX86Api *(*)()>(library->symbol(KAIRO_X86_API_SYMBOL));
    if (!entry) {
        error = std::string(KAIROX86_86BOX_FILE) + " has no " + KAIRO_X86_API_SYMBOL;
        return nullptr;
    }
    const KairoX86Api *api = entry();
    return std::unique_ptr<X86Library>(new X86Library(std::move(library), api));
}

} // namespace kairox86
