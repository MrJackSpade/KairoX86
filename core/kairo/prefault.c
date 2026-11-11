/* First touches made ahead of the emulation thread (KairoX86#373): see prefault.h. */
#include "prefault.h"

#if defined(_WIN32)
/* The host build (tools/exact.ps1 -Local): Windows has no populate call, and the device is where it matters. */
void kairo_prefault(void *at, size_t size) { (void) at; (void) size; }
void kairo_prefault_forget(void *at) { (void) at; }
void kairo_prefault_stop(void) {}
#else

#    include <errno.h>
#    include <pthread.h>
#    include <stdint.h>
#    include <stdio.h>
#    include <string.h>
#    include <sys/mman.h>
#    include <unistd.h>
#    ifdef __ANDROID__
#        include <android/log.h>
#    endif

extern void fatal(const char *format, ...);

#    ifndef MADV_POPULATE_WRITE
#        define MADV_POPULATE_WRITE 23
#    endif

/* Populated a chunk at a time, so forgetting a region waits for one chunk at most. */
#    define PREFAULT_CHUNK (1024 * 1024)
#    define PREFAULT_REGIONS 8

struct region {
    uintptr_t base; /* as given, to forget it by */
    uintptr_t next; /* the first page not yet populated */
    uintptr_t end;  /* page-aligned end */
};

static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  work = PTHREAD_COND_INITIALIZER;
static pthread_cond_t  done = PTHREAD_COND_INITIALIZER;
static pthread_t       helper;
static int             running;
static int             stopping;
/* The kernel has no MADV_POPULATE_WRITE (before Linux 5.14): nothing to do. */
static int             unsupported;
static struct region   regions[PREFAULT_REGIONS];
static int             region_count;
/* The region the helper is populating now (outside the lock), or 0. */
static uintptr_t       busy;

static long page_size(void) { return sysconf(_SC_PAGESIZE); }

static struct region make_region(void *at, size_t size)
{
    const uintptr_t p = (uintptr_t) page_size() - 1;
    struct region   r;
    r.base = (uintptr_t) at;
    /* Only whole pages: a partial page at either end faults as before. */
    r.next = ((uintptr_t) at + p) & ~p;
    r.end  = ((uintptr_t) at + size) & ~p;
    if (r.end < r.next)
        r.end = r.next;
    return r;
}

/* With the lock: the next chunk to populate, [*from, *to). */
static int next_chunk(uintptr_t *base, uintptr_t *from, uintptr_t *to)
{
    for (int i = 0; i < region_count; i++) {
        struct region *r = &regions[i];
        if (r->next < r->end) {
            *base = r->base;
            *from = r->next;
            *to   = (r->end - r->next > PREFAULT_CHUNK) ? (r->next + PREFAULT_CHUNK) : r->end;
            r->next = *to;
            return 1;
        }
    }
    return 0;
}

static void *helper_loop(void *unused)
{
    (void) unused;
    pthread_setname_np(pthread_self(), "kairo-prefault");
    pthread_mutex_lock(&lock);
    while (!stopping) {
        uintptr_t base, from, to;
        if (unsupported || !next_chunk(&base, &from, &to)) {
            pthread_cond_wait(&work, &lock);
            continue;
        }
        busy = base;
        pthread_mutex_unlock(&lock);
        int result;
        /* A signal interrupts the populate; the chunk is simply asked for again. */
        do
            result = madvise((void *) from, to - from, MADV_POPULATE_WRITE);
        while (result != 0 && errno == EINTR);
        const int error = errno;
        pthread_mutex_lock(&lock);
        busy = 0;
        pthread_cond_broadcast(&done);
        if (result != 0) {
            if (error == EINVAL && !unsupported) {
                /* The kernel predates MADV_POPULATE_WRITE: the faults stay on the emulation thread, as before. */
                unsupported = 1;
#    ifdef __ANDROID__
                __android_log_print(ANDROID_LOG_INFO, "KairoX86", "prefault: the kernel has no MADV_POPULATE_WRITE");
#    endif
                continue;
            }
            pthread_mutex_unlock(&lock);
            fatal("prefault: populating %p..%p failed: %s\n", (void *) from, (void *) to, strerror(error));
        }
    }
    pthread_mutex_unlock(&lock);
    return NULL;
}

/* With the lock: the helper running. */
static void start_helper(void)
{
    if (running)
        return;
    stopping = 0;
    if (pthread_create(&helper, NULL, helper_loop, NULL) != 0) {
        pthread_mutex_unlock(&lock);
        fatal("prefault: no helper thread\n");
    }
    running = 1;
}

void kairo_prefault(void *at, size_t size)
{
    pthread_mutex_lock(&lock);
    if (region_count == PREFAULT_REGIONS) {
        pthread_mutex_unlock(&lock);
        fatal("prefault: more than %d regions\n", PREFAULT_REGIONS);
    }
    regions[region_count++] = make_region(at, size);
    start_helper();
    pthread_cond_signal(&work);
    pthread_mutex_unlock(&lock);
}

void kairo_prefault_forget(void *at)
{
    const uintptr_t base = (uintptr_t) at;
    pthread_mutex_lock(&lock);
    for (int i = 0; i < region_count; i++)
        if (regions[i].base == base) {
            regions[i] = regions[--region_count];
            i--;
        }
    while (busy == base)
        pthread_cond_wait(&done, &lock);
    pthread_mutex_unlock(&lock);
}

void kairo_prefault_stop(void)
{
    pthread_mutex_lock(&lock);
    if (!running) {
        region_count = 0;
        pthread_mutex_unlock(&lock);
        return;
    }
    stopping = 1;
    pthread_cond_signal(&work);
    pthread_mutex_unlock(&lock);
    pthread_join(helper, NULL);
    pthread_mutex_lock(&lock);
    running      = 0;
    region_count = 0;
    pthread_mutex_unlock(&lock);
}

#endif
