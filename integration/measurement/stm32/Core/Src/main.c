/*
 * STM32-01: Measurement Firmware Skeleton
 *
 * Nucleo-H723ZG  —  out-of-band timing capture node.
 *
 * Startup sequence:
 *   1. HAL / system clock init (480 MHz core, TIM2 source at 240 MHz / 240 = 1 MHz)
 *   2. GPIO init  (LED, capture input pins)
 *   3. UART3 init (115200 8N1, ST-LINK virtual COM)
 *   4. TIM2 input-capture init  (1 µs tick, CH1-CH4)
 *   5. Module inits (capture ring, export, status, sync)
 *   6. Self-test (STM32-05)
 *   7. Main loop: export_flush + status_tick
 *
 * Authority boundary: no operational MQTT, no actuator control.
 */

#include "stm32h7xx_hal.h"
#include "sd_measure.h"
#include <string.h>
#include <stdio.h>

/* ── Globals ────────────────────────────────────────────────────────────── */
sd_session_t          g_session;
sd_readiness_report_t g_readiness;

/* ── HAL peripheral handles ─────────────────────────────────────────────── */
TIM_HandleTypeDef  htim2;
UART_HandleTypeDef huart3;

/* ── Timer overflow counter (updated in TIM2 period-elapsed IRQ) ────────── */
static volatile uint32_t s_tim2_overflow = 0;

/* ── Forward declarations ───────────────────────────────────────────────── */
static void system_clock_config(void);
static void gpio_init(void);
static void uart3_init(void);
static void tim2_capture_init(void);
static void error_handler(void);

/* ── HAL MSP (minimal — full MSP in HAL-generated code in real project) ── */
void HAL_TIM_IC_CaptureCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance != TIM2) return;

    uint32_t ch_map[4] = {
        TIM_CHANNEL_1, TIM_CHANNEL_2, TIM_CHANNEL_3, TIM_CHANNEL_4
    };
    for (int i = 0; i < SD_CHANNEL_COUNT; i++) {
        if (__HAL_TIM_GET_FLAG(htim, (TIM_FLAG_CC1 << i))) {
            uint32_t ticks = HAL_TIM_ReadCapturedValue(htim, ch_map[i]);
            sd_capture_push((sd_channel_t)i, ticks, s_tim2_overflow);
        }
    }
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM2) s_tim2_overflow++;
}

/* ── app_main (called from startup_stm32h723zgtx.s via Reset_Handler) ──── */
int main(void)
{
    HAL_Init();
    system_clock_config();
    gpio_init();
    uart3_init();
    tim2_capture_init();

    /* Module inits */
    sd_capture_init();
    sd_export_init();
    sd_status_init();
    sd_sync_init();

    /* STM32-05: startup self-test */
    sd_readiness_t level = sd_self_test(&g_readiness);

    /* Emit boot banner + self-test result over UART */
    char banner[256];
    snprintf(banner, sizeof(banner),
        "\r\n# sd_measure boot\r\n"
        "# node_id=%s fw=%s\r\n"
        "# self_test=%s timer=%s export=%s\r\n",
        SD_NODE_ID, SD_FW_VERSION,
        level == SD_READY ? "PASS" : "FAIL",
        g_readiness.timer_ok  ? "OK" : "FAIL",
        g_readiness.export_ok ? "OK" : "FAIL");
    HAL_UART_Transmit(&huart3, (uint8_t *)banner, strlen(banner), 100);

    /* Signal readiness on LED:
     *   LD1 (green) = READY
     *   LD3 (red)   = BLOCKED / FAIL */
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0,   /* LD1 green */
        (level == SD_READY) ? GPIO_PIN_SET : GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14,  /* LD3 red */
        (level != SD_READY) ? GPIO_PIN_SET : GPIO_PIN_RESET);

    /* Main loop */
    while (1) {
        sd_export_flush();   /* drain capture ring → UART CSV rows */
        sd_status_tick();    /* emit heartbeat JSON every 5 s       */
        HAL_Delay(1);
    }
}

/* ── Clock config: 480 MHz core, APB1 120 MHz, TIM2 input 240 MHz ─────── */
static void system_clock_config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    /* HSE + PLL1 → 480 MHz */
    osc.OscillatorType      = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState            = RCC_HSE_BYPASS;  /* Nucleo uses 8 MHz from ST-LINK */
    osc.PLL.PLLState        = RCC_PLL_ON;
    osc.PLL.PLLSource       = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLM            = 4;
    osc.PLL.PLLN            = 240;
    osc.PLL.PLLP            = 2;   /* VCO / 2 = 240 MHz → SYSCLK divider gives 480 */
    osc.PLL.PLLQ            = 4;
    osc.PLL.PLLR            = 2;
    osc.PLL.PLLVCOSEL       = RCC_PLL1VCOWIDE;
    osc.PLL.PLLRGE          = RCC_PLL1VCIRANGE_1;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) error_handler();

    clk.ClockType      = RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK |
                         RCC_CLOCKTYPE_PCLK1  | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
    clk.SYSCLKDivider  = RCC_SYSCLK_DIV1;
    clk.AHBCLKDivider  = RCC_HCLK_DIV2;   /* HCLK = 240 MHz */
    clk.APB1CLKDivider = RCC_APB1_DIV2;   /* APB1 = 120 MHz, TIM2×2 = 240 MHz */
    clk.APB2CLKDivider = RCC_APB2_DIV2;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_4) != HAL_OK) error_handler();
}

