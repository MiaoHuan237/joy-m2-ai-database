"""Behavior contract for V1.20 aggregate candidate generations."""

from __future__ import annotations

from contextlib import closing
import errno
import importlib
import importlib.util
import inspect
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import (
    ImportApprovalError,
    InputFormatError,
    InputMissingError,
    OutputConflictError,
    PipelineError,
)
from joy_m2.ingest.models import ImportCandidate
from joy_m2.ingest.v120_models import (
    V120ApprovedBatch,
    V120CandidateArtifacts,
    V120CandidateBuildRequest,
    V120CandidateVerificationRequest,
    V120BatchLedgerEntry,
    V120EffectiveState,
    V120ImportApproval,
    V120ImportPreflightReport,
    V120ImportPreflightResult,
    V120PreflightRequest,
)
from joy_m2.ingest.v120_manifest import load_v120_import_manifest
from joy_m2.ingest.v120_preflight import preflight_v120_import
from joy_m2.ingest.v120_writer import build_v120_candidate
from joy_m2.ingest.v120_verification import verify_v120_candidate
from joy_m2.ingest.writer_models import ImportApproval
from joy_m2.models import VerificationReport
from tests.integration.test_v120_preflight import (
    A_MANIFEST_SHA,
    A_PREFLIGHT_SHA,
    BASELINE_RELEASE_DIGEST,
    BASELINE_SHA,
    FIXTURES,
    FORMAL_IMAGE_PATH,
    FORMAL_IMAGE_ROLE,
    FORMAL_IMAGE_SHA,
    GENESIS,
    SHARED_IMAGE_SHA,
    _baseline_ref,
    _contract,
    _fixture,
    _literal_a_approved_batch,
    _literal_a_payload,
    _remove_declared_images,
    _rewrite_record,
)


A_CANDIDATE_DIGEST = "7e612d0a44f29ace7efb4fa2b2cb8bfe12b8f437132b5f8365d6c1561c95bd65"
B_MANIFEST_SHA = "f8309935da52c88e4aeed19aa01e4700673e9026e0280b63258a737876137dca"
B_PREFLIGHT_SHA = "66ef57ac30d1f8f0bea9862c8a9b82622af46c870738e013c1a74417bc182e04"
AB_CANDIDATE_DIGEST = "ddf18f27c947c2bcdbb99897023464547d1ae9200fdc528d3abff81ae120697a"
C_MANIFEST_SHA = "b19e471777554722693bbb9e66c588c182e3e15db7e5c9b71bce1705abba1ac2"
C_PREFLIGHT_SHA = "c7dc3c1b0e86898397a7970f0d188029b9dc28c9fc8f3a4d7d0fe73e1a6ba327"
ABC_CANDIDATE_DIGEST = "c6d295039eeff7629353d27666702c1637e6ce246b0f89d9ef5fb806cbd4f76d"


_EXACT_V120_SCHEMA = (
    (
        "table",
        "task10_v120_batch_ledger_v1",
        """CREATE TABLE task10_v120_batch_ledger_v1 (
    batch_ordinal INTEGER PRIMARY KEY CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL UNIQUE CHECK(length(batch_id) BETWEEN 1 AND 128),
    target_release_version TEXT NOT NULL CHECK(target_release_version = 'V1.20'),
    candidate_database_schema TEXT NOT NULL
        CHECK(candidate_database_schema = 'task10-v120-candidate-v1'),
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
              preflight_sha256 || ' V1.20 PARENT ' ||
              parent_candidate_digest),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version = 'V1.19'),
    baseline_database_sha256 TEXT NOT NULL
        CHECK(baseline_database_sha256 =
              '5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff'),
    baseline_release_digest TEXT NOT NULL
        CHECK(baseline_release_digest =
              '7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count = 502),
    batch_candidate_count INTEGER NOT NULL CHECK(batch_candidate_count >= 0),
    cumulative_candidate_count INTEGER NOT NULL
        CHECK(cumulative_candidate_count >= batch_candidate_count),
    projected_question_count INTEGER NOT NULL
        CHECK(projected_question_count = 502 + cumulative_candidate_count),
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    UNIQUE(batch_ordinal, batch_id)
)""",
    ),
    (
        "table",
        "task10_v120_candidates_v1",
        """CREATE TABLE task10_v120_candidates_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    batch_candidate_order INTEGER NOT NULL CHECK(batch_candidate_order >= 0),
    aggregate_order INTEGER NOT NULL CHECK(aggregate_order >= 503),
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
        REFERENCES task10_v120_batch_ledger_v1(batch_ordinal, batch_id)
)""",
    ),
    (
        "table",
        "task10_v120_images_v1",
        """CREATE TABLE task10_v120_images_v1 (
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
        REFERENCES task10_v120_candidates_v1(
            batch_ordinal, batch_id, proposed_question_id
        )
)""",
    ),
    (
        "table",
        "task10_v120_taxonomy_v1",
        """CREATE TABLE task10_v120_taxonomy_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    taxonomy_kind TEXT NOT NULL CHECK(taxonomy_kind IN ('primary_type','tag')),
    value TEXT NOT NULL,
    sort_order INTEGER NOT NULL CHECK(sort_order >= 1),
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    PRIMARY KEY(batch_ordinal, batch_id, taxonomy_kind, value),
    UNIQUE(batch_ordinal, batch_id, taxonomy_kind, sort_order),
    FOREIGN KEY(batch_ordinal, batch_id)
        REFERENCES task10_v120_batch_ledger_v1(batch_ordinal, batch_id)
)""",
    ),
    (
        "view",
        "task10_candidate_questions_v120",
        """CREATE VIEW task10_candidate_questions_v120 AS
SELECT f.*
FROM formal_complete_questions_v119 AS f
UNION ALL
SELECT
    c.aggregate_order AS formal_order,
    c.proposed_question_id AS question_id,
    'task10_v120_candidate' AS authority_kind,
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
FROM task10_v120_candidates_v1 AS c
ORDER BY formal_order""",
    ),
)


def _raw_candidate(letter: str) -> dict[str, object]:
    root = FIXTURES / f"v120-batch-{letter}"
    raw = json.loads((root / "records/candidates.json").read_text(encoding="utf-8"))[0]
    manifest = json.loads((root / "import_manifest.json").read_text(encoding="utf-8"))
    images = {item["relative_path"]: item for item in manifest["image_files"]}
    raw["normalized_text_sha256"] = hashlib.sha256(
        raw["question_text_original"].encode("utf-8")
    ).hexdigest()
    raw["image_sha256s"] = [images[path]["sha256"] for path in raw["image_paths"]]
    ordered_names = (
        "proposed_question_id", "source_id", "source_question_number", "source_section",
        "source_fragment_hash", "normalized_text_sha256", "question_text_original",
        "question_text_zh", "translation_status", "translation_evidence", "solution_original",
        "solution_verified", "answer_status", "explanation_text", "explanation_status",
        "explanation_evidence", "image_paths", "image_sha256s", "image_roles", "primary_type",
        "tags", "tag_status", "difficulty_level", "difficulty_status", "enrichment_status",
    )
    return {name: raw[name] for name in ordered_names}


def _ledger_entry(
    ordinal: int,
    batch_id: str,
    parent: str,
    preflight: str,
    manifest: str,
) -> V120BatchLedgerEntry:
    approval = V120ImportApproval(
        batch_id, preflight, "V1.20", parent,
        f"USER APPROVED IMPORT BATCH {batch_id} {preflight} V1.20 PARENT {parent}",
    )
    return V120BatchLedgerEntry(
        ordinal, batch_id, parent, preflight, manifest, approval,
        1, ordinal, 502 + ordinal,
    )


def _approved_prefix() -> tuple[V120ApprovedBatch, V120ApprovedBatch, V120ApprovedBatch]:
    approved_a = _literal_a_approved_batch()
    ledger_a = _ledger_entry(1, "TASK10-A", GENESIS, A_PREFLIGHT_SHA, A_MANIFEST_SHA)
    root_b, manifest_b = _fixture("b")
    state_b = V120EffectiveState(_baseline_ref(), A_CANDIDATE_DIGEST, (ledger_a,), 1, 503)
    candidate_b = ImportCandidate(**_raw_candidate("b"))
    files_b = tuple(sorted(
        item.relative_path
        for group in (
            manifest_b.candidate_records, manifest_b.source_files, manifest_b.answer_files,
            manifest_b.image_files, manifest_b.teacher_notes_files, manifest_b.common_errors_files,
        )
        for item in group
    ))
    report_b = V120ImportPreflightReport(
        "TASK10-B", "READY FOR USER IMPORT APPROVAL", B_PREFLIGHT_SHA, B_MANIFEST_SHA,
        "V1.19", BASELINE_RELEASE_DIGEST, 502, "V1.20", A_CANDIDATE_DIGEST,
        1, 503, 1, 1, 0, 0, 0, 0, 504, files_b, (), (), 0, 0,
        (), (), (), (), (), (), ((2, 1),), ("TASK10-B-001",), (), (), (),
    )
    result_b = V120ImportPreflightResult(manifest_b, state_b, (candidate_b,), (), report_b)
    approval_b = V120ImportApproval(
        "TASK10-B", B_PREFLIGHT_SHA, "V1.20", A_CANDIDATE_DIGEST,
        f"USER APPROVED IMPORT BATCH TASK10-B {B_PREFLIGHT_SHA} V1.20 PARENT {A_CANDIDATE_DIGEST}",
    )
    approved_b = V120ApprovedBatch(result_b, root_b, approval_b)

    ledger_b = _ledger_entry(2, "TASK10-B", A_CANDIDATE_DIGEST, B_PREFLIGHT_SHA, B_MANIFEST_SHA)
    root_c, manifest_c = _fixture("c")
    state_c = V120EffectiveState(
        _baseline_ref(), AB_CANDIDATE_DIGEST, (ledger_a, ledger_b), 2, 504,
    )
    candidate_c = ImportCandidate(**_raw_candidate("c"))
    files_c = tuple(sorted(
        item.relative_path
        for group in (
            manifest_c.candidate_records, manifest_c.source_files, manifest_c.answer_files,
            manifest_c.image_files, manifest_c.teacher_notes_files, manifest_c.common_errors_files,
        )
        for item in group
    ))
    report_c = V120ImportPreflightReport(
        "TASK10-C", "READY FOR USER IMPORT APPROVAL", C_PREFLIGHT_SHA, C_MANIFEST_SHA,
        "V1.19", BASELINE_RELEASE_DIGEST, 502, "V1.20", AB_CANDIDATE_DIGEST,
        2, 504, 1, 1, 0, 0, 0, 0, 505, files_c, (), (), 0, 0,
        (), (), (), (), (), (), ((1, 1),), ("TASK10-C-001",), (), (), (),
    )
    result_c = V120ImportPreflightResult(manifest_c, state_c, (candidate_c,), (), report_c)
    approval_c = V120ImportApproval(
        "TASK10-C", C_PREFLIGHT_SHA, "V1.20", AB_CANDIDATE_DIGEST,
        f"USER APPROVED IMPORT BATCH TASK10-C {C_PREFLIGHT_SHA} V1.20 PARENT {AB_CANDIDATE_DIGEST}",
    )
    approved_c = V120ApprovedBatch(result_c, root_c, approval_c)
    return approved_a, approved_b, approved_c


def _parent_only_stale_c() -> V120ApprovedBatch:
    approved_a, approved_b, approved_c = _approved_prefix()
    state_after_a = approved_b.preflight_result.effective_state
    provisional_sha = "0" * 64
    provisional_report = replace(
        approved_c.preflight_result.report,
        preflight_sha256=provisional_sha,
        parent_candidate_digest=A_CANDIDATE_DIGEST,
        parent_batch_count=1,
        before_count=503,
        projected_after_count=504,
    )
    provisional_result = V120ImportPreflightResult(
        approved_c.preflight_result.manifest,
        state_after_a,
        approved_c.preflight_result.candidates,
        (),
        provisional_report,
    )
    provisional_approval = V120ImportApproval(
        "TASK10-C", provisional_sha, "V1.20", A_CANDIDATE_DIGEST,
        f"USER APPROVED IMPORT BATCH TASK10-C {provisional_sha} V1.20 PARENT {A_CANDIDATE_DIGEST}",
    )
    provisional = V120ApprovedBatch(
        provisional_result, approved_c.package_root, provisional_approval,
    )
    stale_sha = hashlib.sha256(_canonical_file(_preflight_payload(provisional))).hexdigest()
    report = replace(provisional_report, preflight_sha256=stale_sha)
    result = V120ImportPreflightResult(
        provisional_result.manifest, state_after_a, provisional_result.candidates, (), report,
    )
    approval = V120ImportApproval(
        "TASK10-C", stale_sha, "V1.20", A_CANDIDATE_DIGEST,
        f"USER APPROVED IMPORT BATCH TASK10-C {stale_sha} V1.20 PARENT {A_CANDIDATE_DIGEST}",
    )
    return V120ApprovedBatch(result, approved_c.package_root, approval)


def _forged(value: object, **updates: object):
    result = object.__new__(type(value))
    for name, current in value.__dict__.items():
        object.__setattr__(result, name, updates.get(name, current))
    return result


