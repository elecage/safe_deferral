/*
 * PN-07: Warning Output Node
 *
 * Subscribes to deferral/request and clarification/interaction topics,
 * presents feedback via buzzer, LED, and/or UART TTS output.
 *
 * Authority boundary:
 *   - No policy decision from output node.
 *   - No direct actuator approval.
 *   - No hidden caregiver confirmation.
 *   - Output is presentation only; all routing stays on Mac mini.
 */

#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "mqtt_client.h"
#include "cJSON.h"

#include "../../shared/sd_mqtt_topics.h"

/* ── Configuration ─────────────────────────────────────────────────────── */

#define NODE_SOURCE_ID      "esp32.warning_output_node_01"
/*
 * ESP32-C3 Super Mini pin mapping:
 *   GPIO25/26 do not exist on C3.
 *   GPIO17 does not exist on C3.
 *   UART0 (GPIO20/21) is reserved for flashing — use UART1 on GPIO10.
 *   ESP32-C3 supports LEDC low-speed mode only (no high-speed mode).
 */
#define GPIO_BUZZER         GPIO_NUM_6
#define GPIO_STATUS_LED     GPIO_NUM_7
#define UART_TTS_PORT       UART_NUM_1
#define UART_TTS_TX_PIN     GPIO_NUM_10  /* UART1 TX via GPIO matrix */
#define UART_TTS_BAUD       9600
#define MQTT_BROKER_URI     CONFIG_SD_MQTT_BROKER_URI

/* LEDC (PWM buzzer) config — C3 supports low-speed mode only */
#define LEDC_CHANNEL        LEDC_CHANNEL_0
#define LEDC_TIMER          LEDC_TIMER_0
#define LEDC_MODE           LEDC_LOW_SPEED_MODE
#define BUZZ_FREQ_HZ        2000
#define BUZZ_DUTY           2048    /* 50% of 12-bit range */

static const char *TAG = "pn07_warning";

/* ── State ──────────────────────────────────────────────────────────────── */

static esp_mqtt_client_handle_t s_mqtt;

/* ── Output primitives ──────────────────────────────────────────────────── */

static void buzzer_beep(int duration_ms)
{
    ledc_set_duty(LEDC_MODE, LEDC_CHANNEL, BUZZ_DUTY);
    ledc_update_duty(LEDC_MODE, LEDC_CHANNEL);
    vTaskDelay(pdMS_TO_TICKS(duration_ms));
    ledc_set_duty(LEDC_MODE, LEDC_CHANNEL, 0);
    ledc_update_duty(LEDC_MODE, LEDC_CHANNEL);
}

static void led_set(bool on)
{
    gpio_set_level(GPIO_STATUS_LED, on ? 1 : 0);
}

static void tts_say(const char *msg)
{
    /* Send short ASCII message to UART-connected TTS module (e.g. SYN6988). */
    if (!msg || msg[0] == '\0') return;
    uart_write_bytes(UART_TTS_PORT, msg, strlen(msg));
    uart_write_bytes(UART_TTS_PORT, "\r\n", 2);
    ESP_LOGI(TAG, "TTS: %s", msg);
}

/* ── Message handlers ───────────────────────────────────────────────────── */

static void handle_deferral_request(const char *data, int len)
{
    cJSON *root = cJSON_ParseWithLength(data, len);
    const char *reason = root
        ? cJSON_GetStringValue(cJSON_GetObjectItem(root, "deferral_reason"))
        : NULL;

    ESP_LOGI(TAG, "deferral request received, reason=%s", reason ? reason : "(none)");

    /* Three short beeps for deferral. */
    for (int i = 0; i < 3; i++) {
        buzzer_beep(100);
        vTaskDelay(pdMS_TO_TICKS(100));
    }
    led_set(true);
    tts_say("잠시 대기합니다");   /* "Please wait" in Korean */

    if (root) cJSON_Delete(root);
}

