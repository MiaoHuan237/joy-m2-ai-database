from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import OutputConflictError, PipelineError
from joy_m2.ingest.hkdse_pdf_models import HkdsePdfTranscriptionApproval
from joy_m2.ingest.v120_manifest import load_v120_import_manifest
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
        for summary in (
            "Question text complete: 1",
            "MS text complete: 1",
            "Figure questions: 0",
            "Formula mismatches: 0",
            "Page-boundary ambiguities: 0",
            "Missing content: 0",
        ):
            self.assertIn(summary, report)
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


class HkdsePdfCanonicalBridgeTests(AdapterCase):
    _CANDIDATE_FIELDS = {
        "proposed_question_id",
        "source_id",
        "source_question_number",
        "source_section",
        "source_fragment_hash",
        "question_text_original",
        "question_text_zh",
        "translation_status",
        "translation_evidence",
        "solution_original",
        "solution_verified",
        "answer_status",
        "explanation_text",
        "explanation_status",
        "explanation_evidence",
        "image_paths",
        "image_roles",
        "primary_type",
        "tags",
        "tag_status",
        "difficulty_level",
        "difficulty_status",
        "enrichment_status",
    }

    def setUp(self):
        super().setUp()
        self.proposal = self.propose()
        approval = HkdsePdfTranscriptionApproval(
            self.proposal.batch_id,
            self.proposal.transcription_digest,
            "USER APPROVED PDF TRANSCRIPTION BATCH "
            f"{self.proposal.batch_id} {self.proposal.transcription_digest}",
        )
        self.verified = adapter(self).approve_hkdse_pdf_transcription(
            self.proposal, approval
        )
        self.package_output = self.root / "data" / "staging" / "canonical"

    def bridge(self, output=None, config=None):
        module = adapter(self)
        self.assertTrue(
            hasattr(module, "adapt_verified_hkdse_pdf_transcription_v120"),
            "Task 10B verified canonical bridge must exist before behavior can pass",
        )
        return module.adapt_verified_hkdse_pdf_transcription_v120(
            self.verified,
            output or self.package_output,
            config or self.config,
        )

    def test_root_package_appends_exact_five_adapter_apis_in_order(self):
        import joy_m2.ingest as ingest

        expected = (
            "extract_hkdse_pdf_embedded_pass",
            "load_hkdse_pdf_extraction_pass",
            "propose_hkdse_pdf_transcription",
            "approve_hkdse_pdf_transcription",
            "adapt_verified_hkdse_pdf_transcription_v120",
        )
        self.assertEqual(ingest.__all__[-5:], expected)
        for name in expected:
            self.assertTrue(callable(getattr(ingest, name, None)))

    def test_verified_transcription_projects_exact_v120_package(self):
        package = self.bridge()
        self.assertEqual(package.manifest, load_v120_import_manifest(package.manifest_path))
        self.assertEqual(package.manifest.schema_version, "task10-v120-import-manifest-v1")
        self.assertEqual(package.manifest.target_release_version, "V1.20")
        self.assertEqual(
            tuple(item.relative_path for item in package.manifest.candidate_records),
            ("records/candidates.json",),
        )
        self.assertEqual(
            tuple(item.relative_path for item in package.manifest.source_files),
            ("source/transcription.json", "source/source-map.json"),
        )
        self.assertEqual(
            tuple(item.relative_path for item in package.manifest.answer_files),
            ("answers/official-ms.json",),
        )
        self.assertEqual(package.manifest.image_files, ())

    def test_candidate_is_exact_source_preserving_23_field_payload(self):
        package = self.bridge()
        candidates = json.loads(
            (package.package_root / "records" / "candidates.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(set(candidate), self._CANDIDATE_FIELDS)
        self.assertEqual(candidate["proposed_question_id"], "HKDSE-2012-M2-Q01")
        self.assertEqual(
            candidate["question_text_original"],
            self.verified.records[0].question_text_original,
        )
        self.assertEqual(
            candidate["solution_original"],
            self.verified.records[0].official_ms_original,
        )
        self.assertEqual(candidate["answer_status"], "source_provided")
        self.assertEqual(candidate["tag_status"], "proposed")
        self.assertEqual(candidate["difficulty_status"], "proposed")
        self.assertEqual(candidate["explanation_status"], "missing")
        self.assertEqual(candidate["enrichment_status"], "incomplete")
        expected_fragment = hashlib.sha256(
            self.verified.records[0].question_text_original.encode("utf-8")
        ).hexdigest()
        self.assertEqual(candidate["source_fragment_hash"], expected_fragment)

    def test_source_map_and_answer_evidence_bind_approved_transcription(self):
        package = self.bridge()
        source_map = json.loads(
            (package.package_root / "source" / "source-map.json").read_text(
                encoding="utf-8"
            )
        )
        answers = json.loads(
            (package.package_root / "answers" / "official-ms.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(source_map["transcription_digest"], self.proposal.transcription_digest)
        self.assertEqual(source_map["pp_sha256"], self.proposal.pp_sha256)
        self.assertEqual(source_map["ms_sha256"], self.proposal.ms_sha256)
        self.assertEqual(source_map["records"][0]["staging_id"], "HKDSE-2012-M2-Q01")
        self.assertEqual(
            answers["records"][0]["official_ms_original"],
            self.verified.records[0].official_ms_original,
        )
        self.assertNotIn(str(self.root), canonical_json(source_map))

    def test_unapproved_proposal_and_parallel_carrier_cannot_reach_v120_package(self):
        module = adapter(self)
        self.assertTrue(hasattr(module, "adapt_verified_hkdse_pdf_transcription_v120"))
        for value in (self.proposal, object()):
            with self.subTest(value=type(value)):
                with self.assertRaises(TypeError):
                    module.adapt_verified_hkdse_pdf_transcription_v120(
                        value, self.package_output, self.config
                    )

    def test_equivalent_staging_roots_produce_identical_package_bytes(self):
        first = self.bridge()
        second_root = self.root / "bridge-root"
        for name in ("data/staging", "data/baselines", "releases"):
            (second_root / name).mkdir(parents=True, exist_ok=True)
        second = self.bridge(
            second_root / "data" / "staging" / "canonical",
            PipelineConfig(second_root),
        )
        first_files = {
            path.relative_to(first.package_root).as_posix(): path.read_bytes()
            for path in first.package_root.rglob("*")
            if path.is_file()
        }
        second_files = {
            path.relative_to(second.package_root).as_posix(): path.read_bytes()
            for path in second.package_root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(first_files, second_files)

    def test_bridge_is_no_replace_and_does_not_touch_formal_roots(self):
        frozen_before = tuple(self.config.baselines_root.rglob("*"))
        releases_before = tuple(self.config.releases_root.rglob("*"))
        package = self.bridge()
        before = {
            path.relative_to(package.package_root): path.read_bytes()
            for path in package.package_root.rglob("*")
            if path.is_file()
        }
        with self.assertRaises(OutputConflictError):
            self.bridge()
        after = {
            path.relative_to(package.package_root): path.read_bytes()
            for path in package.package_root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(after, before)
        self.assertEqual(tuple(self.config.baselines_root.rglob("*")), frozen_before)
        self.assertEqual(tuple(self.config.releases_root.rglob("*")), releases_before)

    def test_bridge_rejects_output_inside_approved_transcription_artifacts(self):
        with self.assertRaises(PipelineError):
            self.bridge(self.proposal.artifact_root / "canonical")

    def test_bridge_rejects_symlinked_output_ancestor(self):
        physical = self.root / "data" / "staging" / "physical"
        physical.mkdir()
        alias = self.root / "data" / "staging" / "alias"
        alias.symlink_to(physical, target_is_directory=True)
        with self.assertRaises(PipelineError):
            self.bridge(alias / "canonical")

    def test_bridge_publish_failure_cleans_owned_temporary_tree(self):
        module = adapter(self)
        with mock.patch.object(
            module,
            "atomic_rename_no_replace",
            side_effect=OSError("publish failed"),
        ):
            with self.assertRaises(OSError):
                self.bridge()
        self.assertFalse(self.package_output.exists())
        self.assertEqual(
            tuple(
                self.package_output.parent.glob(
                    f".{self.package_output.name}-*"
                )
            ),
            (),
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
