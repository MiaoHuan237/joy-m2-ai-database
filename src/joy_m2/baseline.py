from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any


DB_NAME = "Joy_M2_Complete_Question_DB_V1_18.sqlite3"
CSV_NAME = "Joy_M2_Complete_Questions_V1_18.csv"
MARKDOWN_NAME = "Joy_M2_完整题497题_知识文档_V1.18.md"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_hashes(release_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    manifest = json.loads((release_dir / "manifest.json").read_text(encoding="utf-8"))
    sums: dict[str, str] = {}
    for line in (release_dir / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        sums[name] = digest
    return manifest, sums


def verify_baseline(release_dir: Path) -> dict[str, Any]:
    release_dir = Path(release_dir).resolve()
    manifest, sums = _read_hashes(release_dir)
    protected = {
        path.name
        for path in release_dir.iterdir()
        if path.is_file() and path.name != "SHA256SUMS.txt"
    }
    manifest_hashes = manifest["artifact_sha256"]
    manifest_hashes_valid = all(
        (release_dir / name).is_file() and _sha256(release_dir / name) == expected
        for name, expected in manifest_hashes.items()
    )
    sum_hashes_valid = set(sums) == protected and all(
        (release_dir / name).is_file() and _sha256(release_dir / name) == expected
        for name, expected in sums.items()
    )

    db_path = release_dir / DB_NAME
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_key_error_count = len(db.execute("PRAGMA foreign_key_check").fetchall())
        user_version = db.execute("PRAGMA user_version").fetchone()[0]
        db_rows = [
            dict(row)
            for row in db.execute("SELECT * FROM complete_questions_v2 ORDER BY question_id")
        ]
        unique_question_count = db.execute(
            "SELECT COUNT(DISTINCT question_id) FROM complete_questions_v2"
        ).fetchone()[0]
        task6_question_count = db.execute(
            "SELECT COUNT(*) FROM complete_questions_v2 WHERE source_order > 45"
        ).fetchone()[0]
        existing_v117_question_count = db.execute(
            "SELECT COUNT(*) FROM complete_questions_v2 WHERE source_order <= 45"
        ).fetchone()[0]
        selectable_question_count = db.execute(
            "SELECT COUNT(*) FROM selectable_complete_questions_v2"
        ).fetchone()[0]
        invalid_selectable_count = db.execute(
            """
            SELECT COUNT(*)
            FROM selectable_complete_questions_v2
            WHERE record_status <> 'published'
               OR joy_approval <> 'approved_by_joy'
               OR selectable <> 1
            """
        ).fetchone()[0]
        legacy_counts = {
            table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("questions", "sources", "topics")
        }
        answer_status_counts = dict(
            db.execute(
                "SELECT answer_status, COUNT(*) FROM complete_questions_v2 GROUP BY answer_status"
            )
        )
        difficulty_counts = {
            str(level): count
            for level, count in db.execute(
                "SELECT difficulty_level, COUNT(*) FROM complete_questions_v2 GROUP BY difficulty_level"
            )
        }
        correction_count = db.execute(
            "SELECT COUNT(*) FROM complete_question_corrections_v2"
        ).fetchone()[0]
        exact_duplicate_count = db.execute(
            "SELECT COUNT(*) FROM complete_questions_v2 WHERE duplicate_status = 'exact_duplicate'"
        ).fetchone()[0]

    with (release_dir / CSV_NAME).open("r", encoding="utf-8-sig", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    csv_exact = len(csv_rows) == len(db_rows)
    if csv_exact:
        for db_row, csv_row in zip(db_rows, csv_rows, strict=True):
            expected = {key: "" if value is None else str(value) for key, value in db_row.items()}
            if csv_row != expected:
                csv_exact = False
                break

    markdown = (release_dir / MARKDOWN_NAME).read_text(encoding="utf-8")
    markdown_question_count = len(
        re.findall(r"^### \d+\. `[^`]+`$", markdown, flags=re.MULTILINE)
    )
    markdown_missing_answer_count = markdown.count("答案状态：`missing_from_source`")
    audit_records = json.loads(
        (release_dir / "complete_questions_452_task6_audited.json").read_text(encoding="utf-8")
    )
    audit_report = json.loads(
        (release_dir / "task6_audit_report.json").read_text(encoding="utf-8")
    )

    checks = {
        "protected_file_set": set(sums) == protected,
        "manifest_hashes": manifest_hashes_valid,
        "sha256sums": sum_hashes_valid,
        "sqlite_integrity": integrity == "ok",
        "sqlite_foreign_keys": foreign_key_error_count == 0,
        "schema_version": user_version == 118,
        "question_counts": len(db_rows) == unique_question_count == selectable_question_count == 497,
        "migration_counts": task6_question_count == 452 and existing_v117_question_count == 45,
        "selectable_contract": invalid_selectable_count == 0,
        "legacy_counts": legacy_counts == {"questions": 1517, "sources": 24, "topics": 12},
        "answer_status_counts": answer_status_counts
        == {"source_provided": 392, "ai_solved_verified": 71, "missing_from_source": 34},
        "difficulty_counts": difficulty_counts
        == {"1": 11, "2": 54, "3": 140, "4": 190, "5": 102},
        "correction_count": correction_count == 59,
        "exact_duplicate_count": exact_duplicate_count == 0,
        "csv_exact": csv_exact,
        "markdown_counts": markdown_question_count == 497 and markdown_missing_answer_count == 34,
        "audit_counts": len(audit_records) == 452
        and audit_report.get("audit_passed") == 452
        and audit_report.get("audit_pending") == 0
        and audit_report.get("blocked") == 0,
        "release_manifest": manifest.get("release_version") == "V1.18"
        and manifest.get("release_status") == "formal"
        and manifest.get("complete_question_count") == 497,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "integrity_check": integrity,
        "foreign_key_error_count": foreign_key_error_count,
        "question_count": len(db_rows),
        "unique_question_count": unique_question_count,
        "task6_question_count": task6_question_count,
        "existing_v117_question_count": existing_v117_question_count,
        "selectable_question_count": selectable_question_count,
        "legacy_counts": legacy_counts,
        "answer_status_counts": answer_status_counts,
        "difficulty_counts": difficulty_counts,
        "correction_count": correction_count,
        "exact_duplicate_count": exact_duplicate_count,
        "csv_row_count": len(csv_rows),
        "markdown_question_count": markdown_question_count,
        "markdown_missing_answer_count": markdown_missing_answer_count,
        "audit_record_count": len(audit_records),
    }
