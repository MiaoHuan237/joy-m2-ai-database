from __future__ import annotations

import importlib
import importlib.util
from dataclasses import MISSING, FrozenInstanceError, fields, is_dataclass
from pathlib import Path
import sys
import unittest
from typing import get_type_hints


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.errors import PipelineError


MODULE_NAME = "joy_m2.ingest.hkdse_pdf_models"
HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64


def pdf_models(test_case: unittest.TestCase):
    spec = importlib.util.find_spec(MODULE_NAME)
    test_case.assertIsNotNone(
        spec,
        "Task 10B hkdse_pdf_models must exist before public contracts can pass",
    )
    return importlib.import_module(MODULE_NAME)


def extraction_record(module, **overrides):
    values = dict(
        staging_id="HKDSE-2012-M2-Q01",
        question_pages=module.HkdsePdfPageSpan(2, 2),
        ms_pages=module.HkdsePdfPageSpan(1, 1),
        question_text_original="1. Let f(x) = e^{2x}. Find f'(0).",
        official_ms_original="f'(x)=2e^{2x}; f'(0)=2. M1A1",
        subparts=(),
        marks=3,
        figure_references=(),
        question_method="embedded_text",
        ms_method="visual_review",
    )
    values.update(overrides)
    return module.HkdsePdfExtractionRecord(**values)


def extraction_pass(module, **overrides):
    values = dict(
        pass_id="A",
        staging_sha256=HEX_A,
        pp_sha256=HEX_B,
        ms_sha256=HEX_C,
        records=(extraction_record(module),),
    )
    values.update(overrides)
    return module.HkdsePdfExtractionPass(**values)


def issue(module, **overrides):
    values = dict(
        code="question_text_mismatch",
        severity="review_required",
        staging_id="HKDSE-2012-M2-Q01",
        field="question_text_original",
        evidence='{"pass_a_sha256":"a","pass_b_sha256":"b"}',
    )
    values.update(overrides)
    return module.HkdsePdfTranscriptionIssue(**values)


def transcription_record(module, **overrides):
    values = dict(
        staging_id="HKDSE-2012-M2-Q01",
        year=2012,
        section="A",
        question_number=1,
        question_pages=module.HkdsePdfPageSpan(2, 2),
        ms_pages=module.HkdsePdfPageSpan(1, 1),
        question_text_original="1. Let f(x) = e^{2x}. Find f'(0).",
        official_ms_original="f'(x)=2e^{2x}; f'(0)=2. M1A1",
        subparts=(),
        marks=3,
        figure_references=(),
        question_methods=("embedded_text", "visual_review"),
        ms_methods=("visual_review", "layout_ocr"),
        status="PROPOSED",
        review_reasons=(),
        module_proposal="T05",
        topic_proposal="first-principles derivative",
        difficulty_proposal=2,
        tag_proposals=("dse_pp", "official_marking_scheme"),
    )
    values.update(overrides)
    return module.HkdsePdfTranscriptionRecord(**values)


def transcription_batch(module, **overrides):
    root = Path("/tmp/task10b-review")
    values = dict(
        batch_id="JOY-M2-HKDSE-2012-PP-MS",
        staging_sha256=HEX_A,
        pp_sha256=HEX_B,
        ms_sha256=HEX_C,
        records=(transcription_record(module),),
        issues=(),
        transcription_digest="d" * 64,
        artifact_root=root,
        transcription_path=root / "transcription.json",
        review_path=root / "PDF_TRANSCRIPTION_REVIEW.md",
    )
    values.update(overrides)
    return module.HkdsePdfTranscriptionBatch(**values)


