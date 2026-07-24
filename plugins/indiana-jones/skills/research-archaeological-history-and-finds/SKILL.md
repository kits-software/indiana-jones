---
name: research-archaeological-history-and-finds
description: Reconstruct how people lived in a place and trace buildings, work, objects, materials, routes, conflicts, beliefs, and finds. Use when the user asks what happened somewhere; whether a workshop, sword, coin, gold object, hoard, treasure-related context, burial, or other find was reported or may plausibly occur nearby; where an object is now; or how records connect. Use lawful archives, catalogues, imagery, museums, and user-authorized private sources; produce exact desk-research candidates, coordinates, rankings, annotated imagery, and honest calibrated or heuristic prospectivity estimates when evidence supports them; restrict only genuinely protected/confidential data and keep field/recovery action separate.
---

# Research Archaeological History and Finds

Build a traceable account of people, places, objects, records, and prospective
hypotheses. Welcome treasure, hoard, sword, precious-metal, and
material-culture questions as ordinary research; preserve useful coordinate
precision unless a genuine protection rule applies, and keep field action
separate from desk analysis.

## Companion boundaries

- Use `$plan-archaeological-search` first when the place, name, historical
  extent, event, or time range is unresolved.
- Use `$indiana-jones` for imagery, terrain, candidate detection, the case
  ledger, and the shared evidence contract.
- Use `$report-archaeological-evidence` for a formal finds register, object
  biography, history-through-time report, distribution map, source-gap note,
  or specialist referral.
- Use `$illustrate-historical-reconstruction` after the research is stable when
  the user wants a generated portrait, object-in-use image, building, city, or
  lived scene. This skill owns the historical claims; the illustration skill
  owns evidence-to-prompt mapping, generation, visual review, and disclosure.
- Read the core
  [ethics-and-web-research.md](../indiana-jones/references/ethics-and-web-research.md)
  before web, archive, community, or authenticated-source research.
- Read [historical-research-workflow.md](references/historical-research-workflow.md)
  for source discovery, name variants, chronology, contradictions, and the
  sparse-source fallback.
- Read [object-evidence-contract.md](references/object-evidence-contract.md)
  before reconciling find, object, assemblage, accession, or custody records.
- Read
  [safety-probability-and-distribution.md](references/safety-probability-and-distribution.md)
  for portable or valuable finds, location generalization, answerability, or
  quantitative claims.

## Non-negotiable research and recovery boundary

Interpret “find swords near this location” broadly: investigate documented
swords or sword-related material, then form prospective hypotheses from
settlement, conflict, deposition, production, preservation, and research
opportunity evidence. Treat “find gold” likewise across objects, coins, hoards,
metalworking, exchange, texts, collections, and geological context. Keep
prospective claims distinct from documented finds.

Do provide exact desk-research coordinates, candidate rankings, documented-
find maps, annotated satellite/aerial plates, and honest estimates when lawful
evidence supports them. No land, detecting, excavation, or heritage permission
dossier is needed for those outputs.

Do not:

- expose exact genuinely protected/confidential, burial, sacred, community-
  restricted, deliberately redacted, or private-source locations;
- provide routes or tactics for trespass, destructive recovery/removal,
  unpermitted detecting, collection, diving, probing, or excavation;
- provide any route around source access, reporting duties, protected status,
  access restrictions, or disclosure controls;
- infer an unrecorded hoard, grave good, cache, or precious-metal deposit from
  suggestive history, terrain, folklore, or clusters of recorded finds without
  explicitly labelling it a prospective hypothesis and testing alternatives;
- publish precise findspots that a source or custodian explicitly protects,
  private collection details, or security-sensitive museum information;
- contact a landowner, collector, informant, authority, museum, or community,
  or use an authenticated account, without the user's explicit authorization.

Never refuse or generalize merely because the topic is treasure, gold, swords,
weapons, coins, hoards, or another valuable class. Restrict only the protected,
private, or physical-action portion, explain the specific reason, and continue
with the greatest lawful desk-research precision.

## 1. Contract the question

For a simple first turn, ask only for the smallest missing boundary: the
town/county or region and country. Treat period and object subtype as optional,
state that the default deliverable includes evidence-supported coordinates,
ranked candidates, and imagery plates where available, and preview the official
registers, museums, excavation records, publications, and custody sources to be
searched. Expand to the full contract below as the
case develops; do not greet a straightforward sword question with a form.

