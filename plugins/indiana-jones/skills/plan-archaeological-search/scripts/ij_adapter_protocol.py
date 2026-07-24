from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from ij_adapters import adapter_descriptor
from ij_artifacts import read_json
from ij_journal import file_sha256, value_sha256
from ij_source_contract import acquisition_contract, verify_source_acquisition


DEFAULT_BROADER_TERMS = {
    "sword": ("weapon", "blade", "scabbard", "hilt", "iron"),
    "weapon": ("arms", "blade", "military equipment", "iron"),
    "gold": ("precious metal", "aurum", "gilded object", "bullion"),
    "coin": ("coinage", "numismatic", "currency", "monetary deposit"),
    "hoard": ("deposit", "cache", "assemblage", "coin deposit"),
    "treasure": ("hoard", "cache", "valuables", "precious metal"),
}


def build_search_ladder(
    *,
    place_aliases: list[str],
    object_terms: list[str],
    language_variants: list[str] | None = None,
    broader_terms: list[str] | None = None,
    maximum: int = 100,
) -> list[dict[str, Any]]:
    if not 1 <= maximum <= 1_000:
        raise ValueError("maximum search-ladder queries must be between 1 and 1000")
    aliases = sorted({value.strip() for value in place_aliases if value.strip()})
    objects = sorted({value.strip() for value in object_terms if value.strip()})
    languages = sorted(
        {value.strip() for value in language_variants or [] if value.strip()}
    )
    expanded_broader = {
        term
        for value in objects
        for term in DEFAULT_BROADER_TERMS.get(value.casefold(), ())
    }
    expanded_broader.update(
        value.strip() for value in broader_terms or [] if value.strip()
    )
    broader = sorted(expanded_broader)
    if not aliases or not objects:
        raise ValueError("search ladder requires place aliases and object terms")
    queries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for stage, terms in (
        ("exact-name-and-class", objects),
        ("historical-and-local-language-variants", languages),
        ("broader-object-and-material-terms", broader),
    ):
        for place in aliases:
            for term in terms:
                key = f"{place.casefold()}\x1f{term.casefold()}"
                if key in seen:
                    continue
                seen.add(key)
                queries.append(
                    {
                        "queryId": f"query_{value_sha256([stage, place, term])[:20]}",
                        "stage": stage,
                        "place": place,
                        "term": term,
                    }
                )
                if len(queries) == maximum:
                    return queries
    return queries


def _verified_checkpoint(
    previous: dict[str, Any],
    source: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if previous.get("schemaVersion") != "archaeological-find-records-1.0":
        raise ValueError("resume input must be a normalized find artifact")
    query = previous.get("queryArtifact")
    if not isinstance(query, dict) or query.get("sourceId") != source.get("sourceId"):
        raise ValueError("resume checkpoint does not match the declared source")
    checkpoint = query.get("checkpoint")
    if not isinstance(checkpoint, dict):
        raise ValueError("resume input lacks a checkpoint")
    expected = {
        "sourceId": query.get("sourceId"),
        "adapter": query.get("adapter"),
        "adapterVersion": query.get("adapterVersion"),
        "query": query.get("query"),
        "rawArtifactSha256": query.get("rawArtifactSha256"),
        "pagination": query.get("pagination"),
    }
    if checkpoint.get("checkpointId") != value_sha256(expected):
        raise ValueError("resume checkpoint is stale or has been altered")
    if checkpoint.get("querySha256") != value_sha256(query.get("query")):
        raise ValueError("resume checkpoint query hash is stale")
    if checkpoint.get("sourceExhausted") is True:
        raise ValueError("source is exhausted; no continuation is available")
    cursor = checkpoint.get("resumeCursor")
    if not isinstance(cursor, str) or not cursor:
        raise ValueError("resume checkpoint lacks a provider cursor")
    descriptor = adapter_descriptor(str(query.get("adapter")))
    if descriptor["version"] != query.get("adapterVersion"):
        raise ValueError("resume checkpoint adapter version is stale")
    if (
        descriptor["format"] != "oai-pmh"
        or descriptor["pagination"] != "resumption-token"
    ):
        raise ValueError("restartable acquisition is implemented only for OAI-PMH")
    return query, checkpoint


def resume_acquisition(
    *,
    previous_artifact: Path,
    source: dict[str, Any],
    out: Path,
    max_bytes: int = 10_000_000,
    max_records: int = 5_000,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    previous = read_json(previous_artifact)
    query, checkpoint = _verified_checkpoint(previous, source)
    acquisition = source.get("acquisition")
    pages = acquisition.get("resumePages") if isinstance(acquisition, dict) else None
    if not isinstance(pages, list):
        raise ValueError("source acquisition lacks declared resumePages")
    cursor = checkpoint["resumeCursor"]
    page = next(
        (
            item
            for item in pages
            if isinstance(item, dict) and item.get("cursor") == cursor
        ),
        None,
    )
    if page is None:
        raise ValueError("provider cursor is not declared in resumePages")
    locator = page.get("locator")
    if not isinstance(locator, str) or not locator:
        raise ValueError("resume page locator is invalid")
    format_name = str(query.get("adapter"))
    next_query = {
        "verb": "ListRecords",
        "resumptionToken": cursor,
        "previousCheckpointId": checkpoint["checkpointId"],
    }
    resumed_source = copy.deepcopy(source)
    resumed_source["acquisition"] = acquisition_contract(
        resumed_source,
        locator=locator,
        format_name=format_name,
        query=next_query,
        snapshot_sha256=page.get("snapshotSha256"),
        retrieved_at=page.get("retrievedAt"),
    )
    verify_source_acquisition(
        resumed_source,
        actual_locator=locator,
        inputs={
            "sourceId": source.get("sourceId"),
            "locator": locator,
            "format": format_name,
            "query": next_query,
        },
    )
    from ij_ingest import acquire_and_normalize

    artifact = acquire_and_normalize(
        source=resumed_source,
        locator=locator,
        format_name=format_name,
        out=out,
        max_bytes=max_bytes,
        max_records=max_records,
        query=next_query,
        timeout_seconds=timeout_seconds,
    )
    if file_sha256(previous_artifact) == file_sha256(out):
        raise ValueError("resume produced an identical page artifact")
    return artifact
