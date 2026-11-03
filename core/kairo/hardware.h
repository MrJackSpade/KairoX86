/*
 * KairoX86's view of the hardware 86Box offers (Kairo#143), for the machine settings: core/kairo/hardware.c.
 *
 * Copyright 2026 MrJackSpade. GPL-2.0-or-later.
 */
#pragma once

/* The answer to [query] as JSON, valid until the next query; NULL for a query it does not know.
 * [rom_folder] is the player's 86Box ROM set, which says whose firmware is there ("available").
 *   "machines"      every machine: [{"id","name","type","available"}]
 *   "machine <id>"  what machine <id> takes: {"cpus":[{"family","name","speeds":[{"speed","multi","name"}]}],
 *                   "ram":{"min","max","step"} (KB), and its cards of each kind ("video", "sound",
 *                   "network", "hdc", "scsi", "fdc"): [{"id","name","available"}] */
const char *hardware_query(const char *rom_folder, const char *query);
