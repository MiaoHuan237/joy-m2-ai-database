"""Public-contract tests for the Task 9C V1.19 candidate writer."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, MISSING, fields
import importlib
import inspect
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from typing import get_type_hints

from joy_m2.config import PipelineConfig
from joy_m2.errors import PipelineError
from joy_m2.ingest.models import (
    BatchImportManifest,
    ImportCandidate,
    ImportPreflightReport,
    ImportPreflightResult,
)
from joy_m2.models import ArtifactRef, VerificationCheck, VerificationReport


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64

BASELINE_TABLES = (
    "complete_question_corrections_v2",
    "complete_question_tags_v2",
    "complete_question_taxonomy_v2",
    "complete_questions_v2",
    "import_runs_v2",
    "question_topics",
    "questions",
    "release_metadata_v2",
    "sources",
    "topics",
)
CANDIDATE_TABLES = (
    "task9_import_batches_v1",
    "task9_import_candidates_v1",
    "task9_import_images_v1",
    "task9_import_taxonomy_v1",
)
CANDIDATE_VIEWS = ("task9_candidate_questions_v1",)

PUBLIC_NAMES = (
    "BatchImportManifest",
    "ImportAdaptation",
    "ImportCandidate",
    "ImportFileEvidence",
    "ImportIssue",
    "ImportPreflightReport",
    "ImportPreflightResult",
    "load_import_manifest",
    "preflight_import",
    "MmdSelection",
    "MmdAdapterManifest",
    "MmdAdapterIssue",
    "MmdAdapterBlockedError",
    "AdaptedImportPackage",
    "adapt_mmd_package",
    "ImportApproval",
    "V119WriterContract",
    "V119WriteRequest",
    "V119VerificationRequest",
    "V119CandidateArtifacts",
    "build_v119_candidate",
    "verify_v119_candidate",
)


def _load_task9c(testcase: unittest.TestCase):
    """Turn an absent public surface into assertion RED, never import ERROR."""

    try:
        errors = importlib.import_module("joy_m2.errors")
        models = importlib.import_module("joy_m2.ingest.writer_models")
        writer = importlib.import_module("joy_m2.ingest.writer")
        verification = importlib.import_module("joy_m2.ingest.writer_verification")
        package = importlib.import_module("joy_m2.ingest")
        return (
            errors.ImportApprovalError,
            models.ImportApproval,
            models.V119WriterContract,
            models.V119WriteRequest,
            models.V119VerificationRequest,
            models.V119CandidateArtifacts,
            writer.build_v119_candidate,
            verification.verify_v119_candidate,
            package,
        )
    except (ImportError, AttributeError) as error:
        testcase.fail(f"Task 9C public contract is missing: {error}")


def _manifest(batch_id: str = "TASK9C-TEST-001") -> BatchImportManifest:
    return BatchImportManifest(
        schema_version="task9-import-manifest-v1",
        batch_id=batch_id,
        project="Joy M2 AI Database",
        module="M2",
        chapter="Task 9C Test",
        target_release_version="V1.19",
        candidate_records=(),
        source_files=(),
        answer_files=(),
        image_files=(),
        teacher_notes_files=(),
        common_errors_files=(),
        language_policy="preserve_source_and_store_reviewed_chinese_separately",
        split_policy="one_complete_question_per_record",
        difficulty_policy="joy_level_1_5",
        tag_policy="controlled_primary_type_and_tags",
        answer_policy="preserve_source_answer_identity",
        explanation_policy="source_or_independently_verified_with_identity",
    )


def _candidate() -> ImportCandidate:
    return ImportCandidate(
        proposed_question_id="TASK9C-Q001",
        source_id="TASK9C-SOURCE",
        source_question_number="1",
        source_section="Test",
        source_fragment_hash=SHA_A,
        normalized_text_sha256=SHA_B,
        question_text_original="Question",
        question_text_zh="题目",
        translation_status="source_present",
        translation_evidence="source:source/test.txt#question-1",
        solution_original="",
        solution_verified="",
        answer_status="missing_from_source",
        explanation_text="",
        explanation_status="missing",
        explanation_evidence=None,
        image_paths=(),
        image_sha256s=(),
        image_roles=(),
        primary_type="Algebra",
        tags=("Test",),
        tag_status="source_provided",
        difficulty_level=2,
        difficulty_status="source_provided",
        enrichment_status="complete",
    )


def _preflight(root: Path, batch_id: str = "TASK9C-TEST-001") -> ImportPreflightResult:
    candidate = _candidate()
    report = ImportPreflightReport(
        batch_id=batch_id,
        status="READY FOR USER IMPORT APPROVAL",
        preflight_sha256=SHA_A,
        manifest_sha256=SHA_B,
        baseline_version="V1.18",
        before_count=497,
        target_release_version="V1.19",
        detected_count=1,
        new_candidate_count=1,
        duplicate_count=0,
        rejected_count=0,
        ambiguous_count=0,
        approved_count=0,
        projected_after_count=498,
        readable_files=(),
        unreadable_files=(),
        unsupported_files=(),
        teacher_notes_file_count=0,
        common_errors_file_count=0,
        ambiguous_splits=(),
        missing_answers=(candidate.proposed_question_id,),
        missing_explanations=(candidate.proposed_question_id,),
        incomplete_enrichments=(),
        missing_images=(),
        orphan_images=(),
        level_counts=((2, 1),),
        proposed_ids=(candidate.proposed_question_id,),
        adaptations=(),
        warnings=(),
        blocking_errors=(),
    )
    return ImportPreflightResult(
        manifest=_manifest(batch_id),
        baseline_database=ArtifactRef(root / "baseline.sqlite3", SHA_C, 1, "sqlite"),
        candidates=(candidate,),
        issues=(),
        report=report,
    )


def _subclass_copy(value):
    subtype = type(f"{type(value).__name__}Subclass", (type(value),), {})
    return subtype(**{field.name: getattr(value, field.name) for field in fields(value)})


class V119WriterPublicContractTests(unittest.TestCase):
    def setUp(self) -> None:
        (
            self.ImportApprovalError,
            self.ImportApproval,
            self.V119WriterContract,
            self.V119WriteRequest,
            self.V119VerificationRequest,
            self.V119CandidateArtifacts,
            self.build_v119_candidate,
            self.verify_v119_candidate,
            self.ingest_package,
        ) = _load_task9c(self)

    def approval(self, batch_id: str = "TASK9C-TEST-001"):
        return self.ImportApproval(
            batch_id=batch_id,
            preflight_sha256=SHA_A,
            target_release_version="V1.19",
            statement=f"USER APPROVED IMPORT BATCH {batch_id} {SHA_A} V1.19",
        )

    def contract(self):
        return self.V119WriterContract(
            profile="V1.19",
            candidate_manifest_schema="task9-v119-candidate-manifest-v1",
            candidate_database_schema="task9-v119-candidate-v1",
            expected_user_version=119,
            database_filename="Joy_M2_V1.19_candidate.sqlite3",
            manifest_filename="candidate_manifest.json",
            sha256s_filename="SHA256SUMS",
            rollback_filename="rollback.json",
            image_root="images/sha256",
            required_baseline_tables=BASELINE_TABLES,
            required_candidate_tables=CANDIDATE_TABLES,
            required_candidate_views=CANDIDATE_VIEWS,
        )

    def test_exact_fields_order_types_no_defaults_and_frozen(self) -> None:
        expected = {
            self.ImportApproval: (
                ("batch_id", str),
                ("preflight_sha256", str),
                ("target_release_version", str),
                ("statement", str),
            ),
            self.V119WriterContract: (
                ("profile", str),
                ("candidate_manifest_schema", str),
                ("candidate_database_schema", str),
                ("expected_user_version", int),
                ("database_filename", str),
                ("manifest_filename", str),
                ("sha256s_filename", str),
                ("rollback_filename", str),
                ("image_root", str),
                ("required_baseline_tables", tuple[str, ...]),
                ("required_candidate_tables", tuple[str, ...]),
                ("required_candidate_views", tuple[str, ...]),
            ),
            self.V119WriteRequest: (
                ("preflight_result", ImportPreflightResult),
                ("package_root", Path),
                ("approval", self.ImportApproval),
                ("output_dir", Path),
                ("contract", self.V119WriterContract),
            ),
            self.V119VerificationRequest: (
                ("candidate_dir", Path),
                ("preflight_result", ImportPreflightResult),
                ("approval", self.ImportApproval),
                ("contract", self.V119WriterContract),
            ),
            self.V119CandidateArtifacts: (
                ("database", ArtifactRef),
                ("manifest", ArtifactRef),
                ("sha256sums", ArtifactRef),
                ("rollback", ArtifactRef),
                ("images", tuple[ArtifactRef, ...]),
                ("verification_report", VerificationReport),
            ),
        }
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            instances = {
                self.ImportApproval: self.approval(),
                self.V119WriterContract: self.contract(),
                self.V119WriteRequest: self.V119WriteRequest(
                    _preflight(root), root / "package", self.approval(), root / "output", self.contract()
                ),
                self.V119VerificationRequest: self.V119VerificationRequest(
                    root / "candidate", _preflight(root), self.approval(), self.contract()
                ),
                self.V119CandidateArtifacts: self.V119CandidateArtifacts(
                    ArtifactRef(root / "db", SHA_A, 1, "sqlite"),
                    ArtifactRef(root / "manifest", SHA_A, 1, "manifest"),
                    ArtifactRef(root / "sums", SHA_A, 1, "sha256sums"),
                    ArtifactRef(root / "rollback", SHA_A, 1, "rollback"),
                    (),
                    VerificationReport("PASS", (VerificationCheck("check", True, "PASS"),)),
                ),
            }
        for model, contract in expected.items():
            self.assertEqual(tuple((field.name, get_type_hints(model)[field.name]) for field in fields(model)), contract)
            self.assertTrue(all(field.default is MISSING and field.default_factory is MISSING for field in fields(model)))
            with self.assertRaises(FrozenInstanceError):
                setattr(instances[model], fields(model)[0].name, object())

    def test_approval_accepts_only_exact_digest_bound_statement(self) -> None:
        approval = self.approval()
        self.assertEqual(approval.target_release_version, "V1.19")

        class StringSubclass(str):
            pass

        mutations = (
            {"batch_id": 1},
            {"batch_id": ""},
            {"batch_id": "a\nb"},
            {"batch_id": "a\rb"},
            {"batch_id": StringSubclass(approval.batch_id)},
            {"preflight_sha256": SHA_A.upper()},
            {"preflight_sha256": "x" * 64},
            {"preflight_sha256": StringSubclass(SHA_A)},
            {"target_release_version": "V1.18"},
            {"target_release_version": StringSubclass("V1.19")},
            {"statement": "USER APPROVED IMPORT BATCH wrong " + SHA_A + " V1.19"},
            {"statement": 1},
            {"statement": StringSubclass(approval.statement)},
        )
        values = {field.name: getattr(approval, field.name) for field in fields(approval)}
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(
                self.ImportApprovalError
            ):
                self.ImportApproval(**(values | mutation))

    def test_writer_contract_accepts_only_exact_closed_profile(self) -> None:
        contract = self.contract()
        self.assertEqual(contract.required_baseline_tables, BASELINE_TABLES)
        self.assertEqual(contract.required_candidate_tables, CANDIDATE_TABLES)
        self.assertEqual(contract.required_candidate_views, CANDIDATE_VIEWS)

        class StringSubclass(str):
            pass

        class IntSubclass(int):
            pass

        values = {field.name: getattr(contract, field.name) for field in fields(contract)}
        mutations = (
            {"profile": "V1.18"},
            {"profile": StringSubclass("V1.19")},
            {"candidate_manifest_schema": "other"},
            {"candidate_database_schema": "other"},
            {"expected_user_version": True},
            {"expected_user_version": 118},
            {"expected_user_version": IntSubclass(119)},
            {"database_filename": "other.sqlite3"},
            {"manifest_filename": "manifest.json"},
            {"sha256s_filename": "SHA256SUMS.txt"},
            {"rollback_filename": "rollback.txt"},
            {"image_root": "/images"},
            {"required_baseline_tables": tuple(reversed(BASELINE_TABLES))},
            {
                "required_baseline_tables": BASELINE_TABLES[:-1]
                + (BASELINE_TABLES[-2],)
            },
            {"required_baseline_tables": set(BASELINE_TABLES)},
            {
                "required_baseline_tables": (
                    StringSubclass(BASELINE_TABLES[0]),
                    *BASELINE_TABLES[1:],
                )
            },
            {"required_candidate_tables": CANDIDATE_TABLES + ("extra",)},
            {"required_candidate_views": ()},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(PipelineError):
                self.V119WriterContract(**(values | mutation))

    def test_contract_tuples_are_defensively_copied(self) -> None:
        baseline = list(BASELINE_TABLES)
        candidates = list(CANDIDATE_TABLES)
        views = list(CANDIDATE_VIEWS)
        values = {field.name: getattr(self.contract(), field.name) for field in fields(self.contract())}
        values.update(
            required_baseline_tables=baseline,
            required_candidate_tables=candidates,
            required_candidate_views=views,
        )
        contract = self.V119WriterContract(**values)
        baseline.append("changed")
        candidates.clear()
        views.clear()
        self.assertEqual(contract.required_baseline_tables, BASELINE_TABLES)
        self.assertEqual(contract.required_candidate_tables, CANDIDATE_TABLES)
        self.assertEqual(contract.required_candidate_views, CANDIDATE_VIEWS)

    def test_requests_require_exact_carriers_and_path_instances(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            preflight = _preflight(root)
            approval = self.approval()
            contract = self.contract()
            write = self.V119WriteRequest(preflight, root / "package", approval, root / "output", contract)
            verify = self.V119VerificationRequest(root / "candidate", preflight, approval, contract)
            self.assertEqual(write.package_root, (root / "package").resolve())
            self.assertEqual(write.output_dir, (root / "output").resolve())
            self.assertEqual(verify.candidate_dir, (root / "candidate").resolve())
            bad_write = (
                (object(), root / "package", approval, root / "output", contract),
                (_subclass_copy(preflight), root / "package", approval, root / "output", contract),
                (preflight, str(root / "package"), approval, root / "output", contract),
                (preflight, root / "package", object(), root / "output", contract),
                (preflight, root / "package", _subclass_copy(approval), root / "output", contract),
                (preflight, root / "package", approval, str(root / "output"), contract),
                (preflight, root / "package", approval, root / "output", object()),
                (preflight, root / "package", approval, root / "output", _subclass_copy(contract)),
            )
            for arguments in bad_write:
                with self.subTest(arguments=arguments), self.assertRaises(PipelineError):
                    self.V119WriteRequest(*arguments)
            bad_verify = (
                (str(root), preflight, approval, contract),
                (root, object(), approval, contract),
                (root, _subclass_copy(preflight), approval, contract),
                (root, preflight, object(), contract),
                (root, preflight, _subclass_copy(approval), contract),
                (root, preflight, approval, object()),
                (root, preflight, approval, _subclass_copy(contract)),
            )
            for arguments in bad_verify:
                with self.subTest(arguments=arguments), self.assertRaises(PipelineError):
                    self.V119VerificationRequest(*arguments)

    def test_candidate_artifacts_require_exact_kinds_and_copy_images(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = ArtifactRef(root / "db", SHA_A, 1, "sqlite")
            manifest = ArtifactRef(root / "manifest", SHA_A, 1, "manifest")
            sums = ArtifactRef(root / "sums", SHA_A, 1, "sha256sums")
            rollback = ArtifactRef(root / "rollback", SHA_A, 1, "rollback")
            image = ArtifactRef(root / "image.png", SHA_A, 1, "image")
            later_image = ArtifactRef(root / "z-image.png", SHA_A, 1, "image")
            earlier_image = ArtifactRef(root / "a-image.png", SHA_A, 1, "image")
            report = VerificationReport("PASS", (VerificationCheck("check", True, "PASS"),))
            images = [image]
            result = self.V119CandidateArtifacts(database, manifest, sums, rollback, images, report)
            images.clear()
            self.assertEqual(result.images, (image,))
            mutations = (
                (object(), manifest, sums, rollback, (), report),
                (_subclass_copy(database), manifest, sums, rollback, (), report),
                (ArtifactRef(root / "db", SHA_A, 1, "json"), manifest, sums, rollback, (), report),
                (database, object(), sums, rollback, (), report),
                (database, ArtifactRef(root / "manifest", SHA_A, 1, "json"), sums, rollback, (), report),
                (database, manifest, object(), rollback, (), report),
                (database, manifest, ArtifactRef(root / "sums", SHA_A, 1, "text"), rollback, (), report),
                (database, manifest, sums, object(), (), report),
                (database, manifest, sums, ArtifactRef(root / "rollback", SHA_A, 1, "json"), (), report),
                (database, manifest, sums, rollback, (object(),), report),
                (database, manifest, sums, rollback, (ArtifactRef(root / "image", SHA_A, 1, "json"),), report),
                (database, manifest, sums, rollback, (later_image, earlier_image), report),
                (database, manifest, sums, rollback, (), object()),
                (database, manifest, sums, rollback, (), _subclass_copy(report)),
            )
            for arguments in mutations:
                with self.subTest(arguments=arguments), self.assertRaises(PipelineError):
                    self.V119CandidateArtifacts(*arguments)

    def test_error_and_package_surface_are_exact(self) -> None:
        writer_models = importlib.import_module("joy_m2.ingest.writer_models")
        self.assertIs(self.ImportApprovalError.__base__, PipelineError)
        self.assertEqual(self.ImportApprovalError.__module__, "joy_m2.errors")
        self.assertFalse(hasattr(writer_models, "ImportApprovalError"))
        self.assertEqual(self.ingest_package.__all__, PUBLIC_NAMES)
        self.assertFalse(hasattr(self.ingest_package, "ImportApprovalError"))
        for name in PUBLIC_NAMES:
            self.assertTrue(hasattr(self.ingest_package, name), name)

    def test_api_signatures_are_exact(self) -> None:
        self.assertEqual(
            str(inspect.signature(self.build_v119_candidate)),
            "(request: 'V119WriteRequest', config: 'PipelineConfig') -> 'V119CandidateArtifacts'",
        )
        self.assertEqual(
            str(inspect.signature(self.verify_v119_candidate)),
            "(request: 'V119VerificationRequest', config: 'PipelineConfig') -> 'VerificationReport'",
        )

    def test_api_scaffolds_raise_without_filesystem_changes(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = PipelineConfig(root)
            package = root / "package"
            package.mkdir()
            output = config.staging_root / "candidate"
            write = self.V119WriteRequest(_preflight(root), package, self.approval(), output, self.contract())
            verify = self.V119VerificationRequest(output, _preflight(root), self.approval(), self.contract())
            before = tuple(sorted(path.relative_to(root) for path in root.rglob("*")))
            for function, request in ((self.build_v119_candidate, write), (self.verify_v119_candidate, verify)):
                with self.subTest(function=function.__name__), self.assertRaisesRegex(
                    NotImplementedError, "^Task 9C writer behavior is not implemented$"
                ):
                    function(request, config)
            after = tuple(sorted(path.relative_to(root) for path in root.rglob("*")))
            self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
