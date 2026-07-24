from __future__ import annotations

import copy
from typing import Any

from ij_spatial import add_google_maps_links


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
    "excavation-context",
    "assemblage",
    "collection",
    "repository",
    "custody-event",
    "analysis",
    "catalogue-record",
    "publication-record",
}
BIOGRAPHY_RELATIONS = {
    "found-at",
    "recovered-during",
    "recovered-in",
    "member-of",
    "member-of-assemblage",
    "made-of",
    "typed-as",
    "dated-to",
    "dated-by",
    "analysed-by",
    "held-by",
    "repository-of",
    "has-custody-event",
    "custody-transferred-to",
    "custody-before",
    "same-object-as",
    "possibly-same-as",
    "catalogued-as",
    "published-as",
}
MATERIAL_KINDS = {
    "object",
    "find-event",
    "assemblage",
    "collection",
    "repository",
    "analysis",
    "custody-event",
    "production-evidence",
    "catalogue-record",
    "publication-record",
}


def _strings(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted(
        {
            value
            for value in values
            if isinstance(value, str) and value.strip()
        }
    )


def _source_catalog(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        source["sourceId"]: source
        for source in plan.get("sources", [])
        if isinstance(source, dict)
        and isinstance(source.get("sourceId"), str)
        and source["sourceId"]
    }


def _citations(
    source_ids: Any,
    catalog: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    ids = _strings(source_ids)
    references = []
    origin_families = set()
    for source_id in ids:
        source = catalog.get(source_id, {})
        origin_family_id = source.get("originFamilyId")
        if isinstance(origin_family_id, str) and origin_family_id:
            origin_families.add(origin_family_id)
        references.append(
            {
                "sourceId": source_id,
                "title": source.get("title"),
                "originFamilyId": origin_family_id,
                "recordType": source.get("recordType"),
            }
        )
    return {
        "sourceIds": ids,
        "originFamilyIds": sorted(origin_families),
        "references": references,
    }


def _classification_and_dating(node: dict[str, Any]) -> dict[str, Any]:
    record = node.get("record")
    record = record if isinstance(record, dict) else {}
    date_interval = record.get("dateInterval")
    interval_basis = (
        date_interval.get("basis") if isinstance(date_interval, dict) else None
    )
    chronology = copy.deepcopy(node.get("chronology"))
    chronology_basis = (
        chronology.get("basis") if isinstance(chronology, dict) else None
    )
    return {
        "classification": copy.deepcopy(
            record.get("objectClass") or record.get("assemblageType")
        ),
        "classificationBasis": copy.deepcopy(record.get("classificationBasis")),
        "chronology": chronology or copy.deepcopy(date_interval),
        "datingBasis": copy.deepcopy(
            record.get("datingBasis") or interval_basis or chronology_basis
        ),
    }


def _context_and_provenience(node: dict[str, Any]) -> dict[str, Any]:
    record = node.get("record")
    record = record if isinstance(record, dict) else {}
    return {
        "contextQuality": copy.deepcopy(
            record.get("contextQuality", "unassessed")
        ),
        "identityStatus": copy.deepcopy(record.get("identityStatus")),
        "sourceNativeIds": copy.deepcopy(record.get("sourceNativeIds", [])),
        "recordNotes": copy.deepcopy(record.get("notes")),
    }


def _node_view(
    node: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    view = {
        "nodeId": node.get("nodeId"),
        "kind": node.get("kind"),
        "label": node.get("label"),
        "authority": node.get("authority"),
        "chronology": copy.deepcopy(node.get("chronology")),
        "coordinate": copy.deepcopy(node.get("coordinate")),
        "locator": copy.deepcopy(node.get("locator")),
        "citations": _citations(node.get("sourceIds"), catalog),
        "sensitivity": node.get("sensitivity"),
        "record": copy.deepcopy(node.get("record")),
        "classificationAndDating": _classification_and_dating(node),
        "contextAndProvenience": _context_and_provenience(node),
    }
    return add_google_maps_links(
        {key: value for key, value in view.items() if value is not None}
    )


def _edge_view(
    edge: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "edgeId": edge.get("edgeId"),
        "from": edge.get("from"),
        "to": edge.get("to"),
        "relation": edge.get("relation"),
        "authority": edge.get("authority"),
        "rationale": edge.get("rationale"),
        "citations": _citations(edge.get("sourceIds"), catalog),
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


def _history_gaps(nodes: list[dict[str, Any]]) -> list[str]:
    if not nodes:
        return ["No sourced historical phase, event, or process nodes were available."]
    gaps = []
    for node in nodes:
        if not node.get("chronology"):
            gaps.append(f"{node.get('nodeId')}: chronology is not bounded")
        if not node.get("sourceIds"):
            gaps.append(f"{node.get('nodeId')}: no direct source citation is declared")
    return gaps


def build_history_report(plan: dict[str, Any]) -> dict[str, Any]:
    catalog = _source_catalog(plan)
    nodes = [
        node
        for node in plan.get("nodes", [])
        if isinstance(node, dict) and node.get("kind") in HISTORY_KINDS
    ]
    history_ids = {node.get("nodeId") for node in nodes}
    edges = [
        edge
        for edge in plan.get("edges", [])
        if isinstance(edge, dict)
        and edge.get("relation") in HISTORY_RELATIONS
        and edge.get("from") in history_ids
        and edge.get("to") in history_ids
    ]
    ordered = _ordered_history_nodes(nodes, edges)
    material_nodes = [
        node
        for node in plan.get("nodes", [])
        if isinstance(node, dict) and node.get("kind") in MATERIAL_KINDS
    ]
    material_ids = {node.get("nodeId") for node in material_nodes}
    evidence_edges = [
        edge
        for edge in plan.get("edges", [])
        if isinstance(edge, dict)
        and (
            edge.get("from") in history_ids
            and edge.get("to") in material_ids
            or edge.get("to") in history_ids
            and edge.get("from") in material_ids
        )
    ]
    contradictions = [
        _edge_view(edge, catalog)
        for edge in plan.get("edges", [])
        if isinstance(edge, dict) and edge.get("relation") == "contradicts"
    ]
    all_sources = {
        source_id
        for node in nodes
        for source_id in _strings(node.get("sourceIds"))
    }
    origin_families = {
        family_id
        for source_id in all_sources
        for family_id in _citations([source_id], catalog)["originFamilyIds"]
    }
    phase_views = []
    for node in ordered:
        node_id = node.get("nodeId")
        related = sorted(
            {
                edge.get("to") if edge.get("from") == node_id else edge.get("from")
                for edge in evidence_edges
                if edge.get("from") == node_id or edge.get("to") == node_id
            }
        )
        phase_view = _node_view(node, catalog)
        phase_view["relatedMaterialEvidenceIds"] = related
        phase_views.append(phase_view)
    return {
        "schemaVersion": "archaeological-history-report-2.0",
        "area": plan.get("area", {}).get("publicDescription"),
        "sequenceAuthority": (
            "documentary and interpretive history; not a Harris stratigraphic matrix"
        ),
        "timeSlices": phase_views,
        "relations": [_edge_view(edge, catalog) for edge in edges],
        "contradictions": contradictions,
        "materialEvidence": [
            _node_view(node, catalog)
            for node in sorted(
                material_nodes, key=lambda item: str(item.get("nodeId"))
            )
        ],
        "historyToMaterialLinks": [
            _edge_view(edge, catalog)
            for edge in sorted(
                evidence_edges, key=lambda item: str(item.get("edgeId"))
            )
        ],
        "sourceCoverage": {
            "declaredSourceCount": len(plan.get("sources", [])),
            "historySourceCount": len(all_sources),
            "historyOriginFamilyCount": len(origin_families),
            "historyNodeCount": len(nodes),
            "materialEvidenceNodeCount": len(material_nodes),
            "citationCoverage": {
                "citedHistoryNodeCount": sum(
                    bool(node.get("sourceIds")) for node in nodes
                ),
                "historyNodeDenominator": len(nodes),
            },
            "note": "Coverage describes declared sources, not historical completeness.",
        },
        "gaps": _history_gaps(ordered),
        "biasWarnings": [
            "Surviving records, excavation opportunity, collecting, and digitization shape the apparent history.",
            "A find date is not a deposition date, and an object is not evidence of local production by itself.",
        ],
        "absenceBoundary": (
            "An unrepresented phase means no phase record was assembled from the declared sources; it does not establish historical absence."
        ),
        "contactRoleSuggestions": [
            {
                "role": "landscape archaeologist or historical geographer",
                "instituteCapability": "phase synthesis, map regression, and settlement-process interpretation",
            },
            {
                "role": "museum or archaeological archive research unit",
                "instituteCapability": "object, excavation, publication, and collection-record reconciliation",
            },
        ],
    }


def _sequence_key(node: dict[str, Any]) -> tuple[str, str]:
    record = node.get("record")
    interval = record.get("dateInterval") if isinstance(record, dict) else None
    earliest = interval.get("earliest") if isinstance(interval, dict) else None
    return str(earliest or ""), str(node.get("nodeId", ""))


def _connected_biography(
    plan: dict[str, Any],
    node_map: dict[str, dict[str, Any]],
    root_id: str,
) -> tuple[set[str], dict[str, dict[str, Any]]]:
    relevant_ids = {root_id}
    relevant_edges: dict[str, dict[str, Any]] = {}
    changed = True
    while changed:
        changed = False
        for edge in plan.get("edges", []):
            if (
                not isinstance(edge, dict)
                or edge.get("relation") not in BIOGRAPHY_RELATIONS
            ):
                continue
            source = edge.get("from")
            target = edge.get("to")
            if source not in relevant_ids and target not in relevant_ids:
                continue
            edge_id = edge.get("edgeId")
            if isinstance(edge_id, str) and edge_id:
                relevant_edges[edge_id] = edge
            for node_id in (source, target):
                node = node_map.get(node_id)
                if (
                    node
                    and node.get("kind") in BIOGRAPHY_KINDS
                    and node_id not in relevant_ids
                ):
                    relevant_ids.add(node_id)
                    changed = True
    return relevant_ids, relevant_edges


def build_object_biography(plan: dict[str, Any], object_node_id: str) -> dict[str, Any]:
    catalog = _source_catalog(plan)
    node_map = {
        node.get("nodeId"): node
        for node in plan.get("nodes", [])
        if isinstance(node, dict)
    }
    root = node_map.get(object_node_id)
    if root is None or root.get("kind") != "object":
        raise ValueError("object_node_id must identify an object node")
    relevant_ids, relevant_edges = _connected_biography(
        plan, node_map, object_node_id
    )
    archaeological_kinds = {
        "object",
        "find-event",
        "excavation-context",
        "assemblage",
    }
    record_kinds = {
        "catalogue-record",
        "publication-record",
        "repository",
        "analysis",
        "custody-event",
        "collection",
    }
    relationships = [
        _edge_view(edge, catalog)
        for edge in sorted(
            relevant_edges.values(), key=lambda item: str(item.get("edgeId"))
        )
    ]
    return {
        "schemaVersion": "archaeological-object-biography-2.0",
        "object": _node_view(root, catalog),
        "relatedEntities": [
            _node_view(node_map[node_id], catalog)
            for node_id in sorted(relevant_ids - {object_node_id})
        ],
        "archaeologicalSequence": [
            _node_view(node_map[node_id], catalog)
            for node_id in sorted(
                (
                    node_id
                    for node_id in relevant_ids
                    if node_map[node_id].get("kind") in archaeological_kinds
                ),
                key=lambda node_id: _sequence_key(node_map[node_id]),
            )
        ],
        "recordAndCustodySequence": [
            _node_view(node_map[node_id], catalog)
            for node_id in sorted(
                (
                    node_id
                    for node_id in relevant_ids
                    if node_map[node_id].get("kind") in record_kinds
                ),
                key=lambda node_id: _sequence_key(node_map[node_id]),
            )
        ],
        "relationships": relationships,
        "identityReconciliation": [
            relationship
            for relationship in relationships
            if relationship.get("relation") in {"same-object-as", "possibly-same-as"}
        ],
        "conflicts": [
            _edge_view(edge, catalog)
            for edge in plan.get("edges", [])
            if isinstance(edge, dict)
            and edge.get("relation") == "contradicts"
            and (
                edge.get("from") in relevant_ids
                or edge.get("to") in relevant_ids
            )
        ],
        "coverageDenominators": {
            "relatedEntityCount": len(relevant_ids),
            "relationshipCount": len(relevant_edges),
            "distinctSourceCount": len(
                {
                    source_id
                    for node_id in relevant_ids
                    for source_id in _strings(node_map[node_id].get("sourceIds"))
                }
            ),
            "distinctOriginFamilyCount": len(
                {
                    family_id
                    for node_id in relevant_ids
                    for family_id in _citations(
                        node_map[node_id].get("sourceIds"), catalog
                    )["originFamilyIds"]
                }
            ),
        },
        "unknownStages": [
            label
            for label, kind in (
                ("recovery or find event", "find-event"),
                ("archaeological context", "excavation-context"),
                ("analysis", "analysis"),
                ("custody event", "custody-event"),
                ("present repository", "repository"),
            )
            if not any(
                node_map[node_id].get("kind") == kind for node_id in relevant_ids
            )
        ],
        "contactRoleSuggestions": [
            {
                "role": "museum registrar or collections-information specialist",
                "instituteCapability": "accession, identity, custody, transfer, and current-repository verification",
            },
            {
                "role": "object and context specialist",
                "instituteCapability": "classification, dating, find-event, and provenience review",
            },
        ],
        "provenanceWarning": (
            "Archaeological provenience, evidence lineage, and collection custody "
            "remain separate authorities; missing intervals are left unknown."
        ),
    }
