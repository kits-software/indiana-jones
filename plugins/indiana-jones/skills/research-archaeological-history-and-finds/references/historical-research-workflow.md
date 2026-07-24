# Historical and finds research workflow

## Contents

1. Question decomposition
2. Name and terminology concordance
3. Source discovery order
4. Query and source ledger
5. Chronology synthesis
6. Contradictions and copied claims
7. Sparse-source fallback
8. Stopping and handoff

## Question decomposition

Turn a broad question into independently answerable claims:

| Question | Required evidence | Frequent trap |
| --- | --- | --- |
| What happened here through time? | phase-dated primary, archaeological, and landscape evidence | flattening centuries into one story |
| Have swords been documented nearby? | object/find records with identity, context, chronology, and safe spatial association | counting replicas, illustrations, or copied reports |
| Is gold documented? | material-specific record with identification basis | confusing gilt, electrum, colour, place-name, and analysed gold |
| Was gold worked locally? | production evidence or securely located documentary craft evidence | treating a finished object as workshop evidence |
| Where is the object now? | accession and custody evidence verified currently | treating an old publication as current custody |
| How likely is the claim? | defined event, denominator, bias model, and calibration | converting search counts into probability |

Write the allowed answer class before searching: documented existence,
association, history, present custody, prospective hypothesis, source coverage,
or an explicitly calibrated estimate. Do not allow a documentary question to
drift into exact or field-action targeting without the required permission and
restricted-handling gate.

## Name and terminology concordance

Build a compact concordance before broad search:

- current official place name and gazetteer identity;
- historical, colonial, endonym, exonym, administrative, parish, estate, and
  excavation-area names;
- local-language forms, diacritics, transliterations, grammatical variants,
  and common OCR errors;
- former institution and collection names;
- object-class synonyms, typological terms, obsolete terminology, plural
  forms, and uncertain classifications;
- material terms and distinctions such as gold, gilded, electrum, foil,
  bullion, coin, jewellery, and metalworking;
- relevant excavation codes, inventory prefixes, collection names, and known
  scholars or projects.

Preserve the source and time validity of each alias. Do not assume two historic
places are identical because they share a translated name.

## Source discovery order

Prefer direct jurisdictional and collection sources:

1. official archaeological inventories, finds registers, statutory reports,
   excavation archives, and planning-archaeology repositories;
2. museum, university, archive, and collection catalogues;
3. specialist excavation and finds publications;
4. archaeological data repositories and disciplinary bibliographies;
5. digitized primary documents, maps, photographs, account books, finding
   aids, and newspapers;
6. peer-reviewed syntheses, theses, and research portals;
7. local histories, community sources, auction catalogues, collector claims,
   social posts, and search snippets as leads only.

Select source families for the actual jurisdiction at runtime. Examples of
useful infrastructure may include national heritage inventories, recognized
portable-antiquities schemes, museum APIs, ARIADNE-connected repositories,
Open Context, tDAR, ADS, Europeana, library catalogues, Crossref, OpenAlex,
OAI-PMH repositories, IIIF manifests, and institutional finding aids. These
examples are discovery leads, not guaranteed current endpoints or universal
authorities.

Verify:

- geographic and chronological remit;
- record granularity and update date;
- whether locations are deliberately generalized;
- licence, API, export, and citation terms;
- whether records are primary or harvested copies;
- whether absence from the service is meaningful.

## Query and source ledger

Record every consequential search:

| Field | Record |
| --- | --- |
| Query ID | Stable local ID |
| Service | Exact catalogue, archive, index, or interface |
| Date | Search date and timezone |
| Access | Public or explicitly authorized named account |
| Query | Exact string, filters, fields, language, and sort |
| Scope | Geographic, temporal, collection, and record-type coverage |
| Results | Count reviewed, IDs retained, and duplicate handling |
| Limitations | Indexing, OCR, truncation, unavailable pages, or access gap |
| Next branch | Alias, citation, source family, or stopping rule |

For APIs or exports, preserve request parameters, response metadata, stable
record identifiers, and a hash or snapshot where the terms permit. For manual
viewers, record the URL, query, access date, and visible record metadata
without scraping.

Create a separate source register. A query is an action; a source is evidence.

## Chronology synthesis

Use bounded phases appropriate to the evidence, not uniform centuries by
default. Represent:

- earliest and latest possible dates;
- dating basis;
- event type: manufacture, use, deposition, construction, abandonment,
  recovery, documentation, or interpretation;
- place identity valid for that phase;
- supporting and conflicting origin families;
- certainty and unresolved interval.

Build a phase table:

| Phase | Directly attested | Inferred activity | Object/find evidence | Conflict or gap |
| --- | --- | --- | --- | --- |

Then explain transitions. Distinguish a change in past activity from a change
in record survival, excavation intensity, collecting practice, cataloguing, or
administrative boundary.

Use genuine stratigraphic relations only for observed physical contexts. A
sequence of rulers, wars, maps, or publications is a research chronology, not
a Harris Matrix.

## Contradictions and copied claims

For each important assertion:

1. locate the earliest accessible origin;
2. identify later sources that independently observed or merely repeated it;
3. compare identifiers, dates, measurements, context, images, and repository;
4. preserve contradictory descriptions;
5. assign status and the evidence needed to resolve it.

Common copied-claim patterns include:

- a museum catalogue repeating an antiquarian place attribution;
- multiple articles citing one preliminary excavation announcement;
- news and social reports quoting one press release;
- collection aggregators harvesting one source record;
- modern maps copying an older uncertain site pin.

Count origin families, not URLs. Report when the origin is inaccessible.

## Sparse-source fallback

Use this branching ladder and stop after the declared budget:

1. exact official name + exact class;
2. aliases, former names, excavation codes, repository IDs;
3. local-language, historical spelling, transliteration, diacritics, and OCR
   variants;
4. broader typology, material, function, and part terms;
5. citation chaining from the strongest located source;
6. archive or catalogue finding aids above item level;
7. one-step geographic or chronological broadening with the change declared;
8. current repository or authority identification;
9. unsent, minimal enquiry package;
10. source-gap report.

Return one of:

- **documented** — a traceable record supports the requested association;
- **documented with material limitations** — a record exists but identity,
  context, chronology, or custody is weak;
- **not located in searched sources** — no relevant record was found within
  explicit coverage;
- **not assessable** — sources, permissions, language, cataloguing, or
  identifiers are inadequate;
- **protected or private-source gated** — a genuinely protected/confidential
  location or unauthorised private source prevents exact disclosure; continue
  with the greatest lawful precision. Field permissions gate field action, not
  desk candidates, coordinates, rankings, plates, or estimates.

Never replace `not located` with `did not exist`.

## Stopping and handoff

Predeclare at least one stop:

- named source classes exhausted;
- a time or query budget reached;
- marginal searches return only repeated origin families;
- identity cannot advance without an inaccessible record;
- source terms or authorization prevent the next lawful action;
- the question has enough independent evidence for its intended decision;
- the remaining private-source, protected-site, or field-action work lacks its
  applicable consent, permission, authority, or handling channel.

At handoff provide:

- question, place/time scope, terminology concordance, and disclosure;
- source and query ledgers;
- normalized object/find/context/custody records;
- chronology and claim-conflict matrix;
- coverage and answerability judgment;
- safest useful next source, specialist, or authority;
- what not to infer.
