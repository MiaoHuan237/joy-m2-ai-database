from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from dataclasses import replace


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from joy_m2 import db as db_api
from joy_m2 import errors
from joy_m2 import models
from joy_m2.audit import pipeline as audit_pipeline
from joy_m2.release import transform_v117_release
from tests.unit.test_audit_pipeline import (
    V117_CANDIDATE,
    make_v117_asset_root,
    task5_request,
    task6_request,
)


V117_DIR = ROOT / "legacy/outputs/25757421d1d8/Task5_V1.17_正式入库"
V117_DATABASE = V117_DIR / "Joy_M2_Complete_Question_DB_V1_17.sqlite3"
V117_MANIFEST = V117_DIR / "manifest.json"
V118_DATABASE = ROOT / "releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3"
V118_SHA256 = "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7"
V116_DATABASE = (
    ROOT / "legacy/task5_work/v116/m2_question_bank/data/m2_question_bank.sqlite3"
)
V117_SHA256 = "58f32e547c4ff0cdd2ae25a9368ea288cbaa70af52869b779d698233aee93fab"
V116_SHA256 = "d647244f54e9e54b25ec4885f16c47171c7521552876a5fa925a16d65d8c7714"

REQUIRED_TABLES = (
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
REQUIRED_VIEWS = (
    "complete_questions",
    "selectable_complete_questions_v2",
    "selectable_questions",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(path: Path, kind: str) -> models.ArtifactRef:
    return models.ArtifactRef(
        path=path,
        sha256=sha256(path),
        size_bytes=path.stat().st_size,
        kind=kind,
    )


def manifest_variant(path: Path, **changes: object) -> Path:
    manifest = json.loads(V117_MANIFEST.read_text(encoding="utf-8"))
    manifest.update(changes)
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def v118_contract() -> models.DatabaseContract:
    return models.DatabaseContract(
        profile="V1.18",
        expected_user_version=118,
        expected_question_count=497,
        expected_existing_question_count=45,
        expected_new_question_count=452,
        expected_answer_status_counts=(
            ("ai_solved_verified", 71),
            ("missing_from_source", 34),
            ("source_provided", 392),
        ),
        required_tables=REQUIRED_TABLES,
        required_views=REQUIRED_VIEWS,
        journal_mode="delete",
        vacuum=True,
    )


def v118_release_spec() -> models.ReleaseSpec:
    return models.ReleaseSpec(
        release_version="V1.18",
        baseline_version="V1.17",
        baseline_sqlite_sha256="58f32e547c4ff0cdd2ae25a9368ea288cbaa70af52869b779d698233aee93fab",
        schema_version="complete-question-v1.0",
        created_at="2026-08-08T21:00:00+08:00",
    )


def v117_contract() -> models.DatabaseContract:
    return models.DatabaseContract(
        profile="V1.17",
        expected_user_version=117,
        expected_question_count=45,
        expected_existing_question_count=0,
        expected_new_question_count=45,
        expected_answer_status_counts=(("source_provided", 45),),
        required_tables=REQUIRED_TABLES,
        required_views=REQUIRED_VIEWS,
        journal_mode="delete",
        vacuum=True,
    )


def v117_release_spec() -> models.ReleaseSpec:
    return models.ReleaseSpec(
        release_version="V1.17",
        baseline_version="V1.16",
        baseline_sqlite_sha256=V116_SHA256,
        schema_version="complete-question-v1.0",
        created_at="2026-08-08T20:00:00+08:00",
    )


def v117_release_batch(root: Path) -> models.V117ReleaseBatch:
    raw_records = json.loads(V117_CANDIDATE.read_text(encoding="utf-8"))
    asset_root = make_v117_asset_root(root, raw_records)
    result = audit_pipeline.audit_batch(task5_request(V117_CANDIDATE, asset_root))
    return transform_v117_release(
        result,
        models.V117ReleaseDecision(
            formal_release_version="V1.17",
            selectable=True,
            record_status="published",
            joy_approval="approved_by_joy",
            approved_at="2026-08-08T20:00:00+08:00",
            schema_version="complete-question-v1.0",
        ),
    )


def build_request(
    *,
    batch: models.AuditedBatch | models.V117ReleaseBatch,
    output: Path,
    baseline: Path = V117_DATABASE,
    manifest: Path = V117_MANIFEST,
    contract: models.DatabaseContract | None = None,
    release_spec: models.ReleaseSpec | None = None,
) -> models.DatabaseBuildRequest:
    return models.DatabaseBuildRequest(
        batch=batch,
        baseline_database=artifact(baseline, "sqlite"),
        baseline_manifest=artifact(manifest, "json"),
        output_path=output,
        release_spec=release_spec or v118_release_spec(),
        contract=contract or v118_contract(),
    )


def require_database_api(test: unittest.TestCase):
    build = getattr(db_api, "build_database", None)
    verify = getattr(db_api, "verify_database", None)
    test.assertIsNotNone(build, "missing approved database API: build_database")
    test.assertIsNotNone(verify, "missing approved database API: verify_database")
    return build, verify


class V118DatabaseBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit_result = audit_pipeline.audit_batch(task6_request())
        cls.batch = cls.audit_result.require_passed()

    def test_build_is_byte_equivalent_and_preserves_the_v117_baseline(self) -> None:
        build_database, verify_database = require_database_api(self)
        baseline_bytes = V117_DATABASE.read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate/Joy_M2_Complete_Question_DB_V1_18.sqlite3"
            request = models.DatabaseBuildRequest(
                batch=self.batch,
                baseline_database=artifact(V117_DATABASE, "sqlite"),
                baseline_manifest=artifact(V117_MANIFEST, "json"),
                output_path=output,
                release_spec=v118_release_spec(),
                contract=v118_contract(),
            )

            result = build_database(request)

            self.assertEqual(result.database.path, output.resolve())
            self.assertEqual(result.database.sha256, V118_SHA256)
            self.assertEqual(result.database.size_bytes, output.stat().st_size)
            self.assertEqual(result.database.kind, "sqlite")
            self.assertEqual(result.release_spec, request.release_spec)
            self.assertEqual(result.verification_report.status, "PASS")
            self.assertTrue(all(check.passed for check in result.verification_report.checks))
            self.assertEqual(sha256(output), V118_SHA256)
            self.assertEqual(output.read_bytes(), V118_DATABASE.read_bytes())
            self.assertEqual(V117_DATABASE.read_bytes(), baseline_bytes)
            self.assertEqual(
                verify_database(output, request.contract),
                result.verification_report,
            )

            with sqlite3.connect(output) as database:
                self.assertEqual(database.execute("PRAGMA user_version").fetchone()[0], 118)
                self.assertEqual(database.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(database.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(
                    database.execute("SELECT COUNT(*) FROM complete_questions_v2").fetchone()[0],
                    497,
                )
                self.assertEqual(
                    database.execute(
                        "SELECT COUNT(*) FROM complete_questions_v2 WHERE source_order > 45"
                    ).fetchone()[0],
                    452,
                )
                self.assertEqual(
                    dict(
                        database.execute(
                            "SELECT answer_status, COUNT(*) FROM complete_questions_v2 "
                            "GROUP BY answer_status"
                        )
                    ),
                    {
                        "ai_solved_verified": 71,
                        "missing_from_source": 34,
                        "source_provided": 392,
                    },
                )

            with sqlite3.connect(V117_DATABASE) as baseline, sqlite3.connect(output) as built:
                self.assertEqual(
                    built.execute(
                        "SELECT * FROM complete_questions_v2 WHERE source_order <= 45 "
                        "ORDER BY source_order"
                    ).fetchall(),
                    baseline.execute(
                        "SELECT * FROM complete_questions_v2 ORDER BY source_order"
                    ).fetchall(),
                )

    def test_frozen_projection_preserves_the_upstream_audit_carriers(self) -> None:
        build_database, _ = require_database_api(self)
        records_before = self.batch.records
        statuses_before = tuple(
            record.question.publication_evidence.record_status
            for record in self.batch.records
        )
        self.assertEqual(set(statuses_before), {"audit_passed"})

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate.sqlite3"

            build_database(build_request(batch=self.batch, output=output))

            self.assertIs(self.batch.records, records_before)
            self.assertEqual(
                tuple(
                    record.question.publication_evidence.record_status
                    for record in self.batch.records
                ),
                statuses_before,
            )
            with sqlite3.connect(output) as database:
                self.assertEqual(
                    database.execute(
                        "SELECT DISTINCT record_status FROM complete_questions_v2 "
                        "WHERE source_order > 45"
                    ).fetchall(),
                    [("published",)],
                )

    def test_frozen_projection_rejects_a_non_audit_passed_source_status(self) -> None:
        build_database, _ = require_database_api(self)
        first = self.batch.records[0]
        invalid_evidence = replace(
            first.question.publication_evidence,
            record_status="published",
        )
        invalid_record = replace(
            first,
            question=replace(
                first.question,
                publication_evidence=invalid_evidence,
            ),
        )
        invalid_batch = models.AuditedBatch(
            (invalid_record, *self.batch.records[1:])
        )

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "not-created/candidate.sqlite3"

            with self.assertRaises(errors.PipelineError):
                build_database(build_request(batch=invalid_batch, output=output))

            self.assertFalse(output.parent.exists())

    def test_existing_output_is_never_overwritten(self) -> None:
        build_database, _ = require_database_api(self)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "existing.sqlite3"
            output.write_bytes(b"sentinel")

            with self.assertRaises(errors.OutputConflictError):
                build_database(build_request(batch=self.batch, output=output))

            self.assertEqual(output.read_bytes(), b"sentinel")

    def test_repeated_builds_are_byte_for_byte_deterministic(self) -> None:
        build_database, _ = require_database_api(self)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "first.sqlite3"
            second = root / "second.sqlite3"

            build_database(build_request(batch=self.batch, output=first))
            build_database(build_request(batch=self.batch, output=second))

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(sha256(first), V118_SHA256)

    def test_profile_batch_mismatch_is_rejected_before_output_creation(self) -> None:
        build_database, _ = require_database_api(self)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "candidate.sqlite3"
            release_batch = v117_release_batch(root)

            with self.assertRaises(errors.PipelineError):
                build_database(build_request(batch=release_batch, output=output))

            self.assertFalse(output.exists())

    def test_unknown_source_is_atomic_foreign_key_failure(self) -> None:
        build_database, _ = require_database_api(self)
        first = self.batch.records[0]
        bad_question = replace(first.question, source_id="UNKNOWN-SOURCE")
        bad_batch = models.AuditedBatch(
            (replace(first, question=bad_question), *self.batch.records[1:])
        )
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate.sqlite3"

            with self.assertRaises(errors.ForeignKeyViolationError):
                build_database(build_request(batch=bad_batch, output=output))

            self.assertFalse(output.exists())

    def test_duplicate_question_id_is_atomic_integrity_failure(self) -> None:
        build_database, _ = require_database_api(self)
        first, second, *remaining = self.batch.records
        duplicate = replace(
            second,
            question=replace(second.question, question_id=first.question.question_id),
        )
        bad_batch = models.AuditedBatch((first, duplicate, *remaining))
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate.sqlite3"

            with self.assertRaises(errors.DatabaseIntegrityError):
                build_database(build_request(batch=bad_batch, output=output))

            self.assertFalse(output.exists())

    def test_malformed_but_manifest_bound_baseline_is_rejected_before_output_parent(self) -> None:
        build_database, _ = require_database_api(self)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = root / V117_DATABASE.name
            shutil.copyfile(V117_DATABASE, baseline)
            with sqlite3.connect(baseline) as database:
                database.execute("DROP VIEW complete_questions")
            baseline_hash = sha256(baseline)
            manifest = root / "manifest.json"
            artifact_digests = json.loads(
                V117_MANIFEST.read_text(encoding="utf-8")
            )["artifact_sha256"].copy()
            artifact_digests[baseline.name] = baseline_hash
            manifest_variant(
                manifest,
                artifact_sha256=artifact_digests,
            )
            output = root / "not-created/candidate.sqlite3"
            request = build_request(
                batch=self.batch,
                output=output,
                baseline=baseline,
                manifest=manifest,
                release_spec=replace(
                    v118_release_spec(), baseline_sqlite_sha256=baseline_hash
                ),
            )

            with self.assertRaises(errors.DatabaseIntegrityError):
                build_database(request)

            self.assertFalse(output.parent.exists())

    def test_baseline_identity_mismatch_produces_no_output(self) -> None:
        build_database, _ = require_database_api(self)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "not-created/candidate.sqlite3"
            request = build_request(batch=self.batch, output=output)
            request = replace(
                request,
                baseline_database=replace(
                    request.baseline_database,
                    sha256="0" * 64,
                ),
            )

            with self.assertRaises(errors.BaselineMismatchError):
                build_database(request)

            self.assertFalse(output.parent.exists())

    def test_manifest_identity_mismatches_produce_no_output(self) -> None:
        build_database, _ = require_database_api(self)
        wrong_identities = (
            ("release_version", "V9.99"),
            ("schema_version", "wrong-schema"),
            ("release_status", "draft"),
            ("release_model", "wrong-model"),
        )
        for field_name, value in wrong_identities:
            with self.subTest(field_name=field_name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = manifest_variant(root / "manifest.json", **{field_name: value})
                output = root / "not-created/candidate.sqlite3"

                with self.assertRaises(errors.BaselineMismatchError):
                    build_database(
                        build_request(
                            batch=self.batch,
                            output=output,
                            manifest=manifest,
                        )
                    )

                self.assertFalse(output.parent.exists())


class V117DatabaseBuildTests(unittest.TestCase):
    def test_build_is_byte_equivalent_and_preserves_v116_tables(self) -> None:
        build_database, verify_database = require_database_api(self)
        baseline_bytes = V116_DATABASE.read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            batch = v117_release_batch(root)
            output = root / "candidate/Joy_M2_Complete_Question_DB_V1_17.sqlite3"
            request = build_request(
                batch=batch,
                output=output,
                baseline=V116_DATABASE,
                contract=v117_contract(),
                release_spec=v117_release_spec(),
            )

            result = build_database(request)

            self.assertEqual(sha256(output), V117_SHA256)
            self.assertEqual(output.read_bytes(), V117_DATABASE.read_bytes())
            self.assertEqual(V116_DATABASE.read_bytes(), baseline_bytes)
            self.assertEqual(result.verification_report.status, "PASS")
            self.assertEqual(
                verify_database(output, request.contract),
                result.verification_report,
            )
            with sqlite3.connect(V116_DATABASE) as baseline, sqlite3.connect(output) as built:
                for table in ("sources", "topics", "questions", "question_topics"):
                    self.assertEqual(
                        built.execute(f"SELECT * FROM {table}").fetchall(),
                        baseline.execute(f"SELECT * FROM {table}").fetchall(),
                    )

    def test_v117_rejects_audit_stage_batch_before_output_creation(self) -> None:
        build_database, _ = require_database_api(self)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw_records = json.loads(V117_CANDIDATE.read_text(encoding="utf-8"))
            asset_root = make_v117_asset_root(root, raw_records)
            audited = audit_pipeline.audit_batch(
                task5_request(V117_CANDIDATE, asset_root)
            ).require_passed()
            output = root / "candidate.sqlite3"
            request = build_request(
                batch=audited,
                output=output,
                baseline=V116_DATABASE,
                contract=v117_contract(),
                release_spec=v117_release_spec(),
            )

            with self.assertRaises(errors.PipelineError):
                build_database(request)

            self.assertFalse(output.exists())

    def test_v117_rejects_wrong_manifest_identity_before_output_creation(self) -> None:
        build_database, _ = require_database_api(self)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            batch = v117_release_batch(root)
            manifest = manifest_variant(
                root / "manifest.json",
                release_status="draft",
            )
            output = root / "not-created/candidate.sqlite3"

            with self.assertRaises(errors.BaselineMismatchError):
                build_database(
                    build_request(
                        batch=batch,
                        output=output,
                        baseline=V116_DATABASE,
                        manifest=manifest,
                        contract=v117_contract(),
                        release_spec=v117_release_spec(),
                    )
                )

            self.assertFalse(output.parent.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
