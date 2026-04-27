"""Tests for DeterministicValidator.

Fixture field names and values follow candidate_action_schema.json exactly.
"""

import pytest

from deterministic_validator.validator import DeterministicValidator
from deterministic_validator.models import ValidationStatus, RoutingTarget


@pytest.fixture(scope="module")
def validator():
    return DeterministicValidator()


AUDIT_ID = "test_audit_001"


# ------------------------------------------------------------------
# Approved — all four catalog entries
# ------------------------------------------------------------------

class TestApproved:
    @pytest.mark.parametrize("action,target", [
        ("light_on",  "living_room_light"),
        ("light_on",  "bedroom_light"),
        ("light_off", "living_room_light"),
        ("light_off", "bedroom_light"),
    ])
    def test_catalog_entry_approved(self, validator, action, target):
        result = validator.validate(
            {"proposed_action": action, "target_device": target},
            audit_correlation_id=AUDIT_ID,
        )
        assert result.validation_status == ValidationStatus.APPROVED
        assert result.routing_target == RoutingTarget.ACTUATOR_DISPATCHER
        assert result.exception_trigger_id == "none"
        assert result.deferral_reason is None
        assert result.executable_payload is not None

    def test_approved_executable_payload_fields(self, validator):
        result = validator.validate(
            {"proposed_action": "light_on", "target_device": "living_room_light"},
            audit_correlation_id=AUDIT_ID,
        )
        ep = result.executable_payload
        assert ep.action == "light_on"
        assert ep.target_device == "living_room_light"
        assert ep.requires_ack is True   # policy mandates ACK for all low-risk actions

    def test_approved_to_dict_schema_shape(self, validator):
        result = validator.validate(
            {"proposed_action": "light_off", "target_device": "bedroom_light"},
            audit_correlation_id=AUDIT_ID,
        )
        d = result.to_dict()
        assert d["validation_status"] == "approved"
        assert d["routing_target"] == "actuator_dispatcher"
        assert d["exception_trigger_id"] == "none"
        assert "executable_payload" in d
        assert "deferral_reason" not in d

    def test_audit_id_preserved_on_approval(self, validator):
        result = validator.validate(
            {"proposed_action": "light_on", "target_device": "bedroom_light"},
            audit_correlation_id="my_audit_xyz",
        )
        assert result.audit_correlation_id == "my_audit_xyz"

    def test_optional_rationale_summary_ignored(self, validator):
        """rationale_summary is for logging only; must not affect routing."""
        result = validator.validate({
            "proposed_action": "light_on",
            "target_device": "living_room_light",
            "rationale_summary": "User seems to want light on.",
        })
        assert result.validation_status == ValidationStatus.APPROVED


# ------------------------------------------------------------------
# Safe deferral — LLM self-reports it cannot resolve
# ------------------------------------------------------------------

class TestSafeDeferral:
    @pytest.mark.parametrize("reason", [
        "ambiguous_target",
        "insufficient_context",
        "policy_restriction",
        "unresolved_multi_candidate",
    ])
    def test_deferral_reason_pass_through(self, validator, reason):
        result = validator.validate({
            "proposed_action": "safe_deferral",
            "target_device": "none",
            "deferral_reason": reason,
        })
        assert result.validation_status == ValidationStatus.SAFE_DEFERRAL
        assert result.routing_target == RoutingTarget.SAFE_DEFERRAL_HANDLER
        assert result.exception_trigger_id == "none"
        assert result.deferral_reason == reason
        assert result.executable_payload is None

    def test_safe_deferral_to_dict_schema_shape(self, validator):
        result = validator.validate({
            "proposed_action": "safe_deferral",
            "target_device": "none",
            "deferral_reason": "ambiguous_target",
        })
        d = result.to_dict()
        assert d["validation_status"] == "safe_deferral"
        assert d["routing_target"] == "context_integrity_safe_deferral_handler"
        assert d["exception_trigger_id"] == "none"
        assert d["deferral_reason"] == "ambiguous_target"
        assert "executable_payload" not in d


# ------------------------------------------------------------------
# Rejected escalation — schema violations (C202)
# ------------------------------------------------------------------

