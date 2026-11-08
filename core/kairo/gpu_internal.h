/*
 * The GPU backend's own parts (gpu.c, gpu_scanout.c, gpu_voodoo.c, gpu_virge.c, gpu_mach64.c, gpu_powervr.c; KairoX86#232): each kernel family's close, which
 * kairo_gpu_close calls before the device goes.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_GPU_INTERNAL_H
#define KAIRO_GPU_INTERNAL_H

void kairo_gpu_frames_close(void); /* gpu_frame.c, KairoX86#330 */
void kairo_gpu_scanout_close(void);
void kairo_gpu_voodoo_close(void);
void kairo_gpu_virge_close(void);
void kairo_gpu_mach64_close(void);
void kairo_gpu_powervr_close(void);

#endif
