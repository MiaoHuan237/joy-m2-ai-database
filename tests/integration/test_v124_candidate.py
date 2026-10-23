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
from joy_m2.errors import (
    ImportApprovalError,
    PipelineError,
    InputFormatError,
    InputMissingError,
    OutputConflictError,
)
from joy_m2.ingest.v124_manifest import load_v124_import_manifest
from joy_m2.ingest.v124_models import (
    V124ApprovedBatch,
    V124CandidateBuildRequest,
    V124CandidateVerificationRequest,
    V124ImportApproval,
    V124PreflightRequest,
)
from joy_m2.ingest.v124_preflight import preflight_v124_import
from joy_m2.models import ArtifactRef
from tests.integration.test_v124_preflight import (
    BASELINE,
    BASELINE_SHA,
    BASELINE_SIZE,
    FIXTURE,
    _contract,
    _make_package,
    _request,
)
from tests.integration.test_v120_preflight import _rename_declared_image, _rewrite_record


GENESIS = "797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a"


def _make_named_package(parent: Path, name: str) -> Path:
    source = FIXTURE.parent / f"v120-batch-{name.lower()}"
    root = parent / f"package-{name.lower()}"
    shutil.copytree(source, root)
    manifest_path = root / "import_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["schema_version"] = "task14-v124-import-manifest-v1"
    payload["target_release_version"] = "V1.24"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return root


def _approved(package: Path, config: PipelineConfig, parent=None) -> V124ApprovedBatch:
    if parent is None:
        request = _request(package)
    else:
        request = V124PreflightRequest(
            load_v124_import_manifest(package / "import_manifest.json"),
            package,
            ArtifactRef(BASELINE, BASELINE_SHA, BASELINE_SIZE, "sqlite"),
            parent,
            _contract(),
        )
    result = preflight_v124_import(request, config)
    report = result.report
    assert report.status == "READY FOR USER IMPORT APPROVAL" and not report.blocking_errors
    assert report.batch_id in {"TASK10-A", "TASK10-B", "TASK10-C"}, report.batch_id
    assert report.parent_candidate_digest == (GENESIS if parent is None else json.loads((parent.candidate_dir / "candidate_manifest.json").read_text())["candidate_digest"])
    approval = V124ImportApproval(
        report.batch_id,
        report.preflight_sha256,
        "V1.24",
        report.parent_candidate_digest,
        f"USER APPROVED IMPORT BATCH {report.batch_id} {report.preflight_sha256} "
        f"V1.24 PARENT {report.parent_candidate_digest}",
    )
    return V124ApprovedBatch(result, package, approval)


