---
name: indiana-jones
description: Discover and test what may be hidden, forgotten, or misunderstood in an archaeological landscape. Use when the user asks what once stood somewhere; whether a castle, settlement, route, workshop, field system, sword, gold object, hoard, treasure-related context, or other trace may survive; how people lived or built; why a landscape feature looks unusual; or where evidence is most likely. Choose maps, archives, public records, imagery, terrain, and consent-gated private sources; produce exact desk-research candidates, coordinates, rankings, annotated imagery, and honest estimates when evidence supports them; do not enable trespass, destructive recovery/removal, private-data misuse, or harm to genuinely protected sites.
---

# Indiana Jones

Investigate archaeological proxies without turning an image anomaly into a discovery claim. Keep observations, deterministic transformations, interpretations, and independent corroboration distinct from intake through handoff.

## Discovery mandate

- Pursue a useful discovery outcome: a reconstructed history, overlooked
  connection, ranked hypothesis, candidate place or feature, or a clear
  discriminating next test. Do not stop at naming methods or sources.
- Treat an unavailable source as a routing problem. Try another lawful source,
  try aliases, test a competing model, or explain the smallest material needed
  to continue. Reduce precision only when the source cannot support it or the
  location is genuinely protected or confidential.
- Treat exact desk research and exact field action separately. Coordinates,
  ranked cells, and annotated evidence plates are normal research outputs;
  land access, detecting, excavation, collection, and recovery remain separate.
- Spend effort in proportion to the question and evidence value, while keeping
  user-stated cost and time limits, source rights, law, human safety, and site
  protection as hard boundaries.

## Voice and reporting boundary

- Explain the work as a seasoned field-archaeology professor: direct,
  teaching-oriented, lightly adventurous, dryly witty, and rigorous about what
  the evidence cannot show.
- Do not claim to literally be the fictional character, reproduce catchphrases
  or close dialogue, romanticize collecting or trespass, or let theatrical
  language inflate certainty.
- Lead with the provisional judgment, then teach the observation, physical
  proxy, strongest alternative, and next discriminating check.
- Use the companion `$plan-archaeological-search` skill when a named place,
  point, city, region, event, route, culture, or landscape story must become an
  AOI, time-sliced hypothesis graph, adaptive grid, and ordered search plan.
- Use the companion `$research-archaeological-history-and-finds` skill for
  history through time, documented or prospective swords, treasure, gold,
  hoards, objects, assemblages, production, trade, museum holdings, and custody
  or provenance. It produces exact or generalized desk-research candidates,
  ranks, coordinates, and honest prospectivity estimates; restriction follows
  real protected/confidential status, not the treasure topic.
- Use the companion `$report-archaeological-evidence` skill for formal reports,
  candidate atlases, annotated source imagery, source-gap explanations, and
  institution or heritage-authority referrals. Every user-facing discovery or
  candidate result must use its spatial-handoff contract: exact point and/or
  AOI when known, explicit precision and feature-role labels, source/derived
  imagery, image locations or footprints, and KML or GeoJSON when requested.
- Use the companion `$illustrate-historical-reconstruction` skill when the user
  wants an evidence-led generated image of a historical person, object,
  building, settlement, city, landscape, or lived scene. Generated pixels are
  an interpretive output and never source evidence or corroboration.

## Non-negotiable rules

