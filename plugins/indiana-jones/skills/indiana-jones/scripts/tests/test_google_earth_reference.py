from __future__ import annotations

import json
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[2]
PLUGIN_DIR = SKILL_DIR.parents[1]


class GoogleEarthReferenceTests(unittest.TestCase):
    def test_skill_routes_browser_research_to_the_dedicated_reference(self) -> None:
        skill = (
            SKILL_DIR.parent / "research-google-earth" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("references/google-earth-browser.md", skill)
        self.assertIn("manual-reference", skill)

    def test_reference_preserves_the_source_and_use_boundary(self) -> None:
        reference = (
            SKILL_DIR / "references" / "google-earth-browser.md"
        ).read_text(encoding="utf-8")
        required_rules = (
            "visible foreground at a human review scale",
            "Catalog data cannot be downloaded, exported, or copied",
            "Do not traverse an AOI as a coordinate grid",
            "complete on-screen attribution text",
            "visualized in Google Earth",
            "Earth may open directly into an existing signed-in session",
            "Use accessibility or",
            "universal Google prohibition",
            "timeline label as an exact acquisition timestamp",
            "Imagery Search",
            "local KML",
            "provider-pays",
            "Detect change output is a separate derived authority",
            "Do not call heatmap intensity an archaeological probability",
            "Visible attribution does not override",
            "Decide from the source",
            "Never:",
            "inspect or call tile, imagery, scene, catalog, or hidden network endpoints",
            "Local computer vision is not inherently prohibited",
            "small, properly attributed static Earth capture",
            "training set, or substitute",
        )
        for rule in required_rules:
            with self.subTest(rule=rule):
                self.assertIn(rule, reference)

    def test_observation_template_requires_provenance_and_attribution(self) -> None:
        template_path = (
            SKILL_DIR / "assets" / "google-earth-observation-template.json"
        )
        template = json.loads(template_path.read_text(encoding="utf-8"))
        self.assertEqual("1.3", template["schemaVersion"])
        self.assertEqual("manual-reference", template["sourceRole"])
        self.assertEqual("Google Earth on web", template["product"])
        self.assertEqual(
            "https://earth.google.com/web/",
            template["officialUrl"],
        )
        self.assertIn("attributionText", template["displayedMetadata"])
        self.assertIn("providers", template["displayedMetadata"])
        catalog = template["catalogLayer"]
        self.assertFalse(catalog["used"])
        self.assertIn("sourceOrCustodian", catalog)
        self.assertIn("terms", catalog)
        self.assertIn("requiredPlan", catalog)
        self.assertIn("styles", catalog)
        self.assertIn("filters", catalog)
        imported = template["importedData"]
        self.assertFalse(imported["used"])
        self.assertIn("custodian", imported)
        self.assertIn("license", imported)
        self.assertIn("sha256", imported)
        detect_change = template["detectChange"]
        self.assertFalse(detect_change["used"])
        self.assertTrue(detect_change["experimental"])
        self.assertFalse(detect_change["projectMutationAuthorized"])
        self.assertIn("modelOrDatasetText", detect_change)
        self.assertIn("comparisonYears", detect_change)
        native_analysis = template["nativeAnalysis"]
        self.assertFalse(native_analysis["used"])
        self.assertFalse(native_analysis["promptOrLabelsTransmitted"])
        self.assertFalse(native_analysis["authorizationRecorded"])
        self.assertIn("requiredPlan", native_analysis)
        self.assertIn("displayedLimitations", native_analysis)
        measurement = template["measurement"]
        self.assertFalse(measurement["used"])
        self.assertIn("displayedValue", measurement)
        self.assertIn("displayedUnit", measurement)
        self.assertFalse(measurement["estimateCaveatRecorded"])
        local_analysis = template["exploratoryLocalAnalysis"]
        self.assertFalse(local_analysis["used"])
        self.assertFalse(local_analysis["systematicDatasetCreated"])
        self.assertIn("useBasis", local_analysis)
        self.assertIn("inputSha256", local_analysis)
        self.assertIn("sourceType", local_analysis)
        self.assertIn("derivedOutputPaths", local_analysis)
        self.assertIn("limitations", local_analysis)
        self.assertFalse(template["displayedMetadata"]["coordinatesRecorded"])
        self.assertEqual([], template["authorization"]["mutationsAllowed"])
        self.assertTrue(
            template["followUp"]["requiresLicensedAnalysisSource"]
        )

    def test_plugin_surfaces_the_google_earth_workflow(self) -> None:
        manifest = json.loads(
            (PLUGIN_DIR / ".codex-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        readme = (PLUGIN_DIR / "README.md").read_text(encoding="utf-8")
        agent = (
            SKILL_DIR.parent
            / "research-google-earth"
            / "agents"
            / "openai.yaml"
        ).read_text(encoding="utf-8")
        interface = manifest["interface"]
        self.assertIn("google earth", manifest["keywords"])
        self.assertIn("Google Earth Browser Research", interface["capabilities"])
        self.assertIn(
            "Could an older castle or settlement be hidden around this place?",
            interface["defaultPrompt"],
        )
        self.assertLessEqual(len(interface["defaultPrompt"]), 3)
        self.assertIn(
            "skills/research-google-earth/SKILL.md",
            readme,
        )
        self.assertIn("$research-google-earth", agent)


if __name__ == "__main__":
    unittest.main()