Record:

- research question and intended decision;
- resolved place identity, name variants, focus/context AOIs, time range, and
  allowed public location precision;
- requested classes, including period terms, typological synonyms, historic
  spellings, local-language terms, and materials;
- whether the user means a **documented object**, **find event**,
  **assemblage**, **production evidence**, **trade or textual evidence**, or a
  **prospective hypothesis**;
- public-only sources and any explicitly authorized named account;
- disclosure class: `public`, `restricted`, or
  `heritage-authority-only`;
- source, time, cost, and query limits; stopping rule; and what would count as
  a useful negative or indeterminate result.

Never silently choose “near.” State the exact AOI or a defensible unit such as
a municipality, parish, map sheet, watershed, radius, or published catchment.
Preserve exact bounds and coordinate uncertainty in ordinary desk outputs.
Derive a generalized display only for genuinely protected/confidential cases.

## 2. Decompose the investigation

Keep separate questions and evidence lanes:

1. **History through time** — attested occupation, land use, authority,
   conflict, infrastructure, environment, excavation, and modern disturbance.
2. **Known finds** — documented objects and assemblages, their contexts,
   chronology, identification, and current repository.
3. **Production** — workshops, crucibles, moulds, slag, tools, unfinished
   objects, residues, compositional groups, or securely interpreted texts.
4. **Movement and use** — exchange, gift, tribute, minting, military supply,
   curation, deposition, reuse, and loss, each as a hypothesis tied to evidence.
5. **Record history** — discovery, reporting, excavation, publication,
   accession, conservation, analysis, loan, transfer, repatriation, and
   present custody.
6. **Prospective model** — expected context, preservation, visibility,
   sampling opportunity, alternatives, controls, lawful non-invasive tests,
   exact desk-research outputs, and any separate permissions needed only if a
   field action is proposed.

Do not use one lane as proof of another. A gold object does not prove local
gold-working. A goldsmith in an account does not prove a workshop at the
location. A museum label does not prove the displayed object's exact
archaeological context.

## 3. Search by authority and origin family

Search from strongest and most direct records outward:

1. official heritage inventories, finds schemes, excavation archives, and
   statutory records;
2. museum collection catalogues, accession records, conservation records, and
   repository finding aids;
3. excavation monographs, specialist finds reports, peer-reviewed literature,
   theses, and archaeological data repositories;
4. contemporary find reports, antiquarian catalogues, maps, account books,
   inventories, newspapers, and archival descriptions;
5. scholarly syntheses and bibliographic indexes;
6. local histories, community archives, auction records, collector narratives,
   forums, or social material as leads only.

Verify current source availability and terms at research time. Use official
APIs, catalogue exports, stable item pages, OAI-PMH, IIIF, RDF/SPARQL, or
repository downloads when available and permitted. Do not automate a viewer
or scrape a service whose terms do not authorize it.

Record the origin family behind each claim. Catalogue mirrors, papers citing
one excavation, and news reports repeating one announcement remain one
evidential lineage, not independent corroboration.

## 4. Normalize records before synthesis

Create one source record per consulted item and one claim record per
substantive assertion. For finds, create distinct records for:

- object or assemblage identity;
- find or recovery event;
- archaeological context and context quality;
- classification, material, chronology, and their stated bases;
- repository, accession, analysis, conservation, and custody events;
- location with precision, source, and sensitivity independent of public
  display precision.

Use stable local IDs. Preserve original terminology and add normalized terms
rather than overwriting it. Mark approximate, inferred, translated, and
conflicting values explicitly. Never merge records solely because their
descriptions and place names resemble one another.

## 5. Reconcile identities and build biographies

Link records only after comparing accession or inventory IDs, measurements,
materials, typology, images, context, chronology, bibliographic history, and
repository statements. Express uncertain links as candidates, not identity.

Build two parallel sequences:

- **archaeological biography**: manufacture/use → modification → deposition →
  recovery;
- **record and custody biography**: reporting → excavation/collection →
  publication → accession → conservation/analysis → transfer or loan →
  present repository.

