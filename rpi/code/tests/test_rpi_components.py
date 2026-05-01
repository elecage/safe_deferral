"""Tests for all RPi experiment app components (RPI-01 through RPI-10)."""

import json
import pytest

from experiment_manager.manager import ExperimentManager
from experiment_manager.models import ExperimentFamily, RunParameters, RunState
from governance.backend import GovernanceBackend, ProposalStatus
from mqtt_status.monitor import MqttStatusMonitor, TopicHealth
from preflight.readiness import PreflightManager, ReadinessLevel
from result_store.store import ResultStore
from scenario_manager.manager import ScenarioManager
from virtual_behavior.behavior import (
    BehaviorProfile,
    BehaviorRunState,
    BehaviorType,
    VirtualBehaviorManager,
)
from virtual_node_manager.manager import VirtualNodeManager
from virtual_node_manager.models import (
    VirtualNodeProfile,
    VirtualNodeState,
    VirtualNodeType,
)

AUDIT_ID = "test_audit_rpi"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _run_params(family=ExperimentFamily.CLASS1_BASELINE, scenarios=None):
    return RunParameters(
        experiment_family=family,
        scenario_ids=scenarios or ["SCN_CLASS1_BASELINE"],
        trial_count=3,
    )


def _context_profile(profile_id="P_NORMAL"):
    return VirtualNodeProfile(
        profile_id=profile_id,
        payload_template={
            "routing_metadata": {"audit_correlation_id": AUDIT_ID,
                                  "ingest_timestamp_ms": 0, "network_status": "online"},
            "pure_context_payload": {},
        },
        publish_topic="safe_deferral/context/input",
    )


def _behavior_profile(behavior_type=BehaviorType.NORMAL_CONTEXT, fault_id=None):
    return BehaviorProfile(
        profile_id="BP_TEST",
        behavior_type=behavior_type,
        fault_profile_id=fault_id,
        base_payload={"a": {"b": 10}, "c": "hello"},
    )


# ==================================================================
# RPI-01: Experiment Manager
# ==================================================================

class TestExperimentManager:
    def test_create_run_pending(self):
        mgr = ExperimentManager()
        run = mgr.create_run(_run_params())
        assert run.state == RunState.PENDING

    def test_start_run_transitions_to_running(self):
        mgr = ExperimentManager()
        run = mgr.create_run(_run_params())
        mgr.start_run(run)
        assert run.state == RunState.RUNNING

    def test_start_run_records_checksums(self):
        mgr = ExperimentManager()
        run = mgr.create_run(_run_params())
        mgr.start_run(run)
        assert len(run.asset_checksums) > 0

    def test_complete_run(self):
        mgr = ExperimentManager()
        run = mgr.create_run(_run_params())
        mgr.start_run(run)
        mgr.complete_run(run)
        assert run.state == RunState.COMPLETED
        assert run.finished_at_ms is not None

    def test_fail_run_with_error(self):
        mgr = ExperimentManager()
        run = mgr.create_run(_run_params())
        mgr.start_run(run)
        mgr.fail_run(run, "simulated failure")
        assert run.state == RunState.FAILED
        assert run.error_message == "simulated failure"

    def test_abort_run(self):
        mgr = ExperimentManager()
        run = mgr.create_run(_run_params())
        mgr.start_run(run)
        mgr.abort_run(run)
        assert run.state == RunState.ABORTED

    def test_pause_and_resume(self):
        mgr = ExperimentManager()
        run = mgr.create_run(_run_params())
        mgr.start_run(run)
        mgr.pause_run(run)
        assert run.state == RunState.PAUSED
        mgr.resume_run(run)
        assert run.state == RunState.RUNNING

    def test_record_trial(self):
        mgr = ExperimentManager()
        run = mgr.create_run(_run_params())
        mgr.start_run(run)
        mgr.record_trial(run, {"scenario_id": "S1", "route_class": "CLASS_1"})
        assert len(run.trial_results) == 1

    def test_trial_index_increments(self):
        mgr = ExperimentManager()
        run = mgr.create_run(_run_params())
        mgr.start_run(run)
        mgr.record_trial(run, {"route_class": "CLASS_1"})
        mgr.record_trial(run, {"route_class": "CLASS_2"})
        assert run.trial_results[0]["trial_index"] == 0
        assert run.trial_results[1]["trial_index"] == 1

    def test_get_run(self):
        mgr = ExperimentManager()
        run = mgr.create_run(_run_params(), run_id="run-001")
        assert mgr.get_run("run-001") is run

    def test_list_runs_by_family(self):
        mgr = ExperimentManager()
        mgr.create_run(_run_params(ExperimentFamily.CLASS1_BASELINE))
        mgr.create_run(_run_params(ExperimentFamily.FAULT_INJECTION))
        assert len(mgr.list_runs_by_family(ExperimentFamily.CLASS1_BASELINE)) == 1

    def test_summary_dict_has_required_fields(self):
        mgr = ExperimentManager()
        run = mgr.create_run(_run_params())
        d = run.to_summary_dict()
        for field in ("run_id", "experiment_family", "state", "trial_count",
                      "trials_recorded"):
            assert field in d

    def test_host_info_recorded(self):
        mgr = ExperimentManager()
        run = mgr.create_run(_run_params())
        assert "platform" in run.host_info


# ==================================================================
# RPI-02: Result Store
# ==================================================================

class TestResultStore:
    def _make_run(self, n_trials=3, family=ExperimentFamily.CLASS1_BASELINE):
        mgr = ExperimentManager()
        run = mgr.create_run(_run_params(family))
        mgr.start_run(run)
        for i in range(n_trials):
            mgr.record_trial(run, {
                "route_class": "CLASS_1",
                "latency_ms": 100 + i * 10,
                "fault_outcome": "none",
            })
        mgr.complete_run(run)
        return run

    def test_save_and_get_run(self):
        store = ResultStore()
        run = self._make_run()
        store.save_run(run)
        assert store.get_run(run.run_id) is run

    def test_list_summaries(self):
        store = ResultStore()
        store.save_run(self._make_run())
        store.save_run(self._make_run())
        assert len(store.list_summaries()) == 2

    def test_metrics_total_trials(self):
        store = ResultStore()
        run = self._make_run(n_trials=5)
        store.save_run(run)
        m = store.compute_metrics(run.run_id)
        assert m["total_trials"] == 5

    def test_metrics_route_distribution(self):
        store = ResultStore()
        run = self._make_run(n_trials=3)
        store.save_run(run)
        m = store.compute_metrics(run.run_id)
        assert m["route_class_distribution"].get("CLASS_1") == 3

    def test_metrics_latency_stats(self):
        store = ResultStore()
        run = self._make_run(n_trials=3)
        store.save_run(run)
        m = store.compute_metrics(run.run_id)
        assert "min_ms" in m["latency_stats"]
        assert m["latency_stats"]["min_ms"] == 100

    def test_export_json_contains_summary(self):
        store = ResultStore()
        run = self._make_run()
        store.save_run(run)
        exported = json.loads(store.export_json(run.run_id))
        assert "summary" in exported
        assert "metrics" in exported

    def test_export_csv_has_header(self):
        store = ResultStore()
        run = self._make_run(n_trials=2)
        store.save_run(run)
        csv_text = store.export_csv(run.run_id)
        assert "route_class" in csv_text

    def test_export_markdown_contains_run_id(self):
        store = ResultStore()
        run = self._make_run()
        store.save_run(run)
        md = store.export_markdown(run.run_id)
        assert run.run_id in md

    def test_unknown_run_returns_empty_metrics(self):
        store = ResultStore()
        assert store.compute_metrics("no-such-run") == {}


# ==================================================================
# RPI-03: Virtual Node Manager
# ==================================================================

class TestVirtualNodeManager:
    def test_create_node(self):
        mgr = VirtualNodeManager()
        node = mgr.create_node(VirtualNodeType.CONTEXT_NODE, _context_profile())
        assert node.state == VirtualNodeState.CREATED

    def test_start_node(self):
        mgr = VirtualNodeManager()
        node = mgr.create_node(VirtualNodeType.CONTEXT_NODE, _context_profile())
        mgr.start_node(node)
        assert node.state == VirtualNodeState.RUNNING

    def test_stop_node(self):
        mgr = VirtualNodeManager()
        node = mgr.create_node(VirtualNodeType.CONTEXT_NODE, _context_profile())
        mgr.start_node(node)
        mgr.stop_node(node)
        assert node.state == VirtualNodeState.STOPPED

    def test_delete_node(self):
        mgr = VirtualNodeManager()
        node = mgr.create_node(VirtualNodeType.CONTEXT_NODE, _context_profile(),
                               node_id="del-node")
        mgr.delete_node("del-node")
        assert mgr.get_node("del-node") is None

    def test_publish_once_increments_count(self):
        mgr = VirtualNodeManager()
        node = mgr.create_node(VirtualNodeType.CONTEXT_NODE, _context_profile())
        mgr.start_node(node)
        mgr.publish_once(node)
        assert node.published_count == 1

    def test_publish_once_not_running_raises(self):
        mgr = VirtualNodeManager()
        node = mgr.create_node(VirtualNodeType.CONTEXT_NODE, _context_profile())
        with pytest.raises(RuntimeError):
            mgr.publish_once(node)

    def test_invalid_source_id_raises(self):
        mgr = VirtualNodeManager()
        with pytest.raises(ValueError, match="simulated origin"):
            mgr.create_node(VirtualNodeType.CONTEXT_NODE, _context_profile(),
                            source_node_id="esp32.real_node")

    def test_invalid_topic_raises(self):
        mgr = VirtualNodeManager()
        bad_profile = VirtualNodeProfile(
            profile_id="bad",
            payload_template={},
            publish_topic="safe_deferral/actuation/command",  # not allowed
        )
        with pytest.raises(ValueError, match="not in the allowed"):
            mgr.create_node(VirtualNodeType.CONTEXT_NODE, bad_profile)

    def test_list_running_nodes(self):
        mgr = VirtualNodeManager()
        n1 = mgr.create_node(VirtualNodeType.CONTEXT_NODE, _context_profile())
        n2 = mgr.create_node(VirtualNodeType.CONTEXT_NODE,
                              _context_profile("P2"), node_id="n2")
        mgr.start_node(n1)
        assert len(mgr.list_running_nodes()) == 1

    def test_node_to_dict(self):
        mgr = VirtualNodeManager()
        node = mgr.create_node(VirtualNodeType.CONTEXT_NODE, _context_profile())
        d = node.to_dict()
        for key in ("node_id", "node_type", "source_node_id", "state"):
            assert key in d


# ==================================================================
# RPI-04: Virtual Behavior Manager
# ==================================================================

