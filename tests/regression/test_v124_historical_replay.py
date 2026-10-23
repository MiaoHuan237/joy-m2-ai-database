"""V1.24 shared layer leaves every published predecessor and its evidence unchanged."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from joy_m2.config import PipelineConfig
from joy_m2.errors import PipelineError
from joy_m2.ingest.v124_models import V124CandidateBuildRequest
from joy_m2.ingest.v124_writer import build_v124_candidate
from tests.integration.test_v124_candidate import _approved
from tests.integration.test_v124_preflight import _make_package, _contract
from tests.regression.test_v123_historical_replay import (
    FROZEN as OLD_FROZEN, sha, tree,
)
from tests.regression import test_v123_historical_replay as historical

ROOT = Path(__file__).resolve().parents[2]
FROZEN = OLD_FROZEN + (("V1.23", 677, "formal_complete_questions_v123",
    "28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd"),)


class V124HistoricalReplayTests(unittest.TestCase):
    def test_six_frozen_databases_counts_and_formal_677_query(self):
        for version, count, view, digest in FROZEN:
            with self.subTest(version=version):
                path = ROOT / "releases" / version / f"Joy_M2_Complete_Question_DB_{version.replace('.', '_')}.sqlite3"
                self.assertEqual(sha(path), digest)
                with sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as db:
                    db.execute("PRAGMA query_only=ON")
                    self.assertEqual(db.execute(f"SELECT COUNT(*) FROM {view}").fetchone(), (count,))
                    if version == "V1.23":
                        rows = db.execute(f"SELECT formal_order,question_id,record_status,selectable FROM {view} ORDER BY formal_order").fetchall()
                        self.assertEqual([r[0] for r in rows], list(range(1, 678)))
                        self.assertEqual(len({r[1] for r in rows}), 677)
                        self.assertEqual({r[2:] for r in rows}, {("published", 1)})
                self.assertEqual(sha(path), digest)

    def test_historical_verifiers_source_approval_and_exports_still_match(self):
        for method in (
            "test_all_historical_formal_verifiers_and_candidate_replay_read_only",
            "test_approved_2023_source_checkpoint_unchanged",
            "test_append_only_public_surface_has_exact_promotion_suffix",
        ):
            with self.subTest(method=method):
                getattr(historical.V123HistoricalReplayTests(method), method)()
        import joy_m2.ingest as ingest
        self.assertFalse(any("v124" in x.lower() for x in ingest.__all__))

    def test_exact_published_v123_and_three_batch_replay_no_materialization(self):
        from tests.integration.test_v123_promotion import selected_candidate, promotion_contract, RECEIPTS
        from joy_m2.ingest import V123PromotionVerificationRequest, verify_v123_promotion
        receipts = {p: (ROOT / p).read_bytes() for p in RECEIPTS}
        formal_before = tree(ROOT / "releases/V1.23")
        candidate = selected_candidate()
        candidate_before = tree(candidate.candidate_dir)
        source_before = {str(b.package_root): tree(b.package_root) for b in candidate.approved_batches}
        report = verify_v123_promotion(V123PromotionVerificationRequest(
            ROOT / "releases/V1.23", candidate, promotion_contract()), PipelineConfig(ROOT))
        self.assertEqual(report.status, "PASS")
        self.assertEqual(len(report.checks), 21)
        self.assertTrue(all(c.passed for c in report.checks))
        self.assertEqual([len(b.preflight_result.candidates) for b in candidate.approved_batches], [12, 13, 13])
        self.assertEqual(tree(candidate.candidate_dir), candidate_before)
        self.assertEqual(tree(ROOT / "releases/V1.23"), formal_before)
        self.assertEqual({p: (ROOT / p).read_bytes() for p in RECEIPTS}, receipts)
        self.assertEqual({str(b.package_root): tree(b.package_root) for b in candidate.approved_batches}, source_before)
        manifest = json.loads((ROOT / "releases/V1.23/manifest.json").read_bytes())
        self.assertEqual(manifest["promotion"]["release_digest"],
            "84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc")

    def test_candidate_writer_cannot_publish_to_formal_path(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            package = _make_package(root)
            approved = _approved(package, PipelineConfig(ROOT))
            target = root / "releases/V1.24"
            target.parent.mkdir()
            with self.assertRaises(PipelineError):
                build_v124_candidate(V124CandidateBuildRequest((approved,), target, _contract()), PipelineConfig(root))
            self.assertFalse(target.exists())
