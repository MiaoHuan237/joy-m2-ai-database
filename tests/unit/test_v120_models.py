"""Public model contracts for the versioned V1.20 candidate authority."""

from __future__ import annotations

from dataclasses import fields, replace
import importlib
import inspect
from pathlib import Path
import sys
import unittest
from typing import get_type_hints

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from joy_m2.errors import ImportApprovalError, PipelineError
from joy_m2.ingest.models import (
    BatchImportManifest,
    ImportAdaptation,
    ImportCandidate,
    ImportFileEvidence,
    ImportIssue,
    ImportPreflightReport,
    ImportPreflightResult,
)
from joy_m2.ingest.promotion_models import (
    ReleasePromotionApproval,
    V119PromotionArtifacts,
    V119PromotionBuildRequest,
    V119PromotionContract,
    V119PromotionVerificationRequest,
    V119PublicationRequest,
)
from joy_m2.ingest.writer_models import (
    ImportApproval,
    V119CandidateArtifacts,
    V119VerificationRequest,
    V119WriteRequest,
    V119WriterContract,
)
from joy_m2.models import ArtifactRef, VerificationReport


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
GENESIS = "4ff624aca875b0191fe8a617516d2919c6d700ce69c5a3b5d236adcf7ecc59f1"
BASELINE_SHA = "5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff"
BASELINE_MANIFEST_SHA = "cd048408df5e062592d5ed8553b3461860c876b0264660ab65c78c428584a510"
BASELINE_RELEASE_DIGEST = "7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d"