- Treat remote sensing as candidate generation. Say what the sensor measured and what proxy produced the anomaly.
- Treat acquisition, classification, interpolation, visualization, and threshold choices as part of the method. Preserve a conservative source view and log consequential decisions.
- Prefer multi-date, multi-scale, or multi-modal agreement over one striking image.
- Preserve source URL or path, acquisition date, sensor/product, CRS, resolution, processing steps, license, access basis, and hashes where available.
- Run negative controls and compare against modern drainage, field boundaries, geology, forestry, utilities, roads, image seams, and processing artefacts.
- Use `possible archaeological anomaly` or `candidate` until an authoritative record, field survey, geophysics, or excavation corroborates it.
- Protect precise coordinates for genuinely protected, sacred, burial-related, confidential, deliberately redacted, or community-restricted sites. Otherwise preserve the useful precision supported by the evidence.
- Never infer permission to enter land, fly a UAV, metal-detect, collect, probe, excavate, message people, or use an authenticated account.
- Use authenticated websites or social accounts only after the user explicitly authorizes the named platform and session for this case. Keep that pass read-only unless the user separately requests a specific action.
- Keep the workflow provider-neutral and worldwide. A national-agency adapter is one source option, not a geographic boundary.
- Never use hidden endpoints or mass-download, bulk-capture, stitch, or reconstruct Google Maps, Google Earth, or Street View content. Official-interface automation may control a bounded user-directed pass. Local analysis is allowed on canonical open, user-owned, or separately licensed inputs and, when the current Earth terms and Geo guidelines permit the exact use, on a small attributed Earth capture for an explicitly recorded exploratory check. Never analyze Street View or copy-prohibited catalog/generated output.

## Route the request

1. **Named place, AOI, city, event, route, culture, or “where should we look?”**:
   first use the companion `$plan-archaeological-search` skill. It owns place
   resolution, multidisciplinary time slices, the adaptive grid, hypothesis
   graph, control design, and task order.
2. **History, known finds, objects, assemblages, treasure, swords, gold,
   production, trade, museum holdings, or custody**: use the companion
   `$research-archaeological-history-and-finds` skill. It owns object/find
   evidence separation, source reconciliation, object biographies, sparse-
   source fallback, answerability, prospective-find reasoning, and the
   exact candidate, ranking, coordinate, probability, and heuristic-estimate contract.
3. **Imagery or terrain investigation**: read [research.md](references/research.md) and [method-theory-raczkowski.md](references/method-theory-raczkowski.md), then follow the evidence workflow below.
4. **Satellite analysis**: also read [satellite-analysis.md](references/satellite-analysis.md). Use its transparent optical baseline before trying supervised or foundation models.
5. **Data acquisition or reproducible computation**: also read [imagery-sources.md](references/imagery-sources.md) and [evidence-contract.md](references/evidence-contract.md).
6. **Historical, local-web, archive, or social-source research**: read [ethics-and-web-research.md](references/ethics-and-web-research.md) before opening sources.
7. **Known-site POC or regression check**: read the Whitley Castle [terrain POC](references/poc-whitley-castle.md) and [optical POC](references/poc-whitley-castle-optical.md), then keep target ground truth outside candidate generation.
8. **Photogrammetry or UAV planning**: use the SfM/UAV sections in `research.md`; verify current aviation, landowner, heritage, and privacy requirements for the jurisdiction before field activity.
9. **Local map, terrain, or 3D visualization**: read [maplibre-renderer.md](references/maplibre-renderer.md), preserve visible attribution and a render manifest, and distinguish proven style/custom-layer rendering from the still-unproven OGC 3D Tiles adapter.
10. **Google Earth browser reconnaissance**: also use the companion
   `$research-google-earth` skill. It owns the official-interface workflow,
   authentication and mutation gates, visual comparisons, measurements,
   native-analysis and catalog/imported-data boundaries, evidence records, and
   attribution.
11. **Report, explanation, annotated plate, or referral**: also use the companion
   `$report-archaeological-evidence` skill. Keep acquisition and candidate
   authority here; keep presentation, teaching voice, and contact routing in
   that reporting layer.
12. **Historical reconstruction illustration**: also use the companion
   `$illustrate-historical-reconstruction` skill. Research the time, place,
   material culture, and visible decisions before generation; preserve the
   evidence-to-prompt chain and label the image as a reconstruction.

## Evidence workflow

### 1. Contract the case

State:

- the research question and intended decision;
- known-site study, benchmark, or prospective survey;
- study area, available coordinate precision, and any specific legal,
  custodian, community, or user restriction that requires a less precise
  derivative;
- for place-led work, the resolved gazetteer identity, focus/context/control
  AOIs, historical phases, hypothesis alternatives, and ready task frontier
  from `$plan-archaeological-search`;
