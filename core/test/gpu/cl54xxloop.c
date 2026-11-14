/* KairoX86#133's accelerator workload: cl54xx.c's passes run over and over with the cache on, so a profile sees the
   engine's cost on the emulation thread. Not a test (it never finishes). */
#define test_main cl54xx_test_main
#include "cl54xx.c"
#undef test_main

void test_main(void) {
    /* The cache on (CR0.CD and NW clear), as a game runs: with it off the recompiler interprets everything */
    __asm__ volatile("movl %%cr0, %%eax\n\t"
                     "andl $0x9fffffff, %%eax\n\t"
                     "movl %%eax, %%cr0\n\t"
                     "wbinvd" ::: "eax", "memory");
    for (;;)
        cl54xx_test_main();
}