def _tree(root: Path) -> tuple[tuple[str, str, int], ...]:
    return tuple(
        (
            path.relative_to(root).as_posix(),
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_size,
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )



from dataclasses import asdict, fields, replace
from unittest import mock

# Test-owned literal DDL pinned to Design section 6; no runtime production DDL import.
ORACLE_SQL = (
    """CREATE TABLE task14_v124_batch_ledger_v1 (
    batch_ordinal INTEGER PRIMARY KEY CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL UNIQUE CHECK(length(batch_id) BETWEEN 1 AND 128),
    target_release_version TEXT NOT NULL CHECK(target_release_version = 'V1.24'),
    candidate_database_schema TEXT NOT NULL
        CHECK(candidate_database_schema = 'task14-v124-candidate-v1'),
    parent_candidate_digest TEXT NOT NULL
        CHECK(length(parent_candidate_digest) = 64
              AND parent_candidate_digest NOT GLOB '*[^0-9a-f]*'),
    preflight_sha256 TEXT NOT NULL UNIQUE
        CHECK(length(preflight_sha256) = 64
              AND preflight_sha256 NOT GLOB '*[^0-9a-f]*'),
    manifest_sha256 TEXT NOT NULL
        CHECK(length(manifest_sha256) = 64
              AND manifest_sha256 NOT GLOB '*[^0-9a-f]*'),
    approval_statement TEXT NOT NULL
        CHECK(approval_statement =
              'USER APPROVED IMPORT BATCH ' || batch_id || ' ' ||
              preflight_sha256 || ' V1.24 PARENT ' ||
              parent_candidate_digest),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version = 'V1.23'),
    baseline_database_sha256 TEXT NOT NULL
        CHECK(baseline_database_sha256 =
              '28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd'),
    baseline_release_digest TEXT NOT NULL
        CHECK(baseline_release_digest =
              '84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count = 677),
    batch_candidate_count INTEGER NOT NULL CHECK(batch_candidate_count >= 0),
    cumulative_candidate_count INTEGER NOT NULL
        CHECK(cumulative_candidate_count >= batch_candidate_count),
    projected_question_count INTEGER NOT NULL
        CHECK(projected_question_count = 677 + cumulative_candidate_count),
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    UNIQUE(batch_ordinal, batch_id)
)""",
    """CREATE TABLE task14_v124_candidates_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    batch_candidate_order INTEGER NOT NULL CHECK(batch_candidate_order >= 0),
    aggregate_order INTEGER NOT NULL CHECK(aggregate_order >= 678),
    proposed_question_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_question_number TEXT NOT NULL,
    source_section TEXT NOT NULL,
    source_fragment_hash TEXT NOT NULL,
    normalized_text_sha256 TEXT NOT NULL,
    question_text_original TEXT NOT NULL,
    question_text_zh TEXT NOT NULL,
    translation_status TEXT NOT NULL
        CHECK(translation_status IN ('source_present','ai_proposed','verified','missing')),
    translation_evidence TEXT,
    solution_original TEXT NOT NULL,
    solution_verified TEXT NOT NULL,
    answer_status TEXT NOT NULL
        CHECK(answer_status IN ('source_provided','ai_solved_verified','missing_from_source')),
    explanation_text TEXT NOT NULL,
    explanation_status TEXT NOT NULL
        CHECK(explanation_status IN ('source_present','ai_proposed','verified','missing')),
    explanation_evidence TEXT,
    image_paths_json TEXT NOT NULL,
    image_sha256s_json TEXT NOT NULL,
    image_roles_json TEXT NOT NULL,
    primary_type TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    tag_status TEXT NOT NULL CHECK(tag_status IN ('source_provided','proposed','missing')),
    difficulty_level INTEGER CHECK(difficulty_level BETWEEN 1 AND 5
                                   OR difficulty_level IS NULL),
    difficulty_status TEXT NOT NULL
        CHECK(difficulty_status IN ('source_provided','proposed','missing')),
    enrichment_status TEXT NOT NULL
        CHECK(enrichment_status IN ('complete','incomplete')),
    candidate_image_paths_json TEXT NOT NULL,
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    selectable INTEGER NOT NULL CHECK(selectable = 0),
    PRIMARY KEY(batch_id, proposed_question_id),
    UNIQUE(proposed_question_id),
    UNIQUE(aggregate_order),
    UNIQUE(batch_ordinal, batch_candidate_order),
    UNIQUE(batch_ordinal, batch_id, proposed_question_id),
    FOREIGN KEY(batch_ordinal, batch_id)
        REFERENCES task14_v124_batch_ledger_v1(batch_ordinal, batch_id)
)""",
    """CREATE TABLE task14_v124_images_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    proposed_question_id TEXT NOT NULL,
    image_order INTEGER NOT NULL CHECK(image_order >= 0),
    source_relative_path TEXT NOT NULL,
    candidate_relative_path TEXT NOT NULL,
    sha256 TEXT NOT NULL
        CHECK(length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9a-f]*'),
    size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
    kind TEXT NOT NULL CHECK(kind = 'image'),
    role TEXT NOT NULL,
    PRIMARY KEY(batch_id, proposed_question_id, image_order),
    FOREIGN KEY(batch_ordinal, batch_id, proposed_question_id)
        REFERENCES task14_v124_candidates_v1(
            batch_ordinal, batch_id, proposed_question_id
        )
)""",
    """CREATE TABLE task14_v124_taxonomy_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    taxonomy_kind TEXT NOT NULL CHECK(taxonomy_kind IN ('primary_type','tag')),
    value TEXT NOT NULL,
    sort_order INTEGER NOT NULL CHECK(sort_order >= 1),
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    PRIMARY KEY(batch_ordinal, batch_id, taxonomy_kind, value),
    UNIQUE(batch_ordinal, batch_id, taxonomy_kind, sort_order),
    FOREIGN KEY(batch_ordinal, batch_id)
        REFERENCES task14_v124_batch_ledger_v1(batch_ordinal, batch_id)
)""",
    """CREATE VIEW task14_candidate_questions_v124 AS
SELECT f.*
FROM formal_complete_questions_v123 AS f
UNION ALL
SELECT
    c.aggregate_order AS formal_order,
    c.proposed_question_id AS question_id,
    'task14_v124_candidate' AS authority_kind,
    c.batch_id AS batch_id,
    c.batch_candidate_order AS candidate_order,
    c.source_id,
    c.source_question_number,
    c.source_section,
    c.source_fragment_hash,
    c.normalized_text_sha256,
    c.question_text_original,
    c.question_text_zh,
    CAST(NULL AS TEXT) AS question_text_zh_reviewed,
    c.translation_status,
    c.translation_evidence,
    c.solution_original,
    c.solution_verified,
    c.answer_status,
    c.explanation_text,
    c.explanation_status,
    c.explanation_evidence,
    c.image_paths_json AS source_image_paths_json,
    c.image_sha256s_json AS source_image_sha256s_json,
    c.image_roles_json AS source_image_roles_json,
    c.primary_type,
    c.tags_json,
    c.tag_status,
    c.difficulty_level,
    c.difficulty_status,
    c.enrichment_status,
    c.candidate_image_paths_json AS formal_image_paths_json,
    c.record_status,
    c.selectable
FROM task14_v124_candidates_v1 AS c
ORDER BY formal_order""",
)

CHECK_NAMES = (
    "candidate_directory", "candidate_contract", "baseline_authority",
    "batch_authority_artifacts", "parent_chain", "approval_binding",
    "preflight_reconstruction", "filesystem_closure", "sha256sums_closure",
    "artifact_references", "rollback_contract", "image_projection",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "v123_preservation", "batch_ledger",
    "candidate_projection", "effective_collision_closure", "count_closure",
    "candidate_digest", "deterministic_identity", "formal_boundary",
)


def _json(value, lf=True):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + ("\n" if lf else "")).encode()


