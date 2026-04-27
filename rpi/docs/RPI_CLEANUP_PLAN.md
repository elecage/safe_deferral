# RPi Cleanup Plan

## Purpose

This plan records the cleanup work required to keep the `rpi/` tree aligned with the current system structure.

The Raspberry Pi remains a non-authoritative experiment support host. It may support virtual nodes, scenario execution, monitoring, result collection, fault injection, and MQTT/payload governance support. It must not become the policy authority, validator authority, caregiver approval authority, actuator authority, or doorlock execution authority.

## Current Review Summary

- `rpi/code/` currently contains no implementation code other than `.gitkeep`.
- `rpi/scripts/` already follows the `install / configure / verify` layout.
- All current RPi shell scripts pass shell syntax checks.
- `requirements-rpi.txt` is broadly aligned with current script needs.
- Tracked `.DS_Store` files exist under `rpi/` and should be removed.
- Per-script `*_FREEZE_MANIFEST.md` files are small, repetitive, and no longer match the current documentation cleanup direction.
- `rpi/docs/README.md` does not fully reflect the current script set. In particular, it omits or under-represents `00_verify_rpi_script_syntax.sh` and `75_verify_rpi_mqtt_payload_alignment.sh`.
- Some wording still reflects older phases or naming, such as `Phase 0`, fixed synced asset counts, and old canonical asset wording.

## Cleanup Principles

- Keep `rpi/` focused on experiment support, not operational authority.
- Preserve the `install / configure / verify` structure.
- Do not add implementation code during this cleanup phase.
- Keep `rpi/code/` as the future implementation location unless a later decision removes it.
- Prefer one clear README or operation document over many small repetitive freeze manifest files.
- Avoid fixed asset counts in documentation where policy/schema/MQTT/payload asset sets may evolve.
- Keep RPi scripts aligned with `common/policies`, `common/schemas`, `common/mqtt`, and `common/payloads`.

## Planned Steps

### Step 1. Remove Non-Project Files

Remove tracked `.DS_Store` files from the RPi tree:

- `rpi/.DS_Store`
- `rpi/scripts/.DS_Store`

Confirm whether repository-level `.DS_Store` handling should be added or updated separately.

### Step 2. Consolidate Freeze Manifests

Remove the per-script `*_FREEZE_MANIFEST.md` files under:

- `rpi/scripts/install/`
- `rpi/scripts/configure/`
- `rpi/scripts/verify/`

Their useful content should be represented by `rpi/docs/README.md` or another single RPi operations document instead of many short duplicate files.

### Step 3. Update RPi README Structure

Revise `rpi/docs/README.md` so it matches the active script set:

- include `00_verify_rpi_script_syntax.sh`,
- include `75_verify_rpi_mqtt_payload_alignment.sh`,
- list the actual install/configure/verify sequence,
- describe Mac mini asset sync as current runtime/reference asset sync,
- avoid hardcoded synced asset counts,
- describe payload and MQTT reference sync alongside policy/schema mirror sync,
- keep the non-authoritative RPi boundary explicit.

### Step 4. Normalize Script Wording

Update script comments and output messages where they contain stale terminology:

- replace old phase-oriented wording when it obscures the current role,
- prefer `canonical/runtime/reference assets` over older phase labels,
- keep the Raspberry Pi role as simulation, virtual-node, fault-injection, monitoring, and verification support.

This step should not change behavior unless a wording mismatch reveals a real script bug.

### Step 5. Verify Script and Documentation Consistency

Run final checks:

- shell syntax check for all RPi scripts,
- search for removed manifest references,
- search for stale `Phase 0` or fixed asset-count wording in active RPi docs/scripts,
- `git diff --check`.

## Out of Scope

The following work is intentionally not part of this cleanup:

- implementing RPi virtual node applications,
- implementing the experiment dashboard,
- implementing scenario orchestration code,
- implementing result analysis/export tooling,
- changing canonical policy/schema/MQTT/payload assets,
- changing Mac mini operational authority behavior.

## Expected End State

After this cleanup, `rpi/` should contain:

- a clean script tree,
- no tracked OS-generated `.DS_Store` files,
- no repetitive per-script freeze manifest clutter,
- documentation that matches the actual scripts,
- clear boundaries that RPi is experiment support only,
- a preserved `rpi/code/` location for future implementation.
