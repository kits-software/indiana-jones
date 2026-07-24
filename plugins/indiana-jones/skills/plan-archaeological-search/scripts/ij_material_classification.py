from __future__ import annotations

import re


_COLOUR = re.compile(
    r"(?i)\b(?:gold(?:en|[- ]colou?red)|gold[- ]tone|silver[- ]colou?red)\b"
)
_SURFACE = re.compile(
    r"(?i)\b(?:gilt|gilded|gold[- ]plated|silver[- ]gilt|"
    r"pozłacan(?:y|a|e)|złocon(?:y|a|e))\b"
)
_AMBIGUOUS = re.compile(
    r"(?i)(?:\b(?:possibly|probably|perhaps|apparently|presumed|unconfirmed|"
    r"uncertain|ambiguous|gold[- ]like|imitat(?:ion|ing))\b|\bgold\s*\?|"
    r"\b(?:gold|aurum|złoto|silver|au|ag)\b[^;]{0,32}\?|"
    r"\b(?:gold|silver)\s+or\b|\bor\s+(?:gold|silver)\b)"
)
_GOLD = re.compile(r"(?i)(?:\bgold\b|\bzłoto\b|\baurum\b|\bau(?:\s*\d+(?:\.\d+)?\s*%)?\b)")
_ELECTRUM = re.compile(r"(?i)\belectrum\b")
_SILVER = re.compile(r"(?i)(?:\bsilver\b|\bsrebro\b|\bag\s*\d+(?:\.\d+)?\s*%)")


def classify_reported_material(
    reported: str | None,
    descriptive_text: str | None = None,
) -> dict[str, object]:
    basis = "catalogue-material-field"
    if not reported:
        if descriptive_text and _COLOUR.search(descriptive_text):
            return {
                "reportedDescription": descriptive_text,
                "materialClass": "colour-description",
                "basis": "catalogue-title-description",
                "certainty": "descriptive-unverified",
                "supportsPreciousMaterial": False,
            }
        if descriptive_text and _SURFACE.search(descriptive_text):
            return {
                "reportedDescription": descriptive_text,
                "materialClass": "surface-treatment",
                "substance": "gold",
                "basis": "catalogue-title-description",
                "certainty": "descriptive-unverified",
                "supportsPreciousMaterial": False,
            }
        return {
            "materialClass": "unreported",
            "basis": "no-material-field",
            "certainty": "unknown",
            "supportsPreciousMaterial": False,
        }
    if _COLOUR.search(reported):
        material_class, substance, supports = "colour-description", None, False
    elif _SURFACE.search(reported):
        material_class, substance, supports = "surface-treatment", "gold", False
    elif _AMBIGUOUS.search(reported):
        material_class, substance, supports = "ambiguous-material", None, False
    elif _ELECTRUM.search(reported):
        material_class, substance, supports = "precious-alloy", "electrum", True
    elif _GOLD.search(reported):
        material_class, substance, supports = "precious-metal", "gold", True
    elif _SILVER.search(reported):
        material_class, substance, supports = "precious-metal", "silver", True
    else:
        material_class, substance, supports = "other-reported-material", None, False
    result: dict[str, object] = {
        "reportedMaterial": reported,
        "materialClass": material_class,
        "basis": basis,
        "certainty": "reported-unverified",
        "supportsPreciousMaterial": supports,
    }
    if substance:
        result["substance"] = substance
    return result
