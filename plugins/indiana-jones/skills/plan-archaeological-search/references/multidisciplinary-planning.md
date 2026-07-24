# Multidisciplinary archaeological area planning

## Architectural boundary

Use three graphs:

1. a **landscape-evidence graph** for sources, claims, processes, places,
   proxies, observations, alternatives, and hypotheses;
2. a **search/task graph** for dependencies, permissions, grid cells, controls,
   budgets, and next actions;
3. a **stratigraphic graph** only for direct physical context relations.

The first two are Research Sequence Graphs. They may borrow Harris's discipline
of explicit ordering, but they are not Harris Matrices.

Harris's formal system represents relative stratigraphic sequence. Its basic
possibilities are no direct relation, superposition, and correlation of
separated parts of a once-whole unit. A source saying that a suburb is “later,”
a map overlay, or a satellite anomaly does not establish physical
superposition. Use
[Harris, *Principles of Archaeological Stratigraphy*, 2nd ed.](https://harrismatrix.com/wp-content/uploads/2019/01/Principles_of_Archaeological_Stratigraphy.-2nd-edition.pdf),
[May, “The Matrix”](https://doi.org/10.11141/ia.55.8), and
[CRMarchaeo](https://cidoc-crm.org/crmarchaeo/ModelVersion/version-2.1) when
actual contexts enter the case.

## What each discipline contributes

| Discipline | Question and output | Boundary |
| --- | --- | --- |
| Landscape archaeology | How activities, routes, resources, settlement, and preservation relate across an area and through time | Suitability is not site presence |
| Urban morphology | Street systems, plots, blocks, building fabric, plan units, fringe belts, accretion, transformation, and persistence | Do not universalize concentric growth or one national town model |
| Historical geography | Administrative limits, route systems, land tenure, map series, settlement hierarchies, changing names and boundaries | Historical maps are surveyed arguments with scale and purpose, not transparent truth |
| Geoarchaeology | Palaeotopography, sedimentation, erosion, waterlogging, burial depth, made ground, truncation, and proxy preservation | Surface silence may coexist with deep or sealed deposits |
| Architectural/building archaeology | Fabric sequence, reuse, repair, building plots, standing remains, and direct physical relationships | Stylistic date is not automatically stratigraphic sequence |
| Archaeological science/remote sensing | Which material process can produce a measurable proxy at the sensor's scale and conditions | An anomaly is candidate evidence, not cultural attribution |
| Documentary history | Dated claims, actors, events, institutions, bias, and contradictions | Several retellings of one text remain one origin family |
| Anthropology and sociology | Social practice, institutions, labor, inequality, exclusion, migration, memory, identity, and living governance | Present categories cannot be projected backward without evidence |
| Toponymy and historical linguistics | Name forms, transfers, semantic shifts, local language, and possible landscape associations | Folk etymology and renamed/moved places are alternatives |
| Community knowledge | Community-defined significance, access, attribution, and landscape history | Community authority governs use and disclosure |

UNESCO's
[Historic Urban Landscape Recommendation](https://www.unesco.org/en/legal-affairs/recommendation-historic-urban-landscape-including-glossary-definitions)
frames the city as layered topography, geomorphology, hydrology, built fabric,
infrastructure, land use, visual relations, social practices, and cultural and
economic values. This is the planning frame: monuments are only one layer.

Historic England's
[Historic Area Assessment guidance](https://historicengland.org.uk/images-books/publications/understanding-place-historic-area-assessments/)
combines archaeology, history, historical geography, landscape history,
architecture, records, maps, GIS, and field observation. Its
[Historic Landscape Characterisation](https://historicengland.org.uk/research/methods/characterisation/historic-landscape-characterisation/)
treats the whole landscape as a dynamic palimpsest rather than leaving
uninteresting blanks.

## AOI hierarchy and adaptive cells

Use:

- `focus`: the place or uncertainty envelope supplied by the user;
- `context`: a question-relevant catchment, shoreline, route network,
  viewshed, settlement hinterland, resource zone, or event extent;
- `controls`: comparable settings outside narrative hotspots and known-site
  concentrations.

Administrative radii are convenient but often archaeologically meaningless.
Use them only as an initial source-discovery envelope.

Begin at the coarsest useful evidence scale. Partition by landscape character,
morphogenetic plan unit, parcel/block, catchment, route segment, landform,
visibility unit, or a declared projected grid. Preserve why each boundary
exists. Subdivide positive and unresolved cells, plus a systematic sample of
negative cells.

For urban subsurface potential, include boreholes, geotechnical logs, previous
interventions, natural topography, made ground, truncation, waterlogging, and
depth. Historic England's
[urban deposit modelling review](https://historicengland.org.uk/research/results/reports/88-2022)
shows why surface form alone is inadequate.

## Settlement and city hypothesis families

Do not begin with a single growth story. Test at least the locally plausible
subset of:

- planned foundation or imposed replanning;
- polycentric settlement and later coalescence;
- route-, gate-, crossing-, waterfront-, or resource-led growth;
- older core beneath, beside, or displaced from the later centre;
- defensive circuits, extramural strips, markets, production, waste, water
  supply, and burial/ritual margins;
- plot persistence, backland infill, fringe belts, satellite settlements, and
  abandoned margins;
- contraction, disaster, rebuilding, reuse, relocation, and reoccupation;
- shoreline or river migration, drainage change, erosion, burial, or
  waterlogging;
- administrative redefinition, cadastral inheritance, modern utilities, or
  planning artefact.

For each phase reconstruct physical, social, economic, institutional, and
intangible layers. Do not assume every mapped change is population growth.

## Historical events and conflict landscapes

Extract every locatable defining feature from each account and retain author,
date, intent, bias, spatial precision, and origin family. Reconstruct period
terrain, routes, crossings, obstacles, visibility, cover, mobility, settlement,
season, weapons/technology, supply, camps, hospitals, movement, retreat,
destruction, rebuilding, commemoration, and burial.

The US National Park Service
[battlefield survey manuals](https://www.nps.gov/orgs/2287/manuals.htm) combine
documentary research, mapping, military terrain analysis, defining features,
and integrity assessment. KOCOA—key terrain, observation/fields of fire, cover,
obstacles, and avenues of approach/withdrawal—is a consistency test. It is not
proof that a narrated movement happened, and it must use the period's
technology, doctrine, mobility, season, and terrain.

Potential conflict dead, burials, sacred locations, and personal data are
sensitive. Do not guide metal detecting, artefact collection, access, or public
triangulation.

## Culture, identity, and social inference

Replace “Culture X lived here, therefore search here” with:

1. Which dated material tradition, documented community, or scholarly label is
   meant?
2. What specific activity is proposed?
3. Which sources establish its time and spatial range?
4. What material process might follow?
5. What could survive and be observed?
6. Which other groups, activities, natural processes, or classification
   histories could produce the same pattern?

Archaeological culture, ethnicity, language, polity, ancestry, and modern
identity are not interchangeable. Use source wording such as
`actor/group-as-described`, record disputes, and avoid essentializing a
community.

Treat oral and community knowledge as a separate authority lane, not a weak
lead to be harvested. Apply the
[CARE Principles](https://www.gida-global.org/careprinciples) and the
[Society for American Archaeology ethics principles](https://www.saa.org/Member/SAAMember/Career-and-Practice/Principles-of-Archaeological-Ethics.aspx).
Agree purpose, access, attribution, precision, retention, withdrawal, and
publication with the appropriate community.

## Predictive planning and controls

Every high-priority cell requires a mechanism:

```text
human activity or natural process
  -> material consequence
  -> survival or destruction process
  -> present observable proxy
  -> discriminating method under stated conditions
```

Predictive modelling without behavioral and archaeological theory can turn
environmental correlation into circular administrative certainty. See
[Verhagen and Whitley 2012](https://doi.org/10.1007/s10816-011-9102-7).
Use the model to choose tests, not to declare low-ranked land empty.

Controls should include:

- similar geology, soil, relief, crop/land cover, and sensor conditions outside
  the predicted zone;
- different dates, seasons, phenological stages, and illumination;
- cloud, no-data, seam, compression, orthorectification, and resampling checks;
- modern drains, utilities, roads, parcels, forestry, extraction, and field
  boundaries;
- geological and geomorphological analogues;
- shifted/rotated morphology templates;
- documentary source-dependency checks;
- geographically separated positives and hard negatives for validated
  detectors.

Avoid random neighboring pixel splits: spatial autocorrelation can exaggerate
validation. Hold out whole sites or geographic blocks and report the full area
and review denominator.

## Desk-study completeness

The
[CIfA desk-based assessment standard](https://www.archaeologists.net/sites/default/files/2023-11/CIfA-SandG-DBA-2020.pdf)
supports a required source-gap register: define aims and area, assess relevance
and reliability, keep full records, list unconsulted sources and consequences,
and identify further evaluation. A desk study defines what is reasonably
knowable from current evidence; it does not establish presence or absence.
