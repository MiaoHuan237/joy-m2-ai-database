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
        con.execute("BEGIN IMMEDIATE")
        for sql in ORACLE_SQL[:-1]:
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
        con.execute(ORACLE_SQL[-1])
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
class V124FirstWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        sandbox = ROOT / "data/staging/task14-v124-synthetic"
        sandbox.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-", dir=sandbox)
        self.root = Path(self.temporary.name)
        self.package = _make_package(self.root)
        for folder in ("data/staging", "data/baselines", "releases"):
            (self.root / folder).mkdir(parents=True)
        self.config = PipelineConfig(ROOT)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _invoke(self, fn, *args):
        try:
            return fn(*args)
        except NotImplementedError:
            self.fail("V1.24 writer/verifier behavior missing")

    def _build(self, *args):
        from joy_m2.ingest.v124_writer import build_v124_candidate
        return self._invoke(build_v124_candidate, *args)

    def _verify(self, *args):
        from joy_m2.ingest.v124_verification import verify_v124_candidate
        return self._invoke(verify_v124_candidate, *args)

    def build(self, output: Path | None = None):
        from joy_m2.ingest.v124_writer import build_v124_candidate as _build
        build_v124_candidate = lambda *args: self._invoke(_build, *args)

        approved = _approved(self.package, self.config)
        target = output or (self.root / "data/staging/candidate")
        return approved, build_v124_candidate(
            V124CandidateBuildRequest((approved,), target, _contract()),
            self.config,
        )

    def test_first_batch_builds_verified_append_only_candidate(self):
        baseline_before = hashlib.sha256(BASELINE.read_bytes()).hexdigest()
        approved, artifacts = self.build()
        self.assertEqual(artifacts.verification_report.status, "PASS")
        self.assertEqual(artifacts.state.candidate_count, 1)
        self.assertEqual(artifacts.state.projected_question_count, 678)
        self.assertEqual(artifacts.state.batch_ledger[0].parent_candidate_digest, GENESIS)
        self.assertTrue(artifacts.database.path.is_file())
        with sqlite3.connect(artifacts.database.path) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM task14_candidate_questions_v124"
                ).fetchone()[0],
                678,
            )
        self.assertEqual(hashlib.sha256(BASELINE.read_bytes()).hexdigest(), baseline_before)
        self.assertEqual(approved.approval.parent_candidate_digest, GENESIS)

    def test_independent_verifier_passes_and_does_not_mutate(self):
        from joy_m2.ingest.v124_verification import verify_v124_candidate as _verify
        verify_v124_candidate = lambda *args: self._invoke(_verify, *args)

        approved, artifacts = self.build()
        root = artifacts.database.path.parent
        before = _tree(root)
        report = verify_v124_candidate(
            V124CandidateVerificationRequest(root, (approved,), _contract()),
            self.config,
        )
        self.assertEqual(report.status, "PASS")
        self.assertEqual(tuple(check.name for check in report.checks), CHECK_NAMES)
        self.assertTrue(all(check.passed for check in report.checks))
        self.assertEqual(_tree(root), before)

    def test_manifest_tamper_returns_structured_fail_without_repair(self):
        from joy_m2.ingest.v124_verification import verify_v124_candidate as _verify
        verify_v124_candidate = lambda *args: self._invoke(_verify, *args)

        approved, artifacts = self.build()
        root = artifacts.database.path.parent
        manifest = root / "candidate_manifest.json"
        manifest.write_bytes(manifest.read_bytes().replace(b'"candidate"', b'"tampered"', 1))
        before = _tree(root)
        report = verify_v124_candidate(
            V124CandidateVerificationRequest(root, (approved,), _contract()),
            self.config,
        )
        self.assertEqual(report.status, "FAIL")
        self.assertEqual(_tree(root), before)

    def test_missing_root_and_malformed_json_keep_exact_error_boundary(self):
        from joy_m2.ingest.v124_verification import verify_v124_candidate as _verify
        verify_v124_candidate = lambda *args: self._invoke(_verify, *args)

        approved = _approved(self.package, self.config)
        missing = self.root / "missing"
        with self.assertRaises(InputMissingError):
            verify_v124_candidate(
                V124CandidateVerificationRequest(missing, (approved,), _contract()),
                self.config,
            )

        _, artifacts = self.build()
        root = artifacts.database.path.parent
        (root / "candidate_manifest.json").write_bytes(b"{")
        with self.assertRaises(InputFormatError):
            verify_v124_candidate(
                V124CandidateVerificationRequest(root, (approved,), _contract()),
                self.config,
            )

    def test_missing_extra_and_tampered_artifacts_are_structured_failures(self):
        from joy_m2.ingest.v124_verification import verify_v124_candidate as _verify
        verify_v124_candidate = lambda *args: self._invoke(_verify, *args)

        for case in ("missing", "extra", "tampered-db"):
            with self.subTest(case=case):
                case_package = _make_package(self.root / f"source-{case}")
                approved = _approved(case_package, self.config)
                candidate_root = self.root / f"candidate-{case}"
                from joy_m2.ingest.v124_writer import build_v124_candidate as _build
                build_v124_candidate = lambda *args: self._invoke(_build, *args)

                artifacts = build_v124_candidate(
                    V124CandidateBuildRequest(
                        (approved,), candidate_root, _contract()
                    ),
                    self.config,
                )
                if case == "missing":
                    (candidate_root / "rollback.json").unlink()
                elif case == "extra":
                    (candidate_root / "rogue.txt").write_text("rogue", encoding="utf-8")
                else:
                    with artifacts.database.path.open("ab") as handle:
                        handle.write(b"tamper")
                before = _tree(candidate_root)
                report = verify_v124_candidate(
                    V124CandidateVerificationRequest(
                        candidate_root, (approved,), _contract()
                    ),
                    self.config,
                )
                self.assertEqual(report.status, "FAIL")
                self.assertEqual(_tree(candidate_root), before)

    def test_existing_output_is_not_replaced(self):
        approved, artifacts = self.build()
        before = _tree(artifacts.database.path.parent)
        from joy_m2.ingest.v124_writer import build_v124_candidate as _build
        build_v124_candidate = lambda *args: self._invoke(_build, *args)

        with self.assertRaises(OutputConflictError):
            build_v124_candidate(
                V124CandidateBuildRequest(
                    (approved,), artifacts.database.path.parent, _contract()
                ),
                self.config,
            )
        self.assertEqual(_tree(artifacts.database.path.parent), before)

    def test_writer_rejects_existing_artifact_ancestors_without_mutation(self):
        approved = _approved(self.package, self.config)
        for marker in ("candidate_manifest.json", "import_manifest.json"):
            for kind in ("file", "dangling-symlink"):
                with self.subTest(marker=marker, kind=kind):
                    protected = self.root / f"protected-{marker}-{kind}"
                    protected.mkdir()
                    path = protected / marker
                    if kind == "file":
                        path.write_text('{"release_version":"V1.23"}\n')
                    else:
                        path.symlink_to(protected / "missing-marker-target")
                    before = _tree(protected)
                    output = protected / "new-child"
                    with self.assertRaises(PipelineError):
                        self._build(V124CandidateBuildRequest(
                            (approved,), output, _contract()), self.config)
                    self.assertFalse(output.exists())
                    self.assertEqual(_tree(protected), before)
                    self.assertEqual(path.is_symlink(), kind == "dangling-symlink")

    def test_verifier_rejects_candidate_nested_in_existing_artifact_root(self):
        approved, artifacts = self.build()
        self.assertEqual(artifacts.verification_report.status, "PASS")
        for marker in ("candidate_manifest.json", "import_manifest.json"):
            with self.subTest(marker=marker):
                protected = self.root / f"verify-protected-{marker}"
                protected.mkdir()
                (protected / marker).write_text('{"release_version":"V1.23"}\n')
                nested = protected / "nested"
                shutil.copytree(artifacts.database.path.parent, nested)
                before = _tree(protected)
                report = self._verify(V124CandidateVerificationRequest(
                    nested, (approved,), _contract()), self.config)
                self.assertEqual(report.status, "FAIL")
                self.assertFalse(next(c.passed for c in report.checks
                                      if c.name == "formal_boundary"))
                self.assertEqual(_tree(protected), before)

    def test_wrong_parent_approval_is_rejected(self):
        approved = _approved(self.package, self.config)
        forged = object.__new__(V124ImportApproval)
        for name, value in approved.approval.__dict__.items():
            object.__setattr__(forged, name, value)
        object.__setattr__(forged, "parent_candidate_digest", "f" * 64)
        bad = object.__new__(V124ApprovedBatch)
        object.__setattr__(bad, "preflight_result", approved.preflight_result)
        object.__setattr__(bad, "package_root", approved.package_root)
        object.__setattr__(bad, "approval", forged)
        from joy_m2.ingest.v124_writer import build_v124_candidate as _build
        build_v124_candidate = lambda *args: self._invoke(_build, *args)

        output = self.root / "data/staging/bad-candidate"
        with self.assertRaises(ImportApprovalError):
            build_v124_candidate(
                V124CandidateBuildRequest((bad,), output, _contract()), self.config
            )
        self.assertFalse(output.exists())

    def test_equivalent_roots_build_byte_identical_candidates(self):
        first_package = self.package
        second_package = _make_package(self.root / "second-source")
        from joy_m2.ingest.v124_writer import build_v124_candidate as _build
        build_v124_candidate = lambda *args: self._invoke(_build, *args)

        first = _approved(first_package, self.config)
        second = _approved(second_package, self.config)
        first_root = self.root / "candidate-one"
        second_root = self.root / "candidate-two"
        build_v124_candidate(
            V124CandidateBuildRequest((first,), first_root, _contract()), self.config
        )
        build_v124_candidate(
            V124CandidateBuildRequest((second,), second_root, _contract()), self.config
        )
        self.assertEqual(_tree(first_root), _tree(second_root))


    def test_private_genesis_oracle_reconstructs_fixed_projection(self):
        import importlib
        self.assertIsNotNone(importlib.util.find_spec("joy_m2.ingest.v124_writer_profiles"))
        p = importlib.import_module("joy_m2.ingest.v124_writer_profiles")
        self.assertTrue(callable(getattr(p, "_genesis_digest", None)))
        self.assertEqual(p._genesis_digest(), GENESIS)
        from unittest import mock
        with mock.patch.object(p, "BASELINE_RELEASE_DIGEST", "0" * 64):
            with self.assertRaises(InputFormatError):
                p._genesis_digest()

    def test_writer_independently_calls_genesis_boundary(self):
        import joy_m2.ingest.v124_writer as writer
        self.assertTrue(callable(getattr(writer, "_genesis_digest", None)))
        from unittest import mock
        approved = _approved(self.package, self.config)
        with mock.patch.object(writer, "_genesis_digest", return_value="0" * 64) as call:
            with self.assertRaises(ImportApprovalError):
                writer.build_v124_candidate(V124CandidateBuildRequest((approved,),
                    self.root / "data/staging/wrong-genesis", _contract()), self.config)
            self.assertGreaterEqual(call.call_count, 1)

    def test_verifier_independently_calls_genesis_boundary(self):
        approved, artifacts = self.build()
        import joy_m2.ingest.v124_verification as verifier
        self.assertTrue(callable(getattr(verifier, "_genesis_digest", None)))
        from unittest import mock
        with mock.patch.object(verifier, "_genesis_digest", side_effect=[GENESIS, "0" * 64]) as call:
            result = verifier.verify_v124_candidate(V124CandidateVerificationRequest(
                artifacts.database.path.parent, (approved,), _contract()), self.config)
            self.assertEqual(result.status, "FAIL")
            self.assertFalse(next(x.passed for x in result.checks if x.name == "parent_chain"))
            self.assertEqual(call.call_count, 2)

    def test_baseline_schema_rows_metadata_remain_exactly_preserved(self):
        approved, artifacts = self.build()
        with sqlite3.connect(f"{BASELINE.as_uri()}?mode=ro", uri=True) as baseline, sqlite3.connect(artifacts.database.path) as candidate:
            rows = baseline.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY name").fetchall()
            for row in rows:
                self.assertEqual(candidate.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name=?", (row[1],)).fetchone(), row)
                if row[0] == "table":
                    quoted = '"' + row[1].replace('"','""') + '"'
                    self.assertEqual(candidate.execute("SELECT * FROM " + quoted).fetchall(),
                                     baseline.execute("SELECT * FROM " + quoted).fetchall())
            self.assertEqual(candidate.execute("PRAGMA user_version").fetchone(), (124,))
            self.assertEqual(candidate.execute("SELECT aggregate_order,record_status,selectable FROM task14_v124_candidates_v1").fetchall(), [(678,"candidate",0)])

    def test_publication_fault_cleans_only_owned_temporary_output(self):
        import joy_m2.ingest.v124_writer as writer
        self.assertTrue(hasattr(writer, "atomic_rename_no_replace"))
        from unittest import mock
        approved = _approved(self.package, self.config)
        output = self.root / "data/staging/fault"
        source = _tree(self.package)
        with mock.patch.object(writer, "atomic_rename_no_replace", side_effect=OSError("injected")):
            with self.assertRaises(PipelineError):
                writer.build_v124_candidate(V124CandidateBuildRequest((approved,), output, _contract()), self.config)
        self.assertFalse(output.exists())
        self.assertEqual(tuple(output.parent.iterdir()), ())
        self.assertEqual(_tree(self.package), source)

    def test_post_verification_source_and_private_artifact_changes_rejected(self):
        import joy_m2.ingest.v124_writer as writer
        from unittest.mock import patch
        original_verify = writer.verify_v124_candidate
        for defect in ('source', 'private'):
            package = _make_package(self.root / defect)
            approved = _approved(package, self.config)
            output = self.root/'data/staging'/defect
            def changed(request, config):
                result = original_verify(request, config)
                self.assertEqual(result.status, 'PASS')
                target = (package/approved.preflight_result.manifest.source_files[0].relative_path) if defect == 'source' else (
                    request.candidate_dir/'candidate_manifest.json')
                target.write_bytes(target.read_bytes() + b' ')
                return result
            with patch.object(writer, 'verify_v124_candidate', side_effect=changed):
                with self.assertRaises(PipelineError):
                    writer.build_v124_candidate(V124CandidateBuildRequest((approved,), output, _contract()), self.config)
            self.assertFalse(output.exists())
            self.assertEqual(tuple(output.parent.iterdir()), ())

    def test_late_destination_race_preserves_other_owner(self):
        import joy_m2.ingest.v124_writer as writer
        from unittest.mock import patch
        approved = _approved(self.package, self.config)
        output = self.root/'data/staging/race'
        rename = writer.atomic_rename_no_replace
        def racing(source, target):
            target.mkdir(); (target/'sentinel').write_bytes(b'other owner')
            return rename(source, target)
        with patch.object(writer, 'atomic_rename_no_replace', side_effect=racing):
            with self.assertRaises(OutputConflictError):
                writer.build_v124_candidate(V124CandidateBuildRequest((approved,), output, _contract()), self.config)
        self.assertEqual((output/'sentinel').read_bytes(), b'other owner')
        self.assertEqual(tuple(output.parent.iterdir()), (output,))


    def test_forged_matching_first_parent_values_rejected_by_both_boundaries(self):
        build_v124_candidate, verify_v124_candidate = self._build, self._verify
        approved, artifacts = self.build()
        root = artifacts.database.path.parent
        before = _tree(root)
        def clone(value, **changes):
            result = object.__new__(type(value))
            for k, v in vars(value).items():
                object.__setattr__(result, k, changes.get(k, v))
            return result
        projection = {"baseline_database_sha256":BASELINE_SHA,"baseline_question_count":678,
            "baseline_release_digest":_contract().baseline_release_digest,
            "baseline_release_version":"V1.23","candidate_count":0,
            "schema":"task14-v124-genesis-v1","target_release_version":"V1.24"}
        changed = hashlib.sha256((json.dumps(projection,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
        for wrong in (None,"","331192032f184a44ed383e6dacc2f06fbacb60ad94414298fcb935ff56cb5906",
            "4ff624aca875b0191fe8a617516d2919c6d700ce69c5a3b5d236adcf7ecc59f1","a"*64,changed):
            with self.subTest(parent=wrong):
                report = clone(approved.preflight_result.report,parent_candidate_digest=wrong)
                state = clone(approved.preflight_result.effective_state,candidate_digest=wrong)
                result = clone(approved.preflight_result,report=report,effective_state=state)
                approval = clone(approved.approval,parent_candidate_digest=wrong,
                    statement=f"USER APPROVED IMPORT BATCH {report.batch_id} {report.preflight_sha256} V1.24 PARENT {wrong}")
                bad = clone(approved,preflight_result=result,approval=approval)
                output = self.root / "data/staging/forged"
                with self.assertRaises(ImportApprovalError):
                    build_v124_candidate(V124CandidateBuildRequest((bad,),output,_contract()), self.config)
                verification = verify_v124_candidate(V124CandidateVerificationRequest(root,(bad,),_contract()),self.config)
                self.assertEqual(verification.status,"FAIL")
                self.assertFalse(output.exists())
                self.assertEqual(_tree(root),before)

    def test_independent_corruption_controls_are_structured_and_read_only(self):
        verify_v124_candidate = self._verify
        approved, artifacts = self.build()
        original = artifacts.database.path.parent
        cases = {
            "manifest": "deterministic_identity", "sums": "sha256sums_closure",
            "rollback": "rollback_contract", "image": "image_projection",
            "unreadable": "sqlite_readability", "schema": "sqlite_schema",
            "integrity": "sqlite_integrity",
            "foreign_key": "sqlite_foreign_keys", "ledger": "batch_ledger",
            "count": "count_closure", "digest": "candidate_digest",
            "artifact_ref": "artifact_references",
        }
        for case, expected in cases.items():
            with self.subTest(case=case):
                target = self.root / "data/staging" / case
                shutil.copytree(original,target)
                db = target / _contract().database_filename
                manifest = target / "candidate_manifest.json"
                if case in ("manifest","digest","artifact_ref"):
                    payload=json.loads(manifest.read_text())
                    if case=="manifest": payload["release_status"]="published"
                    if case=="digest": payload["candidate_digest"]="0"*64
                    if case=="artifact_ref": payload["database"]["size_bytes"]+=1
                    manifest.write_text(json.dumps(payload))
                elif case=="sums": (target/"SHA256SUMS").write_bytes(b"bad\n")
                elif case=="rollback": (target/"rollback.json").write_bytes(b"{}\n")
                elif case=="image": next((target/"images").rglob("*.svg")).write_bytes(b"bad")
                elif case=="unreadable": db.write_bytes(b"not sqlite")
                elif case=="integrity":
                    with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as check:
                        page = check.execute("SELECT rootpage FROM sqlite_master WHERE name='task14_v124_candidates_v1'").fetchone()[0]
                        size = check.execute("PRAGMA page_size").fetchone()[0]
                    content = bytearray(db.read_bytes())
                    content[(page - 1) * size] = 0  # Invalid data b-tree page type.
                    db.write_bytes(content)
                else:
                    with sqlite3.connect(db) as con:
                        con.execute("PRAGMA foreign_keys=OFF")
                        if case=="schema": con.execute("CREATE TABLE rogue(x)")
                        if case=="foreign_key": con.execute("UPDATE task14_v124_images_v1 SET batch_id='missing'")
                        if case=="ledger": con.execute("UPDATE task14_v124_batch_ledger_v1 SET manifest_sha256=?",("0"*64,))
                        if case=="count": con.execute("DELETE FROM task14_v124_candidates_v1")
                before=_tree(target)
                report=verify_v124_candidate(V124CandidateVerificationRequest(target,(approved,),_contract()),self.config)
                self.assertEqual(report.status,"FAIL")
                self.assertFalse(next(x.passed for x in report.checks if x.name==expected))
                self.assertEqual(_tree(target),before)

    def test_forged_empty_or_missing_nested_authority_rejected_without_crash(self):
        build_v124_candidate = self._build
        approved = _approved(self.package, self.config)
        def clone(value, **changes):
            result = object.__new__(type(value))
            for key, item in vars(value).items():
                object.__setattr__(result, key, changes.get(key, item))
            return result
        output = self.root / "forged-carrier"
        valid = V124CandidateBuildRequest((approved,), output, _contract())
        for batches in ((), (clone(approved, approval=None),)):
            with self.subTest(batches=len(batches)):
                forged = clone(valid, approved_batches=batches)
                try:
                    build_v124_candidate(forged, self.config)
                except PipelineError:
                    pass
                except Exception as error:
                    self.fail(f"writer leaked {type(error).__name__}: {error}")
                else:
                    self.fail("writer accepted a forged carrier")
                self.assertFalse(output.exists())

    def _forged_candidates(self, approved, candidates):
        import joy_m2.ingest.v124_verification as m
        self.assertTrue(callable(getattr(m, "_preflight_payload", None)), "verifier payload reconstruction missing")
        from dataclasses import replace
        from joy_m2.ingest.v124_verification import _preflight_payload
        from joy_m2.ingest.v124_writer_profiles import canonical_json_file_bytes
        result = replace(approved.preflight_result, candidates=candidates)
        report = replace(
            result.report,
            proposed_ids=tuple(c.proposed_question_id for c in candidates),
            level_counts=tuple(
                (level, sum(c.difficulty_level == level for c in candidates))
                for level in range(1, 6) if any(c.difficulty_level == level for c in candidates)
            ),
        )
        result = replace(result, report=report)
        intermediate = object.__new__(V124ApprovedBatch)
        for key, value in vars(approved).items():
            object.__setattr__(intermediate, key, result if key == "preflight_result" else value)
        digest = hashlib.sha256(canonical_json_file_bytes(_preflight_payload(intermediate))).hexdigest()
        result = replace(result, report=replace(report, preflight_sha256=digest))
        approval = replace(approved.approval, preflight_sha256=digest,
            statement=f"USER APPROVED IMPORT BATCH {report.batch_id} {digest} V1.24 PARENT {GENESIS}")
        return V124ApprovedBatch(result, approved.package_root, approval)

    def _forged_blocked_source(self, defect):
        from dataclasses import replace
        from types import SimpleNamespace
        from joy_m2.ingest.models import ImportAdaptation
        from joy_m2.ingest.v124_preflight import _formal_indexes
        from joy_m2.ingest.v124_verification import _preflight_payload
        from joy_m2.ingest.v124_writer_profiles import canonical_json_file_bytes
        adaptations = ()
        if defect == 'ambiguous':
            ref = _formal_indexes(BASELINE)[0]['references']['M2QD-BT-TRAIN-Q4']
            _rewrite_record(self.package, dict(source_id=ref['locator'][0],
                source_question_number=ref['locator'][1], source_section=ref['locator'][2],
                source_fragment_hash=ref['fragment']))
        else:
            _rewrite_record(self.package, dict(primary_type='REVIEW-UNCONTROLLED-TYPE',
                                              tags=['REVIEW-UNCONTROLLED-TAG']))
        result = preflight_v124_import(_request(self.package), self.config)
        expected = {'duplicate_ambiguous'} if defect == 'ambiguous' else {'unknown_primary_type', 'unknown_tag'}
        self.assertTrue(expected <= {i.code for i in result.issues})
        if defect == 'ambiguous':
            c = result.candidates[0]
            adaptations = (ImportAdaptation(c.proposed_question_id, ref['question_id'], 'adapted',
                f"matched=source_locator+source_fragment_hash;candidate_normalized_text_sha256={c.normalized_text_sha256};reference_normalized_text_sha256={ref['normalized']}",
                'stable_source_identity_matches_with_transformed_text'),)
        report = replace(result.report, status='READY FOR USER IMPORT APPROVAL',
            new_candidate_count=1, rejected_count=0, ambiguous_count=0,
            projected_after_count=678, ambiguous_splits=(), blocking_errors=(), adaptations=adaptations)
        result = replace(result, report=report, issues=())
        digest = hashlib.sha256(canonical_json_file_bytes(_preflight_payload(
            SimpleNamespace(preflight_result=result)))).hexdigest()
        result = replace(result, report=replace(report, preflight_sha256=digest))
        self.assertEqual(report.batch_id, 'TASK10-A')  # Synthetic only, never a real source approval.
        approval = V124ImportApproval('TASK10-A', digest, 'V1.24', GENESIS,
            f'USER APPROVED IMPORT BATCH TASK10-A {digest} V1.24 PARENT {GENESIS}')
        return V124ApprovedBatch(result, self.package, approval)

    def test_writer_rejects_forged_ready_with_multi_reference_identity(self):
        forged = self._forged_blocked_source('ambiguous')
        with self.assertRaises(PipelineError):
            self._build(V124CandidateBuildRequest((forged,), self.root/'bad', _contract()), self.config)

    def test_same_batch_three_records_may_share_one_identical_image(self):
        manifest_path = self.package/'import_manifest.json'
        manifest = json.loads(manifest_path.read_bytes())
        item = manifest['candidate_records'][0]
        path = self.package/item['relative_path']
        original = json.loads(path.read_bytes())[0]
        rows = []
        for n in range(3):
            row = dict(original, proposed_question_id=f'TASK10-A-SHARED-{n}',
                source_question_number=str(n + 1), source_fragment_hash=hashlib.sha256(f'shared-{n}'.encode()).hexdigest(),
                question_text_original=f'Synthetic distinct image question {n}')
            rows.append(row)
        path.write_bytes(_json(rows))
        item.update(sha256=_hash(path.read_bytes()), size_bytes=path.stat().st_size)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False) + '\n')
        approved = _approved(self.package, self.config)
        self.assertEqual(approved.preflight_result.report.new_candidate_count, 3)
        oracle = self.root/'shared-oracle'
        _independent_candidate(oracle, (approved,), _contract())
        self.assertEqual(self._verify(V124CandidateVerificationRequest(oracle, (approved,), _contract()), self.config).status, 'PASS')
        built = self._build(V124CandidateBuildRequest((approved,), self.root/'shared-built', _contract()), self.config)
        self.assertEqual(built.verification_report.status, 'PASS')
        # The next batch sees all three accepted owners, unlike the same-batch case.
        from tests.integration.test_v120_preflight import _replace_declared_image_bytes
        second = _make_named_package(self.root/'next', 'B')
        image = approved.preflight_result.candidates[0]
        _rename_declared_image(second, image.image_paths[0])
        _replace_declared_image_bytes(second, (self.package/image.image_paths[0]).read_bytes())
        _rewrite_record(second, dict(image_paths=list(image.image_paths), image_roles=list(image.image_roles)))
        parent = V124CandidateVerificationRequest(built.database.path.parent, (approved,), _contract())
        request = V124PreflightRequest(load_v124_import_manifest(second/'import_manifest.json'),
            second, ArtifactRef(BASELINE, BASELINE_SHA, BASELINE_SIZE, 'sqlite'), parent, _contract())
        blocked = preflight_v124_import(request, self.config)
        self.assertIn('duplicate_ambiguous', {i.code for i in blocked.issues})

    def test_independent_verifier_rejects_multi_reference_identity(self):
        from joy_m2.ingest.v124_verification import verify_v124_candidate
        forged = self._forged_blocked_source('ambiguous')
        root = self.root/'independent-bad'
        _independent_candidate(root, (forged,), _contract())
        result = verify_v124_candidate(V124CandidateVerificationRequest(root, (forged,), _contract()), self.config)
        self.assertEqual(result.status, 'FAIL')
        self.assertFalse(next(c.passed for c in result.checks if c.name == 'effective_collision_closure'))

    def test_writer_rejects_forged_ready_with_unknown_taxonomy(self):
        forged = self._forged_blocked_source('taxonomy')
        with self.assertRaises(PipelineError):
            self._build(V124CandidateBuildRequest((forged,), self.root/'bad', _contract()), self.config)

    def test_independent_verifier_rejects_unknown_taxonomy(self):
        from joy_m2.ingest.v124_verification import verify_v124_candidate
        forged = self._forged_blocked_source('taxonomy')
        root = self.root/'independent-bad'
        _independent_candidate(root, (forged,), _contract())
        result = verify_v124_candidate(V124CandidateVerificationRequest(root, (forged,), _contract()), self.config)
        self.assertEqual(result.status, 'FAIL')

    def test_writer_reconstructs_candidates_from_canonical_bytes(self):
        self.build()  # First-generation behavior must exist before hostile-carrier setup.
        from dataclasses import replace
        build_v124_candidate = self._build
        from joy_m2.ingest.v124_preflight import _formal_indexes
        from joy_m2.ingest.v124_verification import _normalized_text_sha256
        approved = _approved(self.package, self.config)
        source = approved.preflight_result.candidates[0]
        primary = next(x for x in sorted(_formal_indexes(BASELINE)[1]) if x != source.primary_type)
        changes = (
            {"solution_original": "not the canonical answer"},
            {"question_text_original": "Not the canonical question",
             "normalized_text_sha256": _normalized_text_sha256("Not the canonical question")},
            {"primary_type": primary},
            {"source_question_number": "forged-source-number"},
            {"translation_evidence": "source:source/source.txt#forged-fragment"},
            {"difficulty_level": 2},
        )
        before = _tree(self.package)
        for index, change in enumerate(changes):
            with self.subTest(change=change):
                forged = self._forged_candidates(approved, (replace(source, **change),))
                output = self.root / f"forged-record-{index}"
                with self.assertRaises(ImportApprovalError):
                    build_v124_candidate(V124CandidateBuildRequest((forged,), output, _contract()), self.config)
                self.assertFalse(output.exists())
                self.assertEqual(_tree(self.package), before)

    def test_writer_rejects_reordered_canonical_candidates(self):
        build_v124_candidate = self._build
        records_path = self.package / "records/candidates.json"
        records = json.loads(records_path.read_text(encoding="utf-8"))
        records.append(dict(
            records[0], proposed_question_id="TASK13-ORDER-002",
            source_question_number="A2", source_fragment_hash="b" * 64,
            question_text_original="Solve 7y + 2 = 37.",
        ))
        raw = (json.dumps(records, ensure_ascii=False) + "\n").encode("utf-8")
        records_path.write_bytes(raw)
        manifest_path = self.package / "import_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["candidate_records"][0].update(
            sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))
        manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        approved = _approved(self.package, self.config)
        self.assertEqual(approved.preflight_result.report.new_candidate_count, 2)
        forged = self._forged_candidates(approved, approved.preflight_result.candidates[::-1])
        before = _tree(self.package)
        output = self.root / "forged-order"
        with self.assertRaises(ImportApprovalError):
            build_v124_candidate(V124CandidateBuildRequest((forged,), output, _contract()), self.config)
        self.assertFalse(output.exists())
        self.assertEqual(_tree(self.package), before)

    def test_verifier_independently_reconstructs_canonical_record_authority(self):
        from dataclasses import replace
        from unittest import mock
        build_v124_candidate, verify_v124_candidate = self._build, self._verify
        approved = _approved(self.package, self.config)
        forged = self._forged_candidates(approved, (
            replace(approved.preflight_result.candidates[0], solution_original="not canonical"),))
        output = self.root / "forged-persisted"
        # Construct hostile synthetic artifacts while bypassing only the writer's
        # package binding; the later independent verifier has no patched checks.
        with mock.patch("joy_m2.ingest.v124_verification._package_evidence_valid", return_value=True):
            build_v124_candidate(V124CandidateBuildRequest((forged,), output, _contract()), self.config)
        before = _tree(output)
        report = verify_v124_candidate(V124CandidateVerificationRequest(output, (forged,), _contract()), self.config)
        self.assertEqual(report.status, "FAIL")
        self.assertFalse(next(c.passed for c in report.checks if c.name == "batch_authority_artifacts"))
        self.assertEqual(_tree(output), before)

    def _invalid_manifest_envelopes(self):
        original = (self.package / "import_manifest.json").read_text(encoding="utf-8")
        parsed = json.loads(original)
        return (
            ("duplicate-key", original.replace("{", '{"target_release_version":"V1.23",', 1)),
            ("reordered-fields", json.dumps(dict(reversed(tuple(parsed.items())))) + "\n"),
        )

    def test_writer_rejects_stale_noncanonical_manifest_envelope(self):
        build_v124_candidate = self._build
        approved = _approved(self.package, self.config)
        manifest_path = self.package / "import_manifest.json"
        cases = self._invalid_manifest_envelopes()
        for name, raw in cases:
            with self.subTest(name=name):
                manifest_path.write_text(raw, encoding="utf-8")
                with self.assertRaises(PipelineError):
                    load_v124_import_manifest(manifest_path)
                before = _tree(self.package)
                output = self.root / name
                with self.assertRaises(ImportApprovalError):
                    build_v124_candidate(V124CandidateBuildRequest((approved,), output, _contract()), self.config)
                self.assertFalse(output.exists())
                self.assertEqual(_tree(self.package), before)

    def test_verifier_rejects_stale_noncanonical_manifest_envelope(self):
        verify_v124_candidate = self._verify
        approved, artifacts = self.build()
        manifest_path = self.package / "import_manifest.json"
        cases = self._invalid_manifest_envelopes()
        for name, raw in cases:
            with self.subTest(name=name):
                manifest_path.write_text(raw, encoding="utf-8")
                with self.assertRaises(PipelineError):
                    load_v124_import_manifest(manifest_path)
                before = _tree(self.root)
                report = verify_v124_candidate(V124CandidateVerificationRequest(
                    artifacts.database.path.parent, (approved,), _contract()), self.config)
                self.assertEqual(report.status, "FAIL")
                self.assertFalse(next(c.passed for c in report.checks if c.name == "batch_authority_artifacts"))
                self.assertEqual(_tree(self.root), before)

    def test_uri_reserved_output_names_are_read_only_and_cleanup_safe(self):
        from unittest import mock
        build_v124_candidate, verify_v124_candidate = self._build, self._verify
        approved = _approved(self.package, self.config)
        for marker in ("#", "?"):
            with self.subTest(marker=marker):
                output = self.root / f"candidate{marker}1"
                try:
                    artifacts = build_v124_candidate(V124CandidateBuildRequest((approved,), output, _contract()), self.config)
                except PipelineError as error:
                    self.fail(f"valid path failed and may create stray files: {error}")
                before = _tree(self.root)
                report = verify_v124_candidate(V124CandidateVerificationRequest(output, (approved,), _contract()), self.config)
                self.assertEqual(report.status, "PASS")
                self.assertEqual(_tree(self.root), before)
                target = self.root / f"fault{marker}2"
                with mock.patch("joy_m2.ingest.v124_writer.atomic_rename_no_replace", side_effect=OSError("injected")):
                    with self.assertRaises(PipelineError):
                        build_v124_candidate(V124CandidateBuildRequest((approved,), target, _contract()), self.config)
                self.assertEqual(_tree(self.root), before)

    def test_unsafe_output_targets_and_read_only_baseline_connection(self):
        self.build(self.root / "control")  # Separate successful prerequisite.
        build_v124_candidate = self._build
        from unittest import mock
        import joy_m2.ingest.v124_writer as writer
        approved=_approved(self.package,self.config)
        link=self.root/"data/staging/link"
        link.symlink_to(self.package,target_is_directory=True)
        for output in (self.package/"nested", link/"nested", BASELINE.parent/"forbidden", ROOT/"tmp/pdfs/task14-v124-synthetic/not-staging"):
            with self.subTest(output=output),self.assertRaises(PipelineError):
                build_v124_candidate(V124CandidateBuildRequest((approved,),output,_contract()),self.config)
            self.assertFalse(output.exists())
        connect=sqlite3.connect
        calls=[]
        def audited_connect(*args,**kwargs):
            if str(BASELINE) in str(args[0]) or BASELINE.as_uri() in str(args[0]):
                calls.append(args[0])
                self.assertIn("mode=ro",str(args[0]))
                self.assertTrue(kwargs.get("uri"))
            return connect(*args,**kwargs)
        with mock.patch.object(writer.sqlite3,"connect",side_effect=audited_connect):
            self.build()
        self.assertTrue(calls)



    def test_writer_matches_independent_oracle_records_and_authority(self):
        approved, artifacts = self.build()
        oracle = self.root / "oracle"
        digest = _independent_candidate(oracle, (approved,), _contract())
        self.assertEqual(artifacts.state.candidate_digest, digest)
        for relative, _, _ in _tree(oracle):
            # Fixture and writer use distinct SQLite insertion code; require all bytes too.
            self.assertEqual((oracle / relative).read_bytes(),
                             (artifacts.database.path.parent / relative).read_bytes(), relative)


