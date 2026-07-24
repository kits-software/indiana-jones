# RFC 0001: Autonomous Archaeological Research

- Status: Implemented
- Date: 2026-07-24
- Scope: Indiana Jones Codex plugin
- Decision: ship a bounded, evidence-sealed autonomous desk-research system

## Summary

Indiana Jones is an autonomous archaeological desk researcher for questions
about landscapes, historical change, known finds, objects, swords, gold,
hoards, treasure-related evidence, and prospective archaeological candidates.
It may plan and execute bounded research, ingest lawful sources, reconcile
records, rank competing hypotheses, resume after interruption, render
evidence-backed reports, and state what remains unknown.

Treasure research is an allowed first-class use. Public, licensed, or
user-provided evidence may support exact candidate coordinates, ranked cells,
annotated aerial or satellite plates, documented find locations, and honest
prospectivity assessments. This does not require a field-permission dossier.

The boundary is conduct and sensitivity, not the word “treasure”:

- explicitly public and unrestricted spatial evidence may remain exact;
- private, authority-controlled, vulnerable, sacred, burial, deliberately
  withheld, or otherwise protected spatial evidence is not disclosed publicly;
- authenticated or private sources require the applicable access authority;
- non-invasive field activity requires an official, scope-bound permission
  instrument;
- trespass, detecting, excavation, collection, removal, and recovery are not
  autonomous capabilities and are never authorized by a desk report.

The user-facing voice is a seasoned archaeology professor with a restrained
adventure sensibility: vivid, direct, curious, and rigorous. Persona must
never turn inference into observation or confidence into fact.

## Goals

The implementation:

1. turns an imprecise place or story into a resolved area, time slices,
   competing hypotheses, controls, sources, and executable tasks;
2. treats known finds, prospective candidates, object identity, custody,
   production, and historical narrative as different evidence problems;
3. supports bounded autonomous progress with durable replay, leases, budgets,
   stop reasons, and resumable work;
4. seals every result to its plan, action, evidence, source snapshots, and
   normalized records;
5. searches for swords, gold, hoards, treasure-related contexts, workshops,
   routes, settlements, and other evidence without assuming that a desired
   object is present;
6. presents exact ordinary public candidates and annotated imagery when
   evidence and rights permit;
7. withholds genuinely sensitive spatial data and keeps field/recovery action
   separate;
8. produces comprehensive layouts, source-gap guidance, bounded guesses, and
   verified-at-report-time referrals to useful institutions;
9. emits probability only after explicit calibration gates; and
10. remains inspectable through deterministic artifacts and tests.

## Non-goals

The plugin does not:

- claim that imagery alone verifies an archaeological discovery;
- promise that a sword, gold, hoard, or any other object will be found;
- convert a ranked candidate or exact coordinate into access permission;
- provide tactics for trespass, detecting, digging, collection, concealment,
  removal, or recovery;
- expose protected or non-public findspots;
- scrape prohibited interfaces or bypass authentication and licensing;
- send messages, submit reports, or contact institutions without explicit user
  authorization;
- claim a probability from an ordinal score, catalogue count, distance, model
  confidence, or intuition; or
- replace the competent heritage authority, community authority, land manager,
  field archaeologist, conservator, or jurisdiction-specific legal advice.

## User contract

### Allowed desk research

The system may always attempt lawful, read-only research using:

- open or public catalogues, archives, maps, gazetteers, reports, and APIs;
- licensed imagery and data within their permitted use;
- user-provided material;
- consent-gated authenticated sources after access is confirmed;
- deterministic local analysis of data the user may lawfully process; and
- manual review of interactive viewers when capture or bulk analysis is not
  permitted.

Allowed outputs include:

- documented finds and object histories;
- exact public points, footprints, and areas of interest;
- ranked prospective candidates and comparison cells;
- annotated satellite, aerial, map, terrain, or LiDAR-derived plates;
- negative results and source-coverage denominators;
- calibrated probabilities or explicitly non-probabilistic heuristic rankings;
- a minimum useful source package when evidence is insufficient; and
- a short, verified referral list for the relevant jurisdiction and problem.

