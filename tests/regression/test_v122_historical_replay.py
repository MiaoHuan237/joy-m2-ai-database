"""Read-only fixed-version replay; never builds historical or real V1.22 data."""
from pathlib import Path
import hashlib
import json
import sqlite3
import unittest

from joy_m2.config import PipelineConfig
from joy_m2.models import ArtifactRef
from joy_m2.ingest import (
    ImportApproval, V119VerificationRequest, V119PromotionVerificationRequest,
    V120PromotionVerificationRequest, V121PromotionVerificationRequest,
    load_import_manifest, preflight_import, verify_v119_candidate,
    verify_v119_promotion, verify_v120_promotion, verify_v121_promotion,
)
from tests.integration.test_v119_promotion import (
    _writer_contract, _promotion_contract as v119_contract,
)
from tests.integration.test_v120_promotion import (
    candidate_for, _promotion_contract as v120_contract,
)
from tests.integration.test_v121_promotion import (
    real_candidate, promotion_contract as v121_contract,
)

ROOT = Path(__file__).resolve().parents[2]
FROZEN = (
    ("V1.18", 497, "complete_questions_v2", "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7"),
    ("V1.19", 502, "formal_complete_questions_v119", "5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff"),
    ("V1.20", 543, "formal_complete_questions_v120", "b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292"),
    ("V1.21", 591, "formal_complete_questions_v121", "93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a"),
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree(root):
    return {p.relative_to(root).as_posix(): sha(p)
            for p in sorted(root.rglob("*")) if p.is_file()}


def historical_requests():
    """Reconstruct exact approved requests with all materialization disabled."""
    config = PipelineConfig(ROOT)
    package = ROOT / "data/staging/task9b-real-0918-canonical-approved-a"
    baseline = ROOT / "releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3"
    result = preflight_import(
        load_import_manifest(package / "import_manifest.json", package),
        package, ArtifactRef(baseline, FROZEN[0][3], baseline.stat().st_size, "sqlite"),
    )
    digest = "4aa3ff8b419a0fcca57c805d5f10f252658cb30c00f6cf1b74c95ab3009333c9"
    assert result.report.preflight_sha256 == digest
    assert result.report.manifest_sha256 == "388bef6a47af331f415fbe10d2d847c889b8c34963d4a161af52ed608e268b7a"
    batch = "TASK9B-REAL-0918-INTERVAL-REPRODUCTION-001"
    approval = ImportApproval(batch, digest, "V1.19",
                              f"USER APPROVED IMPORT BATCH {batch} {digest} V1.19")
    candidate = V119VerificationRequest(
        ROOT / "data/staging/task9c-v119-real-0918-interval-candidate",
        result, approval, _writer_contract(),
    )
    assert verify_v119_candidate(candidate, config).status == "PASS"
    assert sha(candidate.candidate_dir / "candidate_manifest.json") == "b2e0b4607b49f5e1e097fd036dd0614c67128976e7d282f4e2783eb092be9634"
    v120 = candidate_for(ROOT, materialize_candidates=False)
    v121 = real_candidate(materialize=False)
    for request, expected in (
        (v120, "88cc945b6296652c88041e8e51a5c586300c2201a9f48e21abde80d97da3a7b3"),
        (v121, "ecf624e3cb9fd8e7b1e0c664ddc5d51ef67f2d7f16f277c276be828eba32282c"),
    ):
        manifest = json.loads((request.candidate_dir / "candidate_manifest.json").read_text())
        assert manifest["candidate_digest"] == expected
        # Frozen manifest binds every replayed canonical manifest, preflight,
        # approval and ledger row; independent candidate verifiers close these.
    return (
        (verify_v119_promotion, V119PromotionVerificationRequest(
            ROOT / "releases/V1.19", candidate, v119_contract()), 18),
        (verify_v120_promotion, V120PromotionVerificationRequest(
            ROOT / "releases/V1.20", v120, v120_contract()), 21),
        (verify_v121_promotion, V121PromotionVerificationRequest(
            ROOT / "releases/V1.21", v121, v121_contract()), 21),
    )


class V122HistoricalReplayTests(unittest.TestCase):
    def test_four_frozen_databases_and_published_591_baseline(self):
        for version, count, view, digest in FROZEN:
            with self.subTest(version=version):
                db = ROOT / "releases" / version / f"Joy_M2_Complete_Question_DB_{version.replace('.', '_')}.sqlite3"
                self.assertEqual(sha(db), digest)
                with sqlite3.connect(db.as_uri() + "?mode=ro&immutable=1", uri=True) as connection:
                    self.assertEqual(connection.execute(f"SELECT COUNT(*) FROM {view}").fetchone(), (count,))
                    if version == "V1.21":
                        self.assertEqual(connection.execute(
                            f"SELECT formal_order FROM {view} ORDER BY formal_order"
                        ).fetchall(), [(i,) for i in range(1, 592)])
        self.assertTrue((ROOT / "releases/V1.21").is_dir())
        self.assertFalse((ROOT / "releases/V1.22").exists())

    def test_exact_historical_candidate_and_formal_replay_is_read_only(self):
        roots = [ROOT / "releases" / version for version, *_ in FROZEN]
        before = [tree(root) for root in roots]
        for verify, request, count in historical_requests():
            candidate = request.candidate
            candidate_before = tree(candidate.candidate_dir)
            report = verify(request, PipelineConfig(ROOT))
            self.assertEqual(report.status, "PASS")
            self.assertEqual(len(report.checks), count)
            self.assertTrue(all(check.passed for check in report.checks))
            self.assertEqual(tree(candidate.candidate_dir), candidate_before)
        self.assertEqual([tree(root) for root in roots], before)

    def test_2019_approved_evidence_and_original_proposals_remain_immutable(self):
        source = ROOT / "data/staging/task10b-hkdse-2019"
        resolution = source / "transcription-human-resolution-000002"
        patch = json.loads((resolution / "evidence/PATCH_IMMUTABILITY.json").read_text())
        approval = json.loads((resolution / "approval/approval_verification.json").read_text())
        self.assertEqual(approval["transcription_digest"],
                         "3139b39d7c42d17fbc28870d00127dd2792943860ef615a2c950d528f98b6829")
        self.assertEqual(len(patch["original_2019_files"]), 21)
        self.assertEqual(len(approval["proposal_artifact_hashes"]), 7)
        for root, mapping in ((source, patch["original_2019_files"]),
                              (resolution, approval["proposal_artifact_hashes"])):
            for relative, digest in mapping.items():
                self.assertEqual(sha(root / relative), digest, relative)