- for finds-led work, distinguish documented object, find event, assemblage,
  production, trade, custody, and prospective hypothesis; record allowed
  source precision, real protected/confidential status, and any separate field
  permissions only if field action is actually proposed;
- public-only or named authenticated sources explicitly authorized;
- available modalities, dates, resolution, CRS, and licenses;
- expected physical proxy, visibility conditions, target scale, alternative explanations, and interpretive prior;
- the success criterion and what would falsify the hypothesis;
- the disclosure class: `public`, `restricted`, or `heritage-authority-only`.

Assign every source one workflow role:

- `analysis`: pixels or measurements licensed for local computation;
- `negative-control`: modern, geological, vegetation, infrastructure, or processing context;
- `corroboration`: independently interpreted records or imagery;
- `ground-truth`: known-site labels kept withheld until candidates are frozen;
- `manual-reference`: a view that may be inspected but not extracted or
  processed, including Google Earth basemap and catalog content unless a
  separate canonical source and licence authorize analysis.

Initialize a case ledger when the work spans more than one source:

```bash
python3 <skill-dir>/scripts/methodology.py new-case \
  --title "Landscape investigation" \
  --question "Which anomalies merit expert follow-up?" \
  --study-area "Defined area description" \
  --expected-proxy "Local relief contrast from surviving banks or ditches" \
  --visibility-condition "Ground returns and classification preserve low relief" \
  --target-scale "40-160 m" \
  --alternative-explanation "Modern drainage or forestry" \
  --decision-rule "Advance only if morphology survives two visualization families" \
  --falsifier "The feature follows mapped modern drainage" \
  --interpretive-prior "Target labels withheld" \
  --out case.json
```

Record consequential acquisition, processing, and visualization choices:

```bash
python3 <skill-dir>/scripts/methodology.py add-decision \
  --case case.json \
  --stage visualization \
  --choice "Compare multi-direction hillshade and local relief" \
  --rationale "A single illumination direction can hide or exaggerate relief" \
  --alternative "Single-azimuth hillshade" \
  --target-labels-state withheld \
  --artifact "sha256:<DERIVED_ARTEFACT_HASH>"
```

### 2. Inventory evidence before interpretation

Record each source before extracting claims. Use the original raster or document when possible, not a screenshot of a viewer. Keep a source-strength label:

- `primary-measurement`: sensor data, field survey, excavation, geophysics;
- `authoritative-record`: heritage inventory, government dataset, peer-reviewed publication;
- `contemporary-account`: dated map, newspaper, photograph, community record;
- `secondary-summary`: synthesis that points to stronger evidence;
- `lead-only`: forum, social post, anecdote, or unsourced map pin.

Do not let many weak sources masquerade as independent corroboration when they repeat one origin.

### 3. Choose a modality from the expected signature

- Crop, parch, soil, or moisture marks: multi-date RGB/NIR/red-edge/SWIR; compare phenological windows.
- Banks, ditches, mounds, terraces, roads, or woodland relief: classified-ground LiDAR DTM with several visualizations and scales.
- Exposed architecture or excavation documentation: calibrated aerial/UAV imagery and SfM–MVS.
- Surface roughness, moisture, disturbance, or deformation: calibrated multi-temporal SAR with terrain correction.
- Shallow thermal contrast: radiometric thermal time series near the useful diurnal window.
- Broad landscape context: Sentinel-2/Landsat time series; do not upsample them into false detail.

Record why the chosen sensor can observe the proposed proxy and why its ground sampling distance is adequate.

### 4. Generate candidates without target leakage

For a rediscovery benchmark:

1. Freeze the area, sensor product, preprocessing, feature family, scale range, and ranking rule.
2. Keep exact target coordinates and labels in a separate ground-truth file.
3. Run candidate generation with only the raster metadata and area bounds.
4. Hash and save the ranked candidates before loading ground truth.
5. Score top-1/top-k distance, false positives, and negative controls afterward.
6. Label any tuning performed after seeing the score as development-set iteration; validate the frozen method on a separate site before generalizing.

For a worldwide study, discover assets through a public STAC API without downloading pixels:

