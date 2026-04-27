"""Web-Based Experiment Monitoring Dashboard (RPI-08).

FastAPI application served from the Raspberry Pi.

Authority boundary:
  - No direct registry-file editing.
  - No direct operational topic publishing.
  - No unrestricted actuator console.
  - No direct doorlock command button.
  - All create/update/run/export actions call backend service objects.
"""

from typing import Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse, PlainTextResponse
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from experiment_manager.manager import ExperimentManager
from experiment_manager.models import ExperimentFamily, RunParameters, RunState
from preflight.readiness import PreflightManager
from result_store.store import ResultStore
from scenario_manager.manager import ScenarioManager
from mqtt_status.monitor import MqttStatusMonitor


def create_app(
    experiment_manager: Optional[ExperimentManager] = None,
    result_store: Optional[ResultStore] = None,
    scenario_manager: Optional[ScenarioManager] = None,
    preflight_manager: Optional[PreflightManager] = None,
    mqtt_monitor: Optional[MqttStatusMonitor] = None,
) -> "FastAPI":
    if not _FASTAPI_AVAILABLE:
        raise ImportError("fastapi is required for the dashboard app")

    app = FastAPI(
        title="safe_deferral Experiment Dashboard",
        description="Read-only experiment monitoring dashboard for RPi support layer.",
        version="1.0.0",
    )

    _em = experiment_manager or ExperimentManager()
    _rs = result_store or ResultStore()
    _sm = scenario_manager or ScenarioManager()
    _pm = preflight_manager or PreflightManager()
    _mm = mqtt_monitor or MqttStatusMonitor()

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

    # ------------------------------------------------------------------
    # MQTT / interface status
    # ------------------------------------------------------------------

    @app.get("/mqtt/status", summary="Get MQTT interface health report")
    def get_mqtt_status():
        return _mm.build_report().to_dict()

    return app
