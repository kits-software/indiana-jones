# Worldwide source routing for place-led archaeological planning

No global catalog is a comprehensive legal heritage inventory. Route by
jurisdiction, authority, language, source lineage, access stage, and
sensitivity.

## Safety and query privacy first

Classify the AOI as:

- `public`;
- `public-generalized`;
- `restricted-research`;
- `community-or-authority-controlled`.

Public search engines, APIs, cloud notebooks, and map links may retain query
coordinates. For a restricted AOI, search only coarse administrative units,
download lawful regional data, and filter locally. Do not put access tokens in
URLs, plans, logs, screenshots, or citations.

Assign every source:

- `workflowRole`: `analysis`, `negative-control`, `research-context`,
  `corroboration`, `ground-truth`, or `manual-reference`;
- `accessStage`: `pre-detection`, `post-freeze`, or `post-unblinding`;
- `originFamilyId`: the underlying account, dataset, inventory, or measurement
  lineage;
- authority, query, access date, coverage, scale/resolution, rights, access
  basis, sensitivity, and checksum.

Maintain a separate claim ledger with the exact passage/map feature, spatial
and temporal uncertainty, supports, contradictions, analyst, and status.

## 1. Place and name concordance

Start with the competent official national gazetteer when available, then use
federated/collaborative services as crosswalks:

