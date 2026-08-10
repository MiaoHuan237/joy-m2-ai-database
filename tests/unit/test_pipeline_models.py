from __future__ import annotations

from collections.abc import Mapping
from dataclasses import FrozenInstanceError, fields, is_dataclass
import importlib
from pathlib import Path
import sys
import typing
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

legacy_task6_builder = importlib.import_module("legacy.task6_work.build_task6_release")


PUBLIC_VALUE_TYPES = (
    "ReleaseSpec",
    "ApprovalRecord",
    "ArtifactRef",
    "AuditIssue",
    "Correction",
    "PublicationEvidence",
    "QuestionImage",
    "AuditedQuestion",
    "AuditedBatch",
    "AuditResult",
    "AuditContract",
    "AuditRequest",
    "DatabaseContract",
    "DatabaseBuildRequest",
    "DatabaseArtifact",
    "ExportContract",
    "ExportRequest",
    "ExportVerificationRequest",
    "DerivedArtifacts",
    "ReleaseContract",
    "CandidateBuildRequest",
    "VerificationCheck",
    "VerificationReport",
    "CandidateRelease",
    "FormalRelease",
)

ACTUAL_LEGACY_TABLE_COLUMNS = tuple(legacy_task6_builder.TABLE_COLUMNS)

AUDITED_QUESTION_FIELDS = (
    "question_id",
    "source_id",
    "source_question_number",
    "source_section",
    "source_file",
    "source_member",
    "source_sha256",
    "source_member_sha256",
    "source_fragment_hash",
    "source_page",
    "solution_source_file",
    "solution_source_member",
    "solution_source_member_sha256",
    "question_text_original",
    "question_text_zh",
    "question_text_zh_reviewed",
    "question_latex",
    "marks_total",
    "year",
    "image_paths",
    "solution_original",
    "solution_verified",
    "answer_status",
    "answer_verification_status",
    "official_marking_available",
    "primary_type",
    "tags",
    "difficulty_level",
    "difficulty_evidence",
    "difficulty_dimensions",
    "old_difficulty",
    "old_difficulty_label",
    "old_tags",
    "question_review_status",
    "formula_review_status",
    "image_review_status",
    "answer_review_status",
    "correction_status",
    "corrections",
    "duplicate_status",
    "duplicate_reference",
    "duplicate_evidence",
    "audit_notes",
    "review_checks",
    "unresolved_issues",
    "publication_evidence",
    "audited_at",
    "schema_version",
    "selectable",
    "source_heading",
    "formal_release_version",
    "source_order",
)

EXACT_FIELD_CONTRACTS = {
    "ReleaseSpec": (
        "release_version",
        "baseline_version",
        "baseline_sqlite_sha256",
        "schema_version",
        "created_at",
    ),
    "ApprovalRecord": (
        "release_version",
        "candidate_manifest_sha256",
        "approved_by",
        "approved_at",
        "scope",
    ),
    "ArtifactRef": ("path", "sha256", "size_bytes", "kind"),
    "AuditIssue": ("code", "severity", "question_id", "field", "evidence"),
    "Correction": ("field", "error_origin", "original", "corrected", "reason", "evidence"),
    "PublicationEvidence": ("record_status", "joy_approval", "approved_at"),
    "QuestionImage": ("path", "sha256", "role"),
    "AuditedQuestion": AUDITED_QUESTION_FIELDS,
    "AuditedBatch": ("records",),
    "AuditResult": ("records", "issues", "answer_status_counts", "status"),
    "AuditContract": (
        "profile",
        "release_version",
        "schema_version",
        "expected_question_count",
        "expected_source_count",
        "expected_answer_status_counts",
        "allowed_tags",
        "required_fields",
    ),
    "AuditRequest": ("source_path", "asset_root", "contract", "selected_source_ids"),
    "DatabaseContract": (
        "profile",
        "expected_user_version",
        "expected_question_count",
        "expected_existing_question_count",
        "expected_new_question_count",
        "expected_answer_status_counts",
        "required_tables",
        "required_views",
        "journal_mode",
        "vacuum",
    ),
    "DatabaseBuildRequest": (
        "batch",
        "baseline_database",
        "baseline_manifest",
        "output_path",
        "release_spec",
        "contract",
    ),
    "DatabaseArtifact": ("database", "release_spec", "verification_report"),
    "ExportContract": (
        "profile",
        "csv_filename",
        "knowledge_markdown_filename",
        "import_report_filename",
        "project_state_filename",
        "taxonomy_filename",
        "expected_question_count",
        "expected_missing_answer_count",
    ),
    "ExportRequest": ("database", "output_dir", "contract"),
    "ExportVerificationRequest": ("database", "artifacts", "contract"),
    "DerivedArtifacts": (
        "csv",
        "knowledge_markdown",
        "import_report",
        "project_state",
        "taxonomy",
    ),
    "ReleaseContract": (
        "profile",
        "audit_records_filename",
        "audit_report_filename",
        "approval_filename",
        "manifest_filename",
        "sha256sums_filename",
        "candidate_zip_filename",
        "formal_zip_filename",
        "archive_root",
        "protected_artifact_kinds",
        "manifest_required_fields",
        "hash_excluded_kinds",
        "zip_excluded_kinds",
    ),
    "CandidateBuildRequest": (
        "config",
        "run_id",
        "release_spec",
        "audit_request",
        "database_contract",
        "export_contract",
        "release_contract",
    ),
    "VerificationCheck": ("name", "passed", "detail"),
    "VerificationReport": ("status", "checks"),
    "CandidateRelease": (
        "run_id",
        "release_version",
        "candidate_manifest_sha256",
        "verification_report",
        "artifacts",
        "candidate_zip",
    ),
    "FormalRelease": ("release_dir", "manifest", "verification_report", "final_hashes"),
}

