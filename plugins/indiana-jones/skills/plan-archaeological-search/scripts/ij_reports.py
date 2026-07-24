from __future__ import annotations

import copy
import hashlib
from typing import Any

from ij_assessment import assessment_summary
from ij_disclosure import lint_public_value
from ij_public_report import safe_report_record


def _public_id(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _strings(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted(
        {
            value
            for value in values
            if isinstance(value, str) and value.strip()
        }
    )


def _classification(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "reportedClass": copy.deepcopy(record.get("objectClass")),
        "basis": copy.deepcopy(record.get("classificationBasis")),
        "certainty": copy.deepcopy(record.get("classificationCertainty")),
    }


def _dating(record: dict[str, Any]) -> dict[str, Any]:
    chronology = copy.deepcopy(record.get("chronology"))
    nested_basis = chronology.get("basis") if isinstance(chronology, dict) else None
    nested_certainty = (
        chronology.get("certainty") if isinstance(chronology, dict) else None
    )
    return {
        "chronology": chronology,
        "basis": copy.deepcopy(record.get("datingBasis", nested_basis)),
        "certainty": nested_certainty,
    }


def _context_and_provenience(record: dict[str, Any]) -> dict[str, Any]:
    context = copy.deepcopy(record.get("archaeologicalContext"))
    assessment = record.get("contextAssessment")
    assessment = copy.deepcopy(assessment) if isinstance(assessment, dict) else None
    nested_quality = None
    nested_basis = None
    if isinstance(context, dict):
        nested_quality = (
            context.get("contextQuality")
            or context.get("quality")
            or context.get("status")
        )
        nested_basis = context.get("basis")
    if isinstance(assessment, dict):
        nested_quality = assessment.get("quality") or assessment.get("status") or nested_quality
        nested_basis = assessment.get("basis") or nested_basis
    return {
        "archaeologicalContext": context,
        "contextQuality": copy.deepcopy(
            record.get("contextQuality", nested_quality or "unassessed")
        ),
        "provenienceQuality": copy.deepcopy(
            record.get("provenienceQuality", "unassessed")
        ),
        "assessmentBasis": nested_basis,
    }


def _repository_and_custody(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "repository": copy.deepcopy(record.get("repository")),
        "accessionNumber": copy.deepcopy(record.get("accessionNumber")),
        "collection": copy.deepcopy(record.get("collection")),
        "custody": copy.deepcopy(record.get("custody")),
        "custodyEvents": copy.deepcopy(record.get("custodyEvents", [])),
        "analysis": copy.deepcopy(record.get("analysis")),
        "analyses": copy.deepcopy(record.get("analyses", [])),
        "conservation": copy.deepcopy(record.get("conservation")),
    }


def _lineage(entity: dict[str, Any]) -> dict[str, Any]:
    record = entity.get("canonicalRecord", {})
    source_ids = set(_strings(entity.get("sourceIds")))
    if isinstance(record.get("sourceId"), str) and record["sourceId"]:
        source_ids.add(record["sourceId"])
    origin_families = set(_strings(entity.get("originFamilyIds")))
    if isinstance(record.get("originFamilyId"), str) and record["originFamilyId"]:
        origin_families.add(record["originFamilyId"])
    return {
        "sourceIds": sorted(source_ids),
        "originFamilyIds": sorted(origin_families),
        "originRecordHashes": _strings(entity.get("originRecordHashes")),
    }


def _conflicts(entity: dict[str, Any]) -> dict[str, Any]:
    conflicts = entity.get("fieldConflicts")
    if not isinstance(conflicts, dict):
        conflicts = {}
    return {
        "status": entity.get("canonicalStatus", "unreported"),
        "hasUnresolvedConflicts": bool(conflicts),
        "fields": copy.deepcopy({key: conflicts[key] for key in sorted(conflicts)}),
    }


def _coverage(reconciliation: dict[str, Any]) -> dict[str, Any]:
    entities = [
        entity
        for entity in reconciliation.get("entities", [])
        if isinstance(entity, dict)
    ]
    source_ids = {
        source_id
        for entity in entities
        for source_id in _lineage(entity)["sourceIds"]
    }
    origin_families = {
        family_id
        for entity in entities
        for family_id in _lineage(entity)["originFamilyIds"]
    }
    input_records = reconciliation.get("recordCount")
    if not isinstance(input_records, int):
        input_records = sum(
            count
            for count in (
                entity.get("duplicateCount", 1) for entity in entities
            )
            if isinstance(count, int) and count > 0
        )
    assessed = sum(
        isinstance(
            entity.get("canonicalRecord", {}).get("recordReliability"), str
        )
        and entity["canonicalRecord"]["recordReliability"] not in {"", "unassessed"}
        for entity in entities
    )
    return {
        **assessment_summary(reconciliation),
        "denominators": {
            "inputRecordCount": input_records,
            "reconciledEntityCount": len(entities),
            "duplicateRecordCount": max(0, input_records - len(entities)),
            "distinctSourceCount": len(source_ids),
            "distinctOriginFamilyCount": len(origin_families),
            "reliabilityAssessedEntityCount": assessed,
        },
    }


def _specialist_suggestions(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    text = " ".join(
        str(record.get(key, ""))
        for record in records
        for key in ("title", "objectClass", "material", "evidenceClasses")
    ).casefold()
    suggestions = [
        {
            "role": "museum collections curator or registrar",
            "instituteCapability": "collections information and accession reconciliation",
            "askFor": "object identity, accession, repository, custody, and analysis records",
        },
        {
            "role": "regional archaeological record specialist",
            "instituteCapability": "find-event, context, excavation, and source-coverage research",
            "askFor": "context records, unpublished reports, aliases, and known catalogue gaps",
        },
    ]
    if any(term in text for term in ("sword", "weapon", "armour", "armor")):
        suggestions.append(
            {
                "role": "arms and armour material-culture specialist",
                "instituteCapability": "weapon classification, technology, and chronology",
                "askFor": "classification and dating review against securely contextualized comparanda",
            }
        )
    if any(term in text for term in ("gold", "silver", "coin", "hoard", "bullion")):
        suggestions.append(
            {
                "role": "archaeometallurgist or numismatist",
                "instituteCapability": "material identification, production evidence, and hoard analysis",
                "askFor": "non-destructive material review and separation of presence from local production",
            }
        )
    if any(record.get("imageRefs") or record.get("spatialEvidence") for record in records):
        suggestions.append(
            {
                "role": "archaeological remote-sensing or GIS specialist",
                "instituteCapability": "imagery, terrain, and spatial-source interpretation",
                "askFor": "source-date, resolution, georegistration, and alternative-feature review",
            }
        )
    return suggestions


def _entity_row(entity: dict[str, Any], public: bool) -> dict[str, Any]:
    record = entity["canonicalRecord"]
    return {
        "entityId": (
            _public_id("find", entity.get("entityId"))
            if public
            else entity.get("entityId")
        ),
        "record": safe_report_record(record, public),
        "classification": _classification(record),
        "dating": _dating(record),
        "contextAndProvenience": _context_and_provenience(record),
        "repositoryAndCustody": _repository_and_custody(record),
        "citations": _lineage(entity),
        "identity": {
            "basis": entity.get("identityBasis"),
            "status": entity.get("reconciliationStatus"),
            "duplicateCount": entity.get("duplicateCount"),
            "independentSourceCount": entity.get("independentSourceCount"),
        },
        "conflicts": _conflicts(entity),
    }


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
    records: list[dict[str, Any]] = []
    for entity in sorted(
        entities,
        key=lambda item: str(item.get("entityId", ""))
        if isinstance(item, dict)
        else "",
    ):
        if not isinstance(entity, dict) or not isinstance(
            entity.get("canonicalRecord"), dict
        ):
            raise ValueError("reconciled entities require canonicalRecord objects")
        records.append(entity["canonicalRecord"])
        rows.append(_entity_row(entity, public))
    records_found = bool(rows)
    report = {
        "schemaVersion": "archaeological-finds-report-2.0",
        "disclosure": "public" if public else "restricted",
        "area": area_description,
        "locationPolicy": (
            "source-reported points and AOIs retained unless an explicit legal, "
            "custodian, community, or user restriction requires omission"
            if public
            else "research evidence workspace; points, AOIs, and image locations retained"
        ),
        "answer": {
            "status": (
                "documented-records-located"
                if records_found
                else "no-record-located-in-bounded-sources"
            ),
            "archaeologicalAbsenceEstablished": False,
            "explanation": (
                "The register contains reconciled documentary records."
                if records_found
                else "The bounded searches returned no reconciled record; this is not evidence that no find exists."
            ),
        },
        "coverage": _coverage(reconciliation),
        "finds": rows,
        "conflictSummary": {
            "entitiesWithConflicts": sum(
                row["conflicts"]["hasUnresolvedConflicts"] for row in rows
            ),
            "fields": sorted(
                {
                    field
                    for row in rows
                    for field in row["conflicts"]["fields"]
                }
            ),
        },
        "contactRoleSuggestions": _specialist_suggestions(records),
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
    if not isinstance(entity.get("canonicalRecord"), dict):
        raise ValueError("reconciled entity requires canonicalRecord")
    row = _entity_row(entity, public)
    record = entity["canonicalRecord"]
    report = {
        "schemaVersion": "archaeological-object-report-2.0",
        "disclosure": "public" if public else "restricted",
        "entityId": row["entityId"],
        "object": row["record"],
        "classification": row["classification"],
        "dating": row["dating"],
        "contextAndProvenience": row["contextAndProvenience"],
        "repositoryAndCustody": row["repositoryAndCustody"],
        "citations": row["citations"],
        "conflicts": row["conflicts"],
        "identityReconciliation": {
            **row["identity"],
            "recordIds": (
                [_public_id("record", value) for value in entity.get("recordIds", [])]
                if public
                else _strings(entity.get("recordIds"))
            ),
        },
        "archaeologicalSequence": {
            "manufacture": copy.deepcopy(record.get("manufacture")),
            "useOrReuse": copy.deepcopy(record.get("useOrReuse")),
            "deposition": copy.deepcopy(record.get("deposition")),
            "recovery": copy.deepcopy(
                record.get("recovery") or record.get("findEvent")
            ),
            "unknownStages": [
                stage
                for stage, value in (
                    ("manufacture", record.get("manufacture")),
                    ("use-or-reuse", record.get("useOrReuse")),
                    ("deposition", record.get("deposition")),
                    (
                        "recovery",
                        record.get("recovery") or record.get("findEvent"),
                    ),
                )
                if value is None
            ],
        },
        "recordAndCustodySequence": {
            "reporting": copy.deepcopy(record.get("reporting")),
            "publication": copy.deepcopy(record.get("publication")),
            "accession": copy.deepcopy(record.get("accessionNumber")),
            "conservation": copy.deepcopy(record.get("conservation")),
            "analysis": copy.deepcopy(
                record.get("analyses") or record.get("analysis")
            ),
            "custodyEvents": copy.deepcopy(record.get("custodyEvents", [])),
            "currentRepository": copy.deepcopy(record.get("repository")),
        },
        "contactRoleSuggestions": _specialist_suggestions([record]),
        "warning": (
            "Collection provenance, archaeological provenience, and evidence "
            "lineage are separate; an unrecorded stage remains unknown rather than inferred."
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
    attempts: list[dict[str, Any]] = []
    total_records = 0
    all_aliases = set(value for value in aliases if isinstance(value, str) and value)
    all_languages = set(
        value for value in languages if isinstance(value, str) and value
    )
    for artifact in query_artifacts:
        query = artifact.get("queryArtifact")
        if not isinstance(query, dict):
            if artifact.get("schemaVersion") != "archaeological-find-reconciliation-1.0":
                raise ValueError("query artifact is missing provenance")
            source_ids = sorted(
                {
                    source_id
                    for entity in artifact.get("entities", [])
                    if isinstance(entity, dict)
                    for source_id in _strings(entity.get("sourceIds"))
                }
            )
            count = int(artifact.get("recordCount", 0))
            total_records += count
            attempts.append(
                {
                    "sourceId": None,
                    "sourceIds": source_ids,
                    "originFamilyIds": sorted(
                        {
                            family_id
                            for entity in artifact.get("entities", [])
                            if isinstance(entity, dict)
                            for family_id in _strings(entity.get("originFamilyIds"))
                        }
                    ),
                    "adapter": "reconciliation",
                    "query": None,
                    "retrievedAt": None,
                    "resultCount": count,
                    "truncated": False,
                    "failure": None,
                }
            )
            continue
        count = int(query.get("resultCount", len(artifact.get("records", []))))
        total_records += count
        query_value = query.get("query")
        if not isinstance(query_value, dict):
            query_value = {"value": query_value} if query_value is not None else {}
        for key in ("aliases", "alias", "placeAliases"):
            value = query_value.get(key)
            all_aliases.update(_strings(value if isinstance(value, list) else [value]))
        for key in ("languages", "language", "languageVariants"):
            value = query_value.get(key)
            all_languages.update(_strings(value if isinstance(value, list) else [value]))
        origin_families = sorted(
            {
                record["originFamilyId"]
                for record in artifact.get("records", [])
                if isinstance(record, dict)
                and isinstance(record.get("originFamilyId"), str)
                and record["originFamilyId"]
            }
        )
        attempts.append(
            {
                "sourceId": query.get("sourceId"),
                "sourceIds": [query.get("sourceId")] if query.get("sourceId") else [],
                "originFamilyIds": origin_families,
                "adapter": query.get("adapter"),
                "adapterVersion": query.get("adapterVersion"),
                "query": copy.deepcopy(query_value),
                "dateRange": copy.deepcopy(
                    query_value.get("dateRange")
                    or query_value.get("dates")
                    or {
                        "from": query_value.get("fromDate"),
                        "to": query_value.get("toDate"),
                    }
                ),
                "retrievedAt": query.get("retrievedAt"),
                "resultCount": count,
                "truncated": query.get("truncated"),
                "sourceExhausted": query.get("pagination", {}).get("sourceExhausted")
                if isinstance(query.get("pagination"), dict)
                else None,
                "rawArtifactSha256": query.get("rawArtifactSha256"),
                "failure": copy.deepcopy(
                    query.get("failure")
                    or artifact.get("failure")
                    or artifact.get("error")
                ),
                "warnings": copy.deepcopy(
                    query.get("warnings") or artifact.get("warnings", [])
                ),
            }
        )
    attempts.sort(
        key=lambda item: (
            str(item.get("sourceId")),
            str(item.get("retrievedAt")),
            str(item.get("rawArtifactSha256")),
        )
    )
    source_ids = {
        source_id
        for attempt in attempts
        for source_id in attempt.get("sourceIds", [])
        if isinstance(source_id, str)
    }
    origin_families = {
        family_id
        for attempt in attempts
        for family_id in attempt.get("originFamilyIds", [])
        if isinstance(family_id, str)
    }
    failed_attempts = sum(attempt.get("failure") is not None for attempt in attempts)
    question_text = question.casefold()
    subject_roles = _specialist_suggestions(
        [{"title": question, "objectClass": question, "material": question}]
    )
    return {
        "schemaVersion": "archaeological-source-gap-report-2.0",
        "question": question,
        "aliasesTried": sorted(all_aliases),
        "languagesTried": sorted(all_languages),
        "attempts": attempts,
        "totalNormalizedRecords": total_records,
        "coverageDenominators": {
            "attemptCount": len(attempts),
            "distinctSourceCount": len(source_ids),
            "distinctOriginFamilyCount": len(origin_families),
            "failedAttemptCount": failed_attempts,
            "truncatedAttemptCount": sum(
                attempt.get("truncated") is True for attempt in attempts
            ),
            "sourceExhaustedAttemptCount": sum(
                attempt.get("sourceExhausted") is True for attempt in attempts
            ),
        },
        "judgment": (
            "bounded-source-gap"
            if total_records == 0
            else "records-found-coverage-still-incomplete"
        ),
        "absenceStatement": (
            "No matching record was located in the attempted sources; archaeological absence is not established."
            if total_records == 0
            else "Located records answer only the bounded queries and do not establish source completeness."
        ),
        "nextSources": [
            {
                "sourceClass": "official heritage or finds register",
                "why": "Tests whether the bounded catalogues omit recorded find events or contexts.",
            },
            {
                "sourceClass": "museum collection and excavation archive",
                "why": "Tests accession, repository, object identity, custody, and unpublished context.",
            },
            {
                "sourceClass": "scholarly publications, theses, and specialist catalogues",
                "why": "Tests classification, dating, material analysis, and historical terminology.",
            },
            {
                "sourceClass": "historical spellings, local-language, and OCR variants",
                "why": "Tests query recall rather than assuming the preferred modern term was used.",
            },
        ],
        "contactRoleSuggestions": subject_roles,
        "contactRoutingNote": (
            "Resolve the jurisdiction before naming an institute; verify the current "
            "official unit and public research-enquiry route at reporting time."
        ),
        "subjectSignals": {
            "weapon": any(term in question_text for term in ("sword", "weapon")),
            "preciousMaterial": any(
                term in question_text for term in ("gold", "silver", "treasure", "hoard")
            ),
        },
        "warning": "Source exhaustion is not archaeological absence.",
    }


def lint_public_report(value: Any, path: str = "$") -> None:
    lint_public_value(value, path)
