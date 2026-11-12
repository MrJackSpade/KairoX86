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
#include <86box/midi.h>
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
    /* The MIDI out device the MPU-401 and the cards' MIDI ports play through (KairoX86#306): the synths, MT-32 and
       CM-32L with the ROM set's firmware, and FluidSynth; midi_out_device_init adds it as instance 0. */
    { "midi",    midi_out_device_get_internal_name, midi_out_device_getdevice, midi_out_device_available, 0,     0 },
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
        /* "bios": the device's firmware choice, whose files the "files" query lists (KairoX86#438) */
        put(",\"binary\":%s,\"bios\":%s,\"choices\":[", (type == CONFIG_BINARY) ? "true" : "false",
            (type == CONFIG_BIOS) ? "true" : "false");
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

/* The bus a card goes in (86Box's device flags): "agp", "pci", "vlb", "eisa", "mca", "isa16" (an AT's
   16-bit ISA), "isa", or "none" for one on no bus (the board's own, an add-on beside the video card) */
static const char *
card_bus(const device_t *device)
{
    if (device == NULL)
        return "none";
    if (device->flags & DEVICE_AGP)
        return "agp";
    if (device->flags & DEVICE_PCI)
        return "pci";
    if (device->flags & DEVICE_VLB)
        return "vlb";
    if (device->flags & DEVICE_EISA)
        return "eisa";
    if (device->flags & DEVICE_MCA)
        return "mca";
    if (device->flags & DEVICE_ISA16)
        return "isa16";
    if (device->flags & DEVICE_ISA)
        return "isa";
    return "none";
}

/* The cards of [kind] machine [m] takes: those 86Box's device_is_valid allows on its buses, and its
   onboard one ("internal") where the board has it. */
/* KairoX86's legacy displays (KairoX86#229): video cards with no PCI identity that KairoX86 puts on a PCI
   board when a Windows image's display is one Windows met by legacy detection at its ports (DOSBox-X's S3
   Trio64), as kairox86's Win9xMachine.LEGACY_DISPLAYS chooses them. 86Box runs them on any board; its bus
   check would leave them out of a PCI board's choices, and the machine's own card would not fit. */
static bool
legacy_display_fits(const struct kind *kind, const char *id, int m)
{
    return (kind->onboard == MACHINE_VIDEO) && !strcmp(id, "s3_trio64_vlb") && machine_has_bus(m, MACHINE_BUS_PCI);
}

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
        /* "external" is only the second monitor's "card on another output" (vid_table.c's device_external):
           as the video card it is no display at all. */
        if ((kind->onboard == MACHINE_VIDEO) && !strcmp(id, "external"))
            continue;
        /* A board whose video is its only video takes no other (86Box's config keeps it internal). */
        if ((kind->onboard == MACHINE_VIDEO) && machine_has_flags(m, MACHINE_VIDEO_ONLY) && strcmp(id, "internal"))
            continue;
        if (!device_is_valid(device, m) && !legacy_display_fits(kind, id, m))
            continue;
        put(first ? "{\"id\":" : ",{\"id\":");
        first = false;
        put_string(id);
        put(",\"name\":");
        put_string(device ? device->name : id);
        put(",\"bus\":");
        put_string(card_bus(device));
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
    /* "machine <id>": the board's own options, its firmware among them (KairoX86#208). 86Box keeps
       them in the machine device's section: its name, the device being instance 0. */
    if (!strcmp(kind_name, "machine")) {
        const int m = machine_named(id);
        if (m < 0)
            return false;
        const device_t *device = machine_get_device(m);
        put("{\"section\":");
        put_string(device ? device->name : id);
        put(",\"options\":");
        put_options(device);
        put("}");
        return true;
    }
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

/* Every card of every kind with its options, as "options" gives each (KairoX86#207): the text the
   card groups can show, for tools/device_strings.py to translate. */
