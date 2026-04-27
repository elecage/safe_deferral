/*
 * PN-08: Doorlock Interface Node
 *
 * Governed representative doorlock interface.  Receives only explicitly
 * upstream-approved actuation/command messages and controls a relay/motor
 * for the lock mechanism.  Reports ACK, timeout, mismatch, and denied states.
 *
 * Authority boundary:
 *   - No autonomous Class 1 door unlock.
 *   - No unlock from doorbell_detected alone.
 *   - No direct dashboard command bypass.
 *   - No treating caregiver confirmation as validator approval.
 *   - Only commands with action="door_unlock" from actuation/command
 *     are processed, and only after upstream approval.
 *   - Conservative default: lock engaged on boot and reconnect.
 *
 * Note: door_unlock is NOT in the current Class 1 low-risk catalog.
 * This node exists solely as a sensitive-actuation evaluation target.
 * The Mac mini pipeline is responsible for all authority gates.
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

#include "../../shared/sd_mqtt_topics.h"
#include "../../shared/sd_payload.h"

/* ── Configuration ─────────────────────────────────────────────────────── */

#define NODE_SOURCE_ID        "esp32.doorlock_node_01"
#define GPIO_LOCK_RELAY       GPIO_NUM_21    /* HIGH = lock engaged */
#define GPIO_STATUS_LED       GPIO_NUM_22
#define LOCK_PULSE_MS         500            /* relay activation pulse */
#define CMD_TIMEOUT_MS        5000           /* max command processing time */
#define MQTT_BROKER_URI       CONFIG_SD_MQTT_BROKER_URI

/* Only this action string is accepted from actuation/command. */
#define GOVERNED_ACTION       "door_unlock"

static const char *TAG = "pn08_doorlock";

/* ── Lock state ─────────────────────────────────────────────────────────── */

typedef enum {
    LOCK_STATE_LOCKED   = 0,
    LOCK_STATE_UNLOCKED = 1,
    LOCK_STATE_FAULT    = 2,
} lock_state_t;

static esp_mqtt_client_handle_t s_mqtt;
static volatile bool            s_mqtt_connected = false;
static lock_state_t             s_lock_state     = LOCK_STATE_LOCKED;

/* ── Lock control ───────────────────────────────────────────────────────── */

static void lock_engage(void)
{
    gpio_set_level(GPIO_LOCK_RELAY, 1);  /* relay HIGH = lock engaged */
    gpio_set_level(GPIO_STATUS_LED, 0);
    s_lock_state = LOCK_STATE_LOCKED;
    ESP_LOGI(TAG, "lock engaged");
}

static void lock_disengage(void)
{
    gpio_set_level(GPIO_LOCK_RELAY, 0);  /* relay LOW = lock released */
    gpio_set_level(GPIO_STATUS_LED, 1);
    s_lock_state = LOCK_STATE_UNLOCKED;
    ESP_LOGI(TAG, "lock disengaged");
}

/* ── Command handler ────────────────────────────────────────────────────── */

static void handle_actuation_command(const char *data, int data_len)
{
    cJSON *root = cJSON_ParseWithLength(data, data_len);
    if (!root) {
        ESP_LOGE(TAG, "failed to parse command JSON");
        return;
    }

    const char *command_id    = cJSON_GetStringValue(cJSON_GetObjectItem(root, "command_id"));
    const char *action        = cJSON_GetStringValue(cJSON_GetObjectItem(root, "action"));
    const char *target_device = cJSON_GetStringValue(cJSON_GetObjectItem(root, "target_device"));

    if (!command_id || !action || !target_device) {
        ESP_LOGW(TAG, "command missing required fields");
        cJSON_Delete(root);
        return;
    }

    ESP_LOGI(TAG, "command received: id=%s action=%s device=%s",
             command_id, action, target_device);

    bool ok = false;
    const char *ack_status;

    if (strcmp(action, GOVERNED_ACTION) == 0 &&
        strcmp(target_device, "front_door_lock") == 0) {
        /*
         * Only execute if the upstream pipeline sent the explicit governed
         * action.  The Mac mini is responsible for all authority verification.
         * This node executes the physical actuation and reports evidence.
         */
        lock_disengage();
        vTaskDelay(pdMS_TO_TICKS(LOCK_PULSE_MS));
        lock_engage();   /* re-engage after pulse — latch requires explicit unlock command */
        ok = true;
        ack_status = "SUCCESS";
    } else {
        /*
         * Any other action or device is explicitly denied.
         * This enforces the boundary: no non-governed action executes.
         */
        ESP_LOGW(TAG, "action '%s' on device '%s' denied — not in governed path",
                 action, target_device);
        ack_status = "FAILURE";
    }

    /* Publish ACK as closed-loop evidence regardless of outcome. */
    char ack_buf[SD_PAYLOAD_MAX_LEN];
    int64_t now_ms = esp_timer_get_time() / 1000;
    int r = sd_build_ack(
        command_id, target_device ? target_device : "unknown",
        ack_status, NODE_SOURCE_ID, now_ms,
        ack_buf, sizeof(ack_buf));
    if (r > 0 && s_mqtt_connected) {
        esp_mqtt_client_publish(s_mqtt, SD_TOPIC_ACTUATION_ACK, ack_buf, 0, SD_QOS_ACK, 0);
        ESP_LOGI(TAG, "ACK published: %s for command_id=%s", ack_status, command_id);
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
        /* Conservative reconnect: ensure lock is engaged. */
        lock_engage();
        break;
    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGW(TAG, "MQTT disconnected — engaging lock (safe default)");
        s_mqtt_connected = false;
        lock_engage();
        break;
    case MQTT_EVENT_DATA:
        if (strncmp(ev->topic, SD_TOPIC_ACTUATION_COMMAND,
                    (size_t)ev->topic_len) == 0) {
            handle_actuation_command(ev->data, ev->data_len);
        }
        break;
    case MQTT_EVENT_ERROR:
        ESP_LOGE(TAG, "MQTT error — engaging lock (safe default)");
        lock_engage();
        break;
    default: break;
    }
}

/* ── GPIO init ──────────────────────────────────────────────────────────── */

static void gpio_init_lock(void)
{
    gpio_config_t cfg = {
        .pin_bit_mask = (1ULL << GPIO_LOCK_RELAY) | (1ULL << GPIO_STATUS_LED),
        .mode         = GPIO_MODE_OUTPUT,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    gpio_config(&cfg);
    lock_engage();  /* safe startup state */
}

/* ── app_main ───────────────────────────────────────────────────────────── */

void app_main(void)
{
    ESP_LOGI(TAG, "PN-08 Doorlock Interface Node starting, source_id=%s", NODE_SOURCE_ID);
    ESP_LOGI(TAG, "IMPORTANT: autonomous Class 1 unlock is BLOCKED by design");

    gpio_init_lock();

    esp_mqtt_client_config_t mcfg = {
        .broker.address.uri    = MQTT_BROKER_URI,
        .credentials.client_id = NODE_SOURCE_ID,
    };
    s_mqtt = esp_mqtt_client_init(&mcfg);
    esp_mqtt_client_register_event(s_mqtt, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(s_mqtt);

    ESP_LOGI(TAG, "PN-08 ready — lock ENGAGED, awaiting governed commands on %s",
             SD_TOPIC_ACTUATION_COMMAND);
}
