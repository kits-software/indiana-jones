from __future__ import annotations

from typing import Any, Callable


SPATIAL_SENSITIVITIES = {
    "public",
    "restricted",
    "non-public",
    "vulnerable",
    "sacred",
    "burial",
}
SPATIAL_RESTRICTIONS = {
    "withhold",
    "withheld",
    "authority-only",
    "heritage-authority-only",
    "restricted",
    "private",
    "non-public",
}


def spatial_policy(
    record: dict[str, Any],
    source_sensitivity: str,
    source_restriction: str | None,
    risk_classes: list[str],
    findspot_keys: tuple[str, ...],
    string_value: Callable[[Any], str | None],
) -> tuple[str, str | None]:
    lowered = {str(key).casefold(): value for key, value in record.items()}
    declared = string_value(
        lowered.get("spatialsensitivity", lowered.get("sensitivity"))
    )
    for key in findspot_keys:
        raw_findspot = lowered.get(key.casefold())
        if isinstance(raw_findspot, dict):
            nested = string_value(raw_findspot.get("sensitivity"))
            if nested:
                declared = nested
                break
    restriction = string_value(
        lowered.get("spatialrestriction")
    ) or source_restriction
    normalized_restriction = restriction.casefold() if restriction else None
    normalized_declared = declared.casefold() if declared else None
    if "burial" in risk_classes:
        return "burial", normalized_restriction or "authority-only"
    if normalized_restriction in SPATIAL_RESTRICTIONS:
        return "restricted", normalized_restriction
    if normalized_declared in SPATIAL_SENSITIVITIES:
        return normalized_declared, normalized_restriction
    if source_sensitivity in SPATIAL_SENSITIVITIES:
        return source_sensitivity, normalized_restriction
    return "restricted", normalized_restriction or "withhold"