TUPLE_FIELDS = {
    "AuditedBatch": ("records",),
    "AuditResult": ("records", "issues", "answer_status_counts"),
    "AuditContract": (
        "expected_answer_status_counts",
        "allowed_tags",
        "required_fields",
    ),
    "AuditRequest": ("selected_source_ids",),
    "DatabaseContract": (
        "expected_answer_status_counts",
        "required_tables",
        "required_views",
    ),
    "ReleaseContract": (
        "protected_artifact_kinds",
        "manifest_required_fields",
        "hash_excluded_kinds",
        "zip_excluded_kinds",
    ),
}


def import_required(test: unittest.TestCase, module_name: str):
    importlib.invalidate_caches()
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        test.fail(f"required pipeline interface module is not implemented: {error.name}")


def field_names(value_type: type) -> tuple[str, ...]:
    return tuple(field.name for field in fields(value_type))


def annotation_contains_mapping(annotation: object) -> bool:
    origin = typing.get_origin(annotation)
    if annotation in {dict, Mapping} or origin in {dict, Mapping}:
        return True
    return any(annotation_contains_mapping(argument) for argument in typing.get_args(annotation))


def make_correction(models):
    return models.Correction(
        field="solution_original",
        error_origin="source_original",
        original="old",
        corrected="new",
        reason="reviewed correction",
        evidence="source fragment",
    )


def make_publication_evidence(models):
    return models.PublicationEvidence(
        record_status="published",
        joy_approval="approved_by_joy",
        approved_at="2026-08-08T21:00:00+08:00",
    )


def make_question_image(models, path="assets/q1.png", sha256=None, role=None):
    return models.QuestionImage(path=path, sha256=sha256, role=role)


def make_audited_question(models, **overrides):
    values = {name: "value" for name in AUDITED_QUESTION_FIELDS}
    values.update(
        marks_total=4,
        year=2026,
        official_marking_available=False,
        difficulty_level=2,
        old_difficulty=1,
        selectable=True,
        source_order=46,
        image_paths=[make_question_image(models)],
        tags=["微分"],
        difficulty_dimensions=[("概念数", 1)],
        old_tags=["旧标签"],
        corrections=[make_correction(models)],
        review_checks=[("question_boundary", "pass")],
        unresolved_issues=["pending-source-check"],
        publication_evidence=make_publication_evidence(models),
    )
    values.update(overrides)
    return models.AuditedQuestion(**values)


def make_artifact(models, name: str):
    return models.ArtifactRef(
        path=Path("/tmp") / name,
        sha256="a" * 64,
        size_bytes=1,
        kind="test",
    )


def make_release_spec(models):
    return models.ReleaseSpec(
        release_version="V1.19",
        baseline_version="V1.18",
        baseline_sqlite_sha256="b" * 64,
        schema_version="complete-question-v1.0",
        created_at="2026-08-09T12:00:00+08:00",
    )


def make_audit_contract(models, **overrides):
    values = {
        "profile": "V1.18",
        "release_version": "V1.18",
        "schema_version": "complete-question-v1.0",
        "expected_question_count": 452,
        "expected_source_count": 23,
        "expected_answer_status_counts": [
            ["source_provided", 347],
            ["ai_solved_verified", 71],
            ["missing_from_source", 34],
        ],
        "allowed_tags": ["微分"],
        "required_fields": ["question_id"],
    }
    values.update(overrides)
    return models.AuditContract(**values)


