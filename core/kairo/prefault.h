/*
 * First touches made ahead of the emulation thread (KairoX86#373). A boot's emulation thread took thousands of
 * page faults a second in its first seconds writing guest RAM for the first time (the BIOS's memory test, the guest
 * clearing memory). A helper thread populates the RAM (MADV_POPULATE_WRITE: the pages the first write would have
 * mapped, zero-filled, with no content changed) while the machine starts, so the emulation thread takes none.
 * Only memory every boot writes anyway: populating the recompiler's link slots and code pool too cost speed (a
 * slot never written reads through the kernel's one zero page, which stays in cache; populated, each is its own).
 */
#ifndef KAIRO_PREFAULT_H
#define KAIRO_PREFAULT_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Populates [at, at + size) on the helper thread. */
void kairo_prefault(void *at, size_t size);
/* The region starting at at is about to be unmapped: no longer touched once this returns. */
void kairo_prefault_forget(void *at);
/* The machine is closing: the helper ends, every region forgotten. */
void kairo_prefault_stop(void);

#ifdef __cplusplus
}
#endif

#endif
