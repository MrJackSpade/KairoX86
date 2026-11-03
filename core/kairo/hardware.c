/*
 * KairoX86's view of the hardware 86Box offers (Kairo#143): its machines, and for each machine the
 * processors, memory and cards 86Box itself lets it take, as JSON, so the app's machine settings
 * offer exactly 86Box's choices and never a hand-kept copy of them. Every answer comes from 86Box's
 * own tables and eligibility functions, the ones its settings dialogs use.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <86box/86box.h>
#include <86box/device.h>
#include <86box/mem.h>
#include <86box/thread.h>
#include <86box/timer.h>
#include <86box/machine.h>
#include <86box/rom.h>
#include <86box/video.h>
#include <86box/sound.h>
#include <86box/network.h>
#include <86box/hdc.h>
#include <86box/scsi.h>
#include <86box/fdc_ext.h>
#include <86box/mouse.h>
#include "cpu.h"

#include "hardware.h"

/* The answer being built, and the last one given (valid until the next query). */
static char  *text;
static size_t length, room;

static void
put(const char *format, ...)
{
    va_list args;
    for (;;) {
        va_start(args, format);
        const int wrote = vsnprintf(text + length, room - length, format, args);
        va_end(args);
        if (wrote < 0)
            fatal("hardware: could not format its answer\n");
        if ((length + (size_t) wrote) < room) {
            length += (size_t) wrote;
            return;
        }
        room = (room + (size_t) wrote + 1) * 2;
        char *grown = realloc(text, room);
        if (grown == NULL)
            fatal("hardware: no memory for its answer\n");
        text = grown;
    }
}

/* A JSON string. */
static void
put_string(const char *value)
{
    put("\"");
    for (const unsigned char *c = (const unsigned char *) (value ? value : ""); *c; c++) {
        if ((*c == '"') || (*c == '\\'))
            put("\\%c", *c);
        else if (*c < 0x20)
            put("\\u%04x", *c);
        else
            put("%c", *c);
    }
    put("\"");
}

static int
machine_named(const char *id)
{
    for (int m = 0; m < machine_count(); m++)
        if (!strcmp(machine_get_internal_name_ex(m), id))
            return m;
    return -1;
}

/* A kind of card, as 86Box lists it: its internal names, devices and whether its firmware is there. */
struct kind {
    const char *name;
    const char *(*internal_name)(int card);
    const device_t *(*device)(int card);
    int (*available)(int card);
    uintptr_t onboard; /* the machine flag that says the board has one ("internal") */
};

static const struct kind kinds[] = {
    { "video",   video_get_internal_name,         video_card_getdevice,   video_card_available,   MACHINE_VIDEO },
    { "sound",   sound_card_get_internal_name,    sound_card_getdevice,   sound_card_available,   MACHINE_SOUND },
    { "network", network_card_get_internal_name,  network_card_getdevice, network_card_available, MACHINE_NIC },
    { "hdc",     hdc_get_internal_name,           hdc_get_device,         hdc_available,          MACHINE_HDC },
    { "scsi",    scsi_card_get_internal_name,     scsi_card_getdevice,    scsi_card_available,    0 },
    { "fdc",     fdc_card_get_internal_name,      fdc_card_getdevice,     fdc_card_available,     MACHINE_FDC },
};

/* The cards of [kind] machine [m] takes: those 86Box's device_is_valid allows on its buses, and its
   onboard one ("internal") where the board has it. */
static void
put_cards(const struct kind *kind, int m)
{
    put("[");
    bool first = true;
    for (int card = 0; kind->internal_name(card) && kind->internal_name(card)[0]; card++) {
        const char     *id     = kind->internal_name(card);
        const device_t *device = kind->device(card);
        if (!strcmp(id, "internal") && !(kind->onboard && machine_has_flags(m, kind->onboard)))
            continue;
        /* A board whose video is its only video takes no other (86Box's config keeps it internal). */
        if ((kind->onboard == MACHINE_VIDEO) && machine_has_flags(m, MACHINE_VIDEO_ONLY) && strcmp(id, "internal"))
            continue;
        if (!device_is_valid(device, m))
            continue;
        put(first ? "{\"id\":" : ",{\"id\":");
        first = false;
        put_string(id);
        put(",\"name\":");
        put_string(device ? device->name : id);
        put(",\"available\":%s}", kind->available(card) ? "true" : "false");
    }
    put("]");
}

/* Every machine: its internal name, name, type and whether its firmware is there. */
static void
put_machines(void)
{
    put("[");
    for (int m = 0; m < machine_count(); m++) {
        put(m ? ",{\"id\":" : "{\"id\":");
        put_string(machine_get_internal_name_ex(m));
        put(",\"name\":");
        put_string(machines[m].name);
        const char *type = "";
        /* machine_types has one entry for each type, with no end marker. */
        for (int t = 0; t < MACHINE_TYPE_MAX; t++)
            if ((uint32_t) machine_types[t].id == machines[m].type)
                type = machine_types[t].name;
        put(",\"type\":");
        put_string(type);
        put(",\"available\":%s}", machine_available(m) ? "true" : "false");
    }
    put("]");
}

/* What machine [m] takes: its processors (each family's eligible speeds, by 86Box's cpu_speed and
   cpu_multi), its memory range in KB, and its cards of every kind. */
static void
put_machine(int m)
{
    put("{\"cpus\":[");
    bool first_family = true;
    for (int f = 0; cpu_families[f].package; f++) {
        const cpu_family_t *family = &cpu_families[f];
        if (!cpu_family_is_eligible(family, m))
            continue;
        put(first_family ? "{\"family\":" : ",{\"family\":");
        first_family = false;
        put_string(family->internal_name);
        put(",\"name\":");
        char name[128];
        snprintf(name, sizeof(name), "%s %s", family->manufacturer, family->name);
        put_string(name);
        put(",\"speeds\":[");
        bool first_speed = true;
        for (int c = 0; family->cpus[c].cpu_type; c++) {
            if (!cpu_is_eligible(family, c, m))
                continue;
            put(first_speed ? "{\"speed\":%u,\"multi\":%g,\"name\":" : ",{\"speed\":%u,\"multi\":%g,\"name\":",
                family->cpus[c].rspeed, family->cpus[c].multi);
            first_speed = false;
            put_string(family->cpus[c].name);
            put("}");
        }
        put("]}");
    }
    put("],\"ram\":{\"min\":%u,\"max\":%u,\"step\":%d}", machines[m].ram.min, machines[m].ram.max, machines[m].ram.step);
    for (size_t k = 0; k < sizeof(kinds) / sizeof(kinds[0]); k++) {
        put(",");
        put_string(kinds[k].name);
        put(":");
        put_cards(&kinds[k], m);
    }
    put("}");
}

const char *
hardware_query(const char *rom_folder, const char *query)
{
    static bool roms_added;
    if (!roms_added) {
        rom_add_path(rom_folder);
        roms_added = true;
    }
    length = 0;
    if (room == 0) {
        room = 4096;
        text = malloc(room);
        if (text == NULL)
            fatal("hardware: no memory for its answer\n");
    }
    text[0] = 0;
    if (!strcmp(query, "machines"))
        put_machines();
    else if (!strncmp(query, "machine ", 8)) {
        const int m = machine_named(query + 8);
        if (m < 0)
            return NULL;
        put_machine(m);
    } else
        return NULL;
    return text;
}
