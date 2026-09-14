---
name: tesla-wrap
description: "Create or revise Tesla custom-wrap PNGs for every vehicle template in teslamotors/custom-wraps while preserving the selected official UV mask, geometry, world-physical subject orientation, optional labels, and Tesla file limits."
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
- The final PNG must have a transparent background wherever the selected template has alpha 0. Never add a solid white, black, colored, photographic, or rendered background; template transparency must remain byte-for-byte intact.
- Preserve the selected template dimensions. Export PNG under 1,000,000 bytes, with an ASCII filename containing only letters, digits, and underscores and at most 30 characters including `.png`. This skill keeps the user's stricter filename rule even though the official README also mentions dashes and spaces.

## Panel role mapping from the reference wrap

Use the supplied cartoon cat wrap as a composition reference, while using the selected official template as the only geometry source:

- Hood or bonnet islands are the primary hero area. Put one large focal subject there, such as the main cat portrait.
- The four main door islands are the other primary hero areas. Put one clear portrait or one major subject per door and keep the face inside that door island.
- Keep every primary subject fully inside one editable white panel island. A cat's ears, eyes, face, body, paws, or tail must never cross an official seam into an adjacent island. Scale the subject down and leave a visible safety margin when needed; use adjacent islands only for simple supporting motifs.
- Front and rear fenders, quarter panels, hatch pieces, and broad secondary islands are for supporting motifs such as clouds, hearts, stars, color blocks, or cropped background texture.
- Bumpers, mirrors, rocker strips, and narrow islands are for small repeat motifs or color accents. Avoid placing a face, long text, or a detailed scene in a narrow island.
- Roof, sunroof, glass, windows, wheel openings, sensors, black regions, transparent regions, and every other protected island receive no generated artwork. Leave the original template pixels unchanged.
- If a selected vehicle has fewer or differently shaped panels, remap the roles from its own `vehicle_image.png` and `template.png`; never transfer coordinates from another vehicle.

## World-physical orientation rule

Every subject must follow the real vehicle coordinate system after UV mapping:

- Keep world up and down consistent with gravity. Heads, upright objects, sky, and vertical lettering point up in the car view; feet, wheels, ground, and shadows point down.
- Keep the vehicle front and rear direction consistent. A subject may face left or right, but it must not become upside down or sideways merely because its panel is rotated in the UV layout.
- For both left and right side doors, the head or top of the main subject must point toward the sunroof and roofline, while the feet or bottom point toward the side skirt. The vehicle nose is a horizontal front/rear direction on a door, never the world-up direction.
- For side panels, rotate or mirror the source crop only as needed to make the final car-view subject upright. Check both left and right sides independently because their UV orientations can differ; do not assume they need the same UV transform.
- For hood, roof, hatch, bumper, mirror, and narrow strips, use the panel surface normal and `vehicle_image.png` to decide the transform. A 180 degree UV transform is valid only when it produces the correct real-world car view, and it must be rechecked after composition.
- Do not use a global canvas rotation as a substitute for per-panel orientation. Intentional abstract pattern rotation does not excuse an upside-down main subject.

### Cross-model cat-wrap direction defaults

For every supported vehicle that has the corresponding panel roles, use these direction defaults for this cartoon cat-wrap composition:

- Left side-door hero subject: rotate the local UV region clockwise 90 degrees with `--rotate-box-cw90`.
- Right side-door hero subject: rotate the local UV region counter-clockwise 90 degrees with `--rotate-box-ccw90`.
- Hood or bonnet hero subject: rotate the local UV region 180 degrees with `--rotate-box`.

These are shared direction rules across vehicle models, not global-canvas rotations. Confirm the resulting car view against each model's `vehicle_image.png`; if an official UV layout differs materially, preserve the same world-up intent and record a model-specific override.

For a 90-degree side-door transform, size the unrotated subject for its post-rotation bounding box. Leave visible safety margins on all four sides; do not fill the full height of a narrow vertical island. A subject that fits before rotation but is cropped, split, or touches a seam after rotation fails the layout check.

### Model Y 2025 Premium cat-wrap transform map

For the current 1024 x 1024 `modely-2025-premium` template, the cartoon cat composition instantiates the cross-model defaults with these verified local UV transforms. Apply them independently from the unrotated source artwork; never stack them on an already transformed output:

- Left lower side-door island: `69,570,165,222` with `--rotate-box-cw90`.
- Right lower side-door island: `785,573,165,222` with `--rotate-box-ccw90`.
- Hood or bonnet hero island: `376,111,269,227` with `--rotate-box` for 180 degrees.
- Front skirt / front bumper island: `245,9,532,106` with `--rotate-front-bumper` for 180 degrees (equivalent to `--rotate-box 245,9,532,106`). For this model, interpret “front skirt” as this model-specific front bumper island and do not rotate unrelated lower-center pieces.

These coordinates are template-specific and must be re-inspected if the official template changes. The two side-door transforms intentionally differ because the left and right UV islands map to opposite sides of the vehicle.

## Full panel coverage and fake transparency

An observed Model Y Premium failure left gray checkerboard strips inside editable front-fender edges, bumper lips, mirrors, and rocker strips. These were opaque RGB artwork imitating transparency, not actual alpha holes. The files passed protected-pixel and alpha checks despite visibly incomplete panel coverage. Those checks alone do not establish a complete fill.

