# 18. Scenario Node and Component Mapping

## 1. Purpose

This document summarizes the implementation elements required by the current scenario set.

It separates:

- physical or field-side **nodes** such as sensors, input devices, output devices, and actuator endpoints;
- system-level **components** such as Mac mini runtime modules, routing logic, validators, messaging infrastructure, and audit logging.

The document is intended to support hardware planning, node firmware development, system integration, and scenario-based verification.

This document should be interpreted together with:

- `common/docs/architecture/19_class2_clarification_architecture_alignment.md`
- `common/docs/architecture/20_scenario_data_flow_matrix.md`
- `common/schemas/clarification_interaction_schema.json`

---

## 2. Implementation Node Table

Nodes are physical, field-side, or user-facing endpoints. They may be implemented with ESP32, Raspberry Pi Pico W, Raspberry Pi, commercial smart-home devices, sensor modules, or output devices depending on the scenario.

| Category | Node | Main functions | Example hardware / parts | Used scenarios |
|---|---|---|---|---|
| User input | **Bounded Input Node** | Detect button input, debounce input, distinguish single input / repeated input / triple-hit input, collect candidate selection or confirmation input during Class 2 clarification | ESP32, Raspberry Pi Pico W, push button, large adaptive button, tact switch, pull-up/pull-down resistor, enclosure | Baseline, Class 1, Class 2, Class 2-to-Class 1, Class 2-to-Class 0, E002, Conflict Fault, Missing-State |
| Environmental context | **Context Node** | Collect illumination, occupancy, room context, and user-adjacent environmental state | ESP32/Pico W, light sensor, PIR sensor, mmWave sensor, temperature/humidity sensor | Baseline, Class 1, Class 2, Conflict Fault, Missing-State, E001-E005 |
| Occupancy/location | **Occupancy/Location Node** | Estimate the user's room-level location and occupancy status | PIR sensor, mmWave radar, BLE beacon/receiver, UWB module, Wi-Fi RSSI-based module | Class 1, Class 2, Conflict Fault, E005 |
| Lighting actuation | **Lighting Actuator Node** | Turn lights on/off only after Policy Router re-entry and Deterministic Validator approval; report current lighting state; return execution ACK | ESP32, relay module, SSR, smart plug, Matter light, LED light, MOSFET module | Baseline, Class 1, Class 2-to-Class 1, Conflict Fault, Missing-State |
| Device state reporting | **Device State Reporter Node** | Report light/device state periodically or by event; provide last state report time | ESP32/Pico W, relay feedback circuit, current sensor, Matter state query module | Baseline, Class 1, Class 2, Conflict Fault, Missing-State |
| Device health | **Device Health Reporter Node** | Report online/offline status, heartbeat, last response time, and communication health | ESP32 heartbeat firmware, watchdog timer, power-sense circuit, MQTT heartbeat | Missing-State, Class 2, Conflict Fault |
| Emergency aggregation | **Emergency Node** | Generate and publish emergency events from high temperature, smoke, gas, fall, or triple-hit evidence; may provide deterministic evidence for Class 2-to-Class 0 transition | ESP32/Pico W, integrated sensor board, MQTT emergency publisher | E001, E002, E003, E004, E005, Class 2-to-Class 0 |
| High temperature | **Temperature Sensor Node** | Measure indoor temperature, detect abnormal temperature, generate overheating evidence | DS18B20, DHT22, BME280, SHT31, MLX90614, ESP32/Pico W | E001 |
| Smoke detection | **Smoke Sensor Node** | Detect smoke or early fire indication and generate smoke event | MQ-2, photoelectric smoke sensor module, commercial smoke detector relay output, ESP32/Pico W | E003 |
| Gas detection | **Gas Sensor Node** | Detect gas leak or abnormal gas state and generate gas event | MQ-2, MQ-5, MQ-7, MQ-135, commercial gas detector relay output, ESP32/Pico W | E004 |
| Fall detection | **Fall Detection Node** | Generate fall or suspected-fall event | ESP32, IMU sensor, mmWave sensor, depth camera, wearable sensor | E005, Class 2-to-Class 0 |
| Wearable motion | **Wearable Sensor Node** | Detect acceleration, posture change, impact, and motion stop state | ESP32-C3/S3, MPU6050, MPU9250, ICM-20948, battery, charger module, wearable enclosure | E005 |
| Indoor motion | **Motion Sensor Node** | Detect indoor motion changes, prolonged no-motion, or abnormal stationary state | PIR sensor, mmWave radar, ToF sensor, ESP32/Pico W | E005, context support |
| Posture/space sensing | **Vision/Depth Sensor Node** | Detect fallen posture, floor proximity, and movement patterns | Depth camera, RGB camera, Raspberry Pi, edge-AI device, optional Coral TPU | E005 |
| Visitor context | **Doorbell/Visitor Context Node** | Provide doorbell press, visitor detection, and visitor-context state | ESP32, doorbell button, camera, PIR sensor, mmWave sensor, doorbell signal input circuit | Baseline, Class 1, Class 2, E001-E005, Conflict Fault, Missing-State |
| Voice input | **Voice Input Node** | Capture short user responses such as “1번”, “조명”, “긴급”, or “괜찮아요”; provides confirmation evidence only, not final routing authority | USB microphone, ReSpeaker mic array, smart-speaker bridge, Mac mini external microphone | Class 2, Class 2-to-Class 1, Class 2-to-Class 0, Conflict Fault, E005 |
| Voice output | **TTS/Voice Output Node** | Announce execution results, candidate choices, emergency warnings, status checks, and bounded Class 2 clarification prompts | USB speaker, 3.5 mm speaker, Bluetooth speaker, smart speaker, DFPlayer Mini | All scenarios |
| Visual output | **Display Output Node** | Display candidate choices, status messages, warning screens, and confirmation prompts | Small LCD/OLED, tablet, web dashboard, HDMI display, e-paper | Class 2, Conflict Fault, Missing-State, emergency scenarios |
| Warning output | **Warning Output Node** | Provide warning sound, beacon, LED, vibration, or other urgent alert output | Buzzer, siren, LED strip, beacon light, vibration motor, relay module | E001, E002, E003, E004, E005, Class 2-to-Class 0 |

