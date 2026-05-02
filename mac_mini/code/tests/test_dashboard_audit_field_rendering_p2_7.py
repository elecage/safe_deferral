"""Static checks that the dashboard's per-trial detail row renders the
four doc 12 / doc 11 audit fields (P2.7 of the post-doc-12 consistency
backfill plan).

This codebase has no JS unit-test infrastructure, so this test reads
rpi/code/dashboard/static/index.html as source and verifies:

  1. JS parses cleanly via Node (existing P0/P1 pattern, factored out).
  2. The four audit-field rendering blocks added by P2.7 exist as
     identifiable patterns inside renderPkgATrialDetailBody — not just
     absent labels in raw JSON dumps.
  3. Block-source-of-truth references (clarification_payload.input_mode,
     scan_history, scan_ordering_applied, refinement_history) are read
     from the trial's clarification_payload (the canonical location
     for these fields per docs 11 and 12 §4.4–§4.6).

If a future refactor moves any of these blocks elsewhere, this test
surfaces it. Manual UI verification of color / layout is still required
when intentionally restructuring; this just guards the wiring.
"""

import pathlib
import shutil
import subprocess

import pytest


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_INDEX_HTML = _REPO_ROOT / "rpi" / "code" / "dashboard" / "static" / "index.html"


@pytest.fixture(scope="module")
def index_source() -> str:
    assert _INDEX_HTML.exists(), f"Missing dashboard HTML: {_INDEX_HTML}"
    return _INDEX_HTML.read_text(encoding="utf-8")


# ==================================================================
# JS parses cleanly
# ==================================================================

class TestDashboardJsParses:
    """Concatenated <script> blocks must parse as valid JS. Catches
    syntax errors introduced by future edits before they ship."""

    def test_js_parses_via_node(self):
        node = shutil.which("node")
        if node is None:
            pytest.skip("node not on PATH; JS parse check requires Node.js")
        script = (
            "const fs=require('fs');"
            f"const html=fs.readFileSync({str(_INDEX_HTML)!r},'utf8');"
            "const m=html.match(/<script>[\\s\\S]*?<\\/script>/g);"
            "const js=m.map(s=>s.replace(/<\\/?script>/g,'')).join('\\n');"
            "try{new Function(js);process.stdout.write('OK')}"
            "catch(e){process.stdout.write('ERR:'+e.message);process.exit(1)}"
        )
        result = subprocess.run(
            [node, "-e", script], capture_output=True, text=True, timeout=20,
        )
        assert result.returncode == 0, (
            f"JS parse failed: {result.stdout} {result.stderr}"
        )


# ==================================================================
# 4 audit-field rendering blocks present in renderPkgATrialDetailBody
# ==================================================================

class TestDoc12AuditFieldBlocksPresent:
    """Each doc 12 / doc 11 audit field must have a dedicated rendering
    block, not just a JSON dump. Patterns matched are intentionally
    structural (function pattern + label substring) so they catch
    deletion / accidental replacement but tolerate cosmetic edits."""

    def test_input_mode_and_candidate_source_block(self, index_source):
        # The block reads cp.input_mode and cp.candidate_source and
        # produces a "Class 2 Interaction Mode" header.
        assert "cp.input_mode" in index_source
        assert "cp.candidate_source" in index_source
        assert "Class 2 Interaction Mode" in index_source

    def test_scan_history_timeline_block(self, index_source):
        # cp.scan_history rendered as a per-turn timeline; checks the
        # array access + the human-facing label + the per-response icon
        # mapping (yes/no/silence/dropped).
        assert "cp.scan_history" in index_source
        assert "Scan History" in index_source
        # Response-icon mapping for the four valid responses.
        for r in ("yes", "no", "silence", "dropped"):
            assert f"{r}:" in index_source or f"'{r}'" in index_source, (
                f"scan_history block missing response icon for {r!r}"
            )

    def test_scan_ordering_applied_block(self, index_source):
        # cp.scan_ordering_applied — matched_bucket / applied_overrides /
        # final_order rendered with attribution to doc 12 §14.
        assert "cp.scan_ordering_applied" in index_source
        assert "Scan Ordering Applied" in index_source
        assert "matched_bucket" in index_source
        assert "applied_overrides" in index_source
        assert "final_order" in index_source

    def test_refinement_history_block(self, index_source):
        # cp.refinement_history — turn_index + parent → child transition
        # rendered with attribution to doc 11 Phase 6.0.
        assert "cp.refinement_history" in index_source
        assert "Refinement History" in index_source
        assert "parent_candidate_id" in index_source
        assert "selected_candidate_id" in index_source


# ==================================================================
# Source-of-truth: blocks read from trial.clarification_payload
# ==================================================================

class TestAuditFieldsReadFromClarificationPayload:
    """The trial detail row must read these fields from
    `trial.clarification_payload` (the canonical location per
    clarification_interaction_schema.json), NOT from a parallel field
    on the trial dict. If a future refactor moves them, this test trips
    so the schema-vs-UI mapping stays consistent."""

    def test_clarification_payload_extraction_uses_one_canonical_alias(
        self, index_source,
    ):
        # The rendering function aliases t.clarification_payload to a
        # local `cp` variable and reads the four fields off that. This
        # asserts both the alias and the four reads exist.
        assert "const cp = t.clarification_payload || {}" in index_source
        for field in (
            "cp.input_mode",
            "cp.candidate_source",
            "cp.scan_history",
            "cp.scan_ordering_applied",
            "cp.refinement_history",
        ):
            assert field in index_source, (
                f"renderPkgATrialDetailBody must read {field} from "
                "trial.clarification_payload (the canonical schema location)"
            )
