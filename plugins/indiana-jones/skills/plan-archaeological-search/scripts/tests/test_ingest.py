from __future__ import annotations

import json
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from ij_ingest import (
    acquire_and_normalize,
    assessment_summary,
    discover_source_candidates,
    normalize_record,
    pagination_metadata,
    parse_records,
    reconcile_artifacts,
)
from ij_ingest_guard import ValidatingRedirectHandler


PUBLIC_SOURCE = {
    "sourceId": "src_museum",
    "accessBasis": "public",
    "license": "test fixture",
    "sensitivity": "restricted",
}


class SourceParsingTests(unittest.TestCase):
    def test_findspot_sensitivity_preserves_public_and_explicit_restrictions(self) -> None:
        public = normalize_record(
            {"identifier": "A-1", "findspot": "Public catalogue point"},
            source_id="src_public",
            index=1,
            sensitivity="public",
        )
        self.assertEqual("public", public["findspot"]["sensitivity"])
        restricted = normalize_record(
            {"identifier": "A-2", "findspot": "Protected catalogue point"},
            source_id="src_public",
            index=2,
            sensitivity="public",
            spatial_restriction="authority-only",
        )
        self.assertEqual("restricted", restricted["findspot"]["sensitivity"])
        self.assertEqual("authority-only", restricted["spatialRestriction"])

    def test_json_csv_jsonl_iiif_and_xml_adapters_are_bounded(self) -> None:
        self.assertEqual(
            "Sword",
            parse_records(b'{"records":[{"title":"Sword"}]}', "json")[0]["title"],
        )
        self.assertEqual(
            "Sword",
            parse_records(b"title,material\nSword,iron\n", "csv")[0]["title"],
        )
        self.assertEqual(
            "Sword",
            parse_records(b'{"title":"Sword"}\n', "jsonl")[0]["title"],
        )
        self.assertEqual(
            "Sword",
            parse_records(b'{"items":[{"label":"Sword"}]}', "iiif")[0]["label"],
        )
        iiif = parse_records(
            b'{"items":[{"label":{"en":["Gold pendant"]}}]}',
            "iiif",
        )
        normalized = normalize_record(
            iiif[0],
            source_id="src_iiif",
            index=1,
            sensitivity="restricted",
        )
        self.assertEqual("Gold pendant", normalized["title"])
        sparql = parse_records(
            b'{"results":{"bindings":[{"title":{"type":"literal","value":"Sword"}}]}}',
            "sparql-json",
        )
        self.assertEqual("Sword", normalize_record(
            sparql[0],
            source_id="src_sparql",
            index=1,
            sensitivity="restricted",
        )["title"])
        crossref = parse_records(
            b'{"message":{"items":[{"DOI":"10.1/example","title":["Sword study"]}]}}',
            "crossref-json",
        )
        self.assertEqual("10.1/example", crossref[0]["DOI"])
        openalex = parse_records(
            b'{"results":[{"id":"https://openalex.org/W1","title":"Gold study"}]}',
            "openalex-json",
        )
        self.assertEqual("Gold study", openalex[0]["title"])
        doi = parse_records(
            b'{"DOI":"10.1/single","title":"Hoard report"}',
            "doi-json",
        )
        self.assertEqual("10.1/single", doi[0]["DOI"])
        oai = (
            b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
            b"<ListRecords><record><metadata><title>Sword</title></metadata>"
            b"</record></ListRecords></OAI-PMH>"
        )
        self.assertEqual("Sword", parse_records(oai, "oai-pmh")[0]["title"])
        rdf = (
            b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            b"<rdf:Description><title>Gold pendant</title></rdf:Description></rdf:RDF>"
        )
        self.assertEqual(
            "Gold pendant",
            parse_records(rdf, "rdf-xml")[0]["title"],
        )

    def test_json_record_containers_reject_mixed_or_scalar_records(self) -> None:
        for payload in (
            b'[{"title":"Sword"}, 7]',
            b'{"records":[{"title":"Sword"}, "silently lost"]}',
        ):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, "must be an object"):
                    parse_records(payload, "json")

    def test_json_rejects_duplicate_keys_and_non_standard_numbers(self) -> None:
        for payload in (
            b'{"records":[{"title":"Sword","title":"Dagger"}]}',
            b'{"records":[{"weight":NaN}]}',
        ):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, "duplicate key|numeric constant"):
                    parse_records(payload, "json")

    def test_csv_rejects_ambiguous_headers_and_ragged_rows(self) -> None:
        fixtures = {
            "duplicate": b"title,Title\nSword,Iron sword\n",
            "empty": b"title,\nSword,iron\n",
            "short": b"title,material\nSword\n",
            "long": b"title,material\nSword,iron,extra\n",
        }
        for name, payload in fixtures.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "CSV"):
                    parse_records(payload, "csv")

    def test_xml_declarations_are_rejected_independently_of_encoding(self) -> None:
        document = (
            '<?xml version="1.0" encoding="UTF-16"?>'
            '<!DOCTYPE rdf:RDF [<!ENTITY loot "Gold">]>'
            '<rdf:RDF xmlns:rdf="urn:rdf">'
            "<rdf:Description><title>&loot;</title></rdf:Description>"
            "</rdf:RDF>"
        ).encode("utf-16")
        with self.assertRaisesRegex(ValueError, "entity declarations"):
            parse_records(document, "rdf-xml")

    def test_oai_skips_deleted_records_and_exposes_resumption_cursor(self) -> None:
        payload = (
            b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
            b"<ListRecords>"
            b'<record><header status="deleted"><identifier>gone</identifier></header></record>'
            b"<record><header><identifier>kept</identifier></header>"
            b"<metadata><identifier>museum-7</identifier><title>Sword</title></metadata>"
            b"</record>"
            b'<resumptionToken cursor="0" completeListSize="25">next-page</resumptionToken>'
            b"</ListRecords></OAI-PMH>"
        )
        records = parse_records(payload, "oai-pmh")
        self.assertEqual(1, len(records))
        self.assertEqual("Sword", records[0]["title"])
        self.assertEqual("kept", records[0]["oaiIdentifier"])
        self.assertEqual("museum-7", records[0]["identifier"])
        pagination = pagination_metadata(payload, "oai-pmh")
        self.assertFalse(pagination["sourceExhausted"])
        self.assertEqual("next-page", pagination["resumptionToken"])
        self.assertEqual("25", pagination["completeListSize"])

    def test_iiif_manifest_keeps_top_level_metadata(self) -> None:
        manifest = {
            "id": "https://example.org/manifest/1",
            "type": "Manifest",
            "label": {"en": ["Gold pendant catalogue"]},
            "metadata": [{"label": {"en": ["Period"]}, "value": {"en": ["Roman"]}}],
            "items": [{"id": "https://example.org/canvas/1", "type": "Canvas"}],
        }
        record = parse_records(json.dumps(manifest).encode(), "iiif")[0]
        self.assertEqual(manifest["id"], record["id"])
        self.assertEqual(manifest["metadata"], record["metadata"])
        self.assertEqual(manifest["items"], record["items"])
        normalized = normalize_record(
            record,
            source_id="src_iiif_manifest",
            index=1,
            sensitivity="restricted",
        )
        self.assertEqual(manifest["metadata"], normalized["sourceMetadata"])

    def test_rdf_attributes_are_preserved_as_evidence(self) -> None:
        rdf = (
            b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
            b'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            b'<rdf:Description rdf:about="https://example.org/object/1">'
            b'<dc:creator rdf:resource="https://example.org/person/2"/>'
            b"</rdf:Description></rdf:RDF>"
        )
        record = parse_records(rdf, "rdf-xml")[0]
        self.assertEqual("https://example.org/object/1", record["@about"])
        self.assertEqual("https://example.org/person/2", record["creator"])
        self.assertEqual(
            "https://example.org/person/2",
            record["creator.@resource"],
        )
        normalized = normalize_record(
            record,
            source_id="src_rdf",
            index=1,
            sensitivity="restricted",
        )
        self.assertEqual(
            "https://example.org/object/1",
            normalized["sourceAttributes"]["@about"],
        )

    def test_redirect_handler_rejects_private_target_before_following(self) -> None:
        handler = ValidatingRedirectHandler()
        request = urllib.request.Request("https://example.org/public")
        with self.assertRaisesRegex(ValueError, "private|loopback|reserved"):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "http://127.0.0.1/private",
            )

    def test_ingestion_preserves_query_raw_hash_and_normalization_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "records.csv"
            source_path.write_text(
                "identifier,title,material,period,repository,findspot\n"
                "A-1,Sword,iron,medieval,Test Museum,Exact field\n",
                encoding="utf-8",
            )
            out = root / "normalized.json"
            artifact = acquire_and_normalize(
                source=PUBLIC_SOURCE,
                locator=str(source_path),
                format_name="csv",
                out=out,
                max_bytes=10_000,
                max_records=10,
                query={"term": "sword", "page": 1},
            )
            query = artifact["queryArtifact"]
            self.assertEqual({"term": "sword", "page": 1}, query["query"])
            self.assertEqual(64, len(query["rawArtifactSha256"]))
            self.assertEqual(
                {
                    "sha256": query["rawArtifactSha256"],
                    "bytes": source_path.stat().st_size,
                    "relation": "result-attachment",
                    "sourceName": "normalized.json.raw",
                },
                query["rawArtifactRef"],
            )
            self.assertEqual("archaeological-find-v1", query["normalizationVersion"])
            checkpoint = query["checkpoint"]
            self.assertEqual(query["rawArtifactSha256"], checkpoint["rawArtifactSha256"])
            self.assertEqual(64, len(checkpoint["checkpointId"]))
            self.assertEqual(64, len(checkpoint["querySha256"]))
            self.assertTrue(checkpoint["sourceExhausted"])
            self.assertIsNone(checkpoint["resumeCursor"])
            record = artifact["records"][0]
            self.assertIn("weapon", record["riskClasses"])
            self.assertEqual("restricted", record["findspot"]["sensitivity"])

    def test_oai_acquisition_emits_bound_resumption_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "records.xml"
            source_path.write_bytes(
                b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
                b"<ListRecords><record><metadata><title>Sword</title></metadata>"
                b"</record><resumptionToken>next-page</resumptionToken>"
                b"</ListRecords></OAI-PMH>"
            )
            artifact = acquire_and_normalize(
                source=PUBLIC_SOURCE,
                locator=str(source_path),
                format_name="oai-pmh",
                out=root / "normalized.json",
                query={"metadataPrefix": "oai_dc"},
            )
            checkpoint = artifact["queryArtifact"]["checkpoint"]
            self.assertFalse(checkpoint["sourceExhausted"])
            self.assertEqual("next-page", checkpoint["resumeCursor"])
            self.assertEqual(
                artifact["queryArtifact"]["rawArtifactSha256"],
                checkpoint["rawArtifactSha256"],
            )

    def test_acquisition_rejects_invalid_timeout_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "records.json"
            source_path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "timeout_seconds"):
                acquire_and_normalize(
                    source=PUBLIC_SOURCE,
                    locator=str(source_path),
                    format_name="json",
                    out=root / "normalized.json",
                    timeout_seconds=0,
                )

    def test_ingestion_rejects_nested_credential_keys_and_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "records.json"
            source_path.write_text("[]", encoding="utf-8")
            queries = (
                {"filters": [{"client_secret": "not-written"}]},
                {"filters": [{"term": "Bearer ABC"}]},
                {"filters": [{"term": "Authorization%3A%20Bearer%20ABC"}]},
                {"filters": [{"url": "https://user:password@example.org/data"}]},
            )
            for index, query in enumerate(queries):
                with self.subTest(query=query):
                    with self.assertRaisesRegex(ValueError, "credential"):
                        acquire_and_normalize(
                            source=PUBLIC_SOURCE,
                            locator=str(source_path),
                            format_name="json",
                            out=root / f"out-{index}.json",
                            query=query,
                        )

    def test_local_acquisition_stops_at_byte_limit_before_persisting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "records.json"
            source_path.write_bytes(b"[" + (b" " * 100) + b"]")
            out = root / "normalized.json"
            with self.assertRaisesRegex(ValueError, "exceeds max_bytes"):
                acquire_and_normalize(
                    source=PUBLIC_SOURCE,
                    locator=str(source_path),
                    format_name="json",
                    out=out,
                    max_bytes=20,
                )
            self.assertFalse(out.exists())
            self.assertFalse(out.with_suffix(out.suffix + ".raw").exists())

    def test_parse_failure_leaves_no_partial_raw_attachment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "records.json"
            source_path.write_text('{"records":[1]}', encoding="utf-8")
            out = root / "normalized.json"
            with self.assertRaisesRegex(ValueError, "must be an object"):
                acquire_and_normalize(
                    source=PUBLIC_SOURCE,
                    locator=str(source_path),
                    format_name="json",
                    out=out,
                )
            self.assertFalse(out.exists())
            self.assertFalse(out.with_suffix(out.suffix + ".raw").exists())

    def test_automated_ingestion_rejects_non_public_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "records.json"
            source_path.write_text("[]", encoding="utf-8")
            source = {**PUBLIC_SOURCE, "accessBasis": "authenticated"}
            with self.assertRaisesRegex(ValueError, "local ingestion requires"):
                acquire_and_normalize(
                    source=source,
                    locator=str(source_path),
                    format_name="json",
                    out=root / "out.json",
                )

    def test_local_user_provided_snapshot_is_represented_honestly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "records.json"
            source_path.write_text(
                '{"records":[{"identifier":"U-1","title":"User record"}]}',
                encoding="utf-8",
            )
            source = {
                **PUBLIC_SOURCE,
                "sourceId": "src_user_snapshot",
                "accessBasis": "user-provided",
                "license": "User supplied for this bounded case",
            }
            artifact = acquire_and_normalize(
                source=source,
                locator=str(source_path),
                format_name="json",
                out=root / "out.json",
            )
            self.assertEqual(
                "user-provided",
                artifact["queryArtifact"]["accessBasis"],
            )

    def test_remote_discovery_requires_explicit_terms_and_automation_decision(self) -> None:
        source = {
            **PUBLIC_SOURCE,
            "license": "CC0 public catalogue",
            "providerTerms": "public API permits bounded automated research",
            "acquisition": {
                "locator": "https://example.org/records.json",
                "format": "json",
            },
        }
        candidate = discover_source_candidates({"sources": [source]})["candidates"][0]
        self.assertFalse(candidate["executable"])
        self.assertTrue(candidate["authorizationRequired"])
        source["acquisition"].update(
            {
                "automationAuthorized": True,
                "automationBasis": "provider terms section 3",
                "automationCheckedAt": "2026-07-24",
                "adapterVersion": "1.0.0",
                "retentionPolicy": "retain-snapshot",
                "retentionBasis": "Provider permits research snapshots.",
                "retentionDecision": "permitted",
                "retentionEvidenceLocator": "https://example.org/terms",
                "retentionCheckedAt": "2026-07-24",
                "rateLimit": {"requestsPerMinute": 30, "maxConcurrency": 1},
            }
        )
        candidate = discover_source_candidates({"sources": [source]})["candidates"][0]
        self.assertTrue(candidate["executable"])
        self.assertFalse(candidate["authorizationRequired"])
        source["providerTerms"] = "View only; no automated retention or local copies."
        candidate = discover_source_candidates({"sources": [source]})["candidates"][0]
        self.assertFalse(candidate["executable"])


