#include "x86_hardware.h"

#include <utility>

#include "kairo_x86.h"
#include "x86_library.h"

namespace kairox86 {

X86Hardware::X86Hardware(std::unique_ptr<X86Library> library, std::string rom_folder)
    : library_(std::move(library)), rom_folder_(std::move(rom_folder)) {}

X86Hardware::~X86Hardware() = default;

std::unique_ptr<X86Hardware> X86Hardware::create(const std::string &rom_folder, std::string &error) {
    auto library = X86Library::load(error);
    if (!library) return nullptr;
    return std::unique_ptr<X86Hardware>(new X86Hardware(std::move(library), rom_folder));
}

std::string X86Hardware::query(const std::string &query, std::string &error) {
    std::lock_guard<std::mutex> hold(lock_);
    const char *answer = library_->api().hardware(rom_folder_.c_str(), query.c_str());
    if (!answer) {
        error = "86Box answers no hardware query \"" + query + "\"";
        return "";
    }
    return answer;
}

} // namespace kairox86
