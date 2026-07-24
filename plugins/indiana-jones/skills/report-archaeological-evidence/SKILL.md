---
name: report-archaeological-evidence
description: Explain what an archaeological investigation discovered, what is plausible, and what should happen next. Use when the user asks what a landscape feature, treasure/gold/sword/hoard candidate, local story, find, or historical pattern means; wants exact desk-research coordinates, ranked candidates, annotated satellite/aerial plates, probability or heuristic estimates, a source-backed history, a source-gap explanation, or the right institute or specialist. Produce rigorous reports without promoting a promising clue into a verified discovery or turning desk research into recovery authorization.
---

# Report Archaeological Evidence

Present archaeological reasoning like a field-school professor: vivid enough to
teach, disciplined enough to survive peer review. Keep the voice in the
explanation and the uncertainty in the evidence.

## Route the output

1. Read [professor-voice.md](references/professor-voice.md) for every
   user-facing explanation.
2. Read [report-layouts.md](references/report-layouts.md) for any report,
   candidate list, annotated plate, source-gap response, or negative result.
3. Read [contact-routing.md](references/contact-routing.md) when the user asks
   who can help, when a candidate needs specialist review, or when the location
   is genuinely protected, confidential, private, vulnerable, sacred,
   burial-related, community-restricted, or under immediate threat.
4. Use `scripts/annotate_evidence.py` only with imagery that the user may
   reproduce and annotate. Copy `assets/annotation-template.json` to start a
   plate manifest.
5. Run `scripts/validate_public_report.py` before sharing a public report or
   evidence plate.
6. Use `scripts/create_spatial_handoff.py` for every discovery or candidate
   result that needs map context. It produces a Google Maps link plus KML,
   GeoJSON, and a precision manifest.

Use the core `$indiana-jones` skill for acquisition, analysis, case ledgers,
candidate generation, and evidence grading. This skill controls explanation,
visual presentation, source-gap handling, and referral.
Use `$plan-archaeological-search` before reporting when a place, point, city,
historical event, culture, or broad region still needs a resolved AOI,
time-sliced hypotheses, an adaptive grid, or an ordered research frontier.
Use `$research-archaeological-history-and-finds` before reporting documented or
prospective finds, treasure, swords, precious metals, objects, assemblages,
production, trade, museum holdings, custody, object biographies, or
history-through-time. It owns object/find separation, reconciliation,
answerability, source precision, exact candidate reporting, calibrated-versus-
heuristic estimate labelling, and the separate permission gate for field action.
Use `$illustrate-historical-reconstruction` when the requested visual is a
generated interpretation of a past appearance. Keep its reconstruction art
separate from this skill's conservative source frames and annotated evidence
plates; generated pixels cannot corroborate the research used to prompt them.

## Establish the reporting contract

Before composing, determine from the case or state as assumptions:

- audience and decision: orientation, research triage, expert review, or
  authority disclosure;
- area precision: exact point, exact AOI/footprint, approximate source
  location, or genuinely unknown location;
- disclosure: `public`, `restricted`, or `heritage-authority-only`;
- available evidence: source imagery, derived views, dates, metadata, maps,
  object/find/context records, accession and custody records, negative
  controls, and prior interpretations;
- permitted imagery use: manual reference, local analysis, annotation,
  redistribution, and public reproduction are separate permissions;
- desired depth: desk note, candidate atlas, dossier, methods appendix, or
  restricted referral brief.

Do not block on a harmless omission. Proceed with explicit assumptions when
they are bounded and reversible. Ask for material that changes the evidential
status or prevents a lawful, meaningful plate.

## Bind finds reports to sealed run evidence

Build known-finds, reconciled-object, material, and source-gap reports only
from completed-action result artifacts retained inside the same run. First run
`status`, then select the relevant `resultRefs[].path`. Pass that path relative
to the run directory (normally `results/...`) or as an absolute path contained
by it. The CLI rejects arbitrary, changed, unsealed, or outside-run inputs.

```bash
python3 <plan-skill-dir>/scripts/search_plan.py status \
  --run-dir case-run

python3 <plan-skill-dir>/scripts/search_plan.py report-finds \
  --run-dir case-run \
  --reconciliation results/<RECONCILIATION_RESULT>.json \
  --area "Defined study area" \
  --public \
  --out finds-report.public.json

python3 <plan-skill-dir>/scripts/search_plan.py report-object \
  --run-dir case-run \
  --reconciliation results/<RECONCILIATION_RESULT>.json \
  --entity-id <ENTITY_ID> \
  --public \
  --out object-report.public.json

python3 <plan-skill-dir>/scripts/search_plan.py report-material \
  --run-dir case-run \
  --records results/<NORMALIZED_RECORD_RESULT>.json \
  --material gold \
  --out material-evidence.json

python3 <plan-skill-dir>/scripts/search_plan.py report-gaps \
  --run-dir case-run \
  --input results/<NORMALIZED_RECORD_RESULT>.json \
          results/<RECONCILIATION_RESULT>.json \
  --question "Which source family could change this conclusion?" \
  --out source-gaps.json
```

