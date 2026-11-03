/* POC: SLiRP is not built. */
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <wchar.h>
#include <stdbool.h>
#include <86box/86box.h>
#include <86box/device.h>
#include <86box/thread.h>
#include <86box/timer.h>
#include <86box/network.h>
#include <86box/plat_unused.h>

static void *
slirp_stub_init(UNUSED(const netcard_t *card), UNUSED(const uint8_t *mac_addr), UNUSED(void *priv), UNUSED(char *netdrv_errbuf))
{
    fprintf(stderr, "SLiRP networking is not built into this POC.\n");
    abort();
}

const netdrv_t net_slirp_drv = { NULL, slirp_stub_init, NULL, NULL };
int slirp_card_num = 2;
