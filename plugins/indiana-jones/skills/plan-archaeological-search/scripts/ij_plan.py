from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Iterable

from ij_policy import finite_number, unit_score, validate_policy
from ij_entities import provenance_sensitivity_errors, validate_entity_node
from ij_safety import (
    SENSITIVITIES,
    locator_errors,
    safe_locator_problem,
    validate_action_safety,
    validate_source_safety,
)

NODE_KINDS = set(
    """phase event process social-context spatial-feature claim observation hypothesis
    material-expectation proxy test result candidate decision excavation-context object find-event
    assemblage collection repository analysis custody-event production-evidence person-or-organization catalogue-record publication-record source-snapshot""".split()
)
AUTHORITIES = set("observed reported derived inferred hypothesis corroborated".split())
HYPOTHESIS_CLASSES = set("archaeological natural modern processing null".split())
RELATIONS = set(
    """reports measures derived-from supports weakens contradicts corroborates
    alternative-to same-origin-as motivates implies-process may-produce observable-as
    tested-by applies-to produces updates historically-precedes may-precede overlaps-in-time
    part-of route-connects hydrologically-connects visible-from located-at possibly-located-at
    stratigraphically-precedes same-once-whole found-at recovered-during member-of-assemblage
    held-by repository-of analysed-by has-custody-event custody-transferred-to same-object-as
    made-of dated-to recovered-in member-of typed-as dated-by supports-production-of custody-before possibly-same-as catalogued-as published-as reported-by""".split()
)
ORDER_RELATIONS = {"historically-precedes", "stratigraphically-precedes", "derived-from"}
STRATIGRAPHIC_RELATIONS = {"stratigraphically-precedes", "same-once-whole"}
LANES = {"discrimination", "negative-control", "coverage", "corroboration"}
ACTION_STATES = set("planned running completed completed-unverified failed blocked rejected cancelled superseded".split())
STUDY_KINDS = {"prospective-survey", "known-site-rediscovery", "historical-reconstruction"}
DISCLOSURES = {"public", "restricted", "heritage-authority-only"}
@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors

def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"

def _cell_id(row: int, column: int) -> str:
    return f"cell_L0_R{row + 1:02d}C{column + 1:02d}"

