from __future__ import annotations

from dataclasses import replace
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import OutputConflictError, PipelineError
from joy_m2.ingest.hkdse_pdf_models import (
    HkdsePdfAdapterBlockedError,
    HkdsePdfTranscriptionApproval,
    HkdsePdfTranscriptionIssue,
)


FIXTURE = ROOT / "tests" / "fixtures" / "task10b"
MODULE_NAME = "joy_m2.ingest.hkdse_pdf_adapter"


def adapter(test_case: unittest.TestCase):
    spec = importlib.util.find_spec(MODULE_NAME)
    test_case.assertIsNotNone(
        spec,
        "Task 10B hkdse_pdf_adapter must exist before adapter behavior can pass",
    )
    return importlib.import_module(MODULE_NAME)


def embedded_api(test_case: unittest.TestCase):
    module = adapter(test_case)
    test_case.assertTrue(
        hasattr(module, "extract_hkdse_pdf_embedded_pass"),
        "Task 10B embedded extraction API must exist before behavior can pass",
    )
    return module.extract_hkdse_pdf_embedded_pass


def approval_api(test_case: unittest.TestCase):
    module = adapter(test_case)
    test_case.assertTrue(
        hasattr(module, "approve_hkdse_pdf_transcription"),
        "Task 10B approval API must exist before gate behavior can pass",
    )
    return module.approve_hkdse_pdf_transcription


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


class AdapterCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        for name in ("data/staging", "data/baselines", "releases"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.config = PipelineConfig(self.root)
        self.pp = self.root / "pp.pdf"
        self.ms = self.root / "ms.pdf"
        self._pdf(self.pp, 2)
        self._pdf(self.ms, 1)
        self.staging = self.root / "staging.json"
        self.pass_a = self.root / "pass-a.json"
        self.pass_b = self.root / "pass-b.json"
        self.output = self.root / "data" / "staging" / "review"
        self._write_valid_inputs()

    def tearDown(self):
        self.temporary.cleanup()

    def _pdf(self, path: Path, pages: int, texts: tuple[str, ...] | None = None) -> None:
        writer = PdfWriter()
        for index in range(pages):
            page = writer.add_blank_page(width=612, height=792)
            text = texts[index] if texts is not None else ""
            if text:
                font = DictionaryObject(
                    {
                        NameObject("/Type"): NameObject("/Font"),
                        NameObject("/Subtype"): NameObject("/Type1"),
                        NameObject("/BaseFont"): NameObject("/Helvetica"),
                    }
                )
                font_ref = writer._add_object(font)
                page[NameObject("/Resources")] = DictionaryObject(
                    {
                        NameObject("/Font"): DictionaryObject(
                            {NameObject("/F1"): font_ref}
                        )
                    }
                )
                stream = DecodedStreamObject()
                escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
                stream.set_data(
                    f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("ascii")
                )
                page[NameObject("/Contents")] = writer._add_object(stream)
        with path.open("wb") as stream:
            writer.write(stream)

    def _write_valid_inputs(self) -> None:
        staging = json.loads((FIXTURE / "staging.json").read_text(encoding="utf-8"))
        staging["source_pair"]["pp"]["sha256"] = sha(self.pp)
        staging["source_pair"]["ms"]["sha256"] = sha(self.ms)
        write_json(self.staging, staging)
        staging_sha = sha(self.staging)
        for fixture, target, pass_id in (
            ("pass-a.json", self.pass_a, "A"),
            ("pass-b.json", self.pass_b, "B"),
        ):
            value = json.loads((FIXTURE / fixture).read_text(encoding="utf-8"))
            value.update(
                pass_id=pass_id,
                staging_sha256=staging_sha,
                pp_sha256=sha(self.pp),
                ms_sha256=sha(self.ms),
            )
            write_json(target, value)

    def propose(self):
        module = adapter(self)
        try:
            return module.propose_hkdse_pdf_transcription(
                self.staging,
                self.pp,
                self.ms,
                self.pass_a,
                self.pass_b,
                self.output,
                self.config,
            )
        except NotImplementedError as exc:
            self.fail(f"Task 10B comparison/publication is not implemented: {exc}")

    def mutate_pass_record(self, path: Path, **changes: object) -> None:
        value = json.loads(path.read_text(encoding="utf-8"))
        value["records"][0].update(changes)
        write_json(path, value)


class HkdsePdfSourceValidationTests(AdapterCase):
    def test_valid_source_reaches_transcription_proposal(self):
        self.assertEqual(self.propose().batch_id, "JOY-M2-HKDSE-2012-PP-MS")

    def test_pdf_sha_mismatch_blocks_before_output(self):
        staging = json.loads(self.staging.read_text(encoding="utf-8"))
        staging["source_pair"]["pp"]["sha256"] = "0" * 64
        write_json(self.staging, staging)
        with self.assertRaises(HkdsePdfAdapterBlockedError) as captured:
            self.propose()
        self.assertEqual(captured.exception.issues[0].code, "pdf_identity_mismatch")
        self.assertFalse(self.output.exists())

    def test_pdf_page_count_mismatch_blocks_before_output(self):
        staging = json.loads(self.staging.read_text(encoding="utf-8"))
        staging["source_pair"]["ms"]["page_count"] = 2
        write_json(self.staging, staging)
        with self.assertRaises(HkdsePdfAdapterBlockedError) as captured:
            self.propose()
        self.assertIn("pdf_page_mismatch", tuple(issue.code for issue in captured.exception.issues))
        self.assertFalse(self.output.exists())

    def test_invalid_pdf_signature_is_rejected_as_source_identity_failure(self):
        self.pp.write_bytes(b"not a pdf")
        staging = json.loads(self.staging.read_text(encoding="utf-8"))
        staging["source_pair"]["pp"]["sha256"] = sha(self.pp)
        write_json(self.staging, staging)
        with self.assertRaises(HkdsePdfAdapterBlockedError) as captured:
            self.propose()
        self.assertEqual(captured.exception.issues[0].code, "pdf_identity_mismatch")

    def test_staging_duplicate_keys_and_wrong_count_are_fatal(self):
        self.staging.write_text('{"schema":"joy_m2_staging_batch_v1","schema":"duplicate"}\n')
        with self.assertRaises(HkdsePdfAdapterBlockedError) as captured:
            self.propose()
        self.assertEqual(captured.exception.issues[0].code, "staging_contract_mismatch")
        self.assertFalse(self.output.exists())

        self._write_valid_inputs()
        staging = json.loads(self.staging.read_text(encoding="utf-8"))
        staging["summary"]["complete_questions"] = 2
        write_json(self.staging, staging)
        with self.assertRaises(HkdsePdfAdapterBlockedError):
            self.propose()

    def test_pass_source_identity_and_order_must_match_staging(self):
        for mutation in ("digest", "order"):
            with self.subTest(mutation=mutation):
                self._write_valid_inputs()
                value = json.loads(self.pass_b.read_text(encoding="utf-8"))
                if mutation == "digest":
                    value["pp_sha256"] = "f" * 64
                elif mutation == "order":
                    value["records"][0]["staging_id"] = "HKDSE-2012-M2-Q99"
                write_json(self.pass_b, value)
                with self.assertRaises(HkdsePdfAdapterBlockedError) as captured:
                    self.propose()
                self.assertIn(
                    "extraction_pass_invalid",
                    tuple(issue.code for issue in captured.exception.issues),
                )
                self.assertFalse(self.output.exists())

    def test_pass_loader_rejects_duplicate_keys_and_extra_fields(self):
        module = adapter(self)
        self.pass_a.write_text('{"schema_version":"x","schema_version":"y"}\n')
        with self.assertRaises(HkdsePdfAdapterBlockedError):
            module.load_hkdse_pdf_extraction_pass(self.pass_a)
        self._write_valid_inputs()
        value = json.loads(self.pass_a.read_text(encoding="utf-8"))
        value["absolute_path"] = "/private/source.pdf"
        write_json(self.pass_a, value)
        with self.assertRaises(HkdsePdfAdapterBlockedError):
            module.load_hkdse_pdf_extraction_pass(self.pass_a)

    def test_output_must_be_new_strict_staging_descendant(self):
        module = adapter(self)
        with self.assertRaises(PipelineError):
            module.propose_hkdse_pdf_transcription(
                self.staging,
                self.pp,
                self.ms,
                self.pass_a,
                self.pass_b,
                self.root / "outside",
                self.config,
            )
        self.output.mkdir()
        with self.assertRaises(OutputConflictError):
            self.propose()


class HkdsePdfEmbeddedExtractionTests(AdapterCase):
    def _refresh_text_pdfs(self):
        self._pdf(self.pp, 2, ("Cover", "Question One exact source"))
        self._pdf(self.ms, 1, ("Official marking steps M1 A1",))
        self._write_valid_inputs()

    def test_unique_page_owner_produces_bound_embedded_pass_and_canonical_file(self):
        self._refresh_text_pdfs()
        module = adapter(self)
        extract = embedded_api(self)
        output = self.root / "data" / "staging" / "embedded-a.json"
        result = extract(
            self.staging, self.pp, self.ms, "A", output, self.config
        )
        self.assertEqual(result.pass_id, "A")
        self.assertEqual(result.staging_sha256, sha(self.staging))
        self.assertIn("Question One exact source", result.records[0].question_text_original)
        self.assertIn("Official marking steps", result.records[0].official_ms_original)
        self.assertEqual(result.records[0].question_method, "embedded_text")
        self.assertEqual(module.load_hkdse_pdf_extraction_pass(output), result)
        self.assertTrue(output.read_bytes().endswith(b"\n"))

    def test_shared_page_text_is_not_assigned_to_multiple_questions(self):
        self._refresh_text_pdfs()
        staging = json.loads(self.staging.read_text(encoding="utf-8"))
        second = json.loads(json.dumps(staging["records"][0]))
        second["staging_id"] = "HKDSE-2012-M2-Q02"
        second["dedup_key_proposal"] = "HKDSE:2012:M2:Q02"
        second["source_question_no"] = 2
        second["provenance"]["canonical_exam_identity"] = "HKDSE-2012-MATH-M2-Q2"
        staging["records"].append(second)
        staging["summary"]["complete_questions"] = 2
        staging["summary"]["total_marks"] = 6
        staging["summary"]["module_distribution"]["T05"] = 2
        staging["summary"]["difficulty_distribution"]["D2"] = 2
        write_json(self.staging, staging)
        extract = embedded_api(self)
        output = self.root / "data" / "staging" / "shared.json"
        result = extract(
            self.staging, self.pp, self.ms, "A", output, self.config
        )
        self.assertEqual(
            tuple(record.question_text_original for record in result.records),
            ("", ""),
        )
        self.assertEqual(
            tuple(record.official_ms_original for record in result.records),
            ("", ""),
        )

    def test_embedded_output_is_no_replace_and_strictly_staging_scoped(self):
        self._refresh_text_pdfs()
        extract = embedded_api(self)
        output = self.root / "data" / "staging" / "embedded.json"
        extract(
            self.staging, self.pp, self.ms, "B", output, self.config
        )
        before = output.read_bytes()
        with self.assertRaises(OutputConflictError):
            extract(
                self.staging, self.pp, self.ms, "B", output, self.config
            )
        self.assertEqual(output.read_bytes(), before)
        with self.assertRaises(PipelineError):
            extract(
                self.staging,
                self.pp,
                self.ms,
                "A",
                self.root / "outside.json",
                self.config,
            )

    def test_equivalent_roots_produce_identical_pass_bytes(self):
        self._refresh_text_pdfs()
        extract = embedded_api(self)
        first = self.root / "data" / "staging" / "first.json"
        extract(
            self.staging, self.pp, self.ms, "A", first, self.config
        )
        second_root = self.root / "second-repo"
        for name in ("data/staging", "data/baselines", "releases"):
            (second_root / name).mkdir(parents=True, exist_ok=True)
        second_config = PipelineConfig(second_root)
        second = second_root / "data" / "staging" / "second.json"
        extract(
            self.staging, self.pp, self.ms, "A", second, second_config
        )
        self.assertEqual(first.read_bytes(), second.read_bytes())


class HkdsePdfComparisonTests(AdapterCase):
    def propose(self):
        try:
            return super().propose()
        except HkdsePdfAdapterBlockedError as exc:
            self.fail(
                "reviewable pass disagreement was rejected before comparison: "
                f"{tuple(issue.code for issue in exc.issues)}"
            )

    def test_exact_agreement_produces_proposed_record_and_exact_artifacts(self):
        batch = self.propose()
        self.assertEqual(batch.records[0].status, "PROPOSED")
        self.assertEqual(batch.issues, ())
        self.assertEqual(batch.total_questions, 1)
        self.assertEqual(batch.auto_agree_count, 1)
        self.assertEqual(batch.review_required_count, 0)
        self.assertEqual(
            {path.name for path in batch.artifact_root.iterdir()},
            {
                "transcription.json",
                "extraction-pass-a.json",
                "extraction-pass-b.json",
                "PDF_TRANSCRIPTION_REVIEW.md",
            },
        )

    def test_missing_question_and_ms_are_independent_review_issues(self):
        for field, code in (
            ("question_text_original", "question_text_missing"),
            ("official_ms_original", "official_ms_missing"),
        ):
            with self.subTest(field=field):
                self._write_valid_inputs()
                self.mutate_pass_record(self.pass_a, **{field: ""})
                self.mutate_pass_record(self.pass_b, **{field: ""})
                batch = self.propose()
                self.assertEqual(batch.records[0].status, "REVIEW_REQUIRED")
                self.assertIn(code, tuple(issue.code for issue in batch.issues))
                shutil.rmtree(self.output)

    def test_exact_text_tuple_mark_figure_and_page_disagreements_are_reviewable(self):
        cases = (
            ("question_text_original", "A plain sentence.", "question_text_mismatch"),
            ("official_ms_original", "Different official steps", "official_ms_mismatch"),
            ("subparts", ["(a)"], "subpart_mismatch"),
            ("marks", 4, "mark_mismatch"),
            ("figure_references", ["pp:fixture#page=2#region=figure-1"], "figure_mismatch"),
            ("question_pages", {"start_page": 1, "end_page": 1}, "page_boundary_ambiguity"),
        )
        for field, replacement, code in cases:
            with self.subTest(field=field):
                self._write_valid_inputs()
                self.mutate_pass_record(self.pass_b, **{field: replacement})
                batch = self.propose()
                self.assertEqual(batch.records[0].status, "REVIEW_REQUIRED")
                self.assertIn(code, tuple(issue.code for issue in batch.issues))
                shutil.rmtree(self.output)

    def test_minus_sign_disagreement_requires_formula_review_without_repair(self):
        self.mutate_pass_record(
            self.pass_a, question_text_original="Find x - 1."
        )
        self.mutate_pass_record(
            self.pass_b, question_text_original="Find x − 1."
        )
        batch = self.propose()
        self.assertEqual(batch.records[0].question_text_original, "Find x - 1.")
        self.assertEqual(batch.records[0].status, "REVIEW_REQUIRED")
        self.assertIn("question_text_mismatch", tuple(issue.code for issue in batch.issues))
        self.assertIn("formula_mismatch", tuple(issue.code for issue in batch.issues))

    def test_staging_mark_and_page_proposals_do_not_preempt_review_issues(self):
        for field, replacement, code in (
            ("marks", 4, "mark_mismatch"),
            ("question_pages", {"start_page": 1, "end_page": 1}, "page_boundary_ambiguity"),
        ):
            with self.subTest(field=field):
                self._write_valid_inputs()
                self.mutate_pass_record(self.pass_a, **{field: replacement})
                self.mutate_pass_record(self.pass_b, **{field: replacement})
                batch = self.propose()
                self.assertIn(code, tuple(issue.code for issue in batch.issues))
                shutil.rmtree(self.output)

    def test_issue_order_is_stable_and_deterministic(self):
        self.mutate_pass_record(
            self.pass_b,
            question_text_original="Find x − 1.",
            official_ms_original="different",
            marks=4,
        )
        batch = self.propose()
        keys = tuple(
            (issue.staging_id or "", issue.code, issue.field, issue.evidence)
            for issue in batch.issues
        )
        self.assertEqual(keys, tuple(sorted(keys)))

    def test_atomic_publication_failure_cleans_owned_temporary_tree(self):
        module = adapter(self)
        with mock.patch.object(
            module,
            "atomic_rename_no_replace",
            side_effect=OSError("publish failed"),
            create=True,
        ):
            with self.assertRaises(OSError):
                self.propose()
        self.assertFalse(self.output.exists())
        self.assertEqual(
            tuple(self.output.parent.glob(f".{self.output.name}-*")), ()
        )


class HkdsePdfApprovalTests(AdapterCase):
    def approval_for(self, proposal, *, batch_id=None, digest=None):
        chosen_batch = batch_id or proposal.batch_id
        chosen_digest = digest or proposal.transcription_digest
        return HkdsePdfTranscriptionApproval(
            chosen_batch,
            chosen_digest,
            f"USER APPROVED PDF TRANSCRIPTION BATCH {chosen_batch} {chosen_digest}",
        )

    def test_exact_approval_produces_verified_copy_without_file_mutation(self):
        proposal = self.propose()
        before = proposal.transcription_path.read_bytes()
        verified = approval_api(self)(proposal, self.approval_for(proposal))
        self.assertIs(verified.proposal, proposal)
        self.assertEqual(tuple(record.status for record in verified.records), ("VERIFIED",))
        self.assertEqual(
            tuple(replace(record, status="PROPOSED") for record in verified.records),
            proposal.records,
        )
        self.assertEqual(proposal.transcription_path.read_bytes(), before)

    def test_wrong_batch_or_digest_approval_is_rejected(self):
        proposal = self.propose()
        for approval in (
            self.approval_for(proposal, batch_id="OTHER-BATCH"),
            self.approval_for(proposal, digest="f" * 64),
        ):
            with self.subTest(approval=approval):
                with self.assertRaises(PipelineError):
                    approval_api(self)(proposal, approval)

    def test_parallel_carriers_are_rejected(self):
        proposal = self.propose()
        approval = self.approval_for(proposal)
        for candidate_proposal, candidate_approval in (
            (object(), approval),
            (proposal, object()),
        ):
            with self.subTest(proposal=type(candidate_proposal), approval=type(candidate_approval)):
                with self.assertRaises(TypeError):
                    approval_api(self)(candidate_proposal, candidate_approval)

    def test_review_required_proposal_cannot_be_approved(self):
        self.mutate_pass_record(self.pass_b, question_text_original="different")
        proposal = self.propose()
        self.assertEqual(proposal.records[0].status, "REVIEW_REQUIRED")
        with self.assertRaises(PipelineError):
            approval_api(self)(proposal, self.approval_for(proposal))

    def test_any_issue_blocks_even_when_record_envelope_claims_proposed(self):
        proposal = self.propose()
        issue = HkdsePdfTranscriptionIssue(
            "mark_mismatch",
            "review_required",
            proposal.records[0].staging_id,
            "marks",
            '{"reason":"test"}',
        )
        forged = replace(proposal, issues=(issue,))
        with self.assertRaises(PipelineError):
            approval_api(self)(forged, self.approval_for(forged))

    def test_altered_record_invalidates_stored_transcription_digest(self):
        proposal = self.propose()
        altered_record = replace(
            proposal.records[0], question_text_original="altered after proposal"
        )
        forged = replace(proposal, records=(altered_record,))
        with self.assertRaises(PipelineError):
            approval_api(self)(forged, self.approval_for(forged))


if __name__ == "__main__":
    unittest.main()
