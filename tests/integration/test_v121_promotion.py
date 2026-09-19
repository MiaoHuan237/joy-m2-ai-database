"""End-to-end behavior contract for V1.21 formal promotion readiness."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path
import hashlib
import json
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import InputFormatError, OutputConflictError, PipelineError, PromotionError
from joy_m2.ingest import (
    V121ApprovedBatch,
    V121CandidateBuildRequest,
    V121CandidateVerificationRequest,
    V121ImportApproval,
    V121PreflightRequest,
    V121PromotionBuildRequest,
    V121PromotionContract,
    V121PromotionVerificationRequest,
    V121PublicationRequest,
    V121ReleasePromotionApproval,
    build_v121_candidate,
    build_v121_promotion,
    load_v121_import_manifest,
    preflight_v121_import,
    publish_v121_release,
    verify_v121_candidate,
    verify_v121_promotion,
)
from joy_m2.models import ArtifactRef, VerificationCheck, VerificationReport
from tests.integration.test_v121_preflight import (
    BASELINE,
    BASELINE_SHA,
    BASELINE_SIZE,
    _contract as candidate_contract,
)
import joy_m2.ingest.v121_promotion as promotion_module


STAGING = ROOT / "data/staging"
GENESIS = "331192032f184a44ed383e6dacc2f06fbacb60ad94414298fcb935ff56cb5906"
EXPECTED_CANDIDATE_DIGEST = "ecf624e3cb9fd8e7b1e0c664ddc5d51ef67f2d7f16f277c276be828eba32282c"
CHECK_NAMES = (
    "release_directory", "promotion_contract", "candidate_verification",
    "candidate_binding", "manifest_contract", "filesystem_closure",
    "sha256sums_closure", "artifact_references", "rollback_contract",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "v120_preservation", "batch_ledger_closure",
    "promotion_projection", "formal_query", "count_closure",
    "provenance_closure", "deterministic_identity", "publication_boundary",
)
REAL_BATCHES = (
    (2015, "6ea18e76837eefbfa9b2d124abe821a96da5ebc589e9fb14390045ff2110f257", GENESIS),
    (2016, "b65073283472cf9594d7bd6d0f142fe4aae94208f9f9dfebfa3f18b9425031a6", "2716ddff85775c15a332bcf7716749c6976d834ae8f20a114b64f108844c0e36"),
    (2017, "366fbb273ffc8f30b97aaae415c25e5c34897680bf217cfb6890bbf5fa3460f1", "59f424d5aae3fd67eddceef9202a4de63eb42899dcf7a9b0a78bbe567d39adb0"),
    (2018, "32808eeeace90852c8fa9749ad37c484f4ca90fe8c4a4c99f1645427c22a6108", "b9439dc14799504788d7a663b0bf789df2898dcf0d273dd4fac7fea9cb1dbcdf"),
)


def promotion_contract() -> V121PromotionContract:
    return V121PromotionContract(
        "V1.21", "task11-v121-formal-manifest-v1", "task11-v121-formal-v1",
        "task11-v121-promotion-identity-v1", "task11-v121-formal-rollback-v1",
        121, "Joy_M2_Complete_Question_DB_V1_21.sqlite3", "manifest.json",
        "SHA256SUMS.txt", "rollback.json", "images/sha256",
        "task11_v121_promoted_questions_v1", "task11_v121_promotion_v1",
        "formal_complete_questions_v121",
    )


def real_candidate(
    generations: int = 4,
    *,
    root: Path = ROOT,
    materialize: bool = False,
) -> V121CandidateVerificationRequest:
    config = PipelineConfig(root)
    staging = root / "data/staging"
    approved: list[V121ApprovedBatch] = []
    parent = None
    baseline = root / "releases/V1.20/Joy_M2_Complete_Question_DB_V1_20.sqlite3"
    baseline_ref = ArtifactRef(baseline, BASELINE_SHA, BASELINE_SIZE, "sqlite")
    for ordinal, (year, preflight_sha, parent_digest) in enumerate(REAL_BATCHES[:generations], 1):
        batch_root = staging / f"task11-v121-hkdse-{year}"
        package_name = (
            "canonical-v121-taxonomy-approved-a"
            if year == 2015
            else "canonical-v121-approved-a"
        )
        package = batch_root / package_name
        manifest = load_v121_import_manifest(package / "import_manifest.json")
        result = preflight_v121_import(
            V121PreflightRequest(
                manifest, package, baseline_ref, parent, candidate_contract(),
            ),
            config,
        )
        if result.report.preflight_sha256 != preflight_sha:
            raise AssertionError(f"{year} preflight authority drift")
        batch_id = f"JOY-M2-HKDSE-{year}-PP-MS"
        statement = (
            f"USER APPROVED IMPORT BATCH {batch_id} {preflight_sha} "
            f"V1.21 PARENT {parent_digest}"
        )
        approved.append(V121ApprovedBatch(
            result,
            package,
            V121ImportApproval(batch_id, preflight_sha, "V1.21", parent_digest, statement),
        ))
        candidate_dir = batch_root / f"candidate-generation-{ordinal:06d}"
        if materialize:
            build_v121_candidate(
                V121CandidateBuildRequest(
                    tuple(approved), candidate_dir, candidate_contract(),
                ),
                config,
            )
        parent = V121CandidateVerificationRequest(
            candidate_dir, tuple(approved), candidate_contract(),
        )
        report = verify_v121_candidate(parent, config)
        if report.status != "PASS" or len(report.checks) != 24:
            raise AssertionError(f"{year} candidate verification drift")
    assert parent is not None
    return parent


def tree(root: Path) -> tuple[tuple[str, str, int], ...]:
    return tuple(
        (
            path.relative_to(root).as_posix(),
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_size,
        )
        for path in sorted(root.rglob("*")) if path.is_file()
    )


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )


def rewrite_sums(root: Path, filename: str) -> None:
    paths = sorted(
        (
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path.name != filename
        ),
        key=lambda value: value.encode("utf-8"),
    )
    (root / filename).write_text(
        "".join(f"{sha(root / path)}  {path}\n" for path in paths),
        encoding="utf-8",
    )


def rebind_release(root: Path, contract: V121PromotionContract) -> None:
    manifest_path = root / contract.manifest_filename
    database_path = root / contract.database_filename
    rollback_path = root / contract.rollback_filename
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["database"].update({
        "sha256": sha(database_path),
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
        "release_version": "V1.21",
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
        f"USER APPROVED RELEASE PROMOTION V1.21 {digest}"
    )
    rollback = json.loads(rollback_path.read_text(encoding="utf-8"))
    rollback["release_digest"] = digest
    write_json(rollback_path, rollback)
    rollback_ref = {
        "relative_path": contract.rollback_filename,
        "sha256": sha(rollback_path),
        "size_bytes": rollback_path.stat().st_size,
        "kind": "rollback",
    }
    manifest["rollback"] = rollback_ref
    manifest["artifacts"] = [
        rollback_ref if item["kind"] == "rollback" else item
        for item in manifest["artifacts"]
    ]
    write_json(manifest_path, manifest)
    rewrite_sums(root, contract.sha256s_filename)


class V121PromotionBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = PipelineConfig(ROOT)
        cls.candidate = real_candidate()
        cls.contract = promotion_contract()

    def build(self, output: Path):
        return build_v121_promotion(
            V121PromotionBuildRequest(self.candidate, output, self.contract),
            self.config,
        )

    def test_successful_build_has_exact_tree_and_21_pass_checks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task11-promotion-red-", dir=STAGING) as directory:
            output = Path(directory) / "release"
            result = self.build(output)
            self.assertEqual(
                tuple(path.name for path in sorted(output.iterdir())),
                ("Joy_M2_Complete_Question_DB_V1_21.sqlite3", "SHA256SUMS.txt", "manifest.json", "rollback.json"),
            )
            self.assertEqual(result.verification_report.status, "PASS")
            self.assertEqual(tuple(check.name for check in result.verification_report.checks), CHECK_NAMES)
            self.assertTrue(all(check.passed for check in result.verification_report.checks))
            self.assertEqual(result.release_digest, json.loads((output / "manifest.json").read_text())["promotion"]["release_digest"])

    def test_formal_projection_preserves_543_and_promotes_exact_48(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task11-projection-red-", dir=STAGING) as directory:
            output = Path(directory) / "release"
            result = self.build(output)
            with sqlite3.connect(result.database.path) as database:
                self.assertEqual(database.execute("SELECT COUNT(*) FROM formal_complete_questions_v121").fetchone()[0], 591)
                self.assertEqual(database.execute("SELECT COUNT(*) FROM task11_v121_promoted_questions_v1").fetchone()[0], 48)
                self.assertEqual(database.execute("SELECT COUNT(*) FROM task11_v121_promoted_questions_v1 WHERE record_status='published' AND selectable=1").fetchone()[0], 48)
                self.assertEqual(database.execute("SELECT COUNT(*) FROM formal_complete_questions_v121 WHERE formal_order<=543").fetchone()[0], 543)
                self.assertEqual(database.execute("SELECT COUNT(*) FROM task11_v121_candidates_v1 WHERE record_status='candidate'").fetchone()[0], 48)

    def test_two_builds_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task11-determinism-red-", dir=STAGING) as directory:
            root = Path(directory)
            first = self.build(root / "a")
            second = self.build(root / "deep/b")
            self.assertEqual(tree(first.database.path.parent), tree(second.database.path.parent))
            self.assertEqual(first.release_digest, second.release_digest)

    def test_older_candidate_is_rejected_before_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task11-old-red-", dir=STAGING) as directory:
            output = Path(directory) / "release"
            request = V121PromotionBuildRequest(real_candidate(3), output, self.contract)
            with self.assertRaises(PipelineError):
                build_v121_promotion(request, self.config)
            self.assertFalse(output.exists())

    def test_output_conflict_and_candidate_overlap_reject_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task11-path-red-", dir=STAGING) as directory:
            root = Path(directory)
            existing = root / "existing"
            existing.mkdir()
            marker = existing / "marker"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(OutputConflictError):
                self.build(existing)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")
            overlap = self.candidate.candidate_dir / "nested-release"
            with self.assertRaises(PipelineError):
                self.build(overlap)
            self.assertFalse(overlap.exists())

    def test_candidate_bytes_and_ledger_authority_reject_before_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task11-candidate-red-", dir=STAGING) as directory:
            root = Path(directory)
            for case in ("database", "order", "parent", "approval", "count"):
                with self.subTest(case=case):
                    candidate_root = root / case / "candidate"
                    shutil.copytree(self.candidate.candidate_dir, candidate_root)
                    if case == "database":
                        with (candidate_root / self.candidate.contract.database_filename).open("ab") as stream:
                            stream.write(b"tamper")
                    else:
                        manifest_path = candidate_root / self.candidate.contract.manifest_filename
                        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                        if case == "order":
                            payload["batch_ledger"].reverse()
                        elif case == "parent":
                            payload["batch_ledger"][1]["parent_candidate_digest"] = "0" * 64
                        elif case == "approval":
                            payload["batch_ledger"][2]["approval"]["statement"] = "forged"
                        else:
                            payload["counts"]["batch_count"] = 3
                        write_json(manifest_path, payload)
                    candidate = V121CandidateVerificationRequest(
                        candidate_root,
                        self.candidate.approved_batches,
                        self.candidate.contract,
                    )
                    output = root / case / "release"
                    with self.assertRaises(PromotionError):
                        build_v121_promotion(
                            V121PromotionBuildRequest(candidate, output, self.contract),
                            self.config,
                        )
                    self.assertFalse(output.exists())

    def test_builder_rejects_lexical_symlink_output_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task11-symlink-red-", dir=STAGING) as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            link = root / "link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaises(PipelineError):
                self.build(link / "release")
            self.assertFalse((real / "release").exists())

    def test_verifier_preserves_malformed_json_exception_boundary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task11-json-red-", dir=STAGING) as directory:
            output = Path(directory) / "release"
            self.build(output)
            (output / "manifest.json").write_bytes(b"{")
            with self.assertRaises(InputFormatError):
                verify_v121_promotion(
                    V121PromotionVerificationRequest(output, self.candidate, self.contract),
                    self.config,
                )

    def test_parsed_invalid_and_artifact_corruption_are_structured_fail_without_mutation(self) -> None:
        for case in ("wrong-status", "missing", "extra", "database"):
            with self.subTest(case=case), tempfile.TemporaryDirectory(prefix="task11-corrupt-red-", dir=STAGING) as directory:
                output = Path(directory) / "release"
                self.build(output)
                if case == "wrong-status":
                    manifest = output / "manifest.json"
                    payload = json.loads(manifest.read_text(encoding="utf-8"))
                    payload["release_status"] = []
                    manifest.write_text(json.dumps(payload), encoding="utf-8")
                elif case == "missing":
                    (output / "rollback.json").unlink()
                elif case == "extra":
                    (output / "extra.txt").write_text("rogue", encoding="utf-8")
                else:
                    with (output / self.contract.database_filename).open("ab") as stream:
                        stream.write(b"tamper")
                before = tree(output)
                report = verify_v121_promotion(
                    V121PromotionVerificationRequest(output, self.candidate, self.contract),
                    self.config,
                )
                self.assertEqual(report.status, "FAIL")
                self.assertEqual(tree(output), before)

    def test_verifier_rejects_self_consistent_database_authority_forgery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task11-forgery-red-", dir=STAGING) as directory:
            root = Path(directory)
            original = root / "original"
            self.build(original)
            mutations = {
                "rogue_schema": "CREATE TABLE task11_rogue(value TEXT)",
                "metadata": (
                    "UPDATE release_metadata_v2 SET value='592' "
                    "WHERE key='formal_question_count'"
                ),
                "taxonomy": (
                    "DELETE FROM task11_v121_taxonomy_v1 WHERE rowid=("
                    "SELECT MIN(rowid) FROM task11_v121_taxonomy_v1)"
                ),
                "status": (
                    "UPDATE task11_v121_promoted_questions_v1 SET tags_json='[\"tampered\"]' "
                    "WHERE formal_order=544"
                ),
            }
            for name, statement in mutations.items():
                with self.subTest(name=name):
                    release = root / name
                    shutil.copytree(original, release)
                    with sqlite3.connect(release / self.contract.database_filename) as database:
                        database.execute(statement)
                    rebind_release(release, self.contract)
                    before = tree(release)
                    report = verify_v121_promotion(
                        V121PromotionVerificationRequest(release, self.candidate, self.contract),
                        self.config,
                    )
                    self.assertEqual(report.status, "FAIL")
                    self.assertEqual(tree(release), before)
                    failed = {check.name for check in report.checks if not check.passed}
                    self.assertTrue(
                        failed & {"sqlite_schema", "v120_preservation", "promotion_projection"}
                    )

    def test_verifier_missing_candidate_database_is_structured_fail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task11-missing-candidate-red-", dir=STAGING) as directory:
            root = Path(directory)
            output = root / "release"
            self.build(output)
            incomplete = root / "candidate"
            incomplete.mkdir()
            shutil.copyfile(
                self.candidate.candidate_dir / self.candidate.contract.manifest_filename,
                incomplete / self.candidate.contract.manifest_filename,
            )
            candidate = V121CandidateVerificationRequest(
                incomplete, self.candidate.approved_batches, self.candidate.contract,
            )
            report = verify_v121_promotion(
                V121PromotionVerificationRequest(output, candidate, self.contract),
                self.config,
            )
            self.assertEqual(report.status, "FAIL")
            self.assertFalse(next(
                check for check in report.checks if check.name == "candidate_binding"
            ).passed)

    def test_private_build_failure_cleans_owned_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task11-cleanup-red-", dir=STAGING) as directory:
            output = Path(directory) / "release"
            with mock.patch(
                "joy_m2.ingest.v121_promotion_verification.verify_v121_promotion",
                return_value=VerificationReport("FAIL", (VerificationCheck("forced", False, "forced"),)),
            ):
                with self.assertRaises(PipelineError):
                    self.build(output)
            self.assertFalse(output.exists())

    def test_post_rename_failure_cleans_unchanged_but_retains_changed_output(self) -> None:
        import joy_m2.ingest.v121_promotion_verification as verifier_module

        real_verify = verifier_module.verify_v121_promotion
        for changed in (False, True):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory(prefix="task11-rename-red-", dir=STAGING) as directory:
                output = Path(directory) / "release"
                calls = 0

                def fail_second(request, config):
                    nonlocal calls
                    calls += 1
                    if calls == 2:
                        if changed:
                            (request.release_dir / "external-change.txt").write_text("retain")
                        return VerificationReport(
                            "FAIL", (VerificationCheck("publication_boundary", False, "forced"),),
                        )
                    return real_verify(request, config)

                with mock.patch(
                    "joy_m2.ingest.v121_promotion_verification.verify_v121_promotion",
                    side_effect=fail_second,
                ):
                    if changed:
                        with self.assertRaisesRegex(PromotionError, "cannot be cleaned safely"):
                            self.build(output)
                        self.assertTrue((output / "external-change.txt").is_file())
                    else:
                        with self.assertRaises(PromotionError):
                            self.build(output)
                        self.assertFalse(output.exists())

    def test_publication_requires_exact_gate_and_preserves_v120(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task11-publish-red-", dir=STAGING) as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "releases/V1.20", root / "releases/V1.20")
            for year, _, _ in REAL_BATCHES:
                package_name = (
                    "canonical-v121-taxonomy-approved-a"
                    if year == 2015
                    else "canonical-v121-approved-a"
                )
                shutil.copytree(
                    STAGING / f"task11-v121-hkdse-{year}" / package_name,
                    root / "data/staging" / f"task11-v121-hkdse-{year}" / package_name,
                )
            config = PipelineConfig(root)
            candidate = real_candidate(root=root, materialize=True)
            dry_run = root / "data/staging/dry-run"
            artifacts = build_v121_promotion(
                V121PromotionBuildRequest(candidate, dry_run, self.contract), config,
            )
            baseline = root / "releases/V1.20/Joy_M2_Complete_Question_DB_V1_20.sqlite3"
            baseline_before = hashlib.sha256(baseline.read_bytes()).hexdigest()
            approval = V121ReleasePromotionApproval(
                "V1.21",
                artifacts.release_digest,
                f"USER APPROVED RELEASE PROMOTION V1.21 {artifacts.release_digest}",
            )
            published = publish_v121_release(
                V121PublicationRequest(dry_run, candidate, approval, self.contract), config,
            )
            self.assertEqual(published.verification_report.status, "PASS")
            self.assertEqual(tree(dry_run), tree(root / "releases/V1.21"))
            self.assertEqual(hashlib.sha256(baseline.read_bytes()).hexdigest(), baseline_before)
            wrong = V121ReleasePromotionApproval(
                "V1.21", "1" * 64,
                f"USER APPROVED RELEASE PROMOTION V1.21 {'1' * 64}",
            )
            with self.assertRaises(PromotionError):
                publish_v121_release(
                    V121PublicationRequest(dry_run, candidate, wrong, self.contract), config,
                )


if __name__ == "__main__":
    unittest.main()
