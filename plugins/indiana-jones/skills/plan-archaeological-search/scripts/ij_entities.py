from __future__ import annotations

from typing import Any


ENTITY_KINDS = {
    "excavation-context",
    "object",
    "find-event",
    "assemblage",
    "collection",
    "repository",
    "analysis",
    "custody-event",
    "production-evidence",
    "person-or-organization",
    "catalogue-record",
    "publication-record",
    "source-snapshot",
}
COMMON_NODE_FIELDS = {
    "nodeId",
    "kind",
    "label",
    "authority",
    "sourceIds",
    "cellIds",
    "sensitivity",
    "notes",
    "locator",
    "coordinate",
    "chronology",
    "record",
}
COMMON_RECORD_FIELDS = {
    "schemaVersion",
    "certainty",
    "notes",
    "sourceRecordIds",
}
RECORD_FIELDS = {
    "excavation-context": {
        "contextId",
        "contextQuality",
        "description",
    },
    "object": {
        "objectClass",
        "materials",
        "dateInterval",
        "contextQuality",
        "identityStatus",
        "sourceNativeIds",
    },
    "find-event": {
        "eventType",
        "dateInterval",
        "recoveryMethod",
        "publicLocation",
        "contextQuality",
    },
    "assemblage": {
        "assemblageType",
        "membershipBasis",
        "memberObjectIds",
    },
    "collection": {"collectionName", "collectionType"},
    "repository": {"institutionName", "repositoryType", "verifiedAt"},
    "analysis": {
        "analysisType",
        "method",
        "resultSummary",
        "performedAt",
        "sampleId",
    },
    "custody-event": {
        "eventType",
        "dateInterval",
        "custodian",
        "status",
    },
    "production-evidence": {
        "evidenceType",
        "material",
        "interpretation",
        "contextQuality",
    },
    "person-or-organization": {"name", "entityType"},
    "catalogue-record": {"catalogueId", "recordLocator"},
    "publication-record": {"citation", "recordLocator"},
    "source-snapshot": {"snapshotId", "sha256", "retrievedAt"},
}
REQUIRED_FIELDS = {
    kind: fields - {"sampleId", "sourceNativeIds", "memberObjectIds", "verifiedAt"}
    for kind, fields in RECORD_FIELDS.items()
}
ARRAY_FIELDS = {"materials", "sourceNativeIds", "memberObjectIds", "sourceRecordIds"}
OBJECT_FIELDS = {"dateInterval"}
CONTEXT_QUALITIES = {
    "secure-excavated",
    "recorded-survey",
    "reported-find",
    "legacy-provenance",
    "market-only",
    "unknown",
}
IDENTITY_STATES = {
    "same-object",
    "probable-same-object",
    "possible-same-object",
    "different-object",
    "unresolved",
}


def provenance_sensitivity_errors(
    node: dict[str, Any],
    source_map: dict[str, dict[str, Any]],
) -> list[str]:
    if node.get("sensitivity") != "public":
        return []
    protected = sorted(
        source_id
        for source_id in node.get("sourceIds", [])
        if source_id in source_map
        and source_map[source_id].get("sensitivity") != "public"
    )
    if not protected:
        return []
    return [
        f"{node.get('nodeId', '<unknown>')}: public node cites non-public source(s): "
        + ", ".join(protected)
    ]


def validate_entity_node(node: dict[str, Any]) -> list[str]:
    kind = node.get("kind")
    if kind not in ENTITY_KINDS:
        return []
    node_id = node.get("nodeId", "<unknown>")
    errors: list[str] = []
    unknown_node_fields = sorted(set(node) - COMMON_NODE_FIELDS)
    if unknown_node_fields:
        errors.append(
            f"{node_id}: unsupported entity-node fields: "
            + ", ".join(unknown_node_fields)
        )
    record = node.get("record")
    if not isinstance(record, dict):
        return errors + [f"{node_id}: {kind} requires a typed record object"]
    if record.get("schemaVersion") != "archaeological-entity-1.0":
        errors.append(f"{node_id}: entity record must use archaeological-entity-1.0")
    allowed = COMMON_RECORD_FIELDS | RECORD_FIELDS[kind]
    unknown = sorted(set(record) - allowed)
    if unknown:
        errors.append(f"{node_id}: unsupported {kind} record fields: " + ", ".join(unknown))
    for field in sorted(REQUIRED_FIELDS[kind]):
        if field in ARRAY_FIELDS or field in OBJECT_FIELDS:
            if field not in record:
                errors.append(f"{node_id}: {kind} record requires {field}")
            continue
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{node_id}: {kind} record requires non-empty {field}")
    for field in ARRAY_FIELDS.intersection(record):
        value = record[field]
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            errors.append(f"{node_id}: record.{field} must be a string array")
    for field in OBJECT_FIELDS.intersection(record):
        value = record[field]
        if not isinstance(value, dict) or any(
            not isinstance(value.get(part), str) or not value[part].strip()
            for part in ("earliest", "latest", "basis")
        ):
            errors.append(
                f"{node_id}: record.{field} requires earliest, latest, and basis"
            )
    quality = record.get("contextQuality")
    if quality is not None and quality not in CONTEXT_QUALITIES:
        errors.append(f"{node_id}: record.contextQuality is invalid")
    identity = record.get("identityStatus")
    if identity is not None and identity not in IDENTITY_STATES:
        errors.append(f"{node_id}: record.identityStatus is invalid")
    sha256 = record.get("sha256")
    if sha256 is not None and (
        not isinstance(sha256, str)
        or len(sha256) != 64
        or any(character not in "0123456789abcdef" for character in sha256)
    ):
        errors.append(f"{node_id}: record.sha256 must be a lowercase SHA-256 digest")
    return errors
