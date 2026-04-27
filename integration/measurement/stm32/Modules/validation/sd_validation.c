/*
 * STM32-05: Measurement Validation / Self-Test
 *
 * Runs on every boot. Checks:
 *   1. Firmware version visible (always passes)
 *   2. Timer initialization — reads TIM2 counter twice, verifies it advances
 *   3. Capture channel detection — injects a synthetic push per channel and
 *      verifies pop returns correct data
 *   4. Export path — transmits a known pattern over UART and verifies no
 *      HAL timeout (loopback not required; TX-OK is sufficient)
 *   5. No operational side effects (enforced by design — this module only
 *      touches measurement infrastructure)
 *
 * Expected outputs (emitted over UART):
 *   # SELFTEST_START
 *   # SELFTEST_FW_VERSION: 1.0.0 PASS
 *   # SELFTEST_TIMER: PASS (or FAIL)
 *   # SELFTEST_CAPTURE_CH_A: PASS (× 4 channels)
 *   # SELFTEST_EXPORT: PASS
 *   # SELFTEST_RESULT: READY (or BLOCKED/DEGRADED)
 *
 * Authority boundary:
 *   - No claim of operational readiness.
 *   - Measurement readiness only.
 */

#include "sd_measure.h"
#include "stm32h7xx_hal.h"
#include <string.h>
#include <stdio.h>

extern UART_HandleTypeDef huart3;
extern TIM_HandleTypeDef  htim2;

/* ── Helpers ────────────────────────────────────────────────────────────── */

static void emit(const char *s)
{
    HAL_UART_Transmit(&huart3, (uint8_t *)s, strlen(s), 50);
}

static bool test_timer(void)
{
    uint32_t t0 = __HAL_TIM_GET_COUNTER(&htim2);
    HAL_Delay(2);
    uint32_t t1 = __HAL_TIM_GET_COUNTER(&htim2);
    /* After 2 ms at 1 MHz, counter should have advanced ≥ 1000 ticks */
    return (t1 > t0 && (t1 - t0) >= 1000);
}

static bool test_capture_channel(sd_channel_t ch)
{
    /* Inject a synthetic record directly */
    bool pushed = sd_capture_push(ch, 0xABCD0000UL + ch, 0);
    if (!pushed) return false;

    sd_capture_t rec;
    if (!sd_capture_pop(&rec)) return false;

    return (rec.channel == ch && rec.raw_ticks == (0xABCD0000UL + ch));
}

static bool test_export_path(void)
{
    const char *probe = "# SELFTEST_EXPORT_PROBE\r\n";
    HAL_StatusTypeDef r = HAL_UART_Transmit(&huart3, (uint8_t *)probe,
                                             strlen(probe), 100);
    return (r == HAL_OK);
}

/* ── Main self-test entry ────────────────────────────────────────────────── */

sd_readiness_t sd_self_test(sd_readiness_report_t *report)
{
    memset(report, 0, sizeof(*report));
    strncpy(report->fw_version, SD_FW_VERSION, sizeof(report->fw_version) - 1);
    strncpy(report->node_id,    SD_NODE_ID,    sizeof(report->node_id)    - 1);

    emit("# SELFTEST_START\r\n");

    /* 1. Firmware version */
    char buf[64];
    snprintf(buf, sizeof(buf), "# SELFTEST_FW_VERSION: %s PASS\r\n", SD_FW_VERSION);
    emit(buf);

    /* 2. Timer */
    report->timer_ok = test_timer();
    snprintf(buf, sizeof(buf), "# SELFTEST_TIMER: %s\r\n",
             report->timer_ok ? "PASS" : "FAIL");
    emit(buf);

    /* 3. Capture channels */
    const char *ch_names[SD_CHANNEL_COUNT] = {"CH_A", "CH_B", "CH_C", "CH_D"};
    bool all_capture_ok = true;
    for (int i = 0; i < SD_CHANNEL_COUNT; i++) {
        report->capture_ok[i] = test_capture_channel((sd_channel_t)i);
        if (!report->capture_ok[i]) all_capture_ok = false;
        snprintf(buf, sizeof(buf), "# SELFTEST_CAPTURE_%s: %s\r\n",
                 ch_names[i], report->capture_ok[i] ? "PASS" : "FAIL");
        emit(buf);
    }

    /* 4. Export path */
    report->export_ok = test_export_path();
    snprintf(buf, sizeof(buf), "# SELFTEST_EXPORT: %s\r\n",
             report->export_ok ? "PASS" : "FAIL");
    emit(buf);

    /* 5. Determine overall readiness */
    if (!report->timer_ok || !report->export_ok) {
        report->level = SD_BLOCKED;
    } else if (!all_capture_ok) {
        report->level = SD_DEGRADED;
    } else {
        report->level = SD_READY;
    }
    report->self_test_passed = (report->level == SD_READY);

    const char *rl[] = {"READY", "DEGRADED", "BLOCKED", "UNKNOWN"};
    snprintf(buf, sizeof(buf), "# SELFTEST_RESULT: %s\r\n",
             rl[report->level < 4 ? report->level : 3]);
    emit(buf);

    return report->level;
}
