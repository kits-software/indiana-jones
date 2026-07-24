from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from ij_adapter_protocol import build_search_ladder, resume_acquisition
from ij_adapters import adapter_descriptor
from ij_ingest import acquire_and_normalize
from ij_journal import value_sha256
from ij_source_contract import acquisition_contract


PUBLIC_SOURCE = {
    "sourceId": "src_museum",
    "accessBasis": "public",
    "license": "test fixture",
    "sensitivity": "restricted",
}


class AdapterProtocolTests(unittest.TestCase):
    def test_only_oai_claims_restartable_pagination(self) -> None:
        self.assertEqual("resumption-token", adapter_descriptor("oai-pmh")["pagination"])
        for format_name in (
            "json",
            "jsonl",
            "csv",
            "iiif",
            "rdf-xml",
            "sparql-json",
            "crossref-json",
            "openalex-json",
            "doi-json",
        ):
            with self.subTest(format_name=format_name):
                self.assertEqual("none", adapter_descriptor(format_name)["pagination"])

    def test_oai_checkpoint_is_consumed_by_a_declared_restart_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first_path = root / "page-1.xml"
            second_path = root / "page-2.xml"
            first_path.write_bytes(
                b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
                b"<ListRecords><record><metadata><identifier>A-1</identifier>"
                b"<title>Sword</title></metadata></record>"
                b"<resumptionToken>page-2</resumptionToken>"
                b"</ListRecords></OAI-PMH>"
            )
            second_path.write_bytes(
                b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
                b"<ListRecords><record><metadata><identifier>A-2</identifier>"
                b"<title>Scabbard</title></metadata></record>"
                b"<resumptionToken></resumptionToken>"
                b"</ListRecords></OAI-PMH>"
            )
            initial_query = {"verb": "ListRecords", "metadataPrefix": "oai_dc"}
            source = dict(PUBLIC_SOURCE)
            source["acquisition"] = acquisition_contract(
                source,
                locator=str(first_path),
                format_name="oai-pmh",
                query=initial_query,
                snapshot_sha256=hashlib.sha256(first_path.read_bytes()).hexdigest(),
                retrieved_at="2026-07-24T10:00:00Z",
            )
            source["acquisition"]["resumePages"] = [
                {
                    "cursor": "page-2",
                    "locator": str(second_path),
                    "snapshotSha256": hashlib.sha256(
                        second_path.read_bytes()
                    ).hexdigest(),
                    "retrievedAt": "2026-07-24T10:01:00Z",
                }
            ]
            first_out = root / "normalized-1.json"
            first = acquire_and_normalize(
                source=source,
                locator=str(first_path),
                format_name="oai-pmh",
                out=first_out,
                query=initial_query,
            )
            second = resume_acquisition(
                previous_artifact=first_out,
                source=source,
                out=root / "normalized-2.json",
            )
            self.assertEqual("A-2", second["records"][0]["sourceRecordId"])
            self.assertTrue(second["queryArtifact"]["checkpoint"]["sourceExhausted"])
            self.assertEqual(
                first["queryArtifact"]["checkpoint"]["checkpointId"],
                second["queryArtifact"]["query"]["previousCheckpointId"],
            )

    def test_non_oai_checkpoint_cannot_claim_restart_support(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first_path = root / "page-1.json"
            second_path = root / "page-2.json"
            first_path.write_text(
                json.dumps({"records": [{"identifier": "A-1"}]}),
                encoding="utf-8",
            )
            second_path.write_text(
                json.dumps({"records": [{"identifier": "A-2"}]}),
                encoding="utf-8",
            )
            source = dict(PUBLIC_SOURCE)
            source["acquisition"] = acquisition_contract(
                source,
                locator=str(first_path),
                format_name="json",
                query={"page": 1},
                snapshot_sha256=hashlib.sha256(first_path.read_bytes()).hexdigest(),
                retrieved_at="2026-07-24T10:00:00Z",
            )
            source["acquisition"]["resumePages"] = [
                {
                    "cursor": "page-2",
                    "locator": str(second_path),
                    "snapshotSha256": hashlib.sha256(
                        second_path.read_bytes()
                    ).hexdigest(),
                    "retrievedAt": "2026-07-24T10:01:00Z",
                }
            ]
            first_out = root / "normalized-1.json"
            artifact = acquire_and_normalize(
                source=source,
                locator=str(first_path),
                format_name="json",
                out=first_out,
                query={"page": 1},
            )
            pagination = artifact["queryArtifact"]["pagination"]
            pagination.update(
                {"sourceExhausted": False, "resumeCursor": "page-2"}
            )
            basis = {
                "sourceId": artifact["queryArtifact"]["sourceId"],
                "adapter": artifact["queryArtifact"]["adapter"],
                "adapterVersion": artifact["queryArtifact"]["adapterVersion"],
                "query": artifact["queryArtifact"]["query"],
                "rawArtifactSha256": artifact["queryArtifact"]["rawArtifactSha256"],
                "pagination": pagination,
            }
            artifact["queryArtifact"]["checkpoint"].update(
                {
                    "checkpointId": value_sha256(basis),
                    "sourceExhausted": False,
                    "resumeCursor": "page-2",
                }
            )
            first_out.write_text(json.dumps(artifact), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "only for OAI-PMH"):
                resume_acquisition(
                    previous_artifact=first_out,
                    source=source,
                    out=root / "normalized-2.json",
                )

    def test_search_ladder_expands_aliases_and_terms_deterministically(self) -> None:
        first = build_search_ladder(
            place_aliases=["Eboracum", "York", "York"],
            object_terms=["sword", "hoard"],
            language_variants=["gladius"],
            broader_terms=["weapon fitting"],
            maximum=20,
        )
        second = build_search_ladder(
            place_aliases=["York", "Eboracum"],
            object_terms=["hoard", "sword"],
            language_variants=["gladius"],
            broader_terms=["weapon fitting"],
            maximum=20,
        )
        self.assertEqual(first, second)
        self.assertTrue(any(item["term"] == "gladius" for item in first))
        self.assertTrue(
            any(
                item["term"] == "weapon fitting"
                and item["stage"] == "broader-object-and-material-terms"
                for item in first
            )
        )
        self.assertEqual(len(first), len({item["queryId"] for item in first}))


if __name__ == "__main__":
    unittest.main()
