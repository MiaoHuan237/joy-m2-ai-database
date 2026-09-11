"""Phase B behavior contract for the Task 9C V1.19 candidate writer."""

from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

WORKTREE = Path(__file__).resolve().parents[2]
SRC = WORKTREE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import (
    ImportApprovalError,
    InputFormatError,
    OutputConflictError,
    PipelineError,
)
import joy_m2.ingest.writer as writer_module
from joy_m2.ingest.preflight import preflight_import
from joy_m2.ingest.models import ImportIssue
from joy_m2.ingest.writer import build_v119_candidate
from joy_m2.ingest.writer_models import (
    ImportApproval,
    V119WriteRequest,
    V119WriterContract,
)
from joy_m2.models import ArtifactRef, VerificationCheck, VerificationReport

from tests.integration.test_ingest_preflight import (
    _baseline_ref,
    _package,
    _raw_candidate,
)


BASELINE = WORKTREE / "releases" / "V1.18" / "Joy_M2_Complete_Question_DB_V1_18.sqlite3"
BASELINE_SHA256 = "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7"
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
CANDIDATE_COLUMNS = (
    "batch_id",
    "candidate_order",
    "proposed_question_id",
    "source_id",
    "source_question_number",
    "source_section",
    "source_fragment_hash",
    "normalized_text_sha256",
    "question_text_original",
    "question_text_zh",
    "translation_status",
    "translation_evidence",
    "solution_original",
    "solution_verified",
    "answer_status",
    "explanation_text",
    "explanation_status",
    "explanation_evidence",
    "image_paths_json",
    "image_sha256s_json",
    "image_roles_json",
    "primary_type",
    "tags_json",
    "tag_status",
    "difficulty_level",
    "difficulty_status",
    "enrichment_status",
    "candidate_image_paths_json",
    "record_status",
    "selectable",
)
BATCH_COLUMNS = (
    "batch_id",
    "target_release_version",
    "candidate_database_schema",
    "preflight_sha256",
    "manifest_sha256",
    "approval_statement",
    "baseline_release_version",
    "baseline_database_sha256",
    "baseline_question_count",
    "candidate_count",
    "projected_question_count",
    "record_status",
)


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


def _contract() -> V119WriterContract:
    return V119WriterContract(
        "V1.19",
        "task9-v119-candidate-manifest-v1",
        "task9-v119-candidate-v1",
        119,
        "Joy_M2_V1.19_candidate.sqlite3",
        "candidate_manifest.json",
        "SHA256SUMS",
        "rollback.json",
        "images/sha256",
        BASELINE_TABLES,
        CANDIDATE_TABLES,
        CANDIDATE_VIEWS,
    )


def _snapshot(root: Path) -> tuple[tuple[str, str, str], ...]:
    if not root.exists():
        return ()
    entries = []
    for item in sorted(root.rglob("*")):
        relative = item.relative_to(root).as_posix()
        if item.is_symlink():
            entries.append((relative, "symlink", os.readlink(item)))
        elif item.is_dir():
            entries.append((relative, "directory", ""))
        elif item.is_file():
            entries.append((relative, "file", hashlib.sha256(item.read_bytes()).hexdigest()))
        else:
            entries.append((relative, "other", ""))
    return tuple(entries)


def _tree_bytes(root: Path) -> tuple[tuple[str, bytes], ...]:
    return tuple(
        (item.relative_to(root).as_posix(), item.read_bytes())
        for item in sorted(root.rglob("*"))
        if item.is_file()
    )


def _database_snapshot(path: Path, names: tuple[str, ...]) -> tuple[object, ...]:
    with sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True) as database:
        schema = tuple(
            database.execute(
                "SELECT type,name,tbl_name,sql FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
            )
        )
        rows = tuple((name, tuple(database.execute(f'SELECT * FROM "{name}"'))) for name in names)
    return schema, rows


def _rebind_preflight_authority(
    request: V119WriteRequest,
    preflight,
    *,
    forge_approval: bool = False,
) -> V119WriteRequest:
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
    values = (
        preflight.manifest.batch_id,
        preflight_sha256,
        "V1.19",
        f"USER APPROVED IMPORT BATCH {preflight.manifest.batch_id} "
        f"{preflight_sha256} V1.19",
    )
    if forge_approval:
        approval = object.__new__(ImportApproval)
        for name, value in zip(
            ("batch_id", "preflight_sha256", "target_release_version", "statement"),
            values,
            strict=True,
        ):
            object.__setattr__(approval, name, value)
    else:
        approval = ImportApproval(*values)
    return replace(request, preflight_result=preflight, approval=approval)