def new_plan(
    place: str,
    question: str,
    bbox: list[float],
    rows: int,
    columns: int,
    study_kind: str,
    disclosure: str,
    gazetteer_id: str,
) -> dict[str, Any]:
    west, south, east, north = bbox
    geometry_field = "geometry" if disclosure == "public" else "restrictedGeometry"
    spatial_sensitivity = "public" if disclosure == "public" else "restricted"
    cells: list[dict[str, Any]] = []
    lon_step = (east - west) / columns
    lat_step = (north - south) / rows
    for row in range(rows):
        for column in range(columns):
            cell_west = west + column * lon_step
            cell_east = west + (column + 1) * lon_step
            cell_south = south + row * lat_step
            cell_north = south + (row + 1) * lat_step
            neighbors: list[str] = []
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = row + dr, column + dc
                if 0 <= rr < rows and 0 <= cc < columns:
                    neighbors.append(_cell_id(rr, cc))
            cells.append(
                {
                    "cellId": _cell_id(row, column),
                    "level": 0,
                    "parentId": None,
                    "publicLabel": f"study sector {row + 1}-{column + 1}",
                    geometry_field: {
                        "type": "bbox",
                        "crs": "EPSG:4326",
                        "bbox": [
                            round(cell_west, 8),
                            round(cell_south, 8),
                            round(cell_east, 8),
                            round(cell_north, 8),
                        ],
                    },
                    "neighbors": sorted(neighbors),
                    "landscapeContext": [],
                    "coverageState": "unsearched",
                    "sensitivity": spatial_sensitivity,
                }
            )

    case_id = _stable_id("case", place, question, gazetteer_id)
    return {
        "schemaVersion": "2.0",
        "case": {
            "caseId": case_id,
            "question": question,
            "intendedDecision": "Select non-invasive research and survey tasks",
            "studyKind": study_kind,
            "targetLabelsState": "unknown",
            "candidatesFrozen": False,
            "disclosure": disclosure,
            "authorization": {
                "publicWeb": True,
                "authenticatedPlatforms": [],
                "fieldActions": False,
                "communityConsultation": False,
            },
        },
        "area": {
            "namedPlace": place,
            "gazetteerCandidates": [
                {"id": gazetteer_id, "label": place, "selected": True}
            ],
            "selectedGazetteerId": gazetteer_id,
            geometry_field: {"type": "bbox", "crs": "EPSG:4326", "bbox": bbox},
            "sensitivity": spatial_sensitivity,
            "publicDescription": place,
            "analysisCrs": "EPSG:4326",
            "metricPlanning": False,
            "gridMethod": "wgs84-reconnaissance-only",
        },
        "grid": {
            "strategy": "coarse-first-adaptive",
            "rows": rows,
            "columns": columns,
            "cells": cells,
        },
        "sources": [],
        "nodes": [],
        "edges": [],
        "actions": [],
        "policy": {
            "scoreVersion": "ordinal-v1",
            "lanePattern": [
                "discrimination",
                "negative-control",
                "discrimination",
                "coverage",
            ],
            "weights": {
                "discrimination": 0.5,
                "falsification": 0.25,
                "independence": 0.15,
                "coverage": 0.1,
            },
            "burdenWeights": {
                "compute": 0.25,
                "humanReview": 0.35,
                "delay": 0.2,
                "money": 0.2,
            },
            "stoppingRules": [
                "explicit-conduct-or-source-access-gate",
                "unresolved-place-ambiguity",
                "method-inadequacy",
                "stronger-alternative",
                "bounded-sufficiency",
                "budget-exhausted",
                "graph-invalidity",
                "sensitivity-escalation",
                "professional-handoff",
            ],
        },
    }

def _ids(items: Iterable[dict[str, Any]], key: str, label: str, errors: list[str]) -> set[str]:
    result: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        value = item.get(key)
        if not isinstance(value, str) or not value:
            errors.append(f"{label}[{index}] requires non-empty {key}")
            continue
        if value in result:
            errors.append(f"duplicate {label} id: {value}")
        result.add(value)
    return result

