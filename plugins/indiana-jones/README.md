# Indiana Jones

This directory contains the installable Codex plugin. For the human-facing
story, example questions, research foundations, installation guide, and project
principles, start with the [repository README](../../README.md).

Indiana Jones is authored and published by **Paweł Klimkowski**.

The public experience is discovery-led. A user describes a place and a mystery:
an undocumented castle, an earlier settlement, an unusual field mark, the way
people lived, or a local story that may preserve something real. The plugin
chooses the research methods behind the scenes and returns a reconstructed
history, overlooked connection, ranked hypothesis, candidate place or feature,
or the next check most likely to change the conclusion.

Treasure, hoard, sword, weapon, coin, gold, and other portable-find questions
are first-class research topics. Desk research may return documented records,
exact evidence-supported candidate coordinates, ranked cells, annotated
satellite or aerial plates, and calibrated or explicitly heuristic
prospectivity estimates. It needs no field-permission dossier. Exact output is
restricted only for genuinely protected/confidential places or private data;
research never becomes permission for entry, detecting, collection, or
recovery.

## Technical architecture

Under the hood, the worldwide, provider-neutral package combines:

- a multidisciplinary search-planning skill that turns a place, city, event,
  route, culture, or landscape story into resolved AOIs, historical time
  slices, an adaptive grid, competing hypotheses, and an evidence-gated task
  frontier;
- separate landscape-evidence, search/task, and genuine-stratigraphy graph
  authorities, preventing documentary city history from masquerading as a
  Harris Matrix;
- a source-backed research skill covering aerial photography, multispectral and
  hyperspectral imagery, Sentinel/Landsat, SAR, LiDAR/DEM, thermal sensing,
  UAV/SfM photogrammetry, and current computational methods;
- a page-referenced method/theory layer that records how acquisition,
  processing, visualization, and prior knowledge shape what becomes evidence;
- public STAC discovery and bounded OpenStreetMap context;
- hash-bound import of projected terrain rasters from any country or provider;
- a transparent Python terrain-enclosure baseline;
- a hash-bound multi-date optical cube contract and transparent local-contrast,
  spectral-index, regularized-RX, and repeatability baseline;
- a browser-backed local MapLibre GL JS renderer for deterministic styles,
  3D extrusions, custom WebGL modules, and provenance-labelled screenshot
  fallbacks;
- a professor-led reporting skill for candidate atlases, licensed annotated
  satellite/aerial evidence plates, exact coordinate and ranking tables,
  broad-area reconnaissance, source-gap teaching notes, negative-result
  reports, and authority referrals;
- an evidence-led illustration skill that turns source-linked decisions about
  people, objects, buildings, settlements, cities, and lived scenes into
  generated reconstruction art with explicit alternatives, prompt paradata,
  and post-generation anachronism review;
- a history-and-finds skill for documented and prospective swords, treasure,
  gold, hoards, objects, assemblages, production and trade evidence, object
  biographies, museum holdings, custody, and provenance;
- exact and generalized desk-research prospectivity from lawful sources, with
  calibrated probability where evidence supports it and plainly labelled
  heuristic estimates where it does not;
- narrow restrictions for genuinely protected/confidential sites,
  authenticated/private data without consent, trespass, and destructive
  recovery or removal;
- paired conservative-source/annotated imagery plates with provenance hashes
  and a bounded artifact/embedded-metadata validator;
- exact, clickable Google Maps links embedded with every point in reports,
  KML placemarks, and GeoJSON properties, plus complete KML/GeoJSON collections
  for candidate footprints, research AOIs, and image footprints;
- current, jurisdiction-specific routing to heritage authorities, community
  bodies, land managers, archaeologists, university laboratories, museums, and
  archives;
- a consent-gated workflow for local websites, archives, Chrome, Facebook, and
  other authenticated sources;
- a dedicated Google Earth browser skill for bounded current/historical
  imagery checks, gated review of Earth-native experimental analysis,
  terrain-aware measurements, data-layer discovery, exact KML/project handling,
  and exact provider attribution;
- explicit source, claim, uncertainty, sensitivity, and ground-truth
  separation;
- a schema-2, hash-chained, resumable research runtime with leases,
  operation-specific idempotency, finite budgets, typed agent results,
  machine-checked deterministic ingestion/reconciliation, source-identity
  contracts, and sealed report inputs.

Google Maps and Google Earth support bounded official-interface research,
attributed permitted captures, and source-and-use-gated local analysis.
Systematic scraping, bulk reconstruction, and copy-prohibited layers remain
out of scope. Reproducible pixel analysis uses openly licensed, user-owned, or
explicitly licensed source products.

## Start here

