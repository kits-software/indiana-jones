# Research Sequence Graph contract

## What the artefact represents

`search-plan.json` contains:

- a resolved case and nested AOI;
- a hierarchical/adaptive spatial grid;
- a source register with origin lineages;
- a landscape-evidence graph;
- a task/search DAG;
- scheduling and stopping policy.

It does not assert site probability. It does not become a Harris Matrix merely
because some edges express historical order.

## Top-level shape

```json
{
  "schemaVersion": "2.0",
  "case": {},
  "area": {},
  "grid": {"cells": []},
  "sources": [],
  "nodes": [],
  "edges": [],
  "actions": [],
  "policy": {}
}
```

Schema `1.0` remains readable for planning and export. Migrate it before
execution; legacy `completed` actions become non-unlocking
`completed-unverified` actions until evidence is resealed.

Start from `assets/search-plan-template.json` for a worked city/landscape
example or `assets/event-search-plan-template.json` for a disputed historical
event with competing loci. Use `scripts/search_plan.py new` only for a coarse WGS84
reconnaissance grid. Replace or refine it with a suitable projected,
landscape-unit, or externally prepared equal-area grid before metre-scale
analysis.

## Case and area

Required case fields:

- `caseId`, `question`, and `intendedDecision`;
- `studyKind`: `prospective-survey`, `known-site-rediscovery`, or
  `historical-reconstruction`;
- `targetLabelsState` and `candidatesFrozen`;
- `disclosure`;
- explicit authorization state.

Exact sensitive or treasure-oriented research also records
`researchMode: treasure-research-restricted` or `authority-casework` and a
permission bundle for jurisdiction, land access, detecting, excavation,
heritage, and finds reporting. Each entry declares `confirmed` or
`not-required` plus its basis. Public and generalized treasure research does
not require those field permissions.

`area.gazetteerCandidates` preserves all credible intake-region resolutions and
`selectedGazetteerId` must select exactly one anchor region. It does not select
the winning event/site locus: represent disputed loci as separate spatial and
hypothesis nodes linked to cells. Keep a restricted geometry and a separate
public description. `metricPlanning: true` requires a suitable
projected CRS; EPSG:4326 degree cells are not metre-scale units.

Each grid cell records a stable ID, level/parent, restricted geometry, safe
public label, evidenced neighbors, landscape context, coverage, access, and
sensitivity.

## Sources and origin families

Every source has:

- `sourceId`, title, stable locator where safe, and access basis;
- rights/licence and sensitivity;
- `workflowRole`;
- `recordType` and `accessStage`;
- `targetLabelState`;
- `originFamilyId`.

Ten pages quoting one chronicle still contribute one evidential lineage.
Likewise, a derivative map and its source inventory are not independent.

Never store API keys, bearer tokens, passwords, signed URLs, or account cookies
in the plan. The validator rejects common secret-bearing URL keys.

## Evidence nodes

Supported kinds:

```text
phase event process social-context spatial-feature claim observation
hypothesis material-expectation proxy test result candidate decision
excavation-context object find-event assemblage collection repository
analysis custody-event production-evidence person-or-organization
catalogue-record publication-record source-snapshot
```

Every node declares:

- `authority`: `observed`, `reported`, `derived`, `inferred`, `hypothesis`, or
  `corroborated`;
- source and cell IDs;
- spatial/temporal uncertainty when relevant;
- sensitivity and notes.

Observed, reported, derived, inferred, and corroborated nodes require source
provenance. A hypothesis also declares `hypothesisClass`:
`archaeological`, `natural`, `modern`, `processing`, or `null`.

Do not silently promote authority. A result creates a new immutable node and a
decision/update edge; it does not overwrite the earlier hypothesis.

## Edge families and cycles

Evidence/derivation:

```text
reports measures derived-from supports weakens contradicts corroborates
alternative-to same-origin-as motivates implies-process may-produce
observable-as tested-by produces updates
```

Historical/spatial:

```text
historically-precedes may-precede overlaps-in-time part-of route-connects
hydrologically-connects visible-from located-at possibly-located-at
```

Object, find, analysis, and custody:

```text
found-at recovered-during recovered-in member-of member-of-assemblage
made-of typed-as dated-to dated-by analysed-by supports-production-of
held-by repository-of has-custody-event custody-before
custody-transferred-to same-object-as possibly-same-as catalogued-as
published-as reported-by
```

Archaeological provenience, collection custody, and source/evidence lineage
remain distinct. Similar labels or nearby reported findspots cannot alone
create a `same-object-as` edge.

`historically-precedes`, `derived-from`, and
`stratigraphically-precedes` are independently acyclic. Uncertain overlap does
not create an ordering edge.

`stratigraphically-precedes` and `same-once-whole` are reserved for
`excavation-context` nodes. They require `observed-stratigraphy`, source IDs,
and a context-record locator. Map chronology, remote sensing, architectural
style, or a historical inference cannot satisfy that contract.

## Actions and hard gates

Actions record:

- stable ID, label, lane, stage, cells, hypotheses, and sources;
- an allowlisted non-invasive `method` and compatible `actionClass`;
- prerequisites and status;
- an `execution` contract containing an allowlisted executor, typed inputs,
  named outputs, acceptance criteria, timeout, and attempt limit;
- authorization requirement/state;
- whether candidate labels must be frozen;
- whether the action is candidate-focused and its paired control;
- eight normalized ordinal planning inputs.

Allowed lanes:

- `discrimination`;
- `negative-control`;
- `coverage`;
- `corroboration`.

Allowed authorization requirements:

- `none`;
- `user-account`;
- `external-approval`;
- `community-governance`.

