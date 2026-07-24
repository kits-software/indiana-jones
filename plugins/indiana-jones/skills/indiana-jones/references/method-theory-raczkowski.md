# Method, Theory, and Visual Evidence

Use this reference when selecting a sensing method, interpreting an image or
terrain product, designing a detector, or deciding what a non-detection means.
It turns Włodzimierz Rączkowski's methodological critique into operational
controls for remote-sensing archaeology.

## Contents

- [Source identity and custody](#source-identity-and-custody)
- [The method stack](#the-method-stack)
- [Operational consequences](#operational-consequences)
- [Case workflow](#case-workflow)
- [Audit of the supplied notes](#audit-of-the-supplied-notes)
- [Source register](#source-register)

## Source identity and custody

The user-supplied URL is a scan of:

> Włodzimierz Rączkowski, "Metody w archeologii," in *Przeszłość
> społeczna: Próba konceptualizacji*, ed. Stanisław Tabaczyński, Arkadiusz
> Marciniak, Dorota Cyngot, and Anna Zalewska (Poznań: Wydawnictwo
> Poznańskie, 2012), 367-408. ISBN 978-83-7177-791-2.

It is **not** the complete 2002 monograph *Archeologia lotnicza - metoda
wobec teorii*. The 2002 book is cited in the chapter's bibliography, but the
linked PDF contains only the 2012 chapter plus front matter.

Source record:

- public locator: [e-archaeology.org PDF][R2012];
- accessed: 2026-07-24;
- file length: 46 PDF pages;
- printed chapter pages: 367-408; from PDF page 5 onward, printed page equals
  PDF page plus 362;
- SHA-256:
  `bba903a391c56d6725bf7e6c95296ac6556b290147be925f3ea258dab37745cc`;
- extraction: Apple Vision OCR in Polish and English, with visual checks of
  the title, copyright page, section openings, figures, and critical method
  passages;
- rights: PDF page 4 states copyright by the authors and Wydawnictwo
  Poznańskie (2012). The host makes the scan publicly accessible but neither
  the PDF nor the surrounding page states an open redistribution licence.

Keep the downloaded scan in a local, ignored research library. Do not bundle
the PDF, OCR text, or page images with the plugin. This reference is a
page-indexed paraphrase, not a substitute edition of the chapter.

The author's university also hosts a 19-page English summary of the actual
2002 monograph ([R2002S]). It is not the full 288-page Polish book. Its local
source record is:

- official locator: Adam Mickiewicz University Faculty of Archaeology;
- accessed: 2026-07-24;
- SHA-256:
  `fc5b0ecc232e48c43975e3a5cf4e033b67260b2022309e8d2430f4bd3a70fd12`;
- extraction: embedded English text checked against rendered pages;
- rights: no explicit open redistribution licence was located.

Summary-page citations below refer to this 19-page English document, not to
the printed pagination of the monograph. Keep it in the ignored local library
and do not bundle it with the plugin.

The two user-supplied pasted texts are useful research leads, but their
authorship and source chain are not established. Treat them as
`secondary-summary` until each claim is checked against a cited primary or
authoritative source.

## The method stack

Rączkowski uses *method* at three connected levels (pp. 367-372):

1. **Research frame:** assumptions about what can be known, the research
   question, and the role of theory.
2. **Procedure:** how sources are acquired, documented, described, analysed,
   interpreted, and used to justify a claim.
3. **Technique:** a particular instrument or operation such as aerial
   photography, LiDAR, a spectral index, interpolation, edge detection, or a
   classifier.

Do not describe a sensor or algorithm as a self-sufficient method. State the
question and expected physical proxy that make the technique relevant, the
procedure that turns its measurement into evidence, and the interpretive
assumptions that constrain the claim.

The 2002 summary makes the same point historically: flight and photography
technology existed before archaeology could use aerial images effectively.
The additional condition was a research frame able to recognize aerial traces
as relevant to a question (summary pp. 2-3). Technical availability therefore
does not establish methodological fitness.

### Source, data, and evidence are not synonyms

The chapter describes a common progression from archaeological source
(`record`), through documented or processed data (`data`), to support for a
claim (`evidence`). Decisions occur at every transition: what to collect,
which observations to preserve, how to categorize them, and which result
counts for or against a hypothesis (pp. 373-374).

Record these as separate authority levels:

```text
source measurement
  -> declared transformations and selections
  -> derived data product
  -> explicit evidentiary claim
  -> archaeological interpretation
```

Preserve the measurement and transformation lineage so a reviewer can reject
the interpretation without losing the underlying observation.

## Operational consequences

### Visibility is conditional

Aerial photography can reveal shadows, snow or flood patterns, moisture and
soil-colour differences, and differential vegetation growth. These are
conditions that make a proxy visible, not archaeological identities
(pp. 378-379).

Before acquisition, declare:

- expected proxy and causal chain;
- target dimensions and required ground sampling;
- useful crop, soil, moisture, illumination, or canopy conditions;
- dates or seasons likely to provide a contrast;
- modern and natural processes that can produce the same contrast;
- conditions under which the feature would probably remain invisible.

Do not convert a blank image, inventory, or candidate map into evidence of
absence. Kolenda and Rączkowski's later Lower Silesia case study shows how an
apparent settlement "emptiness" can be produced by the information resource
and method rather than past reality ([KR2018]).

### Images and visualizations are constructed products

Photography and remote-sensing images can appear to be direct, objective
copies of a landscape. The chapter instead treats seeing and interpretation
as learned practices shaped by research questions, prior knowledge, and a
shared visual language (pp. 379-382).

An aerial photograph records the crop, soil, shadow, and survey conditions at
the moment of reconnaissance. It does not provide direct contact with the
past society that produced a possible trace (2002 summary, pp. 16-17).

Audit at least:

- why this area, flight line, view angle, date, and image scale were chosen;
- what the frame excludes;
- whether a label, known-site outline, or expected morphology was visible to
  the interpreter;
- which enhancement or visualization first made the anomaly persuasive;
- whether an independent reviewer sees it in a minimally processed product.

Rączkowski's 2020 open-access follow-up extends this critique to digital
remote-sensing visualization, including standardization, classification,
persuasion, and aesthetics ([R2020]).

### Processing is part of interpretation

Digital acquisition does not remove human judgement. Band selection,
algorithm choice, normalization, interpolation, filtering, rendering, and the
decision that an output is "satisfactory" all shape the final image
(pp. 383-389).

For each derived artefact:

- hash and retain the earliest usable measurement or calibrated product;
- record software, version, parameters, masks, resampling, CRS, and output
  hash;
- state the physical or statistical reason for every transformation;
- save at least one conservative baseline and relevant alternative
  parameterizations;
- distinguish exploratory tuning from a recipe frozen before candidate
  review;
- report a candidate that disappears under reasonable settings as unstable.

Do not tune a visualization until a familiar site-like form appears and then
present the image as an independent observation.

### A terrain model is not bare ground itself

The chapter describes airborne laser scanning as a way to model
microtopography where some laser returns reach the ground through canopy
gaps. Ground filtering, point rejection, interpolation, scan density, and
visualization determine the produced terrain model (pp. 384-385).

Use the precise statement:

> Some emitted pulses or pulse components may return from the ground through
> canopy gaps; classified ground returns are then filtered and interpolated
> into a DTM.

Do not say that LiDAR simply "penetrates vegetation" or that a DTM is an
unmediated view of a surface. Inspect classification, density, gaps, and the
point cloud where available. Compare several visualization families and
scales.

### Documentation is also an interpretation

Descriptions, photographs, maps, database fields, and coded classes preserve
some observations while suppressing others. A universal, neutral database is
not achievable because its schema reflects the questions and categories
available to its designer (pp. 389-392).

Preserve:

- raw or earliest-calibrated input;
- derived artefacts rather than only the preferred final render;
- decision context for acquisition, documentation, and processing;
- free-text observations alongside controlled categories;
- rejected explanations and negative evidence;
- unknown and not-recorded values instead of forcing a class.

### A technique does not determine the conclusion

The same technique can serve different research frames. Its presence does not
identify the paradigm or validate the interpretation. The decisive issue is
how its result is interpreted and justified (pp. 404-406).

Keep these questions separate:

1. Is the measured anomaly repeatable?
2. Is an anthropogenic cause more plausible than natural or processing
   alternatives?
3. Is an archaeological cause independently supported?
4. What, if anything, supports a proposed date, function, or cultural
   attribution?

The 2002 summary calls the deliberate study of archaeology's theories,
methods, objectives, and inherited standards `metaarchaeology` (pp. 18-19).
Use the term as a reflexive audit, not as a separate source of evidence.

## Case workflow

### 1. Freeze a research frame

Fill the case ledger's `researchFrame` before candidate generation:

- `expectedProxy`: the measurable property, not the desired site type;
- `visibilityConditions`: circumstances needed for useful contrast;
- `targetScale`: expected size range and required spatial resolution;
- `alternativeExplanations`: natural, modern, and processing hypotheses;
- `decisionRule`: what result advances or rejects the candidate;
- `falsifier`: evidence that would materially weaken the preferred
  interpretation;
- `interpretivePrior`: known records, labels, or expectations visible to the
  analyst.

For a rediscovery benchmark, keep target coordinates and identity outside
this frame and outside the candidate-generation process.

### 2. Log consequential choices

Append a `decisionLog` entry whenever the analyst selects an acquisition,
band, date, mask, kernel, visualization, threshold, classifier, or candidate
cutoff. Include the rationale, alternatives considered, whether target labels
were visible, and affected artefact hashes.

### 3. Separate outputs

Use the evidence contract's `observed`, `derived`, `inferred`, and
`corroborated` levels. Never allow a class name generated by a model to become
an observed fact.

### 4. Run a reflexive review

Before accepting a candidate:

- inspect the source or minimally processed product;
- compare relevant dates, modalities, scales, and parameterizations;
- test at least two non-archaeological explanations;
- ask what acquisition or processing choice made the feature visible;
- ask what reasonable choice would make it disappear;
- obtain a blind or independent review when the claim matters;
- state the validation gap and location-disclosure class.

### 5. Phrase negative results correctly

Write:

> No matching proxy anomaly was detected in the surveyed area with these
> sources, visibility conditions, resolutions, and processing choices.

Do not write:

> No archaeological site is present.

## Audit of the supplied notes

### Supported by the 2012 chapter

- aerial visibility through shadow, snow/flood, moisture, soil colour, and
  vegetation response (pp. 378-379);
- the dependence of aerial-photographic practice on theory and learned visual
  conventions (pp. 379-382);
- spatial and spectral resolution as constraints on satellite use
  (pp. 382-384);
- researcher choice in band selection, processing, algorithms, and
  visualization (p. 384);
- ALS ground-return filtering, interpolation, and visualization as
  interpretive stages (pp. 384-385);
- processing and presentation choices in geophysical prospection
  (pp. 385-389);
- documentation and database schemas as selective interpretations
  (pp. 389-392).

### Supported by the official 2002 English summary

- the user's list of Crawford, early aerial-photography practitioners, the
  cultural-historical and processual turns, and the later postprocessual image
  critique is broadly consistent with the summary (pp. 3-18);
- cropmark, soilmark, and shadow interpretation developed together with
  reflection on moisture, soils, plants, formation processes, and
  disagreement among survey methods (pp. 10-11);
- classifications are problem-dependent even when heritage databases require
  standardized categories (pp. 10-14);
- predictive modelling is presented as a historically processual use of
  environmental variables, sampling, aerial images, and satellite data
  (pp. 11-14), not as a universal recipe;
- aerial photographs are culturally read and do not directly reproduce past
  social reality (pp. 16-18);
- research questions and theory govern the scope and interpretation of a
  method more strongly than the method determines theory (pp. 18-19).

### Supported by later primary publications

- method-produced "emptiness" and the danger of reading non-detection as
  historical absence: Kolenda and Rączkowski (2018) ([KR2018]);
- critical treatment of remote-sensing visualizations as culturally and
  technically produced: Rączkowski (2020) ([R2020]);
- UAS use across RGB, infrared, multispectral, hyperspectral, LiDAR, and radar
  applications, with persistent metric and radiometric validation gaps:
  Adamopoulos and Rinaudo (2020) ([UAS2020]).

### Retain only as leads until verified

- a universal `~50 mm` potential soil-moisture-deficit threshold;
- general claims that one soil family is always better than another;
- a generic `0.5-1 m` maximum useful burial depth;
- universal settlement preferences based only on water, slope, defence, or
  soil fertility;
- claims that one visualization, index, season, or model transfers worldwide;
- unsourced lists of publications, projects, product models, or performance.

These may be useful in a defined region, crop, sensor, or period, but the
supplied summaries do not establish their scope. Predictive models built from
environmental preferences also risk circularity and environmental
determinism. Validate them on geographically separated data and preserve
social, historical, and survey-access alternatives.

### Correct before use

- Replace "LiDAR penetrates vegetation" with the ground-return and
  classification description above.
- Treat Google Maps and Google Earth as bounded interface references. Do not
  use hidden extraction, mass download, batch capture, stitching, or
  reconstruction. A small permitted, attributed Earth capture may support an
  explicitly recorded exploratory local check; use canonical licensed data for
  systematic, repeatable, training, or evaluation work. Never analyze Street
  View or copy-prohibited catalog/generated output.
- Treat the 2012 chapter's IKONOS and Landsat examples as historical. Verify
  current sensor specifications and access terms in
  [research.md](research.md) and [imagery-sources.md](imagery-sources.md).

## Source register

| ID | Source | Use |
| --- | --- | --- |
| R2002S | Rączkowski (2002), official English monograph summary, 19 pp. | History of aerial archaeology and method-theory argument; not the full book |
| R2012 | Rączkowski (2012), "Metody w archeologii," pp. 367-408 | Primary chapter supplied by user; method-theory foundation |
| KR2018 | Kolenda and Rączkowski (2018), "Anatomia pustki," DOI `10.23858/PA66.2018.012` | Non-detection and method-produced information gaps |
| R2020 | Rączkowski (2020), "Power and/or Penury of Visualizations," DOI `10.3390/rs12182996` | Digital visualization and technology critique |
| UAS2020 | Adamopoulos and Rinaudo (2020), UAS review, DOI `10.3390/drones4030046` | Post-2002 sensor and validation cross-check |

[R2002S]: https://archeo.amu.edu.pl/__data/assets/pdf_file/0025/117448/Archeologia-lotnicza-metoda-wobec-teorii.pdf
[R2012]: https://e-archaeology.org/wp-content/uploads/2016/06/R%C4%85czkowski.pdf
[KR2018]: https://doi.org/10.23858/PA66.2018.012
[R2020]: https://doi.org/10.3390/rs12182996
[UAS2020]: https://doi.org/10.3390/drones4030046