def _approved_a_with_recomputed_authority(
    *,
    candidate: ImportCandidate | None = None,
    report_updates: dict[str, object] | None = None,
) -> V120ApprovedBatch:
    base = _approved_prefix()[0]
    selected_candidate = candidate or base.preflight_result.candidates[0]
    updates = report_updates or {}
    payload = _literal_a_payload()
    if candidate is not None:
        payload["candidates"][0]["proposed_question_id"] = candidate.proposed_question_id
        payload["duplicate_classifications"][0]["candidate_id"] = candidate.proposed_question_id
        for item in payload["image_evidence"]:
            item["proposed_question_id"] = candidate.proposed_question_id
    payload["report"].update(updates)
    preflight_sha = hashlib.sha256(_canonical_file(payload)).hexdigest()
    report = replace(
        base.preflight_result.report,
        preflight_sha256=preflight_sha,
        **updates,
    )
    result = V120ImportPreflightResult(
        base.preflight_result.manifest,
        base.preflight_result.effective_state,
        (selected_candidate,),
        (),
        report,
    )
    approval = V120ImportApproval(
        "TASK10-A",
        preflight_sha,
        "V1.20",
        GENESIS,
        f"USER APPROVED IMPORT BATCH TASK10-A {preflight_sha} "
        f"V1.20 PARENT {GENESIS}",
    )
    return V120ApprovedBatch(result, base.package_root, approval)


def _output_root() -> tempfile.TemporaryDirectory:
    staging = ROOT / "data/staging"
    staging.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix="task10a-red-", dir=staging)


_CHECK_NAMES = (
    "candidate_directory", "candidate_contract", "baseline_authority",
    "batch_authority_artifacts", "parent_chain", "approval_binding",
    "preflight_reconstruction", "filesystem_closure", "sha256sums_closure",
    "artifact_references", "rollback_contract", "image_projection",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "v119_preservation", "batch_ledger",
    "candidate_projection", "effective_collision_closure", "count_closure",
    "candidate_digest", "deterministic_identity", "formal_boundary",
)


def _canonical_file(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8") + b"\n"


def _artifact(path: Path, root: Path, kind: str) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "relative_path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
        "kind": kind,
    }


def _tree_fingerprint(root: Path) -> tuple[tuple[str, str, int], ...]:
    return tuple(
        (path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size)
        for path in sorted(root.rglob("*")) if path.is_file()
    )


def _preflight_payload(approved: V120ApprovedBatch) -> dict[str, object]:
    if approved.approval.batch_id == "TASK10-A":
        return _literal_a_payload()
    result = approved.preflight_result
    manifest = result.manifest
    groups = (
        manifest.candidate_records, manifest.source_files, manifest.answer_files,
        manifest.image_files, manifest.teacher_notes_files, manifest.common_errors_files,
    )
    files = sorted(
        ({"relative_path": item.relative_path, "sha256": item.sha256,
          "size_bytes": item.size_bytes, "kind": item.kind}
         for group in groups for item in group),
        key=lambda item: item["relative_path"],
    )
    candidate_values = [_raw_candidate(approved.approval.batch_id[-1].lower())]
    image_lookup = {item.relative_path: item for item in manifest.image_files}
    image_evidence = [
        {"proposed_question_id": candidate.proposed_question_id,
         "relative_path": path, "sha256": image_lookup[path].sha256,
         "size_bytes": image_lookup[path].size_bytes, "kind": "image", "role": role}
        for candidate in result.candidates
        for path, role in zip(candidate.image_paths, candidate.image_roles, strict=True)
    ]
    report = {
        name: ([list(item) if isinstance(item, tuple) else item for item in value]
               if isinstance(value, tuple) else value)
        for name, value in result.report.__dict__.items()
        if name != "preflight_sha256"
    }
    return {
        "schema": "task10-v120-preflight-v1", "batch_id": manifest.batch_id,
        "target_release_version": "V1.20",
        "baseline": _literal_a_payload()["baseline"],
        "parent_state": {
            "candidate_digest": result.effective_state.candidate_digest,
            "batch_count": len(result.effective_state.batch_ledger),
            "candidate_count": result.effective_state.candidate_count,
            "projected_question_count": result.effective_state.projected_question_count,
        },
        "manifest_policies": {
            name: getattr(manifest, name) for name in (
                "schema_version", "project", "module", "chapter", "language_policy",
                "split_policy", "difficulty_policy", "tag_policy", "answer_policy",
                "explanation_policy",
            )
        },
        "candidate_record_order": [item.relative_path for item in manifest.candidate_records],
        "file_evidence": files, "candidates": candidate_values, "issues": [],
        "duplicate_classifications": [
            {"candidate_id": candidate.proposed_question_id, "classification": "new_candidate",
             "reference_question_id": None, "evidence": None}
            for candidate in result.candidates
        ],
        "image_evidence": image_evidence, "report": report,
    }


def _candidate_identity_payload(
    approved_batches: tuple[V120ApprovedBatch, ...],
) -> dict[str, object]:
    """Literal aggregate oracle; it deliberately imports no production digest helper."""
    ledger: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    images: list[dict[str, object]] = []
    cumulative = 0
    for ordinal, approved in enumerate(approved_batches, start=1):
        result = approved.preflight_result
        approval = approved.approval
        prior_count = cumulative
        cumulative += len(result.candidates)
        ledger.append({
            "ordinal": ordinal,
            "batch_id": approval.batch_id,
            "parent_candidate_digest": approval.parent_candidate_digest,
            "preflight_sha256": approval.preflight_sha256,
            "manifest_sha256": result.report.manifest_sha256,
            "approval": {
                "batch_id": approval.batch_id,
                "preflight_sha256": approval.preflight_sha256,
                "target_release_version": approval.target_release_version,
                "parent_candidate_digest": approval.parent_candidate_digest,
                "statement": approval.statement,
            },
            "batch_candidate_count": len(result.candidates),
            "cumulative_candidate_count": cumulative,
            "projected_question_count": 502 + cumulative,
        })
        image_evidence = {
            item.relative_path: item for item in result.manifest.image_files
        }
        for candidate_order, candidate in enumerate(result.candidates):
            candidate_paths: list[str] = []
            for image_order, (source, digest, role) in enumerate(zip(
                candidate.image_paths,
                candidate.image_sha256s,
                candidate.image_roles,
                strict=True,
            )):
                suffix = Path(source).suffix.lower()
                extension = ".jpg" if suffix in {".jpg", ".jpeg"} else suffix
                destination = f"images/sha256/{digest[:2]}/{digest}{extension}"
                candidate_paths.append(destination)
                evidence = image_evidence[source]
                images.append({
                    "batch_ordinal": ordinal,
                    "batch_id": approval.batch_id,
                    "proposed_question_id": candidate.proposed_question_id,
                    "image_order": image_order,
                    "source_relative_path": source,
                    "candidate_relative_path": destination,
                    "sha256": digest,
                    "size_bytes": evidence.size_bytes,
                    "kind": "image",
                    "role": role,
                })
            candidates.append({
                "aggregate_order": 502 + prior_count + candidate_order + 1,
                "batch_ordinal": ordinal,
                "batch_id": approval.batch_id,
                "batch_candidate_order": candidate_order,
                "record": _raw_candidate(approval.batch_id[-1].lower()),
                "candidate_image_paths": candidate_paths,
            })
    images.sort(key=lambda item: (
        item["candidate_relative_path"], item["batch_ordinal"], item["batch_id"],
        item["proposed_question_id"], item["image_order"],
    ))
    return {
        "schema": "task10-v120-candidate-identity-v1",
        "baseline": _literal_a_payload()["baseline"],
        "target_release_version": "V1.20",
        "batch_ledger": ledger,
        "candidate_projection": candidates,
        "image_projection": images,
        "counts": {
            "baseline_question_count": 502,
            "batch_count": len(approved_batches),
            "new_candidate_count": cumulative,
            "projected_question_count": 502 + cumulative,
        },
    }
def _write_parent_oracle(
    candidate_dir: Path,
    approved_batches: tuple[V120ApprovedBatch, ...],
) -> V120CandidateVerificationRequest:
    """Author a self-contained parent generation without calling either production API."""
    candidate_dir.mkdir(parents=True)
    database = candidate_dir / "Joy_M2_V1.20_candidate.sqlite3"
    shutil.copyfile(_baseline_ref().path, database)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("BEGIN IMMEDIATE")
        for object_type, object_name, sql in _EXACT_V120_SCHEMA[:-1]:
            assert object_type == "table"
            assert sql.startswith(f"CREATE TABLE {object_name} (")
            assert "DEFAULT" not in sql.upper()
            connection.execute(sql)
        for ordinal, approved in enumerate(approved_batches, start=1):
            result = approved.preflight_result
            approval = approved.approval
            cumulative = sum(len(item.preflight_result.candidates) for item in approved_batches[:ordinal])
            connection.execute(
                "INSERT INTO task10_v120_batch_ledger_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (ordinal, approval.batch_id, "V1.20", "task10-v120-candidate-v1",
                 approval.parent_candidate_digest, approval.preflight_sha256,
                 result.report.manifest_sha256, approval.statement, "V1.19", BASELINE_SHA,
                 BASELINE_RELEASE_DIGEST, 502, len(result.candidates), cumulative,
                 502 + cumulative, "candidate"),
            )
            for order, candidate in enumerate(result.candidates):
                destinations = [f"images/sha256/{digest[:2]}/{digest}.svg" for digest in candidate.image_sha256s]
                connection.execute(
                    "INSERT INTO task10_v120_candidates_v1 VALUES (" + ",".join("?" for _ in range(32)) + ")",
                    (ordinal, approval.batch_id, order, 502 + cumulative - len(result.candidates) + order + 1,
                     candidate.proposed_question_id, candidate.source_id, candidate.source_question_number,
                     candidate.source_section, candidate.source_fragment_hash, candidate.normalized_text_sha256,
                     candidate.question_text_original, candidate.question_text_zh,
                     candidate.translation_status, candidate.translation_evidence,
                     candidate.solution_original, candidate.solution_verified, candidate.answer_status,
                     candidate.explanation_text, candidate.explanation_status, candidate.explanation_evidence,
                     json.dumps(candidate.image_paths, ensure_ascii=False, separators=(",", ":")),
                     json.dumps(candidate.image_sha256s, ensure_ascii=False, separators=(",", ":")),
                     json.dumps(candidate.image_roles, ensure_ascii=False, separators=(",", ":")),
                     candidate.primary_type, json.dumps(candidate.tags, ensure_ascii=False, separators=(",", ":")),
                     candidate.tag_status, candidate.difficulty_level, candidate.difficulty_status,
                     candidate.enrichment_status, json.dumps(destinations, separators=(",", ":")),
                     "candidate", 0),
                )
                for image_order, (source, digest, role, destination) in enumerate(zip(
                    candidate.image_paths, candidate.image_sha256s, candidate.image_roles,
                    destinations, strict=True,
                )):
                    evidence = next(item for item in result.manifest.image_files if item.relative_path == source)
                    connection.execute(
                        "INSERT INTO task10_v120_images_v1 VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (ordinal, approval.batch_id, candidate.proposed_question_id, image_order,
                         source, destination, digest, evidence.size_bytes, "image", role),
                    )
                taxonomy = (("primary_type", candidate.primary_type),) + tuple(("tag", tag) for tag in candidate.tags)
                counters = {"primary_type": 0, "tag": 0}
                for kind, value in taxonomy:
                    counters[kind] += 1
                    connection.execute(
                        "INSERT INTO task10_v120_taxonomy_v1 VALUES (?,?,?,?,?,?)",
                        (ordinal, approval.batch_id, kind, value, counters[kind], "candidate"),
                    )
        view_type, view_name, view_sql = _EXACT_V120_SCHEMA[-1]
        assert view_type == "view"
        assert view_sql.startswith(f"CREATE VIEW {view_name} AS")
        assert "DEFAULT" not in view_sql.upper()
        connection.execute(view_sql)
        connection.execute("PRAGMA user_version=120")
        connection.commit()

    authority_refs = []
    for ordinal, approved in enumerate(approved_batches, start=1):
        authority = candidate_dir / "authority/batches" / f"{ordinal:06d}" / approved.approval.batch_id
        authority.mkdir(parents=True)
        payload = _preflight_payload(approved)
        assert hashlib.sha256(_canonical_file(payload)).hexdigest() == approved.approval.preflight_sha256
        (authority / "preflight.json").write_bytes(_canonical_file({
            "preflight_sha256": approved.approval.preflight_sha256, "payload": payload,
        }))
        (authority / "approval.json").write_bytes(_canonical_file({
            "schema_version": "task10-v120-import-approval-v1",
            "batch_id": approved.approval.batch_id,
            "preflight_sha256": approved.approval.preflight_sha256,
            "target_release_version": "V1.20",
            "parent_candidate_digest": approved.approval.parent_candidate_digest,
            "statement": approved.approval.statement,
        }))
        authority_refs.extend((_artifact(authority / "approval.json", candidate_dir, "approval"),
                               _artifact(authority / "preflight.json", candidate_dir, "preflight")))

    image_target = candidate_dir / f"images/sha256/88/{SHARED_IMAGE_SHA}.svg"
    image_target.parent.mkdir(parents=True)
    image_target.write_bytes((FIXTURES / "v120-batch-a/images/shared.svg").read_bytes())
    image_refs = [_artifact(image_target, candidate_dir, "image")]
    database_ref = _artifact(database, candidate_dir, "sqlite")
    identity_payload = _candidate_identity_payload(approved_batches)
    digest = hashlib.sha256(_canonical_file(identity_payload)).hexdigest()
    literal_digests = {
        1: A_CANDIDATE_DIGEST,
        2: AB_CANDIDATE_DIGEST,
        3: ABC_CANDIDATE_DIGEST,
    }
    assert digest == literal_digests[len(approved_batches)]
    ledger = [
        {"ordinal": ordinal, "batch_id": item.approval.batch_id,
         "parent_candidate_digest": item.approval.parent_candidate_digest,
         "preflight_sha256": item.approval.preflight_sha256,
         "manifest_sha256": item.preflight_result.report.manifest_sha256,
         "approval": dict(item.approval.__dict__),
         "batch_candidate_count": len(item.preflight_result.candidates),
         "cumulative_candidate_count": ordinal, "projected_question_count": 502 + ordinal}
        for ordinal, item in enumerate(approved_batches, start=1)
    ]
    fixed_paths = [database_ref["relative_path"]] + [item["relative_path"] for item in authority_refs + image_refs]
    fixed_paths += ["candidate_manifest.json", "SHA256SUMS", "rollback.json"]
    rollback = candidate_dir / "rollback.json"
    rollback.write_bytes(_canonical_file({
        "schema_version": "task10-v120-rollback-v1",
        "action": "delete_unpromoted_v120_candidate_tree_if_digest_matches",
        "candidate_digest": digest, "protected_baseline": _literal_a_payload()["baseline"],
        "candidate_artifacts": sorted(fixed_paths),
    }))
    manifest = candidate_dir / "candidate_manifest.json"
    manifest.write_bytes(_canonical_file({
        "schema_version": "task10-v120-candidate-manifest-v1", "release_version": "V1.20",
        "release_status": "candidate", "release_model": "append-only-multi-batch-candidate",
        "baseline": _literal_a_payload()["baseline"], "candidate_digest": digest,
        "counts": {"baseline_question_count": 502, "batch_count": len(approved_batches),
                   "new_candidate_count": len(approved_batches),
                   "projected_question_count": 502 + len(approved_batches)},
        "batch_ledger": ledger, "database": database_ref, "images": image_refs,
        "batch_authority_artifacts": sorted(authority_refs, key=lambda item: item["relative_path"]),
        "rollback": _artifact(rollback, candidate_dir, "rollback"),
        "verification": {"authority": "verify_v120_candidate",
                         "check_names": list(_CHECK_NAMES), "required_status": "PASS"},
    }))
    covered = sorted(path for path in candidate_dir.rglob("*") if path.is_file() and path.name != "SHA256SUMS")
    sums = candidate_dir / "SHA256SUMS"
    sums.write_text("".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(candidate_dir).as_posix()}\n"
        for path in covered
    ), encoding="utf-8", newline="\n")
    for line in sums.read_text(encoding="utf-8").splitlines():
        digest_value, relative = line.split("  ", 1)
        assert hashlib.sha256((candidate_dir / relative).read_bytes()).hexdigest() == digest_value
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        schema_names = tuple(item[1] for item in _EXACT_V120_SCHEMA)
        actual_schema = tuple(connection.execute(
            "SELECT type, name, sql FROM sqlite_schema "
            f"WHERE name IN ({','.join('?' for _ in schema_names)}) ORDER BY type, name",
            schema_names,
        ))
        assert actual_schema == _EXACT_V120_SCHEMA
        assert all("DEFAULT" not in sql.upper() for _, _, sql in actual_schema)
        assert connection.execute("PRAGMA user_version").fetchone() == (120,)
        assert connection.execute("SELECT COUNT(*) FROM task10_v120_batch_ledger_v1").fetchone() == (len(approved_batches),)
        assert connection.execute("SELECT COUNT(*) FROM task10_v120_candidates_v1").fetchone() == (len(approved_batches),)
        assert connection.execute("SELECT COUNT(*) FROM task10_candidate_questions_v120").fetchone() == (502 + len(approved_batches),)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    return V120CandidateVerificationRequest(candidate_dir, approved_batches, _contract())


