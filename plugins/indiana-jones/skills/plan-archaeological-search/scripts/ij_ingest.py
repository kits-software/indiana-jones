from __future__ import annotations

import csv
import io
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ij_ingest_guard import (
    ValidatingRedirectHandler,
    public_host_problem,
    safe_xml_root,
    validate_public_url,
    validate_query_artifact,
)
from ij_journal import file_sha256, value_sha256


NORMALIZATION_VERSION = "archaeological-find-v1"
SUPPORTED_FORMATS = {
    "json",
    "jsonl",
    "csv",
    "oai-pmh",
    "iiif",
    "rdf-xml",
    "sparql-json",
}
ID_KEYS = ("accessionNumber", "accession", "identifier", "id", "recordId")
TITLE_KEYS = ("title", "name", "label", "objectName", "type")
OBJECT_KEYS = ("objectClass", "objectType", "classification", "type", "object")
MATERIAL_KEYS = ("material", "materials", "medium", "substance")
PERIOD_KEYS = ("period", "chronology", "date", "dating", "temporal")
REPOSITORY_KEYS = ("repository", "institution", "museum", "currentLocation")
FINDSPOT_KEYS = ("findspot", "findPlace", "place", "location", "provenience")
CONTEXT_KEYS = ("context", "findContext", "excavationContext", "stratigraphy")
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
PRECIOUS_TERMS = {"gold", "electrum", "silver", "aureus", "solidus"}


def _string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, list):
        values = [item for item in (_string(item) for item in value) if item]
        return "; ".join(values) if values else None
    if isinstance(value, dict):
        for key in ("label", "name", "value", "@value", "id", "@id"):
            candidate = _string(value.get(key))
            if candidate:
                return candidate
        candidates = [
            candidate for candidate in (_string(item) for item in value.values()) if candidate
        ]
        if candidates:
            return "; ".join(candidates)
    return None


