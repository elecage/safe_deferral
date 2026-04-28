/*
 * sd_provision.c — WiFi provisioning via SoftAP + Captive Portal
 *
 * Sections:
 *   A. NVS load / save / erase
 *   B. WiFi STA connection
 *   C. DNS hijack server  (redirects all queries → 192.168.4.1)
 *   D. HTTP server        (serves config form, handles POST /save)
 *   E. SoftAP setup
 *   F. sd_prov_start()    (orchestrates C, D, E)
 */

#include "sd_provision.h"

#include <string.h>
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_http_server.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "lwip/sockets.h"
#include "lwip/netdb.h"
#include "esp_mac.h"
#include "esp_system.h"

static const char *TAG = "sd_prov";

/* ── NVS namespace / keys ───────────────────────────────────────────────── */
#define NVS_NS          "sd_prov"
#define NVS_KEY_SSID    "ssid"
#define NVS_KEY_PASS    "pass"
#define NVS_KEY_MQTT    "mqtt"

/* ── WiFi event group bits ──────────────────────────────────────────────── */
#define WIFI_CONNECTED_BIT  BIT0
#define WIFI_FAIL_BIT       BIT1

static EventGroupHandle_t s_wifi_eg;
static int                s_retry = 0;
#define MAX_RETRY  5

/* ════════════════════════════════════════════════════════════════════════════
 * A. NVS load / save / erase
 * ══════════════════════════════════════════════════════════════════════════*/

bool sd_prov_load(sd_prov_config_t *out)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NS, NVS_READONLY, &h) != ESP_OK) return false;

    size_t sz;
    bool ok = true;

    sz = sizeof(out->wifi_ssid);
    if (nvs_get_str(h, NVS_KEY_SSID, out->wifi_ssid, &sz) != ESP_OK) ok = false;

    sz = sizeof(out->wifi_password);
    if (nvs_get_str(h, NVS_KEY_PASS, out->wifi_password, &sz) != ESP_OK) ok = false;

    sz = sizeof(out->mqtt_broker_uri);
    if (nvs_get_str(h, NVS_KEY_MQTT, out->mqtt_broker_uri, &sz) != ESP_OK) ok = false;

    nvs_close(h);

    if (ok) {
        ESP_LOGI(TAG, "loaded config: ssid=%s mqtt=%s",
                 out->wifi_ssid, out->mqtt_broker_uri);
    }
    return ok;
}

void sd_prov_save(const sd_prov_config_t *cfg)
{
    nvs_handle_t h;
    ESP_ERROR_CHECK(nvs_open(NVS_NS, NVS_READWRITE, &h));
    ESP_ERROR_CHECK(nvs_set_str(h, NVS_KEY_SSID, cfg->wifi_ssid));
    ESP_ERROR_CHECK(nvs_set_str(h, NVS_KEY_PASS, cfg->wifi_password));
    ESP_ERROR_CHECK(nvs_set_str(h, NVS_KEY_MQTT, cfg->mqtt_broker_uri));
    ESP_ERROR_CHECK(nvs_commit(h));
    nvs_close(h);
    ESP_LOGI(TAG, "config saved to NVS");
}

void sd_prov_erase(void)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NS, NVS_READWRITE, &h) == ESP_OK) {
        nvs_erase_all(h);
        nvs_commit(h);
        nvs_close(h);
        ESP_LOGI(TAG, "provisioning config erased");
    }
}

/* ════════════════════════════════════════════════════════════════════════════
 * B. WiFi STA connection
 * ══════════════════════════════════════════════════════════════════════════*/

static void sta_event_handler(void *arg, esp_event_base_t base,
                               int32_t id, void *data)
{
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) {
        if (s_retry < MAX_RETRY) {
            esp_wifi_connect();
            s_retry++;
            ESP_LOGW(TAG, "WiFi retry %d/%d", s_retry, MAX_RETRY);
        } else {
            xEventGroupSetBits(s_wifi_eg, WIFI_FAIL_BIT);
        }
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *ev = data;
        ESP_LOGI(TAG, "WiFi connected, IP=" IPSTR, IP2STR(&ev->ip_info.ip));
        s_retry = 0;
        xEventGroupSetBits(s_wifi_eg, WIFI_CONNECTED_BIT);
    }
}