### Exact spatial policy

Exactness is decided per evidence item.

An exact ordinary desk-research point is retained unless a specific
restriction applies. Schema-2 plans write `public` explicitly and reject
unknown sensitivity values during validation; ad hoc report records are not
treated as protected merely because an optional sensitivity tag is absent. A
topic is not restricted because it concerns treasure, weapons, precious
metal, portable finds, or a high-value candidate.

Public export withholds spatial evidence explicitly marked:

- `restricted`;
- `non-public`;
- `private`;
- `vulnerable`;
- `sacred`;
- `burial`;
- `authority-only`;
- `heritage-authority-only`;
- `withhold`; or
- `withheld`.

Burial language found during normalization escalates the findspot to protected
handling. Public handoff validation also rejects private-network URLs, signed
or credential-bearing URLs, unsafe local paths, and protected-location
classes.

### Field and recovery policy

`public-desk`, `licensed-computation`, and authorized read-only source work do
not require land, detecting, excavation, or recovery permissions.

`field-non-invasive` requires a confirmed official permission bundle bound to:

- the issuing authority;
- the legal or administrative instrument;
- the selected gazetteer area;
- the actual proposed method;
- the valid time window;
- the named holder or team;
- scope and conditions; and
- independently checkable approval references.

A user statement such as “the owner said it is fine” is not sufficient
machine-readable proof.

Physical detecting, digging, lifting, collecting, removing, or recovering
objects remains outside the autonomous action set. Text scanners reject direct
and paraphrased recovery instructions even when hidden inside execution
payloads.

## Architecture

### Workflow

```text
question or source package
          |
          v
place resolution + research package authoring
          |
          v
schema-2 evidence graph + executable actions
          |
          v
readiness, source-access, explicit-conduct, and budget gates
          |
          v
ranked frontier -> bounded action -> sealed result
          |                              |
          +----------- replay -----------+
                         |
                         v
history/finds/object/material/prospectivity reports
                         |
                         v
public exact output or sensitivity-aware withholding
```

The durable authority is the schema-2 plan plus the append-only event journal
and sealed result artifacts. Frontier packets, reports, exports, and prose are
derived views.

### Implemented components

| Concern | Implemented authority |
| --- | --- |
| Plan schema, graph, validation | `skills/plan-archaeological-search/scripts/ij_plan.py` |
| Declarative research packages | `scripts/ij_authoring.py` |
| Readiness and execution contracts | `scripts/ij_readiness.py`, `scripts/ij_execution_spec.py` |
| Action scope and conduct classes | `scripts/ij_safety.py`, `scripts/ij_targeting.py` |
| Field permission instruments | `scripts/ij_permissions.py` |
| Typed archaeological entities | `scripts/ij_entities.py` |
| Frontier ranking and blocking | `scripts/ij_frontier.py` |
| Runtime, leases, replay | `scripts/ij_runtime.py`, `scripts/ij_journal.py` |
| Budgets and stop conditions | `scripts/ij_budgets.py` |
| Result and artifact integrity | `scripts/ij_result_validation.py`, `scripts/ij_runtime_integrity.py`, `scripts/ij_results.py` |
| Source lineage registry | `scripts/ij_lineage.py`, `scripts/ij_source_contract.py` |
| Source acquisition and adapters | `scripts/ij_ingest.py`, `scripts/ij_adapters.py`, `scripts/ij_adapter_protocol.py` |
| XML/OAI parsing | `scripts/ij_xml_records.py`, `scripts/ij_ingest_guard.py` |
| Finds reconciliation and claims | `scripts/ij_workflow.py`, `scripts/ij_claims.py` |
| Candidate freeze and public export | `scripts/ij_candidates.py`, `scripts/ij_artifacts.py`, `scripts/ij_disclosure.py` |
| History and object biography | `scripts/ij_history.py` |
| Material and production reasoning | `scripts/ij_materials.py`, `scripts/ij_material_classification.py` |
| Calibration and assessment | `scripts/ij_calibration.py`, `scripts/ij_probability.py`, `scripts/ij_assessment.py` |
| Deterministic report core | `scripts/ij_reports.py`, `scripts/ij_public_report.py`, `scripts/ij_report_inputs.py`, `scripts/ij_spatial.py` |
| CLI composition | `scripts/search_plan.py`, `scripts/ij_cli_extended.py` |
| Professor voice and report layouts | `skills/report-archaeological-evidence/` |
| Archaeological discovery workflow | `skills/indiana-jones/` |
| History, finds, swords, and gold workflow | `skills/research-archaeological-history-and-finds/` |
| Imagery and reconstruction | `skills/indiana-jones/`, `skills/illustrate-historical-reconstruction/` |