def _first(record: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    lowered = {str(key).casefold(): value for key, value in record.items()}
    for key in keys:
        candidate = _string(record.get(key))
        if candidate:
            return candidate
        candidate = _string(lowered.get(key.casefold()))
        if candidate:
            return candidate
    return None


def _flatten_xml(element: ET.Element) -> dict[str, Any]:
    values: dict[str, Any] = {}

    def append(key: str, value: str) -> None:
        if not value:
            return
        existing = values.get(key)
        if existing is None:
            values[key] = value
        elif isinstance(existing, list):
            existing.append(value)
        else:
            values[key] = [existing, value]

    for attribute, value in element.attrib.items():
        append(f"@{attribute.rsplit('}', 1)[-1]}", value.strip())
    for child in element.iter():
        if child is element:
            continue
        key = child.tag.rsplit("}", 1)[-1]
        value = (child.text or "").strip()
        append(key, value)
        for attribute, attribute_value in child.attrib.items():
            attribute_key = attribute.rsplit("}", 1)[-1]
            append(f"{key}.@{attribute_key}", attribute_value.strip())
            if not value and attribute_key in {"about", "resource", "href"}:
                append(key, attribute_value.strip())
    return values


def _records_from_json(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        records = value
    elif isinstance(value, dict):
        records = None
        sparql_results = value.get("results")
        if isinstance(sparql_results, dict) and isinstance(
            sparql_results.get("bindings"), list
        ):
            records = sparql_results["bindings"]
        message = value.get("message")
        if records is None and isinstance(message, dict) and isinstance(
            message.get("items"), list
        ):
            records = message["items"]
        for key in ("records", "results", "items", "features", "@graph"):
            if records is not None:
                break
            candidate = value.get(key)
            if isinstance(candidate, list):
                records = candidate
                break
        if records is None and isinstance(value.get("data"), list):
            records = value["data"]
        if records is None:
            records = [value]
    else:
        raise ValueError("JSON source must contain an object or array")
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"JSON record {index + 1} must be an object")
    return records


def _records_from_csv(payload: bytes) -> list[dict[str, Any]]:
    reader = csv.reader(io.StringIO(payload.decode("utf-8-sig")))
    try:
        header = next(reader)
    except StopIteration:
        return []
    header = [field.strip() for field in header]
    if not header or any(not field for field in header):
        raise ValueError("CSV headers must be non-empty")
    normalized = [field.casefold() for field in header]
    if len(set(normalized)) != len(normalized):
        raise ValueError("CSV headers must be unique")
    records: list[dict[str, Any]] = []
    for row_number, row in enumerate(reader, 2):
        if not row or all(not field.strip() for field in row):
            continue
        if len(row) != len(header):
            raise ValueError(f"CSV row {row_number} has {len(row)} fields; expected {len(header)}")
        records.append(dict(zip(header, row)))
    return records


def _shape_limits(value: Any, depth: int = 0) -> int:
    if depth > 64:
        raise ValueError("source structure exceeds maximum nesting depth")
    if isinstance(value, dict):
        count = 1 + sum(_shape_limits(item, depth + 1) for item in value.values())
    elif isinstance(value, list):
        count = 1 + sum(_shape_limits(item, depth + 1) for item in value)
    else:
        count = 1
    if count > 500_000:
        raise ValueError("source structure exceeds maximum value count")
    return count


def parse_records(payload: bytes, format_name: str) -> list[dict[str, Any]]:
    if format_name not in SUPPORTED_FORMATS:
        raise ValueError(f"unsupported source format: {format_name}")
    if format_name in {"json", "iiif", "sparql-json"}:
        value = json.loads(payload.decode("utf-8"))
        _shape_limits(value)
        if (
            format_name == "iiif"
            and isinstance(value, dict)
            and value.get("type") == "Manifest"
        ):
            return [value]
        if (
            format_name == "iiif"
            and isinstance(value, dict)
            and str(value.get("@type", "")).casefold().endswith("manifest")
        ):
            return [value]
        return _records_from_json(value)
    if format_name == "jsonl":
        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(payload.decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL line {line_number} must be an object")
            records.append(value)
        return records
    if format_name == "csv":
        return _records_from_csv(payload)
    root = safe_xml_root(payload)
    if format_name == "oai-pmh":
        records = []
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] != "record":
                continue
            header = next(
                (
                    child
                    for child in element
                    if child.tag.rsplit("}", 1)[-1] == "header"
                ),
                None,
            )
            if header is not None and header.attrib.get("status") == "deleted":
                continue
            records.append(_flatten_xml(element))
        return records
    descriptions = [
        element
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1] in {"Description", "NamedIndividual"}
    ]
    return [_flatten_xml(element) for element in descriptions] or [_flatten_xml(root)]


def pagination_metadata(payload: bytes, format_name: str) -> dict[str, Any]:
    if format_name != "oai-pmh":
        return {"sourceExhausted": True}
    root = safe_xml_root(payload)
    token = next(
        (
            element
            for element in root.iter()
            if element.tag.rsplit("}", 1)[-1] == "resumptionToken"
        ),
        None,
    )
    token_text = (token.text or "").strip() if token is not None else ""
    metadata: dict[str, Any] = {
        "sourceExhausted": not bool(token_text),
        "resumptionToken": token_text or None,
    }
    if token is not None:
        for key in ("cursor", "completeListSize", "expirationDate"):
            if key in token.attrib:
                metadata[key] = token.attrib[key]
    return metadata


def _public_host_problem(locator: str) -> str | None:
    return public_host_problem(locator)


def _read_bounded(locator: str, max_bytes: int) -> bytes:
    parsed = urlparse(locator)
    if parsed.scheme in {"http", "https"}:
        validate_public_url(locator)
        request = urllib.request.Request(
            locator,
            headers={"User-Agent": "Indiana-Jones-Archaeology-Research/1.0"},
        )
        opener = urllib.request.build_opener(ValidatingRedirectHandler())
        with opener.open(request, timeout=30) as response:
            final_url = response.geturl()
            validate_public_url(final_url)
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > max_bytes:
                raise ValueError("source exceeds max_bytes")
            payload = response.read(max_bytes + 1)
    elif parsed.scheme:
        raise ValueError("source locator must be a local path or http(s) URL")
    else:
        with Path(locator).open("rb") as stream:
            payload = stream.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise ValueError("source exceeds max_bytes")
    return payload


