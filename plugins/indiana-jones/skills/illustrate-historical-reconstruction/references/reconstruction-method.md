# Evidence-led reconstruction method

## Contents

1. Methodological foundation
2. Reconstruction status
3. Source and decision model
4. Generative-image controls
5. Review and communication
6. Research foundations

## Methodological foundation

A historical illustration is a visual argument assembled from evidence,
analogy, and authored choices. Its realism is not a measure of truth. Preserve
the chain:

```text
research question
  -> time/place/subject contract
  -> source record
  -> visual decision
  -> prompt clause
  -> generated pixels
  -> inspection finding
  -> captioned interpretation
```

This operationalizes the London Charter's requirements to select an
appropriate visualization method, identify and evaluate research sources, and
document enough of the process for the result to be understood and evaluated.
The Seville Principles add archaeological authenticity, historical rigour,
alternative interpretations, metadata, and paradata.

Use the image to answer a stated purpose. A street-level teaching scene, a
forensic facial approximation, an architectural massing study, and a cinematic
book illustration have different tolerances and should not inherit one
another's claims.

## Reconstruction status

Assign one status to every consequential visual decision:

| Status | Meaning | Typical treatment |
| --- | --- | --- |
| `documented` | Direct evidence closely constrains the depicted feature at the stated time and place. | Lock it in the prompt and reject contradictory outputs. |
| `strongly-constrained` | Several independent sources or a close physical model narrow the choice substantially. | Lock the range and disclose residual uncertainty. |
| `plausible` | The choice fits the evidence but comparable alternatives remain. | Select with reasons; generate a variant if visual impact is high. |
| `illustrative` | The detail is needed for a complete scene but evidence does not constrain it closely. | Keep it ordinary, non-focal, and explicitly authored. |
| `contested` | Sources or specialists support materially different readings. | Show matched alternatives or defer depiction. |

Do not turn these into numeric probabilities unless a calibrated model and
representative evidence base exist. Confidence in a wall line does not transfer
to its paint, roof, occupation, inhabitants, or date.

## Source and decision model

### Source authority

Classify each source:

- `primary-direct`: contemporary or physical evidence that directly measures
  the depicted subject, such as a survey, excavated object, photograph,
  portrait, plan, textile, inscription, environmental sample, or scientific
  analysis;
- `primary-indirect`: contemporary evidence that constrains the wider context
  or a related feature, such as a written description, inventory, map,
  iconographic convention, oral testimony, or regional assemblage;
- `secondary`: a later scholarly analysis or published reconstruction;
- `analogy`: a comparison whose temporal, geographic, functional, and social
  distance must be stated;
- `living-tradition`: community-held knowledge or continuing practice used
  with appropriate consent, authority, and attribution.

Record origin families. A museum page, press release, and article repeating
the same excavation report count as one lineage.

### Visual decision record

For each visible element record:

- what the viewer will see;
- status and impact;
- source IDs and rationale;
- rejected or viable alternatives;
- `alternative-variants`, `single-main-with-disclosure`, or
  `defer-depiction` for high-impact uncertainty;
- the exact prompt clause;
- the check that can detect model drift.

High-impact decisions include identity, face, skin or hair depiction, body
form, monument silhouette, street plan, major dimensions, religious
iconography, construction system, political symbols, environmental setting,
and the scene's dominant social story.

### Time and state

Use the narrowest defensible time slice. Record whether the subject is:

- being made or built;
- in ordinary use;
- newly finished;
- repaired, altered, or repurposed;
- damaged, declining, abandoned, buried, excavated, conserved, or restored.

Do not present only an imagined "golden age." Repairs, decay, reused materials,
partial completion, labour, and ordinary maintenance may be historically
essential.

## Generative-image controls

Generative models optimize visual plausibility, not archaeological validity.
Recent evaluation of AI-generated archaeological scenes found weak
correspondence with the scholarly literature, including dated knowledge and
cultural anachronisms. Treat model output as an untrusted rendering of the
brief.

Compile prompts in evidence order:

1. structural anchors;
2. culturally and materially specific descriptors;
3. environmental and social context;
4. aesthetic controls;
5. negative constraints.

This is compatible with the 2026 Heritage-Aligned Reconstruction Framework,
which separates structural dimensions, cultural descriptors, and technical
controls, then evaluates the generated output with expert review. Use that
study as an emerging operational model, not as a universal validation
standard.

