from __future__ import annotations

import csv
import hashlib
import importlib
import inspect
import io
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from joy_m2 import db as db_api
from joy_m2 import errors, models
from joy_m2.audit import pipeline as audit_pipeline
from joy_m2.release import transform_v117_release
from tests.integration.test_db_pipeline import (
    V116_DATABASE,
    V117_DATABASE,
    V117_MANIFEST,
    artifact,
    v117_contract as database_v117_contract,
    v117_release_spec,
    v118_contract as database_v118_contract,
    v118_release_spec,
)
from tests.unit.test_audit_pipeline import (
    V117_CANDIDATE,
    make_v117_asset_root,
    task5_request,
    task6_request,
)


V117_ORACLE = ROOT / "legacy/outputs/25757421d1d8/Task5_V1.17_正式入库"
V118_ORACLE = ROOT / "releases/V1.18"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_callable(test: unittest.TestCase, module_name: str, name: str):
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        module = None
    value = getattr(module, name, None) if module is not None else None
    test.assertTrue(callable(value), f"missing approved Export behavior: {module_name}.{name}")
    return value


class FormatContractTests(unittest.TestCase):
    def test_canonical_json_is_compact_sorted_unicode_utf8(self) -> None:
        serialize = require_callable(
            self, "joy_m2.export.formats", "canonical_json_bytes"
        )

        self.assertEqual(
            serialize({"中": [2, 1]}),
            b'{"\xe4\xb8\xad":[2,1]}',
        )
        self.assertEqual(
            serialize({"z": 1, "a": "中"}),
            b'{"a":"\xe4\xb8\xad","z":1}',
        )

    def test_evidence_json_is_sorted_indented_unicode_with_one_lf(self) -> None:
        serialize = require_callable(
            self, "joy_m2.export.formats", "evidence_json_bytes"
        )

        expected = '{\n  "a": "中",\n  "b": 1\n}\n'.encode()
        self.assertEqual(serialize({"b": 1, "a": "中"}), expected)
        self.assertTrue(expected.endswith(b"\n"))
        self.assertFalse(expected.endswith(b"\n\n"))

    def test_csv_uses_utf8_bom_crlf_and_declared_field_order(self) -> None:
        serialize = require_callable(self, "joy_m2.export.formats", "csv_bytes")

        value = serialize(
            ("question_id", "text", "empty"),
            ({"text": "中文", "empty": "", "question_id": "Q1"},),
        )

        self.assertTrue(value.startswith(b"\xef\xbb\xbfquestion_id,text,empty\r\n"))
        self.assertEqual(value.count(b"\r\n"), 2)
        self.assertNotIn(b"\n", value.replace(b"\r\n", b""))
        with io.TextIOWrapper(
            io.BytesIO(value), encoding="utf-8-sig", newline=""
        ) as handle:
            self.assertEqual(
                list(csv.DictReader(handle)),
                [{"question_id": "Q1", "text": "中文", "empty": ""}],
            )

    def test_text_normalizes_line_endings_and_has_exactly_one_final_lf(self) -> None:
        serialize = require_callable(self, "joy_m2.export.formats", "text_bytes")

        self.assertEqual(serialize("a\r\nb\rc\n\n"), b"a\nb\nc\n")
        self.assertEqual(serialize("a"), b"a\n")

    def test_all_format_primitives_are_byte_deterministic(self) -> None:
        canonical = require_callable(
            self, "joy_m2.export.formats", "canonical_json_bytes"
        )
        evidence = require_callable(
            self, "joy_m2.export.formats", "evidence_json_bytes"
        )
        csv_serialize = require_callable(self, "joy_m2.export.formats", "csv_bytes")
        text = require_callable(self, "joy_m2.export.formats", "text_bytes")
        calls = (
            lambda: canonical({"b": [2], "a": "中"}),
            lambda: evidence({"b": [2], "a": "中"}),
            lambda: csv_serialize(("b", "a"), ({"a": "中", "b": 2},)),
            lambda: text("a\r\nb"),
        )
        for call in calls:
            with self.subTest(call=call):
                self.assertEqual(call(), call())


class ExportPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)

        cls.v118_result = audit_pipeline.audit_batch(task6_request())
        cls.v118_batch = cls.v118_result.require_passed()
        v118_path = cls.root / "V1.18.sqlite3"
        cls.v118_database = db_api.build_database(
            models.DatabaseBuildRequest(
                batch=cls.v118_batch,
                baseline_database=artifact(V117_DATABASE, "sqlite"),
                baseline_manifest=artifact(V117_MANIFEST, "json"),
                output_path=v118_path,
                release_spec=v118_release_spec(),
                contract=database_v118_contract(),
            )
        )

        raw_records = json.loads(V117_CANDIDATE.read_text(encoding="utf-8"))
        asset_root = make_v117_asset_root(cls.root, raw_records)
        cls.v117_result = audit_pipeline.audit_batch(
            task5_request(V117_CANDIDATE, asset_root)
        )
        cls.v117_batch = transform_v117_release(
            cls.v117_result,
            models.V117ReleaseDecision(
                formal_release_version="V1.17",
                selectable=True,
                record_status="published",
                joy_approval="approved_by_joy",
                approved_at="2026-08-08T20:00:00+08:00",
                schema_version="complete-question-v1.0",
            ),
        )
        v117_path = cls.root / "V1.17.sqlite3"
        cls.v117_database = db_api.build_database(
            models.DatabaseBuildRequest(
                batch=cls.v117_batch,
                baseline_database=artifact(V116_DATABASE, "sqlite"),
                baseline_manifest=artifact(V117_MANIFEST, "json"),
                output_path=v117_path,
                release_spec=v117_release_spec(),
                contract=database_v117_contract(),
            )
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def v118_contract(self) -> models.ExportContract:
        return models.ExportContract(
            profile="V1.18",
            audit_records_filename="complete_questions_452_task6_audited.json",
            audit_report_filename="task6_audit_report.json",
            csv_filename="Joy_M2_Complete_Questions_V1_18.csv",
            knowledge_markdown_filename="Joy_M2_完整题497题_知识文档_V1.18.md",
            import_report_filename="Joy_M2_V1.18_正式入库报告.md",
            project_state_filename="PROJECT_STATE.md",
            taxonomy_filename=None,
            expected_question_count=497,
            expected_missing_answer_count=34,
        )

    def v117_contract(self) -> models.ExportContract:
        return models.ExportContract(
            profile="V1.17",
            audit_records_filename="complete_questions_45_approved_v1_17.json",
            audit_report_filename="task4_audit_report.json",
            csv_filename="Joy_M2_Complete_Questions_V1_17.csv",
            knowledge_markdown_filename="Joy_M2_微分应用45题_知识文档_V1.17.md",
            import_report_filename="Joy_M2_V1.17_正式入库报告.md",
            project_state_filename="PROJECT_STATE.md",
            taxonomy_filename="differentiation_application_taxonomy_v1_1.json",
            expected_question_count=45,
            expected_missing_answer_count=0,
        )

    def request(self, profile: str, output_dir: Path) -> models.ExportRequest:
        if profile == "V1.18":
            return models.ExportRequest(
                database=self.v118_database,
                audit_result=self.v118_result,
                record_batch=self.v118_batch,
                output_dir=output_dir,
                contract=self.v118_contract(),
            )
        return models.ExportRequest(
            database=self.v117_database,
            audit_result=self.v117_result,
            record_batch=self.v117_batch,
            output_dir=output_dir,
            contract=self.v117_contract(),
        )

    def test_v118_export_is_byte_equivalent_to_frozen_artifacts(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "exports"
            artifacts = export_database(self.request("V1.18", output))
            contract = self.v118_contract()
            for name in (
                contract.audit_records_filename,
                contract.audit_report_filename,
                contract.csv_filename,
                contract.knowledge_markdown_filename,
                contract.import_report_filename,
                contract.project_state_filename,
            ):
                with self.subTest(name=name):
                    self.assertEqual(
                        (output / name).read_bytes(),
                        (V118_ORACLE / name).read_bytes(),
                    )
            self.assertIsNone(artifacts.taxonomy)

    def test_v117_export_preserves_all_protected_task5_artifacts(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "exports"
            export_database(self.request("V1.17", output))
            contract = self.v117_contract()
            for name in (
                contract.audit_records_filename,
                contract.csv_filename,
                contract.knowledge_markdown_filename,
                contract.import_report_filename,
                contract.project_state_filename,
                contract.taxonomy_filename,
            ):
                with self.subTest(name=name):
                    self.assertEqual(
                        (output / name).read_bytes(),
                        (V117_ORACLE / name).read_bytes(),
                    )

    def test_export_returns_exact_artifact_refs_for_generated_bytes(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "exports"
            artifacts = export_database(self.request("V1.17", output))
            expected = {
                "csv": ("Joy_M2_Complete_Questions_V1_17.csv", "csv"),
                "knowledge_markdown": ("Joy_M2_微分应用45题_知识文档_V1.17.md", "markdown"),
                "import_report": ("Joy_M2_V1.17_正式入库报告.md", "markdown"),
                "project_state": ("PROJECT_STATE.md", "markdown"),
                "taxonomy": ("differentiation_application_taxonomy_v1_1.json", "json"),
                "audit_records": ("complete_questions_45_approved_v1_17.json", "json"),
                "audit_report": ("task4_audit_report.json", "json"),
            }
            for field_name, (filename, kind) in expected.items():
                with self.subTest(field=field_name):
                    reference = getattr(artifacts, field_name)
                    path = output / filename
                    self.assertEqual(reference.path, path.resolve())
                    self.assertEqual(reference.kind, kind)
                    self.assertEqual(reference.size_bytes, len(path.read_bytes()))
                    self.assertEqual(reference.sha256, sha256(path))

    def test_audit_evidence_uses_supplied_carriers_without_recount_or_input_reads(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        missing = self.root / "deliberately-absent"
        input_evidence = models.AuditInputEvidence(
            candidate_json=models.ArtifactRef(missing / "candidate.json", "a" * 64, 1, "json"),
            baseline_database=models.ArtifactRef(missing / "baseline.sqlite3", "b" * 64, 2, "sqlite"),
        )
        result = replace(self.v118_result, input_evidence=input_evidence)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "exports"
            request = models.ExportRequest(
                database=self.v118_database,
                audit_result=result,
                record_batch=self.v118_batch,
                output_dir=output,
                contract=self.v118_contract(),
            )
            export_database(request)

            report = json.loads(
                (output / request.contract.audit_report_filename).read_text(encoding="utf-8")
            )
            self.assertNotIn("status", report)
            self.assertEqual(report["candidate_count"], result.report.candidate_count)
            self.assertEqual(report["source_counts"], dict(result.report.source_counts))
            self.assertFalse(missing.exists())

    def test_pipeline_revalidates_envelope_before_creating_output(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "not-created"
            request = self.request("V1.18", output)
            object.__setattr__(
                request,
                "record_batch",
                models.AuditedBatch(tuple(reversed(self.v118_batch.records))),
            )
            with self.assertRaises(errors.PipelineError):
                export_database(request)
            self.assertFalse(output.exists())

    def test_wrong_profile_and_escaping_filename_are_rejected_before_output(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrong_profile = self.request("V1.18", root / "wrong-profile")
            object.__setattr__(
                wrong_profile,
                "record_batch",
                self.v117_batch,
            )
            with self.assertRaises(errors.PipelineError):
                export_database(wrong_profile)
            self.assertFalse(wrong_profile.output_dir.exists())

            escaping = self.request("V1.18", root / "escaping")
            object.__setattr__(
                escaping.contract,
                "csv_filename",
                "../outside.csv",
            )
            with self.assertRaises(errors.PipelineError):
                export_database(escaping)
            self.assertFalse(escaping.output_dir.exists())
            self.assertFalse((root / "outside.csv").exists())

    def test_existing_output_conflict_is_detected_before_partial_writes(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "exports"
            output.mkdir()
            sentinel = output / self.v118_contract().csv_filename
            sentinel.write_bytes(b"sentinel")

            with self.assertRaises(errors.OutputConflictError):
                export_database(self.request("V1.18", output))

            self.assertEqual(sentinel.read_bytes(), b"sentinel")
            self.assertEqual(tuple(output.iterdir()), (sentinel,))

    def test_publish_failure_removes_partial_outputs_and_temporary_files(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        original_replace = Path.replace
        publication_count = 0

        def fail_second_publication(source: Path, target: Path):
            nonlocal publication_count
            if source.parent.name.startswith(".export-"):
                publication_count += 1
                if publication_count == 2:
                    raise OSError("simulated publication failure")
            return original_replace(source, target)

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "exports"
            with patch.object(Path, "replace", autospec=True, side_effect=fail_second_publication):
                with self.assertRaisesRegex(OSError, "simulated publication failure"):
                    export_database(self.request("V1.18", output))

            self.assertTrue(output.is_dir())
            self.assertEqual(tuple(output.iterdir()), ())

    def test_export_api_has_only_the_single_typed_request_parameter(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        verify_exports = require_callable(
            self, "joy_m2.export.pipeline", "verify_exports"
        )
        self.assertEqual(tuple(inspect.signature(export_database).parameters), ("request",))
        self.assertEqual(tuple(inspect.signature(verify_exports).parameters), ("request",))
        export_api = importlib.import_module("joy_m2.export")
        self.assertEqual(export_api.__all__, ["export_database", "verify_exports"])
        self.assertIs(export_api.export_database, export_database)
        self.assertIs(export_api.verify_exports, verify_exports)

    def test_verify_exports_passes_then_reports_artifact_corruption(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        verify_exports = require_callable(
            self, "joy_m2.export.pipeline", "verify_exports"
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "exports"
            request = self.request("V1.18", output)
            artifacts = export_database(request)
            verification = models.ExportVerificationRequest(
                database=request.database,
                artifacts=artifacts,
                contract=request.contract,
            )

            passed = verify_exports(verification)
            self.assertEqual(passed.status, "PASS")
            self.assertTrue(all(check.passed for check in passed.checks))

            artifacts.csv.path.write_bytes(artifacts.csv.path.read_bytes() + b"corrupt")
            failed = verify_exports(verification)
            self.assertEqual(failed.status, "FAIL")
            self.assertTrue(any(not check.passed for check in failed.checks))

    def test_verify_exports_reports_a_missing_artifact_without_recreating_it(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        verify_exports = require_callable(
            self, "joy_m2.export.pipeline", "verify_exports"
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "exports"
            request = self.request("V1.18", output)
            artifacts = export_database(request)
            verification = models.ExportVerificationRequest(
                database=request.database,
                artifacts=artifacts,
                contract=request.contract,
            )
            preserved = {
                reference.path: reference.path.read_bytes()
                for reference in (
                    artifacts.knowledge_markdown,
                    artifacts.import_report,
                    artifacts.project_state,
                    artifacts.audit_records,
                    artifacts.audit_report,
                )
            }
            artifacts.csv.path.unlink()

            result = verify_exports(verification)

            self.assertEqual(result.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "csv_present" and not check.passed
                    for check in result.checks
                )
            )
            self.assertFalse(artifacts.csv.path.exists())
            self.assertEqual(
                {path: path.read_bytes() for path in preserved},
                preserved,
            )

    def test_verify_exports_reports_an_unexpected_file_without_deleting_it(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        verify_exports = require_callable(
            self, "joy_m2.export.pipeline", "verify_exports"
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "exports"
            request = self.request("V1.18", output)
            artifacts = export_database(request)
            verification = models.ExportVerificationRequest(
                database=request.database,
                artifacts=artifacts,
                contract=request.contract,
            )
            before = {
                reference.path: reference.path.read_bytes()
                for reference in (
                    artifacts.csv,
                    artifacts.knowledge_markdown,
                    artifacts.import_report,
                    artifacts.project_state,
                    artifacts.audit_records,
                    artifacts.audit_report,
                )
            }
            unexpected = output / "unexpected.txt"
            unexpected.write_bytes(b"unexpected")

            result = verify_exports(verification)

            self.assertEqual(result.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "expected_file_set" and not check.passed
                    for check in result.checks
                )
            )
            self.assertEqual(unexpected.read_bytes(), b"unexpected")
            self.assertEqual(
                {path: path.read_bytes() for path in before},
                before,
            )

    def test_verify_exports_reports_wrong_audit_report_structure_without_crashing(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        verify_exports = require_callable(
            self, "joy_m2.export.pipeline", "verify_exports"
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "exports"
            request = self.request("V1.18", output)
            artifacts = export_database(request)
            verification = models.ExportVerificationRequest(
                database=request.database,
                artifacts=artifacts,
                contract=request.contract,
            )
            wrong_value = artifacts.audit_records.path.read_bytes()
            artifacts.audit_report.path.write_bytes(wrong_value)

            result = verify_exports(verification)

            self.assertEqual(result.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "audit_report_json" and not check.passed
                    for check in result.checks
                )
            )
            self.assertEqual(artifacts.audit_report.path.read_bytes(), wrong_value)

    def test_verify_exports_reports_invalid_audit_json_without_crashing(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        verify_exports = require_callable(
            self, "joy_m2.export.pipeline", "verify_exports"
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "exports"
            request = self.request("V1.18", output)
            artifacts = export_database(request)
            verification = models.ExportVerificationRequest(
                database=request.database,
                artifacts=artifacts,
                contract=request.contract,
            )
            artifacts.audit_report.path.write_bytes(b"{not-json")

            result = verify_exports(verification)

            self.assertEqual(result.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "audit_report_json" and not check.passed
                    for check in result.checks
                )
            )
            self.assertEqual(artifacts.audit_report.path.read_bytes(), b"{not-json")

    def test_verify_exports_reports_incomplete_audit_report_object_without_crashing(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        verify_exports = require_callable(
            self, "joy_m2.export.pipeline", "verify_exports"
        )
        invalid_reports = (
            b"{}\n",
            b'{\n  "candidate_count": 452,\n  "source_count": true\n}\n',
            b'{\n  "candidate_count": true,\n  "source_count": 23\n}\n',
        )
        for invalid_report in invalid_reports:
            with self.subTest(invalid_report=invalid_report):
                with tempfile.TemporaryDirectory() as temp:
                    output = Path(temp) / "exports"
                    request = self.request("V1.18", output)
                    artifacts = export_database(request)
                    verification = models.ExportVerificationRequest(
                        database=request.database,
                        artifacts=artifacts,
                        contract=request.contract,
                    )
                    artifacts.audit_report.path.write_bytes(invalid_report)

                    result = verify_exports(verification)

                    self.assertEqual(result.status, "FAIL")
                    self.assertTrue(
                        any(
                            check.name == "audit_report_structure"
                            and not check.passed
                            for check in result.checks
                        )
                    )
                    self.assertEqual(
                        artifacts.audit_report.path.read_bytes(),
                        invalid_report,
                    )

    def test_csv_matches_every_sqlite_cell_and_markdown_has_complete_coverage(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "exports"
            artifacts = export_database(self.request("V1.18", output))
            with sqlite3.connect(self.v118_database.database.path) as database:
                database.row_factory = sqlite3.Row
                database_rows = [
                    dict(row)
                    for row in database.execute(
                        "SELECT * FROM complete_questions_v2 ORDER BY question_id"
                    )
                ]
            with artifacts.csv.path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as handle:
                csv_rows = list(csv.DictReader(handle))
            self.assertEqual(len(csv_rows), 497)
            self.assertEqual(
                csv_rows,
                [
                    {key: "" if value is None else str(value) for key, value in row.items()}
                    for row in database_rows
                ],
            )
            markdown = artifacts.knowledge_markdown.path.read_text(encoding="utf-8")
            self.assertEqual(
                len(
                    re.findall(
                        r"^### \d+\. `[^`]+`$",
                        markdown,
                        flags=re.MULTILINE,
                    )
                ),
                497,
            )
            self.assertEqual(markdown.count("来源未提供答案（`missing_from_source`）。"), 34)

    def test_export_is_deterministic_across_independent_output_directories(self) -> None:
        export_database = require_callable(
            self, "joy_m2.export.pipeline", "export_database"
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = export_database(self.request("V1.18", root / "first"))
            second = export_database(self.request("V1.18", root / "second"))
            for field_name in (
                "csv",
                "knowledge_markdown",
                "import_report",
                "project_state",
                "audit_records",
                "audit_report",
            ):
                with self.subTest(field=field_name):
                    left = getattr(first, field_name)
                    right = getattr(second, field_name)
                    self.assertEqual(left.sha256, right.sha256)
                    self.assertEqual(left.path.read_bytes(), right.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