---

## 3. System Component Table

System components are software, runtime, infrastructure, or logical modules. Most are expected to run on the Mac mini edge hub or as part of the local network and integration runtime.

| Category | Component | Main functions | Implementation form | Used scenarios |
|---|---|---|---|---|
| Central runtime | **Mac mini Edge Hub** | Receive MQTT messages, aggregate context, perform routing, call LLM guidance, coordinate validator, manage Class 2 clarification, dispatch validated commands, write audit records | Mac mini runtime, Python/Node service, Docker/venv | All scenarios |
| Messaging | **MQTT Broker / Messaging Layer** | Transmit context, emergency, command, and audit messages among nodes and runtime services | Mosquitto, Mac mini broker, Wi-Fi/Ethernet network | All scenarios |
| Input pattern analysis | **Input Pattern Detector** | Classify single input, repeated input, triple-hit, and candidate-selection input patterns | ESP32/Pico W firmware or Mac mini module | E002, Class 2, Class 2-to-Class 0, Conflict Fault |
| Input meaning mapping | **Input Context Mapper** | Link input patterns with current context to form candidate intent lists | Mac mini software module | Class 1, Class 2, Conflict Fault |
| Class 2 interaction | **Class 2 Clarification Manager** | Present bounded candidates, collect user/caregiver selection, handle timeout, record transition evidence, and request Policy Router re-entry for Class 0 / Class 1 / safe deferral; no actuation authority | Mac mini software module | Class 2, Class 2-to-Class 1, Class 2-to-Class 0, Conflict Fault, Missing-State |
| Candidate generation | **LLM Guidance Layer** | Generate bounded candidate choices and user-friendly guidance prompts; no final class decision or actuation authority | Mac mini local LLM, API-based LLM, prompt templates | Class 2, Conflict Fault |
| Policy classification | **Policy Router** | Classify inputs into Class 0, Class 1, Class 2, or fault-handling paths; receives Class 2 transition re-entry requests | Mac mini software module | All scenarios |
| Deterministic safety check | **Deterministic Validator** | Validate admissibility and block unsafe autonomous execution | Mac mini software module | Class 1, Class 2-to-Class 1, Conflict Fault, Missing-State |
| Command dispatch | **Actuator Dispatcher** | Send only validated commands to actuator nodes | Mac mini command publisher, MQTT command client | Baseline, Class 1, Class 2-to-Class 1, Conflict Fault |
| Caregiver escalation | **Caregiver Notification / Escalation Interface** | Send emergency alerts, confirmation requests, and help requests to caregiver or administrator | SMS/Kakao/email/app push gateway, REST API, MQTT bridge | Class 2, Conflict Fault, Missing-State, E001-E005 |
| Audit | **Audit Log** | Record input, candidates, decisions, transitions, execution, deferral, notification outcomes, selection results, timeout results, transition targets, and final safe outcomes | JSONL log, SQLite, file-based audit, dashboard integration | All scenarios |
| Context history | **Context History** | Store recent usage patterns, recent lighting events, and state-change history | DB, JSONL, SQLite, time-series log | Conflict Fault, Class 2 |
| Health checking | **Health Check Routine** | Re-request missing state, verify online status, and check last report time | Mac mini polling / heartbeat checker | Missing-State |
| Time sync | **Time Sync / Clock Source** | Maintain timestamp consistency across events | NTP, chrony, Mac mini system clock, optional RTC module | All scenarios |
| Network infrastructure | **Local Network Infrastructure** | Maintain ESP32/RPi/Mac mini connectivity and MQTT transport | Wi-Fi router, Ethernet switch, USB serial, power adapters | All scenarios |

