"""V1.22 exact public contracts; RED precedes each implementation layer."""
import importlib.util
import unittest


class V122ExistenceTests(unittest.TestCase):
    def test_model_module_exists(self):
        self.assertIsNotNone(importlib.util.find_spec("joy_m2.ingest.v122_models"))

"""Public model contracts for the versioned V1.22 candidate authority."""


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
GENESIS = "7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7"
BASELINE_SHA = "93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a"
BASELINE_MANIFEST_SHA = "a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40"
BASELINE_RELEASE_DIGEST = "f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3"


class V122ModelContractTests(unittest.TestCase):
    """Each test names a public-contract mutation it prevents."""

    def setUp(self) -> None:
        self.module = importlib.import_module("joy_m2.ingest.v122_models")

    def _artifact(self, kind: str = "sqlite") -> ArtifactRef:
        return ArtifactRef(Path("/tmp/v122-baseline.sqlite3"), BASELINE_SHA, 10063872, kind)

    def test_frozen_tuple_copy_and_invalid_genesis(self):
        from dataclasses import FrozenInstanceError, MISSING
        state = self._state()
        with self.assertRaises(FrozenInstanceError):
            state.candidate_count = 1
        ledger = []
        copied = self.module.V122EffectiveState(self._artifact(), GENESIS, ledger, 0, 591)
        ledger.append(object())
        self.assertEqual(copied.batch_ledger, ())
        for digest in (None, "", "331192032f184a44ed383e6dacc2f06fbacb60ad94414298fcb935ff56cb5906", "4ff624aca875b0191fe8a617516d2919c6d700ce69c5a3b5d236adcf7ecc59f1", "0" * 64):
            with self.subTest(digest=digest), self.assertRaises(PipelineError):
                self.module.V122EffectiveState(self._artifact(), digest, [], 0, 591)
        for name, carrier in vars(self.module).items():
            if name.startswith("V122") and isinstance(carrier, type):
                self.assertTrue(all(f.default is MISSING and f.default_factory is MISSING for f in fields(carrier)))

    def _evidence(self, path: str, kind: str) -> ImportFileEvidence:
        return ImportFileEvidence(path, SHA_A, 1, kind)

    def _manifest(self):
        return self.module.V122BatchImportManifest(
            "task12-v122-import-manifest-v1", "batch.01-A", "Joy M2 AI Database", "M2", "Algebra",
            "V1.22", [self._evidence("candidates/a.json", "candidate_json")],
            [self._evidence("source/a.mmd", "source")], [self._evidence("answers/a.md", "answer")],
            [self._evidence("images/a.png", "image")], [], [],
            "preserve_source_and_store_reviewed_chinese_separately", "one_complete_question_per_record",
            "joy_level_1_5", "controlled_primary_type_and_tags", "preserve_source_answer_identity",
            "source_or_independently_verified_with_identity",
        )

    def _candidate(self, question_id: str = "V122-Q-1") -> ImportCandidate:
        return ImportCandidate(
            question_id, "source", "1", "section", SHA_A, SHA_B, "Question", "",
            "missing", None, "", "", "missing_from_source", "", "missing", None,
            [], [], [], "algebra", [], "missing", None, "missing", "incomplete",
        )

    def _report(self, manifest=None, *, status: str = "READY FOR USER IMPORT APPROVAL"):
        manifest = manifest or self._manifest()
        return self.module.V122ImportPreflightReport(
            manifest.batch_id, status, SHA_B, SHA_C, "V1.21", BASELINE_RELEASE_DIGEST, 591,
            "V1.22", GENESIS, 0, 591, 1, 1, 0, 0, 0, 0, 592,
            [], [], [], 0, 0, [], [], [], [], [], [], [(1, 1)], ["V122-Q-1"], [], [], [],
        )

    def _state(self):
        return self.module.V122EffectiveState(self._artifact(), GENESIS, [], 0, 591)

    def _result(self, manifest=None):
        manifest = manifest or self._manifest()
        return self.module.V122ImportPreflightResult(manifest, self._state(), [self._candidate()], [], self._report(manifest))

    def _contract(self):
        return self.module.V122CandidateContract(
            "V1.22", "V1.21", 591, BASELINE_SHA, 10063872, BASELINE_MANIFEST_SHA, 7913,
            BASELINE_RELEASE_DIGEST, "task12-v122-import-manifest-v1", "task12-v122-preflight-v1",
            "task12-v122-import-approval-v1", "task12-v122-candidate-manifest-v1",
            "task12-v122-candidate-v1", "task12-v122-candidate-identity-v1", "task12-v122-rollback-v1",
            122, "Joy_M2_V1.22_candidate.sqlite3", "candidate_manifest.json", "SHA256SUMS", "rollback.json",
            "authority/batches", "images/sha256", "formal_complete_questions_v121",
            ["task12_v122_batch_ledger_v1", "task12_v122_candidates_v1", "task12_v122_images_v1", "task12_v122_taxonomy_v1"],
            ["task12_candidate_questions_v122"],
        )

    def _approval(self, manifest=None):
        manifest = manifest or self._manifest()
        return self.module.V122ImportApproval(
            manifest.batch_id, SHA_B, "V1.22", GENESIS,
            f"USER APPROVED IMPORT BATCH {manifest.batch_id} {SHA_B} V1.22 PARENT {GENESIS}",
        )

    def _approved_batch(self):
        manifest = self._manifest()
        return self.module.V122ApprovedBatch(self._result(manifest), Path("/tmp/package"), self._approval(manifest))

    def test_exact_public_field_envelopes_are_frozen_and_default_free(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v122_models"), "V122CandidateContract", None), "V122 model contract missing")
        expected = {
            "V122BatchImportManifest": ("schema_version", "batch_id", "project", "module", "chapter", "target_release_version", "candidate_records", "source_files", "answer_files", "image_files", "teacher_notes_files", "common_errors_files", "language_policy", "split_policy", "difficulty_policy", "tag_policy", "answer_policy", "explanation_policy"),
            "V122AdaptedImportPackage": ("package_root", "manifest_path", "manifest"),
            "V122BatchLedgerEntry": ("ordinal", "batch_id", "parent_candidate_digest", "preflight_sha256", "manifest_sha256", "approval", "batch_candidate_count", "cumulative_candidate_count", "projected_question_count"),
            "V122EffectiveState": ("baseline_database", "candidate_digest", "batch_ledger", "candidate_count", "projected_question_count"),
            "V122PreflightRequest": ("manifest", "package_root", "baseline_database", "parent_candidate", "contract"),
            "V122ImportPreflightReport": ("batch_id", "status", "preflight_sha256", "manifest_sha256", "baseline_version", "baseline_release_digest", "baseline_question_count", "target_release_version", "parent_candidate_digest", "parent_batch_count", "before_count", "detected_count", "new_candidate_count", "duplicate_count", "rejected_count", "ambiguous_count", "approved_count", "projected_after_count", "readable_files", "unreadable_files", "unsupported_files", "teacher_notes_file_count", "common_errors_file_count", "ambiguous_splits", "missing_answers", "missing_explanations", "incomplete_enrichments", "missing_images", "orphan_images", "level_counts", "proposed_ids", "adaptations", "warnings", "blocking_errors"),
            "V122ImportPreflightResult": ("manifest", "effective_state", "candidates", "issues", "report"),
            "V122ImportApproval": ("batch_id", "preflight_sha256", "target_release_version", "parent_candidate_digest", "statement"),
            "V122ApprovedBatch": ("preflight_result", "package_root", "approval"),
            "V122CandidateContract": ("profile", "baseline_release_version", "baseline_question_count", "baseline_database_sha256", "baseline_database_size_bytes", "baseline_manifest_sha256", "baseline_manifest_size_bytes", "baseline_release_digest", "canonical_manifest_schema", "preflight_schema", "approval_schema", "candidate_manifest_schema", "candidate_database_schema", "candidate_identity_schema", "rollback_schema", "expected_user_version", "database_filename", "manifest_filename", "sha256s_filename", "rollback_filename", "authority_root", "image_root", "required_baseline_view", "required_candidate_tables", "required_candidate_views"),
            "V122CandidateBuildRequest": ("approved_batches", "output_dir", "contract"),
            "V122CandidateVerificationRequest": ("candidate_dir", "approved_batches", "contract"),
            "V122CandidateArtifacts": ("database", "manifest", "sha256sums", "rollback", "batch_authorities", "images", "state", "verification_report"),
        }
        for name, field_names in expected.items():
            carrier = getattr(self.module, name)
            self.assertEqual(tuple(field.name for field in fields(carrier)), field_names)
            self.assertTrue(getattr(carrier, "__dataclass_params__").frozen)
            self.assertTrue(all(field.default.__class__.__name__ == "_MISSING_TYPE" for field in fields(carrier)))

    def test_exact_annotations_and_signatures_cover_versioned_and_historical_models(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v122_models"), "V122CandidateContract", None), "V122 model contract missing")
        v122 = self.module
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
            v122.V122BatchImportManifest: (str, str, str, str, str, str, tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], str, str, str, str, str, str),
            v122.V122AdaptedImportPackage: (Path, Path, v122.V122BatchImportManifest),
            v122.V122BatchLedgerEntry: (int, str, str, str, str, v122.V122ImportApproval, int, int, int),
            v122.V122EffectiveState: (ArtifactRef, str, tuple[v122.V122BatchLedgerEntry, ...], int, int),
            v122.V122PreflightRequest: (v122.V122BatchImportManifest, Path, ArtifactRef, v122.V122CandidateVerificationRequest | None, v122.V122CandidateContract),
            v122.V122ImportPreflightReport: (str, str, str, str, str, str, int, str, str, int, int, int, int, int, int, int, int, int, tuple[str, ...], tuple[str, ...], tuple[str, ...], int, int, tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[tuple[int, int], ...], tuple[str, ...], tuple[ImportAdaptation, ...], tuple[str, ...], tuple[str, ...]),
            v122.V122ImportPreflightResult: (v122.V122BatchImportManifest, v122.V122EffectiveState, tuple[ImportCandidate, ...], tuple[ImportIssue, ...], v122.V122ImportPreflightReport),
            v122.V122ImportApproval: (str, str, str, str, str),
            v122.V122ApprovedBatch: (v122.V122ImportPreflightResult, Path, v122.V122ImportApproval),
            v122.V122CandidateContract: (str, str, int, str, int, str, int, str, str, str, str, str, str, str, str, int, str, str, str, str, str, str, str, tuple[str, ...], tuple[str, ...]),
            v122.V122CandidateBuildRequest: (tuple[v122.V122ApprovedBatch, ...], Path, v122.V122CandidateContract),
            v122.V122CandidateVerificationRequest: (Path, tuple[v122.V122ApprovedBatch, ...], v122.V122CandidateContract),
            v122.V122CandidateArtifacts: (ArtifactRef, ArtifactRef, ArtifactRef, ArtifactRef, tuple[ArtifactRef, ...], tuple[ArtifactRef, ...], v122.V122EffectiveState, VerificationReport),
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

    def test_manifest_canonicalizes_evidence_and_rejects_v122_envelope_violations(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v122_models"), "V122CandidateContract", None), "V122 model contract missing")
        manifest = self._manifest()
        self.assertIsInstance(manifest.candidate_records, tuple)
        for batch_id in (".batch", "batch/one", "batch\\one", "batch\n1", "批次", "a" * 129):
            values = list(self._manifest().__dict__.values())
            values[1] = batch_id
            with self.assertRaises(PipelineError):
                self.module.V122BatchImportManifest(*values)
        values = list(self._manifest().__dict__.values())
        values[7] = [self._evidence("candidates/a.json", "source")]
        with self.assertRaises(PipelineError):
            self.module.V122BatchImportManifest(*values)

    def test_adapted_package_and_preflight_request_require_exact_types_and_paths(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v122_models"), "V122CandidateContract", None), "V122 model contract missing")
        manifest = self._manifest()
        package = self.module.V122AdaptedImportPackage(Path("."), Path("manifest.json"), manifest)
        self.assertTrue(package.package_root.is_absolute())
        self.assertTrue(package.manifest_path.is_absolute())
        request = self.module.V122PreflightRequest(manifest, Path("."), self._artifact(), None, self._contract())
        self.assertTrue(request.package_root.is_absolute())
        with self.assertRaises(PipelineError):
            self.module.V122PreflightRequest(manifest, ".", self._artifact(), None, self._contract())

    def test_ledger_and_state_enforce_genesis_contiguity_and_count_closure(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v122_models"), "V122CandidateContract", None), "V122 model contract missing")
        approval = self._approval()
        entry = self.module.V122BatchLedgerEntry(1, approval.batch_id, GENESIS, SHA_B, SHA_C, approval, 1, 1, 592)
        state = self.module.V122EffectiveState(self._artifact(), SHA_A, [entry], 1, 592)
        self.assertEqual(state.batch_ledger, (entry,))
        for ordinal, count, projected in ((0, 1, 592), (1, True, 592), (1, 1, 591)):
            with self.assertRaises(PipelineError):
                self.module.V122BatchLedgerEntry(ordinal, approval.batch_id, GENESIS, SHA_B, SHA_C, approval, count, 1, projected)
        with self.assertRaises(PipelineError):
            self.module.V122EffectiveState(self._artifact(), GENESIS, [], 1, 592)
        with self.assertRaises(PipelineError):
            self.module.V122EffectiveState(self._artifact(), SHA_A, [entry], 0, 591)
        non_genesis = self.module.V122ImportApproval(
            approval.batch_id, SHA_B, "V1.22", SHA_A,
            f"USER APPROVED IMPORT BATCH {approval.batch_id} {SHA_B} V1.22 PARENT {SHA_A}",
        )
        with self.assertRaises(PipelineError):
            self.module.V122BatchLedgerEntry(1, approval.batch_id, SHA_A, SHA_B, SHA_C, non_genesis, 1, 1, 592)

    def test_report_closes_counts_and_fixed_v122_identity(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v122_models"), "V122CandidateContract", None), "V122 model contract missing")
        report = self._report()
        self.assertEqual(report.projected_after_count, 592)
        self.assertIsInstance(report.proposed_ids, tuple)
        values = list(report.__dict__.values())
        values[4] = "V1.18"
        with self.assertRaises(PipelineError):
            self.module.V122ImportPreflightReport(*values)
        values = list(report.__dict__.values())
        values[11] = 2
        with self.assertRaises(PipelineError):
            self.module.V122ImportPreflightReport(*values)
        values = list(report.__dict__.values())
        values[17] = 591
        with self.assertRaises(PipelineError):
            self.module.V122ImportPreflightReport(*values)

    def test_result_preserves_candidate_order_and_canonicalizes_issue_order(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v122_models"), "V122CandidateContract", None), "V122 model contract missing")
        manifest = self._manifest()
        first, second = self._candidate("z"), self._candidate("a")
        report = self._report(manifest)
        issue_z = ImportIssue("code-z", "warning", "z", "field", "evidence")
        issue_a = ImportIssue("code-a", "warning", "a", "field", "evidence")
        result = self.module.V122ImportPreflightResult(manifest, self._state(), [first, second], [issue_z, issue_a], report)
        self.assertEqual(result.candidates, (first, second))
        self.assertEqual(result.issues, (issue_a, issue_z))
        with self.assertRaises(PipelineError):
            self.module.V122ImportPreflightResult(manifest, self._state(), [first], ["not an issue"], report)

    def test_approval_is_parent_bound_and_uses_existing_approval_error(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v122_models"), "V122CandidateContract", None), "V122 model contract missing")
        approval = self._approval()
        self.assertEqual(approval.statement, f"USER APPROVED IMPORT BATCH {approval.batch_id} {SHA_B} V1.22 PARENT {GENESIS}")
        with self.assertRaises(ImportApprovalError):
            self.module.V122ImportApproval("batch 1", SHA_B, "V1.22", GENESIS, approval.statement)
        with self.assertRaises(ImportApprovalError):
            self.module.V122ImportApproval(approval.batch_id, SHA_B.upper(), "V1.22", GENESIS, approval.statement)
        with self.assertRaises(ImportApprovalError):
            self.module.V122ImportApproval(approval.batch_id, SHA_B, "V1.21", GENESIS, approval.statement)

    def test_approved_batch_binds_ready_result_to_exact_approval(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v122_models"), "V122CandidateContract", None), "V122 model contract missing")
        approved = self._approved_batch()
        self.assertTrue(approved.package_root.is_absolute())
        result = self._result()
        mismatched = self.module.V122ImportApproval("other", SHA_B, "V1.22", GENESIS, f"USER APPROVED IMPORT BATCH other {SHA_B} V1.22 PARENT {GENESIS}")
        with self.assertRaises(ImportApprovalError):
            self.module.V122ApprovedBatch(result, Path("."), mismatched)

    def test_contract_is_exact_and_rejects_bool_and_tuple_changes(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v122_models"), "V122CandidateContract", None), "V122 model contract missing")
        contract = self._contract()
        self.assertEqual(contract.required_candidate_tables, ("task12_v122_batch_ledger_v1", "task12_v122_candidates_v1", "task12_v122_images_v1", "task12_v122_taxonomy_v1"))
        values = list(contract.__dict__.values())
        values[15] = True
        with self.assertRaises(PipelineError):
            self.module.V122CandidateContract(*values)
        values = list(contract.__dict__.values())
        values[-1] = []
        with self.assertRaises(PipelineError):
            self.module.V122CandidateContract(*values)

    def test_build_and_verification_requests_require_a_nonempty_ordered_prefix(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v122_models"), "V122CandidateContract", None), "V122 model contract missing")
        approved = self._approved_batch()
        build = self.module.V122CandidateBuildRequest([approved], Path("."), self._contract())
        verify = self.module.V122CandidateVerificationRequest(Path("."), [approved], self._contract())
        self.assertEqual(build.approved_batches, (approved,))
        self.assertEqual(verify.approved_batches, (approved,))
        for request, path in ((self.module.V122CandidateBuildRequest, Path(".")), (self.module.V122CandidateVerificationRequest, Path("."))):
            with self.assertRaises(PipelineError):
                request([], path, self._contract())

    def test_candidate_artifacts_require_exact_kinds_and_stable_destination_order(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v122_models"), "V122CandidateContract", None), "V122 model contract missing")
        report = VerificationReport("PASS", ())
        state = self._state()
        database = ArtifactRef(Path("/tmp/db"), SHA_A, 1, "sqlite")
        manifest = ArtifactRef(Path("/tmp/manifest"), SHA_A, 1, "manifest")
        sums = ArtifactRef(Path("/tmp/sums"), SHA_A, 1, "sha256sums")
        rollback = ArtifactRef(Path("/tmp/rollback"), SHA_A, 1, "rollback")
        preflight = ArtifactRef(Path("/tmp/authority/1/preflight.json"), SHA_A, 1, "preflight")
        approval = ArtifactRef(Path("/tmp/authority/1/approval.json"), SHA_A, 1, "approval")
        image = ArtifactRef(Path("/tmp/images/a"), SHA_A, 1, "image")
        artifacts = self.module.V122CandidateArtifacts(database, manifest, sums, rollback, [approval, preflight], [image], state, report)
        self.assertEqual(artifacts.batch_authorities, (approval, preflight))
        with self.assertRaises(PipelineError):
            self.module.V122CandidateArtifacts(manifest, manifest, sums, rollback, [], [], state, report)
        for position, malformed in (
            (0, ArtifactRef(Path("/tmp/db"), "BAD", 1, "sqlite")),
            (1, ArtifactRef(Path("/tmp/manifest"), SHA_A, True, "manifest")),
            (4, [ArtifactRef(Path("/tmp/authority/1/preflight.json"), "BAD", 1, "preflight")]),
            (5, [ArtifactRef(Path("/tmp/images/a"), SHA_A, True, "image")]),
        ):
            values = [database, manifest, sums, rollback, [approval, preflight], [image], state, report]
            values[position] = malformed
            with self.subTest(position=position), self.assertRaises(PipelineError):
                self.module.V122CandidateArtifacts(*values)

    def test_historical_v119_contracts_remain_closed_to_v122(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v122_models"), "V122CandidateContract", None), "V122 model contract missing")
        self.assertEqual(BatchImportManifest.__dataclass_fields__["target_release_version"].type, "str")
        with self.assertRaises(PipelineError):
            BatchImportManifest(
                "task9-import-manifest-v1", "batch", "Joy M2 AI Database", "M2", "chapter", "V1.22",
                [], [], [], [], [], [], "preserve_source_and_store_reviewed_chinese_separately",
                "one_complete_question_per_record", "joy_level_1_5", "controlled_primary_type_and_tags",
                "preserve_source_answer_identity", "source_or_independently_verified_with_identity",
            )
        self.assertEqual(V119WriterContract.__dataclass_fields__["profile"].type, "str")
        self.assertEqual(V119PromotionContract.__dataclass_fields__["profile"].type, "str")
        self.assertNotIn("V1.22", repr(V119WriterContract))
        with self.assertRaises(PipelineError):
            V119WriterContract(
                "V1.22", "task11-v121-candidate-manifest-v1", "task11-v121-candidate-v1", 119,
                "Joy_M2_V1.21_candidate.sqlite3", "candidate_manifest.json", "SHA256SUMS",
                "rollback.json", "images/sha256", (), (), (),
            )
        with self.assertRaises(PipelineError):
            V119PromotionContract(
                "V1.22", "task11-v121-formal-manifest-v1", "task11-v121-formal-v1",
                "task11-v121-promotion-identity-v1", "task11-v121-formal-rollback-v1", 119,
                "Joy_M2_Complete_Question_DB_V1_19.sqlite3", "manifest.json", "SHA256SUMS.txt",
                "rollback.json", "images/sha256", "task9_promoted_questions_v1",
                "task9_promotion_v1", "formal_complete_questions_v121",
            )
        historical_report = ImportPreflightReport(
            "batch", "READY FOR USER IMPORT APPROVAL", SHA_A, SHA_B, "V1.18", 497,
            "V1.19", 0, 0, 0, 0, 0, 0, 497, (), (), (), 0, 0, (), (), (), (), (), (),
            (), (), (), (), (),
        )
        with self.assertRaises(PipelineError):
            replace(historical_report, target_release_version="V1.22")
        with self.assertRaises(PipelineError):
            V119WriteRequest(self._result(), Path("."), object(), Path("."), object())
        with self.assertRaises(PipelineError):
            V119PromotionBuildRequest(
                self.module.V122CandidateVerificationRequest(Path("."), [self._approved_batch()], self._contract()),
                Path("."), object(),
            )


if __name__ == "__main__":
    unittest.main()


class V122ApiTests(unittest.TestCase):
    def test_exact_append_only_surface(self):
        import joy_m2.ingest as m
        self.assertEqual(m.__all__, ('BatchImportManifest', 'ImportAdaptation', 'ImportCandidate', 'ImportFileEvidence', 'ImportIssue', 'ImportPreflightReport', 'ImportPreflightResult', 'load_import_manifest', 'preflight_import', 'MmdSelection', 'MmdAdapterManifest', 'MmdAdapterIssue', 'MmdAdapterBlockedError', 'AdaptedImportPackage', 'adapt_mmd_package', 'ImportApproval', 'V119WriterContract', 'V119WriteRequest', 'V119VerificationRequest', 'V119CandidateArtifacts', 'build_v119_candidate', 'verify_v119_candidate', 'V119PromotionContract', 'V119PromotionBuildRequest', 'V119PromotionVerificationRequest', 'ReleasePromotionApproval', 'V119PublicationRequest', 'V119PromotionArtifacts', 'build_v119_promotion', 'verify_v119_promotion', 'publish_v119_release', 'V120BatchImportManifest', 'V120AdaptedImportPackage', 'V120BatchLedgerEntry', 'V120EffectiveState', 'V120PreflightRequest', 'V120ImportPreflightReport', 'V120ImportPreflightResult', 'V120ImportApproval', 'V120ApprovedBatch', 'V120CandidateContract', 'V120CandidateBuildRequest', 'V120CandidateVerificationRequest', 'V120CandidateArtifacts', 'load_v120_import_manifest', 'adapt_mmd_package_v120', 'preflight_v120_import', 'build_v120_candidate', 'verify_v120_candidate', 'HkdsePdfPageSpan', 'HkdsePdfExtractionRecord', 'HkdsePdfExtractionPass', 'HkdsePdfTranscriptionIssue', 'HkdsePdfTranscriptionRecord', 'HkdsePdfTranscriptionBatch', 'HkdsePdfTranscriptionApproval', 'VerifiedHkdsePdfTranscriptionBatch', 'HkdsePdfAdapterBlockedError', 'V121BatchImportManifest', 'V121AdaptedImportPackage', 'V121BatchLedgerEntry', 'V121EffectiveState', 'V121PreflightRequest', 'V121ImportPreflightReport', 'V121ImportPreflightResult', 'V121ImportApproval', 'V121ApprovedBatch', 'V121CandidateContract', 'V121CandidateBuildRequest', 'V121CandidateVerificationRequest', 'V121CandidateArtifacts', 'load_v121_import_manifest', 'preflight_v121_import', 'build_v121_candidate', 'verify_v121_candidate', 'adapt_verified_hkdse_pdf_transcription_v121', 'extract_hkdse_pdf_embedded_pass', 'load_hkdse_pdf_extraction_pass', 'propose_hkdse_pdf_transcription', 'approve_hkdse_pdf_transcription', 'adapt_verified_hkdse_pdf_transcription_v120', 'V120PromotionContract', 'V120PromotionBuildRequest', 'V120PromotionVerificationRequest', 'V120ReleasePromotionApproval', 'V120PublicationRequest', 'V120PromotionArtifacts', 'build_v120_promotion', 'verify_v120_promotion', 'publish_v120_release', 'V121PromotionContract', 'V121PromotionBuildRequest', 'V121PromotionVerificationRequest', 'V121ReleasePromotionApproval', 'V121PublicationRequest', 'V121PromotionArtifacts', 'build_v121_promotion', 'verify_v121_promotion', 'publish_v121_release') + ("V122BatchImportManifest","V122AdaptedImportPackage","V122BatchLedgerEntry","V122EffectiveState","V122PreflightRequest","V122ImportPreflightReport","V122ImportPreflightResult","V122ImportApproval","V122ApprovedBatch","V122CandidateContract","V122CandidateBuildRequest","V122CandidateVerificationRequest","V122CandidateArtifacts","load_v122_import_manifest","preflight_v122_import","build_v122_candidate","verify_v122_candidate","adapt_verified_hkdse_pdf_transcription_v122",))

    def test_five_api_signatures(self):
        import joy_m2.ingest as m
        from joy_m2.config import PipelineConfig
        from joy_m2.ingest import v122_models as v
        from joy_m2.ingest.hkdse_pdf_models import VerifiedHkdsePdfTranscriptionBatch
        expected = {
            "load_v122_import_manifest": (("path",), (Path, v.V122BatchImportManifest)),
            "preflight_v122_import": (("request", "config"), (v.V122PreflightRequest, PipelineConfig, v.V122ImportPreflightResult)),
            "build_v122_candidate": (("request", "config"), (v.V122CandidateBuildRequest, PipelineConfig, v.V122CandidateArtifacts)),
            "verify_v122_candidate": (("request", "config"), (v.V122CandidateVerificationRequest, PipelineConfig, VerificationReport)),
            "adapt_verified_hkdse_pdf_transcription_v122": (("verified", "output_dir", "config"), (VerifiedHkdsePdfTranscriptionBatch, Path, PipelineConfig, v.V122AdaptedImportPackage)),
        }
        for name, (params, hints) in expected.items():
            with self.subTest(name=name):
                fn = getattr(m, name, None)
                self.assertIsNotNone(fn, "public API missing")
                self.assertEqual(tuple(inspect.signature(fn).parameters), params)
                self.assertEqual(tuple(get_type_hints(fn).values()), hints)


class V122LoaderTests(unittest.TestCase):
    def setUp(self):
        import tempfile, shutil, json
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "package"
        shutil.copytree(Path(__file__).resolve().parents[2] / "tests/fixtures/task10a/v120-batch-a", self.root)
        self.path = self.root / "import_manifest.json"
        self.payload = json.loads(self.path.read_text())
        self.payload["schema_version"] = "task12-v122-import-manifest-v1"
        self.payload["target_release_version"] = "V1.22"
        self.write()

    def write(self):
        import json
        self.path.write_text(json.dumps(self.payload, ensure_ascii=False) + "\n", encoding="utf-8")

    def load(self):
        from joy_m2.ingest import load_v122_import_manifest
        try:
            return load_v122_import_manifest(self.path)
        except NotImplementedError:
            self.fail("strict V1.22 loader behavior missing")

    def test_load_exact_manifest_and_semantic_file_order(self):
        result = self.load()
        self.assertEqual(result.target_release_version, "V1.22")
        self.assertEqual(tuple(x.relative_path for x in result.candidate_records),
                         tuple(x["relative_path"] for x in self.payload["candidate_records"]))
        self.assertEqual(len(fields(result)), 18)

    def test_duplicate_json_key_rejected(self):
        self.path.write_text(self.path.read_text().replace('{"schema_version":', '{"batch_id":"forged","schema_version":', 1))
        with self.assertRaises(PipelineError):
            self.load()

    def test_missing_extra_wrong_type_and_group_rejected(self):
        import copy
        original = copy.deepcopy(self.payload)
        for mutation in ("missing", "extra", "wrong_type", "group_type", "kind", "escape", "order", "digest"):
            with self.subTest(mutation=mutation):
                self.payload = copy.deepcopy(original)
                if mutation == "missing":
                    del self.payload["batch_id"]
                elif mutation == "extra":
                    self.payload["unapproved"] = 1
                elif mutation == "wrong_type":
                    self.payload["batch_id"] = True
                elif mutation == "group_type":
                    self.payload["candidate_records"] = {}
                elif mutation == "kind":
                    self.payload["candidate_records"][0]["kind"] = "image"
                elif mutation == "escape":
                    self.payload["candidate_records"][0]["relative_path"] = "../outside.json"
                elif mutation == "order":
                    self.payload["schema_version"] = self.payload.pop("schema_version")
                else:
                    self.payload["candidate_records"][0]["sha256"] = "0" * 64
                self.write()
                with self.assertRaises(PipelineError):
                    self.load()

    def test_inventory_closure_and_symlinks_rejected(self):
        rogue = self.root / "rogue.txt"
        rogue.write_text("rogue")
        with self.assertRaises(PipelineError):
            self.load()
        rogue.unlink()
        rogue.symlink_to(self.path)
        with self.assertRaises(PipelineError):
            self.load()
