/* KairoX86#133's accelerator workload: s3.c's 16 bpp passes (solid fills, screen-to-screen blits, lines and host-to-
   screen transfers through the S3 Trio's enhanced engine) run over and over, so a profile sees the engine's cost on
   the emulation thread. Not a test (it never finishes). */
#define test_main s3_test_main
#include "s3.c"
#undef test_main

void test_main(void) {
    __asm__ volatile("fninit");
    /* The cache on (CR0.CD and NW clear), as a game runs: with it off the recompiler interprets everything */
    __asm__ volatile("movl %%cr0, %%eax\n\t"
                     "andl $0x9fffffff, %%eax\n\t"
                     "movl %%eax, %%cr0\n\t"
                     "wbinvd" ::: "eax", "memory");
    outw(0x3d4, 0x4838);
    outb(0x3d4, 0x30);
    const u8 id = inb(0x3d5);
    if ((id < 0x81) || (id == 0xff))
        return;
    for (;;)
        run_mode(16);
}
