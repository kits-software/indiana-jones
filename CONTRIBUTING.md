# Contributing to Indiana Jones

Indiana Jones welcomes improvements to archaeological reasoning, source
routing, reproducibility, reporting, safety, and the experience of asking
ordinary questions about a place.

## Before you begin

- Open an issue before a broad workflow or architecture change.
- Do not include precise coordinates, reversible location clues, access routes,
  or high-resolution evidence for a possible new, vulnerable, sacred,
  burial-related, or non-public site.
- Use only source material that may lawfully be stored and redistributed in
  this public repository.
- Keep observations, transformations, interpretations, alternatives, and
  corroboration separate.
- Preserve negative results. A method that misses is still evidence about the
  method.

## Design principles

Public-facing language starts with the user’s mystery, not the machinery. A
person should be able to ask:

> “What might have stood here, and how could we find out?”

The plugin may choose archives, maps, imagery, terrain, catalogues, community
knowledge, or another appropriate source behind the scenes.

Every workflow should:

1. pursue a useful discovery outcome;
2. state the direct evidence and its provenance;
3. test plausible modern and natural alternatives;
4. protect sensitive locations and respect permissions;
5. continue at a generalized, non-operational scale when exact work is gated;
6. name the evidence that would change the conclusion.

## Repository structure

- `plugins/indiana-jones/.codex-plugin/plugin.json` contains plugin metadata.
- `plugins/indiana-jones/skills/*/SKILL.md` contains agent workflows.
- `plugins/indiana-jones/skills/*/agents/openai.yaml` contains human-facing
  skill metadata.
- `plugins/indiana-jones/skills/*/references` contains detailed methods and
  contracts loaded only when relevant.
- `plugins/indiana-jones/skills/*/scripts` contains reproducible utilities and
  tests.
- `plugins/indiana-jones/rfcs` contains larger research and architecture
  decisions.

Keep individual files below 700 lines when practical. Put detailed,
occasionally needed material in a directly linked reference instead of making
the main skill harder to load.

## Validate a change

From the repository root, validate the plugin and each skill:

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py \
  plugins/indiana-jones

for skill in plugins/indiana-jones/skills/*; do
  python3 /path/to/skill-creator/scripts/quick_validate.py "$skill"
done
```

Run the Python suites:

```bash
python3 -m unittest discover \
  -s plugins/indiana-jones/skills/indiana-jones/scripts/tests \
  -v
python3 -m unittest discover \
  -s plugins/indiana-jones/skills/plan-archaeological-search/scripts/tests \
  -v
python3 -m unittest discover \
  -s plugins/indiana-jones/skills/report-archaeological-evidence/scripts/tests \
  -v
python3 -m unittest discover \
  -s plugins/indiana-jones/skills/illustrate-historical-reconstruction/scripts/tests \
  -v
```

The optional renderer has its own test suite:

```bash
cd plugins/indiana-jones/skills/indiana-jones/scripts/map_renderer
npm install
npm test
```

When changing user-facing skill descriptions, forward-test ordinary prompts
that do not name specialist tools. Confirm that the right skill triggers and
that the answer seeks a discovery rather than returning only a research plan.

## Pull requests

Explain:

- the human question the change improves;
- why the previous behavior was insufficient;
- which evidence or authority boundaries are affected;
- the tests and realistic prompts used;
- any remaining uncertainty, unavailable source, or environment block.

Use lowercase semantic commit messages:

```text
feat: pursue place-led discovery questions
fix: preserve alternatives in candidate reports
docs: explain sensitive-location reporting
```

Do not mix unrelated cleanup into the same pull request.
