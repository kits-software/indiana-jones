from __future__ import annotations

import re
from typing import Any


SENSITIVE_SUBJECTS = {
    "weapon",
    "precious-metal",
    "hoard",
    "treasure",
    "coin",
    "bullion",
    "numismatic-find",
    "antiquity",
    "valuable",
    "buried-wealth",
    "burial",
    "sacred",
    "vulnerable-portable-find",
}
NON_SENSITIVE_CLASSES = {
    "immovable-landscape-feature",
    "generalized-built-feature",
    "modern-feature",
    "natural-feature",
}
PROHIBITED_DIRECTIVE = re.compile(
    r"\b(?:trespass(?:ing)?|loot(?:ing)?|"
    r"(?:unpermitted|unauthori[sz]ed|without\s+(?:landowner\s+)?permission)\s+"
    r"(?:digging|excavation|removal|collection)|"
    r"(?:use|operate|sweep|scan\s+with)\s+(?:(?:a|the)\s+)?"
    r"(?:metal[- ]?)?detector|"
    r"metal[- ]?detect(?:ing)?\s+(?:(?:a|the)\s+)?"
    r"(?:site|field|land|burial|grave|findspot|for\b)|"
    r"dig\s+(?:(?:up\s+)?(?:each|every|any|the)\s+)?"
    r"(?:signals?|targets?|anomal(?:y|ies)|hits?|spots?)|"
    r"(?:excavate|dig\s+(?:up|into|for)|probe|disturb)\s+"
    r"(?:(?:a|an|the|any)\s+)?(?:site|ground|soil|trench|pit|hole|burial|grave|"
    r"human remains|findspot|cache|deposit|hoard|objects?|artefacts?|artifacts?|"
    r"coins?|treasure)|"
    r"(?:recover|retrieve|remove|collect|extract|salvage|take|unearth|lift|"
    r"pick\s+up|dig\s+for)\s+"
    r"(?!(?:records?|information|history|catalogues?|data|evidence|reports?|"
    r"publications?)\b)"
    r"(?:(?:a|an|the|any)\s+)?"
    r"(?:(?:ancient|buried|portable|valuable|numismatic|gold|silver|metallic|"
    r"detected|cache|"
    r"deposit|hoard)\s+(?:of\s+)?){0,5}"
    r"(?:gold|silver|bullion|coins?|coinage|aurei?|aureus|treasures?|caches?|"
    r"valuables?|weapons?|swords?|hoards?|numismatic\s+deposits?|"
    r"antiquities|artefacts?|artifacts?|objects?|finds?))\b",
    re.IGNORECASE,
)
SENSITIVE_SUBJECT_TEXT = re.compile(
    r"\b(?:swords?|weapons?|gold|silver|bullion|coins?|coinage|aurei?|aureus|"
    r"numismatic(?:\s+(?:finds?|deposits?|material))?|treasures?|valuables?|"
    r"buried\s+(?:wealth|valuables?|treasures?)|precious[- ]metals?|hoards?|"
    r"antiquities|artefacts?|artifacts?|burials?|graves?|human remains|"
    r"sacred (?:objects?|sites?)|portable antiquities|"
    r"vulnerable (?:objects?|finds?))\b",
    re.IGNORECASE,
)
EXACT_TARGETING_TEXT = re.compile(
    r"\b(?:exact|precise)\s+(?:cells?|locations?|sites?|coordinates?|"
    r"findspots?|hotspots?)\b|\bpublic\s+findspots?\b|"
    r"\b(?:map|rank|score|prioriti[sz]e)\s+(?:the\s+)?(?:exact\s+)?"
    r"(?:cells?|locations?|sites?|findspots?|hotspots?)\b|"
    r"\bhotspots?\b|\bcoordinates?\s+(?:for|of)\b|"
    r"\bwhere\s+(?:to|can\s+(?:i|we))\s+(?:find|recover|retrieve)\b|"
    r"\bwithin\s+\d+(?:\.\d+)?\s*(?:m|metres?|meters?|ft|feet)\b|"
    r"\b(?:grid|map|GPS|UTM)\s*(?:references?|coordinates?)\b|"
    r"\b(?:locate|target)\b.{0,80}\b(?:gold|silver|bullion|coins?|hoards?|"
    r"treasures?|swords?|weapons?|antiquities)\b",
    re.IGNORECASE,
)


def risk_classification_state(action: dict[str, Any]) -> str | None:
    classification = action.get("objectRiskClassification")
    state = classification.get("state") if isinstance(classification, dict) else None
    return str(state) if isinstance(state, str) else None


def object_risk_errors(action: dict[str, Any]) -> list[str]:
    classification = action.get("objectRiskClassification")
    if classification is None:
        return []
    if not isinstance(classification, dict):
        return ["objectRiskClassification must be an object when supplied"]
    errors: list[str] = []
    state = classification.get("state")
    classes = classification.get("classes")
    if state not in {"sensitive", "non-sensitive"}:
        errors.append("objectRiskClassification.state is invalid")
    if (
        not isinstance(classes, list)
        or not classes
        or any(not isinstance(value, str) or not value for value in classes)
    ):
        errors.append("objectRiskClassification.classes must be a non-empty string array")
        classes = []
    allowed = SENSITIVE_SUBJECTS | NON_SENSITIVE_CLASSES
    unknown = sorted(set(classes) - allowed)
    if unknown:
        errors.append(
            "objectRiskClassification.classes contains unknown values: "
            + ", ".join(unknown)
        )
    if state == "sensitive" and not set(classes).intersection(SENSITIVE_SUBJECTS):
        errors.append("sensitive classification requires a sensitive object class")
    if state == "non-sensitive" and not set(classes).issubset(NON_SENSITIVE_CLASSES):
        errors.append("non-sensitive classification contains a sensitive object class")
    basis = classification.get("basis")
    if not isinstance(basis, str) or not basis.strip():
        errors.append("objectRiskClassification.basis is required")
    return errors
