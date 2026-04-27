# System Structure Figure Render Validation

## 1. Purpose

This document completes Step 10 of
`common/docs/architecture/08_system_structure_figure_revision_plan.md`.

The rendered SVG was inspected for text fit, arrow routing, block crossings,
same-direction arrow ambiguity, missing architecture blocks, and authority
ambiguity.

## 2. Rendered Figure

Validated figure:

```text
common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg
```

The SVG was rendered to a PNG using the bundled local image runtime so the
figure could be reviewed as it appears visually, not only as XML coordinates.

## 3. Adjustments Made After Render Review

The render review identified two presentation issues:

- the subtitle still described the figure as a block-only draft;
- several boundary-lane flow labels were readable but sat too close to dense
  vertical arrow bundles.
- the title subtitle and bottom footer repeated authority-boundary text already
  represented by the block layout and legend;
- field input/context and ACK evidence arrows were present in the figure but
  missing from the legend.

The SVG was updated to:

- remove the outdated block-only draft wording from the subtitle;
- remove the title subtitle and bottom footer to reduce redundant explanatory
  text;
- add a white text halo to flow labels for readability over lines;
- move boundary-lane labels to adjacent open space;
- shorten `confirmation response` to `response` where the arrow direction and
  caregiver path already provide context.
- expand the legend to include field input/context and ACK evidence arrows.

## 4. Validation Result

The rendered figure now satisfies the Step 10 checks:

- text fits inside blocks and labels remain readable;
- major arrows avoid unrelated block interiors;
- same-direction arrows remain visually distinguishable;
- Mac mini, caregiver/Telegram, Raspberry Pi, STM32, physical-node, and
  canonical-asset areas are present;
- authority remains with the Mac mini operational hub;
- Raspberry Pi and STM32 remain clearly non-authoritative support paths.

## 5. Next Step

Proceed to:

```text
Step 11. Documentation update
```

Step 11 should check active architecture documents for references that need to
reflect the final interpretation of the figure.