bool sd_prov_wifi_connect(const sd_prov_config_t *cfg, int timeout_s)
{
    s_wifi_eg = xEventGroupCreate();
    s_retry   = 0;

    esp_netif_create_default_wifi_sta();

    wifi_init_config_t init = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&init));

    esp_event_handler_instance_t h_wifi, h_ip;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, sta_event_handler, NULL, &h_wifi));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, sta_event_handler, NULL, &h_ip));

    wifi_config_t wcfg = {0};
    strncpy((char *)wcfg.sta.ssid,     cfg->wifi_ssid,     sizeof(wcfg.sta.ssid)     - 1);
    strncpy((char *)wcfg.sta.password, cfg->wifi_password, sizeof(wcfg.sta.password) - 1);
    wcfg.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wcfg));
    ESP_ERROR_CHECK(esp_wifi_start());
    esp_wifi_connect();

    EventBits_t bits = xEventGroupWaitBits(s_wifi_eg,
        WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
        pdFALSE, pdFALSE,
        pdMS_TO_TICKS(timeout_s * 1000));

    esp_event_handler_instance_unregister(WIFI_EVENT, ESP_EVENT_ANY_ID, h_wifi);
    esp_event_handler_instance_unregister(IP_EVENT, IP_EVENT_STA_GOT_IP, h_ip);
    vEventGroupDelete(s_wifi_eg);

    if (bits & WIFI_CONNECTED_BIT) return true;

    ESP_LOGW(TAG, "WiFi connection failed");
    esp_wifi_stop();
    esp_wifi_deinit();
    return false;
}

/* ════════════════════════════════════════════════════════════════════════════
 * C. DNS hijack server
 *    Listens on UDP :53, responds to every A-query with 192.168.4.1
 *    so that any hostname the phone tries resolves to our AP address,
 *    triggering the captive-portal browser pop-up.
 * ══════════════════════════════════════════════════════════════════════════*/

#define DNS_PORT        53
#define DNS_BUF_SIZE    512

static void dns_server_task(void *arg)
{
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) { ESP_LOGE(TAG, "dns socket failed"); vTaskDelete(NULL); return; }

    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port   = htons(DNS_PORT),
        .sin_addr.s_addr = htonl(INADDR_ANY),
    };
    if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        ESP_LOGE(TAG, "dns bind failed");
        close(sock);
        vTaskDelete(NULL);
        return;
    }

    ESP_LOGI(TAG, "DNS hijack server listening on UDP :53");

    uint8_t buf[DNS_BUF_SIZE];
    struct sockaddr_in client;
    socklen_t client_len = sizeof(client);

    /* Response template: copy header, flip QR bit, add one A-record answer */
    while (1) {
        int len = recvfrom(sock, buf, sizeof(buf) - 1, 0,
                           (struct sockaddr *)&client, &client_len);
        if (len < 12) continue;  /* too short to be a valid DNS query */

        /*
         * Build minimal DNS response in-place:
         *   - Echo transaction ID (bytes 0-1)
         *   - Flags: QR=1, Opcode=0, AA=1, TC=0, RD=echo, RA=0, RCODE=0
         *   - QDCOUNT = 1 (echo)
         *   - ANCOUNT = 1
         *   - NSCOUNT = ARCOUNT = 0
         *   - Question section: echo original
         *   - Answer section: pointer to question + A record → 192.168.4.1
         */

        uint8_t resp[DNS_BUF_SIZE];
        int qlen = len;  /* include entire question in response */
        memcpy(resp, buf, qlen);

        /* Flags: response (0x8180 = QR+AA+RD) */
        resp[2] = 0x81;
        resp[3] = 0x80;
        /* ANCOUNT = 1 */
        resp[6] = 0x00;
        resp[7] = 0x01;
        /* NSCOUNT = ARCOUNT = 0 */
        resp[8] = resp[9] = resp[10] = resp[11] = 0x00;

        /* Answer: name pointer to offset 12 (0xC00C), type A, class IN,
         *         TTL 60, rdlength 4, rdata 192.168.4.1 */
        int rlen = qlen;
        resp[rlen++] = 0xC0; resp[rlen++] = 0x0C;  /* name pointer */
        resp[rlen++] = 0x00; resp[rlen++] = 0x01;  /* type A       */
        resp[rlen++] = 0x00; resp[rlen++] = 0x01;  /* class IN     */
        resp[rlen++] = 0x00; resp[rlen++] = 0x00;  /* TTL high     */
        resp[rlen++] = 0x00; resp[rlen++] = 0x3C;  /* TTL = 60 s   */
        resp[rlen++] = 0x00; resp[rlen++] = 0x04;  /* rdlength = 4 */
        resp[rlen++] = 192;  resp[rlen++] = 168;   /* 192.168.4.1  */
        resp[rlen++] = 4;    resp[rlen++] = 1;

        sendto(sock, resp, rlen, 0,
               (struct sockaddr *)&client, client_len);
    }
}

