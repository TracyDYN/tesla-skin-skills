---
name: tesla-wrap
description: "Create or revise Tesla custom-wrap PNGs for every vehicle template in teslamotors/custom-wraps while preserving the selected official UV mask, geometry, orientation, optional labels, and Tesla file limits."
---

# Tesla custom wraps for all official models

Use this skill when a user wants a flat Tesla Paint Shop wrap made from personal photos, a style reference, or an existing wrap. Select the exact vehicle slug first. The deliverable is one flat PNG for Tesla import, not a rendered vehicle image.

## Official model catalog

The catalog in `models.json` mirrors the vehicle folders in the official repository:

`cybertruck`, `model3`, `model3-2024-base`, `model3-2024-performance`, `modely`, `modely-2025-base`, `modely-2025-performance`, `modely-2025-premium`, `modely-l`, `models-2021`, `models-2025-plaid`, and `modelx-2021`.

Use the folder slug exactly as written. Each official folder contains its own `template.png` and `vehicle_image.png`. The canvas is template-dependent: official templates are within 512 x 512 to 1024 x 1024, and Cybertruck is currently 1024 x 768. Never force every model to 1024 x 1024.

## Non-negotiable invariants

- Start from the exact selected `template.png` in the Tesla repository: <https://github.com/teslamotors/custom-wraps>.
- Keep the original canvas size, panel contours, seams, transparent/black regions, and every non-white protected pixel. The only editable mask is an opaque pixel whose template RGBA value is exactly `(255,255,255,255)`.
- Do not let generated artwork redraw the template, windows, wheel openings, sensors, or seams. Compose the artwork through `scripts/apply_wrap.py`, which restores protected pixels and reports the protected-pixel and alpha diffs.
- Preserve the selected template dimensions. Export PNG under 1,000,000 bytes, with an ASCII filename containing only letters, digits, and underscores and at most 30 characters including `.png`. This skill keeps the user's stricter filename rule even though the official README also mentions dashes and spaces.

## Workflow

1. Download the selected official template and vehicle reference image. The convenience script can fetch one model or all models into a local clone-shaped directory.
2. Use the built-in image generation tool for the visual artwork. Label the selected template as the geometry reference, the vehicle image as the car-view reference, user photos as identity references, and any prior wrap as a style reference. Ask for a flat UV texture. Repeat the protected-region invariant in the prompt. Do not ask the model to render text; raster text is added deterministically afterward.
3. Match the selected model's panel count and body shape. Keep faces and focal graphics inside their intended body-panel islands. Do not copy one model's bounds, rotations, or panel assumptions to another model.
4. Orient the UV artwork for the selected car view. Inspect `vehicle_image.png` and the official template to determine which islands are left, right, front, rear, roof, mirror, or bumper. Use `--rotate-box x,y,width,height` for any panel that must be inverted; repeat the option for multiple regions. `--rotate-front-bumper` is a convenience option only when a matching `--front-bumper-box` is supplied. The catalog includes one legacy Premium box `245,9,532,106`.
5. Add an exact name or label only after masking. Use `--name` with a Chinese-capable font and a box wholly inside an editable white panel. Set `--name-angle 180` when text belongs to an upside-down region. The script clips text and backgrounds back to the official mask.
6. Run the helper with `--model` or an explicit `--template`, inspect the final PNG, and check its reported protected-pixel diff and alpha diff are both zero. If the file is too large, retry with `--quantize 256` or a smaller palette, then re-check the invariants and preview.

## Deterministic helper

The helper requires Pillow (`python -m pip install pillow`) and keeps the mask logic in one place. List models and fetch official assets as follows:

```text
python scripts/apply_wrap.py --list-models
python scripts/fetch_templates.py --model model3 --dest official_custom_wraps
python scripts/fetch_templates.py --dest official_custom_wraps
```

Generate a wrap from a local clone of the official repository:

```text
python scripts/apply_wrap.py \
  --model model3 \
  --template-root official_custom_wraps \
  --design generated_design.png \
  --output Cat_Model3_Example.png \
  --rotate-front-bumper \
  --name August --name-box 414,31,212,58 --name-angle 180 \
  --font "C:\\Windows\\Fonts\\msyh.ttc"
```

For a direct template path, replace `--model` and `--template-root` with `--template path/to/template.png`. Omit `--name` when the wrap should have no name badge. Use `--rotate-box` for model-specific regions. Use `--rotate-front-bumper` only with a verified box for the selected model. Use `--quantize 256` only when needed to meet the byte limit; it changes editable colors but protected pixels are restored and validated.

## Completion checks

Confirm all of the following before handing off the file:

- output is PNG, matches the selected template dimensions, and is within the byte limit;
- filename matches the allowed ASCII pattern and length;
- protected-pixel diff is 0 and alpha diff is 0;
- no unintended text, badge, watermark, rendered car, or artwork outside the selected official editable mask remains;
- the final image has been visually inspected against the selected `vehicle_image.png`, including bumper and side-panel directions;
- the selected slug and template dimensions are recorded in the delivery note or command log.
