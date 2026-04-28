"""Raspberry Pi experiment support node entry point.

Starts all RPi support services:
  - Dashboard API (port 8888) — read-only experiment monitoring
  - Governance UI (port 8889) — MQTT/payload governance browsing
  - MQTT status monitor — broker connectivity tracking
  - Virtual node manager — simulated sensor/actuator nodes
  - Preflight, experiment, scenario, result managers (available via dashboard)

MQTT topics subscribed for monitoring:
  safe_deferral/validator/output
  safe_deferral/actuation/command
  safe_deferral/audit/log
  safe_deferral/dashboard/observation

Environment variables (loaded from ~/smarthome_workspace/.env):
  MQTT_HOST     default: mac-mini.local
  MQTT_PORT     default: 1883
  MQTT_USER     default: (empty — anonymous)
  MQTT_PASS     default: (empty)
  DASHBOARD_PORT   default: 8888
  GOVERNANCE_PORT  default: 8889
"""

import json
import logging
import os
import sys
import threading
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Optional dotenv
# ---------------------------------------------------------------------------
_ENV_FILE = Path.home() / "smarthome_workspace" / ".env"
try:
    from dotenv import load_dotenv
    if _ENV_FILE.exists():
        load_dotenv(_ENV_FILE)
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Service imports
# ---------------------------------------------------------------------------
import paho.mqtt.client as mqtt

from dashboard.app import create_app
from experiment_manager.manager import ExperimentManager
from governance.backend import GovernanceBackend
from governance.ui_app import create_governance_app
from mqtt_status.monitor import MqttStatusMonitor
from preflight.readiness import PreflightManager
from result_store.store import ResultStore
from scenario_manager.manager import ScenarioManager
from virtual_node_manager.manager import VirtualNodeManager

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("sd.rpi")

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
MQTT_HOST = os.environ.get("MQTT_HOST", "mac-mini.local")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASS = os.environ.get("MQTT_PASS", "")
DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", "8888"))
GOVERNANCE_PORT = int(os.environ.get("GOVERNANCE_PORT", "8889"))

# Topics the RPi monitors (observation only — no actuation)
_MONITOR_TOPICS = [
    "safe_deferral/validator/output",
    "safe_deferral/actuation/command",
    "safe_deferral/audit/log",
    "safe_deferral/dashboard/observation",
]


# ---------------------------------------------------------------------------
# MQTT publisher adapter (for VirtualNodeManager)
# ---------------------------------------------------------------------------
class _PahoPublisher:
    def __init__(self, client: mqtt.Client) -> None:
        self._client = client

    def publish(self, topic: str, payload: dict, qos: int = 1) -> None:
        self._client.publish(topic, json.dumps(payload), qos=qos)


# ---------------------------------------------------------------------------
# FastAPI runner (uvicorn in a daemon thread)
# ---------------------------------------------------------------------------
def _start_fastapi(app, port: int, name: str) -> None:
    try:
        import uvicorn
    except ImportError:
        log.error("uvicorn not installed — %s on port %d will not start", name, port)
        return

    def run():
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

    t = threading.Thread(target=run, daemon=True, name=f"uvicorn-{name}")
    t.start()
    log.info("%s started on port %d", name, port)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    log.info("Safe Deferral — RPi experiment node starting …")
    log.info("MQTT broker: %s:%s", MQTT_HOST, MQTT_PORT)

    # --- MQTT client ---
    client = mqtt.Client(client_id="sd-rpi-node", clean_session=True)
    publisher = _PahoPublisher(client)

    # --- Service components ---
    mqtt_monitor = MqttStatusMonitor()
    preflight = PreflightManager()
    result_store = ResultStore()
    experiment_mgr = ExperimentManager()
    scenario_mgr = ScenarioManager()
    vnm = VirtualNodeManager(mqtt_publisher=publisher)
    governance_backend = GovernanceBackend()

    # --- Dashboard (port 8888) ---
    dashboard_app = create_app(
        experiment_manager=experiment_mgr,
        scenario_manager=scenario_mgr,
        result_store=result_store,
        preflight_manager=preflight,
        mqtt_monitor=mqtt_monitor,
    )
    _start_fastapi(dashboard_app, DASHBOARD_PORT, "dashboard")

    # --- Governance UI (port 8889) ---
    governance_app = create_governance_app(backend=governance_backend)
    _start_fastapi(governance_app, GOVERNANCE_PORT, "governance-ui")

    # --- MQTT callbacks ---
    def on_connect(c, userdata, flags, rc):
        if rc == 0:
            log.info("MQTT connected to %s:%s", MQTT_HOST, MQTT_PORT)
            mqtt_monitor.set_broker_reachable(True)
            for topic in _MONITOR_TOPICS:
                c.subscribe(topic, qos=1)
            log.info("Subscribed to %d monitor topics", len(_MONITOR_TOPICS))
        else:
            log.error("MQTT connect failed rc=%d", rc)
            mqtt_monitor.set_broker_reachable(False)

    def on_disconnect(c, userdata, rc):
        log.warning("MQTT disconnected rc=%d — will auto-reconnect", rc)
        mqtt_monitor.set_broker_reachable(False)

    def on_message(c, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            mqtt_monitor.observe_message(msg.topic)
            log.debug("Monitor received [%s]", msg.topic)
        except Exception as exc:
            log.error("MQTT parse error on %s: %s", msg.topic, exc)

    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS or None)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=2, max_delay=30)

    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    except Exception as exc:
        log.error("Could not connect to MQTT broker at %s:%s — %s", MQTT_HOST, MQTT_PORT, exc)
        log.error("Check that the Mac mini is running and MQTT_HOST is correct in ~/.smarthome_workspace/.env")
        sys.exit(1)

    log.info("Dashboard: http://localhost:%d", DASHBOARD_PORT)
    log.info("Governance: http://localhost:%d", GOVERNANCE_PORT)
    log.info("Entering main loop …")
    client.loop_forever()


if __name__ == "__main__":
    main()
