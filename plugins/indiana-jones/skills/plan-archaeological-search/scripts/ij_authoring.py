from __future__ import annotations

import copy
from typing import Any

from ij_execution_spec import execution_readiness_errors
from ij_plan import validate_plan
from ij_readiness import readiness_errors


PACKAGE_FIELDS = {
    "schemaVersion",
    "case",
    "area",
    "grid",
    "sources",
    "nodes",
    "edges",
    "actions",
    "policy",
}
CASE_FIELDS = {
    "intendedDecision",
    "researchMode",
    "targetLabelsState",
    "candidatesFrozen",
    "candidateArtifactSha256",
    "disclosure",
}
AREA_FIELDS = {
    "publicDescription",
    "analysisCrs",
    "metricPlanning",
    "gridMethod",
    "geometry",
    "restrictedGeometry",
    "sensitivity",
    "spatialRestriction",
}
GRID_FIELDS = {"strategy", "rows", "columns", "cells"}
CELL_FIELDS = {
    "cellId",
    "level",
    "parentId",
    "publicLabel",
    "geometry",
    "restrictedGeometry",
    "neighbors",
    "landscapeContext",
    "coverageState",
    "sensitivity",
    "spatialRestriction",
}
RESTRICTED_SPATIAL_VALUES = {"withhold", "authority-only", "restricted", "private"}
SPATIAL_DISCLOSURES = RESTRICTED_SPATIAL_VALUES | {"public", "none"}


def _validate_grid_package(value: Any) -> None:
    if not isinstance(value, dict) or set(value) - GRID_FIELDS:
        raise ValueError("research package grid contains unsupported fields")
    cells = value.get("cells")
    if not isinstance(cells, list):
        raise ValueError("research package grid.cells must be an array")
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict) or set(cell) - CELL_FIELDS:
            raise ValueError(
                f"research package grid.cells[{index}] contains unsupported fields"
            )
        if (
            "spatialRestriction" in cell
            and cell["spatialRestriction"] not in SPATIAL_DISCLOSURES
        ):
            raise ValueError(
                f"research package grid.cells[{index}].spatialRestriction is invalid"
            )


def _spatial_disclosure_errors(plan: dict[str, Any]) -> list[str]:
    disclosure = plan.get("case", {}).get("disclosure")
    area = plan.get("area", {})
    cells = plan.get("grid", {}).get("cells", [])
    errors: list[str] = []
    public_case = disclosure == "public"
    public_cells = 0
    area_public = area.get("sensitivity") == "public"
    if public_case != area_public:
        errors.append("area sensitivity must match case disclosure")
    area_key = "geometry" if area_public else "restrictedGeometry"
    other_area_key = "restrictedGeometry" if area_public else "geometry"
    if area_key not in area or other_area_key in area:
        errors.append(f"area must use {area_key} exclusively")
    if area_public and area.get("spatialRestriction") in RESTRICTED_SPATIAL_VALUES:
        errors.append("public area cannot carry a restricted spatial disclosure")
    for index, cell in enumerate(cells if isinstance(cells, list) else []):
        if not isinstance(cell, dict):
            continue
        public_cell = cell.get("sensitivity") == "public"
        public_cells += int(public_cell)
        if not public_case and public_cell:
            errors.append(f"grid.cells[{index}] cannot be public in a restricted case")
        geometry_key = "geometry" if public_cell else "restrictedGeometry"
        other_key = "restrictedGeometry" if public_cell else "geometry"
        if geometry_key not in cell or other_key in cell:
            errors.append(f"grid.cells[{index}] must use {geometry_key} exclusively")
        if public_cell and cell.get("spatialRestriction") in RESTRICTED_SPATIAL_VALUES:
            errors.append(
                f"grid.cells[{index}] cannot carry a restricted spatial disclosure"
            )
    if public_case and not public_cells:
        errors.append("public case requires at least one public exact grid cell")
    return errors


def prepare_research_plan(
    skeleton: dict[str, Any],
    package: dict[str, Any],
) -> dict[str, Any]:
    if skeleton.get("schemaVersion") != "2.0":
        raise ValueError("prepare requires a schema 2.0 skeleton")
    if package.get("schemaVersion") != "archaeological-research-package-1.0":
        raise ValueError(
            "research package must use archaeological-research-package-1.0"
        )
    unknown = sorted(set(package) - PACKAGE_FIELDS)
    if unknown:
        raise ValueError("research package has unsupported fields: " + ", ".join(unknown))
    prepared = copy.deepcopy(skeleton)
    for field in ("sources", "nodes", "edges", "actions"):
        value = package.get(field)
        if not isinstance(value, list):
            raise ValueError(f"research package {field} must be an array")
        prepared[field] = copy.deepcopy(value)
    case_updates = package.get("case", {})
    if not isinstance(case_updates, dict) or set(case_updates) - CASE_FIELDS:
        raise ValueError("research package case contains unsupported fields")
    prepared["case"].update(copy.deepcopy(case_updates))
    area_updates = package.get("area", {})
    if not isinstance(area_updates, dict) or set(area_updates) - AREA_FIELDS:
        raise ValueError("research package area contains unsupported fields")
    if (
        "spatialRestriction" in area_updates
        and area_updates["spatialRestriction"] not in SPATIAL_DISCLOSURES
    ):
        raise ValueError("research package area.spatialRestriction is invalid")
    if "geometry" in area_updates and "restrictedGeometry" not in area_updates:
        prepared["area"].pop("restrictedGeometry", None)
    if "restrictedGeometry" in area_updates and "geometry" not in area_updates:
        prepared["area"].pop("geometry", None)
    prepared["area"].update(copy.deepcopy(area_updates))
    if "grid" in package:
        _validate_grid_package(package["grid"])
        prepared["grid"] = copy.deepcopy(package["grid"])
    if "policy" in package:
        if not isinstance(package["policy"], dict):
            raise ValueError("research package policy must be an object")
        prepared["policy"] = copy.deepcopy(package["policy"])
    spatial_errors = _spatial_disclosure_errors(prepared)
    if spatial_errors:
        raise ValueError(
            "prepared plan has inconsistent spatial disclosure: "
            + "; ".join(spatial_errors)
        )
    validation = validate_plan(prepared)
    if not validation.valid:
        raise ValueError("prepared plan is invalid: " + "; ".join(validation.errors))
    readiness = readiness_errors(prepared) + execution_readiness_errors(prepared)
    if readiness:
        raise ValueError("prepared plan is not research-ready: " + "; ".join(readiness))
    return prepared