---

## 4. Scenario-to-Node and Scenario-to-Component Mapping

| Scenario JSON | Required nodes | Required system components |
|---|---|---|
| `baseline_scenario_skeleton.json` | Bounded Input Node, Context Node, Lighting Actuator Node, Device State Reporter Node | Mac mini Edge Hub, MQTT Broker, Policy Router, Deterministic Validator, Actuator Dispatcher, Audit Log |
| `class1_baseline_scenario_skeleton.json` | Bounded Input Node, Context Node, Lighting Actuator Node, Device State Reporter Node | Mac mini Edge Hub, MQTT Broker, Policy Router, Deterministic Validator, Actuator Dispatcher, Audit Log |
| `class0_e001_scenario_skeleton.json` | Temperature Sensor Node, Emergency Node, Warning Output Node | Mac mini Edge Hub, MQTT Broker, Policy Router, Caregiver Notification, Audit Log |
| `class0_e002_scenario_skeleton.json` | Bounded Input Node, Emergency Node, TTS/Voice Output Node or Warning Output Node | Mac mini Edge Hub, MQTT Broker, Input Pattern Detector, Policy Router, Caregiver Notification, Audit Log |
| `class0_e003_scenario_skeleton.json` | Smoke Sensor Node, Emergency Node, Warning Output Node | Mac mini Edge Hub, MQTT Broker, Policy Router, Caregiver Notification, Audit Log |
| `class0_e004_scenario_skeleton.json` | Gas Sensor Node, Emergency Node, Warning Output Node | Mac mini Edge Hub, MQTT Broker, Policy Router, Caregiver Notification, Audit Log |
| `class0_e005_scenario_skeleton.json` | Fall Detection Node, at least one of Wearable/Motion/Vision Sensor Node, Emergency Node, TTS/Voice Output Node or Warning Output Node | Mac mini Edge Hub, MQTT Broker, Policy Router, Caregiver Notification, Audit Log |
| `class2_insufficient_context_scenario_skeleton.json` | Bounded Input Node, Context Node, Device State Reporter Node, TTS/Voice Output Node or Display Output Node | Mac mini Edge Hub, MQTT Broker, Class 2 Clarification Manager, LLM Guidance Layer, Policy Router, Deterministic Validator for Class 2-to-Class 1, Caregiver Notification when unresolved/sensitive, Audit Log |
| `class2_to_class1_transition_scenario` | Bounded Input Node, Context Node, Device State Reporter Node, Lighting Actuator Node, TTS/Voice Output Node or Display Output Node | Mac mini Edge Hub, MQTT Broker, Class 2 Clarification Manager, LLM Guidance Layer, Policy Router, Deterministic Validator, Actuator Dispatcher, ACK Handling, Audit Log |
| `class2_to_class0_transition_scenario` | Bounded Input Node or Voice Input Node, Emergency Node, TTS/Voice Output Node or Warning Output Node | Mac mini Edge Hub, MQTT Broker, Class 2 Clarification Manager, Policy Router, Caregiver Notification / Emergency Handling, Audit Log |
| `class2_timeout_safe_deferral_scenario` | Bounded Input Node, TTS/Voice Output Node or Display Output Node | Mac mini Edge Hub, MQTT Broker, Class 2 Clarification Manager, Safe Deferral Handler, Caregiver Notification when required, Audit Log |
| `conflict_fault_scenario_skeleton.json` | Bounded Input Node, Context Node, Occupancy/Location Node, Lighting Actuator Node, Device State Reporter Node, TTS/Voice Output Node or Display Output Node | Mac mini Edge Hub, MQTT Broker, Input Context Mapper, LLM Guidance Layer, Class 2 Clarification Manager, Policy Router, Deterministic Validator, Audit Log |
| `missing_state_scenario_skeleton.json` | Bounded Input Node, Context Node, Device State Reporter Node, Device Health Reporter Node, TTS/Voice Output Node or Display Output Node | Mac mini Edge Hub, MQTT Broker, Health Check Routine, Class 2 Clarification Manager when clarification is allowed, Policy Router, Deterministic Validator, Audit Log |

