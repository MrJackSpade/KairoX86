/* KairoX86#443's low-resolution 15 bpp workload: the card's first VESA mode at most 320 wide, 15 bits a pixel, with a
   linear frame buffer, refilled over and over (vbe.c's fill) with the cache on, so a profile sees the 15 bpp
   low-resolution scanlines (svga_render_15bpp_lowres). Not a test (it never finishes). */
#define test_main vbe_test_main
#include "vbe.c"
#undef test_main

void test_main(void) {
    /* The cache on (CR0.CD and NW clear), as a game runs: with it off the recompiler interprets everything */
    __asm__ volatile("movl %%cr0, %%eax\n\t"
                     "andl $0x9fffffff, %%eax\n\t"
                     "movl %%eax, %%cr0\n\t"
                     "wbinvd" ::: "eax", "memory");
    const int count = vbe_modes();
    for (int i = 0; i < count; i++) {
        const u16 mode = VBE_MODES[i];
        if (int10(0x4f01, 0, mode, 0, 0x6200, 0) != 0x004f)
            continue;
        const int lfb = (VBE_MODE->attributes & 0x81) == 0x81 && VBE_MODE->framebuffer;
        /* 5-5-5 (a BIOS lists it as 15 or 16 bits a pixel; the green mask's 5 bits tell it from 5-6-5) */
        if (!lfb || (VBE_MODE->model != 6) || ((VBE_MODE->bpp != 15) && (VBE_MODE->bpp != 16)) ||
            (VBE_MODE->green_size != 5) || (VBE_MODE->width > 320))
            continue;
        if (int10(0x4f02, mode | 0x4000, 0, 0, 0, 0) != 0x004f)
            continue;
        for (u32 salt = 0;; salt++)
            fill(VBE_MODE, salt);
    }
}
