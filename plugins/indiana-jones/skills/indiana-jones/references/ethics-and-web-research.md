# Ethics and Web Research

Use this reference for every public-web or authenticated-web investigation. The
goal is to identify and evaluate aerial-archaeology evidence without increasing
risk to people, communities, cultural knowledge, or archaeological places.

This workflow is research support, not fieldwork or legal advice. Follow the
laws, heritage rules, platform terms, institutional ethics requirements, and
community protocols of the relevant jurisdiction. Where rules conflict, use the
more protective handling and ask the user or an appropriate heritage authority.

## Non-negotiable boundaries

- Work read-only. Searching, opening, filtering, and recording minimal research
  notes are allowed only within the authorized scope.
- Never post, react, like, follow, join, friend, comment, message, submit a form,
  contact a source, or change an account or platform setting.
- Never bypass authentication, paywalls, invitation gates, robots controls,
  CAPTCHAs, rate limits, geographic restrictions, revoked links, or other access
  controls. Do not use leaked credentials, copied cookies, hidden APIs, or
  another person's account.
- Never request passwords, session tokens, recovery codes, or other credentials.
  Use only an existing session that the user explicitly authorizes.
- Do not facilitate trespass, unpermitted drone flights, unauthorized metal
  detecting, probing, digging, artifact collection, excavation, removal, or
  disturbance. Authorized professional planning remains confined to the
  documented method, area, validity period, responsible archaeologist, and
  restricted delivery channel; one permission never authorizes another
  activity.
  Do not provide routes, access points, landowner details, or field tactics that
  would make those acts easier.
- Treat cropmarks, soilmarks, shadowmarks, spectral anomalies, historical-map
  alignments, and geometric forms as observations or hypotheses, not confirmed
  archaeological sites.
- Do not publish precise locations covered by a specific legal, custodian,
  sacred/burial, community, confidentiality, or deliberate-redaction
  restriction. Novelty alone does not require suppressing a desk-research point.

## Authorization gate

Before using the web, establish and record:

1. the research question and geographic/topic scope;
2. the permitted source classes;
3. whether the work is public-web or authenticated-web research;
4. the intended output and who may receive it;
5. the stopping condition; and
6. any known community, heritage-authority, or data-use restrictions.

The user's request to search named public sources is sufficient authorization
for those sources. A general research request does not authorize authenticated
accounts, private groups, or a different platform.

Pause for new authorization whenever the work would cross a boundary: public to
authenticated, one platform to another, one account/session to another, or the
agreed topic/geography to a materially different scope.

### Public-web authorization

Public-web research may use pages that an ordinary unauthenticated visitor can
open. Search only within the agreed question. Respect site terms and technical
controls. Do not bulk-harvest, enumerate people, or reconstruct data that a
publisher has deliberately generalized or redacted.

### Authenticated-web authorization

Authenticated research requires explicit authorization naming:

- the platform;
- the existing account or browser session to use;
- the research purpose;
- the permitted pages, groups, searches, or date range; and
- confirmation that the work remains read-only.

Access granted by a login is not permission to republish. Preserve the original
audience and access context. Do not export member lists, reactions, comments, or
private-group material unless each item is necessary, within scope, and lawful
to retain. Prefer a paraphrased research note over a screenshot or full copy.

### Facebook and Chrome

Facebook and the user's Chrome session are optional authenticated sources, not
defaults. Use either only after the user explicitly authorizes that platform and
session for the current research scope.

For Facebook:

- view only the specifically authorized public pages, groups, posts, or searches;
- do not join groups, send requests, open chats, message anyone, or interact;
- do not use personal profiles to build dossiers or infer relationships;
- do not move restricted-group content into a public report; and
- stop if Facebook presents a consent, identity, security, or access challenge.

For Chrome:

- use only the authorized existing profile/session and relevant open tabs;
- do not inspect unrelated history, downloads, bookmarks, email, or accounts;
- do not save passwords, enable sync, install extensions, or change settings; and
- do not treat access in one tab as authorization for other signed-in services.

If the required session or platform is not explicitly authorized, continue with
public sources or ask for authorization. Never work around the missing access.

### Google Maps and Google Earth

Google Maps, Google Earth, satellite view, and Street View are optional manual
references. Opening an official interface does not grant permission to extract
its underlying imagery or data.

Use the companion `$research-google-earth` skill and
[google-earth-browser.md](google-earth-browser.md) for the current browser
workflow. Public exploration is read-only. A signed-in Earth session, project
or annotation edits, imports, exports, sharing, and access requests each
require case-specific authorization.

- Use the official interface for a bounded, user-directed visual check,
  visible-metadata read, deep link, or specifically requested permitted
  capture.
