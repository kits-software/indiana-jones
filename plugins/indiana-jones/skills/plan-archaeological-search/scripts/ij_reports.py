from __future__ import annotations

import copy
import re
from typing import Any

from ij_ingest import assessment_summary


COORDINATE_KEY_PATTERN = re.compile(
    r"^(?:coordinates?|restrictedGeometry|geometry|bbox|lat|latitude|lon|lng|"
    r"longitude|findspot|accessRoute|gridCellIds?)$",
    re.IGNORECASE,
)
COORDINATE_TEXT_PATTERN = re.compile(
    r"(?<![\d.])-?(?:[1-8]?\d(?:\.\d{4,})|90(?:\.0+)?)"
    r"\s*[,;/]\s*"
    r"-?(?:1[0-7]\d(?:\.\d{4,})?|[1-9]?\d(?:\.\d{4,})?|180(?:\.0+)?)"
)


def _safe_record(record: dict[str, Any], public: bool) -> dict[str, Any]:
    allowed = {
        "recordId",
        "sourceId",
        "title",
        "objectClass",
        "material",
        "chronology",
        "repository",
        "evidenceClasses",
        "recordReliability",
    }
    safe = {key: copy.deepcopy(record[key]) for key in allowed if key in record}
    if not public:
        for key in ("findspot", "archaeologicalContext", "accessionNumber", "riskClasses"):
            if key in record:
                safe[key] = copy.deepcopy(record[key])
    return safe


def build_finds_report(
    reconciliation: dict[str, Any],
    *,
    area_description: str,
    public: bool,
) -> dict[str, Any]:
    entities = reconciliation.get("entities")
    if not isinstance(entities, list):
        raise ValueError("reconciliation.entities must be an array")
    rows: list[dict[str, Any]] = []
    for entity in entities:
        if not isinstance(entity, dict) or not isinstance(
            entity.get("canonicalRecord"), dict
        ):
            raise ValueError("reconciled entities require canonicalRecord objects")
        rows.append(
            {
                "entityId": entity.get("entityId"),
                "record": _safe_record(entity["canonicalRecord"], public),
                "duplicateCount": entity.get("duplicateCount"),
                "independentSourceCount": entity.get("independentSourceCount"),
                "reconciliationStatus": entity.get("reconciliationStatus"),
                "sourceIds": sorted(entity.get("sourceIds", [])),
            }
        )
    report = {
        "schemaVersion": "archaeological-finds-report-1.0",
        "disclosure": "public" if public else "restricted",
        "area": area_description,
        "locationPolicy": (
            "generalized study area; exact findspots and target cells withheld"
            if public
            else "restricted evidence workspace; do not redistribute"
        ),
        "coverage": assessment_summary(reconciliation),
        "finds": rows,
        "interpretiveWarnings": [
            "Catalogue records may repeat one origin and are reconciled conservatively.",
            "No record found in searched sources is not evidence of archaeological absence.",
            "Object presence does not establish local manufacture or production.",
        ],
    }
    if public:
        lint_public_report(report)
    return report


def build_object_report(
    reconciliation: dict[str, Any],
    entity_id: str,
    *,
    public: bool,
) -> dict[str, Any]:
    entity = next(
        (
            item
            for item in reconciliation.get("entities", [])
            if isinstance(item, dict) and item.get("entityId") == entity_id
        ),
        None,
    )
    if entity is None:
        raise ValueError(f"unknown reconciled entity: {entity_id}")
    report = {
        "schemaVersion": "archaeological-object-report-1.0",
        "disclosure": "public" if public else "restricted",
        "entityId": entity_id,
        "object": _safe_record(entity["canonicalRecord"], public),
        "identity": {
            "basis": entity.get("identityBasis"),
            "status": entity.get("reconciliationStatus"),
            "recordIds": entity.get("recordIds"),
            "sourceIds": entity.get("sourceIds"),
            "duplicateCount": entity.get("duplicateCount"),
        },
        "biographyCoverage": {
            "manufacture": "unassessed",
            "deposition": "unassessed",
            "discovery": (
                "reported"
                if entity["canonicalRecord"].get("archaeologicalContext")
                else "unassessed"
            ),
            "collectionCustody": (
                "partial"
                if entity["canonicalRecord"].get("repository")
                else "unassessed"
            ),
            "presentRepository": entity["canonicalRecord"].get("repository"),
        },
        "warning": (
            "Collection provenance, archaeological provenience, and evidence "
            "lineage are separate and may each be incomplete."
        ),
    }
    if public:
        lint_public_report(report)
    return report


def build_source_gap_report(
    query_artifacts: list[dict[str, Any]],
    *,
    question: str,
    aliases: list[str],
    languages: list[str],
) -> dict[str, Any]:
    attempts = []
    total_records = 0
    for artifact in query_artifacts:
        query = artifact.get("queryArtifact")
        if not isinstance(query, dict):
            raise ValueError("query artifact is missing provenance")
        count = int(query.get("resultCount", 0))
        total_records += count
        attempts.append(
            {
                "sourceId": query.get("sourceId"),
                "adapter": query.get("adapter"),
                "query": query.get("query"),
                "retrievedAt": query.get("retrievedAt"),
                "resultCount": count,
                "truncated": query.get("truncated"),
                "rawArtifactSha256": query.get("rawArtifactSha256"),
            }
        )
    return {
        "schemaVersion": "archaeological-source-gap-report-1.0",
        "question": question,
        "aliasesTried": sorted(set(aliases)),
        "languagesTried": sorted(set(languages)),
        "attempts": attempts,
        "totalNormalizedRecords": total_records,
        "judgment": (
            "bounded-source-gap"
            if total_records == 0
            else "records-found-coverage-still-incomplete"
        ),
        "nextLawfulChecks": [
            "official heritage or finds register",
            "museum and excavation catalogue",
            "scholarly publications, theses, and archives",
            "historical spellings, local-language variants, and OCR variants",
            "specialist or heritage-authority referral",
        ],
        "warning": "Source exhaustion is not archaeological absence.",
    }


def lint_public_report(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if COORDINATE_KEY_PATTERN.search(str(key)):
                raise ValueError(f"public report contains a restricted key at {path}.{key}")
            lint_public_report(nested, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, nested in enumerate(value):
            lint_public_report(nested, f"{path}[{index}]")
        return
    if isinstance(value, str) and COORDINATE_TEXT_PATTERN.search(value):
        raise ValueError(f"public report contains coordinate-like prose at {path}")