def _terms(record: dict[str, Any]) -> str:
    return " ".join(
        candidate.casefold()
        for candidate in (
            _first(record, TITLE_KEYS),
            _first(record, OBJECT_KEYS),
            _first(record, MATERIAL_KEYS),
            _first(record, CONTEXT_KEYS),
        )
        if candidate
    )


def normalize_record(
    record: dict[str, Any],
    *,
    source_id: str,
    index: int,
    sensitivity: str,
    origin_family_id: str | None = None,
) -> dict[str, Any]:
    title = _first(record, TITLE_KEYS) or f"catalogue record {index}"
    object_class = _first(record, OBJECT_KEYS) or "unclassified object or record"
    material = _first(record, MATERIAL_KEYS)
    chronology = _first(record, PERIOD_KEYS)
    repository = _first(record, REPOSITORY_KEYS)
    accession = _first(record, ID_KEYS)
    findspot = _first(record, FINDSPOT_KEYS)
    context = _first(record, CONTEXT_KEYS)
    terms = _terms(record)
    evidence_classes: list[str] = []
    risk_classes: list[str] = []
    if any(term in terms for term in PRODUCTION_TERMS):
        evidence_classes.append("material-production")
    if any(term in terms for term in PRECIOUS_TERMS):
        evidence_classes.append("precious-material-object")
        risk_classes.append("portable-high-value")
    if any(term in terms for term in WEAPON_TERMS):
        evidence_classes.append("weapon-or-fitting")
        risk_classes.append("weapon")
    if "hoard" in terms:
        evidence_classes.append("assemblage-or-hoard")
        risk_classes.extend(["hoard", "portable-high-value"])
    if any(term in terms for term in {"grave", "burial", "tomb", "funerary"}):
        risk_classes.append("burial")
    raw_hash = value_sha256(record)
    normalized = {
        "recordId": f"{source_id}:{accession or raw_hash[:20]}",
        "sourceId": source_id,
        "originFamilyId": origin_family_id or source_id,
        "sourceRecordId": accession,
        "title": title,
        "objectClass": object_class,
        "material": material,
        "chronology": {"label": chronology, "certainty": "reported"} if chronology else None,
        "archaeologicalContext": context,
        "findspot": (
            {
                "description": findspot,
                "precision": "source-reported-unknown",
                "sensitivity": "restricted" if sensitivity == "public" else sensitivity,
            }
            if findspot
            else None
        ),
        "repository": repository,
        "accessionNumber": accession,
        "evidenceClasses": sorted(set(evidence_classes)),
        "riskClasses": sorted(set(risk_classes)),
        "recordReliability": "unassessed",
        "rawRecordSha256": raw_hash,
        "normalizationVersion": NORMALIZATION_VERSION,
        "sensitivity": sensitivity,
    }
    return {key: value for key, value in normalized.items() if value is not None}


