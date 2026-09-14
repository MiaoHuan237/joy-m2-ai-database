from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import OutputConflictError
from tests.unit.test_hkdse_pdf_adapter import AdapterCase, adapter


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


class HkdsePdfProposalIntegrationTests(AdapterCase):
    def test_transcription_digest_reconstructs_from_semantic_payload(self):
        batch = self.propose()
        payload = json.loads(batch.transcription_path.read_text(encoding="utf-8"))
        digest = payload.pop("transcription_digest")
        reconstructed = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
        self.assertEqual(digest, reconstructed)
        self.assertEqual(batch.transcription_digest, reconstructed)
        self.assertTrue(batch.transcription_path.read_bytes().endswith(b"\n"))

    def test_equivalent_roots_produce_identical_semantic_artifacts(self):
        first = self.propose()
        second_root = self.root / "equivalent-root"
        for name in ("data/staging", "data/baselines", "releases"):
            (second_root / name).mkdir(parents=True, exist_ok=True)
        second_output = second_root / "data" / "staging" / "review"
        second = adapter(self).propose_hkdse_pdf_transcription(
            self.staging,
            self.pp,
            self.ms,
            self.pass_a,
            self.pass_b,
            second_output,
            PipelineConfig(second_root),
        )
        self.assertEqual(first.transcription_digest, second.transcription_digest)
        for name in (
            "transcription.json",
            "extraction-pass-a.json",
            "extraction-pass-b.json",
            "PDF_TRANSCRIPTION_REVIEW.md",
        ):
            self.assertEqual(
                (first.artifact_root / name).read_bytes(),
                (second.artifact_root / name).read_bytes(),
            )

    def test_review_report_is_compact_and_contains_required_question_evidence(self):
        batch = self.propose()
        report = batch.review_path.read_text(encoding="utf-8")
        self.assertIn("JOY-M2-HKDSE-2012-PP-MS", report)
        self.assertIn("HKDSE-2012-M2-Q01", report)
        self.assertIn("PP pages: 2-2", report)
        self.assertIn("MS pages: 1-1", report)
        self.assertIn("Status: PROPOSED", report)
        self.assertIn("Auto agree: 1", report)
        self.assertNotIn(str(self.root), report)

    def test_existing_output_is_not_replaced(self):
        first = self.propose()
        before = {
            path.name: path.read_bytes() for path in first.artifact_root.iterdir()
        }
        with self.assertRaises(OutputConflictError):
            self.propose()
        after = {
            path.name: path.read_bytes() for path in first.artifact_root.iterdir()
        }
        self.assertEqual(after, before)


if __name__ == "__main__":
    import unittest

    unittest.main()
