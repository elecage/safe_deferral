/*
 * STM32-03 (continued): Heartbeat / Health Status Reporter
 *
 * Emits a JSON heartbeat line to UART every SD_HEARTBEAT_INTERVAL_MS.
 * Also exposes sd_status_get_readiness() for the RPi preflight check.
 *
 * JSON format (single line, newline terminated):
 *   {"type":"heartbeat","node_id":"...","fw":"...","session":{"id":...,"state":"...","captures":...},"readiness":"READY","drops":...}
 */

#include "sd_measure.h"
#include "stm32h7xx_hal.h"
#include <stdio.h>
#include <string.h>

extern UART_HandleTypeDef huart3;

#define SD_HEARTBEAT_INTERVAL_MS  5000

static uint32_t s_last_hb_ms = 0;

/* ── Init ───────────────────────────────────────────────────────────────── */

void sd_status_init(void)
{
    s_last_hb_ms = 0;
}

/* ── Tick (called from main loop, ~1 ms cadence) ─────────────────────────  */

void sd_status_tick(void)
{
    uint32_t now = HAL_GetTick();
    if ((now - s_last_hb_ms) < SD_HEARTBEAT_INTERVAL_MS) return;
    s_last_hb_ms = now;

    const char *states[] = {"IDLE", "ARMED", "RUNNING", "DONE"};
    const char *rl[] = {"READY", "DEGRADED", "BLOCKED", "UNKNOWN"};

    char hb[256];
    int len = snprintf(hb, sizeof(hb),
        "{\"type\":\"heartbeat\","
        "\"node_id\":\"%s\","
        "\"fw\":\"%s\","
        "\"uptime_ms\":%lu,"
        "\"session\":{\"id\":%lu,\"state\":\"%s\",\"captures\":%lu},"
        "\"readiness\":\"%s\","
        "\"timer_ok\":%s,"
        "\"export_ok\":%s"
        "}\r\n",
        SD_NODE_ID,
        SD_FW_VERSION,
        now,
        g_session.session_id,
        states[g_session.state < 4 ? g_session.state : 3],
        g_session.capture_count,
        rl[g_readiness.level < 4 ? g_readiness.level : 3],
        g_readiness.timer_ok  ? "true" : "false",
        g_readiness.export_ok ? "true" : "false");

    if (len > 0) {
        HAL_UART_Transmit(&huart3, (uint8_t *)hb, len, 100);
    }
}
