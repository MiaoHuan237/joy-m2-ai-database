from __future__ import annotations

from collections.abc import Mapping
from dataclasses import MISSING, FrozenInstanceError, fields, is_dataclass
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
    "Task4Compatibility",
    "ReleaseCompatibility",
    "AuditedRecord",
    "AuditedBatch",
    "AuditInputEvidence",
    "AuditReport",
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
    "source_heading",
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
    "Task4Compatibility": (
        "task4_resolution_present",
        "task4_resolution",
        "task4_processed_at_present",
        "task4_processed_at",
    ),
    "ReleaseCompatibility": (
        "formal_release_version",
        "selectable",
        "source_order",
    ),
    "AuditedRecord": (
        "question",
        "task4_compatibility",
        "release_compatibility",
    ),
    "AuditedBatch": ("records",),
    "AuditInputEvidence": ("candidate_json", "baseline_database"),
    "AuditReport": (
        "release_version",
        "status",
        "candidate_count",
        "source_count",
        "audit_passed",
        "audit_pending",
        "blocked",
        "exact_duplicate_count",
        "answer_status_counts",
        "image_reference_count",
        "source_counts",
    ),
    "AuditResult": (
        "records",
        "issues",
        "answer_status_counts",
        "status",
        "report",
        "input_evidence",
    ),
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
    "AuditRequest": (
        "candidate_path",
        "baseline_database",
        "asset_root",
        "contract",
        "selected_source_ids",
    ),
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
    "AuditReport": ("answer_status_counts", "source_counts"),
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


def make_audited_record(models, question=None, profile="V1.18"):
    question = question or make_audited_question(models)
    if profile == "V1.17":
        return models.AuditedRecord(
            question=question,
            task4_compatibility=models.Task4Compatibility(False, None, False, None),
            release_compatibility=None,
        )
    return models.AuditedRecord(
        question=question,
        task4_compatibility=None,
        release_compatibility=models.ReleaseCompatibility("V1.18", True, 46),
    )


def make_artifact(models, name: str):
    return models.ArtifactRef(
        path=Path("/tmp") / name,
        sha256="a" * 64,
        size_bytes=1,
        kind="test",
    )


def make_audit_input_evidence(models):
    return models.AuditInputEvidence(
        candidate_json=models.ArtifactRef(
            path=Path("/tmp/candidate.json"),
            sha256="c" * 64,
            size_bytes=2,
            kind="json",
        ),
        baseline_database=models.ArtifactRef(
            path=Path("/tmp/baseline.sqlite3"),
            sha256="b" * 64,
            size_bytes=3,
            kind="sqlite",
        ),
    )


def make_audit_report(
    models,
    *,
    records=(),
    issues=(),
    answer_status_counts=None,
    status=None,
    release_version="V1.18",
    **overrides,
):
    records = tuple(records)
    issues = tuple(issues)
    if status is None:
        status = "failed" if issues else "passed"
    if answer_status_counts is None:
        answer_status_counts = tuple(
            sorted(
                {
                    answer_status: sum(
                        record.question.answer_status == answer_status
                        for record in records
                    )
                    for answer_status in {
                        record.question.answer_status for record in records
                    }
                }.items()
            )
        )
    blocker_ids = {
        issue.question_id for issue in issues if issue.severity == "blocker"
    }
    exact_duplicate_ids = {
        issue.question_id
        for issue in issues
        if issue.severity == "blocker" and issue.code == "exact_duplicate"
    }
    source_counts = tuple(
        sorted(
            {
                source_id: sum(
                    record.question.source_id == source_id for record in records
                )
                for source_id in {record.question.source_id for record in records}
            }.items()
        )
    )
    values = {
        "release_version": release_version,
        "status": status,
        "candidate_count": len(records),
        "source_count": len(source_counts),
        "audit_passed": len(records) - len(blocker_ids),
        "audit_pending": 0,
        "blocked": len(blocker_ids),
        "exact_duplicate_count": len(exact_duplicate_ids),
        "answer_status_counts": answer_status_counts,
        "image_reference_count": sum(
            len(record.question.image_paths) for record in records
        ),
        "source_counts": source_counts,
    }
    values.update(overrides)
    return models.AuditReport(**values)