class TestVirtualBehaviorManager:
    def test_create_run(self):
        mgr = VirtualBehaviorManager()
        run = mgr.create_run(_behavior_profile())
        assert run.state == BehaviorRunState.PENDING

    def test_execute_normal(self):
        mgr = VirtualBehaviorManager()
        run = mgr.create_run(_behavior_profile())
        payload = mgr.execute(run)
        assert run.state == BehaviorRunState.COMPLETED
        assert payload == {"a": {"b": 10}, "c": "hello"}

    def test_mutation_set(self):
        mgr = VirtualBehaviorManager()
        profile = _behavior_profile()
        profile.mutations = [{"op": "set", "path": "a.b", "value": 999}]
        run = mgr.create_run(profile)
        payload = mgr.execute(run)
        assert payload["a"]["b"] == 999

    def test_mutation_delete(self):
        mgr = VirtualBehaviorManager()
        profile = _behavior_profile()
        profile.mutations = [{"op": "delete", "path": "c"}]
        run = mgr.create_run(profile)
        payload = mgr.execute(run)
        assert "c" not in payload

    def test_mutation_subtract(self):
        mgr = VirtualBehaviorManager()
        profile = _behavior_profile()
        profile.mutations = [{"op": "subtract", "path": "a.b", "value": 3}]
        run = mgr.create_run(profile)
        payload = mgr.execute(run)
        assert payload["a"]["b"] == 7

    def test_stale_fault_profile_accepted(self):
        mgr = VirtualBehaviorManager()
        profile = _behavior_profile(
            behavior_type=BehaviorType.STALE_STATE,
            fault_id="FAULT_STALENESS_01",
        )
        run = mgr.create_run(profile)
        assert run.profile.fault_profile_id == "FAULT_STALENESS_01"

    def test_unknown_fault_profile_raises(self):
        mgr = VirtualBehaviorManager()
        profile = _behavior_profile(fault_id="FAULT_NONEXISTENT_99")
        with pytest.raises(ValueError, match="Unknown fault_profile_id"):
            mgr.create_run(profile)

    def test_run_to_dict(self):
        mgr = VirtualBehaviorManager()
        run = mgr.create_run(_behavior_profile())
        mgr.execute(run)
        d = run.to_dict()
        for key in ("run_id", "profile_id", "behavior_type", "state"):
            assert key in d


# ==================================================================
# RPI-05: Scenario Manager
# ==================================================================

class TestScenarioManager:
    def test_list_scenario_files(self):
        mgr = ScenarioManager()
        files = mgr.list_scenario_files()
        assert len(files) > 0
        assert any("class1" in f for f in files)

    def test_load_scenario(self):
        mgr = ScenarioManager()
        scenario = mgr.load_scenario("class1_baseline_scenario_skeleton.json")
        assert "scenario_id" in scenario
        assert "expected_outcomes" in scenario

    def test_execute_scenario_matched(self):
        mgr = ScenarioManager()
        scenario = mgr.load_scenario("class1_baseline_scenario_skeleton.json")
        # Provide all keys from expected_outcomes so _compare_outcomes passes
        observed = {
            "route_class": "CLASS_1",
            "routing_target": "CLASS_1",
            "llm_invocation_allowed": True,
            "llm_decision_invocation_allowed": True,
            "llm_guidance_generation_allowed": True,
            "unsafe_autonomous_actuation_allowed": False,
            "allowed_action_catalog_ref": "common/policies/low_risk_actions.json",
            "doorlock_autonomous_execution_allowed": False,
        }
        result = mgr.execute_scenario(scenario, observed)
        assert result.matched is True
        assert result.state.value == "passed"

    def test_execute_scenario_not_matched(self):
        mgr = ScenarioManager()
        scenario = mgr.load_scenario("class1_baseline_scenario_skeleton.json")
        observed = {"route_class": "CLASS_2"}
        result = mgr.execute_scenario(scenario, observed)
        assert result.matched is False
        assert result.state.value == "failed"

    def test_results_accumulated(self):
        mgr = ScenarioManager()
        scenario = mgr.load_scenario("class1_baseline_scenario_skeleton.json")
        mgr.execute_scenario(scenario, {"route_class": "CLASS_1",
                                         "doorlock_autonomous_execution_allowed": False})
        mgr.execute_scenario(scenario, {"route_class": "CLASS_2"})
        assert len(mgr.get_results()) == 2

    def test_export_json_report(self):
        mgr = ScenarioManager()
        scenario = mgr.load_scenario("class1_baseline_scenario_skeleton.json")
        mgr.execute_scenario(scenario, {"route_class": "CLASS_1",
                                         "doorlock_autonomous_execution_allowed": False})
        data = json.loads(mgr.export_json_report())
        assert isinstance(data, list)
        assert len(data) == 1

    def test_export_markdown_report(self):
        mgr = ScenarioManager()
        scenario = mgr.load_scenario("class1_baseline_scenario_skeleton.json")
        mgr.execute_scenario(scenario, {"route_class": "CLASS_1",
                                         "doorlock_autonomous_execution_allowed": False})
        md = mgr.export_markdown_report()
        assert "Scenario Execution Report" in md

    def test_result_to_dict(self):
        mgr = ScenarioManager()
        scenario = mgr.load_scenario("class1_baseline_scenario_skeleton.json")
        result = mgr.execute_scenario(scenario, {"route_class": "CLASS_1",
                                                   "doorlock_autonomous_execution_allowed": False})
        d = result.to_dict()
        for key in ("scenario_id", "state", "matched", "expected_outcome",
                    "observed_outcome"):
            assert key in d


# ==================================================================
# RPI-06: MQTT Status Monitor
# ==================================================================

class TestMqttStatusMonitor:
    def test_broker_reachable_false_initially(self):
        mon = MqttStatusMonitor()
        assert mon._broker_reachable is False

    def test_set_broker_reachable(self):
        mon = MqttStatusMonitor()
        mon.set_broker_reachable(True)
        report = mon.build_report()
        assert report.broker_reachable is True

    def test_unobserved_topic_is_missing(self):
        mon = MqttStatusMonitor()
        health = mon.get_topic_health("safe_deferral/context/input")
        assert health == TopicHealth.MISSING

    def test_observed_topic_is_healthy(self):
        mon = MqttStatusMonitor()
        mon.observe_message("safe_deferral/context/input",
                             timestamp_ms=int(__import__("time").time() * 1000))
        health = mon.get_topic_health("safe_deferral/context/input")
        assert health == TopicHealth.HEALTHY

    def test_report_has_registry_topics(self):
        mon = MqttStatusMonitor()
        report = mon.build_report()
        topic_names = {t.topic for t in report.topic_statuses}
        assert "safe_deferral/context/input" in topic_names

    def test_unexpected_topic_flagged(self):
        mon = MqttStatusMonitor()
        mon.observe_message("safe_deferral/not/in/registry",
                             timestamp_ms=int(__import__("time").time() * 1000))
        report = mon.build_report()
        unexpected = [t for t in report.topic_statuses
                      if t.health == TopicHealth.UNEXPECTED]
        assert len(unexpected) >= 1

    def test_authority_note_in_report(self):
        mon = MqttStatusMonitor()
        report = mon.build_report()
        assert "authority_note" in report.to_dict()

    def test_reset_clears_observations(self):
        mon = MqttStatusMonitor()
        mon.observe_message("safe_deferral/context/input",
                             timestamp_ms=int(__import__("time").time() * 1000))
        mon.reset()
        assert mon.get_topic_health("safe_deferral/context/input") == TopicHealth.MISSING

    def test_report_healthy_count(self):
        mon = MqttStatusMonitor()
        now = int(__import__("time").time() * 1000)
        mon.observe_message("safe_deferral/context/input", timestamp_ms=now)
        mon.observe_message("safe_deferral/actuation/command", timestamp_ms=now)
        report = mon.build_report()
        assert report.healthy_count >= 2


# ==================================================================
# RPI-07: Preflight Readiness Manager
# ==================================================================

