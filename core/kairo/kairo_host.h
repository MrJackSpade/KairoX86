/*
 * What KairoX86's own devices (core/kairo/) hand the host, through the KairoX86Host the frontend
 * started with (frontend.c).
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#ifndef KAIRO_HOST_H
#define KAIRO_HOST_H

#include <stddef.h>
#include <stdint.h>

/* One whole MIDI message of the guest's, as it wrote it, to the host's MIDI port (KairoX86#305). */
void kairo_host_midi(const uint8_t *message, size_t length);

#endif