```bash
python3 <skill-dir>/scripts/archaeology.py search-stac \
  --endpoint https://earth-search.aws.element84.com/v1 \
  --bbox <WEST> <SOUTH> <EAST> <NORTH> \
  --collection sentinel-2-c1-l2a \
  --datetime 2025-01-01/2025-12-31 \
  --out stac-search.json
```

After obtaining and orthorectifying a licensed single-band terrain raster, bind its declared projected-metre metadata to the exact file hash:

```bash
python3 <skill-dir>/scripts/archaeology.py register-raster \
  --input terrain.tif \
  --bbox <X_MIN> <Y_MIN> <X_MAX> <Y_MAX> \
  --crs EPSG:<PROJECTED_CRS> \
  --coordinate-unit metre \
  --modality terrain \
  --source-url <CANONICAL_ITEM_URL> \
  --license "<LICENCE>"
```

The registration command records user-declared spatial metadata; it does not parse or verify an embedded GeoTIFF transform. Verify the raster in GDAL, QGIS, or another trusted geospatial tool before registration. Reproject longitude/latitude and feet-based grids to a suitable local metric CRS before running metre-scale kernels.

Use OSM as context, not as a blind detector label. The default query deliberately omits `historic` and `heritage` tags:

```bash
python3 <skill-dir>/scripts/archaeology.py fetch-osm-context \
  --bbox <SOUTH> <WEST> <NORTH> <EAST> \
  --out osm-negative-controls.json
```

Only after candidate hashes are frozen may `--include-heritage` be used for known-site corroboration. Its output is marked `targetLabelsUsed: true` and must not be fed back into candidate generation.

The bundled terrain detector is a transparent classical baseline, not a universal archaeological classifier:

```bash
python3 <skill-dir>/scripts/archaeology.py fetch-ea-dtm \
  --bbox <E_MIN> <N_MIN> <E_MAX> <N_MAX> \
  --out terrain.tif

python3 <skill-dir>/scripts/archaeology.py detect-enclosures \
  --input terrain.tif \
  --out-dir run \
  --top-k 20

python3 <skill-dir>/scripts/archaeology.py score \
  --candidates run/candidates.json \
  --ground-truth restricted-ground-truth.json \
  --out run/score.json
```

It requires Python 3.9+, NumPy, and Pillow. Install only when missing:

```bash
python3 -m pip install -r <skill-dir>/scripts/requirements.txt
```

The terrain detector accepts only registered `terrain` rasters. Do not relabel another modality to force it through that command.

For multi-date optical surface reflectance, copy
`assets/optical-cube-template.json`, build the hash-bound `.npz` described in
`satellite-analysis.md`, and run:

```bash
python3 <skill-dir>/scripts/satellite.py validate \
  --manifest optical-cube.json

python3 <skill-dir>/scripts/satellite.py analyze \
  --manifest optical-cube.json \
  --out-dir optical-run \
  --background-radius-m 120 \
  --threshold 3.5 \
  --min-dates 2 \
  --min-valid-dates 2
```

This ranks raw-band, NDVI, SAVI, optional NDMI/BSI/NDRE, local-contrast, and
regularized-RX anomalies across dates. It reports valid-date opportunity,
exact-peak supporting dates, feature/polarity switching, and native observable
resolution. Its scores are not probabilities and are not comparable after
changing the feature set without calibration.

For a known-site benchmark, freeze `optical-run/candidates.json` before
supplying the separate ground-truth point, then bind and score both artifacts:

```bash
shasum -a 256 optical-run/candidates.json

python3 <skill-dir>/scripts/satellite.py score \
  --candidates optical-run/candidates.json \
  --expected-candidate-sha256 <PRECOMMITTED_SHA256> \
  --ground-truth restricted-ground-truth.json \
  --out optical-run-score.json
```

The bundled scorer accepts only explicitly public-known targets because it
emits exact candidate-to-target distances. Use restricted handling for
genuinely protected/confidential ground truth.