def make_audit_result(
    models,
    *,
    records=(),
    issues=(),
    answer_status_counts=None,
    status=None,
    report=None,
    input_evidence=None,
):
    records = tuple(records)
    issues = tuple(issues)
    if status is None:
        status = "failed" if issues else "passed"
    if answer_status_counts is None:
        answer_status_counts = tuple(
            sorted(
                {
                    answer_status: sum(
                        record.question.answer_status == answer_status
                        for record in records
                    )
                    for answer_status in {
                        record.question.answer_status for record in records
                    }
                }.items()
            )
        )
    if report is None:
        report = make_audit_report(
            models,
            records=records,
            issues=issues,
            answer_status_counts=answer_status_counts,
            status=status,
        )
    return models.AuditResult(
        records=records,
        issues=issues,
        answer_status_counts=answer_status_counts,
        status=status,
        report=report,
        input_evidence=input_evidence or make_audit_input_evidence(models),
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


class CompatibilityModelContractTests(unittest.TestCase):
    def require_type(self, models, name: str):
        value_type = getattr(models, name, None)
        self.assertIsNotNone(value_type, f"missing public model: {name}")
        return value_type

    def make_v117_record(self, models, question=None):
        task4_type = self.require_type(models, "Task4Compatibility")
        record_type = self.require_type(models, "AuditedRecord")
        return record_type(
            question=question or make_audited_question(models),
            task4_compatibility=task4_type(False, None, False, None),
            release_compatibility=None,
        )

    def make_v118_record(self, models, question=None):
        release_type = self.require_type(models, "ReleaseCompatibility")
        record_type = self.require_type(models, "AuditedRecord")
        return record_type(
            question=question or make_audited_question(models),
            task4_compatibility=None,
            release_compatibility=release_type("V1.18", True, 46),
        )

    def test_task4_compatibility_has_exact_ordered_typed_fields(self) -> None:
        models = import_required(self, "joy_m2.models")
        value_type = self.require_type(models, "Task4Compatibility")
        self.assertEqual(
            field_names(value_type),
            (
                "task4_resolution_present",
                "task4_resolution",
                "task4_processed_at_present",
                "task4_processed_at",
            ),
        )
        self.assertEqual(
            typing.get_type_hints(value_type),
            {
                "task4_resolution_present": bool,
                "task4_resolution": str | None,
                "task4_processed_at_present": bool,
                "task4_processed_at": str | None,
            },
        )

    def test_task4_compatibility_preserves_missing_and_explicit_null(self) -> None:
        models = import_required(self, "joy_m2.models")
        value_type = self.require_type(models, "Task4Compatibility")
        missing = value_type(False, None, False, None)
        explicit_null = value_type(True, None, True, None)
        self.assertEqual(
            (
                missing.task4_resolution_present,
                missing.task4_resolution,
                missing.task4_processed_at_present,
                missing.task4_processed_at,
            ),
            (False, None, False, None),
        )
        self.assertEqual(
            (
                explicit_null.task4_resolution_present,
                explicit_null.task4_resolution,
                explicit_null.task4_processed_at_present,
                explicit_null.task4_processed_at,
            ),
            (True, None, True, None),
        )
        self.assertNotEqual(missing, explicit_null)

    def test_task4_presence_flags_are_independent(self) -> None:
        models = import_required(self, "joy_m2.models")
        value_type = self.require_type(models, "Task4Compatibility")
        resolution_only = value_type(True, None, False, None)
        processed_at_only = value_type(False, None, True, None)
        self.assertEqual(
            (
                resolution_only.task4_resolution_present,
                resolution_only.task4_processed_at_present,
            ),
            (True, False),
        )
        self.assertEqual(
            (
                processed_at_only.task4_resolution_present,
                processed_at_only.task4_processed_at_present,
            ),
            (False, True),
        )

    def test_release_compatibility_has_exact_ordered_typed_fields(self) -> None:
        models = import_required(self, "joy_m2.models")
        value_type = self.require_type(models, "ReleaseCompatibility")
        self.assertEqual(
            field_names(value_type),
            ("formal_release_version", "selectable", "source_order"),
        )
        self.assertEqual(
            typing.get_type_hints(value_type),
            {
                "formal_release_version": str,
                "selectable": bool,
                "source_order": int,
            },
        )

    def test_closed_compatibility_values_reject_wrong_runtime_types(self) -> None:
        models = import_required(self, "joy_m2.models")
        errors = import_required(self, "joy_m2.errors")
        task4_type = self.require_type(models, "Task4Compatibility")
        release_type = self.require_type(models, "ReleaseCompatibility")
        with self.assertRaises(errors.PipelineError):
            task4_type(False, "derived", False, None)
        with self.assertRaises(errors.PipelineError):
            task4_type(1, None, False, None)
        with self.assertRaises(errors.PipelineError):
            release_type("V1.18", True, False)

    def test_audited_record_has_exact_ordered_typed_fields(self) -> None:
        models = import_required(self, "joy_m2.models")
        value_type = self.require_type(models, "AuditedRecord")
        task4_type = self.require_type(models, "Task4Compatibility")
        release_type = self.require_type(models, "ReleaseCompatibility")
        self.assertEqual(
            field_names(value_type),
            ("question", "task4_compatibility", "release_compatibility"),
        )
        self.assertEqual(
            typing.get_type_hints(value_type),
            {
                "question": models.AuditedQuestion,
                "task4_compatibility": task4_type | None,
                "release_compatibility": release_type | None,
            },
        )

    def test_audited_record_accepts_only_the_two_legal_carrier_combinations(self) -> None:
        models = import_required(self, "joy_m2.models")
        errors = import_required(self, "joy_m2.errors")
        self.require_type(models, "AuditedRecord")
        question = make_audited_question(models)
        v117 = self.make_v117_record(models, question)
        v118 = self.make_v118_record(models, question)
        self.assertIs(v117.question, question)
        self.assertIsNotNone(v117.task4_compatibility)
        self.assertIsNone(v117.release_compatibility)
        self.assertIs(v118.question, question)
        self.assertIsNone(v118.task4_compatibility)
        self.assertIsNotNone(v118.release_compatibility)
        with self.assertRaises(errors.PipelineError):
            type(v117)(question, v117.task4_compatibility, v118.release_compatibility)
        with self.assertRaises(errors.PipelineError):
            type(v117)(question, None, None)

    def test_audit_record_collections_use_the_envelope_type(self) -> None:
        models = import_required(self, "joy_m2.models")
        record_type = self.require_type(models, "AuditedRecord")
        self.assertEqual(
            typing.get_type_hints(models.AuditResult)["records"],
            tuple[record_type, ...],
        )
        self.assertEqual(
            typing.get_type_hints(models.AuditedBatch)["records"],
            tuple[record_type, ...],
        )
        record = self.make_v118_record(models)
        result = make_audit_result(models, records=(record,))
        batch = models.AuditedBatch(records=(record,))
        self.assertEqual(result.records, (record,))
        self.assertEqual(batch.records, (record,))

    def test_require_passed_preserves_all_three_result_rules_with_envelopes(self) -> None:
        models = import_required(self, "joy_m2.models")
        errors = import_required(self, "joy_m2.errors")
        record = self.make_v117_record(
            models,
            make_audited_question(models, question_id="Q1"),
        )
        passed = make_audit_result(models, records=(record,))
        batch = passed.require_passed()
        self.assertEqual(batch.records, passed.records)
        self.assertIs(batch.records[0], record)
        blocked = make_audit_result(
            models,
            records=(record,),
            issues=(models.AuditIssue("exact_duplicate", "blocker", "Q1", "field", "Q0"),),
        )
        with self.assertRaises(errors.AuditBlockedError):
            blocked.require_passed()
        empty = make_audit_result(models)
        self.assertEqual(empty.require_passed().records, ())

    def test_core_question_and_publication_evidence_keep_stage_boundaries(self) -> None:
        models = import_required(self, "joy_m2.models")
        forbidden = {
            "task4_resolution",
            "task4_processed_at",
            "formal_release_version",
            "selectable",
            "source_order",
        }
        self.assertTrue(forbidden.isdisjoint(field_names(models.AuditedQuestion)))
        self.assertEqual(
            typing.get_type_hints(models.PublicationEvidence)["approved_at"],
            str | None,
        )
        evidence = models.PublicationEvidence("audit_passed", "", None)
        self.assertIsNone(evidence.approved_at)

    def test_new_compatibility_models_remain_frozen(self) -> None:
        models = import_required(self, "joy_m2.models")
        values = (
            self.require_type(models, "Task4Compatibility")(False, None, False, None),
            self.require_type(models, "ReleaseCompatibility")("V1.18", True, 46),
            self.make_v117_record(models),
        )
        for value in values:
            with self.subTest(value_type=type(value).__name__):
                self.assertTrue(value.__dataclass_params__.frozen)
                with self.assertRaises(FrozenInstanceError):
                    setattr(value, fields(value)[0].name, "changed")


class Phase2PublicModelContractTests(unittest.TestCase):
    def test_audit_input_evidence_is_the_exact_two_artifact_carrier(self) -> None:
        models = import_required(self, "joy_m2.models")
        evidence_type = getattr(models, "AuditInputEvidence", None)
        self.assertIsNotNone(evidence_type, "missing public model: AuditInputEvidence")
        self.assertEqual(
            typing.get_type_hints(evidence_type),
            {
                "candidate_json": models.ArtifactRef,
                "baseline_database": models.ArtifactRef,
            },
        )
        self.assertEqual(
            field_names(evidence_type),
            ("candidate_json", "baseline_database"),
        )
        self.assertNotIn("baseline_release_archive", field_names(evidence_type))
        evidence = make_audit_input_evidence(models)
        self.assertEqual(evidence.candidate_json.sha256, "c" * 64)
        self.assertEqual(evidence.baseline_database.sha256, "b" * 64)
        self.assertTrue(evidence.__dataclass_params__.frozen)
        with self.assertRaises(FrozenInstanceError):
            evidence.candidate_json = evidence.baseline_database

    def test_audit_request_replaces_source_path_with_explicit_candidate_and_baseline(self) -> None:
        models = import_required(self, "joy_m2.models")
        self.assertEqual(
            typing.get_type_hints(models.AuditRequest),
            {
                "candidate_path": Path,
                "baseline_database": models.ArtifactRef,
                "asset_root": Path,
                "contract": models.AuditContract,
                "selected_source_ids": tuple[str, ...],
            },
        )
        self.assertNotIn("source_path", field_names(models.AuditRequest))
        baseline = make_artifact(models, "baseline.sqlite3")
        request = models.AuditRequest(
            candidate_path=Path("candidate.json"),
            baseline_database=baseline,
            asset_root=Path("assets"),
            contract=make_audit_contract(models),
            selected_source_ids=["source-b", "source-a"],
        )
        self.assertEqual(request.candidate_path, Path("candidate.json").resolve())
        self.assertIs(request.baseline_database, baseline)
        self.assertEqual(request.selected_source_ids, ("source-b", "source-a"))

    def test_audit_report_has_exact_typed_required_fields(self) -> None:
        models = import_required(self, "joy_m2.models")
        report_type = getattr(models, "AuditReport", None)
        self.assertIsNotNone(report_type, "missing public model: AuditReport")
        self.assertEqual(
            typing.get_type_hints(report_type),
            {
                "release_version": str,
                "status": str,
                "candidate_count": int,
                "source_count": int,
                "audit_passed": int,
                "audit_pending": int,
                "blocked": int,
                "exact_duplicate_count": int,
                "answer_status_counts": tuple[tuple[str, int], ...],
                "image_reference_count": int,
                "source_counts": tuple[tuple[str, int], ...],
            },
        )
        self.assertTrue(all(field.default is MISSING for field in fields(report_type)))
        empty = make_audit_report(models)
        self.assertEqual(empty.status, "passed")
        self.assertEqual(empty.candidate_count, 0)
        self.assertEqual(empty.answer_status_counts, ())
        self.assertEqual(empty.source_counts, ())

    def test_audit_result_owns_report_and_input_evidence_with_exact_types(self) -> None:
        models = import_required(self, "joy_m2.models")
        self.assertEqual(
            typing.get_type_hints(models.AuditResult),
            {
                "records": tuple[models.AuditedRecord, ...],
                "issues": tuple[models.AuditIssue, ...],
                "answer_status_counts": tuple[tuple[str, int], ...],
                "status": str,
                "report": models.AuditReport,
                "input_evidence": models.AuditInputEvidence,
            },
        )
        evidence_owners = []
        for name in PUBLIC_VALUE_TYPES:
            for field_name, annotation in typing.get_type_hints(
                getattr(models, name)
            ).items():
                if annotation is models.AuditInputEvidence:
                    evidence_owners.append((name, field_name))
        self.assertEqual(evidence_owners, [("AuditResult", "input_evidence")])

    def test_audit_statistics_use_record_level_deduplicated_blockers(self) -> None:
        models = import_required(self, "joy_m2.models")
        records = (
            make_audited_record(
                models,
                make_audited_question(
                    models,
                    question_id="Q1",
                    source_id="source-b",
                    answer_status="source_provided",
                    image_paths=[
                        make_question_image(models, "assets/q1-a.png"),
                        make_question_image(models, "assets/q1-b.png"),
                    ],
                ),
            ),
            make_audited_record(
                models,
                make_audited_question(
                    models,
                    question_id="Q2",
                    source_id="source-a",
                    answer_status="missing_from_source",
                    image_paths=[],
                ),
            ),
            make_audited_record(
                models,
                make_audited_question(
                    models,
                    question_id="Q3",
                    source_id="source-b",
                    answer_status="source_provided",
                ),
            ),
        )
        issues = (
            models.AuditIssue("exact_duplicate", "blocker", "Q1", "text", "Q0"),
            models.AuditIssue("invalid_difficulty", "blocker", "Q1", "year", "6"),
            models.AuditIssue("exact_duplicate", "blocker", "Q2", "text", "Q0"),
            models.AuditIssue("invalid_tag", "blocker", "Q2", "tags", "bad"),
        )
        report = models.AuditReport(
            release_version="V1.18",
            status="failed",
            candidate_count=3,
            source_count=2,
            audit_passed=1,
            audit_pending=0,
            blocked=2,
            exact_duplicate_count=2,
            answer_status_counts=(
                ("missing_from_source", 1),
                ("source_provided", 2),
            ),
            image_reference_count=3,
            source_counts=(("source-a", 1), ("source-b", 2)),
        )
        result = models.AuditResult(
            records=records,
            issues=issues,
            answer_status_counts=report.answer_status_counts,
            status="failed",
            report=report,
            input_evidence=make_audit_input_evidence(models),
        )
        self.assertEqual(result.report.blocked, 2)
        self.assertEqual(result.report.audit_passed, 1)
        self.assertEqual(result.report.exact_duplicate_count, 2)
        self.assertEqual(result.report.source_counts[0][0], "source-a")

    def test_audit_result_canonicalizes_issues_by_the_exact_approved_key(self) -> None:
        models = import_required(self, "joy_m2.models")
        records = (
            make_audited_record(
                models,
                make_audited_question(models, question_id="Q1"),
            ),
            make_audited_record(
                models,
                make_audited_question(models, question_id="Q2"),
            ),
        )
        q2 = models.AuditIssue("code-a", "blocker", "Q2", "field-a", "a")
        code_b = models.AuditIssue("code-b", "blocker", "Q1", "field-a", "a")
        field_b = models.AuditIssue("code-a", "blocker", "Q1", "field-b", "a")
        evidence_b = models.AuditIssue("code-a", "blocker", "Q1", "field-a", "b")
        evidence_a = models.AuditIssue("code-a", "blocker", "Q1", "field-a", "a")

        result = make_audit_result(
            models,
            records=records,
            issues=[q2, code_b, field_b, evidence_b, evidence_a],
        )

        self.assertEqual(
            result.issues,
            (evidence_a, evidence_b, field_b, code_b, q2),
        )

    def test_audit_result_issue_sort_is_stable_for_equal_keys(self) -> None:
        models = import_required(self, "joy_m2.models")
        record = make_audited_record(
            models,
            make_audited_question(models, question_id="Q1"),
        )
        first = models.AuditIssue("same", "blocker", "Q1", "same", "same")
        second = models.AuditIssue("same", "blocker", "Q1", "same", "same")
        self.assertIsNot(first, second)

        result = make_audit_result(
            models,
            records=[record],
            issues=[first, second],
        )

        self.assertEqual(len(result.issues), 2)
        self.assertIs(result.issues[0], first)
        self.assertIs(result.issues[1], second)

    def test_audit_result_rejects_every_report_or_status_closure_mismatch(self) -> None:
        models = import_required(self, "joy_m2.models")
        errors = import_required(self, "joy_m2.errors")
        record = make_audited_record(
            models,
            make_audited_question(
                models,
                question_id="Q1",
                source_id="source-a",
                image_paths=[],
            ),
        )
        invalid_report_overrides = {
            "candidate_count": 2,
            "source_count": 2,
            "audit_passed": 0,
            "audit_pending": 1,
            "blocked": 1,
            "exact_duplicate_count": 1,
            "answer_status_counts": (("wrong", 1),),
            "image_reference_count": 1,
            "source_counts": (("source-b", 1),),
        }
        for field_name, invalid_value in invalid_report_overrides.items():
            with self.subTest(field=field_name):
                with self.assertRaises(errors.PipelineError):
                    make_audit_result(
                        models,
                        records=[record],
                        report=make_audit_report(
                            models,
                            records=[record],
                            **{field_name: invalid_value},
                        ),
                    )

        blocker = models.AuditIssue(
            "exact_duplicate", "blocker", "Q1", "question_text_original", "Q0"
        )
        with self.assertRaises(errors.PipelineError):
            make_audit_result(models, records=[record], issues=[blocker], status="passed")
        with self.assertRaises(errors.PipelineError):
            make_audit_result(models, records=[record], status="failed")
        with self.assertRaises(errors.PipelineError):
            make_audit_result(models, records=[record], status="PASS")
        with self.assertRaises(errors.PipelineError):
            models.AuditResult(
                records=[object()],
                issues=[],
                answer_status_counts=[],
                status="passed",
                report=make_audit_report(models),
                input_evidence=make_audit_input_evidence(models),
            )
        with self.assertRaises(errors.PipelineError):
            models.AuditResult(
                records=[record],
                issues=[object()],
                answer_status_counts=[["value", 1]],
                status="failed",
                report=make_audit_report(
                    models,
                    records=[record],
                    issues=[blocker],
                ),
                input_evidence=make_audit_input_evidence(models),
            )

    def test_audit_report_rejects_unsorted_or_non_closed_statistics(self) -> None:
        models = import_required(self, "joy_m2.models")
        errors = import_required(self, "joy_m2.errors")
        invalid_reports = (
            {"status": "PASS"},
            {"candidate_count": 1},
            {"audit_pending": 1},
            {"status": "failed"},
            {
                "status": "passed",
                "candidate_count": 1,
                "audit_passed": 0,
                "blocked": 1,
                "answer_status_counts": (("value", 1),),
                "source_count": 1,
                "source_counts": (("source-a", 1),),
            },
            {"answer_status_counts": (("z", 1), ("a", 1)), "candidate_count": 2, "audit_passed": 2},
            {"source_counts": (("z", 1), ("a", 1)), "candidate_count": 2, "audit_passed": 2, "source_count": 2},
        )
        for overrides in invalid_reports:
            with self.subTest(overrides=overrides):
                with self.assertRaises(errors.PipelineError):
                    make_audit_report(models, **overrides)

    def test_public_empty_pass_result_remains_valid_with_authoritative_evidence(self) -> None:
        models = import_required(self, "joy_m2.models")
        result = make_audit_result(models)
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.report.status, "passed")
        self.assertEqual(result.records, ())
        self.assertEqual(result.issues, ())
        self.assertEqual(result.require_passed().records, ())


