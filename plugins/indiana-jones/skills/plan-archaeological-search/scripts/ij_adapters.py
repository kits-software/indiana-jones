from __future__ import annotations

from typing import Any


ADAPTER_REGISTRY: dict[str, dict[str, Any]] = {
    "json": {
        "version": "1.0.0",
        "capabilities": ["bounded-read", "strict-object-records"],
        "pagination": "none",
    },
    "jsonl": {
        "version": "1.0.0",
        "capabilities": ["bounded-read", "strict-line-records"],
        "pagination": "none",
    },
    "csv": {
        "version": "1.0.0",
        "capabilities": ["bounded-read", "strict-tabular-shape"],
        "pagination": "none",
    },
    "oai-pmh": {
        "version": "1.0.0",
        "capabilities": ["bounded-read", "resumption-token", "deleted-record-filter"],
        "pagination": "resumption-token",
    },
    "iiif": {
        "version": "1.0.0",
        "capabilities": ["bounded-read", "manifest-metadata"],
        "pagination": "none",
    },
    "rdf-xml": {
        "version": "1.0.0",
        "capabilities": ["bounded-read", "dtd-disabled", "attribute-preservation"],
        "pagination": "none",
    },
    "sparql-json": {
        "version": "1.0.0",
        "capabilities": ["bounded-read", "binding-preservation"],
        "pagination": "none",
    },
    "crossref-json": {
        "version": "1.0.0",
        "capabilities": ["bounded-read", "scholarly-metadata", "doi-preservation"],
        "pagination": "none",
    },
    "openalex-json": {
        "version": "1.0.0",
        "capabilities": ["bounded-read", "scholarly-metadata", "work-id-preservation"],
        "pagination": "none",
    },
    "doi-json": {
        "version": "1.0.0",
        "capabilities": ["bounded-read", "scholarly-metadata", "doi-preservation"],
        "pagination": "none",
    },
}


def adapter_descriptor(format_name: str) -> dict[str, Any]:
    descriptor = ADAPTER_REGISTRY.get(format_name)
    if descriptor is None:
        raise ValueError(f"unsupported source format: {format_name}")
    return {
        "format": format_name,
        "version": descriptor["version"],
        "capabilities": list(descriptor["capabilities"]),
        "pagination": descriptor["pagination"],
        "retention": "raw-snapshot-required",
    }
