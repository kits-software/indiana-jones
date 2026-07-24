# Archaeological report layouts

## Contents

1. Layout selector
2. Shared evidence plate
3. Broad-area reconnaissance brief
4. Candidate atlas
5. Single-candidate dossier
6. Source-gap teaching note
7. Negative-result report
8. Restricted authority brief
9. Known-finds register
10. Object or assemblage biography
11. History-through-time and material-evidence report
12. Documented and prospective distribution report
13. Permission-gated prospectivity brief
14. Methods and provenance appendix

## Layout selector

| User need | Primary layout | Required visual |
| --- | --- | --- |
| “Where should we look?” with a broad area | Broad-area reconnaissance | Regional context or search-window diagram |
| Several possible anomalies | Candidate atlas | One source-backed plate per advanced candidate |
| One location or feature | Single-candidate dossier | Source frame plus derived comparison |
| Only a screenshot, story, or vague description | Source-gap teaching note | Supplied reference, if lawful, clearly limited |
| No candidates or all rejected | Negative-result report | Coverage/quality view and representative controls |
| Possible new or sensitive site | Restricted authority brief | Restricted plate; no public locator |
| “Were swords, gold, coins, or hoards found nearby?” | Known-finds register | Safe generalized context map or record-coverage view |
| “What happened to this object or collection?” | Object or assemblage biography | Event timeline and identity/custody links |
| Place history plus finds, craft, or trade | History-through-time and material-evidence report | Phase timeline with evidence lanes |
| Compare known finds or prospective areas | Documented and prospective distribution report | Separate generalized record and hypothesis maps |
| Exact prospective work with confirmed permissions | Permission-gated prospectivity brief | Restricted map; generalized public derivative |
| Reproducibility or peer review | Methods appendix | Source and derived artifact index |

Combine layouts only when the audience needs both. Put the decision-facing
summary first and the methods appendix last.

## Shared evidence plate

Every imagery-backed candidate plate should contain:

1. **Title and candidate ID** — stable ID, not a sensational site name.
2. **Source frame** — unwarped or clearly declared export from an authorized
   image product.
3. **Numbered annotations** — outlines or pointers tied to observations.
4. **Legend** — one observation per number; interpretations remain outside the
   image or visibly marked as hypotheses.
5. **Source strip** — provider, product/sensor, date, native resolution, CRS or
   orientation, processing, licence/attribution, and source role.
6. **Disclosure strip** — public, restricted, or authority-only.
7. **Claim boundary** — “candidate, not confirmed” plus the principal unknown.

When processing changes the visible evidence, use a paired layout:

```text
┌──────────────────────────────┬──────────────────────────────┐
│ A. Conservative source view  │ B. Annotated derivative      │
│ identical crop and scale     │ numbered observations        │
├──────────────────────────────┴──────────────────────────────┤
│ source/date/resolution • processing • disclosure • caveat  │
└─────────────────────────────────────────────────────────────┘
```

Do not present a heatmap, hillshade, index, or model mask as if it were the
satellite or aerial photograph.

If only a derived view is available, use the same paired layout but title panel
A “conservative derived view.” State the missing source measurement in the
caption and source request; do not silently promote the derivative to source.

### Annotation grammar

Use:

- solid outline for an observed boundary or tonal/spectral region;
- dashed outline for an approximate or obscured continuation;
- arrow for a local comparison or confounder;
- shaded polygon only when it does not hide the source pixels;
- labels such as “tonal arc,” “low-relief bank,” “linear drainage parallel,”
  or “possible seam.”

Do not write “temple,” “fort,” “road,” or another site class inside the frame
unless an authoritative record independently identifies it.

## Broad-area reconnaissance brief

Use when the user supplies a large region, colloquial place, uncertain
boundary, or no exact AOI.

### Opening

- State how the place was interpreted.
- Give the spatial uncertainty and any assumed boundary.
- State the first-pass decision: which subareas deserve imagery review and why.

### Search-window table

| Window | Landscape basis | Expected proxy | Best source/time | Main confounder | Priority |
| --- | --- | --- | --- | --- | --- |

Base windows on visibility and preservation: terraces, floodplain margins,
plateau edges, palaeochannels, woodland with LiDAR, drought-stressed arable
fields, historic route corridors, or construction-threat zones. Do not rank a
window because its name or folklore sounds promising.

### What to look for

For each high-priority window state:

