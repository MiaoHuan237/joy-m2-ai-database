"""Public-contract RED for V1.21 formal promotion readiness."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
import inspect
from pathlib import Path
import unittest
from typing import get_type_hints

import joy_m2.ingest as ingest
from joy_m2.config import PipelineConfig
from joy_m2.errors import PipelineError, PromotionError
from joy_m2.ingest.v121_models import V121CandidateVerificationRequest
from joy_m2.models import ArtifactRef, VerificationReport


SHA = "1" * 64
EXPORTS = (
    "V121PromotionContract",
    "V121PromotionBuildRequest",
    "V121PromotionVerificationRequest",
    "V121ReleasePromotionApproval",
    "V121PublicationRequest",
    "V121PromotionArtifacts",
    "build_v121_promotion",
    "verify_v121_promotion",
    "publish_v121_release",
)
CONTRACT_VALUES = (
    "V1.21",
    "task11-v121-formal-manifest-v1",
    "task11-v121-formal-v1",
    "task11-v121-promotion-identity-v1",
    "task11-v121-formal-rollback-v1",
    121,
    "Joy_M2_Complete_Question_DB_V1_21.sqlite3",
    "manifest.json",
    "SHA256SUMS.txt",
    "rollback.json",
    "images/sha256",
    "task11_v121_promoted_questions_v1",
    "task11_v121_promotion_v1",
    "formal_complete_questions_v121",
)


def _public(name: str):
    value = getattr(ingest, name, None)
    if value is None:
        raise AssertionError(f"missing V1.21 promotion public contract: {name}")
    return value


def _candidate() -> V121CandidateVerificationRequest:
    return object.__new__(V121CandidateVerificationRequest)


def _contract():
    return _public("V121PromotionContract")(*CONTRACT_VALUES)


def _approval():
    return _public("V121ReleasePromotionApproval")(
        "V1.21", SHA, f"USER APPROVED RELEASE PROMOTION V1.21 {SHA}"
    )


class V121PromotionPublicContractTests(unittest.TestCase):
    def test_exact_append_only_public_surface(self) -> None:
        for name in EXPORTS:
            _public(name)
        historical_prefix = (
            "BatchImportManifest",
            "ImportAdaptation",
            "ImportCandidate",
            "ImportFileEvidence",
            "ImportIssue",
            "ImportPreflightReport",
            "ImportPreflightResult",
            "load_import_manifest",
            "preflight_import",
            "MmdSelection",
            "MmdAdapterManifest",
            "MmdAdapterIssue",
            "MmdAdapterBlockedError",
            "AdaptedImportPackage",
            "adapt_mmd_package",
            "ImportApproval",
            "V119WriterContract",
            "V119WriteRequest",
            "V119VerificationRequest",
            "V119CandidateArtifacts",
            "build_v119_candidate",
            "verify_v119_candidate",
            "V119PromotionContract",
            "V119PromotionBuildRequest",
            "V119PromotionVerificationRequest",
            "ReleasePromotionApproval",
            "V119PublicationRequest",
            "V119PromotionArtifacts",
            "build_v119_promotion",
            "verify_v119_promotion",
            "publish_v119_release",
            "V120BatchImportManifest",
            "V120AdaptedImportPackage",
            "V120BatchLedgerEntry",
            "V120EffectiveState",
            "V120PreflightRequest",
            "V120ImportPreflightReport",
            "V120ImportPreflightResult",
            "V120ImportApproval",
            "V120ApprovedBatch",
            "V120CandidateContract",
            "V120CandidateBuildRequest",
            "V120CandidateVerificationRequest",
            "V120CandidateArtifacts",
            "load_v120_import_manifest",
            "adapt_mmd_package_v120",
            "preflight_v120_import",
            "build_v120_candidate",
            "verify_v120_candidate",
            "HkdsePdfPageSpan",
            "HkdsePdfExtractionRecord",
            "HkdsePdfExtractionPass",
            "HkdsePdfTranscriptionIssue",
            "HkdsePdfTranscriptionRecord",
            "HkdsePdfTranscriptionBatch",
            "HkdsePdfTranscriptionApproval",
            "VerifiedHkdsePdfTranscriptionBatch",
            "HkdsePdfAdapterBlockedError",
            "V121BatchImportManifest",
            "V121AdaptedImportPackage",
            "V121BatchLedgerEntry",
            "V121EffectiveState",
            "V121PreflightRequest",
            "V121ImportPreflightReport",
            "V121ImportPreflightResult",
            "V121ImportApproval",
            "V121ApprovedBatch",
            "V121CandidateContract",
            "V121CandidateBuildRequest",
            "V121CandidateVerificationRequest",
            "V121CandidateArtifacts",
            "load_v121_import_manifest",
            "preflight_v121_import",
            "build_v121_candidate",
            "verify_v121_candidate",
            "adapt_verified_hkdse_pdf_transcription_v121",
            "extract_hkdse_pdf_embedded_pass",
            "load_hkdse_pdf_extraction_pass",
            "propose_hkdse_pdf_transcription",
            "approve_hkdse_pdf_transcription",
            "adapt_verified_hkdse_pdf_transcription_v120",
            "V120PromotionContract",
            "V120PromotionBuildRequest",
            "V120PromotionVerificationRequest",
            "V120ReleasePromotionApproval",
            "V120PublicationRequest",
            "V120PromotionArtifacts",
            "build_v120_promotion",
            "verify_v120_promotion",
            "publish_v120_release",
            "V121PromotionContract",
            "V121PromotionBuildRequest",
            "V121PromotionVerificationRequest",
            "V121ReleasePromotionApproval",
            "V121PublicationRequest",
            "V121PromotionArtifacts",
            "build_v121_promotion",
            "verify_v121_promotion",
            "publish_v121_release",
        )
        v122_suffix = (
            "V122BatchImportManifest",
            "V122AdaptedImportPackage",
            "V122BatchLedgerEntry",
            "V122EffectiveState",
            "V122PreflightRequest",
            "V122ImportPreflightReport",
            "V122ImportPreflightResult",
            "V122ImportApproval",
            "V122ApprovedBatch",
            "V122CandidateContract",
            "V122CandidateBuildRequest",
            "V122CandidateVerificationRequest",
            "V122CandidateArtifacts",
            "load_v122_import_manifest",
            "preflight_v122_import",
            "build_v122_candidate",
            "verify_v122_candidate",
            "adapt_verified_hkdse_pdf_transcription_v122",
        )
        self.assertEqual(historical_prefix[-len(EXPORTS):], EXPORTS)
        self.assertEqual(ingest.__all__, historical_prefix + v122_suffix)

    def test_contract_exact_fields_types_defaults_frozen_and_values(self) -> None:
        cls = _public("V121PromotionContract")
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
        self.assertTrue(all(
            parameter.default is inspect.Parameter.empty
            for parameter in inspect.signature(cls).parameters.values()
        ))
        contract = _contract()
        with self.assertRaises(FrozenInstanceError):
            contract.profile = "V1.22"
        for field in fields(contract):
            bad = True if field.name == "expected_user_version" else "wrong"
            with self.subTest(field=field.name), self.assertRaises(PipelineError):
                replace(contract, **{field.name: bad})

    def test_request_carriers_are_exact_frozen_and_path_safe(self) -> None:
        build_cls = _public("V121PromotionBuildRequest")
        verify_cls = _public("V121PromotionVerificationRequest")
        publish_cls = _public("V121PublicationRequest")
        self.assertEqual(
            tuple(field.name for field in fields(build_cls)),
            ("candidate", "output_dir", "contract"),
        )
        self.assertEqual(
            tuple(field.name for field in fields(verify_cls)),
            ("release_dir", "candidate", "contract"),
        )
        self.assertEqual(
            tuple(field.name for field in fields(publish_cls)),
            ("dry_run_dir", "candidate", "approval", "contract"),
        )
        values = (
            build_cls(_candidate(), Path("staging/out"), _contract()),
            verify_cls(Path("staging/out"), _candidate(), _contract()),
            publish_cls(Path("staging/out"), _candidate(), _approval(), _contract()),
        )
        self.assertTrue(values[0].output_dir.is_absolute())
        self.assertTrue(values[1].release_dir.is_absolute())
        self.assertTrue(values[2].dry_run_dir.is_absolute())
        for value in values:
            with self.assertRaises(FrozenInstanceError):
                value.contract = object()
        invalid = (
            (build_cls, (object(), Path("x"), _contract())),
            (build_cls, (_candidate(), "x", _contract())),
            (build_cls, (_candidate(), Path("x"), object())),
            (verify_cls, (Path("x"), object(), _contract())),
            (verify_cls, ("x", _candidate(), _contract())),
            (publish_cls, (Path("x"), _candidate(), object(), _contract())),
        )
        for cls, arguments in invalid:
            with self.subTest(cls=cls.__name__, arguments=arguments):
                with self.assertRaises(PipelineError):
                    cls(*arguments)

    def test_approval_is_exact_v121_digest_bound_gate(self) -> None:
        cls = _public("V121ReleasePromotionApproval")
        self.assertEqual(
            tuple(field.name for field in fields(cls)),
            ("release_version", "release_digest", "statement"),
        )
        self.assertEqual(_approval().release_digest, SHA)
        invalid = (
            ("V1.20", SHA, f"USER APPROVED RELEASE PROMOTION V1.20 {SHA}"),
            ("V1.21", "A" * 64, f"USER APPROVED RELEASE PROMOTION V1.21 {'A' * 64}"),
            ("V1.21", SHA, f"USER APPROVED RELEASE PROMOTION V1.21 {SHA}\n"),
            ("V1.21", SHA, f"USER APPROVED IMPORT BATCH V1.21 {SHA}"),
        )
        for arguments in invalid:
            with self.subTest(arguments=arguments), self.assertRaises(PromotionError):
                cls(*arguments)

    def test_artifact_result_exact_types_order_and_isolation(self) -> None:
        cls = _public("V121PromotionArtifacts")
        expected = (
            "database", "manifest", "sha256sums", "rollback", "images",
            "release_digest", "verification_report",
        )
        self.assertEqual(tuple(field.name for field in fields(cls)), expected)
        images = [ArtifactRef(Path("images/a.png"), SHA, 1, "image")]
        result = cls(
            ArtifactRef(Path("db"), SHA, 1, "sqlite"),
            ArtifactRef(Path("manifest"), SHA, 1, "manifest"),
            ArtifactRef(Path("sums"), SHA, 1, "sha256sums"),
            ArtifactRef(Path("rollback"), SHA, 1, "rollback"),
            images,
            SHA,
            VerificationReport("PASS", ()),
        )
        images.append(ArtifactRef(Path("images/b.png"), SHA, 1, "image"))
        self.assertEqual(len(result.images), 1)
        self.assertIs(type(result.images), tuple)
        with self.assertRaises(FrozenInstanceError):
            result.release_digest = "2" * 64
        with self.assertRaises(PipelineError):
            replace(result, database=ArtifactRef(Path("db"), SHA, 1, "manifest"))
        with self.assertRaises(PipelineError):
            replace(result, images=[object()])
        with self.assertRaises(PipelineError):
            replace(result, release_digest="BAD")

    def test_public_function_signatures_are_exact(self) -> None:
        cases = (
            ("build_v121_promotion", "V121PromotionBuildRequest", "V121PromotionArtifacts"),
            ("verify_v121_promotion", "V121PromotionVerificationRequest", None),
            ("publish_v121_release", "V121PublicationRequest", "V121PromotionArtifacts"),
        )
        for function_name, request_name, result_name in cases:
            function = _public(function_name)
            signature = inspect.signature(function)
            self.assertEqual(tuple(signature.parameters), ("request", "config"))
            hints = get_type_hints(function)
            self.assertIs(hints["request"], _public(request_name))
            self.assertIs(hints["config"], PipelineConfig)
            expected = VerificationReport if result_name is None else _public(result_name)
            self.assertIs(hints["return"], expected)


if __name__ == "__main__":
    unittest.main()
