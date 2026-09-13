"""End-to-end behavior contract for Task 9D V1.19 promotion."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
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
from joy_m2.errors import InputFormatError, PipelineError, PromotionError
from joy_m2.ingest import (
    ImportApproval,
    ReleasePromotionApproval,
    V119PromotionBuildRequest,
    V119PromotionContract,
    V119PromotionVerificationRequest,
    V119PublicationRequest,
    V119VerificationRequest,
    V119WriteRequest,
    V119WriterContract,
    build_v119_candidate,
    build_v119_promotion,
    preflight_import,
    publish_v119_release,
    verify_v119_candidate,
    verify_v119_promotion,
)
from joy_m2.models import ArtifactRef, VerificationCheck, VerificationReport
import joy_m2.ingest.promotion as promotion_module
import joy_m2.ingest.promotion_verification as verification_module

from tests.integration.test_ingest_preflight import _package, _raw_candidate


BASELINE_SHA = "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7"
BATCH_ID = "TASK9B-REAL-0918-INTERVAL-REPRODUCTION-001"
BASELINE_SOURCE = WORKTREE / "releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3"

BASELINE_TABLES = (
    "complete_question_corrections_v2", "complete_question_tags_v2",
    "complete_question_taxonomy_v2", "complete_questions_v2", "import_runs_v2",
    "question_topics", "questions", "release_metadata_v2", "sources", "topics",
)
CANDIDATE_TABLES = (
    "task9_import_batches_v1", "task9_import_candidates_v1",
    "task9_import_images_v1", "task9_import_taxonomy_v1",
)
CHECK_NAMES = (
    "release_directory", "promotion_contract", "candidate_verification",
    "manifest_contract", "authority_binding", "filesystem_closure",
    "sha256sums_closure", "artifact_references", "rollback_contract",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "baseline_preservation", "promotion_projection",
    "formal_query", "count_closure", "publication_boundary",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def _rewrite_sums(root: Path) -> None:
    paths = sorted(
        (
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path.name != "SHA256SUMS.txt"
        ),
        key=lambda value: value.encode("utf-8"),
    )
    (root / "SHA256SUMS.txt").write_text(
        "".join(f"{_sha256(root / path)}  {path}\n" for path in paths),
        encoding="utf-8",
    )


def _rebind_release(root: Path) -> str:
    manifest_path = root / "manifest.json"
    database_path = root / "Joy_M2_Complete_Question_DB_V1_19.sqlite3"
    rollback_path = root / "rollback.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["database"]["sha256"] = _sha256(database_path)
    manifest["database"]["size_bytes"] = database_path.stat().st_size
    manifest["database"]["semantic_sha256"] = promotion_module._sqlite_semantic_sha256(
        database_path, "formal_complete_questions_v119"
    )
    database_ref = {
        "relative_path": manifest["database"]["relative_path"],
        "sha256": manifest["database"]["sha256"],
        "size_bytes": manifest["database"]["size_bytes"],
        "kind": "sqlite",
    }
    manifest["artifacts"] = [
        database_ref if item["kind"] == "sqlite" else item
        for item in manifest["artifacts"]
    ]
    identity = {
        "schema_version": "task9-v119-promotion-identity-v1",
        "release_version": "V1.19",
        "baseline_database_sha256": manifest["baseline"]["sqlite"]["sha256"],
        "baseline_question_count": 497,
        "candidate_database_sha256": manifest["candidate"]["database"]["sha256"],
        "candidate_manifest_sha256": manifest["candidate"]["manifest"]["sha256"],
        "batch_id": manifest["import_approval"]["batch_id"],
        "preflight_sha256": manifest["import_approval"]["preflight_sha256"],
        "import_approval_statement": manifest["import_approval"]["statement"],
        "promoted_question_count": 5,
        "formal_question_count": 502,
        "formal_sqlite_sha256": manifest["database"]["sha256"],
        "formal_sqlite_semantic_sha256": manifest["database"]["semantic_sha256"],
        "images": manifest["images"],
    }
    digest = hashlib.sha256(
        json.dumps(
            identity,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    ).hexdigest()
    manifest["promotion"]["release_digest"] = digest
    manifest["promotion"]["required_statement"] = (
        f"USER APPROVED RELEASE PROMOTION V1.19 {digest}"
    )
    rollback = json.loads(rollback_path.read_text(encoding="utf-8"))
    rollback["release_digest"] = digest
    _write_json(rollback_path, rollback)
    rollback_ref = {
        "relative_path": "rollback.json",
        "sha256": _sha256(rollback_path),
        "size_bytes": rollback_path.stat().st_size,
        "kind": "rollback",
    }
    manifest["rollback"] = rollback_ref
    manifest["artifacts"] = [
        rollback_ref if item["kind"] == "rollback" else item
        for item in manifest["artifacts"]
    ]
    _write_json(manifest_path, manifest)
    _rewrite_sums(root)
    return digest


def _tree(root: Path) -> tuple[tuple[str, str, bytes | str], ...]:
    if not root.exists():
        return ()
    result = []
    for item in sorted(root.rglob("*")):
        relative = item.relative_to(root).as_posix()
        if item.is_symlink():
            result.append((relative, "symlink", os.readlink(item)))
        elif item.is_dir():
            result.append((relative, "directory", b""))
        else:
            result.append((relative, "file", item.read_bytes()))
    return tuple(result)


def _writer_contract() -> V119WriterContract:
    return V119WriterContract(
        "V1.19", "task9-v119-candidate-manifest-v1",
        "task9-v119-candidate-v1", 119,
        "Joy_M2_V1.19_candidate.sqlite3", "candidate_manifest.json",
        "SHA256SUMS", "rollback.json", "images/sha256",
        BASELINE_TABLES, CANDIDATE_TABLES, ("task9_candidate_questions_v1",),
    )


def _promotion_contract() -> V119PromotionContract:
    return V119PromotionContract(
        "V1.19", "task9-v119-formal-manifest-v1", "task9-v119-formal-v1",
        "task9-v119-promotion-identity-v1", "task9-v119-formal-rollback-v1",
        119, "Joy_M2_Complete_Question_DB_V1_19.sqlite3", "manifest.json",
        "SHA256SUMS.txt", "rollback.json", "images/sha256",
        "task9_promoted_questions_v1", "task9_promotion_v1",
        "formal_complete_questions_v119",
    )


class _Authority:
    def __init__(self, root: Path):
        self.config = PipelineConfig(root)
        baseline = self.config.releases_root / "V1.18" / BASELINE_SOURCE.name
        baseline.parent.mkdir(parents=True)
        shutil.copyfile(BASELINE_SOURCE, baseline)
        package = root / "package"
        package.mkdir()
        records = [
            _raw_candidate(
                proposed_question_id=f"TASK9D-SYNTHETIC-{index:03d}",
                source_question_number=str(index),
                source_section="Task 9D synthetic promotion authority",
                source_fragment_hash=f"{index:x}" * 64,
                question_text_original=f"Task 9D synthetic question {index}: solve x + {index} = {index + 1}.",
                question_text_zh="",
                translation_status="missing",
                translation_evidence=None,
                solution_original="x = 1",
                solution_verified="x = 1",
                explanation_text="",
                explanation_status="missing",
                explanation_evidence=None,
                tags=[],
                tag_status="missing",
                difficulty_level=None,
                difficulty_status="missing",
                enrichment_status="incomplete",
            )
            for index in range(1, 6)
        ]
        manifest = replace(
            _package(
                package,
                record_groups=(("records/candidates.json", records),),
            ),
            batch_id=BATCH_ID,
        )
        baseline_ref = ArtifactRef(baseline, BASELINE_SHA, baseline.stat().st_size, "sqlite")
        self.preflight = preflight_import(manifest, package, baseline_ref)
        self.preflight_sha = self.preflight.report.preflight_sha256
        self.approval = ImportApproval(
            BATCH_ID, self.preflight_sha, "V1.19",
            f"USER APPROVED IMPORT BATCH {BATCH_ID} {self.preflight_sha} V1.19",
        )
        candidate = self.config.staging_root / "candidate"
        candidate_artifacts = build_v119_candidate(
            V119WriteRequest(
                self.preflight,
                package,
                self.approval,
                candidate,
                _writer_contract(),
            ),
            self.config,
        )
        self.candidate_sha = candidate_artifacts.database.sha256
        self.candidate_manifest_sha = candidate_artifacts.manifest.sha256
        self.candidate = V119VerificationRequest(
            candidate, self.preflight, self.approval, _writer_contract()
        )
        self.contract = _promotion_contract()

    def build_request(self, name: str = "promotion") -> V119PromotionBuildRequest:
        return V119PromotionBuildRequest(
            self.candidate, self.config.staging_root / name, self.contract
        )

    def verify_request(self, path: Path) -> V119PromotionVerificationRequest:
        return V119PromotionVerificationRequest(path, self.candidate, self.contract)

    @contextmanager
    def binding(self):
        patch_values = {
            "CANDIDATE_SHA256": self.candidate_sha,
            "CANDIDATE_MANIFEST_SHA256": self.candidate_manifest_sha,
            "BATCH_ID": BATCH_ID,
            "PREFLIGHT_SHA256": self.preflight_sha,
        }
        with (
            mock.patch.multiple(promotion_module, **patch_values),
            mock.patch.multiple(verification_module, **patch_values),
        ):
            yield


class PromotionBehaviorContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.before_v118 = _sha256(BASELINE_SOURCE)
        self.before_staging = _tree(WORKTREE / "data/staging")
        self.before_releases = _tree(WORKTREE / "releases")

    def tearDown(self) -> None:
        self.assertEqual(_sha256(BASELINE_SOURCE), self.before_v118)
        self.assertEqual(_tree(WORKTREE / "data/staging"), self.before_staging)
        self.assertEqual(_tree(WORKTREE / "releases"), self.before_releases)

    @contextmanager
    def authority(self):
        with TemporaryDirectory() as temporary:
            authority = _Authority(Path(temporary))
            with authority.binding():
                candidate_report = verify_v119_candidate(authority.candidate, authority.config)
                self.assertEqual(candidate_report.status, "PASS")
                self.assertEqual(len(candidate_report.checks), 16)
                self.assertEqual(
                    authority.preflight.report.preflight_sha256,
                    authority.preflight_sha,
                )
                yield authority

    def _build(self, request, config):
        try:
            return build_v119_promotion(request, config)
        except NotImplementedError as error:
            self.fail(f"Task 9D builder behavior is missing: {error}")

    def _verify(self, request, config):
        try:
            return verify_v119_promotion(request, config)
        except NotImplementedError as error:
            self.fail(f"Task 9D verifier behavior is missing: {error}")

    def _publish(self, request, config):
        try:
            return publish_v119_release(request, config)
        except NotImplementedError as error:
            self.fail(f"Task 9D publication behavior is missing: {error}")

    def test_successful_build_exact_tree_and_verification_closure(self):
        with self.authority() as authority:
            result = self._build(authority.build_request(), authority.config)
            root = authority.config.staging_root / "promotion"
            self.assertEqual(
                tuple(path.relative_to(root).as_posix() for path in sorted(root.rglob("*")) if path.is_file()),
                ("Joy_M2_Complete_Question_DB_V1_19.sqlite3", "SHA256SUMS.txt", "manifest.json", "rollback.json"),
            )
            self.assertEqual(result.verification_report.status, "PASS")
            self.assertEqual(tuple(check.name for check in result.verification_report.checks), CHECK_NAMES)
            self.assertTrue(all(check.passed for check in result.verification_report.checks))
            self.assertEqual(result.release_digest, json.loads((root / "manifest.json").read_text())["promotion"]["release_digest"])

    def test_verifier_rejects_symlinked_release_root(self):
        with self.authority() as authority:
            result = self._build(authority.build_request(), authority.config)
            source = result.database.path.parent
            source_before = _tree(source)
            formal = authority.config.releases_root / "V1.19"
            formal.symlink_to(source, target_is_directory=True)

            report = self._verify(
                V119PromotionVerificationRequest(
                    formal, authority.candidate, authority.contract
                ),
                authority.config,
            )

            self.assertEqual(report.status, "FAIL")
            checks = {check.name: check.passed for check in report.checks}
            self.assertFalse(checks["release_directory"])
            self.assertFalse(checks["publication_boundary"])
            self.assertEqual(_tree(source), source_before)

    def test_verifier_rejects_release_root_beneath_symlinked_ancestor(self):
        with self.authority() as authority:
            result = self._build(
                authority.build_request("actual/promotion"), authority.config
            )
            source = result.database.path.parent
            source_before = _tree(source)
            linked_parent = authority.config.staging_root / "linked-parent"
            linked_parent.symlink_to(source.parent, target_is_directory=True)

            report = self._verify(
                V119PromotionVerificationRequest(
                    linked_parent / source.name,
                    authority.candidate,
                    authority.contract,
                ),
                authority.config,
            )

            self.assertEqual(report.status, "FAIL")
            checks = {check.name: check.passed for check in report.checks}
            self.assertFalse(checks["release_directory"])
            self.assertFalse(checks["publication_boundary"])
            self.assertEqual(_tree(source), source_before)

    def test_verifier_rejects_symlink_loop_as_structured_fail(self):
        with self.authority() as authority:
            loop = authority.config.staging_root / "loop"
            loop.symlink_to(loop, target_is_directory=True)

            report = self._verify(
                V119PromotionVerificationRequest(
                    loop / "promotion", authority.candidate, authority.contract
                ),
                authority.config,
            )

            self.assertEqual(report.status, "FAIL")
            checks = {check.name: check.passed for check in report.checks}
            self.assertFalse(checks["release_directory"])
            self.assertFalse(checks["publication_boundary"])

    def test_task9d_sqlite_connections_close_on_success_and_partial_open_failure(self):
        class TrackingConnection:
            def __init__(self, connection):
                self.connection = connection
                self.closed = False

            def __getattr__(self, name):
                return getattr(self.connection, name)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return self.connection.__exit__(*args)

            def close(self):
                self.closed = True
                return self.connection.close()

        with self.authority() as authority:
            real_connect = sqlite3.connect
            opened = []

            def tracked_connect(*args, **kwargs):
                connection = TrackingConnection(real_connect(*args, **kwargs))
                opened.append(connection)
                return connection

            with mock.patch.object(sqlite3, "connect", side_effect=tracked_connect):
                self._build(authority.build_request(), authority.config)
            self.assertTrue(opened)
            self.assertTrue(all(connection.closed for connection in opened))

        for failure_call in (2, 3):
            with self.subTest(failure_call=failure_call):
                opened = [mock.Mock() for _ in range(failure_call - 1)]
                sequence = [*opened, sqlite3.OperationalError("synthetic open failure")]
                with mock.patch.object(sqlite3, "connect", side_effect=sequence):
                    result = verification_module._database_checks(
                        Path("formal.sqlite3"),
                        Path("baseline.sqlite3"),
                        Path("candidate.sqlite3"),
                        _promotion_contract(),
                    )
                self.assertFalse(any(result.values()))
                for connection in opened:
                    connection.close.assert_called_once_with()

    def test_database_preserves_497_and_maps_exact_five_without_enrichment(self):
        with self.authority() as authority:
            self._build(authority.build_request(), authority.config)
            formal = authority.config.staging_root / "promotion" / "Joy_M2_Complete_Question_DB_V1_19.sqlite3"
            baseline = authority.config.releases_root / "V1.18" / BASELINE_SOURCE.name
            candidate = authority.candidate.candidate_dir / "Joy_M2_V1.19_candidate.sqlite3"
            with sqlite3.connect(f"file:{baseline}?mode=ro", uri=True) as before, sqlite3.connect(f"file:{formal}?mode=ro", uri=True) as after, sqlite3.connect(f"file:{candidate}?mode=ro", uri=True) as source:
                self.assertEqual(tuple(before.execute("SELECT * FROM complete_questions_v2 ORDER BY source_order")), tuple(after.execute("SELECT * FROM complete_questions_v2 ORDER BY source_order")))
                candidate_rows = tuple(source.execute("SELECT * FROM task9_import_candidates_v1 ORDER BY candidate_order"))
                promoted = tuple(after.execute("SELECT * FROM task9_promoted_questions_v1 ORDER BY candidate_order"))
                self.assertEqual(len(candidate_rows), len(promoted), 5)
                self.assertEqual(tuple(row[3] for row in promoted), tuple(row[2] for row in candidate_rows))
                self.assertEqual(tuple(row[2] for row in promoted), (498, 499, 500, 501, 502))
                self.assertTrue(all(row[-2:] == ("published", 1) for row in promoted))
                self.assertTrue(all(row[17] == "missing" and row[23] == "[]" and row[24] == "missing" and row[25] is None and row[26] == "missing" and row[27] == "incomplete" for row in promoted))
                rows = tuple(after.execute("SELECT formal_order,authority_kind,record_status,selectable FROM formal_complete_questions_v119 ORDER BY formal_order"))
                self.assertEqual(len(rows), 502)
                self.assertEqual(rows[0][0], 1)
                self.assertEqual(rows[-1], (502, "task9_promoted", "published", 1))
                self.assertEqual(after.execute("PRAGMA user_version").fetchone(), (119,))

    def test_equivalent_roots_are_byte_and_identity_deterministic(self):
        with TemporaryDirectory() as first, TemporaryDirectory() as second:
            a = _Authority(Path(first))
            b = _Authority(Path(second))
            self.assertEqual(a.preflight_sha, b.preflight_sha)
            self.assertEqual(a.candidate_sha, b.candidate_sha)
            self.assertEqual(a.candidate_manifest_sha, b.candidate_manifest_sha)
            with a.binding():
                result_a = self._build(a.build_request(), a.config)
                result_b = self._build(b.build_request(), b.config)
            self.assertEqual(_tree(a.config.staging_root / "promotion"), _tree(b.config.staging_root / "promotion"))
            self.assertEqual(result_a.release_digest, result_b.release_digest)
            self.assertEqual(result_a.database.sha256, result_b.database.sha256)

    def test_builder_rejects_candidate_and_authority_drift_before_output(self):
        with self.authority() as authority:
            cases = []
            bad_baseline = replace(
                authority.preflight,
                baseline_database=replace(authority.preflight.baseline_database, sha256="0" * 64),
            )
            cases.append(replace(authority.candidate, preflight_result=bad_baseline))
            bad_batch_manifest = replace(authority.preflight.manifest, batch_id="OTHER")
            cases.append(replace(authority.candidate, preflight_result=replace(authority.preflight, manifest=bad_batch_manifest)))
            bad_report = replace(authority.preflight.report, preflight_sha256="0" * 64)
            cases.append(replace(authority.candidate, preflight_result=replace(authority.preflight, report=bad_report)))
            for index, candidate in enumerate(cases):
                request = replace(authority.build_request(f"bad-{index}"), candidate=candidate)
                with self.subTest(index=index), self.assertRaises(PromotionError):
                    self._build(request, authority.config)
                self.assertFalse(request.output_dir.exists())

    def test_builder_requires_independent_candidate_pass_and_exact_candidate_hashes(self):
        with self.authority() as authority:
            failed = VerificationReport("FAIL", (VerificationCheck("candidate_directory", False, "forced"),))
            with mock.patch(
                "joy_m2.ingest.promotion.verify_v119_candidate",
                return_value=failed,
                create=True,
            ):
                with self.assertRaises(PromotionError):
                    self._build(authority.build_request("forced-fail"), authority.config)
            self.assertFalse((authority.config.staging_root / "forced-fail").exists())
            manifest = authority.candidate.candidate_dir / "candidate_manifest.json"
            manifest.write_bytes(manifest.read_bytes() + b" ")
            with self.assertRaises(PromotionError):
                self._build(authority.build_request("manifest-drift"), authority.config)
            self.assertFalse((authority.config.staging_root / "manifest-drift").exists())

    def test_each_candidate_database_baseline_count_row_and_approval_drift_is_rejected(self):
        cases = ("candidate_database", "baseline_row", "candidate_row", "count", "approval")
        for case in cases:
            with self.subTest(case=case), self.authority() as authority:
                candidate = authority.candidate
                if case == "candidate_database":
                    database = candidate.candidate_dir / "Joy_M2_V1.19_candidate.sqlite3"
                    database.write_bytes(database.read_bytes() + b"\0")
                elif case == "baseline_row":
                    with sqlite3.connect(candidate.preflight_result.baseline_database.path) as database:
                        database.execute("UPDATE complete_questions_v2 SET question_text_original='mutated' WHERE source_order=1")
                elif case == "candidate_row":
                    with sqlite3.connect(candidate.candidate_dir / "Joy_M2_V1.19_candidate.sqlite3") as database:
                        database.execute("DELETE FROM task9_import_candidates_v1 WHERE candidate_order=4")
                elif case == "count":
                    report = object.__new__(type(candidate.preflight_result.report))
                    for field_name, value in candidate.preflight_result.report.__dict__.items():
                        object.__setattr__(
                            report,
                            field_name,
                            4 if field_name == "detected_count" else value,
                        )
                    preflight = replace(
                        candidate.preflight_result,
                        report=report,
                    )
                    candidate = replace(candidate, preflight_result=preflight)
                else:
                    forged = object.__new__(ImportApproval)
                    for name, value in (
                        ("batch_id", BATCH_ID),
                        ("preflight_sha256", authority.preflight_sha),
                        ("target_release_version", "V1.19"),
                        ("statement", "USER APPROVED IMPORT BATCH forged"),
                    ):
                        object.__setattr__(forged, name, value)
                    candidate = replace(candidate, approval=forged)
                request = replace(authority.build_request(f"bad-{case}"), candidate=candidate)
                with self.assertRaises(PromotionError):
                    self._build(request, authority.config)
                self.assertFalse(request.output_dir.exists())

    def test_builder_rejects_output_escape_conflict_and_duplicate_candidate(self):
        with self.authority() as authority:
            outside = replace(authority.build_request(), output_dir=authority.config.repo_root / "outside")
            with self.assertRaises(PipelineError):
                self._build(outside, authority.config)
            conflict = authority.config.staging_root / "conflict"
            conflict.mkdir()
            with self.assertRaises(PipelineError):
                self._build(authority.build_request("conflict"), authority.config)
            self.assertEqual(tuple(conflict.iterdir()), ())
            database = authority.candidate.candidate_dir / "Joy_M2_V1.19_candidate.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute("UPDATE task9_import_candidates_v1 SET proposed_question_id=(SELECT question_id FROM complete_questions_v2 LIMIT 1) WHERE candidate_order=0")
            with self.assertRaises(PromotionError):
                self._build(authority.build_request("duplicate"), authority.config)

    def test_malformed_manifest_is_exception_but_parsed_invalid_is_fail_without_mutation(self):
        with self.authority() as authority:
            self._build(authority.build_request(), authority.config)
            root = authority.config.staging_root / "promotion"
            manifest = root / "manifest.json"
            manifest.write_bytes(b"{")
            before = _tree(root)
            with self.assertRaises(InputFormatError):
                self._verify(authority.verify_request(root), authority.config)
            self.assertEqual(_tree(root), before)
        with self.authority() as authority:
            self._build(authority.build_request(), authority.config)
            root = authority.config.staging_root / "promotion"
            manifest = root / "manifest.json"
            payload = json.loads(manifest.read_text())
            payload["release_version"] = "V9.99"
            manifest.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
            before = _tree(root)
            report = self._verify(authority.verify_request(root), authority.config)
            self.assertEqual(report.status, "FAIL")
            self.assertFalse(next(check for check in report.checks if check.name == "manifest_contract").passed)
            self.assertEqual(_tree(root), before)

    def test_parsed_manifest_wrong_shapes_and_bool_as_int_are_structured_fail(self):
        mutations = (
            [],
            {"release_status": []},
            {"release_status": {}},
            {"release_status": 123},
            {"release_status": True},
            {"release_status": None},
            {"counts": {"baseline_question_count": True, "promoted_question_count": 5, "formal_question_count": 502}},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.authority() as authority:
                self._build(authority.build_request(), authority.config)
                root = authority.config.staging_root / "promotion"
                path = root / "manifest.json"
                if type(mutation) is list:
                    payload = mutation
                else:
                    payload = json.loads(path.read_text())
                    payload.update(mutation)
                _write_json(path, payload)
                before = _tree(root)
                report = self._verify(authority.verify_request(root), authority.config)
                self.assertEqual(report.status, "FAIL")
                self.assertFalse(next(check for check in report.checks if check.name == "manifest_contract").passed)
                self.assertEqual(_tree(root), before)

    def test_unparseable_manifest_payloads_raise_input_format_error(self):
        payloads = (b'{"value":' + b"9" * 5000 + b"}\n",)
        for payload in payloads:
            with self.subTest(size=len(payload)), self.authority() as authority:
                self._build(authority.build_request(), authority.config)
                root = authority.config.staging_root / "promotion"
                (root / "manifest.json").write_bytes(payload)
                before = _tree(root)
                with self.assertRaises(InputFormatError):
                    self._verify(authority.verify_request(root), authority.config)
                self.assertEqual(_tree(root), before)

    def test_malformed_candidate_manifest_propagates_input_format_error(self):
        with self.authority() as authority:
            self._build(authority.build_request(), authority.config)
            root = authority.config.staging_root / "promotion"
            candidate_manifest = authority.candidate.candidate_dir / "candidate_manifest.json"
            candidate_manifest.write_bytes(b"{")
            before = _tree(root)
            with self.assertRaises(InputFormatError):
                self._verify(authority.verify_request(root), authority.config)
            self.assertEqual(_tree(root), before)

    def test_manifest_rebind_races_never_leak_native_json_exceptions(self):
        unparseable = b'{"value":' + b"9" * 5000 + b"}\n"
        with self.authority() as authority:
            manifest = authority.candidate.candidate_dir / "candidate_manifest.json"
            real_verify = promotion_module.verify_v119_candidate

            def corrupt_candidate_after_verify(request, config):
                report = real_verify(request, config)
                manifest.write_bytes(unparseable)
                return report

            request = authority.build_request("candidate-json-race")
            with mock.patch.object(
                promotion_module,
                "verify_v119_candidate",
                side_effect=corrupt_candidate_after_verify,
            ):
                with self.assertRaises(PromotionError):
                    self._build(request, authority.config)
            self.assertFalse(request.output_dir.exists())

        with self.authority() as authority:
            artifacts = self._build(authority.build_request(), authority.config)
            approval = ReleasePromotionApproval(
                "V1.19",
                artifacts.release_digest,
                f"USER APPROVED RELEASE PROMOTION V1.19 {artifacts.release_digest}",
            )
            request = V119PublicationRequest(
                artifacts.database.path.parent,
                authority.candidate,
                approval,
                authority.contract,
            )
            real_verify = verification_module.verify_v119_promotion
            calls = 0

            def corrupt_dry_run_after_verify(call_request, call_config):
                nonlocal calls
                calls += 1
                report = real_verify(call_request, call_config)
                if calls == 1:
                    (call_request.release_dir / "manifest.json").write_bytes(unparseable)
                return report

            with mock.patch.object(
                verification_module,
                "verify_v119_promotion",
                side_effect=corrupt_dry_run_after_verify,
            ):
                with self.assertRaises(PromotionError):
                    self._publish(request, authority.config)
            self.assertFalse((authority.config.releases_root / "V1.19").exists())

    def test_manifest_upstream_sizes_and_canonical_json_bytes_are_verified(self):
        for field in ("baseline", "candidate_database", "candidate_manifest"):
            with self.subTest(field=field), self.authority() as authority:
                self._build(authority.build_request(), authority.config)
                root = authority.config.staging_root / "promotion"
                path = root / "manifest.json"
                payload = json.loads(path.read_text(encoding="utf-8"))
                if field == "baseline":
                    artifact = payload["baseline"]["sqlite"]
                elif field == "candidate_database":
                    artifact = payload["candidate"]["database"]
                else:
                    artifact = payload["candidate"]["manifest"]
                artifact["size_bytes"] += 1
                _write_json(path, payload)
                _rewrite_sums(root)
                report = self._verify(authority.verify_request(root), authority.config)
                self.assertEqual(report.status, "FAIL")
                self.assertFalse(
                    next(
                        check
                        for check in report.checks
                        if check.name == "authority_binding"
                    ).passed
                )
        for artifact in ("manifest", "rollback"):
            with self.subTest(artifact=artifact), self.authority() as authority:
                self._build(authority.build_request(), authority.config)
                root = authority.config.staging_root / "promotion"
                if artifact == "manifest":
                    path = root / "manifest.json"
                    path.write_bytes(b" " + path.read_bytes())
                else:
                    rollback_path = root / "rollback.json"
                    rollback_path.write_bytes(b" " + rollback_path.read_bytes())
                    manifest_path = root / "manifest.json"
                    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                    ref = {
                        "relative_path": "rollback.json",
                        "sha256": _sha256(rollback_path),
                        "size_bytes": rollback_path.stat().st_size,
                        "kind": "rollback",
                    }
                    payload["rollback"] = ref
                    payload["artifacts"] = [
                        ref if item["kind"] == "rollback" else item
                        for item in payload["artifacts"]
                    ]
                    _write_json(manifest_path, payload)
                _rewrite_sums(root)
                report = self._verify(authority.verify_request(root), authority.config)
                self.assertEqual(report.status, "FAIL")
                failed = "manifest_contract" if artifact == "manifest" else "rollback_contract"
                self.assertFalse(
                    next(check for check in report.checks if check.name == failed).passed
                )

    def test_missing_extra_symlink_and_corrupt_artifacts_are_structured_fail(self):
        mutations = ("missing", "extra", "symlink", "sqlite")
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.authority() as authority:
                self._build(authority.build_request(), authority.config)
                root = authority.config.staging_root / "promotion"
                if mutation == "missing":
                    (root / "rollback.json").unlink()
                elif mutation == "extra":
                    (root / "rogue.txt").write_text("rogue")
                elif mutation == "symlink":
                    (root / "rollback.json").unlink()
                    (root / "rollback.json").symlink_to(root / "manifest.json")
                else:
                    (root / "Joy_M2_Complete_Question_DB_V1_19.sqlite3").write_bytes(b"not sqlite")
                before = _tree(root)
                report = self._verify(authority.verify_request(root), authority.config)
                self.assertEqual(report.status, "FAIL")
                self.assertTrue(any(not check.passed for check in report.checks))
                self.assertEqual(_tree(root), before)

    def test_rogue_empty_directories_fail_exact_filesystem_closure(self):
        for relative in ("rogue-empty", "images/sha256/aa/rogue-empty"):
            with self.subTest(relative=relative), self.authority() as authority:
                self._build(authority.build_request(), authority.config)
                root = authority.config.staging_root / "promotion"
                (root / relative).mkdir(parents=True)
                before = _tree(root)
                report = self._verify(authority.verify_request(root), authority.config)
                self.assertEqual(report.status, "FAIL")
                self.assertFalse(
                    next(
                        check
                        for check in report.checks
                        if check.name == "filesystem_closure"
                    ).passed
                )
                self.assertEqual(_tree(root), before)

    def test_formal_projection_tamper_is_fail_not_repaired(self):
        with self.authority() as authority:
            self._build(authority.build_request(), authority.config)
            root = authority.config.staging_root / "promotion"
            database = root / "Joy_M2_Complete_Question_DB_V1_19.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute("UPDATE task9_promoted_questions_v1 SET question_text_original='tampered' WHERE candidate_order=0")
            before = _tree(root)
            report = self._verify(authority.verify_request(root), authority.config)
            self.assertEqual(report.status, "FAIL")
            self.assertFalse(next(check for check in report.checks if check.name == "promotion_projection").passed)
            self.assertEqual(_tree(root), before)

    def test_manifest_sums_rollback_and_digest_mismatches_fail_independently(self):
        cases = ("database_ref", "semantic_digest", "release_digest", "sums", "rollback", "rollback_ref")
        for case in cases:
            with self.subTest(case=case), self.authority() as authority:
                self._build(authority.build_request(), authority.config)
                root = authority.config.staging_root / "promotion"
                manifest_path = root / "manifest.json"
                manifest = json.loads(manifest_path.read_text())
                expected_failed = "artifact_references"
                if case == "database_ref":
                    manifest["database"]["sha256"] = "0" * 64
                elif case == "semantic_digest":
                    manifest["database"]["semantic_sha256"] = "0" * 64
                elif case == "release_digest":
                    manifest["promotion"]["release_digest"] = "0" * 64
                    manifest["promotion"]["required_statement"] = "USER APPROVED RELEASE PROMOTION V1.19 " + "0" * 64
                    expected_failed = "authority_binding"
                elif case == "sums":
                    sums = root / "SHA256SUMS.txt"
                    lines = sums.read_text().splitlines()
                    lines[0] = "0" * 64 + lines[0][64:]
                    sums.write_text("\n".join(lines) + "\n")
                    expected_failed = "sha256sums_closure"
                elif case == "rollback":
                    rollback = json.loads((root / "rollback.json").read_text())
                    rollback["action"] = "wrong"
                    _write_json(root / "rollback.json", rollback)
                    expected_failed = "rollback_contract"
                else:
                    manifest["rollback"]["sha256"] = "0" * 64
                if case not in {"sums", "rollback"}:
                    _write_json(manifest_path, manifest)
                before = _tree(root)
                report = self._verify(authority.verify_request(root), authority.config)
                self.assertEqual(report.status, "FAIL")
                self.assertFalse(next(check for check in report.checks if check.name == expected_failed).passed)
                self.assertEqual(_tree(root), before)

    def test_sqlite_fk_schema_metadata_and_each_promoted_field_tamper_fail(self):
        cases = (
            "foreign_key", "schema", "rogue_schema", "metadata",
            "historical_metadata", "source_text", "answer", "provenance",
            "primary_type", "missing_enrichment",
        )
        for case in cases:
            with self.subTest(case=case), self.authority() as authority:
                self._build(authority.build_request(), authority.config)
                root = authority.config.staging_root / "promotion"
                path = root / "Joy_M2_Complete_Question_DB_V1_19.sqlite3"
                with sqlite3.connect(path) as database:
                    if case == "foreign_key":
                        database.execute("PRAGMA foreign_keys=OFF")
                        database.execute("UPDATE task9_promoted_questions_v1 SET batch_id='OTHER' WHERE candidate_order=0")
                        expected = "sqlite_foreign_keys"
                    elif case == "schema":
                        database.execute("DROP VIEW formal_complete_questions_v119")
                        database.execute("CREATE VIEW formal_complete_questions_v119 AS SELECT 1 AS formal_order")
                        expected = "sqlite_schema"
                    elif case == "rogue_schema":
                        database.execute("CREATE TABLE rogue(value TEXT)")
                        expected = "sqlite_schema"
                    elif case == "metadata":
                        database.execute("UPDATE release_metadata_v2 SET value='V9.99' WHERE key='release_version'")
                        expected = "promotion_projection"
                    elif case == "historical_metadata":
                        database.execute("UPDATE release_metadata_v2 SET value='Someone else' WHERE key='approved_by'")
                        expected = "promotion_projection"
                    elif case == "source_text":
                        database.execute("UPDATE task9_promoted_questions_v1 SET question_text_original='changed' WHERE candidate_order=0")
                        expected = "promotion_projection"
                    elif case == "answer":
                        database.execute("UPDATE task9_promoted_questions_v1 SET solution_original='changed' WHERE candidate_order=0")
                        expected = "promotion_projection"
                    elif case == "provenance":
                        database.execute("UPDATE task9_promoted_questions_v1 SET source_id='changed' WHERE candidate_order=0")
                        expected = "promotion_projection"
                    elif case == "primary_type":
                        database.execute("UPDATE task9_promoted_questions_v1 SET primary_type='changed' WHERE candidate_order=0")
                        expected = "promotion_projection"
                    else:
                        database.execute("UPDATE task9_promoted_questions_v1 SET tags_json='[\"invented\"]',tag_status='proposed',difficulty_level=5,difficulty_status='proposed',enrichment_status='complete' WHERE candidate_order=0")
                        expected = "promotion_projection"
                before = _tree(root)
                report = self._verify(authority.verify_request(root), authority.config)
                self.assertEqual(report.status, "FAIL")
                self.assertFalse(next(check for check in report.checks if check.name == expected).passed)
                self.assertEqual(_tree(root), before)

    def test_all_inherited_baseline_and_candidate_relations_are_preserved(self):
        cases = ("baseline_source", "candidate_batch", "candidate_taxonomy")
        for case in cases:
            with self.subTest(case=case), self.authority() as authority:
                self._build(authority.build_request(), authority.config)
                root = authority.config.staging_root / "promotion"
                database_path = root / "Joy_M2_Complete_Question_DB_V1_19.sqlite3"
                with sqlite3.connect(database_path) as database:
                    if case == "baseline_source":
                        database.execute(
                            "UPDATE sources SET title=title || ' tampered' "
                            "WHERE source_id=(SELECT source_id FROM sources ORDER BY source_id LIMIT 1)"
                        )
                        failed = "baseline_preservation"
                    elif case == "candidate_batch":
                        database.execute(
                            "UPDATE task9_import_batches_v1 SET manifest_sha256=?",
                            ("0" * 64,),
                        )
                        failed = "promotion_projection"
                    else:
                        database.execute(
                            "UPDATE task9_import_taxonomy_v1 SET value=value || '-tampered'"
                        )
                        failed = "promotion_projection"
                _rebind_release(root)
                before = _tree(root)
                report = self._verify(authority.verify_request(root), authority.config)
                self.assertEqual(report.status, "FAIL")
                self.assertFalse(
                    next(check for check in report.checks if check.name == failed).passed
                )
                self.assertEqual(_tree(root), before)

    def test_private_release_sibling_is_not_a_public_verification_root(self):
        with self.authority() as authority:
            self._build(authority.build_request(), authority.config)
            private = authority.config.releases_root / ".V1.19-private"
            shutil.copytree(authority.config.staging_root / "promotion", private)
            report = self._verify(authority.verify_request(private), authority.config)
            self.assertEqual(report.status, "FAIL")
            self.assertFalse(next(check for check in report.checks if check.name == "release_directory").passed)
            self.assertFalse(next(check for check in report.checks if check.name == "publication_boundary").passed)

    def test_publication_requires_exact_gate_d_and_publishes_only_isolated_target(self):
        with self.authority() as authority:
            artifacts = self._build(authority.build_request(), authority.config)
            wrong = ReleasePromotionApproval(
                "V1.19", "0" * 64,
                "USER APPROVED RELEASE PROMOTION V1.19 " + "0" * 64,
            )
            with self.assertRaises(PromotionError):
                self._publish(V119PublicationRequest(artifacts.database.path.parent, authority.candidate, wrong, authority.contract), authority.config)
            target = authority.config.releases_root / "V1.19"
            self.assertFalse(target.exists())
            approval = ReleasePromotionApproval(
                "V1.19", artifacts.release_digest,
                f"USER APPROVED RELEASE PROMOTION V1.19 {artifacts.release_digest}",
            )
            published = self._publish(V119PublicationRequest(artifacts.database.path.parent, authority.candidate, approval, authority.contract), authority.config)
            self.assertTrue(target.is_dir())
            self.assertEqual(_tree(target), _tree(artifacts.database.path.parent))
            self.assertEqual(published.release_digest, artifacts.release_digest)
            self.assertEqual(published.verification_report.status, "PASS")
            self.assertEqual(_sha256(authority.config.releases_root / "V1.18" / BASELINE_SOURCE.name), BASELINE_SHA)

    def test_publication_rejects_symlinked_dry_run_root(self):
        with self.authority() as authority:
            artifacts = self._build(authority.build_request("approved"), authority.config)
            approved_root = artifacts.database.path.parent
            approved_before = _tree(approved_root)
            linked_root = authority.config.staging_root / "linked-promotion"
            linked_root.symlink_to(approved_root, target_is_directory=True)
            approval = ReleasePromotionApproval(
                "V1.19",
                artifacts.release_digest,
                f"USER APPROVED RELEASE PROMOTION V1.19 {artifacts.release_digest}",
            )

            with self.assertRaises(PromotionError):
                self._publish(
                    V119PublicationRequest(
                        linked_root,
                        authority.candidate,
                        approval,
                        authority.contract,
                    ),
                    authority.config,
                )

            self.assertFalse((authority.config.releases_root / "V1.19").exists())
            self.assertEqual(_tree(approved_root), approved_before)

    def test_publication_rejects_symlink_loop_with_promotion_error(self):
        with self.authority() as authority:
            loop = authority.config.staging_root / "loop"
            loop.symlink_to(loop, target_is_directory=True)
            approval = ReleasePromotionApproval(
                "V1.19",
                "0" * 64,
                "USER APPROVED RELEASE PROMOTION V1.19 " + "0" * 64,
            )

            with self.assertRaises(PromotionError):
                self._publish(
                    V119PublicationRequest(
                        loop / "promotion",
                        authority.candidate,
                        approval,
                        authority.contract,
                    ),
                    authority.config,
                )

            self.assertFalse((authority.config.releases_root / "V1.19").exists())

    def test_publication_conflict_and_copy_failure_do_not_replace_or_leave_private_tree(self):
        with self.authority() as authority:
            artifacts = self._build(authority.build_request(), authority.config)
            approval = ReleasePromotionApproval("V1.19", artifacts.release_digest, f"USER APPROVED RELEASE PROMOTION V1.19 {artifacts.release_digest}")
            request = V119PublicationRequest(artifacts.database.path.parent, authority.candidate, approval, authority.contract)
            target = authority.config.releases_root / "V1.19"
            target.mkdir(parents=True)
            marker = target / "keep"
            marker.write_text("unchanged")
            with self.assertRaises(PipelineError):
                self._publish(request, authority.config)
            self.assertEqual(marker.read_text(), "unchanged")
        with self.authority() as authority:
            artifacts = self._build(authority.build_request(), authority.config)
            approval = ReleasePromotionApproval("V1.19", artifacts.release_digest, f"USER APPROVED RELEASE PROMOTION V1.19 {artifacts.release_digest}")
            request = V119PublicationRequest(artifacts.database.path.parent, authority.candidate, approval, authority.contract)
            with mock.patch("joy_m2.ingest.promotion.shutil.copytree", side_effect=OSError("copy failed")):
                with self.assertRaises(PromotionError):
                    self._publish(request, authority.config)
            self.assertFalse((authority.config.releases_root / "V1.19").exists())
            self.assertEqual(tuple(path for path in authority.config.releases_root.iterdir() if path.name != "V1.18"), ())

    def test_publication_rename_and_post_verify_failures_cleanup_only_new_state(self):
        with self.authority() as authority:
            artifacts = self._build(authority.build_request(), authority.config)
            approval = ReleasePromotionApproval("V1.19", artifacts.release_digest, f"USER APPROVED RELEASE PROMOTION V1.19 {artifacts.release_digest}")
            request = V119PublicationRequest(artifacts.database.path.parent, authority.candidate, approval, authority.contract)
            with mock.patch("joy_m2.ingest.promotion.atomic_rename_no_replace", side_effect=OSError("rename failed")):
                with self.assertRaises(PromotionError):
                    self._publish(request, authority.config)
            self.assertFalse((authority.config.releases_root / "V1.19").exists())
            self.assertEqual(tuple(path for path in authority.config.releases_root.iterdir() if path.name != "V1.18"), ())

    def test_gate_d_rebinds_the_copied_snapshot_against_source_swap(self):
        with self.authority() as authority:
            artifacts = self._build(authority.build_request("approved"), authority.config)
            approved_root = authority.config.staging_root / "approved"
            alternate = authority.config.staging_root / "alternate"
            shutil.copytree(approved_root, alternate)
            database_path = alternate / "Joy_M2_Complete_Question_DB_V1_19.sqlite3"
            with sqlite3.connect(database_path) as database:
                database.execute("PRAGMA application_id=1")
            alternate_digest = _rebind_release(alternate)
            self.assertNotEqual(alternate_digest, artifacts.release_digest)
            self.assertEqual(
                self._verify(authority.verify_request(alternate), authority.config).status,
                "PASS",
            )
            approval = ReleasePromotionApproval(
                "V1.19",
                artifacts.release_digest,
                f"USER APPROVED RELEASE PROMOTION V1.19 {artifacts.release_digest}",
            )
            request = V119PublicationRequest(
                approved_root, authority.candidate, approval, authority.contract
            )
            real_fingerprint = promotion_module._tree_fingerprint
            swapped = False

            def swap_before_snapshot(root):
                nonlocal swapped
                if not swapped and root == approved_root:
                    swapped = True
                    shutil.rmtree(approved_root)
                    shutil.copytree(alternate, approved_root)
                return real_fingerprint(root)

            with mock.patch(
                "joy_m2.ingest.promotion._tree_fingerprint",
                side_effect=swap_before_snapshot,
            ):
                with self.assertRaises(PromotionError):
                    self._publish(request, authority.config)
            self.assertTrue(swapped)
            self.assertFalse((authority.config.releases_root / "V1.19").exists())

    def test_builder_post_rename_verify_failure_removes_only_owned_output(self):
        with self.authority() as authority:
            import joy_m2.ingest.promotion_verification as verifier_module
            real_verify = verifier_module.verify_v119_promotion
            calls = 0

            def fail_second(call_request, call_config):
                nonlocal calls
                calls += 1
                if calls == 2:
                    return VerificationReport("FAIL", (VerificationCheck("publication_boundary", False, "forced"),))
                return real_verify(call_request, call_config)

            with mock.patch("joy_m2.ingest.promotion_verification.verify_v119_promotion", side_effect=fail_second):
                with self.assertRaises(PromotionError):
                    self._build(authority.build_request(), authority.config)
            self.assertFalse((authority.config.staging_root / "promotion").exists())
            self.assertTrue(authority.candidate.candidate_dir.is_dir())
        with self.authority() as authority:
            artifacts = self._build(authority.build_request(), authority.config)
            approval = ReleasePromotionApproval("V1.19", artifacts.release_digest, f"USER APPROVED RELEASE PROMOTION V1.19 {artifacts.release_digest}")
            request = V119PublicationRequest(artifacts.database.path.parent, authority.candidate, approval, authority.contract)
            import joy_m2.ingest.promotion_verification as verifier_module
            real_verify = verifier_module.verify_v119_promotion
            calls = 0

            def fail_second(call_request, call_config):
                nonlocal calls
                calls += 1
                if calls == 2:
                    return VerificationReport("FAIL", (VerificationCheck("publication_boundary", False, "forced"),))
                return real_verify(call_request, call_config)

            with mock.patch("joy_m2.ingest.promotion_verification.verify_v119_promotion", side_effect=fail_second):
                with self.assertRaises(PromotionError):
                    self._publish(request, authority.config)
            self.assertFalse((authority.config.releases_root / "V1.19").exists())
            self.assertEqual(tuple(path for path in authority.config.releases_root.iterdir() if path.name != "V1.18"), ())


if __name__ == "__main__":
    unittest.main()
