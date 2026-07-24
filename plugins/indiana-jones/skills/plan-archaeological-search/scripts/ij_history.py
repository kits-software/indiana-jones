from __future__ import annotations

from typing import Any


HISTORY_KINDS = {"phase", "event", "process", "social-context"}
HISTORY_RELATIONS = {
    "historically-precedes",
    "may-precede",
    "overlaps-in-time",
    "part-of",
}
BIOGRAPHY_KINDS = {
    "object",
    "find-event",
    "assemblage",
    "repository",
    "custody-event",
    "analysis",
}
BIOGRAPHY_RELATIONS = {
    "found-at",
    "recovered-in",
    "member-of",
    "made-of",
    "typed-as",
    "dated-by",
    "analysed-by",
    "held-by",
    "custody-before",
    "same-object-as",
    "possibly-same-as",
    "catalogued-as",
    "published-as",
}


def _node_view(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "nodeId": node.get("nodeId"),
        "kind": node.get("kind"),
        "label": node.get("label"),
        "authority": node.get("authority"),
        "chronology": node.get("chronology"),
        "sourceIds": sorted(node.get("sourceIds", [])),
        "sensitivity": node.get("sensitivity"),
    }

def _ordered_history_nodes(
    nodes: list[dict[str, Any]], edges: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    node_map = {node["nodeId"]: node for node in nodes}
    indegree = {node_id: 0 for node_id in node_map}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in node_map}
    for edge in edges:
        if edge.get("relation") != "historically-precedes":
            continue
        source = edge.get("from")
        target = edge.get("to")
        if source in node_map and target in node_map:
            outgoing[source].append(target)
            indegree[target] += 1
    ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
    ordered: list[str] = []
    while ready:
        node_id = ready.pop(0)
        ordered.append(node_id)
        for target in sorted(outgoing[node_id]):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
                ready.sort()
    if len(ordered) != len(node_map):
        raise ValueError("historical sequence contains a cycle")
    return [node_map[node_id] for node_id in ordered]


def build_history_report(plan: dict[str, Any]) -> dict[str, Any]:
    nodes = [
        node
        for node in plan.get("nodes", [])
        if isinstance(node, dict) and node.get("kind") in HISTORY_KINDS
    ]
    edges = [
        edge
        for edge in plan.get("edges", [])
        if isinstance(edge, dict)
        and edge.get("relation") in HISTORY_RELATIONS
        and edge.get("from") in {node.get("nodeId") for node in nodes}
        and edge.get("to") in {node.get("nodeId") for node in nodes}
    ]
    ordered = _ordered_history_nodes(nodes, edges)
    contradictions = [
        {
            "edgeId": edge.get("edgeId"),
            "from": edge.get("from"),
            "to": edge.get("to"),
            "sourceIds": sorted(edge.get("sourceIds", [])),
            "rationale": edge.get("rationale"),
        }
        for edge in plan.get("edges", [])
        if isinstance(edge, dict) and edge.get("relation") == "contradicts"
    ]
    all_sources = {
        source_id
        for node in nodes
        for source_id in node.get("sourceIds", [])
        if isinstance(source_id, str)
    }
    return {
        "schemaVersion": "archaeological-history-report-1.0",
        "area": plan.get("area", {}).get("publicDescription"),
        "sequenceAuthority": (
            "documentary and interpretive history; not a Harris stratigraphic matrix"
        ),
        "timeSlices": [_node_view(node) for node in ordered],
        "relations": [
            {
                "edgeId": edge.get("edgeId"),
                "from": edge.get("from"),
                "to": edge.get("to"),
                "relation": edge.get("relation"),
                "authority": edge.get("authority"),
                "sourceIds": sorted(edge.get("sourceIds", [])),
            }
            for edge in edges
        ],
        "contradictions": contradictions,
        "sourceCoverage": {
            "declaredSourceCount": len(plan.get("sources", [])),
            "historySourceCount": len(all_sources),
            "note": "Coverage describes declared sources, not historical completeness.",
        },
        "gaps": (
            ["No sourced historical phase, event, or process nodes were available."]
            if not ordered
            else []
        ),
    }


def build_object_biography(plan: dict[str, Any], object_node_id: str) -> dict[str, Any]:
    node_map = {
        node.get("nodeId"): node
        for node in plan.get("nodes", [])
        if isinstance(node, dict)
    }
    root = node_map.get(object_node_id)
    if root is None or root.get("kind") != "object":
        raise ValueError("object_node_id must identify an object node")
    relevant_ids = {object_node_id}
    relevant_edges: list[dict[str, Any]] = []
    changed = True
    while changed:
        changed = False
        for edge in plan.get("edges", []):
            if not isinstance(edge, dict) or edge.get("relation") not in BIOGRAPHY_RELATIONS:
                continue
            source = edge.get("from")
            target = edge.get("to")
            if source in relevant_ids or target in relevant_ids:
                relevant_edges.append(edge)
                for node_id in (source, target):
                    node = node_map.get(node_id)
                    if (
                        node
                        and node.get("kind") in BIOGRAPHY_KINDS
                        and node_id not in relevant_ids
                    ):
                        relevant_ids.add(node_id)
                        changed = True
    deduped_edges = {
        edge.get("edgeId"): edge for edge in relevant_edges if edge.get("edgeId")
    }
    return {
        "schemaVersion": "archaeological-object-biography-1.0",
        "object": _node_view(root),
        "relatedEntities": [
            _node_view(node_map[node_id])
            for node_id in sorted(relevant_ids - {object_node_id})
        ],
        "relationships": [
            {
                "edgeId": edge.get("edgeId"),
                "from": edge.get("from"),
                "to": edge.get("to"),
                "relation": edge.get("relation"),
                "authority": edge.get("authority"),
                "sourceIds": sorted(edge.get("sourceIds", [])),
            }
            for edge in sorted(
                deduped_edges.values(), key=lambda item: str(item.get("edgeId"))
            )
        ],
        "provenanceWarning": (
            "Archaeological provenience, evidence lineage, and collection custody "
            "remain separate authorities."
        ),
    }