- [Skill workflow](skills/indiana-jones/SKILL.md)
- [Autonomous-research RFC](rfcs/0001-autonomous-archaeological-research.md)
- [Place and area search planning](skills/plan-archaeological-search/SKILL.md)
- [Multidisciplinary planning](skills/plan-archaeological-search/references/multidisciplinary-planning.md)
- [Worldwide source routing](skills/plan-archaeological-search/references/source-routing.md)
- [Research Sequence Graph contract](skills/plan-archaeological-search/references/graph-contract.md)
- [City/landscape plan template](skills/plan-archaeological-search/assets/search-plan-template.json)
- [Disputed-event plan template](skills/plan-archaeological-search/assets/event-search-plan-template.json)
- [History, finds, treasure, and object research](skills/research-archaeological-history-and-finds/SKILL.md)
- [Object and custody evidence contract](skills/research-archaeological-history-and-finds/references/object-evidence-contract.md)
- [Historical and finds research workflow](skills/research-archaeological-history-and-finds/references/historical-research-workflow.md)
- [Finds prospectivity, distribution, and estimates](skills/research-archaeological-history-and-finds/references/safety-probability-and-distribution.md)
- [Evidence reporting and professor voice](skills/report-archaeological-evidence/SKILL.md)
- [Report layouts](skills/report-archaeological-evidence/references/report-layouts.md)
- [Contact and institute routing](skills/report-archaeological-evidence/references/contact-routing.md)
- [Evidence-led historical illustration](skills/illustrate-historical-reconstruction/SKILL.md)
- [Reconstruction method and source standards](skills/illustrate-historical-reconstruction/references/reconstruction-method.md)
- [People, object, building, city, and scene guides](skills/illustrate-historical-reconstruction/references/subject-evidence-guides.md)
- [Reconstruction brief template](skills/illustrate-historical-reconstruction/assets/reconstruction-brief-template.json)
- [Research synthesis](skills/indiana-jones/references/research.md)
- [Method, theory, and visual evidence](skills/indiana-jones/references/method-theory-raczkowski.md)
- [Worldwide source routing](skills/indiana-jones/references/imagery-sources.md)
- [Satellite methods and software boundary](skills/indiana-jones/references/satellite-analysis.md)
- [Evidence contract](skills/indiana-jones/references/evidence-contract.md)
- [Local MapLibre renderer](skills/indiana-jones/references/maplibre-renderer.md)
- [Web, account, and location ethics](skills/indiana-jones/references/ethics-and-web-research.md)
- [Google Earth browser research](skills/research-google-earth/SKILL.md)
- [img2threejs architecture study](skills/indiana-jones/references/reference-img2threejs.md)
- [Whitley Castle terrain POC](skills/indiana-jones/references/poc-whitley-castle.md)
- [Whitley Castle Sentinel-2 optical POC](skills/indiana-jones/references/poc-whitley-castle-optical.md)

## POC status

The known-site Whitley Castle terrain POC passes its top-20/160 m development
criterion at rank 8 with 16.125 m error. Two earlier failures are retained.
Because the winning scale profile was selected after unblinding, the result is
development evidence and not a held-out generalization claim.

The optical baseline passes synthetic multi-date regression, provenance,
masking, temporal-support, CRS, archive-safety, and input-overwrite tests. Its
first frozen real-data Sentinel-2 test is deliberately retained as a miss:
three precommitted profiles all failed the 160 m criterion, with the nearest
anomaly 191.150 m away. That is one target-withheld localization window, not a
blind survey, an absence claim, or a transferable performance estimate.

## Runtime

The executable baseline requires Python 3.9+, NumPy, and Pillow:

```bash
python3 -m pip install -r skills/indiana-jones/scripts/requirements.txt
python3 -m unittest discover \
  -s skills/indiana-jones/scripts/tests \
  -v
python3 -m unittest discover \
  -s skills/report-archaeological-evidence/scripts/tests \
  -v
python3 -m unittest discover \
  -s skills/plan-archaeological-search/scripts/tests \
  -v
python3 -m unittest discover \
  -s skills/illustrate-historical-reconstruction/scripts/tests \
  -v
```

The planner and finds runtime itself uses the standard library. For a new
coarse schema-2 plan:

```bash
python3 skills/plan-archaeological-search/scripts/search_plan.py new \
  --place "Resolved place" \
  --gazetteer-id "AUTHORITY:ID" \
  --question "Which evidence would discriminate the live hypotheses?" \
  --bbox <WEST> <SOUTH> <EAST> <NORTH> \
  --disclosure public \
  --out case-plan.json
```

`new` creates a structurally valid reconnaissance skeleton, not invented
evidence. Author its sources, competing hypotheses, controls, actions,
execution contracts, acceptance criteria, and stopping policy using the
[graph contract](skills/plan-archaeological-search/references/graph-contract.md).
The two schema-2 assets are worked shapes; replace every example identity,
source, area, and claim before using one for a real case.

Apply a declarative research package and prove that the resulting case is
execution-ready:

