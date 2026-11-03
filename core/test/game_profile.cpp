// Measures a machine run (KairoX86#56): starts a machine folder, then runs a fixed number of frames
// as fast as the host can with scripted input, and reports host time per guest frame. The same run
// on every build, on the host or on the device (with the NDK), makes builds comparable; --hashes
// writes each frame's picture and sound hash, so two runs or two builds can be shown to run the
// guest identically (KairoX86#36).
//
//   game_profile <ROM set> <work dir> <machine folder> <frames> <script> [options]
//
// The machine folder is copied into <work dir>/machine first and the copy runs: 86Box writes its
// CMOS and 86box.cfg back as it runs, so the folder itself would start the next run differently.
//
// <script> is a comma-separated list of <frame>:<+|-><code> events, by frame from the start: "+"
// presses, "-" lets go. A code is a set 1 scan code (0x1c is Enter, 0x3b is F1; 0x100 added for an
// E0 key), "m1" to "m3" a mouse button, "j1" to "j4" the joystick model's buttons 1 to 4, or "p0" to
// "p3" / "n0" to "n3" its axis 0 to 3 pushed to its positive / negative end ("-" lets it back to the
// middle; kairo_x86.h counts the model's inputs), or "x<n>" / "y<n>" the mouse moved n picture pixels
// right / down ("-" left / up). "-" alone is no input.
//
// Options:
//   --warmup <n>    run n frames before measuring (script frames count from the start)
//   --shots <n>     write the picture every n measured frames as <work dir>/frame-<frame>.bmp
//   --hashes <file> write each frame's picture hash, sound hash and sound frames, warmup included
//   --seed <n>      the repeatable run's seed (default 1, so two runs repeat; 0 runs as the app does)
//   --runs <n>      run the machine n times in this process, each from a fresh copy, and fail unless
//                   every run's hashes match the first's
//   --media <frame>:<slot>:<path>  before that frame, put the image at path in a removable drive
//                   (0 and 1 floppy drives A and B, 2 the CD-ROM drive; an empty path empties it);
//                   may be given more than once. A name without a folder is a file of the machine's
//                   folder (its copy in <work dir>/machine). The drives are printed at the end.
//   --place <frame>:<x>:<y>  before that frame, ask the guest's DOS mouse driver to put the pointer on
//                   picture point (x, y) at the program's next position read (KairoX86#44); may be
//                   given more than once. Prints "placed <frame>" once the program has read it.
//   --commands <lines>  startup commands, "|" between lines, typed at the guest's DOS prompt by the
//                   shared startup typer (KairoX86#46). Prints "typed <frame>" once they all are.
//
// Prints one line starting "start ": how long the machine took to start; and one starting "host ":
// the frames per second the host reached, the guest's rate and the frame time distribution. At the
// end, one line starting "input ": the guest's BIOS keyboard waits and polls, its mouse driver reads
// and whether it waits for a key (KairoX86#43).

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

#include "kairo/startup_typer.h"
#include "x86_machine.h"

namespace fs = std::filesystem;

