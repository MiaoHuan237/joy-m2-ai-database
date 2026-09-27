"""End-to-end behavior contract for V1.22 formal promotion readiness."""

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
    V122ApprovedBatch,
    V122CandidateVerificationRequest,
    V122ImportApproval,
    V122PreflightRequest,
    V122PromotionBuildRequest,
    V122PromotionContract,
    V122PromotionVerificationRequest,
    V122PublicationRequest,
    V122ReleasePromotionApproval,
    build_v122_promotion,
    load_v122_import_manifest,
    preflight_v122_import,
    publish_v122_release,
    verify_v122_candidate,
    verify_v122_promotion,
)
from joy_m2.models import ArtifactRef, VerificationCheck, VerificationReport
from tests.integration.test_v122_preflight import (
    BASELINE,
    BASELINE_SHA,
    BASELINE_SIZE,
    _contract as candidate_contract,
)
import joy_m2.ingest.v122_promotion as promotion_module


STAGING = ROOT / "data/staging"
GENESIS = "7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7"
EXPECTED_CANDIDATE_DIGEST = "82b10a551f70eebda2e0aa4d10c962e317767e936b4f0d9aa798629bb8070d46"
CHECK_NAMES = (
    "release_directory", "promotion_contract", "candidate_verification",
    "candidate_binding", "manifest_contract", "filesystem_closure",
    "sha256sums_closure", "artifact_references", "rollback_contract",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "v121_preservation", "batch_ledger_closure",
    "promotion_projection", "formal_query", "count_closure",
    "provenance_closure", "deterministic_identity", "publication_boundary",
)
REAL_BATCHES = (
    (2019, "674624abcd338b2fa3683b982300a30082e3d0e62f95f97e3e8d25e12d1d0fa5", GENESIS),
    (2020, "f57e4aea6fa36d3721ca6705214c47316010a2db58ed7a092fe08f2e68d63530", "83c5efa109132c85dca8b96679ac97d4d9a59dd94e0cc76a57c80871a944ff07"),
    (2021, "f2d387304b68d3648bd2501a52aa0517e3218ac71833c78a322450603010b6b6", "877cafa7425b53a08835277c828b346f29112ecbfce82ae861336a2575047cfc"),
    (2022, "ae96a9a971fafdd6e900ced6f80ee39d4c1365e166b5d4efa7fbcc47383b1fad", "20342ba339ef8200ee6d941683d12698c2504c0872548a26717b2771ee2d1707"),
)


def promotion_contract() -> V122PromotionContract:
    return V122PromotionContract(
        "V1.22", "task12-v122-formal-manifest-v1", "task12-v122-formal-v1",
        "task12-v122-promotion-identity-v1", "task12-v122-formal-rollback-v1",
        122, "Joy_M2_Complete_Question_DB_V1_22.sqlite3", "manifest.json",
        "SHA256SUMS.txt", "rollback.json", "images/sha256",
        "task12_v122_promoted_questions_v1", "task12_v122_promotion_v1",
        "formal_complete_questions_v122",
    )


def real_candidate(
    generations: int = 4,
    *,
    root: Path = ROOT,
) -> V122CandidateVerificationRequest:
    config = PipelineConfig(root)
    staging = root / "data/staging"
    approved: list[V122ApprovedBatch] = []
    parent = None
    baseline = root / "releases/V1.21/Joy_M2_Complete_Question_DB_V1_21.sqlite3"
    baseline_ref = ArtifactRef(baseline, BASELINE_SHA, BASELINE_SIZE, "sqlite")
    for ordinal, (year, preflight_sha, parent_digest) in enumerate(REAL_BATCHES[:generations], 1):
        batch_root = staging / f"task12-v122-hkdse-{year}"
        package_name = "canonical-v122-approved-a"
        package = batch_root / package_name
        manifest = load_v122_import_manifest(package / "import_manifest.json")
        result = preflight_v122_import(
            V122PreflightRequest(
                manifest, package, baseline_ref, parent, candidate_contract(),
            ),
            config,
        )
        if result.report.preflight_sha256 != preflight_sha:
            raise AssertionError(f"{year} preflight authority drift")
        batch_id = f"JOY-M2-HKDSE-{year}-PP-MS"
        statement = (
            f"USER APPROVED IMPORT BATCH {batch_id} {preflight_sha} "
            f"V1.22 PARENT {parent_digest}"
        )
        approved.append(V122ApprovedBatch(
            result,
            package,
            V122ImportApproval(batch_id, preflight_sha, "V1.22", parent_digest, statement),
        ))
        candidate_dir = batch_root / f"candidate-generation-{ordinal:06d}"
        parent = V122CandidateVerificationRequest(
            candidate_dir, tuple(approved), candidate_contract(),
        )
        report = verify_v122_candidate(parent, config)
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


def rebind_release(root: Path, contract: V122PromotionContract) -> None:
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
        "release_version": "V1.22",
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
        f"USER APPROVED RELEASE PROMOTION V1.22 {digest}"
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


