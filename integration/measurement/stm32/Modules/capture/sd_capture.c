/*
 * STM32-02: Timing Capture Module
 *
 * Ring-buffer based edge timestamp collection.
 * Records raw TIM2 ticks + overflow count per channel.
 *
 * Handles:
 *   - Missed edge (ring full): increments drop counter, sets quality=suspect
 *   - Duplicate edge: detected via same tick value on same channel
 *   - Overflow: tracks s_tim2_overflow from main.c via parameter
 *
 * Authority boundary: no latency threshold claims, no operational side effects.
 */

#include "sd_measure.h"
#include <string.h>
#include <stdatomic.h>

/* ── Ring buffer ────────────────────────────────────────────────────────── */

static sd_capture_t s_ring[SD_MAX_CAPTURES];
static volatile uint32_t s_head = 0;   /* write index (ISR)  */
static volatile uint32_t s_tail = 0;   /* read  index (main) */
static volatile uint32_t s_seq  = 0;   /* monotonic sequence */
static volatile uint32_t s_drop = 0;   /* dropped events     */

/* Per-channel: last captured tick to detect duplicates */
static volatile uint32_t s_last_tick[SD_CHANNEL_COUNT];

/* ── Init ───────────────────────────────────────────────────────────────── */

void sd_capture_init(void)
{
    memset(s_ring, 0, sizeof(s_ring));
    s_head = s_tail = s_seq = s_drop = 0;
    for (int i = 0; i < SD_CHANNEL_COUNT; i++) s_last_tick[i] = UINT32_MAX;
}

/* ── Push (called from ISR) ─────────────────────────────────────────────── */

bool sd_capture_push(sd_channel_t ch, uint32_t ticks, uint32_t overflow)
{
    uint32_t next = (s_head + 1) & (SD_MAX_CAPTURES - 1);

    /* Ring full: drop and record */
    if (next == s_tail) {
        s_drop++;
        return false;
    }

    uint8_t quality = 0;

    /* Duplicate detection: same tick as last event on this channel */
    if (ticks == s_last_tick[ch]) {
        quality = 2;  /* suspect */
    }
    s_last_tick[ch] = ticks;

    /* Overflow-adjusted: mark if we wrapped at least once */
    if (overflow > 0 && quality == 0) quality = 1;

    sd_capture_t *rec = &s_ring[s_head];
    rec->raw_ticks      = ticks;
    rec->overflow_count = overflow;
    rec->channel        = ch;
    rec->quality        = quality;
    rec->seq            = s_seq++;

    /* Ensure write is visible before advancing head */
    __DMB();
    s_head = next;
    return true;
}

/* ── Pop (called from main loop via export) ─────────────────────────────── */

bool sd_capture_pop(sd_capture_t *out)
{
    if (s_tail == s_head) return false;

    *out = s_ring[s_tail];
    __DMB();
    s_tail = (s_tail + 1) & (SD_MAX_CAPTURES - 1);
    return true;
}

uint32_t sd_capture_pending(void)
{
    return (s_head - s_tail) & (SD_MAX_CAPTURES - 1);
}

uint32_t sd_capture_drop_count(void)
{
    return s_drop;
}
