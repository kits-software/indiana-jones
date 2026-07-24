from __future__ import annotations

from copy import deepcopy

from ij_calibration import evaluate_held_out_benchmark


PERMISSION_KEYS = (
    "jurisdiction",
    "landAccess",
    "detecting",
    "excavation",
    "heritage",
    "findsReporting",
    "communityAuthority",
)


def complete_permission_fields() -> dict:
    method = "sensitive-findspot-assessment"
    area_id = "example:river-town"
    permissions = {
        key: {
            "state": "confirmed",
            "basis": f"Fixture authority approval for {key}",
            "scope": "Declared fixture area, dates, analytical method, and reporting route",
            "issuer": "Fixture Heritage Authority",
            "instrumentId": f"permit:{key}",
            "officialLocator": f"https://authority.example/permits/{key}",
            "validFrom": "2026-01-01T00:00:00Z",
            "validUntil": "2099-12-31T23:59:59Z",
            "permittedActivities": [method],
            "scopeBindings": {
                "methods": [method],
                "areaIds": [area_id],
            },
            "verifier": "Fixture archaeological reviewer",
            "verifiedAt": "2026-07-24T10:00:00Z",
        }
        for key in PERMISSION_KEYS
    }
    return {
        "permissionRequest": {
            "method": method,
            "areaId": area_id,
        },
        "permissionBundle": permissions,
        "restrictedHandling": {
            "destinationId": "fixture-vault:case-123",
            "channelType": "case-vault",
            "recipientOrganization": "Fixture Heritage Authority",
            "recipientRoles": ["responsible archaeologist", "heritage authority"],
            "responsibleProfessional": "Fixture Archaeologist",
            "accessControlled": True,
            "exactLocationAuthorized": True,
            "verifier": "Fixture security reviewer",
            "verifiedAt": "2026-07-24T10:00:00Z",
        },
    }


def calibration_fixture() -> dict:
    frozen_inputs = {
        "modelSha256": "1" * 64,
        "featuresSha256": "2" * 64,
        "thresholdSha256": "3" * 64,
        "candidateSetSha256": "4" * 64,
    }
    buckets = (
        (0.1, [0, 0, 0, 0, 1]),
        (0.3, [0, 0, 0, 1, 1]),
        (0.6, [0, 0, 1, 1, 1]),
        (0.9, [0, 1, 1, 1, 1]),
    )
    outcomes = [
        (predicted, outcome)
        for predicted, labels in buckets
        for outcome in labels
    ]
    observations = [
        {
            "observationId": f"held-out-{index:02d}",
            "predictedProbability": predicted,
            "observedOutcome": outcome,
            "resolutionStatus": "resolved",
            "split": "held-out",
            "sourceSnapshotId": f"snapshot:{index:02d}",
            "geographyGroupId": f"region-{index % 4}",
        }
        for index, (predicted, outcome) in enumerate(outcomes, 1)
    ]
    benchmark = {
        "schemaVersion": "archaeological-calibration-benchmark-1.0",
        "benchmarkId": "documented-find-held-out-v1",
        "datasetId": "held-out-fixture",
        "eventDefinition": "A documented find in a declared survey unit",
        "denominator": "100 independently surveyed units",
        "status": "resolved",
        "observations": observations,
    }
    evaluation = evaluate_held_out_benchmark(
        benchmark,
        frozen_inputs=frozen_inputs,
    )
    calibration = {
        "eventDefinition": "A documented find in a declared survey unit",
        "denominator": "100 independently surveyed units",
        "detectionProcess": "Frozen systematic survey protocol",
        "reportingProcess": "Mandatory reporting with audited follow-up",
        "biasTreatment": "Inverse reporting weights and missingness sensitivity",
        "validityDomain": "Comparable authorized survey units in the fixture region",
        "sample": {"positive": 20, "negative": 80, "heldOut": 20},
        "geographicallySeparated": True,
        "modelFrozen": True,
        "featuresFrozen": True,
        "thresholdFrozen": True,
        "candidateSetFrozen": True,
        **frozen_inputs,
        "datasetReferences": [
            {
                "datasetId": "training-fixture",
                "role": "training",
                "recordCount": 60,
                "sha256": "5" * 64,
            },
            {
                "datasetId": "calibration-fixture",
                "role": "calibration",
                "recordCount": 20,
                "sha256": "6" * 64,
            },
            {
                "datasetId": "held-out-fixture",
                "role": "held-out",
                "recordCount": evaluation["datasetReference"]["recordCount"],
                "sha256": evaluation["datasetReference"]["sha256"],
            },
        ],
        "heldOutEvaluation": evaluation,
        "heldOutMetrics": deepcopy(evaluation["heldOutMetrics"]),
        "estimatedProbability": 0.31,
        "uncertaintyInterval": [0.2, 0.44],
    }
    return calibration
