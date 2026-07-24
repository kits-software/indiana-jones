# Archaeological Remote Sensing: Research Reference

Last source check: **2026-07-24**.

This reference supports responsible archaeological prospection, mapping, and
monitoring. It is not a fieldwork permit, a substitute for local expertise, or
evidence that a buried site exists.

For the current technical survey of optical time series, spectral indices,
phenology, PCA/MNF/RX, supervised methods, foundation models, SAR,
hyperspectral processing, reusable software, licences, datasets, and the
bundled multi-date optical baseline, read
[satellite-analysis.md](satellite-analysis.md).

## Contents

- [Evidence language](#evidence-language)
- [Foundational reading](#foundational-reading)
- [Proxy-first interpretation](#proxy-first-interpretation)
- [Sensing and reconstruction methods](#sensing-and-reconstruction-methods)
- [Computational methods](#computational-methods)
- [Validation](#validation)
- [Uncertainty and reporting](#uncertainty-and-reporting)
- [Public evidence, protected data, and field conduct](#public-evidence-protected-data-and-field-conduct)
- [Source register](#source-register)

## Evidence language

Use these labels when reasoning or writing results:

- **[CONFIRMED]**: directly supported by an authoritative specification,
  guidance document, or repeatable physical principle cited here.
- **[REPORTED]**: demonstrated by a cited primary study in its study area. It
  is not automatically transferable to another sensor, season, soil, crop, or
  landscape.
- **[INFERENCE]**: an interpretation of a proxy or a recommended conclusion
  drawn from multiple facts. It requires independent testing.
- **[CURRENT 2026-07-23]**: checked against a live official source on the date
  above. Mission composition, products, standards, and access conditions can
  change; recheck before acquisition or publication.

Do not turn **[REPORTED]** performance into **[CONFIRMED]** general
performance. Do not turn an **[INFERENCE]** into a site identification by
removing the qualifier.

## Foundational reading

These books and guides provide orientation and synthesis; they are not
independent confirmation of a new candidate.

- Sarah Parcak, *Satellite Remote Sensing for Archaeology* (2009), a
  landscape-to-site introduction to optical satellite prospection
  ([publisher DOI][B1]).
- Rachel Opitz and David Cowley, eds., *Interpreting Archaeological
  Topography: 3D Data, Visualisation and Observation* (2013), especially for
  LiDAR, 3D data, and interpretation ([publisher page][B2]).
- Žiga Kokalj and Ralf Hesse, *Airborne Laser Scanning Raster Data
  Visualization: A Guide to Good Practice* (2017), an open technical guide to
  DEM visualization choice and parameters ([publisher DOI][B3]).
- Włodzimierz Rączkowski, "Metody w archeologii" (2012) and "Power
  and/or Penury of Visualizations" (2020), for the non-neutrality of
  acquisition, processing, documentation, and visualization choices
  ([page-indexed synthesis][B4], [open article][B5]).
- Historic England, *Using Airborne Lidar in Archaeological Survey: The Light
  Fantastic* (2018), operational guidance and case studies ([A4]).
- Historic England, *Photogrammetric Applications for Cultural Heritage*
  (2017), acquisition, processing, and survey-quality guidance for
  photogrammetry and structure from motion ([A5]).
- **[CURRENT 2026-07-23][CONFIRMED]** Historic England's current
  *Standards and Guidance for Aerial Investigation and Mapping Projects* was
  published on 2026-06-30. Use it for systematic interpretation, mapping,
  records, and GIS deliverables in its jurisdiction ([A7]).

## Proxy-first interpretation

### Core rule

**[CONFIRMED]** Almost every method below measures a surface or near-surface
property affected by many archaeological and non-archaeological processes.
It normally detects a **proxy anomaly**, not a buried object.

| Observation | Measured proxy | Possible archaeological cause | Common non-archaeological causes |
| --- | --- | --- | --- |
| Crop/parch mark | Growth, chlorophyll, biomass, or moisture contrast | Ditch, pit, wall, compacted floor, or robbed foundation changes rooting depth or water supply | Geology, frost cracks, drains, pipes, irrigation, fertilizer, weeds, disease, tramlines |
| Soil mark | Colour, texture, or moisture contrast in bare/ploughed soil | Plough exposes or redistributes fill, masonry, burnt material, or former bank/ditch | Geology, recent earthmoving, field drainage, erosion, soil management |
| Shadow/earthwork mark | Surface form under directional illumination | Bank, ditch, mound, platform, hollow way | Natural microtopography, modern extraction, forestry, drainage |
| Spectral anomaly | Wavelength-dependent reflectance | Altered vegetation, soil, minerals, moisture, or surface material | Crop variety, phenology, soil type, illumination, atmosphere, mixed pixels |
| SAR anomaly | Roughness, geometry, moisture, or dielectric contrast | Earthwork, surface scatterer, moisture pattern, disturbance, or rare shallow dry-sand response | Tillage, rain, vegetation, incidence angle, speckle, layover, double bounce |
| LiDAR/DEM form | Elevation and surface geometry | Surviving bank, ditch, mound, terrace, platform, hollow way | Geology, tree throw, forestry, drainage, roads, interpolation/classification error |
| Thermal anomaly | Apparent temperature and thermal inertia | Shallow masonry, void, pit fill, road, or moisture contrast | Shade, emissivity, vegetation, soil moisture, wind, cloud, topography |
| SfM model form | Reconstructed visible surface | Exposed fabric, earthwork, erosion, or condition change | Texture failure, vegetation motion, reflections, shadows, camera/calibration error |

**[INFERENCE]** A geometric anomaly repeated in independent dates or
modalities is usually a stronger candidate than a one-date anomaly, but
coincident modern land use or shared processing artifacts can still create
agreement.

Use this claim form:

> Method X detected a proxy anomaly of type Y, under acquisition conditions Z,
> with quantified error U. It is a candidate for expert review and independent
> validation.

Avoid:

> The satellite/LiDAR/AI found a buried temple.

### Candidate lifecycle

1. Define the archaeological question and expected physical proxy.
2. Confirm that spatial, spectral, temporal, and radiometric resolution can
   express that proxy.
3. Process the data with provenance and quality masks.
4. Generate candidates without assigning archaeological identity.
5. Compare independent dates, sensors, maps, geology, land use, and known
   modern infrastructure.
6. Conduct expert interpretation and sensitivity review.
7. Validate with authorized non-invasive field methods, geophysics, and only
   where justified and permitted, excavation.
8. Publish evidence, uncertainty, and access-controlled location information.

## Sensing and reconstruction methods

### Aerial RGB and historic photography

- **Signature:** crop/parch marks, soil marks, shadows, standing earthworks,
  exposed structures, erosion, looting, and landscape change.
- **Methods:** systematic visual interpretation; multi-date comparison;
  vertical/oblique image reading; contrast and colour enhancement; stereo
  viewing; orthorectification; feature transcription into GIS.
- **Prerequisites:** seasonally useful imagery, adequate scale and sharpness,
  camera/source metadata, terrain model, control, and archives spanning
  different crops, moisture conditions, and sun angles.
- **Failure modes:** one-season visibility; haze and shadow; image distortion;
  missing metadata; overlapping phases; confirmation bias; geology, drains,
  utilities, irrigation, and agricultural treatment imitating monuments.
- **Claim boundary:** **[CONFIRMED]** buried features can alter soil moisture
  and crop growth, but the resulting mark is not unique to archaeology
  ([A2]). **[INFERENCE]** shape and context suggest a feature class; they do
  not establish date or function.
- **Sources:** Historic England's aerial-photo and cropmark guidance
  ([A1], [A2], [A3]); QuickBird crop-mark case study ([P1]).

### UAV and very-high-resolution optical imaging

- **Signature:** the same visible proxies as aerial RGB, often at centimetric
  ground sampling distance; useful for site condition, exposed fabric,
  vehicle tracks, and looting disturbance.
- **Methods:** planned grid/cross-grid acquisition, radiometric targets where
  needed, orthomosaic production, multi-date change detection, and manual or
  machine-assisted mapping.
- **Prerequisites:** lawful flight, landowner/heritage authorization, safe
  operating conditions, calibrated camera, adequate overlap, GCP or RTK/PPK,
  and independent checkpoints.
- **Failure modes:** rolling shutter, autofocus/exposure changes, wind,
  vegetation motion, glare, repetitive texture, shadows, weak control, and
  false precision from small pixels.
- **Claim boundary:** centimetric imagery improves sampling, not interpretive
  uniqueness. A crisp geometric crop mark remains a proxy.
- **Sources:** Historic England geospatial specifications and photogrammetry
  guidance ([A5], [A6]); UAV multispectral crop-mark case study ([P4]).

### Multispectral optical

- **Signature:** vegetation vigour/stress, chlorophyll, red-edge response,
  soil/background contrast, and moisture differences.
- **Methods:** surface-reflectance preparation; band ratios; NDVI
  `(NIR - Red) / (NIR + Red)`; simple ratio; SAVI/EVI; red-edge and moisture
  indices; PCA; decorrelation stretch; edge detection; multi-date composites.
- **Prerequisites:** bands that straddle the relevant response, atmospheric
  correction, cloud/shadow masks, reliable co-registration, appropriate
  phenological timing, and field/context data.
- **Failure modes:** index saturation, crop variety and management, soil
  background, clouds/haze, BRDF/illumination, coarse/mixed pixels, and a
  useful temporal window lasting only days.
- **Claim boundary:** **[REPORTED]** different vegetation indices and temporal
  windows perform differently across case studies ([P2], [P3], [P4]).
  **[INFERENCE]** there is no universally best archaeological index or date;
  select and validate locally.

### Hyperspectral

- **Signature:** narrow-band vegetation, soil, mineral, pigment, weathering,
  and moisture responses; sometimes subtle anomalies not separable in broad
  bands.
- **Methods:** radiometric and atmospheric correction; bad-band removal;
  dimensionality reduction with PCA/MNF or nonlinear PCA; spectral angle
  mapper; minimum-distance classification; matched filtering; spectral
  unmixing; anomaly detection; physically grounded spectral libraries.
- **Prerequisites:** high signal-to-noise ratio, calibration panels or
  defensible reflectance processing, precise co-registration, sufficient
  spatial resolution, and representative reference spectra/backgrounds.
- **Failure modes:** high dimensionality with few labels, spectral mixing,
  sensor drift, atmosphere, illumination, vegetation and moisture
  variability, overfitting, and distortion introduced by sharpening or
  resampling.
- **Claim boundary:** **[REPORTED]** airborne hyperspectral imagery and
  nonlinear PCA have exposed archaeological proxy anomalies in specific
  study areas ([P5], [P6]). Transfer requires new validation.

### Sentinel-2 and Landsat

- **Best fit:** regional screening, multi-year phenology, large crop/soil
  marks, palaeochannels, land-use context, and condition/change monitoring.
  Individual small features may be subpixel.
- **Methods:** analysis-ready surface reflectance; QA masking; harmonized
  time series; seasonal/percentile composites; indices; PCA; change detection;
  candidate ranking followed by higher-resolution review.
- **[CURRENT 2026-07-23][CONFIRMED]** Copernicus describes Sentinel-2 as a
  13-band mission with four 10 m, six 20 m, and three 60 m bands; the mission
  specification targets a five-day equatorial revisit ([A8]). Recheck current
  spacecraft and product availability before promising coverage.
- **[CURRENT 2026-07-23][CONFIRMED]** USGS lists Landsat 8 at 15 m
  panchromatic, 30 m multispectral, and 100 m thermal native sampling, with a
  16-day repeat cycle and an eight-day offset from Landsat 9 ([A9]). USGS
  Collection 2 Level-2 surface reflectance is 30 m and includes QA/scaling
  requirements ([A10]).
- **Failure modes:** clouds and cloud shadows, aerosols, temporal gaps,
  seasonal mismatch, cross-sensor band differences, mixed pixels, and
  resampling interpreted as new detail.
- **Claim boundary:** upsampling or pansharpening does not create independent
  archaeological information. **[REPORTED]** Sentinel-2 has supported
  archaeological screening in particular landscapes ([P7], [P8]); that does
  not establish a universal minimum detectable feature.

### Synthetic aperture radar

- **Signature:** surface roughness, moisture and dielectric contrast,
  scattering geometry, disturbance, and deformation; clouds and darkness do
  not prevent acquisition.
- **Methods:** radiometric calibration, orbit correction, terrain correction,
  incidence-angle normalization, speckle-aware filtering, polarization and
  frequency comparison, multi-temporal backscatter, coherence, InSAR/DInSAR,
  and change detection.
- **Prerequisites:** sensor wavelength/polarization suited to the target,
  precise geometry, a DEM, comparable acquisition geometry, moisture/weather
  context, and expert interpretation of scattering mechanisms.
- **Failure modes:** speckle, layover, foreshortening, shadow, vegetation,
  rain/soil-moisture change, tillage, double bounce, temporal decorrelation,
  and overinterpreting display contrast.
- **[CURRENT 2026-07-23][CONFIRMED]** ESA specifies Sentinel-1 as C-band SAR;
  default land Interferometric Wide mode is 250 km wide with nominal
  `5 × 20 m` ground resolution ([A11]). Those numbers are acquisition
  specifications, not a promise to resolve archaeological objects.
- **Claim boundary:** **[INFERENCE]** Sentinel-1 C-band should normally be
  treated as a surface/backscatter and change sensor, not a buried-building
  imager. **[REPORTED]** shallow subsurface mapping can occur under unusually
  dry, bare, low-loss conditions, particularly with longer wavelengths, but
  it is conditional rather than routine ([P9], [P10]).

### Airborne LiDAR

- **Signature:** surviving surface microtopography: banks, ditches, mounds,
  terraces, platforms, hollow ways, quarries, and condition change.
- **Methods:** point-cloud QA; return classification; ground filtering;
  strip/trajectory checks; DTM/DSM creation; density and no-data maps;
  visualization at several scales; manual mapping or machine-assisted
  detection.
- **Prerequisites:** sufficient ground returns and point density, known
  vertical/horizontal reference systems, classification metadata, independent
  checkpoints, and access to the point cloud when possible.
- **Failure modes:** dense understory with no ground returns, water, steep
  slopes, strip mismatch, low density, interpolation across gaps, vegetation
  classified as ground, earthworks classified away, and modern forestry or
  drainage.
- **Claim boundary:** **[CONFIRMED]** LiDAR measures returned surface
  elevations. In woodland, some pulses reach the ground through canopy gaps;
  the laser does not literally see through opaque vegetation ([A4]).
  It detects topography, not fully buried remains.
- **Sources:** authoritative survey guide ([A4]), USGS error taxonomy ([A16]),
  and the Local Relief Model paper ([P11]).

### DEM/DTM visualization and local relief

- **Signature:** positive and negative surface forms across selected spatial
  scales.
- **Methods:** hillshade and multi-direction hillshade; slope; sky-view
  factor; positive/negative openness; Local Relief Model or Simple Local
  Relief Model; trend removal; topographic position/local dominance; PCA over
  multiple hillshades; scale-space comparison.
- **Prerequisites:** a defensible bare-earth DTM, explicit cell size and
  kernel radius, no-data awareness, and visualizations preserved as derived
  products rather than source elevation.
- **Failure modes:** directional blindness, filter halos, ringing, artificial
  edges at no-data boundaries, exaggerated noise, scale suppressing the
  target, and confusing visualization values with elevation.
- **Claim boundary:** **[REPORTED]** LRM, sky-view factor, and complementary
  visualization families improve recognition in specific conditions
  ([P11], [P12], [P13], [P14]). **[INFERENCE]** require agreement across
  several parameterizations and inspect the source DTM/point cloud before
  accepting a candidate.

### Thermal infrared

- **Signature:** apparent-temperature and thermal-inertia differences caused
  by material, void, soil moisture, depth, vegetation, and heat exchange.
- **Methods:** radiometric temperature workflow; emissivity/atmospheric
  correction where feasible; repeated dawn, dusk, or night acquisitions;
  thermal time-series or contrast curves; vegetation masking; fusion with
  RGB/multispectral and surface models.
- **Prerequisites:** a radiometric sensor, stable weather, appropriate time of
  day, shallow enough target, flight/sensor metadata, calibration, and
  concurrent ground/weather observations.
- **Failure modes:** solar heating and shade, wind/cloud transitions,
  emissivity differences, wet/clayey soils, vegetation, topography, depth,
  automatic gain control in non-radiometric imagery, and poor thermal
  resolution.
- **Claim boundary:** **[REPORTED]** aerial thermography has detected shallow
  archaeological proxies in favourable conditions, while performance is
  strongly time- and site-dependent ([P15], [P16], [P17]). A single hot/cold
  patch is not diagnostic.

### Photogrammetry and structure from motion

- **Signature:** the visible 3D surface, exposed fabric, texture, earthwork
  form, erosion, cracks, and repeat-survey condition change.
- **Methods:** feature detection/matching, camera pose estimation, bundle
  adjustment, dense multi-view stereo, point cloud, mesh, orthomosaic,
  DEM/DSM, and repeat-survey differencing.
- **Prerequisites:** sharp overlapping imagery from diverse positions,
  stable exposure/focus, camera metadata/calibration, scale/control,
  GCP/RTK/PPK as appropriate, and independent checkpoints excluded from the
  adjustment.
- **Failure modes:** weak or repetitive texture, water/reflections,
  vegetation motion, moving shadows, rolling shutter, bad control geometry,
  self-calibration instability, doming, occlusion, and over-smoothed meshes.
- **Claim boundary:** SfM reconstructs photographed surfaces; it does not
  reveal buried geometry by itself. Report checkpoint error and inspect
  residual patterns, not only a global RMSE ([A5], [A6], [P18]).

## Computational methods

### Preprocessing before detection

**[CONFIRMED]** A detector cannot repair missing information or invalid
geometry. Record and test:

- source, acquisition time, licence, processing level, CRS/vertical datum,
  ground sampling distance, point density, bandpass, bit depth, and nodata;
- radiometric/atmospheric calibration and reflectance or temperature scaling;
- orthorectification and cross-date/cross-modal co-registration error;
- cloud, shadow, saturation, aerosol, water, vegetation, speckle, and
  no-ground-return masks;
- resampling method and every derived band, index, visualization, and kernel
  scale;
- known-site, modern-infrastructure, geology, land-cover, and negative/control
  layers without leaking test labels into training.

### Classical and unsupervised anomaly detection

- **Algorithms:** contrast stretch, ratios/indices, PCA/MNF/NLPCA, robust
  z-scores, RX-style background anomaly detection, matched filtering,
  spectral unmixing, edge/line extraction, Hough or ring templates,
  morphology, texture features, and temporal change statistics.
- **Useful for:** ranking unusual crop response, looting disturbance,
  geometric earthworks, rings/ditches, and spectral outliers where labels are
  scarce.
- **Prerequisites:** an explicit background model, target scale, valid masks,
  threshold-selection procedure, and spatially independent evaluation.
- **Failure modes:** anomaly means unusual, not archaeological; background
  heterogeneity, threshold instability, multiple comparisons, and algorithmic
  artifacts can dominate.
- **Evidence:** nonlinear PCA hyperspectral detection ([P6]), multispectral
  PCA for looting detection ([P19]), and circular-template detection ([P20])
  are **[REPORTED]** case-study results.

### Object detection and instance segmentation

- **Algorithms:** Faster R-CNN, YOLO-family detectors, Mask R-CNN, and other
  box/instance models.
- **Useful for:** discrete mounds, tombs, pits, enclosures, structures, or
  looting holes with reasonably consistent visible form.
- **Prerequisites:** expert labels with provenance, representative hard
  negatives, class definitions, spatially blocked train/validation/test
  regions, augmentation that preserves archaeological geometry, and review
  of label disagreement.
- **Failure modes:** severe class imbalance, tile-edge effects, duplicate
  detections, spatial leakage, domain shift, biased inventories, uncertain
  boundaries, and learning survey/visualization artifacts.
- **Evidence:** tomb CNNs ([P21]), UAV optical deep learning ([P22]), and
  time-series satellite detection ([P23]) are **[REPORTED]** studies, not
  universal benchmarks.

### Semantic segmentation

- **Algorithms:** U-Net-family, HRNet-family, convolutional/transformer
  encoders, multimodal segmentation, and post-processing with connected
  components or morphology.
- **Useful for:** irregular banks, ditches, field systems, settlements,
  hillforts, and disturbance extents where boxes are inadequate.
- **Prerequisites:** stable annotation policy, boundary tolerance, class
  weighting or sampling, independent geographic testing, and pixel plus
  object-level metrics.
- **Failure modes:** fuzzy archaeological boundaries, inconsistent labels,
  visually plausible over-smoothing, tiny-class loss, and high IoU on easy
  background despite missed features.
- **Evidence:** multimodal hillfort segmentation ([P24]) and the
  **[CURRENT 2026][REPORTED]** ADAF airborne-LiDAR deep-learning study
  ([P27]). The 2026 publication confirms a tool and evaluation exist; it does
  not confirm transfer to unseen landscapes.

### Multimodal and temporal fusion

- **Early fusion:** stack co-registered bands/indices/visualizations.
- **Feature fusion:** combine learned or engineered modality features, often
  with attention or gating.
- **Late fusion:** combine independent candidate scores or expert decisions.
- **Temporal fusion:** use phenological sequences, change vectors, recurrent
  models, temporal convolutions, or per-date evidence aggregation.
- **Prerequisites:** quantified co-registration, compatible grids and scale,
  harmonized radiometry, acquisition-time context, modality-specific masks,
  and ablation tests.
- **Failure modes:** misregistration creates edges; upsampling creates false
  detail; seasonal mismatch changes the target; a high-dimensional modality
  dominates; missing modalities break deployment; fusion obscures the causal
  proxy.
- **Claim boundary:** **[REPORTED]** multisensor UAV data and multimodal
  segmentation can improve particular mappings ([P25], [P24]).
  **[INFERENCE]** accept fusion gains only when held-out geographic tests and
  ablations show improvement over each single modality.

### Operational role of automation

Use automation to prioritize and document review, not to silently create
authoritative site records. Preserve:

- model/version, code, parameters, seeds, training sources, and licences;
- the input chip and surrounding context for every candidate;
- raw score, threshold, class, geometry, modality/date evidence, and reviewer
  decision;
- false positives and false negatives, not only accepted candidates;
- a reversible link from derived record to source data.

## Validation

### Validation ladder

Use the strongest lawful and proportionate independent evidence available:

1. **Technical QA:** verify geometry, radiometry, masks, metadata, and
   processing artifacts.
2. **Independent desk review:** a second interpreter checks raw and derived
   data without seeing the first decision where practical.
3. **Contextual comparison:** historic environment records, maps,
   photographs, geology, soils, utilities, land use, and previous surveys.
4. **Authorized field observation:** GNSS mapping, photography, fieldwalking,
   or surface inspection under local rules.
5. **Non-invasive geophysics:** magnetometry, electrical resistance,
   electromagnetic induction, GPR, or other method matched to soil and target.
6. **Selective excavation:** only where research, conservation, applicable
   land/method permission, community governance, and risk justify it.

Remote sensing and geophysics can share environmental confounders. Agreement
is valuable, but independence must be argued rather than assumed.

### Evaluation design

- Split training and test data by site, landscape, acquisition, or region.
  Random neighbouring tiles leak spatial texture and inflate performance.
- Keep a locked test set and document all tuning against validation data.
- Sample known positives, hard negatives, different land covers, and
  genuinely unsearched areas; do not evaluate only attractive candidates.
- Blind interpreters to model confidence where measuring independent expert
  performance.
- Record inter-interpreter agreement and adjudication.
- Field-check a documented sample of both predicted positives and negatives.
- Treat inventories and field survey as imperfect reference data; distinguish
  `not recorded` from `confirmed absent`.

### Metrics

Report counts and denominators:

- true positives, false positives, false negatives, and true negatives when
  the sampling design makes the last quantity meaningful;
- precision/user's accuracy, recall/producer's accuracy, F1, specificity, and
  precision-recall curves for imbalanced data;
- IoU/Dice plus boundary and object-level metrics for segmentation;
- AP/mAP at declared IoU thresholds for detection;
- calibrated probability, reliability diagrams, Brier score, and threshold
  sensitivity when scores are interpreted probabilistically;
- positional and vertical checkpoint errors, including systematic bias;
- per-site, per-land-cover, per-sensor/date results and confidence intervals.

The accuracy-assessment principles in Olofsson et al. ([P26]) are
**[CONFIRMED]** statistical guidance for mapped classes/area estimation, not a
complete archaeological validation protocol. Combine them with current
domain standards ([A7]).

## Uncertainty and reporting

Track uncertainty by source:

- **measurement:** sensor noise, calibration, GSD, point density, atmosphere;
- **geometry:** ephemeris, terrain correction, orthorectification,
  co-registration, CRS/datum, GCP/checkpoint configuration;
- **environment:** crop, phenology, soil moisture, weather, land management,
  canopy, illumination, incidence angle;
- **processing:** masks, interpolation, filters, visualization kernels,
  thresholds, resampling, normalization;
- **model:** training coverage, class imbalance, score calibration, domain
  shift, stochastic variance;
- **interpretation:** feature boundary, type/date/function, modern or natural
  alternatives, interpreter disagreement;
- **validation:** incomplete inventories, biased field access, geophysical
  sensitivity, and excavation sampling.

For every candidate, report:

- proxy observed and plausible causal alternatives;
- source/date/resolution and processing lineage;
- geometry with positional uncertainty rather than spurious precision;
- independent supporting and contradicting evidence;
- confidence separately for `anomaly is real`, `anomaly is anthropogenic`,
  and `anomaly is archaeological`;
- validation status: unreviewed, desk-reviewed, field-observed,
  geophysically supported, excavated, or rejected;
- access/sensitivity classification.

**[INFERENCE]** Non-detection means “not visible with these data, conditions,
and method,” not “absent.” A negative result is informative only after the
method's expected sensitivity and surveyed coverage are established.

## Public evidence, protected data, and field conduct

### Spatial disclosure

- Publish the exact coordinates, AOIs, ranked cells, imagery footprints, and
  source-supported precision of ordinary public desk-research candidates.
  A location is not restricted merely because it may be a new site or concern
  treasure, gold, coins, hoards, swords, weapons, or other portable finds.
- Restrict only fields covered by a named legal protection, deliberate
  redaction, source or custodian condition, private-data constraint, burial or
  sacred-place status, or community-governed rule. State the basis and the
  exact field omitted; preserve all unaffected spatial evidence.
- Public source imagery does not cancel a real protection rule, but analytical
  discoverability does not automatically create one either. Use embargoes,
  access control, or generalization only where the specific rule requires it.
- ADS provides repository guidance for genuinely sensitive archaeological
  data ([A12]). NPS cultural-resource datasets may contain expressly redacted
  or withheld information ([A14], [A15]); those are examples of named
  restricted variants, not defaults for worldwide candidate research.

### Communities and data governance

- Seek landowner or method permission for the field action that requires it,
  heritage-authority involvement for protected places or statutory reporting,
  and community consent for community-controlled knowledge, sacred places, or
  culturally governed imagery and narratives. Ordinary public desk research
  and exact public reporting require none of those by default.
- Apply CARE—Collective Benefit, Authority to Control, Responsibility, and
  Ethics—alongside FAIR/open-science goals when Indigenous or other
  community-governed data are actually in scope ([A13]).
- Record who controls collection, reuse, access, or publication only where
  such control exists. Do not invent a consultation gate for public evidence.

### Field and publication conduct

- Remote detection does not authorize entry, collection, probing,
  metal-detecting, drone flight, geophysics, excavation, removal, or
  disturbance.
- Check aviation, privacy, protected-site, export, land-access, and research
  rules before the corresponding field, recovery, or publication action.
- Report a possible discovery as a candidate, with exact public spatial
  evidence when supported. Expert review improves the claim but is not a
  prerequisite for publishing an honest candidate unless a specific
  protection, reporting duty, or source term says otherwise.
- Preserve attribution, licences, provenance, and limits on training-data
  reuse. Do not publish model outputs that expose data already designated
  protected, confidential, private, or community-restricted.

## Source register

### Books and foundational synthesis

| Source | Focus |
| --- | --- |
| **[B1]** Parcak (2009), *Satellite Remote Sensing for Archaeology*, DOI `10.4324/9780203881460` | Optical satellite archaeology |
| **[B2]** Opitz and Cowley, eds. (2013), *Interpreting Archaeological Topography*, ISBN `9781842175163` | LiDAR, 3D data, visualization, interpretation |
| **[B3]** Kokalj and Hesse (2017), *Airborne Laser Scanning Raster Data Visualization*, DOI `10.3986/9789612549848` | DEM visualization good practice |
| **[B4]** Rączkowski (2012), "Metody w archeologii," pp. 367-408 | Method, theory, and interpretive provenance |
| **[B5]** Rączkowski (2020), "Power and/or Penury of Visualizations," DOI `10.3390/rs12182996` | Remote-sensing visualization critique |

### Authorities and operational specifications

| Source | Source |
| --- | --- |
| **[A1]** Historic England, *Airborne Remote Sensing* | **[A2]** Historic England, *The Formation of Cropmarks* |
| **[A3]** Historic England, *Using Aerial Photographs* | **[A4]** Historic England (2018), *Using Airborne Lidar in Archaeological Survey* |
| **[A5]** Historic England (2017), *Photogrammetric Applications for Cultural Heritage* | **[A6]** Historic England, *Geospatial Survey Specifications for Cultural Heritage* |
| **[A7]** Historic England (2026), *Standards and Guidance for Aerial Investigation and Mapping Projects* | **[A8]** Copernicus Data Space, *Sentinel-2* mission/products |
| **[A9]** USGS, *Landsat 8* specifications | **[A10]** USGS, *Landsat Collection 2 Level-2 Science Products* |
| **[A11]** ESA, *Sentinel-1 Instrument* | **[A12]** Archaeology Data Service, *Sensitive Data* |
| **[A13]** Global Indigenous Data Alliance, *CARE Principles* | **[A14]** NPS, *Data Disclaimers* for cultural-resource data |
| **[A15]** NPS, *Cultural Resource Site Disclosure Policy* | **[A16]** USGS, *Lidar Error Dictionary, v3.2* |

### Primary method and evaluation studies

| Study | Study |
| --- | --- |
| **[P1]** Lasaponara et al. (2007), QuickBird crop marks, DOI `10.1016/j.jas.2006.04.014` | **[P2]** Agapiou et al. (2012), vegetation indices for crop marks, DOI `10.3390/rs4123892` |
| **[P3]** Agapiou et al. (2013), temporal/spectral crop-mark window, DOI `10.1016/j.jas.2012.10.036` | **[P4]** Materazzi et al. (2022), drone multispectral crop marks, DOI `10.1016/j.jasrep.2021.103235` |
| **[P5]** Cavalli et al. (2007), hyperspectral prospection, DOI `10.1016/j.culher.2007.03.003` | **[P6]** Cavalli et al. (2013), hyperspectral nonlinear PCA, DOI `10.1109/JSTARS.2012.2227301` |
| **[P7]** Agapiou et al. (2014), Sentinel-2 potential, DOI `10.3390/rs6032176` | **[P8]** Estanqueiro et al. (2023), Sentinel-2 site detection, DOI `10.1016/j.jasrep.2023.104188` |
| **[P9]** Patruno et al. (2019), multi-frequency polarimetric analysis, DOI `10.3390/rs12010001` | **[P10]** Morrison (2013), subsurface archaeology with SAR, DOI `10.1002/arp.1445` |
| **[P11]** Hesse (2010), Local Relief Models, DOI `10.1002/arp.374` | **[P12]** Zakšek et al. (2011), sky-view factor, DOI `10.3390/rs3020398` |
| **[P13]** Štular et al. (2012), LiDAR-relief visualization, DOI `10.1016/j.jas.2012.05.029` | **[P14]** Bennett et al. (2012), ALS visualization comparison, DOI `10.1002/arp.1414` |
| **[P15]** Casana et al. (2017), aerial thermography, DOI `10.1017/aap.2017.23` | **[P16]** Salgado Carmona et al. (2020), multispectral/thermal UAV, DOI `10.1016/j.jasrep.2020.102312` |
| **[P17]** Ciccone (2024), thermal evapotranspiration anomalies, DOI `10.1002/arp.1946` | **[P18]** Smith et al. (2015), SfM photogrammetry, DOI `10.1177/0309133315615805` |
| **[P19]** Lauricella et al. (2017), PCA looting detection, DOI `10.15184/aqy.2017.90` | **[P20]** Trier et al. (2008), automatic circular-structure detection, DOI `10.1002/arp.339` |
| **[P21]** Caspari et al. (2019), CNN tomb detection, DOI `10.1016/j.jas.2019.104998` | **[P22]** Altaweel et al. (2022), deep learning on optical UAV imagery, DOI `10.3390/rs14030553` |
| **[P23]** Yang et al. (2024), time-series moated-site detection, DOI `10.1016/j.jas.2024.106070` | **[P24]** Canedo et al. (2024), multimodal hillfort segmentation, DOI `10.1002/arp.1958` |
| **[P25]** Brooke et al. (2019), multisensor UAV mapping, DOI `10.3390/rs12010041` | **[P26]** Olofsson et al. (2014), accuracy assessment, DOI `10.1016/j.rse.2014.02.015` |
| **[P27]** Čož et al. (2026), ADAF deep-learning tool for ALS, DOI `10.1016/j.jasrep.2026.105733` |  |

[B1]: https://doi.org/10.4324/9780203881460
[B2]: https://www.oxbowbooks.com/9781842175163/interpreting-archaeological-topography/
[B3]: https://doi.org/10.3986/9789612549848
[B4]: method-theory-raczkowski.md
[B5]: https://doi.org/10.3390/rs12182996
[A1]: https://historicengland.org.uk/research/methods/airborne-remote-sensing/
[A2]: https://historicengland.org.uk/research/methods/airborne-remote-sensing/formation-of-cropmarks/
[A3]: https://historicengland.org.uk/research/methods/airborne-remote-sensing/aerial-photographs/
[A4]: https://historicengland.org.uk/images-books/publications/using-airborne-lidar-in-archaeological-survey/
[A5]: https://historicengland.org.uk/images-books/publications/photogrammetric-applications-for-cultural-heritage/
[A6]: https://historicengland.org.uk/images-books/publications/geospatial-survey-specifications-cultural-heritage/
[A7]: https://historicengland.org.uk/images-books/publications/standards-guidance-aerial-investigation-mapping-projects/
[A8]: https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2
[A9]: https://www.usgs.gov/landsat-missions/landsat-8
[A10]: https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products
[A11]: https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Instrument
[A12]: https://archaeologydataservice.ac.uk/help-guidance/how-to-prepare-data/sensitive-data/
[A13]: https://www.gida-global.org/careprinciples
[A14]: https://www.nps.gov/subjects/gisandmapping/data-disclaimers.htm
[A15]: https://home.nps.gov/arch/learn/management/disclosurepolicy.htm
[A16]: https://www.usgs.gov/media/files/usgs-lidar-error-dictionary-v32
[P1]: https://doi.org/10.1016/j.jas.2006.04.014
[P2]: https://doi.org/10.3390/rs4123892
[P3]: https://doi.org/10.1016/j.jas.2012.10.036
[P4]: https://doi.org/10.1016/j.jasrep.2021.103235
[P5]: https://doi.org/10.1016/j.culher.2007.03.003
[P6]: https://doi.org/10.1109/JSTARS.2012.2227301
[P7]: https://doi.org/10.3390/rs6032176
[P8]: https://doi.org/10.1016/j.jasrep.2023.104188
[P9]: https://doi.org/10.3390/rs12010001
[P10]: https://doi.org/10.1002/arp.1445
[P11]: https://doi.org/10.1002/arp.374
[P12]: https://doi.org/10.3390/rs3020398
[P13]: https://doi.org/10.1016/j.jas.2012.05.029
[P14]: https://doi.org/10.1002/arp.1414
[P15]: https://doi.org/10.1017/aap.2017.23
[P16]: https://doi.org/10.1016/j.jasrep.2020.102312
[P17]: https://doi.org/10.1002/arp.1946
[P18]: https://doi.org/10.1177/0309133315615805
[P19]: https://doi.org/10.15184/aqy.2017.90
[P20]: https://doi.org/10.1002/arp.339
[P21]: https://doi.org/10.1016/j.jas.2019.104998
[P22]: https://doi.org/10.3390/rs14030553
[P23]: https://doi.org/10.1016/j.jas.2024.106070
[P24]: https://doi.org/10.1002/arp.1958
[P25]: https://doi.org/10.3390/rs12010041
[P26]: https://doi.org/10.1016/j.rse.2014.02.015
[P27]: https://doi.org/10.1016/j.jasrep.2026.105733
