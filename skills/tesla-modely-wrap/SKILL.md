---
name: tesla-modely-wrap
description: "Create or revise Tesla Model Y (2025+) Premium custom-wrap PNGs from user photos while preserving the official UV mask, panel orientation, optional name text, and Tesla file limits."
---

# Tesla Model Y Premium custom wraps

Use this skill when a user wants a Tesla Model Y (2025+) Premium Paint Shop wrap made from personal photos, a style reference, or an existing wrap. The deliverable is one flat PNG for Tesla import, not a rendered vehicle image.

## Non-negotiable invariants

- Start from the official `modely-2025-premium/template.png` in the Tesla repository: <https://github.com/teslamotors/custom-wraps/tree/master/modely-2025-premium>.
- Keep the original canvas size, panel contours, seams, transparent/black regions, and every non-white protected pixel. The only editable mask is an opaque pixel whose template RGBA value is exactly `(255,255,255,255)`.
- Do not let generated artwork redraw the template, windows, wheel openings, sensors, or seams. Compose the artwork through `scripts/apply_wrap.py`, which restores protected pixels and reports the protected-pixel and alpha diffs.
- The Premium template is 1024 x 1024. Export PNG under 1,000,000 bytes when possible, with an ASCII filename containing only letters, digits, and underscores and at most 30 characters including `.png`.

## Workflow

1. Obtain the exact official Premium template and verify it is 1024 x 1024. View local reference images before using them as image-generation inputs.
2. Use the built-in image generation tool for the visual artwork. Label the template as the geometry reference, user photos as identity references, and any prior wrap as a style reference. Ask for a flat UV texture and repeat the protected-region invariant in the prompt. Do not ask the model to render Chinese text; raster text is added deterministically afterward.
3. In the generation prompt, require five cat portraits at most: hood plus the four main door panels. Preserve the cat's distinctive markings and keep each face inside its panel.
4. Orient the UV artwork for the car view. Side-panel artwork must have its top facing the template center: left-side pieces use +90 degrees and right-side pieces use +270 degrees (equivalent to -90 degrees). When the user requests the front bumper to be inverted, rotate the top horizontal front-bumper piece 180 degrees with `--rotate-front-bumper`; its default Premium bounds are `245,9,532,106`.
5. Add an exact name or label only after masking. Use `--name` with a Chinese-capable font and a box wholly inside an editable white panel. Set `--name-angle 180` when text belongs to a front-bumper pattern that is itself upside down. The script clips text and backgrounds back to the official mask.
6. Run the helper, inspect the final PNG, and check its reported protected-pixel diff and alpha diff are both zero. If the file is too large, retry with `--quantize 256` or a smaller palette, then re-check the invariants and preview.

## Deterministic helper

The helper requires Pillow (`python -m pip install pillow`) and keeps the mask logic in one place:

```text
python scripts/apply_wrap.py \
  --template template.png \
  --design generated_design.png \
  --output Cat_ModelY_Example.png \
  --rotate-front-bumper \
  --name August --name-box 414,31,212,58 --name-angle 180 \
  --font "C:\\Windows\\Fonts\\msyh.ttc"
```

Omit `--name` when the wrap should have no name badge. Omit `--rotate-front-bumper` when the front-bumper artwork should keep its generated orientation. Use `--quantize 256` only when needed to meet the byte limit; it changes editable colors but protected pixels are restored and validated.

## Completion checks

Confirm all of the following before handing off the file:

- output is PNG, 1024 x 1024, and within the byte limit;
- filename matches the allowed ASCII pattern and length;
- protected-pixel diff is 0 and alpha diff is 0;
- no unintended text, badge, watermark, rendered car, or artwork outside the official editable mask remains;
- the final image has been visually inspected, including the bumper and side-panel directions.