def _rewrite_sums(root: Path) -> None:
    sums = root / "SHA256SUMS"
    covered = sorted(
        path for path in root.rglob("*") if path.is_file() and path != sums
    )
    sums.write_text(
        "".join(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  "
            f"{path.relative_to(root).as_posix()}\n"
            for path in covered
        ),
        encoding="utf-8",
        newline="\n",
    )


def _rewrite_formal_sums(root: Path) -> None:
    covered = tuple(
        root / name
        for name in (
            "Joy_M2_Complete_Question_DB_V1_19.sqlite3",
            "manifest.json",
            "rollback.json",
        )
    )
    (root / "SHA256SUMS.txt").write_text(
        "".join(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
            for path in covered
        ),
        encoding="utf-8",
        newline="\n",
    )


def _with_baseline_path(
    approved: V120ApprovedBatch,
    database_path: Path,
) -> V120ApprovedBatch:
    baseline = _baseline_ref(database_path)
    state = _forged(
        approved.preflight_result.effective_state,
        baseline_database=baseline,
    )
    result = _forged(approved.preflight_result, effective_state=state)
    return _forged(approved, preflight_result=result)


def _refresh_database_artifact(root: Path) -> None:
    manifest_path = root / "candidate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    database = root / "Joy_M2_V1.20_candidate.sqlite3"
    manifest["database"] = _artifact(database, root, "sqlite")
    manifest_path.write_bytes(_canonical_file(manifest))
    _rewrite_sums(root)


def _rewrite_manifest(root: Path, update) -> None:
    path = root / "candidate_manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    update(payload)
    path.write_bytes(_canonical_file(payload))
    _rewrite_sums(root)


def _require_module(testcase: unittest.TestCase, name: str):
    testcase.assertIsNotNone(
        importlib.util.find_spec(name),
        f"{name} must exist before its V1.20 API can pass",
    )
    return importlib.import_module(name)


def _assert_signature(
    testcase: unittest.TestCase,
    function: object,
    names: tuple[str, ...],
    annotations: tuple[object, ...],
    return_annotation: object,
) -> None:
    testcase.assertTrue(callable(function))
    signature = inspect.signature(function)
    parameters = tuple(signature.parameters.values())
    testcase.assertEqual(tuple(parameter.name for parameter in parameters), names)
    testcase.assertEqual(tuple(parameter.annotation for parameter in parameters), annotations)
    testcase.assertTrue(
        all(
            parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
            and parameter.default is inspect.Parameter.empty
            for parameter in parameters
        )
    )
    testcase.assertIs(signature.return_annotation, return_annotation)


class V120CandidateApiTests(unittest.TestCase):
    def test_writer_module_exposes_only_the_exact_versioned_api(self) -> None:
        module = _require_module(self, "joy_m2.ingest.v120_writer")
        self.assertEqual(module.__all__, ("build_v120_candidate",))
        _assert_signature(
            self,
            getattr(module, "build_v120_candidate", None),
            ("request", "config"),
            (V120CandidateBuildRequest, PipelineConfig),
            V120CandidateArtifacts,
        )

    def test_verifier_module_exposes_only_the_exact_versioned_api(self) -> None:
        module = _require_module(self, "joy_m2.ingest.v120_verification")
        self.assertEqual(module.__all__, ("verify_v120_candidate",))
        _assert_signature(
            self,
            getattr(module, "verify_v120_candidate", None),
            ("request", "config"),
            (V120CandidateVerificationRequest, PipelineConfig),
            VerificationReport,
        )

    def test_task10a_entry_points_are_final_root_ingest_exports(self) -> None:
        ingest = importlib.import_module("joy_m2.ingest")
        for name in (
            "preflight_v120_import",
            "build_v120_candidate",
            "verify_v120_candidate",
        ):
            with self.subTest(name=name):
                self.assertIn(name, ingest.__all__)
                self.assertTrue(hasattr(ingest, name))


