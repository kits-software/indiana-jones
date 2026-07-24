# Google Earth browser research

Use Google Earth on the web for bounded visual reconnaissance, source
discovery, and visualization of data whose rights are already known. Do not
treat the interface as a tile service, an export API, or a substitute for a
licensed analysis source.

Indiana Jones applies an archaeological evidence boundary in addition to the
Earth product contract. Google offers native automated analysis inside Earth,
and the Geo guidelines permit some attributed Earth captures. This workflow
still treats the basemap as `manual-reference` evidence and catalog/generated
outputs according to their product-specific copy rules. Do not describe that
preference as a universal Google prohibition.

## Contents

1. Authority and access boundary
2. Current browser capabilities
3. Archaeological observation pass
4. Data and project handling
5. Provenance and attribution
6. Captures and publication
7. Automation and computation boundary
8. Official sources

## Authority and access boundary

Use the official interface at <https://earth.google.com/web/> and follow the
available browser-control skill before interacting with it. Keep the pass in
the visible foreground at a human review scale.

Public exploration authorizes only an unauthenticated, read-only check.
Explicitly obtain authorization naming Google Earth and the browser session
before using a signed-in account. Creating or editing projects, importing
files, adding layers or placemarks, changing sharing, exporting, or requesting
access are mutations and require the user to request that specific action.
Submitting an Imagery Search or Ask Google Earth prompt, supplying Classify
training labels, generating an analysis layer, and requesting an imagery update
are also mutations.
Never send a share invitation, request project access, or publish a link on the
user's behalf without separate authorization.

Earth may open directly into an existing signed-in session. If that session
was not authorized for the case, stop before searching, reading projects, or
opening account-scoped layers. Switch to a clean public browser session when
one is available. Never sign out, switch accounts, or change account state to
work around the authorization gate.

If browser control is unavailable, report that live inspection is blocked.
Official documentation may establish the product contract, but it does not
prove the imagery, layer, attribution, or UI state for a particular place.
Never substitute HTTP fetching, hidden endpoints, standalone browser
automation, or search-result snippets for the requested Earth view.

Preserve exact candidate points, candidate footprints, research AOIs, image
points, and image footprints in the Earth handoff. Omit a feature only when a
specific law, source licence, custodian, community protocol, or user-selected
restriction requires it. A Drive or shared project remains an external
mutation and requires the user's explicit authorization.

## Current browser capabilities

Use only capabilities visible in the current interface:

| Need | Browser action | Evidence limit |
| --- | --- | --- |
| Resolve a place | Search a name, address, or authorized coordinate | Confirm gazetteer identity elsewhere when ambiguity matters |
| Inspect form | Pan, zoom, rotate, tilt, and compare 2D with 3D | 3D imagery can combine several acquisition dates |
| Reduce clutter | Use Satellite or Map plus Clean, Exploration, Everything, or Custom detail | Never hide, crop, or cover attribution |
| Compare time | In Satellite mode, use Historical imagery or Timelapse | Coverage and available dates vary by place and zoom |
| Inspect modeled change | Open an authorized existing Detect change layer, or create one only after a specific mutation request | Experimental AI-derived heatmap; not imagery, ground truth, or an archaeological classifier |
| Search imagery semantically | Use Imagery Search only after authorizing its prompt and AOI | Experimental, web-only, US-only at the current contract; at most 30 approximate matches |
| Train a native classifier | Use Classify only after authorizing labels, training, and project output | Experimental random forest over 10 m AlphaEarth embeddings; not independent validation |
| Ask a spatial question | Use Ask Google Earth only after authorizing prompt transmission | Experimental; prompts may be human-reviewed and generated output can be inaccurate |
| Read metadata | Inspect the status area for date/range, coordinates, altitude, and providers | Record `unavailable` rather than inventing missing metadata |
| Estimate scale | Measure a line, path, or closed polygon in top-down view | Results and terrain statistics are inferred, not survey-grade |
| Preserve context | Copy the current Earth URL | Keep exact view state; record any named restriction that requires omission |
| Inspect data | Open a catalog layer's details or an authorized imported layer | Catalog data cannot be downloaded, exported, or copied |
| Explore a permitted capture | Run a bounded local check on one or a few user-requested attributed static captures | Record the use basis and hash; do not turn captures into a systematic dataset |