static void handle_clarification(const char *data, int len)
{
    cJSON *root = cJSON_ParseWithLength(data, len);
    const char *prompt = root
        ? cJSON_GetStringValue(cJSON_GetObjectItem(root, "clarification_prompt"))
        : NULL;

    ESP_LOGI(TAG, "clarification received, prompt=%s", prompt ? prompt : "(none)");

    /* Two long beeps for clarification needed. */
    buzzer_beep(300);
    vTaskDelay(pdMS_TO_TICKS(150));
    buzzer_beep(300);
    led_set(true);

    if (prompt) tts_say(prompt);
    else        tts_say("확인이 필요합니다");  /* "Confirmation needed" */

    if (root) cJSON_Delete(root);
}

/* ── MQTT event handler ─────────────────────────────────────────────────── */

static void mqtt_event_handler(void *arg, esp_event_base_t base,
                                int32_t event_id, void *event_data)
{
    esp_mqtt_event_handle_t ev = event_data;
    switch (ev->event_id) {
    case MQTT_EVENT_CONNECTED:
        ESP_LOGI(TAG, "MQTT connected — subscribing");
        esp_mqtt_client_subscribe(s_mqtt, SD_TOPIC_DEFERRAL_REQUEST,  1);
        esp_mqtt_client_subscribe(s_mqtt, SD_TOPIC_CLARIFICATION,     1);
        led_set(false);
        break;
    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGW(TAG, "MQTT disconnected");
        led_set(false);
        break;
    case MQTT_EVENT_DATA:
        if (strncmp(ev->topic, SD_TOPIC_DEFERRAL_REQUEST, ev->topic_len) == 0)
            handle_deferral_request(ev->data, ev->data_len);
        else if (strncmp(ev->topic, SD_TOPIC_CLARIFICATION, ev->topic_len) == 0)
            handle_clarification(ev->data, ev->data_len);
        break;
    default: break;
    }
}

/* ── Hardware init ──────────────────────────────────────────────────────── */

static void hw_init(void)
{
    /* LED */
    gpio_config_t led_cfg = {
        .pin_bit_mask = (1ULL << GPIO_STATUS_LED),
        .mode         = GPIO_MODE_OUTPUT,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    gpio_config(&led_cfg);
    led_set(false);

    /* Buzzer (PWM via LEDC) */
    ledc_timer_config_t timer = {
        .speed_mode      = LEDC_MODE,
        .timer_num       = LEDC_TIMER,
        .duty_resolution = LEDC_TIMER_12_BIT,
        .freq_hz         = BUZZ_FREQ_HZ,
        .clk_cfg         = LEDC_AUTO_CLK,
    };
    ledc_timer_config(&timer);
    ledc_channel_config_t ch = {
        .speed_mode = LEDC_MODE,
        .channel    = LEDC_CHANNEL,
        .timer_sel  = LEDC_TIMER,
        .gpio_num   = GPIO_BUZZER,
        .duty       = 0,
    };
    ledc_channel_config(&ch);

    /* UART for TTS module */
    uart_config_t uart_cfg = {
        .baud_rate = UART_TTS_BAUD,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
    };
    uart_param_config(UART_TTS_PORT, &uart_cfg);
    uart_set_pin(UART_TTS_PORT, UART_TTS_TX_PIN, UART_PIN_NO_CHANGE,
                 UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    uart_driver_install(UART_TTS_PORT, 256, 0, 0, NULL, 0);

    ESP_LOGI(TAG, "hardware initialized: LED=%d BUZZER=%d TTS UART=%d",
             GPIO_STATUS_LED, GPIO_BUZZER, UART_TTS_PORT);
}

/* ── app_main ───────────────────────────────────────────────────────────── */

void app_main(void)
{
    ESP_LOGI(TAG, "PN-07 Warning Output Node starting, source_id=%s", NODE_SOURCE_ID);

    hw_init();

    esp_mqtt_client_config_t mcfg = {
        .broker.address.uri    = MQTT_BROKER_URI,
        .credentials.client_id = NODE_SOURCE_ID,
    };
    s_mqtt = esp_mqtt_client_init(&mcfg);
    esp_mqtt_client_register_event(s_mqtt, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(s_mqtt);

    ESP_LOGI(TAG, "PN-07 ready — subscribed to deferral and clarification topics");
}
