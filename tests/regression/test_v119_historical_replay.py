"""Literal V1.19 replay and append-only Task 10A public-surface guards."""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import sqlite3
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import joy_m2.ingest as ingest
from joy_m2.config import PipelineConfig
from joy_m2.errors import PipelineError
from joy_m2.ingest import source_mapping
from joy_m2.ingest.manifest import load_import_manifest


_V119_PUBLIC = (
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
)
_V120_PUBLIC = (
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
)
_TASK10B_PUBLIC = (
    "HkdsePdfPageSpan",
    "HkdsePdfExtractionRecord",
    "HkdsePdfExtractionPass",
    "HkdsePdfTranscriptionIssue",
    "HkdsePdfTranscriptionRecord",
    "HkdsePdfTranscriptionBatch",
    "HkdsePdfTranscriptionApproval",
    "VerifiedHkdsePdfTranscriptionBatch",
    "HkdsePdfAdapterBlockedError",
    "extract_hkdse_pdf_embedded_pass",
    "load_hkdse_pdf_extraction_pass",
    "propose_hkdse_pdf_transcription",
    "approve_hkdse_pdf_transcription",
    "adapt_verified_hkdse_pdf_transcription_v120",
)
_TASK10C_PUBLIC = (
    "V120PromotionContract", "V120PromotionBuildRequest",
    "V120PromotionVerificationRequest", "V120ReleasePromotionApproval",
    "V120PublicationRequest", "V120PromotionArtifacts",
    "build_v120_promotion", "verify_v120_promotion", "publish_v120_release",
)
_V121_PUBLIC = (
    "V121BatchImportManifest", "V121AdaptedImportPackage",
    "V121BatchLedgerEntry", "V121EffectiveState", "V121PreflightRequest",
    "V121ImportPreflightReport", "V121ImportPreflightResult",
    "V121ImportApproval", "V121ApprovedBatch", "V121CandidateContract",
    "V121CandidateBuildRequest", "V121CandidateVerificationRequest",
    "V121CandidateArtifacts", "load_v121_import_manifest",
    "preflight_v121_import", "build_v121_candidate", "verify_v121_candidate",
    "adapt_verified_hkdse_pdf_transcription_v121",
)
_V121_PROMOTION_PUBLIC = (
    "V121PromotionContract", "V121PromotionBuildRequest",
    "V121PromotionVerificationRequest", "V121ReleasePromotionApproval",
    "V121PublicationRequest", "V121PromotionArtifacts",
    "build_v121_promotion", "verify_v121_promotion", "publish_v121_release",
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


class V119HistoricalReplayTests(unittest.TestCase):
    def test_root_public_surface_is_exact_append_only_v119_then_v120(self) -> None:
        self.assertEqual(
            ingest.__all__,
            _V119_PUBLIC + _V120_PUBLIC + _TASK10B_PUBLIC[:9] + _V121_PUBLIC
            + _TASK10B_PUBLIC[9:] + _TASK10C_PUBLIC + _V121_PROMOTION_PUBLIC,
        )
        self.assertEqual(ingest.__all__[: len(_V119_PUBLIC)], _V119_PUBLIC)
        self.assertEqual(
            ingest.__all__[len(_V119_PUBLIC) : len(_V119_PUBLIC) + len(_V120_PUBLIC)],
            _V120_PUBLIC,
        )
        self.assertEqual(
            tuple(name for name in ingest.__all__ if name.startswith("V119")),
            tuple(name for name in _V119_PUBLIC if name.startswith("V119")),
        )
        self.assertNotIn("adapt_mmd_package_from_mapping_v120", ingest.__all__)
        for private in (
            "V120Projection",
            "V120WriterProfile",
            "canonical_json_file_bytes",
            "image_destination",
            "ImportApprovalError",
        ):
            self.assertNotIn(private, ingest.__all__)
            self.assertFalse(hasattr(ingest, private))

    def test_source_mapping_surface_keeps_v119_prefix_and_one_v120_suffix(self) -> None:
        self.assertEqual(
            source_mapping.__all__,
            (
                "SourceMappingProposal",
                "SourceMappingApproval",
                "propose_mmd_source_mapping",
                "adapt_mmd_package_from_mapping",
                "adapt_mmd_package_from_mapping_v120",
            ),
        )
        signature = inspect.signature(
            source_mapping.adapt_mmd_package_from_mapping_v120
        )
        self.assertEqual(
            tuple(signature.parameters),
            (
                "selection_manifest_path",
                "source_mapping_path",
                "approval",
                "source_path",
                "output_dir",
                "config",
            ),
        )
        self.assertEqual(
            tuple(
                parameter.annotation
                for parameter in signature.parameters.values()
            ),
            (
                Path,
                Path,
                source_mapping.SourceMappingApproval,
                Path,
                Path,
                PipelineConfig,
            ),
        )

    def test_formal_v119_identity_and_literal_task9a_oracles_are_unchanged(self) -> None:
        from tests.integration import test_ingest_preflight as task9a

        self.assertEqual(
            (task9a.MANIFEST_SHA256, task9a.PREFLIGHT_SHA256),
            (
                "b5a0ae6597028c48c6f7cdc81bd7e67d61dd369cbf96d7c6a4e96efd73984c5d",
                "087574a8af6fe28ac65a5b5810794952044cb5f0778ed3492d1e7819a4be33c2",
            ),
        )
        root = ROOT / "releases/V1.19"
        database = root / "Joy_M2_Complete_Question_DB_V1_19.sqlite3"
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(
            hashlib.sha256(database.read_bytes()).hexdigest(),
            "5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff",
        )
        self.assertEqual(
            (
                manifest["release_version"],
                manifest["schema_version"],
                manifest["release_status"],
                manifest["promotion"]["release_digest"],
            ),
            (
                "V1.19",
                "task9-v119-formal-manifest-v1",
                "published",
                "7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d",
            ),
        )
        with sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro", uri=True) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM formal_complete_questions_v119"
                ).fetchone(),
                (502,),
            )

    def test_historical_manifest_parser_rejects_v120_without_mutation(self) -> None:
        path = ROOT / "tests/fixtures/task10a/v120-batch-a/import_manifest.json"
        before = path.read_bytes()
        with self.assertRaises(PipelineError):
            load_import_manifest(path, path.parent)
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