Historical imagery is available in current web Earth. It requires the
Satellite basemap and turns off 3D buildings. Treat each selected date as a
separate manual view. Do not infer that a dot on the timeline is complete
coverage, or that no visible mark means archaeological absence.

Do not treat a timeline label as an exact acquisition timestamp. A selected
date means imagery was captured on or before that date; for a displayed range,
the `Imagery Date` is the oldest possible date. Mosaic dates can change under
the cursor, seams may have no date, and 3D imagery has no single collection
date because it combines aerial images from several dates.

Measurements can report length, heading, perimeter, area, and inferred terrain
elevation or slope summaries, depending on feature type. Record the displayed
unit and view state. Completed line or path measurements may include an
elevation-profile chart. Length and area do not account for elevation change,
and Earth does not provide survey-grade control or a two-point elevation
difference.

Detect change is an experimental, project-scoped tool. At the current product
contract it compares annual AlphaEarth Foundations Satellite Embedding data for
two years between 2017 and 2025, produces a nominal 10 m change heatmap, and
accepts an AOI up to 200 km². Recheck these limits at use time. The result
blends several geospatial modalities and may highlight moisture, flooding,
biomass, urban, or agricultural change that is not visible in the selected
optical image.

Other native analysis tools require the same derived-evidence discipline:

- **Imagery Search:** currently experimental, web-only, US-only, and limited
  to Professional plans. It returns at most 30 best matches and may return
  approximations when the requested target is absent.
- **Classify:** currently experimental and trains a random forest from
  user-supplied labels over 10 m annual AlphaEarth embeddings for 2017–2025.
  Record label provenance and never use the training result as its own test.
- **Ask Google Earth:** currently experimental and limited to English for US
  projects. A query can use at most 500 features, output may be inaccurate, and
  prompts may be human-reviewed. Never enter material governed by a specific
  confidentiality, legal, custodian, community, or user restriction.

These limits can change. Inspect the current UI badge, plan, terms, coverage,
and official documentation at use time. Data-layer, table, and generated
analysis outputs may not be downloaded, exported, or copied. Verify the named
feature's current project and storage requirements; do not assume a local KML
file can host its result.

When reproducible AlphaEarth analysis is required, leave Earth and acquire the
canonical licensed dataset through a separate authorized workflow. The current
GCS release provides 2017–2025 annual Cloud Optimized GeoTIFF embeddings under
CC BY 4.0 and requires: `The AlphaEarth Foundations Satellite Embedding dataset
is produced by Google and Google DeepMind.` The bucket is provider-pays, so do
not access it without authorization for the cloud and billing context. This is
independent acquisition, not permission to export an Earth-generated layer.

## Browser control boundary

Earth's WebGL surface may initially expose little more than an accessibility
control to semantic browser automation. Use the current browser-control skill
and one current visual state to locate visible controls. Use accessibility or
DOM state only for control targeting, then verify each result from the visible
interface.

Use accessibility or DOM-backed browser controls to target visible controls
and read text that Earth visibly presents, including the status area. Do not
inspect the WebGL canvas, hidden application state, tile URLs, service calls, or
network traffic to extract imagery or data. A transient operational view may
ground a control action; save or publish it only when the user requested a
permitted attributed capture.

## Archaeological observation pass

Perform one bounded pass:

1. Reconfirm the question, exact point and/or AOI, disclosure class, allowed
   browser session, and whether any mutation is authorized.
2. Open Explore Earth and resolve the named place. Record ambiguity or
   mismatched geography before continuing.
3. Establish a conservative reference view: north-up, top-down, Satellite,
   labels appropriate to the question, and 3D buildings off.
