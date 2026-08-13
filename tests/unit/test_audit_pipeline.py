from __future__ import annotations

from collections import Counter
import hashlib
from io import BytesIO, StringIO
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from joy_m2 import models
from joy_m2.audit import pipeline
from joy_m2.audit import profiles
from joy_m2 import errors


V118_CANDIDATE = ROOT / "releases/V1.18/complete_questions_452_task6_audited.json"
V117_DATABASE = (
    ROOT
    / "legacy/outputs/25757421d1d8/Task5_V1.17_正式入库/Joy_M2_Complete_Question_DB_V1_17.sqlite3"
)
V118_DATABASE = ROOT / "releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3"
ASSET_ROOT = ROOT / "legacy"
V117_CANDIDATE = (
    ROOT
    / "legacy/task4_work/task4_package/03_候选数据/complete_questions_45_task4.json"
)
V116_DATABASE = (
    ROOT / "legacy/task5_work/v116/m2_question_bank/data/m2_question_bank.sqlite3"
)
V117_TAXONOMY = (
    ROOT
    / "legacy/task4_work/task4_package/03_候选数据/differentiation_application_taxonomy_v1.1_task4.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def task6_request() -> models.AuditRequest:
    records = json.loads(V118_CANDIDATE.read_text(encoding="utf-8"))
    with sqlite3.connect(V118_DATABASE) as database:
        allowed_tags = tuple(
            row[0]
            for row in database.execute(
                "SELECT value FROM complete_question_taxonomy_v2 "
                "WHERE taxonomy_kind='tag' ORDER BY sort_order"
            )
        )
    return models.AuditRequest(
        candidate_path=V118_CANDIDATE,
        baseline_database=models.ArtifactRef(
            path=V117_DATABASE,
            sha256=sha256(V117_DATABASE),
            size_bytes=V117_DATABASE.stat().st_size,
            kind="sqlite",
        ),
        asset_root=ASSET_ROOT,
        contract=models.AuditContract(
            profile="V1.18",
            release_version="V1.18",
            schema_version="complete-question-v1.0",
            expected_question_count=452,
            expected_source_count=23,
            expected_answer_status_counts=(
                ("ai_solved_verified", 71),
                ("missing_from_source", 34),
                ("source_provided", 347),
            ),
            allowed_tags=allowed_tags,
            required_fields=tuple(records[0]),
        ),
        selected_source_ids=tuple(
            sorted({record["source_id"] for record in records})
        ),
    )


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def task6_request_for(candidate_path: Path, asset_root: Path) -> models.AuditRequest:
    request = task6_request()
    return models.AuditRequest(
        candidate_path=candidate_path,
        baseline_database=request.baseline_database,
        asset_root=asset_root,
        contract=request.contract,
        selected_source_ids=request.selected_source_ids,
    )


def task5_request(candidate_path: Path, asset_root: Path) -> models.AuditRequest:
    records = json.loads(V117_CANDIDATE.read_text(encoding="utf-8"))
    taxonomy = json.loads(V117_TAXONOMY.read_text(encoding="utf-8"))
    return models.AuditRequest(
        candidate_path=candidate_path,
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


def make_v117_asset_root(root: Path, records: list[dict]) -> Path:
    asset_root = root / "assets"
    asset_root.mkdir()
    for record in records:
        for image in record["image_paths"]:
            path = asset_root / image["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"declared-image")
    return asset_root


class Task6AuditContractTests(unittest.TestCase):
    def test_frozen_v118_json_produces_the_approved_audit_result(self) -> None:
        raw_records = json.loads(V118_CANDIDATE.read_text(encoding="utf-8"))

        result = pipeline.audit_batch(task6_request())

        self.assertEqual(len(result.records), 452)
        self.assertEqual(
            tuple(record.question.question_id for record in result.records),
            tuple(record["question_id"] for record in raw_records),
        )
        self.assertEqual(len({record.question.question_id for record in result.records}), 452)
        self.assertEqual(
            Counter(record.question.source_id for record in result.records),
            Counter(record["source_id"] for record in raw_records),
        )
        self.assertEqual(len(result.report.source_counts), 23)
        self.assertEqual(result.report.image_reference_count, 33)
        self.assertEqual(
            result.answer_status_counts,
            (
                ("ai_solved_verified", 71),
                ("missing_from_source", 34),
                ("source_provided", 347),
            ),
        )
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.report.status, "passed")
        self.assertEqual(result.issues, ())
        self.assertEqual(result.require_passed().records, result.records)

    def test_audit_owns_verified_input_evidence_and_release_carriers(self) -> None:
        raw_records = json.loads(V118_CANDIDATE.read_text(encoding="utf-8"))
        request = task6_request()

        result = pipeline.audit_batch(request)

        self.assertEqual(
            result.input_evidence.candidate_json,
            models.ArtifactRef(
                path=V118_CANDIDATE,
                sha256=sha256(V118_CANDIDATE),
                size_bytes=V118_CANDIDATE.stat().st_size,
                kind="json",
            ),
        )
        self.assertEqual(result.input_evidence.baseline_database, request.baseline_database)
        self.assertTrue(
            all(record.task4_compatibility is None for record in result.records)
        )
        self.assertEqual(
            tuple(
                (
                    record.release_compatibility.formal_release_version,
                    record.release_compatibility.selectable,
                    record.release_compatibility.source_order,
                )
                for record in result.records
            ),
            tuple(
                (
                    record["formal_release_version"],
                    record["selectable"],
                    record["source_order"],
                )
                for record in raw_records
            ),
        )

    def test_candidate_evidence_and_records_use_one_immutable_byte_read(self) -> None:
        records_a = json.loads(V118_CANDIDATE.read_text(encoding="utf-8"))
        records_b = json.loads(V118_CANDIDATE.read_text(encoding="utf-8"))
        records_a[0]["audit_notes"] = "decoded from candidate bytes A"
        records_b[0]["audit_notes"] = "decoded from candidate bytes B"
        candidate_a = json.dumps(records_a, ensure_ascii=False).encode("utf-8")
        candidate_b = json.dumps(records_b, ensure_ascii=False).encode("utf-8")

        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "candidate.json"
            candidate.write_bytes(candidate_a)
            request = task6_request_for(candidate, ASSET_ROOT)
            path_type = type(candidate)
            original_open = path_type.open
            candidate_reads = []

            def controlled_open(path, mode="r", *args, **kwargs):
                if path.resolve() == candidate.resolve():
                    content = candidate_a if not candidate_reads else candidate_b
                    candidate_reads.append(content)
                    if "b" in mode:
                        return BytesIO(content)
                    return StringIO(content.decode(kwargs.get("encoding") or "utf-8"))
                return original_open(path, mode, *args, **kwargs)

            with patch.object(path_type, "open", controlled_open):
                result = pipeline.audit_batch(request)

        self.assertEqual(
            result.input_evidence.candidate_json.sha256,
            hashlib.sha256(candidate_a).hexdigest(),
        )
        self.assertEqual(result.input_evidence.candidate_json.size_bytes, len(candidate_a))
        self.assertEqual(
            result.records[0].question.audit_notes,
            "decoded from candidate bytes A",
        )
        self.assertEqual(len(candidate_reads), 1)


class AuditFailureContractTests(unittest.TestCase):
    def test_duplicate_preserves_an_empty_rolling_predecessor_id(self) -> None:
        records = json.loads(V118_CANDIDATE.read_text(encoding="utf-8"))
        records[0]["question_id"] = ""
        records[1]["question_text_original"] = records[0]["question_text_original"]

        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "empty-predecessor-id.json"
            write_json(candidate, records)
            result = pipeline.audit_batch(task6_request_for(candidate, ASSET_ROOT))

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.report.status, "failed")
        self.assertEqual(
            tuple(issue for issue in result.issues if issue.code == "exact_duplicate"),
            (
                models.AuditIssue(
                    "exact_duplicate",
                    "blocker",
                    records[1]["question_id"],
                    "question_text_original",
                    "",
                ),
            ),
        )

    def test_business_blockers_aggregate_with_record_level_statistics(self) -> None:
        records = json.loads(V118_CANDIDATE.read_text(encoding="utf-8"))
        first_id = records[0]["question_id"]
        second_id = records[1]["question_id"]
        third_id = records[2]["question_id"]
        records[0]["question_text_original"] = "   "
        records[0]["difficulty_level"] = 6
        records[0]["tags"] = [*records[0]["tags"], "not-approved"]
        records[1]["solution_verified"] = ""
        records[1]["image_paths"] = ["missing/figure.png"]
        records[2]["question_text_original"] = records[1]["question_text_original"]
        records[3]["question_text_original"] = records[1]["question_text_original"]

        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "candidate.json"
            write_json(candidate, records)
            result = pipeline.audit_batch(task6_request_for(candidate, ASSET_ROOT))

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.report.status, "failed")
        self.assertEqual(result.report.candidate_count, 452)
        self.assertEqual(result.report.blocked, 4)
        self.assertEqual(result.report.audit_passed, 448)
        self.assertEqual(result.report.audit_pending, 0)
        self.assertEqual(result.report.exact_duplicate_count, 2)
        self.assertEqual(
            [(issue.question_id, issue.code) for issue in result.issues],
            sorted(
                [
                    (first_id, "invalid_difficulty"),
                    (first_id, "invalid_tag"),
                    (first_id, "missing_question_text"),
                    (second_id, "missing_image"),
                    (second_id, "missing_solution"),
                    (third_id, "exact_duplicate"),
                    (records[3]["question_id"], "exact_duplicate"),
                ]
            ),
        )
        duplicate_issues = [
            issue for issue in result.issues if issue.code == "exact_duplicate"
        ]
        self.assertEqual(
            [(issue.question_id, issue.evidence) for issue in duplicate_issues],
            [(third_id, second_id), (records[3]["question_id"], third_id)],
        )
        self.assertEqual(
            result.input_evidence.baseline_database,
            task6_request().baseline_database,
        )
        with self.assertRaises(errors.AuditBlockedError):
            result.require_passed()

    def test_missing_and_malformed_inputs_fail_before_a_result(self) -> None:
        request = task6_request()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            missing_request = models.AuditRequest(
                candidate_path=root / "missing.json",
                baseline_database=request.baseline_database,
                asset_root=ASSET_ROOT,
                contract=request.contract,
                selected_source_ids=request.selected_source_ids,
            )
            with self.assertRaises(errors.InputMissingError):
                pipeline.audit_batch(missing_request)

            malformed = root / "malformed.json"
            malformed.write_text("{", encoding="utf-8")
            with self.assertRaises(errors.InputFormatError):
                pipeline.audit_batch(task6_request_for(malformed, ASSET_ROOT))

            not_a_list = root / "object.json"
            write_json(not_a_list, {})
            with self.assertRaises(errors.InputFormatError):
                pipeline.audit_batch(task6_request_for(not_a_list, ASSET_ROOT))

    def test_baseline_identity_is_verified_before_candidate_decoding(self) -> None:
        request = task6_request()
        wrong_baseline = models.ArtifactRef(
            path=request.baseline_database.path,
            sha256="0" * 64,
            size_bytes=request.baseline_database.size_bytes,
            kind="sqlite",
        )
        with tempfile.TemporaryDirectory() as temp:
            invalid_candidate = Path(temp) / "malformed.json"
            invalid_candidate.write_text("{", encoding="utf-8")
            mismatched = models.AuditRequest(
                candidate_path=invalid_candidate,
                baseline_database=wrong_baseline,
                asset_root=ASSET_ROOT,
                contract=request.contract,
                selected_source_ids=request.selected_source_ids,
            )

            with self.assertRaises(errors.BaselineMismatchError):
                pipeline.audit_batch(mismatched)

    def test_empty_candidate_is_rejected_by_profile_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "empty.json"
            write_json(candidate, [])
            with self.assertRaises(errors.InputFormatError):
                pipeline.audit_batch(task6_request_for(candidate, ASSET_ROOT))

    def test_duplicate_question_ids_are_rejected_as_input_format(self) -> None:
        records = json.loads(V118_CANDIDATE.read_text(encoding="utf-8"))
        records[1]["question_id"] = records[0]["question_id"]
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "duplicate-id.json"
            write_json(candidate, records)
            with self.assertRaises(errors.InputFormatError):
                pipeline.audit_batch(task6_request_for(candidate, ASSET_ROOT))

    def test_v118_rejects_a_matching_but_wrong_profile_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            baseline = Path(temp) / "not-v117.sqlite3"
            with sqlite3.connect(baseline) as database:
                database.execute("PRAGMA user_version=999")
                database.execute(
                    "CREATE TABLE complete_questions "
                    "(question_text_original TEXT, question_id TEXT)"
                )
                database.execute(
                    "CREATE TABLE complete_questions_v2 "
                    "(question_text_original TEXT, question_id TEXT)"
                )
                database.execute(
                    "CREATE TABLE release_metadata_v2 (key TEXT, value TEXT)"
                )
                database.execute(
                    "INSERT INTO release_metadata_v2 VALUES "
                    "('release_version', 'not-V1.17')"
                )
                database.executemany(
                    "INSERT INTO complete_questions VALUES (?, ?)",
                    ((f"legacy baseline {index}", f"legacy-{index}") for index in range(497)),
                )
                database.executemany(
                    "INSERT INTO complete_questions_v2 VALUES (?, ?)",
                    ((f"v2 baseline {index}", f"v2-{index}") for index in range(45)),
                )
            request = task6_request()
            wrong_profile = models.AuditRequest(
                candidate_path=request.candidate_path,
                baseline_database=models.ArtifactRef(
                    baseline,
                    sha256(baseline),
                    baseline.stat().st_size,
                    "sqlite",
                ),
                asset_root=request.asset_root,
                contract=request.contract,
                selected_source_ids=request.selected_source_ids,
            )

            with self.assertRaises(errors.BaselineMismatchError):
                pipeline.audit_batch(wrong_profile)

    def test_absolute_image_path_cannot_escape_the_asset_root(self) -> None:
        records = json.loads(V118_CANDIDATE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            asset_root = root / "assets"
            asset_root.mkdir()
            outside = root / "outside.png"
            outside.write_bytes(b"outside")
            records[0]["image_paths"] = [str(outside)]
            candidate = root / "absolute-image.json"
            write_json(candidate, records)

            result = pipeline.audit_batch(task6_request_for(candidate, asset_root))

        self.assertEqual(result.status, "failed")
        self.assertIn(
            models.AuditIssue(
                "missing_image",
                "blocker",
                records[0]["question_id"],
                "image_paths",
                str(outside),
            ),
            result.issues,
        )


class Task5AuditContractTests(unittest.TestCase):
    def test_task4_audit_json_produces_45_v117_envelopes(self) -> None:
        raw_records = json.loads(V117_CANDIDATE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp:
            asset_root = make_v117_asset_root(Path(temp), raw_records)

            result = pipeline.audit_batch(task5_request(V117_CANDIDATE, asset_root))

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.issues, ())
        self.assertEqual(len(result.records), 45)
        self.assertEqual(
            tuple(record.question.question_id for record in result.records),
            tuple(record["question_id"] for record in raw_records),
        )
        self.assertEqual(result.answer_status_counts, (("source_provided", 45),))
        self.assertEqual(result.report.source_counts, (("M2QD-DIFFERENTIATION-APPLICATIONS", 45),))
        self.assertEqual(result.report.image_reference_count, 1)
        self.assertEqual(result.report.blocked, 0)
        self.assertEqual(result.input_evidence.baseline_database, task5_request(V117_CANDIDATE, Path(temp)).baseline_database)
        self.assertTrue(
            all(record.task4_compatibility is not None for record in result.records)
        )
        self.assertTrue(
            all(record.release_compatibility is None for record in result.records)
        )
        self.assertEqual(
            sum(
                not record.task4_compatibility.task4_resolution_present
                and not record.task4_compatibility.task4_processed_at_present
                for record in result.records
            ),
            24,
        )
        self.assertEqual(
            sum(
                record.task4_compatibility.task4_resolution_present
                and record.task4_compatibility.task4_processed_at_present
                for record in result.records
            ),
            21,
        )

    def test_v117_profile_eligibility_and_shape_errors_fail_fast(self) -> None:
        record = json.loads(V117_CANDIDATE.read_text(encoding="utf-8"))[0]

        published = dict(record)
        published["record_status"] = "published"
        with self.assertRaises(errors.InputFormatError):
            profiles.parse_v117_record(published)

        unresolved = dict(record)
        unresolved["unresolved_issues"] = ["pending"]
        with self.assertRaises(errors.InputFormatError):
            profiles.parse_v117_record(unresolved)

        wrong_order = {key: record[key] for key in reversed(record)}
        with self.assertRaises(errors.InputFormatError):
            profiles.parse_v117_record(wrong_order)

        wrong_marks = dict(record)
        wrong_marks["marks_total"] = True
        with self.assertRaises(errors.InputFormatError):
            profiles.parse_v117_record(wrong_marks)

    def test_v117_rejects_a_matching_but_wrong_profile_baseline(self) -> None:
        raw_records = json.loads(V117_CANDIDATE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            asset_root = make_v117_asset_root(root, raw_records)
            baseline = root / "not-v116.sqlite3"
            with sqlite3.connect(baseline) as database:
                database.execute("PRAGMA user_version=999")
                database.execute(
                    "CREATE TABLE complete_questions "
                    "(question_id TEXT, source_id TEXT, question_text_original TEXT)"
                )
                database.executemany(
                    "INSERT INTO complete_questions VALUES (?, ?, ?)",
                    (
                        (f"legacy-{index}", "unselected-source", f"legacy baseline {index}")
                        for index in range(497)
                    ),
                )
            request = task5_request(V117_CANDIDATE, asset_root)
            wrong_profile = models.AuditRequest(
                candidate_path=request.candidate_path,
                baseline_database=models.ArtifactRef(
                    baseline,
                    sha256(baseline),
                    baseline.stat().st_size,
                    "sqlite",
                ),
                asset_root=request.asset_root,
                contract=request.contract,
                selected_source_ids=request.selected_source_ids,
            )

            with self.assertRaises(errors.BaselineMismatchError):
                pipeline.audit_batch(wrong_profile)


class ProfileSerializationContractTests(unittest.TestCase):
    def test_v118_rejects_missing_extra_and_misordered_fields(self) -> None:
        record = json.loads(V118_CANDIDATE.read_text(encoding="utf-8"))[0]
        missing = dict(record)
        missing.pop("year")
        extra = dict(record)
        extra["unexpected"] = None
        misordered = {field: record[field] for field in reversed(record)}

        for invalid in (missing, extra, misordered):
            with self.subTest(fields=tuple(invalid)):
                with self.assertRaises(errors.InputFormatError):
                    profiles.parse_v118_record(invalid)

    def test_v118_rejects_bool_for_int_and_invalid_nested_types(self) -> None:
        record = json.loads(V118_CANDIDATE.read_text(encoding="utf-8"))[0]
        bool_source_order = dict(record)
        bool_source_order["source_order"] = True
        invalid_image = dict(record)
        invalid_image["image_paths"] = [{"path": "figure.png"}]
        invalid_correction = dict(record)
        invalid_correction["corrections"] = [
            {
                "field": 1,
                "error_origin": "source",
                "original": "old",
                "corrected": "new",
                "reason": "reason",
                "evidence": "evidence",
            }
        ]

        for invalid in (bool_source_order, invalid_image, invalid_correction):
            with self.subTest(invalid=invalid):
                with self.assertRaises(errors.InputFormatError):
                    profiles.parse_v118_record(invalid)

    def test_v118_rejects_a_non_object_record_container(self) -> None:
        with self.assertRaises(errors.InputFormatError):
            profiles.parse_v118_record([])

    def test_v117_rejects_mixed_presence_image_and_wrong_profile_shapes(self) -> None:
        raw_records = json.loads(V117_CANDIDATE.read_text(encoding="utf-8"))
        base_record = next(record for record in raw_records if len(record) == 50)
        mixed_presence = dict(base_record)
        mixed_presence["task4_resolution"] = None

        image_record = next(record for record in raw_records if record["image_paths"])
        invalid_image = dict(image_record)
        invalid_image["image_paths"] = ["not-a-V1.17-image-object"]

        wrong_profile = json.loads(V118_CANDIDATE.read_text(encoding="utf-8"))[0]

        for invalid in (mixed_presence, invalid_image, wrong_profile):
            with self.subTest(invalid=invalid):
                with self.assertRaises(errors.InputFormatError):
                    profiles.parse_v117_record(invalid)

    def test_v117_parser_and_serializer_preserve_all_50_and_52_field_records(self) -> None:
        raw_records = json.loads(V117_CANDIDATE.read_text(encoding="utf-8"))

        serialized = [
            profiles.serialize_v117_record(profiles.parse_v117_record(record))
            for record in raw_records
        ]

        self.assertEqual(serialized, raw_records)
        self.assertEqual(Counter(len(record) for record in serialized), {50: 24, 52: 21})

    def test_v117_explicit_null_compatibility_values_retain_presence(self) -> None:
        raw_record = next(
            record
            for record in json.loads(V117_CANDIDATE.read_text(encoding="utf-8"))
            if "task4_resolution" in record
        )
        raw_record["task4_resolution"] = None
        raw_record["task4_processed_at"] = None

        audited = profiles.parse_v117_record(raw_record)

        self.assertTrue(audited.task4_compatibility.task4_resolution_present)
        self.assertIsNone(audited.task4_compatibility.task4_resolution)
        self.assertTrue(audited.task4_compatibility.task4_processed_at_present)
        self.assertIsNone(audited.task4_compatibility.task4_processed_at)
        self.assertEqual(profiles.serialize_v117_record(audited), raw_record)

    def test_v118_parser_and_serializer_preserve_all_54_field_records(self) -> None:
        raw_records = json.loads(V118_CANDIDATE.read_text(encoding="utf-8"))

        serialized = [
            profiles.serialize_v118_record(profiles.parse_v118_record(record))
            for record in raw_records
        ]

        self.assertEqual(serialized, raw_records)
        self.assertTrue(all(len(record) == 54 for record in serialized))


if __name__ == "__main__":
    unittest.main()
