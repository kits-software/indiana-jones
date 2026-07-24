# Object, find, assemblage, and custody evidence contract

## Contents

1. Record separation
2. Required fields
3. Context quality
4. Object identity and reconciliation
5. Chronology and material claims
6. Object and custody biographies
7. Gold and production claims
8. Contradictions and negative evidence

## Record separation

Keep these entities distinct even when a source combines them:

- **object** — one physical item or defined fragment set;
- **assemblage** — a source-defined group, not automatically one deposition;
- **find event** — discovery or recovery under stated circumstances;
- **archaeological context** — deposit, feature, layer, structure, or survey
  unit with its own identifier and interpretation;
- **classification** — typology or functional label assigned by a named source;
- **analysis** — measurement or expert assessment with method, sample, and date;
- **repository record** — catalogue or accession description;
- **custody event** — accession, loan, transfer, loss, deaccession,
  repatriation, or current holding;
- **claim** — an assertion made by one source about any of the above.

A repository catalogue entry is evidence about an object; it is not the
object. A find event is not a depositional event. A collection assemblage is
not necessarily an archaeological assemblage.

## Required fields

### Source

- stable local source ID;
- title, creator or institution, source type, date, locator, and access date;
- publication, catalogue, inventory, accession, excavation, or archive IDs;
- origin family and sources it copies or cites;
- access basis, licence, disclosure, and preserved snapshot or hash when
  permitted;
- page, figure, record, folio, or query position supporting the claim.

### Object or assemblage

- stable local ID and source-native IDs;
- original name and normalized object class;
- part/whole and assemblage relationships;
- material as stated, analytical method if tested, and uncertainty;
- manufacture or decoration observations;
- measurements, count, condition, and completeness;
- typology, function, cultural attribution, and named attribution source;
- date interval, date basis, and confidence;
- authenticity or modern-intrusion concerns;
- associated finds and context ID;
- sensitivity and public-display rule.

### Find event and context

- event date or interval and event type;
- recovery method: controlled excavation, evaluation, field survey, chance
  find, detecting under a lawful scheme, dredging, antiquarian collection,
  market appearance, or unknown;
- finder or excavator only where ethically and lawfully publishable;
- source location and precision;
- safe public location and generalization method;
- stratigraphic or spatial context ID;
- context description, integrity, disturbance, and association basis;
- reporting authority and report or case number where public;
- chain from field record to repository record.

### Custody or repository event

- event type, date or interval, institution or lawful custodian;
- accession, old accession, loan, transfer, or collection IDs;
- evidence source and certainty;
- predecessor and successor custody records;
- current-status verification date;
- restrictions, claims, or unresolved ownership.

## Context quality

Use an explicit ordinal context-quality label:

| Label | Meaning |
| --- | --- |
| `secure-excavated` | Recorded controlled context with usable stratigraphic documentation |
| `recorded-survey` | Systematic survey context with declared spatial precision |
| `reported-find` | Find event documented, but context integrity is limited |
| `legacy-provenance` | Antiquarian, old-collection, or incomplete contextual history |
| `market-only` | Known from commerce without an independently documented find context |
| `unknown` | Recovery circumstances cannot be established |

Do not let a prestigious current repository improve a weak find context.
Report context quality independently from confidence in the object's present
identity.

## Object identity and reconciliation

Compare:

- accession, excavation, inventory, and publication identifiers;
- material, measurements, weight, preserved portions, decoration, and damage;
- excavation context, find date, find circumstances, and repository;
- photographs or drawings whose reuse is permitted;
- publication and catalogue histories;
- known conservation changes, joins, or separated fragments.

Assign an identity relation:

- `same-object` — decisive identifiers or an unbroken documented chain;
- `probable-same-object` — multiple specific agreements and no material
  contradiction;
- `possible-same-object` — plausible but underdetermined;
- `different-object` — decisive incompatible evidence;
- `unresolved` — insufficient or conflicting evidence.

Preserve the original records. Never collapse them merely to simplify the
story. Record who made the link, when, why, and which evidence could overturn
it.

## Chronology and material claims

Represent chronology as an interval plus a basis:

- stratigraphic relation;
- absolute laboratory date and calibrated range;
- diagnostic association;
- typology or style;
- inscription or coin;
- documentary date;
- repository assertion without accessible basis;
- broad historical inference.

Do not convert a century label into a false point date. Separate an object's
manufacture, use, deposition, discovery, publication, and accession dates.

Record material claims exactly:

- visual identification;
- historical catalogue term;
- non-destructive compositional method;
- sampled laboratory analysis;
- inferred alloy or source;
- unknown.

“Gold,” “gilt,” “electrum,” “gold-coloured,” and “gold-associated” are not
interchangeable.

## Object and custody biographies

Create two ordered sequences:

```text
manufacture → use → repair/reuse → deposition → recovery

reporting → excavation/collection → publication → accession
→ conservation/analysis → transfer/loan/repatriation → current custody
```

Every event needs a bounded date, claim source, and certainty. Use `unknown
interval` rather than a plausible invention. Mark institutional name changes
separately from physical custody changes.

For a private, legacy, market, or conflict-affected chain:

- do not expose private personal details;
- do not validate lawful title from catalogue presence alone;
- identify gaps and inconsistent narratives neutrally;
- route legal, restitution, repatriation, and descendant-community questions
  to the relevant authority or specialist.

## Gold and production claims

Classify every gold-related claim into one lane:

| Lane | Examples | Maximum direct claim |
| --- | --- | --- |
| `object` | tested gold ornament, coin, foil | a gold-bearing object is documented |
| `production` | crucible residue, mould, tools, waste, unfinished object | production activity may be present |
| `specialist-analysis` | composition, isotope, trace element, microscopy | measured material or technical relation |
| `documentary-craft` | recorded goldsmith, workshop rent, guild account | documented craft activity |
| `exchange-or-use` | payment, tribute, gift, deposition, curated heirloom | attested or inferred circulation/use |
| `natural-occurrence` | geological or mining evidence | mineral occurrence or extraction |
| `terminology-only` | place-name, folklore, later epithet | a lead requiring independent evidence |

Do not promote an `object` record into `production`; require production waste,
tools, residues, unfinished items, workshop structure, specialist analysis, or
an independently supported documentary workshop. Even then, state whether
production was local, nearby, imported, or unresolved.

Apply the same discipline to weapons. A sword may represent manufacture, use,
display, curated deposition, burial association, redeposition, river loss, or
later collection. Its presence does not by itself identify a battlefield,
armoury, workshop, or route.

## Contradictions and negative evidence

Maintain a claim matrix:

| Claim ID | Assertion | Source/origin family | Supporting basis | Conflict | Status |
| --- | --- | --- | --- | --- | --- |

Use `supported`, `contested`, `superseded`, `unverified`, or `rejected`, with a
reason. A later catalogue is not automatically superior; it may silently copy
an older error.

Record unsuccessful catalogue queries with service, query, filters, date,
result count, and access limitations. These establish search coverage, not
archaeological absence.
