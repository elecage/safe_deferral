/*
 * STM32-03: Time Sync and Readiness Reporter
 *
 * Manages measurement session state and readiness levels.
 * Accepts session-start / session-stop commands from the host
 * (RPi / experiment runner) over UART.
 *
 * Command format (one line, newline terminated):
 *   SESSION_START <experiment_id>
 *   SESSION_STOP
 *   SESSION_RESET
 *   STATUS
 *
 * Distinguishes measurement readiness from operational readiness:
 *   - Measurement readiness = timer armed, capture path healthy
 *   - Operational readiness is the Mac mini's responsibility
 *
 * Authority boundary:
 *   - No claim of perfect synchronization.
 *   - No blocking or approving operational control decisions.
 */

#include "sd_measure.h"
#include "stm32h7xx_hal.h"
#include <string.h>
#include <stdio.h>

extern UART_HandleTypeDef huart3;
extern TIM_HandleTypeDef  htim2;

/* ── UART receive buffer ────────────────────────────────────────────────── */

#define CMD_BUF_LEN  64

static char     s_cmd_buf[CMD_BUF_LEN];
static uint32_t s_cmd_pos = 0;
static uint8_t  s_rx_byte;   /* single-byte DMA/interrupt receive */

/* ── Timing sync state ──────────────────────────────────────────────────── */

static uint32_t s_session_counter = 0;

/* ── Init ───────────────────────────────────────────────────────────────── */

void sd_sync_init(void)
{
    sd_session_reset();
    /* Start UART receive interrupt for host commands */
    HAL_UART_Receive_IT(&huart3, &s_rx_byte, 1);
}

/* ── Session control ────────────────────────────────────────────────────── */

void sd_session_start(const char *experiment_id)
{
    g_session.session_id    = ++s_session_counter;
    g_session.state         = SD_SESSION_RUNNING;
    g_session.capture_count = 0;
    g_session.start_tick    = __HAL_TIM_GET_COUNTER(&htim2);
    g_session.stop_tick     = 0;
    strncpy(g_session.experiment_id, experiment_id ? experiment_id : "unknown",
            sizeof(g_session.experiment_id) - 1);

    char msg[128];
    snprintf(msg, sizeof(msg),
        "# SESSION_START session_id=%lu experiment_id=%s\r\n",
        g_session.session_id, g_session.experiment_id);
    HAL_UART_Transmit(&huart3, (uint8_t *)msg, strlen(msg), 50);
}

void sd_session_stop(void)
{
    if (g_session.state == SD_SESSION_RUNNING) {
        g_session.stop_tick = __HAL_TIM_GET_COUNTER(&htim2);
        g_session.state     = SD_SESSION_DONE;

        char msg[128];
        snprintf(msg, sizeof(msg),
            "# SESSION_STOP session_id=%lu captures=%lu\r\n",
            g_session.session_id, g_session.capture_count);
        HAL_UART_Transmit(&huart3, (uint8_t *)msg, strlen(msg), 50);
    }
}

void sd_session_reset(void)
{
    memset(&g_session, 0, sizeof(g_session));
    g_session.state = SD_SESSION_IDLE;
}

/* ── Command parser ─────────────────────────────────────────────────────── */

static void process_command(const char *cmd)
{
    if (strncmp(cmd, "SESSION_START", 13) == 0) {
        const char *id = (strlen(cmd) > 14) ? cmd + 14 : "unknown";
        sd_session_start(id);

    } else if (strncmp(cmd, "SESSION_STOP", 12) == 0) {
        sd_session_stop();

    } else if (strncmp(cmd, "SESSION_RESET", 13) == 0) {
        sd_session_reset();
        HAL_UART_Transmit(&huart3, (uint8_t *)"# SESSION_RESET\r\n", 17, 20);

    } else if (strncmp(cmd, "STATUS", 6) == 0) {
        char status[256];
        const char *states[] = {"IDLE", "ARMED", "RUNNING", "DONE"};
        snprintf(status, sizeof(status),
            "# STATUS node_id=%s fw=%s session=%lu state=%s captures=%lu\r\n",
            SD_NODE_ID, SD_FW_VERSION,
            g_session.session_id,
            states[g_session.state < 4 ? g_session.state : 3],
            g_session.capture_count);
        HAL_UART_Transmit(&huart3, (uint8_t *)status, strlen(status), 100);
    }
}

/* ── UART receive callback (one byte at a time) ─────────────────────────── */

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *h)
{
    if (h->Instance != USART3) return;

    char c = (char)s_rx_byte;
    HAL_UART_Receive_IT(&huart3, &s_rx_byte, 1);  /* re-arm */

    if (c == '\n' || c == '\r') {
        if (s_cmd_pos > 0) {
            s_cmd_buf[s_cmd_pos] = '\0';
            process_command(s_cmd_buf);
            s_cmd_pos = 0;
        }
    } else if (s_cmd_pos < CMD_BUF_LEN - 1) {
        s_cmd_buf[s_cmd_pos++] = c;
    }
    /* Overflow: silently reset position */
    else {
        s_cmd_pos = 0;
    }
}
