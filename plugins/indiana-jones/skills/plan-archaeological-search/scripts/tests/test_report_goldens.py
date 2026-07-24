from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
FIXTURE = SCRIPT_DIR / "tests" / "goldens" / "report-research-case.json"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_history import build_history_report, build_object_biography
from ij_materials import build_material_evidence_report
from ij_reports import (
    build_finds_report,
    build_object_report,
    build_source_gap_report,
)


GOLDEN_HASHES = {
    "biography": "3ab3f0a3f4899295ba56810ec18c67db84947fb06b7e4529f4350c133b19ffcf",
    "finds": "7254b516a56a1aacbeb32ad8fd33cd3f7760de1425bd2ca8c38fd3c4159d85e2",
    "gaps": "0e4b3c4c9212cb435b42e1f661ab756b2aa7b7827e3b328f998a25ef2743a534",
    "history": "cbc002d6978b2a15cae09392bf581e081d78bae16924419e02f43ed03ace9665",
    "material": "a22cfffb778e8dee4954ddc79140427248e222358aba97a8a413f9ba8a266f19",
    "object": "cf5f315f0e62d8fcd732932d7e7136d0beb353c3e7ee4e859461f4e1b0a18719",
}


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ReportGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.fixture = fixture
        cls.reports = {
            "finds": build_finds_report(
                fixture["reconciliation"],
                area_description="River crossing exact public research area",
                public=True,
            ),
            "object": build_object_report(
                fixture["reconciliation"],
                "find_sword_001",
                public=True,
            ),
            "history": build_history_report(fixture["plan"]),
            "biography": build_object_biography(
                fixture["plan"],
                "object_sword",
            ),
            "material": build_material_evidence_report(
                fixture["materialRecords"],
                "gold",
            ),
            "gaps": build_source_gap_report(
                fixture["queryArtifacts"],
                question=(
                    "Where are swords, gold, and hoards documented near the River Ford?"
                ),
                aliases=["River Ford"],
                languages=["en"],
            ),
        }

    def test_canonical_report_hashes_are_stable(self) -> None:
        actual = {
            name: _canonical_hash(report)
            for name, report in sorted(self.reports.items())
        }
        self.assertEqual(GOLDEN_HASHES, actual)

    def test_public_finds_preserve_exact_evidence_and_explicit_restrictions(
        self,
    ) -> None:
        report = self.reports["finds"]
        by_title = {
            row["record"]["title"]: row
            for row in report["finds"]
        }
        sword = by_title["Pattern-welded sword"]
        self.assertEqual(
            [19.12345, 54.12345],
            sword["record"]["findspot"]["coordinates"],
        )
        self.assertIn(
            "google.com/maps",
            sword["record"]["findspot"]["googleMapsLink"],
        )
        self.assertEqual(1, len(sword["record"]["imageRefs"]))
        self.assertEqual(
            ["origin_excavation_1984", "origin_museum_catalogue"],
            sword["citations"]["originFamilyIds"],
        )
        self.assertEqual(
            "blade and hilt typology",
            sword["classification"]["basis"],
        )
        self.assertEqual(
            "context-record-and-grid",
            sword["contextAndProvenience"]["provenienceQuality"],
        )
        self.assertTrue(sword["conflicts"]["hasUnresolvedConflicts"])
        self.assertEqual(
            4,
            report["coverage"]["denominators"]["inputRecordCount"],
        )
        restricted = by_title["Gold coin"]["record"]
        self.assertNotIn("findspot", restricted)
        self.assertEqual(
            "withheld-by-explicit-restriction",
            restricted["spatialEvidenceStatus"],
        )

    def test_object_report_keeps_identity_context_custody_and_analysis(self) -> None:
        report = self.reports["object"]
        self.assertEqual("S-17", report["object"]["accessionNumber"])
        self.assertEqual(
            "blade typology plus context terminus post quem",
            report["dating"]["basis"],
        )
        self.assertEqual(
            "River District Museum",
            report["repositoryAndCustody"]["repository"],
        )
        self.assertTrue(report["repositoryAndCustody"]["custodyEvents"])
        self.assertTrue(report["repositoryAndCustody"]["analyses"])
        self.assertTrue(report["conflicts"]["hasUnresolvedConflicts"])
        self.assertEqual(
            2,
            len(report["citations"]["originFamilyIds"]),
        )

    def test_history_and_biography_keep_distinct_evidence_sequences(self) -> None:
        history = self.reports["history"]
        self.assertEqual(2, history["sourceCoverage"]["historyNodeCount"])
        self.assertEqual(1, len(history["contradictions"]))
        sword = next(
            node
            for node in history["materialEvidence"]
            if node["nodeId"] == "object_sword"
        )
        self.assertEqual([19.12345, 54.12345], sword["coordinate"])
        self.assertIn("google.com/maps", sword["googleMapsLink"])
        self.assertEqual(
            ["origin_excavation_1984", "origin_museum_catalogue"],
            sword["citations"]["originFamilyIds"],
        )
        self.assertEqual(
            "blade typology plus associated coin",
            sword["classificationAndDating"]["datingBasis"],
        )
        biography = self.reports["biography"]
        archaeological_kinds = {
            node["kind"] for node in biography["archaeologicalSequence"]
        }
        custody_kinds = {
            node["kind"] for node in biography["recordAndCustodySequence"]
        }
        self.assertIn("find-event", archaeological_kinds)
        self.assertIn("repository", custody_kinds)
        self.assertIn("analysis", custody_kinds)
        self.assertIn("custody-event", custody_kinds)
        self.assertEqual(
            2,
            biography["coverageDenominators"]["distinctOriginFamilyCount"],
        )

    def test_material_report_preserves_lineage_context_and_exact_findspot(
        self,
    ) -> None:
        report = self.reports["material"]
        strongest = report["strongestEvidence"]
        self.assertEqual(
            [19.33333, 54.33333],
            strongest["spatialEvidence"]["findspot"]["coordinates"],
        )
        self.assertIn(
            "google.com/maps",
            strongest["spatialEvidence"]["findspot"]["googleMapsLink"],
        )
        self.assertEqual(
            "origin_excavation_1984",
            strongest["citation"]["originFamilyId"],
        )
        self.assertEqual(
            "excavated morphology and residue",
            strongest["classification"]["basis"],
        )
        self.assertEqual(
            "sealed context assemblage",
            strongest["dating"]["basis"],
        )
        self.assertEqual(
            "three-dimensional excavation record",
            strongest["contextAndProvenience"]["provenienceQuality"],
        )
        self.assertEqual(
            "G-CR-4",
            strongest["repositoryAndCustody"]["accessionNumber"],
        )
        self.assertEqual(2, report["coverageDenominators"]["inputRecordCount"])
        self.assertEqual(1, len(report["conflictRegister"]))
        self.assertTrue(report["contactRoleSuggestions"])

    def test_gap_report_records_queries_languages_dates_failures_and_contacts(
        self,
    ) -> None:
        report = self.reports["gaps"]
        self.assertEqual(
            ["Old Crossing", "River Ford"],
            report["aliasesTried"],
        )
        self.assertEqual(["de", "en", "pl"], report["languagesTried"])
        failed = next(
            attempt
            for attempt in report["attempts"]
            if attempt["sourceId"] == "src_university"
        )
        self.assertEqual("0900", failed["dateRange"]["from"])
        self.assertEqual("provider-timeout", failed["failure"]["code"])
        self.assertEqual(
            1,
            report["coverageDenominators"]["failedAttemptCount"],
        )
        self.assertTrue(report["nextSources"])
        self.assertTrue(report["contactRoleSuggestions"])

    def test_empty_bounded_inputs_never_claim_archaeological_absence(self) -> None:
        finds = build_finds_report(
            {
                "schemaVersion": "archaeological-find-reconciliation-1.0",
                "recordCount": 0,
                "entities": [],
            },
            area_description="Bounded empty fixture",
            public=True,
        )
        self.assertEqual(
            "no-record-located-in-bounded-sources",
            finds["answer"]["status"],
        )
        self.assertFalse(finds["answer"]["archaeologicalAbsenceEstablished"])
        material = build_material_evidence_report([], "gold")
        self.assertEqual(
            "no-record-located-in-bounded-input",
            material["answerBoundary"]["matchingRecordStatus"],
        )
        self.assertFalse(material["answerBoundary"]["materialAbsenceEstablished"])


if __name__ == "__main__":
    unittest.main()
