/*
 * safe_deferral payload builder implementation.
 * See sd_payload.h for API contract.
 */

#include "sd_payload.h"
#include <stdio.h>
#include <string.h>

int sd_build_router_input(
    const char              *pure_context_json,
    const sd_routing_meta_t *meta,
    char                    *out_buf,
    size_t                   out_len
)
{
    int n = snprintf(out_buf, out_len,
        "{"
        "\"pure_context_payload\":%s,"
        "\"routing_metadata\":{"
            "\"source_id\":\"%s\","
            "\"protocol\":\"%s\","
            "\"controlled_experiment\":%s"
        "}"
        "}",
        pure_context_json,
        meta->source_id,
        meta->protocol,
        meta->controlled_experiment ? "true" : "false"
    );
    if (n < 0 || (size_t)n >= out_len) return -1;
    return n;
}

int sd_build_pure_context(
    const char *event_type,
    const char *event_code,
    int64_t     timestamp_ms,
    const char *env_json,
    const char *dev_json,
    char       *out_buf,
    size_t      out_len
)
{
    const char *env = env_json ? env_json : "{}";
    const char *dev = dev_json ? dev_json : "{}";
    int n = snprintf(out_buf, out_len,
        "{"
        "\"trigger_event\":{"
            "\"event_type\":\"%s\","
            "\"event_code\":\"%s\","
            "\"timestamp_ms\":%lld"
        "},"
        "\"environmental_context\":%s,"
        "\"device_states\":%s"
        "}",
        event_type,
        event_code,
        (long long)timestamp_ms,
        env,
        dev
    );
    if (n < 0 || (size_t)n >= out_len) return -1;
    return n;
}

int sd_build_ack(
    const char *command_id,
    const char *target_device,
    const char *ack_status,
    const char *source_id,
    int64_t     timestamp_ms,
    char       *out_buf,
    size_t      out_len
)
{
    int n = snprintf(out_buf, out_len,
        "{"
        "\"command_id\":\"%s\","
        "\"target_device\":\"%s\","
        "\"ack_status\":\"%s\","
        "\"source_id\":\"%s\","
        "\"timestamp_ms\":%lld"
        "}",
        command_id,
        target_device,
        ack_status,
        source_id,
        (long long)timestamp_ms
    );
    if (n < 0 || (size_t)n >= out_len) return -1;
    return n;
}