Only `not-required` or `confirmed`, as appropriate, can enter the frontier.
Legal access, licence, consent, community control, and disclosure are gates,
not score penalties.

`public-desk`, `licensed-computation`, `authenticated-read`,
`community-consultation`, `field-non-invasive`, and `specialist-handoff` have
different method and authorization contracts. Intrusive field methods are
outside this planner. Confirmed field or community work requires case-level
authorization and recorded approval references; pending actions remain valid
but blocked.

Runtime completion additionally requires a hash-bound result reference. A
linked result node can describe evidence in a static plan, but only a sealed
runtime result unlocks a runtime dependency. Editing `status` is never an
execution transition.

Candidate-focused actions require a ready negative-control action plus natural
or modern and processing alternatives. A null hypothesis is strongly expected.

## Ordinal scheduling score

The dependency-light fallback uses:

```text
benefit =
    0.50 * discrimination
  + 0.25 * falsification
  + 0.15 * independence
  + 0.10 * coverage

burden = weighted mean(compute, humanReview, delay, money)
priority = benefit / (1 + burden)
```

All inputs and weights remain visible and versioned. They are planning
judgments between 0 and 1, not calibrated archaeological probabilities.

Use these anchors consistently:

| Value | Benefit dimensions | Burden dimensions |
| --- | --- | --- |
| `0.00` | none or irrelevant | negligible |
| `0.25` | weak/indirect | low |
| `0.50` | useful but incomplete | moderate |
| `0.75` | strong and independently useful | high |
| `1.00` | maximally discriminating/covering for this plan | plan-limiting |

Write one sentence of rationale for each nontrivial value. Compare scores only
inside the same versioned plan and question.

The scheduler operates only on ready actions and cycles through:

```text
discrimination -> negative-control -> discrimination -> coverage
```

Candidate-focused work reserves its paired control in the same batch.
Deterministic sorting uses priority, cell ID, and action ID.

## Commands

Initialize:

```bash
python3 scripts/search_plan.py new \
  --place "Resolved place" \
  --gazetteer-id "AUTHORITY:ID" \
  --question "Which process should we test?" \
  --bbox WEST SOUTH EAST NORTH \
  --rows 3 --columns 3 \
  --out search-plan.json
```

Validate structure:

```bash
python3 scripts/search_plan.py validate --plan search-plan.json
```

Validate research readiness:

```bash
python3 scripts/search_plan.py validate --ready --plan search-plan.json
```

A skeleton may be structurally valid while not ready. Readiness requires
sources, archaeological/natural-or-modern/processing/null hypotheses,
name-resolution and source-coverage actions, discrimination and coverage
lanes, and a negative-control lane for candidate-focused work. A frozen
candidate state also requires its SHA-256, and at least one action must pass
the dependency and authorization gates into the current frontier.

Rank the next batch:

```bash
python3 scripts/search_plan.py rank \
  --plan search-plan.json \
  --limit 4 \
  --out search-frontier.json
```

The frontier includes the source-plan hash, score components, selected batch,
ready-but-unscheduled actions, executable contracts, and blocked actions with
reasons. Ranking enforces research readiness by default.

Create and advance a finite replayable run:

```bash
python3 scripts/search_plan.py init-run \
  --plan search-plan.json \
  --run-dir case-run \
  --max-actions 40 \
  --max-attempts 80 \
  --max-result-bytes 100000000 \
  --max-seconds 86400

python3 scripts/search_plan.py next --run-dir case-run --limit 4
python3 scripts/search_plan.py start-action \
  --run-dir case-run --action-id <ACTION_ID>
python3 scripts/search_plan.py complete-action \
  --run-dir case-run \
  --action-id <ACTION_ID> \
  --attempt-id <ATTEMPT_ID> \
  --result result.json \
  --summary "Evidence judgment" \
  --source-id <SOURCE_ID>
```

Use `fail-action`, `resume`, `status`, `stop`, and deterministic `run-action`
as appropriate. `events.jsonl` is append-only, hash-chained authority;
`state.json` is a replayed cache. Finite action, attempt, byte, and wall-time
budgets are reconstructed from the journal after interruption.

Before unblinding, use `freeze-candidates`. Use `ingest-source` and
`reconcile-finds` for bounded provider-neutral catalogue imports and
conservative identity reconciliation. Use the `report-*` commands for history,
finds, object, material, and source-gap artefacts. `assess-probability` refuses
numeric output until the calibration and, for exact sensitive targets,
permission gates pass.

Export a separate public copy:

```bash
python3 scripts/search_plan.py export-public \
  --plan search-plan.json \
  --out search-plan.public.json
```

Public export constructs a new allowlisted schema with remapped IDs. It never
copies original area/cell geometry, locators, coordinates, sensitive labels,
cell links, arbitrary nested fields, local paths, or non-public URLs. It is not
a proof of safe disclosure; manually test whether the declared public area
description, public source titles, graph structure, imagery, or landmarks can
re-identify a location.

All output commands create new files and refuse to overwrite existing
artefacts, including the source plan.

## Update and stopping rules

After a batch:

1. preserve the old plan and frontier hashes;
2. add result/observation nodes;
3. add explicit support, weakness, contradiction, or update edges;
4. mark completed actions and coverage;
5. add new source gaps and alternatives;
6. regenerate the ready frontier.

Pause or stop for unresolved place ambiguity, lack of lawful/licensed sources,
method inadequacy, a stronger alternative, bounded desk-study sufficiency,
budget, graph invalidity, sensitivity escalation, or a test that belongs to a
qualified specialist, heritage authority, land manager, or community.

Non-detection must be phrased as “not visible under these sources and
conditions,” never “absent.”
