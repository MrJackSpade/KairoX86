#include "x86_library.h"

#include <atomic>
#include <cstdio>
#include <cstdlib>

#if defined(__ANDROID__)
#include <android/dlext.h>
#include <android/log.h>
#include <dlfcn.h>
#elif defined(_WIN32)
#include <windows.h>
#else
#error "KairoX86 loads a fresh 86Box library per machine on Android and Windows only"
#endif

namespace kairox86 {

namespace {

// Ends the process with a message: unloading a copy that cannot be unloaded is a bug, and the
// next machine must not start beside it.
[[noreturn]] void fail(const std::string &message) {
#if defined(__ANDROID__)
    __android_log_print(ANDROID_LOG_FATAL, "KairoX86", "%s", message.c_str());
#else
    std::fprintf(stderr, "%s\n", message.c_str());
#endif
    std::abort();
}

#if defined(_WIN32)
std::string windows_error() {
    return "Windows error " + std::to_string(GetLastError());
}

// The folder of the executable, with its trailing separator.
std::wstring module_folder() {
    std::wstring path(MAX_PATH, L'\0');
    for (;;) {
        DWORD length = GetModuleFileNameW(nullptr, path.data(), DWORD(path.size()));
        if (length == 0) fail("GetModuleFileName failed: " + windows_error());
        if (length < path.size()) {
            path.resize(length);
            break;
        }
        path.resize(path.size() * 2);
    }
    return path.substr(0, path.find_last_of(L"\\/") + 1);
}

std::string narrow(const std::wstring &text) {
    int size = WideCharToMultiByte(CP_UTF8, 0, text.c_str(), int(text.size()), nullptr, 0, nullptr, nullptr);
    std::string out(size_t(size), '\0');
    WideCharToMultiByte(CP_UTF8, 0, text.c_str(), int(text.size()), out.data(), size, nullptr, nullptr);
    return out;
}

std::wstring widen(const std::string &text) {
    int size = MultiByteToWideChar(CP_UTF8, 0, text.c_str(), int(text.size()), nullptr, 0);
    std::wstring out(size_t(size), L'\0');
    MultiByteToWideChar(CP_UTF8, 0, text.c_str(), int(text.size()), out.data(), size);
    return out;
}
#endif

} // namespace

std::unique_ptr<X86Library> X86Library::load(std::string &error) {
#if defined(__ANDROID__)
    android_dlextinfo info{};
    info.flags = ANDROID_DLEXT_FORCE_LOAD;
    void *handle = android_dlopen_ext(KAIROX86_86BOX_FILE, RTLD_NOW | RTLD_LOCAL, &info);
    if (!handle) {
        error = std::string("Could not load ") + KAIROX86_86BOX_FILE + ": " + dlerror();
        return nullptr;
    }
    auto entry = reinterpret_cast<const KairoX86Api *(*)()>(dlsym(handle, KAIRO_X86_API_SYMBOL));
    if (!entry) {
        error = std::string(KAIROX86_86BOX_FILE) + " has no " + KAIRO_X86_API_SYMBOL;
        dlclose(handle);
        return nullptr;
    }
    return std::unique_ptr<X86Library>(new X86Library(handle, entry(), ""));
#else
    static std::atomic<unsigned> copies{0};
    const std::wstring folder = module_folder();
    const std::wstring original = folder + widen(KAIROX86_86BOX_FILE);
    wchar_t temp[MAX_PATH + 1];
    DWORD length = GetTempPathW(MAX_PATH + 1, temp);
    if (length == 0 || length > MAX_PATH) {
        error = "GetTempPath failed: " + windows_error();
        return nullptr;
    }
    const std::wstring copy = std::wstring(temp, length) + L"kairox86_86box-" + std::to_wstring(GetCurrentProcessId()) +
                              L"-" + std::to_wstring(copies.fetch_add(1)) + L".dll";
    if (!CopyFileW(original.c_str(), copy.c_str(), FALSE)) {
        error = "Could not copy " + narrow(original) + " to " + narrow(copy) + ": " + windows_error();
        return nullptr;
    }
    HMODULE module = LoadLibraryW(copy.c_str());
    if (!module) {
        error = "Could not load " + narrow(copy) + ": " + windows_error();
        DeleteFileW(copy.c_str());
        return nullptr;
    }
    auto entry = reinterpret_cast<const KairoX86Api *(*)()>(GetProcAddress(module, KAIRO_X86_API_SYMBOL));
    if (!entry) {
        error = narrow(copy) + " has no " + KAIRO_X86_API_SYMBOL;
        FreeLibrary(module);
        DeleteFileW(copy.c_str());
        return nullptr;
    }
    return std::unique_ptr<X86Library>(new X86Library(module, entry(), narrow(copy)));
#endif
}

X86Library::~X86Library() {
#if defined(__ANDROID__)
    if (dlclose(handle_) != 0) fail(std::string("Could not unload ") + KAIROX86_86BOX_FILE + ": " + dlerror());
#else
    if (!FreeLibrary(static_cast<HMODULE>(handle_))) fail("Could not unload " + copy_ + ": " + windows_error());
    if (!DeleteFileW(widen(copy_).c_str())) fail("Could not delete " + copy_ + ": " + windows_error());
#endif
}

} // namespace kairox86
