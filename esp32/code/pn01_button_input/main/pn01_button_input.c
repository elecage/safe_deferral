/*
 * PN-01: Bounded Button Input Node
 *
 * Detects physical button presses, debounces them, and publishes
 * context input to safe_deferral/context/input.
 *
 * Authority boundary:
 *   - No local policy routing.
 *   - No local actuator command.
 *   - No invented emergency semantics.
 *   - Publishes user_input event only; routing/classification is Mac mini's job.
 */

#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_sntp.h"
#include "mqtt_client.h"

#include "../../shared/sd_mqtt_topics.h"
#include "../../shared/sd_payload.h"

/* ── Configuration ─────────────────────────────────────────────────────── */

#define NODE_SOURCE_ID      "esp32.button_node_01"
#define BUTTON_GPIO         GPIO_NUM_9     /* Built-in boot button on ESP32-C3 Super Mini */
#define DEBOUNCE_MS         50
#define MQTT_BROKER_URI     CONFIG_SD_MQTT_BROKER_URI   /* via menuconfig */

static const char *TAG = "pn01_button";

/* ── Internal types ─────────────────────────────────────────────────────── */

typedef enum {
    BTN_EVENT_PRESS = 0,
    BTN_EVENT_LONG_PRESS,   /* held > 2 s — treated as clarification intent */
} btn_event_type_t;

typedef struct {
    btn_event_type_t type;
    int64_t          timestamp_ms;
} btn_event_t;

/* ── State ──────────────────────────────────────────────────────────────── */

static QueueHandle_t       s_btn_queue;
static esp_mqtt_client_handle_t s_mqtt;
static volatile bool       s_mqtt_connected = false;

/* ── GPIO ISR ───────────────────────────────────────────────────────────── */

static void IRAM_ATTR gpio_isr_handler(void *arg)
{
    static int64_t last_isr_ms = 0;
    int64_t now_ms = esp_timer_get_time() / 1000;

    if ((now_ms - last_isr_ms) < DEBOUNCE_MS) return;
    last_isr_ms = now_ms;

    btn_event_t ev = {
        .type         = BTN_EVENT_PRESS,
        .timestamp_ms = now_ms,
    };
    BaseType_t high_task_woken = pdFALSE;
    xQueueSendFromISR(s_btn_queue, &ev, &high_task_woken);
    if (high_task_woken) portYIELD_FROM_ISR();
}

/* ── MQTT event handler ─────────────────────────────────────────────────── */

static void mqtt_event_handler(void *arg, esp_event_base_t base,
                                int32_t event_id, void *event_data)
{
    esp_mqtt_event_handle_t ev = event_data;
    switch (ev->event_id) {
    case MQTT_EVENT_CONNECTED:
        ESP_LOGI(TAG, "MQTT connected");
        s_mqtt_connected = true;
        break;
    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGW(TAG, "MQTT disconnected");
        s_mqtt_connected = false;
        break;
    case MQTT_EVENT_ERROR:
        ESP_LOGE(TAG, "MQTT error");
        break;
    default:
        break;
    }
}

/* ── Button processing task ─────────────────────────────────────────────── */

static void button_task(void *arg)
{
    btn_event_t ev;
    char env_buf[128], ctx_buf[512], wrapper_buf[SD_PAYLOAD_MAX_LEN];

    sd_routing_meta_t meta = {
        .source_id            = NODE_SOURCE_ID,
        .protocol             = "mqtt",
        .controlled_experiment = false,
    };

    while (1) {
        if (!xQueueReceive(s_btn_queue, &ev, pdMS_TO_TICKS(5000))) continue;

        if (!s_mqtt_connected) {
            ESP_LOGW(TAG, "MQTT not connected, dropping button event");
            continue;
        }

        /* environmental_context: occupancy_detected inferred from button press */
        snprintf(env_buf, sizeof(env_buf),
            "{\"occupancy_detected\":true,"
            "\"doorbell_detected\":false}");

        const char *event_code = (ev.type == BTN_EVENT_LONG_PRESS)
            ? "BUTTON_LONG_PRESS"
            : "BUTTON_PRESS";

        int r = sd_build_pure_context(
            "user_input", event_code, ev.timestamp_ms,
            env_buf, "{}", ctx_buf, sizeof(ctx_buf));
        if (r < 0) { ESP_LOGE(TAG, "ctx overflow"); continue; }

        r = sd_build_router_input(ctx_buf, &meta, wrapper_buf, sizeof(wrapper_buf));
        if (r < 0) { ESP_LOGE(TAG, "wrapper overflow"); continue; }

        int msg_id = esp_mqtt_client_publish(
            s_mqtt, SD_TOPIC_CONTEXT_INPUT, wrapper_buf, 0, SD_QOS_CONTEXT, 0);
        ESP_LOGI(TAG, "published button event msg_id=%d event_code=%s", msg_id, event_code);
    }
}

/* ── GPIO init ──────────────────────────────────────────────────────────── */

static void gpio_init(void)
{
    gpio_config_t cfg = {
        .pin_bit_mask = (1ULL << BUTTON_GPIO),
        .mode         = GPIO_MODE_INPUT,
        .pull_up_en   = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_NEGEDGE,
    };
    gpio_config(&cfg);
    gpio_install_isr_service(0);
    gpio_isr_handler_add(BUTTON_GPIO, gpio_isr_handler, NULL);
    ESP_LOGI(TAG, "GPIO %d configured for button input", BUTTON_GPIO);
}

/* ── MQTT init ──────────────────────────────────────────────────────────── */

static void mqtt_init(void)
{
    esp_mqtt_client_config_t cfg = {
        .broker.address.uri = MQTT_BROKER_URI,
        .credentials.client_id = NODE_SOURCE_ID,
    };
    s_mqtt = esp_mqtt_client_init(&cfg);
    esp_mqtt_client_register_event(s_mqtt, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(s_mqtt);
    ESP_LOGI(TAG, "MQTT client started, broker=%s", MQTT_BROKER_URI);
}

/* ── app_main ───────────────────────────────────────────────────────────── */

void app_main(void)
{
    ESP_LOGI(TAG, "PN-01 Button Input Node starting, source_id=%s", NODE_SOURCE_ID);

    s_btn_queue = xQueueCreate(8, sizeof(btn_event_t));

    gpio_init();
    mqtt_init();

    xTaskCreate(button_task, "button_task", 4096, NULL, 5, NULL);

    ESP_LOGI(TAG, "PN-01 ready — press GPIO%d (built-in boot btn) to publish context input", BUTTON_GPIO);
}
