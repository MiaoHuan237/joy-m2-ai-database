"""End-to-end behavior contract for Task 10C promotion readiness."""

from __future__ import annotations

from contextlib import closing
from dataclasses import fields
from pathlib import Path
import hashlib
import json
import shutil
import sqlite3
import tempfile
import unittest
from unittest import mock

from joy_m2.config import PipelineConfig
from joy_m2.errors import OutputConflictError, PipelineError, PromotionError
from joy_m2.ingest import (
    V120ApprovedBatch,
    V120CandidateBuildRequest,
    V120CandidateVerificationRequest,
    V120ImportApproval,
    V120PreflightRequest,
    V120PromotionBuildRequest,
    V120PromotionContract,
    V120PromotionVerificationRequest,
    V120PublicationRequest,
    V120ReleasePromotionApproval,
    build_v120_promotion,
    build_v120_candidate,
    load_v120_import_manifest,
    preflight_v120_import,
    publish_v120_release,
    verify_v120_candidate,
    verify_v120_promotion,
)
from joy_m2.models import ArtifactRef, VerificationCheck, VerificationReport
from tests.integration.test_v120_preflight import _contract as candidate_contract
import joy_m2.ingest.v120_promotion as promotion_module


ROOT = Path(__file__).resolve().parents[2]
PY_STAGING = ROOT / "data/staging"
BASELINE_SHA = "5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff"
EXPECTED_CANDIDATE_DIGEST = "88cc945b6296652c88041e8e51a5c586300c2201a9f48e21abde80d97da3a7b3"
CHECK_NAMES = (
    "release_directory", "promotion_contract", "candidate_verification",
    "candidate_binding", "manifest_contract", "filesystem_closure",
    "sha256sums_closure", "artifact_references", "rollback_contract",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "v119_preservation", "batch_ledger_closure",
    "promotion_projection", "formal_query", "count_closure",
    "provenance_closure", "deterministic_identity", "publication_boundary",
)
REAL_BATCHES = (
    (
        "JOY-M2-HKDSE-2012-PP-MS",
        "32b74e93476d921bacd60f1acb8775eadfc02f471e5b8f71650009f1bcfd9bdf",
        "4ff624aca875b0191fe8a617516d2919c6d700ce69c5a3b5d236adcf7ecc59f1",
        "task10b-hkdse-2012/canonical-v120-approved-v4-taxonomy",
        "task10a-v120-real-candidate-000001-hkdse-2012",
    ),
    (
        "JOY-M2-HKDSE-2013-PP-MS",
        "c16c2e8dcc40cc0a5da0bce2c88a45f95f29b4cb508c527ef4ca670b0085f66d",
        "e6b30bfc1553b4202db12db4fb3182eafeff7dcab0d4ef0acc7be6d33d3827a4",
        "task10b-hkdse-2013/canonical-v120-approved-v4-taxonomy",
        "task10a-v120-real-candidate-000002-hkdse-2013",
    ),
    (
        "JOY-M2-HKDSE-2014-PP-MS",
        "dfe2938b785bcc774b15d314bbab32648f9e615f015bb7f6d15135e51785cdcc",
        "12a6a2409c33f3644648f6e2a9da327ce54e559e016afff48a32b0e22ff92856",
        "task10b-hkdse-2014/canonical-v120-approved-v1",
        "task10a-v120-real-candidate-000003-hkdse-2014",
    ),
)


def _promotion_contract() -> V120PromotionContract:
    return V120PromotionContract(
        "V1.20", "task10-v120-formal-manifest-v1", "task10-v120-formal-v1",
        "task10-v120-promotion-identity-v1", "task10-v120-formal-rollback-v1",
        120, "Joy_M2_Complete_Question_DB_V1_20.sqlite3", "manifest.json",
        "SHA256SUMS.txt", "rollback.json", "images/sha256",
        "task10_v120_promoted_questions_v1", "task10_v120_promotion_v1",
        "formal_complete_questions_v120",
    )