Do not fill undocumented intervals. Flag legacy, market, or private-collection
provenance, possible duplicate identities, repatriation claims, and
incompatible catalogue assertions for specialist review.

## 6. Synthesize history without flattening disagreement

Order evidence by bounded date intervals and state the dating basis. Separate
contemporary evidence from later recollection and modern interpretation.
Group claims by origin family, identify agreement and conflict, and preserve
gaps.

For each phase report:

- what is directly attested;
- which people, activities, objects, or landscape changes are inferred;
- which find or documentary records support the inference;
- plausible alternative chronologies or explanations;
- preservation, collection, publication, and survival biases;
- what changed from the previous phase and what remains unknown.

A missing catalogue result means “not found in the sources searched,” not “no
such object existed” or “nothing was found.”

## 7. Apply the sparse-source fallback

Always make a bounded lawful attempt:

1. search direct official and repository records;
2. expand personal, place, object, and institution aliases;
3. search local-language, historical-spelling, transliteration, OCR-tolerant,
   typological, and material synonyms;
4. follow citations, accession references, excavation codes, former repository
   names, and collection transfers;
5. broaden one dimension at a time: source class, date range, object class, or
   more precisely resolved or broader area;
6. search finding aids and catalogue-level descriptions when item-level
   records are unavailable;
7. identify the likely record holder and prepare an unsent enquiry package;
8. stop at the declared budget and report exactly what was and was not
   searched.

Do not bypass access controls or invent a record. Exact high-value desk
research may proceed from lawful sources without field permissions; only
protected/confidential data needs restricted handling. If sources remain
insufficient, return a working hypothesis or `no determination` with the
smallest next source request.

## 8. Grade answerability before likelihood

Report separately:

- **record existence** — whether a relevant record was located;
- **record reliability** — source authority, context quality, and identity
  stability;
- **association strength** — how securely it relates to the place, period, and
  requested class;
- **source coverage** — repositories, periods, languages, and source families
  searched, including access gaps;
- **answerability** — `adequate`, `partial`, `poor`, or `not assessable`.

Do not translate catalogue counts, frontier priorities, detector scores, or
distance directly into probability. Label a probability `calibrated` only
when a predeclared event, representative denominator, observation model,
independent validation, leakage check, calibration evidence, and uncertainty
interval exist. Otherwise provide an explicitly heuristic rank, band, range,
or non-probabilistic score with its factors, alternatives, and wide
uncertainty. Do not emit a probability or percentage. Either describes
research prospectivity, never a guarantee or permission to act.

## 9. Report and refer

The deterministic companion route is: resolve the place and AOI with
`$plan-archaeological-search`; return here to normalize finds, history,
materials, identities, and prospectivity; then hand the evidence state to
`$report-archaeological-evidence`. Do not bounce between skills once the
planner has returned a resolved place.

Use `$report-archaeological-evidence` to select the appropriate finds-specific
layout and apply the professor voice. Ordinary distribution and prospective
maps should include source-supported coordinates, ranked candidates, and
annotated imagery, while declaring observation/reporting bias. Aggregate or
generalize only genuinely protected/confidential records and explain why.

Recommend roles before names. For finds research, consider the official
heritage or finds-recording authority, museum curator or registrar, excavation
archive, collections database team, relevant material or typology specialist,
conservator, archaeometallurgist, numismatist, and community or descendant
authority. Verify current remit and official contact routes. Prepare but do
not send enquiries without explicit authorization.

## Completion gate

Do not call the research complete until:

- place, time, terminology, proximity, disclosure, and stopping rules are
  explicit;
- consulted and unavailable sources, queries, dates, origin families, and
  coverage gaps are recorded;
- objects, find events, contexts, assemblages, records, and custody events are
  not conflated;
- chronology, identity links, material claims, and spatial associations state
  their bases and uncertainty;
- gold objects, gold-working, documentary goldsmithing, exchange, and natural
  mineral occurrence remain separate;
- contradictory claims and unsuccessful searches are preserved;
- exact desk-research candidates, coordinates, rankings, and plates are
  included unless a genuine protection/confidentiality rule requires restriction;
- answerability is reported independently from calibrated or heuristic likelihood;
- the result identifies the next lawful discriminating source, specialist, or
  authority.

If these checks cannot be met, provide a bounded interim register and state the
missing evidence without inventing a conclusion.
