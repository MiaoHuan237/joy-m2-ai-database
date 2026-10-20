"""Read-only V1.23 historical authority acceptance; never materialize old data."""
import hashlib
import json
import re
from pathlib import Path
import sqlite3
import tempfile
import unittest

from joy_m2.config import PipelineConfig
from joy_m2.errors import PipelineError
from joy_m2.ingest import (
    V122PromotionVerificationRequest, verify_v122_promotion,
    V123CandidateBuildRequest, build_v123_candidate,
)
from tests.regression.test_v122_historical_replay import (
    FROZEN as OLD_FROZEN, historical_requests, sha, tree,
)
from tests.integration.test_v122_promotion import real_candidate, promotion_contract
from tests.integration.test_v123_candidate import _approved
from tests.integration.test_v123_preflight import _make_package, _contract

ROOT = Path(__file__).resolve().parents[2]
FROZEN = OLD_FROZEN + (("V1.22",639,"formal_complete_questions_v122",
    "a474846a5b1d10a0fe48a259522fbb327747319f4a114452bf9f294405d8d9e0"),)

# Exact human release-promotion approval received 2026-10-20; Design section 8.
APPROVED_V123_RELEASE_DIGEST = "84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc"


def assert_v123_lifecycle(root, approved_digest):
    target=root/"releases/V1.23"
    if approved_digest is None:
        assert not target.exists() and not target.is_symlink(), "unapproved V1.23 publication"
        return
    assert type(approved_digest) is str and re.fullmatch(r"[0-9a-f]{64}",approved_digest)
    assert target.is_dir() and not target.is_symlink(), "approved release missing"
    from tests.integration.test_v123_promotion import selected_candidate, promotion_contract
    from joy_m2.ingest import V123PromotionVerificationRequest, verify_v123_promotion
    report=verify_v123_promotion(V123PromotionVerificationRequest(
        target,selected_candidate(root),promotion_contract()),PipelineConfig(root))
    assert report.status=="PASS" and len(report.checks)==21 and all(c.passed for c in report.checks)
    manifest=json.loads((target/"manifest.json").read_text())
    assert manifest["promotion"]["release_digest"]==approved_digest, "approval identity mismatch"


class V123HistoricalReplayTests(unittest.TestCase):
    def test_five_frozen_databases_counts_and_complete_639_view(self):
        for version,count,view,digest in FROZEN:
            with self.subTest(version=version):
                path = ROOT/"releases"/version/f"Joy_M2_Complete_Question_DB_{version.replace('.','_')}.sqlite3"
                self.assertEqual(sha(path),digest)
                with sqlite3.connect(path.resolve().as_uri()+"?mode=ro&immutable=1",uri=True) as db:
                    db.execute("PRAGMA query_only=ON")
                    self.assertEqual(db.execute(f"SELECT COUNT(*) FROM {view}").fetchone(),(count,))
                    if version=="V1.22":
                        rows=db.execute(f"SELECT formal_order,question_id,record_status,selectable FROM {view} ORDER BY formal_order").fetchall()
                        self.assertEqual([r[0] for r in rows],list(range(1,640)))
                        self.assertEqual(len({r[1] for r in rows}),639)
                        self.assertEqual({r[2:] for r in rows},{("published",1)})
                self.assertEqual(sha(path),digest)

    def test_all_historical_formal_verifiers_and_candidate_replay_read_only(self):
        roots=[ROOT/"releases"/version for version,*_ in FROZEN]
        before=[tree(root) for root in roots]
        requests=historical_requests()+((verify_v122_promotion,
            V122PromotionVerificationRequest(ROOT/"releases/V1.22",
                real_candidate(),promotion_contract()),21),)
        for verify,request,checks in requests:
            with self.subTest(version=request.release_dir if hasattr(request,"release_dir") else verify.__name__):
                candidate_before=tree(request.candidate.candidate_dir)
                report=verify(request,PipelineConfig(ROOT))
                self.assertEqual(report.status,"PASS")
                self.assertEqual(len(report.checks),checks)
                self.assertTrue(all(check.passed for check in report.checks))
                self.assertEqual(tree(request.candidate.candidate_dir),candidate_before)
        self.assertEqual([tree(root) for root in roots],before)

    def test_approved_2023_source_checkpoint_unchanged(self):
        e=ROOT/"data/staging/task10b-hkdse-2023/source-review-000001"
        digest="3a3a223a23f694083469281c64be5c5402152c557e3bc36654d400ce5143d618"
        self.assertEqual(sha(e/"transcription-proposal-000001/transcription.json"),
            "4c9df20019c54876f01e9c0a58352fceb07ed78d9d14246e3bd8288fcab6f700")
        self.assertEqual(sha(e/"input/source-corrected-staging-v2.json"),
            "351462b3e45d4ea0f5b84b400d28aa0431bf3c0a830b16aff8a2eda7940a7490")
        approval=json.loads((e/"TRANSCRIPTION_APPROVAL.json").read_text())
        self.assertEqual(approval,{"batch_id":"JOY-M2-HKDSE-2023-PP-MS",
            "transcription_digest":digest,
            "approval_text":f"USER APPROVED PDF TRANSCRIPTION BATCH JOY-M2-HKDSE-2023-PP-MS {digest}"})

    def test_append_only_public_surface_has_exact_promotion_suffix(self):
        from tests.unit import test_v123_models
        import joy_m2.ingest as ingest
        test_v123_models.V123ApiTests("test_exact_append_only_surface").test_exact_append_only_surface()
        self.assertEqual(ingest.__all__[-9:], (
            "V123PromotionContract","V123PromotionBuildRequest",
            "V123PromotionVerificationRequest","V123ReleasePromotionApproval",
            "V123PublicationRequest","V123PromotionArtifacts",
            "build_v123_promotion","verify_v123_promotion","publish_v123_release"))

    def test_isolated_lifecycle_requires_explicit_exact_approval(self):
        from tests.integration.test_v123_promotion import isolated_candidate, fixture_release, promotion_contract
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve()
            candidate=isolated_candidate(root)
            assert_v123_lifecycle(root,None)
            with self.subTest(case="approved-but-missing"), self.assertRaises(AssertionError):
                assert_v123_lifecycle(root,"1"*64)
            target=fixture_release(root/"releases/V1.23",candidate,promotion_contract())
            digest=json.loads((target/"manifest.json").read_text())["promotion"]["release_digest"]
            for bad in (None,"0"*64,"",True,[],digest.upper()):
                with self.subTest(bad=bad), self.assertRaises(AssertionError):
                    assert_v123_lifecycle(root,bad)
            assert_v123_lifecycle(root,digest)

    def test_synthetic_writer_refuses_formal_output_without_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"releases").mkdir()
            package=_make_package(root)
            approved=_approved(package,PipelineConfig(ROOT))
            with self.assertRaises(PipelineError):
                build_v123_candidate(V123CandidateBuildRequest(
                    (approved,),root/"releases/V1.23",_contract()),PipelineConfig(root))
            self.assertFalse((root/"releases/V1.23").exists())
        assert_v123_lifecycle(ROOT,APPROVED_V123_RELEASE_DIGEST)
