# RFC 0001: Autonomous Archaeological Research

- Status: Proposed
- Target schema: `2.0`
- Scope: `plugins/indiana-jones`
- Decision owners: Indiana Jones plugin maintainers

## Summary

The plugin will become a resumable, evidence-bound archaeological research system rather than a planner that relies on an agent to edit JSON correctly. It will execute lawful research, preserve source and reasoning lineage, track historical and object biographies, produce finds-specific reports, and stop safely when evidence or authorization is insufficient.

The system will support questions such as:

- What happened in this landscape through time?
- Which swords are documented within a safely generalized area?
- Is there evidence for gold objects, gold working, trade, or production?
- Which source or expert could resolve the remaining uncertainty?

Treasure-oriented research is in scope. Public work stays generalized; exact targeting runs only in a restricted or heritage-authority-only case after the system verifies the applicable jurisdiction, land-access, detecting, excavation, heritage, and disclosure permissions. “Always try” means exhaust lawful, evidence-producing paths; it never means silently converting research into unpermitted recovery instructions.

## Motivation

The current planning skill has a strong research model: resolved places, time-sliced hypotheses, independent source families, controls, authorization gates, an adaptive grid, a deterministic frontier, and public redaction. Its executable surface, however, only creates, validates, ranks, and exports plans.

The review found the following gaps:

1. There is no executor, result-ingestion path, checkpoint, retry, or resume loop.
2. An action can be marked `completed` without a result or evidence, allowing dependent work to be unlocked by editing JSON.
3. Research readiness and candidate freezing are advisory rather than hard execution gates.
4. Actions describe work but cannot invoke a bounded, provider-neutral implementation.
5. Budgets and stopping rules are labels rather than enforced controls.
6. Unknown or misspelled sensitivity values can fail open during public export.
7. Malformed input can escape as an implementation traceback rather than a stable diagnostic.
8. Safety checks do not reliably distinguish generalized treasure research, permitted exact targeting, and unpermitted recovery intent.
9. Objects, finds, assemblages, repositories, analyses, and custody histories are not first-class records.
10. Catalogue and archive source routing is advisory rather than executable.
11. The model cannot distinguish robust evidence for material production from the presence of a finished object.
12. There is no finds-specific report or object-biography report.
13. Scheduling scores risk being mistaken for archaeological probability.

## Goals

- Execute public and explicitly authorized research actions from a validated plan.
- Make every state transition attributable, append-only, idempotent, and recoverable after interruption.
- Require evidence-bound result seals before an action can unlock dependants.
- Treat readiness, authorization, candidate freezing, budgets, and stops as runtime invariants.
- Add a provider-neutral adapter contract for catalogues, repositories, archives, and scholarly metadata.
- Represent objects, find events, assemblages, repositories, custody, analyses, and source-qualified relationships.
- Reconstruct historical sequences without converting documentary inference into archaeological stratigraphy.
- Reason explicitly about material production, circulation, deposition, recovery, and curation.
- Support generalized public treasure research and permission-gated exact research without leaking restricted targeting data.
- Produce safe history, finds, object-biography, material-evidence, source-gap, and referral reports.
- Default to qualitative evidence grades; allow numeric probability only after an explicit calibration gate.
- Fail closed on unknown disclosure or sensitivity values.
- Return stable, actionable diagnostics for all untrusted input.
- Preserve version 1 plans without silently changing their meaning.

## Non-goals

- Autonomous physical fieldwalking, metal detecting, collection, probing, excavation, UAV operation, land access, or contact with people and institutions.
- Turning a research result into physical recovery instructions unless the user separately requests that stage and every required permission is confirmed.
- Publishing precise locations merely because another public page exposes them.
- Using hidden extraction, mass download, bulk capture, stitching, or reconstruction on Google Maps, Google Earth, or Street View; analyzing Street View or copy-prohibited outputs; or building a systematic derived dataset without a licence covering the exact use. Bounded exploratory local analysis of a permitted attributed Earth capture is allowed when its use basis and provenance are recorded.
- Treating catalogue absence, remote-sensing non-detection, or incomplete coverage as proof of archaeological absence.
- Generating a probability from an ordinal priority score.
- Defining a single worldwide institution list or treating one jurisdiction’s catalogue model as universal.
- Replacing an archaeologist, curator, heritage or community authority, conservator, or materials specialist.

