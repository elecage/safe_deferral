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
from shared.asset_loader import AssetLoader
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
        asset_loader: Optional[AssetLoader] = None,
    ) -> None:
        loader = asset_loader or AssetLoader()
        self._observation_topic: str = loader.get_topic("safe_deferral/dashboard/observation")
        self._publisher: MqttPublisher = mqtt_publisher or _NoOpPublisher()
        self._audit_reader: Optional[AuditReader] = audit_reader
        self._audit_correlation_id: str = ""
        self._route: Optional[RouteTelemetry] = None
        self._validation: Optional[ValidationTelemetry] = None
        self._ack: Optional[AckTelemetry] = None
        self._class2: Optional[Class2Telemetry] = None
        self._escalation: Optional[EscalationTelemetry] = None

    # ------------------------------------------------------------------
    # Intake methods — called by other components
    # ------------------------------------------------------------------

    def update_route(self, result: PolicyRouterResult) -> None:
        self._audit_correlation_id = result.audit_correlation_id
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
            command_id=record.command_id,
            audit_correlation_id=record.audit_correlation_id,
        )

    def update_class2(self, result: Class2Result) -> None:
        unresolved = result.clarification_record.get("unresolved_reason")
        self._class2 = Class2Telemetry(
            transition_target=result.transition_target.value,
            should_notify_caregiver=result.should_notify_caregiver,
            unresolved_reason=unresolved,
            timestamp_ms=int(time.time() * 1000),
        )

    def escalate_to_class2(self) -> None:
        """Override route_class to CLASS_2 in the current snapshot.

        Called when a CLASS_1 event internally escalates to CLASS_2
        (e.g. safe_deferral → C207).  The PolicyRouter set route_class=CLASS_1
        originally; this corrects it so the experiment observation reflects the
        final outcome class rather than the initial routing decision.
        """
        if self._route is not None:
            self._route = RouteTelemetry(
                route_class="CLASS_2",
                trigger_id=self._route.trigger_id,
                timestamp_ms=self._route.timestamp_ms,
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
            audit_correlation_id=self._audit_correlation_id,
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
        self._publisher.publish(self._observation_topic, snapshot.to_dict(), qos=1)
        return snapshot

    def publish_ack_only(self, record: "DispatchRecord") -> TelemetrySnapshot:
        """Publish an isolated ACK snapshot without touching shared adapter state.

        Used for late-arriving ACKs and ACK timeout events that arrive outside
        of a handle_context() call — prevents mixing ACK data with a different
        event's route/validation fields.
        """
        ack = AckTelemetry(
            dispatch_status=record.dispatch_status.value,
            action=record.action,
            target_device=record.target_device,
            timestamp_ms=record.ack_received_at_ms or record.published_at_ms,
            command_id=record.command_id,
            audit_correlation_id=record.audit_correlation_id,
        )
        snapshot = TelemetrySnapshot(
            snapshot_id=str(uuid.uuid4()),
            generated_at_ms=int(time.time() * 1000),
            ack=ack,
            audit_event_count=self._audit_reader.count() if self._audit_reader else 0,
        )
        self._publisher.publish(self._observation_topic, snapshot.to_dict(), qos=1)
        return snapshot

    def publish_c205_snapshot(
        self,
        class2_result: "Class2Result",
        esc_result: "EscalationResult",
        audit_correlation_id: str = "",
    ) -> TelemetrySnapshot:
        """Publish an isolated C205 snapshot without touching shared adapter state.

        Used by the ACK timeout sweep's _escalate_c205() path.
        """
        unresolved = class2_result.clarification_record.get("unresolved_reason")
        class2 = Class2Telemetry(
            transition_target=class2_result.transition_target.value,
            should_notify_caregiver=class2_result.should_notify_caregiver,
            unresolved_reason=unresolved,
            timestamp_ms=int(time.time() * 1000),
        )
        escalation = EscalationTelemetry(
            escalation_status=esc_result.escalation_status.value,
            notification_channel=esc_result.notification_record.notification_channel,
            timestamp_ms=esc_result.notification_record.sent_at_ms,
        )
        snapshot = TelemetrySnapshot(
            snapshot_id=str(uuid.uuid4()),
            generated_at_ms=int(time.time() * 1000),
            class2=class2,
            escalation=escalation,
            audit_correlation_id=audit_correlation_id,
            audit_event_count=self._audit_reader.count() if self._audit_reader else 0,
        )
        self._publisher.publish(self._observation_topic, snapshot.to_dict(), qos=1)
        return snapshot

    def publish_class2_update(
        self,
        audit_correlation_id: str,
        class2_result: Class2Result,
    ) -> None:
        """Publish a standalone CLASS_2 interaction snapshot.

        Called from the background two-phase waiter thread after Phase 1
        resolves (user response or timeout → caregiver path).  Creates an
        isolated snapshot with the given correlation ID so that the
        observation matches the trial even if the shared adapter state has
        been reset by a subsequent event.

        The snapshot includes route_class=CLASS_2 so the runner's
        _match_observation() can identify it as a final CLASS_2 observation.
        """
        unresolved = class2_result.clarification_record.get("unresolved_reason")
        now_ms = int(time.time() * 1000)
        class2 = Class2Telemetry(
            transition_target=class2_result.transition_target.value,
            should_notify_caregiver=class2_result.should_notify_caregiver,
            unresolved_reason=unresolved,
            timestamp_ms=now_ms,
        )
        route = RouteTelemetry(
            route_class="CLASS_2",
            trigger_id=None,
            timestamp_ms=now_ms,
        )
        snapshot = TelemetrySnapshot(
            snapshot_id=str(uuid.uuid4()),
            generated_at_ms=now_ms,
            audit_correlation_id=audit_correlation_id,
            route=route,
            class2=class2,
            audit_event_count=self._audit_reader.count() if self._audit_reader else 0,
        )
        self._publisher.publish(self._observation_topic, snapshot.to_dict(), qos=1)

    def reset(self) -> None:
        """Clear all accumulated state (useful between experiment runs)."""
        self._audit_correlation_id = ""
        self._route = None
        self._validation = None
        self._ack = None
        self._class2 = None
        self._escalation = None