class V122PromotionBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = PipelineConfig(ROOT)
        cls.candidate = real_candidate()
        cls.contract = promotion_contract()

    def build(self, output: Path):
        result = build_v122_promotion(
            V122PromotionBuildRequest(self.candidate, output, self.contract),
            self.config,
        )
        self.assertIsNotNone(result, 'builder behavior is not implemented')
        return result

    def test_successful_build_has_exact_tree_and_21_pass_checks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task12-promotion-red-", dir=STAGING) as directory:
            output = Path(directory) / "release"
            result = self.build(output)
            self.assertEqual(
                tuple(path.name for path in sorted(output.iterdir())),
                ("Joy_M2_Complete_Question_DB_V1_22.sqlite3", "SHA256SUMS.txt", "manifest.json", "rollback.json"),
            )
            self.assertEqual(result.verification_report.status, "PASS")
            self.assertEqual(tuple(check.name for check in result.verification_report.checks), CHECK_NAMES)
            self.assertTrue(all(check.passed for check in result.verification_report.checks))
            self.assertEqual(result.release_digest, json.loads((output / "manifest.json").read_text())["promotion"]["release_digest"])

    def test_formal_projection_preserves_591_and_promotes_exact_48(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task12-projection-red-", dir=STAGING) as directory:
            output = Path(directory) / "release"
            result = self.build(output)
            with sqlite3.connect(result.database.path) as database:
                self.assertEqual(database.execute("SELECT COUNT(*) FROM formal_complete_questions_v122").fetchone()[0], 639)
                self.assertEqual(database.execute("SELECT COUNT(*) FROM task12_v122_promoted_questions_v1").fetchone()[0], 48)
                self.assertEqual(database.execute("SELECT COUNT(*) FROM task12_v122_promoted_questions_v1 WHERE record_status='published' AND selectable=1").fetchone()[0], 48)
                self.assertEqual(database.execute("SELECT COUNT(*) FROM formal_complete_questions_v122 WHERE formal_order<=591").fetchone()[0], 591)
                self.assertEqual(database.execute("SELECT COUNT(*) FROM task12_v122_candidates_v1 WHERE record_status='candidate'").fetchone()[0], 48)

    def test_two_builds_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task12-determinism-red-", dir=STAGING) as directory:
            root = Path(directory)
            first = self.build(root / "a")
            second = self.build(root / "deep/b")
            self.assertEqual(tree(first.database.path.parent), tree(second.database.path.parent))
            self.assertEqual(first.release_digest, second.release_digest)

    def test_older_candidate_is_rejected_before_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task12-old-red-", dir=STAGING) as directory:
            output = Path(directory) / "release"
            request = V122PromotionBuildRequest(real_candidate(3), output, self.contract)
            with self.assertRaises(PipelineError):
                build_v122_promotion(request, self.config)
            self.assertFalse(output.exists())

    def test_output_conflict_and_candidate_overlap_reject_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task12-path-red-", dir=STAGING) as directory:
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
        with tempfile.TemporaryDirectory(prefix="task12-candidate-red-", dir=STAGING) as directory:
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
                    candidate = V122CandidateVerificationRequest(
                        candidate_root,
                        self.candidate.approved_batches,
                        self.candidate.contract,
                    )
                    output = root / case / "release"
                    with self.assertRaises(PromotionError):
                        build_v122_promotion(
                            V122PromotionBuildRequest(candidate, output, self.contract),
                            self.config,
                        )
                    self.assertFalse(output.exists())

    def test_builder_rejects_lexical_symlink_output_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task12-symlink-red-", dir=STAGING) as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            link = root / "link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaises(PipelineError):
                self.build(link / "release")
            self.assertFalse((real / "release").exists())

    def test_verifier_preserves_malformed_json_exception_boundary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task12-json-red-", dir=STAGING) as directory:
            output = Path(directory) / "release"
            self.build(output)
            (output / "manifest.json").write_bytes(b"{")
            with self.assertRaises(InputFormatError):
                verify_v122_promotion(
                    V122PromotionVerificationRequest(output, self.candidate, self.contract),
                    self.config,
                )

    def test_parsed_invalid_and_artifact_corruption_are_structured_fail_without_mutation(self) -> None:
        for case in (
            "wrong-status", "wrong-images", "wrong-image-entry", "wrong-database-ref",
            "wrong-ledger", "missing", "extra", "database",
        ):
            with self.subTest(case=case), tempfile.TemporaryDirectory(prefix="task12-corrupt-red-", dir=STAGING) as directory:
                output = Path(directory) / "release"
                self.build(output)
                if case == "wrong-status":
                    manifest = output / "manifest.json"
                    payload = json.loads(manifest.read_text(encoding="utf-8"))
                    payload["release_status"] = []
                    manifest.write_text(json.dumps(payload), encoding="utf-8")
                elif case == "wrong-images":
                    manifest = output / "manifest.json"
                    payload = json.loads(manifest.read_text(encoding="utf-8"))
                    payload["images"] = True
                    manifest.write_text(json.dumps(payload), encoding="utf-8")
                elif case == "wrong-image-entry":
                    manifest = output / "manifest.json"
                    payload = json.loads(manifest.read_text(encoding="utf-8"))
                    payload["images"] = [{"relative_path": []}]
                    manifest.write_text(json.dumps(payload), encoding="utf-8")
                elif case == "wrong-database-ref":
                    manifest = output / "manifest.json"
                    payload = json.loads(manifest.read_text(encoding="utf-8"))
                    payload["database"] = {}
                    manifest.write_text(json.dumps(payload), encoding="utf-8")
                elif case == "wrong-ledger":
                    manifest = output / "manifest.json"
                    payload = json.loads(manifest.read_text(encoding="utf-8"))
                    payload["batch_ledger"] = [True]
                    manifest.write_text(json.dumps(payload), encoding="utf-8")
                elif case == "missing":
                    (output / "rollback.json").unlink()
                elif case == "extra":
                    (output / "extra.txt").write_text("rogue", encoding="utf-8")
                else:
                    with (output / self.contract.database_filename).open("ab") as stream:
                        stream.write(b"tamper")
                before = tree(output)
                report = verify_v122_promotion(
                    V122PromotionVerificationRequest(output, self.candidate, self.contract),
                    self.config,
                )
                self.assertEqual(report.status, "FAIL")
                self.assertEqual(tree(output), before)

    def test_verifier_rejects_self_consistent_database_authority_forgery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task12-forgery-red-", dir=STAGING) as directory:
            root = Path(directory)
            original = root / "original"
            self.build(original)
            mutations = {
                "rogue_schema": "CREATE TABLE task12_rogue(value TEXT)",
                "metadata": (
                    "UPDATE release_metadata_v2 SET value='640' "
                    "WHERE key='formal_question_count'"
                ),
                "taxonomy": (
                    "DELETE FROM task12_v122_taxonomy_v1 WHERE rowid=("
                    "SELECT MIN(rowid) FROM task12_v122_taxonomy_v1)"
                ),
                "status": (
                    "UPDATE task12_v122_promoted_questions_v1 SET tags_json='[\"tampered\"]' "
                    "WHERE formal_order=592"
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
                    report = verify_v122_promotion(
                        V122PromotionVerificationRequest(release, self.candidate, self.contract),
                        self.config,
                    )
                    self.assertEqual(report.status, "FAIL")
                    self.assertEqual(tree(release), before)
                    failed = {check.name for check in report.checks if not check.passed}
                    self.assertTrue(
                        failed & {"sqlite_schema", "v121_preservation", "promotion_projection"}
                    )

    def test_verifier_missing_candidate_database_is_structured_fail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task12-missing-candidate-red-", dir=STAGING) as directory:
            root = Path(directory)
            output = root / "release"
            self.build(output)
            incomplete = root / "candidate"
            incomplete.mkdir()
            shutil.copyfile(
                self.candidate.candidate_dir / self.candidate.contract.manifest_filename,
                incomplete / self.candidate.contract.manifest_filename,
            )
            candidate = V122CandidateVerificationRequest(
                incomplete, self.candidate.approved_batches, self.candidate.contract,
            )
            report = verify_v122_promotion(
                V122PromotionVerificationRequest(output, candidate, self.contract),
                self.config,
            )
            self.assertEqual(report.status, "FAIL")
            self.assertFalse(next(
                check for check in report.checks if check.name == "candidate_binding"
            ).passed)

    def test_verifier_parsed_invalid_candidate_manifest_is_structured_fail(self) -> None:
        for missing_key in ("baseline", "batch_ledger", "batch_authority_artifacts"):
            with self.subTest(missing_key=missing_key), tempfile.TemporaryDirectory(
                prefix="task12-candidate-manifest-red-", dir=STAGING,
            ) as directory:
                root = Path(directory)
                candidate_root = root / "candidate"
                shutil.copytree(self.candidate.candidate_dir, candidate_root)
                manifest_path = candidate_root / self.candidate.contract.manifest_filename
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                payload.pop(missing_key)
                write_json(manifest_path, payload)
                candidate = V122CandidateVerificationRequest(
                    candidate_root,
                    self.candidate.approved_batches,
                    self.candidate.contract,
                )
                release = root / "release"
                fixture_release(release, self.candidate, self.contract)
                report = verify_v122_promotion(
                    V122PromotionVerificationRequest(release, candidate, self.contract),
                    self.config,
                )
                self.assertEqual(report.status, "FAIL")
                self.assertFalse(next(
                    check for check in report.checks if check.name == "candidate_verification"
                ).passed)
                self.assertFalse(next(
                    check for check in report.checks if check.name == "candidate_binding"
                ).passed)

    def test_private_build_failure_cleans_owned_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task12-cleanup-red-", dir=STAGING) as directory:
            output = Path(directory) / "release"
            with mock.patch(
                "joy_m2.ingest.v122_promotion_verification.verify_v122_promotion",
                return_value=VerificationReport("FAIL", (VerificationCheck("forced", False, "forced"),)),
            ):
                with self.assertRaises(PipelineError):
                    self.build(output)
            self.assertFalse(output.exists())

    def test_no_replace_race_preserves_identical_competing_output(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as d:
            output = Path(d) / "release"
            def competing_writer(private, target):
                shutil.copytree(private, target)
                raise OutputConflictError("another writer won")
            with mock.patch("joy_m2.ingest.v122_promotion.atomic_rename_no_replace",
                            side_effect=competing_writer):
                with self.assertRaises(OutputConflictError):
                    self.build(output)
            self.assertTrue(output.is_dir(), "must not delete another writer's identical tree")
            self.assertEqual({p.name for p in output.iterdir()},
                {"Joy_M2_Complete_Question_DB_V1_22.sqlite3","manifest.json","SHA256SUMS.txt","rollback.json"})

    def test_post_rename_failure_cleans_unchanged_but_retains_changed_output(self) -> None:
        import joy_m2.ingest.v122_promotion_verification as verifier_module

        real_verify = verifier_module.verify_v122_promotion
        for changed in (False, True):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory(prefix="task12-rename-red-", dir=STAGING) as directory:
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
                    "joy_m2.ingest.v122_promotion_verification.verify_v122_promotion",
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

    def test_publication_requires_exact_gate_and_preserves_v121(self) -> None:
        with tempfile.TemporaryDirectory(prefix="task12-publish-red-", dir=STAGING) as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "releases/V1.21", root / "releases/V1.21")
            for year, _, _ in REAL_BATCHES:
                package_name = "canonical-v122-approved-a"
                shutil.copytree(
                    STAGING / f"task12-v122-hkdse-{year}" / package_name,
                    root / "data/staging" / f"task12-v122-hkdse-{year}" / package_name,
                )
            config = PipelineConfig(root)
            for ordinal, (year, _, _) in enumerate(REAL_BATCHES, 1):
                relative = Path("data/staging") / f"task12-v122-hkdse-{year}" / f"candidate-generation-{ordinal:06d}"
                shutil.copytree(ROOT / relative, root / relative)
            candidate = real_candidate(root=root)
            dry_run = root / "data/staging/dry-run"
            artifacts = build_v122_promotion(
                V122PromotionBuildRequest(candidate, dry_run, self.contract), config,
            )
            baseline = root / "releases/V1.21/Joy_M2_Complete_Question_DB_V1_21.sqlite3"
            baseline_before = hashlib.sha256(baseline.read_bytes()).hexdigest()
            approval = V122ReleasePromotionApproval(
                "V1.22",
                artifacts.release_digest,
                f"USER APPROVED RELEASE PROMOTION V1.22 {artifacts.release_digest}",
            )
            published = publish_v122_release(
                V122PublicationRequest(dry_run, candidate, approval, self.contract), config,
            )
            self.assertIsNotNone(published, "publication behavior is not implemented")
            self.assertEqual(published.verification_report.status, "PASS")
            self.assertEqual(tree(dry_run), tree(root / "releases/V1.22"))
            self.assertEqual(hashlib.sha256(baseline.read_bytes()).hexdigest(), baseline_before)
            wrong = V122ReleasePromotionApproval(
                "V1.22", "1" * 64,
                f"USER APPROVED RELEASE PROMOTION V1.22 {'1' * 64}",
            )
            with self.assertRaises(PromotionError):
                publish_v122_release(
                    V122PublicationRequest(dry_run, candidate, wrong, self.contract), config,
                )


# Independent test-owned fixture literals/serialization from the pinned counterpart.
# No V122 builder or verifier helper is used to construct the verifier oracle.
from contextlib import closing
import math
import re
from pathlib import PurePosixPath

BASELINE_SHA256 = "93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a"
BASELINE_RELEASE_DIGEST = "f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3"
BASELINE_SIZE = 10_063_872
BASELINE_MANIFEST_SHA256 = "a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40"
BASELINE_MANIFEST_SIZE = 7_913
CANDIDATE_DIGEST = "82b10a551f70eebda2e0aa4d10c962e317767e936b4f0d9aa798629bb8070d46"
CANDIDATE_SHA256 = "f1adf0ff7c2034445b1ee4724c03e8c66c6026c5e94d37cc469e1b350c2a9a7a"
CANDIDATE_MANIFEST_SHA256 = "dc974a1f3180fc3d7d416385242d21aec78266f4e52f5a9de5732f31d57a5403"
CANDIDATE_SIZE = 10_330_112
CANDIDATE_MANIFEST_SIZE = 6_851

PROMOTION_TABLE_SQL = """CREATE TABLE task12_v122_promotion_v1 (
    release_version TEXT PRIMARY KEY CHECK(release_version='V1.22'),
    formal_database_schema TEXT NOT NULL CHECK(formal_database_schema='task12-v122-formal-v1'),
    release_model TEXT NOT NULL CHECK(release_model='append-only-multi-batch-promotion'),
    release_status TEXT NOT NULL CHECK(release_status='published'),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version='V1.21'),
    baseline_database_sha256 TEXT NOT NULL CHECK(baseline_database_sha256='93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a'),
    baseline_release_digest TEXT NOT NULL CHECK(baseline_release_digest='f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count=591),
    candidate_digest TEXT NOT NULL CHECK(candidate_digest='82b10a551f70eebda2e0aa4d10c962e317767e936b4f0d9aa798629bb8070d46'),
    candidate_database_sha256 TEXT NOT NULL CHECK(candidate_database_sha256='f1adf0ff7c2034445b1ee4724c03e8c66c6026c5e94d37cc469e1b350c2a9a7a'),
    candidate_database_size INTEGER NOT NULL CHECK(candidate_database_size=10330112),
    candidate_manifest_sha256 TEXT NOT NULL CHECK(candidate_manifest_sha256='dc974a1f3180fc3d7d416385242d21aec78266f4e52f5a9de5732f31d57a5403'),
    candidate_manifest_size INTEGER NOT NULL CHECK(candidate_manifest_size=6851),
    accepted_batch_count INTEGER NOT NULL CHECK(accepted_batch_count=4),
    promoted_question_count INTEGER NOT NULL CHECK(promoted_question_count=48),
    formal_question_count INTEGER NOT NULL CHECK(formal_question_count=639)
)"""

PROMOTED_TABLE_SQL = """CREATE TABLE task12_v122_promoted_questions_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal BETWEEN 1 AND 4),
    batch_id TEXT NOT NULL,
    batch_candidate_order INTEGER NOT NULL CHECK(batch_candidate_order>=0),
    formal_order INTEGER PRIMARY KEY CHECK(formal_order BETWEEN 592 AND 639),
    question_id TEXT NOT NULL UNIQUE,
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
    source_image_paths_json TEXT NOT NULL,
    source_image_sha256s_json TEXT NOT NULL,
    source_image_roles_json TEXT NOT NULL,
    primary_type TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    tag_status TEXT NOT NULL CHECK(tag_status IN ('source_provided','proposed','missing')),
    difficulty_level INTEGER CHECK(difficulty_level BETWEEN 1 AND 5 OR difficulty_level IS NULL),
    difficulty_status TEXT NOT NULL CHECK(difficulty_status IN ('source_provided','proposed','missing')),
    enrichment_status TEXT NOT NULL CHECK(enrichment_status IN ('complete','incomplete')),
    formal_image_paths_json TEXT NOT NULL,
    record_status TEXT NOT NULL CHECK(record_status='published'),
    selectable INTEGER NOT NULL CHECK(selectable=1),
    UNIQUE(batch_ordinal,batch_candidate_order),
    FOREIGN KEY(batch_ordinal,batch_id)
        REFERENCES task12_v122_batch_ledger_v1(batch_ordinal,batch_id)
)"""

FORMAL_VIEW_SQL = """CREATE VIEW formal_complete_questions_v122 AS
SELECT * FROM formal_complete_questions_v121
UNION ALL
SELECT
    p.formal_order,
    p.question_id,
    'task12_v122_promoted' AS authority_kind,
    p.batch_id,
    p.batch_candidate_order AS candidate_order,
    p.source_id,
    p.source_question_number,
    p.source_section,
    p.source_fragment_hash,
    p.normalized_text_sha256,
    p.question_text_original,
    p.question_text_zh,
    CAST(NULL AS TEXT) AS question_text_zh_reviewed,
    p.translation_status,
    p.translation_evidence,
    p.solution_original,
    p.solution_verified,
    p.answer_status,
    p.explanation_text,
    p.explanation_status,
    p.explanation_evidence,
    p.source_image_paths_json,
    p.source_image_sha256s_json,
    p.source_image_roles_json,
    p.primary_type,
    p.tags_json,
    p.tag_status,
    p.difficulty_level,
    p.difficulty_status,
    p.enrichment_status,
    p.formal_image_paths_json,
    p.record_status,
    p.selectable
FROM task12_v122_promoted_questions_v1 AS p
ORDER BY formal_order"""

_ASCII_SPACE = re.compile(r"[ \t\r\n\f\v]+")

def _normalize_sql(value: str) -> str:
    normalized = _ASCII_SPACE.sub(" ", value).strip(" ")
    if normalized.endswith(";"):
        normalized = normalized[:-1].rstrip(" ")
    return normalized



def _canonical_json_file_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8") + b"\n"



def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()



def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()



def _quoted(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'



def _sqlite_json_value(value: object) -> object:
    if value is None or type(value) in {int, str}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise InputFormatError("SQLite contains a non-finite number")
        return value
    if type(value) is bytes:
        return {"blob_hex": value.hex()}
    raise InputFormatError("SQLite contains an unsupported value")



def _sqlite_semantic_payload(path: Path, formal_view: str) -> dict[str, object]:
    uri = f"file:{path.resolve()}?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as database:
        schema_objects = [
            {
                "type": row[0],
                "name": row[1],
                "table_name": row[2],
                "sql": None if row[3] is None else _normalize_sql(row[3]),
            }
            for row in database.execute(
                "SELECT type,name,tbl_name,sql FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
            )
        ]
        table_names = [
            row[0]
            for row in database.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        relations = []
        for name in table_names + [formal_view]:
            info = tuple(database.execute(f"PRAGMA table_info({_quoted(name)})"))
            if not info:
                raise InputFormatError(f"SQLite relation is missing: {name}")
            columns = [row[1] for row in info]
            if name == formal_view:
                order_columns = ["formal_order"]
            else:
                primary = [row[1] for row in sorted((row for row in info if row[5]), key=lambda row: row[5])]
                order_columns = primary or columns
            order = ",".join(_quoted(column) for column in order_columns)
            rows = [
                [_sqlite_json_value(value) for value in row]
                for row in database.execute(
                    f"SELECT * FROM {_quoted(name)} ORDER BY {order}"
                )
            ]
            relations.append({"name": name, "columns": columns, "rows": rows})
        user_version = database.execute("PRAGMA user_version").fetchone()[0]
    return {
        "schema_version": "task12-v122-sqlite-semantic-v1",
        "user_version": user_version,
        "schema_objects": schema_objects,
        "relations": relations,
    }



def _sqlite_semantic_sha256(path: Path, formal_view: str) -> str:
    return _sha256_bytes(_canonical_json_file_bytes(_sqlite_semantic_payload(path, formal_view)))



def _promotion_identity(payload: dict[str, object]) -> str:
    return _sha256_bytes(_canonical_json_file_bytes(payload))



def _candidate_manifest(request: V122CandidateVerificationRequest) -> tuple[dict[str, object], bytes]:
    path = request.candidate_dir / request.contract.manifest_filename
    if not path.is_file() or path.is_symlink():
        raise PromotionError("candidate manifest is missing")
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        raise PromotionError("candidate manifest is unreadable") from error
    if type(payload) is not dict:
        raise PromotionError("candidate manifest is invalid")
    return payload, raw



def _populate_database(path: Path, request: V122PromotionBuildRequest) -> None:
    with closing(sqlite3.connect(path)) as database:
        database.execute("PRAGMA foreign_keys=ON")
        database.execute("BEGIN IMMEDIATE")
        try:
            database.execute(PROMOTION_TABLE_SQL)
            database.execute(PROMOTED_TABLE_SQL)
            database.execute(
                "INSERT INTO task12_v122_promotion_v1 VALUES ("
                + ",".join("?" for _ in range(16)) + ")",
                (
                    "V1.22", request.contract.formal_database_schema,
                    "append-only-multi-batch-promotion", "published", "V1.21",
                    BASELINE_SHA256, BASELINE_RELEASE_DIGEST, 591,
                    CANDIDATE_DIGEST, CANDIDATE_SHA256, CANDIDATE_SIZE,
                    CANDIDATE_MANIFEST_SHA256, CANDIDATE_MANIFEST_SIZE,
                    4, 48, 639,
                ),
            )
            rows = tuple(
                database.execute(
                    "SELECT * FROM task12_v122_candidates_v1 ORDER BY aggregate_order"
                )
            )
            if len(rows) != 48 or tuple(row[3] for row in rows) != tuple(range(592, 640)):
                raise PromotionError("candidate row closure is invalid")
            baseline_ids = {
                row[0] for row in database.execute(
                    "SELECT question_id FROM formal_complete_questions_v121"
                )
            }
            if any(row[4] in baseline_ids for row in rows):
                raise PromotionError("candidate question ID collides with V1.21")
            for row in rows:
                database.execute(
                    "INSERT INTO task12_v122_promoted_questions_v1 VALUES ("
                    + ",".join("?" for _ in range(32))
                    + ")",
                    (*row[:30], "published", 1),
                )
            database.execute(FORMAL_VIEW_SQL)
            metadata = {
                "release_version": "V1.22",
                "baseline_version": "V1.21",
                "baseline_sqlite_sha256": BASELINE_SHA256,
                "release_model": "append-only-multi-batch-promotion",
                "schema_version": request.contract.formal_database_schema,
                "formal_question_count": "639",
                "task12_baseline_release_digest": BASELINE_RELEASE_DIGEST,
                "task12_candidate_digest": CANDIDATE_DIGEST,
                "task12_candidate_sqlite_sha256": CANDIDATE_SHA256,
                "task12_candidate_manifest_sha256": CANDIDATE_MANIFEST_SHA256,
                "task12_accepted_batch_count": "4",
                "task12_promoted_questions": "48",
            }
            for key, value in metadata.items():
                database.execute(
                    "INSERT INTO release_metadata_v2(key,value) VALUES (?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, value),
                )
            database.execute("PRAGMA user_version=122")
            database.commit()
        except Exception:
            database.rollback()
            raise



def _artifact(relative_path: str, path: Path, kind: str) -> dict[str, object]:
    return {
        "relative_path": relative_path,
        "sha256": _sha256_file(path),
        "size_bytes": path.stat().st_size,
        "kind": kind,
    }



def _copy_images(
    candidate_root: Path,
    target_root: Path,
    candidate_manifest: dict[str, object],
) -> list[dict[str, object]]:
    safe_candidate_root = candidate_root.resolve(strict=True)
    declared = candidate_manifest.get("images")
    if type(declared) is not list:
        raise PromotionError("candidate image closure is invalid")
    result = []
    for item in declared:
        if type(item) is not dict:
            raise PromotionError("candidate image entry is invalid")
        relative = _relative_path(item.get("relative_path"))
        source = (safe_candidate_root / relative).resolve(strict=False)
        if (
            not source.is_relative_to(safe_candidate_root)
            or not source.is_file()
            or source.is_symlink()
        ):
            raise PromotionError("candidate image is missing or unsafe")
        target = target_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        projected = _artifact(relative, target, "image")
        if (
            projected["sha256"] != item.get("sha256")
            or projected["size_bytes"] != item.get("size_bytes")
        ):
            raise PromotionError("candidate image bytes do not match authority")
        result.append(projected)
    result.sort(key=lambda item: item["relative_path"].encode("utf-8"))
    return result



def _relative_path(value: object) -> str:
    if type(value) is not str or not value or value == "." or "\x00" in value:
        raise InputFormatError("artifact path must be a non-empty canonical relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or "\\" in value
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise InputFormatError("artifact path must be a canonical relative path")
    return value



def _promotion_payload(
    request: V122PromotionBuildRequest,
    database_artifact: dict[str, object],
    semantic_sha256: str,
    images: list[dict[str, object]],
) -> dict[str, object]:
    manifest, _ = _candidate_manifest(request.candidate)
    contract = {
        field.name: getattr(request.contract, field.name)
        for field in fields(V122PromotionContract)
    }
    return {
        "schema_version": request.contract.promotion_identity_schema,
        "release_version": "V1.22",
        "contract": contract,
        "baseline": _baseline_projection(manifest),
        "candidate": _candidate_projection(manifest),
        "batch_ledger": manifest["batch_ledger"],
        "batch_authority_artifacts": manifest["batch_authority_artifacts"],
        "counts": {
            "baseline_question_count": 591,
            "accepted_batch_count": 4,
            "promoted_question_count": 48,
            "formal_question_count": 639,
        },
        "formal_sqlite_sha256": database_artifact["sha256"],
        "formal_sqlite_size_bytes": database_artifact["size_bytes"],
        "formal_sqlite_semantic_sha256": semantic_sha256,
        "images": images,
        "rollback_action": "remove_release_tree_if_release_digest_matches",
    }



def _baseline_projection(manifest: dict[str, object]) -> dict[str, object]:
    value = manifest["baseline"]
    return {
        "release_version": "V1.21",
        "question_count": 591,
        "release_digest": BASELINE_RELEASE_DIGEST,
        "database_schema": "task11-v121-formal-v1",
        "sqlite": {
            "kind": "sqlite", "sha256": BASELINE_SHA256, "size_bytes": BASELINE_SIZE,
        },
        "manifest": {
            "kind": "manifest",
            "sha256": BASELINE_MANIFEST_SHA256,
            "size_bytes": BASELINE_MANIFEST_SIZE,
        },
    }



def _candidate_projection(manifest: dict[str, object]) -> dict[str, object]:
    return {
        "generation": 4,
        "release_version": "V1.22",
        "release_status": "candidate",
        "database_schema": "task12-v122-candidate-v1",
        "candidate_digest": CANDIDATE_DIGEST,
        "sqlite": {"kind": "sqlite", "sha256": CANDIDATE_SHA256, "size_bytes": CANDIDATE_SIZE},
        "manifest": {
            "kind": "manifest", "sha256": CANDIDATE_MANIFEST_SHA256,
            "size_bytes": CANDIDATE_MANIFEST_SIZE,
        },
    }



def _write_release_artifacts(
    root: Path,
    request: V122PromotionBuildRequest,
    candidate_manifest: dict[str, object],
) -> str:
    contract = request.contract
    database_path = root / contract.database_filename
    database_artifact = _artifact(contract.database_filename, database_path, "sqlite")
    semantic = _sqlite_semantic_sha256(database_path, contract.formal_view)
    images = _copy_images(request.candidate.candidate_dir, root, candidate_manifest)
    release_digest = _promotion_identity(
        _promotion_payload(request, database_artifact, semantic, images)
    )
    paths = sorted(
        [
            contract.database_filename,
            contract.manifest_filename,
            contract.sha256s_filename,
            contract.rollback_filename,
            *(item["relative_path"] for item in images),
        ],
        key=lambda value: value.encode("utf-8"),
    )
    rollback = {
        "schema_version": contract.rollback_schema,
        "action": "remove_release_tree_if_release_digest_matches",
        "release_version": "V1.22",
        "release_digest": release_digest,
        "protected_baseline": {
            "release_version": "V1.21",
            "sqlite_sha256": BASELINE_SHA256,
            "question_count": 591,
            "release_digest": BASELINE_RELEASE_DIGEST,
        },
        "candidate_digest": CANDIDATE_DIGEST,
        "release_artifacts": paths,
    }
    rollback_path = root / contract.rollback_filename
    rollback_path.write_bytes(_canonical_json_file_bytes(rollback))
    rollback_artifact = _artifact(contract.rollback_filename, rollback_path, "rollback")
    manifest = {
        "schema_version": contract.release_manifest_schema,
        "release_version": "V1.22",
        "release_status": "published",
        "release_model": "append-only-multi-batch-promotion",
        "database_schema": contract.formal_database_schema,
        "baseline": _baseline_projection(candidate_manifest),
        "candidate": _candidate_projection(candidate_manifest),
        "batch_ledger": candidate_manifest["batch_ledger"],
        "batch_authority_artifacts": candidate_manifest["batch_authority_artifacts"],
        "counts": {
            "baseline_question_count": 591,
            "accepted_batch_count": 4,
            "promoted_question_count": 48,
            "formal_question_count": 639,
        },
        "database": {
            **database_artifact,
            "semantic_sha256": semantic,
        },
        "images": images,
        "artifacts": sorted(
            [database_artifact, rollback_artifact, *images],
            key=lambda item: item["relative_path"].encode("utf-8"),
        ),
        "verification": {
            "authority": "verify_v122_promotion",
            "check_names": [
                "release_directory", "promotion_contract", "candidate_verification",
                "candidate_binding", "manifest_contract", "filesystem_closure",
                "sha256sums_closure", "artifact_references", "rollback_contract",
                "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
                "sqlite_schema", "v121_preservation", "batch_ledger_closure",
                "promotion_projection", "formal_query", "count_closure",
                "provenance_closure", "deterministic_identity",
                "publication_boundary",
            ],
            "required_status": "PASS",
        },
        "promotion": {
            "gate": "FINAL",
            "release_digest": release_digest,
            "required_statement": f"USER APPROVED RELEASE PROMOTION V1.22 {release_digest}",
            "formal_target": "releases/V1.22",
        },
        "rollback": rollback_artifact,
    }
    manifest_path = root / contract.manifest_filename
    manifest_path.write_bytes(_canonical_json_file_bytes(manifest))
    closure = []
    for item in sorted(
        [database_artifact["relative_path"], contract.manifest_filename, contract.rollback_filename, *(image["relative_path"] for image in images)],
        key=lambda value: value.encode("utf-8"),
    ):
        closure.append(f"{_sha256_file(root / item)}  {item}\n")
    (root / contract.sha256s_filename).write_bytes("".join(closure).encode("utf-8"))
    return release_digest



def fixture_release(output, candidate, contract):
    output.mkdir(parents=True)
    shutil.copyfile(candidate.candidate_dir / candidate.contract.database_filename,
                    output / contract.database_filename)
    request = V122PromotionBuildRequest(candidate, output, contract)
    _populate_database(output / contract.database_filename, request)
    manifest = json.loads((candidate.candidate_dir / candidate.contract.manifest_filename).read_text())
    _write_release_artifacts(output, request, manifest)
    with sqlite3.connect((output / contract.database_filename).as_uri()+"?mode=ro", uri=True) as db:
        assert db.execute("SELECT COUNT(*) FROM formal_complete_questions_v122").fetchone() == (639,)
        assert db.execute("SELECT COUNT(*) FROM formal_complete_questions_v121").fetchone() == (591,)
        assert db.execute("SELECT COUNT(*) FROM task12_v122_promoted_questions_v1 WHERE record_status='published' AND selectable=1").fetchone() == (48,)
    return output


def isolated_candidate(root):
    shutil.copytree(ROOT / "releases/V1.21", root / "releases/V1.21")
    for ordinal, (year, _, _) in enumerate(REAL_BATCHES, 1):
        base = Path("data/staging") / f"task12-v122-hkdse-{year}"
        for leaf in ("canonical-v122-approved-a", f"candidate-generation-{ordinal:06d}"):
            shutil.copytree(ROOT / base / leaf, root / base / leaf)
    return real_candidate(root=root)


class V122PublicationBoundaryTests(unittest.TestCase):
    def test_wrong_approval_is_rejected_before_formal_creation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            candidate = isolated_candidate(root)
            config = PipelineConfig(root)
            contract = promotion_contract()
            output = fixture_release(root/"data/staging/dry", candidate, contract)
            wrong = V122ReleasePromotionApproval("V1.22", "0"*64,
                f"USER APPROVED RELEASE PROMOTION V1.22 {'0'*64}")
            with self.assertRaises(PromotionError):
                publish_v122_release(V122PublicationRequest(output,candidate,wrong,contract),config)
            self.assertFalse((root/"releases/V1.22").exists())

    def test_atomic_no_replace_and_private_copy_tamper_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            candidate = isolated_candidate(root)
            config = PipelineConfig(root)
            contract = promotion_contract()
            output = fixture_release(root/"data/staging/dry", candidate, contract)
            digest = json.loads((output/"manifest.json").read_text())["promotion"]["release_digest"]
            approval = V122ReleasePromotionApproval("V1.22",digest,
                f"USER APPROVED RELEASE PROMOTION V1.22 {digest}")
            request = V122PublicationRequest(output,candidate,approval,contract)
            before = tree(root)
            original_copy = shutil.copytree
            def tamper(source, destination, **kwargs):
                result = original_copy(source,destination,**kwargs)
                (Path(destination)/"rogue").write_bytes(b"tamper")
                return result
            with mock.patch("joy_m2.ingest.v122_promotion.shutil.copytree",side_effect=tamper):
                with self.assertRaises(PromotionError):
                    publish_v122_release(request,config)
            self.assertEqual(tree(root),before)
            published = publish_v122_release(request,config)
            self.assertIsNotNone(published,"publication behavior missing")
            self.assertEqual(published.release_digest,digest)
            frozen = tree(root)
            with self.assertRaises(PipelineError):
                publish_v122_release(request,config)
            self.assertEqual(tree(root),frozen)
            self.assertEqual(tree(output),tree(root/"releases/V1.22"))


class V122IndependentVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = real_candidate()
        cls.contract = promotion_contract()
        cls.config = PipelineConfig(ROOT)

    def test_independent_valid_fixture_reports_21_pass(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as d:
            output = fixture_release(Path(d)/"release", self.candidate, self.contract)
            before = tree(output)
            report = verify_v122_promotion(V122PromotionVerificationRequest(output,self.candidate,self.contract), self.config)
            self.assertIsInstance(report, VerificationReport, "verifier behavior missing")
            self.assertEqual(report.status, "PASS")
            self.assertEqual(tuple(c.name for c in report.checks), CHECK_NAMES)
            self.assertTrue(all(c.passed for c in report.checks))
            self.assertEqual(tree(output), before)

    def test_parsed_corrupt_fixture_is_structured_fail(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as d:
            output = fixture_release(Path(d)/"release", self.candidate, self.contract)
            write_json(output/"manifest.json", {"release_status": []})
            before = tree(output)
            report = verify_v122_promotion(V122PromotionVerificationRequest(output,self.candidate,self.contract), self.config)
            self.assertIsInstance(report, VerificationReport, "verifier behavior missing")
            self.assertEqual(report.status,"FAIL")
            self.assertEqual(tree(output), before)

    def test_malformed_fixture_preserves_format_exception(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as d:
            output = fixture_release(Path(d)/"release", self.candidate, self.contract)
            (output/"manifest.json").write_bytes(b"{")
            with self.assertRaises(InputFormatError):
                verify_v122_promotion(V122PromotionVerificationRequest(output,self.candidate,self.contract), self.config)

    def test_self_consistent_numeric_type_forgery_is_rejected(self):
        for case in ("counts", "baseline", "candidate", "ledger", "rollback",
                     "baseline-size", "authority-size", "artifact-size"):
            with self.subTest(case=case), tempfile.TemporaryDirectory(dir=STAGING) as d:
                output = fixture_release(Path(d)/"release", self.candidate, self.contract)
                manifest = json.loads((output/"manifest.json").read_text())
                if case == "counts":
                    manifest["counts"]["formal_question_count"] = 639.0
                elif case == "baseline":
                    manifest["baseline"]["question_count"] = 591.0
                elif case == "candidate":
                    manifest["candidate"]["generation"] = 4.0
                elif case == "ledger":
                    manifest["batch_ledger"][0]["ordinal"] = True
                elif case == "baseline-size":
                    manifest["baseline"]["sqlite"]["size_bytes"] = 10063872.0
                elif case == "authority-size":
                    manifest["batch_authority_artifacts"][0]["size_bytes"] = 509.0
                elif case == "artifact-size":
                    pass  # Alter after rebinding, which reconstructs references.
                else:
                    rollback = json.loads((output/"rollback.json").read_text())
                    rollback["protected_baseline"]["question_count"] = 591.0
                    write_json(output/"rollback.json",rollback)
                write_json(output/"manifest.json",manifest)
                rebind_release(output,self.contract)
                if case == "artifact-size":
                    manifest = json.loads((output/"manifest.json").read_text())
                    item = manifest["artifacts"][0]
                    item["size_bytes"] = float(item["size_bytes"])
                    write_json(output/"manifest.json",manifest)
                    rewrite_sums(output,self.contract.sha256s_filename)
                before = tree(output)
                report = verify_v122_promotion(
                    V122PromotionVerificationRequest(output,self.candidate,self.contract), self.config)
                self.assertEqual(report.status,"FAIL")
                self.assertEqual(tree(output),before)

    def test_unreadable_sqlite_is_fail_report_not_native_exception(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as d:
            output = fixture_release(Path(d)/"release", self.candidate, self.contract)
            (output/self.contract.database_filename).write_bytes(b"not SQLite")
            before = tree(output)
            try:
                report = verify_v122_promotion(
                    V122PromotionVerificationRequest(output,self.candidate,self.contract), self.config)
            except sqlite3.Error as error:
                self.fail(f"native corruption exception escaped: {error}")
            self.assertEqual(report.status,"FAIL")
            self.assertEqual(tree(output),before)