## Normative language

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` are normative. A “public action” means read-only research against a source whose access basis and licence permit the requested use. An “authorized action” additionally requires a named approval record scoped to that method, provider, account, case, and validity period.

## Design principles

1. **Evidence before state.** Completion follows a sealed result, never an unverified input assertion.
2. **Fail closed.** Unknown safety, sensitivity, licence, state, or method values block execution and public export.
3. **Append, then project.** Events are durable authority; `plan.json` and the frontier are reproducible views.
4. **Bound every expedition.** Every run has request, time, byte, action, and source budgets plus explicit stops.
5. **Separate observation and interpretation.** Records, entities, claims, hypotheses, and conclusions retain different types.
6. **Preserve origin families.** Ten pages repeating one catalogue record are one origin, not ten corroborations.
7. **Precision follows authority.** Exact work is possible in a correctly authorized restricted case, never by topic alone.
8. **Priority is not probability.** Scheduler utility, evidence grade, and calibrated probability have separate schemas.
9. **No silent automation.** Every connector declares its access basis, licence, capabilities, and side-effect class.

## Architecture

### Components

The implementation is split into modules below 700 lines where practical:

- `search_plan.py`: stable CLI and exit-code boundary.
- `ij_errors.py`: typed diagnostics and exception-to-exit-code conversion.
- `ij_plan.py`: schema validation and version dispatch.
- `ij_readiness.py`: structural, research, execution, and publication gates.
- `ij_events.py`: append-only event envelope, hash chain, and replay.
- `ij_state.py`: legal state transitions and materialized plan projection.
- `ij_execution.py`: bounded dispatcher, idempotency, checkpoint, and resume.
- `ij_frontier.py`: deterministic scheduling of ready actions.
- `ij_policy.py`: budgets, stops, scoring policy, and calibration policy.
- `ij_safety.py`: intent, object sensitivity, authorization, and output policy.
- `ij_sources.py`: adapter protocol, discovery, snapshot, and provenance.
- `adapters/`: provider-specific or standards-based read-only adapters.
- `ij_objects.py`: object/find/assemblage normalization and reconciliation.
- `ij_history.py`: time-slice, claim-conflict, and sequence synthesis.
- `ij_materials.py`: material-production evidence evaluation.
- `ij_probability.py`: calibration gate and held-out evaluation.
- `ij_artifacts.py`: canonical hashes and fail-closed exports.
- `ij_reports.py`: history, finds, biography, material, gap, and referral views.

The planner remains provider-neutral. Adapters implement access; they do not
own evidence grading, safety, scheduling, or conclusions.

### Durable case layout

```text
case/
  plan.json                 # Materialized schema-2 plan
  events.jsonl              # Append-only hash-chained authority
  snapshots/                # Hash-addressed source response manifests
  records/                  # Normalized records and extraction manifests
  results/                  # Sealed action results
  candidates/               # Frozen candidate sets
  reports/                  # Restricted reports
  public/                   # Independently redacted exports
  checkpoints/              # Rebuildable run cursors
