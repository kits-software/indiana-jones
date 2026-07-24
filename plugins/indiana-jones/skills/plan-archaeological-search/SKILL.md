---
name: plan-archaeological-search
description: Turn curiosity about a place into an ordered path toward discovery. Use when the user asks where an old castle or settlement may have stood, where swords, gold, hoards, or treasure-related evidence may plausibly occur, what may be hidden around an area, how people used or built a landscape, where an event happened, which explanation is most likely, or where to look next. Resolve place and time, make competing hypotheses explicit, plan exact desk-research candidates and rankings, choose informative lawful checks, and keep field action, private data, and genuinely protected-site disclosure behind their applicable gates.
---

# Plan Archaeological Search

Turn “look around this place” into a defensible sequence of questions and
non-invasive tests. Think across archaeology, history, historical geography,
geoarchaeology, urban morphology, architecture, anthropology, sociology,
toponymy, environmental science, and remote sensing without blurring their
different authorities.

Use the core `$indiana-jones` skill once the plan reaches licensed imagery,
terrain, candidate generation, or evidence grading. Use
`$report-archaeological-evidence` for the user-facing reconnaissance brief,
atlas, source request, or specialist referral. Use
`$research-archaeological-history-and-finds` for documented or prospective
objects, assemblages, swords, treasure, gold, production, repositories, and
custody histories. Use `$illustrate-historical-reconstruction` after the
place, phase, and visible evidence are stable when the user wants a generated
city, settlement, landscape, building, object, or person reconstruction.

## Non-negotiable boundaries

- A point or place name is an intake clue, not a study area. Resolve it to an
  explicit gazetteer record and preserve rejected matches.
- Keep a landscape-evidence graph, a search/task graph, and any genuine
  stratigraphic graph separate.
- Call a relation stratigraphic only when identified physical contexts and
  excavation or standing-building records demonstrate it. Documentary
  chronology, overlapping maps, architectural style, and imagery anomalies do
  not create a Harris Matrix.
- Treat historical narrative as a source of testable hypotheses, not a map of
  where artefacts “must” be.
- Do not equate an archaeological culture or material tradition with a
  homogeneous ethnicity, language, polity, modern nation, or living community.
- Planning priority is a scheduling score, never the probability of a site.
- Source licences and authenticated/private-account consent are hard desk-
  research gates. Land access, permits, and field authority apply only to field
  actions; genuine protected-site and community restrictions control disclosure.
- Known-site coordinates and inventory labels stay withheld during prospective
  candidate generation and rediscovery benchmarks.
- Never turn the plan into directions for trespass, destructive collection or
  removal, probing, unpermitted detecting or excavation, grave disturbance, or
  triangulation of a genuinely protected or deliberately redacted site.

## Route the request

1. **Any named place, point, polygon, city, or broad area**: follow the complete
   workflow below and read [source-routing.md](references/source-routing.md).
2. **Settlement or city growth**: also read the urban sections of
   [multidisciplinary-planning.md](references/multidisciplinary-planning.md).
3. **Battle, migration, disaster, route, industrial episode, or other event**:
   use the event reconstruction route in that reference. Reconstruct period
   terrain rather than applying modern conditions backward.
4. **Culture, community, oral history, place-name, or local story**: use the
   social/identity and community-governance boundaries in both references.
5. **A machine-readable plan or next-action queue**: read
   [graph-contract.md](references/graph-contract.md), copy the city/landscape
   `assets/search-plan-template.json` or disputed-event
   `assets/event-search-plan-template.json`, and use `scripts/search_plan.py`.

## 1. Contract the investigation

Record:

- the exact question, intended decision, and what “interesting” would mean;
- `prospective-survey`, `known-site-rediscovery`, or
  `historical-reconstruction`;
- the supplied point/name and its spatial uncertainty;
- periods, events, activities, material expectations, and exclusions;
- permitted public, licensed, local, or explicitly authorized account sources;
- coordinate precision and `public`, `restricted`, or
  `heritage-authority-only` disclosure;
- whether the deliverable should include exact candidate coordinates, ranked
  cells, annotated satellite/aerial plates, and heuristic or calibrated estimates;
- available time, compute, money, specialist review, and stopping rules;
- what would falsify or materially weaken each leading hypothesis.

Do not reduce the question to “find a castle.” Possible outcomes include an
older settlement core, route or crossing, production zone, abandoned margin,
waterfront, field system, conflict landscape, rebuilding episode, changed
hydrology, later reuse, documentary correction, or an evidence-backed negative
result.

## 2. Resolve place and names

Build a name concordance before spatial search:

- current official and local-script names;
- transliterations, historic forms, exonyms, and spelling/OCR variants;
- former administrative, parish, estate, river, tribal, military, or colonial
  jurisdictions;
