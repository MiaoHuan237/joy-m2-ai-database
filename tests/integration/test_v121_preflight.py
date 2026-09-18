from __future__ import annotations

import inspect
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.ingest.v121_manifest import load_v121_import_manifest
from joy_m2.ingest.v121_models import (
    V121CandidateContract,
    V121PreflightRequest,
)
from joy_m2.models import ArtifactRef
from tests.integration.test_v120_preflight import (
    REFERENCE_FRAGMENT,
    REFERENCE_NUMBER,
    REFERENCE_SECTION,
    REFERENCE_SOURCE_ID,
    _rewrite_record,
)


FIXTURE = ROOT / "tests/fixtures/task10a/v120-batch-a"
BASELINE = ROOT / "releases/V1.20/Joy_M2_Complete_Question_DB_V1_20.sqlite3"
BASELINE_SHA = "b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292"
BASELINE_SIZE = 9_768_960
BASELINE_MANIFEST_SHA = "19ac2e43ded74a3f3eaf75c184b5eb231c9f1b0b152f5914cd822a321b045098"
BASELINE_RELEASE_DIGEST = "1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf"
GENESIS = "331192032f184a44ed383e6dacc2f06fbacb60ad94414298fcb935ff56cb5906"


def _contract() -> V121CandidateContract:
    return V121CandidateContract(
        "V1.21", "V1.20", 543, BASELINE_SHA, BASELINE_SIZE,
        BASELINE_MANIFEST_SHA, 6643, BASELINE_RELEASE_DIGEST,
        "task11-v121-import-manifest-v1", "task11-v121-preflight-v1",
        "task11-v121-import-approval-v1", "task11-v121-candidate-manifest-v1",
        "task11-v121-candidate-v1", "task11-v121-candidate-identity-v1",
        "task11-v121-rollback-v1", 121, "Joy_M2_V1.21_candidate.sqlite3",
        "candidate_manifest.json", "SHA256SUMS", "rollback.json",
        "authority/batches", "images/sha256", "formal_complete_questions_v120",
        (
            "task11_v121_batch_ledger_v1", "task11_v121_candidates_v1",
            "task11_v121_images_v1", "task11_v121_taxonomy_v1",
        ),
        ("task11_candidate_questions_v121",),
    )


def _fingerprint(root: Path) -> tuple[tuple[str, str, int], ...]:
    return tuple(
        (
            path.relative_to(root).as_posix(),
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_size,
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )


def _make_package(parent: Path) -> Path:
    root = parent / "package"
    shutil.copytree(FIXTURE, root)
    manifest_path = root / "import_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["schema_version"] = "task11-v121-import-manifest-v1"
    payload["target_release_version"] = "V1.21"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return root


def _request(package: Path) -> V121PreflightRequest:
    return V121PreflightRequest(
        load_v121_import_manifest(package / "import_manifest.json"),
        package,
        ArtifactRef(BASELINE, BASELINE_SHA, BASELINE_SIZE, "sqlite"),
        None,
        _contract(),
    )


class V121PreflightApiTests(unittest.TestCase):
    def test_v121_preflight_public_api_exists(self):
        import joy_m2.ingest as ingest

        self.assertTrue(callable(getattr(ingest, "preflight_v121_import", None)))
        self.assertEqual(
            tuple(inspect.signature(ingest.preflight_v121_import).parameters),
            ("request", "config"),
        )


class V121GenesisPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.package = _make_package(self.root)
        for name in ("data/staging", "data/baselines", "releases"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.config = PipelineConfig(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def preflight(self, package: Path | None = None):
        from joy_m2.ingest import preflight_v121_import

        return preflight_v121_import(_request(package or self.package), self.config)

    def test_genesis_preflight_closes_counts_and_authority(self):
        result = self.preflight()
        self.assertEqual(result.report.status, "READY FOR USER IMPORT APPROVAL")
        self.assertEqual(result.report.parent_candidate_digest, GENESIS)
        self.assertEqual(result.report.parent_batch_count, 0)
        self.assertEqual(result.report.before_count, 543)
        self.assertEqual(result.report.detected_count, 1)
        self.assertEqual(result.report.new_candidate_count, 1)
        self.assertEqual(result.report.duplicate_count, 0)
        self.assertEqual(result.report.rejected_count, 0)
        self.assertEqual(result.report.projected_after_count, 544)
        self.assertEqual(result.effective_state.candidate_digest, GENESIS)

    def test_equivalent_roots_produce_identical_preflight(self):
        first = self.preflight()
        second_parent = self.root / "other-root"
        second = self.preflight(_make_package(second_parent))
        self.assertEqual(first, second)

    def test_preflight_is_read_only_for_package_and_formal_baseline(self):
        package_before = _fingerprint(self.package)
        baseline_before = (
            hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
            BASELINE.stat().st_size,
        )
        self.preflight()
        self.assertEqual(_fingerprint(self.package), package_before)
        self.assertEqual(
            (hashlib.sha256(BASELINE.read_bytes()).hexdigest(), BASELINE.stat().st_size),
            baseline_before,
        )

    def test_wrong_baseline_artifact_cannot_enter_preflight(self):
        with self.assertRaises(Exception):
            V121PreflightRequest(
                load_v121_import_manifest(self.package / "import_manifest.json"),
                self.package,
                ArtifactRef(BASELINE, "0" * 64, BASELINE_SIZE, "sqlite"),
                None,
                _contract(),
            )

    def test_malformed_candidate_is_structured_blocking_failure(self):
        candidate_path = self.package / "records/candidates.json"
        candidate_path.write_bytes(b"{}\n")
        manifest_path = self.package / "import_manifest.json"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        evidence = payload["candidate_records"][0]
        evidence["sha256"] = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
        evidence["size_bytes"] = candidate_path.stat().st_size
        manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        result = self.preflight()
        self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")
        self.assertIn("invalid_candidate_top_level", {issue.code for issue in result.issues})

    def test_exact_duplicate_against_formal_v120_is_blocking(self):
        with sqlite3.connect(BASELINE) as connection:
            row = connection.execute(
                "SELECT question_text_original FROM formal_complete_questions_v120 "
                "WHERE source_id=? AND source_question_number=? AND source_section=?",
                (REFERENCE_SOURCE_ID, REFERENCE_NUMBER, REFERENCE_SECTION),
            ).fetchone()
        self.assertIsNotNone(row)
        _rewrite_record(self.package, {
            "source_id": REFERENCE_SOURCE_ID,
            "source_question_number": REFERENCE_NUMBER,
            "source_section": REFERENCE_SECTION,
            "source_fragment_hash": REFERENCE_FRAGMENT,
            "question_text_original": row[0],
            "image_paths": [],
            "image_roles": [],
        })
        result = self.preflight()
        self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")
        self.assertIn("duplicate_exact", {issue.code for issue in result.issues})


if __name__ == "__main__":
    unittest.main()
