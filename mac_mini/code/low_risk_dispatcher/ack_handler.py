"""ACK Handler (MM-07).

Resolves closed-loop ACK evidence for dispatched actuation commands.

Two paths:
  handle_ack(record, ack_payload) — called when an ACK arrives on
      safe_deferral/actuation/ack.  Validates command_id match, writes
      ack_status into the DispatchRecord, returns AckResult.

  handle_ack_timeout(record, timestamp_ms) — called by the caller's timer
      when no ACK has arrived within ack_timeout_ms.  Always produces
      AckStatus.TIMEOUT.

Authority rule: ACK is closed-loop evidence only.  It does not constitute
policy approval, caregiver confirmation, or validator authority.
"""

import time
from typing import Optional

from low_risk_dispatcher.models import AckResult, AckStatus, DispatchRecord, DispatchStatus

# Maps action name to the observed_state value that constitutes closed-loop success.
# Only canonical Class 1 actions are listed; unlisted actions skip the state check.
_EXPECTED_OBSERVED_STATE: dict = {
    "light_on": "on",
    "light_off": "off",
}


class AckHandler:

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_ack(
        self,
        record: DispatchRecord,
        ack_payload: dict,
        timestamp_ms: Optional[int] = None,
    ) -> AckResult:
        """Process an incoming ACK payload.

        For success, the ACK must pass four checks in order:
          1. command_id matches the dispatched record.
          2. target_device matches the dispatched record.
          3. audit_correlation_id matches when the ACK includes a non-empty value.
          4. observed_state matches the expected post-action state for known actions.
        Any mismatch produces AckStatus.FAILURE regardless of ack_status.
        """
        ts = timestamp_ms or int(time.time() * 1000)

        if ack_payload.get("command_id", "") != record.command_id:
            return self._resolve(record, AckStatus.FAILURE, ts, observed_state=None)

        if ack_payload.get("target_device", "") != record.target_device:
            return self._resolve(record, AckStatus.FAILURE, ts, observed_state=None)

        ack_audit_id = ack_payload.get("audit_correlation_id", "")
        if ack_audit_id and ack_audit_id != record.audit_correlation_id:
            return self._resolve(record, AckStatus.FAILURE, ts, observed_state=None)

        raw_status = ack_payload.get("ack_status", "")
        observed_state = ack_payload.get("observed_state")

        if raw_status == "success":
            expected = _EXPECTED_OBSERVED_STATE.get(record.action)
            if expected is not None and observed_state != expected:
                return self._resolve(record, AckStatus.FAILURE, ts, observed_state)

        ack_status = AckStatus.SUCCESS if raw_status == "success" else AckStatus.FAILURE
        return self._resolve(record, ack_status, ts, observed_state)

    def handle_ack_timeout(
        self,
        record: DispatchRecord,
        timestamp_ms: Optional[int] = None,
    ) -> AckResult:
        """Mark the dispatch as timed-out; no ACK arrived within the window."""
        ts = timestamp_ms or int(time.time() * 1000)
        return self._resolve(record, AckStatus.TIMEOUT, ts, observed_state=None)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve(
        record: DispatchRecord,
        ack_status: AckStatus,
        ts: int,
        observed_state: Optional[str],
    ) -> AckResult:
        record.ack_status = ack_status
        record.ack_received_at_ms = ts
        record.observed_state = observed_state
        record.dispatch_status = (
            DispatchStatus.ACK_SUCCESS
            if ack_status == AckStatus.SUCCESS
            else (
                DispatchStatus.ACK_FAILURE
                if ack_status == AckStatus.FAILURE
                else DispatchStatus.ACK_TIMEOUT
            )
        )
        return AckResult(
            command_id=record.command_id,
            ack_status=ack_status,
            audit_correlation_id=record.audit_correlation_id,
            observed_state=observed_state,
            resolved_at_ms=ts,
            dispatch_record=record,
        )