class PipelineModelContractTests(unittest.TestCase):
    def test_all_30_approved_shared_value_types_are_public_dataclasses(self) -> None:
        models = import_required(self, "joy_m2.models")
        self.assertEqual(len(PUBLIC_VALUE_TYPES), 30)
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

    def test_all_30_shared_dataclasses_are_declared_frozen(self) -> None:
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
        self.assertEqual(len(EXACT_FIELD_CONTRACTS), 30)
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
            elif name not in {
                "joy_approval",
                "approved_at",
                "formal_release_version",
                "selectable",
                "source_order",
            }:
                mapped_fields.append(name)
        self.assertEqual(len(mapped_fields), 49)
        self.assertEqual(tuple(mapped_fields), AUDITED_QUESTION_FIELDS)
        self.assertNotIn("record_status", AUDITED_QUESTION_FIELDS)
        self.assertNotIn("joy_approval", AUDITED_QUESTION_FIELDS)
        self.assertNotIn("approved_at", AUDITED_QUESTION_FIELDS)
        self.assertNotIn("formal_release_version", AUDITED_QUESTION_FIELDS)
        self.assertNotIn("selectable", AUDITED_QUESTION_FIELDS)
        self.assertNotIn("source_order", AUDITED_QUESTION_FIELDS)

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
        record = make_audited_record(
            models,
            make_audited_question(models, question_id="Q1"),
        )
        result = make_audit_result(
            models,
            records=[record],
            issues=[
                models.AuditIssue(
                    "exact_duplicate",
                    "blocker",
                    "Q1",
                    "question_text_original",
                    "Q0",
                ),
            ],
        )
        self.assertIsInstance(result.records, tuple)
        self.assertIsInstance(result.issues, tuple)
        with self.assertRaises(errors.AuditBlockedError):
            result.require_passed()

    def test_non_blocking_audit_result_preserves_content_in_an_immutable_batch(self) -> None:
        models = import_required(self, "joy_m2.models")
        question = make_audited_question(models)
        record = make_audited_record(models, question)
        result = make_audit_result(models, records=[record])
        batch = result.require_passed()
        self.assertIsInstance(batch, models.AuditedBatch)
        self.assertEqual(batch.records, (record,))
        self.assertIs(batch.records[0], record)
        self.assertIsInstance(batch.records, tuple)
        with self.assertRaises(FrozenInstanceError):
            batch.records = ()

    def test_audited_batch_directly_normalizes_a_record_list_without_aliasing(self) -> None:
        models = import_required(self, "joy_m2.models")
        first = make_audited_record(models)
        second = make_audited_record(
            models,
            make_audited_question(models, question_id="Q2"),
        )
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

    def test_all_17_approved_tuple_fields_normalize_lists_without_aliasing(self) -> None:
        models = import_required(self, "joy_m2.models")
        question = make_audited_question(models)
        record = make_audited_record(models, question)
        records = [record]
        issues = []
        result_counts = [["value", 1]]
        report_source_counts = [["value", 1]]
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
        report = make_audit_report(
            models,
            records=records,
            issues=issues,
            answer_status_counts=result_counts,
            source_counts=report_source_counts,
        )
        result = make_audit_result(
            models,
            records=records,
            issues=issues,
            answer_status_counts=result_counts,
            report=report,
        )
        audit_contract = make_audit_contract(
            models,
            expected_question_count=1,
            expected_answer_status_counts=audit_counts,
            allowed_tags=allowed_tags,
            required_fields=required_fields,
        )
        audit_request = models.AuditRequest(
            candidate_path=Path("candidate.json"),
            baseline_database=make_artifact(models, "baseline.sqlite3"),
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
            ("AuditedBatch", "records"): (batch, (record,)),
            ("AuditResult", "records"): (result, (record,)),
            ("AuditResult", "issues"): (result, ()),
            ("AuditResult", "answer_status_counts"): (result, (("value", 1),)),
            ("AuditReport", "answer_status_counts"): (report, (("value", 1),)),
            ("AuditReport", "source_counts"): (report, (("value", 1),)),
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
        self.assertEqual(sum(len(names) for names in TUPLE_FIELDS.values()), 17)
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

        records.append(record)
        issues.append(models.AuditIssue("late", "blocker", "Q2", "field", "evidence"))
        result_counts[0][0] = "changed"
        result_counts.append(["late", 2])
        report_source_counts[0][0] = "changed"
        report_source_counts.append(["late", 2])
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
        record = make_audited_record(models, question)
        values = [["value", 1]]
        instances = (
            (
                "AuditResult.answer_status_counts",
                make_audit_result(
                    models,
                    records=[record],
                    answer_status_counts=values,
                ),
                "answer_status_counts",
            ),
            (
                "AuditReport.answer_status_counts",
                make_audit_report(
                    models,
                    records=[record],
                    answer_status_counts=values,
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
        record = make_audited_record(models, question)
        blocker = models.AuditIssue("exact_duplicate", "blocker", "Q1", "field", "Q0")
        with self.assertRaises(errors.PipelineError):
            make_audit_result(
                models,
                records=[record],
                issues=[blocker],
                answer_status_counts=[["value", 1]],
                status="passed",
            )
        with self.assertRaises(errors.PipelineError):
            make_audit_result(
                models,
                records=[record],
                issues=[],
                answer_status_counts=[["value", 2]],
            )
        with self.assertRaises(errors.PipelineError):
            make_audit_result(
                models,
                records=[record],
                issues=[],
                answer_status_counts=[["value", 1]],
                status="failed",
            )
        with self.assertRaises(errors.PipelineError):
            make_audit_result(
                models,
                records=[record],
                issues=[],
                answer_status_counts=[["wrong_status", 1]],
            )
        invalid_count_entries = (
            (
                "duplicate answer status",
                [record, record],
                [["value", 1], ["value", 1]],
            ),
            ("negative count", [record], [["value", 2], ["value", -1]]),
            ("zero count", [record], [["value", 1], ["wrong_status", 0]]),
            ("bool count", [record], [["value", True]]),
            ("non-int count", [record], [["value", 1.0]]),
        )
        for reason, records, answer_status_counts in invalid_count_entries:
            with self.subTest(reason=reason):
                with self.assertRaises(errors.PipelineError):
                    make_audit_result(
                        models,
                        records=records,
                        issues=[],
                        answer_status_counts=answer_status_counts,
                    )

    def test_model_path_fields_resolve_to_absolute_frozen_paths(self) -> None:
        models = import_required(self, "joy_m2.models")
        artifact = models.ArtifactRef(Path("artifact.bin"), "a" * 64, 1, "test")
        audit_contract = make_audit_contract(models)
        audit_request = models.AuditRequest(
            candidate_path=Path("candidate.json"),
            baseline_database=models.ArtifactRef(
                Path("baseline.sqlite3"), "b" * 64, 1, "sqlite"
            ),
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
            (audit_request, "candidate_path", Path("candidate.json").resolve()),
            (
                audit_request.baseline_database,
                "path",
                Path("baseline.sqlite3").resolve(),
            ),
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
