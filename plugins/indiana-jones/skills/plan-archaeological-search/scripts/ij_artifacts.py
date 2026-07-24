from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


COORDINATE_TEXT = re.compile(
    r"(?<![\d.])-?(?:[1-8]?\d(?:\.\d{4,})|90(?:\.0+)?)"
    r"\s*[,;/]\s*"
    r"-?(?:1[0-7]\d(?:\.\d{4,})?|[1-9]?\d(?:\.\d{4,})?|180(?:\.0+)?)"
)


def _objects(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("plan root must be a JSON object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output:
        output.write(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def canonical_plan(plan: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(plan)
    sortable = {
        "sources": "sourceId",
        "nodes": "nodeId",
        "edges": "edgeId",
        "actions": "actionId",
    }
    for key, id_key in sortable.items():
        values = normalized.get(key)
        if isinstance(values, list):
            values.sort(
                key=lambda item: str(item.get(id_key, ""))
                if isinstance(item, dict)
                else str(item)
            )
    grid = normalized.get("grid")
    cells = grid.get("cells") if isinstance(grid, dict) else None
    if isinstance(cells, list):
        cells.sort(
            key=lambda item: str(item.get("cellId", ""))
            if isinstance(item, dict)
            else str(item)
        )

    for source in _objects(normalized.get("sources")):
        if isinstance(source.get("aliases"), list):
            source["aliases"] = sorted(source["aliases"], key=str)
    for node in _objects(normalized.get("nodes")):
        for key in ("sourceIds", "cellIds", "notes"):
            if isinstance(node.get(key), list):
                node[key] = sorted(node[key], key=str)
    for edge in _objects(normalized.get("edges")):
        if isinstance(edge.get("sourceIds"), list):
            edge["sourceIds"] = sorted(edge["sourceIds"], key=str)
    for action in _objects(normalized.get("actions")):
        for key in (
            "sourceIds",
            "hypothesisIds",
            "cellIds",
            "prerequisites",
        ):
            if isinstance(action.get(key), list):
                action[key] = sorted(action[key], key=str)
        authorization = action.get("authorization", {})
        if isinstance(authorization, dict) and isinstance(
            authorization.get("approvalReferences"), list
        ):
            authorization["approvalReferences"] = sorted(
                authorization["approvalReferences"], key=str
            )
    for cell in _objects(cells):
        for key in ("neighbors", "landscapeContext"):
            if isinstance(cell.get(key), list):
                cell[key] = sorted(cell[key], key=str)
    case = normalized.get("case")
    case_authorization = case.get("authorization", {}) if isinstance(case, dict) else {}
    if isinstance(case_authorization, dict) and isinstance(
        case_authorization.get("authenticatedPlatforms"), list
    ):
        case_authorization["authenticatedPlatforms"] = sorted(
            case_authorization["authenticatedPlatforms"], key=str
        )
    return normalized


def plan_sha256(plan: dict[str, Any]) -> str:
    payload = json.dumps(
        canonical_plan(plan),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def public_export(plan: dict[str, Any]) -> dict[str, Any]:
    plan = canonical_plan(plan)
    source_hash = plan_sha256(plan)
    sources = _objects(plan.get("sources"))
    nodes = _objects(plan.get("nodes"))
    edges = _objects(plan.get("edges"))
    actions = _objects(plan.get("actions"))
    grid = plan.get("grid") if isinstance(plan.get("grid"), dict) else {}
    cells = _objects(grid.get("cells"))
    case = plan.get("case") if isinstance(plan.get("case"), dict) else {}
    area = plan.get("area") if isinstance(plan.get("area"), dict) else {}
    policy = plan.get("policy") if isinstance(plan.get("policy"), dict) else {}
    source_ids = {
        source.get("sourceId"): f"source_{index:03d}"
        for index, source in enumerate(sources, start=1)
    }
    node_ids = {
        node.get("nodeId"): f"node_{index:03d}"
        for index, node in enumerate(nodes, start=1)
    }
    exported_sources: list[dict[str, Any]] = []
    for source in sources:
        is_public = (
            source.get("sensitivity") == "public"
            and source.get("accessBasis") == "public"
        )
        public_source = {
            "sourceId": source_ids[source.get("sourceId")],
            "title": source.get("title") if is_public else "withheld source",
            "workflowRole": source.get("workflowRole"),
            "recordType": source.get("recordType"),
            "sensitivity": "public" if is_public else "withheld",
        }
        if is_public and source.get("url"):
            public_source["url"] = source["url"]
            public_source["license"] = source.get("license")
        exported_sources.append(public_source)

    exported_nodes: list[dict[str, Any]] = []
    for node in nodes:
        sensitive = node.get("sensitivity") != "public"
        exported_nodes.append(
            {
                "nodeId": node_ids[node.get("nodeId")],
                "kind": node.get("kind"),
                "authority": node.get("authority"),
                "label": (
                    "generalized sensitive research entity"
                    if sensitive
                    else node.get("label")
                ),
                "sensitivity": "withheld" if sensitive else "public",
            }
        )

    exported_edges = [
        {
            "edgeId": f"edge_{index:03d}",
            "from": node_ids[edge.get("from")],
            "to": node_ids[edge.get("to")],
            "relation": edge.get("relation"),
            "authority": edge.get("authority"),
        }
        for index, edge in enumerate(edges, start=1)
        if edge.get("from") in node_ids and edge.get("to") in node_ids
    ]
    exported_actions: list[dict[str, Any]] = []
    for index, action in enumerate(actions, start=1):
        sensitive = (
            action.get("method") == "sensitive-findspot-assessment"
            or action.get("outputPrecision") in {"restricted-exact", "public-exact"}
            or bool(action.get("sensitiveSubjects"))
        )
        public_action = {
            "actionId": f"action_{index:03d}",
            "label": (
                "generalized sensitive research action"
                if sensitive
                else f"{action.get('method')} research action"
            ),
            "lane": action.get("lane"),
            "stage": action.get("stage"),
            "status": action.get("status"),
            "sensitivity": "withheld" if sensitive else "public",
        }
        if not sensitive:
            public_action["method"] = action.get("method")
            public_action["actionClass"] = action.get("actionClass")
        exported_actions.append(public_action)
    exported_cells = [
        {
            "cellId": f"sector_{index:03d}",
            "publicLabel": (
                cell.get("publicLabel")
                if cell.get("sensitivity") == "public"
                else "generalized study sector"
            ),
            "level": cell.get("level"),
            "coverageState": cell.get("coverageState"),
            "sensitivity": (
                "public" if cell.get("sensitivity") == "public" else "withheld"
            ),
        }
        for index, cell in enumerate(cells, start=1)
    ]
    public_description = area.get("publicDescription")
    if not isinstance(public_description, str) or COORDINATE_TEXT.search(
        public_description
    ):
        public_description = "generalized study area"
    return {
        "schemaVersion": "1.0-public",
        "case": {
            "studyKind": case.get("studyKind"),
            "disclosure": "public",
        },
        "area": {
            "publicDescription": public_description,
            "gridMethod": area.get("gridMethod"),
        },
        "grid": {
            "strategy": grid.get("strategy"),
            "cells": exported_cells,
        },
        "sources": exported_sources,
        "nodes": exported_nodes,
        "edges": exported_edges,
        "actions": exported_actions,
        "policy": {
            "scoreVersion": policy.get("scoreVersion"),
            "lanePattern": policy.get("lanePattern"),
            "stoppingRules": policy.get("stoppingRules"),
        },
        "publicExport": {
            "exportedFromSha256": source_hash,
            "coordinatePolicy": (
                "allowlist-built export omits all restricted geometry and locators"
            ),
        },
    }
