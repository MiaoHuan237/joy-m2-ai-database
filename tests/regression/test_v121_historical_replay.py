from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class V121HistoricalReplayTests(unittest.TestCase):
    def test_formal_v120_release_remains_exact_and_v121_is_not_formal(self):
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
        self.assertFalse((ROOT / "releases/V1.21").exists())

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