4. Read the displayed imagery date or range and attribution. If either is
   unavailable at that location or zoom, record that fact.
5. Inspect the requested feature in no more views than needed to answer the
   question. Useful comparisons include current versus selected historical
   dates, Clean versus roads/labels, 2D versus 3D terrain, and an authorized
   native-analysis result versus its verification imagery.
6. If scale matters, measure in top-down view and label the result
   `Google Earth estimate`. Preserve the displayed units and caveats.
7. Record a text observation before interpretation: morphology, polarity,
   orientation, approximate scale, view/date, and what changed between views.
8. Test modern and natural alternatives with licensed contextual sources.
   Google labels or catalog layers may suggest a check but do not independently
   corroborate Google's own imagery.
9. Copy a deep link only when its precision is safe for the intended audience.
10. End the Earth pass. A permitted capture may support one bounded exploratory
    check; move reproducible or systematic analysis to a canonical, licensed
    raster or vector source.

Do not traverse an AOI as a coordinate grid, repeatedly sample the status bar,
or turn the pass into systematic candidate generation. A few user-directed
views are manual reconnaissance; an enumerated search is data extraction.

## Data and project handling

Keep four data authorities distinct:

- **Google basemap or catalog content:** manual reference. Record the displayed
  source, coverage, update date, terms, plan, and experimental status. Do not
  export, copy, or reconstruct raw catalog data.
- **Imported licensed data:** the original file and custodian remain
  authoritative. Hash and register the source outside Earth, then describe
  Earth only as the visualization environment.
- **Earth annotations:** user-created interpretation or presentation, not
  source measurement. Preserve the project/KML provenance and do not promote a
  traced outline into observed evidence.
- **Google-native analysis:** experimental, derived reference output. Preserve
  the named tool, prompt or label authorization, model/dataset, scope, limits,
  plan, result count, and independent verification gap.

Local KML/KMZ can be opened without sign-in and remains in browser-local
storage. Drive projects and imported data layers upload content and require a
signed-in session. Prefer local KML for a small, non-sensitive, user-authorized
visual check. Use Drive only when the user explicitly requests cloud storage
or collaboration and the data licence and disclosure class allow it.

Current web Earth can:

- edit KML/KMZ imports of roughly up to 10,000 features as project features;
- open KML/KMZ as local browser files;
- import KML, KMZ, GeoJSON, or zipped Shapefile data as read-only cloud data
  layers optimized for datasets with 1,000,000 or more features;
- style or filter supported data-layer attributes; and
- export project annotations to KML.

Those product capabilities do not grant rights to upload, analyze, share, or
redistribute the underlying data. Record the source licence first. Do not
upload authenticated archive material or community-restricted knowledge. A
possible-new candidate is not confidential merely because it is new.

Local KML depends on browser-local storage and is not a collaborative project.
Cloud imports require a project the user owns. At the current plan contract,
Standard, Professional, and Professional Advanced offer 1 GB, 10 GB, and 20 GB
of storage, with respective single-file limits of 250 MB, 500 MB, and 500 MB.
Recheck the current plan and quota before any authorized upload.

For a catalog layer, open its detail view and record:

- exact layer title and source or custodian;
- description and geographic coverage;
- last-updated date, if displayed;
- terms of use;
- required plan and experimental status;
- filters or styles applied; and
- access time and Earth URL.

Catalog layers are dynamic, and their data cannot be downloaded, exported, or
copied. Use a linked canonical source only when that source independently
offers the needed data under a suitable licence; cite and acquire it from that
source, not from Earth.

Detect change output is a separate derived authority. Generating it requires an
open or newly created project, an AOI polygon, two comparison years, and a
`Create layer` action. Require explicit authorization for that exact mutation.
Record:

- experimental status and access plan;
- displayed model and dataset name;
- selected years, AOI description, nominal resolution, and area limit;
- generated layer title, visualization state, and access time;
- historical-imagery views used to investigate the type of change; and
- the independent licensed source required to test the interpretation.

