"""Behavior contracts for Task 9C writer primitives and verification."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import unittest
from unittest import mock

from joy_m2.config import PipelineConfig
from joy_m2.errors import InputFormatError, InputMissingError, PipelineError
import joy_m2.ingest.writer as writer_module
import joy_m2.ingest.writer_verification as verifier_module
from joy_m2.ingest.preflight import preflight_import
from joy_m2.ingest.writer import build_v119_candidate
from joy_m2.ingest.writer_models import (
    ImportApproval,
    V119VerificationRequest,
    V119WriteRequest,
    V119WriterContract,
)
from joy_m2.ingest.writer_verification import verify_v119_candidate
from joy_m2.models import ArtifactRef, VerificationReport
from tests.integration.test_ingest_preflight import (
    _baseline_ref,
    _package,
    _raw_candidate,
)


SHA256 = hashlib.sha256
WORKTREE = Path(__file__).resolve().parents[2]
CHECK_NAMES = (
    "candidate_directory",
    "manifest_contract",
    "preflight_approval_binding",
    "filesystem_closure",
    "sha256sums_closure",
    "artifact_references",
    "rollback_contract",
    "image_projection",
    "sqlite_readability",
    "sqlite_integrity",
    "sqlite_foreign_keys",
    "sqlite_schema",
    "sqlite_projection",
    "baseline_preservation",
    "count_closure",
    "publication_boundary",
)
MANIFEST_KEYS = (
    "schema_version",
    "release_version",
    "release_status",
    "release_model",
    "batch",
    "baseline",
    "counts",
    "database",
    "images",
    "candidate_record_evidence",
    "source_evidence",
    "answer_evidence",
    "teacher_notes_evidence",
    "common_errors_evidence",
    "rollback",
)
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
EXPECTED_TASK9_SQL = {
    "task9_import_batches_v1": """
        CREATE TABLE task9_import_batches_v1 (
            batch_id TEXT PRIMARY KEY,
            target_release_version TEXT NOT NULL CHECK(target_release_version='V1.19'),
            candidate_database_schema TEXT NOT NULL CHECK(candidate_database_schema='task9-v119-candidate-v1'),
            preflight_sha256 TEXT NOT NULL,
            manifest_sha256 TEXT NOT NULL,
            approval_statement TEXT NOT NULL,
            baseline_release_version TEXT NOT NULL CHECK(baseline_release_version='V1.18'),
            baseline_database_sha256 TEXT NOT NULL,
            baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count=497),
            candidate_count INTEGER NOT NULL CHECK(candidate_count>=0),
            projected_question_count INTEGER NOT NULL CHECK(projected_question_count=baseline_question_count+candidate_count),
            record_status TEXT NOT NULL CHECK(record_status='candidate')
        )
    """,
    "task9_import_candidates_v1": """
        CREATE TABLE task9_import_candidates_v1 (
            batch_id TEXT NOT NULL REFERENCES task9_import_batches_v1(batch_id),
            candidate_order INTEGER NOT NULL CHECK(candidate_order>=0),
            proposed_question_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_question_number TEXT NOT NULL,
            source_section TEXT NOT NULL,
            source_fragment_hash TEXT NOT NULL,
            normalized_text_sha256 TEXT NOT NULL,
            question_text_original TEXT NOT NULL,
            question_text_zh TEXT NOT NULL,
            translation_status TEXT NOT NULL CHECK(translation_status IN ('source_present','ai_proposed','verified','missing')),
            translation_evidence TEXT,
            solution_original TEXT NOT NULL,
            solution_verified TEXT NOT NULL,
            answer_status TEXT NOT NULL CHECK(answer_status IN ('source_provided','ai_solved_verified','missing_from_source')),
            explanation_text TEXT NOT NULL,
            explanation_status TEXT NOT NULL CHECK(explanation_status IN ('source_present','ai_proposed','verified','missing')),
            explanation_evidence TEXT,
            image_paths_json TEXT NOT NULL,
            image_sha256s_json TEXT NOT NULL,
            image_roles_json TEXT NOT NULL,
            primary_type TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            tag_status TEXT NOT NULL CHECK(tag_status IN ('source_provided','proposed','missing')),
            difficulty_level INTEGER CHECK(difficulty_level BETWEEN 1 AND 5 OR difficulty_level IS NULL),
            difficulty_status TEXT NOT NULL CHECK(difficulty_status IN ('source_provided','proposed','missing')),
            enrichment_status TEXT NOT NULL CHECK(enrichment_status IN ('complete','incomplete')),
            candidate_image_paths_json TEXT NOT NULL,
            record_status TEXT NOT NULL CHECK(record_status='candidate'),
            selectable INTEGER NOT NULL CHECK(selectable=0),
            PRIMARY KEY(batch_id, proposed_question_id),
            UNIQUE(batch_id, candidate_order)
        )
    """,
    "task9_import_images_v1": """
        CREATE TABLE task9_import_images_v1 (
            batch_id TEXT NOT NULL,
            proposed_question_id TEXT NOT NULL,
            image_order INTEGER NOT NULL CHECK(image_order>=0),
            source_relative_path TEXT NOT NULL,
            candidate_relative_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            size_bytes INTEGER NOT NULL CHECK(size_bytes>=0),
            kind TEXT NOT NULL CHECK(kind='image'),
            role TEXT NOT NULL,
            PRIMARY KEY(batch_id, proposed_question_id, image_order),
            FOREIGN KEY(batch_id, proposed_question_id)
                REFERENCES task9_import_candidates_v1(batch_id, proposed_question_id)
        )
    """,
    "task9_import_taxonomy_v1": """
        CREATE TABLE task9_import_taxonomy_v1 (
            batch_id TEXT NOT NULL REFERENCES task9_import_batches_v1(batch_id),
            taxonomy_kind TEXT NOT NULL CHECK(taxonomy_kind IN ('primary_type','tag')),
            value TEXT NOT NULL,
            sort_order INTEGER NOT NULL CHECK(sort_order>=1),
            PRIMARY KEY(batch_id, taxonomy_kind, value),
            UNIQUE(batch_id, taxonomy_kind, sort_order)
        )
    """,
    "task9_candidate_questions_v1": """
        CREATE VIEW task9_candidate_questions_v1 AS
        SELECT *
        FROM task9_import_candidates_v1
        ORDER BY batch_id, candidate_order
    """,
}


class _NonPathLocator:
    def resolve(self, *args, **kwargs):
        return self


class _SecondResolveRaisesPath(type(Path())):
    resolve_calls = 0

    def resolve(self, *args, **kwargs):
        type(self).resolve_calls += 1
        if type(self).resolve_calls > 1:
            raise OSError("synthetic locator failure")
        return self


def _sha(data: bytes) -> str:
    return SHA256(data).hexdigest()


def _normalized_sql(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().rstrip(";")


def _contract() -> V119WriterContract:
    return V119WriterContract(
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


def _approval(preflight) -> ImportApproval:
    digest = preflight.report.preflight_sha256
    batch_id = preflight.manifest.batch_id
    return ImportApproval(
        batch_id=batch_id,
        preflight_sha256=digest,
        target_release_version="V1.19",
        statement=f"USER APPROVED IMPORT BATCH {batch_id} {digest} V1.19",
    )


def _ready_context(
    root: Path,
    *,
    records: list[dict[str, object]] | None = None,
    images: dict[str, bytes] | None = None,
):
    package_root = root / "package"
    package_root.mkdir()
    groups = None if records is None else (("records/candidates.json", records),)
    manifest = _package(package_root, record_groups=groups, images=images)
    preflight = preflight_import(manifest, package_root, _baseline_ref())
    if preflight.report.status != "READY FOR USER IMPORT APPROVAL":
        raise AssertionError(preflight)
    config = PipelineConfig(root / "repository")
    output = config.staging_root / "task9c-candidate"
    request = V119WriteRequest(
        preflight,
        package_root,
        _approval(preflight),
        output,
        _contract(),
    )
    return request, config


def _call_build(testcase: unittest.TestCase, request, config):
    try:
        return build_v119_candidate(request, config)
    except NotImplementedError as error:
        testcase.fail(f"Task 9C builder behavior is missing: {error}")


def _call_verify(testcase: unittest.TestCase, request, config):
    try:
        return verify_v119_candidate(request, config)
    except NotImplementedError as error:
        testcase.fail(f"Task 9C verifier behavior is missing: {error}")


def _verification_request(write_request: V119WriteRequest) -> V119VerificationRequest:
    return V119VerificationRequest(
        write_request.output_dir,
        write_request.preflight_result,
        write_request.approval,
        write_request.contract,
    )


def _rebind_preflight_authority(request: V119WriteRequest, preflight) -> V119WriteRequest:
    from dataclasses import replace

    manifest_sha256, _ = writer_module._recomputed_digests(preflight)
    preflight = replace(
        preflight,
        report=replace(preflight.report, manifest_sha256=manifest_sha256),
    )
    _, preflight_sha256 = writer_module._recomputed_digests(preflight)
    preflight = replace(
        preflight,
        report=replace(preflight.report, preflight_sha256=preflight_sha256),
    )
    approval = ImportApproval(
        preflight.manifest.batch_id,
        preflight_sha256,
        "V1.19",
        f"USER APPROVED IMPORT BATCH {preflight.manifest.batch_id} "
        f"{preflight_sha256} V1.19",
    )
    return replace(request, preflight_result=preflight, approval=approval)


def _fingerprint(root: Path) -> tuple[tuple[str, str], ...]:
    if not root.exists():
        return ()
    return tuple(
        (path.relative_to(root).as_posix(), _sha(path.read_bytes()))
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )


def _entry_snapshot(root: Path) -> tuple[tuple[str, str, str], ...]:
    if not root.exists():
        return ()
    entries = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            entries.append((relative, "symlink", os.readlink(path)))
        elif path.is_dir():
            entries.append((relative, "directory", ""))
        elif path.is_file():
            entries.append((relative, "file", _sha(path.read_bytes())))
        else:
            entries.append((relative, "other", ""))
    return tuple(entries)


class _RealWorktreeGuard:
    def setUp(self) -> None:
        self._worktree_data = _entry_snapshot(WORKTREE / "data" / "staging")
        self._worktree_releases = _entry_snapshot(WORKTREE / "releases")

    def tearDown(self) -> None:
        self.assertEqual(
            _entry_snapshot(WORKTREE / "data" / "staging"), self._worktree_data
        )
        self.assertEqual(
            _entry_snapshot(WORKTREE / "releases"), self._worktree_releases
        )
        self.assertFalse((WORKTREE / "releases" / "V1.19").exists())


def _canonical_json_file(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _refresh_manifest_artifacts_and_sums(request: V119WriteRequest) -> None:
    manifest_path = request.output_dir / request.contract.manifest_filename
    database_path = request.output_dir / request.contract.database_filename
    payload = json.loads(manifest_path.read_bytes())
    payload["database"]["sha256"] = _sha(database_path.read_bytes())
    payload["database"]["size_bytes"] = database_path.stat().st_size
    rollback_path = request.output_dir / request.contract.rollback_filename
    payload["rollback"]["sha256"] = _sha(rollback_path.read_bytes())
    payload["rollback"]["size_bytes"] = rollback_path.stat().st_size
    for image in payload["images"]:
        image_path = request.output_dir / image["relative_path"]
        image["sha256"] = _sha(image_path.read_bytes())
        image["size_bytes"] = image_path.stat().st_size
    manifest_path.write_bytes(_canonical_json_file(payload))
    _rewrite_sums(request)


def _rewrite_sums(request: V119WriteRequest) -> None:
    sums_path = request.output_dir / request.contract.sha256s_filename
    relatives = tuple(
        sorted(
            path.relative_to(request.output_dir).as_posix()
            for path in request.output_dir.rglob("*")
            if path.is_file() and path != sums_path
        )
    )
    sums_path.write_text(
        "".join(
            f"{_sha((request.output_dir / relative).read_bytes())}  {relative}\n"
            for relative in relatives
        ),
        encoding="utf-8",
        newline="",
    )


def _relative_artifact(artifact: ArtifactRef, root: Path) -> dict[str, object]:
    return {
        "relative_path": artifact.path.relative_to(root).as_posix(),
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "kind": artifact.kind,
    }


def _file_evidence_group(values) -> list[dict[str, object]]:
    return [asdict(value) for value in values]


def _expected_manifest(request: V119WriteRequest, artifacts) -> dict[str, object]:
    preflight = request.preflight_result
    report = preflight.report
    manifest = preflight.manifest
    evidence_by_path = {
        item.relative_path: item for item in manifest.image_files
    }
    image_entries = []
    for artifact in artifacts.images:
        relative_path = artifact.path.relative_to(request.output_dir).as_posix()
        bindings = []
        for candidate_order, candidate in enumerate(preflight.candidates):
            for image_order, (source_path, digest, role) in enumerate(
                zip(
                    candidate.image_paths,
                    candidate.image_sha256s,
                    candidate.image_roles,
                    strict=True,
                )
            ):
                if digest == artifact.sha256:
                    bindings.append(
                        {
                            "proposed_question_id": candidate.proposed_question_id,
                            "image_order": image_order,
                            "source_relative_path": source_path,
                            "role": role,
                        }
                    )
                    self_evidence = evidence_by_path[source_path]
                    if self_evidence.size_bytes != artifact.size_bytes:
                        raise AssertionError("image evidence size does not close")
        image_entries.append(
            {
                "relative_path": relative_path,
                "sha256": artifact.sha256,
                "size_bytes": artifact.size_bytes,
                "kind": "image",
                "bindings": bindings,
            }
        )
    return {
        "schema_version": "task9-v119-candidate-manifest-v1",
        "release_version": "V1.19",
        "release_status": "candidate",
        "release_model": "incremental-import-candidate",
        "batch": {
            "batch_id": manifest.batch_id,
            "preflight_sha256": report.preflight_sha256,
            "manifest_sha256": report.manifest_sha256,
            "approval_statement": request.approval.statement,
            "candidate_database_schema": "task9-v119-candidate-v1",
        },
        "baseline": {
            "release_version": "V1.18",
            "question_count": 497,
            "schema_version": "complete-question-v1.0",
            "sqlite": {
                "sha256": preflight.baseline_database.sha256,
                "size_bytes": preflight.baseline_database.size_bytes,
                "kind": "sqlite",
            },
        },
        "counts": {
            name: getattr(report, name)
            for name in (
                "before_count",
                "detected_count",
                "new_candidate_count",
                "duplicate_count",
                "rejected_count",
                "ambiguous_count",
                "approved_count",
                "projected_after_count",
            )
        },
        "database": _relative_artifact(artifacts.database, request.output_dir),
        "images": image_entries,
        "candidate_record_evidence": _file_evidence_group(manifest.candidate_records),
        "source_evidence": _file_evidence_group(manifest.source_files),
        "answer_evidence": _file_evidence_group(manifest.answer_files),
        "teacher_notes_evidence": _file_evidence_group(manifest.teacher_notes_files),
        "common_errors_evidence": _file_evidence_group(manifest.common_errors_files),
        "rollback": _relative_artifact(artifacts.rollback, request.output_dir),
    }


def _assert_full_report(testcase: unittest.TestCase, report: VerificationReport, status: str) -> None:
    testcase.assertIs(type(report), VerificationReport)
    testcase.assertEqual(report.status, status)
    testcase.assertEqual(tuple(check.name for check in report.checks), CHECK_NAMES)
    testcase.assertEqual(len(report.checks), 16)
    testcase.assertTrue(all(type(check.passed) is bool for check in report.checks))
    testcase.assertTrue(
        all(check.detail == ("PASS" if check.passed else "FAIL") for check in report.checks)
    )
    testcase.assertEqual(
        status,
        "PASS" if all(check.passed for check in report.checks) else "FAIL",
    )


def _checks(report: VerificationReport) -> dict[str, bool]:
    return {check.name: check.passed for check in report.checks}


class V119WriterProfileRedTests(_RealWorktreeGuard, unittest.TestCase):
    def test_exact_profile_ddl_objects_and_candidate_boundary(self) -> None:
        self.assertIsNotNone(
            importlib.util.find_spec("joy_m2.ingest.writer_profiles"),
            "Task 9C private writer profile is not implemented",
        )
        with tempfile.TemporaryDirectory() as directory:
            request, config = _ready_context(Path(directory))
            result = _call_build(self, request, config)
            with sqlite3.connect(result.database.path) as database:
                self.assertEqual(database.execute("PRAGMA user_version").fetchone()[0], 119)
                objects = tuple(
                    database.execute(
                        "SELECT type, name FROM sqlite_master "
                        "WHERE name LIKE 'task9_%' ORDER BY type, name"
                    )
                )
                self.assertEqual(
                    objects,
                    tuple(("table", name) for name in CANDIDATE_TABLES)
                    + (("view", CANDIDATE_VIEWS[0]),),
                )
                actual_sql = dict(
                    database.execute(
                        "SELECT name,sql FROM sqlite_master WHERE name LIKE 'task9_%'"
                    )
                )
                self.assertEqual(set(actual_sql), set(EXPECTED_TASK9_SQL))
                self.assertEqual(
                    {name: _normalized_sql(sql) for name, sql in actual_sql.items()},
                    {
                        name: _normalized_sql(sql)
                        for name, sql in EXPECTED_TASK9_SQL.items()
                    },
                )
                self.assertEqual(
                    database.execute(
                        "SELECT COUNT(*) FROM complete_questions_v2"
                    ).fetchone()[0],
                    497,
                )
                self.assertEqual(
                    database.execute(
                        "SELECT COUNT(*) FROM task9_import_candidates_v1 "
                        "WHERE record_status!='candidate' OR selectable!=0"
                    ).fetchone()[0],
                    0,
                )


class V119ImageProjectionRedTests(_RealWorktreeGuard, unittest.TestCase):
    def _image_request(self, root: Path, paths: list[str], contents: list[bytes]):
        record = _raw_candidate(
            image_paths=paths,
            image_roles=[f"role-{index}" for index in range(len(paths))],
        )
        return _ready_context(
            root,
            records=[record],
            images=dict(zip(paths, contents, strict=True)),
        )

    def test_suffix_mapping_dedup_binding_order_and_exact_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shared = b"shared jpeg bytes"
            png = b"png bytes"
            paths = ["images/FIRST.JPG", "images/second.jpeg", "images/third.PNG"]
            request, config = self._image_request(root, paths, [shared, shared, png])
            result = _call_build(self, request, config)
            expected = (
                f"images/sha256/{_sha(shared)[:2]}/{_sha(shared)}.jpg",
                f"images/sha256/{_sha(png)[:2]}/{_sha(png)}.png",
            )
            self.assertEqual(
                tuple(path.path.relative_to(request.output_dir).as_posix() for path in result.images),
                tuple(sorted(expected)),
            )
            self.assertEqual(
                {path.path.read_bytes() for path in result.images},
                {shared, png},
            )
            with sqlite3.connect(result.database.path) as database:
                bindings = tuple(
                    database.execute(
                        "SELECT source_relative_path, candidate_relative_path, image_order "
                        "FROM task9_import_images_v1 ORDER BY image_order"
                    )
                )
            self.assertEqual(tuple(row[0] for row in bindings), tuple(paths))
            self.assertEqual(tuple(row[2] for row in bindings), (0, 1, 2))
            self.assertEqual(bindings[0][1], bindings[1][1])

    def test_unsupported_and_empty_suffix_block_before_staging(self) -> None:
        for suffix in (".gif", ""):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = f"images/unsupported{suffix}"
                request, config = self._image_request(root, [path], [b"unsupported"])
                before = _fingerprint(config.repo_root)
                with self.assertRaises(InputFormatError):
                    _call_build(self, request, config)
                self.assertFalse(request.output_dir.exists())
                self.assertEqual(_fingerprint(config.repo_root), before)

    def test_missing_tampered_and_nonregular_images_block_without_output(self) -> None:
        mutations = (
            "missing",
            "size_mismatch",
            "sha_mismatch",
            "directory",
            "symlink_escape",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                relative = "images/question.png"
                request, config = self._image_request(root, [relative], [b"image bytes"])
                source = request.package_root / relative
                if mutation == "missing":
                    source.unlink()
                elif mutation == "size_mismatch":
                    source.write_bytes(b"longer image bytes")
                elif mutation == "sha_mismatch":
                    source.write_bytes(b"other bytes")
                else:
                    source.unlink()
                    if mutation == "directory":
                        source.mkdir()
                    else:
                        outside = root / "outside.png"
                        outside.write_bytes(b"image bytes")
                        source.symlink_to(outside)
                with self.assertRaises(PipelineError):
                    _call_build(self, request, config)
                self.assertFalse(request.output_dir.exists())

    def test_digest_extension_and_destination_collisions_block_before_temp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, config = self._image_request(
                root,
                ["images/one.jpg", "images/two.png"],
                [b"same", b"same"],
            )
            with self.assertRaises(InputFormatError):
                _call_build(self, request, config)
            self.assertFalse(request.output_dir.exists())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, config = self._image_request(
                root,
                ["images/one.jpg", "images/two.jpeg"],
                [b"same", b"same"],
            )
            (request.package_root / "images/two.jpeg").write_bytes(b"different")
            with self.assertRaises(InputFormatError):
                _call_build(self, request, config)
            self.assertFalse(request.output_dir.exists())

    def test_unreferenced_package_file_is_never_copied(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, config = self._image_request(
                root, ["images/used.png"], [b"used image"]
            )
            extra = request.package_root / "images/unreferenced.png"
            extra.write_bytes(b"must not be copied")
            result = _call_build(self, request, config)
            self.assertFalse(any("unreferenced" in path.as_posix() for path in request.output_dir.rglob("*")))
            self.assertEqual(len(result.images), 1)


class V119ManifestAndVerificationRedTests(_RealWorktreeGuard, unittest.TestCase):
    def _built(self, root: Path):
        record = _raw_candidate(
            image_paths=["images/question.png"],
            image_roles=["question"],
            primary_type="切线与法线",
            tags=["过指定点的切线"],
            tag_status="source_provided",
        )
        request, config = _ready_context(
            root,
            records=[record],
            images={"images/question.png": b"question image bytes"},
        )
        artifacts = _call_build(self, request, config)
        return request, config, artifacts

    def test_manifest_has_exact_schema_identity_evidence_and_path_exclusion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request, _, artifacts = self._built(Path(directory))
            raw = artifacts.manifest.path.read_bytes()
            self.assertTrue(raw.endswith(b"\n"))
            self.assertFalse(raw.endswith(b"\n\n"))
            payload = json.loads(raw)
            expected_payload = _expected_manifest(request, artifacts)
            self.assertEqual(payload, expected_payload)
            self.assertEqual(
                raw,
                json.dumps(
                    expected_payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8")
                + b"\n",
            )
            self.assertEqual(set(payload), set(MANIFEST_KEYS))
            self.assertEqual(payload["schema_version"], "task9-v119-candidate-manifest-v1")
            self.assertEqual(payload["release_version"], "V1.19")
            self.assertEqual(payload["release_status"], "candidate")
            self.assertEqual(payload["release_model"], "incremental-import-candidate")
            self.assertEqual(
                tuple(payload["batch"]),
                (
                    "approval_statement",
                    "batch_id",
                    "candidate_database_schema",
                    "manifest_sha256",
                    "preflight_sha256",
                ),
            )
            self.assertEqual(payload["batch"]["batch_id"], request.approval.batch_id)
            self.assertEqual(
                payload["counts"]["projected_after_count"],
                request.preflight_result.report.projected_after_count,
            )
            text = raw.decode("utf-8")
            for forbidden in (str(request.package_root), str(request.output_dir), tempfile.gettempdir()):
                self.assertNotIn(forbidden, text)
            for artifact in (
                artifacts.database,
                artifacts.manifest,
                artifacts.sha256sums,
                artifacts.rollback,
                *artifacts.images,
            ):
                self.assertEqual(artifact.sha256, _sha(artifact.path.read_bytes()))
                self.assertEqual(artifact.size_bytes, artifact.path.stat().st_size)

    def test_sums_and_rollback_are_exact_complete_nonrecursive_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request, _, artifacts = self._built(Path(directory))
            lines = artifacts.sha256sums.path.read_text(encoding="utf-8").splitlines(keepends=True)
            self.assertTrue(lines)
            self.assertTrue(all(line.endswith("\n") and line.count("  ") == 1 for line in lines))
            parsed = tuple((line[:64], line[66:-1]) for line in lines)
            self.assertEqual(tuple(path for _, path in parsed), tuple(sorted(path for _, path in parsed)))
            self.assertEqual(len({path for _, path in parsed}), len(parsed))
            self.assertNotIn(request.contract.sha256s_filename, {path for _, path in parsed})
            expected = {
                request.contract.database_filename,
                request.contract.manifest_filename,
                request.contract.rollback_filename,
                *(image.path.relative_to(request.output_dir).as_posix() for image in artifacts.images),
            }
            self.assertEqual({path for _, path in parsed}, expected)
            for digest, relative in parsed:
                self.assertRegex(digest, r"^[0-9a-f]{64}$")
                self.assertEqual(digest, _sha((request.output_dir / relative).read_bytes()))
            self.assertEqual(
                artifacts.sha256sums.path.read_bytes(),
                "".join(
                    f"{_sha((request.output_dir / relative).read_bytes())}  {relative}\n"
                    for relative in sorted(expected)
                ).encode("utf-8"),
            )
            rollback = json.loads(artifacts.rollback.path.read_bytes())
            self.assertEqual(
                set(rollback),
                {
                    "schema_version",
                    "action",
                    "batch_id",
                    "preflight_sha256",
                    "baseline",
                    "candidate_artifacts",
                },
            )
            self.assertEqual(rollback["schema_version"], "task9-v119-rollback-v1")
            self.assertEqual(rollback["action"], "delete_unpromoted_candidate_tree")
            self.assertEqual(rollback["batch_id"], request.approval.batch_id)
            self.assertEqual(
                rollback["preflight_sha256"], request.approval.preflight_sha256
            )
            self.assertEqual(
                rollback["baseline"],
                _expected_manifest(request, artifacts)["baseline"],
            )
            all_paths = tuple(sorted(expected | {request.contract.sha256s_filename}))
            self.assertEqual(tuple(rollback["candidate_artifacts"]), all_paths)
            self.assertEqual(
                artifacts.rollback.path.read_bytes(), _canonical_json_file(rollback)
            )

    def test_happy_verifier_returns_exact_ordered_sixteen_check_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request, config, _ = self._built(Path(directory))
            report = _call_verify(self, _verification_request(request), config)
            _assert_full_report(self, report, "PASS")
            self.assertTrue(all(check.passed for check in report.checks))

    def test_verifier_rejects_rebound_ready_authority(self) -> None:
        from dataclasses import replace

        with tempfile.TemporaryDirectory() as directory:
            request, config, _ = self._built(Path(directory))
            forged = _rebind_preflight_authority(
                request,
                replace(
                    request.preflight_result,
                    report=replace(
                        request.preflight_result.report,
                        ambiguous_splits=("NOT-A-REAL-CANDIDATE",),
                    ),
                ),
            )
            report = _call_verify(self, _verification_request(forged), config)
            _assert_full_report(self, report, "FAIL")
            self.assertFalse(_checks(report)["preflight_approval_binding"])

        with tempfile.TemporaryDirectory() as directory:
            request, config, _ = self._built(Path(directory))
            candidate = request.preflight_result.candidates[0]
            object.__setattr__(candidate, "translation_evidence", None)
            forged = _rebind_preflight_authority(request, request.preflight_result)
            before = _entry_snapshot(request.output_dir)
            with self.assertRaises(PipelineError):
                _call_verify(self, _verification_request(forged), config)
            self.assertEqual(_entry_snapshot(request.output_dir), before)

    def test_verifier_reconstructs_all_ready_report_derivations(self) -> None:
        from dataclasses import replace

        mutations = {
            "missing_answers": ("NOT-A-REAL-CANDIDATE",),
            "missing_explanations": ("NOT-A-REAL-CANDIDATE",),
            "incomplete_enrichments": ("NOT-A-REAL-CANDIDATE",),
        }
        for name, value in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                request, config, _ = self._built(Path(directory))
                forged = _rebind_preflight_authority(
                    request,
                    replace(
                        request.preflight_result,
                        report=replace(
                            request.preflight_result.report,
                            **{name: value},
                        ),
                    ),
                )
                report = _call_verify(self, _verification_request(forged), config)
                _assert_full_report(self, report, "FAIL")
                self.assertFalse(_checks(report)["preflight_approval_binding"])

    def test_verifier_rejects_candidate_database_as_its_own_baseline(self) -> None:
        from dataclasses import replace

        with tempfile.TemporaryDirectory() as directory:
            request, config, artifacts = self._built(Path(directory))
            self_baseline = replace(
                request.preflight_result.baseline_database,
                path=artifacts.database.path,
            )
            forged = replace(
                request,
                preflight_result=replace(
                    request.preflight_result,
                    baseline_database=self_baseline,
                ),
            )
            report = _call_verify(self, _verification_request(forged), config)
            _assert_full_report(self, report, "FAIL")
            self.assertFalse(_checks(report)["preflight_approval_binding"])
            self.assertFalse(_checks(report)["baseline_preservation"])

    def test_verifier_requires_exact_frozen_baseline_bytes(self) -> None:
        from dataclasses import replace

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, config, _ = self._built(root)
            forged_path = root / "forged-baseline.sqlite3"
            forged_path.write_bytes(
                request.preflight_result.baseline_database.path.read_bytes()
            )
            with sqlite3.connect(forged_path) as database:
                database.execute(
                    "UPDATE complete_questions_v2 "
                    "SET source_question_number='XXAMPLE-Q1' "
                    "WHERE source_question_number='EXAMPLE-Q1'"
                )
                database.commit()
            forged_ref = ArtifactRef(
                forged_path,
                _sha(forged_path.read_bytes()),
                forged_path.stat().st_size,
                "sqlite",
            )
            forged = _rebind_preflight_authority(
                request,
                replace(
                    request.preflight_result,
                    baseline_database=forged_ref,
                ),
            )
            report = _call_verify(self, _verification_request(forged), config)
            _assert_full_report(self, report, "FAIL")
            self.assertFalse(_checks(report)["preflight_approval_binding"])
            self.assertFalse(_checks(report)["baseline_preservation"])

    def test_verifier_rejects_one_digest_with_conflicting_extensions(self) -> None:
        first = b"same physical image"
        digest = _sha(first)
        records = [
            _raw_candidate(
                image_paths=["images/first.jpg"],
                image_roles=["question"],
            ),
            _raw_candidate(
                proposed_question_id="TASK9-NEW-002",
                source_question_number="2",
                source_section="Second canonical record",
                source_fragment_hash="2" * 64,
                question_text_original="Find y if y + 2 = 4.",
                image_paths=["images/second.png"],
                image_roles=["question"],
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, config = _ready_context(
                root,
                records=records,
                images={"images/first.jpg": first, "images/second.png": first},
            )

            def conflicting_plan(request_value, package_root):
                physical = {}
                bindings = []
                for candidate_order, candidate in enumerate(
                    request_value.preflight_result.candidates
                ):
                    source = candidate.image_paths[0]
                    extension = Path(source).suffix.lower()
                    destination = (
                        f"{request_value.contract.image_root}/{digest[:2]}/"
                        f"{digest}{extension}"
                    )
                    physical[destination] = {
                        "bytes": first,
                        "sha256": digest,
                        "size_bytes": len(first),
                    }
                    bindings.append(
                        {
                            "batch_id": request_value.approval.batch_id,
                            "proposed_question_id": candidate.proposed_question_id,
                            "candidate_order": candidate_order,
                            "image_order": 0,
                            "source_relative_path": source,
                            "candidate_relative_path": destination,
                            "sha256": digest,
                            "size_bytes": len(first),
                            "kind": "image",
                            "role": candidate.image_roles[0],
                        }
                    )
                return physical, tuple(bindings)

            passing = VerificationReport(
                "PASS",
                tuple(
                    __import__("joy_m2.models", fromlist=["VerificationCheck"])
                    .VerificationCheck(name, True, "PASS")
                    for name in CHECK_NAMES
                ),
            )
            with mock.patch(
                "joy_m2.ingest.writer._image_plan",
                side_effect=conflicting_plan,
            ), mock.patch(
                "joy_m2.ingest.writer.verify_v119_candidate",
                return_value=passing,
            ):
                _call_build(self, request, config)
            report = _call_verify(self, _verification_request(request), config)
            _assert_full_report(self, report, "FAIL")
            self.assertFalse(_checks(report)["image_projection"])

    def test_verifier_requires_image_evidence_kind_and_digest_binding(self) -> None:
        from dataclasses import replace

        with tempfile.TemporaryDirectory() as directory:
            request, config, _ = self._built(Path(directory))
            evidence = request.preflight_result.manifest.image_files[0]
            forged_evidence = replace(evidence, sha256="0" * 64)
            forged_manifest = replace(
                request.preflight_result.manifest,
                image_files=(forged_evidence,),
            )
            forged = _rebind_preflight_authority(
                request,
                replace(
                    request.preflight_result,
                    manifest=forged_manifest,
                ),
            )
            report = _call_verify(self, _verification_request(forged), config)
            _assert_full_report(self, report, "FAIL")
            self.assertFalse(_checks(report)["image_projection"])

        with tempfile.TemporaryDirectory() as directory:
            request, config, _ = self._built(Path(directory))
            evidence = request.preflight_result.manifest.image_files[0]
            object.__setattr__(evidence, "kind", "source")
            before = _entry_snapshot(request.output_dir)
            with self.assertRaises(PipelineError):
                _call_verify(self, _verification_request(request), config)
            self.assertEqual(_entry_snapshot(request.output_dir), before)

    def test_verifier_rejects_rebound_nul_image_source_path(self) -> None:
        from dataclasses import replace

        with tempfile.TemporaryDirectory() as directory:
            request, config, artifacts = self._built(Path(directory))
            source_relative = request.preflight_result.candidates[0].image_paths[0]
            nul_relative = "images/nul\x00.png"
            candidate = replace(
                request.preflight_result.candidates[0],
                image_paths=(nul_relative,),
            )
            evidence = replace(
                request.preflight_result.manifest.image_files[0],
                relative_path=nul_relative,
            )
            preflight = replace(
                request.preflight_result,
                manifest=replace(
                    request.preflight_result.manifest,
                    image_files=(evidence,),
                ),
                candidates=(candidate,),
                report=replace(
                    request.preflight_result.report,
                    readable_files=tuple(
                        nul_relative if path == source_relative else path
                        for path in request.preflight_result.report.readable_files
                    ),
                ),
            )
            forged = _rebind_preflight_authority(request, preflight)

            canonical_header = artifacts.database.path.read_bytes()[:100]
            with sqlite3.connect(artifacts.database.path) as database:
                database.execute(
                    "UPDATE task9_import_batches_v1 SET "
                    "preflight_sha256=?, manifest_sha256=?, approval_statement=?",
                    (
                        forged.approval.preflight_sha256,
                        forged.preflight_result.report.manifest_sha256,
                        forged.approval.statement,
                    ),
                )
                database.execute(
                    "UPDATE task9_import_candidates_v1 SET image_paths_json=?",
                    (json.dumps([nul_relative], separators=(",", ":")),),
                )
                database.execute(
                    "UPDATE task9_import_images_v1 SET source_relative_path=?",
                    (nul_relative,),
                )
                database.commit()
            database_bytes = bytearray(artifacts.database.path.read_bytes())
            database_bytes[:100] = canonical_header
            artifacts.database.path.write_bytes(database_bytes)

            rollback = json.loads(artifacts.rollback.path.read_bytes())
            rollback["preflight_sha256"] = forged.approval.preflight_sha256
            artifacts.rollback.path.write_bytes(_canonical_json_file(rollback))
            manifest = json.loads(artifacts.manifest.path.read_bytes())
            manifest["batch"]["preflight_sha256"] = forged.approval.preflight_sha256
            manifest["batch"]["manifest_sha256"] = (
                forged.preflight_result.report.manifest_sha256
            )
            manifest["batch"]["approval_statement"] = forged.approval.statement
            manifest["images"][0]["bindings"][0]["source_relative_path"] = (
                nul_relative
            )
            artifacts.manifest.path.write_bytes(_canonical_json_file(manifest))
            _refresh_manifest_artifacts_and_sums(request)

            before = _entry_snapshot(request.output_dir)
            report = _call_verify(self, _verification_request(forged), config)
            _assert_full_report(self, report, "FAIL")
            self.assertFalse(_checks(report)["image_projection"])
            self.assertEqual(_entry_snapshot(request.output_dir), before)

    def test_verifier_rejects_rebound_nul_nonimage_evidence_paths(self) -> None:
        from dataclasses import replace

        group_names = (
            "candidate_records",
            "source_files",
            "answer_files",
            "teacher_notes_files",
            "common_errors_files",
        )
        for group_name in group_names:
            with self.subTest(group=group_name), tempfile.TemporaryDirectory() as directory:
                request, config, _ = self._built(Path(directory))
                group = getattr(request.preflight_result.manifest, group_name)
                original_path = group[0].relative_path
                nul_path = original_path + "\x00"
                manifest = replace(
                    request.preflight_result.manifest,
                    **{
                        group_name: (
                            replace(group[0], relative_path=nul_path),
                            *group[1:],
                        )
                    },
                )
                preflight = replace(
                    request.preflight_result,
                    manifest=manifest,
                    report=replace(
                        request.preflight_result.report,
                        readable_files=tuple(
                            nul_path if path == original_path else path
                            for path in request.preflight_result.report.readable_files
                        ),
                    ),
                )
                forged = _rebind_preflight_authority(request, preflight)
                before = _entry_snapshot(request.output_dir)
                report = _call_verify(
                    self,
                    _verification_request(forged),
                    config,
                )
                _assert_full_report(self, report, "FAIL")
                self.assertFalse(_checks(report)["preflight_approval_binding"])
                self.assertEqual(_entry_snapshot(request.output_dir), before)

    def test_verifier_does_not_create_wal_or_shm_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request, config, artifacts = self._built(Path(directory))
            with sqlite3.connect(artifacts.database.path) as database:
                self.assertEqual(database.execute("PRAGMA journal_mode=WAL").fetchone(), ("wal",))
            _refresh_manifest_artifacts_and_sums(request)
            before = _entry_snapshot(request.output_dir)
            report = _call_verify(self, _verification_request(request), config)
            _assert_full_report(self, report, "FAIL")
            self.assertEqual(_entry_snapshot(request.output_dir), before)

    def test_manifest_syntax_is_exception_but_parsed_invalid_is_full_fail(self) -> None:
        for malformed in (b"{not-json", b"", b"\xff\xfe"):
            with self.subTest(malformed=malformed), tempfile.TemporaryDirectory() as directory:
                request, config, artifacts = self._built(Path(directory))
                artifacts.manifest.path.write_bytes(malformed)
                with self.assertRaises(InputFormatError):
                    _call_verify(self, _verification_request(request), config)
        with tempfile.TemporaryDirectory() as directory:
            request, config, artifacts = self._built(Path(directory))
            artifacts.manifest.path.write_bytes(b"{}\n")
            _rewrite_sums(request)
            before = _fingerprint(request.output_dir)
            report = _call_verify(self, _verification_request(request), config)
            _assert_full_report(self, report, "FAIL")
            self.assertEqual(_fingerprint(request.output_dir), before)

    def test_excessively_nested_manifest_is_input_format_error_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request, config, artifacts = self._built(Path(directory))
            artifacts.manifest.path.write_bytes(b"[" * 10_000 + b"]" * 10_000)
            before = _entry_snapshot(request.output_dir)
            try:
                _call_verify(self, _verification_request(request), config)
            except InputFormatError:
                pass
            except Exception as error:
                self.fail(
                    "deep JSON leaked an unapproved exception: "
                    f"{type(error).__name__}: {error}"
                )
            else:
                self.fail("deep JSON did not raise InputFormatError")
            self.assertEqual(_entry_snapshot(request.output_dir), before)

    def test_excessively_large_json_integer_is_input_format_error_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request, config, artifacts = self._built(Path(directory))
            artifacts.manifest.path.write_bytes(b"1" * 10_000)
            before = _entry_snapshot(request.output_dir)
            try:
                _call_verify(self, _verification_request(request), config)
            except InputFormatError:
                pass
            except Exception as error:
                self.fail(
                    "oversized JSON integer leaked an unapproved exception: "
                    f"{type(error).__name__}: {error}"
                )
            else:
                self.fail("oversized JSON integer did not raise InputFormatError")
            self.assertEqual(_entry_snapshot(request.output_dir), before)

    def test_excessively_nested_rollback_is_full_fail_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request, config, artifacts = self._built(Path(directory))
            artifacts.rollback.path.write_bytes(b"[" * 10_000 + b"]" * 10_000)
            _refresh_manifest_artifacts_and_sums(request)
            before = _entry_snapshot(request.output_dir)
            try:
                report = _call_verify(self, _verification_request(request), config)
            except Exception as error:
                self.fail(
                    "deep rollback JSON leaked an unapproved exception: "
                    f"{type(error).__name__}: {error}"
                )
            _assert_full_report(self, report, "FAIL")
            self.assertFalse(_checks(report)["rollback_contract"])
            self.assertEqual(_entry_snapshot(request.output_dir), before)

    def test_exact_but_uninitialized_verification_request_is_pipeline_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, config = _ready_context(root)
            malformed = object.__new__(V119VerificationRequest)
            before = _entry_snapshot(config.repo_root)
            try:
                _call_verify(self, malformed, config)
            except PipelineError:
                pass
            except Exception as error:
                self.fail(
                    "invalid exact request leaked an unapproved exception: "
                    f"{type(error).__name__}: {error}"
                )
            else:
                self.fail("invalid exact request was accepted")
            self.assertEqual(_entry_snapshot(config.repo_root), before)

    def test_verifier_rejects_non_path_baseline_locator_without_mutation(self) -> None:
        from dataclasses import replace

        with tempfile.TemporaryDirectory() as directory:
            request, config, _ = self._built(Path(directory))
            baseline = request.preflight_result.baseline_database
            forged_baseline = ArtifactRef(
                _NonPathLocator(),
                baseline.sha256,
                baseline.size_bytes,
                baseline.kind,
            )
            forged = _rebind_preflight_authority(
                request,
                replace(
                    request.preflight_result,
                    baseline_database=forged_baseline,
                ),
            )
            before = _entry_snapshot(request.output_dir)
            try:
                _call_verify(self, _verification_request(forged), config)
            except PipelineError:
                pass
            except Exception as error:
                self.fail(
                    "non-Path baseline locator leaked an unapproved exception: "
                    f"{type(error).__name__}: {error}"
                )
            else:
                self.fail("non-Path baseline locator was accepted")
            self.assertEqual(_entry_snapshot(request.output_dir), before)

    def test_verifier_maps_baseline_resolve_oserror_to_pipeline_error(self) -> None:
        from dataclasses import replace

        with tempfile.TemporaryDirectory() as directory:
            request, config, _ = self._built(Path(directory))
            baseline = request.preflight_result.baseline_database
            _SecondResolveRaisesPath.resolve_calls = 0
            forged_baseline = ArtifactRef(
                _SecondResolveRaisesPath(baseline.path),
                baseline.sha256,
                baseline.size_bytes,
                baseline.kind,
            )
            forged = _rebind_preflight_authority(
                request,
                replace(
                    request.preflight_result,
                    baseline_database=forged_baseline,
                ),
            )
            before = _entry_snapshot(request.output_dir)
            try:
                _call_verify(self, _verification_request(forged), config)
            except PipelineError:
                pass
            except Exception as error:
                self.fail(
                    "baseline resolve leaked an unapproved exception: "
                    f"{type(error).__name__}: {error}"
                )
            else:
                self.fail("failing baseline locator was accepted")
            self.assertEqual(_entry_snapshot(request.output_dir), before)

    def test_candidate_and_manifest_locator_exception_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, config = _ready_context(root)
            with self.assertRaises(InputMissingError):
                _call_verify(self, _verification_request(request), config)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, config = _ready_context(root)
            request.output_dir.parent.mkdir(parents=True)
            request.output_dir.write_bytes(b"not a directory")
            with self.assertRaises(InputFormatError):
                _call_verify(self, _verification_request(request), config)
        with tempfile.TemporaryDirectory() as directory:
            request, config, artifacts = self._built(Path(directory))
            artifacts.manifest.path.unlink()
            with self.assertRaises(InputMissingError):
                _call_verify(self, _verification_request(request), config)

    def test_candidate_symlink_loop_is_pipeline_error_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request, config = _ready_context(Path(directory))
            verification_request = _verification_request(request)
            config.staging_root.mkdir(parents=True)
            request.output_dir.symlink_to(
                request.output_dir.name,
                target_is_directory=True,
            )
            before = _entry_snapshot(config.repo_root)
            try:
                _call_verify(self, verification_request, config)
            except PipelineError:
                pass
            except Exception as error:
                self.fail(
                    "symlink-loop candidate leaked an unapproved exception: "
                    f"{type(error).__name__}: {error}"
                )
            else:
                self.fail("symlink-loop candidate was accepted")
            self.assertEqual(_entry_snapshot(config.repo_root), before)

    def test_all_parsed_manifest_shape_and_type_errors_are_full_fail(self) -> None:
        mutations = {
            "non_mapping": [],
            "missing_key": lambda value: value.pop("counts"),
            "extra_key": lambda value: value.__setitem__("extra", 1),
            "wrong_type": lambda value: value["counts"].__setitem__("before_count", True),
            "malformed_digest": lambda value: value["database"].__setitem__("sha256", "bad"),
            "wrong_identity": lambda value: value.__setitem__("release_version", "V9.99"),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                request, config, artifacts = self._built(Path(directory))
                payload = json.loads(artifacts.manifest.path.read_bytes())
                if callable(mutation):
                    mutation(payload)
                else:
                    payload = mutation
                artifacts.manifest.path.write_bytes(
                    json.dumps(
                        payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                    + b"\n"
                )
                _rewrite_sums(request)
                before = _fingerprint(request.output_dir)
                report = _call_verify(self, _verification_request(request), config)
                _assert_full_report(self, report, "FAIL")
                self.assertFalse(_checks(report)["manifest_contract"])
                self.assertEqual(_fingerprint(request.output_dir), before)

    def test_sums_exception_matrix_and_artifact_failures_do_not_mutate(self) -> None:
        cases = ("missing_sums", "malformed_sums", "missing_artifact", "extra", "tampered")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                request, config, artifacts = self._built(Path(directory))
                if case == "missing_sums":
                    artifacts.sha256sums.path.unlink()
                elif case == "malformed_sums":
                    artifacts.sha256sums.path.write_text("bad\n", encoding="utf-8")
                elif case == "missing_artifact":
                    artifacts.rollback.path.unlink()
                elif case == "extra":
                    (request.output_dir / "rogue.txt").write_bytes(b"rogue")
                else:
                    artifacts.rollback.path.write_bytes(b"{}\n")
                before = _fingerprint(request.output_dir)
                if case == "malformed_sums":
                    with self.assertRaises(InputFormatError):
                        _call_verify(self, _verification_request(request), config)
                else:
                    report = _call_verify(self, _verification_request(request), config)
                    _assert_full_report(self, report, "FAIL")
                    if case == "extra":
                        self.assertFalse(_checks(report)["sha256sums_closure"])
                        self.assertFalse(_checks(report)["rollback_contract"])
                self.assertEqual(_fingerprint(request.output_dir), before)

    def test_manifest_sums_and_rollback_symlinks_are_rejected_without_mutation(self) -> None:
        for artifact_name in ("manifest", "sums", "rollback"):
            with self.subTest(artifact=artifact_name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                request, config, artifacts = self._built(root)
                paths = {
                    "manifest": artifacts.manifest.path,
                    "sums": artifacts.sha256sums.path,
                    "rollback": artifacts.rollback.path,
                }
                artifact_path = paths[artifact_name]
                external = root / f"external-{artifact_name}.txt"
                external.write_bytes(artifact_path.read_bytes())
                artifact_path.unlink()
                artifact_path.symlink_to(external)
                before_candidate = _entry_snapshot(request.output_dir)
                before_external = external.read_bytes()
                if artifact_name in {"manifest", "sums"}:
                    with self.assertRaises(InputFormatError):
                        _call_verify(self, _verification_request(request), config)
                else:
                    report = _call_verify(
                        self,
                        _verification_request(request),
                        config,
                    )
                    _assert_full_report(self, report, "FAIL")
                    self.assertFalse(_checks(report)["rollback_contract"])
                self.assertEqual(
                    _entry_snapshot(request.output_dir),
                    before_candidate,
                )
                self.assertEqual(external.read_bytes(), before_external)

    def test_image_projection_short_circuits_on_symlinked_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, config, _ = self._built(root)
            image_root = request.output_dir / request.contract.image_root
            outside = root / "outside-image-tree"
            image_root.rename(outside)
            image_root.symlink_to(outside, target_is_directory=True)
            candidate_before = _entry_snapshot(request.output_dir)
            outside_before = _entry_snapshot(outside)
            outside_reads: list[str] = []
            real_sha256_file = verifier_module.sha256_file

            def guarded_sha256_file(path: Path) -> str:
                resolved = path.resolve(strict=True)
                if not resolved.is_relative_to(request.output_dir.resolve(strict=True)):
                    outside_reads.append(resolved.as_posix())
                return real_sha256_file(path)

            with mock.patch(
                "joy_m2.ingest.writer_verification.sha256_file",
                side_effect=guarded_sha256_file,
            ):
                report = _call_verify(
                    self,
                    _verification_request(request),
                    config,
                )
            _assert_full_report(self, report, "FAIL")
            self.assertFalse(_checks(report)["filesystem_closure"])
            self.assertFalse(_checks(report)["sha256sums_closure"])
            self.assertFalse(_checks(report)["image_projection"])
            self.assertEqual(outside_reads, [])
            self.assertEqual(_entry_snapshot(request.output_dir), candidate_before)
            self.assertEqual(_entry_snapshot(outside), outside_before)

    def test_invalid_utf8_sums_is_input_format_error(self) -> None:
        malformed_values = (
            b"\xff\xfe",
            b"bad\n",
            b"0" * 64 + b" *file\n",
            b"0" * 64 + b"  ../escape\n",
            b"0" * 64 + b"  file\n\n",
            b"0" * 64 + b"   file\n",
            b"0" * 64 + b"  .\n",
            b"0" * 64 + b"  nul\x00path\n",
        )
        for value in malformed_values:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                request, config, artifacts = self._built(Path(directory))
                artifacts.sha256sums.path.write_bytes(value)
                before = _fingerprint(request.output_dir)
                with self.assertRaises(InputFormatError):
                    _call_verify(self, _verification_request(request), config)
                self.assertEqual(_fingerprint(request.output_dir), before)

    def test_corrupt_sqlite_and_wrong_manifest_artifact_ref_are_structured_fail(self) -> None:
        for case in ("sqlite", "artifact_ref"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                request, config, artifacts = self._built(Path(directory))
                if case == "sqlite":
                    artifacts.database.path.write_bytes(b"not sqlite")
                    _refresh_manifest_artifacts_and_sums(request)
                else:
                    payload = json.loads(artifacts.manifest.path.read_bytes())
                    payload["database"]["kind"] = "json"
                    artifacts.manifest.path.write_bytes(
                        json.dumps(
                            payload,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                        + b"\n"
                    )
                    _rewrite_sums(request)
                report = _call_verify(self, _verification_request(request), config)
                _assert_full_report(self, report, "FAIL")

    def test_sqlite_file_envelope_rejects_trailing_bytes_and_header_version_tamper(self) -> None:
        for case in ("trailing_bytes", "header_version"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                request, config, artifacts = self._built(Path(directory))
                database_bytes = bytearray(artifacts.database.path.read_bytes())
                if case == "trailing_bytes":
                    database_bytes.extend(b"non-canonical trailing bytes")
                else:
                    database_bytes[96:100] = (0x12345678).to_bytes(4, "big")
                artifacts.database.path.write_bytes(database_bytes)
                _refresh_manifest_artifacts_and_sums(request)
                before = _entry_snapshot(request.output_dir)
                report = _call_verify(self, _verification_request(request), config)
                _assert_full_report(self, report, "FAIL")
                self.assertFalse(_checks(report)["sqlite_readability"])
                self.assertEqual(_entry_snapshot(request.output_dir), before)

    def test_sqlite_frozen_header_identity_rejects_repage_and_application_id(self) -> None:
        for case in ("page_size", "application_id"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                request, config, artifacts = self._built(Path(directory))
                with sqlite3.connect(artifacts.database.path) as database:
                    if case == "page_size":
                        database.execute("PRAGMA page_size=8192")
                        database.execute("VACUUM")
                    else:
                        database.execute("PRAGMA application_id=1")
                    database.commit()
                database_bytes = bytearray(artifacts.database.path.read_bytes())
                database_bytes[96:100] = (3_050_004).to_bytes(4, "big")
                artifacts.database.path.write_bytes(database_bytes)
                _refresh_manifest_artifacts_and_sums(request)
                before = _entry_snapshot(request.output_dir)
                report = _call_verify(self, _verification_request(request), config)
                _assert_full_report(self, report, "FAIL")
                self.assertFalse(_checks(report)["sqlite_readability"])
                self.assertEqual(_entry_snapshot(request.output_dir), before)

    def test_sqlite_header_rejects_all_noncanonical_persistent_fields(self) -> None:
        cases = (
            "auto_vacuum",
            "default_cache_size",
            "version_valid_for",
            "schema_cookie",
            "change_counter",
        )
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                request, config, artifacts = self._built(Path(directory))
                if case in {"auto_vacuum", "default_cache_size"}:
                    with sqlite3.connect(artifacts.database.path) as database:
                        if case == "auto_vacuum":
                            database.execute("PRAGMA auto_vacuum=FULL")
                            database.execute("VACUUM")
                        else:
                            database.execute("PRAGMA default_cache_size=123")
                        database.commit()
                database_bytes = bytearray(artifacts.database.path.read_bytes())
                if case == "version_valid_for":
                    database_bytes[92:96] = (1).to_bytes(4, "big")
                elif case == "schema_cookie":
                    schema_cookie = int.from_bytes(database_bytes[40:44], "big")
                    database_bytes[40:44] = (schema_cookie + 1).to_bytes(4, "big")
                elif case == "change_counter":
                    change_counter = int.from_bytes(database_bytes[24:28], "big") + 1
                    encoded = change_counter.to_bytes(4, "big")
                    database_bytes[24:28] = encoded
                    database_bytes[92:96] = encoded
                database_bytes[96:100] = (3_050_004).to_bytes(4, "big")
                artifacts.database.path.write_bytes(database_bytes)
                _refresh_manifest_artifacts_and_sums(request)
                before = _entry_snapshot(request.output_dir)
                report = _call_verify(self, _verification_request(request), config)
                _assert_full_report(self, report, "FAIL")
                self.assertFalse(_checks(report)["sqlite_readability"])
                self.assertEqual(_entry_snapshot(request.output_dir), before)

    def test_sqlite_schema_foreign_key_and_publication_failures_are_structured(self) -> None:
        for case in ("schema", "foreign_key", "publication"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                request, config, artifacts = self._built(Path(directory))
                with sqlite3.connect(artifacts.database.path) as database:
                    if case == "schema":
                        database.execute("DROP VIEW task9_candidate_questions_v1")
                    elif case == "foreign_key":
                        database.execute("PRAGMA foreign_keys=OFF")
                        database.execute(
                            "INSERT INTO task9_import_images_v1 VALUES (?,?,?,?,?,?,?,?,?)",
                            (
                                request.approval.batch_id,
                                "UNKNOWN",
                                0,
                                "images/question.png",
                                "images/sha256/00/" + "0" * 64 + ".png",
                                "0" * 64,
                                0,
                                "image",
                                "question",
                            ),
                        )
                    else:
                        database.execute("PRAGMA ignore_check_constraints=ON")
                        database.execute(
                            "UPDATE task9_import_candidates_v1 SET selectable=1"
                        )
                    database.commit()
                _refresh_manifest_artifacts_and_sums(request)
                before = _fingerprint(request.output_dir)
                report = _call_verify(self, _verification_request(request), config)
                _assert_full_report(self, report, "FAIL")
                expected_check = {
                    "schema": "sqlite_schema",
                    "foreign_key": "sqlite_foreign_keys",
                    "publication": "publication_boundary",
                }[case]
                self.assertFalse(_checks(report)[expected_check])
                self.assertEqual(_fingerprint(request.output_dir), before)

    def test_rollback_image_projection_and_sqlite_semantic_checks_are_independent(self) -> None:
        cases = (
            "rollback",
            "image_projection",
            "sqlite_integrity",
            "sqlite_projection",
            "baseline_preservation",
            "count_closure",
        )
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                request, config, artifacts = self._built(Path(directory))
                if case == "rollback":
                    rollback = json.loads(artifacts.rollback.path.read_bytes())
                    rollback["action"] = "unsafe"
                    artifacts.rollback.path.write_bytes(_canonical_json_file(rollback))
                elif case == "image_projection":
                    artifacts.images[0].path.write_bytes(b"different image bytes")
                elif case == "sqlite_integrity":
                    artifacts.database.path.write_bytes(
                        artifacts.database.path.read_bytes()[:4096]
                    )
                else:
                    with sqlite3.connect(artifacts.database.path) as database:
                        if case == "sqlite_projection":
                            database.execute(
                                "UPDATE task9_import_candidates_v1 "
                                "SET question_text_original='forged'"
                            )
                        elif case == "baseline_preservation":
                            database.execute(
                                "UPDATE release_metadata_v2 SET value='forged' "
                                "WHERE key='release_version'"
                            )
                        else:
                            database.execute("DELETE FROM task9_import_candidates_v1")
                        database.commit()
                _refresh_manifest_artifacts_and_sums(request)
                before = _fingerprint(request.output_dir)
                report = _call_verify(self, _verification_request(request), config)
                _assert_full_report(self, report, "FAIL")
                expected = {
                    "rollback": "rollback_contract",
                    "image_projection": "image_projection",
                    "sqlite_integrity": "sqlite_integrity",
                    "sqlite_projection": "sqlite_projection",
                    "baseline_preservation": "baseline_preservation",
                    "count_closure": "count_closure",
                }[case]
                self.assertFalse(_checks(report)[expected])
                self.assertEqual(_fingerprint(request.output_dir), before)


if __name__ == "__main__":
    unittest.main()
