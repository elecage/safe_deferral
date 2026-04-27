"""Operational MQTT Context Intake (MM-01).

Receives context payloads (from MQTT or direct call in tests), validates
them against policy_router_input_schema.json, and classifies each as
ACCEPTED, REJECTED, or QUARANTINED.

Processing rules:
  1. JSON parse failure                                → REJECTED
  2. Outer schema validation failure (including pure_context_payload
     via $ref to context_schema.json)                 → REJECTED
  3. All checks pass                                   → ACCEPTED

  QUARANTINED is reserved for future semantic checks that are not
  currently expressible in the JSON schema (e.g. cross-field invariants,
  runtime freshness rules applied outside the Policy Router).  Under the
  current schema structure, all known failure modes result in REJECTED.

Authority boundary:
  - No actuator dispatch.
  - No LLM invocation.
  - No policy decision on unvalidated payloads.
  - doorbell_detected is visitor context only — never doorlock authorization.
  - REJECTED / QUARANTINED results must never become Class 1 requests.
"""

import time
import uuid
from typing import Optional

import jsonschema

from audit_logger.logger import AuditLogger
from audit_logger.models import AuditEvent, EventGroup
from context_intake.models import IntakeResult, IntakeStatus
from shared.asset_loader import AssetLoader


class ContextIntake:
    """Validates and classifies incoming context payloads.

    Usage:
        intake = ContextIntake()
        result = intake.process(raw_payload)
        if result.is_accepted:
            router_result = router.route(result.raw_payload)
    """

    def __init__(
        self,
        asset_loader: Optional[AssetLoader] = None,
        audit_logger: Optional[AuditLogger] = None,
    ) -> None:
        loader = asset_loader or AssetLoader()
        self._schema = loader.load_schema("policy_router_input_schema.json")
        self._context_schema = loader.load_schema("context_schema.json")
        self._resolver = loader.make_schema_resolver()
        self._audit_logger = audit_logger

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(
        self,
        raw_payload: dict,
        ingest_timestamp_ms: Optional[int] = None,
    ) -> IntakeResult:
        """Process a single incoming context payload.

        raw_payload may come from an MQTT message body (already parsed from JSON)
        or be passed directly in tests.
        """
        ts = ingest_timestamp_ms or int(time.time() * 1000)

        # --- Step 1: outer schema validation ---
        rejection = self._validate_outer_schema(raw_payload)
        if rejection:
            return self._make_result(
                IntakeStatus.REJECTED, raw_payload, ts, rejection
            )

        source_node_id = raw_payload.get("source_node_id", "unknown")
        routing_metadata = raw_payload.get("routing_metadata", {})
        pure_ctx = raw_payload.get("pure_context_payload", {})
        audit_id = routing_metadata.get("audit_correlation_id") or str(uuid.uuid4())

        # --- Step 2: pure_context_payload schema validation (quarantine) ---
        quarantine_reason = self._validate_context_schema(pure_ctx)
        if quarantine_reason:
            result = IntakeResult(
                status=IntakeStatus.QUARANTINED,
                source_node_id=source_node_id,
                audit_correlation_id=audit_id,
                ingest_timestamp_ms=ts,
                pure_context_payload=None,
                routing_metadata=None,
                rejection_reason=quarantine_reason,
                raw_payload=raw_payload,
            )
            self._emit_audit(result)
            return result

        result = IntakeResult(
            status=IntakeStatus.ACCEPTED,
            source_node_id=source_node_id,
            audit_correlation_id=audit_id,
            ingest_timestamp_ms=ts,
            pure_context_payload=pure_ctx,
            routing_metadata=routing_metadata,
            rejection_reason=None,
            raw_payload=raw_payload,
        )
        self._emit_audit(result)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_outer_schema(self, payload: dict) -> Optional[str]:
        """Return rejection reason string or None if valid."""
        try:
            validator = jsonschema.Draft7Validator(
                self._schema, resolver=self._resolver
            )
            errors = list(validator.iter_errors(payload))
            if errors:
                return f"schema_validation_failed: {errors[0].message}"
        except Exception as exc:
            return f"schema_validation_error: {exc}"
        return None

    def _validate_context_schema(self, pure_ctx: dict) -> Optional[str]:
        """Validate pure_context_payload against context_schema.json.
        Returns quarantine reason or None."""
        try:
            validator = jsonschema.Draft7Validator(
                self._context_schema, resolver=self._resolver
            )
            errors = list(validator.iter_errors(pure_ctx))
            if errors:
                return f"context_schema_invalid: {errors[0].message}"
        except Exception as exc:
            return f"context_schema_error: {exc}"
        return None

    def _make_result(
        self,
        status: IntakeStatus,
        raw_payload: dict,
        ts: int,
        reason: str,
    ) -> IntakeResult:
        result = IntakeResult(
            status=status,
            source_node_id=raw_payload.get("source_node_id", "unknown"),
            audit_correlation_id=str(uuid.uuid4()),
            ingest_timestamp_ms=ts,
            pure_context_payload=None,
            routing_metadata=None,
            rejection_reason=reason,
            raw_payload=raw_payload,
        )
        self._emit_audit(result)
        return result

    def _emit_audit(self, result: IntakeResult) -> None:
        if self._audit_logger is None:
            return
        group = (
            EventGroup.SYSTEM
            if result.status != IntakeStatus.ACCEPTED
            else EventGroup.ROUTING
        )
        self._audit_logger.log(AuditEvent(
            event_group=group,
            event_type=f"context_intake_{result.status.value}",
            audit_correlation_id=result.audit_correlation_id,
            summary=(
                f"Context intake {result.status.value} "
                f"from {result.source_node_id}"
            ),
            payload=result.to_audit_dict(),
        ))