def candidate_for(
    root: Path, *, materialize_candidates: bool = False,
) -> V120CandidateVerificationRequest:
    config = PipelineConfig(root)
    staging = root / "data/staging"
    baseline = root / "releases/V1.19/Joy_M2_Complete_Question_DB_V1_19.sqlite3"
    baseline_ref = ArtifactRef(baseline, BASELINE_SHA, baseline.stat().st_size, "sqlite")
    approved: list[V120ApprovedBatch] = []
    parent = None
    for batch_id, preflight_sha, parent_digest, package_name, candidate_name in REAL_BATCHES:
        package = staging / package_name
        manifest = load_v120_import_manifest(package / "import_manifest.json")
        result = preflight_v120_import(
            V120PreflightRequest(manifest, package, baseline_ref, parent, candidate_contract()),
            config,
        )
        if result.report.preflight_sha256 != preflight_sha:
            raise AssertionError("real preflight authority drift")
        statement = (
            f"USER APPROVED IMPORT BATCH {batch_id} {preflight_sha} "
            f"V1.20 PARENT {parent_digest}"
        )
        approved.append(V120ApprovedBatch(
            result, package,
            V120ImportApproval(batch_id, preflight_sha, "V1.20", parent_digest, statement),
        ))
        candidate_dir = staging / candidate_name
        if materialize_candidates:
            build_v120_candidate(
                V120CandidateBuildRequest(
                    tuple(approved), candidate_dir, candidate_contract(),
                ),
                config,
            )
        parent = V120CandidateVerificationRequest(
            candidate_dir, tuple(approved), candidate_contract(),
        )
        report = verify_v120_candidate(parent, config)
        if report.status != "PASS" or len(report.checks) != 24:
            raise AssertionError("real candidate verification drift")
    assert parent is not None
    return parent


def real_candidate() -> V120CandidateVerificationRequest:
    return candidate_for(ROOT)


def _tree(root: Path) -> tuple[tuple[str, str, int], ...]:
    return tuple(
        (
            path.relative_to(root).as_posix(),
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_size,
        )
        for path in sorted(root.rglob("*")) if path.is_file()
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )


def _rewrite_sums(root: Path, filename: str) -> None:
    paths = sorted(
        (
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path.name != filename
        ),
        key=lambda value: value.encode("utf-8"),
    )
    (root / filename).write_text(
        "".join(f"{_sha(root / path)}  {path}\n" for path in paths),
        encoding="utf-8",
    )


def _rebind_release(root: Path, contract: V120PromotionContract) -> None:
    manifest_path = root / contract.manifest_filename
    database_path = root / contract.database_filename
    rollback_path = root / contract.rollback_filename
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["database"].update({
        "sha256": _sha(database_path),
        "size_bytes": database_path.stat().st_size,
        "semantic_sha256": promotion_module._sqlite_semantic_sha256(
            database_path, contract.formal_view,
        ),
    })
    database_ref = {
        key: manifest["database"][key]
        for key in ("relative_path", "sha256", "size_bytes", "kind")
    }
    manifest["artifacts"] = [
        database_ref if item["kind"] == "sqlite" else item
        for item in manifest["artifacts"]
    ]
    payload = {
        "schema_version": contract.promotion_identity_schema,
        "release_version": "V1.20",
        "contract": {field.name: getattr(contract, field.name) for field in fields(contract)},
        "baseline": manifest["baseline"],
        "candidate": manifest["candidate"],
        "batch_ledger": manifest["batch_ledger"],
        "batch_authority_artifacts": manifest["batch_authority_artifacts"],
        "counts": manifest["counts"],
        "formal_sqlite_sha256": manifest["database"]["sha256"],
        "formal_sqlite_size_bytes": manifest["database"]["size_bytes"],
        "formal_sqlite_semantic_sha256": manifest["database"]["semantic_sha256"],
        "images": manifest["images"],
        "rollback_action": "remove_release_tree_if_release_digest_matches",
    }
    digest = hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8") + b"\n"
    ).hexdigest()
    manifest["promotion"]["release_digest"] = digest
    manifest["promotion"]["required_statement"] = (
        f"USER APPROVED RELEASE PROMOTION V1.20 {digest}"
    )
    rollback = json.loads(rollback_path.read_text(encoding="utf-8"))
    rollback["release_digest"] = digest
    _write_json(rollback_path, rollback)
    rollback_ref = {
        "relative_path": contract.rollback_filename,
        "sha256": _sha(rollback_path),
        "size_bytes": rollback_path.stat().st_size,
        "kind": "rollback",
    }
    manifest["rollback"] = rollback_ref
    manifest["artifacts"] = [
        rollback_ref if item["kind"] == "rollback" else item
        for item in manifest["artifacts"]
    ]
    _write_json(manifest_path, manifest)
    _rewrite_sums(root, contract.sha256s_filename)


