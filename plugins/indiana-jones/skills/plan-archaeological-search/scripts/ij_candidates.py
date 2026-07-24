from __future__ import annotations

import math
from typing import Any


ROOT_FIELDS = {"schemaVersion", "lineage", "candidates"}
LINEAGE_FIELDS = {"sourceIds", "generationActionIds", "groundTruthState"}
CANDIDATE_FIELDS = {
    "candidateId",
    "publicArea",
    "evidenceGrade",
    "score",
    "rank",
    "cellIds",
    "sourceIds",
    "rationale",
    "sensitivity",
    "coordinates",
    "geometry",
    "hypothesis",
    "evidenceReferences",
    "imageryAnnotationRefs",
}
EVIDENCE_GRADES = {"hypothesis", "weak", "moderate", "strong"}
SENSITIVITIES = {
    "public",
    "restricted",
    "non-public",
    "vulnerable",
    "sacred",
    "burial",
}


def _string_ids(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if (
        not isinstance(value, list)
        or (not allow_empty and not value)
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
    ):
        qualifier = "possibly empty " if allow_empty else "non-empty "
        raise ValueError(f"{label} must be a unique {qualifier}string array")
    return value


def _coordinate(value: Any, label: str) -> list[float]:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(
            not isinstance(item, (int, float))
            or isinstance(item, bool)
            or not math.isfinite(float(item))
            for item in value
        )
        or not -180 <= float(value[0]) <= 180
        or not -90 <= float(value[1]) <= 90
    ):
        raise ValueError(f"{label} must be a finite [longitude, latitude] pair")
    return [float(value[0]), float(value[1])]


def _validate_geometry(value: Any, label: str) -> None:
    if not isinstance(value, dict) or set(value) != {"type", "coordinates"}:
        raise ValueError(f"{label} must be an allowlisted GeoJSON geometry")
    geometry_type = value.get("type")
    coordinates = value.get("coordinates")
    if geometry_type == "Point":
        _coordinate(coordinates, f"{label}.coordinates")
        return
    if geometry_type != "Polygon" or not isinstance(coordinates, list) or not coordinates:
        raise ValueError(f"{label}.type must be Point or Polygon")
    for ring_index, ring in enumerate(coordinates):
        if not isinstance(ring, list) or len(ring) < 4:
            raise ValueError(f"{label}.coordinates[{ring_index}] must be a closed ring")
        normalized = [
            _coordinate(point, f"{label}.coordinates[{ring_index}][{point_index}]")
            for point_index, point in enumerate(ring)
        ]
        if normalized[0] != normalized[-1]:
            raise ValueError(f"{label}.coordinates[{ring_index}] must be closed")