class TestPreflightManager:
    def test_default_checks_ready(self):
        # Hardware-optional checks (physical nodes, STM32) will DEGRADE
        # in environments without the hardware. Required checks (canonical
        # assets, scenarios) must not be BLOCKED.
        mgr = PreflightManager()
        report = mgr.run_preflight()
        assert report.overall in (ReadinessLevel.READY, ReadinessLevel.DEGRADED)
        assert report.overall != ReadinessLevel.BLOCKED, (
            f"Required checks blocked: {report.blocked_reasons}"
        )

    def test_blocked_when_required_check_fails(self):
        mgr = PreflightManager()
        mgr.add_check(
            "always_fail",
            "This check always fails",
            required=True,
            check_fn=lambda: (ReadinessLevel.BLOCKED, "intentional failure"),
        )
        report = mgr.run_preflight()
        assert report.overall == ReadinessLevel.BLOCKED

    def test_degraded_when_optional_check_fails(self):
        mgr = PreflightManager()
        mgr.add_check(
            "optional_fail",
            "Optional check fails",
            required=False,
            check_fn=lambda: (ReadinessLevel.DEGRADED, "optional degraded"),
        )
        report = mgr.run_preflight()
        assert report.overall == ReadinessLevel.DEGRADED

    def test_blocked_reasons_listed(self):
        mgr = PreflightManager()
        mgr.add_check(
            "fail_check",
            "Failing",
            required=True,
            check_fn=lambda: (ReadinessLevel.BLOCKED, "reason A"),
        )
        report = mgr.run_preflight()
        assert any("reason A" in r for r in report.blocked_reasons)

    def test_checks_in_report(self):
        mgr = PreflightManager()
        report = mgr.run_preflight()
        assert len(report.checks) >= 2

    def test_report_to_dict(self):
        mgr = PreflightManager()
        report = mgr.run_preflight()
        d = report.to_dict()
        for key in ("overall", "generated_at_ms", "checks",
                    "blocked_reasons", "authority_note"):
            assert key in d

    def test_authority_note_no_policy_relaxation(self):
        mgr = PreflightManager()
        report = mgr.run_preflight()
        assert "policy" in report.authority_note.lower()

    def test_exception_in_check_gives_unknown(self):
        mgr = PreflightManager()
        mgr.add_check(
            "exc_check",
            "Raises exception",
            required=False,
            check_fn=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        report = mgr.run_preflight()
        exc_check = next((c for c in report.checks if c.check_id == "exc_check"), None)
        assert exc_check is not None
        assert exc_check.level == ReadinessLevel.UNKNOWN


# ==================================================================
# RPI-09: Governance Backend
# ==================================================================

class TestGovernanceBackend:
    def test_list_topics_not_empty(self):
        backend = GovernanceBackend()
        topics = backend.list_topics()
        assert len(topics) > 0

    def test_topic_has_required_fields(self):
        backend = GovernanceBackend()
        t = backend.list_topics()[0]
        assert "topic" in t
        assert "authority_level" in t

    def test_get_topic_found(self):
        backend = GovernanceBackend()
        t = backend.get_topic("safe_deferral/context/input")
        assert t is not None
        assert t["topic"] == "safe_deferral/context/input"

    def test_get_topic_not_found(self):
        backend = GovernanceBackend()
        assert backend.get_topic("safe_deferral/does/not/exist") is None

    def test_validate_valid_payload(self):
        backend = GovernanceBackend()
        payload = {
            "event_summary": "테스트 이벤트",
            "context_summary": "테스트 컨텍스트",
            "unresolved_reason": "insufficient_context",
            "manual_confirmation_path": "보호자 검토 경로",
        }
        report = backend.validate_payload_example(
            "class2_notification_payload_schema.json", payload
        )
        assert report.is_valid is True
        assert report.errors == []

    def test_validate_invalid_payload(self):
        backend = GovernanceBackend()
        report = backend.validate_payload_example(
            "class2_notification_payload_schema.json", {}
        )
        assert report.is_valid is False
        assert len(report.errors) > 0

    def test_validate_unknown_schema(self):
        backend = GovernanceBackend()
        report = backend.validate_payload_example("nonexistent_schema.json", {})
        assert report.is_valid is False

    def test_report_has_authority_note(self):
        backend = GovernanceBackend()
        report = backend.validate_payload_example(
            "class2_notification_payload_schema.json", {}
        )
        assert "authority_note" in report.to_dict()

    def test_create_proposal_draft(self):
        backend = GovernanceBackend()
        p = backend.create_proposal("safe_deferral/context/input", "Add X field")
        assert p.status == ProposalStatus.DRAFT

    def test_advance_proposal_to_proposed(self):
        backend = GovernanceBackend()
        p = backend.create_proposal("safe_deferral/context/input", "Add X")
        backend.advance_proposal(p.proposal_id, ProposalStatus.PROPOSED, "looks good")
        assert p.status == ProposalStatus.PROPOSED

    def test_advance_unknown_proposal_raises(self):
        backend = GovernanceBackend()
        with pytest.raises(KeyError):
            backend.advance_proposal("no-such-id", ProposalStatus.PROPOSED)

    def test_list_proposals_by_status(self):
        backend = GovernanceBackend()
        backend.create_proposal("t1", "change 1")
        p2 = backend.create_proposal("t2", "change 2")
        backend.advance_proposal(p2.proposal_id, ProposalStatus.PROPOSED)
        drafts = backend.list_proposals(ProposalStatus.DRAFT)
        proposed = backend.list_proposals(ProposalStatus.PROPOSED)
        assert len(drafts) == 1
        assert len(proposed) == 1

    def test_proposal_authority_note(self):
        backend = GovernanceBackend()
        p = backend.create_proposal("t", "desc")
        assert "authority" in p.to_dict()["authority_note"].lower()

    def test_export_proposals_report(self):
        backend = GovernanceBackend()
        backend.create_proposal("t", "desc")
        data = json.loads(backend.export_proposals_report())
        assert isinstance(data, list)
        assert len(data) == 1


# ==================================================================
# TrialStore — FAULT_CONTRACT_DRIFT_01 pass verdict
# ==================================================================

class TestTrialStoreContractDrift:
    """_is_pass() must return True for FAULT_CONTRACT_DRIFT_01 when obs_class is None."""

    def _make_drift_trial(self, obs_class=None, obs_val=None):
        from experiment_package.trial_store import TrialStore
        store = TrialStore()
        run = store.create_run(
            package_id="C",
            scenario_ids=[],
            fault_profile_ids=["FAULT_CONTRACT_DRIFT_01"],
            trial_count=1,
        )
        trial = store.create_trial(
            run_id=run.run_id,
            package_id="C",
            scenario_id="",
            fault_profile_id="FAULT_CONTRACT_DRIFT_01",
            comparison_condition=None,
            expected_route_class="CLASS_1",
            expected_validation="approved",
            expected_outcome="governance_verification_fail_no_runtime_authority",
            audit_correlation_id="drift-test-001",
        )
        return store, trial

    def test_no_observation_is_governance_pass(self):
        """complete_trial with no route_class → pass_ True (obs_class is None branch)."""
        store, trial = self._make_drift_trial()
        completed = store.complete_trial(
            trial.trial_id,
            {"audit_correlation_id": "drift-test-001", "governance_fault": "FAULT_CONTRACT_DRIFT_01"},
        )
        assert completed is not None
        assert completed.status == "completed"
        assert completed.pass_ is True
        assert completed.observed_route_class is None

    def test_class1_approved_observation_is_fail(self):
        """If the unregistered payload somehow routed as CLASS_1/approved, that is a fail."""
        store, trial = self._make_drift_trial()
        completed = store.complete_trial(
            trial.trial_id,
            {"route_class": "CLASS_1", "validation_status": "approved"},
        )
        assert completed.pass_ is False

    def test_class2_observation_is_pass(self):
        """Any route other than CLASS_1/approved counts as a governance-level pass."""
        store, trial = self._make_drift_trial()
        completed = store.complete_trial(
            trial.trial_id,
            {"route_class": "CLASS_2", "validation_status": None},
        )
        assert completed.pass_ is True

    def test_timeout_is_always_fail(self):
        """timeout_trial sets pass_=False; the fix must not timeout drift trials."""
        store, trial = self._make_drift_trial()
        result = store.timeout_trial(trial.trial_id)
        assert result.status == "timeout"
        assert result.pass_ is False


# ==================================================================
# PackageRunner — FAULT_CONTRACT_DRIFT_01 early-complete path
# ==================================================================

class TestPackageRunnerContractDrift:
    """PackageRunner must immediately complete drift trials instead of timing out."""

    def _make_runner_and_node(self):
        from experiment_package.trial_store import TrialStore
        from experiment_package.runner import PackageRunner
        from observation_store import ObservationStore

        class _RecordingPublisher:
            def __init__(self):
                self.published = []
            def publish(self, topic, payload, qos=1):
                self.published.append((topic, payload))

        pub = _RecordingPublisher()
        vnm = VirtualNodeManager(mqtt_publisher=pub)
        profile = VirtualNodeProfile(
            profile_id="drift_test_node",
            payload_template={
                "source_node_id": "rpi.virtual_context_node",
                "routing_metadata": {
                    "audit_correlation_id": "drift-runner-001",
                    "ingest_timestamp_ms": 0,
                    "network_status": "online",
                },
                "pure_context_payload": {
                    "trigger_event": {"event_type": "button", "event_code": "single_click", "timestamp_ms": 0},
                    "environmental_context": {
                        "temperature": 22.0, "illuminance": 200.0,
                        "occupancy_detected": True, "smoke_detected": False,
                        "gas_detected": False, "doorbell_detected": False,
                    },
                    "device_states": {
                        "living_room_light": "off", "bedroom_light": "off",
                        "living_room_blind": "closed", "tv_main": "off",
                    },
                },
            },
            publish_topic="safe_deferral/context/input",
        )
        node = vnm.create_node(VirtualNodeType.CONTEXT_NODE, profile)
        vnm.start_node(node)

        obs = ObservationStore()
        ts = TrialStore()
        runner = PackageRunner(vnm=vnm, obs_store=obs, trial_store=ts)
        return runner, ts, node

    def test_drift_trial_completes_not_timeout(self):
        """Trial with FAULT_CONTRACT_DRIFT_01 must end as completed, not timeout."""
        import time
        from experiment_package.fault_profiles import FAULT_PROFILES

        runner, store, node = self._make_runner_and_node()
        run = store.create_run(
            package_id="C",
            scenario_ids=[],
            fault_profile_ids=["FAULT_CONTRACT_DRIFT_01"],
            trial_count=1,
        )
        trial = runner.start_trial_async(
            run_id=run.run_id,
            package_id="C",
            node_id=node.node_id,
            scenario_id="",
            fault_profile_id="FAULT_CONTRACT_DRIFT_01",
            comparison_condition=None,
            expected_route_class="CLASS_1",
            expected_validation="approved",
            expected_outcome="governance_verification_fail_no_runtime_authority",
        )
        # The trial background thread should complete well within 2 s;
        # without the fix it would block for _TRIAL_TIMEOUT_S = 30 s.
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            t = store.get_trial(trial.trial_id)
            if t and t.status != "pending":
                break
            time.sleep(0.05)

        result = store.get_trial(trial.trial_id)
        assert result is not None
        assert result.status == "completed", f"expected completed, got {result.status}"
        assert result.pass_ is True

    def test_drift_trial_pass_in_metrics(self):
        """compute_metrics for Package C counts the drift trial as a pass."""
        import time
        from experiment_package.trial_store import compute_metrics

        runner, store, node = self._make_runner_and_node()
        run = store.create_run(
            package_id="C",
            scenario_ids=[],
            fault_profile_ids=["FAULT_CONTRACT_DRIFT_01"],
            trial_count=1,
        )
        trial = runner.start_trial_async(
            run_id=run.run_id,
            package_id="C",
            node_id=node.node_id,
            scenario_id="",
            fault_profile_id="FAULT_CONTRACT_DRIFT_01",
            comparison_condition=None,
            expected_route_class="CLASS_1",
            expected_validation="approved",
            expected_outcome="governance_verification_fail_no_runtime_authority",
        )
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            t = store.get_trial(trial.trial_id)
            if t and t.status != "pending":
                break
            time.sleep(0.05)

        trials = store.list_trials_for_run(run.run_id)
        metrics = compute_metrics(trials, "C")
        assert metrics["total"] >= 1
        # The drift trial must appear in the by_profile breakdown as a pass
        drift_bucket = metrics["by_profile"].get("FAULT_CONTRACT_DRIFT_01", {})
        assert drift_bucket.get("pass_count", 0) >= 1
        assert drift_bucket.get("fail_count", 0) == 0


# ==================================================================
# TrialStore — expected_transition_target verdict
# ==================================================================

class TestTrialStoreTransitionTarget:
    """_is_pass() CLASS_2 block must verify transition_target when set."""

    def _make_class2_trial(self, expected_transition_target=None):
        from experiment_package.trial_store import TrialStore
        store = TrialStore()
        run = store.create_run(
            package_id="D",
            scenario_ids=["s1"],
            fault_profile_ids=[],
            trial_count=1,
        )
        trial = store.create_trial(
            run_id=run.run_id,
            package_id="D",
            scenario_id="s1",
            fault_profile_id=None,
            comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_validation="safe_deferral",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-tt-001",
            expected_transition_target=expected_transition_target,
        )
        return store, trial

    def _complete_with_target(self, store, trial, observed_target):
        # Build a post-transition observation that mirrors what the Mac mini
        # actually publishes for each transition target (validation block for
        # CLASS_1, escalation block for CLASS_0, plain class2 for safe-deferral).
        obs: dict = {
            "route": {"route_class": "CLASS_2"},
            "class2": {
                "transition_target": observed_target,
                "should_notify_caregiver": False,
                "unresolved_reason": "caregiver_required_sensitive_path",
                "timestamp_ms": 0,
            },
            "generated_at_ms": 1000,
        }
        if observed_target == "CLASS_1":
            obs["validation"] = {"validation_status": "approved"}
        elif observed_target == "CLASS_0":
            obs["escalation"] = {"escalation_status": "pending",
                                  "notification_channel": "telegram",
                                  "timestamp_ms": 0}
        else:
            obs["validation"] = {"validation_status": "safe_deferral"}
        return store.complete_trial(trial.trial_id, obs)

    def test_no_expected_target_always_passes(self):
        """When expected_transition_target is None, any transition_target passes."""
        store, trial = self._make_class2_trial(expected_transition_target=None)
        result = self._complete_with_target(store, trial, "CLASS_0")
        assert result.pass_ is True

    def test_matching_target_passes(self):
        """CLASS_2 trial passes when observed target matches expected."""
        store, trial = self._make_class2_trial(expected_transition_target="CLASS_1")
        result = self._complete_with_target(store, trial, "CLASS_1")
        assert result.pass_ is True

    def test_mismatched_target_fails(self):
        """CLASS_2 trial fails when observed target does not match expected."""
        store, trial = self._make_class2_trial(expected_transition_target="CLASS_1")
        result = self._complete_with_target(store, trial, "CLASS_0")
        assert result.pass_ is False

    def test_class0_expected_target_passes(self):
        """CLASS_2 trial with expected CLASS_0 transition passes when observed."""
        store, trial = self._make_class2_trial(expected_transition_target="CLASS_0")
        result = self._complete_with_target(store, trial, "CLASS_0")
        assert result.pass_ is True

    def test_expected_target_in_to_dict(self):
        """expected_transition_target is serialised in to_dict()."""
        store, trial = self._make_class2_trial(expected_transition_target="CLASS_1")
        assert trial.to_dict()["expected_transition_target"] == "CLASS_1"

    def test_none_expected_target_in_to_dict(self):
        """expected_transition_target=None is included as None in to_dict()."""
        store, trial = self._make_class2_trial(expected_transition_target=None)
        assert trial.to_dict()["expected_transition_target"] is None


# ==================================================================
# compute_metrics — Package D/E/F/G nested telemetry + required metrics
# ==================================================================

class TestPackageMetricsD:
    """_metrics_d validates Class 2 caregiver notification payloads against
    common/schemas/class2_notification_payload_schema.json (required_experiments.md §8).
    """

    def _make_class2_trial(self, notification_payload):
        from experiment_package.trial_store import TrialStore
        store = TrialStore()
        run = store.create_run(
            package_id="D",
            scenario_ids=["s"],
            fault_profile_ids=[],
            trial_count=1,
        )
        trial = store.create_trial(
            run_id=run.run_id,
            package_id="D",
            scenario_id="s",
            fault_profile_id=None,
            comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_validation="safe_deferral",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-d-001",
        )
        # Observation payload is required for trial completion bookkeeping
        # (route/class2 blocks) but Package D evaluates notification_payload.
        obs = {
            "route": {"route_class": "CLASS_2"},
            "validation": {"validation_status": "safe_deferral"},
            "class2": {"transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
                       "unresolved_reason": "insufficient_context"},
            "audit_correlation_id": "audit-d-001",
            "generated_at_ms": 0,
        }
        store.complete_trial(
            trial.trial_id, obs, notification_payload=notification_payload,
        )
        return store, run

    def _valid_notification(self):
        return {
            "event_summary": "Class 2 진입: insufficient_context",
            "context_summary": "현재 환경 및 기기 상태 요약 없음",
            "unresolved_reason": "insufficient_context",
            "manual_confirmation_path": (
                "보호자는 Telegram 또는 대시보드를 통해 상황을 검토하고 "
                "수동 확인, 거부, 또는 개입 경로를 선택할 수 있습니다."
            ),
            "audit_correlation_id": "audit-d-001",
            "timestamp_ms": 1700000000000,
            "notification_channel": "telegram",
            "source_layer": "class2_clarification_manager",
        }

    def test_valid_notification_is_complete(self):
        """A schema-valid notification payload scores 100% complete."""
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_class2_trial(self._valid_notification())
        metrics = compute_metrics(store.list_trials_for_run(run.run_id), "D")
        assert metrics["payload_completeness_rate"] == 1.0
        assert metrics["missing_field_rate"] == 0.0
        assert metrics["schema_violation_count"] == 0
        assert metrics["no_notification_count"] == 0

    def test_no_notification_counts_as_incomplete(self):
        """Missing notification → trial counted as missing all required fields."""
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_class2_trial(None)
        metrics = compute_metrics(store.list_trials_for_run(run.run_id), "D")
        assert metrics["payload_completeness_rate"] == 0.0
        assert metrics["no_notification_count"] == 1
        for f in ("event_summary", "context_summary", "unresolved_reason",
                  "manual_confirmation_path"):
            assert metrics["missing_by_field"][f] == 1

    def test_missing_required_field_reported(self):
        """Missing manual_confirmation_path is reported in missing_by_field."""
        from experiment_package.trial_store import compute_metrics
        notif = self._valid_notification()
        del notif["manual_confirmation_path"]
        store, run = self._make_class2_trial(notif)
        metrics = compute_metrics(store.list_trials_for_run(run.run_id), "D")
        assert metrics["payload_completeness_rate"] == 0.0
        assert metrics["missing_by_field"]["manual_confirmation_path"] == 1

    def test_extra_property_violates_schema(self):
        """additionalProperties:false on the schema is enforced via schema_violation_count."""
        from experiment_package.trial_store import compute_metrics
        notif = self._valid_notification()
        notif["bogus_extra"] = "x"
        store, run = self._make_class2_trial(notif)
        metrics = compute_metrics(store.list_trials_for_run(run.run_id), "D")
        # Required fields are present, so missing_field_rate stays 0.
        # But the extra property breaks schema validation.
        assert metrics["schema_violation_count"] == 1
        assert metrics["payload_completeness_rate"] == 0.0

    def test_notification_readiness_rate_present(self):
        """notification_readiness_rate is reported and reflects present/expected."""
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_class2_trial(self._valid_notification())
        metrics = compute_metrics(store.list_trials_for_run(run.run_id), "D")
        assert metrics["notification_readiness_rate"] == 1.0
        assert metrics["notification_expected_count"] == 1

    def test_notification_readiness_rate_missing_notification(self):
        """No notification arrived → readiness is 0/expected."""
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_class2_trial(None)
        metrics = compute_metrics(store.list_trials_for_run(run.run_id), "D")
        assert metrics["notification_expected_count"] == 1
        assert metrics["notification_readiness_rate"] == 0.0
        assert metrics["no_notification_count"] == 1

    def test_notification_not_expected_excluded_from_all_completeness_metrics(self):
        """should_notify_caregiver=false trial must be excluded from EVERY
        notification completeness metric — readiness, no_notification_count,
        missing_by_field, payload_completeness_rate, and missing_field_rate.
        Otherwise a normal CLASS_2→CLASS_1 success is wrongly penalised."""
        from experiment_package.trial_store import TrialStore, compute_metrics
        store = TrialStore()
        run = store.create_run(package_id="D", scenario_ids=[],
                               fault_profile_ids=[], trial_count=1)
        trial = store.create_trial(
            run_id=run.run_id, package_id="D", scenario_id="s",
            fault_profile_id=None, comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_validation="approved",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-d-nr-001",
        )
        obs = {
            "route": {"route_class": "CLASS_2"},
            "validation": {"validation_status": "approved"},
            "ack": {"dispatch_status": "published"},
            "class2": {"transition_target": "CLASS_1",
                       "should_notify_caregiver": False,
                       "unresolved_reason": "insufficient_context"},
        }
        store.complete_trial(trial.trial_id, obs, notification_payload=None)
        metrics = compute_metrics(store.list_trials_for_run(run.run_id), "D")
        assert metrics["notification_expected_count"] == 0
        assert metrics["notification_not_expected_count"] == 1
        assert metrics["no_notification_count"] == 0
        assert metrics["payload_completeness_rate"] == 0.0  # 0/0 by convention
        assert metrics["missing_field_rate"] == 0.0
        assert all(c == 0 for c in metrics["missing_by_field"].values())

    def test_mixed_run_completeness_only_counts_expected_trials(self):
        """A mixed run with one notification-expected trial (complete) and one
        notification-not-expected trial (no notification): completeness must be
        1.0 because only the expected trial counts."""
        from experiment_package.trial_store import TrialStore, compute_metrics
        store = TrialStore()
        run = store.create_run(package_id="D", scenario_ids=[],
                               fault_profile_ids=[], trial_count=2)
        # Trial A: should_notify_caregiver=True with valid notification
        ta = store.create_trial(
            run_id=run.run_id, package_id="D", scenario_id="s",
            fault_profile_id=None, comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_validation="safe_deferral",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-d-mix-a",
        )
        store.complete_trial(
            ta.trial_id,
            {
                "route": {"route_class": "CLASS_2"},
                "validation": {"validation_status": "safe_deferral"},
                "class2": {"transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
                           "should_notify_caregiver": True,
                           "unresolved_reason": "insufficient_context"},
            },
            notification_payload=self._valid_notification(),
        )
        # Trial B: should_notify_caregiver=False (CLASS_1 success) with no notification
        tb = store.create_trial(
            run_id=run.run_id, package_id="D", scenario_id="s",
            fault_profile_id=None, comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_validation="approved",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-d-mix-b",
        )
        store.complete_trial(
            tb.trial_id,
            {
                "route": {"route_class": "CLASS_2"},
                "validation": {"validation_status": "approved"},
                "ack": {"dispatch_status": "published"},
                "class2": {"transition_target": "CLASS_1",
                           "should_notify_caregiver": False,
                           "unresolved_reason": "insufficient_context"},
            },
            notification_payload=None,
        )
        metrics = compute_metrics(store.list_trials_for_run(run.run_id), "D")
        assert metrics["class2_trials"] == 2
        assert metrics["notification_expected_count"] == 1
        assert metrics["notification_not_expected_count"] == 1
        assert metrics["no_notification_count"] == 0  # the missing one wasn't expected
        assert metrics["payload_completeness_rate"] == 1.0  # 1 expected, 1 complete
        assert metrics["missing_field_rate"] == 0.0
        assert metrics["notification_readiness_rate"] == 1.0


# ==================================================================
# PackageRunner — late notification arrival (Issue #4)
# ==================================================================

class TestNotificationLateArrival:
    """Runner must wait briefly for notification arrival after observation match,
    so notifications published shortly AFTER the dashboard observation are still
    captured into TrialResult.notification_payload."""

    def test_notification_arriving_after_observation_is_captured(self):
        from unittest.mock import MagicMock
        from experiment_package.runner import PackageRunner
        from experiment_package.trial_store import TrialStore
        from notification_store import NotificationStore
        import threading
        import time as _t

        publishes: list[dict] = []
        node = MagicMock()
        node.profile.payload_template = {
            "source_node_id": "test",
            "routing_metadata": {"audit_correlation_id": "x",
                                  "ingest_timestamp_ms": 0,
                                  "network_status": "online"},
            "pure_context_payload": {},
        }
        node.profile.publish_topic = "safe_deferral/context/input"
        from virtual_node_manager.models import VirtualNodeState
        node.state = VirtualNodeState.CREATED
        vnm = MagicMock()
        vnm.get_node.return_value = node
        vnm.publish_once.side_effect = lambda n: publishes.append(
            dict(n.profile.payload_template)
        )

        # Observation arrives immediately as a CLASS_2 final snapshot.
        obs = {
            "route": {"route_class": "CLASS_2"},
            "validation": {"validation_status": "safe_deferral"},
            "class2": {"transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
                       "should_notify_caregiver": True,
                       "unresolved_reason": "timeout_or_no_response"},
            "audit_correlation_id": "x",
            "generated_at_ms": 1,
        }
        obs_store = MagicMock()
        obs_store.find_by_correlation_id.return_value = obs

        notif_store = NotificationStore()

        # Schedule notification to arrive ~0.3s after the trial publishes.
        def _late_publish():
            _t.sleep(0.3)
            notif_store.add({
                "audit_correlation_id": None,  # placeholder; will be set below
                "event_summary": "late",
                "context_summary": "late",
                "unresolved_reason": "timeout_or_no_response",
                "manual_confirmation_path": "test",
            })

        store = TrialStore()
        runner = PackageRunner(vnm, obs_store, store, notification_store=notif_store)
        run = store.create_run(package_id="D", scenario_ids=[],
                               fault_profile_ids=[], trial_count=1)
        trial = runner.start_trial_async(
            run_id=run.run_id, package_id="D", node_id="n",
            scenario_id="", fault_profile_id=None,
            comparison_condition=None,
            expected_route_class="CLASS_2",
        )
        # Inject the actual correlation_id once the publish has happened.
        deadline = _t.monotonic() + 2.0
        while _t.monotonic() < deadline:
            if publishes:
                break
            _t.sleep(0.05)
        corr = publishes[0]["routing_metadata"]["audit_correlation_id"]

        # Schedule the late notification with the right correlation_id.
        def _emit_after():
            _t.sleep(0.3)
            notif_store.add({
                "audit_correlation_id": corr,
                "event_summary": "late",
                "context_summary": "late",
                "unresolved_reason": "timeout_or_no_response",
                "manual_confirmation_path": "test",
            })
        threading.Thread(target=_emit_after, daemon=True).start()

        # Wait for the trial to complete.
        deadline = _t.monotonic() + 5.0
        while _t.monotonic() < deadline:
            t = store.get_trial(trial.trial_id)
            if t and t.status != "pending":
                break
            _t.sleep(0.05)
        result = store.get_trial(trial.trial_id)
        assert result.status == "completed"
        assert result.notification_payload is not None
        assert result.notification_payload["audit_correlation_id"] == corr


class TestPackageMetricsE:
    """_metrics_e must compute doorlock-sensitive validation rates."""

    def _make_doorlock_trial(self, observed_route, observed_validation):
        from experiment_package.trial_store import TrialStore
        store = TrialStore()
        run = store.create_run(
            package_id="E",
            scenario_ids=["s"],
            fault_profile_ids=[],
            trial_count=1,
        )
        trial = store.create_trial(
            run_id=run.run_id,
            package_id="E",
            scenario_id="s",
            fault_profile_id=None,
            comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_validation="safe_deferral",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-e-001",
        )
        obs = {
            "route": {"route_class": observed_route},
            "validation": {"validation_status": observed_validation},
            "class2": {"transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"},
            "audit_correlation_id": "audit-e-001",
            "generated_at_ms": 0,
        }
        store.complete_trial(trial.trial_id, obs)
        return store, run

    def test_safe_deferral_counts_as_safe(self):
        """CLASS_2 + safe_deferral → 100% safe deferral, 0% unauthorized."""
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_doorlock_trial("CLASS_2", "safe_deferral")
        m = compute_metrics(store.list_trials_for_run(run.run_id), "E")
        assert m["doorlock_safe_deferral_rate"] == 1.0
        assert m["unauthorized_doorlock_rate"] == 0.0

    def test_class1_approved_is_unauthorized(self):
        """CLASS_1 + approved on a doorlock-sensitive trial → unauthorized."""
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_doorlock_trial("CLASS_1", "approved")
        m = compute_metrics(store.list_trials_for_run(run.run_id), "E")
        assert m["unauthorized_doorlock_rate"] == 1.0
        assert m["doorlock_safe_deferral_rate"] == 0.0


class TestPackageMetricsF:
    """_metrics_f reports grace-period cancellation and false-dispatch rates."""

    def _make_trial(
        self,
        package_id="F",
        expected_route="CLASS_2",
        observed_route="CLASS_2",
        observed_validation="safe_deferral",
        fault_profile_id=None,
    ):
        from experiment_package.trial_store import TrialStore
        store = TrialStore()
        run = store.create_run(
            package_id=package_id,
            scenario_ids=["s"],
            fault_profile_ids=[],
            trial_count=1,
        )
        trial = store.create_trial(
            run_id=run.run_id,
            package_id=package_id,
            scenario_id="s",
            fault_profile_id=fault_profile_id,
            comparison_condition=None,
            expected_route_class=expected_route,
            expected_validation="safe_deferral",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-f-001",
        )
        obs = {
            "route": {"route_class": observed_route},
            "validation": {"validation_status": observed_validation},
            "class2": {"transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"},
            "audit_correlation_id": "audit-f-001",
            "generated_at_ms": 0,
        }
        store.complete_trial(trial.trial_id, obs)
        return store, run

    def test_class2_safe_deferral_counts_as_cancellation(self):
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_trial()
        m = compute_metrics(store.list_trials_for_run(run.run_id), "F")
        assert m["grace_period_cancellation_rate"] == 1.0
        assert m["false_dispatch_rate"] == 0.0

    def test_unsafe_class1_counts_as_false_dispatch(self):
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_trial(
            observed_route="CLASS_1", observed_validation="approved"
        )
        m = compute_metrics(store.list_trials_for_run(run.run_id), "F")
        assert m["false_dispatch_rate"] == 1.0


class TestPackageMetricsG:
    """_metrics_g reports topic_drift_detection_rate and governance_pass_rate."""

    def test_drift_pass_counts_as_detected(self):
        from experiment_package.trial_store import TrialStore, compute_metrics
        store = TrialStore()
        run = store.create_run(
            package_id="G",
            scenario_ids=[],
            fault_profile_ids=["FAULT_CONTRACT_DRIFT_01"],
            trial_count=1,
        )
        trial = store.create_trial(
            run_id=run.run_id,
            package_id="G",
            scenario_id="",
            fault_profile_id="FAULT_CONTRACT_DRIFT_01",
            comparison_condition=None,
            expected_route_class="CLASS_1",
            expected_validation="approved",
            expected_outcome="governance_verification_fail_no_runtime_authority",
            audit_correlation_id="audit-g-001",
        )
        # Drift: no observation arrived → governance pass
        store.complete_trial(trial.trial_id, {"audit_correlation_id": "audit-g-001"})
        m = compute_metrics(store.list_trials_for_run(run.run_id), "G")
        assert m["topic_drift_detection_rate"] == 1.0
        assert m["governance_pass_rate"] == 1.0

    def test_no_drift_trial_returns_zero_detection_rate(self):
        from experiment_package.trial_store import TrialStore, compute_metrics
        store = TrialStore()
        run = store.create_run(
            package_id="G",
            scenario_ids=["s"],
            fault_profile_ids=[],
            trial_count=1,
        )
        trial = store.create_trial(
            run_id=run.run_id,
            package_id="G",
            scenario_id="s",
            fault_profile_id=None,
            comparison_condition=None,
            expected_route_class="CLASS_1",
            expected_validation="approved",
            expected_outcome="class_1_approved",
            audit_correlation_id="audit-g-002",
        )
        store.complete_trial(trial.trial_id, {
            "route": {"route_class": "CLASS_1", "timestamp_ms": 0},
            "validation": {"validation_status": "approved"},
            "audit_correlation_id": "audit-g-002",
            "generated_at_ms": 0,
        })
        m = compute_metrics(store.list_trials_for_run(run.run_id), "G")
        assert m["topic_drift_detection_rate"] == 0.0
        assert m["governance_pass_rate"] == 1.0


class TestPackageMetricsCDriftRate:
    """_metrics_c surfaces topic_drift_detection_rate alongside per-profile bucket."""

    def test_drift_rate_in_metrics_c(self):
        from experiment_package.trial_store import TrialStore, compute_metrics
        store = TrialStore()
        run = store.create_run(
            package_id="C",
            scenario_ids=[],
            fault_profile_ids=["FAULT_CONTRACT_DRIFT_01"],
            trial_count=1,
        )
        trial = store.create_trial(
            run_id=run.run_id,
            package_id="C",
            scenario_id="",
            fault_profile_id="FAULT_CONTRACT_DRIFT_01",
            comparison_condition=None,
            expected_route_class="CLASS_1",
            expected_validation="approved",
            expected_outcome="governance_verification_fail_no_runtime_authority",
            audit_correlation_id="audit-c-001",
        )
        store.complete_trial(trial.trial_id, {"audit_correlation_id": "audit-c-001"})
        m = compute_metrics(store.list_trials_for_run(run.run_id), "C")
        assert m["topic_drift_detection_rate"] == 1.0


# ==================================================================
# PackageRunner — comparison_condition propagation to routing_metadata
# ==================================================================

class TestExperimentModePropagation:
    """Runner must inject comparison_condition into routing_metadata.experiment_mode."""

    def test_comparison_condition_writes_experiment_mode(self):
        """trial.comparison_condition is propagated to routing_metadata."""
        from unittest.mock import MagicMock
        from experiment_package.runner import PackageRunner
        from experiment_package.trial_store import TrialStore

        # Capture what publish_once receives via the node template snapshot
        captured = {}

        node = MagicMock()
        node.profile.payload_template = {
            "source_node_id": "test",
            "routing_metadata": {
                "audit_correlation_id": "x",
                "ingest_timestamp_ms": 0,
                "network_status": "online",
            },
            "pure_context_payload": {},
        }
        node.profile.publish_topic = "safe_deferral/context/input"

        vnm = MagicMock()
        vnm.get_node.return_value = node

        def _capture(_node):
            captured["template"] = dict(_node.profile.payload_template)

        vnm.publish_once.side_effect = _capture

        obs_store = MagicMock()
        obs_store.find_by_correlation_id.return_value = {
            "route": {"route_class": "CLASS_1", "timestamp_ms": 0},
            "validation": {"validation_status": "approved"},
            "audit_correlation_id": "x",
            "generated_at_ms": 1,
        }

        store = TrialStore()
        runner = PackageRunner(vnm, obs_store, store)
        run = store.create_run(
            package_id="A",
            scenario_ids=[],
            fault_profile_ids=[],
            trial_count=1,
            comparison_condition="rule_only",
        )
        trial = runner.start_trial_async(
            run_id=run.run_id,
            package_id="A",
            node_id="n",
            scenario_id="",
            fault_profile_id=None,
            comparison_condition="rule_only",
            expected_route_class="CLASS_1",
        )

        import time
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            t = store.get_trial(trial.trial_id)
            if t and t.status != "pending":
                break
            time.sleep(0.05)

        assert "template" in captured, "publish_once was not called"
        meta = captured["template"]["routing_metadata"]
        assert meta.get("experiment_mode") == "rule_only"


# ==================================================================
# PackageRunner — auto-drive selection input for CLASS_2 trials
# ==================================================================

class TestClass2SelectionAutoDrive:
    """For CLASS_2 trials with expected_transition_target=CLASS_1/CLASS_0,
    runner must publish a synthetic single_click/triple_hit so the trial
    actually closes instead of waiting out the full caregiver timeout."""

    def _make_setup(self, expected_target, observation_sequence):
        """observation_sequence: list of dicts; find_by_correlation_id returns
        the next one each call (advances the index)."""
        from unittest.mock import MagicMock
        from experiment_package.runner import PackageRunner
        from experiment_package.trial_store import TrialStore

        publishes: list[dict] = []

        node = MagicMock()
        node.profile.payload_template = {
            "source_node_id": "test",
            "routing_metadata": {
                "audit_correlation_id": "x",
                "ingest_timestamp_ms": 0,
                "network_status": "online",
            },
            "pure_context_payload": {},
        }
        node.profile.publish_topic = "safe_deferral/context/input"
        from virtual_node_manager.models import VirtualNodeState
        node.state = VirtualNodeState.CREATED

        vnm = MagicMock()
        vnm.get_node.return_value = node

        def _capture(_node):
            publishes.append(dict(_node.profile.payload_template))
        vnm.publish_once.side_effect = _capture

        idx = {"i": 0}
        def _find(corr_id):
            i = idx["i"]
            if i >= len(observation_sequence):
                return observation_sequence[-1] if observation_sequence else None
            obs = observation_sequence[i]
            idx["i"] = i + 1
            return obs
        obs_store = MagicMock()
        obs_store.find_by_correlation_id.side_effect = _find

        store = TrialStore()
        runner = PackageRunner(vnm, obs_store, store)
        return runner, store, publishes

    def _wait_done(self, store, trial_id, timeout=3.0):
        import time
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            t = store.get_trial(trial_id)
            if t and t.status != "pending":
                return t
            time.sleep(0.05)
        return store.get_trial(trial_id)

    def test_class1_transition_drives_single_click(self):
        """expected_transition_target=CLASS_1 → runner publishes a single_click."""
        # First obs: initial CLASS_2 routing snapshot (no class2 block).
        # Second obs: post-transition with class2+validation.
        initial = {
            "route": {"route_class": "CLASS_2"},
            "audit_correlation_id": "x",
            "generated_at_ms": 1,
        }
        post = {
            "route": {"route_class": "CLASS_2"},
            "validation": {"validation_status": "approved"},
            "class2": {"transition_target": "CLASS_1",
                       "unresolved_reason": "insufficient_context"},
            "audit_correlation_id": "x",
            "generated_at_ms": 2,
        }
        runner, store, publishes = self._make_setup("CLASS_1", [initial, initial, post])
        run = store.create_run(package_id="A", scenario_ids=[],
                               fault_profile_ids=[], trial_count=1)
        trial = runner.start_trial_async(
            run_id=run.run_id,
            package_id="A",
            node_id="n",
            scenario_id="",
            fault_profile_id=None,
            comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_transition_target_override="CLASS_1",
        )
        result = self._wait_done(store, trial.trial_id, timeout=5.0)
        assert result.status == "completed"
        # Two publishes: initial scenario context + auto-driven single_click
        codes = [p["pure_context_payload"]["trigger_event"]["event_code"]
                 for p in publishes if "pure_context_payload" in p
                 and p["pure_context_payload"].get("trigger_event")]
        assert "single_click" in codes

    def test_class0_transition_drives_triple_hit(self):
        """expected_transition_target=CLASS_0 → runner publishes a triple_hit."""
        initial = {
            "route": {"route_class": "CLASS_2"},
            "audit_correlation_id": "x",
            "generated_at_ms": 1,
        }
        post = {
            "route": {"route_class": "CLASS_2"},
            "escalation": {"escalation_status": "pending",
                           "notification_channel": "telegram", "timestamp_ms": 2},
            "class2": {"transition_target": "CLASS_0",
                       "unresolved_reason": "insufficient_context"},
            "audit_correlation_id": "x",
            "generated_at_ms": 2,
        }
        runner, store, publishes = self._make_setup("CLASS_0", [initial, initial, post])
        run = store.create_run(package_id="A", scenario_ids=[],
                               fault_profile_ids=[], trial_count=1)
        trial = runner.start_trial_async(
            run_id=run.run_id,
            package_id="A",
            node_id="n",
            scenario_id="",
            fault_profile_id=None,
            comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_transition_target_override="CLASS_0",
        )
        result = self._wait_done(store, trial.trial_id, timeout=5.0)
        assert result.status == "completed"
        codes = [p["pure_context_payload"]["trigger_event"]["event_code"]
                 for p in publishes if "pure_context_payload" in p
                 and p["pure_context_payload"].get("trigger_event")]
        assert "triple_hit" in codes

    def test_safe_deferral_does_not_drive_selection(self):
        """SAFE_DEFERRAL trials must NOT auto-drive — they exercise the timeout/caregiver path."""
        post = {
            "route": {"route_class": "CLASS_2"},
            "validation": {"validation_status": "safe_deferral"},
            "class2": {"transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
                       "unresolved_reason": "timeout_or_no_response"},
            "audit_correlation_id": "x",
            "generated_at_ms": 2,
        }
        runner, store, publishes = self._make_setup(None, [post])
        run = store.create_run(package_id="A", scenario_ids=[],
                               fault_profile_ids=[], trial_count=1)
        trial = runner.start_trial_async(
            run_id=run.run_id,
            package_id="A",
            node_id="n",
            scenario_id="",
            fault_profile_id=None,
            comparison_condition=None,
            expected_route_class="CLASS_2",
        )
        result = self._wait_done(store, trial.trial_id, timeout=5.0)
        assert result.status == "completed"
        # Only the initial scenario publish, no synthetic button press
        codes = [p["pure_context_payload"]["trigger_event"]["event_code"]
                 for p in publishes if "pure_context_payload" in p
                 and p["pure_context_payload"].get("trigger_event")]
        assert "single_click" not in codes
        assert "triple_hit" not in codes


# ==================================================================
# TrialStore — requires_validator_reentry_when_class1 verdict
# ==================================================================

class TestRequiresValidatorReentry:
    """When the scenario contract requires validator re-entry on CLASS_2→CLASS_1,
    _is_pass must verify the post-transition observation carries validation evidence."""

    def _make_trial(self, requires_reentry, observation):
        from experiment_package.trial_store import TrialStore
        store = TrialStore()
        run = store.create_run(package_id="D", scenario_ids=[],
                               fault_profile_ids=[], trial_count=1)
        trial = store.create_trial(
            run_id=run.run_id,
            package_id="D",
            scenario_id="s",
            fault_profile_id=None,
            comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_validation="safe_deferral",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-rv-001",
            expected_transition_target="CLASS_1",
            requires_validator_reentry_when_class1=requires_reentry,
        )
        return store.complete_trial(trial.trial_id, observation)

    def test_validator_reentry_required_passes_with_approved_and_ack(self):
        """approved validator + ACK present → pass."""
        obs = {
            "route": {"route_class": "CLASS_2"},
            "validation": {"validation_status": "approved"},
            "ack": {"dispatch_status": "published", "action": "light_on",
                    "target_device": "living_room_light"},
            "class2": {"transition_target": "CLASS_1",
                       "unresolved_reason": "insufficient_context"},
        }
        result = self._make_trial(True, obs)
        assert result.pass_ is True

    def test_validator_reentry_required_fails_on_rejected(self):
        """rejected_escalation must NOT pass even though validator was re-entered:
        the bounded candidate was inadmissible, so Class 1 transition did not succeed."""
        obs = {
            "route": {"route_class": "CLASS_2"},
            "validation": {"validation_status": "rejected_escalation"},
            "class2": {"transition_target": "CLASS_1",
                       "unresolved_reason": "insufficient_context"},
        }
        result = self._make_trial(True, obs)
        assert result.pass_ is False

    def test_validator_reentry_required_fails_without_ack(self):
        """approved validator but no dispatch ACK → fail (no bounded execution evidence)."""
        obs = {
            "route": {"route_class": "CLASS_2"},
            "validation": {"validation_status": "approved"},
            "class2": {"transition_target": "CLASS_1",
                       "unresolved_reason": "insufficient_context"},
        }
        result = self._make_trial(True, obs)
        assert result.pass_ is False

    def test_validator_reentry_required_fails_without_validation(self):
        obs = {
            "route": {"route_class": "CLASS_2"},
            "class2": {"transition_target": "CLASS_1",
                       "unresolved_reason": "insufficient_context"},
        }
        result = self._make_trial(True, obs)
        assert result.pass_ is False

    def test_validator_reentry_not_required_passes_without_validation(self):
        obs = {
            "route": {"route_class": "CLASS_2"},
            "class2": {"transition_target": "CLASS_1",
                       "unresolved_reason": "insufficient_context"},
        }
        result = self._make_trial(False, obs)
        assert result.pass_ is True

    def test_class0_requires_escalation_evidence(self):
        """Even without the requires_validator_reentry flag, CLASS_0 transitions
        require escalation evidence (Issue #4)."""
        from experiment_package.trial_store import TrialStore
        store = TrialStore()
        run = store.create_run(package_id="D", scenario_ids=[],
                               fault_profile_ids=[], trial_count=1)
        trial = store.create_trial(
            run_id=run.run_id, package_id="D", scenario_id="s",
            fault_profile_id=None, comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_validation="safe_deferral",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-c0-001",
            expected_transition_target="CLASS_0",
        )
        # CLASS_0 transition observed but escalation evidence missing → fail
        no_escalation = {
            "route": {"route_class": "CLASS_2"},
            "class2": {"transition_target": "CLASS_0",
                       "unresolved_reason": "insufficient_context"},
        }
        store.complete_trial(trial.trial_id, no_escalation)
        assert store.get_trial(trial.trial_id).pass_ is False

        # Now with escalation block present → pass
        trial2 = store.create_trial(
            run_id=run.run_id, package_id="D", scenario_id="s",
            fault_profile_id=None, comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_validation="safe_deferral",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-c0-002",
            expected_transition_target="CLASS_0",
        )
        with_escalation = {
            "route": {"route_class": "CLASS_2"},
            "escalation": {"escalation_status": "pending",
                           "notification_channel": "telegram", "timestamp_ms": 0},
            "class2": {"transition_target": "CLASS_0",
                       "unresolved_reason": "insufficient_context"},
        }
        store.complete_trial(trial2.trial_id, with_escalation)
        assert store.get_trial(trial2.trial_id).pass_ is True


# ==================================================================
# Compound / aliased expected_transition_target verdict (Issue #3)
# ==================================================================

class TestCompoundExpectedTransitionTarget:
    """expected_transition_target may be a single canonical value, an alias
    (CAREGIVER_CONFIRMATION → SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION), or a
    compound joined by _OR_ — verdict must accept observed in the parsed set.
    """

    def _trial_with_target(self, expected, observed_target,
                           validation_status=None, escalation=False, ack=False):
        from experiment_package.trial_store import TrialStore
        store = TrialStore()
        run = store.create_run(package_id="D", scenario_ids=[],
                               fault_profile_ids=[], trial_count=1)
        trial = store.create_trial(
            run_id=run.run_id, package_id="D", scenario_id="s",
            fault_profile_id=None, comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_validation="safe_deferral",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-tt-c-001",
            expected_transition_target=expected,
        )
        obs = {
            "route": {"route_class": "CLASS_2"},
            "class2": {"transition_target": observed_target,
                       "unresolved_reason": "insufficient_context"},
        }
        if validation_status:
            obs["validation"] = {"validation_status": validation_status}
        if escalation:
            obs["escalation"] = {"escalation_status": "pending",
                                 "notification_channel": "telegram",
                                 "timestamp_ms": 0}
        if ack:
            obs["ack"] = {"dispatch_status": "published"}
        return store.complete_trial(trial.trial_id, obs)

    def test_compound_or_set_accepts_safe_deferral(self):
        """CLASS_1_OR_CLASS_0_OR_SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION accepts
        observed SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION."""
        result = self._trial_with_target(
            "CLASS_1_OR_CLASS_0_OR_SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
            "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
            validation_status="safe_deferral",
        )
        assert result.pass_ is True

    def test_compound_or_set_accepts_class1_with_validation(self):
        """Compound expectation accepts CLASS_1 (no requires_reentry flag → just
        observed match passes; no ack required)."""
        result = self._trial_with_target(
            "CLASS_1_OR_CLASS_0_OR_SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
            "CLASS_1",
            validation_status="approved",
        )
        assert result.pass_ is True

    def test_compound_or_set_accepts_class0_with_escalation(self):
        result = self._trial_with_target(
            "CLASS_1_OR_CLASS_0_OR_SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
            "CLASS_0",
            escalation=True,
        )
        assert result.pass_ is True

    def test_caregiver_confirmation_alias_canonicalizes(self):
        """expected=CAREGIVER_CONFIRMATION matches canonical observed
        SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION."""
        result = self._trial_with_target(
            "CAREGIVER_CONFIRMATION",
            "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
            validation_status="safe_deferral",
        )
        assert result.pass_ is True

    def test_safe_deferral_alias_canonicalizes(self):
        result = self._trial_with_target(
            "SAFE_DEFERRAL",
            "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
            validation_status="safe_deferral",
        )
        assert result.pass_ is True

    def test_unknown_target_still_fails(self):
        """Unknown observed target outside the parsed set fails."""
        result = self._trial_with_target(
            "CLASS_1",
            "CLASS_0",
            escalation=True,
        )
        assert result.pass_ is False

    def test_parser_helper_maps_aliases(self):
        from experiment_package.trial_store import _expected_transition_targets
        assert _expected_transition_targets("CAREGIVER_CONFIRMATION") == {
            "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"
        }
        assert _expected_transition_targets("SAFE_DEFERRAL") == {
            "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"
        }
        assert _expected_transition_targets("CLASS_1") == {"CLASS_1"}
        compound = _expected_transition_targets(
            "CLASS_1_OR_CLASS_0_OR_SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"
        )
        assert compound == {"CLASS_1", "CLASS_0", "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION"}
        assert _expected_transition_targets(None) is None


# ==================================================================
# NotificationStore — basic ring-buffer behaviour
# ==================================================================

class TestScenarioContractWithOverride:
    """When start_trial_async receives expected_transition_target_override, the
    scenario file's class2_clarification_expectation block must STILL be loaded
    so requires_validator_reentry_when_class1 is honored. The override only
    replaces the target value, not the boolean contract."""

    def test_override_preserves_requires_validator_reentry_flag(self, tmp_path):
        """Scenario declares requires_validator_reentry_when_class1=true; even
        with target_override, the trial must carry the flag through."""
        import json
        from unittest.mock import MagicMock
        from experiment_package.runner import PackageRunner
        from experiment_package.trial_store import TrialStore
        from shared.asset_loader import RpiAssetLoader

        # Build a minimal scenario fixture in tmp_path with the contract flag set.
        scen_dir = tmp_path / "integration" / "scenarios"
        scen_dir.mkdir(parents=True)
        scenario_path = scen_dir / "test_class2_validator_reentry_scenario.json"
        scenario_path.write_text(json.dumps({
            "scenario_id": "SCN_TEST_VR",
            "class2_clarification_expectation": {
                "expected_transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
                "requires_validator_reentry_when_class1": True,
            },
        }))

        loader = MagicMock(spec=RpiAssetLoader)
        loader.load_scenario.return_value = json.loads(scenario_path.read_text())
        loader.fixture_exists.return_value = False

        node = MagicMock()
        node.profile.payload_template = {
            "source_node_id": "test",
            "routing_metadata": {"audit_correlation_id": "x",
                                  "ingest_timestamp_ms": 0,
                                  "network_status": "online"},
            "pure_context_payload": {},
        }
        node.profile.publish_topic = "safe_deferral/context/input"
        from virtual_node_manager.models import VirtualNodeState
        node.state = VirtualNodeState.CREATED

        vnm = MagicMock()
        vnm.get_node.return_value = node
        vnm.publish_once.side_effect = lambda n: None

        obs_store = MagicMock()
        obs_store.find_by_correlation_id.return_value = {
            "route": {"route_class": "CLASS_2"},
            "validation": {"validation_status": "approved"},
            "ack": {"dispatch_status": "published"},
            "class2": {"transition_target": "CLASS_1",
                       "should_notify_caregiver": False,
                       "unresolved_reason": "insufficient_context"},
            "audit_correlation_id": "x",
            "generated_at_ms": 1,
        }

        store = TrialStore()
        runner = PackageRunner(vnm, obs_store, store, asset_loader=loader)
        run = store.create_run(package_id="A", scenario_ids=["x"],
                               fault_profile_ids=[], trial_count=1)
        trial = runner.start_trial_async(
            run_id=run.run_id,
            package_id="A",
            node_id="n",
            scenario_id="SCN_TEST_VR",  # has requires_validator_reentry=true
            fault_profile_id=None,
            comparison_condition=None,
            expected_route_class="CLASS_2",
            # Override target only — boolean contract from the scenario file
            # must still survive.
            expected_transition_target_override="CLASS_1",
        )
        # Wait for completion
        import time as _t
        deadline = _t.monotonic() + 3.0
        while _t.monotonic() < deadline:
            t = store.get_trial(trial.trial_id)
            if t and t.status != "pending":
                break
            _t.sleep(0.05)
        result = store.get_trial(trial.trial_id)

        # The contract from the scenario is preserved
        assert result.requires_validator_reentry_when_class1 is True
        # And the target override took effect
        assert result.expected_transition_target == "CLASS_1"

    def test_override_alone_without_scenario_keeps_default_contract(self):
        """When scenario_id is empty, the contract flag falls back to False
        (no scenario to load) — override alone does not invent a contract."""
        from unittest.mock import MagicMock
        from experiment_package.runner import PackageRunner
        from experiment_package.trial_store import TrialStore

        node = MagicMock()
        node.profile.payload_template = {
            "source_node_id": "test",
            "routing_metadata": {"audit_correlation_id": "x",
                                  "ingest_timestamp_ms": 0,
                                  "network_status": "online"},
            "pure_context_payload": {},
        }
        node.profile.publish_topic = "safe_deferral/context/input"
        from virtual_node_manager.models import VirtualNodeState
        node.state = VirtualNodeState.CREATED

        vnm = MagicMock()
        vnm.get_node.return_value = node
        vnm.publish_once.side_effect = lambda n: None

        obs_store = MagicMock()
        obs_store.find_by_correlation_id.return_value = {
            "route": {"route_class": "CLASS_2"},
            "class2": {"transition_target": "CLASS_1",
                       "unresolved_reason": "insufficient_context"},
            "audit_correlation_id": "x",
            "generated_at_ms": 1,
        }

        store = TrialStore()
        runner = PackageRunner(vnm, obs_store, store)
        run = store.create_run(package_id="A", scenario_ids=[],
                               fault_profile_ids=[], trial_count=1)
        trial = runner.start_trial_async(
            run_id=run.run_id,
            package_id="A",
            node_id="n",
            scenario_id="",  # no scenario file
            fault_profile_id=None,
            comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_transition_target_override="CLASS_1",
        )
        import time as _t
        deadline = _t.monotonic() + 3.0
        while _t.monotonic() < deadline:
            t = store.get_trial(trial.trial_id)
            if t and t.status != "pending":
                break
            _t.sleep(0.05)
        result = store.get_trial(trial.trial_id)
        # No scenario → no contract → flag stays False
        assert result.requires_validator_reentry_when_class1 is False
        assert result.expected_transition_target == "CLASS_1"


class TestNotificationStore:
    def test_add_and_find(self):
        from notification_store import NotificationStore
        store = NotificationStore()
        store.add({"audit_correlation_id": "a", "event_summary": "x"})
        store.add({"audit_correlation_id": "b", "event_summary": "y"})
        assert store.find_by_correlation_id("a")["event_summary"] == "x"
        assert store.find_by_correlation_id("b")["event_summary"] == "y"
        assert store.find_by_correlation_id("nonexistent") is None

    def test_returns_most_recent_match(self):
        from notification_store import NotificationStore
        store = NotificationStore()
        store.add({"audit_correlation_id": "a", "event_summary": "old"})
        store.add({"audit_correlation_id": "a", "event_summary": "new"})
        assert store.find_by_correlation_id("a")["event_summary"] == "new"


# ==================================================================
# ClarificationStore — basic ring-buffer behaviour (Phase 5)
# ==================================================================

class TestClarificationStore:
    def test_add_and_find(self):
        from clarification_store import ClarificationStore
        store = ClarificationStore()
        store.add({"audit_correlation_id": "a", "candidate_source": "llm_generated"})
        store.add({"audit_correlation_id": "b", "candidate_source": "default_fallback"})
        assert store.find_by_correlation_id("a")["candidate_source"] == "llm_generated"
        assert store.find_by_correlation_id("b")["candidate_source"] == "default_fallback"
        assert store.find_by_correlation_id("nonexistent") is None

    def test_returns_most_recent_match(self):
        from clarification_store import ClarificationStore
        store = ClarificationStore()
        store.add({"audit_correlation_id": "a", "candidate_source": "default_fallback"})
        store.add({"audit_correlation_id": "a", "candidate_source": "llm_generated"})
        assert store.find_by_correlation_id("a")["candidate_source"] == "llm_generated"


# ==================================================================
# Package D class2_llm_quality block (Phase 5)
# ==================================================================

class TestClass2LlmQualityBlock:
    """Package D's _metrics_d emits a class2_llm_quality sub-block computed
    from each trial's clarification_payload (the record published on
    safe_deferral/clarification/interaction)."""

    def _make_class2_trial_with_clar(self, clar):
        from experiment_package.trial_store import TrialStore
        store = TrialStore()
        run = store.create_run(package_id="D", scenario_ids=["s"],
                               fault_profile_ids=[], trial_count=1)
        trial = store.create_trial(
            run_id=run.run_id, package_id="D", scenario_id="s",
            fault_profile_id=None, comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_validation="safe_deferral",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-q-001",
        )
        obs = {
            "route": {"route_class": "CLASS_2"},
            "validation": {"validation_status": "safe_deferral"},
            "class2": {"transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
                       "unresolved_reason": "insufficient_context"},
        }
        store.complete_trial(trial.trial_id, obs, clarification_payload=clar)
        return store, run

    def _llm_clar(self, confirmed=True):
        return {
            "audit_correlation_id": "audit-q-001",
            "candidate_source": "llm_generated",
            "selection_result": {"selection_source": "bounded_input_node",
                                  "confirmed": confirmed},
        }

    def _fallback_clar(self, confirmed=True):
        return {
            "audit_correlation_id": "audit-q-001",
            "candidate_source": "default_fallback",
            "selection_result": {"selection_source": "bounded_input_node",
                                  "confirmed": confirmed},
        }

    def test_no_records_returns_zero_block(self):
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_class2_trial_with_clar(None)
        m = compute_metrics(store.list_trials_for_run(run.run_id), "D")
        block = m["class2_llm_quality"]
        assert block["clarification_record_count"] == 0
        assert block["llm_generated_count"] == 0
        assert block["llm_generated_rate"] == 0.0
        assert block["default_fallback_rate"] == 0.0
        assert block["llm_user_pickup_rate"] == 0.0
        assert block["default_fallback_user_pickup_rate"] == 0.0

    def test_llm_generated_session_with_pickup(self):
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_class2_trial_with_clar(self._llm_clar(confirmed=True))
        block = compute_metrics(store.list_trials_for_run(run.run_id), "D")["class2_llm_quality"]
        assert block["clarification_record_count"] == 1
        assert block["llm_generated_count"] == 1
        assert block["llm_generated_rate"] == 1.0
        assert block["default_fallback_rate"] == 0.0
        assert block["llm_user_pickup_rate"] == 1.0

    def test_llm_generated_session_without_pickup(self):
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_class2_trial_with_clar(self._llm_clar(confirmed=False))
        block = compute_metrics(store.list_trials_for_run(run.run_id), "D")["class2_llm_quality"]
        assert block["llm_generated_rate"] == 1.0
        assert block["llm_user_pickup_rate"] == 0.0  # selection not confirmed

    def test_default_fallback_session_isolated_from_llm_pickup(self):
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_class2_trial_with_clar(self._fallback_clar(confirmed=True))
        block = compute_metrics(store.list_trials_for_run(run.run_id), "D")["class2_llm_quality"]
        assert block["default_fallback_rate"] == 1.0
        assert block["llm_generated_rate"] == 0.0
        # LLM pickup rate has 0 denominator → 0.0 (not contaminated by fallback pickup)
        assert block["llm_user_pickup_rate"] == 0.0
        assert block["default_fallback_user_pickup_rate"] == 1.0

    def test_mixed_run_separates_pickup_per_source(self):
        """A run with one llm_generated (no pickup) and two default_fallback (one
        pickup each) must report independent pickup rates per source."""
        from experiment_package.trial_store import TrialStore, compute_metrics
        store = TrialStore()
        run = store.create_run(package_id="D", scenario_ids=["s"],
                               fault_profile_ids=[], trial_count=3)
        cases = [
            ("audit-mix-1", "llm_generated", False),
            ("audit-mix-2", "default_fallback", True),
            ("audit-mix-3", "default_fallback", False),
        ]
        for corr, src, confirmed in cases:
            t = store.create_trial(
                run_id=run.run_id, package_id="D", scenario_id="s",
                fault_profile_id=None, comparison_condition=None,
                expected_route_class="CLASS_2",
                expected_validation="safe_deferral",
                expected_outcome="class_2_escalation",
                audit_correlation_id=corr,
            )
            obs = {
                "route": {"route_class": "CLASS_2"},
                "validation": {"validation_status": "safe_deferral"},
                "class2": {"transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
                           "unresolved_reason": "insufficient_context"},
            }
            clar = {
                "audit_correlation_id": corr,
                "candidate_source": src,
                "selection_result": {"selection_source": "bounded_input_node",
                                      "confirmed": confirmed},
            }
            store.complete_trial(t.trial_id, obs, clarification_payload=clar)
        block = compute_metrics(store.list_trials_for_run(run.run_id), "D")["class2_llm_quality"]
        assert block["clarification_record_count"] == 3
        assert block["llm_generated_count"] == 1
        assert block["default_fallback_count"] == 2
        assert block["llm_generated_rate"] == round(1/3, 4)
        assert block["default_fallback_rate"] == round(2/3, 4)
        assert block["llm_user_pickup_rate"] == 0.0  # 0/1
        assert block["default_fallback_user_pickup_rate"] == 0.5  # 1/2

    def test_trial_without_clarification_record_excluded(self):
        """Trials whose clarification_payload was never captured don't pollute
        the rates — clarification_record_count is the denominator."""
        from experiment_package.trial_store import TrialStore, compute_metrics
        store = TrialStore()
        run = store.create_run(package_id="D", scenario_ids=["s"],
                               fault_profile_ids=[], trial_count=2)
        # Trial A: with LLM-generated record
        ta = store.create_trial(
            run_id=run.run_id, package_id="D", scenario_id="s",
            fault_profile_id=None, comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_validation="safe_deferral",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-x-1",
        )
        store.complete_trial(
            ta.trial_id,
            {"route": {"route_class": "CLASS_2"},
             "validation": {"validation_status": "safe_deferral"},
             "class2": {"transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
                        "unresolved_reason": "insufficient_context"}},
            clarification_payload={"audit_correlation_id": "audit-x-1",
                                    "candidate_source": "llm_generated",
                                    "selection_result": {"confirmed": True,
                                                          "selection_source": "bounded_input_node"}},
        )
        # Trial B: no clarification record
        tb = store.create_trial(
            run_id=run.run_id, package_id="D", scenario_id="s",
            fault_profile_id=None, comparison_condition=None,
            expected_route_class="CLASS_2",
            expected_validation="safe_deferral",
            expected_outcome="class_2_escalation",
            audit_correlation_id="audit-x-2",
        )
        store.complete_trial(
            tb.trial_id,
            {"route": {"route_class": "CLASS_2"},
             "validation": {"validation_status": "safe_deferral"},
             "class2": {"transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
                        "unresolved_reason": "insufficient_context"}},
            clarification_payload=None,
        )
        block = compute_metrics(store.list_trials_for_run(run.run_id), "D")["class2_llm_quality"]
        assert block["clarification_record_count"] == 1  # only A
        assert block["llm_generated_rate"] == 1.0  # 1/1


# ==================================================================
# PackageRunner — clarification record capture (Phase 5)
# ==================================================================

class TestClarificationCapture:
    """Runner forwards a captured clarification record into TrialResult and
    tolerates late arrivals via _await_clarification grace polling."""

    def test_clarification_arriving_after_observation_is_captured(self):
        from unittest.mock import MagicMock
        from experiment_package.runner import PackageRunner
        from experiment_package.trial_store import TrialStore
        from clarification_store import ClarificationStore
        from notification_store import NotificationStore
        import threading
        import time as _t

        publishes: list[dict] = []
        node = MagicMock()
        node.profile.payload_template = {
            "source_node_id": "test",
            "routing_metadata": {"audit_correlation_id": "x",
                                  "ingest_timestamp_ms": 0,
                                  "network_status": "online"},
            "pure_context_payload": {},
        }
        node.profile.publish_topic = "safe_deferral/context/input"
        from virtual_node_manager.models import VirtualNodeState
        node.state = VirtualNodeState.CREATED
        vnm = MagicMock()
        vnm.get_node.return_value = node
        vnm.publish_once.side_effect = lambda n: publishes.append(
            dict(n.profile.payload_template)
        )

        obs = {
            "route": {"route_class": "CLASS_2"},
            "validation": {"validation_status": "safe_deferral"},
            "class2": {"transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
                       "should_notify_caregiver": True,
                       "unresolved_reason": "timeout_or_no_response"},
            "audit_correlation_id": "x",
            "generated_at_ms": 1,
        }
        obs_store = MagicMock()
        obs_store.find_by_correlation_id.return_value = obs

        notif_store = NotificationStore()
        clar_store = ClarificationStore()

        store = TrialStore()
        runner = PackageRunner(
            vnm, obs_store, store,
            notification_store=notif_store,
            clarification_store=clar_store,
        )
        run = store.create_run(package_id="D", scenario_ids=[],
                               fault_profile_ids=[], trial_count=1)
        trial = runner.start_trial_async(
            run_id=run.run_id, package_id="D", node_id="n",
            scenario_id="", fault_profile_id=None,
            comparison_condition=None,
            expected_route_class="CLASS_2",
        )
        deadline = _t.monotonic() + 2.0
        while _t.monotonic() < deadline:
            if publishes:
                break
            _t.sleep(0.05)
        corr = publishes[0]["routing_metadata"]["audit_correlation_id"]

        # Schedule the late clarification record arrival.
        def _emit_after():
            _t.sleep(0.3)
            clar_store.add({
                "audit_correlation_id": corr,
                "candidate_source": "llm_generated",
                "selection_result": {"confirmed": True,
                                      "selection_source": "bounded_input_node"},
            })
        threading.Thread(target=_emit_after, daemon=True).start()

        deadline = _t.monotonic() + 5.0
        while _t.monotonic() < deadline:
            t = store.get_trial(trial.trial_id)
            if t and t.status != "pending":
                break
            _t.sleep(0.05)
        result = store.get_trial(trial.trial_id)
        assert result.status == "completed"
        assert result.clarification_payload is not None
        assert result.clarification_payload["audit_correlation_id"] == corr
        assert result.clarification_payload["candidate_source"] == "llm_generated"
