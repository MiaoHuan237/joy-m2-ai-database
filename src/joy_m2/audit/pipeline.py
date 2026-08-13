"""Maintained audit pipeline boundary."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from ..errors import BaselineMismatchError, InputFormatError, InputMissingError
from ..models import (
    ArtifactRef,
    AuditInputEvidence,
    AuditIssue,
    AuditReport,
    AuditRequest,
    AuditResult,
)
from .profiles import parse_v117_record, parse_v118_record


V116_BASELINE_OBJECTS = {
    "question_topics": "table",
    "questions": "table",
    "sources": "table",
    "topics": "table",
    "complete_questions": "view",
    "selectable_questions": "view",
}

V117_BASELINE_OBJECTS = V116_BASELINE_OBJECTS | {
    "complete_question_corrections_v2": "table",
    "complete_question_tags_v2": "table",
    "complete_question_taxonomy_v2": "table",
    "complete_questions_v2": "table",
    "import_runs_v2": "table",
    "release_metadata_v2": "table",
    "selectable_complete_questions_v2": "view",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_candidate(path: Path) -> tuple[ArtifactRef, bytes]:
    if not path.exists():
        raise InputMissingError(f"candidate JSON does not exist: {path}")
    if not path.is_file():
        raise InputFormatError(f"candidate JSON is not a regular file: {path}")
    try:
        content = path.read_bytes()
    except OSError as error:
        raise InputFormatError("candidate JSON cannot be read") from error
    return (
        ArtifactRef(path, hashlib.sha256(content).hexdigest(), len(content), "json"),
        content,
    )


def _require_asset_root(path: Path) -> None:
    if not path.exists():
        raise InputMissingError(f"asset root does not exist: {path}")
    if not path.is_dir():
        raise InputFormatError(f"asset root is not a directory: {path}")


def _require_baseline(
    expected: ArtifactRef,
    profile: str,
    selected_source_ids: tuple[str, ...],
) -> dict[str, str]:
    path = expected.path
    if not path.exists() or not path.is_file():
        raise BaselineMismatchError(f"baseline database is missing: {path}")
    if expected.kind != "sqlite":
        raise BaselineMismatchError("baseline database kind must be 'sqlite'")
    if path.stat().st_size != expected.size_bytes or _sha256(path) != expected.sha256:
        raise BaselineMismatchError("baseline database identity does not match")

    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
            if database.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise InputFormatError("baseline database integrity check failed")
            objects = {
                name: object_type
                for name, object_type in database.execute(
                    "SELECT name, type FROM sqlite_master "
                    "WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'"
                )
            }
            if profile == "V1.18":
                metadata = dict(
                    database.execute(
                        "SELECT key, value FROM release_metadata_v2 "
                        "WHERE key IN ('release_version', 'baseline_version', 'schema_version')"
                    )
                ) if "release_metadata_v2" in objects else {}
                if (
                    database.execute("PRAGMA user_version").fetchone()[0] != 117
                    or objects != V117_BASELINE_OBJECTS
                    or metadata
                    != {
                        "release_version": "V1.17",
                        "baseline_version": "V1.16",
                        "schema_version": "complete-question-v1.0",
                    }
                ):
                    raise BaselineMismatchError(
                        "V1.18 audit requires a V1.17 baseline database"
                    )
                if (
                    database.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
                    != 1517
                    or database.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
                    != 24
                    or database.execute(
                        "SELECT COUNT(*) FROM complete_questions_v2"
                    ).fetchone()[0]
                    != 45
                    or database.execute(
                        "SELECT COUNT(*) FROM complete_questions"
                    ).fetchone()[0]
                    != 497
                ):
                    raise BaselineMismatchError(
                        "V1.17 baseline database record counts do not match"
                    )
                rows = database.execute(
                    "SELECT question_text_original, question_id FROM complete_questions_v2"
                )
            else:
                if (
                    database.execute("PRAGMA user_version").fetchone()[0] != 0
                    or objects != V116_BASELINE_OBJECTS
                ):
                    raise BaselineMismatchError(
                        "V1.17 audit requires a V1.16 baseline database"
                    )
                if (
                    database.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
                    != 1517
                    or database.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
                    != 24
                    or database.execute(
                        "SELECT COUNT(*) FROM complete_questions"
                    ).fetchone()[0]
                    != 497
                ):
                    raise BaselineMismatchError(
                        "V1.16 baseline database record count does not match"
                    )
                placeholders = ",".join("?" for _ in selected_source_ids)
                query = "SELECT question_text_original, question_id FROM complete_questions"
                parameters = ()
                if selected_source_ids:
                    query += f" WHERE source_id NOT IN ({placeholders})"
                    parameters = selected_source_ids
                rows = database.execute(query, parameters)
            return {_normalized_text(text): question_id for text, question_id in rows}
    except (BaselineMismatchError, InputFormatError):
        raise
    except sqlite3.Error as error:
        raise InputFormatError("baseline database cannot be read") from error


def _load_candidate(content: bytes) -> list[object]:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise InputFormatError("candidate JSON cannot be decoded") from error
    if type(value) is not list:
        raise InputFormatError("candidate JSON must contain a record array")
    return value


def _normalized_text(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def _validate_contract(records, request: AuditRequest) -> None:
    contract = request.contract
    answer_counts = tuple(
        sorted(Counter(record.question.answer_status for record in records).items())
    )
    source_ids = {record.question.source_id for record in records}
    question_ids = [record.question.question_id for record in records]
    if len(records) != contract.expected_question_count:
        raise InputFormatError("candidate count does not match the audit profile")
    if len(source_ids) != contract.expected_source_count:
        raise InputFormatError("candidate source count does not match the audit profile")
    if len(set(question_ids)) != len(question_ids):
        raise InputFormatError("candidate question ids must be unique")
    if answer_counts != tuple(sorted(contract.expected_answer_status_counts)):
        raise InputFormatError("candidate answer counts do not match the audit profile")
    if source_ids != set(request.selected_source_ids):
        raise InputFormatError("candidate sources do not match selected_source_ids")
    if any(record.question.schema_version != contract.schema_version for record in records):
        raise InputFormatError("candidate schema version does not match the audit profile")


def _audit_issues(records, request: AuditRequest, normalized_seen: dict[str, str]):
    issues = []
    allowed_tags = set(request.contract.allowed_tags)
    asset_root = request.asset_root.resolve()
    for record in records:
        question = record.question
        if not question.question_text_original.strip():
            issues.append(
                AuditIssue(
                    "missing_question_text",
                    "blocker",
                    question.question_id,
                    "question_text_original",
                    "empty",
                )
            )
        if question.difficulty_level not in range(1, 6):
            issues.append(
                AuditIssue(
                    "invalid_difficulty",
                    "blocker",
                    question.question_id,
                    "difficulty_level",
                    str(question.difficulty_level),
                )
            )
        if (
            question.answer_status != "missing_from_source"
            and not question.solution_verified.strip()
        ):
            issues.append(
                AuditIssue(
                    "missing_solution",
                    "blocker",
                    question.question_id,
                    "solution_verified",
                    question.answer_status,
                )
            )
        for image in question.image_paths:
            declared_path = Path(image.path)
            resolved_path = (asset_root / declared_path).resolve()
            try:
                resolved_path.relative_to(asset_root)
                inside_asset_root = not declared_path.is_absolute()
            except ValueError:
                inside_asset_root = False
            if not inside_asset_root or not resolved_path.is_file():
                issues.append(
                    AuditIssue(
                        "missing_image",
                        "blocker",
                        question.question_id,
                        "image_paths",
                        image.path,
                    )
                )
        normalized = _normalized_text(question.question_text_original)
        if normalized in normalized_seen:
            duplicate_id = normalized_seen[normalized]
            issues.append(
                AuditIssue(
                    "exact_duplicate",
                    "blocker",
                    question.question_id,
                    "question_text_original",
                    duplicate_id,
                )
            )
        normalized_seen[normalized] = question.question_id
        for tag in question.tags:
            if tag not in allowed_tags:
                issues.append(
                    AuditIssue(
                        "invalid_tag",
                        "blocker",
                        question.question_id,
                        "tags",
                        tag,
                    )
                )
    return tuple(issues)


def audit_batch(request: AuditRequest) -> AuditResult:
    """Audit one explicit JSON candidate against one explicit baseline database."""

    candidate_json, candidate_bytes = _require_candidate(request.candidate_path)
    _require_asset_root(request.asset_root)
    normalized_seen = _require_baseline(
        request.baseline_database,
        request.contract.profile,
        request.selected_source_ids,
    )
    raw_records = _load_candidate(candidate_bytes)
    parser = {
        "V1.17": parse_v117_record,
        "V1.18": parse_v118_record,
    }[request.contract.profile]
    records = tuple(parser(record) for record in raw_records)
    _validate_contract(records, request)

    issues = _audit_issues(records, request, normalized_seen)
    answer_status_counts = tuple(
        sorted(Counter(record.question.answer_status for record in records).items())
    )
    blocker_ids = {
        issue.question_id for issue in issues if issue.severity == "blocker"
    }
    exact_duplicate_ids = {
        issue.question_id
        for issue in issues
        if issue.severity == "blocker" and issue.code == "exact_duplicate"
    }
    source_counts = tuple(
        sorted(Counter(record.question.source_id for record in records).items())
    )
    status = "failed" if issues else "passed"
    report = AuditReport(
        release_version=request.contract.release_version,
        status=status,
        candidate_count=len(records),
        source_count=len(source_counts),
        audit_passed=len(records) - len(blocker_ids),
        audit_pending=0,
        blocked=len(blocker_ids),
        exact_duplicate_count=len(exact_duplicate_ids),
        answer_status_counts=answer_status_counts,
        image_reference_count=sum(
            len(record.question.image_paths) for record in records
        ),
        source_counts=source_counts,
    )
    return AuditResult(
        records=records,
        issues=issues,
        answer_status_counts=answer_status_counts,
        status=status,
        report=report,
        input_evidence=AuditInputEvidence(
            candidate_json=candidate_json,
            baseline_database=request.baseline_database,
        ),
    )
