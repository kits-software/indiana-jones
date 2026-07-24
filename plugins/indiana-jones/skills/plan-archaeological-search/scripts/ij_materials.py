from __future__ import annotations

import copy
import re
from typing import Any

from ij_spatial import add_google_maps_links


PRODUCTION_LADDER = {
    "direct-installation": 6,
    "production-debris": 5,
    "secure-tools-or-residues": 4,
    "validated-production-analysis": 3,
    "documentary-production": 2,
    "finished-object-or-raw-material": 1,
}
DIRECT_TERMS = {"furnace", "hearth", "crucible setting", "moulding area"}
DEBRIS_TERMS = {
    "slag",
    "crucible",
    "mould",
    "mold",
    "tuyere",
    "casting waste",
    "cupellation debris",
    "production debris",
    "production waste",
    "metalworking debris",
}
TOOL_TERMS = {"goldsmith tool", "anvil", "hammer", "drawplate", "residue"}
UNFINISHED_TERMS = {"unfinished", "casting sprue", "offcut", "blank", "preform"}
DOCUMENTARY_TERMS = {"account", "ledger", "goldsmith", "workshop", "guild"}
SECURE_CONTEXT_TERMS = {
    "sealed",
    "stratified",
    "in situ",
    "in-situ",
    "primary context",
    "excavated context",
    "workshop floor",
}
INSECURE_CONTEXT_TERMS = {
    "unsealed",
    "unstratified",
    "not in situ",
    "not in-situ",
    "redeposited",
    "surface find",
    "stray find",
    "unknown context",
    "context unknown",
    "legacy collection",
    "unprovenanced",
    "unprovenienced",
}
PRODUCTION_LINK_KINDS = {
    "installation",
    "production-debris",
    "residue",
    "tool",
    "unfinished-object",
}
NON_SUPPORTING_MATERIAL_CLASSES = {
    "ambiguous-material",
    "colour-description",
    "surface-treatment",
    "unreported",
}
SUPPORTING_MATERIAL_CLASSES = {"precious-metal", "precious-alloy"}
RESTRICTED_SPATIAL_VALUES = {
    "restricted",
    "private",
    "authority-only",
    "heritage-authority-only",
    "withheld",
    "withhold",
}


def _contains_term(text: str, terms: set[str]) -> bool:
    return any(
        re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, re.IGNORECASE)
        for term in terms
    )


def _material_assessment(record: dict[str, Any]) -> dict[str, Any]:
    assessment = record.get("materialAssessment")
    if isinstance(assessment, dict):
        return dict(assessment)
    return {
        "reportedMaterial": record.get("material"),
        "materialClass": "unreported",
        "basis": "missing-normalized-material-assessment",
        "certainty": "unknown",
        "supportsPreciousMaterial": False,
    }


def _spatial_value(value: Any) -> tuple[Any, bool]:
    if isinstance(value, dict):
        if value.get("sensitivity") in RESTRICTED_SPATIAL_VALUES:
            return None, True
        result = {}
        withheld = False
        for key, nested in value.items():
            copied, child_withheld = _spatial_value(nested)
            withheld = withheld or child_withheld
            if copied is not None:
                result[key] = copied
        return result, withheld
    if isinstance(value, list):
        result = []
        withheld = False
        for nested in value:
            copied, child_withheld = _spatial_value(nested)
            withheld = withheld or child_withheld
            if copied is not None:
                result.append(copied)
        return result, withheld
    return copy.deepcopy(value), False


