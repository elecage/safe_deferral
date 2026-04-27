"""Low-Risk Dispatcher (MM-07).

Accepts a ValidatorResult with status=APPROVED and publishes an actuation
command to safe_deferral/actuation/command.  Returns a DispatchResult that
carries the command payload and a mutable DispatchRecord for ACK tracking.

Authority boundary:
  - Only dispatches ExecutablePayload that was approved by DeterministicValidator.
  - Does not invoke LLM, bypass policy, or dispatch Class 0 / Class 2 paths.
  - MQTT publishing is injected via MqttPublisher protocol so the dispatcher
    itself has no network dependency and can be unit-tested synchronously.
"""

import time
import uuid
from typing import Optional, Protocol

from deterministic_validator.models import ExecutablePayload, ValidatorResult, ValidationStatus
from low_risk_dispatcher.models import (
    AckStatus,
    DispatchRecord,
    DispatchResult,
    DispatchStatus,
)
from shared.asset_loader import AssetLoader


class MqttPublisher(Protocol):
    """Minimal interface the dispatcher needs to publish a command."""

    def publish(self, topic: str, payload: dict, qos: int = 1) -> None: ...


class _NoOpPublisher:
    """Used when no MQTT client is injected (test / dry-run mode)."""

    def publish(self, topic: str, payload: dict, qos: int = 1) -> None:
        pass


class LowRiskDispatcher:
    """Publishes approved low-risk actuation commands.

    Typical call sequence:
        result = dispatcher.dispatch(validator_result)
        # … wait for ACK via MQTT subscription …
        ack_result = ack_handler.handle_ack(result.dispatch_record, ack_payload)
    """

    COMMAND_TOPIC = "safe_deferral/actuation/command"

    def __init__(
        self,
        mqtt_publisher: Optional[MqttPublisher] = None,
        asset_loader: Optional[AssetLoader] = None,
    ) -> None:
        loader = asset_loader or AssetLoader()
        policy = loader.load_policy_table()
        gc = policy["global_constraints"]
        self._ack_timeout_ms: int = gc["actuation_ack_timeout_ms"]
        self._publisher: MqttPublisher = mqtt_publisher or _NoOpPublisher()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def dispatch(
        self,
        validator_result: ValidatorResult,
        command_id: Optional[str] = None,
    ) -> DispatchResult:
        """Publish a command for the approved ExecutablePayload.

        Raises ValueError if the validator result is not APPROVED or has no
        executable payload — callers must not reach this method on non-approved
        results.
        """
        if validator_result.validation_status != ValidationStatus.APPROVED:
            raise ValueError(
                f"dispatch() requires APPROVED status, got "
                f"{validator_result.validation_status.value}"
            )
        payload_obj: ExecutablePayload = validator_result.executable_payload
        if payload_obj is None:
            raise ValueError("dispatch() requires a non-None executable_payload")

        cid = command_id or str(uuid.uuid4())
        now_ms = int(time.time() * 1000)

        command_payload = {
            "command_id": cid,
            "source_decision": "validator_output",
            "action": payload_obj.action,
            "target_device": payload_obj.target_device,
            "requires_ack": payload_obj.requires_ack,
            "audit_correlation_id": validator_result.audit_correlation_id,
            "authority_note": (
                "This low-risk command is valid only after deterministic validator approval."
            ),
        }

        record = DispatchRecord(
            command_id=cid,
            action=payload_obj.action,
            target_device=payload_obj.target_device,
            requires_ack=payload_obj.requires_ack,
            audit_correlation_id=validator_result.audit_correlation_id,
            source_decision="validator_output",
            dispatch_status=DispatchStatus.PENDING,
            published_at_ms=now_ms,
            ack_status=None,
            ack_received_at_ms=None,
            observed_state=None,
            ack_timeout_ms=self._ack_timeout_ms,
        )

        self._publisher.publish(self.COMMAND_TOPIC, command_payload, qos=1)
        record.dispatch_status = DispatchStatus.PUBLISHED

        return DispatchResult(
            command_id=cid,
            dispatch_status=DispatchStatus.PUBLISHED,
            action=payload_obj.action,
            target_device=payload_obj.target_device,
            audit_correlation_id=validator_result.audit_correlation_id,
            command_payload=command_payload,
            dispatch_record=record,
        )
