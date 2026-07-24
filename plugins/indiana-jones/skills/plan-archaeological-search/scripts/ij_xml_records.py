from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any


def _append(values: dict[str, Any], key: str, value: str) -> None:
    if not value:
        return
    existing = values.get(key)
    if existing is None:
        values[key] = value
    elif isinstance(existing, list):
        existing.append(value)
    else:
        values[key] = [existing, value]


def flatten_xml(element: ET.Element) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for attribute, value in element.attrib.items():
        _append(values, f"@{attribute.rsplit('}', 1)[-1]}", value.strip())
    for child in element.iter():
        if child is element:
            continue
        key = child.tag.rsplit("}", 1)[-1]
        value = (child.text or "").strip()
        _append(values, key, value)
        for attribute, attribute_value in child.attrib.items():
            attribute_key = attribute.rsplit("}", 1)[-1]
            _append(values, f"{key}.@{attribute_key}", attribute_value.strip())
            if not value and attribute_key in {"about", "resource", "href"}:
                _append(values, key, attribute_value.strip())
    return values


def oai_records(root: ET.Element) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "record":
            continue
        header = next(
            (child for child in element if child.tag.rsplit("}", 1)[-1] == "header"),
            None,
        )
        if (
            header is not None
            and str(header.attrib.get("status", "")).casefold() == "deleted"
        ):
            continue
        metadata = next(
            (child for child in element if child.tag.rsplit("}", 1)[-1] == "metadata"),
            None,
        )
        record = flatten_xml(metadata) if metadata is not None else {}
        if header is not None:
            for child in header.iter():
                if child is header:
                    continue
                key = child.tag.rsplit("}", 1)[-1]
                value = (child.text or "").strip()
                if value:
                    _append(record, f"oai{key[:1].upper()}{key[1:]}", value)
        records.append(record)
    return records


def oai_pagination(root: ET.Element) -> dict[str, Any]:
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
