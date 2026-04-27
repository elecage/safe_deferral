"""Deterministic Validator — Class 1 execution gate.

Receives a single LLM-generated candidate action and decides:
  - approved            → forward ExecutablePayload to actuator dispatcher
  - safe_deferral       → forward to context-integrity safe deferral handler
  - rejected_escalation → forward to Class 2 clarification/escalation

Authority rule (from 02_safety_and_authority_boundaries.md):
  - Only the canonical low-risk catalog (low_risk_actions.json) defines
    admissible autonomous actions. Schema validity alone is not enough.
  - Doorlock and any sensitive actuation must not be approved here.
  - Candidate text is guidance only; it is never execution authority by itself.
"""

from typing import Optional

import jsonschema

from deterministic_validator.models import (
    ExecutablePayload,
    RoutingTarget,
    ValidationStatus,
    ValidatorResult,
)
from shared.asset_loader import AssetLoader


class DeterministicValidator:
    def __init__(self, asset_loader: Optional[AssetLoader] = None):
        loader = asset_loader or AssetLoader()

        self._candidate_schema = loader.load_schema("candidate_action_schema.json")
        self._resolver = loader.make_schema_resolver()

        low_risk = loader.load_low_risk_actions()
        # Build catalog: (action, target_device) → requires_ack
        self._catalog: dict[tuple[str, str], bool] = {
            (item["action"], target): item["requires_ack"]
            for item in low_risk["allowed_actions_taxonomy"]
            for target in item["allowed_targets"]
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(
        self,
        candidate: dict,
        audit_correlation_id: str = "",
    ) -> ValidatorResult:
        """Validate a single LLM candidate action against the low-risk catalog."""

        # Step 1: schema validation (C202 on failure)
        schema_error = self._validate_schema(candidate)
        if schema_error:
            return self._rejected(
                exception_trigger_id="C202",
                audit_correlation_id=audit_correlation_id,
            )

        proposed_action: str = candidate["proposed_action"]
        target_device: str = candidate["target_device"]

        # Step 2: candidate self-reports deferral → pass through
        if proposed_action == "safe_deferral":
            return ValidatorResult(
                validation_status=ValidationStatus.SAFE_DEFERRAL,
                routing_target=RoutingTarget.SAFE_DEFERRAL_HANDLER,
                exception_trigger_id="none",
                executable_payload=None,
                deferral_reason=candidate["deferral_reason"],
                audit_correlation_id=audit_correlation_id,
            )

        # Step 3: catalog check (C203 on unknown action/target pair)
        requires_ack = self._catalog.get((proposed_action, target_device))
        if requires_ack is None:
            return self._rejected(
                exception_trigger_id="C203",
                audit_correlation_id=audit_correlation_id,
            )

        # Step 4: approved
        return ValidatorResult(
            validation_status=ValidationStatus.APPROVED,
            routing_target=RoutingTarget.ACTUATOR_DISPATCHER,
            exception_trigger_id="none",
            executable_payload=ExecutablePayload(
                action=proposed_action,
                target_device=target_device,
                requires_ack=requires_ack,
            ),
            deferral_reason=None,
            audit_correlation_id=audit_correlation_id,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_schema(self, candidate: dict) -> Optional[str]:
        try:
            validator = jsonschema.Draft7Validator(
                schema=self._candidate_schema,
                resolver=self._resolver,
            )
            errors = sorted(validator.iter_errors(candidate), key=str)
            if errors:
                return errors[0].message
        except Exception as exc:  # noqa: BLE001
            return str(exc)
        return None

    @staticmethod
    def _rejected(exception_trigger_id: str, audit_correlation_id: str) -> ValidatorResult:
        return ValidatorResult(
            validation_status=ValidationStatus.REJECTED_ESCALATION,
            routing_target=RoutingTarget.CLASS_2_ESCALATION,
            exception_trigger_id=exception_trigger_id,
            executable_payload=None,
            deferral_reason=None,
            audit_correlation_id=audit_correlation_id,
        )
