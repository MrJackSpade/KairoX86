/*
 * The firmware configuration device of KairoX86's free machine (kairo_pc.h): the interface SeaBIOS
 * reads QEMU's machine description through. A 16-bit write to port 510h selects an item by its
 * key and rewinds it; each byte read from port 511h is the item's next byte, 0 past its end. Key 0
 * is the signature "QEMU", key 1 the interface's version (1: this port interface, no DMA), key 19h
 * the directory of named files (a big-endian count, then for each file its big-endian size and
 * key, two reserved bytes and its 56-byte name); files take keys from 20h in the order added.
 *
 * Written from SeaBIOS's side of the interface (src/fw/paravirt.c), not from QEMU's device.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <86box/86box.h>
#include <86box/device.h>
#include <86box/io.h>
#include <86box/config.h>
#include <86box/plat.h>
#include <86box/plat_unused.h>
#include <86box/kairo_pc.h>

#define FW_CFG_PORT_SEL  0x0510
#define FW_CFG_PORT_DATA 0x0511

#define FW_CFG_SIGNATURE 0x0000
#define FW_CFG_ID        0x0001
#define FW_CFG_FILE_DIR  0x0019
#define FW_CFG_FILE_KEY  0x0020
#define FW_CFG_NAME_LEN  56

typedef struct fw_cfg_item_t {
    uint16_t key;
    uint8_t *data;
    uint32_t len;
} fw_cfg_item_t;

struct kairo_fw_cfg_t {
    fw_cfg_item_t *items;
    int            count;
    kairo_buf_t    dir;      /* key 19h, rebuilt as files are added */
    int            files;
    uint16_t       selected;
    uint32_t       offset;
    FILE          *log;      /* firmware.log, while [KairoX86] firmware_log is 1 */
};

void
kairo_buf_free(kairo_buf_t *b)
{
    free(b->data);
    b->data = NULL;
    b->len = b->cap = 0;
}

uint32_t
kairo_buf_put(kairo_buf_t *b, const void *data, uint32_t len)
{
    const uint32_t at = b->len;

    if ((b->len + len) > b->cap) {
        uint32_t cap = b->cap ? b->cap : 256;
        while (cap < (b->len + len))
            cap *= 2;
        uint8_t *grown = realloc(b->data, cap);
        if (grown == NULL)
            fatal("KairoX86 PC: out of memory building its firmware tables\n");
        b->data = grown;
        b->cap  = cap;
    }
    if (data != NULL)
        memcpy(b->data + b->len, data, len);
    else
        memset(b->data + b->len, 0, len);
    b->len += len;
    return at;
}

uint32_t
kairo_buf_zero(kairo_buf_t *b, uint32_t len)
{
    return kairo_buf_put(b, NULL, len);
}

uint32_t
kairo_buf_u8(kairo_buf_t *b, uint8_t v)
{
    return kairo_buf_put(b, &v, 1);
}

uint32_t
kairo_buf_u16(kairo_buf_t *b, uint16_t v)
{
    const uint8_t le[2] = { v & 0xff, v >> 8 };
    return kairo_buf_put(b, le, 2);
}

uint32_t
kairo_buf_u32(kairo_buf_t *b, uint32_t v)
{
    const uint8_t le[4] = { v & 0xff, (v >> 8) & 0xff, (v >> 16) & 0xff, v >> 24 };
    return kairo_buf_put(b, le, 4);
}

uint32_t
kairo_buf_u64(kairo_buf_t *b, uint64_t v)
{
    const uint32_t at = kairo_buf_u32(b, (uint32_t) v);
    kairo_buf_u32(b, (uint32_t) (v >> 32));
    return at;
}

void
kairo_buf_set_u16(kairo_buf_t *b, uint32_t at, uint16_t v)
{
    b->data[at]     = v & 0xff;
    b->data[at + 1] = v >> 8;
}

void
kairo_buf_set_u32(kairo_buf_t *b, uint32_t at, uint32_t v)
{
    b->data[at]     = v & 0xff;
    b->data[at + 1] = (v >> 8) & 0xff;
    b->data[at + 2] = (v >> 16) & 0xff;
    b->data[at + 3] = v >> 24;
}

void
kairo_buf_align(kairo_buf_t *b, uint32_t align)
{
    while (b->len % align)
        kairo_buf_u8(b, 0);
}

static fw_cfg_item_t *
fw_cfg_find(kairo_fw_cfg_t *cfg, uint16_t key)
{
    for (int i = 0; i < cfg->count; i++) {
        if (cfg->items[i].key == key)
            return &cfg->items[i];
    }
    return NULL;
}

void
kairo_fw_cfg_add(kairo_fw_cfg_t *cfg, uint16_t key, const void *data, uint32_t len)
{
    fw_cfg_item_t *item = fw_cfg_find(cfg, key);

    if (item == NULL) {
        fw_cfg_item_t *grown = realloc(cfg->items, (cfg->count + 1) * sizeof(fw_cfg_item_t));
        if (grown == NULL)
            fatal("KairoX86 PC: out of memory building its firmware tables\n");
        cfg->items = grown;
        item       = &cfg->items[cfg->count++];
        item->key  = key;
    } else
        free(item->data);
    item->data = malloc(len ? len : 1);
    if (item->data == NULL)
        fatal("KairoX86 PC: out of memory building its firmware tables\n");
    if (len)
        memcpy(item->data, data, len);
    item->len = len;
}