```

Source content is stored only when access terms permit it. Otherwise the
snapshot contains canonical identifiers, retrieval metadata, response hashes,
and a reproducibility note without retaining prohibited content.

### Event envelope

Every mutation MUST append an event before updating a materialized view:

```json
{
  "eventId": "evt_...",
  "caseId": "case_...",
  "sequence": 42,
  "eventType": "action.result-recorded",
  "occurredAt": "2026-07-24T12:00:00Z",
  "actor": {"kind": "agent", "id": "codex"},
  "commandId": "cmd_...",
  "idempotencyKey": "sha256:...",
  "previousEventHash": "sha256:...",
  "payloadHash": "sha256:...",
  "payload": {}
}
```

Replay MUST reproduce the same plan hash. A duplicated idempotency key with
the same payload returns the prior result; the same key with a different
payload is an error. A broken sequence or hash chain blocks mutation.

## Schema 2.0

### Existing records

Version 2 retains places, areas, grid cells, sources, graph nodes and edges,
actions, hypotheses, policies, and disclosure classes. Enumerated values are
validated at every boundary. Unknown values are errors, never extensions by
accident.

### Archaeological object

```json
{
  "objectId": "obj_...",
  "preferredLabel": "double-edged sword",
  "objectClass": ["weapon", "sword"],
  "materials": [{"material": "iron", "claimId": "claim_..."}],
  "typology": [{"system": "catalogue-name", "term": "type", "claimId": "claim_..."}],
  "chronology": {"earliest": 1200, "latest": 1350, "basisClaimIds": ["claim_..."]},
  "authenticity": "reported",
  "currentRepositoryId": "repo_...",
  "accessionIdentifiers": [{"scheme": "local", "value": "123"}],
  "sensitivity": "restricted",
  "provenanceSourceIds": ["src_..."]
}
```

`authenticity` is one of `unassessed`, `reported`, `contested`, `verified`, or
`rejected`. Object labels and classifications are assertions with sources, not
timeless facts.

### Find event

A find event records:

- `findEventId`, object or assemblage IDs, date or interval, and recovery
  method;
- archaeological context and context-quality grade;
- original location assertion, precision, coordinate uncertainty, and
  sensitivity;
- discoverer/recovery body only when lawful and necessary;
- excavation, inventory, publication, and reporting identifiers;
- claim and source lineage;
- whether the record describes an observation, report, legacy attribution, or
  inferred association.

Public outputs use a separately derived generalized area. They never transform
a precise restricted location into a public one in place.

### Assemblage

An assemblage has an ID, membership assertions, formation interpretation,
context, chronology, recovery history, completeness caveat, source lineage,
and sensitivity. Membership can be contested or source-specific.

### Repository and custody

A repository represents a museum, archive, laboratory, heritage body, private
collection where lawful to record, or an unknown repository. A custody event
links an object or assemblage to a repository or responsible body over an
interval and records:

- event type: `recovered`, `transferred`, `accessioned`, `loaned`,
  `deaccessioned`, `lost`, `repatriated`, or `reported`;
- supporting claim and source IDs;
- legal/ethical caveats;
- confidence and contradiction status.

This is collection provenance. It MUST NOT be presented as archaeological
provenience.

### Analysis and production evidence

An analysis stores method, sample relationship, laboratory or analyst,
calibration/limitations, result, units, source, and object/context link.

Production evidence uses explicit classes:

1. direct installation: furnace, hearth, crucible setting, moulding area;
2. production debris: slag, crucible, mould, tuyere, casting waste;
3. tools or residues linked to a secure production context;
4. compositional, isotopic, metallographic, or use-wear evidence;
5. documentary or iconographic production evidence;
6. finished object or raw material without production context.

The material reasoner MUST NOT infer local gold working from a gold object
alone. It reports the strongest supported statement—presence, circulation,
repair, working, or production—and the evidence required to advance it.

### Graph additions

New node kinds:

- `object`, `find-event`, `assemblage`, `repository`, `custody-event`;
- `analysis`, `production-evidence`, `person-or-organization`;
- `catalogue-record`, `publication-record`, `source-snapshot`.

New relations:

- `found-at`, `recovered-in`, `member-of`, `made-of`, `typed-as`;
- `dated-by`, `analysed-by`, `supports-production-of`;
- `held-by`, `custody-before`, `same-object-as`, `possibly-same-as`;
- `catalogued-as`, `published-as`, `reported-by`, `derived-from`.

Only real excavated contexts may participate in Harris-style stratigraphic
relations. Documentary, object-biography, and custody sequence edges remain
separate.

### Claims and conflicts

Every extracted fact is a claim with:

- subject, predicate, object/value, temporal scope, and spatial scope;
- source and origin-family IDs;
- quoted span or machine-readable record locator;
- extraction method and version;
- assertion status and evidence grade;
- contradiction links and adjudication state.

Entity reconciliation MUST preserve every source identifier and expose the
rule or review decision behind `same-object-as`. It MUST NOT merge solely on a
similar description and nearby location.

## Action execution

### States

```text
planned -> ready -> running -> completed
                    |    |       |
                    |    |       +-> superseded
                    |    +-> failed -> ready (bounded retry)
                    +-> blocked -> ready (block resolved)
