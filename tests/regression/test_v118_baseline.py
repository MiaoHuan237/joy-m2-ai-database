from __future__ import annotations

import importlib
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "releases" / "V1.18"


def load_baseline_module():
    spec = importlib.util.find_spec("joy_m2.baseline")
    if spec is None:
        raise AssertionError("joy_m2.baseline must provide the baseline verifier")
    return importlib.import_module("joy_m2.baseline")


class V118BaselineTests(unittest.TestCase):
    def test_locked_release_preserves_all_business_invariants(self) -> None:
        baseline = load_baseline_module()

        result = baseline.verify_baseline(BASELINE)

        self.assertEqual(result["status"], "PASS", result)
        self.assertTrue(all(result["checks"].values()), result)
        self.assertEqual(result["question_count"], 497)
        self.assertEqual(result["unique_question_count"], 497)
        self.assertEqual(result["task6_question_count"], 452)
        self.assertEqual(result["existing_v117_question_count"], 45)
        self.assertEqual(result["selectable_question_count"], 497)
        self.assertEqual(result["legacy_counts"], {"questions": 1517, "sources": 24, "topics": 12})
        self.assertEqual(
            result["answer_status_counts"],
            {"ai_solved_verified": 71, "missing_from_source": 34, "source_provided": 392},
        )
        self.assertEqual(result["difficulty_counts"], {"1": 11, "2": 54, "3": 140, "4": 190, "5": 102})
        self.assertEqual(result["correction_count"], 59)
        self.assertEqual(result["csv_row_count"], 497)
        self.assertEqual(result["markdown_question_count"], 497)
        self.assertEqual(result["markdown_missing_answer_count"], 34)

    def test_module_cli_returns_machine_readable_pass_result(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "joy_m2", "verify-baseline"],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["question_count"], 497)


if __name__ == "__main__":
    unittest.main()