class V120ApprovalBindingTests(unittest.TestCase):
    """Phase D REDs: writer consumption revalidates exact parent-bound approval."""

    def test_exact_v120_approval_reaches_candidate_builder_without_extra_authority(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as directory:
            request = V120CandidateBuildRequest(
                (approved,), Path(directory) / "candidate", _contract(),
            )
            build_v120_candidate(request, PipelineConfig(ROOT))

    def test_writer_rejects_each_forged_approval_field_before_creating_output(self) -> None:
        approved = _approved_prefix()[0]
        mutations = {
            "batch_id": "OTHER-BATCH", "preflight_sha256": "d" * 64,
            "target_release_version": "V1.19", "parent_candidate_digest": "e" * 64,
            "statement": "USER APPROVED IMPORT BATCH forged",
        }
        for field, value in mutations.items():
            with self.subTest(field=field), _output_root() as directory:
                bad_approval = _forged(approved.approval, **{field: value})
                bad_batch = _forged(approved, approval=bad_approval)
                output = Path(directory) / "candidate"
                with self.assertRaises(ImportApprovalError):
                    build_v120_candidate(
                        V120CandidateBuildRequest((bad_batch,), output, _contract()),
                        PipelineConfig(ROOT),
                    )
                self.assertFalse(output.exists())

    def test_writer_rejects_reordered_noncontiguous_and_cross_parent_prefixes(self) -> None:
        approved_a, approved_b, approved_c = _approved_prefix()
        cases = (
            (approved_b, approved_a),
            (approved_a, approved_c),
            (approved_a, _forged(
                approved_b,
                approval=_forged(
                    approved_b.approval,
                    parent_candidate_digest="f" * 64,
                    statement=(
                        f"USER APPROVED IMPORT BATCH TASK10-B {B_PREFLIGHT_SHA} "
                        f"V1.20 PARENT {'f' * 64}"
                    ),
                ),
            )),
        )
        for index, prefix in enumerate(cases):
            with self.subTest(case=index), _output_root() as directory:
                output = Path(directory) / "candidate"
                with self.assertRaises(ImportApprovalError):
                    build_v120_candidate(
                        V120CandidateBuildRequest(prefix, output, _contract()),
                        PipelineConfig(ROOT),
                    )
                self.assertFalse(output.exists())

    def test_parent_only_stale_approval_is_rejected_against_current_effective_parent(self) -> None:
        approved_a, approved_b, _ = _approved_prefix()
        stale_c = _parent_only_stale_c()
        self.assertEqual(stale_c.approval.batch_id, stale_c.preflight_result.report.batch_id)
        self.assertEqual(stale_c.approval.preflight_sha256, stale_c.preflight_result.report.preflight_sha256)
        self.assertEqual(stale_c.approval.target_release_version, "V1.20")
        self.assertEqual(stale_c.approval.parent_candidate_digest, stale_c.preflight_result.effective_state.candidate_digest)
        self.assertEqual(
            stale_c.approval.statement,
            f"USER APPROVED IMPORT BATCH TASK10-C {stale_c.approval.preflight_sha256} "
            f"V1.20 PARENT {A_CANDIDATE_DIGEST}",
        )
        self.assertNotEqual(stale_c.approval.parent_candidate_digest, AB_CANDIDATE_DIGEST)
        with _output_root() as directory:
            output = Path(directory) / "candidate"
            with self.assertRaises(ImportApprovalError):
                build_v120_candidate(
                    V120CandidateBuildRequest((approved_a, approved_b, stale_c), output, _contract()),
                    PipelineConfig(ROOT),
                )
            self.assertFalse(output.exists())

    def test_historical_v119_approval_statement_remains_exact_and_separate(self) -> None:
        digest = "a" * 64
        approval = ImportApproval(
            "TASK9-HISTORICAL", digest, "V1.19",
            f"USER APPROVED IMPORT BATCH TASK9-HISTORICAL {digest} V1.19",
        )
        self.assertEqual(
            approval.statement,
            f"USER APPROVED IMPORT BATCH TASK9-HISTORICAL {digest} V1.19",
        )
        with self.assertRaises(ImportApprovalError):
            ImportApproval(
                "TASK9-HISTORICAL", digest, "V1.19",
                f"USER APPROVED IMPORT BATCH TASK9-HISTORICAL {digest} V1.20 PARENT {GENESIS}",
            )


class V120FirstBatchWriterTests(unittest.TestCase):
    """Phase H REDs: exact first-prefix publication and failure atomicity."""

    def _request(self, output: Path, approved: V120ApprovedBatch | None = None):
        return V120CandidateBuildRequest(
            ((approved or _approved_prefix()[0]),), output, _contract(),
        )

    def test_one_batch_with_multiple_candidates_writes_distinct_taxonomy_catalogue(self) -> None:
        """Catches taxonomy order restarting for every candidate in one batch."""
        with _output_root() as directory:
            root = Path(directory)
            package = root / "package-multi"
            shutil.copytree(FIXTURES / "v120-batch-a", package)
            records = json.loads(
                (package / "records/candidates.json").read_text(encoding="utf-8")
            )
            second = dict(records[0])
            second.update({
                "proposed_question_id": "TASK10-A-002",
                "source_id": "TASK10-SOURCE-A-2",
                "source_question_number": "A2",
                "source_section": "Synthetic batch A second question",
                "source_fragment_hash": "d" * 64,
                "question_text_original": "Factor x^2 - 5x + 6.",
                "question_text_zh": "因式分解 x^2 - 5x + 6。",
                "translation_evidence": "source:source/source.txt#translation-A2",
                "solution_original": "(x - 2)(x - 3)",
                "solution_verified": "(x - 2)(x - 3)",
                "explanation_text": "Find two numbers with sum 5 and product 6.",
                "explanation_evidence": "source:source/source.txt#explanation-A2",
                "image_paths": [],
                "image_roles": [],
                "tags": ["一元一次方程", "因式分解"],
            })
            record_bytes = json.dumps(
                [records[0], second],
                ensure_ascii=False,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8") + b"\n"
            (package / "records/candidates.json").write_bytes(record_bytes)
            manifest_payload = json.loads(
                (package / "import_manifest.json").read_text(encoding="utf-8")
            )
            manifest_payload["candidate_records"][0]["sha256"] = hashlib.sha256(
                record_bytes
            ).hexdigest()
            manifest_payload["candidate_records"][0]["size_bytes"] = len(record_bytes)
            (package / "import_manifest.json").write_bytes(
                json.dumps(
                    manifest_payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8") + b"\n"
            )
            manifest = load_v120_import_manifest(package / "import_manifest.json")
            preflight = preflight_v120_import(
                V120PreflightRequest(
                    manifest, package, _baseline_ref(), None, _contract(),
                ),
                PipelineConfig(ROOT),
            )
            self.assertEqual(
                preflight.report.status,
                "READY FOR USER IMPORT APPROVAL",
                preflight.issues,
            )
            self.assertEqual(len(preflight.candidates), 2)
            approval = V120ImportApproval(
                manifest.batch_id,
                preflight.report.preflight_sha256,
                "V1.20",
                GENESIS,
                f"USER APPROVED IMPORT BATCH {manifest.batch_id} "
                f"{preflight.report.preflight_sha256} V1.20 PARENT {GENESIS}",
            )
            approved = V120ApprovedBatch(preflight, package, approval)
            output = root / "candidate-multi"

            try:
                artifacts = build_v120_candidate(
                    self._request(output, approved), PipelineConfig(ROOT),
                )
            except sqlite3.IntegrityError as error:
                self.fail(f"multi-candidate taxonomy must not collide: {error}")

            self.assertEqual(artifacts.verification_report.status, "PASS")
            with closing(sqlite3.connect(artifacts.database.path)) as database:
                self.assertEqual(
                    tuple(database.execute(
                        "SELECT taxonomy_kind,value,sort_order "
                        "FROM task10_v120_taxonomy_v1 "
                        "ORDER BY taxonomy_kind,sort_order"
                    )),
                    (
                        ("primary_type", "代数", 1),
                        ("tag", "一元一次方程", 1),
                        ("tag", "因式分解", 2),
                    ),
                )

    def test_first_prefix_matches_the_independent_tree_schema_and_artifact_oracle(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as directory:
            root = Path(directory)
            expected = root / "independent-oracle"
            actual = root / "writer-output"
            _write_parent_oracle(expected, (approved,))

            artifacts = build_v120_candidate(
                self._request(actual, approved), PipelineConfig(ROOT),
            )

            self.assertEqual(_tree_fingerprint(actual), _tree_fingerprint(expected))
            self.assertEqual(artifacts.database.path, actual / "Joy_M2_V1.20_candidate.sqlite3")
            self.assertEqual(artifacts.manifest.path, actual / "candidate_manifest.json")
            self.assertEqual(artifacts.sha256sums.path, actual / "SHA256SUMS")
            self.assertEqual(artifacts.rollback.path, actual / "rollback.json")
            self.assertEqual(len(artifacts.batch_authorities), 2)
            self.assertEqual(len(artifacts.images), 1)
            self.assertEqual(artifacts.state.candidate_digest, A_CANDIDATE_DIGEST)
            self.assertEqual(artifacts.state.candidate_count, 1)
            self.assertEqual(artifacts.state.projected_question_count, 503)
            self.assertEqual(artifacts.verification_report.status, "PASS")
            with closing(sqlite3.connect(artifacts.database.path)) as database:
                self.assertEqual(database.execute("PRAGMA user_version").fetchone(), (120,))
                self.assertEqual(
                    tuple(database.execute(
                        "SELECT type, name, sql FROM sqlite_schema "
                        "WHERE name LIKE 'task10_%' ORDER BY type, name"
                    )),
                    _EXACT_V120_SCHEMA,
                )
                self.assertEqual(
                    database.execute(
                        "SELECT authority_kind, record_status, selectable "
                        "FROM task10_candidate_questions_v120 WHERE formal_order=503"
                    ).fetchone(),
                    ("task10_v120_candidate", "candidate", 0),
                )

    def test_independent_verifier_runs_against_private_tree_before_publication(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as directory:
            output = Path(directory) / "candidate"
            real_verify = verify_v120_candidate
            observations: list[tuple[Path, bool]] = []

            def verify_before_publish(request, config):
                observations.append((request.candidate_dir, output.exists()))
                self.assertNotEqual(request.candidate_dir, output)
                self.assertTrue(request.candidate_dir.exists())
                return real_verify(request, config)

            with mock.patch(
                "joy_m2.ingest.v120_writer.verify_v120_candidate",
                side_effect=verify_before_publish,
                create=True,
            ) as verifier:
                artifacts = build_v120_candidate(
                    self._request(output, approved), PipelineConfig(ROOT),
                )
            verifier.assert_called_once()
            self.assertEqual(len(observations), 1)
            self.assertFalse(observations[0][1])
            self.assertEqual(artifacts.database.path.parent, output)

    def test_nonready_missing_or_stale_nested_authority_fails_before_output(self) -> None:
        approved = _approved_prefix()[0]
        nonready_report = _forged(
            approved.preflight_result.report,
            status="BLOCKED — IMPORT PREFLIGHT FAILED",
            blocking_errors=("collision_candidate_id",),
        )
        cases = (
            _forged(approved, approval=None),
            _forged(
                approved,
                preflight_result=_forged(
                    approved.preflight_result, report=nonready_report,
                ),
            ),
            _forged(
                approved,
                preflight_result=_forged(
                    approved.preflight_result,
                    effective_state=_forged(
                        approved.preflight_result.effective_state,
                        candidate_digest="f" * 64,
                    ),
                ),
            ),
        )
        for index, bad in enumerate(cases):
            with self.subTest(index=index), _output_root() as directory:
                output = Path(directory) / "candidate"
                with self.assertRaises(ImportApprovalError):
                    build_v120_candidate(self._request(output, bad), PipelineConfig(ROOT))
                self.assertFalse(output.exists())

    def test_inconsistent_ready_report_fails_before_private_tree_creation(self) -> None:
        forged = _approved_a_with_recomputed_authority(
            report_updates={
                "detected_count": 2,
                "new_candidate_count": 2,
                "projected_after_count": 504,
            },
        )
        with _output_root() as directory:
            output = Path(directory) / "candidate"
            with mock.patch(
                "joy_m2.ingest.v120_writer.tempfile.mkdtemp",
                side_effect=AssertionError("private tree must not be created"),
            ) as make_temporary:
                with self.assertRaises(ImportApprovalError):
                    build_v120_candidate(
                        self._request(output, forged), PipelineConfig(ROOT)
                    )
            make_temporary.assert_not_called()
            self.assertFalse(output.exists())

    def test_ready_baseline_adaptation_builds_and_verifies(self) -> None:
        with _output_root() as directory:
            root = Path(directory)
            package = root / "adapted-package"
            shutil.copytree(FIXTURES / "v120-batch-a", package)
            _remove_declared_images(package)
            with closing(sqlite3.connect(_baseline_ref().path)) as database:
                reference = database.execute(
                    "SELECT question_id,source_id,source_question_number,source_section,"
                    "source_fragment_hash FROM formal_complete_questions_v119 "
                    "WHERE question_id='M2QD-DA-PARTB-Q4'"
                ).fetchone()
            self.assertIsNotNone(reference)
            _rewrite_record(package, {
                "source_id": reference[1],
                "source_question_number": reference[2],
                "source_section": reference[3],
                "source_fragment_hash": reference[4],
                "image_paths": [],
                "image_roles": [],
            })
            manifest = load_v120_import_manifest(package / "import_manifest.json")
            preflight = preflight_v120_import(
                V120PreflightRequest(
                    manifest,
                    package,
                    _baseline_ref(),
                    None,
                    _contract(),
                ),
                PipelineConfig(ROOT),
            )
            self.assertEqual(preflight.report.status, "READY FOR USER IMPORT APPROVAL")
            self.assertEqual(preflight.issues, ())
            self.assertEqual(len(preflight.report.adaptations), 1)
            approval = V120ImportApproval(
                preflight.manifest.batch_id,
                preflight.report.preflight_sha256,
                "V1.20",
                GENESIS,
                f"USER APPROVED IMPORT BATCH {preflight.manifest.batch_id} "
                f"{preflight.report.preflight_sha256} V1.20 PARENT {GENESIS}",
            )
            approved = V120ApprovedBatch(preflight, package, approval)
            output = root / "candidate"

            artifacts = build_v120_candidate(
                self._request(output, approved), PipelineConfig(ROOT)
            )

            self.assertEqual(artifacts.verification_report.status, "PASS")
            self.assertEqual(
                verify_v120_candidate(
                    V120CandidateVerificationRequest(
                        output, (approved,), _contract(),
                    ),
                    PipelineConfig(ROOT),
                ).status,
                "PASS",
            )

    def test_baseline_candidate_id_collision_fails_before_private_tree_creation(self) -> None:
        with closing(sqlite3.connect(_baseline_ref().path)) as database:
            formal_id = database.execute(
                "SELECT question_id FROM formal_complete_questions_v119 "
                "ORDER BY formal_order LIMIT 1"
            ).fetchone()[0]
        base_candidate = _approved_prefix()[0].preflight_result.candidates[0]
        candidate = replace(base_candidate, proposed_question_id=formal_id)
        forged = _approved_a_with_recomputed_authority(
            candidate=candidate,
            report_updates={"proposed_ids": (formal_id,)},
        )
        with _output_root() as directory:
            output = Path(directory) / "candidate"
            with mock.patch(
                "joy_m2.ingest.v120_writer.tempfile.mkdtemp",
                side_effect=AssertionError("private tree must not be created"),
            ) as make_temporary:
                with self.assertRaises(ImportApprovalError):
                    build_v120_candidate(
                        self._request(output, forged), PipelineConfig(ROOT)
                    )
            make_temporary.assert_not_called()
            self.assertFalse(output.exists())

    def test_cross_batch_candidate_id_collision_fails_before_private_tree_creation(self) -> None:
        approved_a, approved_b, _ = _approved_prefix()
        repeated_id = approved_a.preflight_result.candidates[0].proposed_question_id
        candidate = replace(
            approved_b.preflight_result.candidates[0],
            proposed_question_id=repeated_id,
        )
        payload = _preflight_payload(approved_b)
        payload["candidates"][0]["proposed_question_id"] = repeated_id
        payload["duplicate_classifications"][0]["candidate_id"] = repeated_id
        for item in payload["image_evidence"]:
            item["proposed_question_id"] = repeated_id
        payload["report"]["proposed_ids"] = [repeated_id]
        preflight_sha = hashlib.sha256(_canonical_file(payload)).hexdigest()
        report = replace(
            approved_b.preflight_result.report,
            preflight_sha256=preflight_sha,
            proposed_ids=(repeated_id,),
        )
        result = replace(
            approved_b.preflight_result,
            candidates=(candidate,),
            report=report,
        )
        approval = V120ImportApproval(
            "TASK10-B",
            preflight_sha,
            "V1.20",
            A_CANDIDATE_DIGEST,
            f"USER APPROVED IMPORT BATCH TASK10-B {preflight_sha} "
            f"V1.20 PARENT {A_CANDIDATE_DIGEST}",
        )
        forged_b = V120ApprovedBatch(result, approved_b.package_root, approval)
        with _output_root() as directory:
            output = Path(directory) / "candidate"
            with mock.patch(
                "joy_m2.ingest.v120_writer.tempfile.mkdtemp",
                side_effect=AssertionError("private tree must not be created"),
            ) as make_temporary:
                with self.assertRaises(ImportApprovalError):
                    build_v120_candidate(
                        V120CandidateBuildRequest(
                            (approved_a, forged_b), output, _contract(),
                        ),
                        PipelineConfig(ROOT),
                    )
            make_temporary.assert_not_called()
            self.assertFalse(output.exists())

    def test_reused_batch_id_fails_before_private_tree_creation(self) -> None:
        approved_a, approved_b, _ = _approved_prefix()
        with _output_root() as directory:
            root = Path(directory)
            package = root / "duplicate-batch-package"
            shutil.copytree(approved_b.package_root, package)
            manifest_path = package / "import_manifest.json"
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_payload["batch_id"] = approved_a.approval.batch_id
            manifest_path.write_bytes(
                json.dumps(
                    manifest_payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8") + b"\n"
            )
            manifest = load_v120_import_manifest(manifest_path)
            manifest_sha = hashlib.sha256(_canonical_file(manifest_payload)).hexdigest()

            preflight_payload = _preflight_payload(approved_b)
            preflight_payload["batch_id"] = approved_a.approval.batch_id
            preflight_payload["report"]["batch_id"] = approved_a.approval.batch_id
            preflight_payload["report"]["manifest_sha256"] = manifest_sha
            preflight_sha = hashlib.sha256(_canonical_file(preflight_payload)).hexdigest()
            report = replace(
                approved_b.preflight_result.report,
                batch_id=approved_a.approval.batch_id,
                preflight_sha256=preflight_sha,
                manifest_sha256=manifest_sha,
            )
            result = V120ImportPreflightResult(
                manifest,
                approved_b.preflight_result.effective_state,
                approved_b.preflight_result.candidates,
                (),
                report,
            )
            approval = V120ImportApproval(
                approved_a.approval.batch_id,
                preflight_sha,
                "V1.20",
                A_CANDIDATE_DIGEST,
                f"USER APPROVED IMPORT BATCH {approved_a.approval.batch_id} "
                f"{preflight_sha} V1.20 PARENT {A_CANDIDATE_DIGEST}",
            )
            forged = V120ApprovedBatch(result, package, approval)
            output = root / "candidate"

            with mock.patch(
                "joy_m2.ingest.v120_writer.tempfile.mkdtemp",
                side_effect=AssertionError("private tree must not be created"),
            ) as make_temporary:
                with self.assertRaises(ImportApprovalError):
                    build_v120_candidate(
                        V120CandidateBuildRequest(
                            (approved_a, forged), output, _contract(),
                        ),
                        PipelineConfig(ROOT),
                    )
            make_temporary.assert_not_called()
            self.assertFalse(output.exists())

    def test_package_image_and_candidate_source_swaps_are_rejected_before_output(self) -> None:
        approved = _approved_prefix()[0]
        mutations = (
            ("image", "images/shared.svg", b"mutated image bytes\n"),
            ("candidate", "records/candidates.json", b"[]\n"),
        )
        for label, relative, content in mutations:
            with self.subTest(label=label), _output_root() as directory:
                root = Path(directory)
                package = root / "package"
                shutil.copytree(approved.package_root, package)
                (package / relative).write_bytes(content)
                swapped = _forged(approved, package_root=package)
                output = root / "candidate"
                with self.assertRaises(PipelineError):
                    build_v120_candidate(self._request(output, swapped), PipelineConfig(ROOT))
                self.assertFalse(output.exists())

    def test_package_source_swap_after_first_read_never_publishes(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as directory:
            root = Path(directory)
            package = root / "package"
            shutil.copytree(approved.package_root, package)
            swapped = _forged(approved, package_root=package)
            source = package / "images/shared.svg"
            output = root / "candidate"
            original_read = Path.read_bytes
            original_write = Path.write_bytes
            changed = False

            def swap_after_first_read(path):
                nonlocal changed
                data = original_read(path)
                if path == source and not changed:
                    changed = True
                    original_write(source, b"swapped after validation\n")
                return data

            with mock.patch.object(
                Path,
                "read_bytes",
                autospec=True,
                side_effect=swap_after_first_read,
            ):
                with self.assertRaises(PipelineError):
                    build_v120_candidate(self._request(output, swapped), PipelineConfig(ROOT))
            self.assertTrue(changed)
            self.assertFalse(output.exists())

    def test_package_source_swap_after_verifier_pass_never_publishes(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as directory:
            root = Path(directory)
            package = root / "package"
            shutil.copytree(approved.package_root, package)
            swapped = _forged(approved, package_root=package)
            source = package / "records/candidates.json"
            output = root / "candidate"
            real_verify = verify_v120_candidate
            verified = []

            def swap_after_verification(request, config):
                report = real_verify(request, config)
                self.assertEqual(report.status, "PASS")
                verified.append(report)
                source.write_bytes(b"[]\n")
                return report

            with mock.patch(
                "joy_m2.ingest.v120_writer.verify_v120_candidate",
                side_effect=swap_after_verification,
            ):
                with self.assertRaises(PipelineError):
                    build_v120_candidate(
                        self._request(output, swapped), PipelineConfig(ROOT)
                    )

            self.assertEqual(len(verified), 1)
            self.assertFalse(output.exists())
            self.assertFalse(any(
                path.name.startswith(f".{output.name}.tmp-")
                for path in root.iterdir()
            ))

    def test_private_tree_tamper_after_verifier_pass_never_publishes(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as directory:
            root = Path(directory)
            output = root / "candidate"
            real_verify = verify_v120_candidate

            def tamper_after_verification(request, config):
                report = real_verify(request, config)
                self.assertEqual(report.status, "PASS")
                next((request.candidate_dir / "images").rglob("*.svg")).write_bytes(
                    b"tampered after verification\n"
                )
                return report

            with mock.patch(
                "joy_m2.ingest.v120_writer.verify_v120_candidate",
                side_effect=tamper_after_verification,
            ):
                with self.assertRaises(PipelineError):
                    build_v120_candidate(
                        self._request(output, approved), PipelineConfig(ROOT)
                    )

            self.assertFalse(output.exists())

    def test_formal_baseline_swap_after_verifier_pass_never_publishes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            formal = repo / "releases/V1.19"
            shutil.copytree(_baseline_ref().path.parent, formal)
            approved = _with_baseline_path(
                _approved_prefix()[0],
                formal / "Joy_M2_Complete_Question_DB_V1_19.sqlite3",
            )
            output = repo / "data/staging/candidate"
            real_verify = verify_v120_candidate

            def mutate_baseline_after_verification(request, config):
                report = real_verify(request, config)
                self.assertEqual(report.status, "PASS")
                baseline = approved.preflight_result.effective_state.baseline_database.path
                content = bytearray(baseline.read_bytes())
                content[-1] ^= 1
                baseline.write_bytes(content)
                return report

            with mock.patch(
                "joy_m2.ingest.v120_writer.verify_v120_candidate",
                side_effect=mutate_baseline_after_verification,
            ):
                with self.assertRaises(PipelineError):
                    build_v120_candidate(
                        self._request(output, approved), PipelineConfig(repo)
                    )

            self.assertFalse(output.exists())

    def test_cleanup_never_deletes_a_substituted_nonowned_private_path(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as directory:
            root = Path(directory)
            output = root / "candidate"
            captured: dict[str, Path] = {}

            def substitute_private_root(request, _config):
                private = request.candidate_dir
                owned = root / "moved-writer-owned-tree"
                private.rename(owned)
                private.mkdir()
                (private / "external-marker").write_bytes(b"must survive\n")
                captured.update(private=private, owned=owned)
                raise PipelineError("injected verifier failure")

            with mock.patch(
                "joy_m2.ingest.v120_writer.verify_v120_candidate",
                side_effect=substitute_private_root,
            ):
                with self.assertRaises(PipelineError):
                    build_v120_candidate(
                        self._request(output, approved), PipelineConfig(ROOT)
                    )

            self.assertEqual(
                (captured["private"] / "external-marker").read_bytes(),
                b"must survive\n",
            )
            self.assertFalse(captured["owned"].exists())
            self.assertFalse(output.exists())

    def test_external_lexical_symlink_ancestor_into_staging_is_rejected(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as staging_directory, tempfile.TemporaryDirectory() as alias_directory:
            staging = Path(staging_directory)
            physical = staging / "physical"
            nested = physical / "nested"
            nested.mkdir(parents=True)
            alias = Path(alias_directory) / "alias"
            alias.symlink_to(physical, target_is_directory=True)
            output = alias / "nested/candidate"

            with self.assertRaises(PipelineError):
                build_v120_candidate(
                    self._request(output, approved), PipelineConfig(ROOT)
                )

            self.assertFalse((nested / "candidate").exists())

    def test_new_generation_cannot_be_nested_inside_a_prior_candidate(self) -> None:
        approved_a, approved_b, _ = _approved_prefix()
        with _output_root() as directory:
            root = Path(directory)
            prior = root / "candidate-a"
            build_v120_candidate(
                self._request(prior, approved_a), PipelineConfig(ROOT)
            )
            before = _tree_fingerprint(prior)
            child = prior / "candidate-ab"

            with self.assertRaises(PipelineError):
                build_v120_candidate(
                    V120CandidateBuildRequest(
                        (approved_a, approved_b), child, _contract(),
                    ),
                    PipelineConfig(ROOT),
                )

            self.assertFalse(child.exists())
            self.assertEqual(_tree_fingerprint(prior), before)
            report = verify_v120_candidate(
                V120CandidateVerificationRequest(prior, (approved_a,), _contract()),
                PipelineConfig(ROOT),
            )
            self.assertEqual(report.status, "PASS")

    def test_output_conflict_and_all_forbidden_root_overlaps_fail_without_mutation(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as directory:
            root = Path(directory)
            existing = root / "existing"
            existing.mkdir()
            marker = existing / "marker"
            marker.write_bytes(b"keep")
            with self.assertRaises(PipelineError):
                build_v120_candidate(self._request(existing, approved), PipelineConfig(ROOT))
            self.assertEqual(marker.read_bytes(), b"keep")

        forbidden = (
            approved.package_root,
            approved.preflight_result.effective_state.baseline_database.path,
            ROOT / "releases/V1.20/candidate",
        )
        for output in forbidden:
            with self.subTest(output=output):
                before = output.read_bytes() if output.is_file() else _tree_fingerprint(output) if output.exists() else ()
                with self.assertRaises(PipelineError):
                    build_v120_candidate(self._request(output, approved), PipelineConfig(ROOT))
                after = output.read_bytes() if output.is_file() else _tree_fingerprint(output) if output.exists() else ()
                self.assertEqual(after, before)

    def test_symlink_leaf_ancestor_loop_and_resolved_escape_are_rejected_before_output(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as directory, tempfile.TemporaryDirectory() as outside_directory:
            staging = Path(directory)
            outside = Path(outside_directory)
            leaf_target = staging / "leaf-target"
            leaf_target.mkdir()
            leaf = staging / "leaf"
            leaf.symlink_to(leaf_target, target_is_directory=True)
            ancestor = staging / "ancestor"
            ancestor.symlink_to(staging, target_is_directory=True)
            loop = staging / "loop"
            loop.symlink_to(loop, target_is_directory=True)
            escape = staging / "escape"
            escape.symlink_to(outside, target_is_directory=True)
            cases = (leaf, ancestor / "candidate", loop / "candidate", escape / "candidate")
            for output in cases:
                with self.subTest(output=output):
                    request = _forged(
                        self._request(staging / "safe-candidate", approved),
                        output_dir=output,
                    )
                    with self.assertRaises(PipelineError):
                        build_v120_candidate(request, PipelineConfig(ROOT))
            self.assertEqual(tuple(outside.iterdir()), ())

    def test_public_request_preserves_symlink_ancestor_for_writer_rejection(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as directory:
            staging = Path(directory)
            physical = staging / "physical"
            physical.mkdir()
            alias = staging / "alias"
            alias.symlink_to(physical, target_is_directory=True)
            output = alias / "candidate"

            with self.assertRaises(PipelineError):
                build_v120_candidate(
                    self._request(output, approved),
                    PipelineConfig(ROOT),
                )

            self.assertFalse((physical / "candidate").exists())

    def test_failed_private_verification_cleans_owned_tree_and_never_publishes(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as directory:
            root = Path(directory)
            output = root / "candidate"
            before = tuple(root.iterdir())
            failed = VerificationReport(
                "FAIL",
                tuple(),
            )
            with mock.patch(
                "joy_m2.ingest.v120_writer.verify_v120_candidate",
                return_value=failed,
                create=True,
            ):
                with self.assertRaises(PipelineError):
                    build_v120_candidate(self._request(output, approved), PipelineConfig(ROOT))
            self.assertFalse(output.exists())
            self.assertEqual(tuple(root.iterdir()), before)

    def test_symlinked_private_artifact_is_rejected_and_private_tree_is_cleaned(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as directory:
            root = Path(directory)
            output = root / "candidate"
            outside = root / "outside-image.svg"
            outside.write_bytes(b"outside remains unchanged\n")
            original = outside.read_bytes()
            real_verify = verify_v120_candidate

            def replace_staged_image_with_symlink(request, config):
                image = next((request.candidate_dir / "images").rglob("*.svg"))
                image.unlink()
                image.symlink_to(outside)
                return real_verify(request, config)

            with mock.patch(
                "joy_m2.ingest.v120_writer.verify_v120_candidate",
                side_effect=replace_staged_image_with_symlink,
                create=True,
            ):
                with self.assertRaises(PipelineError):
                    build_v120_candidate(self._request(output, approved), PipelineConfig(ROOT))
            self.assertFalse(output.exists())
            self.assertEqual(outside.read_bytes(), original)
            self.assertEqual(tuple(path for path in root.iterdir() if path != outside), ())


class V120SecondBatchCandidateTests(unittest.TestCase):
    """Phase F REDs: full A+B prefix is semantic and the parent is immutable."""

    def test_second_generation_consumes_complete_ab_prefix_and_preserves_parent(self) -> None:
        approved_a, approved_b, _ = _approved_prefix()
        with _output_root() as directory:
            root = Path(directory)
            independent_parent = root / "independent-parent-a"
            _write_parent_oracle(independent_parent, (approved_a,))
            before = _tree_fingerprint(independent_parent)
            independent_ab = root / "independent-oracle-ab"
            _write_parent_oracle(independent_ab, (approved_a, approved_b))
            output = root / "candidate-ab"
            artifacts = build_v120_candidate(
                V120CandidateBuildRequest(
                    (approved_a, approved_b), output, _contract(),
                ),
                PipelineConfig(ROOT),
            )
            self.assertEqual(_tree_fingerprint(independent_parent), before)
            self.assertEqual(_tree_fingerprint(output), _tree_fingerprint(independent_ab))
            with closing(sqlite3.connect(artifacts.database.path)) as database:
                self.assertEqual(
                    tuple(database.execute(
                        "SELECT batch_ordinal,batch_id,parent_candidate_digest "
                        "FROM task10_v120_batch_ledger_v1 ORDER BY batch_ordinal"
                    )),
                    (
                        (1, "TASK10-A", GENESIS),
                        (2, "TASK10-B", A_CANDIDATE_DIGEST),
                    ),
                )
                self.assertEqual(
                    tuple(database.execute(
                        "SELECT batch_ordinal,batch_id,proposed_question_id,aggregate_order "
                        "FROM task10_v120_candidates_v1 ORDER BY aggregate_order"
                    )),
                    (
                        (1, "TASK10-A", "TASK10-A-001", 503),
                        (2, "TASK10-B", "TASK10-B-001", 504),
                    ),
                )
                self.assertEqual(
                    tuple(database.execute(
                        "SELECT batch_ordinal,batch_id,proposed_question_id,image_order "
                        "FROM task10_v120_images_v1 ORDER BY batch_ordinal,image_order"
                    )),
                    (
                        (1, "TASK10-A", "TASK10-A-001", 0),
                        (2, "TASK10-B", "TASK10-B-001", 0),
                    ),
                )
        self.assertEqual(tuple(entry.batch_id for entry in artifacts.state.batch_ledger), ("TASK10-A", "TASK10-B"))
        self.assertEqual(artifacts.state.candidate_count, 2)
        self.assertEqual(artifacts.state.projected_question_count, 504)
        self.assertEqual(artifacts.state.candidate_digest, AB_CANDIDATE_DIGEST)

    def test_stale_parent_preflight_and_reused_approval_are_not_appendable(self) -> None:
        approved_a, approved_b, _ = _approved_prefix()
        stale_result = _forged(
            approved_b.preflight_result,
            effective_state=_forged(
                approved_b.preflight_result.effective_state,
                candidate_digest="e" * 64,
            ),
        )
        stale = _forged(approved_b, preflight_result=stale_result)
        for candidate in (stale, _forged(approved_b, approval=approved_a.approval)):
            with self.subTest(kind=candidate.approval.batch_id), _output_root() as directory:
                root = Path(directory)
                parent = root / "verified-parent-a"
                _write_parent_oracle(parent, (approved_a,))
                before = _tree_fingerprint(parent)
                output = root / "candidate"
                with self.assertRaises(ImportApprovalError):
                    build_v120_candidate(
                        V120CandidateBuildRequest((approved_a, candidate), output, _contract()),
                        PipelineConfig(ROOT),
                    )
                self.assertFalse(output.exists())
                self.assertEqual(_tree_fingerprint(parent), before)


class V120ThirdBatchCandidateTests(unittest.TestCase):
    """Phase G REDs: A/B/C semantic order and image-binding identity."""

    def test_three_batches_preserve_abc_acceptance_order_and_aggregate_counts(self) -> None:
        prefix = _approved_prefix()
        with _output_root() as directory:
            artifacts = build_v120_candidate(
                V120CandidateBuildRequest(prefix, Path(directory) / "candidate-abc", _contract()),
                PipelineConfig(ROOT),
            )
        self.assertEqual(tuple(entry.batch_id for entry in artifacts.state.batch_ledger), ("TASK10-A", "TASK10-B", "TASK10-C"))
        self.assertEqual(artifacts.state.candidate_count, 3)
        self.assertEqual(artifacts.state.projected_question_count, 505)
        self.assertEqual(artifacts.state.candidate_digest, ABC_CANDIDATE_DIGEST)

    def test_semantic_tuple_reorder_is_rejected_instead_of_sorted(self) -> None:
        approved_a, approved_b, approved_c = _approved_prefix()
        for prefix in ((approved_b, approved_a, approved_c), (approved_a, approved_c, approved_b)):
            with self.subTest(order=tuple(item.approval.batch_id for item in prefix)), _output_root() as directory:
                output = Path(directory) / "candidate"
                with self.assertRaises(ImportApprovalError):
                    build_v120_candidate(
                        V120CandidateBuildRequest(prefix, output, _contract()),
                        PipelineConfig(ROOT),
                    )
                self.assertFalse(output.exists())

    def test_identical_image_bytes_publish_once_but_keep_all_four_ordered_bindings(self) -> None:
        prefix = _approved_prefix()
        with _output_root() as directory:
            artifacts = build_v120_candidate(
                V120CandidateBuildRequest(prefix, Path(directory) / "candidate-images", _contract()),
                PipelineConfig(ROOT),
            )
            self.assertEqual(len(artifacts.images), 1)
            self.assertEqual(artifacts.images[0].sha256, SHARED_IMAGE_SHA)
            with closing(sqlite3.connect(artifacts.database.path)) as connection:
                bindings = connection.execute(
                    "SELECT batch_ordinal, batch_id, proposed_question_id, image_order, "
                    "candidate_relative_path, sha256, role FROM task10_v120_images_v1 "
                    "ORDER BY candidate_relative_path, batch_ordinal, batch_id, "
                    "proposed_question_id, image_order"
                ).fetchall()
            destination = f"images/sha256/88/{SHARED_IMAGE_SHA}.svg"
            self.assertEqual(
                bindings,
                [
                    (1, "TASK10-A", "TASK10-A-001", 0, destination, SHARED_IMAGE_SHA, "question"),
                    (2, "TASK10-B", "TASK10-B-001", 0, destination, SHARED_IMAGE_SHA, "worked_example"),
                    (3, "TASK10-C", "TASK10-C-001", 0, destination, SHARED_IMAGE_SHA, "question"),
                    (3, "TASK10-C", "TASK10-C-001", 1, destination, SHARED_IMAGE_SHA, "worked_example"),
                ],
            )

    def test_different_bytes_claiming_one_content_address_are_rejected(self) -> None:
        approved_a, approved_b, _ = _approved_prefix()
        forged_candidate = _forged(
            approved_b.preflight_result.candidates[0],
            image_sha256s=(SHARED_IMAGE_SHA,),
        )
        forged_result = _forged(approved_b.preflight_result, candidates=(forged_candidate,))
        with _output_root() as directory:
            swapped_package = Path(directory) / "swapped-package-b"
            shutil.copytree(approved_b.package_root, swapped_package)
            (swapped_package / "images/shared-copy.svg").write_bytes(b"different bytes\n")
            forged_b = _forged(
                approved_b,
                preflight_result=forged_result,
                package_root=swapped_package,
            )
            output = Path(directory) / "candidate"
            with self.assertRaises(ImportApprovalError):
                build_v120_candidate(
                    V120CandidateBuildRequest((approved_a, forged_b), output, _contract()),
                    PipelineConfig(ROOT),
                )
            self.assertFalse(output.exists())

    def test_verifier_behavior_call_reaches_the_independent_scaffold(self) -> None:
        approved = _approved_prefix()[0]
        with _output_root() as directory:
            candidate = Path(directory) / "independent-candidate-a"
            _write_parent_oracle(candidate, (approved,))
            verify_v120_candidate(
                V120CandidateVerificationRequest(candidate, (approved,), _contract()),
                PipelineConfig(ROOT),
            )


class V120DeterminismAtomicityTests(unittest.TestCase):
    """Phase J REDs: rebuildability, atomic failure cleanup, and rollback."""

    @staticmethod
    def _tree_bytes(root: Path) -> tuple[tuple[str, bytes], ...]:
        return tuple(
            (path.relative_to(root).as_posix(), path.read_bytes())
            for path in sorted(root.rglob("*"))
            if path.is_file()
        )

    @staticmethod
    def _artifact_identity(reference, root: Path) -> tuple[str, str, int, str]:
        return (
            reference.path.relative_to(root).as_posix(),
            reference.sha256,
            reference.size_bytes,
            reference.kind,
        )

    def test_full_abc_rebuild_is_byte_identical_across_roots_and_physical_order(self) -> None:
        prefix = _approved_prefix()
        with _output_root() as first_directory, _output_root() as second_directory:
            first_root = Path(first_directory)
            second_root = Path(second_directory)
            rebased = []
            for index, approved in enumerate(prefix, start=1):
                package = second_root / f"package-{index}"
                package.mkdir()
                files = sorted(
                    (path for path in approved.package_root.rglob("*") if path.is_file()),
                    reverse=True,
                )
                for source in files:
                    destination = package / source.relative_to(approved.package_root)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, destination)
                rebased.append(replace(approved, package_root=package))

            first_output = first_root / "candidate-abc"
            second_output = second_root / "candidate-abc"
            first = build_v120_candidate(
                V120CandidateBuildRequest(prefix, first_output, _contract()),
                PipelineConfig(ROOT),
            )
            second = build_v120_candidate(
                V120CandidateBuildRequest(tuple(rebased), second_output, _contract()),
                PipelineConfig(ROOT),
            )

            self.assertNotEqual(first_output, second_output)
            self.assertEqual(
                self._tree_bytes(first_output), self._tree_bytes(second_output),
            )
            self.assertEqual(first.database.sha256, second.database.sha256)
            self.assertEqual(first.manifest.sha256, second.manifest.sha256)
            self.assertEqual(first.sha256sums.sha256, second.sha256sums.sha256)
            self.assertEqual(first.rollback.sha256, second.rollback.sha256)
            self.assertEqual(first.state, second.state)
            self.assertEqual(first.verification_report, second.verification_report)
            self.assertEqual(
                tuple(check.name for check in first.verification_report.checks),
                _CHECK_NAMES,
            )
            for left, right in (
                ((first.database,), (second.database,)),
                ((first.manifest,), (second.manifest,)),
                ((first.sha256sums,), (second.sha256sums,)),
                ((first.rollback,), (second.rollback,)),
                (first.batch_authorities, second.batch_authorities),
                (first.images, second.images),
            ):
                self.assertEqual(
                    tuple(self._artifact_identity(item, first_output) for item in left),
                    tuple(self._artifact_identity(item, second_output) for item in right),
                )

    def test_failures_at_each_private_build_phase_publish_nothing(self) -> None:
        prefix = _approved_prefix()
        formal_v118 = ROOT / "releases/V1.18"
        formal_v119 = ROOT / "releases/V1.19"
        frozen_before = (
            _tree_fingerprint(formal_v118), _tree_fingerprint(formal_v119),
        )
        writer = importlib.import_module("joy_m2.ingest.v120_writer")
        bad_schema = (
            writer.TASK10_SCHEMA_SQL[0],
            "CREATE TABLE deliberately_invalid(",
            *writer.TASK10_SCHEMA_SQL[2:],
        )
        original_write_bytes = Path.write_bytes

        def fail_during_file_write(path: Path, data: bytes) -> int:
            if path.name == "preflight.json":
                raise OSError("injected authority write failure")
            return original_write_bytes(path, data)

        cases = (
            (
                "before_transaction",
                mock.patch.object(
                    writer, "_populate_database",
                    side_effect=PipelineError("injected before transaction"),
                ),
                PipelineError,
            ),
            (
                "during_transaction",
                mock.patch.object(writer, "TASK10_SCHEMA_SQL", bad_schema),
                sqlite3.OperationalError,
            ),
            (
                "during_file_write",
                mock.patch.object(
                    Path, "write_bytes", autospec=True,
                    side_effect=fail_during_file_write,
                ),
                OSError,
            ),
            (
                "before_verification_completion",
                mock.patch.object(
                    writer, "verify_v120_candidate",
                    return_value=VerificationReport("FAIL", ()),
                ),
                PipelineError,
            ),
            (
                "during_verification",
                mock.patch.object(
                    writer, "verify_v120_candidate",
                    side_effect=PipelineError("injected verifier failure"),
                ),
                PipelineError,
            ),
        )
        for label, patcher, expected in cases:
            with self.subTest(label=label), _output_root() as directory:
                root = Path(directory)
                parent = root / "prior-generation-ab"
                _write_parent_oracle(parent, prefix[:2])
                parent_before = _tree_fingerprint(parent)
                entries_before = tuple(sorted(root.iterdir()))
                output = root / "candidate-abc"
                with patcher, self.assertRaises(expected):
                    build_v120_candidate(
                        V120CandidateBuildRequest(prefix, output, _contract()),
                        PipelineConfig(ROOT),
                    )
                self.assertFalse(output.exists())
                self.assertEqual(tuple(sorted(root.iterdir())), entries_before)
                self.assertEqual(_tree_fingerprint(parent), parent_before)
        self.assertEqual(
            (_tree_fingerprint(formal_v118), _tree_fingerprint(formal_v119)),
            frozen_before,
        )

    def test_adaptations_preserve_batch_order_across_inverse_candidate_ids(self) -> None:
        """Catches verifier-wide sorting that discards semantic batch order."""
        with _output_root() as directory:
            root = Path(directory)
            with closing(sqlite3.connect(_baseline_ref().path)) as database:
                references = tuple(database.execute(
                    "SELECT question_id,source_id,source_question_number,"
                    "source_section,source_fragment_hash "
                    "FROM formal_complete_questions_v119 "
                    "WHERE source_fragment_hash<>'' AND source_image_paths_json='[]' "
                    "ORDER BY formal_order LIMIT 2"
                ))
            self.assertEqual(len(references), 2)

            def adapted_batch(
                letter: str,
                package: Path,
                reference: tuple[str, str, str, str, str],
                candidate_id: str,
                parent: V120CandidateVerificationRequest | None,
            ) -> V120ApprovedBatch:
                shutil.copytree(FIXTURES / f"v120-batch-{letter}", package)
                _remove_declared_images(package)
                _rewrite_record(package, {
                    "proposed_question_id": candidate_id,
                    "source_id": reference[1],
                    "source_question_number": reference[2],
                    "source_section": reference[3],
                    "source_fragment_hash": reference[4],
                    "image_paths": [],
                    "image_roles": [],
                })
                manifest = load_v120_import_manifest(
                    package / "import_manifest.json"
                )
                preflight = preflight_v120_import(
                    V120PreflightRequest(
                        manifest,
                        package,
                        _baseline_ref(),
                        parent,
                        _contract(),
                    ),
                    PipelineConfig(ROOT),
                )
                self.assertEqual(
                    preflight.report.status,
                    "READY FOR USER IMPORT APPROVAL",
                )
                self.assertEqual(
                    tuple(item.candidate_id for item in preflight.report.adaptations),
                    (candidate_id,),
                )
                approval = V120ImportApproval(
                    manifest.batch_id,
                    preflight.report.preflight_sha256,
                    "V1.20",
                    preflight.effective_state.candidate_digest,
                    f"USER APPROVED IMPORT BATCH {manifest.batch_id} "
                    f"{preflight.report.preflight_sha256} V1.20 PARENT "
                    f"{preflight.effective_state.candidate_digest}",
                )
                return V120ApprovedBatch(preflight, package, approval)

            first = adapted_batch(
                "a", root / "package-z", references[0], "Z-ADAPT", None,
            )
            first_output = root / "candidate-z"
            build_v120_candidate(
                V120CandidateBuildRequest((first,), first_output, _contract()),
                PipelineConfig(ROOT),
            )
            parent = V120CandidateVerificationRequest(
                first_output, (first,), _contract(),
            )
            second = adapted_batch(
                "b", root / "package-a", references[1], "A-ADAPT", parent,
            )
            second_output = root / "candidate-za"

            artifacts = build_v120_candidate(
                V120CandidateBuildRequest(
                    (first, second), second_output, _contract(),
                ),
                PipelineConfig(ROOT),
            )

            self.assertEqual(artifacts.verification_report.status, "PASS")
            self.assertEqual(
                verify_v120_candidate(
                    V120CandidateVerificationRequest(
                        second_output, (first, second), _contract(),
                    ),
                    PipelineConfig(ROOT),
                ).status,
                "PASS",
            )

    def test_no_replace_race_cleans_private_tree_and_preserves_destination(self) -> None:
        prefix = _approved_prefix()
        writer = importlib.import_module("joy_m2.ingest.v120_writer")
        with _output_root() as directory:
            root = Path(directory)
            output = root / "candidate-abc"
            existing_bytes = b"concurrent publisher\n"

            def lose_no_replace_race(source: Path, destination: Path) -> None:
                destination.mkdir()
                (destination / "owner.txt").write_bytes(existing_bytes)
                raise OSError(errno.EEXIST, "destination exists", str(destination))

            with mock.patch.object(
                writer, "atomic_rename_no_replace",
                side_effect=lose_no_replace_race,
            ), self.assertRaises(OutputConflictError):
                build_v120_candidate(
                    V120CandidateBuildRequest(prefix, output, _contract()),
                    PipelineConfig(ROOT),
                )

            self.assertEqual(
                self._tree_bytes(output), (("owner.txt", existing_bytes),),
            )
            self.assertFalse(any(
                path.name.startswith(f".{output.name}.tmp-")
                for path in root.iterdir()
            ))

    def test_rollback_is_exact_and_requires_digest_and_complete_closure(self) -> None:
        prefix = _approved_prefix()
        with _output_root() as directory:
            root = Path(directory) / "candidate-abc"
            artifacts = build_v120_candidate(
                V120CandidateBuildRequest(prefix, root, _contract()),
                PipelineConfig(ROOT),
            )
            rollback_path = root / "rollback.json"
            rollback = json.loads(rollback_path.read_text(encoding="utf-8"))
            self.assertEqual(
                tuple(sorted(rollback)),
                (
                    "action", "candidate_artifacts", "candidate_digest",
                    "protected_baseline", "schema_version",
                ),
            )
            self.assertEqual(rollback["schema_version"], "task10-v120-rollback-v1")
            self.assertEqual(
                rollback["action"],
                "delete_unpromoted_v120_candidate_tree_if_digest_matches",
            )
            self.assertEqual(rollback["candidate_digest"], artifacts.state.candidate_digest)
            self.assertEqual(rollback["candidate_artifacts"], sorted(
                path.relative_to(root).as_posix()
                for path in root.rglob("*") if path.is_file()
            ))

            for label, mutate in (
                ("digest", lambda payload: payload.update(candidate_digest="f" * 64)),
                (
                    "closure",
                    lambda payload: payload["candidate_artifacts"].pop(0),
                ),
            ):
                with self.subTest(label=label):
                    rollback_path.write_bytes(_canonical_file(rollback))
                    payload = json.loads(rollback_path.read_text(encoding="utf-8"))
                    mutate(payload)
                    rollback_path.write_bytes(_canonical_file(payload))
                    _rewrite_manifest(
                        root,
                        lambda manifest: manifest.update(
                            rollback=_artifact(rollback_path, root, "rollback"),
                        ),
                    )
                    before = _tree_fingerprint(root)
                    report = verify_v120_candidate(
                        V120CandidateVerificationRequest(root, prefix, _contract()),
                        PipelineConfig(ROOT),
                    )
                    self.assertEqual(report.status, "FAIL")
                    checks = {check.name: check.passed for check in report.checks}
                    self.assertFalse(checks["rollback_contract"])
                    self.assertEqual(_tree_fingerprint(root), before)


class V120VerifierTests(unittest.TestCase):
    """Phase I REDs: independently verify the complete aggregate candidate tree."""

    def _verify(self, request, config):
        try:
            return verify_v120_candidate(request, config)
        except NotImplementedError:
            self.fail("verify_v120_candidate has no behavior implementation")

    def _assert_failed(self, report: VerificationReport, *names: str) -> None:
        self.assertIs(type(report), VerificationReport)
        self.assertEqual(report.status, "FAIL")
        checks = {check.name: check.passed for check in report.checks}
        self.assertEqual(tuple(checks), _CHECK_NAMES)
        for name in names:
            self.assertFalse(checks[name], name)

    def _valid(self, root: Path, count: int = 1):
        approved = _approved_prefix()[:count]
        request = _write_parent_oracle(root, approved)
        return approved, request, PipelineConfig(ROOT)

    def _assert_collision_sql(
        self,
        sql: str,
        parameters: tuple[object, ...] = (),
    ) -> None:
        with _output_root() as directory:
            root = Path(directory) / "candidate-a"
            _, request, config = self._valid(root)
            database_path = root / "Joy_M2_V1.20_candidate.sqlite3"
            with closing(sqlite3.connect(database_path)) as database:
                database.execute(sql, parameters)
                database.commit()
            _refresh_database_artifact(root)
            report = self._verify(request, config)
            self._assert_failed(report, "effective_collision_closure")

    def test_valid_independent_tree_passes_exact_24_checks_without_mutation(self) -> None:
        for count in (1, 2, 3):
            with self.subTest(count=count), _output_root() as directory:
                root = Path(directory) / f"candidate-{count}"
                _, request, config = self._valid(root, count)
                before = _tree_fingerprint(root)
                report = self._verify(request, config)
                self.assertEqual(report.status, "PASS")
                self.assertEqual(tuple(check.name for check in report.checks), _CHECK_NAMES)
                self.assertTrue(all(
                    check.passed and check.detail == "PASS" for check in report.checks
                ))
                self.assertEqual(_tree_fingerprint(root), before)

    def test_copied_formal_baseline_is_not_the_configured_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            copied = repo / "copied-v119"
            shutil.copytree(_baseline_ref().path.parent, copied)
            approved = (
                _with_baseline_path(
                    _approved_prefix()[0],
                    copied / "Joy_M2_Complete_Question_DB_V1_19.sqlite3",
                ),
            )
            root = repo / "data/staging/candidate-a"
            request = _write_parent_oracle(root, approved)
            before = _tree_fingerprint(root)
            report = self._verify(request, PipelineConfig(repo))
            self._assert_failed(report, "baseline_authority", "formal_boundary")
            self.assertEqual(_tree_fingerprint(root), before)

    def test_mutated_formal_rollback_with_refreshed_sums_is_not_exact_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            copied = repo / "releases/V1.19"
            shutil.copytree(_baseline_ref().path.parent, copied)
            rollback = copied / "rollback.json"
            payload = json.loads(rollback.read_text(encoding="utf-8"))
            payload["action"] = "forged-action"
            rollback.write_bytes(_canonical_file(payload))
            _rewrite_formal_sums(copied)
            approved = (
                _with_baseline_path(
                    _approved_prefix()[0],
                    copied / "Joy_M2_Complete_Question_DB_V1_19.sqlite3",
                ),
            )
            root = repo / "data/staging/candidate-a"
            request = _write_parent_oracle(root, approved)
            baseline_before = _tree_fingerprint(copied)
            candidate_before = _tree_fingerprint(root)
            report = self._verify(request, PipelineConfig(repo))
            self._assert_failed(report, "baseline_authority", "formal_boundary")
            self.assertEqual(_tree_fingerprint(copied), baseline_before)
            self.assertEqual(_tree_fingerprint(root), candidate_before)

    def test_crlf_sha256sums_is_a_structured_nonmutating_failure(self) -> None:
        with _output_root() as directory:
            root = Path(directory) / "candidate-a"
            _, request, config = self._valid(root)
            sums = root / "SHA256SUMS"
            sums.write_bytes(sums.read_bytes().replace(b"\n", b"\r\n"))
            before = _tree_fingerprint(root)
            report = self._verify(request, config)
            self._assert_failed(report, "sha256sums_closure", "deterministic_identity")
            self.assertEqual(_tree_fingerprint(root), before)

    def test_missing_root_raises_input_missing(self) -> None:
        approved = _approved_prefix()[:1]
        with _output_root() as directory:
            missing = Path(directory) / "missing"
            request = V120CandidateVerificationRequest(missing, approved, _contract())
            with self.assertRaises(InputMissingError):
                self._verify(request, PipelineConfig(ROOT))

    def test_malformed_json_is_input_format_error_and_never_mutates(self) -> None:
        for relative in (
            "candidate_manifest.json",
            "rollback.json",
            "authority/batches/000001/TASK10-A/preflight.json",
            "authority/batches/000001/TASK10-A/approval.json",
        ):
            with self.subTest(relative=relative), _output_root() as directory:
                root = Path(directory) / "candidate-a"
                _, request, config = self._valid(root)
                (root / relative).write_bytes(b"{not-json\n")
                before = _tree_fingerprint(root)
                with self.assertRaises(InputFormatError):
                    self._verify(request, config)
                self.assertEqual(_tree_fingerprint(root), before)

    def test_parsed_invalid_json_returns_structured_fail_without_mutation(self) -> None:
        cases = (
            ("candidate_manifest.json", {}, "candidate_contract"),
            ("rollback.json", {}, "rollback_contract"),
            ("authority/batches/000001/TASK10-A/preflight.json", {}, "preflight_reconstruction"),
            ("authority/batches/000001/TASK10-A/approval.json", {}, "approval_binding"),
        )
        for relative, payload, check in cases:
            with self.subTest(relative=relative), _output_root() as directory:
                root = Path(directory) / "candidate-a"
                _, request, config = self._valid(root)
                (root / relative).write_bytes(_canonical_file(payload))
                _rewrite_sums(root)
                before = _tree_fingerprint(root)
                report = self._verify(request, config)
                self._assert_failed(report, check)
                self.assertEqual(_tree_fingerprint(root), before)

    def test_missing_extra_and_tampered_artifacts_are_structured_failures(self) -> None:
        mutations = (
            ("missing", lambda root: (root / "rollback.json").unlink(), "filesystem_closure"),
            ("extra", lambda root: (root / "rogue.bin").write_bytes(b"rogue"), "filesystem_closure"),
            ("tampered", lambda root: next((root / "images").rglob("*.svg")).write_bytes(b"tampered"), "sha256sums_closure"),
        )
        for label, mutate, check in mutations:
            with self.subTest(label=label), _output_root() as directory:
                root = Path(directory) / "candidate-a"
                _, request, config = self._valid(root)
                mutate(root)
                before = _tree_fingerprint(root)
                report = self._verify(request, config)
                self._assert_failed(report, check)
                self.assertEqual(_tree_fingerprint(root), before)

    def test_wrong_artifact_reference_is_rejected_even_when_sums_are_refreshed(self) -> None:
        with _output_root() as directory:
            root = Path(directory) / "candidate-a"
            _, request, config = self._valid(root)
            _rewrite_manifest(root, lambda manifest: manifest["database"].update(sha256="f" * 64))
            report = self._verify(request, config)
            self._assert_failed(report, "artifact_references")

    def test_sqlite_integrity_foreign_key_schema_and_row_failures_are_independent(self) -> None:
        def corrupt(root: Path) -> None:
            path = root / "Joy_M2_V1.20_candidate.sqlite3"
            path.write_bytes(path.read_bytes()[:4096])

        def foreign_key(root: Path) -> None:
            path = root / "Joy_M2_V1.20_candidate.sqlite3"
            with closing(sqlite3.connect(path)) as database:
                database.execute("PRAGMA foreign_keys=OFF")
                database.execute("DELETE FROM task10_v120_batch_ledger_v1")
                database.commit()

        def schema(root: Path) -> None:
            with closing(sqlite3.connect(root / "Joy_M2_V1.20_candidate.sqlite3")) as database:
                database.execute("CREATE TABLE rogue_task10_object(value TEXT)")
                database.commit()

        def row(root: Path) -> None:
            with closing(sqlite3.connect(root / "Joy_M2_V1.20_candidate.sqlite3")) as database:
                database.execute("UPDATE task10_v120_candidates_v1 SET question_text_original='changed'")
                database.commit()

        cases = (
            ("integrity", corrupt, "sqlite_integrity"),
            ("foreign", foreign_key, "sqlite_foreign_keys"),
            ("schema", schema, "sqlite_schema"),
            ("row", row, "candidate_projection"),
        )
        for label, mutate, check in cases:
            with self.subTest(label=label), _output_root() as directory:
                root = Path(directory) / "candidate-a"
                _, request, config = self._valid(root)
                mutate(root)
                _refresh_database_artifact(root)
                report = self._verify(request, config)
                self._assert_failed(report, check)

    def test_noncontiguous_ledger_and_wrong_parent_chain_are_rejected(self) -> None:
        with _output_root() as directory:
            root = Path(directory) / "candidate-a"
            _, request, config = self._valid(root)
            path = root / "Joy_M2_V1.20_candidate.sqlite3"
            with closing(sqlite3.connect(path)) as database:
                database.execute("PRAGMA foreign_keys=OFF")
                database.execute("UPDATE task10_v120_images_v1 SET batch_ordinal=2")
                database.execute("UPDATE task10_v120_candidates_v1 SET batch_ordinal=2")
                database.execute("UPDATE task10_v120_taxonomy_v1 SET batch_ordinal=2")
                database.execute("UPDATE task10_v120_batch_ledger_v1 SET batch_ordinal=2")
                database.commit()
            _refresh_database_artifact(root)
            self._assert_failed(self._verify(request, config), "batch_ledger")

        with _output_root() as directory:
            root = Path(directory) / "candidate-a"
            _, request, config = self._valid(root)
            _rewrite_manifest(
                root,
                lambda manifest: manifest["batch_ledger"][0].update(parent_candidate_digest="f" * 64),
            )
            self._assert_failed(self._verify(request, config), "parent_chain")

    def test_wrong_preflight_and_approval_authority_are_rejected(self) -> None:
        cases = (
            ("preflight.json", "payload", "preflight_reconstruction"),
            ("approval.json", "statement", "approval_binding"),
        )
        for filename, key, check in cases:
            with self.subTest(filename=filename), _output_root() as directory:
                root = Path(directory) / "candidate-a"
                _, request, config = self._valid(root)
                path = root / "authority/batches/000001/TASK10-A" / filename
                payload = json.loads(path.read_text(encoding="utf-8"))
                if key == "payload":
                    payload[key]["batch_id"] = "OTHER"
                else:
                    payload[key] = "forged"
                path.write_bytes(_canonical_file(payload))
                _rewrite_sums(root)
                self._assert_failed(self._verify(request, config), check)

    def test_v119_inherited_row_mutation_is_rejected_independently(self) -> None:
        with _output_root() as directory:
            root = Path(directory) / "candidate-a"
            _, request, config = self._valid(root)
            database_path = root / "Joy_M2_V1.20_candidate.sqlite3"
            with closing(sqlite3.connect(database_path)) as database:
                database.execute(
                    "UPDATE complete_questions_v2 "
                    "SET audit_notes=COALESCE(audit_notes,'') || '[mutated]' "
                    "WHERE question_id=(SELECT question_id FROM complete_questions_v2 "
                    "ORDER BY question_id LIMIT 1)"
                )
                database.commit()
            _refresh_database_artifact(root)
            self._assert_failed(self._verify(request, config), "v119_preservation")

    def test_candidate_id_collision_leakage_is_rejected(self) -> None:
        self._assert_collision_sql(
            "UPDATE task10_v120_candidates_v1 SET proposed_question_id=("
            "SELECT question_id FROM formal_complete_questions_v119 "
            "ORDER BY formal_order LIMIT 1)"
        )

    def test_source_locator_collision_leakage_is_rejected(self) -> None:
        self._assert_collision_sql(
            "UPDATE task10_v120_candidates_v1 SET "
            "source_id=(SELECT source_id FROM formal_complete_questions_v119 "
            "ORDER BY formal_order LIMIT 1),"
            "source_question_number=(SELECT source_question_number "
            "FROM formal_complete_questions_v119 ORDER BY formal_order LIMIT 1),"
            "source_section=(SELECT source_section FROM formal_complete_questions_v119 "
            "ORDER BY formal_order LIMIT 1)"
        )

    def test_fragment_collision_leakage_is_rejected(self) -> None:
        self._assert_collision_sql(
            "UPDATE task10_v120_candidates_v1 SET source_fragment_hash=("
            "SELECT source_fragment_hash FROM formal_complete_questions_v119 "
            "WHERE source_fragment_hash IS NOT NULL ORDER BY formal_order LIMIT 1)"
        )

    def test_normalized_text_collision_leakage_is_rejected(self) -> None:
        self._assert_collision_sql(
            "UPDATE task10_v120_candidates_v1 SET normalized_text_sha256=("
            "SELECT normalized_text_sha256 FROM formal_complete_questions_v119 "
            "WHERE normalized_text_sha256 IS NOT NULL ORDER BY formal_order LIMIT 1)"
        )

    def test_image_binding_collision_leakage_is_rejected(self) -> None:
        self.assertNotEqual(SHARED_IMAGE_SHA, FORMAL_IMAGE_SHA)
        self._assert_collision_sql(
            "UPDATE task10_v120_candidates_v1 SET image_paths_json=?,"
            "image_sha256s_json=?,image_roles_json=?",
            (
                json.dumps((FORMAL_IMAGE_PATH,), separators=(",", ":")),
                json.dumps((SHARED_IMAGE_SHA,), separators=(",", ":")),
                json.dumps((FORMAL_IMAGE_ROLE,), separators=(",", ":")),
            ),
        )

    def test_wrong_counts_and_candidate_digest_are_rejected(self) -> None:
        cases = (
            ("count", lambda manifest: manifest["counts"].update(new_candidate_count=2), "count_closure"),
            ("digest", lambda manifest: manifest.update(candidate_digest="f" * 64), "candidate_digest"),
        )
        for label, update, check in cases:
            with self.subTest(label=label), _output_root() as directory:
                root = Path(directory) / "candidate-a"
                _, request, config = self._valid(root)
                _rewrite_manifest(root, update)
                self._assert_failed(self._verify(request, config), check)

    def test_release_v120_path_is_always_a_structured_formal_boundary_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            root = repo / "releases/V1.20/candidate"
            approved = _approved_prefix()[:1]
            request = _write_parent_oracle(root, approved)
            report = self._verify(request, PipelineConfig(repo))
            self._assert_failed(report, "formal_boundary")

    def test_candidate_root_symlink_leaf_ancestor_loop_and_escape_fail_without_mutation(self) -> None:
        with _output_root() as directory:
            base = Path(directory)
            target = base / "real-candidate"
            approved, request, config = self._valid(target)
            before = _tree_fingerprint(target)

            leaf = base / "leaf"
            leaf.symlink_to(target, target_is_directory=True)
            leaf_request = _forged(request, candidate_dir=leaf)
            self._assert_failed(self._verify(leaf_request, config), "candidate_directory", "formal_boundary")

            ancestor = base / "ancestor"
            ancestor.symlink_to(target.parent, target_is_directory=True)
            ancestor_request = _forged(request, candidate_dir=ancestor / target.name)
            self._assert_failed(self._verify(ancestor_request, config), "candidate_directory", "formal_boundary")

            loop = base / "loop"
            loop.symlink_to(loop, target_is_directory=True)
            loop_request = _forged(request, candidate_dir=loop)
            self._assert_failed(self._verify(loop_request, config), "candidate_directory", "formal_boundary")
            self.assertEqual(_tree_fingerprint(target), before)

        with tempfile.TemporaryDirectory() as directory, _output_root() as candidate_directory:
            repo = Path(directory) / "repo"
            staging = repo / "data/staging"
            staging.mkdir(parents=True)
            outside = Path(candidate_directory) / "outside"
            approved = _approved_prefix()[:1]
            request = _write_parent_oracle(outside, approved)
            link = staging / "escape"
            link.symlink_to(outside, target_is_directory=True)
            escaped = _forged(request, candidate_dir=link)
            self._assert_failed(
                self._verify(escaped, PipelineConfig(repo)),
                "candidate_directory", "formal_boundary",
            )

    def test_public_verification_request_preserves_symlink_root_for_rejection(self) -> None:
        with _output_root() as directory:
            base = Path(directory)
            physical = base / "physical-candidate"
            approved, _, config = self._valid(physical)
            before = _tree_fingerprint(physical)
            alias = base / "candidate-alias"
            alias.symlink_to(physical, target_is_directory=True)

            request = V120CandidateVerificationRequest(alias, approved, _contract())
            self._assert_failed(
                self._verify(request, config),
                "candidate_directory",
                "formal_boundary",
            )
            self.assertEqual(_tree_fingerprint(physical), before)

    def test_configured_staging_root_symlink_is_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            formal = repo / "releases/V1.19"
            shutil.copytree(_baseline_ref().path.parent, formal)
            actual_staging = repo / "actual-staging"
            actual_staging.mkdir(parents=True)
            (repo / "data").mkdir()
            staging = repo / "data/staging"
            staging.symlink_to(actual_staging, target_is_directory=True)
            approved = (
                _with_baseline_path(
                    _approved_prefix()[0],
                    formal / "Joy_M2_Complete_Question_DB_V1_19.sqlite3",
                ),
            )
            root = staging / "candidate-a"
            request = _write_parent_oracle(root, approved)
            before = _tree_fingerprint(actual_staging)

            report = self._verify(request, PipelineConfig(repo))

            self._assert_failed(report, "candidate_directory", "formal_boundary")
            self.assertEqual(_tree_fingerprint(actual_staging), before)

    def test_forged_pipeline_config_cannot_authorize_outside_staging(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outside = Path(directory)
            root = outside / "candidate-a"
            approved = _approved_prefix()[:1]
            request = _write_parent_oracle(root, approved)
            before = _tree_fingerprint(root)
            config = PipelineConfig(ROOT)
            object.__setattr__(config, "staging_root", outside)

            with self.assertRaises(PipelineError):
                self._verify(request, config)

            self.assertEqual(_tree_fingerprint(root), before)

    def test_forged_verification_request_tuple_cannot_authorize_candidate(self) -> None:
        with _output_root() as directory:
            root = Path(directory) / "candidate-a"
            _, request, config = self._valid(root)
            object.__setattr__(request, "approved_batches", list(request.approved_batches))
            before = _tree_fingerprint(root)

            with self.assertRaises(PipelineError):
                self._verify(request, config)

            self.assertEqual(_tree_fingerprint(root), before)

    def test_forged_nested_approval_carrier_is_a_structured_failure(self) -> None:
        with _output_root() as directory:
            root = Path(directory) / "candidate-a"
            approved, request, config = self._valid(root)
            forged_approval = SimpleNamespace(**approved[0].approval.__dict__)
            forged_batch = _forged(approved[0], approval=forged_approval)
            forged_request = _forged(request, approved_batches=(forged_batch,))
            before = _tree_fingerprint(root)

            report = self._verify(forged_request, config)

            self._assert_failed(report, "approval_binding", "preflight_reconstruction")
            self.assertEqual(_tree_fingerprint(root), before)

    def test_exact_typed_inconsistent_preflight_report_is_rejected(self) -> None:
        approved_a, approved_b, _ = _approved_prefix()
        old_report = approved_b.preflight_result.report
        inconsistent_report = replace(
            old_report,
            detected_count=2,
            new_candidate_count=2,
            projected_after_count=505,
            proposed_ids=("TASK10-B-001", "TASK10-B-GHOST"),
        )
        provisional_result = replace(
            approved_b.preflight_result, report=inconsistent_report,
        )
        provisional_approval = replace(
            approved_b.approval,
            preflight_sha256=inconsistent_report.preflight_sha256,
            statement=(
                f"USER APPROVED IMPORT BATCH TASK10-B "
                f"{inconsistent_report.preflight_sha256} V1.20 PARENT {A_CANDIDATE_DIGEST}"
            ),
        )
        provisional = V120ApprovedBatch(
            provisional_result, approved_b.package_root, provisional_approval,
        )
        preflight_sha = hashlib.sha256(
            _canonical_file(_preflight_payload(provisional))
        ).hexdigest()
        report = replace(inconsistent_report, preflight_sha256=preflight_sha)
        result = replace(provisional_result, report=report)
        approval = V120ImportApproval(
            "TASK10-B",
            preflight_sha,
            "V1.20",
            A_CANDIDATE_DIGEST,
            f"USER APPROVED IMPORT BATCH TASK10-B {preflight_sha} "
            f"V1.20 PARENT {A_CANDIDATE_DIGEST}",
        )
        forged_b = V120ApprovedBatch(result, approved_b.package_root, approval)

        with _output_root() as directory:
            root = Path(directory) / "candidate-ab"
            request = _write_parent_oracle(root, (approved_a, approved_b))
            forged_request = _forged(
                request, approved_batches=(approved_a, forged_b),
            )
            before = _tree_fingerprint(root)

            verification = self._verify(forged_request, PipelineConfig(ROOT))

            self._assert_failed(verification, "preflight_reconstruction")
            self.assertEqual(_tree_fingerprint(root), before)

    def test_external_lexical_symlink_ancestor_into_staging_fails_verification(self) -> None:
        with _output_root() as staging_directory, tempfile.TemporaryDirectory() as alias_directory:
            staging = Path(staging_directory)
            physical = staging / "physical/candidate-a"
            _, request, config = self._valid(physical)
            before = _tree_fingerprint(physical)
            alias = Path(alias_directory) / "alias"
            alias.symlink_to(physical.parent, target_is_directory=True)
            aliased_request = _forged(
                request, candidate_dir=alias / physical.name,
            )

            report = self._verify(aliased_request, config)

            self._assert_failed(report, "candidate_directory", "formal_boundary")
            self.assertEqual(_tree_fingerprint(physical), before)

    def test_candidate_nested_inside_another_candidate_fails_formal_boundary(self) -> None:
        approved_a, approved_b, _ = _approved_prefix()
        with _output_root() as directory:
            root = Path(directory)
            parent = root / "candidate-a"
            _write_parent_oracle(parent, (approved_a,))
            child = parent / "candidate-ab"
            child_request = _write_parent_oracle(child, (approved_a, approved_b))
            before = _tree_fingerprint(child)

            report = self._verify(child_request, PipelineConfig(ROOT))

            self._assert_failed(report, "formal_boundary")
            self.assertEqual(_tree_fingerprint(child), before)

    def test_symlinked_artifact_is_structured_fail_and_never_repaired(self) -> None:
        with _output_root() as directory:
            root = Path(directory) / "candidate-a"
            _, request, config = self._valid(root)
            image = next((root / "images").rglob("*.svg"))
            saved = Path(directory) / "saved.svg"
            saved.write_bytes(image.read_bytes())
            image.unlink()
            image.symlink_to(saved)
            before_target = hashlib.sha256(saved.read_bytes()).hexdigest()
            report = self._verify(request, config)
            self._assert_failed(report, "filesystem_closure", "formal_boundary")
            self.assertTrue(image.is_symlink())
            self.assertEqual(hashlib.sha256(saved.read_bytes()).hexdigest(), before_target)

    def test_verifier_is_independent_of_writer_and_production_preflight(self) -> None:
        from unittest import mock

        with _output_root() as directory:
            root = Path(directory) / "candidate-a"
            _, request, config = self._valid(root)
            with mock.patch(
                "joy_m2.ingest.v120_writer.build_v120_candidate",
                side_effect=AssertionError("writer must not be called"),
            ), mock.patch(
                "joy_m2.ingest.v120_preflight.preflight_v120_import",
                side_effect=AssertionError("preflight must not be called"),
            ):
                report = self._verify(request, config)
            self.assertEqual(report.status, "PASS")


if __name__ == "__main__":
    unittest.main()
