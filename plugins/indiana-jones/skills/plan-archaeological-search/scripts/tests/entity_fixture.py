from __future__ import annotations


def entity_record(kind: str) -> dict:
    common = {"schemaVersion": "archaeological-entity-1.0"}
    records = {
        "excavation-context": {
            "contextId": "context-1",
            "contextQuality": "secure-excavated",
            "description": "Recorded fixture context",
        },
        "object": {
            "objectClass": "sword",
            "materials": ["iron"],
            "dateInterval": {
                "earliest": "1000",
                "latest": "1200",
                "basis": "reported typology",
            },
            "contextQuality": "reported-find",
            "identityStatus": "same-object",
        },
        "find-event": {
            "eventType": "controlled excavation",
            "dateInterval": {
                "earliest": "2024-01-01",
                "latest": "2024-01-01",
                "basis": "field record",
            },
            "recoveryMethod": "controlled excavation",
            "publicLocation": "Fixture district",
            "contextQuality": "secure-excavated",
        },
        "assemblage": {
            "assemblageType": "context-defined group",
            "membershipBasis": "field inventory",
        },
        "collection": {
            "collectionName": "Fixture collection",
            "collectionType": "archaeological repository collection",
        },
        "repository": {
            "institutionName": "Fixture Museum",
            "repositoryType": "museum",
        },
        "analysis": {
            "analysisType": "compositional",
            "method": "XRF",
            "resultSummary": "Iron alloy reported",
            "performedAt": "2024-01-01",
        },
        "custody-event": {
            "eventType": "accession",
            "dateInterval": {
                "earliest": "2024-01-02",
                "latest": "2024-01-02",
                "basis": "accession register",
            },
            "custodian": "Fixture Museum",
            "status": "documented",
        },
        "production-evidence": {
            "evidenceType": "crucible residue",
            "material": "copper alloy",
            "interpretation": "qualified local working evidence",
            "contextQuality": "secure-excavated",
        },
        "person-or-organization": {
            "name": "Fixture Institute",
            "entityType": "organization",
        },
        "catalogue-record": {
            "catalogueId": "CAT-1",
            "recordLocator": "record:CAT-1",
        },
        "publication-record": {
            "citation": "Fixture report 2024",
            "recordLocator": "report:2024:1",
        },
        "source-snapshot": {
            "snapshotId": "snapshot:src_hul",
            "sha256": "a" * 64,
            "retrievedAt": "2024-01-01T00:00:00Z",
        },
    }
    return {**common, **records[kind]}
