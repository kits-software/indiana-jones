---
name: research-google-earth
description: Use Google Earth in the browser for bounded, attributed archaeological reconnaissance and geospatial source discovery. Use when Codex is asked to open or inspect Google Earth, compare current or historical imagery, navigate 2D/3D terrain, estimate distance or area, inspect catalog or Google-native experimental analysis outputs such as Detect change, Imagery Search, Classify, or Ask Google Earth, visualize authorized KML/KMZ/GeoJSON/Shapefile data, copy an exact Earth link, prepare a limited attributed evidence capture, or run bounded local analysis on an input whose exact use is permitted. Do not use for bulk tile or canvas scraping, systematic screenshotting, hidden API access, coordinate harvesting, copy-prohibited catalog export, unlicensed dataset construction, or disclosure that violates a specific legal, custodian, community, or user restriction.
---

# Research with Google Earth

Use the official Google Earth web interface as a manual research instrument,
not as an imagery API or authoritative archaeological dataset.

## Required reading

Read:

- [the complete browser workflow](../indiana-jones/references/google-earth-browser.md);
- [web, account, and location ethics](../indiana-jones/references/ethics-and-web-research.md); and
- [the evidence contract](../indiana-jones/references/evidence-contract.md).

Use the available browser-control skill before opening Earth. If no supported
browser is connected, report the live-UI block and do not substitute HTTP
fetches, hidden endpoints, or standalone automation as case evidence.

## Contract the pass

Establish the research question, exact point and/or AOI when known, stopping
condition, disclosure class, and allowed source role. Public exploration
permits only a small read-only pass.

Require explicit authorization naming Google Earth and the browser session
before using a signed-in account. Also require the user to request the exact
mutation before creating or editing a project, importing data, adding
annotations or layers, submitting a native-analysis prompt or training labels,
exporting, sharing, requesting access, or requesting an imagery update.

If Earth opens in a signed-in session that was not authorized, stop before
searching, reading projects, or opening account-scoped layers. Switch to a clean
public browser session when one is available; never sign out, switch accounts,
or change account state to manufacture unauthenticated access.

Preserve candidate points, candidate footprints, research AOIs, image points,
and image footprints in Earth/KML handoffs. Omit a feature only when a specific
law, source licence, custodian, community protocol, or user-selected
restriction requires it, and record the authority and reason. Uploading a
feature to a Drive-backed project is a separate mutation and still requires
the user's explicit authorization.

## Run one bounded observation

1. Open <https://earth.google.com/web/> and use Explore Earth.
2. Search the place or exact research coordinate and resolve ambiguity.
3. Establish a north-up, top-down Satellite reference view with 3D buildings
   off and a suitable detail preset.
4. Record the displayed imagery date or `unavailable`, complete attribution
   text, providers, view state, access time, and safe Earth URL.
5. Inspect only the views needed for the question: current versus selected
   historical dates, Clean versus contextual labels, 2D versus 3D terrain, or
   an already-authorized Google-native analysis layer or result.
6. Measure only when scale matters. Record the displayed units and label
   results as inferred Google Earth estimates, not survey measurements.
7. Write the direct observation before interpretation. Name at least two
   modern or natural alternatives and the licensed source needed to test them.
8. Stop the Earth pass. Move reproducible or systematic pixel/vector analysis
   to a canonical licensed source; a bounded permitted capture may support a
   separately recorded exploratory local check.

Do not turn the pass into an enumerated sweep across coordinates, dates,
layers, zooms, or camera positions. Use browser control on visible interface
state; do not inspect hidden application state, tile URLs, service calls, or
network traffic to extract map content.

Use browser accessibility or DOM state only to locate visible interface
controls and read metadata that Earth visibly presents. A transient browser
view may ground a control action. Retain it as evidence only when the user
requested a capture and the exact use is permitted.

## Handle data without losing authority

Treat Google basemap and catalog content as `manual-reference`. Inspect a
catalog layer's title, source, coverage, update date, terms, plan, and
experimental status. Catalog data cannot be downloaded, exported, or copied;
follow a canonical source link only when that source independently offers data
under a suitable licence.

Treat Google-native analysis output as a Google-generated, experimental derived
reference, not a sensor measurement, canonical dataset, or independent
archaeological classifier. Detect change, Imagery Search, Classify, and Ask
Google Earth can create or analyze project data and may transmit prompts,
labels, or AOIs. Require explicit authorization for the named feature and exact
mutation. Verify its current project, storage, and plan requirements; do not
assume local KML can host a native-analysis result. Never enter confidential or
sensitive-site information. Record the displayed model or dataset, scope,
  limits, plan, result count, layer status, and verification views; verify the
  result against historical imagery and an independent licensed source. Do not
download, export, copy, or capture a catalog or generated output when its
product terms prohibit that action.

For user-owned or openly licensed imports, hash and register the original file
outside Earth. Cite its original custodian and licence, followed by
`visualized in Google Earth`. Do not describe Google as the author of imported
data.

Local computation is a source-and-use decision, not a blanket prohibition:

- analyze user-owned, openly licensed, or separately licensed source data under
  its recorded licence, preferably from the canonical original rather than an
  Earth rendering;
- use canonical AlphaEarth Foundations GCS assets under their stated CC BY 4.0
  terms and required attribution when that dataset fits the question;
- a small, attributed Google Earth static capture may support a bounded,
  user-requested exploratory local check only when the current Earth terms and
  Geo guidelines permit that capture and intended use;
- preserve the unaltered capture, attribution, URL, displayed date, providers,
  access time, use basis, and hash, and store any computed overlay separately;
- label capture-derived results as non-reproducible exploratory evidence, not a
  survey, discovery, reusable dataset, model benchmark, or training corpus; and
- never run local analysis on Street View, a copy-prohibited catalog/data
  layer, or a Google-generated output whose product terms forbid copying.

For systematic coverage, repeatable science, model evaluation, or training,
acquire the canonical licensed dataset or a separate licence that covers the
exact workflow. Do not use Earth automation to assemble a substitute imagery,
terrain, building, coordinate, or provider dataset.

Local KML stays in browser storage. Drive projects and imported data layers
upload content. Use either only when the data rights, disclosure class, and
case-specific authorization permit it.

## Record and attribute

Copy
`../indiana-jones/assets/google-earth-observation-template.json` into the
case workspace and complete it. Preserve:

- access/session class and mutation authorization;
- safe study-area label and disclosure class;
- basemap, detail, camera, 2D/3D, and historical-imagery state;
- displayed date or range, attribution, providers, altitude, and measurements;
- catalog-layer sources, terms, styles, and filters;
- Google-native analysis feature, prompt/label authorization, scope, limits,
  model or dataset, result count, and verification state;
- observed facts, inference, alternatives, and limitations; and
- capture purpose, hash, and attribution state when a capture is permitted;
  plus the operation, use basis, and limits for any exploratory local analysis.

Prefer a text note and exact deep link. If the user requests a permitted,
non-commercial static Google Earth capture, retain all Google and third-party
attribution legibly beside the imagery and keep the number of captures small.
Never screenshot, extract, stitch, digitize, or analyze Street View imagery.

## Completion gate

Return:

- the provisional finding and strongest alternative;
- the Earth view/date and measurement limitations;
- exact source and provider attribution;
- an exact deep link or a named restriction that required it to be withheld;
- the canonical licensed source required for analysis; and
- any browser, authorization, coverage, or metadata block.

Do not claim discovery, absence, survey accuracy, independent corroboration, or
live UI proof that the completed pass did not establish.
