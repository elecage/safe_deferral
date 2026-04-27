/*
 * PN-05: Gas / Smoke / Fire Evidence Node
 *
 * Monitors gas, smoke, or fire sensors and publishes emergency event
 * context to safe_deferral/emergency/event when a threshold is crossed.
 *
 * Authority boundary:
 *   - No local emergency routing authority.
 *   - No invented trigger thresholds outside canonical policy.
 *   - No direct actuator or notification command.
 *   - Publishes evidence only; Mac mini performs Class 0 routing.
 *
 * Emergency event codes (aligned with E001-E005 in policy_table.json):
 *   E001 = GAS_ALERT
 *   E002 = SMOKE_ALERT
 *   E003 = FIRE_ALERT
 */

#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "mqtt_client.h"

#include "../../shared/sd_mqtt_topics.h"
#include "../../shared/sd_payload.h"

/* ── Configuration ─────────────────────────────────────────────────────── */

#define NODE_SOURCE_ID      "esp32.gas_smoke_fire_node_01"
#define SAMPLE_INTERVAL_MS  2000    /* check every 2 s */
#define MQTT_BROKER_URI     CONFIG_SD_MQTT_BROKER_URI

/*
 * Sensor thresholds.
 * Align with experiment definitions in required_experiments.md.
 * Do NOT invent thresholds here without documenting in policy.
 */
#define GAS_THRESHOLD_PPM   300.0f
#define SMOKE_THRESHOLD_OBS 0.15f  /* obscuration fraction */

static const char *TAG = "pn05_gsf";

/* ── State ──────────────────────────────────────────────────────────────── */

static esp_mqtt_client_handle_t s_mqtt;
static volatile bool            s_mqtt_connected = false;
static bool                     s_gas_alerted   = false;
static bool                     s_smoke_alerted = false;

/* ── Sensor stubs ───────────────────────────────────────────────────────── */

static bool read_gas_ppm(float *out)
{
    /* Replace with MQ-2/MQ-135 ADC read. */
    *out = 50.0f;
    return true;
}

static bool read_smoke_obs(float *out)
{
    /* Replace with photoelectric smoke sensor read. */
    *out = 0.02f;
    return true;
}

/* ── Publish helper ─────────────────────────────────────────────────────── */

static void publish_emergency(const char *event_code,
                               const char *env_json,
                               int64_t     ts_ms)
{
    char ctx_buf[512], wrapper_buf[SD_PAYLOAD_MAX_LEN];

    sd_routing_meta_t meta = {
        .source_id             = NODE_SOURCE_ID,
        .protocol              = "mqtt",
        .controlled_experiment = false,
    };

    int r = sd_build_pure_context(
        "emergency", event_code, ts_ms,
        env_json, "{}", ctx_buf, sizeof(ctx_buf));
    if (r < 0) { ESP_LOGE(TAG, "ctx overflow"); return; }

    r = sd_build_router_input(ctx_buf, &meta, wrapper_buf, sizeof(wrapper_buf));
    if (r < 0) { ESP_LOGE(TAG, "wrapper overflow"); return; }

    /* Emergency events publish to emergency/event topic. */
    int msg_id = esp_mqtt_client_publish(
        s_mqtt, SD_TOPIC_EMERGENCY_EVENT, wrapper_buf, 0, SD_QOS_EMERGENCY, 0);
    ESP_LOGW(TAG, "EMERGENCY published event_code=%s msg_id=%d", event_code, msg_id);
}

/* ── Sensor monitoring task ─────────────────────────────────────────────── */

static void sensor_task(void *arg)
{
    char env_buf[128];

    while (1) {
        vTaskDelay(pdMS_TO_TICKS(SAMPLE_INTERVAL_MS));
        if (!s_mqtt_connected) continue;

        int64_t now_ms = esp_timer_get_time() / 1000;
        float gas_ppm = 0.0f, smoke_obs = 0.0f;

        if (read_gas_ppm(&gas_ppm) && gas_ppm > GAS_THRESHOLD_PPM) {
            if (!s_gas_alerted) {
                snprintf(env_buf, sizeof(env_buf),
                         "{\"gas_detected\":true,\"doorbell_detected\":false,"
                         "\"occupancy_detected\":false}");
                publish_emergency("E001_GAS_ALERT", env_buf, now_ms);
                s_gas_alerted = true;
            }
        } else {
            s_gas_alerted = false;
        }

        if (read_smoke_obs(&smoke_obs) && smoke_obs > SMOKE_THRESHOLD_OBS) {
            if (!s_smoke_alerted) {
                snprintf(env_buf, sizeof(env_buf),
                         "{\"smoke_detected\":true,\"doorbell_detected\":false,"
                         "\"occupancy_detected\":false}");
                publish_emergency("E002_SMOKE_ALERT", env_buf, now_ms);
                s_smoke_alerted = true;
            }
        } else {
            s_smoke_alerted = false;
        }
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
        s_gas_alerted    = false;
        s_smoke_alerted  = false;
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
    ESP_LOGI(TAG, "PN-05 Gas/Smoke/Fire Node starting, source_id=%s", NODE_SOURCE_ID);

    esp_mqtt_client_config_t mcfg = {
        .broker.address.uri    = MQTT_BROKER_URI,
        .credentials.client_id = NODE_SOURCE_ID,
    };
    s_mqtt = esp_mqtt_client_init(&mcfg);
    esp_mqtt_client_register_event(s_mqtt, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(s_mqtt);

    xTaskCreate(sensor_task, "sensor_task", 4096, NULL, 6, NULL);

    ESP_LOGI(TAG, "PN-05 ready — gas threshold=%.0f ppm, smoke threshold=%.2f",
             GAS_THRESHOLD_PPM, SMOKE_THRESHOLD_OBS);
}
