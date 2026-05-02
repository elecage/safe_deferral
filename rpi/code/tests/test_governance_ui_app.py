"""Integration tests for the governance FastAPI app (RPI-10).

Exercises every endpoint of `governance.ui_app.create_governance_app`
end-to-end via FastAPI TestClient against a fresh GovernanceBackend.

Boundary check: these tests confirm the UI app stays a non-authoritative
reader. It MUST NOT publish operational control topics, modify canonical
assets, or grant approval — those constraints are documented on
ui_app.py and enforced via GovernanceBackend (which itself does no MQTT
publish, no canonical-asset writes). The endpoint surface here is
purely browsing + validation reports + draft proposals.
"""

import json

import pytest
from fastapi.testclient import TestClient

from governance.backend import GovernanceBackend, ProposalStatus
from governance.ui_app import create_governance_app


@pytest.fixture
def client():
    """Fresh backend + TestClient per test for isolation."""
    backend = GovernanceBackend()
    app = create_governance_app(backend=backend)
    return TestClient(app)


# ==================================================================
# Topic registry browsing
# ==================================================================

class TestListTopics:
    def test_returns_list(self, client):
        r = client.get("/governance/topics")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # Registry has real entries — sanity check the shape.
        assert len(data) > 0
        assert "topic" in data[0]


class TestGetTopic:
    def test_known_topic_returns_entry(self, client):
        # Pick a topic from the live registry rather than hardcoding —
        # registry is canonical and may evolve.
        topics = client.get("/governance/topics").json()
        first_topic = topics[0]["topic"]
        r = client.get(f"/governance/topics/{first_topic}")
        assert r.status_code == 200
        assert r.json()["topic"] == first_topic

    def test_unknown_topic_returns_404(self, client):
        r = client.get("/governance/topics/nonexistent_topic_does_not_exist")
        assert r.status_code == 404
        assert "not in registry" in r.json()["detail"]


# ==================================================================
# Payload validation
# ==================================================================

class TestValidatePayload:
    def test_missing_schema_name_returns_400(self, client):
        r = client.post("/governance/validate", json={"payload": {}})
        assert r.status_code == 400
        assert "schema_name" in r.json()["detail"]

    def test_missing_payload_returns_400(self, client):
        r = client.post(
            "/governance/validate",
            json={"schema_name": "candidate_action_schema.json"},
        )
        assert r.status_code == 400

    def test_valid_payload_returns_is_valid_true(self, client):
        # Use a minimal candidate_action that conforms to schema.
        body = {
            "schema_name": "candidate_action_schema.json",
            "payload": {
                "proposed_action": "light_on",
                "target_device": "living_room_light",
            },
            "example_path": "test/integration/light_on_minimal",
        }
        r = client.post("/governance/validate", json=body)
        assert r.status_code == 200
        report = r.json()
        assert report["is_valid"] is True
        assert report["errors"] == []
        assert "authority_note" in report

    def test_invalid_payload_returns_errors(self, client):
        body = {
            "schema_name": "candidate_action_schema.json",
            "payload": {"proposed_action": "doorlock_open", "target_device": "front_door"},
        }
        r = client.post("/governance/validate", json=body)
        assert r.status_code == 200
        report = r.json()
        assert report["is_valid"] is False
        assert len(report["errors"]) > 0


class TestValidationReports:
    def test_initially_empty(self, client):
        r = client.get("/governance/validation-reports")
        assert r.status_code == 200
        assert r.json() == []

    def test_records_after_validate(self, client):
        client.post("/governance/validate", json={
            "schema_name": "candidate_action_schema.json",
            "payload": {
                "proposed_action": "light_on", "target_device": "living_room_light",
            },
        })
        reports = client.get("/governance/validation-reports").json()
        assert len(reports) == 1
        assert reports[0]["is_valid"] is True

    def test_export_returns_json_string(self, client):
        client.post("/governance/validate", json={
            "schema_name": "candidate_action_schema.json",
            "payload": {
                "proposed_action": "light_on", "target_device": "living_room_light",
            },
        })
        r = client.get("/governance/validation-reports/export")
        assert r.status_code == 200
        # PlainTextResponse — body is the JSON string itself.
        parsed = json.loads(r.text)
        assert isinstance(parsed, list)
        assert len(parsed) == 1


