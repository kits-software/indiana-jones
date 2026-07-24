<p align="center">
  <img
    src="assets/indiana-jones-hero-transparent.png"
    alt="A small explorer in a brown fedora carrying a map and field bag"
    width="260"
  />
</p>

<h1 align="center">Indiana Jones</h1>

<p align="center">
  <strong>Read a landscape like a historical record.</strong>
</p>

<p align="center">
  Ask about a lost castle, an earlier settlement, an unusual mark, or how people
  once lived. Indiana Jones follows the evidence until the story becomes
  testable.
</p>

<p align="center">
  <a href="#add-to-codex">
    <img
      src="https://img.shields.io/badge/Add_to_Codex-C77932?style=for-the-badge&logo=openai&logoColor=white"
      alt="Add to Codex"
    />
  </a>
  &nbsp;
  <a href="#try-a-question"><strong>See what it can discover →</strong></a>
</p>

<p align="center">
  <sub>
    Created, authored, and published by <strong>Paweł Klimkowski</strong>
    · Experimental release 0.1.0
  </sub>
</p>

---

Indiana Jones is a place-led archaeological research plugin for Codex. Give it
a place, photograph, local story, object, or historical question. It chooses
the useful research methods behind the scenes, searches public or authorized
evidence, tests competing explanations, and returns the clearest discovery the
evidence can support.

You do not need to know which archive, map, sensor, catalogue, model, or
specialist method to request. Start with the mystery.

## Add to Codex

Register this repository as a plugin marketplace, then install Indiana Jones:

```bash
codex plugin marketplace add kits-software/indiana-jones --ref main
codex plugin add indiana-jones@indiana-jones-lab
```

Start a new Codex task after installation so the bundled skills are loaded.
In the desktop app, open **Plugins**, choose **Indiana Jones Lab**, and select
**Indiana Jones**.

> [!NOTE]
> GitHub does not preserve `codex://` install links. The button above leads here
> so the public install path stays visible, auditable, and reliable.

For local development:

```bash
git clone https://github.com/kits-software/indiana-jones.git
cd indiana-jones
codex plugin marketplace add .
codex plugin add indiana-jones@indiana-jones-lab
```

## What it does

| Discover | Challenge | Reconstruct |
| --- | --- | --- |
| Finds overlooked records, landscape relationships, candidate areas, and plausible traces of earlier activity. | Makes archaeological, natural, modern, and processing explanations compete against the same evidence. | Builds source-led histories and illustrations while labeling what is documented, inferred, comparative, or invented. |

Every useful answer aims to include:

- what was directly observed or documented;
- the most plausible interpretation and its strongest alternatives;
- the provenance, limits, and sensitivity of the evidence;
- what remains unknown; and
- the next lawful, non-invasive check most likely to change the conclusion.

## Try a question

| Find a lost place | Reconstruct daily life |
| --- | --- |
| “An old castle is said to have stood somewhere around this valley. Where could it plausibly have been, and what would prove or disprove each possibility?” | “How did people live, build, farm, and travel around this village between 1200 and 1500?” |

| Explain a landscape mark | Rebuild a historical scene |
| --- | --- |
| “This ring-shaped mark appears in a field. What are the archaeological, natural, and modern explanations—and which best fits the evidence?” | “Show how this harbour city and the people working on its quays could have looked around 120 CE. Label what is known, inferred, or illustrative.” |

You can also begin with a photograph, an object, a disputed local story, a
route, a building, a city, or a broad question about what may once have existed.

## What comes back