- Do not inspect hidden endpoints or mass-download, bulk-capture, cache, stitch,
  or reconstruct map, satellite, Earth, or Street View content.
- Do not assemble a digitized archaeological dataset, feature corpus, training
  set, or model-evaluation set from Earth captures unless a licence covers the
  exact use.
- Local analysis is allowed for canonical open, user-owned, or separately
  licensed source data. A small attributed Earth capture may support a bounded
  exploratory check when current Earth terms and Geo guidelines permit the
  capture and intended use.
- Keep all visible Google and third-party attribution intact.
- Do not export, copy, or reconstruct raw Earth catalog-layer data.
- Prefer a text observation and exact deep link. Retain only a small number of
  permitted, user-requested static Earth captures with attribution legible and
  adjacent; never screenshot Street View.
- Preserve the original capture separately, record its hash and use basis, and
  label any capture-derived computation as exploratory and non-reproducible.
- Use openly licensed or user-licensed Earth-observation products for
  systematic or reproducible pixel analysis.

The governing contract depends on the product: Maps Platform API content,
Earth end-user content, catalog layers, imported data, generated outputs, and
Street View do not share one blanket rule. Recheck the current
[Earth Additional Terms](https://www.google.com/help/terms_maps-earth/),
[Google Geo guidelines](https://about.google/brand-resource-center/products-and-services/geo-guidelines/),
and any product-specific terms for the exact source, jurisdiction, account, and
intended output.

## Privacy and data minimization

Collect the least information needed to evaluate the archaeological claim.

- Avoid names, faces, usernames, home or email addresses, telephone numbers,
  vehicle plates, parcel ownership, daily routines, and relationship networks.
- Do not combine otherwise public fragments to expose a person's identity,
  private activity, community knowledge, or a protected site's location.
- Crop or redact screenshots. Remove notifications, account identifiers, faces,
  unrelated comments, coordinates, and other incidental personal information.
- Strip EXIF and other embedded location metadata from derived images before
  sharing them.
- Keep authenticated-source notes separate from public-source notes and label
  their access restrictions.
- Do not retain raw authenticated content when a minimal claim note and source
  reference are sufficient.
- Honor deletion, embargo, attribution, and audience restrictions supplied by
  the source, community, archive, or heritage authority.

The Archaeology Data Service notes that archaeological archives can contain
personal, confidential, and sensitive information, and that a site or findspot
location can itself be sensitive when disclosure may endanger it. Use
anonymization, informed consent, restricted access, or embargoes as appropriate:
[ADS, Sensitive data](https://archaeologydataservice.ac.uk/help-guidance/how-to-prepare-data/sensitive-data/).

## Source and claim provenance

Maintain a source register. For each source, record only:

```yaml
source_id: src-001
title: Human-readable title
publisher_or_custodian: Organization or account
url_or_archive_id: Stable locator
accessed_at: ISO-8601 timestamp
access_class: public | authenticated | restricted
source_type: primary | secondary | community-knowledge | imagery | map
license_or_terms: Known reuse limits
location_sensitivity: public | generalized | protected | unknown
retention_note: What was retained and why
```

Maintain a separate claim register:

```yaml
claim_id: clm-001
claim: Concise statement
status: observed | reported | inferred | hypothesis | contradicted
source_ids: [src-001]
evidence_region: Image tile, frame, map sheet, or text section
confidence: low | medium | high
alternatives: [Modern drainage, geology, agricultural pattern]
reviewed_at: ISO-8601 timestamp
sensitivity: public | restricted | authority-only
```

Rules:

- Never promote an inference or third-party report to an observation.
- Preserve disagreement and plausible non-archaeological explanations.
- Prefer stable institutional records, original imagery metadata, survey
  reports, and heritage inventories over reposts or unsourced captions.
- Record the imagery date, provider, resolution or scale, processing applied,
  and whether the image is current, historical, composite, or AI-generated.
- Mark inaccessible, deleted, or unverifiable sources; do not silently replace
  them with a search-result snippet.
- Keep quotations short and necessary. Use paraphrase when wording is not
  evidentially important.
- Record every redaction or generalization with the authority that required it
  so a reviewer can understand why the output differs from the source evidence.

## Archaeological coordinate and protection handling

Exact coordinates are ordinary research evidence unless a specific protection
applies. For example, the U.S. National Park Service summarizes ARPA's
prohibition on public disclosure of sensitive information about archaeological
resources on certain U.S. public and Indian lands. Other jurisdictions differ:
[NPS, Archaeological Resources Protection Act](https://www.nps.gov/subjects/archeology/archaeological-resources-protection-act.htm).

For ordinary lawful desk research, preserve exact candidate points,
AOIs, footprints, rankings, image points, image footprints, and imagery links
with source precision and uncertainty.
Apply the following controls only to a genuinely protected/confidential point:

- Preserve any official sensitivity or disclosure classification.
- Do not calculate, expose, or confirm exact coordinates when the governing
  restriction forbids it; novelty alone is not such a restriction.
- In the protected public derivative, use the least precision that supports the
  research purpose and cannot be trivially reversed.
- Remove coordinates, pins, tile identifiers, cadastral references, access
  routes, distinctive nearby landmarks, camera metadata, and reversible map
  overlays from public artifacts.
- Keep any essential precise location in an access-controlled,
  authority-directed record. Do not place it in chat logs, filenames, commits,
  issue trackers, screenshots, or public repositories.
- Do not infer a redacted location by cross-referencing terrain, property
  records, social posts, or image metadata.
- Do not downgrade protection because a location is rumored, previously leaked,
  or technically discoverable.

NPS archaeological documentation guidance recommends separating confidential
locational or religious information from a public report when disclosure risks
vandalism:
[NPS, Archeological Documentation Guidelines](https://www.nps.gov/articles/sec-standards-archeo-doc-guidelines.htm).

## Community and heritage authority

Archaeological information can concern living communities, Indigenous Peoples,
descendant groups, sacred places, burials, and knowledge governed by community
protocol rather than public availability.

Apply the CARE Principles for Indigenous Data Governance:

- **Collective Benefit:** define how the work benefits, or at minimum does not
  burden, the people connected to the data.
- **Authority to Control:** recognize the right of Indigenous Peoples and
  communities to govern access, interpretation, use, and disclosure.
- **Responsibility:** support respectful relationships, attribution, capacity,
  and accountable stewardship.
- **Ethics:** assess present and future harms before collection, analysis, or
  sharing.

CARE complements technical open-data practices; it is not permission to make
Indigenous data open. Local community standards and governance take priority:
[Global Indigenous Data Alliance, CARE Principles](https://www.gida-global.org/careprinciples).

Before interpreting, operationalizing, or publishing sensitive community-linked
evidence:

1. identify the appropriate Indigenous, descendant, local-community, religious,
   land-management, and heritage authorities;
2. check for community research codes, data-governance rules, cultural
   protocols, embargoes, and preferred terminology;
3. ask the user to obtain appropriate consultation or consent through official
   channels;
4. record who has authority to decide access and disclosure, not personal
   details about community members; and
5. follow the resulting limits on analysis, storage, attribution, and release.

Do not treat absence of an online objection as consent. Do not ask community
members to reveal restricted knowledge. The Society for American Archaeology's
ethics principles emphasize stewardship, responsibility, preservation,
reporting, and compliance with governing laws:
[SAA, Principles of Archaeological Ethics](https://www.saa.org/Member/SAAMember/Career-and-Practice/Principles-of-Archaeological-Ethics.aspx).

## Protected or urgent new-site escalation

When research suggests a previously unrecorded site that is also covered by a
specific protection, confidentiality, burial/sacred, community, or active-
threat concern:

1. Stop public triangulation and do not solicit crowdsourced identification.
2. Preserve minimal, non-destructive evidence: source identifiers, imagery
   dates, a restricted feature outline, alternative explanations, confidence,
   and the general jurisdiction.
3. Run a false-positive review. Consider geology, vegetation, drainage,
   agricultural machinery, utilities, roads, image stitching, compression, and
   modern structures.
4. Identify the responsible official channel: national or regional heritage
   agency, local Historic Environment Record, State or Tribal Historic
   Preservation Office, Indigenous or descendant-community heritage authority,
   public-land manager, or qualified professional archaeologist.
5. Prepare a restricted report or draft for the user. Do not submit it, message
   anyone, or publish it from this workflow.
6. Give precise location evidence only to the appropriate authority through its
   approved secure channel and only when the user has chosen to do so.
7. Await authority and community guidance before broader disclosure, field
   verification, drone work, sampling, or publication.

If there is an immediate threat from construction, looting, fire, erosion, or
other damage, identify the official urgent-reporting route and advise the user
to contact the responsible authority. Do not confront suspected looters, enter
land, or organize an informal recovery.

## Completion checklist

Before returning research:

- authorization scope and access class are recorded;
- all browsing remained read-only and no messages or interactions occurred;
- every material claim links to provenance and states its evidential status;
- personal and authenticated-source data are minimized;
- specifically protected/confidential locations are handled according to their
  named restriction and metadata-clean;
- alternative explanations and uncertainty are visible;
- community and heritage-authority interests are identified;
- no field access, collection, excavation, or circumvention is encouraged; and
- any escalation package is restricted, unsent, and directed to an appropriate
  authority rather than the public.