- morphology and approximate scale;
- polarity or spectral/relief signature;
- useful season, sun angle, water state, or crop stage;
- minimum ground sampling distance;
- modern/natural comparison layers;
- evidence that would reject the interpretation.

### Output

If evidence was actually inspected, attach source-backed candidate plates.
Otherwise return a reconnaissance plan and minimum source request. Do not
manufacture candidate dots on a regional map.

## Candidate atlas

Use for two or more inspected candidates.

### Executive field note

- provisional ranking and the reason;
- total area/dates/images searched;
- number generated, reviewed, advanced, and rejected;
- most important coverage or source limitation;
- disclosure and coordinate handling.

### Candidate register

| Rank | Candidate ID | E-grade | Observed proxy | Strongest alternative | Corroboration | Next action |
| --- | --- | --- | --- | --- | --- | --- |

Use “not ranked” when candidates came from incomparable sources or methods.

### Candidate section

For each advanced candidate include:

1. evidence plate;
2. observed;
3. derived;
4. working interpretation;
5. at least two alternatives and discriminating tests;
6. independent corroboration and counter-evidence;
7. positional/resolution/coverage uncertainty;
8. grade with reasons and validation gap;
9. one non-invasive next action.

Add a rejection gallery for instructive false positives. Showing why drains,
field edges, geology, tree throws, shadows, and seams failed is part of the
method, not clutter.

## Single-candidate dossier

Use this order:

### Provisional judgment

One paragraph: advance, hold, or reject; grade; decisive reason; principal
unknown.

### Evidence plate

Include the conservative source frame and any declared derived comparison.

### Observation ledger

| Item | Observation | Source/date | Scale or resolution | Limitation |
| --- | --- | --- | --- | --- |

### Interpretation tree

```text
observed proxy
├─ archaeological working hypothesis
│  └─ expected independent signature
├─ modern land-use explanation
│  └─ map/date check
└─ natural or processing explanation
   └─ geology/raw-product check
```

### Chronology and context

Separate datable evidence from typological resemblance. Shape alone rarely
dates a feature.

### Next discriminating test

Name the cheapest lawful test that most changes the conclusion: another date,
rawer product, LiDAR, historic mapping, geophysics, expert desk review, or
authorized non-invasive survey.

### Referral

Name a role or verified institution only when it can perform the next test or
holds authority for the place.

## Source-gap teaching note

Use when sources are missing, weak, or unsuitable.

### What can be said now

State the maximum claim supported by the supplied material.

### What to inspect

Teach:

- the expected physical proxy;
- where in the landscape it is most visible;
- which season/date/modality is useful;
- which look-alikes to compare;
- what non-detection would and would not mean.

### Minimum useful source package

Request only what changes the assessment:

- original file or stable source/item URL;
- approximate AOI or generalized place;
- acquisition date and provider/product;
- scale, pixel size, or map sheet;
- unedited source view plus any derived version;
- licence or user's permission to analyze and reproduce;
- relevant known records, if this is not a blind benchmark.

### Working hypothesis

If a bounded guess is useful, list the assumption, reason, falsifier, and
cheapest discriminating source. Otherwise state “no determination.”

## Negative-result report

Do not write “nothing is there.” Report:

- area, dates, modalities, and usable coverage searched;
- visibility opportunity and quality failures;
- detector/review rule and threshold sensitivity;
- number and classes of rejected anomalies;
- hard-negative examples;
- whether the result is “not visible under these conditions,” “method did not
  detect,” or “candidate rejected”;
- a different source or condition that could still change the result.

Include a coverage plate or representative negative controls when possible.

## Restricted authority brief

Keep it concise and neutral:

1. handling banner and intended recipient role;
2. reason for referral and urgency;
3. generalized public location;
4. precise locator only in the authorized restricted enclosure;
5. source and acquisition provenance;
6. conservative source plate and annotations;
7. observed/derived/inferred separation;
8. alternatives already checked;
9. sensitivity, community, land-status, and threat considerations;
10. requested action, such as confidential desk review;
11. sender-controlled contact draft, never automatically submitted.

Do not place precise coordinates in filenames, public manifests, image labels,
or email subjects.

## Known-finds register

Use for documented swords, weapons, coins, gold objects, hoards, grave goods,
tools, production debris, or other material associated with a safely stated
area.

### Opening