Paths in the table after the first row are relative to
`skills/plan-archaeological-search/` unless they begin with `skills/`.

## Evidence model

### Plan

Schema `2.0` records:

- the case question, intended decision, research mode, disclosure, and
  authorization;
- a selected gazetteer identity and exact/restricted geometry;
- adaptive grid cells and landscape context;
- sources with origin-family identity, workflow role, access basis, record
  type, licence, target-label state, and sensitivity;
- typed nodes and source-bound edges;
- competing archaeological, natural, modern, processing, and null hypotheses;
- actions, prerequisites, methods, controls, outcomes, scores, execution
  contracts, acceptance criteria, and stopping policy; and
- optional frozen candidate evidence.

Observed, reported, derived, inferred, hypothesis, and corroborated authority
states remain distinct. A public node may not cite a non-public source.

### Typed archaeological entities

The graph supports typed records for:

- excavation contexts;
- objects;
- find events;
- assemblages;
- collections and repositories;
- analyses;
- custody events;
- production evidence;
- people and organizations;
- catalogue and publication records; and
- source snapshots.

Object identity is conservative. Reconciliation preserves source-native IDs,
origin families, conflicting fields, and the stated match basis. Similar
titles or nearby locations alone do not prove that two records describe the
same object.

Gold-related evidence is separated into material presence, surface treatment,
finished object, production debris, documentary craft activity, trade or
circulation, and geological occurrence. A gold object does not prove local
gold working. The same discipline separates a sword, fitting, depiction,
replica, production trace, and find event.

### Source snapshots and result seals

A manual `research-result-2.0` must contain:

- the active `actionId`;
- source-bound observations or explicit negative results;
- one evidence statement for every acceptance criterion;
- method and adapter versions;
- result sensitivity and disclosure;
- source snapshot references; and
- normalized record references when used.

An agent may not invent `snapshot:<sourceId>`. It must reference a
content-addressed snapshot from a sealed prerequisite or include captured
source text in a local snapshot manifest bound to:

- the declared action source;
- its plan origin family and access basis;
- a lowercase SHA-256 content digest;
- a timezone-aware retrieval timestamp; and
- `snapshot:<sourceId>:<contentSha256>`.

The validator recomputes the digest from the captured text. Deterministic
ingestion derives the same hash-qualified identity from retained raw bytes.
The complete result JSON and deterministic raw attachment are retained and
sealed, so a manifest cannot substitute an unverifiable digest for evidence
bytes.

Completion seals the plan hash, action hash, execution inputs, evidence,
versions, attempt, command, timing, budgets, snapshots, normalized records,
authorization, sensitivity, and disclosure. Runtime audit replays the journal
and verifies retained result bytes against their seals.

## Autonomous execution

### Lifecycle

The implemented lifecycle is:

```text
planned -> running -> completed
                    -> failed
                    -> interrupted -> planned
planned -> blocked
run -> explicitly stopped
```

