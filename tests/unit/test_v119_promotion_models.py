"""Public-contract tests for Task 9D V1.19 promotion."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path
import inspect
import sys
import unittest
from typing import get_type_hints

WORKTREE = Path(__file__).resolve().parents[2]
SRC = WORKTREE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import joy_m2.ingest as ingest
from joy_m2.config import PipelineConfig
from joy_m2.errors import PipelineError, PromotionError
from joy_m2.ingest.writer_models import ImportApproval, V119VerificationRequest
from joy_m2.models import ArtifactRef, VerificationReport


BASE_EXPORTS = (
    "BatchImportManifest", "ImportAdaptation", "ImportCandidate",
    "ImportFileEvidence", "ImportIssue", "ImportPreflightReport",
    "ImportPreflightResult", "load_import_manifest", "preflight_import",
    "MmdSelection", "MmdAdapterManifest", "MmdAdapterIssue",
    "MmdAdapterBlockedError", "AdaptedImportPackage", "adapt_mmd_package",
    "ImportApproval", "V119WriterContract", "V119WriteRequest",
    "V119VerificationRequest", "V119CandidateArtifacts",
    "build_v119_candidate", "verify_v119_candidate",
)
TASK9D_EXPORTS = (
    "V119PromotionContract", "V119PromotionBuildRequest",
    "V119PromotionVerificationRequest", "ReleasePromotionApproval",
    "V119PublicationRequest", "V119PromotionArtifacts",
    "build_v119_promotion", "verify_v119_promotion", "publish_v119_release",
)
TASK10A_EXPORTS = (
    "V120BatchImportManifest", "V120AdaptedImportPackage",
    "V120BatchLedgerEntry", "V120EffectiveState", "V120PreflightRequest",
    "V120ImportPreflightReport", "V120ImportPreflightResult",
    "V120ImportApproval", "V120ApprovedBatch", "V120CandidateContract",
    "V120CandidateBuildRequest", "V120CandidateVerificationRequest",
    "V120CandidateArtifacts", "load_v120_import_manifest",
    "adapt_mmd_package_v120", "preflight_v120_import",
    "build_v120_candidate", "verify_v120_candidate",
)
TASK10B_EXPORTS = (
    "HkdsePdfPageSpan", "HkdsePdfExtractionRecord",
    "HkdsePdfExtractionPass", "HkdsePdfTranscriptionIssue",
    "HkdsePdfTranscriptionRecord", "HkdsePdfTranscriptionBatch",
    "HkdsePdfTranscriptionApproval", "VerifiedHkdsePdfTranscriptionBatch",
    "HkdsePdfAdapterBlockedError", "extract_hkdse_pdf_embedded_pass",
    "load_hkdse_pdf_extraction_pass", "propose_hkdse_pdf_transcription",
    "approve_hkdse_pdf_transcription",
    "adapt_verified_hkdse_pdf_transcription_v120",
)
SHA = "1" * 64


def _require_public(name: str):
    value = getattr(ingest, name, None)
    if value is None:
        raise AssertionError(f"missing Task 9D public contract: {name}")
    return value


def _contract():
    cls = _require_public("V119PromotionContract")
    return cls(
        "V1.19", "task9-v119-formal-manifest-v1", "task9-v119-formal-v1",
        "task9-v119-promotion-identity-v1", "task9-v119-formal-rollback-v1",
        119, "Joy_M2_Complete_Question_DB_V1_19.sqlite3", "manifest.json",
        "SHA256SUMS.txt", "rollback.json", "images/sha256",
        "task9_promoted_questions_v1", "task9_promotion_v1",
        "formal_complete_questions_v119",
    )


def _candidate():
    return object.__new__(V119VerificationRequest)


def _approval():
    cls = _require_public("ReleasePromotionApproval")
    return cls(
        "V1.19", SHA,
        f"USER APPROVED RELEASE PROMOTION V1.19 {SHA}",
    )


class PromotionPublicContractTests(unittest.TestCase):
    def test_exact_append_only_public_surface(self):
        for name in TASK9D_EXPORTS:
            _require_public(name)
        self.assertEqual(
            ingest.__all__,
            BASE_EXPORTS + TASK9D_EXPORTS + TASK10A_EXPORTS + TASK10B_EXPORTS,
        )

    def test_contract_exact_fields_types_defaults_and_frozen(self):
        cls = _require_public("V119PromotionContract")
        expected = (
            "profile", "release_manifest_schema", "formal_database_schema",
            "promotion_identity_schema", "rollback_schema",
            "expected_user_version", "database_filename", "manifest_filename",
            "sha256s_filename", "rollback_filename", "image_root",
            "promoted_table", "promotion_table", "formal_view",
        )
        self.assertEqual(tuple(field.name for field in fields(cls)), expected)
        hints = get_type_hints(cls)
        self.assertEqual(tuple(hints), expected)
        self.assertEqual(tuple(hints.values()), (str,) * 5 + (int,) + (str,) * 8)
        signature = inspect.signature(cls)
        self.assertTrue(all(p.default is inspect.Parameter.empty for p in signature.parameters.values()))
        contract = _contract()
        with self.assertRaises(FrozenInstanceError):
            contract.profile = "V1.20"

    def test_contract_rejects_every_wrong_fixed_value_and_bool_integer(self):
        contract = _contract()
        for field in fields(contract):
            bad = True if field.name == "expected_user_version" else "wrong"
            with self.subTest(field=field.name), self.assertRaises(PipelineError):
                replace(contract, **{field.name: bad})

    def test_request_fields_types_paths_and_frozen(self):
        build_cls = _require_public("V119PromotionBuildRequest")
        verify_cls = _require_public("V119PromotionVerificationRequest")
        publish_cls = _require_public("V119PublicationRequest")
        self.assertEqual(tuple(f.name for f in fields(build_cls)), ("candidate", "output_dir", "contract"))
        self.assertEqual(tuple(f.name for f in fields(verify_cls)), ("release_dir", "candidate", "contract"))
        self.assertEqual(tuple(f.name for f in fields(publish_cls)), ("dry_run_dir", "candidate", "approval", "contract"))
        build = build_cls(_candidate(), Path("relative/staging"), _contract())
        verify = verify_cls(Path("relative/release"), _candidate(), _contract())
        publish = publish_cls(Path("relative/dry-run"), _candidate(), _approval(), _contract())
        self.assertTrue(build.output_dir.is_absolute())
        self.assertTrue(verify.release_dir.is_absolute())
        self.assertTrue(publish.dry_run_dir.is_absolute())
        for value, name in ((build, "output_dir"), (verify, "release_dir"), (publish, "dry_run_dir")):
            with self.assertRaises(FrozenInstanceError):
                setattr(value, name, Path("elsewhere"))

    def test_requests_reject_parallel_carriers_and_non_paths(self):
        build_cls = _require_public("V119PromotionBuildRequest")
        verify_cls = _require_public("V119PromotionVerificationRequest")
        publish_cls = _require_public("V119PublicationRequest")
        for cls, values in (
            (build_cls, (object(), Path("x"), _contract())),
            (build_cls, (_candidate(), "x", _contract())),
            (build_cls, (_candidate(), Path("x"), object())),
            (verify_cls, ("x", _candidate(), _contract())),
            (verify_cls, (Path("x"), object(), _contract())),
            (publish_cls, (Path("x"), _candidate(), object(), _contract())),
        ):
            with self.subTest(cls=cls.__name__, values=values), self.assertRaises(PipelineError):
                cls(*values)

    def test_release_approval_exact_gate_d_contract(self):
        cls = _require_public("ReleasePromotionApproval")
        self.assertEqual(tuple(f.name for f in fields(cls)), ("release_version", "release_digest", "statement"))
        approval = _approval()
        self.assertEqual(approval.release_digest, SHA)
        with self.assertRaises(FrozenInstanceError):
            approval.statement = "changed"
        invalid = (
            ("V1.18", SHA, f"USER APPROVED RELEASE PROMOTION V1.18 {SHA}"),
            ("V1.19", "A" * 64, f"USER APPROVED RELEASE PROMOTION V1.19 {'A' * 64}"),
            ("V1.19", "x", "USER APPROVED RELEASE PROMOTION V1.19 x"),
            ("V1.19", SHA, f"USER APPROVED RELEASE PROMOTION V1.19 {SHA}\n"),
        )
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(PromotionError):
                cls(*values)
        import_approval = object.__new__(ImportApproval)
        publish_cls = _require_public("V119PublicationRequest")
        with self.assertRaises(PipelineError):
            publish_cls(Path("x"), _candidate(), import_approval, _contract())

    def test_artifact_result_exact_contract_and_tuple_isolation(self):
        cls = _require_public("V119PromotionArtifacts")
        self.assertEqual(
            tuple(f.name for f in fields(cls)),
            ("database", "manifest", "sha256sums", "rollback", "images", "release_digest", "verification_report"),
        )
        refs = [ArtifactRef(Path("images/a.png"), SHA, 1, "image")]
        result = cls(
            ArtifactRef(Path("db"), SHA, 1, "sqlite"),
            ArtifactRef(Path("manifest"), SHA, 1, "manifest"),
            ArtifactRef(Path("sums"), SHA, 1, "sha256sums"),
            ArtifactRef(Path("rollback"), SHA, 1, "rollback"),
            refs, SHA, VerificationReport("PASS", ()),
        )
        refs.append(ArtifactRef(Path("images/b.png"), SHA, 1, "image"))
        self.assertEqual(len(result.images), 1)
        self.assertIs(type(result.images), tuple)
        with self.assertRaises(FrozenInstanceError):
            result.release_digest = "2" * 64

    def test_artifact_result_rejects_wrong_kinds_order_digest_and_report(self):
        cls = _require_public("V119PromotionArtifacts")
        valid = (
            ArtifactRef(Path("db"), SHA, 1, "sqlite"),
            ArtifactRef(Path("manifest"), SHA, 1, "manifest"),
            ArtifactRef(Path("sums"), SHA, 1, "sha256sums"),
            ArtifactRef(Path("rollback"), SHA, 1, "rollback"),
            (), SHA, VerificationReport("PASS", ()),
        )
        mutations = (
            (0, ArtifactRef(Path("db"), SHA, 1, "manifest")),
            (4, (ArtifactRef(Path("b"), SHA, 1, "image"), ArtifactRef(Path("a"), SHA, 1, "image"))),
            (5, "BAD"),
            (6, object()),
        )
        for index, value in mutations:
            args = list(valid)
            args[index] = value
            with self.subTest(index=index), self.assertRaises(PipelineError):
                cls(*args)

    def test_public_function_signatures_are_exact(self):
        build = _require_public("build_v119_promotion")
        verify = _require_public("verify_v119_promotion")
        publish = _require_public("publish_v119_release")
        build_cls = _require_public("V119PromotionBuildRequest")
        verify_cls = _require_public("V119PromotionVerificationRequest")
        publish_cls = _require_public("V119PublicationRequest")
        result_cls = _require_public("V119PromotionArtifacts")
        expected = (
            (build, ("request", "config"), build_cls, result_cls),
            (verify, ("request", "config"), verify_cls, VerificationReport),
            (publish, ("request", "config"), publish_cls, result_cls),
        )
        for function, names, request_type, return_type in expected:
            with self.subTest(function=function.__name__):
                self.assertEqual(tuple(inspect.signature(function).parameters), names)
                hints = get_type_hints(function)
                self.assertIs(hints["request"], request_type)
                self.assertIs(hints["config"], PipelineConfig)
                self.assertIs(hints["return"], return_type)


if __name__ == "__main__":
    unittest.main()