planned/ready/blocked/failed -> rejected
planned/ready/blocked/failed -> cancelled
v1 completed -> completed-unverified -> completed (sealed evidence)
```

The executor derives `ready`; callers cannot set it directly. `running`
requires a lease, attempt ID, budget reservation, executable adapter, current
authorization, and a matching plan hash. Expired leases become recoverable
attempts, not silent failures.

`completed` requires a result seal containing:

- action, attempt, command, plan, input, and output hashes;
- adapter and method versions;
- start/end timestamps and consumed budget;
- source snapshot and normalized record IDs;
- observations, negative results, warnings, and errors;
- authorization record when applicable;
- result sensitivity and disclosure decision.

Dependency checks require a valid seal. A JSON field saying `completed` cannot
unlock work. `completed-unverified` is archival and never satisfies a
prerequisite.

### Commands

Existing commands remain:

```text
new
validate
rank
export-public
```

Version 2 adds:

```text
migrate                 Convert a v1 case into a new v2 destination.
freeze-candidates       Hash and seal a candidate set before ground truth.
source-discover         List bounded source candidates without ingesting them.
source-ingest           Snapshot and normalize selected source records.
extract-claims          Produce reviewable claims from a sealed snapshot.
reconcile-entities      Propose or approve cross-source entity links.
record-result           Seal an external or manually reviewed action result.
advance                 Execute one ready bounded batch.
run                     Repeat bounded batches until a stop condition.
resume                  Recover leases and continue an interrupted run.
audit                   Replay events and verify hashes, gates, and lineage.
report-history          Build a sourced time-slice and conflict report.
report-finds            Build a safely generalized known-finds report.
report-object           Build an object and custody biography.
report-material         Build a material-production evidence matrix.
report-gaps             Explain source coverage and the next lawful checks.
```

Mutating commands require `--case-dir` and either an explicit
`--idempotency-key` or a deterministic command manifest. They refuse to
overwrite inputs. `run` requires explicit finite budgets and never contacts,
posts, purchases, books, downloads prohibited content, or changes an external
system.

### Readiness gates

`advance`, `run`, `resume`, `record-result`, and every report enforce their
appropriate gate:

- **Structural:** schema, references, acyclic task graph, safe locators.
- **Research:** resolved place, safe area description, hypotheses and
  alternatives, source coverage, controls, and a falsifier.
- **Execution:** current plan hash, executable action, adapter, access basis,
  licence, authorization, budgets, and prerequisites.
- **Candidate:** required freeze seal exists and ground-truth lineage cannot
  flow into candidate generation.
- **Publication:** known sensitivity, generalized geometry, source rights,
  and a redaction audit.

`rank` MUST enforce research readiness by default. `--allow-draft` MAY produce
an explicitly non-executable planning preview.

### Budgets and stopping

A run policy requires finite non-negative limits:

- actions, attempts, retries per action, wall-clock time, and bytes retained;
- requests globally and per provider;
- records, candidates, and report items;
- provider-specific rate and concurrency caps.

The dispatcher reserves budget atomically before an attempt and records actual
use afterward. Resume reconstructs remaining budget from events.

Supported stops include:

- all required hypotheses reach their evidence threshold;
- every allowed adapter is exhausted for the declared query variants;
- a configured number of consecutive actions yields no novel origin family,
  claim, object, or contradiction;
- the next action exceeds budget, authorization, licence, or safety limits;
- a contradiction or sensitivity escalation requires expert review;
- no executable frontier remains.

Every stop emits a reason, supporting metrics, unresolved questions, and the
next lawful action. “No executable frontier” is not “nothing exists.”

## Source adapters

### Adapter contract

Each adapter declares:

- stable ID and semantic version;
- supported standards, record types, jurisdictions, languages, and query
  capabilities;
- access basis, authentication requirement, licence discovery behavior,
  retention constraints, and side-effect class;
- rate/concurrency defaults;
- methods for `discover`, `fetch`, `normalize`, and `checkpoint`;
- deterministic pagination cursor and canonical record identifier;
- fields that may contain sensitive location or personal information.

Initial adapters SHOULD cover generic JSON/CSV, OAI-PMH, IIIF manifests,
RDF/SPARQL, and DOI/OpenAlex/Crossref-style scholarly metadata. Named heritage
register, museum, excavation repository, or numismatic adapters are added only
with fixtures, current terms review, and a jurisdiction note.

Discovery returns source candidates, never implicit authorization. Ingestion
requires an allowlisted candidate and records the exact query, aliases,
language, bounds, date, pagination, retrieval time, response hash, licence,
and origin family.

### “Always try” fallback

The executor can expand a documented search ladder within budget:

1. official heritage and finds registers;
2. excavation repositories and museum catalogues;
3. scholarly publications, theses, archives, and historical maps;
4. alternate place names, historical spellings, languages, and OCR variants;
5. citation following and identifier reconciliation;
6. a broader, safely generalized area, period, or object class;
7. a source-gap result naming unavailable, inaccessible, unlicensed, or
   undiscovered evidence.

Expansion never weakens safety, precision, authorization, or licence gates.
Guesses are emitted as hypotheses with discriminating tests, not catalogue
facts.

## Safety and disclosure

### Intent classes

Every case and action is classified before scheduling:

- `documentary-known-records`: lawful research into documented finds;
- `landscape-research`: non-invasive candidate or historical research;
- `treasure-research-public`: generalized documentary or prospective research;
- `treasure-research-restricted`: exact analysis under recorded authority and disclosure control;
- `authority-casework`: exact heritage information under recorded authority control;
- `field-proposal`: planning only, never permission to act;
- `intrusive-or-evasive`: unpermitted trespass, detecting, collection, excavation, burial disturbance, access bypass, or concealment.

Public modes may run within ordinary gates but cannot emit exact targeting data. Restricted treasure research requires `restricted` or `heritage-authority-only` disclosure and a permission bundle that resolves the governing jurisdiction and records `confirmed` or lawfully `not-required`, with source, scope, approving body, and validity period, for land access, detecting, excavation, heritage consent, finds/treasure reporting, and any community or sacred-site authority applicable to the case. Unknown, expired, contradictory, or incomplete permissions block exact targeting.

The plugin may continue a blocked exact request as generalized public research only after making the scope change explicit. Physical activity is never performed autonomously. `intrusive-or-evasive` is rejected.

### High-risk object policy

Weapons, coins, precious-metal objects, hoards, burials, grave goods, sacred objects, human remains, and vulnerable portable finds receive a high-risk review even when the source is public.

Allowed:

- search documented records;
- discuss history, typology, chronology, collection, and published context;
- provide counts or patterns at a deliberately generalized scale;
- under the restricted treasure mode, compare exact candidates and estimate a defined target event when every permission, evidence, and calibration gate passes;
- refer the user to a museum, archaeologist, community authority, or heritage authority.

Rejected or restricted:

- public exact findspot lists, cell rankings, hotspot maps, access routes, or terrain-navigation details;
- exact targeting without the complete permission bundle and restricted disclosure;
- combining individually public records to reveal a sensitive pattern;
- instructions to detect, collect, probe, or excavate beyond the confirmed permission scope;
- evasion of reporting, land, heritage, community, burial, or access controls.

Safety classification examines intent, object class, precision, aggregation risk, jurisdiction, permissions, action sequence, and output—not only prohibited verbs or object topics.

### Fail-closed export

Only the exact value `public`, plus a successful publication gate, permits public output. Missing, misspelled, unknown, inherited, or contradictory sensitivity is treated as `restricted`. Public export uses an allowlist and recomputes safe geometry from policy; it never copies and opportunistically rounds a source coordinate.

An export manifest records excluded fields, generalization method, aggregation threshold, reviewer, input hash, and output hash. Public reports receive a second independent lint covering labels, prose, URLs, identifiers, image metadata, and attachments.

## History and finds reporting

Reports preserve source citations, origin families, conflicts, uncertainty,
negative evidence, and the exact coverage denominator.

`report-history` contains:

- resolved name concordance and area;
- sourced time slices, events, processes, and competing interpretations;
- what changed, what persisted, and which intervals lack evidence;
- documentary sequence clearly separated from stratigraphy.

`report-finds` contains:

- safely generalized study area and search coverage;
- objects and assemblages grouped by class and period;
- context-quality and recovery-method distribution;
- duplicate/reconciliation warnings;
- repository, accession, and source links when disclosure permits;
- explicit distinction between no record found and evidence of absence.

`report-object` contains:

- classification and dating claims;
- find context and provenience quality;
- conservation or analysis evidence;
- custody chronology and present repository;
- authenticity, identity, and ownership disputes.

`report-material` contains an evidence matrix for presence, circulation,
repair, working, or production and identifies the next discriminating evidence.

`report-gaps` records attempted sources, queries, aliases, languages, dates,
permissions, failures, and the institutions or specialists best placed to
continue. Contact information is verified at report time; the executor does
not message anyone.

## Probability and scoring

Three concepts remain structurally separate:

- `priorityScore`: deterministic scheduler utility for choosing the next
  action; never rendered with a percent sign.
- `evidenceGrade`: ordinal assessment with reasons and limitations.
- `estimatedProbability`: optional calibrated estimate for a precisely defined
  event.

Numeric probability is blocked unless the case has:

- a declared event and denominator;
- representative positive and negative observations;
- documented detection and reporting processes;
- bias and missingness treatment;
- geographically separated training, calibration, and held-out evaluation;
- a frozen model, features, threshold, and candidate set;
- calibration metrics such as Brier score and reliability bins;
- uncertainty intervals and a validity-domain statement.

Treasure-target probability may run only in `treasure-research-restricted` after both the permission bundle and calibration gate pass; it remains restricted and cannot authorize physical activity. Public mode reports evidence grades and generalized patterns. When calibration fails, every mode states which data would be required rather than inventing a percentage.

## Input and error handling

All JSON, JSONL, adapter responses, cursors, manifests, URLs, and CLI values are
untrusted. Parsers enforce size, depth, count, numeric-finiteness, encoding,
enumeration, and schema limits before business logic.

Expected invalid input MUST produce:

```json
{
  "ok": false,
  "error": {
    "code": "IJ_SCHEMA_INVALID",
    "message": "Action status is not recognized.",
    "path": "$.actions[2].status",
    "hint": "Use one of: planned, blocked, rejected."
  }
}
```

No expected user, provider, or file error prints a traceback. Exit codes are
stable: `2` invalid invocation, `3` invalid data, `4` safety/authorization
block, `5` budget/stop, `6` provider failure, and `7` integrity failure.
Unexpected defects may retain a traceback only behind an explicit debug flag
and MUST redact secrets.

Tests include malformed and truncated JSON, wrong container types, deep nesting, huge values, non-finite numbers, invalid UTF-8, broken cursors, unknown enumerations, adapter timeouts, and partially written event logs.

## Migration and backward compatibility

- Version 1 files remain readable by `validate`, `rank --allow-draft`, and
  `export-public`, using the stricter fail-closed exporter.
- Mutating or executing a version 1 plan is refused until migration.
- `migrate --input v1.json --out <new-case-dir>` is non-destructive and writes
  a migration manifest with before/after hashes and every default or warning.
- Version 1 `completed` actions become `completed-unverified`; they do not satisfy prerequisites until an operator attaches a result and runs `record-result`.
- Existing node and edge IDs are retained. New records receive deterministic
  IDs where identity is unambiguous and review-required IDs otherwise.
- Unknown legacy sensitivity becomes `restricted`; it is never guessed.
- Existing priority weights retain their ordinal meaning and are never copied
  into probability fields.
- Public export remains schema `1.0-public` during a deprecation window, with a
  new `2.0-public` export available explicitly. Golden fixtures cover both.
- Migration is idempotent and refuses to overwrite its source or destination.

## Threat model

| Threat | Consequence | Required control |
|---|---|---|
| User edits an action to `completed` | False evidence unlocks work | Event authority and result seals |
| Ground truth enters candidate generation | Inflated rediscovery performance | Freeze seal and lineage gate |
| Misspelled sensitivity | Precise location leaks | Closed enum and deny-by-default export |
| An exact treasure request looks documentary | Unpermitted recovery guidance is produced | Research mode, permission bundle, precision, aggregation, and sequence classifier |
| Public records are combined | Sensitive hotspot emerges | Aggregation-risk review and generalized output |
| Repeated source copies | False corroboration | Origin-family deduplication |
| Catalogue records refer to one object | Inflated find counts | Reviewable entity reconciliation |
| Finished gold object implies workshop | False production claim | Material evidence ladder |
| Adapter changes or paginates poorly | Irreproducible or skipped records | Versioned adapter, snapshot hash, deterministic cursor |
| Authentication leaks in URL or logs | Credential exposure | Secret-safe locator validation and redaction |
| Crash after external read | Duplicate or inconsistent state | Idempotency, append-first events, leases, resume |
| Endless “always try” expansion | Cost and provider abuse | Finite budgets, novelty stop, source exhaustion |
| Priority score is read as probability | False quantitative certainty | Separate schemas and calibration gate |
| Malformed input crashes CLI | Lost work or leaked internals | Typed boundary errors and fuzz corpus |
| Report cites stale contacts | Failed or harmful referral | Verify at report time; no autonomous outreach |

## Milestones

### M0: Safety and parser boundary

- Add typed diagnostics and stable exit codes.
- Close all sensitivity enums and public-export paths.
- Classify portable-find targeting and aggregation risk.
- Add malformed-input and redaction regression suites.

### M1: Durable execution

- Add event log, replay, hash chain, idempotency, leases, and checkpoints.
- Implement action states and sealed completion.
- Enforce readiness, authorization, freeze, and executable-adapter gates.
- Implement budgets, stops, `advance`, `run`, `resume`, and `audit`.

### M2: Finds and history model

- Add object, find, assemblage, repository, custody, analysis, claim, and conflict records.
- Add migration from version 1 and legacy-completion quarantine.
- Implement entity reconciliation and historical sequence synthesis.

### M3: Executable source routing

- Implement the adapter protocol and standards-based fixture adapters.
- Add bounded discovery, ingestion, snapshots, claim extraction, and source exhaustion.
- Prove restart-safe pagination and origin-family deduplication.

### M4: Reasoning and reports

- Implement material-production rules and counterexamples.
- Add history, finds, object, material, gap, and referral reports.
- Add public generalization manifests and independent leakage lint.

### M5: Calibrated inference

- Enforce the probability gate.
- Add a held-out, non-sensitive benchmark with calibration metrics.
- Prove that uncalibrated cases emit no percentage or probability field.

## Acceptance matrix

| Review finding | Implementation target | Required acceptance proof |
|---|---|---|
| No executor or resume loop | `ij_events.py`, `ij_execution.py`, CLI `advance/run/resume/audit` | Kill a fixture run after each event boundary; resume produces the uninterrupted event and result hashes |
| Forgeable completion | `ij_state.py`, result seals, frontier gate | Hand-edited `completed` cannot unlock a dependant; sealed result can |
| Optional readiness/freeze | `ij_readiness.py`, `ij_execution.py`, `search_plan.py` | Every execution command rejects an unready plan or missing/stale freeze seal |
| Non-executable actions | Adapter binding and dispatcher | Every schedulable method resolves to one executable adapter or is blocked with a typed reason |
| Inert budgets/stops | `ij_policy.py`, reservation events | Request/action/time/retry/novelty fixture stops exactly at its configured boundary and resumes with the correct remainder |
| Fail-open redaction | `ij_artifacts.py`, publication lint | Unknown, missing, misspelled, nested, image-metadata, and prose coordinates are withheld |
| Malformed input crashes | `ij_errors.py`, boundary parsers | Invalid-input corpus returns stable JSON diagnostics without traceback |
| Treasure and portable-find safety | `ij_safety.py` | Public sword/gold research is generalized; unauthorized exact work is blocked; an exact restricted fixture runs only with the complete permission bundle |
| Missing archaeological entities | `ij_objects.py`, schema 2 | Round-trip an object, find event, assemblage, repository, analysis, and contested custody biography |
| Advisory source routing | `ij_sources.py`, `adapters/` | Discover, ingest, checkpoint, resume, normalize, and hash fixtures for each supported standard |
| Weak material reasoning | `ij_materials.py` | Finished gold object alone cannot yield local-production; secure crucible/debris evidence can support a qualified claim |
| Missing finds reports | `ij_reports.py` | Golden history/finds/object/material/gap reports preserve citations, conflicts, coverage, and safe precision |
| Priority/probability confusion | `ij_probability.py`, report schemas | Priority never appears as probability; insufficient calibration blocks numeric output; held-out fixture reports calibration |
| Unsafe legacy state | migration command | v1 completed actions migrate to non-unlocking `completed-unverified`; source remains byte-identical |

In addition to row-specific tests, the suite MUST include:

- end-to-end “documented swords near a named place” research with duplicate catalogue records, contested context, interruption, and safe reporting;
- end-to-end “gold objects versus gold-working evidence” research where the correct conclusion is weaker than the initial hypothesis;
- permission-complete restricted treasure research that executes exact analysis but cannot enter a public export;
- sparse-source fallback that exhausts lawful variants and reports a bounded gap without inventing evidence;
- an authority-only fixture proving exact data remains absent from public plans, logs, reports, images, URLs, and attachments;
- static checks keeping authored implementation and test files below 700 lines where practical.

All integration tests use local fixtures or explicitly authorized test services. No test contacts a live catalogue by default.

## Definition of done

This RFC is implemented only when:

1. Every acceptance-matrix row passes in CI.
2. A fresh version 2 case can be created, made ready, executed, interrupted, resumed, audited, reported, and publicly exported from documented commands.
3. Replay from `events.jsonl` reproduces the final plan and result hashes.
4. No action satisfies a prerequisite without a valid result seal.
5. No path bypasses readiness, authorization, candidate-freeze, budget, stop, or safety gates.
6. Unknown sensitivity and disclosure values are denied everywhere.
7. Malformed input and provider failures produce stable redacted diagnostics.
8. Object, find, assemblage, repository, custody, analysis, and conflict histories survive serialization and migration.
9. Source adapters demonstrate bounded, restart-safe, provenance-preserving discovery and ingestion.
10. Reports distinguish object presence, circulation, working, and production; catalogue silence remains a source gap.
11. Public sword/gold research is cited and generalized; exact treasure research requires the complete permission bundle, stays restricted, and never silently becomes physical recovery guidance.
12. No numeric probability appears without the permission policy applicable to its target, the calibration gate, and held-out evidence.
13. Documentation states what executes autonomously, what remains approval-gated, and what the system will never do.
14. Version 1 fixtures remain readable, migrations are non-destructive and idempotent, and both public export contracts pass their golden tests.
15. A maintainer signs off the threat-model tests and a qualified archaeology or heritage reviewer signs off object, provenance, permission, and disclosure behavior.

Until every condition holds, the plugin MUST describe itself as an archaeological research planner and evidence assistant, not as a fully autonomous archaeological researcher.
