// Boots a machine folder on the core and runs it for a given guest time, writing the screen as PNG
// at the given guest seconds and at the end, and reporting the frames, the picture sizes, the sound
// and how fast the host ran it.
//
//   boot_test <rom folder> <out folder> <machine folder>[>stop text][|...] <seconds>
//             [snapshot seconds, comma separated] [frame:scancode,...]
//
// in the shared host test's order (shared/tools/test-core.ps1: firmware, work folder, media, seconds).
//
// The machine folder holds the machine's 86box.cfg and the disks it names (86Box's own layout); the
// rom folder is the 86Box ROM set itself (its machines/, video/... folders). The machines run in
// turn in one process; one given with ">stop text" must stop with a reason containing it.

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
#include <psapi.h>
#include <tlhelp32.h>
#else
#include <dirent.h>
#include <unistd.h>
#endif

namespace {

#if defined(_WIN32)
// The module a thread started in, by its start address; "" when it cannot be told.
std::string thread_module(DWORD id) {
    using Query = LONG(WINAPI *)(HANDLE, int, void *, ULONG, ULONG *);
    static const auto query = reinterpret_cast<Query>(
        reinterpret_cast<void *>(GetProcAddress(GetModuleHandleW(L"ntdll.dll"), "NtQueryInformationThread")));
    HANDLE thread = OpenThread(THREAD_QUERY_INFORMATION, FALSE, id);
    if (!thread || !query) return "";
    void *start = nullptr;
    // ThreadQuerySetWin32StartAddress
    const LONG status = query(thread, 9, &start, sizeof(start), nullptr);
    CloseHandle(thread);
    HMODULE module = nullptr;
    if (status != 0 || !GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                                           static_cast<LPCWSTR>(start), &module))
        return "";
    char name[MAX_PATH];
    const DWORD length = GetModuleFileNameA(module, name, MAX_PATH);
    return std::string(name, length);
}
#endif

