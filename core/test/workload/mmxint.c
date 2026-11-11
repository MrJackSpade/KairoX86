/*
 * A compiled Pentium-class CPU workload with no owner files (KairoX86#417): forever, an MMX pass over a 64 KB buffer
 * (PADDW, PMULLW, PACKUSWB, PADDUSB, PSRLW), an integer pass of shifts and rotates whose flags are read (RCL, ADC,
 * SHLD, ROR, SBB, a carry branch: the lazy-flag rebuild's path), and a 640x480 16 bpp linear framebuffer fill through
 * VBE, its pattern salted with the pass so every frame differs. Built by make_workload.py on core/test/gpu's runtime.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "../gpu/runtime.h"

/* 64 KB of data at 2 MB (unreal mode reaches it) */
#define BUF        ((u32 *) 0x200000)
#define BUF_QWORDS (65536 / 8)

static void
mmx_pass(u32 *buf, u32 pairs)
{
    __asm__ volatile("movl $0x00030001, %%eax\n\t"
                     "movd %%eax, %%mm7\n\t"
                     "punpckldq %%mm7, %%mm7\n\t"
                     "1:\n\t"
                     "movq (%0), %%mm0\n\t"
                     "movq 8(%0), %%mm1\n\t"
                     "paddw %%mm7, %%mm0\n\t"
                     "pmullw %%mm7, %%mm1\n\t"
                     "movq %%mm0, %%mm2\n\t"
                     "packuswb %%mm1, %%mm2\n\t"
                     "paddusb %%mm2, %%mm0\n\t"
                     "psrlw $1, %%mm1\n\t"
                     "movq %%mm0, (%0)\n\t"
                     "movq %%mm1, 8(%0)\n\t"
                     "addl $16, %0\n\t"
                     "decl %1\n\t"
                     "jnz 1b\n\t"
                     "emms"
                     : "+r"(buf), "+r"(pairs)
                     :
                     : "eax", "memory", "cc");
}

/* The flags each instruction leaves are read by the next: a rotate through carry, add with carry, a double shift,
   subtract with borrow, a branch on carry */
static u32
int_pass(u32 seed, u32 count)
{
    u32 a = seed, b = seed ^ 0x5a5a5a5au, c = 0, d = 0x13579bdfu, e = 0;

    __asm__ volatile("1:\n\t"
                     "roll $3, %0\n\t"
                     "rcll $1, %1\n\t"
                     "adcl %0, %2\n\t"
                     "shldl $5, %1, %0\n\t"
                     "rorl $7, %1\n\t"
                     "sbbl %2, %3\n\t"
                     "jnc 2f\n\t"
                     "incl %4\n\t"
                     "2:\n\t"
                     "shrl $1, %3\n\t"
                     "adcl $0, %4\n\t"
                     "decl %5\n\t"
                     "jnz 1b"
                     : "+r"(a), "+r"(b), "+r"(c), "+r"(d), "+r"(e), "+r"(count)
                     :
                     : "cc");
    return a ^ b ^ c ^ d ^ e;
}

static void
fill(u16 *fb, u16 pitch, u32 salt)
{
    for (u32 y = 0; y < 480; y++) {
        u32 *line = (u32 *) ((u8 *) fb + y * pitch);
        for (u32 x = 0; x < 320; x++)
            line[x] = pattern(x, y, salt);
    }
}

void
test_main(void)
{
    if (vbe_modes() < 0)
        return;
    const u16 mode = vbe_find(640, 480, 16);
    if (!mode)
        return;
    u16 *const fb    = (u16 *) VBE_MODE->framebuffer;
    const u16  pitch = VBE_MODE->pitch;
    if (int10(0x4f02, mode | 0x4000, 0, 0, 0, 0) != 0x004f)
        return;
    for (u32 i = 0; i < BUF_QWORDS * 2; i++)
        BUF[i] = pattern(i, 0, 1);
    u32 salt = 0;
    for (;;) {
        mmx_pass(BUF, BUF_QWORDS / 2);
        salt = int_pass(salt + 1, 20000);
        fill(fb, pitch, salt);
    }
}