def _string_array(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        errors.append(f"{label} must be a string array")
        return []
    return value

def _choice(value: Any, choices: set[str]) -> bool:
    return isinstance(value, str) and value in choices

def _bbox(
    value: Any,
    label: str,
    errors: list[str],
    *,
    geographic: bool = True,
) -> list[float] | None:
    if (
        not isinstance(value, list)
        or len(value) != 4
        or any(not finite_number(item) for item in value)
    ):
        errors.append(f"{label} must be [west, south, east, north]")
        return None
    west, south, east, north = [float(item) for item in value]
    if west >= east or south >= north:
        errors.append(f"{label} has an invalid extent")
        return None
    if geographic:
        if not (-180 <= west <= 180 and -180 <= east <= 180):
            errors.append(f"{label} longitude is outside EPSG:4326 bounds")
        if not (-90 <= south <= 90 and -90 <= north <= 90):
            errors.append(f"{label} latitude is outside EPSG:4326 bounds")
    return [west, south, east, north]

def _cycle_witness(pairs: list[tuple[str, str]]) -> list[str] | None:
    graph: dict[str, list[str]] = {}
    for source, target in sorted(pairs):
        graph.setdefault(source, []).append(target)
        graph.setdefault(target, [])
    color: dict[str, int] = {node: 0 for node in graph}
    stack: list[str] = []
    positions: dict[str, int] = {}

    def visit(node: str) -> list[str] | None:
        color[node] = 1
        positions[node] = len(stack)
        stack.append(node)
        for neighbor in graph[node]:
            if color[neighbor] == 0:
                found = visit(neighbor)
                if found:
                    return found
            elif color[neighbor] == 1:
                return stack[positions[neighbor] :] + [neighbor]
        stack.pop()
        positions.pop(node, None)
        color[node] = 2
        return None

    for node in sorted(graph):
        if color[node] == 0:
            found = visit(node)
            if found:
                return found
    return None

def _validate_place(plan: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    area = plan.get("area")
    if not isinstance(area, dict):
        errors.append("area must be an object")
        return
    selected = area.get("selectedGazetteerId")
    candidates = area.get("gazetteerCandidates")
    if not isinstance(candidates, list) or not candidates:
        errors.append("area.gazetteerCandidates must contain an explicit place resolution")
        return
    if any(not isinstance(item, dict) for item in candidates):
        errors.append("area.gazetteerCandidates entries must be objects")
    candidate_ids = {item.get("id") for item in candidates if isinstance(item, dict) and isinstance(item.get("id"), str)}
    if not isinstance(selected, str) or selected not in candidate_ids:
        errors.append("area.selectedGazetteerId must select one listed gazetteer candidate")
    selected_count = sum(
        1 for item in candidates if isinstance(item, dict) and item.get("selected") is True
    )
    if selected_count != 1:
        errors.append("exactly one gazetteer candidate must be selected")
    if len(candidates) > 1:
        warnings.append("place had multiple gazetteer candidates; preserve rejected matches")

    geometries = [(key, area.get(key)) for key in ("geometry", "restrictedGeometry") if key in area]
    if not geometries:
        errors.append("area requires geometry or restrictedGeometry")
    for key, geometry in geometries:
        if not isinstance(geometry, dict):
            errors.append(f"area.{key} must be an object")
            continue
        _bbox(
            geometry.get("bbox"),
            f"area.{key}.bbox",
            errors,
            geographic=geometry.get("crs", "EPSG:4326") == "EPSG:4326",
        )
    if "sensitivity" in area and not _choice(area.get("sensitivity"), SENSITIVITIES):
        errors.append("area.sensitivity is invalid")
    if area.get("metricPlanning") is True and area.get("analysisCrs") == "EPSG:4326":
        errors.append("metre-scale planning requires a suitable projected CRS, not EPSG:4326")

def _validate_grid(plan: dict[str, Any], errors: list[str]) -> set[str]:
    grid = plan.get("grid")
    if not isinstance(grid, dict) or not isinstance(grid.get("cells"), list):
        errors.append("grid.cells must be an array")
        return set()
    raw_cells = grid["cells"]
    cell_ids = _ids(raw_cells, "cellId", "grid.cells", errors)
    parent_pairs: list[tuple[str, str]] = []
    for cell in (item for item in raw_cells if isinstance(item, dict)):
        cell_id = cell.get("cellId", "<unknown>")
        if not _choice(cell.get("sensitivity"), SENSITIVITIES):
            errors.append(f"{cell_id}: invalid sensitivity")
        for key in ("geometry", "restrictedGeometry"):
            geometry = cell.get(key)
            if geometry is None:
                continue
            if not isinstance(geometry, dict):
                errors.append(f"{cell_id}: {key} must be an object")
            else:
                _bbox(
                    geometry.get("bbox"),
                    f"{cell_id}.{key}.bbox",
                    errors,
                    geographic=geometry.get("crs", "EPSG:4326") == "EPSG:4326",
                )
        neighbors = _string_array(cell.get("neighbors", []), f"{cell_id}: neighbors", errors)
        for neighbor in neighbors:
            if neighbor not in cell_ids:
                errors.append(f"{cell_id}: unknown neighbor {neighbor}")
        parent = cell.get("parentId")
        if parent is not None and (
            not isinstance(parent, str) or parent not in cell_ids
        ):
            errors.append(f"{cell_id}: unknown parentId {parent}")
        elif parent is not None and isinstance(cell_id, str):
            parent_pairs.append((parent, cell_id))
    witness = _cycle_witness(parent_pairs)
    if witness:
        errors.append(f"grid parent cycle: {' -> '.join(witness)}")
    return cell_ids

def _validate_sources(plan: dict[str, Any], errors: list[str]) -> set[str]:
    sources = plan.get("sources")
    if not isinstance(sources, list):
        errors.append("sources must be an array")
        return set()
    source_ids = _ids(sources, "sourceId", "sources", errors)
    for source in (item for item in sources if isinstance(item, dict)):
        source_id = source.get("sourceId", "<unknown>")
        if not isinstance(source.get("originFamilyId"), str) or not source.get(
            "originFamilyId"
        ):
            errors.append(f"{source_id}: originFamilyId is required")
        errors.extend(validate_source_safety(source))
    return source_ids

def _validate_nodes(
    plan: dict[str, Any],
    source_map: dict[str, dict[str, Any]],
    cell_ids: set[str],
    errors: list[str],
) -> tuple[set[str], dict[str, dict[str, Any]]]:
    source_ids = set(source_map)
    nodes = plan.get("nodes")
    if not isinstance(nodes, list):
        errors.append("nodes must be an array")
        return set(), {}
    node_ids = _ids(nodes, "nodeId", "nodes", errors)
    node_map = {
        item.get("nodeId"): item
        for item in nodes
        if isinstance(item, dict) and isinstance(item.get("nodeId"), str)
    }
    for node in (item for item in nodes if isinstance(item, dict)):
        node_id = node.get("nodeId", "<unknown>")
        kind = node.get("kind")
        authority = node.get("authority")
        if not _choice(kind, NODE_KINDS):
            errors.append(f"{node_id}: invalid node kind {kind!r}")
        errors.extend(validate_entity_node(node))
        errors.extend(provenance_sensitivity_errors(node, source_map))
        if not _choice(authority, AUTHORITIES):
            errors.append(f"{node_id}: invalid authority {authority!r}")
        sensitivity = node.get("sensitivity")
        if not _choice(sensitivity, SENSITIVITIES):
            errors.append(f"{node_id}: invalid sensitivity")
        linked_sources = _string_array(
            node.get("sourceIds", []), f"{node_id}: sourceIds", errors
        )
        for source_id in linked_sources:
            if source_id not in source_ids:
                errors.append(f"{node_id}: unknown sourceId {source_id}")
        if authority in ("observed", "reported", "derived", "inferred", "corroborated"):
            if not linked_sources:
                errors.append(f"{node_id}: authority {authority} requires source provenance")
        linked_cells = _string_array(
            node.get("cellIds", []), f"{node_id}: cellIds", errors
        )
        for cell_id in linked_cells:
            if cell_id not in cell_ids:
                errors.append(f"{node_id}: unknown cellId {cell_id}")
        if kind == "hypothesis":
            hypothesis_class = node.get("hypothesisClass")
            if not _choice(hypothesis_class, HYPOTHESIS_CLASSES):
                errors.append(f"{node_id}: hypothesisClass is required and invalid")
        if node.get("locator") is not None:
            problem = safe_locator_problem(node.get("locator"))
            if problem:
                errors.append(f"{node_id}: locator {problem}")
    return node_ids, node_map

def _validate_edges(
    plan: dict[str, Any],
    node_ids: set[str],
    node_map: dict[str, dict[str, Any]],
    source_map: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    edges = plan.get("edges")
    if not isinstance(edges, list):
        errors.append("edges must be an array")
        return
    _ids(edges, "edgeId", "edges", errors)
    source_ids = set(source_map)
    order_pairs: dict[str, list[tuple[str, str]]] = {key: [] for key in ORDER_RELATIONS}
    for edge in (item for item in edges if isinstance(item, dict)):
        edge_id = edge.get("edgeId", "<unknown>")
        relation = edge.get("relation")
        source = edge.get("from")
        target = edge.get("to")
        if not _choice(relation, RELATIONS):
            errors.append(f"{edge_id}: invalid relation {relation!r}")
            continue
        if not isinstance(source, str) or not isinstance(target, str) or source not in node_ids or target not in node_ids:
            errors.append(f"{edge_id}: endpoints must reference graph nodes")
            continue
        linked_sources = _string_array(
            edge.get("sourceIds", []), f"{edge_id}: sourceIds", errors
        )
        for source_id in linked_sources:
            if source_id not in source_ids:
                errors.append(f"{edge_id}: unknown sourceId {source_id}")
        edge_authority = edge.get("authority")
        if not _choice(edge_authority, AUTHORITIES | {"observed-stratigraphy"}):
            errors.append(f"{edge_id}: invalid edge authority {edge_authority!r}")
        if edge_authority not in ("hypothesis", "observed-stratigraphy") and not linked_sources:
            errors.append(f"{edge_id}: edge authority {edge_authority} requires provenance")
        if not isinstance(edge.get("rationale"), str) or not edge.get("rationale"):
            errors.append(f"{edge_id}: rationale is required")
        if edge.get("recordLocator") is not None:
            problem = safe_locator_problem(edge.get("recordLocator"))
            if problem:
                errors.append(f"{edge_id}: recordLocator {problem}")
        if relation in STRATIGRAPHIC_RELATIONS:
            source_node = node_map[source]
            target_node = node_map[target]
            if (
                source_node.get("kind") != "excavation-context"
                or target_node.get("kind") != "excavation-context"
            ):
                errors.append(f"{edge_id}: stratigraphic relations require excavation contexts")
            for context_node in (source_node, target_node):
                context_sources = [
                    source_map[source_id]
                    for source_id in context_node.get("sourceIds", [])
                    if source_id in source_map
                ]
                if context_node.get("authority") not in {"observed", "corroborated"}:
                    errors.append(f"{edge_id}: excavation context must have observed authority")
                if not any(
                    source.get("recordType") == "excavation-record"
                    for source in context_sources
                ):
                    errors.append(f"{edge_id}: context lacks an excavation-record source")
            if edge.get("authority") != "observed-stratigraphy":
                errors.append(f"{edge_id}: stratigraphic relation requires observed-stratigraphy")
            if not linked_sources or not edge.get("recordLocator"):
                errors.append(f"{edge_id}: stratigraphic relation requires record provenance")
            elif not any(
                source_map[source_id].get("recordType") == "excavation-record"
                for source_id in linked_sources
                if source_id in source_map
            ):
                errors.append(f"{edge_id}: relation lacks an excavation-record source")
        elif edge.get("authority") == "observed-stratigraphy":
            errors.append(f"{edge_id}: observed-stratigraphy is reserved for context relations")
        if relation in ORDER_RELATIONS:
            order_pairs[relation].append((source, target))

    for relation, pairs in order_pairs.items():
        witness = _cycle_witness(pairs)
        if witness:
            errors.append(f"{relation} cycle: {' -> '.join(witness)}")


def _validate_actions(
    plan: dict[str, Any],
    source_ids: set[str],
    node_ids: set[str],
    cell_ids: set[str],
    errors: list[str],
    warnings: list[str],
) -> None:
    actions = plan.get("actions")
    if not isinstance(actions, list):
        errors.append("actions must be an array")
        return
    action_ids = _ids(actions, "actionId", "actions", errors)
    action_map = {
        item.get("actionId"): item
        for item in actions
        if isinstance(item, dict) and isinstance(item.get("actionId"), str)
    }
    raw_sources = plan.get("sources")
    raw_nodes = plan.get("nodes")
    source_map = {
        item.get("sourceId"): item
        for item in (raw_sources if isinstance(raw_sources, list) else [])
        if isinstance(item, dict) and isinstance(item.get("sourceId"), str)
    }
    node_map = {
        item.get("nodeId"): item
        for item in (raw_nodes if isinstance(raw_nodes, list) else [])
        if isinstance(item, dict) and isinstance(item.get("nodeId"), str)
    }
    requirement_pairs: list[tuple[str, str]] = []
    for action in (item for item in actions if isinstance(item, dict)):
        action_id = action.get("actionId", "<unknown>")
        if not _choice(action.get("lane"), LANES):
            errors.append(f"{action_id}: invalid lane")
        if not _choice(action.get("status"), ACTION_STATES):
            errors.append(f"{action_id}: invalid status")
        for field in ("candidateFocused", "requiresCandidatesFrozen"):
            if field in action and not isinstance(action[field], bool):
                errors.append(f"{action_id}: {field} must be boolean")
        if not isinstance(action.get("candidateFocused"), bool):
            errors.append(f"{action_id}: candidateFocused must be boolean")
        linked_sources = _string_array(
            action.get("sourceIds", []), f"{action_id}: sourceIds", errors
        )
        for source_id in linked_sources:
            if source_id not in source_ids:
                errors.append(f"{action_id}: unknown sourceId {source_id}")
        hypotheses = _string_array(
            action.get("hypothesisIds", []), f"{action_id}: hypothesisIds", errors
        )
        for node_id in hypotheses:
            if node_id not in node_ids:
                errors.append(f"{action_id}: unknown hypothesis node {node_id}")
        linked_cells = _string_array(
            action.get("cellIds", []), f"{action_id}: cellIds", errors
        )
        for cell_id in linked_cells:
            if cell_id not in cell_ids:
                errors.append(f"{action_id}: unknown cellId {cell_id}")
        prerequisites = _string_array(
            action.get("prerequisites", []), f"{action_id}: prerequisites", errors
        )
        for prerequisite in prerequisites:
            if prerequisite not in action_ids:
                errors.append(f"{action_id}: unknown prerequisite {prerequisite}")
            else:
                requirement_pairs.append((prerequisite, action_id))
        authorization = action.get("authorization", {})
        if not isinstance(authorization, dict):
            errors.append(f"{action_id}: authorization must be an object")
            authorization = {}
        required = authorization.get("required")
        state = authorization.get("state")
        if not _choice(
            required,
            {"none", "user-account", "external-approval", "community-governance"},
        ):
            errors.append(f"{action_id}: invalid authorization.required")
        if not _choice(state, {"not-required", "confirmed", "pending", "not-authorized"}):
            errors.append(f"{action_id}: invalid authorization.state")
        result_ids = _string_array(
            action.get("resultNodeIds", []), f"{action_id}: resultNodeIds", errors
        )
        for result_id in result_ids:
            result = node_map.get(result_id)
            if result is None:
                errors.append(f"{action_id}: unknown result node {result_id}")
            elif result.get("kind") != "result":
                errors.append(f"{action_id}: resultNodeIds must reference result nodes")
        result_refs = action.get("resultRefs", [])
        if not isinstance(result_refs, list) or any(
            not isinstance(ref, dict)
            or any(not isinstance(ref.get(key), str) or not ref.get(key) for key in ("path", "sha256"))
            or len(ref.get("sha256", "")) != 64
            or any(character not in "0123456789abcdef" for character in ref.get("sha256", ""))
            for ref in result_refs
        ):
            errors.append(f"{action_id}: resultRefs must contain path and sha256")
            result_refs = []
        if action.get("status") == "completed":
            if not result_ids and not result_refs:
                errors.append(f"{action_id}: completed action requires linked result evidence")
            if required != "none" and state != "confirmed":
                errors.append(f"{action_id}: completed action requires confirmed authorization")
        scores = action.get("scores")
        if not isinstance(scores, dict):
            errors.append(f"{action_id}: scores must be an object")
        else:
            for key in (
                "discrimination",
                "falsification",
                "independence",
                "coverage",
                "compute",
                "humanReview",
                "delay",
                "money",
            ):
                value = scores.get(key)
                if not unit_score(value):
                    errors.append(f"{action_id}: scores.{key} must be between 0 and 1")
        pair_id = action.get("pairedControlActionId")
        if pair_id is not None and not isinstance(pair_id, str):
            errors.append(f"{action_id}: pairedControlActionId must be a string")
        if action.get("candidateFocused") is True:
            pair = action_map.get(pair_id) if isinstance(pair_id, str) else None
            if pair is None or pair.get("lane") != "negative-control":
                errors.append(f"{action_id}: candidate-focused action requires a control action")
        errors.extend(validate_action_safety(plan, action, action_map, source_map))

    witness = _cycle_witness(requirement_pairs)
    if witness:
        errors.append(f"action prerequisite cycle: {' -> '.join(witness)}")

    raw_nodes = plan.get("nodes")
    hypothesis_classes = {
        node.get("hypothesisClass")
        for node in (raw_nodes if isinstance(raw_nodes, list) else [])
        if isinstance(node, dict) and node.get("kind") == "hypothesis"
        and isinstance(node.get("hypothesisClass"), str)
    }
    if any(isinstance(action, dict) and action.get("candidateFocused") is True for action in actions):
        if not hypothesis_classes.intersection({"natural", "modern"}):
            errors.append("candidate-focused plan requires a natural or modern alternative")
        if "processing" not in hypothesis_classes:
            errors.append("candidate-focused plan requires a processing/data-quality alternative")
        if "null" not in hypothesis_classes:
            warnings.append("candidate-focused plan should preserve an explicit null hypothesis")


def validate_plan(plan: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(plan, dict):
        return ValidationResult(errors=["plan must be an object"], warnings=[])
    if plan.get("schemaVersion") not in ("1.0", "2.0"):
        errors.append("schemaVersion must be '1.0' or '2.0'")
    case = plan.get("case")
    if not isinstance(case, dict):
        errors.append("case must be an object")
    else:
        if not _choice(case.get("studyKind"), STUDY_KINDS):
            errors.append("case.studyKind is invalid")
        if not _choice(case.get("disclosure"), DISCLOSURES):
            errors.append("case.disclosure is invalid")
        for key in ("caseId", "question", "intendedDecision"):
            if not isinstance(case.get(key), str) or not case.get(key):
                errors.append(f"case.{key} is required")
        authorization = case.get("authorization")
        if not isinstance(authorization, dict):
            errors.append("case.authorization must be an object")
        else:
            for key in ("publicWeb", "fieldActions", "communityConsultation"):
                if not isinstance(authorization.get(key), bool):
                    errors.append(f"case.authorization.{key} must be boolean")
            platforms = authorization.get("authenticatedPlatforms")
            if (
                not isinstance(platforms, list)
                or any(not isinstance(platform, str) or not platform for platform in platforms)
            ):
                errors.append(
                    "case.authorization.authenticatedPlatforms must be a string array"
                )
        if not isinstance(case.get("candidatesFrozen"), bool):
            errors.append("case.candidatesFrozen must be boolean")

    _validate_place(plan, errors, warnings)
    cell_ids = _validate_grid(plan, errors)
    source_ids = _validate_sources(plan, errors)
    source_map = {
        source.get("sourceId"): source
        for source in plan.get("sources", [])
        if isinstance(source, dict) and isinstance(source.get("sourceId"), str)
    }
    node_ids, node_map = _validate_nodes(plan, source_map, cell_ids, errors)
    _validate_edges(plan, node_ids, node_map, source_map, errors)
    _validate_actions(plan, source_ids, node_ids, cell_ids, errors, warnings)
    errors.extend(validate_policy(plan))
    errors.extend(locator_errors(plan))
    return ValidationResult(errors=errors, warnings=warnings)
