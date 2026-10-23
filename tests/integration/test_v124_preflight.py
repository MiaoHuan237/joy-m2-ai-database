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
from joy_m2.ingest.v124_manifest import load_v124_import_manifest
from joy_m2.ingest.v124_models import (
    V124CandidateContract,
    V124PreflightRequest,
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
BASELINE = ROOT / "releases/V1.23/Joy_M2_Complete_Question_DB_V1_23.sqlite3"
BASELINE_SHA = "28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd"
BASELINE_SIZE = 10_928_128
BASELINE_MANIFEST_SHA = "54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498"
BASELINE_RELEASE_DIGEST = "84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc"
GENESIS = "797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a"


def _contract() -> V124CandidateContract:
    return V124CandidateContract(
        "V1.24", "V1.23", 677, BASELINE_SHA, BASELINE_SIZE,
        BASELINE_MANIFEST_SHA, 6728, BASELINE_RELEASE_DIGEST,
        "task14-v124-import-manifest-v1", "task14-v124-preflight-v1",
        "task14-v124-import-approval-v1", "task14-v124-candidate-manifest-v1",
        "task14-v124-candidate-v1", "task14-v124-candidate-identity-v1",
        "task14-v124-rollback-v1", 124, "Joy_M2_V1.24_candidate.sqlite3",
        "candidate_manifest.json", "SHA256SUMS", "rollback.json",
        "authority/batches", "images/sha256", "formal_complete_questions_v123",
        (
            "task14_v124_batch_ledger_v1", "task14_v124_candidates_v1",
            "task14_v124_images_v1", "task14_v124_taxonomy_v1",
        ),
        ("task14_candidate_questions_v124",),
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
    payload["schema_version"] = "task14-v124-import-manifest-v1"
    payload["target_release_version"] = "V1.24"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return root


def _request(package: Path, parent=None) -> V124PreflightRequest:
    return V124PreflightRequest(
        load_v124_import_manifest(package / "import_manifest.json"),
        package,
        ArtifactRef(BASELINE, BASELINE_SHA, BASELINE_SIZE, "sqlite"),
        parent,
        _contract(),
    )


class V124BaselineTests(unittest.TestCase):
    def reader(self, path):
        from joy_m2.ingest.v124_preflight import _formal_indexes
        try: return _formal_indexes(path)
        except NotImplementedError: self.fail('exact V123 formal baseline loader missing')

    def test_current_formal_677_not_inherited_candidate_double_count(self):
        before = _fingerprint(BASELINE.parent)
        indexes, primary, tags = self.reader(BASELINE)
        self.assertEqual(len(indexes['references']), 677)
        self.assertIn('向量', primary); self.assertIn('vector', tags)
        for qid in ('HKDSE-2023-M2-Q01', 'HKDSE-2025-M2-Q01'):
            self.assertIn(qid, indexes['references'])
        self.assertEqual(_fingerprint(BASELINE.parent), before)

    def test_reserved_uri_and_images_exact(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/'資料 #% space'; root.mkdir()
            target = root/BASELINE.name
            shutil.copyfile(BASELINE, target)
            shutil.copyfile(BASELINE.parent/'manifest.json', root/'manifest.json')
            indexes, _, _ = self.reader(target)
            self.assertEqual(indexes, self.reader(BASELINE)[0])
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), BASELINE_SHA)

    def test_missing_path_no_creation_and_identity_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'absent.sqlite3'
            with self.assertRaises(PipelineError): self.reader(path)
            self.assertFalse(path.exists())
            path.write_bytes(b'invalid database')
            with self.assertRaises(PipelineError): self.reader(path)

    def test_manifest_identity_is_required(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/BASELINE.name
            shutil.copyfile(BASELINE, path)
            (path.parent/'manifest.json').write_text('{}')
            with self.assertRaises(PipelineError): self.reader(path)

    def test_inner_metadata_view_and_selectability_checks(self):
        from joy_m2.ingest import v124_preflight as p
        # Patch only expected byte identity of isolated corrupt copies, never a historical reader.
        self.assertTrue(hasattr(p, '_BASELINE_SHA'), 'baseline constants scaffold required')
        for sql in ["UPDATE release_metadata_v2 SET value='wrong' WHERE key='schema_version'",
                    'DROP VIEW formal_complete_questions_v123']:
            with self.subTest(sql=sql), tempfile.TemporaryDirectory() as folder:
                path = Path(folder)/BASELINE.name
                shutil.copyfile(BASELINE, path)
                shutil.copyfile(BASELINE.parent/'manifest.json', path.parent/'manifest.json')
                with sqlite3.connect(path) as con: con.execute(sql)
                with mock.patch.object(p, '_BASELINE_SHA', hashlib.sha256(path.read_bytes()).hexdigest()), \
                     mock.patch.object(p, '_BASELINE_SIZE', path.stat().st_size):
                    with self.assertRaises(PipelineError): self.reader(path)

class V124GenesisPreflightTests(unittest.TestCase):
    def test_oxford_promoted_rows_participate_without_publisher_relabeling(self):
        with sqlite3.connect(BASELINE.resolve().as_uri() + '?mode=ro&immutable=1', uri=True) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute('SELECT * FROM formal_complete_questions_v123 WHERE batch_id=?',
                ('JOY-M2-STG-MOCK-2025-26-C-SET1-20260903',)).fetchall()
        self.assertEqual(len(rows), 13)
        row = dict(rows[0])
        manifest_path = self.package / 'import_manifest.json'
        manifest = json.loads(manifest_path.read_text())
        for image in manifest['image_files']:
            (self.package / image['relative_path']).unlink()
        manifest['image_files'] = []
        manifest_path.write_text(json.dumps(manifest))
        _rewrite_record(self.package, {**{k: row[k] for k in (
            'source_id', 'source_question_number', 'source_section',
            'source_fragment_hash', 'question_text_original')}, 'image_paths': [], 'image_roles': []})
        result = self.preflight()
        self.assertEqual((result.report.before_count, result.report.duplicate_count), (677, 1))

    def formal_record(self, year=2019):
        with sqlite3.connect(BASELINE.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as con:
            con.row_factory = sqlite3.Row
            row = con.execute("SELECT * FROM formal_complete_questions_v123 WHERE question_id=?",
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
        for year in (2019, 2020, 2021, 2022, 2023, 2025):
            with self.subTest(year=year):
                self.package = _make_package(self.root / str(year))
                self.matching_package(year)
                result = self.preflight()
                self.assertEqual((result.report.before_count, result.report.duplicate_count), (677, 1))
        self.package = original

    def test_historical_image_identity_is_indexed_without_restage(self):
        self.preflight()
        from joy_m2.ingest import v124_preflight as m
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
        self.assertEqual(_request(self.package).manifest.target_release_version, "V1.24")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def invoke(self, request):
        from joy_m2.ingest.v124_preflight import preflight_v124_import
        try:
            return preflight_v124_import(request, self.config)
        except NotImplementedError:
            self.fail("V1.24 genesis preflight behavior missing")

    def preflight(self, package: Path | None = None):
        from joy_m2.ingest.v124_preflight import preflight_v124_import

        try:
            return preflight_v124_import(_request(package or self.package), self.config)
        except NotImplementedError:
            self.fail('V1.24 genesis preflight behavior missing')

    def test_complete_677_baseline_and_genesis(self):
        result = self.preflight()
        self.assertEqual(result.report.status, "READY FOR USER IMPORT APPROVAL")
        self.assertEqual(result.report.parent_candidate_digest, GENESIS)
        self.assertEqual(result.report.parent_batch_count, 0)
        self.assertEqual(result.report.before_count, 677)
        self.assertEqual(result.report.detected_count, 1)
        self.assertEqual(result.report.new_candidate_count, 1)
        self.assertEqual(result.report.duplicate_count, 0)
        self.assertEqual(result.report.rejected_count, 0)
        self.assertEqual(result.report.projected_after_count, 678)
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
            V124PreflightRequest(
                load_v124_import_manifest(self.package / "import_manifest.json"),
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

    def test_exact_duplicate_against_formal_v123_is_blocking(self):
        with sqlite3.connect(f'{BASELINE.as_uri()}?mode=ro', uri=True) as connection:
            row = connection.execute(
                "SELECT question_text_original FROM formal_complete_questions_v123 "
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
            "baseline_question_count": 677,
            "baseline_release_digest": BASELINE_RELEASE_DIGEST,
            "baseline_release_version": "V1.23", "candidate_count": 0,
            "schema": "task14-v124-genesis-v1", "target_release_version": "V1.24",
        }
        digest = hashlib.sha256((json.dumps(payload, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False) + "\n").encode()).hexdigest()
        self.assertEqual(digest, GENESIS)
        self.assertIsNone(_request(self.package).parent_candidate)
        self.assertEqual(self.preflight().report.parent_candidate_digest, digest)

    def test_all_677_rows_indexed_once_including_2019_2022(self):
        with sqlite3.connect(f"{BASELINE.as_uri()}?mode=ro", uri=True) as con:
            row = con.execute("SELECT source_id,source_question_number,source_section,"
                "source_fragment_hash,question_text_original FROM formal_complete_questions_v123 "
                "WHERE formal_order > 591 ORDER BY formal_order LIMIT 1").fetchone()
        _rewrite_record(self.package, dict(zip(("source_id","source_question_number",
            "source_section","source_fragment_hash","question_text_original"), row),
            image_paths=[], image_roles=[]))
        result = self.preflight()
        self.assertEqual((result.report.before_count, result.report.duplicate_count,
            result.report.new_candidate_count, result.report.rejected_count), (677,1,0,0))
        from joy_m2.ingest import v124_preflight as m
        indexes, _, _ = m._formal_indexes(BASELINE)
        self.assertEqual(len(indexes["references"]), 677)

    def test_deep_schema_view_count_gates_not_masked_by_outer_hash(self):
        self.preflight()  # valid control; no missing prerequisite counted as deeper RED
        from joy_m2.ingest import v124_preflight as m
        shutil.copyfile(BASELINE.parent / "manifest.json", self.root / "manifest.json")
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
                        sql = con.execute("SELECT sql FROM sqlite_master WHERE name='formal_complete_questions_v123'").fetchone()[0]
                        columns = [row[1] for row in con.execute("PRAGMA table_info(formal_complete_questions_v123)")]
                        con.execute("DROP VIEW formal_complete_questions_v123")
                        if mutation == "count":
                            import re
                            query = re.split(r"\bAS\b", sql, maxsplit=1, flags=re.IGNORECASE)[1]
                            con.execute("CREATE VIEW formal_complete_questions_v123 AS SELECT * FROM (" + query + ") WHERE formal_order < 677")
                        elif mutation in ("duplicate_id", "selectable", "status"):
                            import re
                            query = re.split(r"\bAS\b", sql, maxsplit=1, flags=re.IGNORECASE)[1]
                            altered = {"duplicate_id": ("question_id", "'repeated-id'"),
                                       "selectable": ("selectable", "0"), "status": ("record_status", "'candidate'")}
                            field, value = altered[mutation]
                            projection = ",".join(value + ' AS "' + col + '"' if col == field else '"' + col + '"' for col in columns)
                            con.execute("CREATE VIEW formal_complete_questions_v123 AS SELECT " + projection + " FROM (" + query + ")")
                data = path.read_bytes()
                with mock.patch.object(m, "_BASELINE_SIZE", len(data)), mock.patch.object(m, "_BASELINE_SHA", hashlib.sha256(data).hexdigest()):
                    if mutation == "control":
                        self.assertEqual(len(m._formal_indexes(path)[0]["references"]), 677)
                    else:
                        with self.assertRaises(PipelineError):
                            m._formal_indexes(path)

    def test_file_integrity_after_loading_is_structured_blocker(self):
        request = _request(self.package)
        path = self.package / request.manifest.image_files[0].relative_path
        path.write_bytes(b"changed bytes")
        from joy_m2.ingest.v124_preflight import preflight_v124_import
        try:
            result = preflight_v124_import(request, self.config)
        except NotImplementedError:
            self.fail("V1.24 file-integrity preflight missing")
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
        from joy_m2.ingest.v124_preflight import preflight_v124_import
        copy = self.root / "baseline # 副本"
        copy.mkdir()
        database = copy / BASELINE.name
        shutil.copyfile(BASELINE, database)
        manifest = copy / "manifest.json"
        shutil.copyfile(BASELINE.parent / "manifest.json", manifest)
        request = replace(_request(self.package),
            baseline_database=ArtifactRef(database, BASELINE_SHA, BASELINE_SIZE, "sqlite"))
        self.assertEqual(self.invoke(request).report.before_count, 677)
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


from joy_m2.ingest.v124_models import V124CandidateBuildRequest, V124CandidateVerificationRequest
from joy_m2.ingest.v124_preflight import preflight_v124_import
from tests.integration.test_v120_preflight import _rename_declared_image
_tree = _fingerprint

class V124ParentPreflightTests(unittest.TestCase):

    def test_parent_taxonomy_participates_and_ledger_is_exact(self):
        from unittest.mock import patch
        import joy_m2.ingest.v124_preflight as preflight
        a, artifacts, parent, package = self.parent_and_b()
        accepted = a.preflight_result.candidates[0]
        _rewrite_record(package, {"primary_type": accepted.primary_type, "tags": list(accepted.tags)})
        original = preflight._formal_indexes
        with patch.object(preflight, "_formal_indexes",
                          side_effect=lambda path: (original(path)[0], frozenset(), frozenset())):
            result = self.preflight_parent(package, parent)
        self.assertEqual(result.report.status, "READY FOR USER IMPORT APPROVAL")
        self.assertEqual(result.effective_state.batch_ledger, artifacts.state.batch_ledger)
        self.assertEqual(result.effective_state.candidate_count, 1)

    def test_retained_formal_ids_still_block_with_parent(self):
        _, _, parent, package = self.parent_and_b()
        _rewrite_record(package, {"proposed_question_id": "HKDSE-2022-M2-Q01"})
        result = self.preflight_parent(package, parent)
        self.assertEqual(result.report.rejected_count, 1)
        self.assertIn("collision_candidate_id", {issue.code for issue in result.issues})

    def test_parent_missing_closure_and_wrong_version_are_context_failures(self):
        _, _, parent, package = self.parent_and_b()
        self.preflight_parent(package, parent)  # Successful prerequisite, not setup failure.
        path = parent.candidate_dir / "candidate_manifest.json"
        original = path.read_bytes()
        for label, update in (("version", {"release_version": "V1.23"}),
                              ("genesis-reset", {"candidate_digest": GENESIS}),
                              ("count", {"counts": {}})):
            with self.subTest(label=label):
                payload = json.loads(original)
                payload.update(update)
                path.write_text(json.dumps(payload))
                before = _tree(parent.candidate_dir)
                with self.assertRaises(PipelineError):
                    self.preflight_parent(package, parent)
                self.assertEqual(_tree(parent.candidate_dir), before)
                path.write_bytes(original)
        sums = parent.candidate_dir / "SHA256SUMS"
        sums.unlink()
        before = _tree(parent.candidate_dir)
        with self.assertRaises(PipelineError):
            self.preflight_parent(package, parent)
        self.assertEqual(_tree(parent.candidate_dir), before)

    def test_parent_request_mismatch_and_stale_supplied_authority_rejected(self):
        from dataclasses import replace
        from tests.integration.test_v124_candidate import _approved
        _, _, parent, package = self.parent_and_b()
        self.preflight_parent(package, parent)
        before = _tree(parent.candidate_dir)
        other = _approved(package, self.config)
        wrong = replace(parent, approved_batches=(other,))
        with self.assertRaises(PipelineError):
            self.preflight_parent(package, wrong)
        self.assertEqual(_tree(parent.candidate_dir), before)

    def test_parent_changes_during_indexing_are_rejected(self):
        from unittest.mock import patch
        from joy_m2.models import VerificationReport
        import joy_m2.ingest.v124_preflight as preflight
        _, _, parent, package = self.parent_and_b()
        self.preflight_parent(package, parent)
        real = preflight.verify_v124_candidate
        good = real(parent, self.config)
        before = _tree(parent.candidate_dir)
        with patch.object(preflight, "verify_v124_candidate",
                          side_effect=(good, VerificationReport("FAIL", ()))):
            with self.assertRaises(PipelineError):
                self.preflight_parent(package, parent)
        self.assertEqual(_tree(parent.candidate_dir), before)

    def test_equivalent_verified_parent_roots_produce_identical_preflight(self):
        from joy_m2.ingest.v124_writer import build_v124_candidate
        from tests.integration.test_v124_candidate import _make_named_package
        a, _, parent, package = self.parent_and_b()
        result = self.preflight_parent(package, parent)
        twin = self.root / "parent-twin"
        build_v124_candidate(V124CandidateBuildRequest((a,), twin, _contract()), self.config)
        other_package = _make_named_package(self.root / "independent", "b")
        result2 = self.preflight_parent(other_package,
            V124CandidateVerificationRequest(twin, (a,), _contract()))
        self.assertEqual(result, result2)
    def setUp(self):
        from tests.integration.test_v124_candidate import V124FirstWriterTests
        V124FirstWriterTests.setUp(self)

    def tearDown(self):
        self.temporary.cleanup()

    def build(self):
        from tests.integration.test_v124_candidate import V124FirstWriterTests
        return V124FirstWriterTests.build(self)

    def _invoke(self, fn, *args):
        return fn(*args)

    def parent_and_b(self):
        from tests.integration.test_v124_candidate import _make_named_package
        from joy_m2.ingest.v124_models import V124CandidateVerificationRequest
        from joy_m2.ingest.v124_verification import verify_v124_candidate
        approved, artifacts = self.build()
        parent = V124CandidateVerificationRequest(artifacts.database.path.parent, (approved,), _contract())
        self.assertEqual(verify_v124_candidate(parent,self.config).status,"PASS")
        self.assertEqual(artifacts.state.projected_question_count,678)
        package = _make_named_package(self.root,"b")
        return approved, artifacts, parent, package

    def preflight_parent(self,package,parent):
        from dataclasses import replace
        try:
            return preflight_v124_import(replace(_request(package),parent_candidate=parent), self.config)
        except NotImplementedError:
            self.fail("verified first-generation prerequisite passed; parent preflight missing")

    def test_verified_parent_binding_counts_and_preservation(self):
        _, artifacts, parent, package = self.parent_and_b()
        before=_tree(parent.candidate_dir)
        result=self.preflight_parent(package,parent)
        self.assertEqual(result.report.status,"READY FOR USER IMPORT APPROVAL")
        self.assertEqual(result.report.parent_candidate_digest,artifacts.state.candidate_digest)
        self.assertNotEqual(result.report.parent_candidate_digest,GENESIS)
        self.assertEqual((result.report.parent_batch_count,result.report.before_count,
            result.report.new_candidate_count,result.report.projected_after_count),(1,678,1,679))
        self.assertEqual(_tree(parent.candidate_dir),before)


    def test_duplicate_and_collision_against_verified_parent(self):
        approved, artifacts, parent, package=self.parent_and_b()
        first=approved.preflight_result.candidates[0]
        _rename_declared_image(package,first.image_paths[0])
        _rewrite_record(package,{"proposed_question_id":first.proposed_question_id,
            "source_id":first.source_id,"source_question_number":first.source_question_number,
            "source_section":first.source_section,"source_fragment_hash":first.source_fragment_hash,
            "question_text_original":first.question_text_original,
            "image_paths":list(first.image_paths),"image_roles":list(first.image_roles)})
        before=_tree(parent.candidate_dir)
        result=self.preflight_parent(package,parent)
        self.assertEqual((result.report.duplicate_count,result.report.new_candidate_count),(1,0))
        self.assertIn("duplicate_exact",{i.code for i in result.issues})
        _rewrite_record(package,{"question_text_original":"Different content retaining the same candidate ID"})
        result=self.preflight_parent(package,parent)
        self.assertEqual(result.report.rejected_count,1)
        self.assertIn("collision_candidate_id",{i.code for i in result.issues})
        self.assertEqual(_tree(parent.candidate_dir),before)

    def test_corrupt_verified_parent_cannot_be_used(self):
        _, _, parent, package=self.parent_and_b()
        manifest=parent.candidate_dir/"candidate_manifest.json"
        payload=json.loads(manifest.read_text())
        payload["candidate_digest"]="0"*64
        manifest.write_text(json.dumps(payload))
        before=_tree(parent.candidate_dir)
        with self.assertRaises(PipelineError):
            self.preflight_parent(package,parent)
        self.assertEqual(_tree(parent.candidate_dir),before)