- [GeoNames downloads/API](https://www.geonames.org/export/);
- [Getty TGN Linked Open Data](https://www.getty.edu/research/tools/vocabularies/lod/index.html);
- [USGS GNIS](https://www.usgs.gov/us-board-on-geographic-names/download-gnis-data);
- [NGA GNS](https://geonames.nga.mil/geonames/GNSSearch/);
- [Pleiades](https://pleiades.stoa.org/) for ancient places;
- [World Historical Gazetteer](https://whgazetteer.org/) for temporal names and
  reconciliation.

Preserve local scripts, transliterations, historic and colonial/military
exonyms, parish/estate/river variants, obsolete spellings, feature type, date
range, authority ID, position, and uncertainty. Federated records are not
automatically legal or custodial authority.

## 2. Heritage and community authority screen

Find the competent national, regional, municipal, Indigenous, and community
heritage authorities. [UNESCO States Parties](https://whc.unesco.org/en/statesparties/)
helps identify jurisdiction, while
[ARIADNE](https://portal.ariadne-infrastructure.eu/) can discover provider
records. Neither replaces the competent local register.

For independent discovery or benchmarking, a custodian should retain exact
known-site locations and give the analyst only generalized exclusions/no-go
masks. Freeze and hash candidates before unblinding. Respect locations that an
authority or community intentionally generalizes; never reverse-engineer them.

## 3. Historic maps, aerials, and plans

Search by every alias plus historic jurisdiction, date interval, map series,
sheet, scale, creating agency, estate/parish, and nearby landmark:

- [OldMapsOnline](https://www.oldmapsonline.org/en/maps/about-oldmapsonline) for
  global discovery;
- national libraries and archives;
- [Library of Congress Maps](https://www.loc.gov/maps/);
- [USGS declassified satellite imagery](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-declassified-data-declassified-satellite-imagery-1);
- [NARA aerial photography](https://www.archives.gov/research/cartographic/aerial-photography);
- [UK National Archives overseas maps](https://www.nationalarchives.gov.uk/help-with-your-research/research-guides/maps-plans-of-lands-abroad/);
- [NCAP](https://www.ncap.org/).

An aggregator record does not license a scan. Record object-level rights,
creator, date, scale, sheet/series ID, scan ID, control points, georeferencing
method, RMSE, and known symbolic or surveying limitations.

Google Maps and Google Earth support bounded official-interface checks.
Do not use hidden endpoints or mass-download, bulk-capture, stitch, or
reconstruct their content. A permitted, attributed Earth capture may support a
small exploratory local check when its exact use basis is recorded. Never
analyze Street View. Use canonical licensed open, institutional, user-owned, or
separately licensed imagery for systematic or reproducible computation.

## 4. Modern map and linked-data context

Use [OpenStreetMap](https://www.openstreetmap.org/copyright), lawful Overpass
queries, or regional extracts to inspect modern roads, paths, drains, quarries,
buildings, cemeteries, utilities, land use, and other confounders. Archaeology
and heritage tags are volunteer leads, not authoritative labels. Do not upload
unpublished candidates.

Use [Wikidata data access](https://www.wikidata.org/wiki/Help:Data_access) and
Wikipedia to discover aliases, official IDs, bibliographies, and leads, then
follow their references. Do not count a linked-data copy and its source as
independent corroboration.

For restricted AOIs, download coarse regional OSM/Wikidata data and filter
locally instead of sending exact coordinates to public query endpoints.

## 5. Geology, soils, terrain, and hydrology

Use environmental data to model proxy visibility, preservation, formation,
transport, erosion, deposition, catchments, palaeochannels, and modern
confounders:

- national geological, soil, mapping, and hydrographic surveys;
- [OneGeology](https://onegeology.org/use/) as a survey-service router;
- [SoilGrids](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs.html);
- [Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM);
- [SRTM](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-shuttle-radar-topography-mission-srtm-1);
- [OpenTopography](https://opentopography.org/about);
- [HydroSHEDS](https://www.hydrosheds.org/);
- [JRC Global Surface Water](https://global-surface-water.appspot.com/download).

Record model resolution and uncertainty. Global DEMs can contain canopy and
buildings and miss subtle archaeology; SoilGrids is broad modeled context.
Product licences and attribution differ.

## 6. Cadasters, censuses, deeds, and administrative records

Search official statistics offices, land/cadastral authorities, municipal and
national archives by historic jurisdiction, parish/village, parcel or folio,
owner/occupier, occupation, creating agency, and date. These can reveal parcel
continuity, settlement growth, land use, field names, production, displacement,
and institutional change.

Historic deeds do not establish current title or access permission. Protect
living-person and fine-grained household data. Federations such as
[IPUMS International](https://international.ipums.org/international/) have
specific licence, redistribution, and re-identification restrictions.

## 7. Archives, newspapers, local histories, and military records

Archives are arranged by record creator and fonds, not only modern place name.
Search the agency, operation, estate, parish, former district, map series, and
date. Catalog descriptions may not mention maps or photographs inside a file.

Use national/local archives and libraries plus lawful discovery services such
as [Europeana](https://www.europeana.eu/),
[DPLA](https://dp.la/), and
[Library of Congress Chronicling America](https://www.loc.gov/collections/chronicling-america/).
Verify OCR against the page image. Separate eyewitness account, hearsay,
editorial interpretation, and later summary.

Military, diplomatic, colonial, engineering, and boundary records may contain
valuable aerials, route surveys, intelligence descriptions, and map indexes.
Preserve operational, colonial, and cartographic bias. Declassification does
not guarantee unrestricted rights.

## 8. Academic literature and repositories

Search all aliases and local-language equivalents with relevant period,
activity, material, geomorphology, palaeochannel, survey, excavation, and
remote-sensing terms. Follow citations backward and forward:

- [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/);
- [OpenAlex](https://developers.openalex.org/);
- [DataCite](https://support.datacite.org/docs/api);
- [OpenAIRE](https://explore.openaire.eu/);
- ARIADNE, [tDAR](https://core.tdar.org/), and
  [Open Context](https://opencontext.org/).

Index metadata does not license the article or dataset. Check the provider and
object-level access, ethics, attribution, and location controls.

## 9. Finds, museum, and collection records

For objects, assemblages, accessions, laboratory results, and custody history,
also use `$research-archaeological-history-and-finds`. Prefer a competent
official register, excavation archive, museum catalogue, or repository export
over a search snippet or aggregator.

The planner can boundedly ingest public JSON, JSONL, CSV, OAI-PMH, IIIF, and
RDF-XML records:

```bash
python3 scripts/search_plan.py ingest-source \
  --plan search-plan.json \
  --source-id <DECLARED_SOURCE_ID> \
  --input <PUBLIC_URL_OR_LOCAL_EXPORT> \
  --format <json|jsonl|csv|oai-pmh|iiif|rdf-xml> \
  --out normalized-records.json
```

The adapter records the exact query, retrieval time, access basis, licence,
raw-response hash, byte and record bounds, truncation, and normalization
version. It refuses authenticated or authority-controlled sources; those
remain explicit read-only agent actions after named authorization. Preserve
original terms and reconcile objects conservatively by strong identifiers.

For treasure, swords, precious metals, hoards, burials, or other vulnerable
portable material, public catalogue research and generalized distributions
are valid. Exact prospective work belongs to a restricted or
heritage-authority-only case with the complete recorded permission bundle.

## 10. Oral, community, and social sources

Community knowledge has its own authority and governance. Start with recognized
community bodies and co-design purpose, access, attribution, precision,
retention, withdrawal, and publication. Use the
[Oral History Association principles](https://oralhistory.org/principles-and-best-practices-revised-2018/),
[CARE Principles](https://www.gida-global.org/careprinciples), and
[Local Contexts labels](https://localcontexts.org/labels/traditional-knowledge-labels/)
as guidance; labels do not replace permission.

Public social content is not informed consent. Do not scrape private groups,
impersonate members, solicit precise find spots, quote identifiable people, or
geolocate posts. Use Facebook, other social platforms, or signed-in browser
sessions only after the user explicitly authorizes the named platform and
session for this case. Keep the first pass read-only. Messaging, posting, or
joining requires a separate explicit instruction.

## Reusable query recipes

Official register:

```text
site:<official-government-domain>
("<current name>" OR "<historic name>" OR "<local-script name>")
(archaeolog* OR <local term> OR monument* OR heritage)
(register OR inventory OR survey OR report)
```

Archive/catalog:

```text
("<alias 1>" OR "<alias 2>" OR "<former district>")
(cadastre OR estate OR tax OR survey OR canal OR road OR fort* OR burial OR mound)
<date range or creating agency>
```

Academic:

```text
("<all place aliases>" OR "<historic administrative unit>")
(archaeolog* OR excavation OR field survey OR ceramic*
 OR geomorph* OR palaeochannel OR geoarchaeolog*)
```

Add local-language terms and OCR variants. Record the exact query and search
date. “Not found” means only not found in these catalogs, languages, dates, and
access conditions.

## Leakage and disclosure checks

- Separate contextual priors from direct archaeological evidence.
- Do not tune and validate on the same published site set.
- Do not output coordinates more precise than the source or authority permits.
- Multiple coarse sources may intersect to re-identify a withheld location.
- Do not publish exact candidates in issue trackers, public maps, notebooks,
  repositories, or social posts.
- Stop and refer when research encounters human remains, sacred knowledge,
  threatened sites, access-controlled registers, unclear land access, or
  probable looting risk.
