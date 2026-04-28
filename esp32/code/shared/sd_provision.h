/*
 * sd_provision.h — WiFi provisioning via SoftAP + Captive Portal
 *
 * Flow:
 *   1. sd_prov_load()        — try to load saved credentials from NVS
 *   2. sd_prov_wifi_connect() — connect with saved credentials
 *   3. If either fails → sd_prov_start() — open SoftAP, serve config form,
 *      block until user submits, save to NVS, then call esp_restart().
 *
 * Typical app_main usage:
 *
 *   sd_prov_config_t cfg;
 *   if (!sd_prov_load(&cfg) || !sd_prov_wifi_connect(&cfg, 30)) {
 *       sd_prov_start(&cfg);   // does not return — restarts on save
 *   }
 *   // WiFi connected.  Use cfg.mqtt_broker_uri.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

/* ── Stored configuration ───────────────────────────────────────────────── */

typedef struct {
    char wifi_ssid[64];
    char wifi_password[64];
    char mqtt_broker_uri[128];  /* e.g. "mqtt://192.168.1.100:1883" */
} sd_prov_config_t;

/* ── NVS helpers ────────────────────────────────────────────────────────── */

/**
 * Load previously saved provisioning config from NVS.
 * Returns true if a valid config was found.
 */
bool sd_prov_load(sd_prov_config_t *out);

/**
 * Save provisioning config to NVS.
 */
void sd_prov_save(const sd_prov_config_t *cfg);

/**
 * Erase saved config from NVS.
 * Calling this before reboot forces re-provisioning on next start.
 */
void sd_prov_erase(void);

/* ── WiFi connection ────────────────────────────────────────────────────── */

/**
 * Connect to WiFi using cfg credentials.
 * Blocks up to timeout_s seconds.
 * Returns true on successful IP assignment.
 */
bool sd_prov_wifi_connect(const sd_prov_config_t *cfg, int timeout_s);

/* ── SoftAP captive-portal provisioning ─────────────────────────────────── */

/**
 * Start the provisioning SoftAP and captive-portal HTTP server.
 * Blocks until the user submits valid credentials, then saves to NVS
 * and calls esp_restart().  This function does NOT return.
 *
 * SoftAP SSID: "sd-XXXXXX" where XXXXXX = last 3 bytes of MAC (hex).
 * SoftAP is open (no password) for easy first-time access.
 */
void sd_prov_start(sd_prov_config_t *out);
