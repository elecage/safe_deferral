"""MQTT/Payload Governance Backend (RPI-09).

Provides browse/validate/draft/export APIs for MQTT topic and payload governance.

Authority boundary:
  - No direct policy/schema edits.
  - No direct operational subscription mutation.
  - Governance reports are evidence artifacts — not operational authority.
  - Draft/proposed/committed distinctions must be preserved.
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import jsonschema

from shared.asset_loader import RpiAssetLoader


class ProposalStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    COMMITTED = "committed"    # requires explicit review — not auto-committed
    REJECTED = "rejected"


@dataclass
class TopicProposal:
    proposal_id: str
    topic: str
    status: ProposalStatus
    change_description: str
    proposed_at_ms: int
    reviewed_at_ms: Optional[int] = None
    reviewer_notes: str = ""

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "topic": self.topic,
            "status": self.status.value,
            "change_description": self.change_description,
            "proposed_at_ms": self.proposed_at_ms,
            "reviewed_at_ms": self.reviewed_at_ms,
            "reviewer_notes": self.reviewer_notes,
            "authority_note": (
                "This proposal is a draft/governance artifact. "
                "It does not modify canonical assets or grant operational authority."
            ),
        }


@dataclass
class ValidationReport:
    report_id: str
    schema_name: str
    payload_example_path: str
    is_valid: bool
    errors: list[str]
    generated_at_ms: int
    authority_note: str = (
        "Validation reports are evidence artifacts. "
        "They do not authorize actuation or override policy."
    )

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "schema_name": self.schema_name,
            "payload_example_path": self.payload_example_path,
            "is_valid": self.is_valid,
            "errors": self.errors,
            "generated_at_ms": self.generated_at_ms,
            "authority_note": self.authority_note,
        }


class GovernanceBackend:
    """MQTT/Payload governance backend.

    Usage:
        backend = GovernanceBackend()
        topics = backend.list_topics()
        report = backend.validate_payload_example("class2_notification_payload_schema.json",
                                                   payload_dict)
        proposal = backend.create_proposal("safe_deferral/context/input", "Add field X")
    """

    def __init__(self, asset_loader: Optional[RpiAssetLoader] = None) -> None:
        self._loader = asset_loader or RpiAssetLoader()
        self._proposals: dict[str, TopicProposal] = {}
        self._reports: list[ValidationReport] = []

    # ------------------------------------------------------------------
    # Topic registry browsing
    # ------------------------------------------------------------------

    def list_topics(self) -> list[dict]:
        registry = self._loader.load_topic_registry()
        return [
            {
                "topic": t["topic"],
                "description": t.get("description", ""),
                "authority_level": t.get("authority_level", ""),
                "payload_family": t.get("payload_family"),
                "schema": t.get("schema"),
                "audit_recommended": t.get("audit_recommended", False),
            }
            for t in registry.get("topics", [])
        ]

    def get_topic(self, topic: str) -> Optional[dict]:
        registry = self._loader.load_topic_registry()
        for t in registry.get("topics", []):
            if t["topic"] == topic:
                return t
        return None

    # ------------------------------------------------------------------
    # Payload validation
    # ------------------------------------------------------------------

    def validate_payload_example(
        self,
        schema_name: str,
        payload: dict,
        example_path: str = "",
    ) -> ValidationReport:
        """Validate a payload dict against a named schema."""
        try:
            schema = self._loader.load_schema(schema_name)
        except FileNotFoundError:
            report = ValidationReport(
                report_id=str(uuid.uuid4()),
                schema_name=schema_name,
                payload_example_path=example_path,
                is_valid=False,
                errors=[f"Schema not found: {schema_name}"],
                generated_at_ms=int(time.time() * 1000),
            )
            self._reports.append(report)
            return report

        errors = []
        try:
            validator = jsonschema.Draft7Validator(schema)
            for err in validator.iter_errors(payload):
                errors.append(err.message)
        except Exception as exc:
            errors.append(str(exc))

        report = ValidationReport(
            report_id=str(uuid.uuid4()),
            schema_name=schema_name,
            payload_example_path=example_path,
            is_valid=len(errors) == 0,
            errors=errors,
            generated_at_ms=int(time.time() * 1000),
        )
        self._reports.append(report)
        return report

    def get_validation_reports(self) -> list[ValidationReport]:
        return list(self._reports)

    def export_validation_report(self) -> str:
        return json.dumps([r.to_dict() for r in self._reports], indent=2)

    # ------------------------------------------------------------------
    # Proposals
    # ------------------------------------------------------------------

    def create_proposal(
        self,
        topic: str,
        change_description: str,
        proposal_id: Optional[str] = None,
    ) -> TopicProposal:
        pid = proposal_id or str(uuid.uuid4())
        proposal = TopicProposal(
            proposal_id=pid,
            topic=topic,
            status=ProposalStatus.DRAFT,
            change_description=change_description,
            proposed_at_ms=int(time.time() * 1000),
        )
        self._proposals[pid] = proposal
        return proposal

    def advance_proposal(
        self,
        proposal_id: str,
        new_status: ProposalStatus,
        reviewer_notes: str = "",
    ) -> TopicProposal:
        """Advance a proposal status. COMMITTED requires explicit reviewer action."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            raise KeyError(f"Proposal {proposal_id} not found")
        proposal.status = new_status
        proposal.reviewed_at_ms = int(time.time() * 1000)
        proposal.reviewer_notes = reviewer_notes
        return proposal

    def list_proposals(
        self, status_filter: Optional[ProposalStatus] = None
    ) -> list[TopicProposal]:
        proposals = list(self._proposals.values())
        if status_filter:
            proposals = [p for p in proposals if p.status == status_filter]
        return proposals

    def export_proposals_report(self) -> str:
        return json.dumps(
            [p.to_dict() for p in self._proposals.values()], indent=2
        )