Do not call heatmap intensity an archaeological probability. Do not export,
digitize, or feed the generated layer into local analysis. Treat it as
`manual-reference` and preserve false-positive alternatives such as soil
moisture, flooding, biomass, agricultural practice, and urban development.

Apply the same authority boundary to Imagery Search, Classify, and Ask Google
Earth. Do not download, export, copy, screenshot, or transcribe their
data-layer, table, or generated output when the product-specific terms prohibit
it. A safe claim note may record the tool, scope, visible limitation, and
provisional finding without reproducing the output.

## Provenance and attribution

Start from `assets/google-earth-observation-template.json`. Store completed
records in the case workspace. Use restricted storage only when a specific
legal, source, custodian, community, privacy, or user rule requires it.

For every Earth-derived observation, record:

- product name and official/deep-link URL;
- access time and public/authenticated session class;
- exact study-area geometry, feature roles, precision, and disclosure class;
- basemap, detail preset, 2D/3D state, heading, tilt, and camera altitude when
  relevant;
- historical-imagery state and exact displayed imagery date or range;
- the complete on-screen attribution text and every named provider;
- any catalog layer metadata, filters, and terms;
- any native-analysis tool, prompt/label authorization, model or dataset,
  scope, limits, plan, result count, and verification state;
- displayed measurement, units, feature type, and estimate caveat;
- observed facts, inference, alternatives, and visibility limits; and
- whether no capture, an attributed static capture, or only a text note was
  retained.

Attribution rules:

1. Transcribe attribution as displayed for that view. Do not replace a named
   third-party provider with `Google`.
2. Cite imported data to its original custodian and licence, followed by
   `visualized in Google Earth`; Google is not the data author merely because
   Earth rendered it.
3. Cite an Earth catalog layer to the exact layer, displayed data source,
   terms, access date, and Earth interface. Mark it `manual-reference` unless a
   separate licence and canonical source authorize local analysis.
4. Record imagery dates as displayed, including a range or `unavailable`.
   Google imagery is not real-time, and 3D imagery may not have one collection
   date.
5. Keep attribution adjacent to every retained image. A bibliography entry
   elsewhere does not repair attribution cropped from the image.

## Captures and publication

Prefer a text observation and deep link. Capture an image only when the user
requests an evidence image and the intended use is permitted.

Visible attribution does not override a catalog, data-layer, table, or
generated-output prohibition on copying. Do not capture those products unless
their specific current terms allow the exact intended use.

For a Google Earth static capture:

- keep the full Google and third-party attribution visible, legible, and
  adjacent;
- retain only a small number needed for the non-commercial research,
  educational, news, recreational, or instructional purpose;
- record the intended use, capture time, URL, imagery date, and file hash;
- do not materially alter the imagery; label a simulation, projection, or
  hypothetical overlay clearly;
- never use Earth imagery for commercial or promotional output; and
- do not embed Google Earth in a site or app.

These are the plugin's conservative default capture limits, not a restatement
of every medium-specific Google licence. Recheck the current Geo guidelines and
intended print, web, film, educational, news, or commercial use before release.

Street View has stricter rules: do not screenshot, extract, download, stitch,
digitize, or analyze Street View imagery. Inspect it only in the official
interface when the case authorization and question require it.

Before release, apply only restrictions actually recorded for the case.
Visible attribution satisfies attribution, not unrelated legal, privacy, or
community obligations.

### Bounded local analysis

Local computer vision is not inherently prohibited. Decide from the source,
the exact use, and the terms that apply to that source:

- Prefer user-owned, open, or separately licensed originals. Analyze imported
  data from its canonical file, not merely from Earth's rendering.
- Canonical AlphaEarth Foundations GCS assets are published under CC BY 4.0.
  Preserve the dataset's required attribution and provenance.
- A small, properly attributed static Earth capture may support a bounded,
  user-requested exploratory check when the current Earth terms and Geo
  guidelines permit both the capture and intended use.
