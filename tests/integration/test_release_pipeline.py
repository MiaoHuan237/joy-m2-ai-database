from __future__ import annotations

from dataclasses import replace
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import typing
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from joy_m2 import errors, models
from joy_m2.config import PipelineConfig
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
    ASSET_ROOT,
    V117_CANDIDATE,
    make_v117_asset_root,
    task5_request,
    task6_request,
    task6_request_for,
    write_json,
)


V117_BASELINE_V116_ZIP_SHA256 = (
    "5f73f541f5c2da5bf3e5540daf7dbfb40566a339eaee79ef3e25d8eabd0404ae"
)


def require_release_api(test: unittest.TestCase, name: str):
    module = importlib.import_module("joy_m2.release.pipeline")
    value = getattr(module, name, None)
    test.assertTrue(callable(value), f"missing approved Release API: {name}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_contract(profile: str) -> models.ExportContract:
    if profile == "V1.17":
        return models.ExportContract(
            profile=profile,
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
    return models.ExportContract(
        profile=profile,
        audit_records_filename="complete_questions_452_task6_audited.json",
        audit_report_filename="task6_audit_report.json",
        csv_filename="Joy_M2_Complete_Questions_V1_18.csv",
        knowledge_markdown_filename="Joy_M2_完整题497题_知识文档.V1.18.md",
        import_report_filename="Joy_M2_V1.18_正式入库报告.md",
        project_state_filename="PROJECT_STATE.md",
        taxonomy_filename=None,
        expected_question_count=497,
        expected_missing_answer_count=34,
    )


def release_contract(profile: str, *, prefix: str = "") -> models.ReleaseContract:
    if profile == "V1.17":
        required = (
            "artifact_sha256",
            "baseline_v116_sqlite_sha256",
            "baseline_v116_zip_sha256",
            "release_model",
            "release_status",
            "release_version",
            "schema_version",
            "task4_candidate_sha256",
        )
    else:
        required = (
            "artifact_sha256",
            "baseline_v117_sqlite_sha256",
            "release_status",
            "release_version",
            "schema_version",
        )
    return models.ReleaseContract(
        profile=profile,
        approval_filename=f"{prefix}approval.json",
        manifest_filename=f"{prefix}manifest.json",
        sha256sums_filename=f"{prefix}SHA256SUMS.txt",
        candidate_zip_filename=f"{prefix}candidate.zip",
        formal_zip_filename=f"{prefix}formal.zip",
        archive_root=f"{prefix}release-root",
        protected_artifact_kinds=("sqlite", "csv", "markdown", "json", "manifest", "approval"),
        manifest_required_fields=required,
        hash_excluded_kinds=("sha256sums", "zip"),
        zip_excluded_kinds=("zip",),
    )


def decision() -> models.V117ReleaseDecision:
    return models.V117ReleaseDecision(
        formal_release_version="V1.17",
        selectable=True,
        record_status="published",
        joy_approval="approved_by_joy",
        approved_at="2026-08-08T20:00:00+08:00",
        schema_version="complete-question-v1.0",
    )


def candidate_request(
    root: Path,
    profile: str,
    *,
    run_id: str = "run-1",
    audit_request: models.AuditRequest | None = None,
    baseline_manifest: models.ArtifactRef | None = None,
    contract: models.ReleaseContract | None = None,
) -> models.CandidateBuildRequest:
    config = PipelineConfig(root)
    if profile == "V1.17":
        if audit_request is None:
            records = json.loads(V117_CANDIDATE.read_text(encoding="utf-8"))
            assets = make_v117_asset_root(root, records)
            audit_request = task5_request(V117_CANDIDATE, assets)
        return models.CandidateBuildRequest(
            config=config,
            run_id=run_id,
            release_spec=v117_release_spec(),
            audit_request=audit_request,
            v117_release_decision=decision(),
            baseline_manifest=baseline_manifest or artifact(V117_MANIFEST, "json"),
            database_contract=database_v117_contract(),
            export_contract=export_contract(profile),
            release_contract=contract or release_contract(profile),
        )
    return models.CandidateBuildRequest(
        config=config,
        run_id=run_id,
        release_spec=v118_release_spec(),
        audit_request=audit_request or task6_request(),
        v117_release_decision=None,
        baseline_manifest=baseline_manifest or artifact(V117_MANIFEST, "json"),
        database_contract=database_v118_contract(),
        export_contract=export_contract(profile),
        release_contract=contract or release_contract(profile),
    )


def _write_test_zip(path: Path, root: Path, files: tuple[Path, ...], archive_root: str) -> None:
    with zipfile.ZipFile(
        path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for source in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
            name = f"{archive_root}/{source.relative_to(root).as_posix()}"
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def synthetic_candidate(root: Path, *, prefix: str = "authority-") -> models.CandidateRelease:
    candidate_root = root / "candidate"
    candidate_root.mkdir(parents=True)
    contract = models.ReleaseContract(
        profile="V9.99",
        approval_filename=f"{prefix}approval.json",
        manifest_filename=f"{prefix}manifest.json",
        sha256sums_filename=f"{prefix}SHA256SUMS.txt",
        candidate_zip_filename=f"{prefix}candidate.zip",
        formal_zip_filename=f"{prefix}formal.zip",
        archive_root=f"{prefix}root",
        protected_artifact_kinds=("payload", "manifest", "approval"),
        manifest_required_fields=(
            "artifact_sha256",
            "release_status",
            "release_version",
            "schema_version",
        ),
        hash_excluded_kinds=("sha256sums", "zip"),
        zip_excluded_kinds=("zip",),
    )
    payload = candidate_root / "payload.txt"
    payload.write_bytes(b"candidate payload\n")
    manifest = candidate_root / contract.manifest_filename
    manifest.write_text(
        json.dumps(
            {
                "artifact_sha256": {payload.name: sha256(payload)},
                "release_status": "candidate",
                "release_version": "V9.99",
                "schema_version": "complete-question-v1.0",
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sums = candidate_root / contract.sha256sums_filename
    sums.write_text(
        f"{sha256(manifest)}  {manifest.name}\n{sha256(payload)}  {payload.name}\n",
        encoding="utf-8",
    )
    candidate_zip = candidate_root / contract.candidate_zip_filename
    _write_test_zip(
        candidate_zip,
        candidate_root,
        (manifest, payload, sums),
        contract.archive_root,
    )
    return models.CandidateRelease(
        run_id="synthetic-run",
        release_version="V9.99",
        release_contract=contract,
        candidate_manifest_sha256=sha256(manifest),
        verification_report=models.VerificationReport(
            status="PASS",
            checks=(models.VerificationCheck("fixture", True, "valid"),),
        ),
        artifacts=(
            artifact(payload, "payload"),
            artifact(manifest, "manifest"),
            artifact(sums, "sha256sums"),
        ),
        candidate_zip=artifact(candidate_zip, "zip"),
    )


def formalize_synthetic_candidate(candidate: models.CandidateRelease) -> Path:
    root = candidate.candidate_zip.path.parent
    contract = candidate.release_contract
    manifest = root / contract.manifest_filename
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["release_status"] = "formal"
    manifest.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    payload = root / "payload.txt"
    sums = root / contract.sha256sums_filename
    sums.write_text(
        f"{sha256(manifest)}  {manifest.name}\n{sha256(payload)}  {payload.name}\n",
        encoding="utf-8",
    )
    candidate.candidate_zip.path.unlink()
    formal_zip = root / contract.formal_zip_filename
    _write_test_zip(
        formal_zip,
        root,
        (manifest, payload, sums),
        contract.archive_root,
    )
    return formal_zip


def rewrite_synthetic_candidate_manifest(
    candidate: models.CandidateRelease,
    **overrides: object,
) -> models.CandidateRelease:
    root = candidate.candidate_zip.path.parent
    contract = candidate.release_contract
    manifest = root / contract.manifest_filename
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value.update(overrides)
    manifest.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    payload = root / "payload.txt"
    sums = root / contract.sha256sums_filename
    sums.write_text(
        f"{sha256(manifest)}  {manifest.name}\n{sha256(payload)}  {payload.name}\n",
        encoding="utf-8",
    )
    _write_test_zip(
        candidate.candidate_zip.path,
        root,
        (manifest, payload, sums),
        contract.archive_root,
    )
    return replace(
        candidate,
        candidate_manifest_sha256=sha256(manifest),
        artifacts=(
            artifact(payload, "payload"),
            artifact(manifest, "manifest"),
            artifact(sums, "sha256sums"),
        ),
        candidate_zip=artifact(candidate.candidate_zip.path, "zip"),
    )


def approval(candidate: models.CandidateRelease, **overrides) -> models.ApprovalRecord:
    values = {
        "release_version": candidate.release_version,
        "candidate_manifest_sha256": candidate.candidate_manifest_sha256,
        "approved_by": "Joy",
        "approved_at": "2026-08-17T12:00:00+08:00",
        "scope": "synthetic release approval",
    }
    values.update(overrides)
    return models.ApprovalRecord(**values)


class CandidateBuildTests(unittest.TestCase):
    def test_v118_build_preserves_contract_identity_and_projects_only_v118_evidence(self) -> None:
        build_candidate = require_release_api(self, "build_candidate")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = candidate_request(root, "V1.18")

            candidate = build_candidate(request)

            self.assertIs(candidate.release_contract, request.release_contract)
            self.assertEqual(candidate.run_id, request.run_id)
            self.assertEqual(candidate.release_version, "V1.18")
            self.assertEqual(candidate.verification_report.status, "PASS")
            candidate_root = request.config.staging_root / request.run_id
            self.assertTrue(candidate_root.is_dir())
            manifest = json.loads(
                (candidate_root / request.release_contract.manifest_filename).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                manifest["baseline_v117_sqlite_sha256"],
                request.audit_request.baseline_database.sha256,
            )
            self.assertNotIn("baseline_v116_zip_sha256", manifest)
            self.assertEqual(manifest["release_version"], "V1.18")
            self.assertEqual(manifest["release_status"], "candidate")
            self.assertTrue(candidate.candidate_zip.path.is_file())
            self.assertEqual(candidate.candidate_zip.path.parent, candidate_root)

    def test_v117_build_uses_explicit_decision_and_historical_manifest_projection(self) -> None:
        build_candidate = require_release_api(self, "build_candidate")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = candidate_request(root, "V1.17")

            candidate = build_candidate(request)

            manifest = json.loads(
                (request.config.staging_root / request.run_id / request.release_contract.manifest_filename).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                manifest["task4_candidate_sha256"],
                hashlib.sha256(request.audit_request.candidate_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                manifest["baseline_v116_sqlite_sha256"],
                request.audit_request.baseline_database.sha256,
            )
            self.assertEqual(
                manifest["baseline_v116_zip_sha256"],
                V117_BASELINE_V116_ZIP_SHA256,
            )
            self.assertIs(candidate.release_contract, request.release_contract)

    def test_v117_and_v118_builds_are_byte_deterministic_across_equivalent_roots(self) -> None:
        build_candidate = require_release_api(self, "build_candidate")
        for profile in ("V1.17", "V1.18"):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as first_temp, tempfile.TemporaryDirectory() as second_temp:
                first_request = candidate_request(Path(first_temp), profile, run_id="same-run")
                second_request = candidate_request(Path(second_temp), profile, run_id="same-run")

                first = build_candidate(first_request)
                second = build_candidate(second_request)

                first_by_name = {ref.path.name: ref for ref in first.artifacts}
                second_by_name = {ref.path.name: ref for ref in second.artifacts}
                self.assertEqual(first.candidate_manifest_sha256, second.candidate_manifest_sha256)
                self.assertEqual(first.candidate_zip.sha256, second.candidate_zip.sha256)
                self.assertEqual(first.candidate_zip.path.read_bytes(), second.candidate_zip.path.read_bytes())
                self.assertEqual(set(first_by_name), set(second_by_name))
                for name in sorted(first_by_name):
                    self.assertEqual(first_by_name[name].sha256, second_by_name[name].sha256)
                    self.assertEqual(
                        first_by_name[name].path.read_bytes(),
                        second_by_name[name].path.read_bytes(),
                    )

    def test_existing_run_and_invalid_baseline_manifest_are_atomic(self) -> None:
        build_candidate = require_release_api(self, "build_candidate")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = candidate_request(root, "V1.18")
            target = request.config.staging_root / request.run_id
            target.mkdir(parents=True)
            sentinel = target / "sentinel"
            sentinel.write_bytes(b"keep")
            with self.assertRaises(errors.OutputConflictError):
                build_candidate(request)
            self.assertEqual(sentinel.read_bytes(), b"keep")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            invalid_manifest = replace(
                artifact(V117_MANIFEST, "json"),
                sha256="0" * 64,
            )
            request = candidate_request(
                root,
                "V1.18",
                baseline_manifest=invalid_manifest,
            )
            with self.assertRaises(errors.BaselineMismatchError):
                build_candidate(request)
            self.assertFalse((request.config.staging_root / request.run_id).exists())

    def test_failed_audit_and_failed_final_verification_publish_no_candidate(self) -> None:
        build_candidate = require_release_api(self, "build_candidate")
        records = json.loads(task6_request().candidate_path.read_text(encoding="utf-8"))
        records[1]["question_text_original"] = records[0]["question_text_original"]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate_json = root / "blocked.json"
            write_json(candidate_json, records)
            blocked_request = candidate_request(
                root,
                "V1.18",
                audit_request=task6_request_for(candidate_json, ASSET_ROOT),
            )
            with self.assertRaises(errors.AuditBlockedError):
                build_candidate(blocked_request)
            self.assertFalse(
                (blocked_request.config.staging_root / blocked_request.run_id).exists()
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = candidate_request(root, "V1.18")
            failed = models.VerificationReport(
                status="FAIL",
                checks=(models.VerificationCheck("injected", False, "failure"),),
            )
            with patch("joy_m2.release.pipeline.verify_candidate", return_value=failed):
                with self.assertRaises(errors.PipelineError):
                    build_candidate(request)
            self.assertFalse((request.config.staging_root / request.run_id).exists())


class VerificationApiTests(unittest.TestCase):
    def test_release_apis_have_the_exact_approved_typed_signatures(self) -> None:
        module = importlib.import_module("joy_m2.release.pipeline")
        self.assertEqual(
            typing.get_type_hints(module.build_candidate),
            {
                "request": models.CandidateBuildRequest,
                "return": models.CandidateRelease,
            },
        )
        self.assertEqual(
            typing.get_type_hints(module.verify_candidate),
            {
                "candidate": models.CandidateRelease,
                "return": models.VerificationReport,
            },
        )
        self.assertEqual(
            typing.get_type_hints(module.verify_release),
            {
                "release_dir": Path,
                "contract": models.ReleaseContract,
                "return": models.VerificationReport,
            },
        )
        self.assertEqual(
            typing.get_type_hints(module.promote_candidate),
            {
                "candidate": models.CandidateRelease,
                "approval": models.ApprovalRecord,
                "config": PipelineConfig,
                "return": models.FormalRelease,
            },
        )

    def test_candidate_verification_passes_then_reports_missing_tampered_and_extra_files(self) -> None:
        verify_candidate = require_release_api(self, "verify_candidate")
        with tempfile.TemporaryDirectory() as temporary:
            candidate = synthetic_candidate(Path(temporary))
            root = candidate.candidate_zip.path.parent
            before = {path.name: path.read_bytes() for path in root.iterdir()}

            self.assertEqual(verify_candidate(candidate).status, "PASS")

            payload = root / "payload.txt"
            payload.write_bytes(b"tampered\n")
            self.assertEqual(verify_candidate(candidate).status, "FAIL")
            self.assertEqual(payload.read_bytes(), b"tampered\n")
            payload.write_bytes(before["payload.txt"])

            extra = root / "extra.txt"
            extra.write_bytes(b"extra")
            self.assertEqual(verify_candidate(candidate).status, "FAIL")
            self.assertEqual(extra.read_bytes(), b"extra")
            extra.unlink()

            candidate.candidate_zip.path.unlink()
            self.assertEqual(verify_candidate(candidate).status, "FAIL")
            self.assertEqual(
                (root / candidate.release_contract.manifest_filename).read_bytes(),
                before[candidate.release_contract.manifest_filename],
            )

    def test_candidate_verification_rejects_version_envelope_mismatch(self) -> None:
        verify_candidate = require_release_api(self, "verify_candidate")
        with tempfile.TemporaryDirectory() as temporary:
            candidate = synthetic_candidate(Path(temporary))
            forged = replace(candidate, release_version="V9.98")

            report = verify_candidate(forged)

            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "candidate_manifest_identity" and not check.passed
                    for check in report.checks
                )
            )

    def test_candidate_verification_rejects_wrong_status_and_schema_identity(self) -> None:
        verify_candidate = require_release_api(self, "verify_candidate")
        cases = (
            {"release_status": "formal"},
            {"schema_version": "wrong-schema"},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory() as temporary:
                candidate = rewrite_synthetic_candidate_manifest(
                    synthetic_candidate(Path(temporary)),
                    **overrides,
                )

                report = verify_candidate(candidate)

                self.assertEqual(report.status, "FAIL")
                self.assertTrue(
                    any(
                        check.name == "candidate_manifest_identity"
                        and not check.passed
                        for check in report.checks
                    )
                )

    def test_candidate_verification_raises_input_format_for_malformed_manifest(self) -> None:
        verify_candidate = require_release_api(self, "verify_candidate")
        with tempfile.TemporaryDirectory() as temporary:
            candidate = synthetic_candidate(Path(temporary))
            manifest = (
                candidate.candidate_zip.path.parent
                / candidate.release_contract.manifest_filename
            )
            manifest.write_text("{", encoding="utf-8")

            with self.assertRaises(errors.InputFormatError):
                verify_candidate(candidate)

    def test_candidate_parsed_manifest_with_wrong_top_level_returns_fail(self) -> None:
        verify_candidate = require_release_api(self, "verify_candidate")
        with tempfile.TemporaryDirectory() as temporary:
            candidate = synthetic_candidate(Path(temporary))
            manifest = (
                candidate.candidate_zip.path.parent
                / candidate.release_contract.manifest_filename
            )
            manifest.write_text("[]\n", encoding="utf-8")

            report = verify_candidate(candidate)

            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "manifest_structure" and not check.passed
                    for check in report.checks
                )
            )

    def test_candidate_wrong_frozen_field_type_returns_structured_fail(self) -> None:
        verify_candidate = require_release_api(self, "verify_candidate")
        with tempfile.TemporaryDirectory() as temporary:
            candidate = synthetic_candidate(Path(temporary))
            contract = replace(
                candidate.release_contract,
                profile="V1.18",
                manifest_required_fields=(
                    "artifact_sha256",
                    "baseline_v117_sqlite_sha256",
                    "complete_question_count",
                    "legacy_compatibility_retained",
                    "release_status",
                    "release_version",
                    "schema_version",
                    "task6_imported_question_count",
                ),
            )
            candidate = replace(
                candidate,
                release_version="V1.18",
                release_contract=contract,
            )
            candidate = rewrite_synthetic_candidate_manifest(
                candidate,
                release_version="V1.18",
                baseline_v117_sqlite_sha256=123,
                complete_question_count=497,
                legacy_compatibility_retained=True,
                task6_imported_question_count=452,
            )

            report = verify_candidate(candidate)

            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "manifest_field_types" and not check.passed
                    for check in report.checks
                )
            )

    def test_candidate_unhashable_release_status_returns_structured_fail(self) -> None:
        verify_candidate = require_release_api(self, "verify_candidate")
        with tempfile.TemporaryDirectory() as temporary:
            candidate = rewrite_synthetic_candidate_manifest(
                synthetic_candidate(Path(temporary)),
                release_status=[],
            )
            root = candidate.candidate_zip.path.parent
            before = {path.name: path.read_bytes() for path in root.iterdir()}

            report = verify_candidate(candidate)

            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "manifest_field_types" and not check.passed
                    for check in report.checks
                )
            )
            self.assertEqual(
                {path.name: path.read_bytes() for path in root.iterdir()},
                before,
            )

    def test_release_verification_is_non_mutating_for_valid_missing_tampered_and_extra_files(self) -> None:
        verify_release = require_release_api(self, "verify_release")
        with tempfile.TemporaryDirectory() as temporary:
            candidate = synthetic_candidate(Path(temporary))
            root = candidate.candidate_zip.path.parent
            contract = candidate.release_contract
            formal_zip = formalize_synthetic_candidate(candidate)
            payload = root / "payload.txt"
            self.assertEqual(verify_release(root, contract).status, "PASS")

            formal_zip.unlink()
            self.assertEqual(verify_release(root, contract).status, "FAIL")
            self.assertFalse(formal_zip.exists())
            _write_test_zip(
                formal_zip,
                root,
                (
                    root / contract.manifest_filename,
                    payload,
                    root / contract.sha256sums_filename,
                ),
                contract.archive_root,
            )

            before = {path.name: path.read_bytes() for path in root.iterdir()}
            payload.write_bytes(b"tampered")
            self.assertEqual(verify_release(root, contract).status, "FAIL")
            self.assertEqual(payload.read_bytes(), b"tampered")
            payload.write_bytes(before["payload.txt"])
            (root / "extra.txt").write_bytes(b"extra")
            self.assertEqual(verify_release(root, contract).status, "FAIL")
            self.assertEqual((root / "extra.txt").read_bytes(), b"extra")

        with tempfile.TemporaryDirectory() as temporary:
            empty = Path(temporary)
            with self.assertRaises(errors.InputMissingError):
                verify_release(empty, release_contract("V1.18"))


class PromotionTests(unittest.TestCase):
    def test_promotion_uses_only_candidate_contract_and_is_atomic_and_non_overwriting(self) -> None:
        promote_candidate = require_release_api(self, "promote_candidate")
        verify_release = require_release_api(self, "verify_release")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = synthetic_candidate(root)
            config = PipelineConfig(root / "repository")
            candidate_before = {
                path.name: path.read_bytes()
                for path in candidate.candidate_zip.path.parent.iterdir()
            }

            formal = promote_candidate(candidate, approval(candidate), config)

            expected = config.releases_root / candidate.release_version
            self.assertEqual(formal.release_dir, expected.resolve())
            self.assertTrue((expected / candidate.release_contract.approval_filename).is_file())
            self.assertTrue((expected / candidate.release_contract.formal_zip_filename).is_file())
            self.assertEqual(formal.verification_report.status, "PASS")
            self.assertEqual(
                verify_release(expected, candidate.release_contract).status,
                "PASS",
            )
            self.assertEqual(
                candidate_before,
                {
                    path.name: path.read_bytes()
                    for path in candidate.candidate_zip.path.parent.iterdir()
                },
            )
            with self.assertRaises(errors.PipelineError):
                promote_candidate(candidate, approval(candidate), config)

    def test_promotion_rejects_every_invalid_approval_and_tampered_candidate_without_output(self) -> None:
        promote_candidate = require_release_api(self, "promote_candidate")
        invalid = (
            {"release_version": "V9.98"},
            {"candidate_manifest_sha256": "0" * 64},
            {"approved_by": "Not Joy"},
            {"approved_at": "2026-08-17T12:00:00"},
            {"scope": ""},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                candidate = synthetic_candidate(root)
                config = PipelineConfig(root / "repository")
                with self.assertRaises(errors.PromotionError):
                    promote_candidate(candidate, approval(candidate, **overrides), config)
                self.assertFalse((config.releases_root / candidate.release_version).exists())

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = synthetic_candidate(root)
            config = PipelineConfig(root / "repository")
            (candidate.candidate_zip.path.parent / "payload.txt").write_bytes(b"tampered")
            with self.assertRaises(errors.PromotionError):
                promote_candidate(candidate, approval(candidate), config)
            self.assertFalse((config.releases_root / candidate.release_version).exists())

    def test_promotion_rejects_forged_version_envelope_without_output(self) -> None:
        promote_candidate = require_release_api(self, "promote_candidate")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = synthetic_candidate(root)
            forged = replace(candidate, release_version="V9.98")
            config = PipelineConfig(root / "repository")
            before = {
                path.name: path.read_bytes()
                for path in candidate.candidate_zip.path.parent.iterdir()
            }

            with self.assertRaises(errors.PromotionError):
                promote_candidate(forged, approval(forged), config)

            self.assertFalse((config.releases_root / "V9.98").exists())
            self.assertFalse((config.releases_root / "V9.99").exists())
            self.assertEqual(
                before,
                {
                    path.name: path.read_bytes()
                    for path in candidate.candidate_zip.path.parent.iterdir()
                },
            )

    def test_promotion_requires_stored_and_fresh_candidate_pass(self) -> None:
        promote_candidate = require_release_api(self, "promote_candidate")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = synthetic_candidate(root)
            failed = replace(
                candidate,
                verification_report=models.VerificationReport(
                    status="FAIL",
                    checks=(
                        models.VerificationCheck(
                            "stored_candidate_verification",
                            False,
                            "stored verification failed",
                        ),
                    ),
                ),
            )
            config = PipelineConfig(root / "repository")
            before = {
                path.name: path.read_bytes()
                for path in candidate.candidate_zip.path.parent.iterdir()
            }

            with self.assertRaises(errors.PromotionError):
                promote_candidate(failed, approval(failed), config)

            self.assertFalse((config.releases_root / failed.release_version).exists())
            self.assertEqual(
                before,
                {
                    path.name: path.read_bytes()
                    for path in candidate.candidate_zip.path.parent.iterdir()
                },
            )

    def test_failed_formal_verification_leaves_no_partial_release(self) -> None:
        promote_candidate = require_release_api(self, "promote_candidate")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = synthetic_candidate(root)
            config = PipelineConfig(root / "repository")
            failed = models.VerificationReport(
                status="FAIL",
                checks=(models.VerificationCheck("injected", False, "failure"),),
            )
            with patch("joy_m2.release.pipeline.verify_release", return_value=failed):
                with self.assertRaises(errors.PromotionError):
                    promote_candidate(candidate, approval(candidate), config)
            self.assertFalse((config.releases_root / candidate.release_version).exists())


if __name__ == "__main__":
    unittest.main()
