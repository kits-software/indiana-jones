# Satellite imagery analysis for archaeological proxy detection

Status: research and implementation boundary reviewed 2026-07-24.

This reference covers computational analysis of satellite imagery. It does not
describe a universal archaeological-site detector because the literature does
not support one. Satellite measurements can expose crop, soil, moisture,
roughness, relief, deformation, and disturbance proxies under particular
conditions. The output is a ranked anomaly that still needs independent
archaeological interpretation and validation.

## Conclusions that control the skill

1. Start from the proposed physical proxy, not from a favourite model.
2. Prefer analysis-ready multi-date stacks to a visually striking single date.
3. Compare a pixel with a defensible local or ecological background.
4. Preserve raw reflectance because an index can suppress the useful contrast.
5. Treat 10–30 m imagery as landscape-scale evidence. Resampling does not add
   spatial detail.
6. Keep optical, SAR, terrain, historical, and inventory evidence separate
   until candidate-level late fusion.
7. Do not train or tune on known-site coordinates and then call rediscovery an
   independent test.
8. Do not report an anomaly score as a site probability unless it is calibrated
   on geographically independent and representative data.
9. Never treat an inventory absence as a negative label.
10. Preserve candidate coordinates in spatial artifacts unless a named legal,
    source, custodian, privacy, or community restriction requires withholding.

The bundled method implements the transparent part of this boundary: validated
multi-date surface-reflectance cubes, raw bands and explicit indices, local
standardized contrast, regularized RX anomaly distance, temporal repeatability,
and connected-component ranking. It does not include a pretrained
archaeological classifier.

## Sensor and preprocessing contracts

### Sentinel-2 L2A

