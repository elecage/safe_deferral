/*
 * safe_deferral MQTT topic constants.
 * Keep in sync with common/mqtt/topic_registry.json.
 *
 * Physical nodes publish only to the topics listed below.
 * No node may publish to validator/output, llm/candidate_action,
 * caregiver/confirmation, or audit/log as an authority source.
 */
#pragma once

/* --- Operational inputs (physical nodes publish here) --- */
#define SD_TOPIC_CONTEXT_INPUT        "safe_deferral/context/input"
#define SD_TOPIC_EMERGENCY_EVENT      "safe_deferral/emergency/event"
#define SD_TOPIC_ACTUATION_ACK        "safe_deferral/actuation/ack"

/* --- Operational outputs (physical nodes subscribe here) --- */
#define SD_TOPIC_ACTUATION_COMMAND    "safe_deferral/actuation/command"
#define SD_TOPIC_DEFERRAL_REQUEST     "safe_deferral/deferral/request"
#define SD_TOPIC_CLARIFICATION        "safe_deferral/clarification/interaction"

/* --- MQTT QoS levels used by physical nodes --- */
#define SD_QOS_CONTEXT   1   /* context/input: at-least-once */
#define SD_QOS_EMERGENCY 1   /* emergency/event: at-least-once */
#define SD_QOS_ACK       1   /* actuation/ack: at-least-once */
#define SD_QOS_CMD_SUB   1   /* actuation/command subscription */
