from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.ingest import (
    V120PromotionVerificationRequest,
    V121PromotionVerificationRequest,
    verify_v120_candidate,
    verify_v120_promotion,
    verify_v121_candidate,
    verify_v121_promotion,
)
from tests.integration.test_v120_promotion import (
    REAL_BATCHES as V120_BATCHES,
    _promotion_contract as v120_promotion_contract,
    candidate_for as v120_candidate_for,
)
from tests.integration.test_v121_promotion import (
    REAL_BATCHES as V121_BATCHES,
    promotion_contract,
    real_candidate as v121_candidate_for,
    tree,
)


class V121HistoricalReplayTests(unittest.TestCase):
    def test_historical_replay_remains_exact_after_v121_promotion(self):
        release = ROOT / "releases/V1.20"
        expected = {
            "Joy_M2_Complete_Question_DB_V1_20.sqlite3": (
                9_768_960,
                "b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292",
            ),
            "manifest.json": (
                6_643,
                "19ac2e43ded74a3f3eaf75c184b5eb231c9f1b0b152f5914cd822a321b045098",
            ),
            "rollback.json": (
                657,
                "27298a8e5983b31fc5349fbc41e49f821bd98ded17f5a9c94f5d37e94996a3db",
            ),
            "SHA256SUMS.txt": (
                268,
                "f6727df2d70fe2a44b2ff026a49e2bf0f6d178b8ff829026b84bc36253b74913",
            ),
        }
        self.assertEqual({path.name for path in release.iterdir()}, set(expected))
        for name, (size, digest) in expected.items():
            path = release / name
            self.assertEqual(path.stat().st_size, size, name)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest, name)
        for version, digest, count, view in (
            ("V1.18", "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7", 497, "complete_questions_v2"),
            ("V1.19", "5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff", 502, "formal_complete_questions_v119"),
        ):
            database = ROOT / "releases" / version / f"Joy_M2_Complete_Question_DB_{version.replace('.', '_')}.sqlite3"
            self.assertEqual(hashlib.sha256(database.read_bytes()).hexdigest(), digest)
            with sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1", uri=True) as connection:
                self.assertEqual(connection.execute(f"SELECT COUNT(*) FROM {view}").fetchone(), (count,))

        formal = ROOT / "releases/V1.21"
        self.assertTrue(formal.is_dir())
        approved = {
            "Joy_M2_Complete_Question_DB_V1_21.sqlite3": "93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a",
            "manifest.json": "a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40",
            "rollback.json": "c7170aa0eabb0f3d8e20df265d7ca5dd1c8aadd32e3836ca13c3143d1f450bb2",
            "SHA256SUMS.txt": "357bd18b4d77b545cf6deafde4216e9c82ba86187d8b405d3ee1bb1b12cb892f",
        }
        self.assertEqual({path.name for path in formal.iterdir()}, set(approved))
        for name, digest in approved.items():
            self.assertEqual(hashlib.sha256((formal / name).read_bytes()).hexdigest(), digest, name)
        manifest = json.loads((formal / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["release_version"], "V1.21")
        self.assertEqual(manifest["counts"]["formal_question_count"], 591)
        self.assertEqual(
            manifest["promotion"]["release_digest"],
            "f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3",
        )

        # Reuse committed read-only authority replay; never rebuild or publish.
        candidate = v121_candidate_for(materialize=False)
        report = verify_v121_promotion(
            V121PromotionVerificationRequest(formal, candidate, promotion_contract()),
            PipelineConfig(ROOT),
        )
        self.assertEqual(report.status, "PASS")
        self.assertEqual(len(report.checks), 21)
        self.assertTrue(all(check.passed for check in report.checks))

        # The only lifecycle difference in this isolated fixture is the exact
        # approved release copy. Historical candidate bytes/approvals stay fixed.
        with TemporaryDirectory(prefix="v121-historical-lifecycle-") as directory:
            root = Path(directory).resolve()
            copied = [Path("releases") / version for version in ("V1.18", "V1.19", "V1.20")]
            for _, _, _, package, generation in V120_BATCHES:
                copied.extend((Path("data/staging") / package, Path("data/staging") / generation))
            for ordinal, (year, _, _) in enumerate(V121_BATCHES, 1):
                batch_root = Path("data/staging") / f"task11-v121-hkdse-{year}"
                package = "canonical-v121-taxonomy-approved-a" if year == 2015 else "canonical-v121-approved-a"
                copied.extend((batch_root / package, batch_root / f"candidate-generation-{ordinal:06d}"))
            for relative in copied:
                shutil.copytree(ROOT / relative, root / relative)
            before = {relative: tree(root / relative) for relative in copied}
            snapshots = []
            config = PipelineConfig(root)
            for published in (False, True):
                if published:
                    shutil.copytree(formal, root / "releases/V1.21")
                self.assertEqual((root / "releases/V1.21").exists(), published)
                v120 = v120_candidate_for(root, materialize_candidates=False)
                v121 = v121_candidate_for(root=root, materialize=False)
                reports = (
                    verify_v120_candidate(v120, config),
                    verify_v121_candidate(v121, config),
                    verify_v120_promotion(
                        V120PromotionVerificationRequest(root / "releases/V1.20", v120, v120_promotion_contract()),
                        config,
                    ),
                )
                for replay_report, count in zip(reports, (24, 24, 21), strict=True):
                    self.assertEqual(replay_report.status, "PASS")
                    self.assertEqual(len(replay_report.checks), count)
                    self.assertTrue(all(check.passed for check in replay_report.checks))
                snapshots.append((v120, v121, reports))
            self.assertEqual(snapshots[0], snapshots[1])
            self.assertEqual(before, {relative: tree(root / relative) for relative in copied})
            self.assertEqual(tree(formal), tree(root / "releases/V1.21"))

    def test_formal_v120_identity_and_543_question_view_are_unchanged(self):
        database = ROOT / "releases/V1.20/Joy_M2_Complete_Question_DB_V1_20.sqlite3"
        with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone(), (120,))
            metadata = dict(connection.execute(
                "SELECT key, value FROM release_metadata_v2 "
                "WHERE key IN ('release_version', 'schema_version')"
            ))
            self.assertEqual(metadata["release_version"], "V1.20")
            self.assertEqual(metadata["schema_version"], "task10-v120-formal-v1")
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM formal_complete_questions_v120"
                ).fetchone(),
                (543,),
            )

    def test_v120_manifest_and_candidate_entry_points_remain_public(self):
        import joy_m2.ingest as ingest

        for name in (
            "load_v120_import_manifest",
            "preflight_v120_import",
            "build_v120_candidate",
            "verify_v120_candidate",
        ):
            self.assertTrue(callable(getattr(ingest, name, None)), name)


if __name__ == "__main__":
    unittest.main()
