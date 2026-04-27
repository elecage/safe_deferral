/*
 * safe_deferral payload builder helpers.
 *
 * All builders produce JSON strings aligned with:
 *   common/schemas/context_schema.json
 *   common/schemas/policy_router_input_schema.json
 *
 * Authority boundary: builders produce candidate context input only.
 * They do not produce policy decisions, validator output, or actuator
 * commands on behalf of the node.
 */
#pragma once

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

/* Maximum JSON payload size for physical node output. */
#define SD_PAYLOAD_MAX_LEN  1024

/*
 * Routing metadata included in every policy_router_input wrapper.
 * source_id must begin with "esp32." for physical nodes.
 */
typedef struct {
    const char *source_id;      /* e.g. "esp32.button_node_01" */
    const char *protocol;       /* always "mqtt" */
    bool        controlled_experiment;
} sd_routing_meta_t;

/*
 * Build a policy_router_input JSON wrapper around a pure_context_payload.
 *
 * pure_context_json: pre-built pure_context_payload JSON string.
 * meta:             routing metadata.
 * out_buf:          caller-supplied output buffer.
 * out_len:          size of out_buf.
 *
 * Returns number of bytes written (excluding NUL), or -1 on overflow.
 */
int sd_build_router_input(
    const char           *pure_context_json,
    const sd_routing_meta_t *meta,
    char                 *out_buf,
    size_t                out_len
);

/*
 * Build a pure_context_payload JSON string.
 *
 * event_type:   e.g. "user_input", "sensor_event", "emergency"
 * event_code:   e.g. "BUTTON_PRESS", "E001_GAS_ALERT"
 * timestamp_ms: epoch milliseconds (from SNTP or RTC).
 * env_json:     environmental_context JSON object string (or NULL).
 * dev_json:     device_states JSON object string (or NULL).
 *
 * Returns bytes written or -1 on overflow.
 */
int sd_build_pure_context(
    const char *event_type,
    const char *event_code,
    int64_t     timestamp_ms,
    const char *env_json,
    const char *dev_json,
    char       *out_buf,
    size_t      out_len
);

/*
 * Build an actuation ACK JSON payload.
 *
 * command_id:   echo of the command_id from actuation/command.
 * target_device: e.g. "living_room_light".
 * ack_status:   "SUCCESS" or "FAILURE".
 * source_id:    this node's source_id.
 * timestamp_ms: when the ACK was generated.
 *
 * Returns bytes written or -1 on overflow.
 */
int sd_build_ack(
    const char *command_id,
    const char *target_device,
    const char *ack_status,
    const char *source_id,
    int64_t     timestamp_ms,
    char       *out_buf,
    size_t      out_len
);