namespace {

// A path as UTF-8 in a std::string (C++20's u8string is std::u8string).
std::string utf8(const fs::path &path) {
    const std::u8string text = path.u8string();
    return std::string(text.begin(), text.end());
}

int fail(const std::string &message) {
    std::fprintf(stderr, "FAIL: %s\n", message.c_str());
    return 1;
}

// The machine as the startup typer drives it (startup_typer.h), as x86_core.cpp gives it in the app.
struct Typed {
    kairox86::X86Machine &machine;
    kairo::Prompt prompt() { return machine.waits_for_line() ? kairo::Prompt::Line : kairo::Prompt::None; }
    bool typed_key(char c, int &code, bool &shift) { return kairox86::X86Machine::typed_key(c, code, shift); }
    int special_key(kairo::SpecialKey key) {
        using Special = kairox86::X86Machine::Special;
        switch (key) {
        case kairo::SpecialKey::Return: return kairox86::X86Machine::special_key(Special::Return);
        case kairo::SpecialKey::Shift: return kairox86::X86Machine::special_key(Special::Shift);
        case kairo::SpecialKey::Ctrl: return kairox86::X86Machine::special_key(Special::Ctrl);
        default: return -1;
        }
    }
    bool expand_command(std::string &) { return true; }
    void key(int code, bool down) { machine.key(code, down); }
};

struct MediaEvent {
    long frame;
    int slot;
    std::string path;
};

struct Event {
    long frame;
    bool down;
    char kind;  // 'k' a scan code, 'm' a mouse button, 'j' a joystick button, 'p'/'n' a joystick axis,
                // 'x'/'y' mouse motion
    int code;
};

bool parse_script(const std::string &script, std::vector<Event> &events, std::string &error) {
    if (script == "-") return true;
    size_t start = 0;
    while (start <= script.size()) {
        const size_t end = std::min(script.find(',', start), script.size());
        const std::string item = script.substr(start, end - start);
        const size_t colon = item.find(':');
        if (colon == std::string::npos || colon + 2 >= item.size() || (item[colon + 1] != '+' && item[colon + 1] != '-')) {
            error = "bad script event \"" + item + "\"";
            return false;
        }
        const std::string what = item.substr(colon + 2);
        Event event{std::stol(item.substr(0, colon)), item[colon + 1] == '+', 'k', 0};
        if (what[0] == 'm' || what[0] == 'j' || what[0] == 'p' || what[0] == 'n' || what[0] == 'x' || what[0] == 'y') {
            event.kind = what[0];
            event.code = std::stoi(what.substr(1));
        } else {
            event.code = int(std::stol(what, nullptr, 0));
        }
        events.push_back(event);
        start = end + 1;
    }
    return true;
}

// FNV-1a, over a frame's picture or sound.
uint64_t hash(const uint8_t *data, size_t size, uint64_t value = 1469598103934665603ull) {
    for (size_t i = 0; i < size; ++i) value = (value ^ data[i]) * 1099511628211ull;
    return value;
}

// The picture, 0x00RRGGBB words, as a 24-bit BMP.
void write_bmp(const std::string &path, const uint8_t *bgra, uint32_t width, uint32_t height) {
    const uint32_t row = width * 3 + (4 - width * 3 % 4) % 4;
    std::vector<uint8_t> file(54 + size_t(row) * height, 0);
    auto put32 = [&](size_t at, uint32_t value) {
        for (int i = 0; i < 4; ++i) file[at + i] = uint8_t(value >> (8 * i));
    };
    file[0] = 'B';
    file[1] = 'M';
    put32(2, uint32_t(file.size()));
    put32(10, 54);
    put32(14, 40);
    put32(18, width);
    put32(22, height);
    file[26] = 1;
    file[28] = 24;
    for (uint32_t y = 0; y < height; ++y) {
        const uint8_t *in = bgra + size_t(height - 1 - y) * width * 4;
        uint8_t *out = file.data() + 54 + size_t(y) * row;
        for (uint32_t x = 0; x < width; ++x, in += 4) {
            *out++ = in[0];
            *out++ = in[1];
            *out++ = in[2];
        }
    }
    std::ofstream(path, std::ios::binary).write(reinterpret_cast<const char *>(file.data()), std::streamsize(file.size()));
}

} // namespace