- feature type, applicable date range, source ID, coordinate uncertainty, and
  selected gazetteer identifier.

If plausible matches remain geographically distinct, stop spatial planning and
ask the user to choose. Do not silently select the most famous match.

Toponyms can generate leads about terrain, ownership, occupation, route,
religious dedication, vegetation, or hydrology, but folk etymology and name
transfer are strong alternatives. A suggestive name is not site evidence.

## 3. Define nested areas and an adaptive grid

Define three linked areas:

1. `focus`: the named place or uncertainty envelope;
2. `context`: the relevant catchment, route network, viewshed, shoreline,
   resource zone, settlement hinterland, or event extent;
3. `controls`: comparable terrain outside narrative hotspots and known-site
   clusters.

Start cells no finer than the coarsest useful source. Prefer landscape units,
historic plan units, blocks/plots, catchments, route segments, land parcels, or
visibility zones over an arbitrary uniform grid. A WGS84 degree grid is only a
coarse reconnaissance index; use a suitable projected or equal-area grid for
metre-scale measurement, splitting large or cross-zone studies as needed.

Connect cells by explicit evidence: adjacency, route, hydrology, visibility,
historic plan unit, phase, common source uncertainty, or shared hypothesis.
Never invent a route or viewshed edge from proximity alone. Subdivide a cell
only when new evidence supports a finer decision, and refine a predeclared
sample of negative cells as well as positive ones.

## 4. Reconstruct time slices

Treat the landscape as layered and dynamic. For every defensible phase record:

- terrain, geology, soils, hydrology, shoreline, sedimentation, and
  palaeotopography;
- routes, crossings, gates, plots, fields, tenure, and administrative limits;
- cores, planned additions, polycentric growth, contraction, relocation,
  destruction, rebuilding, reuse, and abandonment;
- production, exchange, water supply, waste, governance, ritual, burial, and
  marginal zones;
- institutions, labor, inequality, exclusion, migration, memory, contested
  meaning, and community-held knowledge;
- modern fill, truncation, quarrying, drainage, utilities, forestry,
  agriculture, and development;
- preservation depth and whether any proposed sensor could observe the proxy.

Do not assume cities grow monotonically outward. Maintain competing models such
as planned foundation, route- or waterfront-led growth, polycentric expansion,
contraction/reoccupation, hydrological relocation, imposed replanning, and
modern cadastral artefact.

## 5. Turn stories into testable chains

For every archival claim, historical event, cultural association, or local
story, build this chain:

```text
source claim
  -> motivates hypothesis
  -> implies activity or formation process
  -> may produce material expectation
  -> may survive as observable proxy
  -> is tested by a licensed, non-invasive method
  -> is applied to focus and control cells
  -> produces an observation
  -> supports, weakens, or contradicts a hypothesis
```

Create a hypothesis card with date/spatial uncertainty, suitability mechanism,
expected material, formation and survival process, proxy scale, modality,
strongest natural/modern/processing alternatives, discriminating test,
falsifier, sensitivity, and required authority.

For conflict or another moving event, extract source-linked defining features
and reconstruct period routes, crossings, obstacles, cover, observation,
mobility, supply, camps, hospitals, retreat, destruction, and burial zones.
Terrain plausibility helps discriminate narratives; it does not prove an
account. Burial and conflict-dead locations are sensitive by default.

## 6. Build the three graph layers

### Landscape-evidence graph

Represent places, phases, events, processes, social contexts, source claims,
material expectations, proxies, observations, candidates, alternatives, and
decisions. Every assertion keeps source IDs, origin family, authority,
temporal/spatial uncertainty, rationale, sensitivity, and revision history.

### Search/task graph

Represent non-invasive actions and prerequisites across cells. Keep separate
lanes for:

- `discrimination`: distinguish live hypotheses;
- `negative-control`: test confounders and false positives;
- `coverage`: prevent famous stories or exciting cells from consuming the
  survey;
- `corroboration`: inspect withheld inventories or seek expert review after the
  appropriate freeze.

### Stratigraphic graph

Create this only for actual physical contexts. Orient direct relative sequence
consistently; cite the context record and plan/section. The research and task
graphs may borrow the discipline of explicit ordering, but they are not a
Harris Matrix.

## 7. Research in independent lanes

Use [source-routing.md](references/source-routing.md) to search in parallel:

- competent heritage and community authorities;
- historic maps, aerials, cadasters, plans, and imagery;
- gazetteers, toponyms, archives, censuses, newspapers, and local histories;
- geology, soils, terrain, hydrology, palaeoenvironment, and disturbance;
- academic literature, reports, repositories, and bibliographies;
- modern context from OpenStreetMap and other lawful sources;
- oral/community knowledge only through consented, governed engagement.