Sentinel-2 supplies blue, green, red, and broad NIR at 10 m; red-edge,
narrow-NIR, and SWIR bands are 20 m. Use L2A surface reflectance, keep the
product processing baseline, and mask cloud, cloud shadow, snow, saturation,
and no-data. Copernicus documents the
[L2A product](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html)
and [processing-baseline changes](https://sentiwiki.copernicus.eu/web/s2-processing).

Do not mix uncorrected digital numbers across the baseline-04.00 change. Do not
describe a 20 m band resampled to 10 m as 10 m evidence. A five-day nominal
revisit is not a five-day usable time series under cloud.

### Landsat Collection 2 and HLS

Apply the documented Landsat Collection 2 surface-reflectance transform
`DN * 0.0000275 - 0.2`; use the QA bands for cloud, cirrus, shadow, and
saturation. See the official [scale-factor
guide](https://www.usgs.gov/faqs/how-do-i-use-a-scale-factor-landsat-level-2-science-products)
and [quality-band guide](https://www.usgs.gov/landsat-missions/landsat-collection-2-quality-assessment-bands).

Harmonized Landsat Sentinel-2 (HLS) is useful for phenology because it applies
atmospheric correction, cloud masking, BRDF/nadir normalization, bandpass
adjustment, and a common 30 m grid. Preserve the product version and consult
the [HLS algorithm description](https://hls.gsfc.nasa.gov/algorithms/).
Thirty-metre HLS is not suitable for resolving small individual features.

### Registration and masks

All dates and bands in one cube must share:

- a projected metric CRS;
- a north-up grid and explicit metric bounding box;
- an exact pixel size and array shape;
- documented reflectance scale and offset;
- a per-date valid mask;
- documented alignment and resampling;
- item IDs, acquisition timestamps, asset URLs, and source terms.

Use nearest-neighbour resampling for categorical masks. Record the kernel used
for continuous reflectance. Quantify residual displacement when fusing
modalities; a visually plausible overlay is not a registration measurement.

The bundled validator rejects longitude/latitude, feet-based grids, and global
Mercator because metre-scale kernels need a suitable local projected CRS.
Common worldwide UTM and selected national/polar metric EPSG identifiers work
without an extra dependency. Other EPSG identifiers, WKT, and PROJ strings
require `pyproj` so the projection and axis units can be checked
authoritatively; a unit label in the manifest is not accepted as proof.

## Optical methods

### Raw reflectance and spectral shape

The most direct test compares per-date surface reflectance inside a candidate
with its local background. Raw red, red-edge, NIR, and SWIR can be more
informative than a derived index in a particular crop and season.

[Corbo, Jaia, and Tapete
2026](https://doi.org/10.3390/land15050753) examined Sentinel-2 reflectance
signatures over Roman contexts across the archive from 2017. The work supports
multi-season spectral separability as a prospecting proxy, but it is a
known-context demonstration, not a transferred detector.

[Abate et al. 2020](https://doi.org/10.3390/rs12081309) compared
multi-temporal Sentinel-2 bands, indices, spectral unmixing, tasseled-cap
features, and PCA in the Foggia landscape. Useful dates and components were
dataset-dependent; single bands could outperform indices.

Implementation rule: retain valid raw reflectance bands alongside every
derived index. Never select a worldwide “best month.”

### Vegetation, moisture, water, and soil indices

The bundled baseline defines:

- `NDVI = (NIR - red) / (NIR + red)`;
- `SAVI = 1.5 * (NIR - red) / (NIR + red + 0.5)`;
- `NDMI = (NIR - SWIR1) / (NIR + SWIR1)`, when SWIR1 exists;
- `BSI = ((SWIR1 + red) - (NIR + blue)) /
  ((SWIR1 + red) + (NIR + blue))`, when the required bands exist;
- `NDRE = (NIR - red-edge1) / (NIR + red-edge1)`, when red edge exists.

These are contrast transforms, not archaeology indices. Drought, crop variety,
fertilizer, irrigation, pests, drainage, compaction, geology, and bare-soil
mixtures can produce the same responses.

[Agapiou, Hegyi, and Stavilă
2023](https://doi.org/10.3390/rs15020464) used Sentinel-2 phenology at the
Csanádpalota megafort. [Agapiou and Gravanis
2024](https://doi.org/10.3390/rs16101705) evaluated reflectance-signature
classification for cropmark proxies. Both support date-conditioned spectral
analysis; neither supplies a worldwide decision threshold.

[Estanqueiro et al.
2023](https://doi.org/10.1016/j.jasrep.2023.104188) used multi-date
Sentinel-2 bands, combinations, indices, PCA, and signatures in the Serbian
Banat. Many soil marks were only two or three pixels wide. The reported field
confirmation rate is useful local evidence, not a global precision estimate.

Implementation rule: record the crop or land-cover context and compare the same
phenological phase across years where possible. Treat two-to-three-pixel
geometry as weak.

### Temporal composites and phenology

Useful summaries include:

- same-season median and robust spread;
- lower and upper reflectance quantiles;
- amplitude and date of extrema;
- anomaly against the same seasonal window in other years;
- persistence across independent seasons;
- short-lived peak visibility preserved separately from persistence.

[Valente et al. 2022](https://doi.org/10.1002/arp.1874) first used MODIS NDWI
to identify a local visibility window, then reduced Landsat and Sentinel-2
stacks and tested unsupervised clustering in northern Iraqi Kurdistan. The
field-survey result also shows the resolution boundary: Landsat missed many
medium and small targets that were more legible in Sentinel-2.

[Alders et al.
2024](https://doi.org/10.1007/s10816-024-09644-x) used repeated PlanetScope
observations and seasonal composites in tropical island landscapes. It
supports repeated-observation reasoning but relies on commercial imagery and
is not a validated detector.

Implementation rule: `datesAtOrAboveThreshold` is evidence of repeatability,
not independence. Adjacent dates from the same crop episode, orbit, or weather
regime must not be counted as independent confirmation.

### PCA, MNF, and unmixing

PCA can compress correlated features and expose weak contrast in later
components. It also rotates the evidence into scene-specific axes and can make
interpretation harder. MNF first estimates and whitens noise, then orders
components by signal-to-noise ratio. A poor noise covariance makes the result
unreliable.

PCA is supported in the Foggia and Banat studies above. Hyperspectral
demonstrations include [Alicandro et al.
2022](https://doi.org/10.3390/land11112070) and [Sech et al.
2024](https://doi.org/10.1109/IGARSS53475.2024.10642261). PRISMA's 30 m
hyperspectral pixels can discriminate spectra at landscape scale but do not
resolve small geometry. Pansharpening changes localization and can introduce
fusion artifacts; it does not create independent spectral evidence.

Implementation decision: PCA and MNF are documented experimental branches, not
default bundled transformations. The first baseline keeps named, inspectable
features. If added, freeze component count and noise estimation before
ground-truth review and retain the original feature cube.

### RX anomaly distance

RX ranks multivariate departures from a background:

`d(x) = sqrt((x - μ)^T Σ^-1 (x - μ))`.

The bundled implementation robustly scales each named feature, estimates a
per-date global covariance from a deterministic sample, shrinks it toward a
spherical covariance, and robustly standardizes the resulting distances. A
local standardized-contrast path runs in parallel.

RX does not say why a pixel is unusual. It is sensitive to heterogeneous
backgrounds, cloud edges, seams, water boundaries, modern construction, and
bad pixels. General RX assumptions and local/global variants are discussed in
[Matteoli et al. 2015](https://doi.org/10.3390/rs70403966).

Implementation rule: RX is a ranking feature, never a class label or
probability. Stratify by comparable land cover before interpreting scores in a
heterogeneous scene.

### Geometry and morphology

Edges, lines, rings, rectangles, connected components, and Hough support can
measure geometric consistency. The same primitives are common in roads,
irrigation, parcel boundaries, drains, utilities, quarrying, modern
foundations, and geology.

Implementation decision: the baseline groups thresholded anomaly pixels using
eight-connectivity and reports area and bounding boxes. More aggressive
morphology is deferred. If opening, closing, Hough, or size filters are added,
the unfiltered anomaly raster must remain an auditable artifact and every
discarded component must remain countable.

## Supervised and learned methods

### Random forests

[Orengo et al. 2020](https://doi.org/10.1073/pnas.2005583117) combined
multi-temporal Sentinel-1 and Sentinel-2 features in a random forest to detect
large mounds in the Cholistan Desert. The positive training set was very small,
hard-negative tuning was iterative, and the targets were generally large. The
[archived code](https://doi.org/10.34810/DATA184) is GPL-3.0, but its method
must still be revalidated outside arid mound landscapes.

[Yang et al. 2025](https://doi.org/10.1038/s40494-025-01557-6) combined
geographic context with annual Sentinel-2 features for ancient-city
susceptibility in Jianghan. A random pixel split can place pixels from one
known site in both train and validation sets. Its probability surface mixes
settlement-location prior with direct optical evidence.

Implementation decision: do not ship a global random forest. A project may
train one only with complete-site and buffered geographic splits, explicit
hard negatives, a withheld region, and separate reporting for environmental
susceptibility versus observed image anomaly.

### Object detection and segmentation

[Berganzo-Besga et al.
2021](https://doi.org/10.3390/rs13204181) combined a Sentinel-2 random-forest
land-suitability mask, multi-scale relief from LiDAR, and YOLO for mound
detection. It demonstrates staged multimodal screening, not a universal
satellite detector.

[Yang et al. 2024](https://doi.org/10.1016/j.jas.2024.106070) used
multi-temporal Sentinel-2 fusion and an object detector for large moated sites
in northeast Thailand. The model reported 629 detections, which the authors
narrowed to 116 probable sites; six highest-confidence candidates were visually
verified with high-resolution GEE imagery. No official reusable code or weights
were found.

[Canedo et al.](https://doi.org/10.1002/arp.1958) fused local-relief and
orthophoto inputs for hillfort segmentation. Geographic transfer degraded,
while local hard-negative mining sharply reduced false positives.

Implementation decision: learned detection is feature-class- and
landscape-specific. Require DTM-only, optical-only, early-fusion, late-fusion,
and missing-modality ablations before promotion.

### Earth-observation foundation models

Foundation models provide embeddings, not archaeological authority.

- [CROMA](https://github.com/antofuller/CROMA) is an MIT-licensed
  Sentinel-1/Sentinel-2 encoder and the preferred first radar-optical
  experiment.
- [AnySat](https://github.com/gastruc/AnySat) is an MIT-licensed
  multi-resolution, multi-sensor research alternative.
- [TerraMind](https://github.com/IBM/terramind) is Apache-2.0 and supports
  several modalities. Generated modalities are model outputs, not observations
  or corroboration.
- [DOFA](https://github.com/zhu-xlab/DOFA) has MIT code and separately licensed
  weights. Check the exact checkpoint.
- [Prithvi EO 2.0](https://github.com/NASA-IMPACT/Prithvi-EO-2.0) has MIT code;
  its HLS optical inputs are 30 m and too coarse for many individual features.
- [SatMAE](https://github.com/sustainlab-group/SatMAE) is CC BY-NC 4.0, not a
  permissive commercial software dependency. Do not bundle it.

[DeepAndes](https://arxiv.org/abs/2504.20303) is an archaeology-oriented
self-supervised model for high-resolution Andean imagery. An NSF record also
describes [DeepAndesArch](https://par.nsf.gov/biblio/10621637), fine-tuned on
GeoPACHA labels. The public record does not establish a generally reusable,
licensed worldwide archaeological checkpoint.

The [PANGAEA benchmark](https://github.com/VMarsocci/pangaea-bench) is a warning
against assuming that a foundation encoder will beat a small supervised or
classical baseline on every EO task.

Implementation decision: no weights are bundled. Fetch one explicitly licensed
checkpoint at a pinned revision only after the user requests that experiment.
Record framework licence, checkpoint licence, pretraining-data terms,
and imagery-provider rights separately. Record a spatial handling restriction
only when a named legal, source, custodian, private-data, protected-site, or
community rule applies; otherwise preserve exact public coordinates. Compare
against the transparent baseline on held-out regions.

## SAR methods and boundary

SAR measures microwave backscatter and phase, not buried archaeology directly.
Backscatter varies with roughness, moisture, vegetation structure, incidence
geometry, and polarization. Coherence measures temporal stability under a
particular interferometric pair. InSAR measures deformation or topography.

[Cigna et al.
2024](https://doi.org/10.1080/10095020.2023.2223603) present six demonstration
cases using multi-temporal backscatter, coherence, and InSAR for prospection
and heritage protection. [Caspari et al.
2020](https://doi.org/10.3390/rs12071076) studied circular anthropogenic
features in L-band PALSAR data. [Patruno et al.
2020](https://doi.org/10.3390/rs12010001) compared sensors, wavelengths,
polarizations, and geometry. These papers show conditional utility, not a
generic Sentinel-1 buried-feature detector.

For reproducible Sentinel-1 GRD:

1. preserve product ID, checksum, acquisition time, relative orbit, pass,
   polarization, incidence geometry, and processing baseline;
2. apply precise orbit information, border-noise removal, and thermal-noise
   removal;
3. calibrate to linear sigma-zero or gamma-zero and retain the linear raster;
4. apply radiometric terrain flattening and Range-Doppler terrain correction
   with a named and versioned DEM;
5. produce layover, foreshortening, radar-shadow, water, edge, and no-data
   masks;
6. compare the same orbit, pass, polarization, and compatible incidence
   geometry;
7. condition interpretation on rainfall, soil moisture, vegetation, harvest,
   and season;
8. record any multilooking or speckle filter because smoothing changes the
   observable scale.

SLC coherence requires a separate TOPS split/deburst, precise coregistration,
baseline tracking, coherence, and terrain-correction pipeline. Never mix SLC
coherence silently with GRD backscatter.

Implementation decision: SAR preprocessing remains an external SNAP or other
auditable processor. The skill may ingest its calibrated, registered outputs
later, but the optical baseline must not accept SAR arrays relabelled as
reflectance.

## Physically based and hyperspectral research

[Gravanis and Agapiou
2026](https://doi.org/10.1038/s41598-026-45441-0) use PROSAIL in forward and
inverse modes, synthetic cropmark signatures, and an ensemble of
machine-learning classifiers for retrospective testing on measurements from
one controlled test field sampled in two campaigns 13 years apart. The associated
[ACSS2 data](https://doi.org/10.5281/zenodo.15767205) make this a valuable
research branch.

The method models vegetation radiative transfer and can support physically
plausible synthetic signatures. It does not remove the domain gap between
controlled hyperspectral measurements and 10–30 m mixed satellite pixels.

Implementation decision: defer PROSAIL training until a named crop, sensor
response, growth phase, and held-out field or satellite dataset are contracted.
Do not present synthetic signatures as independent measurements.

## Software and licence boundary

This table records the decision as of 2026-07-24. Verify current versions,
Python floors, licences, and asset terms before installation.

| Tool | Licence | Skill decision |
|---|---|---|
| NumPy | BSD-3-Clause | Bundled base computation. |
| Pillow | HPND | Bundled diagnostic images. |
| GDAL | MIT | System or official binary dependency; never vendor native builds. |
| Rasterio | BSD-3-Clause | Optional GeoTIFF/COG adapter. |
| pystac-client | Apache-2.0 | Optional STAC paging adapter; asset terms remain separate. |
| odc-stac | Apache-2.0 | Preferred optional multi-item cube loader. |
| stackstac | MIT | Optional alternative, not installed beside odc-stac by default. |
| xarray/rioxarray | Apache-2.0 | Optional labelled-cube environment. |
| scikit-image | BSD-3-Clause | Add only when explicit morphology is implemented. |
| scikit-learn | BSD-3-Clause | Add only for frozen PCA or supervised experiments. |
| Spectral Python | MIT | Optional hyperspectral PCA/MNF/RX comparison. |
| PyOD | BSD-2-Clause | Experiment only; too broad for the base. |
| TorchGeo | MIT | Isolated deep-learning environment; no implicit downloads. |
| TerraTorch | Apache-2.0, with explicitly listed MIT files | Isolated model environment; inspect each checkpoint. |
| Orfeo Toolbox | Apache-2.0 in current lines | External version-pinned CLI. |
| ESA SNAP | GPL-3.0 | External graph/CLI; do not copy into a permissive package. |
| QGIS | GPL-2.0-or-later | Manual QA/export, not runtime evidence by itself. |
| GRASS GIS | GPL-2.0-or-later | External CLI in an isolated mapset. |
| SAGA GIS | mixed GPL/LGPL components | External version-pinned CLI only. |

The base runtime remains NumPy and Pillow. A future optional satellite
environment should use official Rasterio and pystac-client distributions, not
vendored binaries. Network and model downloads remain explicit.

## Dataset boundary

No mature, globally representative, safely redistributable archaeological
satellite benchmark was found.

- [Archaeoscape](https://archaeoscape.ai/data/2024/) is a valuable,
  credentialed Cambodian ALS/orthophoto benchmark under custom noncommercial
  terms. It is not a global satellite dataset and must not be re-localized.
- [Microsoft looted-site
  detection](https://github.com/microsoft/looted_site_detection) has MIT code,
  but uses Planet imagery and sensitive Afghanistan coordinates. Code licence
  does not relicense pixels or locations.
- [DAFA-LS](https://github.com/ElliotVincent/DAFA-LS) supports known-site
  looting monitoring from Planet time series. It is not unknown-site
  discovery, and Planet terms remain separate.
- The CAA 2025
  [archaeological-sites dataset](https://huggingface.co/datasets/lldbrett/archaeological-sites-caa2025)
  exposes derived Sentinel/FABDEM samples and exact centroids under a broad
  dataset-card claim. Do not bundle it without source-by-source rights,
  sensitivity, and geographic-leakage review.
- [MAPS palaeochannels](https://github.com/IIT-CCHT/MAPS-dataset) offers MIT
  code and separately licensed annotations over Copernicus imagery. It is a
  useful temporal-pipeline regression case, but palaeochannels are proxies, not
  archaeological sites.
- National inventories and OSM are withheld corroboration or ground truth.
  They are incomplete and must not supply default negatives.

For every benchmark, place all dates, augmentations, neighbouring chips, and
tiles from one site or landscape in one split. Hold out buffered geographic
blocks and then an entire region. Report false candidates per square kilometre
and precision at a fixed expert-review budget.

## Bundled optical baseline

### Input artifact

Copy `assets/optical-cube-template.json`. The referenced `.npz` must contain:

- arrays named `red` and `nir`;
- optional `blue`, `green`, `swir1`, `swir2`, and `rededge1`;
- an explicit `valid` boolean array;
- every array shaped `[date, row, column]`.

The manifest is rejected unless it records:

- exact array SHA-256;
- two or more unique acquisition timestamps;
- projected metric CRS, bbox, north-up state, and pixel size;
- per-band native GSD, surface-reflectance scale, offset, sensor, and
  processing level;
- mask and resampling policy;
- per-date stable, unsigned item URL, collection, processing version, access
  basis/time, licence, and a non-secret asset locator for every band;
- a disclosure class, defaulting to `public`;
- `targetLabelsUsed: false`.

The bbox may cover at most 400 km² and the cube at most 1,000,000
date-pixel observations. Tile larger investigations. These are computation and
disclosure guardrails, not scientific scale recommendations.
Signed URLs, embedded credentials, and common credential-bearing query keys
are rejected because source provenance is copied into the result. A pixel
marked valid must be finite in every declared band; correct the cube or mask
rather than allowing the runtime to silently change the stated mask policy.

### Validation and execution

```bash
python3 <skill-dir>/scripts/satellite.py validate \
  --manifest optical-cube.json

python3 <skill-dir>/scripts/satellite.py analyze \
  --manifest optical-cube.json \
  --out-dir optical-run \
  --background-radius-m 120 \
  --threshold 3.5 \
  --min-pixels 2 \
  --min-dates 2 \
  --min-valid-dates 2 \
  --top-k 50
```

Use a new output directory for every run. The command refuses to replace an
existing directory and stages the complete bundle beside it before one atomic
publish, so a failed run cannot leave a mixed or partial result.

The analysis:

1. verifies geometry, masks, provenance, modality, and content hash;
2. applies scale and offset to surface reflectance;
3. creates named raw-band and index features;
4. computes a per-date local standardized contrast in a metric window;
5. computes a shrinkage-regularized global RX distance per date;
6. keeps the strongest named local or RX response per date;
7. labels components separately on every date, preventing different-date
   neighbours from becoming one object;
8. records valid dates, exact-peak supporting dates, support fraction, feature,
   polarity, and native observable resolution;
9. deduplicates cross-date proposals only when their component pixels overlap;
10. ranks by support fraction, support-date count, peak score, and single-date
    component area;
11. records reflectance transforms, implementation hashes, plugin version, and
    Python/NumPy/Pillow versions;
12. emits hash-bound JSON, score arrays, and a diagnostic preview.

The deterministic RX sample is for reproducibility, not statistical
independence. The threshold is exploratory until calibrated on held-out
landscapes. Adding optional bands changes the local maximum and RX feature
space, so scores and thresholds are not comparable across different feature
sets without calibration. Candidate coordinates remain in the input projected
CRS. The analytical artifact is marked as containing precise coordinates and
must follow the case disclosure class. Public release preserves the exact
candidates, AOIs, and image footprints by default; a separate reviewed artifact
omits or generalizes only geometry covered by a specific restriction.

### Output interpretation

For each candidate:

- `score` is a standardized anomaly score, not probability;
- `peak.feature` identifies the raw band, index, or regularized RX path;
- `peak.polarity` preserves whether local reflectance was high or low;
- `validDateCountAtPeakPixel`, `supportDateCountAtPeakPixel`, and
  `supportFractionAtPeakPixel` expose observation opportunity;
- `supportSignals` records the date, feature, polarity, score, and native
  observable resolution of every exact-peak crossing;
- `sameFeatureAndPolarityAcrossSupport` reveals feature switching;
- `observableResolutionM` is the coarsest native GSD among the winning
  per-pixel signals in that dated component and its exact-peak supporting
  dates, not its resampled grid spacing;
- `componentGridAreaM2`, projected centroid, and bbox describe one date's
  thresholded grid component, not the true area of a buried feature.

Before archaeological interpretation, test:

- cloud, shadow, snow, saturation, seam, and edge artifacts;
- parcel boundaries, drainage, irrigation, vehicle tracks, utilities, roads,
  construction, and extraction;
- crop type, planting, harvest, fertilizer, pests, and drought;
- soil, moisture, geology, water edges, and topography;
- whether the anomaly survives an independent season or modality.

Freeze and hash the candidate artifact before opening heritage labels.
For a public known-site rediscovery benchmark, keep the target point in a
separate ground-truth JSON using the candidate CRS. Unblind only after the run
is frozen:

```bash
shasum -a 256 optical-run/candidates.json

python3 <skill-dir>/scripts/satellite.py score \
  --candidates optical-run/candidates.json \
  --expected-candidate-sha256 <PRECOMMITTED_SHA256> \
  --ground-truth restricted-ground-truth.json \
  --out optical-run-score.json
```

The score binds candidate and ground-truth hashes and reports localization
distance and top-k rank without copying the target coordinates into the score
artifact. It measures this known-site window only; it is not precision,
recall, discovery evidence, or a transferable detection rate.
Because exact distances are not spatially redacted, this bundled scorer
accepts only explicitly `public-known...` ground truth and inherits the
candidate artifact's disclosure class. Score genuinely protected,
confidential, private, burial-related, sacred, or community-restricted targets
only in a workflow that honors their named handling rule and does not emit this
public artifact.

## Real-data calibration

The frozen [Whitley Castle Sentinel-2 POC](poc-whitley-castle-optical.md)
missed its 160 m known-site localization tolerance under all three
precommitted profiles. The nearest anomaly was 191.150 m away. That negative
result is retained because the baseline is candidate generation, not a
universal detector, and because post-score threshold or tolerance changes
would destroy the benchmark boundary.

The test used four seasonal Sentinel-2 L2A dates, a fixed 4 × 4 km
target-selected AOI, blue/green/red/NIR/SWIR1, SCL masking, and a 10 m analysis
grid. It is one target-withheld localization window, not a blind survey or a
precision/recall estimate. The next promotion gate is a geographically
separate public known site with the method frozen in advance and matched hard
negatives.

## Promotion gates

A new method enters the default runtime only if it:

1. states the physical proxy and observable scale;
2. preserves source, preprocessing, model, and output provenance;
3. beats or materially complements the transparent baseline;
4. is evaluated on complete-site, buffered geographic, and held-out-region
   splits;
5. reports candidate-level precision, recall, false candidates per square
   kilometre, threshold sensitivity, and expert-review burden;
6. includes hard negatives and missing-modality tests;
7. has compatible code, weight, data, and imagery rights, plus a documented
   basis for any spatial restriction actually applied;
8. never turns generated or super-resolved pixels into independent evidence.

## Research process note

A Grok 4.5 Expert research pass was used on 2026-07-24 to widen discovery
across optical, phenological, anomaly, SAR, hyperspectral, and foundation-model
methods. Its claims were treated as leads and checked against the primary
papers, official repositories, model cards, and dataset-owner pages cited
above. Grok Heavy was not used because that mode required a paid upgrade.
