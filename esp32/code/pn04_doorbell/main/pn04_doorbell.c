/*
 * PN-04: Doorbell / Visitor Context Node
 *
 * Detects a doorbell press and publishes context with
 * environmental_context.doorbell_detected = true.
 *
 * Authority boundary:
 *   - No door unlock authorization.
 *   - No doorlock state insertion into device_states.
 *   - No local doorlock control.
 *   - doorbell_detected is visitor-arrival context, not authorization.
 *   - Non-visitor scenarios always publish doorbell_detected = false.
 */

#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "mqtt_client.h"

#include "../../shared/sd_mqtt_topics.h"
#include "../../shared/sd_payload.h"

/* ── Configuration ─────────────────────────────────────────────────────── */

#define NODE_SOURCE_ID    "esp32.doorbell_node_01"
/*
 * ESP32-C3 Super Mini: GPIO4 used by lighting node.
 * Use GPIO3 for doorbell input.
 */
#define DOORBELL_GPIO     GPIO_NUM_3
#define DEBOUNCE_MS       100
#define MQTT_BROKER_URI   CONFIG_SD_MQTT_BROKER_URI

static const char *TAG = "pn04_doorbell";

/* ── State ──────────────────────────────────────────────────────────────── */

static QueueHandle_t            s_bell_queue;
static esp_mqtt_client_handle_t s_mqtt;
static volatile bool            s_mqtt_connected = false;

/* ── ISR ────────────────────────────────────────────────────────────────── */

static void IRAM_ATTR doorbell_isr(void *arg)
{
    static int64_t last_ms = 0;
    int64_t now_ms = esp_timer_get_time() / 1000;
    if ((now_ms - last_ms) < DEBOUNCE_MS) return;
    last_ms = now_ms;
    BaseType_t high = pdFALSE;
    xQueueSendFromISR(s_bell_queue, &now_ms, &high);
    if (high) portYIELD_FROM_ISR();
}

/* ── Publish task ───────────────────────────────────────────────────────── */

static void doorbell_task(void *arg)
{
    int64_t event_ms;
    char env_buf[128], ctx_buf[512], wrapper_buf[SD_PAYLOAD_MAX_LEN];

    sd_routing_meta_t meta = {
        .source_id             = NODE_SOURCE_ID,
        .protocol              = "mqtt",
        .controlled_experiment = false,
    };

    while (1) {
        if (!xQueueReceive(s_bell_queue, &event_ms, pdMS_TO_TICKS(5000))) continue;
        if (!s_mqtt_connected) {
            ESP_LOGW(TAG, "MQTT not connected, dropping doorbell event");
            continue;
        }

        /*
         * Set doorbell_detected = true.
         * Do NOT add door_lock_state or front_door_lock to device_states —
         * those fields are not in the canonical context_schema.json.
         */
        snprintf(env_buf, sizeof(env_buf),
                 "{\"doorbell_detected\":true,\"occupancy_detected\":true}");

        int r = sd_build_pure_context(
            "sensor_event", "DOORBELL_PRESS", event_ms,
            env_buf, "{}", ctx_buf, sizeof(ctx_buf));
        if (r < 0) { ESP_LOGE(TAG, "ctx overflow"); continue; }

        r = sd_build_router_input(ctx_buf, &meta, wrapper_buf, sizeof(wrapper_buf));
        if (r < 0) { ESP_LOGE(TAG, "wrapper overflow"); continue; }

        int msg_id = esp_mqtt_client_publish(
            s_mqtt, SD_TOPIC_CONTEXT_INPUT, wrapper_buf, 0, SD_QOS_CONTEXT, 0);
        ESP_LOGI(TAG, "doorbell context published, msg_id=%d", msg_id);
    }
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
    default: break;
    }
}

/* ── app_main ───────────────────────────────────────────────────────────── */

void app_main(void)
{
    ESP_LOGI(TAG, "PN-04 Doorbell Node starting, source_id=%s", NODE_SOURCE_ID);

    s_bell_queue = xQueueCreate(4, sizeof(int64_t));

    gpio_config_t cfg = {
        .pin_bit_mask = (1ULL << DOORBELL_GPIO),
        .mode         = GPIO_MODE_INPUT,
        .pull_up_en   = GPIO_PULLUP_ENABLE,
        .intr_type    = GPIO_INTR_NEGEDGE,
    };
    gpio_config(&cfg);
    gpio_install_isr_service(0);
    gpio_isr_handler_add(DOORBELL_GPIO, doorbell_isr, NULL);

    esp_mqtt_client_config_t mcfg = {
        .broker.address.uri    = MQTT_BROKER_URI,
        .credentials.client_id = NODE_SOURCE_ID,
    };
    s_mqtt = esp_mqtt_client_init(&mcfg);
    esp_mqtt_client_register_event(s_mqtt, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(s_mqtt);

    xTaskCreate(doorbell_task, "doorbell_task", 4096, NULL, 5, NULL);

    ESP_LOGI(TAG, "PN-04 ready — GPIO%d monitors doorbell", DOORBELL_GPIO);
}
