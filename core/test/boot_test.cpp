// Boots a machine folder on the core and runs it for a given guest time, writing the screen as PNG
// at the given guest seconds and at the end, and reporting the frames, the picture sizes, the sound
// and how fast the host ran it.
//
//   boot_test <rom folder> <out folder> <machine folder> <seconds> [snapshot seconds, comma separated]
//
// in the shared host test's order (shared/tools/test-core.ps1: firmware, work folder, media, seconds).
//
// The machine folder holds the machine's 86box.cfg and the disks it names (86Box's own layout); the
// rom folder is the 86Box ROM set itself (its machines/, video/... folders). Runs one machine, then ends.

#include <png.h>

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "x86_machine.h"

#if defined(_WIN32)
#include <windows.h>
#include <tlhelp32.h>
#else
#include <dirent.h>
#endif

namespace {

// The process's threads, to show a closed machine left none of its own behind.
int thread_count() {
#if defined(_WIN32)
    const DWORD process = GetCurrentProcessId();
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (snapshot == INVALID_HANDLE_VALUE) return -1;
    THREADENTRY32 entry{};
    entry.dwSize = sizeof(entry);
    int count = 0;
    for (BOOL more = Thread32First(snapshot, &entry); more; more = Thread32Next(snapshot, &entry))
        if (entry.th32OwnerProcessID == process) ++count;
    CloseHandle(snapshot);
    return count;
#else
    DIR *tasks = opendir("/proc/self/task");
    if (!tasks) return -1;
    int count = 0;
    while (dirent *entry = readdir(tasks))
        if (entry->d_name[0] != '.') ++count;
    closedir(tasks);
    return count;
#endif
}

bool write_png(const std::string &path, const uint8_t *bgra, uint32_t width, uint32_t height) {
    FILE *file = std::fopen(path.c_str(), "wb");
    if (!file) return false;
    png_structp png = png_create_write_struct(PNG_LIBPNG_VER_STRING, nullptr, nullptr, nullptr);
    png_infop info = png_create_info_struct(png);
    if (setjmp(png_jmpbuf(png))) {
        png_destroy_write_struct(&png, &info);
        std::fclose(file);
        return false;
    }
    png_init_io(png, file);
    png_set_IHDR(png, info, width, height, 8, PNG_COLOR_TYPE_RGB, PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_DEFAULT,
                 PNG_FILTER_TYPE_DEFAULT);
    png_write_info(png, info);
    std::vector<uint8_t> row(size_t(width) * 3);
    for (uint32_t y = 0; y < height; ++y) {
        const uint8_t *in = bgra + size_t(y) * width * 4;
        for (uint32_t x = 0; x < width; ++x) {
            row[x * 3] = in[x * 4 + 2];
            row[x * 3 + 1] = in[x * 4 + 1];
            row[x * 3 + 2] = in[x * 4];
        }
        png_write_row(png, row.data());
    }
    png_write_end(png, nullptr);
    png_destroy_write_struct(&png, &info);
    return std::fclose(file) == 0;
}

} // namespace

int main(int argc, char **argv) {
    if (argc < 5) {
        std::fprintf(stderr, "usage: boot_test <rom folder> <out folder> <machine folder> <seconds> [snapshot seconds]\n");
        return 2;
    }
    const std::string out = argv[2];
    const double seconds = std::atof(argv[4]);
    std::set<int> snapshots;
    if (argc > 5) {
        std::stringstream list(argv[5]);
        for (std::string item; std::getline(list, item, ',');) snapshots.insert(std::atoi(item.c_str()));
    }

    kairox86::Config config;
    config.machine_folder = argv[3];
    config.rom_folder = argv[1];
    std::string error;
    const int threads_before = thread_count();
    const auto started = std::chrono::steady_clock::now();
    auto machine = kairox86::X86Machine::create(config, error);
    if (!machine) {
        std::fprintf(stderr, "start failed: %s\n", error.c_str());
        return 1;
    }

    double guest = 0;
    int next_second = 0;
    unsigned long frames = 0;
    uint64_t audio_frames = 0;
    int peak = 0;
    std::vector<int16_t> audio(48000 * 2);
    uint32_t width = 0, height = 0;
    const uint8_t *pixels = nullptr;
    while (guest < seconds) {
        if (!machine->run_frame(error)) {
            std::fprintf(stderr, "stopped at %.3f s: %s\n", guest, error.c_str());
            return 1;
        }
        guest += machine->frame_seconds();
        ++frames;
        for (uint32_t got; (got = machine->read_audio(audio.data(), uint32_t(audio.size() / 2))) > 0;) {
            audio_frames += got;
            for (uint32_t i = 0; i < got * 2; ++i) peak = std::max(peak, std::abs(int(audio[i])));
        }
        pixels = machine->frame(width, height);
        while (next_second <= int(guest)) {
            if (snapshots.count(next_second) && pixels) {
                const std::string path = out + "/frame-" + std::to_string(next_second) + "s.png";
                if (!write_png(path, pixels, width, height)) {
                    std::fprintf(stderr, "could not write %s\n", path.c_str());
                    return 1;
                }
                std::printf("%3d s: %ux%u -> %s\n", next_second, width, height, path.c_str());
            }
            ++next_second;
        }
    }
    const double wall = std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
    if (pixels) {
        const std::string path = out + "/frame-last.png";
        if (!write_png(path, pixels, width, height)) {
            std::fprintf(stderr, "could not write %s\n", path.c_str());
            return 1;
        }
        std::printf("last: %ux%u -> %s\n", width, height, path.c_str());
    } else {
        std::printf("no picture\n");
    }
    std::printf("%lu frames, %.2f guest s in %.2f host s (%.0f%%), %llu audio frames, peak %d\n", frames, guest, wall,
                100.0 * guest / wall, static_cast<unsigned long long>(audio_frames), peak);
    machine->close();
    const int threads_after = thread_count();
    std::printf("threads: %d before the machine, %d after it closed\n", threads_before, threads_after);
    std::fflush(stdout);
    if (threads_after != threads_before) {
        std::fprintf(stderr, "the closed machine left %d thread(s) running\n", threads_after - threads_before);
        return 1;
    }
    machine.reset();
    return 0;
}