/* ════════════════════════════════════════════════════════════════════════════
 * D. HTTP server — config form + POST /save
 * ══════════════════════════════════════════════════════════════════════════*/

/* Minimal HTML form — kept short to fit in flash easily */
static const char *s_form_html =
    "<!DOCTYPE html><html><head>"
    "<meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>safe_deferral 설정 / Setup</title>"
    "<style>"
    "body{font-family:sans-serif;max-width:420px;margin:40px auto;padding:0 16px}"
    "h2{color:#333}label{display:block;margin-top:14px;font-weight:bold}"
    "input{width:100%;padding:8px;margin-top:4px;box-sizing:border-box;"
    "border:1px solid #ccc;border-radius:4px;font-size:16px}"
    "button{margin-top:20px;width:100%;padding:12px;background:#0066cc;"
    "color:#fff;border:none;border-radius:6px;font-size:16px;cursor:pointer}"
    "button:active{background:#0052a3}"
    ".note{font-size:12px;color:#666;margin-top:6px}"
    "</style></head><body>"
    "<h2>🔧 safe_deferral 노드 설정</h2>"
    "<p>Wi-Fi 및 MQTT 브로커 정보를 입력하세요.<br>"
    "<small>Enter Wi-Fi credentials and MQTT broker address.</small></p>"
    "<form method='POST' action='/save'>"
    "<label>Wi-Fi SSID</label>"
    "<input name='ssid' type='text' required maxlength='63' autocomplete='off'>"
    "<label>Wi-Fi 비밀번호 / Password</label>"
    "<input name='pass' type='password' maxlength='63' autocomplete='off'>"
    "<div class='note'>비밀번호가 없는 경우 비워두세요 / Leave empty for open networks</div>"
    "<label>MQTT 브로커 주소 / MQTT Broker URI</label>"
    "<input name='mqtt' type='text' required maxlength='127' "
    "placeholder='mqtt://192.168.1.100:1883'>"
    "<button type='submit'>저장 후 재시작 / Save &amp; Restart</button>"
    "</form></body></html>";

static const char *s_saved_html =
    "<!DOCTYPE html><html><head>"
    "<meta charset='utf-8'>"
    "<title>저장 완료 / Saved</title>"
    "<style>body{font-family:sans-serif;max-width:420px;margin:40px auto;"
    "padding:0 16px;text-align:center}</style></head><body>"
    "<h2>✅ 저장 완료!</h2>"
    "<p>설정이 저장되었습니다. 노드가 재시작됩니다.<br>"
    "<small>Settings saved. The node will restart and connect to your network.</small></p>"
    "</body></html>";