// The process's threads, to show a closed machine left none of its own behind. On Windows, without
// the system's own worker threads (started in ntdll.dll), which it starts and retires in a process
// whatever the program does; the core's threads start in the C runtime's thread start.
int thread_count() {
#if defined(_WIN32)
    const DWORD process = GetCurrentProcessId();
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (snapshot == INVALID_HANDLE_VALUE) return -1;
    THREADENTRY32 entry{};
    entry.dwSize = sizeof(entry);
    int count = 0;
    for (BOOL more = Thread32First(snapshot, &entry); more; more = Thread32Next(snapshot, &entry))
        if (entry.th32OwnerProcessID == process) {
            std::string module = thread_module(entry.th32ThreadID);
            for (char &c : module) c = char(std::tolower(static_cast<unsigned char>(c)));
            if (module.find("ntdll.dll") == std::string::npos) ++count;
        }
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

// The process's memory in use, in bytes, to show a closed machine gave back what it took (KairoX86#186):
// its private committed memory on Windows, its resident set elsewhere; -1 when it cannot be told.
long long memory_in_use() {
#if defined(_WIN32)
    PROCESS_MEMORY_COUNTERS_EX counters{};
    if (!GetProcessMemoryInfo(GetCurrentProcess(), reinterpret_cast<PROCESS_MEMORY_COUNTERS *>(&counters),
                              sizeof(counters)))
        return -1;
    return static_cast<long long>(counters.PrivateUsage);
#else
    FILE *statm = std::fopen("/proc/self/statm", "r");
    if (!statm) return -1;
    long long pages = 0, resident = 0;
    const int read = std::fscanf(statm, "%lld %lld", &pages, &resident);
    std::fclose(statm);
    return read == 2 ? resident * sysconf(_SC_PAGESIZE) : -1;
#endif
}

// How much more than the first run a later run may leave in use: the C library's heap and the
// system's own caches move by a few megabytes from run to run; a machine's own memory is hundreds.
constexpr long long kMemoryKept = 32ll << 20;

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

// A key pressed on the script: at guest frame [frame], the key with scan code [code] goes down, and up
// a few frames later.
struct Press {
    unsigned long frame;
    int code;
};

constexpr unsigned long kHeldFrames = 4;

// One machine run: boots [folder], runs it [seconds] of guest time with [presses], writes its
// pictures into [out] named after run [index], closes it and checks it left no thread behind. With
// [expected_stop], the machine must stop before then, with a reason containing that text (the
// stop tests, core/test/stops/); without it, it must not stop.
bool run_machine(int index, const std::string &rom_folder, const std::string &folder, const std::string &out,
                 double seconds, const std::set<int> &snapshots, const std::vector<Press> &presses,
                 const std::string &expected_stop) {
    std::printf("run %d: %s%s%s\n", index, folder.c_str(), expected_stop.empty() ? "" : ", to stop with: ",
                expected_stop.c_str());
    kairox86::Config config;
    config.machine_folder = folder;
    config.rom_folder = rom_folder;
    std::string error;
    const int threads_before = thread_count();
    const auto started = std::chrono::steady_clock::now();
    auto machine = kairox86::X86Machine::create(config, error);
    if (!machine) {
        std::fprintf(stderr, "run %d: start failed: %s\n", index, error.c_str());
        return false;
    }
    std::printf("  keyboard: %s\n", machine->keyboard_model().c_str());

    double guest = 0;
    int next_second = 0;
    unsigned long frames = 0;
    uint64_t audio_frames = 0;
    int peak = 0;
    std::vector<int16_t> audio(48000 * 2);
    uint32_t width = 0, height = 0;
    const uint8_t *pixels = nullptr;
    const std::string prefix = out + "/run" + std::to_string(index) + "-";
    std::string stop;
    // The guest seconds the host ran flat out as loading (KairoX86#41) and the power-on self test (#60).
    double loading = 0;
    while (guest < seconds) {
        for (const Press &press : presses) {
            if (press.frame == frames) machine->key(press.code, true);
            if (press.frame + kHeldFrames == frames) machine->key(press.code, false);
        }
        if (!machine->run_frame(error)) {
            stop = error;
            std::printf("  stopped at %.3f s: %s\n", guest, stop.c_str());
            break;
        }
        guest += machine->frame_seconds();
        if (machine->loading()) loading += machine->frame_seconds();
        ++frames;
        for (uint32_t got; (got = machine->read_audio(audio.data(), uint32_t(audio.size() / 2))) > 0;) {
            audio_frames += got;
            for (uint32_t i = 0; i < got * 2; ++i) peak = std::max(peak, std::abs(int(audio[i])));
        }
        pixels = machine->frame(width, height);
        while (next_second <= int(guest)) {
            if (snapshots.count(next_second) && pixels) {
                const std::string path = prefix + std::to_string(next_second) + "s.png";
                if (!write_png(path, pixels, width, height)) {
                    std::fprintf(stderr, "could not write %s\n", path.c_str());
                    return false;
                }
                std::printf("  %3d s: %ux%u -> %s\n", next_second, width, height, path.c_str());
            }
            ++next_second;
        }
    }
    const double wall = std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
    if (pixels) {
        const std::string path = prefix + "last.png";
        if (!write_png(path, pixels, width, height)) {
            std::fprintf(stderr, "could not write %s\n", path.c_str());
            return false;
        }
        std::printf("  last: %ux%u -> %s\n", width, height, path.c_str());
    } else {
        std::printf("  no picture\n");
    }
    std::printf("  %lu frames, %.2f guest s in %.2f host s (%.0f%%), %llu audio frames, peak %d\n", frames, guest, wall,
                100.0 * guest / wall, static_cast<unsigned long long>(audio_frames), peak);
    std::printf("  loading: %.2f guest s\n", loading);
    // What the Auto touch mode reads (KairoX86#43, #190).
    const kairox86::X86Machine::GuestInput input = machine->guest_input();
    std::printf("  guest input: %llu keyboard waits, %llu polls, %llu mouse reads, mouse driven %s\n",
                static_cast<unsigned long long>(input.keyboard_waits), static_cast<unsigned long long>(input.keyboard_polls),
                static_cast<unsigned long long>(input.mouse_reads), input.mouse_driven ? "yes" : "no");
    machine->close();
    machine.reset();
    const int threads_after = thread_count();
    const long long memory_after = memory_in_use();
    std::printf("  threads: %d before the machine, %d after it closed\n", threads_before, threads_after);
    std::fflush(stdout);
    bool passed = true;
    if (threads_after != threads_before) {
        std::fprintf(stderr, "run %d: the closed machine left %d thread(s) running\n", index, threads_after - threads_before);
        passed = false;
    }
    // What a closed machine keeps (KairoX86#186): every run ends within kMemoryKept of where the first
    // run ended, once the C library's heap has grown to what a machine uses.
    static long long first_memory = -1;
    if (first_memory < 0) first_memory = memory_after;
    std::printf("  memory: %lld MB in use after it closed, %lld MB after the first run closed\n", memory_after >> 20,
                first_memory >> 20);
    if ((memory_after < 0) || (memory_after - first_memory > kMemoryKept)) {
        std::fprintf(stderr, "run %d: the closed machine kept %lld MB more than the first run\n", index,
                     (memory_after - first_memory) >> 20);
        passed = false;
    }
    if (expected_stop.empty() && !stop.empty()) {
        std::fprintf(stderr, "run %d: stopped: %s\n", index, stop.c_str());
        passed = false;
    } else if (!expected_stop.empty() && stop.find(expected_stop) == std::string::npos) {
        std::fprintf(stderr, "run %d: expected a stop with \"%s\", got %s\n", index, expected_stop.c_str(),
                     stop.empty() ? "none" : ("\"" + stop + "\"").c_str());
        passed = false;
    }
    return passed;
}

std::vector<std::string> split(const std::string &text, char separator) {
    std::vector<std::string> parts;
    std::stringstream list(text);
    for (std::string item; std::getline(list, item, separator);)
        if (!item.empty()) parts.push_back(item);
    return parts;
}

} // namespace