/* ── GPIO: LED outputs, capture inputs (PA0-PA3) ────────────────────────── */
static void gpio_init(void)
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();

    /* LED outputs (LD1=PB0, LD2=PE1, LD3=PB14) */
    GPIO_InitTypeDef led = {
        .Pin   = GPIO_PIN_0 | GPIO_PIN_14,
        .Mode  = GPIO_MODE_OUTPUT_PP,
        .Pull  = GPIO_NOPULL,
        .Speed = GPIO_SPEED_FREQ_LOW,
    };
    HAL_GPIO_Init(GPIOB, &led);
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0 | GPIO_PIN_14, GPIO_PIN_RESET);

    /* Capture inputs PA0-PA3 configured as AF for TIM2 — done in tim2_init */
}

/* ── UART3: 115200 8N1 → ST-LINK USB virtual COM ────────────────────────── */
static void uart3_init(void)
{
    __HAL_RCC_USART3_CLK_ENABLE();
    __HAL_RCC_GPIOD_CLK_ENABLE();

    GPIO_InitTypeDef gpio = {
        .Pin       = GPIO_PIN_8 | GPIO_PIN_9,  /* PD8=TX, PD9=RX */
        .Mode      = GPIO_MODE_AF_PP,
        .Pull      = GPIO_NOPULL,
        .Speed     = GPIO_SPEED_FREQ_LOW,
        .Alternate = GPIO_AF7_USART3,
    };
    HAL_GPIO_Init(GPIOD, &gpio);

    huart3.Instance          = USART3;
    huart3.Init.BaudRate     = 115200;
    huart3.Init.WordLength   = UART_WORDLENGTH_8B;
    huart3.Init.StopBits     = UART_STOPBITS_1;
    huart3.Init.Parity       = UART_PARITY_NONE;
    huart3.Init.Mode         = UART_MODE_TX_RX;
    huart3.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
    huart3.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart3) != HAL_OK) error_handler();
}

/* ── TIM2: 1 MHz free-run, input capture on CH1-CH4 (PA0-PA3) ──────────── */
static void tim2_capture_init(void)
{
    __HAL_RCC_TIM2_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    /* PA0-PA3: TIM2_CH1-CH4 alternate function */
    GPIO_InitTypeDef gpio = {
        .Pin       = GPIO_PIN_0 | GPIO_PIN_1 | GPIO_PIN_2 | GPIO_PIN_3,
        .Mode      = GPIO_MODE_AF_PP,
        .Pull      = GPIO_PULLDOWN,
        .Speed     = GPIO_SPEED_FREQ_HIGH,
        .Alternate = GPIO_AF1_TIM2,
    };
    HAL_GPIO_Init(GPIOA, &gpio);

    /* TIM2 base: prescaler = 240-1 → 1 MHz tick */
    htim2.Instance               = TIM2;
    htim2.Init.Prescaler         = (uint32_t)(240 - 1);  /* 240 MHz / 240 = 1 MHz */
    htim2.Init.CounterMode       = TIM_COUNTERMODE_UP;
    htim2.Init.Period             = 0xFFFFFFFFUL;  /* 32-bit free-run */
    htim2.Init.ClockDivision     = TIM_CLOCKDIVISION_DIV1;
    htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_Base_Init(&htim2) != HAL_OK) error_handler();

    /* Input capture config for all 4 channels */
    TIM_IC_InitTypeDef ic = {
        .ICPolarity  = TIM_ICPOLARITY_RISING,
        .ICSelection = TIM_ICSELECTION_DIRECTTI,
        .ICPrescaler = TIM_ICPSC_DIV1,
        .ICFilter    = 0x04,  /* debounce filter: 4 samples */
    };
    uint32_t channels[4] = {
        TIM_CHANNEL_1, TIM_CHANNEL_2, TIM_CHANNEL_3, TIM_CHANNEL_4
    };
    for (int i = 0; i < 4; i++) {
        if (HAL_TIM_IC_ConfigChannel(&htim2, &ic, channels[i]) != HAL_OK)
            error_handler();
    }

    /* Enable update (overflow) and capture IRQs */
    HAL_NVIC_SetPriority(TIM2_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(TIM2_IRQn);

    HAL_TIM_Base_Start_IT(&htim2);
    for (int i = 0; i < 4; i++)
        HAL_TIM_IC_Start_IT(&htim2, channels[i]);
}

/* ── IRQ handler ────────────────────────────────────────────────────────── */
void TIM2_IRQHandler(void) { HAL_TIM_IRQHandler(&htim2); }

/* ── Error handler ──────────────────────────────────────────────────────── */
static void error_handler(void)
{
    /* Blink red LED fast to indicate hard fault. */
    __HAL_RCC_GPIOB_CLK_ENABLE();
    while (1) {
        HAL_GPIO_TogglePin(GPIOB, GPIO_PIN_14);
        HAL_Delay(100);
    }
}
