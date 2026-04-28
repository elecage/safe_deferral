# STM32-05 Measurement Node Validation Checklist

Node: `stm32_time_probe_01`  
Board: STM32 Nucleo-H723ZG  
Firmware: `sd_measure` v1.0.0

---

## 1. Board Boot

| # | Check | Expected Output | Pass/Fail |
|---|-------|----------------|-----------|
| 1.1 | Board powers on | LD1 (green) lights up within 1 s | |
| 1.2 | UART3 TX active | Virtual COM port enumerates at 115200 | |
| 1.3 | Boot banner visible | `# sd_measure boot` followed by selftest lines | |
| 1.4 | No LD3 (red) LED during normal boot | LD3 off = READY | |

## 2. Firmware Version / Build ID

| # | Check | Expected | Pass/Fail |
|---|-------|----------|-----------|
| 2.1 | Firmware version in banner | `# SELFTEST_FW_VERSION: 1.0.0 PASS` | |
| 2.2 | Node ID in heartbeat | `"node_id":"stm32_time_probe_01"` | |

## 3. Timer Initialization

| # | Check | Expected | Pass/Fail |
|---|-------|----------|-----------|
| 3.1 | TIM2 counter advances | `# SELFTEST_TIMER: PASS` | |
| 3.2 | Timer resolution | Counter increments ~1000 per 1 ms (1 µs tick) | |
| 3.3 | No TIM2 init error logged | No `error_handler` invocation | |

## 4. Capture Channel Detection

| # | Check | Expected | Pass/Fail |
|---|-------|----------|-----------|
| 4.1 | CH_A synthetic push/pop | `# SELFTEST_CAPTURE_CH_A: PASS` | |
| 4.2 | CH_B synthetic push/pop | `# SELFTEST_CAPTURE_CH_B: PASS` | |
| 4.3 | CH_C synthetic push/pop | `# SELFTEST_CAPTURE_CH_C: PASS` | |
| 4.4 | CH_D synthetic push/pop | `# SELFTEST_CAPTURE_CH_D: PASS` | |
| 4.5 | Physical edge on PA0 (CH_A) | `DATA,1,<seq>,CH_A,...` row appears in UART output | |

## 5. Export Path

| # | Check | Expected | Pass/Fail |
|---|-------|----------|-----------|
| 5.1 | UART TX probe | `# SELFTEST_EXPORT: PASS` | |
| 5.2 | CSV header emitted on boot | `# HEADER: type,session_id,...` line visible | |
| 5.3 | DATA rows on capture | After SESSION_START, DATA rows appear per edge | |
| 5.4 | META row on session stop | `META,<id>,<experiment_id>,...` visible | |

## 6. RPi Preflight Integration

| # | Check | Expected | Pass/Fail |
|---|-------|----------|-----------|
| 6.1 | Heartbeat JSON emitted every 5 s | `{"type":"heartbeat",...}` line | |
| 6.2 | RPi can parse heartbeat | `readiness` field = `"READY"` | |
| 6.3 | STATUS command response | Send `STATUS\n` → `# STATUS node_id=stm32_time_probe_01 ...` | |

## 7. Session Control

| # | Check | Expected | Pass/Fail |
|---|-------|----------|-----------|
| 7.1 | SESSION_START command | `# SESSION_START session_id=1 experiment_id=TEST` | |
| 7.2 | Capture during session | DATA rows accumulate | |
| 7.3 | SESSION_STOP command | `# SESSION_STOP session_id=1 captures=<N>` | |
| 7.4 | SESSION_RESET clears state | Next SESSION_START gives session_id=2 | |

## 8. No Operational Side Effects

| # | Check | Expected | Pass/Fail |
|---|-------|----------|-----------|
| 8.1 | No MQTT publish | No MQTT traffic observed on broker | |
| 8.2 | No actuation command | Relay / GPIO outputs unchanged | |
| 8.3 | No policy routing | Mac mini routing log unaffected | |
| 8.4 | Capture ring full | Drop counter increments, no crash | |

---

## Machine-Readable Result Format

After running the checklist, emit this summary (can be parsed by RPi preflight):

```json
{
  "node_id": "stm32_time_probe_01",
  "fw_version": "1.0.0",
  "selftest_result": "READY",
  "checks": {
    "boot": true,
    "timer": true,
    "capture_ch_a": true,
    "capture_ch_b": true,
    "capture_ch_c": true,
    "capture_ch_d": true,
    "export": true,
    "no_operational_side_effects": true
  }
}
```

## Runbook for Repeated Class-Wise Latency Experiments

1. Confirm all checklist items above pass.
2. Wire capture inputs:
   - PA0 (CH_A) ← trigger source edge signal
   - PA1 (CH_B) ← hub/bridge observable event signal
   - PA2 (CH_C) ← actuator ACK edge signal
3. Open serial terminal at 115200 8N1 (or use RPi serial ingest script).
4. Send `SESSION_START <experiment_id>` before each run.
5. Run experiment scenario via RPi experiment runner.
6. Send `SESSION_STOP` after run completes.
7. Collect `DATA,...` rows and `META,...` row.
8. Transfer CSV to RPi result store.
9. Repeat from step 4 for each run (default 30 runs per class).
