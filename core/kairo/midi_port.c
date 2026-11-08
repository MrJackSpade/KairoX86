/*
 * KairoX86's MIDI out device "MIDI port" (KairoX86#305): the guest's MIDI output, every byte it writes
 * to the MPU-401 or a card's MIDI port, unchanged and in order, to a MIDI input port of the device
 * (the shared sender, cpp/kairo/midi_out.h, through the host's midi callback). 86Box hands it each byte
 * as the guest writes it (midi_device_t's write, ahead of 86Box's own parser, which would expand
 * running status and drop some MT-32 SysEx): it only cuts the stream into whole messages, which the
 * device's MIDI port is sent one at a time. A status byte starts a message and its data bytes end it;
 * data bytes after a complete message (running status) are a message of their own, as written; a
 * SysEx runs from F0 to F7, or to the next status byte, which then starts its own; real-time bytes
 * (F8 to FF) go at once, alone, wherever they come.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#include <86box/86box.h>
#include <86box/device.h>
#include <86box/midi.h>
#include <86box/plat_unused.h>

#include "kairo_host.h"

/* A SysEx longer than this goes in pieces of this size: the shared sender's longest message is far
   longer, and a guest's SysEx is rarely above a few kilobytes. */
#define LONGEST 65536

static struct {
    uint8_t message[LONGEST];
    size_t  length;
    /* The data bytes a message of the running status takes; 0 when there is none to run (none yet,
       or a system message, which ends running status) */
    size_t  data_bytes;
    bool    sysex;
} port;

static void
flush(void)
{
    if (port.length != 0)
        kairo_host_midi(port.message, port.length);
    port.length = 0;
}

static void
put(uint8_t val)
{
    if (port.length == LONGEST)
        flush();
    port.message[port.length++] = val;
}

static int
midi_port_write(uint8_t val)
{
    if (val >= 0xf8) {
        /* Real time: alone, now, inside any message */
        kairo_host_midi(&val, 1);
    } else if (port.sysex && (val == 0xf7)) {
        /* The SysEx's end */
        put(val);
        flush();
        port.sysex = false;
    } else if (val & 0x80) {
        /* A status byte ends what was open (a SysEx without its F7 too) and starts its own message */
        flush();
        port.sysex = (val == 0xf0);
        put(val);
        /* Channel messages run on; system ones (F0 to F7) end running status */
        const size_t data_bytes = (MIDI_evt_len[val] > 0) ? MIDI_evt_len[val] - 1 : 0;
        port.data_bytes         = (val < 0xf0) ? data_bytes : 0;
        if (!port.sysex && (data_bytes == 0))
            flush();
    } else if (port.sysex) {
        put(val);
    } else {
        /* A data byte: the open message's, or under running status the first of a message without its
           status byte, as the guest wrote it; one with nothing to belong to goes alone */
        put(val);
        const size_t data = (port.message[0] & 0x80) ? port.length - 1 : port.length;
        const size_t takes = (port.message[0] & 0x80) ? ((MIDI_evt_len[port.message[0]] > 0) ? MIDI_evt_len[port.message[0]] - 1 : 0)
                                                      : port.data_bytes;
        if (data >= takes)
            flush();
    }
    return 1;
}

/* Messages 86Box makes itself (MIDI in passed through: its real-time bytes), whole. */
static void
midi_port_msg(uint8_t *msg)
{
    const size_t length = MIDI_evt_len[msg[0]] ? MIDI_evt_len[msg[0]] : 1;
    kairo_host_midi(msg, length);
}

static void
midi_port_sysex(uint8_t *sysex, unsigned int len)
{
    kairo_host_midi(sysex, len);
}

static void *
midi_port_init(UNUSED(const device_t *info))
{
    midi_device_t *dev = calloc(1, sizeof(midi_device_t));
    memset(&port, 0, sizeof(port));
    dev->play_msg   = midi_port_msg;
    dev->play_sysex = midi_port_sysex;
    dev->write      = midi_port_write;
    midi_out_init(dev);
    return dev;
}

/* midi_out_close frees the midi_device_t too, as for 86Box's own MIDI out devices. */
static void
midi_port_close(UNUSED(void *priv))
{
    flush();
    midi_out_close();
}

const device_t kairo_midi_port_device = {
    .name          = "MIDI port",
    .internal_name = "kairo_midi_port",
    .flags         = 0,
    .local         = 0,
    .init          = midi_port_init,
    .close         = midi_port_close,
    .reset         = NULL,
    .available     = NULL,
    .speed_changed = NULL,
    .force_redraw  = NULL,
    .config        = NULL
};