`init-run` copies and hash-binds the plan. `next` returns a bounded ready batch
and blocked reasons. `start-action` creates an expiring lease. `run-action`
executes deterministic adapters. `complete-action` seals a structured result.
`resume` interrupts only expired leases; it never steals a live lease. `audit`
replays and verifies the run.

`advance` and `run` execute finite deterministic work until a declared stop or
an agent handoff is required. Agent work is represented as a bounded task
packet and must return through the same result validator.

### Operation-specific idempotency

Idempotency is intentionally narrow:

- `start-action` accepts a caller idempotency key and returns the same attempt
  only for the same action;
- replaying `complete-action` requires the same result hash, summary,
  normalized source-ID set, and attachment hashes; explicitly supplied
  acceptance evidence must equal the sealed evidence, while omission defers to
  that sealed evidence;
- reusing a key or changing any of those bound values is rejected; and
- offline artifacts use exclusive creation and do not overwrite prior output.

The RFC does not claim universal command idempotency.

### Budgets and stops

Run budgets cover:

- unique actions started;
- attempts started;
- retained result bytes;
- elapsed seconds;
- requests;
- requests per provider;
- records returned; and
- consecutive completions with no novelty.

Budget is reserved before an action and reconciled on completion, failure, or
interruption. The frontier reports deterministic `budget-exhausted:*` reasons.
Other stops include explicit user stop, safety/access gate, unresolved place,
method inadequacy, stronger alternative, bounded sufficiency, graph
invalidity, sensitivity escalation, and professional handoff.

No candidate-count, report-item-count, requests-per-minute, or concurrency
budget is claimed by this implementation.

## Source acquisition

The bounded standard-library adapters support:

- JSON;
- JSON Lines;
- CSV;
- OAI-PMH;
- IIIF JSON;
- RDF/XML; and
- SPARQL JSON results;
- Crossref JSON;
- OpenAlex JSON; and
- DOI metadata JSON.

Remote automated ingestion is limited to explicitly public sources. Local
ingestion accepts public, licensed, or user-provided sources. Redirects,
private-network destinations, unsafe URLs, nested credentials, unsafe XML,
oversized payloads, excessive records, stale acquisition contracts, and
overwrites are rejected.

Every acquisition retains the raw bytes, raw digest, query artifact, adapter
version, normalization version, source identity, origin family, access basis,
pagination state, and checkpoint.

Only OAI-PMH currently implements restartable pagination through a declared
resumption token and predeclared continuation page. Every other listed format
is a bounded single-snapshot parser; the plugin does not claim resumable paging
for it.

The search ladder expands place aliases, object terms, language variants, and
broader terms in a deterministic finite sequence. Exhaustion becomes evidence:
searched branches, denominators, access gaps, parse failures, and unresolved
queries appear in source-gap reports.

## History, finds, and treasure research

The autonomous workflow can:

- trace a place through historical phases;
- find documented swords, fittings, weapons, coins, gold objects, hoards,
  workshop evidence, and related records;
- connect find events, contexts, repositories, accessions, analyses, custody,
  conservation, and publications;
- reconcile duplicate or contradictory catalogue records;
- distinguish an object’s presence from production, trade, deposition, and
  recovery;
- map documented distributions separately from prospective hypotheses;
- freeze candidates before later ground-truth or authority-controlled review;
- rank candidates with explicit factors and counterevidence; and
- record a negative result without turning non-detection into absence.

“Always try” means continue through the next lawful source branch or bounded
hypothesis when useful. It does not mean fabricate evidence, bypass access, or
ignore a stop condition.

## Probability

`calibrated-probability` is allowed only when the supplied benchmark and
held-out evaluation establish:

- a predeclared event and spatial unit;
- a representative denominator;
- an observation model;
- independent validation;
- origin-family leakage control;
- calibration evidence and metrics;
- an uncertainty interval; and
- an explicit output and sensitivity scope.

