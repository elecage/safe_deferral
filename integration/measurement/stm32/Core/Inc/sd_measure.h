/*
 * sd_measure.h — safe_deferral STM32 measurement node top-level header.
 *
 * STM32 Nucleo-H723ZG  (STM32H723ZGTx)
 * Role: out-of-band timing / latency capture node.
 *
 * Authority boundary:
 *   - No operational MQTT publishing.
 *   - No actuator control or policy decision.
 *   - Measurement output is evidence / artifact only.
 *   - No latency threshold claim unless grounded in active experiment docs.
 *
 * Export path: UART3 (115200, 8N1) → ST-LINK USB virtual COM, or USB CDC.
 *
 * Capture channels (TIM2/TIM5 32-bit free-run counter, input capture):
 *   CH_A  = CAPTURE_A : trigger source edge       (PA0 / TIM2_CH1)
 *   CH_B  = CAPTURE_B : hub/bridge observable edge (PA1 / TIM2_CH2)
 *   CH_C  = CAPTURE_C : actuator ACK edge          (PA2 / TIM2_CH3)
 *   CH_D  = CAPTURE_D : spare / future use         (PA3 / TIM2_CH4)
 *
 * Timer: TIM2 runs at 1 MHz (1 µs resolution).  Overflow is tracked.
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

/* ── Firmware identity ──────────────────────────────────────────────────── */
#define SD_FW_VERSION        "1.0.0"
#define SD_NODE_ID           "stm32_time_probe_01"
#define SD_NODE_CLASS        "measurement_node"
#define SD_IMPLEMENTATION    "stm32_nucleo_h723zg"

/* ── Timer / capture ────────────────────────────────────────────────────── */
#define SD_TIMER_FREQ_HZ     1000000UL   /* TIM2 / TIM5 at 1 MHz → 1 µs tick */
#define SD_MAX_CAPTURES      4096        /* ring buffer depth */
#define SD_CHANNEL_COUNT     4

typedef enum {
    SD_CH_A = 0,   /* trigger source */
    SD_CH_B = 1,   /* hub observable */
    SD_CH_C = 2,   /* actuator ACK   */
    SD_CH_D = 3,   /* spare          */
} sd_channel_t;

/* ── Capture record ─────────────────────────────────────────────────────── */
typedef struct {
    uint32_t    raw_ticks;      /* TIM2 captured value (1 µs per tick)  */
    uint32_t    overflow_count; /* number of TIM2 overflows before this */
    sd_channel_t channel;
    uint8_t     quality;        /* 0=OK, 1=overflow-adjusted, 2=suspect */
    uint32_t    seq;            /* monotonic sequence number            */
} sd_capture_t;

/* ── Session ────────────────────────────────────────────────────────────── */
typedef enum {
    SD_SESSION_IDLE    = 0,
    SD_SESSION_ARMED   = 1,
    SD_SESSION_RUNNING = 2,
    SD_SESSION_DONE    = 3,
} sd_session_state_t;

typedef struct {
    uint32_t           session_id;
    sd_session_state_t state;
    uint32_t           capture_count;
    uint32_t           start_tick;
    uint32_t           stop_tick;
    char               experiment_id[32];
} sd_session_t;

/* ── Readiness ──────────────────────────────────────────────────────────── */
typedef enum {
    SD_READY   = 0,
    SD_DEGRADED = 1,
    SD_BLOCKED  = 2,
    SD_UNKNOWN  = 3,
} sd_readiness_t;

typedef struct {
    sd_readiness_t  level;
    bool            timer_ok;
    bool            capture_ok[SD_CHANNEL_COUNT];
    bool            export_ok;
    bool            self_test_passed;
    char            fw_version[16];
    char            node_id[32];
} sd_readiness_report_t;

/* ── Global handles (defined in main.c, used across modules) ────────────── */
extern sd_session_t        g_session;
extern sd_readiness_report_t g_readiness;

/* ── Module init functions ──────────────────────────────────────────────── */
void sd_capture_init(void);
void sd_sync_init(void);
void sd_export_init(void);
void sd_status_init(void);

/* ── Module tick / process functions (called from main loop) ────────────── */
void sd_status_tick(void);     /* heartbeat / serial status emit */
void sd_export_flush(void);    /* drain capture ring to UART     */

/* ── Session control ────────────────────────────────────────────────────── */
void sd_session_start(const char *experiment_id);
void sd_session_stop(void);
void sd_session_reset(void);

/* ── Capture API (called from ISR and modules) ──────────────────────────── */
bool sd_capture_push(sd_channel_t ch, uint32_t ticks, uint32_t overflow);
bool sd_capture_pop(sd_capture_t *out);
uint32_t sd_capture_pending(void);

/* ── Self-test (STM32-05) ───────────────────────────────────────────────── */
sd_readiness_t sd_self_test(sd_readiness_report_t *report);
