/*
 * An x87 workload with no owner files (KairoX86#379): forever, the Mandelbrot set in double precision, one text
 * character a point on the 80x25 text screen, the view zooming a little each pass so every frame differs. clang
 * compiles it to FLD, FMUL, FADD, FSUB(P), FUCOM(PP), FNSTSW and FSTP. It needs nothing but an FPU and a text mode, so
 * it runs on the standard's 486 as well as the Pentium-class machines. Built by make_workload.py on core/test/gpu's
 * runtime, as mmxint is.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include "../gpu/runtime.h"

#define TEXT    ((volatile u16 *) 0xb8000)
#define MAXITER 48

static u32
escape(double cr, double ci)
{
    double zr = 0.0, zi = 0.0;
    u32    n  = 0;

    while (n < MAXITER) {
        const double zr2 = zr * zr;
        const double zi2 = zi * zi;

        if (zr2 + zi2 > 4.0)
            break;
        zi = 2.0 * zr * zi + ci;
        zr = zr2 - zi2 + cr;
        n++;
    }
    return n;
}

void
test_main(void)
{
    static const char shade[] = " .:-=+*#%@";
    double            scale   = 3.0;
    u32               pass    = 0;

    for (;;) {
        const double cx = -0.743643887 + 0.0000001 * (double) (pass & 7);
        const double cy = 0.131825904;

        for (u32 y = 0; y < 25; y++) {
            for (u32 x = 0; x < 80; x++) {
                const double cr = cx + ((double) x - 40.0) * scale / 80.0;
                const double ci = cy + ((double) y - 12.5) * scale / 25.0;
                const u32    n  = escape(cr, ci);

                TEXT[y * 80 + x] = (u16) (0x0700 | ((n + pass) & 0x70) << 8 | (u8) shade[n % 10]);
            }
        }
        scale *= 0.97;
        if (scale < 1e-6)
            scale = 3.0;
        pass++;
    }
}
