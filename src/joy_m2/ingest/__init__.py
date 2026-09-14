"""Public Task 9 ingest contracts and entry points."""

from .adapter import adapt_mmd_package, adapt_mmd_package_v120
from .adapter_models import (
    AdaptedImportPackage,
    MmdAdapterBlockedError,
    MmdAdapterIssue,
    MmdAdapterManifest,
    MmdSelection,
)
from .manifest import load_import_manifest
from .hkdse_pdf_models import (
    HkdsePdfAdapterBlockedError,
    HkdsePdfExtractionPass,
    HkdsePdfExtractionRecord,
    HkdsePdfPageSpan,
    HkdsePdfTranscriptionApproval,
    HkdsePdfTranscriptionBatch,
    HkdsePdfTranscriptionIssue,
    HkdsePdfTranscriptionRecord,
    VerifiedHkdsePdfTranscriptionBatch,
)
from .hkdse_pdf_adapter import (
    extract_hkdse_pdf_embedded_pass,
    load_hkdse_pdf_extraction_pass,
    propose_hkdse_pdf_transcription,
)
from .models import (
    BatchImportManifest,
    ImportAdaptation,
    ImportCandidate,
    ImportFileEvidence,
    ImportIssue,
    ImportPreflightReport,
    ImportPreflightResult,
)
from .preflight import preflight_import
from .promotion import build_v119_promotion, publish_v119_release
from .promotion_models import (
    ReleasePromotionApproval,
    V119PromotionArtifacts,
    V119PromotionBuildRequest,
    V119PromotionContract,
    V119PromotionVerificationRequest,
    V119PublicationRequest,
)
from .promotion_verification import verify_v119_promotion
from .writer import build_v119_candidate
from .writer_models import (
    ImportApproval,
    V119CandidateArtifacts,
    V119VerificationRequest,
    V119WriteRequest,
    V119WriterContract,
)
from .writer_verification import verify_v119_candidate
from .v120_manifest import load_v120_import_manifest
from .v120_models import (
    V120AdaptedImportPackage,
    V120ApprovedBatch,
    V120BatchImportManifest,
    V120BatchLedgerEntry,
    V120CandidateArtifacts,
    V120CandidateBuildRequest,
    V120CandidateContract,
    V120CandidateVerificationRequest,
    V120EffectiveState,
    V120ImportApproval,
    V120ImportPreflightReport,
    V120ImportPreflightResult,
    V120PreflightRequest,
)
from .v120_preflight import preflight_v120_import
from .v120_verification import verify_v120_candidate
from .v120_writer import build_v120_candidate


__all__ = (
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
    "extract_hkdse_pdf_embedded_pass",
    "load_hkdse_pdf_extraction_pass",
    "propose_hkdse_pdf_transcription",
)
