# Evidence contract

## Contents

1. Case ledger
2. Research frame
3. Decision log
4. Source records
5. Candidate records
6. Benchmark separation
7. Reporting grades

## Case ledger

Use one JSON case ledger when an investigation spans several sources or processing runs. The bundled `new-case` command creates the canonical shape.

Required concepts:

- `caseId`, title, question, creation time, and status;
- generalized study area and intended decision;
- expected physical proxy, visibility conditions, and target scale;
- alternative explanations, decision rule, falsifier, and interpretive prior;
- disclosure class and allowed output precision;
- public-web, authenticated-platform, mutation, and field-action authorization;
- source, derived artefact, claim, and candidate arrays;
- a log of rejected explanations and missing evidence.

Authorization is narrow. A platform name in one case does not authorize another platform, a later case, messaging, posting, downloading restricted data, or field access.

## Research frame

Schema `1.1` case ledgers include:

```json
{
  "researchFrame": {
    "expectedProxy": "measurable property rather than desired site class",
    "visibilityConditions": [],
    "targetScale": "expected dimensions and required resolution",
    "alternativeExplanations": [],
    "decisionRule": "result that advances or rejects the candidate",
    "falsifier": "evidence that weakens the preferred interpretation",
    "interpretivePrior": "records, labels, or expectations visible to the analyst"
  }
}
```

Fill this before candidate generation. For rediscovery benchmarks, record that target labels are withheld without copying the identity or location into the frame. See [method-theory-raczkowski.md](method-theory-raczkowski.md) for why acquisition, processing, and interpretation choices are part of the method.

## Decision log

Log consequential choices rather than preserving only the final preferred image:

```json
{
  "stage": "visualization",
  "choice": "compare multi-direction hillshade with local relief",
  "rationale": "a single illumination direction can hide relief",
  "alternativesConsidered": ["single-azimuth hillshade"],
  "targetLabelsState": "withheld",
  "affectedArtifacts": ["sha256:..."]
}
```

Use `unknown`, `visible`, or `withheld` for `targetLabelsState`. A decision record is provenance, not proof that the decision was correct.

## Source records

Each record must include:

```json
{
  "sourceId": "src_<stable-id>",
  "kind": "primary-measurement",
  "locator": "https://example.org/item-or-a-local-path",
  "accessBasis": "public",
  "accessedAt": "ISO-8601 timestamp",
  "sha256": "hash for local or downloaded content when available",
  "license": "stated licence or unknown",
  "sensor": "product or instrument when relevant",
  "acquiredAt": "source acquisition date when known",
  "crs": "EPSG code or unknown",
  "resolution": "ground sampling distance or scale",
  "notes": "limits, transformations, and archive context"
}
```

Keep `locator` precise in the restricted ledger. Public reports may replace it with a collection-level URL when item-level disclosure exposes a vulnerable site.

## Candidate records

Every candidate separates four authority levels:

- `observed`: a direct statement about source pixels, terrain, metadata, or a document;
- `derived`: a reproducible transformation, measurement, or model result;
- `inferred`: an archaeological interpretation or hypothesis;
- `corroborated`: independently supported by an authoritative record or stronger investigation.

Minimum candidate shape:

```json
{
  "candidateId": "cand_<stable-id>",
  "restrictedLocation": {
    "crs": "EPSG:27700",
    "x": 0,
    "y": 0,
    "positionalErrorM": 0
  },
  "publicLocation": {
    "precision": "region-only",
    "label": "generalized study area"
  },
  "observations": [],
  "derivedSignals": [],
  "interpretations": [],
  "alternatives": [],
  "corroboration": [],
  "sensitivity": "restricted",
  "nextAction": "expert desk review"
}
```

Do not serialize precise coordinates into a public artefact and then merely hide them in the presentation layer.

## Benchmark separation

Candidate generation and scoring are separate stages:

```text
raster + area + frozen detector -> ranked candidates + hashes
ranked candidates + withheld ground truth -> score
```

The candidate artefact records:

- input SHA-256;
- source sidecar SHA-256;
- algorithm and schema versions;
- every tunable parameter;
- CRS and bounding box;
- generated-at time;
- ranked coordinates and non-probabilistic scores;
- diagnostic artefact hashes.

Ground truth records the authoritative identifier, exact coordinate or polygon, tolerance, and source. Do not load it in the detector process.

If parameters change after scoring, record a new run and call the previous site a development site. A generalization claim requires a frozen run on a geographically separate validation site.

## Reporting grades

Use grades as an auditable shorthand, not as calibrated probabilities:

- **E0 — image artefact or rejected:** preprocessing, seam, no-data, or known modern/natural cause explains the signal.
- **E1 — unresolved anomaly:** repeatable observation but weak morphology or context.
- **E2 — archaeological candidate:** coherent proxy, plausible morphology/context, and alternatives tested.
- **E3 — independently corroborated:** another date, modality, historic source, or authoritative inventory supports the same feature.
- **E4 — professionally validated:** heritage specialist, field survey, geophysics, or excavation confirms the interpretation.

Always print the reasons, counter-evidence, and validation gap beside the grade.
