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
        obs = {
            "route": {"route_class": "CLASS_2"},
            "validation": {"validation_status": "safe_deferral"},
            "class2": {
                "transition_target": observed_target,
                "should_notify_caregiver": False,
                "unresolved_reason": "caregiver_required_sensitive_path",
                "timestamp_ms": 0,
            },
            "generated_at_ms": 1000,
        }
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
    """_metrics_d must read the nested observation snapshot, not flat keys."""

    def _make_class2_trial(self, observation):
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
        store.complete_trial(trial.trial_id, observation)
        return store, run

    def _full_class2_observation(self):
        return {
            "audit_correlation_id": "audit-d-001",
            "generated_at_ms": 1700000000000,
            "route": {
                "route_class": "CLASS_2",
                "trigger_id": "C206",
                "timestamp_ms": 1699999999999,
            },
            "validation": {"validation_status": "safe_deferral"},
            "class2": {
                "transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
                "should_notify_caregiver": True,
                "unresolved_reason": "insufficient_context",
                "timestamp_ms": 1700000000001,
            },
        }

    def test_complete_nested_observation_is_complete(self):
        """A well-formed nested CLASS_2 telemetry snapshot scores 100% complete."""
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_class2_trial(self._full_class2_observation())
        metrics = compute_metrics(store.list_trials_for_run(run.run_id), "D")
        assert metrics["payload_completeness_rate"] == 1.0
        assert metrics["missing_field_rate"] == 0.0

    def test_flat_keys_alone_no_longer_score_complete(self):
        """The pre-fix flat-key shape must NOT count as a complete CLASS_2 payload."""
        from experiment_package.trial_store import compute_metrics
        store, run = self._make_class2_trial({
            "route_class": "CLASS_2",
            "validation_status": "safe_deferral",
            "audit_correlation_id": "audit-d-001",
            "snapshot_ts_ms": 1700000000000,
            "ingest_timestamp_ms": 1699999999999,
        })
        metrics = compute_metrics(store.list_trials_for_run(run.run_id), "D")
        assert metrics["payload_completeness_rate"] == 0.0

    def test_missing_field_appears_in_breakdown(self):
        """Missing class2.unresolved_reason is reported in missing_by_field."""
        from experiment_package.trial_store import compute_metrics
        obs = self._full_class2_observation()
        del obs["class2"]["unresolved_reason"]
        store, run = self._make_class2_trial(obs)
        metrics = compute_metrics(store.list_trials_for_run(run.run_id), "D")
        assert metrics["missing_by_field"]["class2.unresolved_reason"] == 1
        assert metrics["payload_completeness_rate"] == 0.0


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