class _WriterRedCase(unittest.TestCase):
    def setUp(self) -> None:
        self.worktree_data = _snapshot(WORKTREE / "data" / "staging")
        self.worktree_releases = _snapshot(WORKTREE / "releases")

    def tearDown(self) -> None:
        self.assertEqual(_snapshot(WORKTREE / "data" / "staging"), self.worktree_data)
        self.assertEqual(_snapshot(WORKTREE / "releases"), self.worktree_releases)
        self.assertFalse((WORKTREE / "releases" / "V1.19").exists())

    def _ready_request(
        self,
        directory: Path,
        *,
        record: dict[str, object] | None = None,
        records: list[dict[str, object]] | None = None,
        images: dict[str, bytes] | None = None,
    ) -> tuple[V119WriteRequest, PipelineConfig]:
        package_root = directory / "package"
        package_root.mkdir()
        if record is not None and records is not None:
            raise AssertionError("use record or records, not both")
        selected = records if records is not None else ([record] if record is not None else None)
        groups = None if selected is None else (("records/candidates.json", selected),)
        manifest = _package(package_root, record_groups=groups, images=images)
        preflight = preflight_import(manifest, package_root, _baseline_ref())
        self.assertEqual(preflight.report.status, "READY FOR USER IMPORT APPROVAL")
        approval = ImportApproval(
            preflight.manifest.batch_id,
            preflight.report.preflight_sha256,
            "V1.19",
            f"USER APPROVED IMPORT BATCH {preflight.manifest.batch_id} "
            f"{preflight.report.preflight_sha256} V1.19",
        )
        config = PipelineConfig(directory / "temporary-repository")
        output = config.staging_root / "candidate-v119"
        return V119WriteRequest(preflight, package_root, approval, output, _contract()), config

    def _build(self, request: V119WriteRequest, config: PipelineConfig):
        try:
            return build_v119_candidate(request, config)
        except NotImplementedError as error:
            self.fail(f"Phase B writer behavior remains absent: {error}")