| Your question | Indiana Jones tries to return |
| --- | --- |
| Could an older castle or settlement be hidden here? | Plausible zones, competing site models, supporting and contradicting evidence, and discriminating next checks |
| How did people live in this area? | A time-sliced account of water, routes, fields, resources, buildings, work, belief, conflict, and daily life |
| Why is this town shaped this way? | A reconstruction of streets, plots, boundaries, institutions, lost features, and phases of growth |
| Can you show me how it looked? | An evidence-led illustration with source-linked visual choices, anachronism checks, alternatives, and a clear uncertainty caption |
| Does this unusual mark mean anything? | Direct observations, archaeological interpretations, natural and modern alternatives, and a ranked judgment |
| Is the local story true? | Name variants, documentary chains, landscape fit, contradictions, missing evidence, and a bounded conclusion |
| Where should we look next? | An ordered research frontier favoring informative, lawful, non-invasive checks |

## Why this project exists

The history of a place rarely survives in one neat record. It is scattered
across street and field shapes, old names, maps, excavation reports, museum
catalogues, aerial photographs, terrain, geology, community memory, and the
gaps between them.

Professional archaeology brings those forms of evidence together. Indiana
Jones turns that multidisciplinary practice into an accessible research
companion whose public experience begins with a human question, not a list of
tools.

The goal is not a dramatic answer from one striking image. The goal is a useful
account of what may have happened, a ranked set of explanations, and a clear
path toward better evidence.

## How an investigation works

1. **Frame the mystery.** Resolve the place, time range, story, and what a
   useful answer would change.
2. **Reconstruct the landscape.** Ask how terrain, water, routes, resources,
   authority, and later disturbance shaped what could have existed.
3. **Search across evidence.** Combine suitable public or authorized records,
   maps, imagery, terrain, publications, catalogues, and local knowledge.
4. **Make explanations compete.** Test archaeological ideas against geology,
   agriculture, drainage, infrastructure, image artefacts, folklore, and
   inherited assumptions.
5. **Return a discovery packet.** Separate observations, derived results,
   interpretations, alternatives, corroboration, uncertainty, and next steps.
6. **Keep going responsibly.** If one route is blocked, pursue another lawful
   source or reduce location precision instead of abandoning the question.

## Discovery first. Evidence always.

Indiana Jones is expected to find things: overlooked records, relationships
between landscape and history, plausible locations, repeated patterns, and
candidate features worth further study. It should not retreat into a tool list
or stop merely because one source is unavailable.

> [!IMPORTANT]
> An attractive pattern is a hypothesis, not a discovery claim. Generated
> reconstruction art is a derived interpretation, never documentary evidence
> or independent corroboration.

When exact work would be unsafe, unlawful, or harmful, the investigation
continues at a responsible scale. It can still search public records,
reconstruct the historical landscape, compare hypotheses, identify the missing
permission, and prepare a useful handoff.

### Hard boundaries

- No permission is inferred for access, detecting, collection, flying,
  probing, or excavation.
- Precise locations of possible new, sacred, burial-related, vulnerable, or
  non-public sites are protected.
- Sources are attributed, and their licences determine how they may be
  analyzed or reproduced.
- Local and descendant communities are research partners and knowledge
  holders, not obstacles to route around.
- Looting, trespass, covert investigation, and evasion of heritage law are
  never part of the workflow.

## What is real today

This is an experimental `0.1.0` release. Its strongest capability today is
structured, source-backed research: turning an ordinary question into a
multidisciplinary investigation, preserving uncertainty, and producing a
clear next step.

The repository includes transparent Python baselines for terrain and
multi-date optical analysis. They are deliberately not marketed as magical
“lost city detectors.”

- In a known-site Whitley Castle terrain development test, the target ranked
  8th with 16.125 m error.
- A frozen Sentinel-2 optical test missed its 160 m criterion, with the nearest
  anomaly 191.150 m away.

Both results remain public because an honest miss teaches more than a hidden
one.

<details>
<summary><strong>Under the hood</strong></summary>

The provider-neutral package includes place resolution, historical time
slices, adaptive search areas, evidence and task graphs, provenance ledgers,
source-sensitive disclosure, terrain and multi-date optical baselines,
browser-backed map rendering, evidence-led illustration, object and custody
research, Google Earth reconnaissance, and public-report validation.

