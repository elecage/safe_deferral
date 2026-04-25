# SESSION_HANDOFF_2026-04-25_OV_PHASE2_BACKGROUND_RETRY_STATUS.md

Date: 2026-04-25
Scope: OV Phase 2 background creation/retry status and next-session handoff
Status: Handoff recorded. Next session should resume from Phase OV-2.

## 1. Purpose

This addendum records the current state of Operational View (OV) figure work after Phase OV-1 scaffold creation and the initial Phase OV-2 background attempts.

Important handoff instruction:

```text
Next session should resume from Phase OV-2: Canonical Korean apartment background creation / approval.
```

Do not proceed to scenario overlays until the canonical background is approved.

---

## 2. Completed before this handoff

### 2.1 Phase OV-0 plan recorded

Recorded in:

```text
common/docs/runtime/SESSION_HANDOFF_2026-04-25_OV_FIGURE_DEVELOPMENT_PLAN.md
```

### 2.2 Phase OV-1 scaffold completed

Recorded in:

```text
common/docs/runtime/SESSION_HANDOFF_2026-04-25_OV_PHASE1_SCAFFOLD_UPDATE.md
```

Created scaffold/spec files:

```text
common/docs/architecture/figures/OV/README.md
common/docs/architecture/figures/OV/specs/ov_style_guide.md
common/docs/architecture/figures/OV/specs/ov_generation_prompt_template.md
common/docs/architecture/figures/OV/specs/ov_node_coordinate_map.json
common/docs/architecture/figures/OV/specs/ov_scenario_figure_manifest.json
common/docs/architecture/figures/OV/specs/ov_color_symbol_legend.md
```

---

## 3. Phase OV-2 current status

Phase OV-2 goal:

```text
Create and approve the canonical Korean apartment background for all OV figures.
```

Expected final Phase OV-2 outputs:

```text
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.png
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.metadata.json
```

Optional editable/vector base:

```text
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.svg
```

Current state:

```text
- Phase OV-2 is not complete.
- A hand-authored SVG base was created but rejected by the user as not sufficiently apartment-like.
- Image-generation attempts produced more realistic apartment layouts, but the generated background still needs correction before being accepted as canonical.
- No generated image has been approved as the final canonical OV background.
```

---

## 4. Created but rejected / not approved asset

Created:

```text
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.svg
```

Commit:

```text
902ef27f8cab4a22a91043e74fb1fb46e5fefac4
```

Reason this SVG must not be treated as canonical:

```text
The user stated that the SVG does not sufficiently represent an apartment shape and cannot be used as the actual canonical background.
```

Action for next session:

```text
Do not use ov_base_korean_apartment_v1.svg as the approved canonical background unless it is explicitly replaced or substantially revised.
```

Recommended handling:

```text
- Either delete it in a later cleanup pass, or
- keep it only as a rejected draft/reference, clearly marked as non-canonical.
```

---

## 5. Image-generation attempts and user feedback

### 5.1 First image-generation attempt

A generated top-down/isometric Korean apartment-like image was produced and looked more realistic than the hand-authored SVG.

However, it had embedded labels/metadata-like text or visual elements that violated the OV base-background rule.

Decision:

```text
Do not save the first generated image as canonical.
```

### 5.2 Second image-generation attempt

A second more realistic apartment image was generated after asking for a text-free apartment-like layout.

User feedback on the second image:

```text
- Bathroom access is wrong: the bathroom door appears connected to the outer vestibule/전실 instead of the living room/common interior.
- The bathroom should connect to the living room/common indoor area.
- The empty space between the two lower rooms is unrealistic and should not be designed that way.
- The two lower-room doors are not drawn with proper hinge/door geometry.
- The lower-left bedroom appears to have two doors, which is unrealistic and should be corrected.
```

Interpretation:

```text
The user prefers the realistic generated apartment style, but the layout must be architecturally plausible before being accepted as the canonical OV background.
```

---

## 6. Required corrections for the next Phase OV-2 attempt

The next canonical background attempt must satisfy these user requirements:

```text
1. Korean apartment-like realistic or high-quality isometric indoor layout.
2. No embedded text labels, no metadata panels, no node names baked into the image.
3. Bathroom door must connect to the living room/common interior area, not only to an outer vestibule/전실.
4. Remove unrealistic empty void between the two lower rooms.
5. Lower rooms must have normal single-entry doors unless a clear architectural reason exists.
6. The lower-left room must not appear to have two doors.
7. Room doors should have plausible hinge/swing geometry.
8. Layout should remain suitable for fixed node overlays and scenario arrows.
9. Background should not emphasize doorlock or imply door-unlock authority.
10. Background should remain low visual noise and reusable across all scenarios.
```

Recommended additional constraints:

```text
- one main entrance;
- one living room connected to kitchen/dining;
- at least two bedrooms, preferably three if space permits;
- one bathroom accessible from the common living/hallway area;
- balcony/veranda visible;
- clear wall/ceiling locations for sensor nodes;
- empty right-side or edge space for later overlay panels is helpful but should not appear as a strange room void.
```

---

## 7. Recommended next prompt for image generation

Use a prompt like the following in the next session:

```text
Create a clean, realistic, top-down isometric 3D rendering of a modern Korean apartment interior for a technical operational-view background. The apartment should have one main entrance, a living room connected to kitchen/dining, three bedrooms, one bathroom connected to the common living/hallway area, and a balcony/veranda. The bathroom door must open to the common interior hallway/living area, not to an outside vestibule. The two lower bedrooms must be separated by a normal wall, with no unrealistic empty void between them. Each bedroom should have a single plausible hinged door with correct door-swing geometry; the lower-left bedroom must not have two doors. Use warm neutral colors, light wood floors, clean walls, realistic furniture, and low visual clutter. Include no text labels, no UI panels, no metadata, no arrows, no node names, no scenario event icons, and no people. Leave enough clean wall/ceiling space for later IoT node overlays. Do not emphasize door locks. 16:9 canvas, high-resolution, academic technical figure style.
```

Negative prompt:

```text
No text, no labels, no metadata panels, no UI panels, no arrows, no people, no duplicated doors, no impossible room voids, no bathroom connected only to an exterior vestibule, no two doors into the lower-left bedroom, no distorted doors, no unrealistic hinges, no clutter, no dramatic lighting, no doorlock emphasis.
```

---

## 8. Recommended Phase OV-2 workflow for next session

1. Generate a corrected apartment background image using the prompt above.
2. Review the generated image against the correction checklist.
3. If the layout is still wrong, do not save it as canonical; generate again or manually revise the prompt.
4. Once approved by the user, save the approved image as:

```text
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.png
```

5. Create metadata:

```text
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.metadata.json
```

6. Update:

```text
common/docs/architecture/figures/OV/README.md
common/docs/runtime/SESSION_HANDOFF.md
```

7. Create a Phase OV-2 completion handoff addendum.

---

## 9. Important boundary for next session

Do not proceed to Phase OV-3 node-position overlay until the user approves the canonical apartment background.

Reason:

```text
All OV scenario overlays depend on stable room geometry and fixed node coordinates.
```

---

## 10. Next-session starting point

Start next session with:

```text
Phase OV-2 — Canonical Korean apartment background creation / approval
```

Begin by acknowledging:

```text
The previous hand-authored SVG was rejected as not apartment-like enough. The user prefers the realistic generated apartment style, but the bathroom access, lower-room void, and bedroom-door geometry must be corrected before saving any image as canonical.
```