void
kairo_fw_cfg_add_file(kairo_fw_cfg_t *cfg, const char *name, const void *data, uint32_t len)
{
    const uint16_t key = FW_CFG_FILE_KEY + cfg->files;
    char           entry_name[FW_CFG_NAME_LEN] = { 0 };

    if (strlen(name) >= FW_CFG_NAME_LEN)
        fatal("KairoX86 PC: fw_cfg file name \"%s\" is too long\n", name);
    strcpy(entry_name, name);
    kairo_fw_cfg_add(cfg, key, data, len);

    /* The directory: a big-endian count, then each file's entry (all big-endian). */
    cfg->files++;
    if (cfg->dir.len == 0)
        kairo_buf_zero(&cfg->dir, 4);
    cfg->dir.data[0] = (cfg->files >> 24) & 0xff;
    cfg->dir.data[1] = (cfg->files >> 16) & 0xff;
    cfg->dir.data[2] = (cfg->files >> 8) & 0xff;
    cfg->dir.data[3] = cfg->files & 0xff;
    const uint8_t head[8] = { (len >> 24) & 0xff, (len >> 16) & 0xff, (len >> 8) & 0xff, len & 0xff,
                              key >> 8, key & 0xff, 0, 0 };
    kairo_buf_put(&cfg->dir, head, sizeof(head));
    kairo_buf_put(&cfg->dir, entry_name, FW_CFG_NAME_LEN);
    kairo_fw_cfg_add(cfg, FW_CFG_FILE_DIR, cfg->dir.data, cfg->dir.len);
}

static void
fw_cfg_select(UNUSED(uint16_t port), uint16_t val, void *priv)
{
    kairo_fw_cfg_t *cfg = (kairo_fw_cfg_t *) priv;

    cfg->selected = val;
    cfg->offset   = 0;
}

static uint8_t
fw_cfg_data(UNUSED(uint16_t port), void *priv)
{
    kairo_fw_cfg_t      *cfg  = (kairo_fw_cfg_t *) priv;
    const fw_cfg_item_t *item = fw_cfg_find(cfg, cfg->selected);

    if ((item == NULL) || (cfg->offset >= item->len))
        return 0x00;
    return item->data[cfg->offset++];
}

/* SeaBIOS's log (its debug port, 402h), when 86box.cfg's [KairoX86] firmware_log is 1: written to
   firmware.log in the machine's folder, on the PC and the device alike. */
static void
fw_cfg_debug_out(UNUSED(uint16_t port), uint8_t val, void *priv)
{
    kairo_fw_cfg_t *cfg = (kairo_fw_cfg_t *) priv;

    fputc(val, cfg->log);
    if (val == '\n')
        fflush(cfg->log);
}

/* Reads of the debug port give E9h, which SeaBIOS checks before it writes there. */
static uint8_t
fw_cfg_debug_in(UNUSED(uint16_t port), UNUSED(void *priv))
{
    return 0xe9;
}

static void *
fw_cfg_init(UNUSED(const device_t *info))
{
    kairo_fw_cfg_t *cfg = (kairo_fw_cfg_t *) calloc(1, sizeof(kairo_fw_cfg_t));
    const uint32_t  id  = 0x00000001; /* the port interface, no DMA */

    kairo_fw_cfg_add(cfg, FW_CFG_SIGNATURE, "QEMU", 4);
    kairo_fw_cfg_add(cfg, FW_CFG_ID, &id, sizeof(id));
    io_sethandler(FW_CFG_PORT_SEL, 1, NULL, NULL, NULL, NULL, fw_cfg_select, NULL, cfg);
    io_sethandler(FW_CFG_PORT_DATA, 1, fw_cfg_data, NULL, NULL, NULL, NULL, NULL, cfg);
    if (config_kairo_int("firmware_log", 0)) {
        char path[1024];
        snprintf(path, sizeof(path), "%sfirmware.log", usr_path);
        cfg->log = plat_fopen(path, "ab");
        if (cfg->log == NULL)
            fatal("KairoX86 PC: could not open %s for the firmware log\n", path);
        io_sethandler(0x0402, 1, fw_cfg_debug_in, NULL, NULL, fw_cfg_debug_out, NULL, NULL, cfg);
    }
    return cfg;
}

static void
fw_cfg_close(void *priv)
{
    kairo_fw_cfg_t *cfg = (kairo_fw_cfg_t *) priv;

    if (cfg->log != NULL)
        fclose(cfg->log);
    for (int i = 0; i < cfg->count; i++)
        free(cfg->items[i].data);
    free(cfg->items);
    kairo_buf_free(&cfg->dir);
    free(cfg);
}

const device_t kairo_fw_cfg_device = {
    .name          = "KairoX86 firmware configuration",
    .internal_name = "kairo_fw_cfg",
    .flags         = 0,
    .local         = 0,
    .init          = fw_cfg_init,
    .close         = fw_cfg_close,
    .reset         = NULL,
    .available     = NULL,
    .speed_changed = NULL,
    .force_redraw  = NULL,
    .config        = NULL
};
