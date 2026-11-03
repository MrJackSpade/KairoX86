/* POC shim: the few SDL calls sdl_plat*.c make, implemented on POSIX. */
#ifndef HEADLESS_SDL_SHIM_H
#define HEADLESS_SDL_SHIM_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <limits.h>

static inline void
SDL_Delay(uint32_t ms)
{
    usleep((useconds_t) ms * 1000);
}

static inline uint64_t
SDL_GetPerformanceCounter(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t) ts.tv_sec * 1000000000ull + (uint64_t) ts.tv_nsec;
}

static inline uint64_t
SDL_GetPerformanceFrequency(void)
{
    return 1000000000ull;
}

static inline uint64_t
SDL_GetTicks(void)
{
    return SDL_GetPerformanceCounter() / 1000000ull;
}

#ifdef _WIN32
#    include <windows.h>

static inline const char *
SDL_GetBasePath(void)
{
    static char path[MAX_PATH];
    DWORD       n = GetModuleFileNameA(NULL, path, sizeof(path));
    if ((n == 0) || (n >= sizeof(path))) {
        fprintf(stderr, "GetModuleFileNameA failed: %lu\n", GetLastError());
        abort();
    }
    char *slash = strrchr(path, '\\');
    slash[1]    = 0;
    return path;
}
#else
static inline const char *
SDL_GetBasePath(void)
{
    static char path[PATH_MAX];
    ssize_t     n = readlink("/proc/self/exe", path, sizeof(path) - 1);
    if (n <= 0) {
        perror("readlink /proc/self/exe");
        abort();
    }
    path[n] = 0;
    char *slash = strrchr(path, '/');
    slash[1]    = 0;
    return path;
}
#endif

static inline char *
SDL_GetPrefPath(const char *org, const char *app)
{
    (void) org;
    (void) app;
    return strdup(SDL_GetBasePath());
}

static inline void
SDL_free(void *p)
{
    free(p);
}

#endif