```bash
python3 skills/plan-archaeological-search/scripts/search_plan.py prepare \
  --plan case-plan.json \
  --package research-package.json \
  --out case-ready.json

python3 skills/plan-archaeological-search/scripts/search_plan.py validate \
  --ready \
  --plan case-ready.json
```

The package uses `archaeological-research-package-1.0` and supplies the
case/area decisions plus sources, typed entity nodes, edges, and executable
actions. The command rejects unknown package fields and any result that is not
schema-valid and ready.

Validate, initialize, execute, interrupt or resume, and audit the authored case
with the actual runtime commands:

```bash
python3 skills/plan-archaeological-search/scripts/search_plan.py validate \
  --ready \
  --plan case-plan.json

python3 skills/plan-archaeological-search/scripts/search_plan.py rank \
  --plan case-plan.json \
  --limit 4 \
  --out case-frontier.json

python3 skills/plan-archaeological-search/scripts/search_plan.py init-run \
  --plan case-plan.json \
  --run-dir case-run \
  --max-actions 100 \
  --max-attempts 200 \
  --max-result-bytes 100000000 \
  --max-seconds 86400

python3 skills/plan-archaeological-search/scripts/search_plan.py next \
  --run-dir case-run \
  --limit 4 \
  --out task-packet.json

python3 skills/plan-archaeological-search/scripts/search_plan.py run \
  --run-dir case-run
```

Build a finite alias/object/language query ladder before source acquisition:

```bash
python3 skills/plan-archaeological-search/scripts/search_plan.py search-ladder \
  --place-alias "York" \
  --place-alias "Eboracum" \
  --object-term "sword" \
  --language-variant "gladius" \
  --broader-term "weapon fitting" \
  --maximum 100 \
  --out search-ladder.json
```

When evidence is useful but no held-out calibration set exists, emit a ranked
heuristic assessment without inventing a percentage:

```bash
python3 skills/plan-archaeological-search/scripts/search_plan.py assess-heuristic \
  --input candidate-evidence.json \
  --plan case-ready.json \
  --out heuristic-assessment.json
```

The input declares the method, score meaning, evidence references,
assumptions, uncertainty, limitations, and candidates. The command rejects
probability fields, preserves exact unrestricted coordinates and imagery
references, and labels the result `heuristic-ranking-not-probability`.

Checkpoint-bearing OAI-PMH fixtures can continue with `resume-source`; it
verifies the prior page, adapter version, query hash, declared cursor, and next
snapshot before ingesting the continuation. Public plans support both stable
export contracts:

```bash
python3 skills/plan-archaeological-search/scripts/search_plan.py export-public \
  --plan case-ready.json \
  --schema 2.0-public \
  --out case.public.json
```

After an actual interruption, resume only when the unfinished lease has
expired; active leases are deliberately not stolen:

```bash
python3 skills/plan-archaeological-search/scripts/search_plan.py resume \
  --run-dir case-run
```

Audit the journal, retained candidates, result seals, attachments, and budget
projection at any checkpoint:

```bash
python3 skills/plan-archaeological-search/scripts/search_plan.py audit \
  --run-dir case-run
```

The loop executes bounded ingestion and reconciliation actions, emits typed
packets for scholarly agent research, resumes expired leases, verifies retained
candidate and result seals, and records a reason when it stops. Exact
high-value desk prospectivity, coordinates, rankings, and annotated evidence
plates are ordinary outputs when lawful sources support them. Protected or
confidential site data stays restricted, and the runtime never performs
recovery or external contact. The four finds-specific report commands accept
only sealed completed-action artifacts from the same `--run-dir`; see the
[reporting skill](skills/report-archaeological-evidence/SKILL.md) for the
complete invocation contract.

The terrain detector supports single-band terrain rasters. A separate optical
command validates and analyzes registered multi-date surface-reflectance
cubes. SAR, thermal, hyperspectral, learned-model, and photogrammetric paths
remain explicitly routed to their calibrated, licence-checked workflows. The
reporting utility renders a conservative source frame beside its annotated
derivative and writes a hash-bound sidecar; its public validator performs a
bounded check for disclosure mismatches and unreviewed embedded-image metadata.
Declared coordinates, map links, AOIs, and image footprints are intentional
evidence and remain intact. Every exported point receives a derived clickable
Google Maps link.

The optional MapLibre renderer requires Node 22+, MapLibre GL JS, and a local
Chrome/Edge/Chromium executable:

```bash
cd skills/indiana-jones/scripts/map_renderer
npm install
npm test
```

The checked-in fixture proves local 3D extrusion, a shared-context custom
WebGL layer, raster-DEM terrain, framebuffer diagnostics, and screenshot
fallback on macOS software WebGL2. Native-GPU and Windows runs, plus the
Three.js OGC 3D Tiles adapter, remain separate proof gates.