class TestRejectedSchemaViolation:
    def test_empty_candidate(self, validator):
        result = validator.validate({})
        assert result.validation_status == ValidationStatus.REJECTED_ESCALATION
        assert result.exception_trigger_id == "C202"

    def test_missing_proposed_action(self, validator):
        result = validator.validate({"target_device": "living_room_light"})
        assert result.validation_status == ValidationStatus.REJECTED_ESCALATION
        assert result.exception_trigger_id == "C202"

    def test_missing_target_device(self, validator):
        result = validator.validate({"proposed_action": "light_on"})
        assert result.validation_status == ValidationStatus.REJECTED_ESCALATION
        assert result.exception_trigger_id == "C202"

    def test_unknown_proposed_action(self, validator):
        """Sensitive actions (doorlock etc.) must never appear here."""
        result = validator.validate({
            "proposed_action": "door_unlock",
            "target_device": "living_room_light",
        })
        assert result.validation_status == ValidationStatus.REJECTED_ESCALATION
        assert result.exception_trigger_id == "C202"

    def test_unknown_target_device(self, validator):
        result = validator.validate({
            "proposed_action": "light_on",
            "target_device": "front_door_lock",
        })
        assert result.validation_status == ValidationStatus.REJECTED_ESCALATION
        assert result.exception_trigger_id == "C202"

    def test_light_action_with_none_target(self, validator):
        """allOf rule: light_on/off must not have target_device='none'."""
        result = validator.validate({
            "proposed_action": "light_on",
            "target_device": "none",
        })
        assert result.validation_status == ValidationStatus.REJECTED_ESCALATION
        assert result.exception_trigger_id == "C202"

    def test_safe_deferral_without_deferral_reason(self, validator):
        """allOf rule: safe_deferral requires deferral_reason."""
        result = validator.validate({
            "proposed_action": "safe_deferral",
            "target_device": "none",
        })
        assert result.validation_status == ValidationStatus.REJECTED_ESCALATION
        assert result.exception_trigger_id == "C202"

    def test_safe_deferral_with_non_none_target(self, validator):
        """allOf rule: safe_deferral must have target_device='none'."""
        result = validator.validate({
            "proposed_action": "safe_deferral",
            "target_device": "living_room_light",
            "deferral_reason": "ambiguous_target",
        })
        assert result.validation_status == ValidationStatus.REJECTED_ESCALATION
        assert result.exception_trigger_id == "C202"

    def test_light_action_with_deferral_reason(self, validator):
        """allOf rule: light_on/off must not include deferral_reason."""
        result = validator.validate({
            "proposed_action": "light_on",
            "target_device": "living_room_light",
            "deferral_reason": "ambiguous_target",
        })
        assert result.validation_status == ValidationStatus.REJECTED_ESCALATION
        assert result.exception_trigger_id == "C202"

    def test_extra_unknown_field(self, validator):
        """additionalProperties: false — unknown fields must fail."""
        result = validator.validate({
            "proposed_action": "light_on",
            "target_device": "living_room_light",
            "doorlock_command": "unlock",
        })
        assert result.validation_status == ValidationStatus.REJECTED_ESCALATION
        assert result.exception_trigger_id == "C202"

    def test_rejected_to_dict_schema_shape(self, validator):
        result = validator.validate({})
        d = result.to_dict()
        assert d["validation_status"] == "rejected_escalation"
        assert d["routing_target"] == "class_2_escalation"
        assert d["exception_trigger_id"] == "C202"
        assert "executable_payload" not in d
        assert "deferral_reason" not in d


# ------------------------------------------------------------------
# Doorlock / sensitive actuation — must never be approved
# ------------------------------------------------------------------

class TestSensitiveActuationBlocked:
    def test_doorlock_action_blocked(self, validator):
        result = validator.validate({
            "proposed_action": "door_unlock",
            "target_device": "living_room_light",
        })
        assert result.validation_status == ValidationStatus.REJECTED_ESCALATION

    def test_doorlock_target_blocked_even_with_valid_action(self, validator):
        result = validator.validate({
            "proposed_action": "light_on",
            "target_device": "front_door_lock",
        })
        assert result.validation_status == ValidationStatus.REJECTED_ESCALATION
