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
from preflight.readiness import PreflightManager
from result_store.store import ResultStore
from scenario_manager.manager import ScenarioManager
from mqtt_status.monitor import MqttStatusMonitor
from virtual_node_manager.manager import VirtualNodeManager
from virtual_node_manager.models import (
    VirtualNodeProfile, VirtualNodeState, VirtualNodeType, ACTUATOR_DEVICES,
)

_STATIC_DIR = pathlib.Path(__file__).parent / "static"


def create_app(
    experiment_manager: Optional[ExperimentManager] = None,
    result_store: Optional[ResultStore] = None,
    scenario_manager: Optional[ScenarioManager] = None,
    preflight_manager: Optional[PreflightManager] = None,
    mqtt_monitor: Optional[MqttStatusMonitor] = None,
    virtual_node_manager: Optional[VirtualNodeManager] = None,
    observation_store: Optional[ObservationStore] = None,
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
        profile = VirtualNodeProfile(
            profile_id=body.get("profile_id", f"profile_{node_type.value}"),
            payload_template=body.get("payload_template", {}),
            publish_topic=publish_topic,
            publish_interval_ms=int(body.get("publish_interval_ms", 1000)),
            repeat_count=int(body.get("repeat_count", 1)),
        )
        source_node_id = (
            body.get("source_node_id")
            or ("rpi.mock_actuator_controlled_mode" if is_simulator
                else f"rpi.virtual_{node_type.value}")
        )
        device_target = body.get("device_target") or None
        try:
            node = _vnm.create_node(
                node_type, profile,
                source_node_id=source_node_id,
                device_target=device_target,
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
        node.profile = VirtualNodeProfile(
            profile_id=body.get("profile_id", node.profile.profile_id),
            payload_template=body.get("payload_template", node.profile.payload_template),
            publish_topic=publish_topic,
            publish_interval_ms=int(body.get("publish_interval_ms", node.profile.publish_interval_ms)),
            repeat_count=int(body.get("repeat_count", node.profile.repeat_count)),
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

    # ------------------------------------------------------------------
    # Static files (after all routes so /docs still works)
    # ------------------------------------------------------------------

    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    return app