static void
put_all_options(void)
{
    put("[");
    bool first = true;
    for (size_t k = 0; k < sizeof(kinds) / sizeof(kinds[0]); k++) {
        for (int card = 0; kinds[k].internal_name(card) && kinds[k].internal_name(card)[0]; card++) {
            put(first ? "{\"kind\":" : ",{\"kind\":");
            first = false;
            put_string(kinds[k].name);
            put(",\"id\":");
            put_string(kinds[k].internal_name(card));
            put(",\"options\":");
            put_options(kinds[k].device(card));
            put("}");
        }
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

/* The files a "files" query found (KairoX86#438): each once, with whether it is in the ROM set. */
#define FILES_MAX 64
static char probed[FILES_MAX][256]; /* copies: a device may name a file from a buffer of its own */
static bool probed_present[FILES_MAX];
static int  probed_count;

static void
add_file(const char *fn, bool present)
{
    for (int f = 0; f < probed_count; f++)
        if (!strcmp(probed[f], fn))
            return;
    if (probed_count == FILES_MAX)
        fatal("hardware: more than %d firmware files for one device\n", FILES_MAX);
    if (strlen(fn) >= sizeof(probed[0]))
        fatal("hardware: firmware file name too long: %s\n", fn);
    strcpy(probed[probed_count], fn);
    probed_present[probed_count] = present;
    probed_count++;
}

/* rom_present while a "files" query runs an availability check: every file the check asks about is
   noted and counted as there, so the check goes on to ask about the rest. */
static int
probe_file(const char *fn, int present)
{
    if (fn != NULL)
        add_file(fn, present);
    return 1;
}

/* [device]'s BIOS choices, when it picks its firmware from a list (its first option, as
   machine_device_available reads it), else NULL. */
static const device_config_t *
bios_config(const device_t *device)
{
    const device_config_t *config = device ? device->config : NULL;
    return ((config != NULL) && (config->type == CONFIG_BIOS)) ? config : NULL;
}

/* The files of BIOS choice [wanted] (its internal name), or of the default choice for NULL or a name it
   does not have, as device_get_bios_file falls back. */
static void
add_bios_files(const device_config_t *config, const char *wanted)
{
    const device_config_bios_t *chosen = NULL;
    for (const device_config_bios_t *bios = config->bios; bios->name && bios->internal_name && bios->files_no; bios++) {
        if ((wanted != NULL) && !strcmp(bios->internal_name, wanted))
            chosen = bios;
        if ((chosen == NULL) && !strcmp(bios->internal_name, config->default_string))
            chosen = bios;
    }
    if (chosen == NULL)
        fatal("hardware: no default BIOS among %s's choices\n", config->name);
    for (int8_t f = 0; f < chosen->files_no; f++)
        add_file(chosen->files[f], rom_present(chosen->files[f]));
}

/* The firmware files [kind]'s [id] reads ("machine" for a board), with BIOS choice [bios] (NULL for
   its default) where it has a list of them: [{"path","present"}], each path as the ROM set holds it
   (without 86Box's "roms/"). Found by 86Box's own availability check, so they are exactly the files
   whose absence makes it unavailable. */
static bool
put_files(const char *kind_name, const char *id, const char *bios)
{
    probed_count            = 0;
    const device_t *device  = NULL;
    int             m       = -1;
    int             card    = -1;
    const struct kind *kind = NULL;
    if (!strcmp(kind_name, "machine")) {
        if ((m = machine_named(id)) < 0)
            return false;
        device = machine_get_device(m);
    } else {
        for (size_t k = 0; (k < sizeof(kinds) / sizeof(kinds[0])) && (kind == NULL); k++)
            if (!strcmp(kinds[k].name, kind_name))
                kind = &kinds[k];
        if (kind == NULL)
            return false;
        for (int c = 0; kind->internal_name(c) && kind->internal_name(c)[0]; c++)
            if (!strcmp(kind->internal_name(c), id))
                card = c;
        if (card < 0)
            return false;
        device = kind->device(card);
    }
    const device_config_t *config = bios_config(device);
    if (config != NULL)
        add_bios_files(config, bios);
    else {
        rom_present_probe = probe_file;
        if (m >= 0)
            (void) machine_available(m);
        else
            (void) kind->available(card);
        rom_present_probe = NULL;
    }
    put("[");
    for (int f = 0; f < probed_count; f++) {
        put(f ? ",{\"path\":" : "{\"path\":");
        put_string(!strncmp(probed[f], "roms/", 5) ? (probed[f] + 5) : probed[f]);
        put(",\"present\":%s}", probed_present[f] ? "true" : "false");
    }
    put("]");
    return true;
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
    } else if (!strcmp(query, "all options"))
        put_all_options();
    else if (!strncmp(query, "files ", 6)) {
        /* "files <kind> <id>" or "files <kind> <id> <BIOS choice>" */
        char kind_name[32], id[128], bios[128];
        const int fields = sscanf(query + 6, "%31s %127s %127s", kind_name, id, bios);
        if ((fields < 2) || !put_files(kind_name, id, (fields == 3) ? bios : NULL))
            return NULL;
    } else
        return NULL;
    return text;
}