- Preserve the unaltered capture and attribution, hash the file, record the
  view/date/providers/use basis, and write derived masks or overlays to
  separate files.
- Treat results from a rendered capture as exploratory and
  non-reproducible. Do not call them survey measurements, independent
  corroboration, or a reusable detection dataset.

For an AOI sweep, repeatable computation, feature corpus, training/evaluation
set, or reusable dataset, use the canonical licensed source or obtain a licence
covering that exact workflow. A screen-capture permission is not permission to
mass-download, reconstruct, or create a substitute Google dataset.

## Automation and computation boundary

The following list is an Indiana Jones workflow boundary for archaeological
evidence integrity and licensing. Google independently prohibits unauthorized
copying, bulk feeds, substitute datasets, and specified downstream uses while
offering its own native analysis tools inside Earth.

Never:

- inspect or call tile, imagery, scene, catalog, or hidden network endpoints;
- scrape hidden application state or automate DOM/canvas extraction to collect
  map content, coordinates, dates, elevations, or provider data;
- enumerate coordinates, dates, zoom levels, layers, or camera positions to
  assemble a corpus;
- mass-download, bulk-capture, stitch, cache, or reconstruct Google content;
- build a feature corpus, model evaluation set, training set, or substitute
  imagery dataset from Earth captures without a licence covering that use;
- run OCR, computer vision, feature extraction, model evaluation, or training
  on Street View or copy-prohibited catalog/generated outputs;
- digitize an archaeological dataset from Google basemap, catalog, or Street
  View content without a licence covering the exact systematic use;
- export, copy, or reconstruct raw catalog-layer data;
- reconstruct terrain, buildings, meshes, textures, or other 3D products;
- remove or obscure attribution; or
- treat absence from Earth, its timeline, or its catalog as evidence of
  archaeological absence.

## Official sources

Recheck these at use time because the web product and catalog change:

- [Google Earth web documentation](https://developers.google.com/maps/documentation/earth)
- [Navigate the globe](https://developers.google.com/maps/documentation/earth/navigate-the-globe)
- [Basemap settings](https://developers.google.com/maps/documentation/earth/basemap-settings)
- [Imagery dates, altitude, and coordinates](https://developers.google.com/maps/documentation/earth/imagery-dates-alt-coord)
- [Historical imagery](https://developers.google.com/maps/documentation/earth/historical-imagery)
- [How Earth imagery dates work](https://support.google.com/earth/answer/6327779)
- [Detect change (Experimental)](https://developers.google.com/maps/documentation/earth/detect-change)
- [Imagery Search (Experimental)](https://developers.google.com/maps/documentation/earth/imagery-search)
- [Classify (Experimental)](https://developers.google.com/maps/documentation/earth/classify)
- [Ask Google Earth](https://developers.google.com/maps/documentation/earth/gemini/overview)
- [AlphaEarth Foundations canonical GCS data](https://developers.google.com/earth-engine/guides/aef_on_gcs_readme)
- [Measurements](https://developers.google.com/maps/documentation/earth/measure-distances)
- [Project management](https://developers.google.com/maps/documentation/earth/manage-projects-homescreen)
- [Import data](https://developers.google.com/maps/documentation/earth/import-kml)
- [Earth data types](https://developers.google.com/maps/documentation/earth/projects-kml)
- [Earth plans and quotas](https://developers.google.com/maps/documentation/earth/earth-plans)
- [Data-layer metadata and restrictions](https://developers.google.com/maps/documentation/earth/learn-about-data-layers)
- [Pre-GA terms](https://developers.google.com/maps/documentation/earth/pre-ga-terms)
- [Request an imagery update](https://developers.google.com/maps/documentation/earth/tell-us-about-a-problem)
- [Google Earth Additional Terms](https://www.google.com/help/terms_maps-earth/)
- [Google Geo usage and attribution guidelines](https://about.google/brand-resource-center/products-and-services/geo-guidelines/)

This workflow was checked against official documentation on 2026-07-24. A
current live interface check remains required for case-specific claims.