If a gate fails, the system emits
`heuristic-ranking-not-probability`. It may provide an ordinal rank, band, or
non-probabilistic score with supporting and opposing factors, alternatives,
coverage, and uncertainty. It must not emit a probability or percentage.
The CLI exposes this contract as `assess-heuristic`; calibrated output remains
a separate `assess-probability` command.

Neither form authorizes field activity or recovery.

## Reporting

### Deterministic report core

The code produces stable schemas for:

- known-finds reports;
- reconciled object reports;
- historical phase reports;
- object biographies;
- material/production evidence reports;
- source-gap reports;
- candidate assessments; and
- public exports and spatial handoffs.

Reports preserve source IDs, origin families, record IDs, classification,
dating, context, custody, conflicts, denominators, limitations, and disclosure
decisions. Public serialization removes internal IDs and restricted spatial
fields while retaining explicitly public exact evidence.

### Professor-led layouts

The reporting skill composes the deterministic artifacts into:

- a broad-area reconnaissance brief;
- a candidate atlas;
- a single-candidate dossier;
- a source-gap teaching note;
- a negative-result report;
- a restricted authority brief;
- a known-finds register;
- an object or assemblage biography;
- a history-through-time and material-evidence report;
- a documented-versus-prospective distribution report; and
- a prospectivity and field-action brief.

For an imprecise area it explains the search windows, what signatures to look
for, where each modality is useful, what controls distinguish alternatives,
and which missing source would most change the answer.

When evidence is thin, it chooses one of three honest outputs:

1. proceed with bounded assumptions and list the assumption, reason, falsifier,
   and confidence;
2. ask for a minimum useful source package; or
3. stop with a source-gap report when the question is not answerable.

### Imagery and annotations

When rights permit, candidate reports pair the source image with an annotated
plate. Numbered annotations describe observations, not conclusions. The report
records source, acquisition date, provider, licence, CRS or georeferencing,
processing, image footprint, candidate footprint, positional uncertainty,
alternatives, and source/annotation/rendered SHA-256 hashes.

An interactive-viewer screenshot is a manual reference unless its terms allow
derivative capture and analysis. Open imagery or a user/licensed local raster
is preferred for reproducible pixel work.

### Contacts and institutes

The contact workflow matches the actual need to:

- a competent heritage authority;
- an Indigenous, descendant, religious, or community authority;
- a local or regional archaeological service;
- a museum, archive, finds liaison, or collections unit;
- a university or national laboratory;
- a geophysics, remote-sensing, dating, materials, conservation, or
  osteoarchaeology specialist; or
- a land manager for separately proposed field access.

Contact names, unit remit, official page, and public route must be verified at
report time because institutional details change. The plugin explains why the
first contact is appropriate and what evidence package to send. It may draft a
message but does not send it without explicit authorization.

## Migration and compatibility

Legacy schema-1 plans are never executed as trusted evidence. `migrate` creates
a separate schema-2 artifact and manifest, marks legacy completions
unverified, preserves typed records, and does not overwrite the source.
Candidate freezing hash-binds a candidate set before later ground-truth access.

Expected invalid input is returned as a structured diagnostic with a stable
code, message, path where available, retryability, and suggested resolution.
Secrets are redacted from diagnostics and public output.

## Acceptance matrix