class V120PromotionBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = PipelineConfig(ROOT)
        cls.candidate = real_candidate()
        cls.contract = _promotion_contract()

    def _build(self, output: Path):
        return build_v120_promotion(
            V120PromotionBuildRequest(self.candidate, output, self.contract),
            self.config,
        )

    def test_successful_build_has_exact_tree_and_21_pass_checks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            output = Path(directory) / "release"
            result = self._build(output)
            self.assertEqual(
                tuple(path.relative_to(output).as_posix() for path in sorted(output.rglob("*")) if path.is_file()),
                ("Joy_M2_Complete_Question_DB_V1_20.sqlite3", "SHA256SUMS.txt", "manifest.json", "rollback.json"),
            )
            self.assertEqual(result.verification_report.status, "PASS")
            self.assertEqual(tuple(check.name for check in result.verification_report.checks), CHECK_NAMES)
            self.assertTrue(all(check.passed for check in result.verification_report.checks))

    def test_formal_projection_preserves_502_and_promotes_exact_41(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            output = Path(directory) / "release"
            result = self._build(output)
            candidate_db = self.candidate.candidate_dir / "Joy_M2_V1.20_candidate.sqlite3"
            with closing(sqlite3.connect(candidate_db)) as source, closing(sqlite3.connect(result.database.path)) as formal:
                baseline = tuple(source.execute("SELECT * FROM formal_complete_questions_v119 ORDER BY formal_order"))
                actual = tuple(formal.execute("SELECT * FROM formal_complete_questions_v120 ORDER BY formal_order"))
                candidate_rows = tuple(source.execute("SELECT * FROM task10_candidate_questions_v120 ORDER BY formal_order"))[502:]
                self.assertEqual(actual[:502], baseline)
                self.assertEqual(len(actual), 543)
                self.assertTrue(all(row[-2:] == ("published", 1) for row in actual[502:]))
                for candidate_row, formal_row in zip(candidate_rows, actual[502:], strict=True):
                    self.assertEqual(formal_row[:2], candidate_row[:2])
                    self.assertEqual(formal_row[3:-2], candidate_row[3:-2])

    def test_two_builds_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            first = Path(directory) / "a"
            second = Path(directory) / "b"
            first_result = self._build(first)
            second_result = self._build(second)
            self.assertEqual(_tree(first), _tree(second))
            self.assertEqual(first_result.release_digest, second_result.release_digest)

    def test_older_candidate_generation_is_rejected_before_output(self) -> None:
        older = V120CandidateVerificationRequest(
            PY_STAGING / REAL_BATCHES[1][4], self.candidate.approved_batches[:2],
            candidate_contract(),
        )
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            output = Path(directory) / "release"
            with self.assertRaises(PromotionError):
                build_v120_promotion(
                    V120PromotionBuildRequest(older, output, self.contract), self.config,
                )
            self.assertFalse(output.exists())

    def test_candidate_bytes_and_ledger_authority_are_rejected_before_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            root = Path(directory)
            cases = ("database_bytes", "ledger_order", "ledger_parent", "ledger_approval")
            for case in cases:
                with self.subTest(case=case):
                    candidate_root = root / case / "candidate"
                    shutil.copytree(self.candidate.candidate_dir, candidate_root)
                    if case == "database_bytes":
                        with (candidate_root / self.candidate.contract.database_filename).open("ab") as handle:
                            handle.write(b"tampered")
                    else:
                        manifest_path = candidate_root / self.candidate.contract.manifest_filename
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        if case == "ledger_order":
                            manifest["batch_ledger"].reverse()
                        elif case == "ledger_parent":
                            manifest["batch_ledger"][1]["parent_candidate_digest"] = "0" * 64
                        else:
                            manifest["batch_ledger"][2]["approval"]["statement"] = "forged"
                        _write_json(manifest_path, manifest)
                    candidate = V120CandidateVerificationRequest(
                        candidate_root,
                        self.candidate.approved_batches,
                        self.candidate.contract,
                    )
                    output = root / case / "release"
                    with self.assertRaises(PromotionError):
                        build_v120_promotion(
                            V120PromotionBuildRequest(candidate, output, self.contract),
                            self.config,
                        )
                    self.assertFalse(output.exists())

    def test_output_must_not_overlap_candidate_authority(self) -> None:
        roots = (
            self.candidate.candidate_dir,
            PY_STAGING / REAL_BATCHES[0][4],
            PY_STAGING / REAL_BATCHES[1][4],
        )
        for root in roots:
            with self.subTest(root=root.name):
                output = root / "nested-release"
                with self.assertRaises(PipelineError):
                    self._build(output)
                self.assertFalse(output.exists())

    def test_existing_output_conflicts_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            output = Path(directory) / "release"
            output.mkdir()
            marker = output / "marker"
            marker.write_bytes(b"keep")
            with self.assertRaises(OutputConflictError):
                self._build(output)
            self.assertEqual(marker.read_bytes(), b"keep")

    def test_verifier_returns_fail_for_parsed_manifest_corruption(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            output = Path(directory) / "release"
            self._build(output)
            manifest = json.loads((output / "manifest.json").read_text())
            manifest["counts"]["formal_question_count"] = 542
            (output / "manifest.json").write_text(
                json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
            )
            report = verify_v120_promotion(
                V120PromotionVerificationRequest(output, self.candidate, self.contract),
                self.config,
            )
            self.assertEqual(report.status, "FAIL")
            self.assertFalse(next(check for check in report.checks if check.name == "manifest_contract").passed)

    def test_verifier_rejects_self_consistent_manifest_artifact_forgery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            output = Path(directory) / "release"
            self._build(output)
            manifest_path = output / self.contract.manifest_filename
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"] = []
            _write_json(manifest_path, manifest)
            _rewrite_sums(output, self.contract.sha256s_filename)

            report = verify_v120_promotion(
                V120PromotionVerificationRequest(output, self.candidate, self.contract),
                self.config,
            )
            self.assertEqual(report.status, "FAIL")
            self.assertFalse(
                next(check for check in report.checks if check.name == "manifest_contract").passed
            )

    def test_verifier_rejects_wrong_rollback_artifact_path_with_unchanged_digest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            output = Path(directory) / "release"
            result = self._build(output)
            manifest_path = output / self.contract.manifest_filename
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            forged = {
                "relative_path": self.contract.database_filename,
                "sha256": manifest["database"]["sha256"],
                "size_bytes": manifest["database"]["size_bytes"],
                "kind": "rollback",
            }
            manifest["rollback"] = forged
            manifest["artifacts"] = [
                forged if item["kind"] == "rollback" else item
                for item in manifest["artifacts"]
            ]
            _write_json(manifest_path, manifest)
            _rewrite_sums(output, self.contract.sha256s_filename)

            report = verify_v120_promotion(
                V120PromotionVerificationRequest(output, self.candidate, self.contract),
                self.config,
            )
            self.assertEqual(result.release_digest, manifest["promotion"]["release_digest"])
            self.assertEqual(report.status, "FAIL")
            self.assertFalse(
                next(check for check in report.checks if check.name == "manifest_contract").passed
            )

    def test_verifier_rejects_release_invented_image_with_reclosed_hashes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            output = Path(directory) / "release"
            self._build(output)
            image_bytes = b"release-invented-image"
            image_digest = hashlib.sha256(image_bytes).hexdigest()
            image_relative = f"images/sha256/{image_digest}.png"
            image_path = output / image_relative
            image_path.parent.mkdir(parents=True)
            image_path.write_bytes(image_bytes)
            image_ref = {
                "relative_path": image_relative,
                "sha256": image_digest,
                "size_bytes": len(image_bytes),
                "kind": "image",
            }
            manifest_path = output / self.contract.manifest_filename
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["images"] = [image_ref]
            manifest["artifacts"].append(image_ref)
            rollback_path = output / self.contract.rollback_filename
            rollback = json.loads(rollback_path.read_text(encoding="utf-8"))
            rollback["release_artifacts"] = sorted(
                [*rollback["release_artifacts"], image_relative],
                key=lambda value: value.encode("utf-8"),
            )
            _write_json(rollback_path, rollback)
            _write_json(manifest_path, manifest)
            _rebind_release(output, self.contract)

            report = verify_v120_promotion(
                V120PromotionVerificationRequest(output, self.candidate, self.contract),
                self.config,
            )
            self.assertEqual(report.status, "FAIL")
            self.assertFalse(
                next(check for check in report.checks if check.name == "manifest_contract").passed
            )

    def test_verifier_rejects_self_consistent_database_authority_forgery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            root = Path(directory)
            original = root / "original"
            self._build(original)
            mutations = {
                "rogue_schema": "CREATE TABLE task10c_rogue(value TEXT)",
                "metadata": (
                    "UPDATE release_metadata_v2 SET value='544' "
                    "WHERE key='formal_question_count'"
                ),
                "retained_taxonomy": (
                    "DELETE FROM task10_v120_taxonomy_v1 WHERE rowid=("
                    "SELECT MIN(rowid) FROM task10_v120_taxonomy_v1)"
                ),
            }
            for name, statement in mutations.items():
                with self.subTest(name=name):
                    release = root / name
                    shutil.copytree(original, release)
                    with sqlite3.connect(release / self.contract.database_filename) as database:
                        database.execute(statement)
                    _rebind_release(release, self.contract)
                    report = verify_v120_promotion(
                        V120PromotionVerificationRequest(
                            release, self.candidate, self.contract,
                        ),
                        self.config,
                    )
                    self.assertEqual(report.status, "FAIL")
                    failed = {check.name for check in report.checks if not check.passed}
                    self.assertTrue(
                        failed & {"sqlite_schema", "v119_preservation", "promotion_projection"}
                    )

    def test_builder_rejects_lexical_symlink_output_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            link = root / "link"
            link.symlink_to(real, target_is_directory=True)
            output = link / "release"
            with self.assertRaises(PipelineError):
                self._build(output)
            self.assertFalse((real / "release").exists())

    def test_verifier_returns_structured_fail_when_candidate_database_is_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            root = Path(directory)
            output = root / "release"
            self._build(output)
            incomplete = root / "candidate"
            incomplete.mkdir()
            shutil.copyfile(
                self.candidate.candidate_dir / self.candidate.contract.manifest_filename,
                incomplete / self.candidate.contract.manifest_filename,
            )
            candidate = V120CandidateVerificationRequest(
                incomplete, self.candidate.approved_batches, self.candidate.contract,
            )
            report = verify_v120_promotion(
                V120PromotionVerificationRequest(output, candidate, self.contract),
                self.config,
            )
            self.assertEqual(report.status, "FAIL")
            self.assertFalse(
                next(check for check in report.checks if check.name == "candidate_binding").passed
            )

    def test_verifier_rejects_missing_extra_symlink_rollback_and_database_corruption_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            root = Path(directory)
            original = root / "original"
            self._build(original)
            cases = ("missing", "extra", "symlink", "rollback", "database")
            for case in cases:
                with self.subTest(case=case):
                    release = root / case
                    shutil.copytree(original, release)
                    if case == "missing":
                        (release / "rollback.json").unlink()
                    elif case == "extra":
                        (release / "rogue.txt").write_bytes(b"rogue")
                    elif case == "symlink":
                        (release / "rogue-link").symlink_to("manifest.json")
                    elif case == "rollback":
                        payload = json.loads((release / "rollback.json").read_text())
                        payload["candidate_digest"] = "0" * 64
                        (release / "rollback.json").write_text(
                            json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
                        )
                    else:
                        database = release / self.contract.database_filename
                        with sqlite3.connect(database) as connection:
                            connection.execute(
                                "UPDATE task10_v120_promoted_questions_v1 "
                                "SET tags_json='[\"tampered\"]' WHERE formal_order=503"
                            )
                    before = _tree(release)
                    report = verify_v120_promotion(
                        V120PromotionVerificationRequest(release, self.candidate, self.contract),
                        self.config,
                    )
                    self.assertEqual(report.status, "FAIL")
                    self.assertEqual(_tree(release), before)

    def test_builder_post_rename_verification_failure_cleans_only_owned_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            output = Path(directory) / "release"
            import joy_m2.ingest.v120_promotion_verification as verifier_module

            real_verify = verifier_module.verify_v120_promotion
            calls = 0

            def fail_second(request, config):
                nonlocal calls
                calls += 1
                if calls == 2:
                    return VerificationReport(
                        "FAIL", (VerificationCheck("publication_boundary", False, "forced"),),
                    )
                return real_verify(request, config)

            with mock.patch(
                "joy_m2.ingest.v120_promotion_verification.verify_v120_promotion",
                side_effect=fail_second,
            ):
                with self.assertRaises(PromotionError):
                    self._build(output)
            self.assertFalse(output.exists())
            self.assertTrue(self.candidate.candidate_dir.is_dir())

    def test_builder_retains_changed_output_when_cleanup_ownership_is_lost(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task10c-red-", dir=PY_STAGING) as directory:
            output = Path(directory) / "release"
            import joy_m2.ingest.v120_promotion_verification as verifier_module

            real_verify = verifier_module.verify_v120_promotion
            calls = 0

            def mutate_second(request, config):
                nonlocal calls
                calls += 1
                if calls == 2:
                    (request.release_dir / "external-change.txt").write_bytes(b"retain")
                    return VerificationReport(
                        "FAIL", (VerificationCheck("publication_boundary", False, "forced"),),
                    )
                return real_verify(request, config)

            with mock.patch(
                "joy_m2.ingest.v120_promotion_verification.verify_v120_promotion",
                side_effect=mutate_second,
            ):
                with self.assertRaisesRegex(PromotionError, "cannot be cleaned safely"):
                    self._build(output)
            self.assertTrue((output / "external-change.txt").is_file())

    def test_release_digest_binds_exact_candidate_digest(self) -> None:
        manifest = json.loads(
            (self.candidate.candidate_dir / "candidate_manifest.json").read_text()
        )
        self.assertEqual(manifest["candidate_digest"], EXPECTED_CANDIDATE_DIGEST)

    def test_publication_requires_exact_gate_and_isolated_target_then_rollback_is_non_destructive(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="task10c-publication-", dir=PY_STAGING,
        ) as directory:
            isolated = Path(directory)
            shutil.copytree(ROOT / "releases/V1.19", isolated / "releases/V1.19")
            for _, _, _, package_name, _ in REAL_BATCHES:
                shutil.copytree(PY_STAGING / package_name, isolated / "data/staging" / package_name)

            config = PipelineConfig(isolated)
            candidate = candidate_for(isolated, materialize_candidates=True)
            dry_run = config.staging_root / "task10c-dry-run"
            artifacts = build_v120_promotion(
                V120PromotionBuildRequest(candidate, dry_run, self.contract), config,
            )
            baseline = config.releases_root / "V1.19/Joy_M2_Complete_Question_DB_V1_19.sqlite3"
            baseline_before = hashlib.sha256(baseline.read_bytes()).hexdigest()
            wrong = V120ReleasePromotionApproval(
                "V1.20", "0" * 64,
                "USER APPROVED RELEASE PROMOTION V1.20 " + "0" * 64,
            )
            with self.assertRaises(PromotionError):
                publish_v120_release(
                    V120PublicationRequest(dry_run, candidate, wrong, self.contract), config,
                )
            self.assertFalse((config.releases_root / "V1.20").exists())

            approval = V120ReleasePromotionApproval(
                "V1.20", artifacts.release_digest,
                f"USER APPROVED RELEASE PROMOTION V1.20 {artifacts.release_digest}",
            )
            published = publish_v120_release(
                V120PublicationRequest(dry_run, candidate, approval, self.contract), config,
            )
            target = config.releases_root / "V1.20"
            self.assertEqual(_tree(target), _tree(dry_run))
            self.assertEqual(published.release_digest, artifacts.release_digest)
            self.assertEqual(published.verification_report.status, "PASS")
            self.assertEqual(hashlib.sha256(baseline.read_bytes()).hexdigest(), baseline_before)

            rollback = json.loads((target / "rollback.json").read_text())
            self.assertEqual(rollback["release_digest"], artifacts.release_digest)
            self.assertEqual(rollback["action"], "remove_release_tree_if_release_digest_matches")
            shutil.rmtree(target)
            self.assertFalse(target.exists())
            self.assertEqual(hashlib.sha256(baseline.read_bytes()).hexdigest(), baseline_before)

            import joy_m2.ingest.v120_promotion_verification as verifier_module

            real_verify = verifier_module.verify_v120_promotion
            calls = 0

            def fail_unchanged_target(call_request, call_config):
                nonlocal calls
                calls += 1
                if calls == 2:
                    return VerificationReport(
                        "FAIL", (VerificationCheck("publication_boundary", False, "forced"),),
                    )
                return real_verify(call_request, call_config)

            with mock.patch(
                "joy_m2.ingest.v120_promotion_verification.verify_v120_promotion",
                side_effect=fail_unchanged_target,
            ):
                with self.assertRaises(PromotionError):
                    publish_v120_release(
                        V120PublicationRequest(
                            dry_run, candidate, approval, self.contract,
                        ),
                        config,
                    )
            self.assertFalse(target.exists())

            calls = 0

            def fail_changed_target(call_request, call_config):
                nonlocal calls
                calls += 1
                if calls == 2:
                    (call_request.release_dir / "external-change.txt").write_bytes(b"retain")
                    return VerificationReport(
                        "FAIL", (VerificationCheck("publication_boundary", False, "forced"),),
                    )
                return real_verify(call_request, call_config)

            with mock.patch(
                "joy_m2.ingest.v120_promotion_verification.verify_v120_promotion",
                side_effect=fail_changed_target,
            ):
                with self.assertRaisesRegex(PromotionError, "cannot be cleaned safely"):
                    publish_v120_release(
                        V120PublicationRequest(
                            dry_run, candidate, approval, self.contract,
                        ),
                        config,
                    )
            self.assertTrue((target / "external-change.txt").is_file())


if __name__ == "__main__":
    unittest.main()
