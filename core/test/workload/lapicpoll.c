/*
 * A local APIC register workload with no owner files (KairoX86#400): forever, a pass of local APIC register accesses
 * through its MMIO window at FEE00000h (the task priority written and read back, the timer's current count read, as a
 * driver polls them), an integer pass, and a 640x480 16 bpp linear framebuffer fill through VBE salted with what the
 * reads returned, so every frame shows them. It needs a processor with a local APIC and a board that maps it (an IOAPIC
 * board on the APIC path). Built by make_workload.py on core/test/gpu's runtime, as mmxint is.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "../gpu/runtime.h"

#define LAPIC(off) (*(volatile u32 *) (0xfee00000u + (off)))
#define LAPIC_TPR  0x080
#define LAPIC_SVR  0x0f0
#define LAPIC_LVTT 0x320
#define LAPIC_TICR 0x380
#define LAPIC_TCCR 0x390
#define LAPIC_TDCR 0x3e0

/* The APIC software-enabled, its timer periodic and masked (it counts, and interrupts nothing) */
static void
lapic_start(void)
{
    LAPIC(LAPIC_SVR)  = LAPIC(LAPIC_SVR) | 0x100;
    LAPIC(LAPIC_TDCR) = 0x0b; /* divide by 1 */
    LAPIC(LAPIC_LVTT) = 0x30000 | 0xf0;
    LAPIC(LAPIC_TICR) = 0x00100000;
}

static u32
lapic_pass(u32 seed, u32 count)
{
    u32 acc = seed;

    for (u32 i = 0; i < count; i++) {
        LAPIC(LAPIC_TPR) = (i << 4) & 0xf0;
        acc += LAPIC(LAPIC_TPR);
        acc = (acc << 3) ^ (acc >> 5) ^ LAPIC(LAPIC_TCCR);
    }
    LAPIC(LAPIC_TPR) = 0;
    return acc;
}

static u32
int_pass(u32 seed, u32 count)
{
    u32 a = seed, b = seed ^ 0x5a5a5a5au;

    for (u32 i = 0; i < count; i++) {
        a = (a << 7) | (a >> 25);
        b += a ^ i;
        a ^= b >> 3;
    }
    return a ^ b;
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
    lapic_start();
    u32 salt = 0;
    for (;;) {
        salt = lapic_pass(salt + 1, 20000);
        salt = int_pass(salt, 20000);
        fill(fb, pitch, salt);
    }
}