/* URL-decode a percent-encoded string in-place */
static void url_decode(char *dst, const char *src, size_t dst_size)
{
    size_t i = 0, j = 0;
    while (src[i] && j < dst_size - 1) {
        if (src[i] == '%' && src[i+1] && src[i+2]) {
            char hex[3] = { src[i+1], src[i+2], '\0' };
            dst[j++] = (char)strtol(hex, NULL, 16);
            i += 3;
        } else if (src[i] == '+') {
            dst[j++] = ' ';
            i++;
        } else {
            dst[j++] = src[i++];
        }
    }
    dst[j] = '\0';
}

/* Parse a single key=value from an application/x-www-form-urlencoded body */
static void parse_field(const char *body, const char *key,
                         char *out, size_t out_size)
{
    char search[72];
    snprintf(search, sizeof(search), "%s=", key);
    const char *p = strstr(body, search);
    if (!p) { out[0] = '\0'; return; }
    p += strlen(search);
    const char *end = strchr(p, '&');
    size_t flen = end ? (size_t)(end - p) : strlen(p);
    if (flen >= out_size) flen = out_size - 1;
    char raw[128] = {0};
    if (flen < sizeof(raw)) {
        memcpy(raw, p, flen);
        raw[flen] = '\0';
    }
    url_decode(out, raw, out_size);
}

/* State shared between HTTP handler and sd_prov_start() */
static volatile bool     s_prov_done = false;
static sd_prov_config_t  s_prov_result;

/* GET / and GET /config — serve the HTML form */
static esp_err_t handle_get_form(httpd_req_t *req)
{
    httpd_resp_set_type(req, "text/html");
    httpd_resp_send(req, s_form_html, HTTPD_RESP_USE_STRLEN);
    return ESP_OK;
}

/* POST /save — parse form body, save, trigger restart */
static esp_err_t handle_post_save(httpd_req_t *req)
{
    char body[512] = {0};
    int  received  = 0;
    int  remaining = req->content_len;

    while (remaining > 0) {
        int r = httpd_req_recv(req,
            body + received,
            (remaining < (int)(sizeof(body) - received - 1))
                ? remaining : (int)(sizeof(body) - received - 1));
        if (r <= 0) {
            httpd_resp_send_500(req);
            return ESP_FAIL;
        }
        received  += r;
        remaining -= r;
    }
    body[received] = '\0';

    parse_field(body, "ssid", s_prov_result.wifi_ssid,
                sizeof(s_prov_result.wifi_ssid));
    parse_field(body, "pass", s_prov_result.wifi_password,
                sizeof(s_prov_result.wifi_password));
    parse_field(body, "mqtt", s_prov_result.mqtt_broker_uri,
                sizeof(s_prov_result.mqtt_broker_uri));

    ESP_LOGI(TAG, "provisioning form: ssid='%s' mqtt='%s'",
             s_prov_result.wifi_ssid, s_prov_result.mqtt_broker_uri);

    if (s_prov_result.wifi_ssid[0] == '\0' ||
        s_prov_result.mqtt_broker_uri[0] == '\0') {
        /* Incomplete — send form back with error note */
        httpd_resp_set_type(req, "text/html");
        httpd_resp_set_status(req, "400 Bad Request");
        httpd_resp_sendstr(req,
            "<html><body><p style='color:red'>SSID and MQTT URI are required."
            "</p><a href='/'>Back / 돌아가기</a></body></html>");
        return ESP_OK;
    }

    httpd_resp_set_type(req, "text/html");
    httpd_resp_send(req, s_saved_html, HTTPD_RESP_USE_STRLEN);

    s_prov_done = true;   /* signal sd_prov_start() to proceed */
    return ESP_OK;
}

/*
 * Catch-all handler: redirect any unknown path to /config.
 * This is what makes iOS/Android show the captive-portal pop-up:
 * - iOS checks http://captive.apple.com/hotspot-detect.html
 * - Android checks http://clients3.google.com/generate_204
 * Both get redirected to our form.
 */
