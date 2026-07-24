# Indiana Jones

This directory contains the installable Codex plugin. For the human-facing
story, example questions, research foundations, installation guide, and project
principles, start with the [repository README](../../README.md).

The public experience is discovery-led. A user describes a place and a mystery:
an undocumented castle, an earlier settlement, an unusual field mark, the way
people lived, or a local story that may preserve something real. The plugin
chooses the research methods behind the scenes and returns a reconstructed
history, overlooked connection, ranked hypothesis, candidate place or feature,
or the next check most likely to change the conclusion.

## Technical architecture

Under the hood, the worldwide, provider-neutral package combines:

- a multidisciplinary search-planning skill that turns a place, city, event,
  route, culture, or landscape story into resolved AOIs, historical time
  slices, an adaptive grid, competing hypotheses, and a permission-gated task
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
  evidence plates, broad-area reconnaissance, source-gap teaching notes,
  negative-result reports, and authority referrals;
- an evidence-led illustration skill that turns source-linked decisions about
  people, objects, buildings, settlements, cities, and lived scenes into
  generated reconstruction art with explicit alternatives, prompt paradata,
  and post-generation anachronism review;
- a history-and-finds skill for documented and prospective swords, treasure,
  gold, hoards, objects, assemblages, production and trade evidence, object
  biographies, museum holdings, custody, and provenance;
- generalized public prospectivity plus restricted exact workflows gated by
  current jurisdictional, land, method, heritage, reporting, and community
  permissions;
- paired conservative-source/annotated imagery plates with provenance hashes
  and a bounded public-disclosure validator;
- current, jurisdiction-specific routing to heritage authorities, community
  bodies, land managers, archaeologists, university laboratories, museums, and
  archives;
- a consent-gated workflow for local websites, archives, Chrome, Facebook, and
  other authenticated sources;
- a dedicated Google Earth browser skill for bounded current/historical
  imagery checks, gated review of Earth-native experimental analysis,
  terrain-aware measurements, data-layer discovery, safe KML/project handling,
  and exact provider attribution;
- explicit source, claim, uncertainty, sensitivity, and ground-truth
  separation.

Google Maps and Google Earth support bounded official-interface research,
attributed permitted captures, and source-and-use-gated local analysis.
Systematic scraping, bulk reconstruction, and copy-prohibited layers remain
out of scope. Reproducible pixel analysis uses openly licensed, user-owned, or
explicitly licensed source products.

## Start here

- [Skill workflow](skills/indiana-jones/SKILL.md)
- [Place and area search planning](skills/plan-archaeological-search/SKILL.md)
- [Multidisciplinary planning](skills/plan-archaeological-search/references/multidisciplinary-planning.md)
- [Worldwide source routing](skills/plan-archaeological-search/references/source-routing.md)
- [Research Sequence Graph contract](skills/plan-archaeological-search/references/graph-contract.md)
- [City/landscape plan template](skills/plan-archaeological-search/assets/search-plan-template.json)
- [Disputed-event plan template](skills/plan-archaeological-search/assets/event-search-plan-template.json)
- [History, finds, treasure, and object research](skills/research-archaeological-history-and-finds/SKILL.md)
- [Object and custody evidence contract](skills/research-archaeological-history-and-finds/references/object-evidence-contract.md)
- [Historical and finds research workflow](skills/research-archaeological-history-and-finds/references/historical-research-workflow.md)
- [Safe prospectivity, distribution, and probability](skills/research-archaeological-history-and-finds/references/safety-probability-and-distribution.md)
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

The terrain detector supports single-band terrain rasters. A separate optical
command validates and analyzes registered multi-date surface-reflectance
cubes. SAR, thermal, hyperspectral, learned-model, and photogrammetric paths
remain explicitly routed to their calibrated, licence-checked workflows. The
reporting utility renders a conservative source frame beside its annotated
derivative and writes a hash-bound sidecar; its public validator performs a
bounded check for coordinate, filename, and embedded-image metadata leakage.

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
