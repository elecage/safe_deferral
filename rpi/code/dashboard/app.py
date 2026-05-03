"""Web-Based Experiment Monitoring Dashboard (RPI-08).

FastAPI application served from the Raspberry Pi.

Authority boundary:
  - No direct registry-file editing.
  - No direct operational topic publishing.
  - No unrestricted actuator console.
  - No direct doorlock command button.
  - All create/update/run/export actions call backend service objects.
"""

import pathlib
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from observation_store import ObservationStore
from experiment_manager.manager import ExperimentManager
from experiment_manager.models import ExperimentFamily, RunParameters, RunState
from experiment_package.definitions import PACKAGES, PackageId
from experiment_package.fault_profiles import FAULT_PROFILES
from experiment_package.trial_store import TrialStore, compute_metrics
from experiment_package.runner import PackageRunner
from preflight.readiness import PreflightManager
from result_store.store import ResultStore
from scenario_manager.manager import ScenarioManager
from mqtt_status.monitor import MqttStatusMonitor
from virtual_node_manager.manager import VirtualNodeManager
from virtual_node_manager.models import (
    VirtualNodeProfile, VirtualNodeState, VirtualNodeType, ACTUATOR_DEVICES,
)
from node_presence.registry import NodePresenceRegistry

_STATIC_DIR = pathlib.Path(__file__).parent / "static"