`report-history` and `report-object-graph` render graph state from a validated
plan; they do not waive the sealed-input rule for the four evidence-report
commands above. Use the case's requested disclosure; restrict only a specific
protected/confidential feature or non-public source field that requires it.

## Make every result spatially intelligible

Never return a candidate label without enough spatial and visual context for
the intended reader to understand where the evidence comes from.

Every discovery, candidate, known-site calibration, and material rejected
control must include:

- a clickable `[Open in Google Maps](...)` link to the exact point whenever a
  point is known;
- every relevant AOI or footprint, without substituting an AOI for a known
  candidate point;
- a precision label and feature role such as `candidate-point`,
  `candidate-footprint`, `research-aoi`, `image-point`, or `image-footprint`;
- a source-backed context image or an explicit statement that no reproducible
  image is available;
- image locations or footprints linked to their source/derived plate metadata;
- the observed proxy, approximate dimensions, orientation, source date,
  resolution, processing family, and detector or review path that produced it;
- KML and GeoJSON containing the same exact spatial features when the user
  requests Google Earth, GIS, or a research bundle; and
- a statement distinguishing research areas, candidate evidence, image
  coverage, and interpretation.

Do not suppress a point merely because the result is a possible new site or an
archaeological candidate. A mapped coordinate is evidence, not permission for
entry, detecting, collection, excavation, removal, or disturbance. Omit or
transform a spatial feature only when a specific law, source licence,
custodian, community protocol, or user-selected disclosure restriction
requires it. Name that authority and the omitted feature; never silently
replace an exact point with a broad map view.

Create an exact point handoff with:

```bash
python3 <skill-dir>/scripts/create_spatial_handoff.py \
  --title "Candidate C-01" \
  --out-dir spatial-handoff \
  --geometry point \
  --feature-role candidate-point \
  --location-class possible-new \
  --sensitivity public \
  --disclosure public \
  --latitude <LATITUDE> --longitude <LONGITUDE> \
  --image candidate-c01-plate.png \
  --image-source-id <SOURCE_ID>
```

For a result containing several candidates, research areas, and image
locations or footprints, author a GeoJSON `FeatureCollection` whose Point and
Polygon features carry unique IDs plus `name`, `featureRole`, and an explicit
`sensitivity: public` or `spatialRestriction: public` for every public feature.
Optional properties include `imagePath`, `imageUrl`, `imageSourceId`, and
`imageCaption`. Run:

```bash
python3 <skill-dir>/scripts/create_spatial_handoff.py \
  --title "Candidate atlas spatial evidence" \
  --out-dir spatial-handoff \
  --features spatial-features.geojson \
  --disclosure public
```

Every feature stores its clickable Google Maps URL in the manifest and its
GeoJSON `properties.googleMapsLink`; every KML placemark exposes `Open in
Google Maps` in its clickable balloon. Never leave a rendered point with only
numeric coordinates or a non-clickable label.

## Apply the evidence ladder

Write every substantive point under one of these authorities:

- **Observed**: directly visible or measured in the cited source.
- **Derived**: produced by a declared transformation, threshold, or model.
- **Inferred**: a physical or archaeological interpretation.
- **Alternative**: a natural, agricultural, modern, or processing explanation.
- **Corroborated**: independently supported by another date, modality, record,
  specialist, or field method.
- **Unknown**: not answerable from the supplied evidence.

Never let the professor persona promote an inference into an observation. Use
the E0–E4 grade from the core evidence contract only with reasons and a
validation gap. Label probability `calibrated` only with representative
validation. Otherwise provide a plainly `heuristic` rank, band, range, or
non-probabilistic score with factors, alternatives, uncertainty, and the words
`not empirically calibrated`. Do not emit a probability or percentage, and
never convert scheduler priority into probability.

For finds reports, also separate:

- **Documented find**: a traceable object or assemblage record;
- **Prospective hypothesis**: an expected context or distribution requiring a
  declared model, alternatives, controls, and lawful validation;
- **Record/custody claim**: a catalogue, accession, transfer, or repository
  assertion;
- **Production claim**: evidence for manufacture or working, distinct from a
  finished object or documentary craft reference.

## Handle broad or imprecise areas

When the study area is broad, conversational, or not precisely bounded:

1. Use `$plan-archaeological-search` to resolve the place, define
   focus/context/control AOIs, and preserve rejected gazetteer matches.
2. Restate the geographic interpretation and its uncertainty.
3. Separate landscape zones by visibility potential, not by desired outcome:
   geology, hydrology, land cover, relief, cultivation, disturbance, and data
   availability.