def _hash(value):
    return hashlib.sha256(value).hexdigest()


def _independent_candidate(root, approved_batches, contract):
    """Test-owned full artifact oracle. No production builder/DDL/projection helper."""
    assert len(approved_batches) == 1  # First-generation oracle, not a parallel engine.
    batch, = approved_batches
    assert batch.approval.batch_id in {"TASK10-A", "TASK10-B", "TASK10-C"}
    result = batch.preflight_result
    assert result.report.status == "READY FOR USER IMPORT APPROVAL"
    baseline = {
        "release_version": "V1.23", "question_count": 677,
        "database_schema": "task13-v123-formal-v1",
        "sqlite": {"sha256": contract.baseline_database_sha256,
                   "size_bytes": contract.baseline_database_size_bytes, "kind": "sqlite"},
        "manifest": {"sha256": contract.baseline_manifest_sha256,
                     "size_bytes": contract.baseline_manifest_size_bytes, "kind": "manifest"},
        "release_digest": contract.baseline_release_digest,
    }
    root.mkdir(parents=True)
    database = root / contract.database_filename
    shutil.copyfile(BASELINE, database)
    records = [asdict(c) for c in result.candidates]
    approval = asdict(batch.approval)
    count = len(records)
    ledger = [{
        "ordinal": 1, "batch_id": approval["batch_id"],
        "parent_candidate_digest": GENESIS, "preflight_sha256": approval["preflight_sha256"],
        "manifest_sha256": result.report.manifest_sha256, "approval": approval,
        "batch_candidate_count": count, "cumulative_candidate_count": count,
        "projected_question_count": 677 + count,
    }]
    counts = {"baseline_question_count": 677, "batch_count": 1,
              "new_candidate_count": count, "projected_question_count": 677 + count}
    image_files = {f.relative_path: f for f in result.manifest.image_files}
    projections, images, physical, image_evidence = [], [], {}, []
    for order, record in enumerate(records):
        destinations = []
        for image_order, (source, digest, role) in enumerate(zip(
                record["image_paths"], record["image_sha256s"], record["image_roles"], strict=True)):
            evidence = image_files[source]
            ext = Path(source).suffix.lower()
            if ext == ".jpeg":
                ext = ".jpg"
            assert ext in {".jpg", ".svg", ".png"}
            dest = f"images/sha256/{digest[:2]}/{digest}{ext}"
            data = (batch.package_root / source).read_bytes()
            assert _hash(data) == digest and len(data) == evidence.size_bytes
            physical[dest] = data
            destinations.append(dest)
            images.append({
                "batch_ordinal": 1, "batch_id": approval["batch_id"],
                "proposed_question_id": record["proposed_question_id"], "image_order": image_order,
                "source_relative_path": source, "candidate_relative_path": dest,
                "sha256": digest, "size_bytes": len(data), "kind": "image", "role": role,
            })
            image_evidence.append({
                "proposed_question_id": record["proposed_question_id"], "relative_path": source,
                "sha256": digest, "size_bytes": len(data), "kind": "image", "role": role,
            })
        projections.append({
            "aggregate_order": 678 + order, "batch_ordinal": 1, "batch_id": approval["batch_id"],
            "batch_candidate_order": order, "record": record, "candidate_image_paths": destinations,
        })
    images.sort(key=lambda i: (i["candidate_relative_path"], i["batch_ordinal"],
                              i["batch_id"], i["proposed_question_id"], i["image_order"]))
    identity = {
        "schema": "task14-v124-candidate-identity-v1", "baseline": baseline,
        "target_release_version": "V1.24", "batch_ledger": ledger,
        "candidate_projection": projections, "image_projection": images, "counts": counts,
    }
    digest = _hash(_json(identity))
    # Explicit columns/projections; do not ask the implementation for expected rows.
    with sqlite3.connect(database) as con:
        con.execute("PRAGMA foreign_keys=ON")
        for sql in ORACLE_SQL:
            con.execute(sql)
        row = (1, approval["batch_id"], "V1.24", "task14-v124-candidate-v1", GENESIS,
               approval["preflight_sha256"], result.report.manifest_sha256, approval["statement"],
               "V1.23", contract.baseline_database_sha256, contract.baseline_release_digest,
               677, count, count, 677 + count, "candidate")
        con.execute("INSERT INTO task14_v124_batch_ledger_v1 VALUES (" + ",".join("?" for _ in row) + ")", row)
        names = (
            "proposed_question_id", "source_id", "source_question_number", "source_section",
            "source_fragment_hash", "normalized_text_sha256", "question_text_original",
            "question_text_zh", "translation_status", "translation_evidence", "solution_original",
            "solution_verified", "answer_status", "explanation_text", "explanation_status",
            "explanation_evidence", "image_paths", "image_sha256s", "image_roles", "primary_type",
            "tags", "tag_status", "difficulty_level", "difficulty_status", "enrichment_status",
        )
        for projection in projections:
            record = projection["record"]
            raw = [(_json(record[name], False).decode() if name in {
                "image_paths", "image_sha256s", "image_roles", "tags"} else record[name]) for name in names]
            row = (1, approval["batch_id"], projection["batch_candidate_order"],
                   projection["aggregate_order"], *raw,
                   _json(projection["candidate_image_paths"], False).decode(), "candidate", 0)
            con.execute("INSERT INTO task14_v124_candidates_v1 VALUES (" + ",".join("?" for _ in row) + ")", row)
        for image in images:
            con.execute("INSERT INTO task14_v124_images_v1 VALUES (?,?,?,?,?,?,?,?,?,?)", tuple(
                image[name] for name in ("batch_ordinal", "batch_id", "proposed_question_id",
                "image_order", "source_relative_path", "candidate_relative_path", "sha256",
                "size_bytes", "kind", "role")))
        for kind, values in (
            ("primary_type", sorted({r["primary_type"] for r in records})),
            ("tag", sorted({t for r in records for t in r["tags"]})),
        ):
            for order, value in enumerate(values, 1):
                con.execute("INSERT INTO task14_v124_taxonomy_v1 VALUES (?,?,?,?,?,?)",
                            (1, approval["batch_id"], kind, value, order, "candidate"))
        con.execute("PRAGMA user_version=124")
        assert con.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        assert con.execute("PRAGMA foreign_key_check").fetchall() == []
        assert con.execute("SELECT COUNT(*) FROM formal_complete_questions_v123").fetchone() == (677,)
        assert con.execute("SELECT COUNT(*) FROM task14_candidate_questions_v124").fetchone() == (677 + count,)
        assert con.execute("SELECT aggregate_order,record_status,selectable FROM task14_v124_candidates_v1 ORDER BY aggregate_order").fetchall() == [
            (678 + n, "candidate", 0) for n in range(count)]
    manifest = asdict(result.manifest)
    groups = ("candidate_records", "source_files", "answer_files", "image_files",
              "teacher_notes_files", "common_errors_files")
    policies = ("schema_version", "project", "module", "chapter", "language_policy",
                "split_policy", "difficulty_policy", "tag_policy", "answer_policy", "explanation_policy")
    report = asdict(result.report)
    report.pop("preflight_sha256")
    payload = {
        "schema": "task14-v124-preflight-v1", "batch_id": approval["batch_id"],
        "target_release_version": "V1.24", "baseline": baseline,
        "parent_state": {"candidate_digest": GENESIS, "batch_count": 0,
                         "candidate_count": 0, "projected_question_count": 677},
        "manifest_policies": {k: manifest[k] for k in policies},
        "candidate_record_order": [f["relative_path"] for f in manifest["candidate_records"]],
        "file_evidence": sorted([f for g in groups for f in manifest[g]], key=lambda f: f["relative_path"]),
        "candidates": records, "issues": [],
        "duplicate_classifications": [{"candidate_id": r["proposed_question_id"],
            "classification": "new_candidate", "reference_question_id": None, "evidence": None} for r in records],
        "image_evidence": image_evidence, "report": report,
    }
    assert _hash(_json(payload)) == approval["preflight_sha256"], "oracle preflight projection invalid"
    authority_root = f"authority/batches/000001/{approval['batch_id']}"
    files = {
        f"{authority_root}/approval.json": _json({"schema_version": "task14-v124-import-approval-v1", **approval}),
        f"{authority_root}/preflight.json": _json({"preflight_sha256": approval["preflight_sha256"], "payload": payload}),
        **physical,
    }
    all_paths = sorted([contract.database_filename, "candidate_manifest.json", "SHA256SUMS", "rollback.json", *files])
    files["rollback.json"] = _json({
        "schema_version": "task14-v124-rollback-v1",
        "action": "delete_unpromoted_v124_candidate_tree_if_digest_matches",
        "candidate_digest": digest, "protected_baseline": baseline, "candidate_artifacts": all_paths,
    })
    for relative, data in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def ref(relative, kind):
        data = (root / relative).read_bytes()
        return {"relative_path": relative, "sha256": _hash(data), "size_bytes": len(data), "kind": kind}

    (root / "candidate_manifest.json").write_bytes(_json({
        "schema_version": "task14-v124-candidate-manifest-v1",
        "release_version": "V1.24", "release_status": "candidate",
        "release_model": "append-only-multi-batch-candidate",
        "baseline": baseline, "candidate_digest": digest, "counts": counts, "batch_ledger": ledger,
        "database": ref(contract.database_filename, "sqlite"),
        "images": [ref(p, "image") for p in sorted(physical)],
        "batch_authority_artifacts": [ref(p, "approval" if p.endswith("approval.json") else "preflight")
                                     for p in sorted(files) if p.startswith("authority/")],
        "rollback": ref("rollback.json", "rollback"),
        "verification": {"authority": "verify_v124_candidate", "check_names": list(CHECK_NAMES), "required_status": "PASS"},
    }))
    (root / "SHA256SUMS").write_text("".join(
        f"{_hash((root / p).read_bytes())}  {p}\n" for p in all_paths if p != "SHA256SUMS"), encoding="utf-8")
    return digest