int main(int argc, char **argv) {
    if (argc < 6) return fail("usage: game_profile <ROM set> <work dir> <machine folder> <frames> <script> [options]");
    const fs::path work = fs::path(reinterpret_cast<const char8_t *>(argv[2]));
    const fs::path source = fs::path(reinterpret_cast<const char8_t *>(argv[3]));
    const long frames = std::atol(argv[4]);
    std::vector<Event> events;
    std::string error;
    if (!parse_script(argv[5], events, error)) return fail(error);
    long warmup = 0, shots = 0, runs = 1;
    uint32_t seed = 1;
    std::string hashes_path;
    std::vector<MediaEvent> media;
    std::vector<std::array<long, 3>> places;
    std::string commands;
    for (int i = 6; i < argc; ++i) {
        const std::string option = argv[i];
        if (i + 1 >= argc) return fail(option + " needs a value");
        const std::string value = argv[++i];
        if (option == "--warmup") warmup = std::atol(value.c_str());
        else if (option == "--shots") shots = std::atol(value.c_str());
        else if (option == "--hashes") hashes_path = value;
        else if (option == "--seed") seed = uint32_t(std::strtoul(value.c_str(), nullptr, 0));
        else if (option == "--runs") runs = std::atol(value.c_str());
        else if (option == "--media") {
            const size_t first = value.find(':'), second = first == std::string::npos ? first : value.find(':', first + 1);
            if (second == std::string::npos) return fail("--media is <frame>:<slot>:<path>, not " + value);
            media.push_back({std::atol(value.substr(0, first).c_str()), std::atoi(value.substr(first + 1, second - first - 1).c_str()),
                             value.substr(second + 1)});
        }
        else if (option == "--commands") {
            commands = value;
            std::replace(commands.begin(), commands.end(), '|', '\n');
        }
        else if (option == "--place") {
            std::array<long, 3> place{};
            if (std::sscanf(value.c_str(), "%ld:%ld:%ld", &place[0], &place[1], &place[2]) != 3)
                return fail("--place is <frame>:<x>:<y>, not " + value);
            places.push_back(place);
        }
        else return fail("unknown option " + option);
    }
    if (!fs::is_regular_file(source / "86box.cfg")) return fail("no 86box.cfg in " + utf8(source));

    if (runs < 1) return fail("--runs must be at least 1");

    // Each run is one machine, as the app runs one after another in its process: a later run starts
    // on memory the earlier ones used, so a read of memory the emulation never wrote shows as a
    // difference between runs (KairoX86#36).
    std::vector<std::vector<std::string>> lines(static_cast<size_t>(runs));
    for (long run = 0; run < runs; ++run) {
        if (runs > 1) std::printf("run %ld\n", run + 1);
        const fs::path folder = work / "machine";
        fs::remove_all(folder);
        fs::create_directories(work);
        fs::copy(source, folder, fs::copy_options::recursive);

        kairox86::Config config;
        config.rom_folder = argv[1];
        config.machine_folder = utf8(folder);
        config.seed = seed;
        using Clock = std::chrono::steady_clock;
        const auto started = Clock::now();
        auto machine = kairox86::X86Machine::create(config, error);
        if (!machine) return fail("could not start: " + error);
        std::printf("start %.3f s\n", std::chrono::duration<double>(Clock::now() - started).count());

        std::vector<int16_t> audio(48000 * 2);
        std::vector<double> times;
        times.reserve(size_t(frames));
        long loading = 0, last_loading = -1;
        bool placing = false;
        kairo::StartupTyper typer;
        typer.start(commands);
        Typed typed{*machine};
        bool typing = !commands.empty();
        for (long frame = 0; frame < warmup + frames; ++frame) {
            for (const MediaEvent &change : media) {
                if (change.frame != frame) continue;
                const bool plain = !change.path.empty() && change.path.find_first_of("/\\") == std::string::npos;
                const std::string path = plain ? utf8(folder / change.path) : change.path;
                if (!machine->media(change.slot, path))
                    return fail("could not put \"" + path + "\" in slot " + std::to_string(change.slot));
            }
            if (!typer.frame(typed, error)) return fail("startup commands: " + error);
            if (typing && !typer.active()) {
                std::printf("typed %ld\n", frame);
                typing = false;
            }
            if (placing && !machine->mouse_placing()) {
                std::printf("placed %ld\n", frame);
                placing = false;
            }
            for (const std::array<long, 3> &place : places) {
                if (place[0] != frame) continue;
                machine->mouse_place(int(place[1]), int(place[2]));
                placing = true;
            }
            for (const Event &event : events) {
                if (event.frame != frame) continue;
                if (event.kind == 'k') machine->key(event.code, event.down);
                else if (event.kind == 'm') machine->mouse_button(event.code, event.down);
                else if (event.kind == 'j') machine->joystick_button(event.code - 1, event.down);
                else if (event.kind == 'x') machine->mouse_move(event.down ? event.code : -event.code, 0);
                else if (event.kind == 'y') machine->mouse_move(0, event.down ? event.code : -event.code);
            else machine->joystick_axis(event.code, event.down ? (event.kind == 'p' ? 32767 : -32767) : 0);
            }
            const auto before = Clock::now();
            if (!machine->run_frame(error)) return fail("stopped at frame " + std::to_string(frame) + ": " + error);
            const double ms = std::chrono::duration<double, std::milli>(Clock::now() - before).count();
            if (machine->loading()) {
                ++loading;
                last_loading = frame;
            }
            uint32_t got, total = 0;
            uint64_t sound = 1469598103934665603ull;
            while ((got = machine->read_audio(audio.data(), uint32_t(audio.size() / 2))) > 0) {
                total += got;
                sound = hash(reinterpret_cast<const uint8_t *>(audio.data()), size_t(got) * 4, sound);
            }
            uint32_t width = 0, height = 0;
            const uint8_t *pixels = machine->frame(width, height);
            char line[160];
            std::snprintf(line, sizeof(line), "%ld %ux%u %016llx %016llx %u", frame, width, height,
                          (unsigned long long) (pixels ? hash(pixels, size_t(width) * height * 4) : 0),
                          (unsigned long long) sound, total);
            lines[size_t(run)].push_back(line);
            if (frame >= warmup) {
                times.push_back(ms);
                const long measured = frame - warmup;
                if (run == 0 && shots > 0 && measured % shots == 0 && pixels)
                    write_bmp(utf8(work / ("frame-" + std::to_string(measured) + ".bmp")), pixels, width, height);
            }
        }
        if (times.empty()) return fail("no frames measured");
        std::vector<double> sorted = times;
        std::sort(sorted.begin(), sorted.end());
        double total = 0;
        for (double t : times) total += t;
        const double mean = total / double(times.size());
        std::printf("host %.2f frames/s (guest %.2f), frame ms mean %.3f median %.3f p95 %.3f max %.3f over %zu frames\n",
                    1000.0 / mean, 1.0 / machine->frame_seconds(), mean, sorted[sorted.size() / 2],
                    sorted[std::min(sorted.size() - 1, sorted.size() * 95 / 100)], sorted.back(), times.size());
        // The frames the app would run flat out (X86Machine::loading).
        std::printf("loading %ld frames, the last at frame %ld\n", loading, last_loading);
        // How the guest read its input (KairoX86#43), for the Auto touch mode.
        const kairox86::X86Machine::GuestInput input = machine->guest_input();
        std::printf("input waits %llu polls %llu mouse %llu waiting %d\n", (unsigned long long) input.keyboard_waits,
                    (unsigned long long) input.keyboard_polls, (unsigned long long) input.mouse_reads,
                    input.keyboard_waiting ? 1 : 0);
        // What the removable drives hold at the end.
        const std::vector<std::string> held = machine->media_paths();
        for (size_t slot = 0; slot < held.size(); ++slot) std::printf("media %zu: %s\n", slot, held[slot].c_str());
        // The lock keys' lamps at the end: bit 0 Caps Lock, 1 Num Lock, 2 Scroll Lock.
        std::printf("locks %d\n", machine->locks());
        machine->close();
    }

    if (!hashes_path.empty()) {
        std::FILE *hashes = std::fopen(hashes_path.c_str(), "w");
        if (!hashes) return fail("cannot write " + hashes_path);
        for (const std::string &line : lines[0]) std::fprintf(hashes, "%s\n", line.c_str());
        std::fclose(hashes);
    }
    for (long run = 1; run < runs; ++run)
        for (size_t frame = 0; frame < lines[0].size(); ++frame)
            if (lines[size_t(run)][frame] != lines[0][frame])
                return fail("run " + std::to_string(run + 1) + " differs from run 1 at frame " + std::to_string(frame) + ": " +
                            lines[size_t(run)][frame] + " against " + lines[0][frame]);
    if (runs > 1) std::printf("runs: all %ld runs match\n", runs);
    return 0;
}
