# What img2threejs teaches this plugin

## Identity

The project the user named is
[`hoainho/img2threejs`](https://github.com/hoainho/img2threejs), spelled without
the word “image” in the repository name. It is an agent-agnostic skill that can
run under Codex, Claude Code, or OpenCode. It is not, by itself, a current Codex
plugin bundle because its repository does not contain the required
`.codex-plugin/plugin.json` manifest.

[`Three.js Object Sculptor`](https://github.com/vinhhien112/Three.js-Object-Sculptor-Codex-Plugin)
is a useful manifested Codex-plugin analogue. It wraps a related workflow in a
plugin layout with `.codex-plugin/`, `skills/`, scripts, and tests.

Current Codex plugin examples use a required manifest plus optional skills,
apps, MCP configuration, agents, commands, hooks, and assets:
[`openai/plugins`](https://github.com/openai/plugins).

## How img2threejs is built

The repository separates judgment from mechanical work:

- `SKILL.md` is the short orchestration and routing layer.
- `grimoire/` holds detailed rubrics loaded only for the current stage.
- `forge/` contains deterministic Python for probing, spec construction,
  validation, build-state gates, generation, and comparison packaging.
- A structured `ObjectSculptSpec` is written before code generation.
- Build passes are locked in order rather than regenerating the whole object.
- Each pass requires a real browser render and a side-by-side evidence sheet.
- The agent makes the visual judgment; scripts enforce schemas and state.
- Rejection or a request for more source views is an expected valid result.

Its core loop is:

```text
reference
  -> suitability and complexity assessment
  -> structured spec
  -> deterministic validation
  -> one locked build pass
  -> browser render
  -> packaged comparison
  -> evidence-bound review
  -> refine, request input, stop, or continue
```

This is token-efficient because code performs repeatable bookkeeping and the
agent spends context on interpretation.

## Translation to Indiana Jones

The architecture transfers well, but archaeological claims need a stronger
authority boundary:

| img2threejs | Indiana Jones |
| --- | --- |
| Reference image | Sensor raster, archive, map, or authorized source |
| Suitability gate | Sensor/proxy/resolution/licence fitness gate |
| ObjectSculptSpec | Case ledger and source manifest |
| Deterministic forge scripts | Hashing, raster registration, feature extraction, ranking, scoring |
| Render evidence sheet | Raw/derived/candidate diagnostics with hashes |
| Visual pass decision | Observed/derived/inferred/corroborated evidence review |
| Hidden-side uncertainty | Resolution, vegetation, date, georeferencing, and equifinality uncertainty |
| Valid stop | Reject anomaly, request another modality, or escalate to an expert |

Indiana Jones adds controls that the 3D task does not need:

- candidate generation and ground-truth scoring are separate processes;
- exact known-site labels stay withheld during a rediscovery run;
- modern map context and heritage records cannot silently become model inputs;
- possible new-site coordinates are restricted;
- Google, social, and authenticated sources have explicit access and reuse
  gates;
- an agent cannot “approve” a site as archaeological from pixels alone;
- field access, drone work, collection, and excavation are outside implied
  authorization.

## What was copied conceptually

- thin skill instructions with progressive disclosure;
- deterministic scripts for repeatable operations;
- structured manifests before interpretation;
- stage gates that fail closed;
- evidence artifacts rather than prose-only confidence;
- honest rejection and missing-input outcomes.

## What was not copied

- no Three.js code generation;
- no claim that visual similarity is equivalent to archaeological validity;
- no monolithic universal model;
- no use of a commercial map viewer as a downloadable imagery provider;
- no confidence percentage without representative calibration.

The resulting plugin is deliberately a research-and-evidence system with one
transparent terrain baseline, not an autonomous archaeological-site finder.
