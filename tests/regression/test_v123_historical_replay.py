"""Read-only V1.23 historical authority acceptance; never materialize old data."""
import hashlib
import json
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

    def test_append_only_public_surface_has_no_new_promotion_authority(self):
        from tests.unit import test_v123_models
        import joy_m2.ingest as ingest
        test_v123_models.V123ApiTests("test_exact_append_only_surface").test_exact_append_only_surface()
        self.assertFalse(any("v123" in name.lower() and ("promotion" in name.lower() or "publish" in name.lower()) for name in ingest.__all__))

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
        self.assertFalse((ROOT/"releases/V1.23").exists())
