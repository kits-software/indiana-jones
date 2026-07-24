from __future__ import annotations

from typing import Any

from ij_journal import value_sha256


CLAIM_FIELDS = {
    "title": "preferred-label",
    "objectClass": "object-class",
    "material": "made-of",
    "chronology": "dated-to",
    "archaeologicalContext": "recovered-in-context",
    "findspot": "found-at",
    "repository": "held-by",
    "accessionNumber": "accession-identifier",
}


def extract_claims(artifact: dict[str, Any]) -> dict[str, Any]:
    records = artifact.get("records")
    query = artifact.get("queryArtifact")
    if not isinstance(records, list) or not isinstance(query, dict):
        raise ValueError("normalized artifact requires records and queryArtifact")
    claims: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("normalized records must contain objects")
        record_id = record.get("recordId")
        source_id = record.get("sourceId")
        raw_hash = record.get("rawRecordSha256")
        if not all(isinstance(value, str) and value for value in (record_id, source_id, raw_hash)):
            raise ValueError("normalized record lacks identity or raw-record lineage")
        for field, predicate in CLAIM_FIELDS.items():
            if field not in record or record[field] in (None, "", [], {}):
                continue
            value = record[field]
            claim_key = {
                "recordId": record_id,
                "predicate": predicate,
                "value": value,
                "rawRecordSha256": raw_hash,
            }
            claims.append(
                {
                    "claimId": f"claim_{value_sha256(claim_key)[:20]}",
                    "subjectId": record_id,
                    "predicate": predicate,
                    "value": value,
                    "sourceIds": [source_id],
                    "originFamilyId": query.get("originFamilyId", source_id),
                    "recordLocator": {
                        "sourceRecordId": record.get("sourceRecordId"),
                        "rawRecordSha256": raw_hash,
                    },
                    "extraction": {
                        "method": "deterministic-field-mapping",
                        "version": record.get("normalizationVersion"),
                    },
                    "assertionStatus": "source-reported",
                    "evidenceGrade": "unassessed",
                    "contradictionClaimIds": [],
                    "sensitivity": record.get("sensitivity", "restricted"),
                }
            )
    return {
        "schemaVersion": "archaeological-claims-1.0",
        "sourceArtifactSha256": value_sha256(artifact),
        "claimCount": len(claims),
        "claims": sorted(claims, key=lambda item: item["claimId"]),
    }