def acquire_and_normalize(
    *,
    source: dict[str, Any],
    locator: str,
    format_name: str,
    out: Path,
    max_bytes: int = 10_000_000,
    max_records: int = 5_000,
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if max_bytes < 1 or max_bytes > 100_000_000:
        raise ValueError("max_bytes must be between 1 and 100000000")
    if max_records < 1 or max_records > 100_000:
        raise ValueError("max_records must be between 1 and 100000")
    source_id = source.get("sourceId")
    if not isinstance(source_id, str) or not source_id:
        raise ValueError("source.sourceId is required")
    if source.get("accessBasis") != "public":
        raise ValueError("automated ingestion is limited to explicitly public sources")
    query_artifact = {} if query is None else query
    validate_query_artifact(query_artifact)
    payload = _read_bounded(locator, max_bytes)
    raw_path = out.with_suffix(out.suffix + ".raw")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("xb") as stream:
        stream.write(payload)
    records = parse_records(payload, format_name)
    truncated = len(records) > max_records
    records = records[:max_records]
    pagination = pagination_metadata(payload, format_name)
    if truncated:
        pagination["sourceExhausted"] = False
        pagination["stopReason"] = "local-record-limit"
    sensitivity = source.get("sensitivity", "restricted")
    normalized = [
        normalize_record(
            record,
            source_id=source_id,
            index=index,
            sensitivity=sensitivity,
            origin_family_id=source.get("originFamilyId"),
        )
        for index, record in enumerate(records, 1)
    ]
    artifact = {
        "schemaVersion": "archaeological-find-records-1.0",
        "queryArtifact": {
            "sourceId": source_id,
            "adapter": format_name,
            "locator": locator,
            "query": query_artifact,
            "pagination": pagination,
            "retrievedAt": time.time(),
            "accessBasis": source.get("accessBasis"),
            "license": source.get("license"),
            "providerTerms": source.get("providerTerms", "verify source terms"),
            "rawArtifactPath": raw_path.name,
            "rawArtifactSha256": file_sha256(raw_path),
            "rawBytes": len(payload),
            "resultCount": len(normalized),
            "truncated": truncated,
            "maxRecords": max_records,
            "normalizationVersion": NORMALIZATION_VERSION,
        },
        "records": normalized,
    }
    with out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(artifact, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    return artifact


def _identity_key(record: dict[str, Any]) -> tuple[str, ...]:
    accession = _string(record.get("accessionNumber"))
    repository = _string(record.get("repository"))
    if accession and repository:
        return ("accession", repository.casefold(), accession.casefold())
    source_record = _string(record.get("sourceRecordId"))
    source_id = _string(record.get("sourceId"))
    if source_record and source_id:
        return ("source-record", source_id.casefold(), source_record.casefold())
    return ("unique", _string(record.get("recordId")) or value_sha256(record))


def _conservative_canonical(
    records: list[dict[str, Any]],
    conflicts: dict[str, list[Any]],
) -> tuple[dict[str, Any], str]:
    if len(records) == 1:
        return dict(records[0]), "single-record"
    provenance_fields = {
        "recordId",
        "sourceId",
        "originFamilyId",
        "rawRecordSha256",
    }
    shared_keys = set(records[0]).intersection(*(set(record) for record in records[1:]))
    canonical: dict[str, Any] = {}
    for field in sorted(shared_keys - provenance_fields - set(conflicts)):
        encoded = {
            json.dumps(record[field], ensure_ascii=False, sort_keys=True)
            for record in records
        }
        if len(encoded) == 1:
            canonical[field] = records[0][field]
    return canonical, "unresolved-conflicts" if conflicts else "consensus"


def reconcile_artifacts(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    clusters: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for artifact in artifacts:
        records = artifact.get("records")
        if not isinstance(records, list):
            raise ValueError("find artifact records must be an array")
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("find artifact records must contain objects")
            clusters.setdefault(_identity_key(record), []).append(record)
    reconciled: list[dict[str, Any]] = []
    for key, records in sorted(clusters.items()):
        records = sorted(
            records,
            key=lambda record: (
                str(record.get("sourceId", "")),
                str(record.get("rawRecordSha256", "")),
            ),
        )
        source_ids = sorted(
            {str(record.get("sourceId")) for record in records if record.get("sourceId")}
        )
        origin_families = sorted(
            {
                str(record.get("originFamilyId"))
                for record in records
                if record.get("originFamilyId")
            }
        )
        origin_hashes = sorted(
            {
                str(record.get("rawRecordSha256"))
                for record in records
                if record.get("rawRecordSha256")
            }
        )
        conflict_fields: dict[str, list[Any]] = {}
        for field in (
            "title",
            "objectClass",
            "material",
            "chronology",
            "archaeologicalContext",
            "findspot",
            "repository",
            "accessionNumber",
            "evidenceClasses",
            "riskClasses",
            "recordReliability",
            "sensitivity",
        ):
            values = {
                json.dumps(record[field], ensure_ascii=False, sort_keys=True)
                for record in records
                if field in record
            }
            if len(values) > 1:
                conflict_fields[field] = [json.loads(value) for value in sorted(values)]
        canonical_record, canonical_status = _conservative_canonical(
            records,
            conflict_fields,
        )
        reconciled.append(
            {
                "entityId": f"find_{value_sha256(list(key))[:24]}",
                "identityBasis": key[0],
                "canonicalRecord": canonical_record,
                "canonicalStatus": canonical_status,
                "recordIds": sorted(str(record.get("recordId")) for record in records),
                "sourceIds": source_ids,
                "originFamilyIds": origin_families,
                "originRecordHashes": origin_hashes,
                "duplicateCount": len(records),
                "independentSourceCount": len(origin_families),
                "reconciliationStatus": (
                    "contested-identifier-match"
                    if key[0] == "accession" and conflict_fields
                    else "strong-identifier-match"
                    if key[0] == "accession"
                    else "not-merged"
                ),
                "fieldConflicts": conflict_fields,
            }
        )
    return {
        "schemaVersion": "archaeological-find-reconciliation-1.0",
        "entityCount": len(reconciled),
        "recordCount": sum(len(items) for items in clusters.values()),
        "entities": reconciled,
    }


def discover_source_candidates(
    plan: dict[str, Any],
    *,
    record_types: set[str] | None = None,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for source in plan.get("sources", []):
        if not isinstance(source, dict):
            continue
        if record_types and source.get("recordType") not in record_types:
            continue
        acquisition = source.get("acquisition")
        adapter = acquisition.get("format") if isinstance(acquisition, dict) else None
        candidates.append(
            {
                "sourceId": source.get("sourceId"),
                "title": source.get("title"),
                "recordType": source.get("recordType"),
                "accessBasis": source.get("accessBasis"),
                "license": source.get("license"),
                "sensitivity": source.get("sensitivity"),
                "adapter": adapter,
                "executable": (
                    source.get("accessBasis") == "public"
                    and adapter in SUPPORTED_FORMATS
                    and isinstance(acquisition.get("locator"), str)
                    if isinstance(acquisition, dict)
                    else False
                ),
                "authorizationRequired": source.get("accessBasis") != "public",
            }
        )
    return {
        "schemaVersion": "archaeological-source-discovery-1.0",
        "candidateCount": len(candidates),
        "implicitAuthorization": False,
        "candidates": candidates,
    }


def acquisition_binding_errors(plan: dict[str, Any]) -> list[str]:
    source_map = {
        source.get("sourceId"): source
        for source in plan.get("sources", [])
        if isinstance(source, dict) and isinstance(source.get("sourceId"), str)
    }
    errors: list[str] = []
    for action in plan.get("actions", []):
        if not isinstance(action, dict) or action.get("status") != "planned":
            continue
        spec = action.get("execution", {})
        inputs = spec.get("inputs", {}) if isinstance(spec, dict) else {}
        if spec.get("executor") != "ingest-source" or not isinstance(inputs, dict):
            continue
        source = source_map.get(inputs.get("sourceId"), {})
        acquisition = source.get("acquisition")
        if not isinstance(acquisition, dict):
            errors.append(f"action {action.get('actionId')} source lacks acquisition")
        elif any(acquisition.get(key) != inputs.get(key) for key in ("locator", "format")):
            errors.append(f"action {action.get('actionId')} acquisition does not match source")
    return errors


def assessment_summary(reconciliation: dict[str, Any]) -> dict[str, Any]:
    entities = reconciliation.get("entities", [])
    source_ids = {
        source_id
        for entity in entities
        if isinstance(entity, dict)
        for source_id in entity.get("sourceIds", [])
    }
    assessed = [
        entity
        for entity in entities
        if isinstance(entity, dict)
        and entity.get("canonicalRecord", {}).get("recordReliability") != "unassessed"
    ]
    return {
        "assessmentVersion": "non-probabilistic-v1",
        "answerability": "supported" if entities else "no-records-in-searched-sources",
        "sourceCoverage": {
            "distinctSources": len(source_ids),
            "note": "Coverage is limited to ingested sources and is not a completeness claim.",
        },
        "recordReliability": {
            "assessedEntities": len(assessed),
            "unassessedEntities": len(entities) - len(assessed),
        },
        "associationStrength": "requires claim-specific scholarly assessment",
        "probability": None,
        "probabilityReason": (
            "No calibrated representative detection model or base rate was supplied."
        ),
    }
