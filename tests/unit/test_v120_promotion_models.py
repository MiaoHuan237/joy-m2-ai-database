"""Public-contract RED for Task 10C V1.20 promotion."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
import inspect
from pathlib import Path
import unittest
from typing import get_type_hints

import joy_m2.ingest as ingest
from joy_m2.config import PipelineConfig
from joy_m2.errors import PipelineError, PromotionError
from joy_m2.ingest.v120_models import V120CandidateVerificationRequest
from joy_m2.models import ArtifactRef, VerificationReport


SHA = "1" * 64
EXPORTS = (
    "V120PromotionContract",
    "V120PromotionBuildRequest",
    "V120PromotionVerificationRequest",
    "V120ReleasePromotionApproval",
    "V120PublicationRequest",
    "V120PromotionArtifacts",
    "build_v120_promotion",
    "verify_v120_promotion",
    "publish_v120_release",
)
CONTRACT_VALUES = (
    "V1.20",
    "task10-v120-formal-manifest-v1",
    "task10-v120-formal-v1",
    "task10-v120-promotion-identity-v1",
    "task10-v120-formal-rollback-v1",
    120,
    "Joy_M2_Complete_Question_DB_V1_20.sqlite3",
    "manifest.json",
    "SHA256SUMS.txt",
    "rollback.json",
    "images/sha256",
    "task10_v120_promoted_questions_v1",
    "task10_v120_promotion_v1",
    "formal_complete_questions_v120",
)


def _public(name: str):
    value = getattr(ingest, name, None)
    if value is None:
        raise AssertionError(f"missing Task 10C public contract: {name}")
    return value


def _candidate() -> V120CandidateVerificationRequest:
    return object.__new__(V120CandidateVerificationRequest)


def _contract():
    return _public("V120PromotionContract")(*CONTRACT_VALUES)


def _approval():
    return _public("V120ReleasePromotionApproval")(
        "V1.20", SHA, f"USER APPROVED RELEASE PROMOTION V1.20 {SHA}"
    )


class V120PromotionPublicContractTests(unittest.TestCase):
    def test_exact_append_only_public_surface(self) -> None:
        for name in EXPORTS:
            _public(name)
        self.assertEqual(ingest.__all__[-len(EXPORTS):], EXPORTS)

    def test_contract_exact_fields_types_defaults_frozen_and_values(self) -> None:
        cls = _public("V120PromotionContract")
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
            contract.profile = "V1.21"
        for field in fields(contract):
            bad = True if field.name == "expected_user_version" else "wrong"
            with self.subTest(field=field.name), self.assertRaises(PipelineError):
                replace(contract, **{field.name: bad})

    def test_request_carriers_are_exact_frozen_and_path_safe(self) -> None:
        build_cls = _public("V120PromotionBuildRequest")
        verify_cls = _public("V120PromotionVerificationRequest")
        publish_cls = _public("V120PublicationRequest")
        self.assertEqual(tuple(f.name for f in fields(build_cls)), ("candidate", "output_dir", "contract"))
        self.assertEqual(tuple(f.name for f in fields(verify_cls)), ("release_dir", "candidate", "contract"))
        self.assertEqual(tuple(f.name for f in fields(publish_cls)), ("dry_run_dir", "candidate", "approval", "contract"))
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
            (verify_cls, (Path("x"), object(), _contract())),
            (publish_cls, (Path("x"), _candidate(), object(), _contract())),
        )
        for cls, arguments in invalid:
            with self.subTest(cls=cls.__name__), self.assertRaises(PipelineError):
                cls(*arguments)

    def test_approval_is_exact_v120_digest_bound_gate(self) -> None:
        cls = _public("V120ReleasePromotionApproval")
        self.assertEqual(tuple(f.name for f in fields(cls)), ("release_version", "release_digest", "statement"))
        self.assertEqual(_approval().release_digest, SHA)
        invalid = (
            ("V1.19", SHA, f"USER APPROVED RELEASE PROMOTION V1.19 {SHA}"),
            ("V1.20", "A" * 64, f"USER APPROVED RELEASE PROMOTION V1.20 {'A' * 64}"),
            ("V1.20", SHA, f"USER APPROVED RELEASE PROMOTION V1.20 {SHA}\n"),
        )
        for arguments in invalid:
            with self.subTest(arguments=arguments), self.assertRaises(PromotionError):
                cls(*arguments)

    def test_artifact_result_exact_types_order_and_isolation(self) -> None:
        cls = _public("V120PromotionArtifacts")
        expected = (
            "database", "manifest", "sha256sums", "rollback", "images",
            "release_digest", "verification_report",
        )
        self.assertEqual(tuple(f.name for f in fields(cls)), expected)
        images = [ArtifactRef(Path("images/a.png"), SHA, 1, "image")]
        result = cls(
            ArtifactRef(Path("db"), SHA, 1, "sqlite"),
            ArtifactRef(Path("manifest"), SHA, 1, "manifest"),
            ArtifactRef(Path("sums"), SHA, 1, "sha256sums"),
            ArtifactRef(Path("rollback"), SHA, 1, "rollback"),
            images, SHA, VerificationReport("PASS", ()),
        )
        images.append(ArtifactRef(Path("images/b.png"), SHA, 1, "image"))
        self.assertEqual(len(result.images), 1)
        self.assertIs(type(result.images), tuple)
        with self.assertRaises(PipelineError):
            replace(result, database=ArtifactRef(Path("db"), SHA, 1, "manifest"))
        with self.assertRaises(PipelineError):
            replace(result, release_digest="BAD")

    def test_public_function_signatures_are_exact(self) -> None:
        cases = (
            ("build_v120_promotion", "V120PromotionBuildRequest", "V120PromotionArtifacts"),
            ("verify_v120_promotion", "V120PromotionVerificationRequest", None),
            ("publish_v120_release", "V120PublicationRequest", "V120PromotionArtifacts"),
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
