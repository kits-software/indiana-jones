# Whitley Castle Sentinel-2 optical POC

## Result

The transparent multi-date optical baseline missed the precommitted 160 m
localization tolerance in all three frozen profiles. The nearest anomaly was
191.150 m from the withheld target under profiles A and B, and 191.915 m under
profile C.

| Profile | Background radius | Threshold | Nearest rank | Error | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| A-default | 120 m | 3.5 | 36 / 50 | 191.150 m | miss |
| B-lower-threshold | 120 m | 3.0 | 41 / 50 | 191.150 m | miss |
| C-broader-background | 250 m | 3.5 | 25 / 50 | 191.915 m | miss |

This is a negative known-site localization result. It does not show that the
fort is absent, that it is invisible in every satellite acquisition, or that
the method has a measured worldwide detection rate. It does show that this
frozen four-date Sentinel-2 configuration did not satisfy its own criterion.
No threshold, date, extent, feature, or tolerance was changed after unblinding.

The public, coordinate-redacted evidence record is
[`result-summary.json`](../assets/poc/whitley-castle-optical/result-summary.json).
The exact candidate artifacts remain restricted because they contain precise
coordinates for every ranked anomaly.

## Benchmark boundary

Whitley Castle is a public, already-known scheduled Roman fort near Alston.
The target source is the
[Archaeology Data Service record](https://doi.org/10.5284/1012483).

The 4 × 4 km AOI was deliberately selected around the known site. The analyst
knew the benchmark identity, but the selection program and candidate generator
did not receive the target coordinate or ground-truth file. This therefore
tests target-withheld localization inside a target-selected window. It is not
an analyst-blind regional survey or a new-site search.

The rule frozen before scoring was:

- return the top 50 candidates;
- count a hit when a candidate centroid lies within 160 m of the target;
- report the actual rank and nearest distance;
- retain misses;
- do not tune after reading ground truth.

## Imagery selection

The public [Earth Search](https://earth-search.aws.element84.com/v1) STAC API
was queried for the `sentinel-2-c1-l2a` collection. Four seasonal windows were
declared before selection. Within each window, the intersecting item with the
lowest item-level `eo:cloud_cover` was selected, with acquisition time and item
ID as tie-breakers.

The source pixels remain governed by the
[Copernicus Sentinel Data Legal Notice](https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice);
the Earth Search mirror does not replace those terms. Derived uses should carry
the applicable modified-Copernicus attribution.

| Window | Item | Acquisition | Tile cloud |
| --- | --- | --- | ---: |
| winter | `S2B_T30UWF_20250309T112234_L2A` | 2025-03-09 11:26:09 UTC | 8.920007% |
| spring | `S2C_T30UWF_20250516T113334_L2A` | 2025-05-16 11:36:19 UTC | 0.003076% |
| summer | `S2C_T30UWF_20250712T112136_L2A` | 2025-07-12 11:26:29 UTC | 3.254170% |
| autumn | `S2A_T30UWF_20250922T112128_L2A` | 2025-09-22 11:26:21 UTC | 3.686428% |

Item-level cloud percentage is only a selection proxy. The SCL mask was still
applied within the AOI.

## Preprocessing

The fixed analysis grid was:

- CRS: EPSG:32630;
- extent: 4,000 × 4,000 m;
- shape: 400 × 400;
- pixel spacing: 10 m, north-up;
- bands: blue, green, red, NIR, and SWIR1;
- native GSD: 10 m for blue/green/red/NIR and 20 m for SWIR1;
- SWIR1 resampling: bilinear to the 10 m grid;
- SCL resampling: nearest-neighbour from native 20 m;
- valid SCL classes: 2, 4, 5, 6, and 7;
- invalid SCL classes: 0, 1, 3, 8, 9, 10, and 11;
- source DN zero: invalid;
- reflectance transform: `DN × 0.0001 − 0.1`.

All 640,000 date-pixel observations were valid after masking. That removes
cloud opportunity as an explanation for this miss, but does not remove crop
state, soil moisture, sub-pixel scale, or weak-proxy explanations.

The source cube combined 20 reflectance assets and four SCL assets. Stable
Earth Search URLs and provider-declared SHA-256 multihashes were recorded
during acquisition. The 4.3 MB derived cube is intentionally not shipped with
the plugin; reacquisition must re-check the item identities, provider hashes,
crop parameters, and final cube hash.

## Frozen analysis

All profiles used:

```text
minimum pixels:       2
minimum dates:        2
minimum valid dates:  2
top-k:                50
RX shrinkage:         0.15
RX maximum samples:   50000
```

The three predeclared sensitivity profiles were:

```text
A-default:             background 120 m, threshold 3.5
B-lower-threshold:     background 120 m, threshold 3.0
C-broader-background:  background 250 m, threshold 3.5
```

Candidate hashes were created before the ground-truth file:

| Artifact | SHA-256 |
| --- | --- |
| selection | `fa925293fdcea476ae22e879e7f5aebb629563a4bc0a057dd1e360d29139fca1` |
| profiles | `4ea05c66c7654312ef73b8c05c9655c96209ae02c89b8c93308c81a3d1e47cf5` |
| cube | `9bb5b6dc5ed1e2a54b0a0f3ecdab89ee07b5d1790c5e96f0344067965c6dc862` |
| cube manifest | `1168e3b669f6a2343c27364088208255689ef4cb9c956b14b54c6edf87c3c38f` |
| A candidates | `25995b16bc84ecc8d5b682c6bbcb71a90e95d6996d2bb6ed6666aaf627121719` |
| B candidates | `4dbac976af1eccee46c147fc24d8e2c2389a3c040068fc110b08bb5bd8b7b8f2` |
| C candidates | `97cfa06edf2d59d448fca39b4cc232de8dd902b407521109535743e2917eb9c4` |
| ground truth, created afterward | `cf13079c688dfdbef3deb0025eaa58822b97a603348b9931b9c6147636150655` |

The scorer was called with each precommitted candidate hash. It read and hashed
the immutable candidate bytes before loading ground truth, required contiguous
ranks, and emitted its own implementation identity. The score hashes are
retained in the public summary.

The retained score artifacts identify the exact historical scorer bytes.
Candidate freezing remains valid because all three candidate files were
generated and hashed before the ground-truth file existed. A later adversarial
audit found that the historical command loaded ground-truth content before it
finished validating the already-frozen candidate schema. The current runtime
now completes candidate schema, bbox, rank, centroid, diagnostic, and hash
validation before opening ground-truth content. Historical score hashes are
preserved rather than silently replaced.

## Interpretation

The same four-date-support anomaly was nearest under profiles A and B. A
closely aligned anomaly was nearest under profile C. That repeatability makes
the location worth interpreting in a restricted review, but 191 m still fails
the frozen criterion and does not identify part of the fort.

Plausible explanations include:

- the fort-scale proxy is too weak or spatially diffuse at 10–20 m native GSD;
- the chosen dates do not capture the decisive crop, moisture, or soil state;
- local-standardization and RX emphasize stronger agricultural or geological
  anomalies elsewhere;
- a centroid is an imperfect localization statistic for a broad or fragmented
  response;
- the fixed threshold and component rules discard a lower-amplitude target
  signal.

Those are hypotheses, not excuses to move the tolerance. A development pass may
inspect target-centred band/index traces and candidate morphology, but any
resulting rule must be frozen and tested on a geographically separate site.

## Acquisition incident

One remote July SWIR1 `gdalwarp` stopped progressing. Only that temporary
process was terminated. The same frozen COG was then cropped through bounded
GDAL `/vsicurl/` access at native 20 m and resampled locally. No item, date,
extent, mask, feature, or ranking parameter changed.

## What this adds to the terrain POC

The [terrain POC](poc-whitley-castle.md) localized the fort at rank 8 after a
post-unblinding scale change, so it is development evidence. This optical POC
preserves a precommitted miss. Together they show why modality, native
resolution, phenology, target scale, and leakage discipline must be reported
separately.

Next validation should use a frozen method on a geographically separate public
known site, plus matched modern, agricultural, geological, and extraction
negative windows. A single miss and one tuned terrain hit cannot estimate
precision, recall, or worldwide usefulness.