class V124FirstVerifierTests(unittest.TestCase):
    def setUp(self):
        sandbox = ROOT / "data/staging"
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-v124-oracle-", dir=sandbox)
        self.root = Path(self.temp.name)
        self.config = PipelineConfig(ROOT)
        self.package = _make_package(self.root)
        self.approved = _approved(self.package, self.config)
        self.target = self.root / "candidate"
        self.digest = _independent_candidate(self.target, (self.approved,), _contract())
        self.request = V124CandidateVerificationRequest(self.target, (self.approved,), _contract())

    def tearDown(self):
        self.temp.cleanup()

    def verify(self, request=None):
        from joy_m2.ingest.v124_verification import verify_v124_candidate
        try:
            return verify_v124_candidate(request or self.request, self.config)
        except NotImplementedError:
            self.fail("independent V1.24 verifier behavior missing")

    def test_test_owned_oracle_passes_all_24_checks_and_is_read_only(self):
        before = _tree(self.target)
        report = self.verify()
        self.assertEqual(report.status, "PASS", report)
        self.assertEqual(tuple(c.name for c in report.checks), CHECK_NAMES)
        self.assertTrue(all(c.passed for c in report.checks))
        self.assertEqual(_tree(self.target), before)

    def test_schema_rows_and_metadata_preserved_in_independent_oracle(self):
        with sqlite3.connect(BASELINE.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as base:
            with sqlite3.connect((self.target / _contract().database_filename).as_uri() + "?mode=ro&immutable=1", uri=True) as candidate:
                for kind, name, table, sql in base.execute(
                    "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"):
                    self.assertEqual(candidate.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name=?", (name,)).fetchone(),
                                     (kind, name, table, sql))
                    if kind in {"table", "view"}:
                        self.assertEqual(sorted(base.execute(f'SELECT * FROM "{name}"').fetchall(), key=repr),
                                         sorted(candidate.execute(f'SELECT * FROM "{name}"').fetchall(), key=repr))
        self.assertEqual(self.verify().status, "PASS")

    def test_corrupt_layers_are_structured_failures_without_repair(self):
        self.assertEqual(self.verify().status, "PASS")  # validated control before deep mutations
        mutations = {
            "missing": ("filesystem_closure", lambda p: (p / "rollback.json").unlink()),
            "extra": ("filesystem_closure", lambda p: (p / "extra.txt").write_text("extra")),
            "sums": ("sha256sums_closure", lambda p: (p / "SHA256SUMS").write_text("bad")),
            "manifest-shape": ("candidate_contract", lambda p: (p / "candidate_manifest.json").write_text("[]")),
            "image": ("image_projection", lambda p: next((p / "images").rglob("*.svg")).write_bytes(b"bad")),
            "rollback": ("rollback_contract", lambda p: (p / "rollback.json").write_text("{}")),
            "approval": ("approval_binding", lambda p: next((p / "authority").rglob("approval.json")).write_text("{}")),
            "preflight": ("preflight_reconstruction", lambda p: next((p / "authority").rglob("preflight.json")).write_text("{}")),
        }
        for name, (check, mutate) in mutations.items():
            with self.subTest(name=name):
                target = self.root / ('mutated-' + name)
                shutil.copytree(self.target, target)
                mutate(target)
                before = _tree(target)
                report = self.verify(replace(self.request, candidate_dir=target))
                self.assertEqual(report.status, "FAIL")
                self.assertFalse(next(c.passed for c in report.checks if c.name == check))
                self.assertEqual(_tree(target), before)

    def test_sqlite_tampering_is_detected_at_specific_boundaries(self):
        self.assertEqual(self.verify().status, "PASS")
        for name, sql, check in (
            ("schema", "PRAGMA user_version=0", "sqlite_schema"),
            ("baseline", "UPDATE release_metadata_v2 SET value='wrong' WHERE key='release_version'", "v123_preservation"),
            ("ledger", "UPDATE task14_v124_batch_ledger_v1 SET batch_candidate_count=0", "batch_ledger"),
            ("candidate", "UPDATE task14_v124_candidates_v1 SET solution_original='tampered'", "candidate_projection"),
            ("image", "UPDATE task14_v124_images_v1 SET role='solution'", "candidate_projection"),
        ):
            with self.subTest(name=name):
                target = self.root / ('mutated-' + name)
                shutil.copytree(self.target, target)
                with sqlite3.connect(target / _contract().database_filename) as con:
                    con.execute(sql)
                before = _tree(target)
                report = self.verify(replace(self.request, candidate_dir=target))
                self.assertEqual(report.status, "FAIL")
                self.assertFalse(next(c.passed for c in report.checks if c.name == check))
                self.assertEqual(_tree(target), before)

    def test_digest_counts_and_artifact_references_not_trusted(self):
        self.assertEqual(self.verify().status, "PASS")
        for name in ("digest", "size", "hash", "count", "parent"):
            with self.subTest(name=name):
                target = self.root / name
                shutil.copytree(self.target, target)
                path = target / "candidate_manifest.json"
                payload = json.loads(path.read_bytes())
                if name == "digest": payload["candidate_digest"] = "0" * 64
                if name == "size": payload["database"]["size_bytes"] += 1
                if name == "hash": payload["database"]["sha256"] = "0" * 64
                if name == "count": payload["counts"]["new_candidate_count"] += 1
                if name == "parent": payload["batch_ledger"][0]["parent_candidate_digest"] = "0" * 64
                path.write_bytes(_json(payload))
                self.assertEqual(self.verify(replace(self.request, candidate_dir=target)).status, "FAIL")

    def test_changed_canonical_source_and_forged_equal_parent_rejected(self):
        self.assertEqual(self.verify().status, "PASS")
        forged = replace(self.approved.approval, parent_candidate_digest="1" * 64,
                         statement=self.approved.approval.statement.replace(GENESIS, "1" * 64))
        report = replace(self.approved.preflight_result.report, parent_candidate_digest="1" * 64)
        import copy
        batch = copy.deepcopy(self.approved)
        object.__setattr__(batch, 'approval', forged)
        object.__setattr__(batch.preflight_result, 'report', report)
        object.__setattr__(batch.preflight_result.effective_state, 'candidate_digest', '1' * 64)
        verified = self.verify(replace(self.request, approved_batches=(batch,)))
        self.assertEqual(verified.status, "FAIL")
        self.assertFalse(next(c.passed for c in verified.checks if c.name == "parent_chain"))
        source = self.package / self.approved.preflight_result.manifest.source_files[0].relative_path
        source.write_bytes(source.read_bytes() + b"\nchanged")
        self.assertEqual(self.verify().status, "FAIL")

    def test_missing_root_and_malformed_json_exception_boundaries(self):
        with self.assertRaises(InputMissingError):
            self.verify(replace(self.request, candidate_dir=self.root / "missing"))
        (self.target / "candidate_manifest.json").write_bytes(b"{")
        with self.assertRaises(InputFormatError):
            self.verify()
