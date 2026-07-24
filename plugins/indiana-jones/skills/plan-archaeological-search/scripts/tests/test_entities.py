from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE = SKILL_DIR / "assets" / "search-plan-template.json"
sys.path.insert(0, str(SCRIPT_DIR))

from entity_fixture import entity_record
from ij_artifacts import read_json, write_json
from ij_entities import ENTITY_KINDS
from ij_migrate import migrate_plan
from ij_plan import validate_plan


class ArchaeologicalEntitySchemaTests(unittest.TestCase):
    def _plan_with_entities(self) -> dict:
        plan = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        for index, kind in enumerate(sorted(ENTITY_KINDS), 1):
            plan["nodes"].append(
                {
                    "nodeId": f"entity_{index:02d}",
                    "kind": kind,
                    "label": f"Typed fixture {kind}",
                    "authority": "reported",
                    "sourceIds": ["src_hul"],
                    "cellIds": [],
                    "sensitivity": "restricted",
                    "record": entity_record(kind),
                }
            )
        return plan

    def test_every_archaeological_entity_round_trips_with_typed_fields(self) -> None:
        plan = self._plan_with_entities()
        self.assertEqual([], validate_plan(plan).errors)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "plan.json"
            write_json(path, plan)
            restored = read_json(path)
        self.assertEqual(plan, restored)
        records = {
            node["kind"]: node["record"]
            for node in restored["nodes"]
            if node.get("kind") in ENTITY_KINDS
        }
        self.assertEqual(ENTITY_KINDS, set(records))
        self.assertEqual("sword", records["object"]["objectClass"])
        self.assertEqual("Fixture Museum", records["repository"]["institutionName"])
        self.assertEqual("accession", records["custody-event"]["eventType"])

    def test_entity_nodes_reject_missing_records_and_arbitrary_fields(self) -> None:
        plan = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        plan["nodes"].append(
            {
                "nodeId": "bad_object",
                "kind": "object",
                "label": "Unstructured object",
                "authority": "reported",
                "sourceIds": ["src_hul"],
                "cellIds": [],
                "sensitivity": "restricted",
                "nonsense": "silently accepted before schema 2",
            }
        )
        errors = validate_plan(plan).errors
        self.assertTrue(any("unsupported entity-node fields" in error for error in errors))
        self.assertTrue(any("requires a typed record" in error for error in errors))

    def test_public_node_cannot_cite_a_non_public_source(self) -> None:
        plan = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        plan["sources"][0]["sensitivity"] = "non-public"
        plan["nodes"].append(
            {
                "nodeId": "leaky_public_claim",
                "kind": "claim",
                "label": "Claim derived from protected source",
                "authority": "reported",
                "sourceIds": ["src_hul"],
                "cellIds": [],
                "sensitivity": "public",
            }
        )
        self.assertTrue(
            any(
                "public node cites non-public source" in error
                for error in validate_plan(plan).errors
            )
        )

    def test_migration_preserves_typed_entity_histories_byte_for_byte(self) -> None:
        plan = self._plan_with_entities()
        plan["schemaVersion"] = "1.0"
        original_records = [
            node["record"]
            for node in plan["nodes"]
            if node.get("kind") in ENTITY_KINDS
        ]
        migrated, manifest = migrate_plan(plan)
        migrated_records = [
            node["record"]
            for node in migrated["nodes"]
            if node.get("kind") in ENTITY_KINDS
        ]
        self.assertEqual(original_records, migrated_records)
        self.assertEqual("2.0", migrated["schemaVersion"])
        self.assertEqual(64, len(manifest["sourcePlanSha256"]))


if __name__ == "__main__":
    unittest.main()