- define “near,” area, period, terminology, and source coverage;
- distinguish documented finds from prospective hypotheses;
- state answerability and the strongest material limitation;
- state public location generalization and suppression rules.

### Register

| Find ID | Object/assemblage | Material basis | Date basis | Context quality | Safe place association | Repository/ID | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |

Follow each record with:

- source and origin family;
- object identity and duplicate-link status;
- find event and context, if documented;
- classification, material, and chronology bases;
- present custody verification or gap;
- contradictory records and what would resolve them.

Do not count catalogue mirrors or papers repeating one excavation as
independent finds. State “not located in searched sources,” never “none
exist,” when coverage is incomplete.

## Object or assemblage biography

Keep the archaeological and record/custody sequences separate:

```text
manufacture → use/reuse → deposition → recovery

reporting → publication → accession → conservation/analysis
→ transfer/loan/repatriation → current custody
```

For every event show:

- bounded date and basis;
- object, assemblage, context, repository, or custody entity involved;
- source and origin family;
- certainty and contradiction;
- sensitive or private information withheld.

Include an identity reconciliation table when several accession, excavation,
publication, or legacy collection records may describe the same object. Do not
fill a missing custody interval with a plausible story.

## History-through-time and material-evidence report

Use for “what happened here?” when objects, production, trade, or excavation
history must join documentary and landscape evidence.

### Phase table

| Phase | Directly attested | Object/find evidence | Production evidence | Exchange/use hypothesis | Conflict or gap |
| --- | --- | --- | --- | --- | --- |

Explain transitions and changes in evidence opportunity. Separate:

- gold objects from gold-working;
- documentary goldsmithing from an excavated workshop;
- weapons from battle, armoury, production, or route interpretations;
- find date from deposition date;
- archaeological change from excavation, collecting, reporting, or
  digitization bias.

End each phase with the cheapest lawful source or test that could discriminate
the principal alternatives.

## Documented and prospective distribution report

Never combine known-find density and prospectivity in one unlabeled surface.
Use paired panels:

```text
┌──────────────────────────────┬──────────────────────────────┐
│ A. Documented-record pattern │ B. Prospective hypothesis    │
│ coverage and reporting bias  │ assumptions and controls     │
├──────────────────────────────┴──────────────────────────────┤
│ generalized unit • suppression • permissions • caveat       │
└─────────────────────────────────────────────────────────────┘
```

Panel A must state source coverage, duplicate handling, investigation
opportunity, and why record density is not past abundance. Panel B must state
expected context, preservation and detection opportunity, alternatives,
negative controls, validation method, and why the model is not a guarantee.

Public panels use broad units and low-count suppression. Do not provide filters
or combinations that reconstruct protected points. Exact professional layers
belong only in the permission-gated restricted brief.

## Permission-gated prospectivity brief

Use exact or actionable treasure, hoard, sword, precious-metal, burial, or
portable-find planning only when the case records:

- exact jurisdiction and relevant current law or official guidance;
- landholder authorization and geographic scope;
- detecting, survey, diving, excavation, export, and finds-reporting
  permissions as applicable;
- protected-site, environmental, aviation, and community authority;
- responsible professional and receiving heritage authority;
- allowed method, time window, data handling, stopping, discovery, and
  emergency procedures;
- restricted recipients and a generalized public derivative.

Structure:

1. permission and authority matrix;
2. precise research question and bounded area;
3. documented evidence and source coverage;
4. prospective model, alternatives, negative controls, and calibration status;
5. ranked tests, not promises of recovery;
6. field action, stop-work, reporting, custody, and conservation gates;
7. restricted exact map;
8. public generalized summary;
9. unresolved permission or evidence blockers.

If any required permission is absent or ambiguous, mark the corresponding
exact action `blocked` and continue with generalized research. Do not refuse
the treasure topic itself.

## Methods and provenance appendix

Include:

- research question, decision rule, falsifier, and interpretive prior;
- source register with roles, licences, dates, CRS, resolution, and hashes;
- processing and visualization decision log;
- candidate-generation parameters and software versions;
- denominator and validation metrics, if applicable;
- rejected alternatives and negative controls;
- object, find-event, context, assemblage, accession, identity-link, and
  custody records when applicable;
- documented-versus-prospective separation, permission matrix, and public
  generalization rule;
- artifact register with source, annotation, rendered-output, and report hashes;
- disclosure/redaction log;
- unresolved evidence and next responsible reviewer.