class V124MultiBatchTests(unittest.TestCase):

    def test_all_read_only_connections_use_immutable_uri_and_query_only(self):
        from unittest.mock import patch
        from joy_m2.ingest.v124_writer import build_v124_candidate
        from joy_m2.ingest.v124_verification import verify_v124_candidate
        original = sqlite3.connect
        observed = []
        def observe(*args, **kwargs):
            connection = original(*args, **kwargs)
            if "mode=ro" in str(args[0]):
                statements = []
                connection.set_trace_callback(statements.append)
                observed.append((str(args[0]), kwargs, statements))
            return connection
        with patch.object(sqlite3, "connect", side_effect=observe):
            a = _approved(self.package, self.config)
            parent = self.root / "readonly-control"
            build_v124_candidate(V124CandidateBuildRequest((a,),parent,_contract()),self.config)
            request = V124CandidateVerificationRequest(parent,(a,),_contract())
            self.assertEqual(verify_v124_candidate(request,self.config).status,"PASS")
            _approved(_make_named_package(self.root,"b"),self.config,request)
        self.assertTrue(observed)
        for uri, kwargs, statements in observed:
            self.assertIn("immutable=1",uri)
            self.assertTrue(kwargs.get("uri"))
            self.assertIn("PRAGMA query_only=ON", statements)

    def prefix(self):
        from joy_m2.ingest.v124_writer import build_v124_candidate
        from joy_m2.ingest.v124_verification import verify_v124_candidate
        a = _approved(self.package, self.config)
        parent = self.root / "parent-prefix"
        artifacts = build_v124_candidate(V124CandidateBuildRequest((a,), parent, _contract()), self.config)
        request = V124CandidateVerificationRequest(parent, (a,), _contract())
        self.assertEqual(verify_v124_candidate(request, self.config).status, "PASS")
        b = _approved(_make_named_package(self.root, "b"), self.config, request)
        self.assertEqual(b.preflight_result.report.before_count, 678)
        self.assertEqual(b.approval.parent_candidate_digest, artifacts.state.candidate_digest)
        return a, b, parent

    def append(self, prefix, target):
        from joy_m2.ingest.v124_writer import build_v124_candidate
        return self._invoke(build_v124_candidate,
            V124CandidateBuildRequest(prefix, target, _contract()), self.config)

    def test_third_preflight_contains_entire_prefix_not_only_last(self):
        from dataclasses import replace
        a, b, parent = self.prefix()
        before = _tree(parent)
        child = self.append((a, b), self.root / "child")
        request = V124CandidateVerificationRequest(child.database.path.parent, (a,b), _contract())
        c = _make_named_package(self.root, "c")
        ready = preflight_v124_import(replace(_request(c), parent_candidate=request), self.config)
        self.assertEqual((ready.report.before_count, ready.report.projected_after_count), (679,680))
        self.assertEqual(ready.report.parent_batch_count, 2)
        for accepted in (a,b):
            first = accepted.preflight_result.candidates[0]
            _rewrite_record(c, {"proposed_question_id": first.proposed_question_id})
            blocked = preflight_v124_import(replace(_request(c), parent_candidate=request), self.config)
            self.assertIn("collision_candidate_id", {i.code for i in blocked.issues})
        self.assertEqual(_tree(parent), before)

    def test_fault_and_existing_destination_preserve_every_parent_byte(self):
        from unittest.mock import patch
        a, b, parent = self.prefix()
        self.append((a,b), self.root / "control")
        before = _tree(self.root)
        with patch("joy_m2.ingest.v124_writer.atomic_rename_no_replace", side_effect=OSError("injected")):
            with self.assertRaises(PipelineError):
                self.append((a,b), self.root / "failed")
        self.assertEqual(_tree(self.root), before)
        with self.assertRaises(OutputConflictError):
            self.append((a,b), parent)
        self.assertEqual(_tree(self.root), before)

    def test_invalid_prefixes_approvals_and_substitution_are_rejected(self):
        from dataclasses import replace
        from joy_m2.ingest.v124_verification import verify_v124_candidate
        a, b, parent = self.prefix()
        child = self.append((a,b), self.root / "control")
        before = _tree(self.root)
        for label, prefix in (("duplicate-batch",(a,a)),("truncated",(b,)),("substituted",(b,a))):
            with self.subTest(label=label), self.assertRaises(PipelineError):
                self.append(prefix, self.root / label)
            report = verify_v124_candidate(V124CandidateVerificationRequest(
                child.database.path.parent, prefix, _contract()), self.config)
            self.assertEqual(report.status, "FAIL")
        for key, values in (("target_release_version", ("V1.23",)),
                            ("parent_candidate_digest", (None,"",GENESIS,"0"*64))):
            for value in values:
                with self.subTest(key=key,value=value):
                    approval = object.__new__(V124ImportApproval)
                    for field, original in vars(b.approval).items():
                        object.__setattr__(approval, field, value if field==key else original)
                    forged = object.__new__(V124ApprovedBatch)
                    for field, original in vars(b).items():
                        object.__setattr__(forged, field, approval if field=="approval" else original)
                    with self.assertRaises(PipelineError):
                        self.append((a,forged),self.root/"forged")
        self.assertEqual(_tree(self.root), before)

    def test_collision_defense_rejects_forged_ready_batch(self):
        from dataclasses import replace
        a,b,parent = self.prefix()
        self.append((a,b), self.root / "control")
        # Valid authority cannot be manufactured by copying a previous candidate
        # under a report that still claims one net-new B record.
        forged_result = replace(b.preflight_result, candidates=a.preflight_result.candidates)
        forged = replace(b, preflight_result=forged_result)
        before = _tree(parent)
        with self.assertRaises(PipelineError):
            self.append((a,forged),self.root/"collision")
        self.assertEqual(_tree(parent), before)
    setUp = V124FirstWriterTests.setUp
    tearDown = V124FirstWriterTests.tearDown
    _invoke = V124FirstWriterTests._invoke

    def test_second_batch_requires_verified_parent_and_appends_atomically(self):
        from joy_m2.ingest.v124_writer import build_v124_candidate as _build
        build_v124_candidate = lambda *args: self._invoke(_build, *args)

        approved_a = _approved(self.package, self.config)
        parent_root = self.root / "parent"
        parent = build_v124_candidate(
            V124CandidateBuildRequest((approved_a,), parent_root, _contract()),
            self.config,
        )
        package_b = _make_named_package(self.root, "b")
        parent_request = V124CandidateVerificationRequest(
            parent_root, (approved_a,), _contract()
        )
        approved_b = _approved(package_b, self.config, parent_request)
        self.assertEqual(approved_b.approval.parent_candidate_digest, parent.state.candidate_digest)
        self.assertEqual(approved_b.preflight_result.report.status, "READY FOR USER IMPORT APPROVAL")
        child = build_v124_candidate(
            V124CandidateBuildRequest(
                (approved_a, approved_b), self.root / "child", _contract()
            ),
            self.config,
        )
        self.assertEqual(parent.state.projected_question_count, 678)
        self.assertEqual(child.state.projected_question_count, 679)
        self.assertEqual(len(child.state.batch_ledger), 2)
        self.assertEqual(
            child.state.batch_ledger[1].parent_candidate_digest,
            parent.state.candidate_digest,
        )
        twin = build_v124_candidate(
            V124CandidateBuildRequest((approved_a, approved_b),
                                     self.root / "child-twin", _contract()),
            self.config,
        )
        self.assertEqual(_tree(child.database.path.parent), _tree(twin.database.path.parent))
        self.assertEqual(child.state.candidate_digest, twin.state.candidate_digest)
        with self.assertRaises(PipelineError):
            build_v124_candidate(
                V124CandidateBuildRequest((approved_a, approved_b),
                                         parent_root / "nested", _contract()),
                self.config,
            )

    def test_stale_preflight_and_approval_cannot_append_and_preserve_parent(self):
        from joy_m2.ingest.v124_writer import build_v124_candidate as _build
        build_v124_candidate = lambda *args: self._invoke(_build, *args)

        approved_a = _approved(self.package, self.config)
        parent_a = self.root / "parent-a"
        build_v124_candidate(
            V124CandidateBuildRequest((approved_a,), parent_a, _contract()),
            self.config,
        )
        package_b = _make_named_package(self.root, "b")
        approved_b = _approved(
            package_b,
            self.config,
            V124CandidateVerificationRequest(parent_a, (approved_a,), _contract()),
        )
        parent_ab = self.root / "parent-ab"
        build_v124_candidate(
            V124CandidateBuildRequest(
                (approved_a, approved_b), parent_ab, _contract()
            ),
            self.config,
        )
        before = _tree(parent_ab)
        package_c = _make_named_package(self.root, "c")
        stale_c = _approved(
            package_c,
            self.config,
            V124CandidateVerificationRequest(parent_a, (approved_a,), _contract()),
        )
        current_c = _approved(
            _make_named_package(self.root / "current", "c"),
            self.config,
            V124CandidateVerificationRequest(
                parent_ab, (approved_a, approved_b), _contract()
            ),
        )
        self.assertNotEqual(
            stale_c.preflight_result.report.parent_candidate_digest,
            current_c.preflight_result.report.parent_candidate_digest,
        )
        self.assertNotEqual(
            stale_c.preflight_result.report.preflight_sha256,
            current_c.preflight_result.report.preflight_sha256,
        )
        output = self.root / "stale-child"
        with self.assertRaises(ImportApprovalError):
            build_v124_candidate(
                V124CandidateBuildRequest(
                    (approved_a, approved_b, stale_c), output, _contract()
                ),
                self.config,
            )
        self.assertFalse(output.exists())
        self.assertEqual(_tree(parent_ab), before)


    def test_multi_batch_verifier_rejects_nonmatching_existing_generation(self):
        from joy_m2.ingest.v124_writer import build_v124_candidate
        from joy_m2.ingest.v124_verification import verify_v124_candidate
        approved_a=_approved(self.package,self.config)
        parent_root=self.root/"parent-verify"
        parent=build_v124_candidate(V124CandidateBuildRequest((approved_a,),parent_root,_contract()),self.config)
        request=V124CandidateVerificationRequest(parent_root,(approved_a,),_contract())
        self.assertEqual(verify_v124_candidate(request,self.config).status,"PASS")
        approved_b=_approved(_make_named_package(self.root,"b"),self.config,request)
        self.assertEqual(approved_b.approval.parent_candidate_digest,parent.state.candidate_digest)
        try:
            result=verify_v124_candidate(V124CandidateVerificationRequest(parent_root,(approved_a,approved_b),_contract()),self.config)
        except NotImplementedError:
            self.fail("valid B authority reached multi-batch verifier missing behavior")
        self.assertEqual(result.status,"FAIL")

    def test_reordered_genesis_stale_package_and_forged_counts_block(self):
        from joy_m2.ingest.v124_writer import build_v124_candidate
        from joy_m2.ingest.v124_verification import verify_v124_candidate
        from dataclasses import replace
        approved_a=_approved(self.package,self.config)
        parent_root=self.root/"parent-negatives"
        parent=build_v124_candidate(V124CandidateBuildRequest((approved_a,),parent_root,_contract()),self.config)
        parent_request=V124CandidateVerificationRequest(parent_root,(approved_a,),_contract())
        self.assertEqual(verify_v124_candidate(parent_request,self.config).status,"PASS")
        package_b=_make_named_package(self.root,"b")
        b=_approved(package_b,self.config,parent_request)
        stale=_approved(package_b,self.config,None)
        self.assertNotEqual(b.approval.parent_candidate_digest,stale.approval.parent_candidate_digest)
        before=_tree(parent_root)
        for label,prefix in (("reordered",(b,approved_a)),("stale-genesis",(approved_a,stale))):
            with self.subTest(label=label):
                output=self.root/label
                try:
                    with self.assertRaises(ImportApprovalError):
                        build_v124_candidate(V124CandidateBuildRequest(prefix,output,_contract()),self.config)
                except NotImplementedError:
                    self.fail("valid B authority reached missing multi-batch writer")
                self.assertFalse(output.exists())
                self.assertEqual(_tree(parent_root),before)
        forged_report = object.__new__(type(b.preflight_result.report))
        for key, value in vars(b.preflight_result.report).items():
            object.__setattr__(forged_report, key, value + 1 if key == "new_candidate_count" else value)
        forged_result = replace(b.preflight_result, report=forged_report)
        forged_b = replace(b, preflight_result=forged_result)
        with self.assertRaises(ImportApprovalError):
            build_v124_candidate(V124CandidateBuildRequest(
                (approved_a, forged_b), self.root/"forged-counts", _contract()), self.config)
        verification = verify_v124_candidate(V124CandidateVerificationRequest(
            parent_root, (approved_a, forged_b), _contract()), self.config)
        self.assertEqual(verification.status, "FAIL")
        self.assertFalse((self.root/"forged-counts").exists())
        record=package_b/"records/candidates.json"
        record.write_bytes(record.read_bytes()+b" ")
        with self.assertRaises(ImportApprovalError):
            self._invoke(build_v124_candidate,V124CandidateBuildRequest((approved_a,b),self.root/"stale-bytes",_contract()),self.config)
        self.assertEqual(_tree(parent_root),before)
