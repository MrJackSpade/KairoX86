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
#include <86box/gameport.h>
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
    uintptr_t onboard; /* the machine flag that says the board has one ("internal"); ONBOARD_ALWAYS for every board */
    int instance;      /* the instance 86Box adds the first card as: its options' section is "<name> #<n>" (device.c) */
};

/* A mouse is there whatever the ROM set: 86Box's mice need no firmware of their own. */
static int
mouse_available(int mouse)
{
    const device_t *device = mouse_get_device(mouse);
    return (device == NULL) || device_available(device);
}

static const char *
mouse_internal_name(int mouse)
{
    return mouse_get_internal_name(mouse);
}

static const device_t *
mouse_device(int mouse)
{
    return mouse_get_device(mouse);
}

/* 86Box runs every board with its own floppy controller ("internal") when 86box.cfg names none
   (config.c), and each board's init adds it then, whether or not the board has MACHINE_FDC
   (KairoX86#204): "none" is a board without one. */
#define ONBOARD_ALWAYS UINTPTR_MAX

static const struct kind kinds[] = {
    /* The instances are those 86Box adds the first card of each kind with: video_reset, sound_card_init,
       network_init, hdc_init and scsi_card_init add slot i as i + 1; fdc_card_init and mouse_reset add
       theirs as 0. */
    { "video",   video_get_internal_name,         video_card_getdevice,   video_card_available,   MACHINE_VIDEO, 1 },
    { "sound",   sound_card_get_internal_name,    sound_card_getdevice,   sound_card_available,   MACHINE_SOUND, 1 },
    { "network", network_card_get_internal_name,  network_card_getdevice, network_card_available, MACHINE_NIC,   1 },
    { "hdc",     hdc_get_internal_name,           hdc_get_device,         hdc_available,          MACHINE_HDC,   1 },
    { "scsi",    scsi_card_get_internal_name,     scsi_card_getdevice,    scsi_card_available,    0,             1 },
    { "fdc",     fdc_card_get_internal_name,      fdc_card_getdevice,     fdc_card_available,     ONBOARD_ALWAYS, 0 },
    { "mouse",   mouse_internal_name,             mouse_device,           mouse_available,        MACHINE_MOUSE, 0 },
};

/* Whether every file of a BIOS choice is in the ROM set, as machine_device_available counts them. */
static bool
bios_present(const device_config_bios_t *bios)
{
    if (bios->files_no == -1)
        return true;
    for (int8_t f = 0; f < bios->files_no; f++)
        if (!rom_present(bios->files[f]))
            return false;
    return true;
}

/* A choice of an option: its value as 86box.cfg keeps it, its name, and whether it can be picked. */
static void
put_choice(bool first, const char *value, const char *label, bool available)
{
    put(first ? "{\"value\":" : ",{\"value\":");
    put_string(value);
    put(",\"label\":");
    put_string(label);
    put(",\"available\":%s}", available ? "true" : "false");
}

/* The options of [device] the settings can offer (KairoX86#201), as 86Box's own device_config lists
   them: each with its key, its description, its default and its choices, values written as 86box.cfg
   keeps them (device.c's device_get_config_*: integers in decimal, hex16 as %04X, hex20 as %05X, a
   BIOS by its internal name). Options without a list of values (text, file names, serial ports, MIDI
   devices, MAC addresses, plain numbers) are the player's 86box.cfg's alone and are not listed. */
static void
put_options(const device_t *device)
{
    put("[");
    bool first_option = true;
    for (const device_config_t *config = device ? device->config : NULL; config && (config->type != CONFIG_END); config++) {
        const int type  = config->type & ~CONFIG_DEP;
        char      value[32];
        bool      first = true;
        if ((type != CONFIG_BINARY) && (type != CONFIG_SELECTION) && (type != CONFIG_SPINNER) && (type != CONFIG_MEMORY)
            && (type != CONFIG_HEX16) && (type != CONFIG_HEX20) && (type != CONFIG_BIOS))
            continue;
        put(first_option ? "{\"key\":" : ",{\"key\":");
        first_option = false;
        put_string(config->name);
        put(",\"label\":");
        put_string(config->description);
        put(",\"default\":");
        if (type == CONFIG_BIOS)
            put_string(config->default_string);
        else {
            snprintf(value, sizeof(value), (type == CONFIG_HEX16) ? "%04X" : (type == CONFIG_HEX20) ? "%05X" : "%i",
                     config->default_int);
            put_string(value);
        }
        put(",\"binary\":%s,\"choices\":[", (type == CONFIG_BINARY) ? "true" : "false");
        if (type == CONFIG_BINARY) {
            put_choice(true, "0", "", true);
            put_choice(false, "1", "", true);
        } else if (type == CONFIG_SPINNER) {
            const int step = (config->spinner.step > 0) ? config->spinner.step : 1;
            for (int v = config->spinner.min; v <= config->spinner.max; v += step) {
                snprintf(value, sizeof(value), "%i", v);
                put_choice(first, value, value, true);
                first = false;
            }
        } else if (type == CONFIG_BIOS) {
            for (const device_config_bios_t *bios = config->bios; bios->name && bios->internal_name && bios->files_no; bios++) {
                put_choice(first, bios->internal_name, bios->name, bios_present(bios));
                first = false;
            }
        } else {
            for (const device_config_selection_t *choice = config->selection; choice->description && choice->description[0]; choice++) {
                snprintf(value, sizeof(value), (type == CONFIG_HEX16) ? "%04X" : (type == CONFIG_HEX20) ? "%05X" : "%i",
                         choice->value);
                put_choice(first, value, choice->description, true);
                first = false;
            }
        }
        put("]}");
    }
    put("]");
}