static esp_err_t handle_redirect(httpd_req_t *req)
{
    httpd_resp_set_status(req, "302 Found");
    httpd_resp_set_hdr(req, "Location", "http://192.168.4.1/config");
    httpd_resp_send(req, NULL, 0);
    return ESP_OK;
}

static httpd_handle_t start_http_server(void)
{
    httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
    cfg.uri_match_fn   = httpd_uri_match_wildcard;
    cfg.max_uri_handlers = 8;

    httpd_handle_t server = NULL;
    if (httpd_start(&server, &cfg) != ESP_OK) {
        ESP_LOGE(TAG, "failed to start HTTP server");
        return NULL;
    }

    httpd_uri_t uri_root   = { .uri="/",       .method=HTTP_GET,  .handler=handle_get_form  };
    httpd_uri_t uri_config = { .uri="/config",  .method=HTTP_GET,  .handler=handle_get_form  };
    httpd_uri_t uri_save   = { .uri="/save",    .method=HTTP_POST, .handler=handle_post_save };
    httpd_uri_t uri_catch  = { .uri="/*",       .method=HTTP_GET,  .handler=handle_redirect  };

    httpd_register_uri_handler(server, &uri_root);
    httpd_register_uri_handler(server, &uri_config);
    httpd_register_uri_handler(server, &uri_save);
    httpd_register_uri_handler(server, &uri_catch);

    return server;
}

/* ════════════════════════════════════════════════════════════════════════════
 * E. SoftAP setup
 * ══════════════════════════════════════════════════════════════════════════*/

static void start_softap(void)
{
    /* Build SSID from last 3 bytes of MAC: "sd-AABBCC" */
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_SOFTAP);
    char ssid[32];
    snprintf(ssid, sizeof(ssid), "sd-%02X%02X%02X",
             mac[3], mac[4], mac[5]);

    esp_netif_create_default_wifi_ap();

    wifi_init_config_t init = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&init));

    wifi_config_t ap_cfg = {
        .ap = {
            .ssid_len       = 0,
            .channel        = 6,
            .authmode       = WIFI_AUTH_OPEN,  /* open AP for easy access */
            .max_connection = 4,
        },
    };
    strncpy((char *)ap_cfg.ap.ssid, ssid, sizeof(ap_cfg.ap.ssid) - 1);

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &ap_cfg));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "SoftAP started: SSID='%s'  IP=192.168.4.1", ssid);
    ESP_LOGI(TAG, "Connect your phone to '%s' then open http://192.168.4.1", ssid);
}

/* ════════════════════════════════════════════════════════════════════════════
 * F. sd_prov_start() — main provisioning entry point
 * ══════════════════════════════════════════════════════════════════════════*/

void sd_prov_start(sd_prov_config_t *out)
{
    ESP_LOGI(TAG, "Starting provisioning mode");
    s_prov_done = false;
    memset(&s_prov_result, 0, sizeof(s_prov_result));

    /* nvs_flash_init / esp_netif_init / esp_event_loop_create_default
     * must already have been called by the caller (app_main). */
    start_softap();

    /* DNS hijack: runs in its own task so HTTP server isn't blocked */
    xTaskCreate(dns_server_task, "dns_srv", 4096, NULL, 5, NULL);

    /* HTTP server */
    httpd_handle_t server = start_http_server();
    if (!server) {
        ESP_LOGE(TAG, "cannot start HTTP server — halting");
        while (1) vTaskDelay(pdMS_TO_TICKS(1000));
    }

    /* Wait for user to submit the form */
    while (!s_prov_done) {
        vTaskDelay(pdMS_TO_TICKS(200));
    }

    /* Give the browser time to receive the "saved" page */
    vTaskDelay(pdMS_TO_TICKS(1500));

    /* Save to NVS */
    sd_prov_save(&s_prov_result);
    if (out) *out = s_prov_result;

    ESP_LOGI(TAG, "Provisioning complete — restarting...");
    esp_restart();
    /* does not return */
}
