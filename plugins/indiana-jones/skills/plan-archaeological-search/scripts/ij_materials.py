from __future__ import annotations

from typing import Any


PRODUCTION_LADDER = {
    "direct-installation": 6,
    "production-debris": 5,
    "secure-tools-or-residues": 4,
    "laboratory-analysis": 3,
    "documentary-production": 2,
    "finished-object-or-raw-material": 1,
}
DIRECT_TERMS = {"furnace", "hearth", "crucible setting", "moulding area", "workshop floor"}
DEBRIS_TERMS = {"slag", "crucible", "mould", "mold", "tuyere", "casting waste"}
TOOL_TERMS = {"goldsmith tool", "anvil", "hammer", "drawplate", "residue"}
ANALYSIS_TERMS = {"isotope", "metallography", "xrf", "sem-eds", "composition"}
DOCUMENTARY_TERMS = {"account", "ledger", "goldsmith", "workshop", "guild"}


def _record_text(record: dict[str, Any]) -> str:
    values = [
        record.get("title"),
        record.get("objectClass"),
        record.get("material"),
        record.get("archaeologicalContext"),
    ]
    return " ".join(str(value).casefold() for value in values if value)


def classify_production_evidence(record: dict[str, Any]) -> dict[str, Any]:
    text = _record_text(record)
    context = str(record.get("archaeologicalContext", "")).casefold()
    if any(term in text for term in DIRECT_TERMS):
        evidence_class = "direct-installation"
    elif any(term in text for term in DEBRIS_TERMS):
        evidence_class = "production-debris"
    elif any(term in text for term in TOOL_TERMS) and context:
        evidence_class = "secure-tools-or-residues"
    elif any(term in text for term in ANALYSIS_TERMS):
        evidence_class = "laboratory-analysis"
    elif any(term in text for term in DOCUMENTARY_TERMS):
        evidence_class = "documentary-production"
    else:
        evidence_class = "finished-object-or-raw-material"
    return {
        "recordId": record.get("recordId"),
        "evidenceClass": evidence_class,
        "ordinalStrength": PRODUCTION_LADDER[evidence_class],
        "secureContext": bool(context),
        "sourceId": record.get("sourceId"),
        "reason": (
            "Classification identifies the strongest production proxy in this record; "
            "it does not by itself establish local production."
        ),
    }

def build_material_evidence_report(
    records: list[dict[str, Any]], material: str
) -> dict[str, Any]:
    classified = [
        classify_production_evidence(record)
        for record in records
        if material.casefold() in _record_text(record)
    ]
    strongest = max(
        classified,
        key=lambda item: (item["ordinalStrength"], str(item.get("recordId"))),
        default=None,
    )
    if not strongest:
        conclusion = "no-record-in-searched-sources"
    elif strongest["ordinalStrength"] >= PRODUCTION_LADDER["production-debris"]:
        conclusion = "local-working-or-production-supported-pending-specialist-review"
    elif strongest["evidenceClass"] == "documentary-production":
        conclusion = "documentary-working-supported-physical-workshop-unconfirmed"
    elif strongest["evidenceClass"] in {
        "secure-tools-or-residues",
        "laboratory-analysis",
    }:
        conclusion = "working-plausible-production-not-yet-demonstrated"
    else:
        conclusion = "material-presence-only"
    return {
        "schemaVersion": "archaeological-material-evidence-1.0",
        "material": material,
        "conclusion": conclusion,
        "strongestEvidence": strongest,
        "evidenceMatrix": sorted(
            classified,
            key=lambda item: (-item["ordinalStrength"], str(item.get("recordId"))),
        ),
        "alternativeExplanations": [
            "imported finished object",
            "circulation, repair, curation, or redeposition",
            "legacy or insecure collection provenance",
        ],
        "nextDiscriminatingEvidence": [
            "secure production installation or debris",
            "context-linked tools, residues, or unfinished pieces",
            "specialist compositional or metallographic analysis",
            "independent documentary and excavation corroboration",
        ],
        "warning": "A finished gold object alone is not evidence of local gold working.",
    }
