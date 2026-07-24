# Whitley Castle known-site POC

## Claim

The bundled classical terrain detector can rank an enclosure-like anomaly within
16.125 m of the authoritative study-area centre for Whitley Castle Roman fort.
The hit is rank 8 of 20 in a 25 km² terrain tile.

This is a development-set known-site localization POC. It is not:

- evidence for a new archaeological site;
- a blind regional discovery;
- a top-1 result;
- an estimate of precision or recall;
- validation outside England, outside LiDAR terrain, or on a held-out site.

Whitley Castle is one regression fixture. The skill and raster contract are
provider-neutral and worldwide.

## Why this site

The user's example “Alsten” was interpreted as Alston. Whitley Castle lies near
Alston and has an unusually diagnostic earthwork form.

[Historic England Research Report 89/2009](https://historicengland.org.uk/research/results/reports/89-2009)
describes the fort as lozenge-shaped, exceptionally preserved, and surrounded by
multiple outer banks and ditches. The
[Archaeology Data Service geophysical survey record](https://doi.org/10.5284/1012483)
publishes the study-area centre as NGR NY 6949 4868.

The benchmark uses a public, already-known scheduled monument. It does not
expose a possible new or restricted site.

## Input

- Product: Environment Agency LIDAR Composite DTM, 1 m.
- Source: [National Data Library record](https://www.data.gov.uk/dataset/01b3ee39-da3f-47b6-83da-dc98e73a461f/lidar-composite-digital-terrain-model-dtm-1m).
- Access: bounded WCS `GetCoverage`.
- CRS: EPSG:27700, coordinates in metres.
- Bounding box: `365000 545000 370000 550000`.
- Raster shape: 5000 × 5000 float pixels.
- Raster SHA-256:
  `786edd9fdb128416d0431add418fd1aeae017f122603c28353b2a754b6e6ffb9`.
- Analysis resolution: 4 m after deterministic 4 × 4 mean reduction.

The composite combines surveys acquired between 2000 and 2022. This POC did not
resolve the underlying survey-index date for the target pixel, which remains a
provenance gap.

The 100 MB source raster is intentionally excluded from the plugin. Reacquire
it:

```bash
python3 <skill-dir>/scripts/archaeology.py fetch-ea-dtm \
  --bbox 365000 545000 370000 550000 \
  --out <skill-dir>/assets/poc/raw/whitley-castle-dtm.tif
```

Verify the resulting input hash before replaying the detector. A composite
dataset update can legitimately produce a new hash and a non-comparable run.

## Evidence separation

Candidate generation receives:

- the DTM pixels;
- its hash-bound source sidecar;
- the projected bbox and CRS;
- scale, shape, orientation, ranking, and suppression parameters.

It does not load the ground-truth JSON, ADS identifier, target coordinate, OSM
heritage tags, a monument overlay, map labels, or the Historic England report.

The ground-truth artifact is
[`assets/poc/whitley-castle/ground-truth.json`](../assets/poc/whitley-castle/ground-truth.json).
Its SHA-256 is
`9f856d2e87d1435b1de2a1561fc7ee59eca213ebe899426a743a8c798ff5e9ae`.
Every score artifact binds both candidate and ground-truth files by hash.

The 5 × 5 km AOI was selected because it contains this known site, so the test
measures localization within a known-site window rather than landscape-scale
discovery. The success criterion was a top-20 candidate within 160 m of the ADS
study-area centre.

## Detector

The terrain baseline:

1. replaces non-finite cells with the finite median;
2. reduces the 1 m DTM to 4 m;
3. calculates local-relief residuals at 12, 35, and 90 m;
4. combines absolute residual, local-gradient, and slope evidence;
5. correlates diamond and ellipse double-ring templates through FFT;
6. normalizes each template response by median absolute deviation in version
   1.1;
7. measures boundary and angular-sector coverage;
8. applies spatial non-maximum suppression and returns 20 ranked candidates.

Its score is relative, not a calibrated archaeological probability. Natural
landforms, mining, agriculture, roads, drainage, and processing effects produce
false positives.

## Three-run history

| Run | Change | Result | Nearest error |
| --- | --- | --- | --- |
| 01 | Raw template responses; radii 60/90/120 m | Miss | 523.225 m, rank 17 |
| 02 | Robust per-template response normalization; mixed 40–120 m scales | Miss | 471.699 m, rank 4 |
| 03 | Post-unblinding fort-scale branch; radii 90–180 m | Hit at rank 8 | 16.125 m |

Runs 01 and 02 are preserved as failures. After those scores were inspected,
diagnosis showed that small-scale proposals and mixed-scale suppression
discarded the whole-enclosure response. Run 03 was therefore tuned on Whitley
and must be called development evidence.

Run 03 uses:

```text
major radii:           90, 100, 110, 120, 140, 160, 180 m
aspects:               1.25, 1.65
angles:                0, 30, 60, 90, 120, 150 degrees
families:              diamond, ellipse
response normalization robust-per-template
minimum distance:      180 m
top-k:                 20
```

Replay:

```bash
python3 <skill-dir>/scripts/archaeology.py detect-enclosures \
  --input <skill-dir>/assets/poc/raw/whitley-castle-dtm.tif \
  --out-dir <skill-dir>/assets/poc/whitley-castle/run-03 \
  --downsample 4 \
  --top-k 20 \
  --minimum-distance 180 \
  --major-radii 90,100,110,120,140,160,180 \
  --aspects 1.25,1.65 \
  --angles 0,30,60,90,120,150 \
  --families diamond,ellipse \
  --response-normalization robust-per-template

python3 <skill-dir>/scripts/archaeology.py score \
  --candidates <skill-dir>/assets/poc/whitley-castle/run-03/candidates.json \
  --ground-truth <skill-dir>/assets/poc/whitley-castle/ground-truth.json \
  --out <skill-dir>/assets/poc/whitley-castle/run-03/score.json
```

## Passing candidate

Candidate `cand_18a36be61b97`:

- rank: 8;
- localization error: 16.125 m;
- template: 100 m major-radius diamond, aspect 1.65, angle 90°;
- boundary coverage: 0.833333;
- sector coverage: 0.8125;
- interpretation emitted by the detector: geometric terrain anomaly,
  archaeological status unverified.

The [candidate overlay](../assets/poc/whitley-castle/run-03/candidates.png)
shows rank 8 at the visible lozenge-shaped earthwork. The score becomes
independently corroborated only after the withheld ADS/Historic England records
are consulted.

## What the POC proves

- A deterministic local Python pipeline can preserve source, runtime,
  implementation, parameter, diagnostic, candidate, and ground-truth hashes.
- A morphology-constrained terrain branch can localize this known fort.
- Failed runs and post-unblinding tuning can be preserved without disguising
  them as validation.

## What remains

- Freeze the fort-scale rule and test a geographically separate known fort
  without further tuning.
- Add matched modern, geological, agricultural, and mining negative windows.
- Measure false positives per km² and top-k stability across terrain products.
- The bundled optical baseline has now been run on a frozen four-date
  Sentinel-2 surface-reflectance cube. All three precommitted profiles missed
  the 160 m tolerance; see
  [the optical POC](poc-whitley-castle-optical.md). SAR, thermal, and
  photogrammetric pipelines remain separate future validations.
- Test the provider-neutral acquisition flow outside the UK. Global 10–30 m
  products cannot be assumed to reveal earthworks visible in a 1 m DTM.