// boot_test <rom folder> <out folder> <machine folders, separated by |> <seconds> [snapshot seconds]
// [presses, frame:scancode separated by commas, the scan code in decimal or 0x hex]. The machines run in
// turn in one process, as the app runs one game after another, each from the start.
int main(int argc, char **argv) {
    if (argc < 5) {
        std::fprintf(stderr, "usage: boot_test <rom folder> <out folder> <machine folder>[|<machine folder>...] <seconds> "
                             "[snapshot seconds] [frame:scancode,...]\n");
        return 2;
    }
    const std::string out = argv[2];
    const double seconds = std::atof(argv[4]);
    std::set<int> snapshots;
    if (argc > 5)
        for (const std::string &item : split(argv[5], ',')) snapshots.insert(std::atoi(item.c_str()));
    std::vector<Press> presses;
    if (argc > 6)
        for (const std::string &item : split(argv[6], ',')) {
            const size_t colon = item.find(':');
            if (colon == std::string::npos) {
                std::fprintf(stderr, "a press is frame:scancode, not %s\n", item.c_str());
                return 2;
            }
            presses.push_back({std::stoul(item.substr(0, colon)), int(std::stoul(item.substr(colon + 1), nullptr, 0))});
        }
    // Each machine is "<folder>" or "<folder>><expected stop text>" ('>' is in no Windows or
    // Android path). Every machine runs, so one stop test failing still shows the others.
    const std::vector<std::string> machines = split(argv[3], '|');
    int failed = 0;
    for (size_t i = 0; i < machines.size(); ++i) {
        const size_t mark = machines[i].find('>');
        const std::string folder = machines[i].substr(0, mark);
        const std::string expected_stop = mark == std::string::npos ? "" : machines[i].substr(mark + 1);
        if (!run_machine(int(i), argv[1], folder, out, seconds, snapshots, presses, expected_stop)) ++failed;
    }
    if (failed) std::fprintf(stderr, "%d of %zu runs failed\n", failed, machines.size());
    return failed ? 1 : 0;
}