Maintain both a source ledger and a claim ledger. Pages that repeat one account
share one `originFamilyId`; repetition is not independent corroboration. Record
unconsulted and unproductive sources and what their absence means.

## 8. Order the next search batch

Copy the template or initialize a coarse plan:

```bash
python3 <skill-dir>/scripts/search_plan.py new \
  --place "Resolved local name" \
  --gazetteer-id "<AUTHORITY:ID>" \
  --question "Which process best explains the settlement pattern?" \
  --bbox <WEST> <SOUTH> <EAST> <NORTH> \
  --rows 3 \
  --columns 3 \
  --disclosure public \
  --out search-plan.json
```

`new` emits a schema-2 coarse reconnaissance skeleton. It deliberately cannot
invent source authority, hypotheses, controls, or acceptance evidence. Author
those fields against [graph-contract.md](references/graph-contract.md), or use
the schema-2 city/landscape and event assets as worked shapes after replacing
every example identity, source, area, and claim.

After adding sources, typed entity nodes, edges, and executable actions, apply
the bounded package and require readiness:

```bash
python3 <skill-dir>/scripts/search_plan.py prepare \
  --plan search-plan.json \
  --package research-package.json \
  --out search-plan.ready.json

python3 <skill-dir>/scripts/search_plan.py validate \
  --ready \
  --plan search-plan.ready.json

python3 <skill-dir>/scripts/search_plan.py rank \
  --plan search-plan.ready.json \
  --limit 4 \
  --out search-frontier.json
```

`prepare` accepts only `archaeological-research-package-1.0`, rejects unknown
fields, and refuses to write a plan that is not schema-valid and ready.
Structural validation and research readiness are separate. A new empty
skeleton is structurally valid but fails `validate --ready` until it contains
sources, archaeological and alternative hypotheses, coverage, controls where
needed, and executable research actions.

The ordinal planner combines discrimination, falsification, independence,
coverage, and burden. It schedules only ready, typed non-invasive actions,
pairs candidate-focused work with a matched negative control, preserves
dependency order, and prints every score component. Case authorization, source
access stage, licence, applicable private-source consent, and genuine
protected-site disclosure remain hard gates. Field permissions do not gate
desk research or its exact coordinate, ranking, plate, or estimate outputs.

## 9. Execute as an auditable graph search

Migrate a legacy plan non-destructively before execution:

```bash
python3 <skill-dir>/scripts/search_plan.py migrate \
  --plan legacy-plan.json \
  --out-dir migrated-case
```

Every planned action needs an `execution` object declaring its executor,
inputs, outputs, acceptance criteria, timeout, and retry limit. Use
`codex-research` for agent-executed scholarly work, `ingest-source` for bounded
public catalogue ingestion, and `reconcile-records` for conservative
cross-source identity reconciliation.

Initialize a finite run only after `validate --ready` passes:

```bash
python3 <skill-dir>/scripts/search_plan.py init-run \
  --plan search-plan.json \
  --run-dir case-run \
  --max-actions 40 \
  --max-attempts 80 \
  --max-result-bytes 100000000 \
  --max-seconds 86400

python3 <skill-dir>/scripts/search_plan.py next \
  --run-dir case-run \
  --limit 4 \
  --out task-packet.json
```

For a `codex-research` task, lease it before using tools and seal the result
after preserving the evidence artefact:

```bash
python3 <skill-dir>/scripts/search_plan.py start-action \
  --run-dir case-run \
  --action-id <ACTION_ID> \
  --idempotency-key <CALLER_STABLE_KEY>

python3 <skill-dir>/scripts/search_plan.py complete-action \
  --run-dir case-run \
  --action-id <ACTION_ID> \
  --attempt-id <ATTEMPT_ID> \
  --result result.json \
  --summary "Bounded evidence judgment" \
  --source-id <SOURCE_ID>
```

The `result.json` must use `research-result-2.0` and include sourced
observations, negative results, warnings, errors, source snapshot and
normalized-record IDs, method/adapter versions, sensitivity, disclosure, and
one evidence item per acceptance criterion. Free-text criterion claims cannot
complete an action.

Use `fail-action --retryable` for a bounded retry. After interruption, use
`resume`; it refuses active leases and converts only expired attempts into
retryable or terminal states according to the action limit. Use `status` to replay and verify the
hash-chained event journal and all result hashes. Never edit runtime status to
simulate completion; dependencies unlock only from sealed result references.

For a deterministic public-source action, use `run-action`. Use `advance` for
one deterministic batch or `run` to repeat deterministic batches until a
`codex-research` task, private-source/protected-site gate, budget, or stop requires judgment.
Use `source-discover` to audit declared adapter readiness and `extract-claims`
to convert normalized fields into reviewable, source-linked assertions. To
ingest or reconcile data outside a run:

