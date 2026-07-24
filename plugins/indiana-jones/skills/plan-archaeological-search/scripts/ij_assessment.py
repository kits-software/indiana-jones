from __future__ import annotations

from typing import Any


def assessment_summary(reconciliation: dict[str, Any]) -> dict[str, Any]:
    entities = reconciliation.get("entities", [])
    source_ids = {
        source_id
        for entity in entities
        if isinstance(entity, dict)
        for source_id in entity.get("sourceIds", [])
    }
    assessed = [
        entity
        for entity in entities
        if isinstance(entity, dict)
        and entity.get("canonicalRecord", {}).get("recordReliability") != "unassessed"
    ]
    if not entities or not assessed:
        prospective_support = "insufficient"
    elif len(source_ids) >= 2 and len(assessed) >= 2:
        prospective_support = "moderate prospective support"
    else:
        prospective_support = "weak prospective support"
    answerability = (
        "bounded-negative-result"
        if not entities
        else "not-assessable"
        if not assessed
        else "adequate-for-bounded-catalogue-question"
        if len(assessed) == len(entities) and len(source_ids) >= 2
        else "partial"
    )
    return {
        "assessmentVersion": "non-probabilistic-v1",
        "answerability": answerability,
        "sourceCoverage": {
            "distinctSources": len(source_ids),
            "note": "Coverage is limited to ingested sources and is not a completeness claim.",
        },
        "recordReliability": {
            "assessedEntities": len(assessed),
            "unassessedEntities": len(entities) - len(assessed),
        },
        "associationStrength": "requires claim-specific scholarly assessment",
        "qualitativeProspectiveAssessment": {
            "level": prospective_support,
            "scale": [
                "insufficient",
                "weak prospective support",
                "moderate prospective support",
                "strong but unvalidated prospective support",
            ],
            "limit": (
                "This ordinal describes background research support only. "
                "It is not a find probability, recovery prediction, or field authorization."
            ),
        },
        "probability": None,
        "probabilityReason": (
            "No calibrated representative detection model or base rate was supplied."
        ),
    }
