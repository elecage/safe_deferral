# OV Generation Prompt Template

## 1. Purpose

This file stores the prompt, negative prompt, seed, canvas, and metadata rules for generating the canonical Korean apartment background used by OV figures.

The generated background is not itself the full scenario figure. Scenario-specific node highlights, arrows, labels, and policy/topic panels should be added later as SVG overlays.

---

## 2. Fixed seed values

Use these values unless a later version intentionally supersedes them:

```text
OV_STYLE_SEED = 20260425
OV_BASE_BACKGROUND_SEED = 20260425
OV_OVERLAY_STYLE_SEED = 20260425
```

Important caveat:

```text
Seed is recorded for reproducibility, but the approved canonical background file is the actual visual baseline.
```

---

## 3. Base background prompt

```text
A clean semi-isometric technical illustration of a modern Korean apartment interior, showing entrance, living room, kitchen, bedroom, bathroom, and balcony in one coherent view. Minimal warm neutral colors, low visual noise, no people, fixed IoT node placeholders on walls and ceilings, clear space for overlay arrows and labels, academic paper figure style, 16:9 canvas.
```

---

## 4. Negative prompt

```text
No text labels, no random people, no clutter, no dramatic lighting, no photorealistic mess, no distorted floorplan, no duplicated rooms, no door lock emphasis, no emergency scene by default, no visible brand logos, no excessive decorations, no unreadable tiny text, no floating UI panels baked into the background.
```

---

## 5. Required visual features

The base background should include these apartment zones:

```text
- entrance / 현관
- living room / 거실
- kitchen / 주방
- bedroom / 침실
- bathroom / 욕실
- balcony / 베란다
```

The base background may include very subtle neutral placeholders for IoT node locations, but the active node labels and scenario-specific graphics must be added through overlays.

---

## 6. Canvas and export target

Working canvas:

```text
1920 x 1080 px
```

Paper-ready export target:

```text
3840 x 2160 px
```

Aspect ratio:

```text
16:9
```

---

## 7. Background metadata template

When the canonical background is created, add:

```text
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.metadata.json
```

Suggested metadata structure:

```json
{
  "asset_id": "ov_base_korean_apartment_v1",
  "asset_type": "canonical_background",
  "created_date": "YYYY-MM-DD",
  "style_seed": 20260425,
  "base_background_seed": 20260425,
  "prompt_file": "../specs/ov_generation_prompt_template.md",
  "prompt": "A clean semi-isometric technical illustration of a modern Korean apartment interior...",
  "negative_prompt": "No text labels, no random people...",
  "canvas": {
    "width": 1920,
    "height": 1080,
    "aspect_ratio": "16:9"
  },
  "tool_or_model": "TBD",
  "manual_edit_notes": [],
  "approved_as_canonical": false,
  "approval_notes": "TBD"
}
```

---

## 8. Scenario overlay prompt pattern

Scenario overlays should not regenerate the base background.

Use this pattern only for manually describing or generating overlay elements:

```text
Using the fixed canonical Korean apartment background ov_base_korean_apartment_v1, create a transparent SVG overlay for [FIGURE_ID] [SCENARIO_NAME]. Highlight only the active nodes, show event icons, show data-flow arrows, and label the key topic/payload/policy flow. Preserve the fixed node coordinates from ov_node_coordinate_map.json. Do not alter the background.
```

---

## 9. Prohibited prompt outcomes

Do not generate backgrounds or overlays that imply:

```text
- LLM has actuation authority;
- dashboard or test app can directly control actuators;
- doorbell context authorizes door unlock;
- Class 2 is always terminal failure;
- Class 1 can execute outside the low-risk catalog;
- emergency is triggered by LLM-generated text alone;
- audit log is a control component.
```
