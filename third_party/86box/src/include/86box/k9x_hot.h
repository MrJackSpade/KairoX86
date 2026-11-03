/*
 * Globals the ARM64 block link routine reads on every block transition are
 * placed together in one ELF section, so the routine reaches each one with a
 * single load at a fixed offset from __start_k9xhot instead of first loading
 * its address from a literal pool.
 */
#ifndef EMU_K9X_HOT_H
#define EMU_K9X_HOT_H

#if (defined(__aarch64__) || defined(_M_ARM64)) && defined(__ELF__)
#    define K9X_HOT     __attribute__((section("k9xhot")))
#    define K9X_HAS_HOT 1
extern char __start_k9xhot[];
#else
#    define K9X_HOT
#endif

#endif