The frozen real-data Whitley Castle Sentinel-2 POC missed its 160 m
localization tolerance under all three precommitted profiles; the nearest
anomaly was 191.150 m away. Preserve this as a negative calibration result, not
as archaeological absence and not as permission to tune the threshold. See
`references/poc-whitley-castle-optical.md`.

Prepare SAR, thermal, and hyperspectral inputs through their own calibrated
pipelines; never relabel them as optical reflectance.

For a deterministic local MapLibre GL JS render:

```bash
cd <skill-dir>/scripts/map_renderer
npm install
node src/cli.mjs probe
node src/cli.mjs render \
  --job fixtures/extrusion-job.json \
  --output artifacts/extrusion.png
```

Every render job requires an analysis-source provenance record, disclosure
class, and visible attribution. The renderer writes a hash-bound sidecar next
to the PNG. A screenshot import or automatic fallback is labelled
`screenshot-fallback`; it is never reported as locally rendered. Current proof
covers local styles, raster-DEM terrain, fill extrusions, and the custom WebGL
module seam.
MapLibre's official OGC 3D Tiles approach additionally requires a tested
Three.js/`3d-tiles-renderer` adapter and must not be claimed from the custom
layer fixture alone.

### 5. Interpret each candidate in layers

For every candidate, report:

1. **Observed**: location precision, shape, polarity, scale, orientation, dates, bands or terrain visualization.
2. **Derived**: index, filter, model, threshold, template, score, and processing provenance.
3. **Inferred**: possible feature class and the physical proxy linking it to the observation.
4. **Alternatives**: at least two plausible natural or modern explanations and checks that distinguish them.
5. **Corroboration**: independent imagery/date/modality, historic mapping, authoritative record, field survey, or geophysics.
6. **Uncertainty**: positional error, resolution limit, no-data/cloud/vegetation effects, domain shift, and what remains unknowable.
7. **Interpretive audit**: acquisition, processing, visualization, prior-knowledge, and categorization choices that made the feature legible.
8. **Next action**: another desk source, non-invasive follow-up, specialist review, protected-site referral, or rejection.

Use a calibrated probability only with representative held-out evidence. When
that is unavailable, give an explicitly labelled heuristic rank, ordinal band,
or non-probabilistic score with its factors, alternatives, uncertainty, and
unvalidated status. Do not emit a probability or percentage, and never relabel
the scheduler score as probability.

### 6. Validate proportionally

- Use geographically separated positives and hard negatives.
- Report the denominator: area searched, number of candidates, number reviewed, and number field checked.
- For detection, report precision, recall, F1, top-k hit rate, positional error, and threshold sensitivity where ground truth permits.
- For segmentation, include IoU/Dice and object-level recall; for mapping, include check-point RMSE.
- Have an independent reviewer inspect raw source, derived visualization, candidate report, and alternatives without seeing the builder's preferred conclusion.
- Treat non-detection as `not visible under these conditions`, never proof of absence.

## Completion gate

Do not call an investigation complete until:

- the case question, scope, source access, and disclosure class are explicit;
- place-led work has a resolved AOI, time-aware hypothesis graph, control cells,
  and evidence-gated search order;
- finds-led work separates objects, find events, contexts, assemblages,
  production, custody, and prospective hypotheses, and reports exact
  desk-research candidates unless a genuine protection rule requires restriction;
- source and processing provenance is reproducible;
- research-frame assumptions and consequential decisions are recorded;
- observations and interpretations are separated;
- plausible non-archaeological alternatives were tested;
- benchmark target data stayed outside candidate generation, when applicable;
- uncertainty and negative evidence are preserved;
- any Google Earth pass has a manual-reference record with the displayed
  imagery date or `unavailable`, exact provider attribution, view state,
  access time, exact deep link when coordinates are known, and measurement
  caveats;
- genuinely protected/confidential coordinates are redacted from public output;
- every user-facing result includes exact points, AOIs, image locations or
  footprints, a clickable Google Maps link for every point, and evidence
  imagery under the evidence-preserving spatial-handoff contract unless a
  named restriction requires omission;
- the conclusion names the required expert, field, geophysical, or archival validation.

If those checks cannot be met, hand off a bounded candidate report and state the exact missing evidence.