class HkdsePdfPublicModelTests(unittest.TestCase):
    def test_exact_fields_types_no_defaults_and_frozen(self):
        module = pdf_models(self)
        expected = {
            module.HkdsePdfPageSpan: (
                ("start_page", "end_page"),
                {"start_page": int, "end_page": int},
            ),
            module.HkdsePdfExtractionRecord: (
                (
                    "staging_id", "question_pages", "ms_pages",
                    "question_text_original", "official_ms_original", "subparts",
                    "marks", "figure_references", "question_method", "ms_method",
                ),
                {
                    "staging_id": str,
                    "question_pages": module.HkdsePdfPageSpan,
                    "ms_pages": module.HkdsePdfPageSpan,
                    "question_text_original": str,
                    "official_ms_original": str,
                    "subparts": tuple[str, ...],
                    "marks": int,
                    "figure_references": tuple[str, ...],
                    "question_method": str,
                    "ms_method": str,
                },
            ),
            module.HkdsePdfExtractionPass: (
                ("pass_id", "staging_sha256", "pp_sha256", "ms_sha256", "records"),
                {
                    "pass_id": str,
                    "staging_sha256": str,
                    "pp_sha256": str,
                    "ms_sha256": str,
                    "records": tuple[module.HkdsePdfExtractionRecord, ...],
                },
            ),
            module.HkdsePdfTranscriptionIssue: (
                ("code", "severity", "staging_id", "field", "evidence"),
                {
                    "code": str,
                    "severity": str,
                    "staging_id": str | None,
                    "field": str,
                    "evidence": str,
                },
            ),
            module.HkdsePdfTranscriptionRecord: (
                (
                    "staging_id", "year", "section", "question_number",
                    "question_pages", "ms_pages", "question_text_original",
                    "official_ms_original", "subparts", "marks",
                    "figure_references", "question_methods", "ms_methods", "status",
                    "review_reasons", "module_proposal", "topic_proposal",
                    "difficulty_proposal", "tag_proposals",
                ),
                {
                    "staging_id": str,
                    "year": int,
                    "section": str,
                    "question_number": int,
                    "question_pages": module.HkdsePdfPageSpan,
                    "ms_pages": module.HkdsePdfPageSpan,
                    "question_text_original": str,
                    "official_ms_original": str,
                    "subparts": tuple[str, ...],
                    "marks": int,
                    "figure_references": tuple[str, ...],
                    "question_methods": tuple[str, ...],
                    "ms_methods": tuple[str, ...],
                    "status": str,
                    "review_reasons": tuple[str, ...],
                    "module_proposal": str,
                    "topic_proposal": str,
                    "difficulty_proposal": int,
                    "tag_proposals": tuple[str, ...],
                },
            ),
            module.HkdsePdfTranscriptionBatch: (
                (
                    "batch_id", "staging_sha256", "pp_sha256", "ms_sha256",
                    "records", "issues", "transcription_digest", "artifact_root",
                    "transcription_path", "review_path",
                ),
                {
                    "batch_id": str,
                    "staging_sha256": str,
                    "pp_sha256": str,
                    "ms_sha256": str,
                    "records": tuple[module.HkdsePdfTranscriptionRecord, ...],
                    "issues": tuple[module.HkdsePdfTranscriptionIssue, ...],
                    "transcription_digest": str,
                    "artifact_root": Path,
                    "transcription_path": Path,
                    "review_path": Path,
                },
            ),
            module.HkdsePdfTranscriptionApproval: (
                ("batch_id", "transcription_digest", "approval_text"),
                {"batch_id": str, "transcription_digest": str, "approval_text": str},
            ),
            module.VerifiedHkdsePdfTranscriptionBatch: (
                ("proposal", "approval", "records"),
                {
                    "proposal": module.HkdsePdfTranscriptionBatch,
                    "approval": module.HkdsePdfTranscriptionApproval,
                    "records": tuple[module.HkdsePdfTranscriptionRecord, ...],
                },
            ),
        }
        instances = (
            module.HkdsePdfPageSpan(1, 2),
            extraction_record(module),
            extraction_pass(module),
            issue(module),
            transcription_record(module),
            transcription_batch(module),
            module.HkdsePdfTranscriptionApproval(
                "JOY-M2-HKDSE-2012-PP-MS",
                "d" * 64,
                "USER APPROVED PDF TRANSCRIPTION BATCH "
                "JOY-M2-HKDSE-2012-PP-MS " + "d" * 64,
            ),
        )
        approval = instances[-1]
        verified_records = (transcription_record(module, status="VERIFIED"),)
        instances += (
            module.VerifiedHkdsePdfTranscriptionBatch(
                transcription_batch(module), approval, verified_records
            ),
        )
        for carrier, (names, hints) in expected.items():
            with self.subTest(carrier=carrier.__name__):
                self.assertTrue(is_dataclass(carrier))
                self.assertEqual(tuple(field.name for field in fields(carrier)), names)
                self.assertEqual(get_type_hints(carrier), hints)
                self.assertTrue(
                    all(
                        field.default is MISSING and field.default_factory is MISSING
                        for field in fields(carrier)
                    )
                )
        for value in instances:
            with self.subTest(instance=type(value).__name__), self.assertRaises(
                FrozenInstanceError
            ):
                setattr(value, fields(value)[0].name, "changed")

    def test_page_span_rejects_bool_zero_and_inverted_range(self):
        module = pdf_models(self)
        for start, end in ((True, 2), (0, 2), (3, 2), (1, False)):
            with self.subTest(start=start, end=end), self.assertRaises(PipelineError):
                module.HkdsePdfPageSpan(start, end)

    def test_extraction_record_copies_tuples_and_rejects_unknown_methods(self):
        module = pdf_models(self)
        subparts = ["(a)", "(b)"]
        figures = ["pp:" + HEX_B + "#page=2#region=figure-1"]
        record = extraction_record(module, subparts=subparts, figure_references=figures)
        subparts.clear()
        figures.clear()
        self.assertEqual(record.subparts, ("(a)", "(b)"))
        self.assertEqual(
            record.figure_references,
            ("pp:" + HEX_B + "#page=2#region=figure-1",),
        )
        with self.assertRaises(PipelineError):
            extraction_record(module, question_method="generic_ocr")

    def test_extraction_pass_validates_identity_and_exact_record_types(self):
        module = pdf_models(self)
        for overrides in (
            {"pass_id": "C"},
            {"staging_sha256": "A" * 64},
            {"records": [object()]},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(PipelineError):
                extraction_pass(module, **overrides)

    def test_issue_taxonomy_severity_evidence_and_stable_sort_key(self):
        module = pdf_models(self)
        with self.assertRaises(PipelineError):
            issue(module, code="generic_failure")
        with self.assertRaises(PipelineError):
            issue(module, severity="warning")
        with self.assertRaises(PipelineError):
            issue(module, evidence='{"path":"/private/source.pdf"}')
        first = issue(module, evidence='{"n":2}')
        second = issue(module, evidence='{"n":1}')
        batch = transcription_batch(
            module,
            records=(transcription_record(module, status="REVIEW_REQUIRED", review_reasons=("question_text_mismatch",)),),
            issues=(first, second),
        )
        self.assertEqual(tuple(item.evidence for item in batch.issues), ('{"n":1}', '{"n":2}'))

    def test_transcription_record_preserves_raw_text_and_validates_status(self):
        module = pdf_models(self)
        raw = " x − 1  \n\n"
        record = transcription_record(module, question_text_original=raw)
        self.assertEqual(record.question_text_original, raw)
        with self.assertRaises(PipelineError):
            transcription_record(module, status="AUTO_AGREE")
        with self.assertRaises(PipelineError):
            transcription_record(module, year=True)

    def test_batch_validates_paths_and_derives_metrics(self):
        module = pdf_models(self)
        records = (
            transcription_record(module),
            transcription_record(
                module,
                staging_id="HKDSE-2012-M2-Q02",
                question_number=2,
                question_text_original="",
                official_ms_original="",
                status="REVIEW_REQUIRED",
                review_reasons=("question_text_missing", "official_ms_missing"),
                figure_references=("pp:" + HEX_B + "#page=2#region=figure-1",),
            ),
        )
        issues = (
            issue(
                module,
                code="question_text_missing",
                staging_id="HKDSE-2012-M2-Q02",
                field="question_text_original",
                evidence='{"reason":"empty"}',
            ),
            issue(
                module,
                code="official_ms_missing",
                staging_id="HKDSE-2012-M2-Q02",
                field="official_ms_original",
                evidence='{"reason":"empty"}',
            ),
        )
        batch = transcription_batch(module, records=records, issues=issues)
        self.assertEqual(batch.total_questions, 2)
        self.assertEqual(batch.auto_agree_count, 1)
        self.assertEqual(batch.review_required_count, 1)
        self.assertEqual(batch.question_complete_count, 1)
        self.assertEqual(batch.ms_complete_count, 1)
        self.assertEqual(batch.figure_question_count, 1)
        self.assertEqual(batch.missing_content_count, 2)
        with self.assertRaises(PipelineError):
            transcription_batch(module, transcription_path=Path("/tmp/elsewhere.json"))

    def test_approval_and_verified_envelope_close_identity(self):
        module = pdf_models(self)
        proposal = transcription_batch(module)
        approval = module.HkdsePdfTranscriptionApproval(
            proposal.batch_id,
            proposal.transcription_digest,
            "USER APPROVED PDF TRANSCRIPTION BATCH "
            f"{proposal.batch_id} {proposal.transcription_digest}",
        )
        verified = module.VerifiedHkdsePdfTranscriptionBatch(
            proposal,
            approval,
            (transcription_record(module, status="VERIFIED"),),
        )
        self.assertIs(verified.proposal, proposal)
        with self.assertRaises(PipelineError):
            module.HkdsePdfTranscriptionApproval(
                proposal.batch_id,
                proposal.transcription_digest,
                "USER APPROVED IMPORT BATCH wrong",
            )
        with self.assertRaises(PipelineError):
            module.VerifiedHkdsePdfTranscriptionBatch(
                proposal,
                approval,
                (transcription_record(module, status="PROPOSED"),),
            )


if __name__ == "__main__":
    unittest.main()
