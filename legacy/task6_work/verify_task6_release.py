from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_release(release_dir: Path) -> dict[str, Any]:
    manifest = json.loads((release_dir / "manifest.json").read_text(encoding="utf-8"))
    hash_errors: list[str] = []
    for name, expected in manifest["artifact_sha256"].items():
        path = release_dir / name
        if not path.is_file() or sha256_file(path) != expected:
            hash_errors.append(name)

    sums: dict[str, str] = {}
    for line in (release_dir / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        sums[name] = digest
    protected = {
        path.name for path in release_dir.iterdir()
        if path.is_file() and path.name != "SHA256SUMS.txt"
    }
    if set(sums) != protected:
        hash_errors.append("SHA256SUMS.txt:file-set")
    for name, expected in sums.items():
        path = release_dir / name
        if not path.is_file() or sha256_file(path) != expected:
            hash_errors.append(f"SHA256SUMS.txt:{name}")

    db_path = release_dir / "Joy_M2_Complete_Question_DB_V1_18.sqlite3"
    csv_path = release_dir / "Joy_M2_Complete_Questions_V1_18.csv"
    markdown_path = release_dir / "Joy_M2_完整题497题_知识文档_V1.18.md"
    audit_path = release_dir / "complete_questions_452_task6_audited.json"
    audit_report_path = release_dir / "task6_audit_report.json"
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_key_errors = len(db.execute("PRAGMA foreign_key_check").fetchall())
        db_rows = [dict(row) for row in db.execute("SELECT * FROM complete_questions_v2 ORDER BY question_id")]
        task6_count = db.execute("SELECT COUNT(*) FROM complete_questions_v2 WHERE source_order>45").fetchone()[0]
        old_45_count = db.execute("SELECT COUNT(*) FROM complete_questions_v2 WHERE source_order<=45").fetchone()[0]
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    csv_exact = len(csv_rows) == len(db_rows)
    if csv_exact:
        for db_row, csv_row in zip(db_rows, csv_rows, strict=True):
            expected = {key: "" if value is None else str(value) for key, value in db_row.items()}
            if csv_row != expected:
                csv_exact = False
                break
    markdown_count = len(
        re.findall(
            r"^### \d+\. `[^`]+`$",
            markdown_path.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
    )
    audit_records = json.loads(audit_path.read_text(encoding="utf-8"))
    audit_report = json.loads(audit_report_path.read_text(encoding="utf-8"))
    checks = {
        "hashes": not hash_errors,
        "integrity": integrity == "ok",
        "foreign_keys": foreign_key_errors == 0,
        "question_count": len(db_rows) == 497,
        "task6_count": task6_count == 452,
        "old_45_count": old_45_count == 45,
        "csv_exact": csv_exact,
        "markdown_count": markdown_count == 497,
        "audit_count": len(audit_records) == 452,
        "audit_status": audit_report.get("audit_passed") == 452
        and audit_report.get("audit_pending") == 0
        and audit_report.get("blocked") == 0,
        "baseline_hash": manifest.get("baseline_v117_sqlite_sha256")
        == "58f32e547c4ff0cdd2ae25a9368ea288cbaa70af52869b779d698233aee93fab",
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "hash_errors": hash_errors,
        "integrity_check": integrity,
        "foreign_key_error_count": foreign_key_errors,
        "question_count": len(db_rows),
        "task6_question_count": task6_count,
        "existing_v117_question_count": old_45_count,
        "csv_row_count": len(csv_rows),
        "markdown_question_count": markdown_count,
        "audit_record_count": len(audit_records),
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("Usage: verify_task6_release.py RELEASE_DIR", file=sys.stderr)
        return 2
    result = verify_release(Path(args[0]).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