Include exact scale relationships when known. Use regional terms for masonry,
timber framing, textiles, ceramics, tools, hairstyles, and iconography rather
than generic "ancient" or "medieval" language. Add negative constraints for
features likely to be supplied by model priors.

Do not use photorealism as the default measure of quality. Depending on the
evidence, a painterly reconstruction, cutaway, diagrammatic massing study, or
matched alternatives may communicate the interpretation more honestly.

## Review and communication

Review the output in separate passes:

1. **Geometry**: scale, silhouette, plan, spacing, pose, perspective, and
   construction feasibility.
2. **Material culture**: clothing, tools, surfaces, joinery, wear, repair,
   pigments, and manufacturing traces.
3. **Environment**: topography, hydrology, plants, animals, season, light, and
   weather.
4. **Social context**: activity, labour, age and body diversity, status,
   crowding, accessibility, and whose presence or absence the image implies.
5. **Anachronism and bias**: modern technologies, fantasy conventions,
   national or racial stereotypes, colonial framing, and blended periods.
6. **Communication**: whether the caption makes the evidential status visible
   without requiring the viewer to infer it from style.

When the image represents a living or descendant community's heritage,
community knowledge is not decorative consultation. Record disagreements,
rights, restrictions, and requested modes of depiction. ICOMOS interpretation
principles call for multidisciplinary evidence, comparison of alternative
reconstructions, respect for living traditions, and meaningful participation
by associated communities.

## Research foundations

Consulted 2026-07-24:

- [London Charter principles](https://londoncharter.org/principles.html) —
  appropriate aims and methods, structured source evaluation, documentation,
  sustainability, and access.
- [Seville Principles](https://www.vi-mm.eu/wp-content/uploads/2016/10/The-Seville-Principles.pdf)
  — interdisciplinarity, purpose, authenticity, historical rigour, scientific
  transparency, metadata, paradata, and expert evaluation.
- [ICOMOS Charter for the Interpretation and Presentation of Cultural Heritage Sites](https://www.icomos.org/images/DOCUMENTS/Charters/interpretation_e_1.pdf)
  — systematic environmental, archaeological, architectural, historical,
  written, oral, iconographic, and photographic analysis; alternative
  reconstructions; context; inclusiveness; and community rights.
- [Limoncelli, Principles and Methods for the Virtual Archaeological Reconstruction of an Ancient Monument](https://iris.unipa.it/handle/10447/629193)
  — direct primary, indirect primary, and secondary source distinctions across
  acquisition, processing, and presentation.
- [Apollonio and Giovannini, paradata and uncertainty in digital reconstruction](https://cris.unibo.it/handle/11585/537582)
  — linking reconstruction hypotheses to documented sources and subjective
  decisions.
- [Artificial Intelligence and the Interpretation of the Past](https://www.cambridge.org/core/journals/advances-in-archaeological-practice/article/artificial-intelligence-and-the-interpretation-of-the-past/8FE3F2CB6BBFAD49F75FFC3031158A5A)
  — empirical evidence of dated knowledge, cultural anachronism, and weak
  alignment between AI outputs and archaeological literature.
- [HARF: a human-AI collaborative framework for cultural heritage reconstruction](https://www.sciencedirect.com/science/article/pii/S2212054826000615)
  — an emerging structured-prompt and expert-review workflow for generative
  heritage imagery.
- [Facial reconstruction: anatomical art or artistic anatomy?](https://pmc.ncbi.nlm.nih.gov/articles/PMC2815945/)
  — anatomical constraints and the limits of inferring soft tissue, hair,
  pigmentation, expression, and other appearance details.
- [ANSI/ASB Best Practice Recommendation 089: Facial Approximation in Forensic Anthropology](https://www.aafs.org/sites/default/files/media/documents/BPR_089_e1.pdf)
  — specialist collaboration, tested methods, limitations, pre-release review,
  and the requirement not to present an approximation as an exact likeness or
  identification evidence.
- [UNESCO Recommendation on the Ethics of Artificial Intelligence](https://www.unesco.org/en/legal-affairs/recommendation-ethics-artificial-intelligence)
  — traceability, bias, cultural diversity, inclusion, human oversight, and
  participatory governance for AI-mediated cultural work.
- [UNESCO Ethical Principles for Safeguarding Intangible Cultural Heritage](https://ich.unesco.org/en/ethics-and-ich-00866)
  — community authority, consent, customary access, and protection from
  misrepresentation or decontextualization.
