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
from joy_m2.ingest.v123_manifest import load_v123_import_manifest
from joy_m2.ingest.v123_models import (
    V123CandidateContract,
    V123PreflightRequest,
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
BASELINE = ROOT / "releases/V1.22/Joy_M2_Complete_Question_DB_V1_22.sqlite3"
BASELINE_SHA = "a474846a5b1d10a0fe48a259522fbb327747319f4a114452bf9f294405d8d9e0"
BASELINE_SIZE = 10_510_336
BASELINE_MANIFEST_SHA = "441e00ac1536b959b40b6177bd17a6f14632a287f85145e202a51bcf137ddc8b"
BASELINE_RELEASE_DIGEST = "89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b"
GENESIS = "ea3b7db78210e045761784a2e415387c1b17f13b5aedde484ca2ae248a45eec7"


def _contract() -> V123CandidateContract:
    return V123CandidateContract(
        "V1.23", "V1.22", 639, BASELINE_SHA, BASELINE_SIZE,
        BASELINE_MANIFEST_SHA, 7915, BASELINE_RELEASE_DIGEST,
        "task13-v123-import-manifest-v1", "task13-v123-preflight-v1",
        "task13-v123-import-approval-v1", "task13-v123-candidate-manifest-v1",
        "task13-v123-candidate-v1", "task13-v123-candidate-identity-v1",
        "task13-v123-rollback-v1", 123, "Joy_M2_V1.23_candidate.sqlite3",
        "candidate_manifest.json", "SHA256SUMS", "rollback.json",
        "authority/batches", "images/sha256", "formal_complete_questions_v122",
        (
            "task13_v123_batch_ledger_v1", "task13_v123_candidates_v1",
            "task13_v123_images_v1", "task13_v123_taxonomy_v1",
        ),
        ("task13_candidate_questions_v123",),
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
    payload["schema_version"] = "task13-v123-import-manifest-v1"
    payload["target_release_version"] = "V1.23"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return root


def _request(package: Path) -> V123PreflightRequest:
    return V123PreflightRequest(
        load_v123_import_manifest(package / "import_manifest.json"),
        package,
        ArtifactRef(BASELINE, BASELINE_SHA, BASELINE_SIZE, "sqlite"),
        None,
        _contract(),
    )


class V123PreflightApiTests(unittest.TestCase):
    def test_v123_preflight_public_api_exists(self):
        import joy_m2.ingest as ingest

        self.assertTrue(callable(getattr(ingest, "preflight_v123_import", None)))
        self.assertEqual(
            tuple(inspect.signature(ingest.preflight_v123_import).parameters),
            ("request", "config"),
        )


class V123GenesisPreflightTests(unittest.TestCase):
    def formal_record(self, year=2019):
        with sqlite3.connect(BASELINE.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as con:
            con.row_factory = sqlite3.Row
            row = con.execute("SELECT * FROM formal_complete_questions_v122 WHERE question_id=?",
                              (f"HKDSE-{year}-M2-Q01",)).fetchone()
        self.assertIsNotNone(row)
        return dict(row)

    def matching_package(self, year=2019):
        row = self.formal_record(year)
        manifest_path = self.package / "import_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        for image in manifest["image_files"]:
            (self.package / image["relative_path"]).unlink()
        manifest["image_files"] = []
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        _rewrite_record(self.package, {**{k: row[k] for k in (
            "source_id", "source_question_number", "source_section", "source_fragment_hash", "question_text_original")},
            "image_paths": [], "image_roles": []})
        return row

    def test_fuller_ms_exact_duplicate_stays_blocked(self):
        self.matching_package()
        _rewrite_record(self.package, {"solution_original": "Synthetic fuller MS does not change identity", "answer_status": "source_provided"})
        result = self.preflight()
        self.assertEqual((result.report.duplicate_count, result.report.new_candidate_count, result.report.rejected_count), (1, 0, 0))
        self.assertEqual(result.report.blocking_errors, ("duplicate_exact",))
        self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")

    def test_truthful_second_source_matching_hash_collides(self):
        self.matching_package()
        _rewrite_record(self.package, {"source_id": "SYNTHETIC-SECOND-SOURCE"})
        result = self.preflight()
        self.assertEqual((result.report.new_candidate_count, result.report.rejected_count), (0, 1))
        self.assertEqual(set(result.report.blocking_errors), {"collision_fragment_sha256", "collision_normalized_text_sha256"})

    def test_nonmatching_identity_is_not_proof_of_new_original(self):
        result = self.preflight()
        self.assertEqual(result.report.new_candidate_count, 1)
        self.assertEqual(result.issues, ())
        self.assertNotIn("new_original_count", vars(result.report))

    def test_single_baseline_adaptation_predicates(self):
        self.matching_package()
        _rewrite_record(self.package, {"question_text_original": "Synthetic independently transformed text x+7=9."})
        result = self.preflight()
        self.assertEqual((result.report.new_candidate_count, result.report.rejected_count), (1, 0))
        self.assertEqual(len(result.report.adaptations), 1)
        self.assertEqual(result.report.adaptations[0].reference_question_id, "HKDSE-2019-M2-Q01")
        self.assertEqual(result.report.adaptations[0].adaptation_kind, "adapted")
        _rewrite_record(self.package, {"proposed_question_id": "HKDSE-2019-M2-Q01"})
        rejected = self.preflight()
        self.assertEqual(rejected.report.adaptations, ())
        self.assertIn("collision_candidate_id", rejected.report.blocking_errors)

    def test_multiple_matches_ambiguous(self):
        self.matching_package()
        _rewrite_record(self.package, {"source_fragment_hash": self.formal_record(2020)["source_fragment_hash"]})
        result = self.preflight()
        self.assertEqual((result.report.ambiguous_count, result.report.rejected_count, result.report.new_candidate_count), (1, 1, 0))
        self.assertIn("duplicate_ambiguous", result.report.blocking_errors)

    def test_package_blocker_preserves_record_classification(self):
        self.matching_package()
        request = _request(self.package)
        answer = self.package / request.manifest.answer_files[0].relative_path
        answer.write_bytes(b"changed answer file")
        result = self.invoke(request)
        self.assertEqual((result.report.duplicate_count, result.report.rejected_count), (1, 0))
        self.assertEqual(set(result.report.blocking_errors), {"file_integrity_mismatch", "duplicate_exact"})

    def test_untrusted_candidate_file_is_omitted_not_counted_rejected(self):
        request = _request(self.package)
        (self.package / request.manifest.candidate_records[0].relative_path).write_bytes(b"untrusted")
        result = self.invoke(request)
        self.assertEqual((result.report.detected_count, result.report.rejected_count), (0, 0))
        self.assertIn("file_integrity_mismatch", result.report.blocking_errors)

    def test_mixed_duplicate_blocks_batch(self):
        from tests.integration.test_v120_preflight import _rewrite_candidate_payload
        self.matching_package()
        records = json.loads((self.package / "records/candidates.json").read_text())
        second = {**records[0], "proposed_question_id": "SYNTHETIC-NEW-Q2", "source_id": "SYNTHETIC-NEW",
                  "source_fragment_hash": "4" * 64, "question_text_original": "Synthetic x+4=11. Solve."}
        _rewrite_candidate_payload(self.package, json.dumps(records + [second]).encode())
        result = self.preflight()
        self.assertEqual((result.report.detected_count, result.report.duplicate_count, result.report.new_candidate_count), (2, 1, 1))
        self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")

    def test_each_2019_through_2022_layer_participates(self):
        original = self.package
        for year in (2019, 2020, 2021, 2022):
            with self.subTest(year=year):
                self.package = _make_package(self.root / str(year))
                self.matching_package(year)
                result = self.preflight()
                self.assertEqual((result.report.before_count, result.report.duplicate_count), (639, 1))
        self.package = original

    def test_historical_image_identity_is_indexed_without_restage(self):
        self.preflight()
        from joy_m2.ingest import v123_preflight as m
        indexes, _, _ = m._formal_indexes(BASELINE)
        from tests.integration.test_v120_preflight import FORMAL_IMAGE_PATH, FORMAL_IMAGE_ROLE, FORMAL_IMAGE_SHA
        images = indexes["references"]["M2QD-DA-PARTB-Q4"]["images"]
        self.assertIn((FORMAL_IMAGE_PATH, FORMAL_IMAGE_ROLE, FORMAL_IMAGE_SHA), images)

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.package = _make_package(self.root)
        for name in ("data/staging", "data/baselines", "releases"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.config = PipelineConfig(self.root)
        self.assertEqual(_request(self.package).manifest.target_release_version, "V1.23")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def invoke(self, request):
        from joy_m2.ingest import preflight_v123_import
        try:
            return preflight_v123_import(request, self.config)
        except NotImplementedError:
            self.fail("V1.23 genesis preflight behavior missing")

    def preflight(self, package: Path | None = None):
        from joy_m2.ingest import preflight_v123_import

        try:
            return preflight_v123_import(_request(package or self.package), self.config)
        except NotImplementedError:
            self.fail('V1.23 genesis preflight behavior missing')

    def test_complete_639_baseline_and_genesis(self):
        result = self.preflight()
        self.assertEqual(result.report.status, "READY FOR USER IMPORT APPROVAL")
        self.assertEqual(result.report.parent_candidate_digest, GENESIS)
        self.assertEqual(result.report.parent_batch_count, 0)
        self.assertEqual(result.report.before_count, 639)
        self.assertEqual(result.report.detected_count, 1)
        self.assertEqual(result.report.new_candidate_count, 1)
        self.assertEqual(result.report.duplicate_count, 0)
        self.assertEqual(result.report.rejected_count, 0)
        self.assertEqual(result.report.projected_after_count, 640)
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
            V123PreflightRequest(
                load_v123_import_manifest(self.package / "import_manifest.json"),
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

    def test_exact_duplicate_against_formal_v122_is_blocking(self):
        with sqlite3.connect(f'{BASELINE.as_uri()}?mode=ro', uri=True) as connection:
            row = connection.execute(
                "SELECT question_text_original FROM formal_complete_questions_v122 "
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


    def test_canonical_genesis_projection(self):
        payload = {
            "baseline_database_sha256": BASELINE_SHA,
            "baseline_question_count": 639,
            "baseline_release_digest": BASELINE_RELEASE_DIGEST,
            "baseline_release_version": "V1.22", "candidate_count": 0,
            "schema": "task13-v123-genesis-v1", "target_release_version": "V1.23",
        }
        digest = hashlib.sha256((json.dumps(payload, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False) + "\n").encode()).hexdigest()
        self.assertEqual(digest, GENESIS)
        self.assertIsNone(_request(self.package).parent_candidate)
        self.assertEqual(self.preflight().report.parent_candidate_digest, digest)

    def test_all_639_rows_indexed_once_including_2019_2022(self):
        with sqlite3.connect(f"{BASELINE.as_uri()}?mode=ro", uri=True) as con:
            row = con.execute("SELECT source_id,source_question_number,source_section,"
                "source_fragment_hash,question_text_original FROM formal_complete_questions_v122 "
                "WHERE formal_order > 591 ORDER BY formal_order LIMIT 1").fetchone()
        _rewrite_record(self.package, dict(zip(("source_id","source_question_number",
            "source_section","source_fragment_hash","question_text_original"), row),
            image_paths=[], image_roles=[]))
        result = self.preflight()
        self.assertEqual((result.report.before_count, result.report.duplicate_count,
            result.report.new_candidate_count, result.report.rejected_count), (639,1,0,0))
        from joy_m2.ingest import v123_preflight as m
        indexes, _, _ = m._formal_indexes(BASELINE)
        self.assertEqual(len(indexes["references"]), 639)

    def test_deep_schema_view_count_gates_not_masked_by_outer_hash(self):
        self.preflight()  # valid control; no missing prerequisite counted as deeper RED
        from joy_m2.ingest import v123_preflight as m
        for mutation in ("control", "schema", "version", "view", "count", "duplicate_id", "selectable", "status"):
            with self.subTest(mutation=mutation):
                path = self.root / (mutation + ".sqlite3")
                shutil.copyfile(BASELINE, path)
                with sqlite3.connect(path) as con:
                    if mutation == "schema":
                        con.execute("UPDATE release_metadata_v2 SET value='wrong' WHERE key='schema_version'")
                    if mutation == "version":
                        con.execute("UPDATE release_metadata_v2 SET value='V1.21' WHERE key='release_version'")
                    if mutation in ("view", "count", "duplicate_id", "selectable", "status"):
                        sql = con.execute("SELECT sql FROM sqlite_master WHERE name='formal_complete_questions_v122'").fetchone()[0]
                        columns = [row[1] for row in con.execute("PRAGMA table_info(formal_complete_questions_v122)")]
                        con.execute("DROP VIEW formal_complete_questions_v122")
                        if mutation == "count":
                            import re
                            query = re.split(r"\bAS\b", sql, maxsplit=1, flags=re.IGNORECASE)[1]
                            con.execute("CREATE VIEW formal_complete_questions_v122 AS SELECT * FROM (" + query + ") WHERE formal_order < 639")
                        elif mutation in ("duplicate_id", "selectable", "status"):
                            import re
                            query = re.split(r"\bAS\b", sql, maxsplit=1, flags=re.IGNORECASE)[1]
                            altered = {"duplicate_id": ("question_id", "'repeated-id'"),
                                       "selectable": ("selectable", "0"), "status": ("record_status", "'candidate'")}
                            field, value = altered[mutation]
                            projection = ",".join(value + ' AS "' + col + '"' if col == field else '"' + col + '"' for col in columns)
                            con.execute("CREATE VIEW formal_complete_questions_v122 AS SELECT " + projection + " FROM (" + query + ")")
                data = path.read_bytes()
                with mock.patch.object(m, "_BASELINE_SIZE", len(data)), mock.patch.object(m, "_BASELINE_SHA", hashlib.sha256(data).hexdigest()):
                    if mutation == "control":
                        self.assertEqual(len(m._formal_indexes(path)[0]["references"]), 639)
                    else:
                        with self.assertRaises(PipelineError):
                            m._formal_indexes(path)

    def test_file_integrity_after_loading_is_structured_blocker(self):
        request = _request(self.package)
        path = self.package / request.manifest.image_files[0].relative_path
        path.write_bytes(b"changed bytes")
        from joy_m2.ingest import preflight_v123_import
        try:
            result = preflight_v123_import(request, self.config)
        except NotImplementedError:
            self.fail("V1.23 file-integrity preflight missing")
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
        from joy_m2.ingest import preflight_v123_import
        copy = self.root / "baseline # 副本"
        copy.mkdir()
        database = copy / BASELINE.name
        shutil.copyfile(BASELINE, database)
        manifest = copy / "manifest.json"
        shutil.copyfile(BASELINE.parent / "manifest.json", manifest)
        request = replace(_request(self.package),
            baseline_database=ArtifactRef(database, BASELINE_SHA, BASELINE_SIZE, "sqlite"))
        self.assertEqual(self.invoke(request).report.before_count, 639)
        for mutation in ("identity", "missing"):
            with self.subTest(mutation=mutation):
                if mutation == "identity":
                    payload = json.loads(manifest.read_text())
                    payload["release_version"] = "V9.99"
                    manifest.write_text(json.dumps(payload))
                else:
                    manifest.unlink()
                with self.assertRaises(PipelineError):
                    self.invoke(request)


if __name__ == "__main__":
    unittest.main()
