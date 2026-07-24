---
name: report-archaeological-evidence
description: Explain what an archaeological investigation has discovered, what is merely plausible, and what should happen next. Use when the user asks what a landscape feature, candidate place, local story, find, or historical pattern means; wants a clear illustrated or source-backed account; needs competing explanations ranked; wants a place or community history told through time; or needs the right archaeologist, heritage authority, university, museum, community body, or specialist. Produce rigorous explanations, candidate atlases, annotated imagery, negative results, source requests, and referrals without promoting a promising clue into a verified discovery.
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
   may be new, vulnerable, sacred, burial-related, or under immediate threat.
4. Use `scripts/annotate_evidence.py` only with imagery that the user may
   reproduce and annotate. Copy `assets/annotation-template.json` to start a
   plate manifest.
5. Run `scripts/validate_public_report.py` before sharing a public report or
   evidence plate.

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
answerability, public generalization, and the permission gate for exact
actionable research.
Use `$illustrate-historical-reconstruction` when the requested visual is a
generated interpretation of a past appearance. Keep its reconstruction art
separate from this skill's conservative source frames and annotated evidence
plates; generated pixels cannot corroborate the research used to prompt them.

## Establish the reporting contract

Before composing, determine from the case or state as assumptions:

- audience and decision: orientation, research triage, expert review, or
  authority disclosure;
- area precision: exact authorized AOI, generalized region, or genuinely
  unknown location;
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
validation gap; do not convert it into a probability.

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
7. Generalize the public location of a possible new or vulnerable site.

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

Do not message, submit, or disclose coordinates without the user's explicit
instruction and the authority rules in the core skill. A university lab can
help interpret data; it does not replace a heritage authority, land manager, or
community authority.

For exact treasure, hoard, weapon, precious-metal, burial, or portable-find
research, do not reject the topic. Publicly report a generalized prospective
assessment. Place exact maps, rankings, or field-method plans only in a
restricted or heritage-authority brief after jurisdictional, land, method,
heritage, reporting, environmental, and community permissions are confirmed.

## Completion gate

Before delivery, verify that:

- the chosen layout matches the user's decision;
- the opening gives a clear provisional judgment;
- source frames and derived views are distinguishable;
- every annotation is observational and traceable;
- assumptions, alternatives, counter-evidence, and unknowns remain visible;
- the report says where and what to look for next;
- missing sources are requested specifically;
- sensitive locations are generalized in public material;
- referrals are jurisdiction-specific, current, role-appropriate, and unsent;
- known finds and prospective hypotheses are distinct; object, context,
  assemblage, production, and custody claims are not conflated;
- public high-value locations are generalized, and exact actionable material
  is restricted and permission-bound;
- the professor voice clarifies the archaeology without theatrical imitation,
  catchphrases, colonial collection framing, or inflated certainty.