- Determine whether a pixel needs artwork from the exact official template, never from a generated outline or a viewer's checkerboard background. Every exact opaque white template pixel must receive intentional opaque artwork through the panel boundary. Preserve actual template transparency and all protected pixels.
- In generation/edit prompts, explicitly forbid painted transparency grids, accidental gray/blank borders, and inset replacement panel outlines inside editable islands. Extend matching background artwork to the official edges; keep the existing subjects and their orientations.
- Inspect exported files at full resolution and zoom into both front-fender inner edges, bumper lips, mirrors, rocker strips, and narrow secondary islands. Compare suspicious strips against the official mask and inspect RGB as well as alpha. Preview over contrasting solid backgrounds: a baked checkerboard remains visible regardless of the backdrop.
- Do not classify all gray, white, black, or checked artwork as a defect. Preserve intentional fur, shadows, comic contours, mechanical accents, and decorative checks. Color thresholds may flag candidates but require visual and template-based review.
- For a repair, generate matching edge-fill artwork and composite only the affected editable areas through the official mask. Check alignment before compositing; do not paste shifted generated panel edges or black margins into the official white region. Avoid indiscriminately replacing a fixed-width band on every panel, which can alter intact subjects or introduce smearing. Inspect repaired edges for residual grids, dark slivers, stretching, and visible joins.
- Revalidate opacity inside the editable mask, protected pixels, template transparency, dimensions, and file size after export. Compare explicitly unchanged areas against the input (for example, preserve a previously approved hood pixel-for-pixel during an edge-only repair). For a batch, inspect every final file, not only the reported example.

## Workflow

1. Download the selected official template and vehicle reference image. The convenience script can fetch one model or all models into a local clone-shaped directory.
2. Use the built-in image generation tool for the visual artwork. Label the selected template as the geometry reference, the vehicle image as the car-view reference, user photos as identity references, and any prior wrap as a style reference. Ask for a flat UV texture with a transparent background and no scene, car render, or backdrop. State that artwork may change only exact opaque white template pixels; all alpha-0, dark, transparent, glass, roof, sunroof, window, wheel, sensor, seam, and other non-white pixels must remain untouched. Do not ask the model to render text; raster text is added deterministically afterward.
3. Match the selected model's panel count and body shape. Keep faces and focal graphics inside their intended body-panel islands. Do not copy one model's bounds, rotations, or panel assumptions to another model.
4. Perform a world-up review in the car view. On both side doors, verify that heads point toward the sunroof and feet point toward the side skirt. Verify every face, person, animal, object, horizon, wheel, shadow, and text baseline against gravity and the vehicle front/rear direction. Fix each panel transform before continuing.
5. Add an exact name or label only after masking. Use `--name` with a Chinese-capable font and an explicitly inspected `--name-box` wholly inside an editable white panel. The script now refuses a missing name box so a coordinate from another vehicle cannot be reused. Set `--name-angle 180` only when the selected panel mapping requires it, then verify the text is upright in the car view. The script clips text and backgrounds back to the official mask.
6. Run the helper with `--model` or an explicit `--template`, inspect the final PNG, and check its reported protected-pixel and alpha diffs are both zero. If the file is too large, retry with `--quantize 256` or a smaller palette, then re-check the invariants and preview.

7. Perform the full-panel coverage review above on the exported PNG. Zero alpha/protected-pixel diffs do not detect opaque fake-transparency grids; resolve any visually unfilled editable areas before delivery.

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
  --output Cat_Model3_Example.png
```

For a direct template path, replace `--model` and `--template-root` with `--template path/to/template.png`. Omit `--name` when the wrap should have no name badge. When adding a label, first inspect the selected template and pass both `--name` and a matching `--name-box x,y,width,height`; do not reuse the old Premium coordinates. Use `--rotate-box` for 180-degree model-specific regions, `--rotate-box-cw90` for clockwise quarter-turn regions, and `--rotate-box-ccw90` for counter-clockwise quarter-turn regions. The quarter-turn options preserve the requested region size and do not rescale an oversized subject, so fit the source artwork for its rotated bounds before applying them. Use `--rotate-front-bumper` only with a verified box for the selected model. Use `--quantize 256` only when needed to meet the byte limit; it changes editable colors but protected pixels are restored and validated.

## Completion checks

Confirm all of the following before handing off the file:

- output is PNG, matches the selected template dimensions, and is within the byte limit;
- filename matches the allowed ASCII pattern and length;
- protected-pixel diff is 0 and alpha diff is 0;
- every editable template pixel is opaque and intentionally filled, with no baked transparency grid or unintended blank edge strip; narrow islands and panel boundaries have been visually checked in every deliverable;
- no unintended text, badge, watermark, rendered car, backdrop, or artwork outside the selected official editable mask remains;
- every primary subject is fully contained within its intended single panel island, with no face, limb, or major detail crossing a seam;
- after every local rotation, every primary subject remains complete inside the transformed panel island, with no cropped edge, seam interruption, or clipped accessory;
- every template alpha-0 pixel remains transparent in the final PNG;
- the final image has been visually inspected against the selected `vehicle_image.png`, including bumper and side-panel directions and world-physical subject orientation;
- the selected slug and template dimensions are recorded in the delivery note or command log.