class V120ModelContractTests(unittest.TestCase):
    """Each test names a public-contract mutation it prevents."""

    def setUp(self) -> None:
        self.module = importlib.import_module("joy_m2.ingest.v120_models")

    def _artifact(self, kind: str = "sqlite") -> ArtifactRef:
        return ArtifactRef(Path("/tmp/v120-baseline.sqlite3"), BASELINE_SHA, 9478144, kind)

    def _evidence(self, path: str, kind: str) -> ImportFileEvidence:
        return ImportFileEvidence(path, SHA_A, 1, kind)

    def _manifest(self):
        return self.module.V120BatchImportManifest(
            "task10-v120-import-manifest-v1", "batch.01-A", "Joy M2 AI Database", "M2", "Algebra",
            "V1.20", [self._evidence("candidates/a.json", "candidate_json")],
            [self._evidence("source/a.mmd", "source")], [self._evidence("answers/a.md", "answer")],
            [self._evidence("images/a.png", "image")], [], [],
            "preserve_source_and_store_reviewed_chinese_separately", "one_complete_question_per_record",
            "joy_level_1_5", "controlled_primary_type_and_tags", "preserve_source_answer_identity",
            "source_or_independently_verified_with_identity",
        )

    def _candidate(self, question_id: str = "V120-Q-1") -> ImportCandidate:
        return ImportCandidate(
            question_id, "source", "1", "section", SHA_A, SHA_B, "Question", "",
            "missing", None, "", "", "missing_from_source", "", "missing", None,
            [], [], [], "algebra", [], "missing", None, "missing", "incomplete",
        )

    def _report(self, manifest=None, *, status: str = "READY FOR USER IMPORT APPROVAL"):
        manifest = manifest or self._manifest()
        return self.module.V120ImportPreflightReport(
            manifest.batch_id, status, SHA_B, SHA_C, "V1.19", BASELINE_RELEASE_DIGEST, 502,
            "V1.20", GENESIS, 0, 502, 1, 1, 0, 0, 0, 0, 503,
            [], [], [], 0, 0, [], [], [], [], [], [], [(1, 1)], ["V120-Q-1"], [], [], [],
        )

    def _state(self):
        return self.module.V120EffectiveState(self._artifact(), GENESIS, [], 0, 502)

    def _result(self, manifest=None):
        manifest = manifest or self._manifest()
        return self.module.V120ImportPreflightResult(manifest, self._state(), [self._candidate()], [], self._report(manifest))

    def _contract(self):
        return self.module.V120CandidateContract(
            "V1.20", "V1.19", 502, BASELINE_SHA, 9478144, BASELINE_MANIFEST_SHA, 3242,
            BASELINE_RELEASE_DIGEST, "task10-v120-import-manifest-v1", "task10-v120-preflight-v1",
            "task10-v120-import-approval-v1", "task10-v120-candidate-manifest-v1",
            "task10-v120-candidate-v1", "task10-v120-candidate-identity-v1", "task10-v120-rollback-v1",
            120, "Joy_M2_V1.20_candidate.sqlite3", "candidate_manifest.json", "SHA256SUMS", "rollback.json",
            "authority/batches", "images/sha256", "formal_complete_questions_v119",
            ["task10_v120_batch_ledger_v1", "task10_v120_candidates_v1", "task10_v120_images_v1", "task10_v120_taxonomy_v1"],
            ["task10_candidate_questions_v120"],
        )

    def _approval(self, manifest=None):
        manifest = manifest or self._manifest()
        return self.module.V120ImportApproval(
            manifest.batch_id, SHA_B, "V1.20", GENESIS,
            f"USER APPROVED IMPORT BATCH {manifest.batch_id} {SHA_B} V1.20 PARENT {GENESIS}",
        )

    def _approved_batch(self):
        manifest = self._manifest()
        return self.module.V120ApprovedBatch(self._result(manifest), Path("/tmp/package"), self._approval(manifest))

    def test_exact_public_field_envelopes_are_frozen_and_default_free(self) -> None:
        expected = {
            "V120BatchImportManifest": ("schema_version", "batch_id", "project", "module", "chapter", "target_release_version", "candidate_records", "source_files", "answer_files", "image_files", "teacher_notes_files", "common_errors_files", "language_policy", "split_policy", "difficulty_policy", "tag_policy", "answer_policy", "explanation_policy"),
            "V120AdaptedImportPackage": ("package_root", "manifest_path", "manifest"),
            "V120BatchLedgerEntry": ("ordinal", "batch_id", "parent_candidate_digest", "preflight_sha256", "manifest_sha256", "approval", "batch_candidate_count", "cumulative_candidate_count", "projected_question_count"),
            "V120EffectiveState": ("baseline_database", "candidate_digest", "batch_ledger", "candidate_count", "projected_question_count"),
            "V120PreflightRequest": ("manifest", "package_root", "baseline_database", "parent_candidate", "contract"),
            "V120ImportPreflightReport": ("batch_id", "status", "preflight_sha256", "manifest_sha256", "baseline_version", "baseline_release_digest", "baseline_question_count", "target_release_version", "parent_candidate_digest", "parent_batch_count", "before_count", "detected_count", "new_candidate_count", "duplicate_count", "rejected_count", "ambiguous_count", "approved_count", "projected_after_count", "readable_files", "unreadable_files", "unsupported_files", "teacher_notes_file_count", "common_errors_file_count", "ambiguous_splits", "missing_answers", "missing_explanations", "incomplete_enrichments", "missing_images", "orphan_images", "level_counts", "proposed_ids", "adaptations", "warnings", "blocking_errors"),
            "V120ImportPreflightResult": ("manifest", "effective_state", "candidates", "issues", "report"),
            "V120ImportApproval": ("batch_id", "preflight_sha256", "target_release_version", "parent_candidate_digest", "statement"),
            "V120ApprovedBatch": ("preflight_result", "package_root", "approval"),
            "V120CandidateContract": ("profile", "baseline_release_version", "baseline_question_count", "baseline_database_sha256", "baseline_database_size_bytes", "baseline_manifest_sha256", "baseline_manifest_size_bytes", "baseline_release_digest", "canonical_manifest_schema", "preflight_schema", "approval_schema", "candidate_manifest_schema", "candidate_database_schema", "candidate_identity_schema", "rollback_schema", "expected_user_version", "database_filename", "manifest_filename", "sha256s_filename", "rollback_filename", "authority_root", "image_root", "required_baseline_view", "required_candidate_tables", "required_candidate_views"),
            "V120CandidateBuildRequest": ("approved_batches", "output_dir", "contract"),
            "V120CandidateVerificationRequest": ("candidate_dir", "approved_batches", "contract"),
            "V120CandidateArtifacts": ("database", "manifest", "sha256sums", "rollback", "batch_authorities", "images", "state", "verification_report"),
        }
        for name, field_names in expected.items():
            carrier = getattr(self.module, name)
            self.assertEqual(tuple(field.name for field in fields(carrier)), field_names)
            self.assertTrue(getattr(carrier, "__dataclass_params__").frozen)
            self.assertTrue(all(field.default.__class__.__name__ == "_MISSING_TYPE" for field in fields(carrier)))

    def test_exact_annotations_and_signatures_cover_versioned_and_historical_models(self) -> None:
        v120 = self.module
        historical_fields = {
            BatchImportManifest: ("schema_version", "batch_id", "project", "module", "chapter", "target_release_version", "candidate_records", "source_files", "answer_files", "image_files", "teacher_notes_files", "common_errors_files", "language_policy", "split_policy", "difficulty_policy", "tag_policy", "answer_policy", "explanation_policy"),
            ImportPreflightReport: ("batch_id", "status", "preflight_sha256", "manifest_sha256", "baseline_version", "before_count", "target_release_version", "detected_count", "new_candidate_count", "duplicate_count", "rejected_count", "ambiguous_count", "approved_count", "projected_after_count", "readable_files", "unreadable_files", "unsupported_files", "teacher_notes_file_count", "common_errors_file_count", "ambiguous_splits", "missing_answers", "missing_explanations", "incomplete_enrichments", "missing_images", "orphan_images", "level_counts", "proposed_ids", "adaptations", "warnings", "blocking_errors"),
            ImportApproval: ("batch_id", "preflight_sha256", "target_release_version", "statement"),
            V119WriterContract: ("profile", "candidate_manifest_schema", "candidate_database_schema", "expected_user_version", "database_filename", "manifest_filename", "sha256s_filename", "rollback_filename", "image_root", "required_baseline_tables", "required_candidate_tables", "required_candidate_views"),
            V119WriteRequest: ("preflight_result", "package_root", "approval", "output_dir", "contract"),
            V119VerificationRequest: ("candidate_dir", "preflight_result", "approval", "contract"),
            V119CandidateArtifacts: ("database", "manifest", "sha256sums", "rollback", "images", "verification_report"),
            V119PromotionContract: ("profile", "release_manifest_schema", "formal_database_schema", "promotion_identity_schema", "rollback_schema", "expected_user_version", "database_filename", "manifest_filename", "sha256s_filename", "rollback_filename", "image_root", "promoted_table", "promotion_table", "formal_view"),
            V119PromotionBuildRequest: ("candidate", "output_dir", "contract"),
            V119PromotionVerificationRequest: ("release_dir", "candidate", "contract"),
            ReleasePromotionApproval: ("release_version", "release_digest", "statement"),
            V119PublicationRequest: ("dry_run_dir", "candidate", "approval", "contract"),
            V119PromotionArtifacts: ("database", "manifest", "sha256sums", "rollback", "images", "release_digest", "verification_report"),
        }
        expected = {
            v120.V120BatchImportManifest: (str, str, str, str, str, str, tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], str, str, str, str, str, str),
            v120.V120AdaptedImportPackage: (Path, Path, v120.V120BatchImportManifest),
            v120.V120BatchLedgerEntry: (int, str, str, str, str, v120.V120ImportApproval, int, int, int),
            v120.V120EffectiveState: (ArtifactRef, str, tuple[v120.V120BatchLedgerEntry, ...], int, int),
            v120.V120PreflightRequest: (v120.V120BatchImportManifest, Path, ArtifactRef, v120.V120CandidateVerificationRequest | None, v120.V120CandidateContract),
            v120.V120ImportPreflightReport: (str, str, str, str, str, str, int, str, str, int, int, int, int, int, int, int, int, int, tuple[str, ...], tuple[str, ...], tuple[str, ...], int, int, tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[tuple[int, int], ...], tuple[str, ...], tuple[ImportAdaptation, ...], tuple[str, ...], tuple[str, ...]),
            v120.V120ImportPreflightResult: (v120.V120BatchImportManifest, v120.V120EffectiveState, tuple[ImportCandidate, ...], tuple[ImportIssue, ...], v120.V120ImportPreflightReport),
            v120.V120ImportApproval: (str, str, str, str, str),
            v120.V120ApprovedBatch: (v120.V120ImportPreflightResult, Path, v120.V120ImportApproval),
            v120.V120CandidateContract: (str, str, int, str, int, str, int, str, str, str, str, str, str, str, str, int, str, str, str, str, str, str, str, tuple[str, ...], tuple[str, ...]),
            v120.V120CandidateBuildRequest: (tuple[v120.V120ApprovedBatch, ...], Path, v120.V120CandidateContract),
            v120.V120CandidateVerificationRequest: (Path, tuple[v120.V120ApprovedBatch, ...], v120.V120CandidateContract),
            v120.V120CandidateArtifacts: (ArtifactRef, ArtifactRef, ArtifactRef, ArtifactRef, tuple[ArtifactRef, ...], tuple[ArtifactRef, ...], v120.V120EffectiveState, VerificationReport),
            BatchImportManifest: (str, str, str, str, str, str, tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], str, str, str, str, str, str),
            ImportPreflightReport: (str, str, str, str, str, int, str, int, int, int, int, int, int, int, tuple[str, ...], tuple[str, ...], tuple[str, ...], int, int, tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[tuple[int, int], ...], tuple[str, ...], tuple[ImportAdaptation, ...], tuple[str, ...], tuple[str, ...]),
            ImportApproval: (str, str, str, str),
            V119WriterContract: (str, str, str, int, str, str, str, str, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]),
            V119WriteRequest: (ImportPreflightResult, Path, ImportApproval, Path, V119WriterContract),
            V119VerificationRequest: (Path, ImportPreflightResult, ImportApproval, V119WriterContract),
            V119CandidateArtifacts: (ArtifactRef, ArtifactRef, ArtifactRef, ArtifactRef, tuple[ArtifactRef, ...], VerificationReport),
            V119PromotionContract: (str, str, str, str, str, int, str, str, str, str, str, str, str, str),
            V119PromotionBuildRequest: (V119VerificationRequest, Path, V119PromotionContract),
            V119PromotionVerificationRequest: (Path, V119VerificationRequest, V119PromotionContract),
            ReleasePromotionApproval: (str, str, str),
            V119PublicationRequest: (Path, V119VerificationRequest, ReleasePromotionApproval, V119PromotionContract),
            V119PromotionArtifacts: (ArtifactRef, ArtifactRef, ArtifactRef, ArtifactRef, tuple[ArtifactRef, ...], str, VerificationReport),
        }
        for carrier, annotations in expected.items():
            with self.subTest(carrier=carrier.__name__):
                hints = get_type_hints(carrier)
                field_names = historical_fields.get(carrier, tuple(field.name for field in fields(carrier)))
                self.assertEqual(tuple(hints), field_names)
                self.assertEqual(tuple(hints.values()), annotations)
                signature = inspect.signature(carrier)
                self.assertEqual(tuple(signature.parameters), field_names)
                self.assertTrue(all(parameter.default is inspect.Parameter.empty for parameter in signature.parameters.values()))

    def test_manifest_canonicalizes_evidence_and_rejects_v120_envelope_violations(self) -> None:
        manifest = self._manifest()
        self.assertIsInstance(manifest.candidate_records, tuple)
        for batch_id in (".batch", "batch/one", "batch\\one", "batch\n1", "批次", "a" * 129):
            values = list(self._manifest().__dict__.values())
            values[1] = batch_id
            with self.assertRaises(PipelineError):
                self.module.V120BatchImportManifest(*values)
        values = list(self._manifest().__dict__.values())
        values[7] = [self._evidence("candidates/a.json", "source")]
        with self.assertRaises(PipelineError):
            self.module.V120BatchImportManifest(*values)

    def test_adapted_package_and_preflight_request_require_exact_types_and_paths(self) -> None:
        manifest = self._manifest()
        package = self.module.V120AdaptedImportPackage(Path("."), Path("manifest.json"), manifest)
        self.assertTrue(package.package_root.is_absolute())
        self.assertTrue(package.manifest_path.is_absolute())
        request = self.module.V120PreflightRequest(manifest, Path("."), self._artifact(), None, self._contract())
        self.assertTrue(request.package_root.is_absolute())
        with self.assertRaises(PipelineError):
            self.module.V120PreflightRequest(manifest, ".", self._artifact(), None, self._contract())

    def test_ledger_and_state_enforce_genesis_contiguity_and_count_closure(self) -> None:
        approval = self._approval()
        entry = self.module.V120BatchLedgerEntry(1, approval.batch_id, GENESIS, SHA_B, SHA_C, approval, 1, 1, 503)
        state = self.module.V120EffectiveState(self._artifact(), SHA_A, [entry], 1, 503)
        self.assertEqual(state.batch_ledger, (entry,))
        for ordinal, count, projected in ((0, 1, 503), (1, True, 503), (1, 1, 502)):
            with self.assertRaises(PipelineError):
                self.module.V120BatchLedgerEntry(ordinal, approval.batch_id, GENESIS, SHA_B, SHA_C, approval, count, 1, projected)
        with self.assertRaises(PipelineError):
            self.module.V120EffectiveState(self._artifact(), GENESIS, [], 1, 503)
        with self.assertRaises(PipelineError):
            self.module.V120EffectiveState(self._artifact(), SHA_A, [entry], 0, 502)
        non_genesis = self.module.V120ImportApproval(
            approval.batch_id, SHA_B, "V1.20", SHA_A,
            f"USER APPROVED IMPORT BATCH {approval.batch_id} {SHA_B} V1.20 PARENT {SHA_A}",
        )
        with self.assertRaises(PipelineError):
            self.module.V120BatchLedgerEntry(1, approval.batch_id, SHA_A, SHA_B, SHA_C, non_genesis, 1, 1, 503)

    def test_report_closes_counts_and_fixed_v120_identity(self) -> None:
        report = self._report()
        self.assertEqual(report.projected_after_count, 503)
        self.assertIsInstance(report.proposed_ids, tuple)
        values = list(report.__dict__.values())
        values[4] = "V1.18"
        with self.assertRaises(PipelineError):
            self.module.V120ImportPreflightReport(*values)
        values = list(report.__dict__.values())
        values[11] = 2
        with self.assertRaises(PipelineError):
            self.module.V120ImportPreflightReport(*values)
        values = list(report.__dict__.values())
        values[17] = 502
        with self.assertRaises(PipelineError):
            self.module.V120ImportPreflightReport(*values)

    def test_result_preserves_candidate_order_and_canonicalizes_issue_order(self) -> None:
        manifest = self._manifest()
        first, second = self._candidate("z"), self._candidate("a")
        report = self._report(manifest)
        issue_z = ImportIssue("code-z", "warning", "z", "field", "evidence")
        issue_a = ImportIssue("code-a", "warning", "a", "field", "evidence")
        result = self.module.V120ImportPreflightResult(manifest, self._state(), [first, second], [issue_z, issue_a], report)
        self.assertEqual(result.candidates, (first, second))
        self.assertEqual(result.issues, (issue_a, issue_z))
        with self.assertRaises(PipelineError):
            self.module.V120ImportPreflightResult(manifest, self._state(), [first], ["not an issue"], report)

    def test_approval_is_parent_bound_and_uses_existing_approval_error(self) -> None:
        approval = self._approval()
        self.assertEqual(approval.statement, f"USER APPROVED IMPORT BATCH {approval.batch_id} {SHA_B} V1.20 PARENT {GENESIS}")
        with self.assertRaises(ImportApprovalError):
            self.module.V120ImportApproval("batch 1", SHA_B, "V1.20", GENESIS, approval.statement)
        with self.assertRaises(ImportApprovalError):
            self.module.V120ImportApproval(approval.batch_id, SHA_B.upper(), "V1.20", GENESIS, approval.statement)
        with self.assertRaises(ImportApprovalError):
            self.module.V120ImportApproval(approval.batch_id, SHA_B, "V1.19", GENESIS, approval.statement)

    def test_approved_batch_binds_ready_result_to_exact_approval(self) -> None:
        approved = self._approved_batch()
        self.assertTrue(approved.package_root.is_absolute())
        result = self._result()
        mismatched = self.module.V120ImportApproval("other", SHA_B, "V1.20", GENESIS, f"USER APPROVED IMPORT BATCH other {SHA_B} V1.20 PARENT {GENESIS}")
        with self.assertRaises(ImportApprovalError):
            self.module.V120ApprovedBatch(result, Path("."), mismatched)

    def test_contract_is_exact_and_rejects_bool_and_tuple_changes(self) -> None:
        contract = self._contract()
        self.assertEqual(contract.required_candidate_tables, ("task10_v120_batch_ledger_v1", "task10_v120_candidates_v1", "task10_v120_images_v1", "task10_v120_taxonomy_v1"))
        values = list(contract.__dict__.values())
        values[15] = True
        with self.assertRaises(PipelineError):
            self.module.V120CandidateContract(*values)
        values = list(contract.__dict__.values())
        values[-1] = []
        with self.assertRaises(PipelineError):
            self.module.V120CandidateContract(*values)

    def test_build_and_verification_requests_require_a_nonempty_ordered_prefix(self) -> None:
        approved = self._approved_batch()
        build = self.module.V120CandidateBuildRequest([approved], Path("."), self._contract())
        verify = self.module.V120CandidateVerificationRequest(Path("."), [approved], self._contract())
        self.assertEqual(build.approved_batches, (approved,))
        self.assertEqual(verify.approved_batches, (approved,))
        for request, path in ((self.module.V120CandidateBuildRequest, Path(".")), (self.module.V120CandidateVerificationRequest, Path("."))):
            with self.assertRaises(PipelineError):
                request([], path, self._contract())

    def test_candidate_artifacts_require_exact_kinds_and_stable_destination_order(self) -> None:
        report = VerificationReport("PASS", ())
        state = self._state()
        database = ArtifactRef(Path("/tmp/db"), SHA_A, 1, "sqlite")
        manifest = ArtifactRef(Path("/tmp/manifest"), SHA_A, 1, "manifest")
        sums = ArtifactRef(Path("/tmp/sums"), SHA_A, 1, "sha256sums")
        rollback = ArtifactRef(Path("/tmp/rollback"), SHA_A, 1, "rollback")
        preflight = ArtifactRef(Path("/tmp/authority/1/preflight.json"), SHA_A, 1, "preflight")
        approval = ArtifactRef(Path("/tmp/authority/1/approval.json"), SHA_A, 1, "approval")
        image = ArtifactRef(Path("/tmp/images/a"), SHA_A, 1, "image")
        artifacts = self.module.V120CandidateArtifacts(database, manifest, sums, rollback, [approval, preflight], [image], state, report)
        self.assertEqual(artifacts.batch_authorities, (approval, preflight))
        with self.assertRaises(PipelineError):
            self.module.V120CandidateArtifacts(manifest, manifest, sums, rollback, [], [], state, report)
        for position, malformed in (
            (0, ArtifactRef(Path("/tmp/db"), "BAD", 1, "sqlite")),
            (1, ArtifactRef(Path("/tmp/manifest"), SHA_A, True, "manifest")),
            (4, [ArtifactRef(Path("/tmp/authority/1/preflight.json"), "BAD", 1, "preflight")]),
            (5, [ArtifactRef(Path("/tmp/images/a"), SHA_A, True, "image")]),
        ):
            values = [database, manifest, sums, rollback, [approval, preflight], [image], state, report]
            values[position] = malformed
            with self.subTest(position=position), self.assertRaises(PipelineError):
                self.module.V120CandidateArtifacts(*values)

    def test_historical_v119_contracts_remain_closed_to_v120(self) -> None:
        self.assertEqual(BatchImportManifest.__dataclass_fields__["target_release_version"].type, "str")
        with self.assertRaises(PipelineError):
            BatchImportManifest(
                "task9-import-manifest-v1", "batch", "Joy M2 AI Database", "M2", "chapter", "V1.20",
                [], [], [], [], [], [], "preserve_source_and_store_reviewed_chinese_separately",
                "one_complete_question_per_record", "joy_level_1_5", "controlled_primary_type_and_tags",
                "preserve_source_answer_identity", "source_or_independently_verified_with_identity",
            )
        self.assertEqual(V119WriterContract.__dataclass_fields__["profile"].type, "str")
        self.assertEqual(V119PromotionContract.__dataclass_fields__["profile"].type, "str")
        self.assertNotIn("V1.20", repr(V119WriterContract))
        with self.assertRaises(PipelineError):
            V119WriterContract(
                "V1.20", "task9-v119-candidate-manifest-v1", "task9-v119-candidate-v1", 119,
                "Joy_M2_V1.19_candidate.sqlite3", "candidate_manifest.json", "SHA256SUMS",
                "rollback.json", "images/sha256", (), (), (),
            )
        with self.assertRaises(PipelineError):
            V119PromotionContract(
                "V1.20", "task9-v119-formal-manifest-v1", "task9-v119-formal-v1",
                "task9-v119-promotion-identity-v1", "task9-v119-formal-rollback-v1", 119,
                "Joy_M2_Complete_Question_DB_V1_19.sqlite3", "manifest.json", "SHA256SUMS.txt",
                "rollback.json", "images/sha256", "task9_promoted_questions_v1",
                "task9_promotion_v1", "formal_complete_questions_v119",
            )
        historical_report = ImportPreflightReport(
            "batch", "READY FOR USER IMPORT APPROVAL", SHA_A, SHA_B, "V1.18", 497,
            "V1.19", 0, 0, 0, 0, 0, 0, 497, (), (), (), 0, 0, (), (), (), (), (), (),
            (), (), (), (), (),
        )
        with self.assertRaises(PipelineError):
            replace(historical_report, target_release_version="V1.20")
        with self.assertRaises(PipelineError):
            V119WriteRequest(self._result(), Path("."), object(), Path("."), object())
        with self.assertRaises(PipelineError):
            V119PromotionBuildRequest(
                self.module.V120CandidateVerificationRequest(Path("."), [self._approved_batch()], self._contract()),
                Path("."), object(),
            )


if __name__ == "__main__":
    unittest.main()
