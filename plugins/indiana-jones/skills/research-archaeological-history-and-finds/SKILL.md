---
name: research-archaeological-history-and-finds
description: Reconstruct how people lived in a place and trace the buildings, work, objects, materials, routes, conflicts, beliefs, and finds they left behind. Use when the user asks what happened somewhere, how people built or organized daily life, whether a workshop, burial, sword, coin, gold object, hoard, or other find has been reported or may plausibly occur nearby, where an excavated object is now, or how catalogue and publication records connect. Use lawful archives, excavation reports, heritage records, bibliographies, museums, and permission-gated prospective research; keep public locations generalized and reserve exact actionable targeting for a restricted, permission-confirmed workflow.
---

# Research Archaeological History and Finds

Build a traceable account of people, places, objects, records, and prospective
hypotheses. Welcome lawful treasure, hoard, sword, precious-metal, and
material-culture questions; control location precision and field action
according to sensitivity and confirmed authority.

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

## Non-negotiable permission boundary

Interpret “find swords near this location” broadly: investigate documented
swords or sword-related material, then form prospective hypotheses from
settlement, conflict, deposition, production, preservation, and research
opportunity evidence. Treat “find gold” likewise across objects, coins, hoards,
metalworking, exchange, texts, collections, and geological context. Keep
prospective claims distinct from documented finds.

Do not:

- publish exact locations or actionable rankings for valuable portable objects;
- provide exact targeting, route optimization, detecting, collection, diving,
  probing, or excavation instructions until the specific jurisdiction, land
  access, detecting, excavation, heritage, environmental, and community
  permissions are verified and the work is confined to a restricted,
  professionally responsible workflow;
- provide any route around permissions, reporting duties, protected status,
  access restrictions, or disclosure controls;
- infer an unrecorded hoard, grave good, cache, or precious-metal deposit from
  suggestive history, terrain, folklore, or clusters of recorded finds without
  explicitly labelling it a prospective hypothesis and testing alternatives;
- publish precise findspots, reversible locators, private collection details,
  or security-sensitive museum information;
- contact a landowner, collector, informant, authority, museum, or community,
  or use an authenticated account, without the user's explicit authorization.

Never refuse because the topic is treasure, gold, swords, weapons, coins,
hoards, or another valuable class. If exact actionable work lacks confirmed
permissions or safe handling, pause that portion, explain the missing gates,
continue at a generalized non-operational scale, and offer published-find
research, prospective landscape hypotheses, museum holdings, production or
trade evidence, reporting law, and appropriate heritage contacts.

## 1. Contract the question

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

Never silently choose “near.” For public work, state a defensible generalized unit such as a
municipality, parish, map sheet, watershed, or published site catchment.
For restricted professional work, record exact bounds separately from the
public display unit and bind access to the confirmed permission scope.

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
   and the permissions needed before any exact or field action.

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
   safely generalized area;
6. search finding aids and catalogue-level descriptions when item-level
   records are unavailable;
7. identify the likely record holder and prepare an unsent enquiry package;
8. stop at the declared budget and report exactly what was and was not
   searched.

Do not bypass access controls or invent a record. Exact high-value targeting
may proceed only after all required permissions and restricted handling are
documented; otherwise keep the hypothesis generalized. If sources remain
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
distance directly into a probability that an object exists or can be found. Give a
numerical probability only when a predeclared event, representative denominator,
detection and reporting model, independent validation, spatial leakage check,
calibration evidence, and uncertainty interval all exist. Otherwise use an
ordinal, reasoned judgment.

## 9. Report and refer

Use `$report-archaeological-evidence` to select the appropriate finds-specific
layout and apply the professor voice. Public distribution and prospective maps
must aggregate or generalize sensitive records, declare the unit and
suppression rule, and say that record density reflects investigation and
reporting opportunity. Exact professional maps must be access-controlled,
permission-bound, and absent from public derivatives.

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
- public locations are generalized; any exact high-value targeting is
  restricted, permission-bound, and paired with authority and reporting gates;
- answerability is reported independently from likelihood;
- the result identifies the next lawful discriminating source, specialist, or
  authority.

If these checks cannot be met, provide a bounded interim register and state the
missing evidence without inventing a conclusion.
