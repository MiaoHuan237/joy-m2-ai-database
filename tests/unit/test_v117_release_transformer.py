from __future__ import annotations

from collections import Counter
import builtins
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import typing
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from joy_m2 import errors, models
from joy_m2.audit import pipeline as audit_pipeline
from joy_m2 import release
from legacy.task5_work import build_task5_release as legacy_task5


V117_CANDIDATE = (
    ROOT
    / "legacy/task4_work/task4_package/03_候选数据/complete_questions_45_task4.json"
)
V117_TAXONOMY = (
    ROOT
    / "legacy/task4_work/task4_package/03_候选数据/differentiation_application_taxonomy_v1.1_task4.json"
)
V116_DATABASE = ROOT / "legacy/task5_work/v116/m2_question_bank/data/m2_question_bank.sqlite3"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_v117_asset_root(root: Path, records: list[dict]) -> Path:
    asset_root = root / "assets"
    asset_root.mkdir()
    for record in records:
        for image in record["image_paths"]:
            path = asset_root / image["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"declared-image")
    return asset_root


def make_v117_request(asset_root: Path) -> models.AuditRequest:
    records = json.loads(V117_CANDIDATE.read_text(encoding="utf-8"))
    taxonomy = json.loads(V117_TAXONOMY.read_text(encoding="utf-8"))
    return models.AuditRequest(
        candidate_path=V117_CANDIDATE,
        baseline_database=models.ArtifactRef(
            path=V116_DATABASE,
            sha256=sha256(V116_DATABASE),
            size_bytes=V116_DATABASE.stat().st_size,
            kind="sqlite",
        ),
        asset_root=asset_root,
        contract=models.AuditContract(
            profile="V1.17",
            release_version="V1.17",
            schema_version="complete-question-v1.0-draft",
            expected_question_count=45,
            expected_source_count=1,
            expected_answer_status_counts=(("source_provided", 45),),
            allowed_tags=tuple(taxonomy["tags"]),
            required_fields=tuple(records[0]),
        ),
        selected_source_ids=("M2QD-DIFFERENTIATION-APPLICATIONS",),
    )


def make_decision() -> models.V117ReleaseDecision:
    return models.V117ReleaseDecision(
        formal_release_version="V1.17",
        selectable=True,
        record_status="published",
        joy_approval="approved_by_joy",
        approved_at="2026-08-08T20:00:00+08:00",
        schema_version="complete-question-v1.0",
    )


def make_result(
    records: tuple[models.AuditedRecord, ...],
    *,
    issues: tuple[models.AuditIssue, ...] = (),
    input_evidence: models.AuditInputEvidence,
    release_version: str = "V1.17",
) -> models.AuditResult:
    answer_counts = tuple(
        sorted(Counter(record.question.answer_status for record in records).items())
    )
    source_counts = tuple(
        sorted(Counter(record.question.source_id for record in records).items())
    )
    blocker_ids = {
        issue.question_id for issue in issues if issue.severity == "blocker"
    }
    duplicate_ids = {
        issue.question_id
        for issue in issues
        if issue.severity == "blocker" and issue.code == "exact_duplicate"
    }
    status = "failed" if issues else "passed"
    report = models.AuditReport(
        release_version=release_version,
        status=status,
        candidate_count=len(records),
        source_count=len(source_counts),
        audit_passed=len(records) - len(blocker_ids),
        audit_pending=0,
        blocked=len(blocker_ids),
        exact_duplicate_count=len(duplicate_ids),
        answer_status_counts=answer_counts,
        image_reference_count=sum(
            len(record.question.image_paths) for record in records
        ),
        source_counts=source_counts,
    )
    return models.AuditResult(
        records=records,
        issues=issues,
        answer_status_counts=answer_counts,
        status=status,
        report=report,
        input_evidence=input_evidence,
    )


class V117ReleaseTransformerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw_records = json.loads(V117_CANDIDATE.read_text(encoding="utf-8"))
        cls.temp = tempfile.TemporaryDirectory()
        cls.asset_root = make_v117_asset_root(Path(cls.temp.name), cls.raw_records)
        cls.audit_result = audit_pipeline.audit_batch(make_v117_request(cls.asset_root))
        cls.decision = make_decision()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def require_transformer(self):
        transform = getattr(release, "transform_v117_release", None)
        self.assertIsNotNone(
            transform,
            "missing approved transformer API: transform_v117_release",
        )
        return transform

    def test_public_api_has_the_exact_typed_audit_result_boundary(self) -> None:
        transform = self.require_transformer()
        self.assertEqual(
            typing.get_type_hints(transform),
            {
                "result": models.AuditResult,
                "decision": models.V117ReleaseDecision,
                "return": models.V117ReleaseBatch,
            },
        )
        self.assertEqual(release.__all__, ("transform_v117_release",))
        with self.assertRaises(errors.PipelineError):
            transform(self.audit_result.records, self.decision)
        with self.assertRaises(errors.PipelineError):
            transform(list(self.audit_result.records), self.decision)

    def test_passed_result_maps_all_records_by_the_seven_frozen_operations(self) -> None:
        transform = self.require_transformer()
        batch = transform(self.audit_result, self.decision)
        expected = legacy_task5.approve_records(self.raw_records)
        self.assertIsInstance(batch, models.V117ReleaseBatch)
        self.assertEqual(len(batch.records), 45)
        self.assertEqual(
            tuple(record.audited_record.question.question_id for record in batch.records),
            tuple(item["question_id"] for item in expected),
        )
        self.assertEqual(len({item["question_id"] for item in expected}), 45)
        for index, (release_record, audited_record, legacy_record) in enumerate(
            zip(batch.records, self.audit_result.records, expected),
            start=1,
        ):
            with self.subTest(question_id=legacy_record["question_id"]):
                self.assertIs(release_record.audited_record, audited_record)
                self.assertEqual(
                    release_record.publication_evidence,
                    models.PublicationEvidence(
                        record_status=legacy_record["record_status"],
                        joy_approval=legacy_record["joy_approval"],
                        approved_at=legacy_record["approved_at"],
                    ),
                )
                self.assertEqual(
                    release_record.release_compatibility,
                    models.ReleaseCompatibility(
                        formal_release_version=legacy_record["formal_release_version"],
                        selectable=legacy_record["selectable"],
                        source_order=legacy_record["source_order"],
                    ),
                )
                self.assertEqual(release_record.schema_version, legacy_record["schema_version"])
                self.assertEqual(release_record.release_compatibility.source_order, index)
                compatibility = audited_record.task4_compatibility
                self.assertEqual(
                    compatibility.task4_resolution_present,
                    "task4_resolution" in self.raw_records[index - 1],
                )
                self.assertEqual(
                    compatibility.task4_processed_at_present,
                    "task4_processed_at" in self.raw_records[index - 1],
                )

    def test_transform_is_deterministic_and_preserves_audit_ownership(self) -> None:
        transform = self.require_transformer()
        first = transform(self.audit_result, self.decision)
        second = transform(self.audit_result, self.decision)
        evidence = self.audit_result.input_evidence
        self.assertEqual(first, second)
        self.assertEqual(
            tuple(record.audited_record for record in first.records),
            self.audit_result.records,
        )
        self.assertIs(first.records[0].audited_record, self.audit_result.records[0])
        self.assertIs(self.audit_result.input_evidence, evidence)
        self.assertEqual(self.audit_result.status, "passed")
        self.assertEqual(self.audit_result.report.candidate_count, 45)

    def test_transform_calls_require_passed_and_blocks_failed_results(self) -> None:
        transform = self.require_transformer()
        question_id = self.audit_result.records[0].question.question_id
        issue = models.AuditIssue(
            "exact_duplicate",
            "blocker",
            question_id,
            "question_text_original",
            question_id,
        )
        failed = make_result(
            self.audit_result.records,
            issues=(issue,),
            input_evidence=self.audit_result.input_evidence,
        )
        calls = []
        original = models.AuditResult.require_passed

        def tracked_require_passed(result):
            calls.append(result)
            return original(result)

        with patch.object(models.AuditResult, "require_passed", tracked_require_passed):
            with self.assertRaises(errors.AuditBlockedError):
                transform(failed, self.decision)
        self.assertEqual(calls, [failed])

    def test_empty_v118_mixed_and_incompatible_results_are_rejected(self) -> None:
        transform = self.require_transformer()
        empty = make_result(
            (),
            input_evidence=self.audit_result.input_evidence,
        )
        first = self.audit_result.records[0]
        v118 = models.AuditedRecord(
            question=first.question,
            task4_compatibility=None,
            release_compatibility=models.ReleaseCompatibility("V1.18", True, 46),
        )
        v118_result = make_result(
            (v118,),
            input_evidence=self.audit_result.input_evidence,
        )
        mixed_result = make_result(
            (first, v118),
            input_evidence=self.audit_result.input_evidence,
        )
        wrong_release = make_result(
            (first,),
            input_evidence=self.audit_result.input_evidence,
            release_version="V1.18",
        )
        for reason, result in (
            ("empty", empty),
            ("V1.18", v118_result),
            ("mixed", mixed_result),
            ("wrong release", wrong_release),
        ):
            with self.subTest(reason=reason):
                with self.assertRaises(errors.PipelineError):
                    transform(result, self.decision)

    def test_transform_performs_no_input_file_hash_or_legacy_runtime_access(self) -> None:
        transform = self.require_transformer()
        with (
            patch.object(Path, "open", side_effect=AssertionError("unexpected open")),
            patch.object(Path, "read_bytes", side_effect=AssertionError("unexpected read")),
            patch.object(Path, "stat", side_effect=AssertionError("unexpected stat")),
            patch.object(builtins, "open", side_effect=AssertionError("unexpected open")),
        ):
            batch = transform(self.audit_result, self.decision)
        self.assertEqual(len(batch.records), 45)


if __name__ == "__main__":
    unittest.main(verbosity=2)