def create_app(
    experiment_manager: Optional[ExperimentManager] = None,
    result_store: Optional[ResultStore] = None,
    scenario_manager: Optional[ScenarioManager] = None,
    preflight_manager: Optional[PreflightManager] = None,
    mqtt_monitor: Optional[MqttStatusMonitor] = None,
    virtual_node_manager: Optional[VirtualNodeManager] = None,
    observation_store: Optional[ObservationStore] = None,
    trial_store: Optional[TrialStore] = None,
    package_runner: Optional[PackageRunner] = None,
    node_presence_registry: Optional[NodePresenceRegistry] = None,
    sim_state=None,  # Optional[SimStateStore]
    sweep_runner=None,  # Optional[paper_eval.sweep_runner.SweepRunner]
) -> "FastAPI":
    if not _FASTAPI_AVAILABLE:
        raise ImportError("fastapi is required for the dashboard app")

    app = FastAPI(
        title="safe_deferral Experiment Dashboard",
        description="Experiment monitoring dashboard for RPi support layer.",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _em = experiment_manager or ExperimentManager()
    _rs = result_store or ResultStore()
    _sm = scenario_manager or ScenarioManager()
    _pm = preflight_manager or PreflightManager()
    _mm = mqtt_monitor or MqttStatusMonitor()
    _vnm = virtual_node_manager or VirtualNodeManager()
    _obs = observation_store or ObservationStore()
    _ts = trial_store or TrialStore()
    _pr = package_runner or PackageRunner(vnm=_vnm, obs_store=_obs, trial_store=_ts)
    _npr = node_presence_registry or NodePresenceRegistry()

    # SimStateStore — may be None when running unit tests without full wiring
    try:
        from sim_state_store import SimStateStore, ENV_SENSOR_FIELDS, DEVICE_FIELDS
        _sss = sim_state if sim_state is not None else SimStateStore()
    except ImportError:
        _sss = None
        ENV_SENSOR_FIELDS = {}
        DEVICE_FIELDS = {}

    # Paper-eval sweep runner (Phase 4 MVP). Optional: tests inject a fake;
    # production wires a real runner in main.py. None means the
    # /paper_eval/sweeps endpoints respond with 503.
    _sweep_runner = sweep_runner

    # ------------------------------------------------------------------
    # Health check — instant response, no IO
    # ------------------------------------------------------------------

    @app.get("/health", summary="Instant server health probe", include_in_schema=False)
    def health():
        return {"ok": True}

    # ------------------------------------------------------------------
    # Root — serve dashboard UI
    # ------------------------------------------------------------------

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def serve_ui():
        index = _STATIC_DIR / "index.html"
        if index.exists():
            return HTMLResponse(content=index.read_text(encoding="utf-8"))
        return HTMLResponse(content="<h1>Dashboard UI not found</h1>", status_code=404)

    # ------------------------------------------------------------------
    # Preflight
    # ------------------------------------------------------------------

    @app.get("/preflight", summary="Run preflight readiness check")
    def get_preflight():
        report = _pm.run_preflight()
        return report.to_dict()

    # ------------------------------------------------------------------
    # Experiment runs
    # ------------------------------------------------------------------

    @app.get("/runs", summary="List all experiment runs")
    def list_runs():
        return [r.to_summary_dict() for r in _em.list_runs()]

    @app.get("/runs/{run_id}", summary="Get a specific run summary")
    def get_run(run_id: str):
        run = _em.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        return run.to_summary_dict()

    @app.post("/runs", summary="Create and start a new experiment run")
    def create_run(body: dict):
        family_str = body.get("experiment_family", "class1_baseline")
        try:
            family = ExperimentFamily(family_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown family: {family_str}")
        params = RunParameters(
            experiment_family=family,
            scenario_ids=body.get("scenario_ids", []),
            trial_count=body.get("trial_count", 1),
            fault_profile_ids=body.get("fault_profile_ids", []),
        )
        run = _em.create_run(params)
        _em.start_run(run)
        _rs.save_run(run)
        return run.to_summary_dict()

    @app.post("/runs/{run_id}/abort", summary="Abort a running experiment")
    def abort_run(run_id: str):
        run = _em.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        _em.abort_run(run)
        return run.to_summary_dict()

    # ------------------------------------------------------------------
    # Results and exports
    # ------------------------------------------------------------------

    @app.get("/runs/{run_id}/export/json", summary="Export run as JSON")
    def export_json(run_id: str):
        run = _em.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        _rs.save_run(run)
        return JSONResponse(content={"json": _rs.export_json(run_id)})

    @app.get("/runs/{run_id}/export/markdown",
             summary="Export run as Markdown", response_class=PlainTextResponse)
    def export_markdown(run_id: str):
        run = _em.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        _rs.save_run(run)
        return _rs.export_markdown(run_id)

    @app.get("/runs/{run_id}/export/csv",
             summary="Export trial results as CSV", response_class=PlainTextResponse)
    def export_csv(run_id: str):
        run = _em.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        _rs.save_run(run)
        return _rs.export_csv(run_id)

    @app.get("/runs/{run_id}/metrics", summary="Compute metrics for a run")
    def get_metrics(run_id: str):
        run = _em.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        _rs.save_run(run)
        return _rs.compute_metrics(run_id)

    # ------------------------------------------------------------------
    # Scenarios
    # ------------------------------------------------------------------

    @app.get("/scenarios", summary="List available scenario contracts")
    def list_scenarios():
        return {"scenarios": _sm.list_scenario_files()}

    @app.get("/scenarios/results", summary="Get scenario execution results")
    def get_scenario_results():
        return [r.to_dict() for r in _sm.get_results()]

    @app.get("/scenarios/report/markdown",
             summary="Get scenario Markdown report", response_class=PlainTextResponse)
    def get_scenario_markdown():
        return _sm.export_markdown_report()

    @app.get("/scenarios/{filename}", summary="Get scenario contract content")
    def get_scenario(filename: str):
        try:
            return _sm.load_scenario(filename)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Scenario {filename} not found")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    # ------------------------------------------------------------------
    # MQTT / interface status
    # ------------------------------------------------------------------

    @app.get("/mqtt/status", summary="Get MQTT interface health report")
    def get_mqtt_status():
        return _mm.build_report().to_dict()

    # ------------------------------------------------------------------
    # Observations (dashboard/observation telemetry from Mac mini)
    # ------------------------------------------------------------------

    @app.get("/observations", summary="List recent dashboard observation payloads")
    def list_observations(limit: int = 50):
        return _obs.list_recent(limit=limit)

    @app.delete("/observations", summary="Clear observation buffer")
    def clear_observations():
        _obs.clear()
        return {"cleared": True}

    # ------------------------------------------------------------------
    # Virtual nodes
    # ------------------------------------------------------------------

    @app.get("/nodes", summary="List all virtual nodes")
    def list_nodes():
        return [n.to_dict() for n in _vnm.list_nodes()]

    @app.get("/nodes/actuator_devices", summary="List valid actuator device targets")
    def list_actuator_devices():
        return {"devices": ACTUATOR_DEVICES}

    @app.post("/nodes", summary="Create a virtual node")
    def create_node(body: dict):
        try:
            node_type = VirtualNodeType(body.get("node_type", "context_node"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid node_type")

        is_simulator = node_type == VirtualNodeType.ACTUATOR_SIMULATOR
        publish_topic = body.get(
            "publish_topic",
            "safe_deferral/actuation/ack" if is_simulator else "safe_deferral/context/input",
        )
        timing_claim = body.get("simulated_response_timing_ms")
        if timing_claim is not None and not isinstance(timing_claim, dict):
            raise HTTPException(
                status_code=400,
                detail="simulated_response_timing_ms must be an object or null",
            )
        profile = VirtualNodeProfile(
            profile_id=body.get("profile_id", f"profile_{node_type.value}"),
            payload_template=body.get("payload_template", {}),
            publish_topic=publish_topic,
            publish_interval_ms=int(body.get("publish_interval_ms", 1000)),
            repeat_count=int(body.get("repeat_count", 1)),
            simulated_response_timing_ms=timing_claim,
        )
        source_node_id = (
            body.get("source_node_id")
            or ("rpi.mock_actuator_controlled_mode" if is_simulator
                else f"rpi.virtual_{node_type.value}")
        )
        device_target = body.get("device_target") or None
        sensor_name = body.get("sensor_name") or None
        try:
            node = _vnm.create_node(
                node_type, profile,
                source_node_id=source_node_id,
                device_target=device_target,
                sensor_name=sensor_name,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return node.to_dict()

    @app.put("/nodes/{node_id}", summary="Update a virtual node profile")
    def update_node(node_id: str, body: dict):
        node = _vnm.get_node(node_id)
        if node is None:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        if node.state == VirtualNodeState.RUNNING:
            raise HTTPException(status_code=409, detail="Stop the node before updating")

        publish_topic = body.get("publish_topic", node.profile.publish_topic)
        # Merge incoming timing claim onto existing one so the modal's two
        # known keys (user_response_ms / caregiver_response_ms) do not wipe
        # other profile-declared keys. Explicit None in the body clears.
        if "simulated_response_timing_ms" in body:
            incoming = body["simulated_response_timing_ms"]
            if incoming is None:
                merged_timing = None
            elif isinstance(incoming, dict):
                merged_timing = dict(node.profile.simulated_response_timing_ms or {})
                merged_timing.update(incoming)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="simulated_response_timing_ms must be an object or null",
                )
        else:
            merged_timing = node.profile.simulated_response_timing_ms
        node.profile = VirtualNodeProfile(
            profile_id=body.get("profile_id", node.profile.profile_id),
            payload_template=body.get("payload_template", node.profile.payload_template),
            publish_topic=publish_topic,
            publish_interval_ms=int(body.get("publish_interval_ms", node.profile.publish_interval_ms)),
            repeat_count=int(body.get("repeat_count", node.profile.repeat_count)),
            simulated_response_timing_ms=merged_timing,
        )
        if "source_node_id" in body:
            try:
                _vnm._validate_source_id(body["source_node_id"])
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc))
            node.source_node_id = body["source_node_id"]
        if "device_target" in body:
            dt = body["device_target"] or None
            if dt is not None and dt not in ACTUATOR_DEVICES:
                raise HTTPException(status_code=400, detail=f"Invalid device_target: {dt}")
            node.device_target = dt
        return node.to_dict()

    @app.delete("/nodes/{node_id}", summary="Delete a virtual node")
    def delete_node(node_id: str):
        node = _vnm.get_node(node_id)
        if node is None:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        _vnm.delete_node(node_id)
        return {"deleted": node_id}

    @app.post("/nodes/{node_id}/start", summary="Start a virtual node")
    def start_node(node_id: str):
        node = _vnm.get_node(node_id)
        if node is None:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        _vnm.start_node(node)
        return node.to_dict()

    @app.post("/nodes/{node_id}/stop", summary="Stop a virtual node")
    def stop_node(node_id: str):
        node = _vnm.get_node(node_id)
        if node is None:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        _vnm.stop_node(node)
        return node.to_dict()

    @app.post("/nodes/{node_id}/publish", summary="Publish one message from a node")
    def publish_node(node_id: str):
        node = _vnm.get_node(node_id)
        if node is None:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        try:
            payload = _vnm.publish_once(node)
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return {"published": True, "payload": payload, "published_count": node.published_count}

    @app.post(
        "/nodes/{node_id}/interact",
        summary="Publish one message with a custom event_code (CLASS_2 user interaction)",
    )
    def interact_node(node_id: str, body: dict):
        """Publish a single message from this node with a temporarily overridden
        trigger_event.event_code and optionally event_type.

        The node's payload_template is not modified.  Use this to simulate a
        user button press (e.g. single_click to select a CLASS_2 candidate)
        while a trial's user-wait phase is active.

        Body fields:
          event_code  (required) — e.g. "single_click", "double_click", "triple_hit"
          event_type  (optional, default "button")
        """
        node = _vnm.get_node(node_id)
        if node is None:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

        event_code = body.get("event_code")
        if not event_code:
            raise HTTPException(status_code=400, detail="event_code is required")
        event_type = body.get("event_type", "button")

        # Temporarily override the trigger_event fields in the template
        import copy, time as _time
        original_template = node.profile.payload_template
        patched = copy.deepcopy(original_template)
        patched.setdefault("pure_context_payload", {})
        patched["pure_context_payload"].setdefault("trigger_event", {})
        patched["pure_context_payload"]["trigger_event"]["event_type"] = event_type
        patched["pure_context_payload"]["trigger_event"]["event_code"] = event_code
        patched["pure_context_payload"]["trigger_event"]["timestamp_ms"] = int(
            _time.time() * 1000
        )

        # Temporarily force RUNNING state so publish_once() proceeds even when
        # the node was stopped after a single-shot trial publish.  The state is
        # restored in the finally block regardless of outcome.
        original_state = node.state
        node.state = VirtualNodeState.RUNNING
        node.profile.payload_template = patched
        try:
            payload = _vnm.publish_once(node)
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        finally:
            node.state = original_state
            node.profile.payload_template = original_template

        return {
            "published": True,
            "event_type": event_type,
            "event_code": event_code,
            "payload": payload,
            "published_count": node.published_count,
        }

    # ------------------------------------------------------------------
    # Simulation State Store — live environment and device state
    # ------------------------------------------------------------------

    @app.get("/sim/state", summary="Get current simulation environment and device states")
    def get_sim_state():
        """Return the current SimStateStore snapshot.

        Context virtual nodes read this state at publish time to assemble
        the full pure_context_payload — so what you see here is what the
        Mac mini will receive as environmental_context and device_states
        on the next trigger publish.
        """
        if _sss is None:
            return {"env": {}, "devices": {}, "env_fields": [], "device_fields": {}}
        return _sss.to_dict()

    @app.post("/sim/state/env", summary="Update one or more environmental sensor values")
    def update_sim_env(body: dict):
        """Set environmental sensor values in the SimStateStore.

        Body: { "temperature": 28.0, "smoke_detected": true, ... }

        These values will be included in the next CONTEXT_NODE publish
        (and any ENV_SENSOR_NODE publishes will override them again).
        """
        if _sss is None:
            raise HTTPException(status_code=503, detail="SimStateStore not available")
        unknown = [k for k in body if k not in ENV_SENSOR_FIELDS]
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown env sensor fields: {unknown}. "
                       f"Allowed: {list(ENV_SENSOR_FIELDS.keys())}",
            )
        try:
            _sss.update_from_dict(env=body)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return _sss.to_dict()

    @app.post("/sim/state/device", summary="Update one or more device states")
    def update_sim_device(body: dict):
        """Set device states in the SimStateStore.

        Body: { "living_room_light": "on", "bedroom_light": "off", ... }
        """
        if _sss is None:
            raise HTTPException(status_code=503, detail="SimStateStore not available")
        unknown = [k for k in body if k not in DEVICE_FIELDS]
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown device fields: {unknown}. "
                       f"Allowed: {list(DEVICE_FIELDS.keys())}",
            )
        try:
            _sss.update_from_dict(devices=body)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return _sss.to_dict()

    @app.post("/sim/state/reset", summary="Reset simulation state to default values")
    def reset_sim_state():
        """Restore all environmental sensor and device state values to defaults."""
        if _sss is None:
            raise HTTPException(status_code=503, detail="SimStateStore not available")
        _sss.reset_to_defaults()
        return _sss.to_dict()

    @app.post(
        "/sim/nodes/sensor",
        summary="Create and start an ENV_SENSOR_NODE virtual node",
    )
    def create_sensor_node(body: dict):
        """Create an ENV_SENSOR_NODE for one environmental sensor field.

        Body fields:
          sensor_name  (required) — e.g. "temperature", "smoke_detected"
          value        (required) — initial value (number or bool)
          interval_ms  (optional, default 5000) — periodic publish interval

        The node is started automatically and publishes immediately so the
        SimStateStore reflects the new value at once.
        """
        sensor_name = body.get("sensor_name")
        if not sensor_name or sensor_name not in ENV_SENSOR_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"sensor_name must be one of {list(ENV_SENSOR_FIELDS.keys())}",
            )
        value = body.get("value")
        if value is None:
            raise HTTPException(status_code=400, detail="value is required")
        interval_ms = int(body.get("interval_ms", 5000))

        profile = VirtualNodeProfile(
            profile_id=f"env_sensor_{sensor_name}",
            payload_template={"sensor_name": sensor_name, "value": value},
            publish_topic="safe_deferral/sim/sensor",
            publish_interval_ms=interval_ms,
        )
        try:
            node = _vnm.create_node(
                VirtualNodeType.ENV_SENSOR_NODE,
                profile,
                source_node_id=f"rpi.virtual_env_sensor.{sensor_name}",
                sensor_name=sensor_name,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        _vnm.start_node(node)
        _vnm.publish_once(node)  # immediate publish to seed SimStateStore
        return node.to_dict()

    @app.post(
        "/sim/nodes/device",
        summary="Create and start a DEVICE_STATE_NODE virtual node",
    )
    def create_device_node(body: dict):
        """Create a DEVICE_STATE_NODE for one simulated actuator.

        Body fields:
          device_name  (required) — e.g. "living_room_light"
          state        (required) — initial state string (e.g. "off", "on")
          interval_ms  (optional, default 5000)

        The node is started automatically and publishes immediately.
        """
        device_name = body.get("device_name")
        if not device_name or device_name not in DEVICE_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"device_name must be one of {list(DEVICE_FIELDS.keys())}",
            )
        state = body.get("state", "off")
        interval_ms = int(body.get("interval_ms", 5000))

        profile = VirtualNodeProfile(
            profile_id=f"device_{device_name}",
            payload_template={"device_name": device_name, "state": state},
            publish_topic="safe_deferral/sim/device",
            publish_interval_ms=interval_ms,
        )
        try:
            node = _vnm.create_node(
                VirtualNodeType.DEVICE_STATE_NODE,
                profile,
                source_node_id=f"rpi.virtual_device.{device_name}",
                device_target=device_name,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        _vnm.start_node(node)
        _vnm.publish_once(node)  # immediate publish to seed SimStateStore
        return node.to_dict()

    @app.post(
        "/sim/nodes/sensor/{node_id}/value",
        summary="Update an existing ENV_SENSOR_NODE value and republish",
    )
    def update_sensor_node_value(node_id: str, body: dict):
        """Change the sensor value of an existing ENV_SENSOR_NODE and publish once.

        Body: { "value": <new_value> }

        Both the node template and the SimStateStore are updated so future
        periodic publishes will use the new value.
        """
        node = _vnm.get_node(node_id)
        if node is None:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        if node.node_type != VirtualNodeType.ENV_SENSOR_NODE:
            raise HTTPException(status_code=400, detail="Node is not an env_sensor_node")

        new_value = body.get("value")
        if new_value is None:
            raise HTTPException(status_code=400, detail="value is required")

        # Update the node template so periodic publishes use the new value
        import copy
        new_template = copy.deepcopy(node.profile.payload_template)
        new_template["value"] = new_value
        node.profile.payload_template = new_template

        # Publish immediately (force RUNNING state if needed)
        original_state = node.state
        node.state = VirtualNodeState.RUNNING
        try:
            payload = _vnm.publish_once(node)
        finally:
            node.state = original_state

        return {"published": True, "sensor_name": node.sensor_name, "value": new_value, "payload": payload}

    @app.post(
        "/sim/nodes/device/{node_id}/state",
        summary="Update an existing DEVICE_STATE_NODE state and republish",
    )
    def update_device_node_state(node_id: str, body: dict):
        """Change the device state of an existing DEVICE_STATE_NODE and publish once.

        Body: { "state": "on" }
        """
        node = _vnm.get_node(node_id)
        if node is None:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        if node.node_type != VirtualNodeType.DEVICE_STATE_NODE:
            raise HTTPException(status_code=400, detail="Node is not a device_state_node")

        new_state = body.get("state")
        if new_state is None:
            raise HTTPException(status_code=400, detail="state is required")

        import copy
        new_template = copy.deepcopy(node.profile.payload_template)
        new_template["state"] = new_state
        node.profile.payload_template = new_template

        original_state = node.state
        node.state = VirtualNodeState.RUNNING
        try:
            payload = _vnm.publish_once(node)
        finally:
            node.state = original_state

        return {"published": True, "device_name": node.device_target, "state": new_state, "payload": payload}

    # ------------------------------------------------------------------
    # Experiment packages (A~G definitions)
    # ------------------------------------------------------------------

    @app.get("/packages", summary="List experiment package definitions (A~G)")
    def list_packages():
        return [pkg.to_dict() for pkg in PACKAGES.values()]

    @app.get("/packages/{package_id}", summary="Get a single package definition")
    def get_package(package_id: str):
        try:
            pid = PackageId(package_id.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown package_id: {package_id!r}")
        pkg = PACKAGES.get(pid)
        if pkg is None:
            raise HTTPException(status_code=404, detail=f"Package {package_id} not found")
        return pkg.to_dict()

    # ------------------------------------------------------------------
    # Fault profiles
    # ------------------------------------------------------------------

    @app.get("/fault_profiles", summary="List all deterministic fault profiles")
    def list_fault_profiles():
        return [fp.to_dict() for fp in FAULT_PROFILES.values()]

    @app.get("/fault_profiles/{profile_id}", summary="Get a single fault profile")
    def get_fault_profile(profile_id: str):
        fp = FAULT_PROFILES.get(profile_id)
        if fp is None:
            raise HTTPException(status_code=404, detail=f"Fault profile {profile_id!r} not found")
        return fp.to_dict()

    # ------------------------------------------------------------------
    # Package runs
    # ------------------------------------------------------------------

    @app.post("/package_runs", summary="Create a package experiment run")
    def create_package_run(body: dict):
        package_id = body.get("package_id", "").upper()
        try:
            PackageId(package_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown package_id: {package_id!r}")

        run = _ts.create_run(
            package_id=package_id,
            scenario_ids=body.get("scenario_ids", []),
            fault_profile_ids=body.get("fault_profile_ids", []),
            trial_count=int(body.get("trial_count", 1)),
            comparison_condition=body.get("comparison_condition"),
        )
        return run.to_dict()

    @app.get("/package_runs", summary="List all package runs")
    def list_package_runs():
        return [r.to_dict() for r in _ts.list_runs()]

    @app.get("/package_runs/class2_phase_budgets",
             summary="Live CLASS_2 trial phase budgets (policy-derived)")
    def get_class2_phase_budgets():
        """Reflects the live PackageRunner attributes derived from
        policy_table.global_constraints. The dashboard fetches this so the
        rendered phase breakdown is the same value the runner actually uses
        — no hardcoded numbers in the dashboard.

        Trials carry their own snapshot (trial.class2_phase_budgets_snapshot)
        captured at trial creation time; that snapshot is the historically
        correct source for past trials. This endpoint is for the *current*
        budget that any new trial would receive.
        """
        return {
            "source": "policy_table.global_constraints + runner module defaults",
            "llm_budget_s": _pr._class2_llm_budget_s,
            "user_phase_timeout_s": _pr._class2_user_phase_timeout_s,
            "caregiver_phase_timeout_s": _pr._class2_caregiver_phase_timeout_s,
            "trial_timeout_slack_s": _pr._class2_trial_timeout_slack_s,
            "trial_timeout_s": _pr._class2_trial_timeout_s,
            "policy_fields": {
                "llm_request_timeout_ms": "global_constraints.llm_request_timeout_ms",
                "class2_clarification_timeout_ms": "global_constraints.class2_clarification_timeout_ms",
                "caregiver_response_timeout_ms": "global_constraints.caregiver_response_timeout_ms",
            },
        }

    @app.get("/package_runs/{run_id}", summary="Get package run status and trial list")
    def get_package_run(run_id: str):
        run = _ts.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Package run {run_id} not found")
        trials = _ts.list_trials_for_run(run_id)
        return {
            **run.to_dict(),
            "trials": [t.to_dict() for t in trials],
        }

    @app.get("/package_runs/{run_id}/metrics",
             summary="Compute paper-level metrics for a package run")
    def get_package_metrics(run_id: str):
        run = _ts.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Package run {run_id} not found")
        trials = _ts.list_trials_for_run(run_id)
        return compute_metrics(trials, run.package_id)

    @app.get("/package_runs/{run_id}/export/json",
             summary="Export package run trials as JSON")
    def export_package_json(run_id: str):
        run = _ts.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Package run {run_id} not found")
        trials = _ts.list_trials_for_run(run_id)
        return {"run": run.to_dict(), "trials": [t.to_dict() for t in trials]}

    @app.get("/package_runs/{run_id}/export/csv",
             summary="Export package run trials as CSV", response_class=PlainTextResponse)
    def export_package_csv(run_id: str):
        run = _ts.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Package run {run_id} not found")
        trials = _ts.list_trials_for_run(run_id)
        lines = [
            "trial_id,package_id,scenario_id,fault_profile_id,comparison_condition,"
            "expected_route_class,observed_route_class,expected_validation,"
            "observed_validation,latency_ms,pass_,status"
        ]
        for t in trials:
            lines.append(
                f"{t.trial_id},{t.package_id},{t.scenario_id},"
                f"{t.fault_profile_id or ''},"
                f"{t.comparison_condition or ''},"
                f"{t.expected_route_class},{t.observed_route_class or ''},"
                f"{t.expected_validation},{t.observed_validation or ''},"
                f"{t.latency_ms or ''},"
                f"{'true' if t.pass_ else 'false'},{t.status}"
            )
        return PlainTextResponse("\n".join(lines), media_type="text/csv")

    @app.get("/package_runs/{run_id}/export/markdown",
             summary="Export package run as Markdown report", response_class=PlainTextResponse)
    def export_package_markdown(run_id: str):
        run = _ts.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Package run {run_id} not found")
        trials = _ts.list_trials_for_run(run_id)
        metrics = compute_metrics(trials, run.package_id)
        completed = [t for t in trials if t.status == "completed"]
        lines = [
            f"# Package {run.package_id} Run Report",
            f"",
            f"**Run ID**: `{run.run_id}`  ",
            f"**Package**: {run.package_id}  ",
            f"**Trials**: {len(trials)} total, {len(completed)} completed  ",
            f"",
            f"## Metrics",
            f"",
            f"```json",
            __import__("json").dumps(metrics, indent=2),
            f"```",
            f"",
            f"## Trial Results",
            f"",
            f"| # | Scenario | Fault | Expected | Observed | Latency | Pass |",
            f"|---|---|---|---|---|---|---|",
        ]
        for i, t in enumerate(trials, 1):
            latency = f"{t.latency_ms:.0f}ms" if t.latency_ms else "—"
            pass_icon = "✅" if t.pass_ else ("⏳" if t.status == "pending" else "❌")
            lines.append(
                f"| {i} | {t.scenario_id} | {t.fault_profile_id or '—'} | "
                f"{t.expected_route_class} | {t.observed_route_class or '…'} | "
                f"{latency} | {pass_icon} |"
            )
        return PlainTextResponse("\n".join(lines))

    # ------------------------------------------------------------------
    # Individual trials
    # ------------------------------------------------------------------

    @app.post("/package_runs/{run_id}/trial",
              summary="Execute one trial (async — returns trial_id immediately)")
    def run_trial(run_id: str, body: dict):
        run = _ts.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Package run {run_id} not found")

        node_id = body.get("node_id")
        if not node_id:
            raise HTTPException(status_code=400, detail="node_id is required")

        fault_profile_id = body.get("fault_profile_id") or None
        try:
            trial = _pr.start_trial_async(
                run_id=run_id,
                package_id=run.package_id,
                node_id=node_id,
                scenario_id=body.get("scenario_id", run.scenario_ids[0] if run.scenario_ids else ""),
                fault_profile_id=fault_profile_id,
                comparison_condition=body.get("comparison_condition") or run.comparison_condition,
                expected_route_class=body.get("expected_route_class", "CLASS_1"),
                expected_validation=body.get("expected_validation", "approved"),
                expected_outcome=body.get("expected_outcome"),
                user_response_script=body.get("user_response_script"),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return trial.to_dict()

    @app.get("/trials/{trial_id}", summary="Get trial status and result")
    def get_trial(trial_id: str):
        trial = _ts.get_trial(trial_id)
        if trial is None:
            raise HTTPException(status_code=404, detail=f"Trial {trial_id} not found")
        return trial.to_dict()

    # ------------------------------------------------------------------
    # Node presence
    # ------------------------------------------------------------------

    @app.get("/node_presence", summary="List all tracked nodes (physical + virtual)")
    def get_node_presence():
        nodes = _npr.snapshot()
        online_physical = _npr.online_count(source="physical")
        online_virtual = _npr.online_count(source="virtual")
        return {
            "nodes": nodes,
            "summary": {
                "total": len(nodes),
                "online_physical": online_physical,
                "online_virtual": online_virtual,
                "online_total": online_physical + online_virtual,
            },
            "authority_note": (
                "Node presence is a monitoring artifact. "
                "It does not grant policy, validator, or actuator authority."
            ),
        }

    @app.get("/node_presence/{node_id}", summary="Get presence record for a specific node")
    def get_node_presence_by_id(node_id: str):
        entry = _npr.get(node_id)
        if entry is None:
            raise HTTPException(status_code=404, detail=f"Node {node_id!r} not tracked")
        return entry.to_dict()

    # ------------------------------------------------------------------
    # Paper-eval matrix sweep (Phase 4 MVP)
    # ------------------------------------------------------------------
    # All endpoints return 503 when sweep_runner is None (i.e. tests /
    # configurations that don't wire it). The runner is single-slot —
    # only one sweep can be in flight at a time.

    def _require_sweep_runner():
        if _sweep_runner is None:
            raise HTTPException(
                status_code=503,
                detail="paper-eval sweep runner not configured on this dashboard",
            )

    @app.post("/paper_eval/sweeps",
              summary="Start a paper-eval matrix sweep (single-slot)")
    def start_sweep(body: dict):
        _require_sweep_runner()
        matrix_path_str = body.get("matrix_path")
        node_id = body.get("node_id")
        if not matrix_path_str or not node_id:
            raise HTTPException(
                status_code=400,
                detail="Required: matrix_path (str), node_id (str)",
            )
        matrix_path = pathlib.Path(matrix_path_str)
        if not matrix_path.is_absolute():
            # Resolve relative paths against the dashboard's repo_root for
            # consistency with other paper_eval CLI usage.
            matrix_path = (_sweep_runner._repo_root / matrix_path).resolve()
        if not matrix_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"matrix file not found: {matrix_path}",
            )
        try:
            return _sweep_runner.start(
                matrix_path=matrix_path,
                node_id=node_id,
                per_trial_timeout_s=float(body.get("per_trial_timeout_s", 600.0)),
                poll_interval_s=float(body.get("poll_interval_s", 2.0)),
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

    @app.get("/paper_eval/sweeps/current",
             summary="Current sweep status + per-cell progress")
    def get_current_sweep():
        _require_sweep_runner()
        return _sweep_runner.get_state()

    @app.post("/paper_eval/sweeps/current/cancel",
              summary="Cancel the running sweep at the next safe point")
    def cancel_current_sweep():
        _require_sweep_runner()
        return _sweep_runner.cancel()

    def _require_artifact(state: dict, key: str, label: str) -> pathlib.Path:
        path_str = state.get(key)
        if not path_str:
            raise HTTPException(
                status_code=404,
                detail=f"{label} not yet produced (sweep status={state.get('status')})",
            )
        p = pathlib.Path(path_str)
        if not p.exists():
            raise HTTPException(
                status_code=410,
                detail=f"{label} path recorded but file no longer exists: {p}",
            )
        return p

    @app.get("/paper_eval/sweeps/current/manifest",
             summary="Download sweep_manifest.json for the current/last sweep")
    def get_current_manifest():
        _require_sweep_runner()
        state = _sweep_runner.get_state()
        path = _require_artifact(state, "manifest_path", "manifest")
        return JSONResponse(content=__import__("json").loads(path.read_text(encoding="utf-8")))

    @app.get("/paper_eval/sweeps/current/aggregated",
             summary="Download aggregated_matrix.json for the current/last sweep")
    def get_current_aggregated():
        _require_sweep_runner()
        state = _sweep_runner.get_state()
        path = _require_artifact(state, "aggregated_path", "aggregated matrix")
        return JSONResponse(content=__import__("json").loads(path.read_text(encoding="utf-8")))

    @app.get("/paper_eval/sweeps/current/digest.csv",
             summary="Download digest CSV (paper-ready, one row per cell)",
             response_class=PlainTextResponse)
    def get_current_digest_csv():
        _require_sweep_runner()
        state = _sweep_runner.get_state()
        path = _require_artifact(state, "digest_csv_path", "digest CSV")
        return PlainTextResponse(path.read_text(encoding="utf-8"),
                                 media_type="text/csv")

    @app.get("/paper_eval/sweeps/current/digest.md",
             summary="Download digest Markdown (paper-ready, sub-grid grouped)",
             response_class=PlainTextResponse)
    def get_current_digest_md():
        _require_sweep_runner()
        state = _sweep_runner.get_state()
        path = _require_artifact(state, "digest_md_path", "digest Markdown")
        return PlainTextResponse(path.read_text(encoding="utf-8"),
                                 media_type="text/markdown")

    # ------------------------------------------------------------------
    # Static files (after all routes so /docs still works)
    # ------------------------------------------------------------------

    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    return app
