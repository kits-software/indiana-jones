---
name: illustrate-historical-reconstruction
description: Research and create attractive, evidence-led illustrations of how historical people, objects, clothing, buildings, interiors, settlements, cities, landscapes, or lived scenes could have appeared at a specified place and time. Use when the user asks to see, depict, visualize, reconstruct, bring to life, or make an image of the past, including a named historical figure, an ordinary person from a culture or occupation, a lost structure, an ancient or medieval city, an artefact in use, or a before-and-after historical scene. Produce a clearly labelled reconstruction rather than presenting generated imagery as documentary evidence.
---

# Illustrate Historical Reconstruction

Create a compelling image of the past whose beauty is constrained by evidence
rather than substituted for it. Treat the image as a testable interpretation,
not as an observation, discovery, exact likeness, or time-travel photograph.

## Companion boundaries

- Use `$plan-archaeological-search` first when the place identity, historical
  extent, phase, event, route, or time slice is unresolved.
- Use `$research-archaeological-history-and-finds` to establish the history,
  material culture, clothing, work, buildings, object biographies, documentary
  records, and archaeological context that constrain the scene.
- Use `$indiana-jones` for imagery, terrain, source provenance, candidate
  investigation, and the shared archaeological evidence contract.
- Use `$report-archaeological-evidence` for source-backed explanation,
  annotated evidence plates, public disclosure review, or specialist referral.
  Generated reconstruction art and annotated source evidence must remain
  visibly different products.
- Use the installed `$imagegen` skill and built-in image-generation tool for
  the final raster illustration. Follow its save-path, input-role, inspection,
  iteration, and delivery rules.
- Read the core
  [ethics-and-web-research.md](../indiana-jones/references/ethics-and-web-research.md)
  before archive, web, community, or authenticated-source research.

Read [reconstruction-method.md](references/reconstruction-method.md) for every
reconstruction. Also read [subject-evidence-guides.md](references/subject-evidence-guides.md)
for the relevant subject class.

## Non-negotiable rules

- Freeze a place, time slice, subject state, and viewpoint before generation.
  Do not blend attractive features from different centuries into a timeless
  composite unless the user explicitly requests a comparative montage.
- Map each consequential visible choice to a source, an explicit analogy, or a
  labelled illustrative decision. Repetition of one source lineage is not
  independent support.
- Treat Grok, ChatGPT, another AI assistant, search snippets, and generated
  summaries as lead-finding aids only. Verify every visual claim against the
  underlying publication, catalogue, record, measurement, or community source.
- Use `documented`, `strongly-constrained`, `plausible`, `illustrative`, or
  `contested` for reconstruction status. These labels describe the support for
  a visual decision, not the beauty or realism of the image.
- Generate alternatives, defer the feature, or disclose a single chosen
  interpretation whenever a high-impact feature is `plausible`,
  `illustrative`, or `contested`.
- Never claim an exact face from a skull, a generic period portrait, ancestry,
  or an image model. Separate facial approximation, pigmentation evidence,
  clothing evidence, and invented grooming, expression, or personality.
- Do not produce a remains-based facial approximation without appropriate
  anthropological analysis and specialist review. When those inputs are
  unavailable, offer a period-and-context portrait that does not claim the
  individual's face.
- Represent use, repair, wear, weather, unfinished work, age, body diversity,
  season, ecology, and ordinary infrastructure when evidence supports them.
  Do not make every building pristine, every person a model, or every city a
  ceremonial centre.
- Add negative constraints for anachronistic materials, technologies,
  silhouettes, symbols, crops, animals, street furniture, and visual clichés.
- Do not use a reference image for generation merely because it is visible
  online. Record whether it may be copied, transformed, or used as an image
  input; otherwise keep it as a manual research reference.
- Respect descendant, Indigenous, host, religious, and associated communities.
  Do not invent sacred imagery, funerary display, body exposure, ethnicity, or
  culturally restricted knowledge to make a scene more dramatic.
- Keep sensitive archaeological coordinates and reversible locators out of
  public prompts, filenames, image metadata, and captions.
- Label the result `evidence-led historical reconstruction`, `plausible
  reconstruction`, or `illustrative reconstruction` as warranted. Never call a
  generated image a photograph, scan, source frame, or verified appearance.

## Workflow

### 1. Contract the image

Determine, or state bounded assumptions for:

- subject kind and identity;
- place, polity or cultural context, and allowed geographic precision;
- exact date, date range, reign, occupation phase, or event moment;
- state of the subject at that moment, such as newly built, inhabited,
  repaired, damaged, abandoned, excavated, or restored;
- intended audience and use;
- framing, viewpoint, aspect ratio, medium, and desired emotional register;
- whether the user wants one leading reconstruction, alternatives, a
  comparison, a cutaway, a street-level scene, or an aerial overview;
- disclosure class and treatment of culturally sensitive material.