---

## 5. Interpretation Notes

### 5.1 Node versus component

A **node** is a deployed endpoint that senses, accepts input, controls a device, or provides user-facing output.

Examples:

```text
Bounded Input Node
Lighting Actuator Node
Smoke Sensor Node
TTS/Voice Output Node
Warning Output Node
```

A **component** is a runtime, software, infrastructure, or logical module that processes messages, reasons over context, validates decisions, dispatches commands, or records outcomes.

Examples:

```text
Policy Router
Deterministic Validator
Class 2 Clarification Manager
LLM Guidance Layer
Audit Log
```

### 5.2 Class 2 clarification implication

Class 2 should be treated as a clarification and transition state, not a simple terminal failure state.

The required interaction path is:

```text
Ambiguous or insufficient user input
→ Class 2 clarification
→ bounded candidate generation
→ user/caregiver confirmation, timeout, or deterministic emergency evidence
→ Policy Router re-entry
→ Class 1 bounded assistance, Class 0 emergency handling, safe deferral, or caregiver confirmation
```

Important boundaries:

```text
Class 2 Clarification Manager ≠ actuator authority
LLM Guidance Layer ≠ final class decision
Candidate prompt ≠ validator approval
Candidate prompt ≠ emergency trigger
Candidate prompt ≠ doorlock authorization
Clarification selection ≠ validator bypass
```

### 5.3 Class 2 interaction evidence

Class 2 clarification should leave auditable evidence for:

```text
- initial ambiguous or insufficient input;
- unresolved reason;
- generated candidate choices;
- presentation channel;
- user/caregiver selection;
- timeout or no-response result;
- transition target;
- Policy Router re-entry result;
- validator result when Class 1 is reached;
- emergency evidence when Class 0 is reached;
- final safe outcome.
```

### 5.4 Fault-scenario implication

Fault scenarios should not be treated as generic failures only.

- `conflict_fault_scenario_skeleton.json` means multiple plausible candidates remain simultaneously admissible.
- `missing_state_scenario_skeleton.json` means a required state report or health signal is absent.

Both should lead to conservative handling rather than unsafe autonomous execution. They may enter Class 2 clarification-like handling only when clarification is safe and bounded; otherwise they should remain in safe deferral or caregiver confirmation paths.

---

## 6. Recommended Implementation Order

A practical implementation order is:

```text
1. Mac mini Edge Hub + MQTT Broker + Audit Log
2. Bounded Input Node
3. Lighting Actuator Node + Device State Reporter Node
4. Context Node
5. Class 1 lighting assistance scenario
6. Missing-State and Conflict Fault handling
7. Class 2 Clarification Manager + TTS candidate presentation
8. Class 2-to-Class 1 transition validation
9. Class 2-to-Class 0 transition validation
10. Class 2 timeout / safe deferral validation
11. E002 triple-hit emergency request
12. E001/E003/E004 environmental emergency sensors
13. E005 fall detection
```

The recommended strategy is to stabilize lighting assistance first, then verify missing-state and conflict behavior, then add Class 2 clarification and transition tests, and finally attach emergency-sensor scenarios.
