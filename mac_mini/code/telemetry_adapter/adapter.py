"""Read-Only Telemetry Adapter (MM-10).

Collects minimum experiment-safe state from upstream components and
exposes it as a read-only TelemetrySnapshot.

Authority boundary (02_safety_and_authority_boundaries.md §9):
  - Snapshot is visibility data only.
  - No dashboard-originated policy override.
  - No direct actuator control.
  - No registry, policy, or schema editing through this adapter.
  - MQTT publishing target is safe_deferral/dashboard/observation only.

update_*() methods are the intake points — called by each component after
it produces a result.  get_snapshot() returns the current state.
publish() pushes the snapshot to the injected MqttPublisher.
"""

import time
import uuid
from typing import Optional, Protocol

from audit_logger.logger import AuditReader
from caregiver_escalation.models import EscalationResult
from class2_clarification_manager.models import Class2Result
from deterministic_validator.models import ValidatorResult
from low_risk_dispatcher.models import DispatchRecord
from policy_router.models import PolicyRouterResult
from telemetry_adapter.models import (
    AckTelemetry,
    Class2Telemetry,
    EscalationTelemetry,
    RouteTelemetry,
    TelemetrySnapshot,
    ValidationTelemetry,
)

OBSERVATION_TOPIC = "safe_deferral/dashboard/observation"


class MqttPublisher(Protocol):
    def publish(self, topic: str, payload: dict, qos: int = 1) -> None: ...


class _NoOpPublisher:
    def publish(self, topic: str, payload: dict, qos: int = 1) -> None:
        pass


class TelemetryAdapter:
    """Accumulates component results and exposes a read-only telemetry snapshot.

    Typical wiring:
        telemetry = TelemetryAdapter(mqtt_publisher=mqtt_client)
        router_result = router.route(context_input)
        telemetry.update_route(router_result)
        validator_result = validator.validate(candidate)
        telemetry.update_validation(validator_result)
        ...
        telemetry.publish()
    """

    def __init__(
        self,
        mqtt_publisher: Optional[MqttPublisher] = None,
        audit_reader: Optional[AuditReader] = None,
    ) -> None:
        self._publisher: MqttPublisher = mqtt_publisher or _NoOpPublisher()
        self._audit_reader: Optional[AuditReader] = audit_reader
        self._route: Optional[RouteTelemetry] = None
        self._validation: Optional[ValidationTelemetry] = None
        self._ack: Optional[AckTelemetry] = None
        self._class2: Optional[Class2Telemetry] = None
        self._escalation: Optional[EscalationTelemetry] = None

    # ------------------------------------------------------------------
    # Intake methods — called by other components
    # ------------------------------------------------------------------

    def update_route(self, result: PolicyRouterResult) -> None:
        self._route = RouteTelemetry(
            route_class=result.route_class.value,
            trigger_id=result.trigger_id,
            timestamp_ms=result.routed_at_ms,
        )

    def update_validation(self, result: ValidatorResult) -> None:
        self._validation = ValidationTelemetry(
            validation_status=result.validation_status.value,
            exception_trigger_id=result.exception_trigger_id,
            timestamp_ms=int(time.time() * 1000),
        )

    def update_ack(self, record: DispatchRecord) -> None:
        self._ack = AckTelemetry(
            dispatch_status=record.dispatch_status.value,
            action=record.action,
            target_device=record.target_device,
            timestamp_ms=record.ack_received_at_ms or record.published_at_ms,
        )

    def update_class2(self, result: Class2Result) -> None:
        unresolved = result.clarification_record.get("unresolved_reason")
        self._class2 = Class2Telemetry(
            transition_target=result.transition_target.value,
            should_notify_caregiver=result.should_notify_caregiver,
            unresolved_reason=unresolved,
            timestamp_ms=int(time.time() * 1000),
        )

    def update_escalation(self, result: EscalationResult) -> None:
        self._escalation = EscalationTelemetry(
            escalation_status=result.escalation_status.value,
            notification_channel=result.notification_record.notification_channel,
            timestamp_ms=result.notification_record.sent_at_ms,
        )

    # ------------------------------------------------------------------
    # Snapshot / publish
    # ------------------------------------------------------------------

    def get_snapshot(self) -> TelemetrySnapshot:
        """Return the current telemetry snapshot (always read-only)."""
        audit_count = 0
        if self._audit_reader is not None:
            audit_count = self._audit_reader.count()

        return TelemetrySnapshot(
            snapshot_id=str(uuid.uuid4()),
            generated_at_ms=int(time.time() * 1000),
            route=self._route,
            validation=self._validation,
            ack=self._ack,
            class2=self._class2,
            escalation=self._escalation,
            audit_event_count=audit_count,
        )

    def publish(self) -> TelemetrySnapshot:
        """Build snapshot and publish to safe_deferral/dashboard/observation."""
        snapshot = self.get_snapshot()
        self._publisher.publish(OBSERVATION_TOPIC, snapshot.to_dict(), qos=1)
        return snapshot

    def reset(self) -> None:
        """Clear all accumulated state (useful between experiment runs)."""
        self._route = None
        self._validation = None
        self._ack = None
        self._class2 = None
        self._escalation = None