class V119DatabaseProjectionRedTests(_WriterRedCase):
    def test_candidate_database_has_exact_additive_projection_and_preserves_v118(self) -> None:
        """Production change that would make this fail: exact candidate projection."""
        shared = b"shared jpeg image"
        unique = b"unique png image"
        first = _raw_candidate(
            image_paths=["images/shared.JPEG"],
            image_roles=["question"],
            tags=["过指定点的切线", "已知切点求切线"],
            tag_status="source_provided",
            primary_type="切线与法线",
        )
        second = _raw_candidate(
            proposed_question_id="TASK9-NEW-002",
            source_question_number="2",
            source_section="Second canonical record",
            source_fragment_hash="2" * 64,
            question_text_original="Find y if y + 2 = 4.",
            image_paths=["images/shared.JPEG", "images/unique.png"],
            image_roles=["shared", "solution"],
            tags=["过指定点的切线"],
            tag_status="source_provided",
            primary_type="极值与曲线性质",
            difficulty_level=None,
            difficulty_status="missing",
        )
        baseline_schema, _ = _database_snapshot(BASELINE, ())
        baseline_data_names = tuple(
            row[1] for row in baseline_schema if row[0] in {"table", "view"}
        )
        baseline_schema, baseline_rows = _database_snapshot(BASELINE, baseline_data_names)
        baseline_before = hashlib.sha256(BASELINE.read_bytes()).hexdigest()
        self.assertEqual(baseline_before, BASELINE_SHA256)
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(
                Path(temporary),
                records=[first, second],
                images={"images/shared.JPEG": shared, "images/unique.png": unique},
            )
            artifacts = self._build(request, config)
            with sqlite3.connect(artifacts.database.path) as database:
                self.assertEqual(database.execute("PRAGMA user_version").fetchone()[0], 119)
                self.assertEqual(database.execute("PRAGMA integrity_check").fetchone(), ("ok",))
                self.assertEqual(database.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(
                    tuple(row[1] for row in database.execute("PRAGMA table_info(task9_import_batches_v1)")),
                    BATCH_COLUMNS,
                )
                self.assertEqual(
                    tuple(row[1] for row in database.execute("PRAGMA table_info(task9_import_candidates_v1)")),
                    CANDIDATE_COLUMNS,
                )
                batch = database.execute(
                    f"SELECT {','.join(BATCH_COLUMNS)} FROM task9_import_batches_v1"
                ).fetchone()
                report = request.preflight_result.report
                self.assertEqual(
                    batch,
                    (
                        request.approval.batch_id,
                        "V1.19",
                        "task9-v119-candidate-v1",
                        report.preflight_sha256,
                        report.manifest_sha256,
                        request.approval.statement,
                        "V1.18",
                        BASELINE_SHA256,
                        497,
                        2,
                        499,
                        "candidate",
                    ),
                )
                destination_by_digest = {
                    hashlib.sha256(shared).hexdigest(): (
                        "images/sha256/"
                        f"{hashlib.sha256(shared).hexdigest()[:2]}/"
                        f"{hashlib.sha256(shared).hexdigest()}.jpg"
                    ),
                    hashlib.sha256(unique).hexdigest(): (
                        "images/sha256/"
                        f"{hashlib.sha256(unique).hexdigest()[:2]}/"
                        f"{hashlib.sha256(unique).hexdigest()}.png"
                    ),
                }

                def expected_candidate(candidate, order):
                    values = tuple(asdict(candidate)[field] for field in asdict(candidate))
                    projected = []
                    for name, value in zip(asdict(candidate), values, strict=True):
                        projected.append(
                            json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                            if name in {"image_paths", "image_sha256s", "image_roles", "tags"}
                            else value
                        )
                    return (
                        request.approval.batch_id,
                        order,
                        *projected,
                        json.dumps(
                            [destination_by_digest[digest] for digest in candidate.image_sha256s],
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                        "candidate",
                        0,
                    )

                expected_candidates = tuple(
                    expected_candidate(candidate, order)
                    for order, candidate in enumerate(request.preflight_result.candidates)
                )
                self.assertEqual(
                    tuple(database.execute(
                        f"SELECT {','.join(CANDIDATE_COLUMNS)} "
                        "FROM task9_import_candidates_v1 ORDER BY candidate_order"
                    )),
                    expected_candidates,
                )
                expected_images = tuple(
                    (
                        request.approval.batch_id,
                        candidate.proposed_question_id,
                        image_order,
                        source_path,
                        destination_by_digest[digest],
                        digest,
                        len(shared if source_path.endswith("JPEG") else unique),
                        "image",
                        role,
                    )
                    for candidate in request.preflight_result.candidates
                    for image_order, (source_path, digest, role) in enumerate(
                        zip(
                            candidate.image_paths,
                            candidate.image_sha256s,
                            candidate.image_roles,
                            strict=True,
                        )
                    )
                )
                self.assertEqual(
                    tuple(database.execute(
                        "SELECT * FROM task9_import_images_v1 "
                        "ORDER BY proposed_question_id,image_order"
                    )),
                    expected_images,
                )
                self.assertEqual(
                    tuple(database.execute(
                        "SELECT taxonomy_kind,value,sort_order "
                        "FROM task9_import_taxonomy_v1 ORDER BY taxonomy_kind,sort_order"
                    )),
                    (
                        ("primary_type", "切线与法线", 1),
                        ("primary_type", "极值与曲线性质", 2),
                        ("tag", "已知切点求切线", 1),
                        ("tag", "过指定点的切线", 2),
                    ),
                )
                self.assertEqual(
                    database.execute("SELECT COUNT(*) FROM complete_questions_v2").fetchone(),
                    (497,),
                )
                self.assertEqual(
                    database.execute("SELECT COUNT(*) FROM task9_candidate_questions_v1").fetchone(),
                    (2,),
                )
                self.assertEqual(
                    database.execute(
                        "SELECT COUNT(*) FROM task9_import_candidates_v1 "
                        "WHERE record_status!='candidate' OR selectable!=0"
                    ).fetchone(),
                    (0,),
                )
                for candidate in request.preflight_result.candidates:
                    self.assertEqual(
                        database.execute(
                            "SELECT COUNT(*) FROM complete_questions_v2 WHERE question_id=?",
                            (candidate.proposed_question_id,),
                        ).fetchone(),
                        (0,),
                    )
                    self.assertEqual(
                        database.execute(
                            "SELECT COUNT(*) FROM selectable_complete_questions_v2 WHERE question_id=?",
                            (candidate.proposed_question_id,),
                        ).fetchone(),
                        (0,),
                    )
            candidate_schema, candidate_rows = _database_snapshot(
                artifacts.database.path, baseline_data_names
            )
            baseline_schema_by_name = {row[1]: row for row in baseline_schema}
            candidate_schema_by_name = {row[1]: row for row in candidate_schema}
            self.assertEqual(
                {name: candidate_schema_by_name[name] for name in baseline_schema_by_name},
                baseline_schema_by_name,
            )
            self.assertEqual(
                set(candidate_schema_by_name) - set(baseline_schema_by_name),
                set(CANDIDATE_TABLES + CANDIDATE_VIEWS),
            )
            self.assertEqual(candidate_rows, baseline_rows)
        self.assertEqual(hashlib.sha256(BASELINE.read_bytes()).hexdigest(), baseline_before)


class V119BuilderBoundaryRedTests(_WriterRedCase):
    def test_exact_but_uninitialized_write_request_is_pipeline_error(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = PipelineConfig(root / "temporary-repository")
            malformed = object.__new__(V119WriteRequest)
            before = _snapshot(config.repo_root)
            try:
                self._build(malformed, config)
            except PipelineError:
                pass
            except Exception as error:
                self.fail(
                    "invalid exact write request leaked an unapproved exception: "
                    f"{type(error).__name__}: {error}"
                )
            else:
                self.fail("invalid exact write request was accepted")
            self.assertEqual(_snapshot(config.repo_root), before)

    def test_exact_but_uninitialized_writer_contract_is_pipeline_error(self) -> None:
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            object.__setattr__(
                request,
                "contract",
                object.__new__(V119WriterContract),
            )
            before = _snapshot(config.repo_root)
            try:
                self._build(request, config)
            except PipelineError:
                pass
            except Exception as error:
                self.fail(
                    "invalid exact writer contract leaked an unapproved exception: "
                    f"{type(error).__name__}: {error}"
                )
            else:
                self.fail("invalid exact writer contract was accepted")
            self.assertEqual(_snapshot(config.repo_root), before)

    def test_builder_rejects_non_path_baseline_locator_without_mutation(self) -> None:
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
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
            before = _snapshot(config.repo_root)
            try:
                self._build(forged, config)
            except PipelineError:
                pass
            except Exception as error:
                self.fail(
                    "non-Path baseline locator leaked an unapproved exception: "
                    f"{type(error).__name__}: {error}"
                )
            else:
                self.fail("non-Path baseline locator was accepted")
            self.assertEqual(_snapshot(config.repo_root), before)

    def test_builder_maps_baseline_resolve_oserror_to_pipeline_error(self) -> None:
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
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
            before = _snapshot(config.repo_root)
            try:
                self._build(forged, config)
            except PipelineError:
                pass
            except Exception as error:
                self.fail(
                    "baseline resolve leaked an unapproved exception: "
                    f"{type(error).__name__}: {error}"
                )
            else:
                self.fail("failing baseline locator was accepted")
            self.assertEqual(_snapshot(config.repo_root), before)

    def test_builder_rejects_rebound_nul_image_path_without_output(self) -> None:
        with TemporaryDirectory() as temporary:
            record = _raw_candidate(
                image_paths=["images/question.png"],
                image_roles=["question"],
            )
            request, config = self._ready_request(
                Path(temporary),
                record=record,
                images={"images/question.png": b"question image bytes"},
            )
            source_relative = "images/question.png"
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
            before = _snapshot(config.repo_root)
            try:
                self._build(forged, config)
            except InputFormatError:
                pass
            except Exception as error:
                self.fail(
                    "NUL image path leaked an unapproved exception: "
                    f"{type(error).__name__}: {error}"
                )
            else:
                self.fail("NUL image path was accepted")
            self.assertEqual(_snapshot(config.repo_root), before)

    def test_builder_rejects_rebound_nul_nonimage_evidence_paths(self) -> None:
        group_names = (
            "candidate_records",
            "source_files",
            "answer_files",
            "teacher_notes_files",
            "common_errors_files",
        )
        for group_name in group_names:
            with self.subTest(group=group_name), TemporaryDirectory() as temporary:
                request, config = self._ready_request(Path(temporary))
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
                before = _snapshot(config.repo_root)
                with self.assertRaises(InputFormatError):
                    self._build(forged, config)
                self.assertEqual(_snapshot(config.repo_root), before)

    def test_builder_symlink_loop_locator_is_pipeline_error_without_mutation(self) -> None:
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            config.staging_root.mkdir(parents=True)
            request.output_dir.symlink_to(
                request.output_dir.name,
                target_is_directory=True,
            )
            before = _snapshot(config.repo_root)
            try:
                self._build(request, config)
            except PipelineError:
                pass
            except Exception as error:
                self.fail(
                    "symlink-loop output leaked an unapproved exception: "
                    f"{type(error).__name__}: {error}"
                )
            else:
                self.fail("symlink-loop output was accepted")
            self.assertEqual(_snapshot(config.repo_root), before)

    def test_builder_requires_ready_digest_bound_approval_and_frozen_baseline(self) -> None:
        """Production change that would make this fail: exhaustive entry gates."""
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            blocked_report = replace(
                request.preflight_result.report,
                status="BLOCKED — IMPORT PREFLIGHT FAILED",
            )
            blocked = replace(
                request,
                preflight_result=replace(request.preflight_result, report=blocked_report),
            )
            with self.assertRaises(ImportApprovalError):
                self._build(blocked, config)

            forged_report = replace(
                request.preflight_result.report,
                preflight_sha256="0" * 64,
            )
            forged_approval = ImportApproval(
                request.approval.batch_id,
                "0" * 64,
                "V1.19",
                f"USER APPROVED IMPORT BATCH {request.approval.batch_id} "
                f"{'0' * 64} V1.19",
            )
            forged = replace(
                request,
                preflight_result=replace(request.preflight_result, report=forged_report),
                approval=forged_approval,
            )
            with self.assertRaises(ImportApprovalError):
                self._build(forged, config)

            forged_manifest_report = replace(
                request.preflight_result.report,
                manifest_sha256="0" * 64,
            )
            forged_manifest = replace(
                request,
                preflight_result=replace(
                    request.preflight_result,
                    report=forged_manifest_report,
                ),
            )
            with self.assertRaises(ImportApprovalError):
                self._build(forged_manifest, config)

            closure_cases = (
                replace(
                    request.preflight_result,
                    report=replace(
                        request.preflight_result.report,
                        detected_count=2,
                        new_candidate_count=2,
                        projected_after_count=499,
                    ),
                ),
                replace(
                    request.preflight_result,
                    report=replace(
                        request.preflight_result.report,
                        blocking_errors=("missing_image",),
                    ),
                ),
                replace(
                    request.preflight_result,
                    report=replace(
                        request.preflight_result.report,
                        proposed_ids=(
                            request.preflight_result.candidates[0].proposed_question_id,
                            request.preflight_result.candidates[0].proposed_question_id,
                        ),
                    ),
                ),
                replace(
                    request.preflight_result,
                    issues=(
                        ImportIssue(
                            "missing_image",
                            "blocking",
                            request.preflight_result.candidates[0].proposed_question_id,
                            "image_paths",
                            '{"relative_path":"missing.png"}',
                        ),
                    ),
                ),
            )
            for index, preflight in enumerate(closure_cases):
                with self.subTest(closure=index), self.assertRaises(ImportApprovalError):
                    self._build(replace(request, preflight_result=preflight), config)

            request_subtype = type("V119WriteRequestSubclass", (V119WriteRequest,), {})
            subclass_request = request_subtype(
                request.preflight_result,
                request.package_root,
                request.approval,
                request.output_dir,
                request.contract,
            )
            with self.assertRaises(PipelineError):
                self._build(subclass_request, config)

            forged_approval_with_newline = object.__new__(ImportApproval)
            for name, value in asdict(request.approval).items():
                object.__setattr__(forged_approval_with_newline, name, value)
            object.__setattr__(
                forged_approval_with_newline,
                "batch_id",
                request.approval.batch_id + "\nFORGED",
            )
            with self.assertRaises(ImportApprovalError):
                self._build(
                    replace(request, approval=forged_approval_with_newline),
                    config,
                )

            baseline_copy = Path(temporary) / "baseline-copy.sqlite3"
            baseline_copy.write_bytes(BASELINE.read_bytes())
            forged_baseline = replace(
                request.preflight_result.baseline_database,
                path=baseline_copy,
            )
            baseline_copy.write_bytes(b"tampered")
            bad_baseline = replace(
                request,
                preflight_result=replace(
                    request.preflight_result,
                    baseline_database=forged_baseline,
                ),
            )
            with self.assertRaises(PipelineError):
                self._build(bad_baseline, config)
            self.assertFalse(request.output_dir.exists())

    def test_builder_rejects_rebound_ambiguous_splits(self) -> None:
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
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
            with self.assertRaises(ImportApprovalError):
                self._build(forged, config)
            self.assertFalse(request.output_dir.exists())

    def test_builder_revalidates_exact_nested_candidate_without_repair(self) -> None:
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            candidate = request.preflight_result.candidates[0]
            object.__setattr__(candidate, "translation_evidence", None)
            forged = _rebind_preflight_authority(request, request.preflight_result)
            with self.assertRaises(ImportApprovalError):
                self._build(forged, config)
            self.assertFalse(request.output_dir.exists())

    def test_builder_maps_missing_image_cross_closure_to_approval_error(self) -> None:
        with TemporaryDirectory() as temporary:
            record = _raw_candidate(
                image_paths=["images/question.png"],
                image_roles=["question"],
            )
            request, config = self._ready_request(
                Path(temporary),
                record=record,
                images={"images/question.png": b"question image bytes"},
            )
            missing_evidence = replace(
                request.preflight_result,
                manifest=replace(
                    request.preflight_result.manifest,
                    image_files=(),
                ),
                report=replace(
                    request.preflight_result.report,
                    readable_files=tuple(
                        path
                        for path in request.preflight_result.report.readable_files
                        if path != "images/question.png"
                    ),
                ),
            )
            try:
                self._build(
                    replace(request, preflight_result=missing_evidence), config
                )
            except ImportApprovalError:
                pass
            except Exception as error:
                self.fail(
                    "missing image evidence leaked a non-approval exception: "
                    f"{type(error).__name__}: {error}"
                )
            else:
                self.fail("missing image evidence was accepted")
            self.assertFalse(request.output_dir.exists())

    def test_builder_rejects_fully_rebound_crlf_batch_carriers(self) -> None:
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            batch_id = request.preflight_result.manifest.batch_id + "\nFORGED"
            preflight = replace(
                request.preflight_result,
                manifest=replace(
                    request.preflight_result.manifest,
                    batch_id=batch_id,
                ),
                report=replace(
                    request.preflight_result.report,
                    batch_id=batch_id,
                ),
            )
            forged = _rebind_preflight_authority(
                request,
                preflight,
                forge_approval=True,
            )
            with self.assertRaises(ImportApprovalError):
                self._build(forged, config)
            self.assertFalse(request.output_dir.exists())

    def test_builder_rejects_baseline_check_use_mutation(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            request, config = self._ready_request(root)
            baseline_copy = root / "baseline-copy.sqlite3"
            baseline_copy.write_bytes(BASELINE.read_bytes())
            copied_reference = replace(
                request.preflight_result.baseline_database,
                path=baseline_copy,
            )
            request = replace(
                request,
                preflight_result=replace(
                    request.preflight_result,
                    baseline_database=copied_reference,
                ),
            )
            real_validate = writer_module._validate_baseline

            def mutate_after_validation(reference):
                validated = real_validate(reference)
                with sqlite3.connect(reference.path) as database:
                    database.execute(
                        "UPDATE complete_questions_v2 "
                        "SET source_question_number='XXAMPLE-Q1' "
                        "WHERE source_question_number='EXAMPLE-Q1'"
                    )
                    database.commit()
                self.assertEqual(reference.path.stat().st_size, reference.size_bytes)
                self.assertNotEqual(
                    hashlib.sha256(reference.path.read_bytes()).hexdigest(),
                    reference.sha256,
                )
                return validated

            with mock.patch(
                "joy_m2.ingest.writer._validate_baseline",
                side_effect=mutate_after_validation,
            ), self.assertRaises(PipelineError):
                self._build(request, config)
            self.assertFalse(request.output_dir.exists())

    def test_builder_rejects_wrong_config_output_conflict_and_unsafe_output(self) -> None:
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            subtype = type("PipelineConfigSubclass", (PipelineConfig,), {})
            with self.assertRaises(PipelineError):
                self._build(request, subtype(config.repo_root))
            request.output_dir.mkdir(parents=True)
            sentinel = request.output_dir / "preserve.txt"
            sentinel.write_bytes(b"preserve")
            with self.assertRaises(OutputConflictError):
                self._build(request, config)
            self.assertEqual(sentinel.read_bytes(), b"preserve")
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            unsafe = replace(request, output_dir=config.staging_root)
            with self.assertRaises(PipelineError):
                self._build(unsafe, config)
            outside = replace(request, output_dir=Path(temporary) / "outside")
            with self.assertRaises(PipelineError):
                self._build(outside, config)
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            config.staging_root.mkdir(parents=True)
            outside_root = Path(temporary) / "escaped"
            outside_root.mkdir()
            (config.staging_root / "link").symlink_to(outside_root, target_is_directory=True)
            escaped = replace(request, output_dir=config.staging_root / "link" / "candidate")
            with self.assertRaises(PipelineError):
                self._build(escaped, config)

    def test_builder_does_not_repreflight_or_reread_non_image_package_files(self) -> None:
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            for group in (
                request.preflight_result.manifest.candidate_records,
                request.preflight_result.manifest.source_files,
                request.preflight_result.manifest.answer_files,
                request.preflight_result.manifest.teacher_notes_files,
                request.preflight_result.manifest.common_errors_files,
            ):
                for evidence in group:
                    (request.package_root / evidence.relative_path).unlink()
            with mock.patch(
                "joy_m2.ingest.preflight.preflight_import",
                side_effect=AssertionError("writer must not re-preflight"),
            ):
                artifacts = self._build(request, config)
            self.assertTrue(artifacts.database.path.is_file())

    def test_builder_uses_only_temporary_output_and_keeps_real_worktree_empty(self) -> None:
        """Production change that would make this fail: repository boundary."""
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            self._build(request, config)
            self.assertTrue(request.output_dir.is_relative_to(config.staging_root))


class V119DeterminismAndAtomicityRedTests(_WriterRedCase):
    def test_equivalent_temporary_roots_produce_identical_candidate_bytes(self) -> None:
        """Production change that would make this fail: all-artifact determinism."""
        with TemporaryDirectory() as first, TemporaryDirectory() as second:
            record = _raw_candidate(
                image_paths=["images/diagram.PNG"],
                image_roles=["question"],
            )
            image_bytes = {"images/diagram.PNG": b"deterministic image bytes"}
            request_one, config_one = self._ready_request(
                Path(first), record=record, images=image_bytes
            )
            request_two, config_two = self._ready_request(
                Path(second), record=record, images=image_bytes
            )
            first_artifacts = self._build(request_one, config_one)
            second_artifacts = self._build(request_two, config_two)
            self.assertEqual(_tree_bytes(request_one.output_dir), _tree_bytes(request_two.output_dir))

            def identity(artifacts, root):
                values = (
                    artifacts.database,
                    artifacts.manifest,
                    artifacts.sha256sums,
                    artifacts.rollback,
                    *artifacts.images,
                )
                return tuple(
                    (item.path.relative_to(root).as_posix(), item.sha256, item.size_bytes, item.kind)
                    for item in values
                )

            self.assertEqual(
                identity(first_artifacts, request_one.output_dir),
                identity(second_artifacts, request_two.output_dir),
            )

    def test_legal_question_and_fragment_roots_are_path_independent(self) -> None:
        with TemporaryDirectory() as temporary:
            parent = Path(temporary)
            built = []
            for name in ("legal?root", "legal#root"):
                root = parent / name
                root.mkdir()
                request, config = self._ready_request(root)
                try:
                    self._build(request, config)
                except PipelineError as error:
                    self.fail(f"legal staging root was rejected: {error}")
                built.append(_tree_bytes(request.output_dir))
            self.assertEqual(built[0], built[1])

    def test_builder_publishes_once_without_partial_destination(self) -> None:
        """Production change that would make this fail: one atomic rename."""
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            real_publish = writer_module.atomic_rename_no_replace
            real_connect = sqlite3.connect
            publications = []
            sql_trace = []

            def traced_connect(*args, **kwargs):
                connection = real_connect(*args, **kwargs)
                if request.contract.database_filename in str(args[0]):
                    connection.set_trace_callback(sql_trace.append)
                return connection

            def publish(operation):
                def invoke(source, destination, *args, **kwargs):
                    source_path = Path(source)
                    destination_path = Path(destination)
                    self.assertFalse(destination_path.exists())
                    self.assertEqual(destination_path, request.output_dir)
                    self.assertTrue(source_path.is_dir())
                    self.assertEqual(
                        {
                            item.relative_to(source_path).as_posix()
                            for item in source_path.rglob("*")
                            if item.is_file()
                        },
                        {
                            request.contract.database_filename,
                            request.contract.manifest_filename,
                            request.contract.sha256s_filename,
                            request.contract.rollback_filename,
                        },
                    )
                    publications.append((source_path, destination_path))
                    return operation(source, destination, *args, **kwargs)

                return invoke

            with mock.patch("sqlite3.connect", side_effect=traced_connect), mock.patch(
                "joy_m2.ingest.writer.atomic_rename_no_replace",
                side_effect=publish(real_publish),
            ):
                artifacts = self._build(request, config)
            self.assertEqual(len(publications), 1)
            normalized_trace = tuple(statement.strip().upper() for statement in sql_trace)
            self.assertEqual(sum(value == "BEGIN IMMEDIATE" for value in normalized_trace), 1)
            self.assertEqual(sum(value == "COMMIT" for value in normalized_trace), 1)
            self.assertEqual(sum(value == "VACUUM" for value in normalized_trace), 1)
            ddl_positions = tuple(
                next(
                    index
                    for index, statement in enumerate(normalized_trace)
                    if statement.startswith(f"CREATE {kind} {name}".upper())
                )
                for kind, name in (
                    ("TABLE", "task9_import_batches_v1"),
                    ("TABLE", "task9_import_candidates_v1"),
                    ("TABLE", "task9_import_images_v1"),
                    ("TABLE", "task9_import_taxonomy_v1"),
                    ("VIEW", "task9_candidate_questions_v1"),
                )
            )
            self.assertEqual(ddl_positions, tuple(sorted(ddl_positions)))
            self.assertEqual(artifacts.database.path.parent, request.output_dir)
            self.assertEqual(
                int.from_bytes(artifacts.database.path.read_bytes()[96:100], "big"),
                3_050_004,
            )
            self.assertEqual(
                {path.relative_to(request.output_dir).as_posix() for path in request.output_dir.rglob("*") if path.is_file()},
                {
                    request.contract.database_filename,
                    request.contract.manifest_filename,
                    request.contract.sha256s_filename,
                    request.contract.rollback_filename,
                },
            )
            leftovers = tuple(
                path for path in config.staging_root.iterdir() if path != request.output_dir
            )
            self.assertEqual(leftovers, ())

    def test_failed_prepublication_verification_cleans_temp_and_preserves_unrelated_files(self) -> None:
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            config.staging_root.mkdir(parents=True)
            sentinel = config.staging_root / "unrelated.txt"
            sentinel.write_bytes(b"keep")
            failed = VerificationReport(
                "FAIL",
                tuple(VerificationCheck(str(index), False, "FAIL") for index in range(16)),
            )
            with mock.patch(
                "joy_m2.ingest.writer.verify_v119_candidate",
                return_value=failed,
                create=True,
            ) as verifier:
                with self.assertRaises(PipelineError):
                    self._build(request, config)
            verifier.assert_called_once()
            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertFalse(request.output_dir.exists())
            self.assertEqual(tuple(config.staging_root.iterdir()), (sentinel,))

    def test_result_construction_failure_prevents_publication(self) -> None:
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            config.staging_root.mkdir(parents=True)
            sentinel = config.staging_root / "unrelated.txt"
            sentinel.write_bytes(b"keep")
            with mock.patch(
                "joy_m2.ingest.writer._final_artifact",
                side_effect=OSError("injected final carrier failure"),
            ), self.assertRaises(OSError):
                self._build(request, config)
            self.assertFalse(request.output_dir.exists())
            self.assertEqual(tuple(config.staging_root.iterdir()), (sentinel,))
            self.assertEqual(sentinel.read_bytes(), b"keep")

    def test_publication_never_replaces_destination_created_after_verification(self) -> None:
        with TemporaryDirectory() as temporary:
            request, config = self._ready_request(Path(temporary))
            real_verify = writer_module.verify_v119_candidate

            def create_competing_destination(*args, **kwargs):
                report = real_verify(*args, **kwargs)
                request.output_dir.mkdir(parents=True)
                return report

            with mock.patch(
                "joy_m2.ingest.writer.verify_v119_candidate",
                side_effect=create_competing_destination,
            ), self.assertRaises(OutputConflictError):
                self._build(request, config)
            self.assertTrue(request.output_dir.is_dir())
            self.assertEqual(tuple(request.output_dir.iterdir()), ())

    def test_transaction_artifact_and_rename_failures_clean_only_private_temp(self) -> None:
        for stage in ("transaction", "artifact", "rename"):
            with self.subTest(stage=stage), TemporaryDirectory() as temporary:
                request, config = self._ready_request(Path(temporary))
                config.staging_root.mkdir(parents=True)
                sentinel = config.staging_root / "unrelated.txt"
                sentinel.write_bytes(b"keep")
                baseline_before = hashlib.sha256(BASELINE.read_bytes()).hexdigest()
                package_before = _snapshot(request.package_root)
                real_connect = sqlite3.connect
                real_write_bytes = Path.write_bytes

                def failing_connect(*args, **kwargs):
                    if request.contract.database_filename in str(args[0]):
                        raise sqlite3.OperationalError("injected transaction failure")
                    return real_connect(*args, **kwargs)

                def failing_write_bytes(path, data):
                    if path.name == request.contract.rollback_filename:
                        raise OSError("injected artifact failure")
                    return real_write_bytes(path, data)

                if stage == "transaction":
                    patcher = mock.patch("sqlite3.connect", side_effect=failing_connect)
                elif stage == "artifact":
                    patcher = mock.patch.object(Path, "write_bytes", failing_write_bytes)
                else:
                    patcher = mock.patch(
                        "joy_m2.ingest.writer.atomic_rename_no_replace",
                        side_effect=OSError("injected rename failure"),
                    )
                with patcher, self.assertRaises(Exception):
                    self._build(request, config)
                self.assertFalse(request.output_dir.exists())
                self.assertEqual(tuple(config.staging_root.iterdir()), (sentinel,))
                self.assertEqual(sentinel.read_bytes(), b"keep")
                self.assertEqual(_snapshot(request.package_root), package_before)
                self.assertEqual(hashlib.sha256(BASELINE.read_bytes()).hexdigest(), baseline_before)


if __name__ == "__main__":
    unittest.main()
