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
    # Static files (after all routes so /docs still works)
    # ------------------------------------------------------------------

    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    return app
