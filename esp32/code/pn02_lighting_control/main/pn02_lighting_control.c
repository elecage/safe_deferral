/*
 * PN-02: Lighting Control Node
 *
 * Receives upstream-approved low-risk lighting commands from
 * safe_deferral/actuation/command and controls living_room_light /
 * bedroom_light GPIOs.  Reports ACK to safe_deferral/actuation/ack.
 *
 * Authority boundary:
 *   - Accepts only commands from actuation/command (upstream approved).
 *   - No acceptance of raw LLM candidates.
 *   - No local expansion of the low-risk catalog.
 *   - No non-lighting actuation.
 *   - Conservative startup: all lights OFF on boot and reconnect.
 */

#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "mqtt_client.h"
#include "cJSON.h"

#include "nvs_flash.h"
#include "../../shared/sd_mqtt_topics.h"
#include "../../shared/sd_payload.h"
#include "../../shared/sd_provision.h"

/* ── Configuration ─────────────────────────────────────────────────────── */

#define NODE_SOURCE_ID           "esp32.lighting_node_01"
/*
 * ESP32-C3 Super Mini: GPIO18/19 are USB D-/D+, not usable as outputs.
 * Use GPIO4 and GPIO5 instead.
 */
#define GPIO_LIVING_ROOM_LIGHT   GPIO_NUM_4
#define GPIO_BEDROOM_LIGHT       GPIO_NUM_5

/* Allowed target devices — no other devices may be controlled. */
#define DEVICE_LIVING_ROOM  "living_room_light"
#define DEVICE_BEDROOM      "bedroom_light"

/* Allowed actions from canonical low_risk_actions.json */
#define ACTION_LIGHT_ON   "light_on"
#define ACTION_LIGHT_OFF  "light_off"

static const char *TAG = "pn02_lighting";

/* ── State ──────────────────────────────────────────────────────────────── */

static esp_mqtt_client_handle_t s_mqtt;
static volatile bool            s_mqtt_connected = false;

/* ── Light control ──────────────────────────────────────────────────────── */

static gpio_num_t device_to_gpio(const char *device)
{
    if (strcmp(device, DEVICE_LIVING_ROOM) == 0) return GPIO_LIVING_ROOM_LIGHT;
    if (strcmp(device, DEVICE_BEDROOM)     == 0) return GPIO_BEDROOM_LIGHT;
    return GPIO_NUM_NC;
}

static void apply_light_command(const char *device, const char *action,
                                 bool *out_ok)
{
    gpio_num_t pin = device_to_gpio(device);
    if (pin == GPIO_NUM_NC) {
        ESP_LOGW(TAG, "unknown device '%s' — ignored", device);
        *out_ok = false;
        return;
    }
    if (strcmp(action, ACTION_LIGHT_ON) == 0) {
        gpio_set_level(pin, 1);
        *out_ok = true;
    } else if (strcmp(action, ACTION_LIGHT_OFF) == 0) {
        gpio_set_level(pin, 0);
        *out_ok = true;
    } else {
        /* Reject any action not in the low-risk catalog. */
        ESP_LOGW(TAG, "non-catalog action '%s' for '%s' — rejected", action, device);
        *out_ok = false;
    }
}

/* ── Command handler ────────────────────────────────────────────────────── */

static void handle_actuation_command(const char *data, int data_len)
{
    cJSON *root = cJSON_ParseWithLength(data, data_len);
    if (!root) {
        ESP_LOGE(TAG, "failed to parse command JSON");
        return;
    }

    const char *command_id   = cJSON_GetStringValue(cJSON_GetObjectItem(root, "command_id"));
    const char *action       = cJSON_GetStringValue(cJSON_GetObjectItem(root, "action"));
    const char *target_device = cJSON_GetStringValue(cJSON_GetObjectItem(root, "target_device"));

    if (!command_id || !action || !target_device) {
        ESP_LOGW(TAG, "command missing required fields, ignoring");
        cJSON_Delete(root);
        return;
    }

    ESP_LOGI(TAG, "command: id=%s action=%s device=%s", command_id, action, target_device);

    bool ok = false;
    apply_light_command(target_device, action, &ok);

    /* Publish ACK regardless of outcome so Mac mini gets closed-loop evidence. */
    char ack_buf[SD_PAYLOAD_MAX_LEN];
    int64_t now_ms = esp_timer_get_time() / 1000;
    int r = sd_build_ack(
        command_id, target_device,
        ok ? "SUCCESS" : "FAILURE",
        NODE_SOURCE_ID, now_ms,
        ack_buf, sizeof(ack_buf));
    if (r > 0 && s_mqtt_connected) {
        esp_mqtt_client_publish(s_mqtt, SD_TOPIC_ACTUATION_ACK, ack_buf, 0, SD_QOS_ACK, 0);
        ESP_LOGI(TAG, "ACK published: %s", ok ? "SUCCESS" : "FAILURE");
    }

    cJSON_Delete(root);
}

/* ── MQTT event handler ─────────────────────────────────────────────────── */

static void mqtt_event_handler(void *arg, esp_event_base_t base,
                                int32_t event_id, void *event_data)
{
    esp_mqtt_event_handle_t ev = event_data;
    switch (ev->event_id) {
    case MQTT_EVENT_CONNECTED:
        ESP_LOGI(TAG, "MQTT connected — subscribing to actuation/command");
        s_mqtt_connected = true;
        esp_mqtt_client_subscribe(s_mqtt, SD_TOPIC_ACTUATION_COMMAND, SD_QOS_CMD_SUB);
        /* Conservative reconnect: turn all lights off. */
        gpio_set_level(GPIO_LIVING_ROOM_LIGHT, 0);
        gpio_set_level(GPIO_BEDROOM_LIGHT, 0);
        ESP_LOGI(TAG, "reconnect safe state: all lights OFF");
        break;
    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGW(TAG, "MQTT disconnected");
        s_mqtt_connected = false;
        break;
    case MQTT_EVENT_DATA:
        if (strncmp(ev->topic, SD_TOPIC_ACTUATION_COMMAND,
                    (size_t)ev->topic_len) == 0) {
            handle_actuation_command(ev->data, ev->data_len);
        }
        break;
    case MQTT_EVENT_ERROR:
        ESP_LOGE(TAG, "MQTT error");
        break;
    default:
        break;
    }
}

/* ── GPIO init ──────────────────────────────────────────────────────────── */

static void gpio_init_lights(void)
{
    gpio_config_t cfg = {
        .pin_bit_mask = (1ULL << GPIO_LIVING_ROOM_LIGHT) | (1ULL << GPIO_BEDROOM_LIGHT),
        .mode         = GPIO_MODE_OUTPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    gpio_config(&cfg);
    /* Safe startup state: all lights OFF. */
    gpio_set_level(GPIO_LIVING_ROOM_LIGHT, 0);
    gpio_set_level(GPIO_BEDROOM_LIGHT, 0);
    ESP_LOGI(TAG, "lights GPIO initialized, startup state: OFF");
}

/* ── MQTT init ──────────────────────────────────────────────────────────── */

static void mqtt_init(const char *broker_uri)
{
    esp_mqtt_client_config_t cfg = {
        .broker.address.uri   = broker_uri,
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
    ESP_LOGI(TAG, "PN-02 Lighting Control Node starting, source_id=%s", NODE_SOURCE_ID);

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

    gpio_init_lights();
    mqtt_init(prov_cfg.mqtt_broker_uri);

    ESP_LOGI(TAG, "PN-02 ready — awaiting commands on %s", SD_TOPIC_ACTUATION_COMMAND);
}
