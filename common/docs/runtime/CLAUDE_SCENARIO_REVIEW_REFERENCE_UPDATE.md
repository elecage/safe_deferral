# CLAUDE_SCENARIO_REVIEW_REFERENCE_UPDATE.md

## Purpose

This note records the required `CLAUDE.md` reference update after the scenario review guide split introduced by PR #12.

It exists because `CLAUDE.md` is long and should not be rewritten through a truncated connector response. The actual `CLAUDE.md` edit should be performed with a safe full-file editing method.

Related issue:

```text
https://github.com/elecage/safe_deferral/issues/13
```

---

## Required instruction change

Future agents and developers should prefer the split scenario review guide index:

```text
integration/scenarios/docs/README.md
```

and then the topic-specific split docs:

```text
integration/scenarios/docs/scenario_review_principles.md
integration/scenarios/docs/scenario_review_class0_class1.md
integration/scenarios/docs/scenario_review_class2.md
integration/scenarios/docs/scenario_review_faults.md
```

The older monolithic guide remains retained only for compatibility:

```text
integration/scenarios/scenario_review_guide.md
```

Do not treat the older monolithic guide as the primary scenario review source when it conflicts with the split docs or the latest `SESSION_HANDOFF` addenda.

---

## Exact `CLAUDE.md` update required

### 1. Update the optional follow-up list under “반드시 먼저 읽을 문서 순서”

Replace or expand the current scenario review guide reference so that the split docs are preferred:

```text
- /integration/scenarios/scenario_manifest_rules.md
- /integration/scenarios/docs/README.md
- /integration/scenarios/docs/scenario_review_principles.md
- /integration/scenarios/docs/scenario_review_class0_class1.md
- /integration/scenarios/docs/scenario_review_class2.md
- /integration/scenarios/docs/scenario_review_faults.md
- /integration/scenarios/scenario_review_guide.md  # retained legacy compatibility reference only
```

### 2. Update the “시나리오 / integration 문서” section

Use this ordering:

```text
* /integration/README.md
* /integration/requirements.md
* /integration/scenarios/README.md
* /integration/scenarios/scenario_manifest_rules.md
* /integration/scenarios/docs/README.md
* /integration/scenarios/docs/scenario_review_principles.md
* /integration/scenarios/docs/scenario_review_class0_class1.md
* /integration/scenarios/docs/scenario_review_class2.md
* /integration/scenarios/docs/scenario_review_faults.md
* /integration/scenarios/scenario_review_guide.md  # retained legacy compatibility reference only
* /integration/measurement/class_wise_latency_profiles.md
* /integration/tests/integration_test_runner_skeleton.py
* /integration/tests/expected_outcome_comparator.py
```

### 3. Add a scenario review guide note

Add near the integration/scenario reference section:

```markdown
### Scenario review guide note

`integration/scenarios/scenario_review_guide.md` is retained for compatibility, but new scenario review work should prefer the split guide index:

- `integration/scenarios/docs/README.md`

and then the topic-specific split docs:

- `integration/scenarios/docs/scenario_review_principles.md`
- `integration/scenarios/docs/scenario_review_class0_class1.md`
- `integration/scenarios/docs/scenario_review_class2.md`
- `integration/scenarios/docs/scenario_review_faults.md`

Do not treat the older monolithic guide as the primary source when it conflicts with the split docs or the latest `SESSION_HANDOFF` addenda.
```

---

## Current scenario review baseline

As of the PR #12 merge, scenario review should use:

```text
safe_deferral/clarification/interaction = dedicated Class 2 clarification interaction evidence topic
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json = current Class 2 clarification interaction schema
common/payloads/examples/clarification_interaction_two_options_pending.json = representative Class 2 clarification example payload
integration/scenarios/docs/ = preferred split scenario review guide location
integration/scenarios/scenario_review_guide.md = retained legacy compatibility reference only
```

---

## Safety note for editing `CLAUDE.md`

Do not update `CLAUDE.md` from a truncated connector response.

Safe options:

```text
1. Clone locally, edit with git, run diff, push branch.
2. Use a GitHub editor session that preserves the whole file.
3. Use an API workflow that fetches the complete raw file and verifies the full replacement diff before committing.
```

After the actual `CLAUDE.md` edit is merged, this helper note can remain as a trace record or be superseded by a later cleanup PR.