def _spatial_evidence(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("spatialRestriction") in {"withhold", "authority-only"}:
        return {
            "status": "withheld-by-explicit-restriction",
            "withheldFields": [
                key
                for key in ("findspot", "spatialEvidence", "imageRefs")
                if key in record
            ],
        }
    result: dict[str, Any] = {}
    withheld_fields = []
    for key in ("findspot", "spatialEvidence", "imageRefs"):
        if key not in record:
            continue
        copied, withheld = _spatial_value(record[key])
        if copied is not None:
            result[key] = copied
        if withheld:
            withheld_fields.append(key)
    result["status"] = (
        "withheld-by-explicit-restriction"
        if withheld_fields
        else "retained-as-reported"
    )
    if withheld_fields:
        result["withheldFields"] = sorted(withheld_fields)
    return add_google_maps_links(result)


def _record_details(
    record: dict[str, Any],
    context_basis: str,
) -> dict[str, Any]:
    chronology = copy.deepcopy(record.get("chronology"))
    chronology_basis = (
        chronology.get("basis") if isinstance(chronology, dict) else None
    )
    assessment = record.get("contextAssessment")
    assessment = copy.deepcopy(assessment) if isinstance(assessment, dict) else None
    return {
        "description": {
            "title": copy.deepcopy(record.get("title")),
            "objectClass": copy.deepcopy(record.get("objectClass")),
            "material": copy.deepcopy(record.get("material")),
        },
        "classification": {
            "reportedClass": copy.deepcopy(record.get("objectClass")),
            "basis": copy.deepcopy(record.get("classificationBasis")),
            "certainty": copy.deepcopy(record.get("classificationCertainty")),
        },
        "dating": {
            "chronology": chronology,
            "basis": copy.deepcopy(record.get("datingBasis") or chronology_basis),
        },
        "contextAndProvenience": {
            "archaeologicalContext": copy.deepcopy(
                record.get("archaeologicalContext")
            ),
            "contextAssessment": assessment,
            "contextQuality": copy.deepcopy(
                record.get("contextQuality", "unassessed")
            ),
            "provenienceQuality": copy.deepcopy(
                record.get("provenienceQuality", "unassessed")
            ),
            "assessmentBasis": context_basis,
        },
        "repositoryAndCustody": {
            "repository": copy.deepcopy(record.get("repository")),
            "accessionNumber": copy.deepcopy(record.get("accessionNumber")),
            "collection": copy.deepcopy(record.get("collection")),
            "custody": copy.deepcopy(record.get("custody")),
            "custodyEvents": copy.deepcopy(record.get("custodyEvents", [])),
            "analysis": copy.deepcopy(record.get("analysis")),
            "analyses": copy.deepcopy(record.get("analyses", [])),
            "laboratoryAssessment": copy.deepcopy(
                record.get("laboratoryAssessment")
            ),
        },
        "spatialEvidence": _spatial_evidence(record),
        "conflicts": copy.deepcopy(
            record.get("fieldConflicts") or record.get("conflicts") or {}
        ),
    }


def _supports_material(assessment: dict[str, Any], material: str) -> bool:
    if assessment.get("materialClass") in NON_SUPPORTING_MATERIAL_CLASSES:
        return False
    if assessment.get("materialClass") not in SUPPORTING_MATERIAL_CLASSES:
        return False
    if assessment.get("supportsPreciousMaterial") is not True:
        return False
    certainty = str(assessment.get("certainty", "")).casefold()
    if any(
        term in certainty
        for term in ("ambiguous", "uncertain", "descriptive", "unknown")
    ):
        return False
    substance = str(assessment.get("substance", "")).casefold()
    target = material.casefold().strip()
    if not substance or not target:
        return False
    return substance == target


def _secure_context(record: dict[str, Any]) -> tuple[bool, str]:
    assessment = record.get("contextAssessment")
    if isinstance(assessment, dict):
        secure = assessment.get("secure") is True or assessment.get("status") == "secure"
        basis = assessment.get("basis")
        if secure and isinstance(basis, str) and basis.strip():
            if _contains_term(basis.casefold(), INSECURE_CONTEXT_TERMS):
                return False, "The context assessment contains an insecure qualifier."
            return True, basis.strip()
    context = record.get("archaeologicalContext")
    if isinstance(context, dict):
        secure = context.get("secure") is True or context.get("status") == "secure"
        basis = context.get("basis") or context.get("description")
        if secure and isinstance(basis, str) and basis.strip():
            if _contains_term(basis.casefold(), INSECURE_CONTEXT_TERMS):
                return False, "The context record contains an insecure qualifier."
            return True, basis.strip()
        context_text = " ".join(str(value) for value in context.values())
    else:
        context_text = str(context or "")
    folded = context_text.casefold()
    if _contains_term(folded, INSECURE_CONTEXT_TERMS):
        return False, "The source describes an insecure or unresolved context."
    if _contains_term(folded, SECURE_CONTEXT_TERMS):
        return True, context_text
    return False, "No secure archaeological context is documented."


def _validated_lab_evidence(record: dict[str, Any], material: str) -> bool:
    assessment = record.get("laboratoryAssessment")
    if not isinstance(assessment, dict) or assessment.get("validated") is not True:
        return False
    method = assessment.get("method")
    target = assessment.get("substance") or assessment.get("material")
    result = assessment.get("result")
    validator = assessment.get("validator")
    report_id = assessment.get("reportId")
    artifact_sha256 = assessment.get("artifactSha256")
    auditable_reference = (
        isinstance(report_id, str)
        and bool(report_id.strip())
        or isinstance(artifact_sha256, str)
        and len(artifact_sha256) == 64
        and all(character in "0123456789abcdefABCDEF" for character in artifact_sha256)
    )
    return (
        isinstance(method, str)
        and bool(method.strip())
        and isinstance(result, str)
        and bool(result.strip())
        and isinstance(target, str)
        and target.casefold().strip() == material.casefold().strip()
        and isinstance(validator, str)
        and bool(validator.strip())
        and auditable_reference
    )


def _link_matches_proxy(
    kind: str,
    proxy: str,
    related: dict[str, Any],
) -> bool:
    if kind == "installation":
        return proxy == "direct-installation"
    if kind == "production-debris":
        return proxy == "production-debris"
    object_text = str(related.get("objectClass", "")).casefold()
    if kind == "residue":
        return _contains_term(object_text, {"residue"})
    if kind == "tool":
        return _contains_term(object_text, TOOL_TERMS - {"residue"})
    return _contains_term(object_text, UNFINISHED_TERMS)


def _linked_production_evidence(
    record: dict[str, Any],
    material: str,
    related_records: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    links = record.get("productionEvidenceLinks")
    if not isinstance(links, list):
        return []
    accepted: list[dict[str, Any]] = []
    for link in links:
        if not isinstance(link, dict) or link.get("kind") not in PRODUCTION_LINK_KINDS:
            continue
        if not isinstance(link.get("recordId"), str) or not link["recordId"].strip():
            continue
        if link.get("contextLink") not in {"same-context", "stratigraphically-linked"}:
            continue
        related = related_records.get(link["recordId"])
        if not isinstance(related, dict):
            continue
        related_assessment = _material_assessment(related)
        related_material = _supports_material(related_assessment, material)
        related_lab = _validated_lab_evidence(related, material)
        related_proxy = _production_proxy(related)
        related_secure, _basis = _secure_context(related)
        if (
            not related_secure
            or not (related_material or related_lab)
            or not _link_matches_proxy(str(link["kind"]), related_proxy, related)
        ):
            continue
        accepted.append(dict(link))
    return accepted


def _production_proxy(record: dict[str, Any]) -> str:
    object_text = str(record.get("objectClass", "")).casefold()
    title_text = str(record.get("title", "")).casefold()
    physical_text = (
        title_text
        if not object_text or object_text == "unclassified object or record"
        else object_text
    )
    if _contains_term(physical_text, DIRECT_TERMS):
        return "direct-installation"
    if _contains_term(physical_text, DEBRIS_TERMS):
        return "production-debris"
    if _contains_term(physical_text, TOOL_TERMS | UNFINISHED_TERMS):
        return "secure-tools-or-residues"
    if _contains_term(f"{object_text} {title_text}", DOCUMENTARY_TERMS):
        return "documentary-production"
    return "finished-object-or-raw-material"


def classify_production_evidence(
    record: dict[str, Any],
    material: str = "gold",
    related_records: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    assessment = _material_assessment(record)
    material_supported = _supports_material(assessment, material)
    secure_context, context_basis = _secure_context(record)
    proxy = _production_proxy(record)
    record_id = record.get("recordId")
    if related_records is None:
        related_records = (
            {str(record_id): record}
            if isinstance(record_id, str) and record_id
            else {}
        )
    links = _linked_production_evidence(record, material, related_records)
    lab_validated = _validated_lab_evidence(record, material)
    presence_supported = material_supported or lab_validated
    production_object = proxy in {
        "direct-installation",
        "production-debris",
        "secure-tools-or-residues",
    }
    material_linked = presence_supported
    proxy_linked = production_object or bool(links)
    working_supported = secure_context and material_linked and proxy_linked
    production_supported = working_supported and (
        proxy in {"direct-installation", "production-debris"}
        or any(
            link["kind"] in {"installation", "production-debris"}
            for link in links
        )
    )
    evidence_class = (
        "validated-production-analysis"
        if lab_validated and proxy_linked and proxy == "finished-object-or-raw-material"
        else proxy
    )
    if evidence_class == "validated-production-analysis" and not proxy_linked:
        evidence_class = "finished-object-or-raw-material"
    return {
        "recordId": record.get("recordId"),
        "sourceId": record.get("sourceId"),
        "originFamilyId": record.get("originFamilyId"),
        "rawRecordSha256": record.get("rawRecordSha256"),
        "citation": {
            "sourceId": record.get("sourceId"),
            "originFamilyId": record.get("originFamilyId"),
            "rawRecordSha256": record.get("rawRecordSha256"),
            "sourceRecordId": record.get("sourceRecordId"),
        },
        "evidenceClass": evidence_class,
        "ordinalStrength": PRODUCTION_LADDER[evidence_class],
        "materialAssessment": assessment,
        "materialPresenceSupported": presence_supported,
        "reportedMaterialSupported": material_supported,
        "secureContext": secure_context,
        "secureContextBasis": context_basis,
        "linkedProductionEvidence": links,
        "validatedLaboratoryEvidence": lab_validated,
        "workingSupported": working_supported,
        "productionSupported": production_supported,
        **_record_details(record, context_basis),
        "reason": (
            "Local working requires material-specific evidence, secure archaeological "
            "context, and a production proxy. Production additionally requires an "
            "installation or production debris; a finished object or analytical "
            "method name alone is insufficient."
        ),
    }


def _matches_material(record: dict[str, Any], assessment: dict[str, Any], material: str) -> bool:
    target = material.casefold().strip()
    laboratory = record.get("laboratoryAssessment")
    laboratory_substance = (
        laboratory.get("substance") or laboratory.get("material")
        if isinstance(laboratory, dict)
        else None
    )
    reported = " ".join(
        str(value).casefold()
        for value in (
            record.get("material"),
            assessment.get("reportedMaterial"),
            assessment.get("reportedDescription"),
            assessment.get("substance"),
            record.get("title"),
            laboratory_substance,
        )
        if value
    )
    return bool(target) and target in reported


def _conclusion(status: str, record_ids: list[str], basis: str) -> dict[str, Any]:
    return {
        "status": status,
        "recordIds": sorted(set(record_ids)),
        "basis": basis,
    }


def build_material_evidence_report(
    records: list[dict[str, Any]], material: str
) -> dict[str, Any]:
    related_records = {
        str(record["recordId"]): record
        for record in records
        if isinstance(record, dict)
        and isinstance(record.get("recordId"), str)
        and record["recordId"]
    }
    classified: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("material evidence records must contain objects")
        if not all(
            isinstance(record.get(key), str) and record[key]
            for key in ("recordId", "sourceId")
        ):
            raise ValueError(
                "material evidence records require recordId and sourceId lineage"
            )
        assessment = _material_assessment(record)
        if _matches_material(record, assessment, material):
            classified.append(
                classify_production_evidence(
                    record,
                    material,
                    related_records,
                )
            )
    presence_ids = [
        str(item["recordId"])
        for item in classified
        if item["materialPresenceSupported"] and item.get("recordId")
    ]
    circulation_ids = [
        str(item["recordId"])
        for item in classified
        if item["materialPresenceSupported"]
        and item["secureContext"]
        and item["evidenceClass"] == "finished-object-or-raw-material"
        and item.get("recordId")
    ]
    working_ids = [
        str(item["recordId"])
        for item in classified
        if item["workingSupported"] and item.get("recordId")
    ]
    production_ids = [
        str(item["recordId"])
        for item in classified
        if item["productionSupported"] and item.get("recordId")
    ]
    conclusions = {
        "presence": _conclusion(
            "supported" if presence_ids else "not-supported",
            presence_ids,
            "A normalized material assessment or structured validated laboratory "
            "result supports the target substance; colour, surface treatment, and "
            "ambiguous descriptions are excluded.",
        ),
        "circulation": _conclusion(
            "supported" if circulation_ids else "not-demonstrated",
            circulation_ids,
            "A target-material object in secure archaeological context supports local "
            "circulation or deposition, not manufacture.",
        ),
        "working": _conclusion(
            "supported" if working_ids else "not-demonstrated",
            working_ids,
            "Working requires secure context plus material-linked residues, tools, "
            "unfinished objects, debris, or installations.",
        ),
        "production": _conclusion(
            "supported-pending-specialist-review"
            if production_ids
            else "not-demonstrated",
            production_ids,
            "Production requires the working threshold plus an installation or "
            "production debris.",
        ),
    }
    if production_ids:
        summary = "local-production-supported-pending-specialist-review"
    elif working_ids:
        summary = "local-working-supported-production-not-demonstrated"
    elif circulation_ids:
        summary = "material-circulation-supported-working-not-demonstrated"
    elif presence_ids:
        summary = "material-presence-only"
    elif classified:
        summary = "material-description-does-not-establish-material-presence"
    else:
        summary = "no-record-in-searched-sources"
    strongest = max(
        classified,
        key=lambda item: (item["ordinalStrength"], str(item.get("recordId"))),
        default=None,
    )
    source_ids = {
        record["sourceId"]
        for record in records
        if isinstance(record, dict)
        and isinstance(record.get("sourceId"), str)
        and record["sourceId"]
    }
    origin_families = {
        record["originFamilyId"]
        for record in records
        if isinstance(record, dict)
        and isinstance(record.get("originFamilyId"), str)
        and record["originFamilyId"]
    }
    conflicts = [
        {
            "recordId": record.get("recordId"),
            "fields": copy.deepcopy(
                record.get("fieldConflicts") or record.get("conflicts")
            ),
        }
        for record in records
        if isinstance(record, dict)
        and (record.get("fieldConflicts") or record.get("conflicts"))
    ]
    return {
        "schemaVersion": "archaeological-material-evidence-2.0",
        "material": material,
        "conclusion": summary,
        "answerBoundary": {
            "matchingRecordStatus": (
                "matching-records-located"
                if classified
                else "no-record-located-in-bounded-input"
            ),
            "materialAbsenceEstablished": False,
            "explanation": (
                "The conclusion is limited to the supplied records and their declared material assessments."
            ),
        },
        "coverageDenominators": {
            "inputRecordCount": len(records),
            "matchingRecordCount": len(classified),
            "distinctSourceCount": len(source_ids),
            "distinctOriginFamilyCount": len(origin_families),
            "secureContextMatchCount": sum(
                item["secureContext"] for item in classified
            ),
            "validatedAnalysisMatchCount": sum(
                item["validatedLaboratoryEvidence"] for item in classified
            ),
        },
        "conclusions": conclusions,
        "strongestEvidence": strongest,
        "evidenceMatrix": sorted(
            classified,
            key=lambda item: (-item["ordinalStrength"], str(item.get("recordId"))),
        ),
        "conflictRegister": sorted(
            conflicts, key=lambda item: str(item.get("recordId"))
        ),
        "alternativeExplanations": [
            "imported finished object",
            "circulation, repair, curation, or redeposition",
            "surface treatment or colour description mistaken for bulk material",
            "legacy or insecure collection provenance",
        ],
        "nextDiscriminatingEvidence": [
            "secure production installation or debris",
            "context-linked tools, residues, or unfinished pieces",
            "validated material-specific residue or metallographic analysis",
            "independent documentary and excavation corroboration",
        ],
        "contactRoleSuggestions": [
            {
                "role": "archaeometallurgist or archaeological materials laboratory",
                "instituteCapability": "material identification, residue, metallography, and production-evidence review",
                "askFor": "method-appropriate confirmation tied to the exact object and context record",
            },
            {
                "role": "context archaeologist or excavation archive specialist",
                "instituteCapability": "provenience, stratigraphy, assemblage, and recovery-history review",
                "askFor": "the context record and independent evidence linking objects, debris, tools, and installations",
            },
            {
                "role": "museum curator, conservator, or registrar",
                "instituteCapability": "accession, analysis, conservation, custody, and object-identity records",
                "askFor": "the complete object file and any prior analytical reports",
            },
        ],
        "warning": (
            "A finished object, a gilded or gold-coloured description, a contextless "
            "crucible, or an XRF method label alone does not establish local working."
        ),
    }
