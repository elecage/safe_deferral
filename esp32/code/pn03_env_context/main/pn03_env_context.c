/*
 * PN-03: Environmental Context Node
 *
 * Periodically samples temperature, illuminance, occupancy state and
 * publishes a context payload to safe_deferral/context/input.
 *
 * Authority boundary:
 *   - No autonomous action based on sensed values.
 *   - No unsupported schema fields.
 *   - Reports only schema-declared environmental_context fields.
 *   - Conservative invalid-reading handling: omit or default the field.
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

#include "nvs_flash.h"
#include "../../shared/sd_mqtt_topics.h"
#include "../../shared/sd_payload.h"
#include "../../shared/sd_provision.h"

/* ── Configuration ─────────────────────────────────────────────────────── */

#define NODE_SOURCE_ID      "esp32.env_context_node_01"
#define SAMPLE_INTERVAL_MS  10000   /* publish every 10 s */

/*
 * Sensor validity ranges (conservative — outside these the reading is
 * considered invalid and omitted).
 */
#define TEMP_MIN_C   (-20.0f)
#define TEMP_MAX_C   (60.0f)
#define LUX_MIN      0.0f
#define LUX_MAX      100000.0f

static const char *TAG = "pn03_env_ctx";

/* ── State ──────────────────────────────────────────────────────────────── */

static esp_mqtt_client_handle_t s_mqtt;
static volatile bool            s_mqtt_connected = false;

/* ── Sensor stubs ───────────────────────────────────────────────────────── */
/*
 * Replace these with actual sensor driver calls (e.g. DHT22, BH1750,
 * PIR).  Return false if the reading is invalid.
 */

static bool read_temperature(float *out_celsius)
{
    /* Stub: returns a fixed value.  Replace with hardware driver. */
    *out_celsius = 22.5f;
    return (*out_celsius >= TEMP_MIN_C && *out_celsius <= TEMP_MAX_C);
}

static bool read_illuminance(float *out_lux)
{
    /* Stub: returns a fixed value. */
    *out_lux = 450.0f;
    return (*out_lux >= LUX_MIN && *out_lux <= LUX_MAX);
}

static bool read_occupancy(bool *out_detected)
{
    /* Stub: PIR output.  Replace with gpio_get_level(PIR_GPIO). */
    *out_detected = false;
    return true;
}

/* ── Context publish task ───────────────────────────────────────────────── */

static void env_context_task(void *arg)
{
    char env_buf[256], ctx_buf[512], wrapper_buf[SD_PAYLOAD_MAX_LEN];

    sd_routing_meta_t meta = {
        .source_id             = NODE_SOURCE_ID,
        .protocol              = "mqtt",
        .controlled_experiment = false,
    };

    while (1) {
        vTaskDelay(pdMS_TO_TICKS(SAMPLE_INTERVAL_MS));

        if (!s_mqtt_connected) continue;

        float temp_c = 0.0f, lux = 0.0f;
        bool  occupancy = false;
        bool  temp_ok  = read_temperature(&temp_c);
        bool  lux_ok   = read_illuminance(&lux);
        bool  occ_ok   = read_occupancy(&occupancy);

        /*
         * Build environmental_context JSON.
         * Omit fields whose readings are invalid rather than publishing
         * out-of-range values.
         */
        int  pos = 0;
        char *p  = env_buf;
        int   rem = (int)sizeof(env_buf);

        pos = snprintf(p, rem, "{");
        p += pos; rem -= pos;

        bool first = true;

        if (temp_ok) {
            pos = snprintf(p, rem, "%s\"temperature\":%.1f", first ? "" : ",", temp_c);
            p += pos; rem -= pos; first = false;
        }
        if (lux_ok) {
            pos = snprintf(p, rem, "%s\"illuminance\":%.1f", first ? "" : ",", lux);
            p += pos; rem -= pos; first = false;
        }
        if (occ_ok) {
            pos = snprintf(p, rem, "%s\"occupancy_detected\":%s",
                           first ? "" : ",", occupancy ? "true" : "false");
            p += pos; rem -= pos; first = false;
        }
        /* doorbell_detected is always false for this node. */
        pos = snprintf(p, rem, "%s\"doorbell_detected\":false}", first ? "" : ",");
        p += pos;

        if (rem <= 0) { ESP_LOGE(TAG, "env_buf overflow"); continue; }

        int64_t now_ms = esp_timer_get_time() / 1000;
        int r = sd_build_pure_context(
            "sensor_event", "ENV_SAMPLE", now_ms,
            env_buf, "{}", ctx_buf, sizeof(ctx_buf));
        if (r < 0) { ESP_LOGE(TAG, "ctx overflow"); continue; }

        r = sd_build_router_input(ctx_buf, &meta, wrapper_buf, sizeof(wrapper_buf));
        if (r < 0) { ESP_LOGE(TAG, "wrapper overflow"); continue; }

        int msg_id = esp_mqtt_client_publish(
            s_mqtt, SD_TOPIC_CONTEXT_INPUT, wrapper_buf, 0, SD_QOS_CONTEXT, 0);
        ESP_LOGI(TAG, "published env context msg_id=%d temp=%.1f lux=%.1f occ=%d",
                 msg_id, temp_ok ? temp_c : 0.0f, lux_ok ? lux : 0.0f, (int)occupancy);
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
    case MQTT_EVENT_ERROR:
        ESP_LOGE(TAG, "MQTT error");
        break;
    default:
        break;
    }
}

/* ── MQTT init ──────────────────────────────────────────────────────────── */

static void mqtt_init(const char *broker_uri)
{
    esp_mqtt_client_config_t cfg = {
        .broker.address.uri    = broker_uri,
        .credentials.client_id = NODE_SOURCE_ID,
    };
    s_mqtt = esp_mqtt_client_init(&cfg);
    esp_mqtt_client_register_event(s_mqtt, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(s_mqtt);
    ESP_LOGI(TAG, "MQTT client started, broker=%s", broker_uri);
}

/* ── app_main ───────────────────────────────────────────────────────────── */

void app_main(void)
{
    ESP_LOGI(TAG, "PN-03 Environmental Context Node starting, source_id=%s", NODE_SOURCE_ID);

    esp_err_t nvs_err = nvs_flash_init();
    if (nvs_err == ESP_ERR_NVS_NO_FREE_PAGES || nvs_err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        nvs_err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(nvs_err);
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    sd_prov_config_t prov_cfg;
    if (!sd_prov_load(&prov_cfg) || !sd_prov_wifi_connect(&prov_cfg, 30)) {
        ESP_LOGW(TAG, "WiFi not configured or connect failed — starting provisioning");
        sd_prov_start(&prov_cfg);   /* does not return */
    }
    ESP_LOGI(TAG, "WiFi connected, broker=%s", prov_cfg.mqtt_broker_uri);

    mqtt_init(prov_cfg.mqtt_broker_uri);
    xTaskCreate(env_context_task, "env_ctx_task", 4096, NULL, 5, NULL);

    ESP_LOGI(TAG, "PN-03 ready — publishing every %d ms", SAMPLE_INTERVAL_MS);
}
