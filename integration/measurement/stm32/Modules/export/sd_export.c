/*
 * STM32-04: Measurement Export Path
 *
 * Drains the capture ring buffer and emits CSV rows over UART3.
 *
 * Output format (one row per capture):
 *   DATA,<session_id>,<seq>,<channel>,<raw_ticks>,<overflow_count>,<abs_us>,<quality>
 *
 * Where:
 *   abs_us = overflow_count * 2^32 + raw_ticks  (µs since TIM2 start)
 *   quality: 0=OK, 1=overflow-adjusted, 2=suspect
 *
 * Session metadata row (emitted on session stop):
 *   META,<session_id>,<experiment_id>,<start_tick>,<stop_tick>,<capture_count>
 *
 * Authority boundary:
 *   - No direct write to operational audit log as authority.
 *   - No hidden data transformation that prevents reproducibility.
 *   - Raw ticks are emitted as-is; host performs delta calculations.
 */

#include "sd_measure.h"
#include "stm32h7xx_hal.h"
#include <stdio.h>
#include <string.h>

extern UART_HandleTypeDef huart3;

/* Channel label strings — match sd_channel_t order */
static const char *const s_ch_label[SD_CHANNEL_COUNT] = {
    "CH_A", "CH_B", "CH_C", "CH_D"
};

/* ── Init ───────────────────────────────────────────────────────────────── */

void sd_export_init(void)
{
    /* Emit CSV header once on boot */
    const char *hdr =
        "# HEADER: type,session_id,seq,channel,raw_ticks,overflow_count,abs_us,quality\r\n";
    HAL_UART_Transmit(&huart3, (uint8_t *)hdr, strlen(hdr), 50);
}

/* ── Flush (called from main loop) ─────────────────────────────────────── */

void sd_export_flush(void)
{
    sd_capture_t rec;
    char row[128];

    while (sd_capture_pop(&rec)) {
        /* Compute absolute µs (64-bit arithmetic to handle overflow wrap) */
        uint64_t abs_us = (uint64_t)rec.overflow_count * 0x100000000ULL
                        + (uint64_t)rec.raw_ticks;

        int len = snprintf(row, sizeof(row),
            "DATA,%lu,%lu,%s,%lu,%lu,%llu,%u\r\n",
            g_session.session_id,
            rec.seq,
            s_ch_label[rec.channel < SD_CHANNEL_COUNT ? rec.channel : 3],
            rec.raw_ticks,
            rec.overflow_count,
            (unsigned long long)abs_us,
            rec.quality);

        if (len > 0 && len < (int)sizeof(row)) {
            HAL_UART_Transmit(&huart3, (uint8_t *)row, len, 20);
        }

        /* Update session capture count */
        if (g_session.state == SD_SESSION_RUNNING) {
            g_session.capture_count++;
        }
    }
}

/* ── Export session metadata ────────────────────────────────────────────── */

void sd_export_session_meta(void)
{
    char meta[192];
    int len = snprintf(meta, sizeof(meta),
        "META,%lu,%s,%lu,%lu,%lu\r\n",
        g_session.session_id,
        g_session.experiment_id,
        g_session.start_tick,
        g_session.stop_tick,
        g_session.capture_count);
    if (len > 0) {
        HAL_UART_Transmit(&huart3, (uint8_t *)meta, len, 50);
    }
}
