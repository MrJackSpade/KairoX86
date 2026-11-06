/*
 * The GPU backend's own parts (gpu.c, gpu_scanout.c; KairoX86#232): each kernel family's close, which
 * kairo_gpu_close calls before the device goes.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_INTERNAL_H
#define KAIRO_GPU_INTERNAL_H

void kairo_gpu_scanout_close(void);

#endif