def make_database_contract(models, **overrides):
    values = {
        "profile": "V1.18",
        "expected_user_version": 118,
        "expected_question_count": 497,
        "expected_existing_question_count": 45,
        "expected_new_question_count": 452,
        "expected_answer_status_counts": [
            ["source_provided", 392],
            ["ai_solved_verified", 71],
            ["missing_from_source", 34],
        ],
        "required_tables": ["complete_questions_v2"],
        "required_views": ["selectable_complete_questions_v2"],
        "journal_mode": "DELETE",
        "vacuum": True,
    }
    values.update(overrides)
    return models.DatabaseContract(**values)


def make_release_contract(models, **overrides):
    values = {
        "profile": "V1.18",
        "audit_records_filename": "audited.json",
        "audit_report_filename": "audit-report.json",
        "approval_filename": "approval.json",
        "manifest_filename": "manifest.json",
        "sha256sums_filename": "SHA256SUMS.txt",
        "candidate_zip_filename": "candidate.zip",
        "formal_zip_filename": "formal.zip",
        "archive_root": "release",
        "protected_artifact_kinds": ["database", "csv"],
        "manifest_required_fields": ["release_version", "artifacts"],
        "hash_excluded_kinds": ["sha256sums", "zip"],
        "zip_excluded_kinds": ["zip"],
    }
    values.update(overrides)
    return models.ReleaseContract(**values)


def make_database_artifact(models):
    return models.DatabaseArtifact(
        database=make_artifact(models, "database.sqlite3"),
        release_spec=make_release_spec(models),
        verification_report=models.VerificationReport(
            status="PASS",
            checks=[models.VerificationCheck("database", True, "matched")],
        ),
    )


def make_export_contract(models):
    return models.ExportContract(
        profile="V1.18",
        csv_filename="questions.csv",
        knowledge_markdown_filename="knowledge.md",
        import_report_filename="import.md",
        project_state_filename="PROJECT_STATE.md",
        taxonomy_filename=None,
        expected_question_count=497,
        expected_missing_answer_count=34,
    )


class PipelineErrorContractTests(unittest.TestCase):
    def test_exception_hierarchy_matches_the_approved_contract(self) -> None:
        errors = import_required(self, "joy_m2.errors")
        direct_pipeline_errors = (
            errors.ConfigurationError,
            errors.AuditBlockedError,
            errors.DatabaseBuildError,
            errors.OutputConflictError,
            errors.PromotionError,
        )
        self.assertTrue(all(issubclass(error, errors.PipelineError) for error in direct_pipeline_errors))
        self.assertTrue(issubclass(errors.InputMissingError, errors.InputError))
        self.assertTrue(issubclass(errors.InputFormatError, errors.InputError))
        self.assertTrue(issubclass(errors.BaselineMismatchError, errors.InputError))
        self.assertTrue(issubclass(errors.InputError, errors.PipelineError))
        self.assertTrue(issubclass(errors.ForeignKeyViolationError, errors.DatabaseBuildError))
        self.assertTrue(issubclass(errors.DatabaseIntegrityError, errors.DatabaseBuildError))


