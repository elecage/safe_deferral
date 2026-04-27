/*
 * PN-06: Fall-Detection Node
 *
 * Interfaces with an IMU (e.g. MPU-6050 via I2C) and publishes fall
 * evidence to safe_deferral/emergency/event when a fall pattern is detected.
 *
 * Authority boundary:
 *   - No arbitrary fall payload.
 *   - No local emergency dispatch beyond evidence reporting.
 *   - Ambiguous signals are handled conservatively (not published).
 *   - Fall event code E004_FALL_DETECTED aligns with policy_table.json.
 */

#include <stdio.h>
#include <string.h>
#include <math.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "mqtt_client.h"

#include "../../shared/sd_mqtt_topics.h"
#include "../../shared/sd_payload.h"

/* ── Configuration ─────────────────────────────────────────────────────── */

#define NODE_SOURCE_ID        "esp32.fall_detect_node_01"
#define SAMPLE_INTERVAL_MS    100    /* IMU sample rate: 10 Hz */
#define MQTT_BROKER_URI       CONFIG_SD_MQTT_BROKER_URI

/*
 * Fall detection thresholds.
 * Free-fall phase: resultant acceleration below LOW_G_THRESHOLD.
 * Impact phase:    resultant acceleration above HIGH_G_THRESHOLD.
 * Impact must follow free-fall within IMPACT_WINDOW_MS.
 *
 * These values should be validated against experiment fall scenarios.
 */
#define LOW_G_THRESHOLD_MS2   3.0f   /* m/s² — free-fall indicator */
#define HIGH_G_THRESHOLD_MS2  25.0f  /* m/s² — impact indicator */
#define IMPACT_WINDOW_MS      500    /* max ms between free-fall and impact */

static const char *TAG = "pn06_fall";

/* ── State ──────────────────────────────────────────────────────────────── */

typedef enum {
    FALL_STATE_IDLE,
    FALL_STATE_FREE_FALL,   /* low-G phase detected */
    FALL_STATE_CONFIRMED,   /* high-G impact detected after free-fall */
} fall_state_t;

static esp_mqtt_client_handle_t s_mqtt;
static volatile bool            s_mqtt_connected = false;
static fall_state_t             s_fall_state     = FALL_STATE_IDLE;
static int64_t                  s_freefall_ms    = 0;
static bool                     s_event_sent     = false;

/* ── IMU stub ───────────────────────────────────────────────────────────── */
/*
 * Replace with actual MPU-6050 / ICM-42688-P I2C read.
 * Returns resultant acceleration magnitude in m/s².
 */
static bool read_imu_accel_magnitude(float *out_ms2)
{
    /*
     * Replace with actual MPU-6050 / ICM-42688-P I2C read.
     * ESP32-C3 Super Mini I2C pin recommendation:
     *   SDA = GPIO8,  SCL = GPIO10
     * (GPIO matrix allows any pin; avoid GPIO0/1 for ADC conflict)
     * Initialize with: i2c_config_t conf = { .sda_io_num = GPIO_NUM_8,
     *                                         .scl_io_num = GPIO_NUM_10, ... }
     */
    *out_ms2 = 9.8f;
    return true;
}

/* ── Publish fall evidence ──────────────────────────────────────────────── */

static void publish_fall_event(int64_t ts_ms)
{
    char ctx_buf[512], wrapper_buf[SD_PAYLOAD_MAX_LEN];
    const char *env_json =
        "{\"occupancy_detected\":true,\"doorbell_detected\":false}";

    sd_routing_meta_t meta = {
        .source_id             = NODE_SOURCE_ID,
        .protocol              = "mqtt",
        .controlled_experiment = false,
    };

    int r = sd_build_pure_context(
        "emergency", "E004_FALL_DETECTED", ts_ms,
        env_json, "{}", ctx_buf, sizeof(ctx_buf));
    if (r < 0) { ESP_LOGE(TAG, "ctx overflow"); return; }

    r = sd_build_router_input(ctx_buf, &meta, wrapper_buf, sizeof(wrapper_buf));
    if (r < 0) { ESP_LOGE(TAG, "wrapper overflow"); return; }

    int msg_id = esp_mqtt_client_publish(
        s_mqtt, SD_TOPIC_EMERGENCY_EVENT, wrapper_buf, 0, SD_QOS_EMERGENCY, 0);
    ESP_LOGW(TAG, "FALL EVENT published, msg_id=%d", msg_id);
}

/* ── Detection task ─────────────────────────────────────────────────────── */

static void fall_detect_task(void *arg)
{
    float accel_ms2 = 0.0f;

    while (1) {
        vTaskDelay(pdMS_TO_TICKS(SAMPLE_INTERVAL_MS));
        if (!s_mqtt_connected) continue;

        if (!read_imu_accel_magnitude(&accel_ms2)) continue;

        int64_t now_ms = esp_timer_get_time() / 1000;

        switch (s_fall_state) {
        case FALL_STATE_IDLE:
            if (accel_ms2 < LOW_G_THRESHOLD_MS2) {
                s_fall_state  = FALL_STATE_FREE_FALL;
                s_freefall_ms = now_ms;
                s_event_sent  = false;
                ESP_LOGD(TAG, "free-fall phase detected, accel=%.2f", accel_ms2);
            }
            break;

        case FALL_STATE_FREE_FALL:
            if ((now_ms - s_freefall_ms) > IMPACT_WINDOW_MS) {
                /* No impact within window — ambiguous, reset conservatively. */
                ESP_LOGD(TAG, "impact window expired, resetting");
                s_fall_state = FALL_STATE_IDLE;
            } else if (accel_ms2 > HIGH_G_THRESHOLD_MS2) {
                s_fall_state = FALL_STATE_CONFIRMED;
                if (!s_event_sent && s_mqtt_connected) {
                    publish_fall_event(now_ms);
                    s_event_sent = true;
                }
            }
            break;

        case FALL_STATE_CONFIRMED:
            /* Require accel to return to normal range before next event. */
            if (accel_ms2 > LOW_G_THRESHOLD_MS2 && accel_ms2 < HIGH_G_THRESHOLD_MS2) {
                s_fall_state = FALL_STATE_IDLE;
                ESP_LOGI(TAG, "fall state reset to idle");
            }
            break;
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
        s_fall_state     = FALL_STATE_IDLE;
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
    ESP_LOGI(TAG, "PN-06 Fall Detection Node starting, source_id=%s", NODE_SOURCE_ID);

    esp_mqtt_client_config_t mcfg = {
        .broker.address.uri    = MQTT_BROKER_URI,
        .credentials.client_id = NODE_SOURCE_ID,
    };
    s_mqtt = esp_mqtt_client_init(&mcfg);
    esp_mqtt_client_register_event(s_mqtt, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(s_mqtt);

    xTaskCreate(fall_detect_task, "fall_task", 4096, NULL, 6, NULL);

    ESP_LOGI(TAG, "PN-06 ready — IMU sampling every %d ms", SAMPLE_INTERVAL_MS);
}