Do not block a harmless creative request for perfect documentation. For a
quick request, perform a bounded source pass, state assumptions, and lower the
label to `plausible` or `illustrative` where necessary.

### 2. Research the visible decisions

Search the strongest independent source families that can constrain what the
viewer will actually see. Prefer:

1. direct contemporary measurements, photographs, portraits, plans, maps,
   excavated remains, inscriptions, objects, textiles, environmental samples,
   and scientific analyses;
2. indirect contemporary descriptions, views, inventories, chronicles, oral
   histories, and iconography evaluated for purpose and bias;
3. later scholarly reconstructions and securely dated regional comparanda;
4. broad analogy only when its geographic, temporal, social, and functional
   distance is recorded.

Research the unglamorous constraints too: dimensions, circulation, drainage,
roofing, fuel, waste, light, tools, repair, vegetation, animals, seasonality,
labour, and social variation. These often prevent the most convincing-looking
anachronisms.

### 3. Build the reconstruction brief

Copy `assets/reconstruction-brief-template.json`. Give every source and visual
decision a stable ID. Record:

- source authority, origin family, role, date, locator, and use basis;
- the proposed depiction for each visible element;
- status, rationale, source IDs, alternatives, and visual impact;
- negative constraints and known model failure modes;
- the exact prompt, inspection checks, uncertainty policy, and caption.

Keep aesthetic choices such as cinematic lighting separate from historical
claims. Aesthetic choices may be beautiful; they simply need to remain
recognizable as choices.

Run the preflight validator before generation:

```bash
python3 <skill-dir>/scripts/validate_reconstruction_brief.py \
  reconstruction-brief.json \
  --stage preflight
```

### 4. Compile the prompt from evidence

Use the `historical-scene` image-generation class. Structure the prompt in this
order:

1. identity, place, time slice, and subject state;
2. geometry, scale, pose, street plan, or other locked structural anchors;
3. materials, construction, clothing, technology, iconography, and condition;
4. environment, activity, social context, and human-scale cues;
5. composition, medium, lighting, palette, and mood;
6. explicit negative constraints and invariants.

Use precise archaeological, architectural, textile, and material vocabulary.
Do not ask the model to invent missing facts. Translate each uncertain choice
into one selected hypothesis or a planned variant.

### 5. Generate and inspect

Call the built-in image-generation tool directly. If licensed or user-owned
reference images are supplied, label each role before the call:

- `structural reference`;
- `material or costume reference`;
- `portrait or identity reference`;
- `composition or style reference`;
- `edit target`.

After generation, inspect the actual image at high detail. Check:

- locked proportions, plan, pose, silhouette, and spatial relationships;
- clothing, materials, construction, tools, flora, fauna, and technology;
- modern artefacts, fantasy defaults, copied stereotypes, and mixed periods;
- over-idealized bodies, pristine surfaces, empty cities, impossible labour,
  or implausible lighting and weather;
- whether a striking invented detail has become the visual focal point.

Reject or revise an image that violates a high-impact anchor even if it is
beautiful. Iterate with one targeted correction and repeat the inspection.

### 6. Handle uncertainty visibly

For unresolved high-impact choices, prefer one of:

- `alternative-variants`: generate matched views that change only the disputed
  feature;
- `single-main-with-disclosure`: choose the best-supported option and explain
  the alternatives beside the image;
- `defer-depiction`: crop, obscure, simplify, or omit the unknowable element.

Do not encode uncertainty only as fog, transparency, or sketchiness inside an
otherwise photorealistic image; viewers may read that as style rather than
epistemic status. Carry the uncertainty in the caption and evidence ledger.

### 7. Package and deliver

Update the brief with the final prompt, generation date, tool, output path,
reference-image roles, checks, remaining issues, and caption. Run:

```bash
python3 <skill-dir>/scripts/validate_reconstruction_brief.py \
  reconstruction-brief.json \
  --stage final
```

Deliver:

1. the image or matched variants;
2. a one-sentence reconstruction label and time/place anchor;
3. the strongest documented features;
4. the largest visible uncertainties and alternatives;
5. a concise source list;
6. the saved image and brief paths when project-bound.

Do not place dense citations or an evidence table inside the generated image.
Keep those in the surrounding caption or report where they remain readable and
auditable.

## Completion gate

Do not call the reconstruction complete until:

- the place, time slice, subject state, audience, and disclosure are explicit;
- every high-impact visual choice has a source, analogy, or illustrative label;
- source permissions and image-input roles are recorded;
- prompt anchors and anachronism exclusions are derived from the brief;
- the generated pixels were inspected against structural, cultural, material,
  environmental, and bias checks;
- unresolved high-impact choices use a declared variant policy;
- the final image is labelled as a reconstruction, not evidence;
- the caption states what is documented, inferred, illustrative, and unknown;
- the prompt, sources, decisions, tool, date, and output are preserved as
  reconstruction paradata.
