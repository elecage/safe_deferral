# SESSION_HANDOFF_2026-04-24_PROMPT_REFACTOR_AND_EVAL_UPDATE.md

## Purpose

This addendum records repository-level updates made after the main `SESSION_HANDOFF.md` had already grown large enough to become difficult to review and update safely through connector-based editing.

It should be read together with:
- `common/docs/runtime/SESSION_HANDOFF.md`

---

## 1. Prompt document refactor completed

The original prompt document was split for maintainability.

### New structure
- `common/docs/architecture/12_prompts.md`
  - now serves as an index file
- `common/docs/architecture/12_prompts_core_system.md`
  - hub/backend/runtime/system-generation prompt set
- `common/docs/architecture/12_prompts_nodes_and_evaluation.md`
  - ESP32/STM32/node/evaluation/paper-oriented prompt set

### Reason for the split
The original prompt document had become too long to:
- review comfortably,
- verify trailing additions safely,
- and maintain reliably when adding new paper-oriented evaluation prompts.

The split preserves prompt numbering while improving edit safety and future discoverability.

---

## 2. Prompt index restored

`common/docs/architecture/12_prompts.md` had been removed during the split process and was later restored as an index file.

The intended role of the file is now:
- lightweight entry point
- pointer to the two split prompt documents
- explanation of numbering continuity

This means future sessions should not treat `12_prompts.md` as the full prompt body.

---

## 3. Contribution-1-supporting evaluation prompts added

To better support the paper’s Contribution 1
(**LLM-assisted intent recovery for constrained alternative input**),
additional prompts were added into the node/evaluation prompt document.

### Added prompts
- `Prompt 29. Implement Intent Recovery Comparison Baseline Runner`
- `Prompt 30. Generate Constrained-Input Intent Recovery Scenario Set`
- `Prompt 32. Implement Sensitive Actuation Visitor-Response Evaluation Flow`

### Intention
These prompts were added because the repository previously had:
- safety/routing/fault-injection prompts,
- node firmware prompts,
- and evaluation-support prompts,

but it did not yet explicitly include generation guidance for:
- constrained-input intent recovery comparison,
- direct-mapping vs rule-only vs LLM-assisted baseline comparison,
- or visitor-response / sensitive-actuation evaluation flows tied to the paper contribution framing.

---

## 4. Formatting issue fixed in nodes/evaluation prompt document

During manual edits, the tail section of `12_prompts_nodes_and_evaluation.md` temporarily developed malformed markdown/code-fence structure around Prompts 29/30/32.

This has been repaired.

Future sessions should assume:
- the split structure is canonical,
- the prompt index file is restored,
- and Prompts 29/30/32 are now part of the maintained prompt set.

---

## 5. Relation to experiment documentation

These prompt additions were made to align with the updated experiment baseline document:
- `common/docs/required_experiments.md`

In particular, they support the newly added evaluation framing for:
- intent recovery comparison under constrained input,
- non-LLM baselines,
- and visitor-response / sensitive-actuation safety evaluation.

They also align with:
- `common/docs/paper/01_paper_contributions.md`

---

## 6. Practical interpretation for future sessions

Future sessions should assume the following:

1. The prompt architecture is now split and should remain split unless there is a deliberate repository-wide restructuring.
2. `12_prompts_core_system.md` should be used for backend/runtime/system generation.
3. `12_prompts_nodes_and_evaluation.md` should be used for:
   - ESP32 node firmware,
   - STM32 measurement support,
   - experiment-readiness support,
   - constrained-input evaluation,
   - and doorlock/visitor-response sensitive-actuation evaluation.
4. Contribution 1 now has explicit prompt-level support in addition to experiment-document support.
5. Prompt numbering continuity is preserved intentionally; Prompt 31 remains available for later addition if needed.

---

## 7. Recommendation about the handoff document itself

The main `SESSION_HANDOFF.md` has become large enough that future maintenance may be safer if the runtime handoff documentation is split into:

- a stable long-form master handoff, and
- dated or topic-specific handoff addenda.

Suggested future direction:
- keep `SESSION_HANDOFF.md` as the master summary,
- add lightweight dated companion files for major milestone updates,
- optionally create separate handoff notes for:
  - runtime/deployment state,
  - paper/contribution state,
  - prompt/document refactor state.

This addendum is the first example of that safer pattern.
