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
from joy_m2.errors import PipelineError
from dataclasses import replace
from unittest import mock
from joy_m2.ingest.v122_manifest import load_v122_import_manifest
from joy_m2.ingest.v122_models import (
    V122CandidateContract,
    V122PreflightRequest,
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
BASELINE = ROOT / "releases/V1.21/Joy_M2_Complete_Question_DB_V1_21.sqlite3"
BASELINE_SHA = "93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a"
BASELINE_SIZE = 10_063_872
BASELINE_MANIFEST_SHA = "a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40"
BASELINE_RELEASE_DIGEST = "f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3"
GENESIS = "7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7"


def _contract() -> V122CandidateContract:
    return V122CandidateContract(
        "V1.22", "V1.21", 591, BASELINE_SHA, BASELINE_SIZE,
        BASELINE_MANIFEST_SHA, 7913, BASELINE_RELEASE_DIGEST,
        "task12-v122-import-manifest-v1", "task12-v122-preflight-v1",
        "task12-v122-import-approval-v1", "task12-v122-candidate-manifest-v1",
        "task12-v122-candidate-v1", "task12-v122-candidate-identity-v1",
        "task12-v122-rollback-v1", 122, "Joy_M2_V1.22_candidate.sqlite3",
        "candidate_manifest.json", "SHA256SUMS", "rollback.json",
        "authority/batches", "images/sha256", "formal_complete_questions_v121",
        (
            "task12_v122_batch_ledger_v1", "task12_v122_candidates_v1",
            "task12_v122_images_v1", "task12_v122_taxonomy_v1",
        ),
        ("task12_candidate_questions_v122",),
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
    payload["schema_version"] = "task12-v122-import-manifest-v1"
    payload["target_release_version"] = "V1.22"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return root


def _request(package: Path) -> V122PreflightRequest:
    return V122PreflightRequest(
        load_v122_import_manifest(package / "import_manifest.json"),
        package,
        ArtifactRef(BASELINE, BASELINE_SHA, BASELINE_SIZE, "sqlite"),
        None,
        _contract(),
    )


class V122PreflightApiTests(unittest.TestCase):
    def test_v122_preflight_public_api_exists(self):
        import joy_m2.ingest as ingest

        self.assertTrue(callable(getattr(ingest, "preflight_v122_import", None)))
        self.assertEqual(
            tuple(inspect.signature(ingest.preflight_v122_import).parameters),
            ("request", "config"),
        )


class V122GenesisPreflightTests(unittest.TestCase):
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
        from joy_m2.ingest import preflight_v122_import

        try:
            return preflight_v122_import(_request(package or self.package), self.config)
        except NotImplementedError:
            self.fail('V1.22 genesis preflight behavior missing')

    def test_genesis_preflight_closes_counts_and_authority(self):
        result = self.preflight()
        self.assertEqual(result.report.status, "READY FOR USER IMPORT APPROVAL")
        self.assertEqual(result.report.parent_candidate_digest, GENESIS)
        self.assertEqual(result.report.parent_batch_count, 0)
        self.assertEqual(result.report.before_count, 591)
        self.assertEqual(result.report.detected_count, 1)
        self.assertEqual(result.report.new_candidate_count, 1)
        self.assertEqual(result.report.duplicate_count, 0)
        self.assertEqual(result.report.rejected_count, 0)
        self.assertEqual(result.report.projected_after_count, 592)
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
        with self.assertRaises(PipelineError):
            V122PreflightRequest(
                load_v122_import_manifest(self.package / "import_manifest.json"),
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

    def test_exact_duplicate_against_formal_v121_is_blocking(self):
        with sqlite3.connect(f'{BASELINE.as_uri()}?mode=ro', uri=True) as connection:
            row = connection.execute(
                "SELECT question_text_original FROM formal_complete_questions_v121 "
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


    def test_no_parent_artifact_still_binds_reconstructed_genesis(self):
        payload = {
            "baseline_database_sha256": BASELINE_SHA,
            "baseline_question_count": 591,
            "baseline_release_digest": BASELINE_RELEASE_DIGEST,
            "baseline_release_version": "V1.21", "candidate_count": 0,
            "schema": "task12-v122-genesis-v1", "target_release_version": "V1.22",
        }
        digest = hashlib.sha256((json.dumps(payload, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False) + "\n").encode()).hexdigest()
        self.assertEqual(digest, GENESIS)
        self.assertIsNone(_request(self.package).parent_candidate)
        self.assertEqual(self.preflight().report.parent_candidate_digest, digest)

    def test_all_591_rows_indexed_once_including_2015_2018(self):
        with sqlite3.connect(f"{BASELINE.as_uri()}?mode=ro", uri=True) as con:
            row = con.execute("SELECT source_id,source_question_number,source_section,"
                "source_fragment_hash,question_text_original FROM formal_complete_questions_v121 "
                "WHERE formal_order > 543 ORDER BY formal_order LIMIT 1").fetchone()
        _rewrite_record(self.package, dict(zip(("source_id","source_question_number",
            "source_section","source_fragment_hash","question_text_original"), row),
            image_paths=[], image_roles=[]))
        result = self.preflight()
        self.assertEqual((result.report.before_count, result.report.duplicate_count,
            result.report.new_candidate_count, result.report.rejected_count), (591,1,0,0))
        from joy_m2.ingest import v122_preflight as m
        indexes, _, _ = m._formal_indexes(BASELINE)
        self.assertEqual(len(indexes["references"]), 591)

    def test_deep_schema_view_count_gates_not_masked_by_outer_hash(self):
        self.preflight()  # valid control; no missing prerequisite counted as deeper RED
        from joy_m2.ingest import v122_preflight as m
        for mutation in ("control", "schema", "view", "count"):
            with self.subTest(mutation=mutation):
                path = self.root / (mutation + ".sqlite3")
                shutil.copyfile(BASELINE, path)
                with sqlite3.connect(path) as con:
                    if mutation == "schema":
                        con.execute("UPDATE release_metadata_v2 SET value='wrong' WHERE key='schema_version'")
                    if mutation in ("view", "count"):
                        sql = con.execute("SELECT sql FROM sqlite_master WHERE name='formal_complete_questions_v121'").fetchone()[0]
                        con.execute("DROP VIEW formal_complete_questions_v121")
                        if mutation == "count":
                            import re
                            query = re.split(r"\bAS\b", sql, maxsplit=1, flags=re.IGNORECASE)[1]
                            con.execute("CREATE VIEW formal_complete_questions_v121 AS SELECT * FROM (" + query + ") WHERE formal_order < 591")
                data = path.read_bytes()
                with mock.patch.object(m, "_BASELINE_SIZE", len(data)), mock.patch.object(m, "_BASELINE_SHA", hashlib.sha256(data).hexdigest()):
                    if mutation == "control":
                        self.assertEqual(len(m._formal_indexes(path)[0]["references"]), 591)
                    else:
                        with self.assertRaises(PipelineError):
                            m._formal_indexes(path)

    def test_file_integrity_after_loading_is_structured_blocker(self):
        request = _request(self.package)
        path = self.package / request.manifest.image_files[0].relative_path
        path.write_bytes(b"changed bytes")
        from joy_m2.ingest import preflight_v122_import
        try:
            result = preflight_v122_import(request, self.config)
        except NotImplementedError:
            self.fail("V1.22 file-integrity preflight missing")
        self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")
        self.assertIn("file_integrity_mismatch", {x.code for x in result.issues})
        self.assertEqual(result.report.detected_count,
            result.report.new_candidate_count + result.report.duplicate_count + result.report.rejected_count)

    def test_taxonomy_and_candidate_shape_blockers_preserve_issue_order(self):
        from tests.integration.test_v120_preflight import _rewrite_candidate_payload
        for code, change in (
            ("unknown_primary_type", {"primary_type":"NOT-CONTROLLED"}),
            ("unknown_tag", {"tags":["NOT-CONTROLLED"]}),
            ("invalid_candidate_record", {"difficulty_level":True}),
        ):
            with self.subTest(code=code):
                package = _make_package(self.root / code)
                _rewrite_record(package, change)
                result = self.preflight(package)
                self.assertIn(code, {i.code for i in result.issues})
                expected_rejected = 0 if code == "invalid_candidate_record" else 1
                self.assertEqual((result.report.new_candidate_count, result.report.rejected_count), (0, expected_rejected))
                self.assertEqual(result.issues, tuple(sorted(result.issues, key=lambda i:(i.proposed_question_id or "",i.code,i.field,i.evidence))))
        package = _make_package(self.root / "malformed")
        _rewrite_candidate_payload(package, b"{")
        self.assertIn("malformed_candidate_json", {i.code for i in self.preflight(package).issues})

    def test_sibling_manifest_is_required_even_when_database_digest_is_correct(self):
        from joy_m2.ingest import preflight_v122_import
        copy = self.root / "baseline-copy"
        copy.mkdir()
        database = copy / BASELINE.name
        shutil.copyfile(BASELINE, database)
        manifest = copy / "manifest.json"
        shutil.copyfile(BASELINE.parent / "manifest.json", manifest)
        request = replace(_request(self.package),
            baseline_database=ArtifactRef(database, BASELINE_SHA, BASELINE_SIZE, "sqlite"))
        self.assertEqual(preflight_v122_import(request, self.config).report.before_count, 591)
        for mutation in ("identity", "missing"):
            with self.subTest(mutation=mutation):
                if mutation == "identity":
                    payload = json.loads(manifest.read_text())
                    payload["release_version"] = "V9.99"
                    manifest.write_text(json.dumps(payload))
                else:
                    manifest.unlink()
                with self.assertRaises(PipelineError):
                    preflight_v122_import(request, self.config)


if __name__ == "__main__":
    unittest.main()