def validate_candidate_artifact(plan: dict[str, Any], value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("candidate artifact must be an object")
    unknown_root = sorted(set(value) - ROOT_FIELDS)
    if unknown_root:
        raise ValueError("candidate artifact has unsupported fields: " + ", ".join(unknown_root))
    if value.get("schemaVersion") != "candidate-set-1.0":
        raise ValueError("candidate artifact must use candidate-set-1.0")
    lineage = value.get("lineage")
    if not isinstance(lineage, dict) or set(lineage) - LINEAGE_FIELDS:
        raise ValueError("candidate artifact requires an allowlisted lineage object")
    source_ids = _string_ids(lineage.get("sourceIds"), "lineage.sourceIds")
    generation_ids = _string_ids(
        lineage.get("generationActionIds", []),
        "lineage.generationActionIds",
        allow_empty=True,
    )
    if lineage.get("groundTruthState") != "withheld":
        raise ValueError("candidate lineage must keep ground truth withheld")
    source_map = {
        source.get("sourceId"): source
        for source in plan.get("sources", [])
        if isinstance(source, dict) and isinstance(source.get("sourceId"), str)
    }
    for source_id in source_ids:
        source = source_map.get(source_id)
        if source is None:
            raise ValueError(f"candidate lineage references unknown source {source_id}")
        if (
            source.get("accessStage") != "pre-detection"
            or source.get("targetLabelState") != "none"
            or source.get("workflowRole") == "ground-truth"
        ):
            raise ValueError(f"candidate lineage uses post-freeze or target-bearing source {source_id}")
    action_map = {
        action.get("actionId"): action
        for action in plan.get("actions", [])
        if isinstance(action, dict) and isinstance(action.get("actionId"), str)
    }
    for action_id in generation_ids:
        action = action_map.get(action_id)
        if action is None or action.get("stage") != "candidate-generation":
            raise ValueError(f"candidate lineage action is not candidate-generation: {action_id}")
        if any(source_id not in source_ids for source_id in action.get("sourceIds", [])):
            raise ValueError(f"candidate lineage action uses an undeclared source: {action_id}")
    candidates = value.get("candidates")
    if not isinstance(candidates, list) or not candidates or len(candidates) > 100_000:
        raise ValueError("candidate artifact requires 1-100000 candidates")
    known_cells = {
        cell.get("cellId")
        for cell in plan.get("grid", {}).get("cells", [])
        if isinstance(cell, dict) and isinstance(cell.get("cellId"), str)
    }
    seen: set[str] = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict) or set(candidate) - CANDIDATE_FIELDS:
            raise ValueError(f"candidate {index} contains unsupported or malformed fields")
        candidate_id = candidate.get("candidateId")
        if not isinstance(candidate_id, str) or not candidate_id or candidate_id in seen:
            raise ValueError(f"candidate {index} has a missing or duplicate candidateId")
        seen.add(candidate_id)
        grade = candidate.get("evidenceGrade")
        score = candidate.get("score")
        if grade is not None and grade not in EVIDENCE_GRADES:
            raise ValueError(f"candidate {candidate_id} has an invalid evidence grade")
        if score is not None and not (
            isinstance(score, (int, float))
            and not isinstance(score, bool)
            and math.isfinite(float(score))
            and 0.0 <= float(score) <= 1.0
        ):
            raise ValueError(f"candidate {candidate_id} has an invalid finite score")
        if grade is None and score is None:
            raise ValueError(f"candidate {candidate_id} requires an evidence grade or score")
        rank = candidate.get("rank")
        if rank is not None and (
            not isinstance(rank, int) or isinstance(rank, bool) or rank < 1
        ):
            raise ValueError(f"candidate {candidate_id} rank must be a positive integer")
        sensitivity = candidate.get("sensitivity")
        if sensitivity is not None and sensitivity not in SENSITIVITIES:
            raise ValueError(f"candidate {candidate_id} sensitivity is invalid")
        for field in ("publicArea", "rationale", "hypothesis"):
            value = candidate.get(field)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(f"candidate {candidate_id}.{field} must be text")
        for field in ("evidenceReferences", "imageryAnnotationRefs"):
            if field in candidate:
                _string_ids(
                    candidate[field],
                    f"candidate {candidate_id}.{field}",
                )
        if "coordinates" in candidate:
            _coordinate(
                candidate["coordinates"],
                f"candidate {candidate_id}.coordinates",
            )
        if "geometry" in candidate:
            _validate_geometry(
                candidate["geometry"],
                f"candidate {candidate_id}.geometry",
            )
        candidate_sources = candidate.get("sourceIds", source_ids)
        if any(
            source_id not in source_ids
            for source_id in _string_ids(
                candidate_sources,
                f"candidate {candidate_id}.sourceIds",
            )
        ):
            raise ValueError(f"candidate {candidate_id} has undeclared lineage")
        cell_ids = _string_ids(
            candidate.get("cellIds", []),
            f"candidate {candidate_id}.cellIds",
            allow_empty=True,
        )
        if any(cell_id not in known_cells for cell_id in cell_ids):
            raise ValueError(f"candidate {candidate_id} references an unknown grid cell")