See the [technical plugin README](plugins/indiana-jones/README.md) for runtime
requirements, tests, proof-of-concept details, and the implementation map.

</details>

<details>
<summary><strong>Research foundations</strong></summary>

- [Historic England: Archaeological Landscapes](https://historicengland.org.uk/research/current/discover-and-understand/landscapes/)
- [CIfA: Standard and guidance for archaeological desk-based assessment](https://www.archaeologists.net/sites/default/files/CIfAS%26GDBA_4.pdf)
- [Historic England: Aerial Investigation and Mapping](https://historicengland.org.uk/research/methods/airborne-remote-sensing/aerial-investigation/)
- [Historic England: Using Airborne Lidar in Archaeological Survey](https://historicengland.org.uk/research/methods/airborne-remote-sensing/lidar/)
- [Historic England: Formation of Cropmarks](https://historicengland.org.uk/research/methods/airborne-remote-sensing/formation-of-cropmarks/)
- [UNESCO: Recommendation on the Historic Urban Landscape](https://whc.unesco.org/en/hul/)
- [The London Charter for computer-based cultural heritage visualization](https://londoncharter.org/principles.html)
- [The Seville Principles for virtual archaeology](https://www.vi-mm.eu/wp-content/uploads/2016/10/The-Seville-Principles.pdf)
- [ICOMOS Charter for Interpretation and Presentation](https://www.icomos.org/images/DOCUMENTS/Charters/interpretation_e_1.pdf)
- [ANSI/ASB Best Practice Recommendation 089 for facial approximation](https://www.aafs.org/sites/default/files/media/documents/BPR_089_e1.pdf)
- [Archaeology Data Service: Sensitive Data](https://archaeologydataservice.ac.uk/help-guidance/how-to-prepare-data/sensitive-data/)
- [UNESCO: International principles applicable to archaeological excavations](https://www.unesco.org/en/legal-affairs/recommendation-international-principles-applicable-archaeological-excavations)

</details>

## Citation

If Indiana Jones contributes to your research, publication, teaching, software,
or methodology, please cite **Paweł Klimkowski** as the author and publisher.
GitHub provides a ready-to-copy citation through **Cite this repository**,
backed by [`CITATION.cff`](CITATION.cff).

> Klimkowski, Paweł. (2026). *Indiana Jones: Evidence-Led Archaeological
> Discovery for Codex* (Version 0.1.0) [Computer software]. Paweł Klimkowski.
> https://github.com/kits-software/indiana-jones

<details>
<summary>Copy BibTeX</summary>

```bibtex
@software{klimkowski2026indianajones,
  author = {Paweł Klimkowski},
  title = {Indiana Jones: Evidence-Led Archaeological Discovery for Codex},
  year = {2026},
  publisher = {Paweł Klimkowski},
  version = {0.1.0},
  url = {https://github.com/kits-software/indiana-jones}
}
```

</details>

## Project links

- [`plugins/indiana-jones`](plugins/indiana-jones) — installable Codex plugin
- [`plugins/indiana-jones/skills`](plugins/indiana-jones/skills) — discovery,
  planning, research, reconstruction, and reporting workflows
- [`plugins/indiana-jones/rfcs`](plugins/indiana-jones/rfcs) — research and
  architecture decisions
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution and validation guide
- [`SECURITY.md`](SECURITY.md) — software and sensitive-location reporting
- [`CITATION.cff`](CITATION.cff) — machine-readable citation metadata

Contributions are welcome from archaeologists, historians, geospatial
researchers, museum and archive professionals, heritage practitioners,
local-history groups, and engineers who care about reproducible evidence.

If a report may reveal a vulnerable location, do not post coordinates, access
routes, imagery crops, or reversible locators in a public issue. Follow
[`SECURITY.md`](SECURITY.md) instead.

---

Indiana Jones is an independent, unofficial project. It is not affiliated with
or endorsed by Lucasfilm Ltd., Disney, or their affiliates.