Before execution, bind each ingest action to the source's acquisition contract:
locator, format, source-identity hash, query hash, local snapshot hash and
retrieval date when applicable, or an explicit remote automation, retention,
version, and rate decision. The executor rechecks these bindings and the local
bytes so an arbitrary export cannot inherit another source's authority.

```bash
python3 <skill-dir>/scripts/search_plan.py search-ladder \
  --place-alias "<CURRENT_NAME>" \
  --place-alias "<HISTORICAL_NAME>" \
  --object-term "sword" \
  --language-variant "<LOCAL_TERM>" \
  --broader-term "weapon fitting" \
  --maximum 100 \
  --out search-ladder.json

python3 <skill-dir>/scripts/search_plan.py ingest-source \
  --plan search-plan.json \
  --source-id <SOURCE_ID> \
  --input <PUBLIC_URL_OR_LOCAL_EXPORT> \
  --format <json|jsonl|csv|oai-pmh|iiif|rdf-xml|sparql-json> \
  --out normalized-records.json

python3 <skill-dir>/scripts/search_plan.py reconcile-finds \
  --input normalized-records.json other-records.json \
  --out reconciled-finds.json
```

When an OAI-PMH response carries a resumption token, continue only through the
source's declared `resumePages` contract:

```bash
python3 <skill-dir>/scripts/search_plan.py resume-source \
  --plan search-plan.json \
  --source-id <SOURCE_ID> \
  --previous normalized-records.json \
  --out normalized-records.page-2.json
```

If the evidence can rank candidates but cannot support calibrated probability,
write a `heuristic-archaeological-assessment-input-1.0` file with the method,
score meaning, evidence references, assumptions, uncertainty, limitations, and
candidates, then run:

```bash
python3 <skill-dir>/scripts/search_plan.py assess-heuristic \
  --input candidate-evidence.json \
  --plan search-plan.json \
  --out heuristic-assessment.json
```

The result is explicitly `heuristic-ranking-not-probability`; probability
fields are rejected. Exact unrestricted coordinates, geometry, map links, and
imagery annotation references remain available, while a candidate carrying an
explicit spatial restriction is withheld independently of the others.

The direct ingestion and reconciliation commands above produce reviewable but
unsealed working artifacts. They cannot feed `report-finds`, `report-object`,
`report-material`, or `report-gaps`. For reportable evidence, declare
`ingest-source` and `reconcile-records` actions in the ready plan, execute them
with `run-action`, then pass only completed-action `resultRefs[].path` values
from `status` to the report commands together with the same `--run-dir`.

The journal is durable authority; `state.json` is a replayed cache. Each batch
must preserve negative results, proposed hypothesis changes, coverage, source
gaps, alternatives, and authorization evidence. Stop explicitly on
source-access failure, prohibited physical conduct, ambiguity, method
inadequacy, falsification, bounded sufficiency, budget, graph invalidity,
protected-site disclosure, or professional-boundary rules.

Before ground-truth or inventory unblinding, freeze a clean candidate artefact:

```bash
python3 <skill-dir>/scripts/search_plan.py freeze-candidates \
  --plan search-plan.json \
  --candidates candidates.json \
  --out-plan search-plan.frozen.json \
  --out-seal candidate-freeze.json
```

“No signal” means not observed with these sources and conditions. It does not
clear a cell or prove absence.

For a separate public artefact:

```bash
python3 <skill-dir>/scripts/search_plan.py export-public \
  --plan search-plan.json \
  --schema 2.0-public \
  --out search-plan.public.json
```

Use `1.0-public` for the legacy public shape and `2.0-public` when typed public
entity records are required. The export is rebuilt from a public allowlist. It
may preserve exact ordinary
candidate coordinates, ranked cells, and public evidence-plate links when
their sources support that precision. It excludes private locators, protected
or confidential geometry, sensitive labels, and non-public source URLs. It is
still only a bounded technical check; review real protection, source terms,
landmarks, graph intersections, and community restrictions manually.

## Completion gate

Do not call the plan ready until:

- the place identity and AOI hierarchy are explicit;
- time slices and at least one competing historical process are present;
- every archaeological hypothesis has natural/modern, processing, and null
  alternatives where relevant;
- each search window links a claim to process, material expectation, proxy,
  discriminating test, and control;
- source lineage prevents copied accounts from becoming false corroboration;
- the adaptive grid matches source resolution and landscape logic;
- task dependencies, applicable private/field permissions, licences, and genuine
  protected-site disclosure gates validate;
- known-site labels remain in their declared pre/post-freeze stage;
- stopping and professional-handoff rules are explicit;
- the first batch explains why each action is being run now.