# ==================================================================
# Proposals
# ==================================================================

class TestProposals:
    def test_initially_empty(self, client):
        r = client.get("/governance/proposals")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_requires_topic(self, client):
        r = client.post("/governance/proposals", json={"change_description": "x"})
        assert r.status_code == 400

    def test_create_returns_draft(self, client):
        r = client.post("/governance/proposals", json={
            "topic": "safe_deferral/test/topic",
            "change_description": "test draft",
        })
        assert r.status_code == 200
        p = r.json()
        assert p["topic"] == "safe_deferral/test/topic"
        assert p["status"] == "draft"
        assert "authority_note" in p
        assert "does not modify canonical assets" in p["authority_note"]

    def test_list_filters_by_status(self, client):
        client.post("/governance/proposals", json={"topic": "t/1"})
        client.post("/governance/proposals", json={"topic": "t/2"})
        # Both start as draft.
        drafts = client.get("/governance/proposals?status=draft").json()
        assert len(drafts) == 2
        proposed = client.get("/governance/proposals?status=proposed").json()
        assert proposed == []

    def test_list_invalid_status_returns_400(self, client):
        """Invalid status filter must return 400 (not propagate ValueError
        as a 500). Mirrors advance_proposal's existing 400-on-bad-status
        contract."""
        client.post("/governance/proposals", json={"topic": "t/1"})
        r = client.get("/governance/proposals?status=bogus")
        assert r.status_code == 400
        assert "Invalid status" in r.json()["detail"]


class TestAdvanceProposal:
    def test_unknown_proposal_returns_404(self, client):
        r = client.post(
            "/governance/proposals/does_not_exist/advance",
            json={"status": "proposed"},
        )
        assert r.status_code == 404

    def test_missing_status_returns_400(self, client):
        # Need a real proposal_id to reach the status check.
        created = client.post("/governance/proposals", json={"topic": "t/1"}).json()
        r = client.post(
            f"/governance/proposals/{created['proposal_id']}/advance",
            json={},
        )
        assert r.status_code == 400
        assert "status" in r.json()["detail"]

    def test_invalid_status_value_returns_400(self, client):
        created = client.post("/governance/proposals", json={"topic": "t/1"}).json()
        r = client.post(
            f"/governance/proposals/{created['proposal_id']}/advance",
            json={"status": "totally_invalid"},
        )
        assert r.status_code == 400
        assert "Invalid status" in r.json()["detail"]

    def test_advance_draft_to_proposed(self, client):
        created = client.post("/governance/proposals", json={"topic": "t/1"}).json()
        r = client.post(
            f"/governance/proposals/{created['proposal_id']}/advance",
            json={"status": "proposed", "reviewer_notes": "looks ok"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "proposed"
        assert r.json()["reviewer_notes"] == "looks ok"


class TestExportProposals:
    def test_returns_json_string_even_when_empty(self, client):
        r = client.get("/governance/proposals/export")
        assert r.status_code == 200
        parsed = json.loads(r.text)
        assert isinstance(parsed, list)
        assert parsed == []

    def test_includes_created_proposals(self, client):
        client.post("/governance/proposals", json={"topic": "t/1"})
        r = client.get("/governance/proposals/export")
        parsed = json.loads(r.text)
        assert len(parsed) == 1
        assert parsed[0]["topic"] == "t/1"


# ==================================================================
# Boundary: this app must not expose any control-publish or asset-write
# endpoint. Spot-check by enumerating the live OpenAPI surface and
# refusing surprises.
# ==================================================================

class TestNonAuthoritativeBoundary:
    """Per ui_app.py docstring: no direct file edits, no operational
    control publish, no caregiver approval spoofing. Enforced by
    construction (GovernanceBackend has no MQTT client, no asset writer).
    This test catches regressions where someone adds a route that would
    cross that line by inspecting the registered route paths."""

    def test_no_publish_or_actuation_paths(self, client):
        paths = list(client.app.openapi().get("paths", {}).keys())
        forbidden_substrings = (
            "actuation", "command", "publish",
            "policy_table", "schema_edit", "caregiver/approve",
        )
        for p in paths:
            for bad in forbidden_substrings:
                assert bad not in p, (
                    f"governance UI exposed forbidden path: {p} "
                    f"(matched substring {bad!r}) — boundary violation"
                )
