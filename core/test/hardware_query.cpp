// Prints the core's answer to a hardware query (Kairo#143, core/kairo/hardware.h), as the app's
// machine settings get it:
//
//   hardware_query <ROM set> <query>       such as "machines" or "machine 486ap4"

#include <cstdio>
#include <string>

#include "x86_hardware.h"

int main(int argc, char **argv) {
    if (argc != 3) {
        std::fprintf(stderr, "usage: hardware_query <ROM set> <query>\n");
        return 2;
    }
    std::string error;
    auto hardware = kairox86::X86Hardware::create(argv[1], error);
    if (!hardware) {
        std::fprintf(stderr, "FAIL: %s\n", error.c_str());
        return 1;
    }
    const std::string answer = hardware->query(argv[2], error);
    if (answer.empty()) {
        std::fprintf(stderr, "FAIL: %s\n", error.c_str());
        return 1;
    }
    std::fwrite(answer.data(), 1, answer.size(), stdout);
    std::printf("\n");
    return 0;
}
