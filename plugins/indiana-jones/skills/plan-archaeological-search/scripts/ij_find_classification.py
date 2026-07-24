from __future__ import annotations

from typing import Any


PRODUCTION_TERMS = {
    "crucible",
    "cupellation",
    "mould",
    "mold",
    "slag",
    "casting waste",
    "metalworking debris",
    "unfinished",
    "goldsmith",
    "workshop",
}
WEAPON_TERMS = {"sword", "dagger", "spear", "weapon", "scabbard"}


def evidence_and_risk_classes(
    terms: str,
    material_assessment: dict[str, Any],
) -> tuple[list[str], list[str]]:
    evidence: list[str] = []
    risks: list[str] = []
    if any(term in terms for term in PRODUCTION_TERMS):
        evidence.append("material-production")
    if material_assessment["supportsPreciousMaterial"]:
        evidence.append("precious-material-object")
        risks.append("portable-high-value")
    elif material_assessment["materialClass"] == "surface-treatment":
        evidence.append("precious-surface-treatment")
    if any(term in terms for term in WEAPON_TERMS):
        evidence.append("weapon-or-fitting")
        risks.append("weapon")
    if "hoard" in terms:
        evidence.append("assemblage-or-hoard")
        risks.extend(["hoard", "portable-high-value"])
    if any(term in terms for term in {"grave", "burial", "tomb", "funerary"}):
        risks.append("burial")
    return sorted(set(evidence)), sorted(set(risks))
