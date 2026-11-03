// The hardware 86Box offers (Kairo#143), for the machine settings: a copy of the 86Box library of its
// own (x86_library.h), with no machine running, answering core/kairo/hardware.h's queries.

#pragma once

#include <memory>
#include <mutex>
#include <string>

namespace kairox86 {

class X86Library;

class X86Hardware {
public:
    // The hardware as the player's 86Box ROM set at [rom_folder] has firmware for; null with error set
    // when the library cannot be loaded.
    static std::unique_ptr<X86Hardware> create(const std::string &rom_folder, std::string &error);
    ~X86Hardware();

    // The answer to [query] as JSON ("machines", "machine <id>"): "" with error set for a query the
    // core does not know.
    std::string query(const std::string &query, std::string &error);

private:
    X86Hardware(std::unique_ptr<X86Library> library, std::string rom_folder);

    std::unique_ptr<X86Library> library_;
    std::string rom_folder_;
    std::mutex lock_;
};

} // namespace kairox86
