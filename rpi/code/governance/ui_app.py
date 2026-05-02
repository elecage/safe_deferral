"""MQTT/Payload Governance UI (RPI-10).

FastAPI application that exposes governance browsing and validation
through backend APIs.

Authority boundary:
  - No direct file writes to canonical assets.
  - No direct operational control publish.
  - No caregiver approval spoofing.
  - No dashboard control authority.
  - All validation and export via GovernanceBackend.
"""

from typing import Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse, PlainTextResponse
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from governance.backend import GovernanceBackend, ProposalStatus


def create_governance_app(
    backend: Optional[GovernanceBackend] = None,
) -> "FastAPI":
    if not _FASTAPI_AVAILABLE:
        raise ImportError("fastapi is required for the governance UI app")

    app = FastAPI(
        title="safe_deferral Governance UI",
        description=(
            "Non-authoritative MQTT/payload governance browsing and validation. "
            "No direct file edits, no operational control publish."
        ),
        version="1.0.0",
    )

    _backend = backend or GovernanceBackend()

    # ------------------------------------------------------------------
    # Topic registry browsing
    # ------------------------------------------------------------------

    @app.get("/governance/topics", summary="Browse all registry topics")
    def list_topics():
        return _backend.list_topics()

    @app.get("/governance/topics/{topic:path}", summary="Get a specific topic entry")
    def get_topic(topic: str):
        entry = _backend.get_topic(topic)
        if entry is None:
            raise HTTPException(status_code=404, detail=f"Topic '{topic}' not in registry")
        return entry

    # ------------------------------------------------------------------
    # Payload validation
    # ------------------------------------------------------------------

    @app.post("/governance/validate", summary="Validate a payload against a schema")
    def validate_payload(body: dict):
        schema_name = body.get("schema_name")
        payload = body.get("payload")
        example_path = body.get("example_path", "")
        if not schema_name or payload is None:
            raise HTTPException(
                status_code=400,
                detail="Required fields: schema_name (str), payload (dict)",
            )
        report = _backend.validate_payload_example(schema_name, payload, example_path)
        return report.to_dict()

    @app.get("/governance/validation-reports",
             summary="Get all validation reports")
    def get_reports():
        return [r.to_dict() for r in _backend.get_validation_reports()]

    @app.get("/governance/validation-reports/export",
             summary="Export validation reports as JSON",
             response_class=PlainTextResponse)
    def export_reports():
        return _backend.export_validation_report()

    # ------------------------------------------------------------------
    # Proposals
    # ------------------------------------------------------------------

    @app.get("/governance/proposals", summary="List topic proposals")
    def list_proposals(status: Optional[str] = None):
        if status:
            try:
                sf = ProposalStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid status: {status}"
                )
        else:
            sf = None
        return [p.to_dict() for p in _backend.list_proposals(status_filter=sf)]

    @app.post("/governance/proposals", summary="Create a draft proposal")
    def create_proposal(body: dict):
        topic = body.get("topic")
        desc = body.get("change_description", "")
        if not topic:
            raise HTTPException(status_code=400, detail="Required: topic (str)")
        proposal = _backend.create_proposal(topic, desc)
        return proposal.to_dict()

    @app.post("/governance/proposals/{proposal_id}/advance",
              summary="Advance a proposal status (draft→proposed→committed/rejected)")
    def advance_proposal(proposal_id: str, body: dict):
        new_status_str = body.get("status")
        notes = body.get("reviewer_notes", "")
        if not new_status_str:
            raise HTTPException(status_code=400, detail="Required: status (str)")
        try:
            new_status = ProposalStatus(new_status_str)
        except ValueError:
            raise HTTPException(status_code=400,
                                detail=f"Invalid status: {new_status_str}")
        try:
            proposal = _backend.advance_proposal(proposal_id, new_status, notes)
        except KeyError:
            raise HTTPException(status_code=404,
                                detail=f"Proposal {proposal_id} not found")
        return proposal.to_dict()

    @app.get("/governance/proposals/export",
             summary="Export all proposals as JSON",
             response_class=PlainTextResponse)
    def export_proposals():
        return _backend.export_proposals_report()

    return app