class FindNormalizationTests(unittest.TestCase):
    def test_gold_object_does_not_become_production_evidence(self) -> None:
        record = normalize_record(
            {
                "identifier": "G-1",
                "title": "Gold pendant",
                "material": "gold",
            },
            source_id="src_museum",
            index=1,
            sensitivity="restricted",
        )
        self.assertIn("precious-material-object", record["evidenceClasses"])
        self.assertNotIn("material-production", record["evidenceClasses"])
        self.assertEqual("precious-metal", record["materialAssessment"]["materialClass"])

    def test_material_evidence_separates_metal_surface_and_colour_claims(self) -> None:
        fixtures = (
            (
                {"title": "Gold-coloured brooch"},
                "colour-description",
                None,
            ),
            (
                {"title": "Golden eagle emblem"},
                "colour-description",
                None,
            ),
            (
                {"title": "Gilded fitting", "material": "gilded copper"},
                "surface-treatment",
                "precious-surface-treatment",
            ),
            (
                {"title": "Assayed fragment", "material": "Au 92%"},
                "precious-metal",
                "precious-material-object",
            ),
            (
                {"title": "Pierścień", "material": "złoto"},
                "precious-metal",
                "precious-material-object",
            ),
        )
        for index, (source, material_class, evidence_class) in enumerate(fixtures):
            with self.subTest(source=source):
                record = normalize_record(
                    source,
                    source_id="src_material",
                    index=index + 1,
                    sensitivity="restricted",
                )
                self.assertEqual(
                    material_class,
                    record["materialAssessment"]["materialClass"],
                )
                if material_class == "colour-description":
                    self.assertEqual(
                        "catalogue-title-description",
                        record["materialAssessment"]["basis"],
                    )
                if evidence_class:
                    self.assertIn(evidence_class, record["evidenceClasses"])
                else:
                    self.assertNotIn(
                        "precious-material-object",
                        record["evidenceClasses"],
                    )

    def test_crucible_is_separate_material_production_evidence(self) -> None:
        record = normalize_record(
            {
                "identifier": "C-1",
                "title": "Crucible with gold residue",
                "material": "ceramic and gold",
                "context": "secure workshop floor",
            },
            source_id="src_excavation",
            index=1,
            sensitivity="restricted",
        )
        self.assertIn("material-production", record["evidenceClasses"])
        self.assertIn("portable-high-value", record["riskClasses"])

    def test_reconciliation_merges_only_strong_accession_identity(self) -> None:
        first = normalize_record(
            {
                "accessionNumber": "A-1",
                "title": "Iron sword",
                "repository": "Test Museum",
            },
            source_id="src_one",
            index=1,
            sensitivity="restricted",
        )
        second = normalize_record(
            {
                "accessionNumber": "A-1",
                "title": "Sword",
                "repository": "Test Museum",
            },
            source_id="src_two",
            index=1,
            sensitivity="restricted",
        )
        similar = normalize_record(
            {
                "title": "Sword",
                "repository": "Test Museum",
            },
            source_id="src_three",
            index=1,
            sensitivity="restricted",
        )
        result = reconcile_artifacts(
            [
                {"records": [first, similar]},
                {"records": [second]},
            ]
        )
        self.assertEqual(2, result["entityCount"])
        merged = next(
            entity
            for entity in result["entities"]
            if entity["identityBasis"] == "accession"
        )
        self.assertEqual(2, merged["duplicateCount"])
        self.assertEqual(2, merged["independentSourceCount"])

    def test_reconciliation_entity_id_is_stable_when_sort_order_changes(self) -> None:
        target = normalize_record(
            {
                "accessionNumber": "Z-9",
                "title": "Sword",
                "repository": "Test Museum",
            },
            source_id="src_target",
            index=1,
            sensitivity="restricted",
        )
        first = reconcile_artifacts([{"records": [target]}])
        earlier = normalize_record(
            {
                "accessionNumber": "A-1",
                "title": "Brooch",
                "repository": "Earlier Museum",
            },
            source_id="src_earlier",
            index=1,
            sensitivity="restricted",
        )
        second = reconcile_artifacts([{"records": [earlier, target]}])
        first_id = first["entities"][0]["entityId"]
        second_id = next(
            entity["entityId"]
            for entity in second["entities"]
            if entity["canonicalRecord"].get("accessionNumber") == "Z-9"
        )
        self.assertEqual(first_id, second_id)

    def test_conflicted_match_has_no_arbitrary_canonical_value(self) -> None:
        first = normalize_record(
            {
                "accessionNumber": "A-1",
                "title": "Iron sword",
                "material": "iron",
                "repository": "Test Museum",
            },
            source_id="src_one",
            index=1,
            sensitivity="restricted",
        )
        second = normalize_record(
            {
                "accessionNumber": "A-1",
                "title": "Bronze sword",
                "material": "bronze",
                "repository": "Test Museum",
            },
            source_id="src_two",
            index=1,
            sensitivity="restricted",
        )
        entity = reconcile_artifacts([{"records": [first, second]}])["entities"][0]
        self.assertEqual("unresolved-conflicts", entity["canonicalStatus"])
        self.assertEqual(
            "Unresolved title (2 reported variants)",
            entity["canonicalRecord"]["title"],
        )
        self.assertNotIn("material", entity["canonicalRecord"])
        self.assertEqual(
            ["Bronze sword", "Iron sword"],
            entity["fieldConflicts"]["title"],
        )
        self.assertEqual("A-1", entity["canonicalRecord"]["accessionNumber"])

    def test_reconciliation_rejects_unbounded_artifact_lists(self) -> None:
        with self.assertRaisesRegex(ValueError, "artifact count"):
            reconcile_artifacts([{"records": []}] * 513)
        with self.assertRaisesRegex(ValueError, "record count"):
            reconcile_artifacts([{"records": [{}] * 100_001}])

    def test_assessment_refuses_to_invent_probability(self) -> None:
        reconciled = {
            "entities": [
                {
                    "sourceIds": ["src_one"],
                    "canonicalRecord": {"recordReliability": "unassessed"},
                }
            ]
        }
        summary = assessment_summary(reconciled)
        self.assertEqual("not-assessable", summary["answerability"])
        self.assertIsNone(summary["probability"])
        self.assertEqual(
            "insufficient",
            summary["qualitativeProspectiveAssessment"]["level"],
        )
        self.assertIn("calibrated", summary["probabilityReason"])


if __name__ == "__main__":
    unittest.main()
