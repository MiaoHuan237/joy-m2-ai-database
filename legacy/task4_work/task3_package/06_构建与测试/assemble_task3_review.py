#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

from build_task3_review import (
    build_validation_report,
    merge_review_records,
    render_precheck_report,
    review_to_csv_row,
    verify_hash_baseline,
)


REVIEW_GROUPS = ("教材例题", "应试训练", "甲部特训", "乙部特训")
EXPECTED_SECTIONS = {"教材例题": 8, "应试训练": 14, "甲部特训": 17, "乙部特训": 6}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def assemble(args):
    baseline = load_json(args.baseline)
    reviews = []
    for group in REVIEW_GROUPS:
        reviews.extend(load_json(Path(args.review_dir) / f"review_{group}.json"))

    merged = merge_review_records(baseline, reviews, audited_at=args.audited_at)
    taxonomy = load_json(args.taxonomy)
    hash_baseline = load_json(args.hash_baseline)
    hash_issues = verify_hash_baseline(args.root, hash_baseline)
    validation = build_validation_report(
        merged,
        expected_ids={row["question_id"] for row in baseline},
        primary_types=taxonomy["primary_types"],
        tags=taxonomy["tags"],
        expected_sections=EXPECTED_SECTIONS,
        hash_issues=hash_issues,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reviewed_json = output_dir / "complete_questions_45_reviewed.json"
    validation_json = output_dir / "task3_validation_report.json"
    reviewed_csv = output_dir / "微分应用45题审计工作表_已复核.csv"
    report_md = output_dir / f"Joy_M2_微分应用45题_入库预检报告_{args.audited_at}.md"

    write_json(reviewed_json, merged)
    write_json(validation_json, validation)
    csv_rows = [
        review_to_csv_row(row, validation_status=validation["status"])
        for row in merged
    ]
    with reviewed_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    report_md.write_text(
        render_precheck_report(merged, validation, audited_at=args.audited_at),
        encoding="utf-8",
    )

    return {
        "reviewed_json": str(reviewed_json),
        "reviewed_csv": str(reviewed_csv),
        "validation_json": str(validation_json),
        "precheck_report": str(report_md),
        "validation_status": validation["status"],
        "validation_summary": validation["summary"],
        "distribution": validation["distribution"],
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Assemble Task 3 reviewed question artifacts.")
    parser.add_argument("--root", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--review-dir", required=True)
    parser.add_argument("--taxonomy", required=True)
    parser.add_argument("--hash-baseline", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--audited-at", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(assemble(parse_args()), ensure_ascii=False, indent=2))
