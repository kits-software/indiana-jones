from __future__ import annotations

import copy
from typing import Any

from ij_spatial import add_google_maps_links


SPATIAL_FIELDS = ("findspot", "spatialEvidence", "imageRefs")
RESTRICTED_SPATIAL_VALUES = {
    "restricted",
    "private",
    "authority-only",
    "heritage-authority-only",
    "non-public",
    "vulnerable",
    "sacred",
    "burial",
    "withheld",
    "withhold",
}
REPORT_RECORD_FIELDS = {
    "recordId",
    "sourceId",
    "sourceRecordId",
    "title",
    "objectClass",
    "classificationBasis",
    "classificationCertainty",
    "material",
    "materialAssessment",
    "chronology",
    "datingBasis",
    "archaeologicalContext",
    "contextAssessment",
    "contextQuality",
    "provenienceQuality",
    "repository",
    "accessionNumber",
    "collection",
    "custody",
    "custodyEvents",
    "analyses",
    "analysis",
    "laboratoryAssessment",
    "conservation",
    "identityStatus",
    "evidenceClasses",
    "recordReliability",
    "spatialRestriction",
    "sensitivity",
}


def _copy_public_spatial(value: Any) -> tuple[Any, bool]:
    if isinstance(value, dict):
        if (
            value.get("sensitivity") in RESTRICTED_SPATIAL_VALUES
            or value.get("spatialRestriction") in RESTRICTED_SPATIAL_VALUES
        ):
            return None, True
        result: dict[str, Any] = {}
        withheld = False
        for key, nested in value.items():
            copied, child_withheld = _copy_public_spatial(nested)
            withheld = withheld or child_withheld
            if copied is not None:
                result[key] = copied
        return result, withheld
    if isinstance(value, list):
        result = []
        withheld = False
        for nested in value:
            copied, child_withheld = _copy_public_spatial(nested)
            withheld = withheld or child_withheld
            if copied is not None:
                result.append(copied)
        return result, withheld
    return copy.deepcopy(value), False


def safe_report_record(record: dict[str, Any], public: bool) -> dict[str, Any]:
    allowed = set(REPORT_RECORD_FIELDS)
    if public:
        allowed -= {"recordId", "sourceId"}
    safe = {key: copy.deepcopy(record[key]) for key in allowed if key in record}
    restriction = record.get("spatialRestriction")
    withheld_fields: list[str] = []
    for key in SPATIAL_FIELDS:
        if key not in record:
            continue
        if public and restriction in RESTRICTED_SPATIAL_VALUES:
            withheld_fields.append(key)
            continue
        if public:
            copied, withheld = _copy_public_spatial(record[key])
        else:
            copied, withheld = copy.deepcopy(record[key]), False
        if copied is not None:
            safe[key] = copied
        if withheld:
            withheld_fields.append(key)
    if not public and "riskClasses" in record:
        safe["riskClasses"] = copy.deepcopy(record["riskClasses"])
    if withheld_fields:
        safe["spatialEvidenceStatus"] = "withheld-by-explicit-restriction"
        safe["withheldSpatialFields"] = sorted(set(withheld_fields))
    return add_google_maps_links(safe)