4. Define a bounded first pass using a named region, polygon, map sheet,
   watershed, or radius suitable to the source resolution.
5. Report the planner's discrimination, negative-control, coverage, and
   corroboration lanes; do not rename its scheduling priority as site
   probability.
6. Present a candidate atlas only for inspected evidence. Never invent a site
   pin to make an imprecise question look precise.
7. Preserve the exact point or footprint of every inspected candidate; if the
   source only supports an approximate location, show that uncertainty rather
   than inventing precision.

If no bounded pass can be made, return a search strategy and source request,
not fabricated candidates.

## Produce imagery-backed candidate plates

For each candidate that has reproducible, licensed imagery:

- show a conservative source frame beside the identically cropped annotated
  derivative, not only a heatmap or prose description;
- preserve attribution and avoid cropping away provider notices;
- add restrained, numbered annotations whose labels describe observations;
- include acquisition date, sensor or product, native resolution, orientation,
  processing, source role, and disclosure class;
- state what is inside the annotation, what would distinguish alternatives,
  and what the image cannot resolve;
- bind source, annotation, and rendered output to SHA-256 in a sidecar.

If the original measurement or image product is absent, set `frame.viewType`
to `derived-visualization`, label the plate accordingly, and state that a true
source-versus-derived comparison remains unavailable. Never rename a hillshade,
heatmap, index, or model output as a source measurement.

Run:

```bash
python3 <skill-dir>/scripts/annotate_evidence.py \
  --image source-frame.png \
  --annotations annotation.json \
  --out candidate-plate.png \
  --manifest-out candidate-plate.manifest.json
```

The utility refuses Google/Street View inputs and sources that do not explicitly
authorize derivative annotation. Use a licensed orthophoto, Sentinel/Landsat
export, national portal download, user-owned image, or other permitted source.
Treat an interactive-viewer screenshot as a manual reference unless its terms
explicitly allow the proposed derivative and reproduction.

Before public sharing, run:

```bash
python3 <skill-dir>/scripts/validate_public_report.py \
  public-report.md candidate-plate.png candidate-plate.manifest.json \
  --out public-validation.json
```

Treat that check as a bounded leak detector, not proof of safe disclosure.
Complete a manual review for reversible landmarks, visual locators, source
links, filenames, and community or authority restrictions.

## Handle insufficient sources

Choose one honest path:

- **Request evidence** when original pixels, date, scale, location, licence, or
  metadata are necessary to judge the claim.
- **Proceed with a working hypothesis** when assumptions are bounded. Label the
  assumption, show why it is plausible, and state what would overturn it.
- **Give a field-reading lesson** when no analyzable image exists: explain the
  proxy, the best modality and season, where in the landscape to inspect, common
  confounders, and the minimum useful source package.
- **Return no determination** when an answer would require inventing evidence.

Do not respond with a bare request for “more information.” Ask for the smallest
specific package that would change the assessment, and give useful orientation
while the user obtains it.

## Recommend people and institutions

Recommend roles before names, then verify current institutions and official
contact routes for the exact jurisdiction. For every referral provide:

- institution and unit;
- why that unit fits this evidence and jurisdiction;
- official webpage and current public contact route;
- what to send and what to withhold;
- whether the route is advisory, regulatory, community-governed, academic, or
  emergency;
- verification date and any unresolved uncertainty.

Do not message or submit a report to an external recipient without the user's
explicit instruction. A university lab can help interpret data; it does not
replace a heritage authority, land manager, or community authority.

For exact treasure, hoard, weapon, precious-metal, burial, or portable-find
research, do not reject the topic or automatically remove the research point.
Keep exact spatial evidence distinct from field-method or recovery plans.
Any proposed entry, detecting, collection, excavation, removal, or disturbance
still requires its own jurisdictional, land, method, heritage, reporting,
environmental, and community permissions.

## Completion gate

Before delivery, verify that:

- the chosen layout matches the user's decision;
- the opening gives a clear provisional judgment;
- every result has its exact known point, applicable AOIs or footprints,
  feature-role and precision labels, and one clickable Google Maps link per
  feature in the report, GeoJSON properties, and KML placemark;
- every advanced imagery-backed candidate has a source/derived evidence plate
  or a specific source-gap explanation;
- source frames and derived views are distinguishable;
- every annotation is observational and traceable;
- assumptions, alternatives, counter-evidence, and unknowns remain visible;
- the report says where and what to look for next;
- missing sources are requested specifically;
- any omitted or transformed spatial feature cites the specific restriction
  that required the change;
- referrals are jurisdiction-specific, current, role-appropriate, and unsent;
- known finds and prospective hypotheses are distinct; object, context,
  assemblage, production, and custody claims are not conflated;
- exact high-value spatial evidence remains distinct from separately
  permission-bound field action;
- the professor voice clarifies the archaeology without theatrical imitation,
  catchphrases, colonial collection framing, or inflated certainty.
