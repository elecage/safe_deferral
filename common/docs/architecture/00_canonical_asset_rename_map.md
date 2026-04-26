# Canonical Asset Rename Map

## 1. Purpose

This document is the execution map for removing version strings and `FROZEN`
labels from active policy, schema, MQTT, and scenario references.

It supports the broader cleanup plan in:

```text
common/docs/architecture/00_documentation_and_asset_restructure_plan.md
```

This document fixes the target names before any broad rename is performed.

---

## 2. Naming Decision

Active canonical files should have stable descriptive names.

Do not encode these in active filenames:

- semantic version strings,
- `FROZEN`,
- temporary phase labels,
- superseded baseline labels.

Historical version information should be represented through:

- git history,
- `common/asset_manifest.json`,
- `common/history/`,
- runtime handoff records,
- or explicit changelog text.

Selected archive root:

```text
common/history/
```

Rationale:

- `history` is clearer than `archive` for old policy/schema/MQTT assets,
- history files should keep the same descriptive canonical basename as the
  active file where practical,
- `common/docs/archive/` can still be used for legacy prose documents,
- `common/docs/runtime/` remains session history and may keep old filenames.

---

## 3. Active Canonical Asset Targets

Important content-source rule:

- `policy_table.json` should be created from the current active policy content
  in `policy_table_v1_2_0_FROZEN.json`, not from the older
  `policy_table_v1_1_2_FROZEN.json`.
- `topic_registry.json` should be created from the current active registry
  content in `topic_registry_v1_1_0.json`, not from the older
  `topic_registry_v1_0_0.json`.
- The target filenames intentionally drop version and `FROZEN` markers. The
  source version remains documented here and in `common/asset_manifest.json`.

### 3.1 Policy assets

| Asset role | Current file | Target active file | Action |
|---|---|---|---|
| Routing policy | `common/policies/policy_table_v1_2_0_FROZEN.json` | `common/policies/policy_table.json` | Rename to active canonical |
| Low-risk action catalog | `common/policies/low_risk_actions_v1_1_0_FROZEN.json` | `common/policies/low_risk_actions.json` | Rename to active canonical |
| Fault injection rules | `common/policies/fault_injection_rules_v1_4_0_FROZEN.json` | `common/policies/fault_injection_rules.json` | Rename to active canonical |
| Output profile | `common/policies/output_profile_v1_1_0.json` | `common/policies/output_profile.json` | Rename to active canonical |

### 3.2 Schema assets

| Asset role | Current file | Target active file | Action |
|---|---|---|---|
| Policy Router input schema | `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json` | `common/schemas/policy_router_input_schema.json` | Rename to active canonical |
| Context schema | `common/schemas/context_schema_v1_0_0_FROZEN.json` | `common/schemas/context_schema.json` | Rename to active canonical |
| Candidate action schema | `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json` | `common/schemas/candidate_action_schema.json` | Rename to active canonical |
| Validator output schema | `common/schemas/validator_output_schema_v1_1_0_FROZEN.json` | `common/schemas/validator_output_schema.json` | Rename to active canonical |
| Class 2 notification schema | `common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json` | `common/schemas/class2_notification_payload_schema.json` | Rename to active canonical |
| Clarification interaction schema | `common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json` | `common/schemas/clarification_interaction_schema.json` | Rename to active canonical |

### 3.3 MQTT assets

| Asset role | Current file | Target active file | Action |
|---|---|---|---|
| Topic registry | `common/mqtt/topic_registry_v1_1_0.json` | `common/mqtt/topic_registry.json` | Rename to active canonical |
| Publisher/subscriber matrix | `common/mqtt/publisher_subscriber_matrix_v1_0_0.md` | `common/mqtt/publisher_subscriber_matrix.md` | Rename to active canonical |
| Topic-payload contracts | `common/mqtt/topic_payload_contracts_v1_0_0.md` | `common/mqtt/topic_payload_contracts.md` | Rename to active canonical |

---

## 4. Historical Asset Targets

### 4.1 Policy history

| Current file | Target history file | Reason |
|---|---|---|
| `common/policies/policy_table_v1_1_2_FROZEN.json` | `common/history/policies/policy_table.json` | Superseded by current Class 2 clarification baseline |

### 4.2 Schema history

| Current file | Target history file | Reason |
|---|---|---|
| `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json` | `common/history/schemas/class2_notification_payload_schema.json` | Superseded by current Class 2 notification payload schema |

### 4.3 MQTT history

| Current file | Target history file | Reason |
|---|---|---|
| `common/mqtt/topic_registry_v1_0_0.json` | `common/history/mqtt/topic_registry.json` | Superseded by current topic registry with role metadata and Class 2 clarification topic |

---

## 5. References To Update

The rename must update all active references in the following areas.

### 5.1 Root guidance