class PipelineModelContractTests(unittest.TestCase):
    def test_all_25_approved_shared_value_types_are_public_dataclasses(self) -> None:
        models = import_required(self, "joy_m2.models")
        self.assertEqual(len(PUBLIC_VALUE_TYPES), 25)
        self.assertEqual(
            tuple(name for name in PUBLIC_VALUE_TYPES if hasattr(models, name)),
            PUBLIC_VALUE_TYPES,
        )
        self.assertTrue(all(is_dataclass(getattr(models, name)) for name in PUBLIC_VALUE_TYPES))
        public_dataclasses = {
            name
            for name, value in vars(models).items()
            if not name.startswith("_") and isinstance(value, type) and is_dataclass(value)
        }
        self.assertEqual(public_dataclasses, set(PUBLIC_VALUE_TYPES))

    def test_all_25_shared_dataclasses_are_declared_frozen(self) -> None:
        models = import_required(self, "joy_m2.models")
        for name in PUBLIC_VALUE_TYPES:
            with self.subTest(value_type=name):
                value_type = getattr(models, name)
                self.assertTrue(value_type.__dataclass_params__.frozen)

    def test_every_shared_dataclass_instance_rejects_field_reassignment(self) -> None:
        models = import_required(self, "joy_m2.models")
        for name in PUBLIC_VALUE_TYPES:
            with self.subTest(value_type=name):
                value_type = getattr(models, name)
                declared_fields = fields(value_type)
                self.assertGreater(len(declared_fields), 0, name)
                instance = object.__new__(value_type)
                object.__setattr__(instance, declared_fields[0].name, "original")
                with self.assertRaises(FrozenInstanceError):
                    setattr(instance, declared_fields[0].name, "changed")

    def test_approved_key_types_have_exact_explicit_field_order(self) -> None:
        models = import_required(self, "joy_m2.models")
        self.assertEqual(tuple(EXACT_FIELD_CONTRACTS), PUBLIC_VALUE_TYPES)
        self.assertEqual(len(EXACT_FIELD_CONTRACTS), 25)
        for name, expected in EXACT_FIELD_CONTRACTS.items():
            with self.subTest(value_type=name):
                self.assertEqual(field_names(getattr(models, name)), expected)

    def test_audited_question_maps_the_real_legacy_fields_without_publication_duplication(self) -> None:
        self.assertEqual(
            ACTUAL_LEGACY_TABLE_COLUMNS,
            tuple(legacy_task6_builder.TABLE_COLUMNS),
        )
        self.assertEqual(len(ACTUAL_LEGACY_TABLE_COLUMNS), 54)
        mapped_fields = []
        for name in ACTUAL_LEGACY_TABLE_COLUMNS:
            if name == "record_status":
                mapped_fields.append("publication_evidence")
            elif name not in {"joy_approval", "approved_at"}:
                mapped_fields.append(name)
        self.assertEqual(len(mapped_fields), 52)
        self.assertEqual(tuple(mapped_fields), AUDITED_QUESTION_FIELDS)
        self.assertNotIn("record_status", AUDITED_QUESTION_FIELDS)
        self.assertNotIn("joy_approval", AUDITED_QUESTION_FIELDS)
        self.assertNotIn("approved_at", AUDITED_QUESTION_FIELDS)

    def test_public_values_have_no_extras_or_unbounded_mapping_fields(self) -> None:
        models = import_required(self, "joy_m2.models")
        for name in PUBLIC_VALUE_TYPES:
            with self.subTest(value_type=name):
                value_type = getattr(models, name)
                self.assertNotIn("extras", field_names(value_type))
                annotations = typing.get_type_hints(value_type)
                self.assertFalse(
                    any(annotation_contains_mapping(value) for value in annotations.values()),
                    f"{name} exposes an unbounded mapping field",
                )

    def test_audited_question_collection_inputs_become_tuples_and_parent_is_frozen(self) -> None:
        models = import_required(self, "joy_m2.models")
        question = make_audited_question(models)
        question_image = make_question_image(models)
        expected = {
            "image_paths": (question_image,),
            "tags": ("微分",),
            "difficulty_dimensions": (("概念数", 1),),
            "old_tags": ("旧标签",),
            "corrections": (make_correction(models),),
            "review_checks": (("question_boundary", "pass"),),
            "unresolved_issues": ("pending-source-check",),
        }
        for name, value in expected.items():
            with self.subTest(field=name):
                self.assertEqual(getattr(question, name), value)
                self.assertIsInstance(getattr(question, name), tuple)
        with self.assertRaises(FrozenInstanceError):
            question.tags = ()

    def test_question_image_enforces_only_general_value_invariants(self) -> None:
        models = import_required(self, "joy_m2.models")
        errors = import_required(self, "joy_m2.errors")
        annotations = typing.get_type_hints(models.QuestionImage)
        self.assertEqual(tuple(annotations), ("path", "sha256", "role"))
        self.assertEqual(
            annotations,
            {
                "path": str,
                "sha256": str | None,
                "role": str | None,
            },
        )

        path_only = models.QuestionImage("assets/q1.png", None, None)
        evidenced = models.QuestionImage(
            "assets/q2.png",
            "a" * 64,
            "required_question_figure",
        )
        self.assertEqual(
            (path_only.path, path_only.sha256, path_only.role),
            ("assets/q1.png", None, None),
        )
        self.assertEqual(evidenced.sha256, "a" * 64)
        with self.assertRaises(FrozenInstanceError):
            evidenced.path = "changed.png"

        class StringSubclass(str):
            pass

        invalid_values = (
            ("", None, None),
            (1, None, None),
            (StringSubclass("assets/q1.png"), None, None),
            ("assets/q1.png", "a" * 63, "figure"),
            ("assets/q1.png", "A" * 64, "figure"),
            ("assets/q1.png", "g" * 64, "figure"),
            ("assets/q1.png", 1, "figure"),
            ("assets/q1.png", StringSubclass("a" * 64), "figure"),
            ("assets/q1.png", "a" * 64, ""),
            ("assets/q1.png", "a" * 64, 1),
            ("assets/q1.png", "a" * 64, StringSubclass("figure")),
            ("assets/q1.png", "a" * 64, None),
            ("assets/q1.png", None, "figure"),
        )
        for path, sha256, role in invalid_values:
            with self.subTest(path=path, sha256=sha256, role=role):
                with self.assertRaises(errors.PipelineError):
                    models.QuestionImage(path, sha256, role)

    def test_audited_question_accepts_only_question_images_and_defensively_copies_lists(self) -> None:
        models = import_required(self, "joy_m2.models")
        errors = import_required(self, "joy_m2.errors")
        annotations = typing.get_type_hints(models.AuditedQuestion)
        self.assertEqual(
            annotations["image_paths"],
            tuple[models.QuestionImage, ...],
        )
        first = make_question_image(models, "assets/first.png")
        second = make_question_image(models, "assets/second.png", "b" * 64, "figure")
        source_images = [first, second]

        question = make_audited_question(models, image_paths=source_images)
        source_images.reverse()
        source_images.append(first)

        self.assertEqual(question.image_paths, (first, second))
        self.assertIs(question.image_paths[0], first)
        self.assertIs(question.image_paths[1], second)
        self.assertIsInstance(question.image_paths, tuple)
        with self.assertRaises(FrozenInstanceError):
            question.image_paths = ()

        invalid_collections = (
            ["assets/q1.png"],
            [{"path": "assets/q1.png", "sha256": None, "role": None}],
            {"path": "assets/q1.png"},
            [first, "assets/q2.png"],
        )
        for image_paths in invalid_collections:
            with self.subTest(image_paths=image_paths):
                with self.assertRaises(errors.PipelineError):
                    make_audited_question(models, image_paths=image_paths)

    def test_audited_question_nullable_integer_fields_reject_bool_and_coercion(self) -> None:
        models = import_required(self, "joy_m2.models")
        errors = import_required(self, "joy_m2.errors")
        annotations = typing.get_type_hints(models.AuditedQuestion)
        self.assertEqual(annotations["marks_total"], int | None)
        self.assertEqual(annotations["year"], int | None)
        for marks_total, year in ((None, None), (4, None), (None, 2026), (4, 2026)):
            with self.subTest(marks_total=marks_total, year=year):
                question = make_audited_question(
                    models,
                    marks_total=marks_total,
                    year=year,
                )
                self.assertIs(question.marks_total, marks_total)
                self.assertIs(question.year, year)

        for field, value in (
            ("marks_total", True),
            ("marks_total", "4"),
            ("marks_total", 4.0),
            ("year", False),
            ("year", "2026"),
            ("year", 2026.0),
        ):
            with self.subTest(field=field, value=value):
                with self.assertRaises(errors.PipelineError):
                    make_audited_question(models, **{field: value})

    def test_audit_contract_profile_is_a_closed_literal_at_type_and_runtime(self) -> None:
        models = import_required(self, "joy_m2.models")
        errors = import_required(self, "joy_m2.errors")
        self.assertEqual(typing.get_args(models.AuditProfile), ("V1.17", "V1.18"))
        self.assertIs(
            typing.get_type_hints(models.AuditContract)["profile"],
            models.AuditProfile,
        )
        for profile in ("V1.17", "V1.18"):
            with self.subTest(profile=profile):
                self.assertEqual(make_audit_contract(models, profile=profile).profile, profile)
        for profile in ("", "v1.18", "V1.19", 118, True):
            with self.subTest(profile=profile):
                with self.assertRaises(errors.PipelineError):
                    make_audit_contract(models, profile=profile)

    def test_verification_report_normalizes_checks_and_is_frozen(self) -> None:
        models = import_required(self, "joy_m2.models")
        check = models.VerificationCheck("hashes", False, "mismatch")
        report = models.VerificationReport(status="FAIL", checks=[check])
        self.assertEqual(report.checks, (check,))
        self.assertIsInstance(report.checks, tuple)
        self.assertFalse(all(item.passed for item in report.checks))
        with self.assertRaises(FrozenInstanceError):
            report.checks = ()

    def test_blocking_audit_issue_cannot_become_an_audited_batch(self) -> None:
        models = import_required(self, "joy_m2.models")
        errors = import_required(self, "joy_m2.errors")
        result = models.AuditResult(
            records=[],
            issues=[
                models.AuditIssue(
                    "exact_duplicate",
                    "blocker",
                    "Q1",
                    "question_text_original",
                    "Q0",
                ),
            ],
            answer_status_counts=[],
            status="FAIL",
        )
        self.assertIsInstance(result.records, tuple)
        self.assertIsInstance(result.issues, tuple)
        with self.assertRaises(errors.AuditBlockedError):
            result.require_passed()

    def test_non_blocking_audit_result_preserves_content_in_an_immutable_batch(self) -> None:
        models = import_required(self, "joy_m2.models")
        question = make_audited_question(models)
        result = models.AuditResult(
            records=[question],
            issues=[],
            answer_status_counts=[["value", 1]],
            status="PASS",
        )
        batch = result.require_passed()
        self.assertIsInstance(batch, models.AuditedBatch)
        self.assertEqual(batch.records, (question,))
        self.assertIs(batch.records[0], question)
        self.assertIsInstance(batch.records, tuple)
        with self.assertRaises(FrozenInstanceError):
            batch.records = ()

    def test_audited_batch_directly_normalizes_a_record_list_without_aliasing(self) -> None:
        models = import_required(self, "joy_m2.models")
        first = make_audited_question(models)
        second = make_audited_question(models, question_id="Q2")
        source_records = [first, second]
        batch = models.AuditedBatch(records=source_records)
        source_records.reverse()
        source_records.append(first)
        self.assertEqual(batch.records, (first, second))
        self.assertIs(batch.records[0], first)
        self.assertIs(batch.records[1], second)
        self.assertIsInstance(batch.records, tuple)
        self.assertTrue(batch.__dataclass_params__.frozen)
        with self.assertRaises(FrozenInstanceError):
            batch.records = ()

    def test_all_15_approved_tuple_fields_normalize_lists_without_aliasing(self) -> None:
        models = import_required(self, "joy_m2.models")
        question = make_audited_question(models)
        records = [question]
        issues = []
        result_counts = [["value", 1]]
        audit_counts = [["value", 1]]
        allowed_tags = ["微分"]
        required_fields = ["question_id"]
        selected_source_ids = ["source-a", "source-b"]
        database_counts = [["value", 1]]
        required_tables = ["complete_questions_v2"]
        required_views = ["selectable_complete_questions_v2"]
        protected_kinds = ["database", "csv"]
        manifest_fields = ["release_version", "artifacts"]
        hash_exclusions = ["sha256sums", "zip"]
        zip_exclusions = ["zip"]

        batch = models.AuditedBatch(records=records)
        result = models.AuditResult(
            records=records,
            issues=issues,
            answer_status_counts=result_counts,
            status="PASS",
        )
        audit_contract = make_audit_contract(
            models,
            expected_question_count=1,
            expected_answer_status_counts=audit_counts,
            allowed_tags=allowed_tags,
            required_fields=required_fields,
        )
        audit_request = models.AuditRequest(
            source_path=Path("source.sqlite3"),
            asset_root=Path("assets"),
            contract=audit_contract,
            selected_source_ids=selected_source_ids,
        )
        database_contract = make_database_contract(
            models,
            expected_question_count=1,
            expected_existing_question_count=0,
            expected_new_question_count=1,
            expected_answer_status_counts=database_counts,
            required_tables=required_tables,
            required_views=required_views,
        )
        release_contract = make_release_contract(
            models,
            protected_artifact_kinds=protected_kinds,
            manifest_required_fields=manifest_fields,
            hash_excluded_kinds=hash_exclusions,
            zip_excluded_kinds=zip_exclusions,
        )

        expected = {
            ("AuditedBatch", "records"): (batch, (question,)),
            ("AuditResult", "records"): (result, (question,)),
            ("AuditResult", "issues"): (result, ()),
            ("AuditResult", "answer_status_counts"): (result, (("value", 1),)),
            ("AuditContract", "expected_answer_status_counts"): (
                audit_contract,
                (("value", 1),),
            ),
            ("AuditContract", "allowed_tags"): (audit_contract, ("微分",)),
            ("AuditContract", "required_fields"): (audit_contract, ("question_id",)),
            ("AuditRequest", "selected_source_ids"): (
                audit_request,
                ("source-a", "source-b"),
            ),
            ("DatabaseContract", "expected_answer_status_counts"): (
                database_contract,
                (("value", 1),),
            ),
            ("DatabaseContract", "required_tables"): (
                database_contract,
                ("complete_questions_v2",),
            ),
            ("DatabaseContract", "required_views"): (
                database_contract,
                ("selectable_complete_questions_v2",),
            ),
            ("ReleaseContract", "protected_artifact_kinds"): (
                release_contract,
                ("database", "csv"),
            ),
            ("ReleaseContract", "manifest_required_fields"): (
                release_contract,
                ("release_version", "artifacts"),
            ),
            ("ReleaseContract", "hash_excluded_kinds"): (
                release_contract,
                ("sha256sums", "zip"),
            ),
            ("ReleaseContract", "zip_excluded_kinds"): (release_contract, ("zip",)),
        }
        self.assertEqual(sum(len(names) for names in TUPLE_FIELDS.values()), 15)
        self.assertEqual(
            set(expected),
            {
                (name, field)
                for name, fields_ in TUPLE_FIELDS.items()
                for field in fields_
            },
        )
        for (value_type, field), (instance, wanted) in expected.items():
            with self.subTest(value_type=value_type, field=field):
                value = getattr(instance, field)
                self.assertEqual(value, wanted)
                self.assertIsInstance(value, tuple)
                with self.assertRaises(FrozenInstanceError):
                    setattr(instance, field, ())

        records.append(question)
        issues.append(models.AuditIssue("late", "blocker", "Q2", "field", "evidence"))
        result_counts[0][0] = "changed"
        result_counts.append(["late", 2])
        audit_counts[0][0] = "changed"
        audit_counts.append(["late", 2])
        allowed_tags.append("late")
        required_fields.append("late")
        selected_source_ids.reverse()
        database_counts[0][0] = "changed"
        database_counts.append(["late", 2])
        required_tables.append("late")
        required_views.append("late")
        protected_kinds.append("late")
        manifest_fields.append("late")
        hash_exclusions.append("late")
        zip_exclusions.append("late")
        for (value_type, field), (instance, wanted) in expected.items():
            with self.subTest(value_type=value_type, field=field, check="source mutation"):
                self.assertEqual(getattr(instance, field), wanted)

    def test_nested_count_fields_normalize_both_sequence_levels(self) -> None:
        models = import_required(self, "joy_m2.models")
        question = make_audited_question(models)
        values = [["value", 1]]
        instances = (
            (
                "AuditResult.answer_status_counts",
                models.AuditResult(
                    records=[question],
                    issues=[],
                    answer_status_counts=values,
                    status="PASS",
                ),
                "answer_status_counts",
            ),
            (
                "AuditContract.expected_answer_status_counts",
                make_audit_contract(
                    models,
                    expected_question_count=1,
                    expected_answer_status_counts=values,
                ),
                "expected_answer_status_counts",
            ),
            (
                "DatabaseContract.expected_answer_status_counts",
                make_database_contract(
                    models,
                    expected_question_count=1,
                    expected_existing_question_count=0,
                    expected_new_question_count=1,
                    expected_answer_status_counts=values,
                ),
                "expected_answer_status_counts",
            ),
        )
        for name, instance, field in instances:
            with self.subTest(field=name):
                normalized = getattr(instance, field)
                self.assertEqual(normalized, (("value", 1),))
                self.assertIsInstance(normalized, tuple)
                self.assertIsInstance(normalized[0], tuple)

    def test_audit_result_rejects_inconsistent_status_and_statistics(self) -> None:
        models = import_required(self, "joy_m2.models")
        errors = import_required(self, "joy_m2.errors")
        question = make_audited_question(models)
        blocker = models.AuditIssue("exact_duplicate", "blocker", "Q1", "field", "Q0")
        with self.assertRaises(errors.PipelineError):
            models.AuditResult(
                records=[question],
                issues=[blocker],
                answer_status_counts=[["value", 1]],
                status="PASS",
            )
        with self.assertRaises(errors.PipelineError):
            models.AuditResult(
                records=[question],
                issues=[],
                answer_status_counts=[["value", 2]],
                status="PASS",
            )
        with self.assertRaises(errors.PipelineError):
            models.AuditResult(
                records=[question],
                issues=[],
                answer_status_counts=[["value", 1]],
                status="FAIL",
            )
        with self.assertRaises(errors.PipelineError):
            models.AuditResult(
                records=[question],
                issues=[],
                answer_status_counts=[["wrong_status", 1]],
                status="PASS",
            )
        invalid_count_entries = (
            (
                "duplicate answer status",
                [question, question],
                [["value", 1], ["value", 1]],
            ),
            ("negative count", [question], [["value", 2], ["value", -1]]),
            ("zero count", [question], [["value", 1], ["wrong_status", 0]]),
            ("bool count", [question], [["value", True]]),
            ("non-int count", [question], [["value", 1.0]]),
        )
        for reason, records, answer_status_counts in invalid_count_entries:
            with self.subTest(reason=reason):
                with self.assertRaises(errors.PipelineError):
                    models.AuditResult(
                        records=records,
                        issues=[],
                        answer_status_counts=answer_status_counts,
                        status="PASS",
                    )

    def test_model_path_fields_resolve_to_absolute_frozen_paths(self) -> None:
        models = import_required(self, "joy_m2.models")
        artifact = models.ArtifactRef(Path("artifact.bin"), "a" * 64, 1, "test")
        audit_contract = make_audit_contract(models)
        audit_request = models.AuditRequest(
            source_path=Path("source.sqlite3"),
            asset_root=Path("assets"),
            contract=audit_contract,
            selected_source_ids=[],
        )
        database_request = models.DatabaseBuildRequest(
            batch=models.AuditedBatch(records=[]),
            baseline_database=artifact,
            baseline_manifest=models.ArtifactRef(
                Path("manifest.json"), "b" * 64, 1, "manifest"
            ),
            output_path=Path("staging/candidate.sqlite3"),
            release_spec=make_release_spec(models),
            contract=make_database_contract(
                models,
                expected_question_count=0,
                expected_existing_question_count=0,
                expected_new_question_count=0,
                expected_answer_status_counts=[],
            ),
        )
        export_request = models.ExportRequest(
            database=make_database_artifact(models),
            output_dir=Path("staging/exports"),
            contract=make_export_contract(models),
        )
        release_contract = make_release_contract(models)
        formal_release = models.FormalRelease(
            release_dir=Path("releases/V1.19"),
            manifest=make_artifact(models, "manifest.json"),
            verification_report=models.VerificationReport(
                status="PASS",
                checks=[models.VerificationCheck("release", True, "matched")],
            ),
            final_hashes=[],
        )
        cases = (
            (artifact, "path", Path("artifact.bin").resolve()),
            (audit_request, "source_path", Path("source.sqlite3").resolve()),
            (audit_request, "asset_root", Path("assets").resolve()),
            (database_request, "output_path", Path("staging/candidate.sqlite3").resolve()),
            (export_request, "output_dir", Path("staging/exports").resolve()),
            (formal_release, "release_dir", Path("releases/V1.19").resolve()),
        )
        for instance, field, wanted in cases:
            with self.subTest(value_type=type(instance).__name__, field=field):
                value = getattr(instance, field)
                self.assertIsInstance(value, Path)
                self.assertTrue(value.is_absolute())
                self.assertEqual(value, wanted)
                with self.assertRaises(FrozenInstanceError):
                    setattr(instance, field, Path("changed"))
        self.assertIsInstance(export_request.contract.csv_filename, str)
        self.assertIsInstance(release_contract.manifest_filename, str)
        self.assertNotIsInstance(export_request.contract.csv_filename, Path)
        self.assertNotIsInstance(release_contract.manifest_filename, Path)

    def test_approved_nested_and_optional_artifact_types_are_explicit(self) -> None:
        models = import_required(self, "joy_m2.models")
        database_request_hints = typing.get_type_hints(models.DatabaseBuildRequest)
        candidate_request_hints = typing.get_type_hints(models.CandidateBuildRequest)
        derived_hints = typing.get_type_hints(models.DerivedArtifacts)
        self.assertIs(database_request_hints["baseline_database"], models.ArtifactRef)
        self.assertIs(database_request_hints["baseline_manifest"], models.ArtifactRef)
        self.assertIs(candidate_request_hints["audit_request"], models.AuditRequest)
        self.assertEqual(
            set(typing.get_args(derived_hints["taxonomy"])),
            {models.ArtifactRef, type(None)},
        )
        common = {
            "csv": make_artifact(models, "questions.csv"),
            "knowledge_markdown": make_artifact(models, "knowledge.md"),
            "import_report": make_artifact(models, "import.md"),
            "project_state": make_artifact(models, "PROJECT_STATE.md"),
        }
        without_taxonomy = models.DerivedArtifacts(**common, taxonomy=None)
        taxonomy = make_artifact(models, "taxonomy.json")
        with_taxonomy = models.DerivedArtifacts(**common, taxonomy=taxonomy)
        self.assertIsNone(without_taxonomy.taxonomy)
        self.assertIs(with_taxonomy.taxonomy, taxonomy)
        with self.assertRaises(FrozenInstanceError):
            with_taxonomy.taxonomy = None

    def test_candidate_release_normalizes_complete_artifact_set_and_is_frozen(self) -> None:
        models = import_required(self, "joy_m2.models")
        artifact = make_artifact(models, "artifact.json")
        package = make_artifact(models, "candidate.zip")
        report = models.VerificationReport(
            status="PASS",
            checks=[models.VerificationCheck("hashes", True, "matched")],
        )
        candidate = models.CandidateRelease(
            run_id="run-1",
            release_version="V1.19",
            candidate_manifest_sha256="b" * 64,
            verification_report=report,
            artifacts=[artifact],
            candidate_zip=package,
        )
        self.assertEqual(candidate.artifacts, (artifact,))
        self.assertIsInstance(candidate.artifacts, tuple)
        with self.assertRaises(FrozenInstanceError):
            candidate.artifacts = ()

    def test_formal_release_normalizes_final_hashes_and_is_frozen(self) -> None:
        models = import_required(self, "joy_m2.models")
        manifest = make_artifact(models, "manifest.json")
        final_hash = make_artifact(models, "formal.zip")
        report = models.VerificationReport(
            status="PASS",
            checks=[models.VerificationCheck("hashes", True, "matched")],
        )
        release = models.FormalRelease(
            release_dir=Path("/tmp/releases/V1.19"),
            manifest=manifest,
            verification_report=report,
            final_hashes=[final_hash],
        )
        self.assertEqual(release.final_hashes, (final_hash,))
        self.assertIsInstance(release.final_hashes, tuple)
        with self.assertRaises(FrozenInstanceError):
            release.final_hashes = ()


if __name__ == "__main__":
    unittest.main()