/* The game port's joysticks: every one 86Box has, for any machine (the game port is a card or the board's). */
static void
put_joysticks(void)
{
    put("[");
    for (int js = 0; joystick_get_internal_name(js)[0]; js++) {
        put(js ? ",{\"id\":" : "{\"id\":");
        put_string(joystick_get_internal_name(js));
        put(",\"name\":");
        put_string(joystick_get_name(js));
        put(",\"available\":true}");
    }
    put("]");
}

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
        if (!strcmp(id, "internal") && kind->onboard != ONBOARD_ALWAYS && !(kind->onboard && machine_has_flags(m, kind->onboard)))
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

/* Card [id] of [kind]'s options (KairoX86#201): the section of 86box.cfg 86Box reads them from
   (device.c: the device's name, " #<instance>" when the instance is not 0) and the options
   themselves. Its own query, for the chosen cards only: every card's options in the machine
   query made it too large to read on the app's main thread (KairoX86#202). */
static bool
put_card_options(const char *kind_name, const char *id)
{
    for (size_t k = 0; k < sizeof(kinds) / sizeof(kinds[0]); k++) {
        if (strcmp(kinds[k].name, kind_name))
            continue;
        for (int card = 0; kinds[k].internal_name(card) && kinds[k].internal_name(card)[0]; card++) {
            if (strcmp(kinds[k].internal_name(card), id))
                continue;
            const device_t *device = kinds[k].device(card);
            char            section[256];
            if (device && kinds[k].instance)
                snprintf(section, sizeof(section), "%s #%i", device->name, kinds[k].instance);
            else
                snprintf(section, sizeof(section), "%s", device ? device->name : id);
            put("{\"section\":");
            put_string(section);
            put(",\"options\":");
            put_options(device);
            put("}");
            return true;
        }
        return false;
    }
    return false;
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

/* The memory a machine has when its 86box.cfg names none (KairoX86#62): the most it takes up to a
   cap. Up to the 486 boards the cap is 16 MB, as on DOSBox: software in 286 protected mode (Windows
   3.0's standard mode, 16-bit DOS extenders) can crash with more than 15 MB of extended memory. From
   the Pentium boards (Socket 4) on, it is 64 MB, for the Windows 9x games they run. A machine
   whose least is above the cap keeps its least. */
#define DOS_RAM_CAP     (16 * 1024)
#define WINDOWS_RAM_CAP (64 * 1024)

uint32_t
hardware_default_ram(int m)
{
    const machine_memory_t *ram = &machines[m].ram;
    const uint32_t          cap = ((machines[m].type >= MACHINE_TYPE_SOCKET4) && (machines[m].type < MACHINE_TYPE_MISC))
        ? WINDOWS_RAM_CAP : DOS_RAM_CAP;
    /* The sizes 86Box offers: from the least by the step to the most (a step of 0: the two ends). */
    const uint32_t step = (ram->step > 0) ? (uint32_t) ram->step : (ram->max - ram->min);
    uint32_t       size = ram->min;

    while ((step > 0) && ((size + step) <= ram->max) && ((size + step) <= cap))
        size += step;
    return size;
}

/* What machine [m] takes: its processors (each family's eligible speeds, by 86Box's cpu_speed and
   cpu_multi), its memory range in KB with its default (hardware_default_ram), and its cards of every
   kind. */
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
    put("],\"ram\":{\"min\":%u,\"max\":%u,\"step\":%d,\"default\":%u}", machines[m].ram.min, machines[m].ram.max,
        machines[m].ram.step, hardware_default_ram(m));
    for (size_t k = 0; k < sizeof(kinds) / sizeof(kinds[0]); k++) {
        put(",");
        put_string(kinds[k].name);
        put(":");
        put_cards(&kinds[k], m);
    }
    put(",\"joystick\":");
    put_joysticks();
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
    } else if (!strncmp(query, "options ", 8)) {
        /* "options <kind> <card id>" */
        const char *kind = query + 8;
        const char *id   = strchr(kind, ' ');
        if (id == NULL)
            return NULL;
        char kind_name[32];
        snprintf(kind_name, sizeof(kind_name), "%.*s", (int) (id - kind), kind);
        if (!put_card_options(kind_name, id + 1))
            return NULL;
    } else
        return NULL;
    return text;
}