```text
README.md
CLAUDE.md
```

`CLAUDE.md` should be simplified rather than only mechanically updated.

### 5.2 Active architecture documents

```text
common/docs/architecture/
```

Current legacy `01` through `20` documents should either:

- be consolidated into the new active document set,
- receive superseded notices,
- or move to `common/docs/archive/architecture_legacy/`.

During the transition, active canonical docs must use the new names.

### 5.3 MQTT and payload references

```text
common/mqtt/README.md
common/payloads/README.md
common/payloads/examples/*.json
common/payloads/templates/*.json
```

### 5.4 Policy-internal and schema-reference fields

Some policy JSON files contain embedded references to other policy, schema, and
MQTT assets.

These embedded references must be updated after renaming.

Known examples:

```text
common/policies/policy_table.json
common/policies/fault_injection_rules.json
common/policies/output_profile.json
```

### 5.5 Scenario contract layer

```text
integration/scenarios/*.json
integration/scenarios/*.md
integration/scenarios/docs/*.md
integration/scenarios/scenario_manifest_schema.json
```

Scenario JSON files are active contract assets and should reference canonical
asset names.

### 5.6 Integration data and remaining non-Python assets

Even though Python files have been removed, JSON/Markdown data under
`integration/` may still reference old names.

Known active or semi-active areas:

```text
integration/README.md
integration/requirements.md
integration/tests/data/*.json
integration/measurement/*.md
```

### 5.7 Device and script documentation

Scripts and device README files currently reference old names.

These should be updated when asset files are renamed:

```text
mac_mini/scripts/
mac_mini/docs/
rpi/scripts/
rpi/docs/
esp32/docs/
```

If a script becomes obsolete during the cleanup, prefer updating its documented
asset references or marking it as legacy rather than leaving it pointed at old
active filenames.

---

## 6. Current Reference Risk Summary

The current repository still has broad references to versioned names in:

- root docs,
- active architecture docs,
- scenario contracts,
- payload README and examples,
- Mac mini scripts,
- Raspberry Pi scripts,
- integration README/requirements,
- runtime handoff history.

Runtime handoff history can keep old names.

Active docs, scenario JSON, scripts, and payload references should migrate.

---

## 7. Migration Order

### Step 1. Prepare directories

Create:

```text
common/history/policies/
common/history/schemas/
common/history/mqtt/
```

### Step 2. Rename active assets

Use `git mv` for active policy, schema, and MQTT files.

Canonical source files:

```text
common/policies/policy_table_v1_2_0_FROZEN.json
→ common/policies/policy_table.json

common/mqtt/topic_registry_v1_1_0.json
→ common/mqtt/topic_registry.json
```

The older `policy_table_v1_1_2_FROZEN.json` and
`topic_registry_v1_0_0.json` are historical inputs only.

### Step 3. Move historical assets

Use `git mv` for superseded policy/schema/MQTT files into `common/history/`.

### Step 4. Add asset manifest

Add:

```text
common/asset_manifest.json
```

The manifest should list:

- current canonical assets,
- historical assets,
- source version / former path metadata for historical assets,
- old-to-new path mappings,
- paths excluded from active-reference validation.

### Step 5. Update embedded JSON references

Update path references inside:

```text
common/policies/*.json
common/mqtt/*.json
common/payloads/**/*.json
integration/scenarios/**/*.json
integration/tests/data/*.json
```

### Step 6. Update Markdown and shell references

Update active Markdown and shell references.

Historical exceptions:

```text
common/docs/runtime/
common/docs/archive/
common/history/
```

### Step 7. Simplify `CLAUDE.md`

Do not preserve every old file list. Replace it with the new canonical read
order and concise non-negotiable boundaries.

---

## 8. Active Reference Validation Rule

After migration, active paths should not contain these patterns:

```text
_FROZEN
_v1_
topic_registry_v1_
policy_table_v1_
low_risk_actions_v1_
fault_injection_rules_v1_
output_profile_v1_
schema_v1_
publisher_subscriber_matrix_v1_
topic_payload_contracts_v1_
```

Allowed exception paths:

```text
common/history/
common/docs/runtime/
common/docs/archive/
```

Temporary exception:

```text
common/docs/architecture/00_documentation_and_asset_restructure_plan.md
common/docs/architecture/00_canonical_asset_rename_map.md
```

These planning documents may mention old names while the migration is in
progress.

---

## 9. First Migration Batch Recommendation

The first actual migration batch should be limited to:

1. create `common/history/` directories,
2. rename policy/schema/MQTT assets,
3. add `common/asset_manifest.json`,
4. update references inside `common/policies/`, `common/mqtt/`, and
   `common/payloads/`,
5. update `integration/scenarios/` JSON references.

Do not consolidate all architecture prose in the same batch. Keep prose
consolidation as a separate batch so review remains possible.