| Review finding | Implemented authority | Required proof |
| --- | --- | --- |
| No executor or resume loop | `ij_runtime.py`, `ij_executors.py`, CLI `run/resume/audit` | Fault after each durable boundary; resumed and uninterrupted hashes match |
| Forgeable completion | `ij_results.py`, `ij_runtime_integrity.py`, frontier gate | Edited completion cannot unlock a dependent; a sealed result can |
| Optional readiness or freeze | `ij_execution_spec.py`, `ij_candidates.py`, runtime | Execution rejects an unready plan or stale/missing freeze seal |
| Non-executable actions | `ij_adapters.py`, execution bindings | Every schedulable method resolves to an executor or a typed block |
| Inert budgets and stops | `ij_budgets.py`, reservation events | Each limit stops exactly at its boundary and resumes with the right remainder |
| Spatial evidence over-withheld | `ij_artifacts.py`, `ij_spatial.py`, handoff validator | Public points/AOIs/footprints survive; explicit restrictions withhold only affected geometry and invalid states never leak |
| Malformed input crashes | `ij_errors.py`, bounded parsers | Invalid fixtures return stable redacted JSON diagnostics without tracebacks |
| Treasure research confused with field action | `ij_safety.py`, `ij_targeting.py` | Exact desk fixtures emit coordinates, rankings, and plates; explicit unlawful/destructive conduct is blocked |
| Missing archaeological entities | `ij_entities.py`, schema 2 | Object, find, assemblage, repository, analysis, and contested custody round-trip |
| Advisory source routing | `ij_ingest.py`, adapter protocol | Supported fixtures discover, ingest, checkpoint, resume, normalize, and hash |
| Weak material reasoning | `ij_materials.py` | A gold object alone cannot prove production; secure debris/context can support a qualified claim |
| Missing finds reports | `ij_reports.py`, golden fixtures | History/finds/object/material/gap reports preserve citations, conflicts, coverage, and supported precision |
| Priority confused with probability | `ij_probability.py`, `ij_calibration.py` | Priority never appears as probability; heuristic and calibrated outputs obey separate gates |
| Unsafe legacy state | `ij_migrate.py` | Legacy completions migrate as non-unlocking, source bytes unchanged |

## Definition of done

1. Every acceptance-matrix row has automated proof.
2. A fresh public schema-2 case can be authored, executed, interrupted,
   resumed, audited, reported, spatially handed off, and publicly exported
   using documented commands.
3. Replay reproduces the final plan, event, and result hashes.
4. No prerequisite is satisfied without a valid result seal.
5. Readiness, source access, candidate freeze, budgets, stops, explicit
   protected-site restrictions, and explicit physical-conduct gates cannot be
   bypassed.
6. Unknown schema, disclosure, sensitivity, method, and licence values fail
   with stable diagnostics rather than silently changing meaning.
7. Provider failures and malformed input return redacted, actionable errors.
8. Object, find, assemblage, repository, custody, analysis, and conflict
   histories survive serialization and migration.
9. Source adapters demonstrate bounded, provenance-preserving discovery and
   ingestion; restart claims are limited to formats with checkpoint proof.
10. Reports distinguish presence, circulation, working, and production, and
    distinguish catalogue silence from archaeological absence.
11. Lawful sword, gold, coin, hoard, and treasure research produces cited
    exact coordinates, rankings, imagery references, annotated plates, and map
    handoffs without a field-permission dossier.
12. Every prospectivity number is labelled calibrated or heuristic; calibrated
    claims require held-out evidence and heuristic estimates expose assumptions,
    uncertainty, and limitations.
13. The professor voice, candidate layouts, source-gap guidance, bounded
    assumptions, and institute/specialist referral routes are documented.
14. Schema-1 fixtures remain readable; migration is non-destructive and
    idempotent; both public export contracts retain their golden hashes.
15. The plugin and every contributed skill pass their official validators, all
    relevant suites pass, repository whitespace is clean, and authored source
    files stay below the repository line limit.

Current repository verification is recorded in the implementation handoff
rather than frozen into this normative RFC, because test counts can grow.

## Deployment notes

This RFC completes the engineering implementation for bounded autonomous desk
research. Before using it to support a real field program, operators should
obtain jurisdiction-specific review from the relevant archaeological,
community, land-access, data-rights, and legal authorities. That review is a
deployment recommendation, not a prerequisite for lawful desk research and
not part of the repository engineering definition of done.

The plugin should describe itself as an autonomous archaeological desk
researcher and evidence assistant. It should not describe itself as an
autonomous excavator, detectorist, recovery service, or heritage authority.
