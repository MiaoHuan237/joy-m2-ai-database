# Task 7 Verification Report

Date: 2026-08-08 (Asia/Singapore)<br>
Branch: `task7/codex-engineering-init`<br>
Scope: Git/project initialization and V1.18 freeze only

## Result

Task 7 acceptance passed. No Task 8 pipeline module, App/API feature, new question, answer completion, or formal data migration was introduced.

## Frozen baseline

- Release: V1.18
- Complete questions: 497
- V1.17 retained: 45
- Task 6 migrated: 452
- Answer identity: 392 `source_provided`, 71 `ai_solved_verified`, 34 `missing_from_source`
- `SHA256SUMS.txt`: `ae7fea3558a8942262ab8578a66d9d4c3330fe0c9683de9aeaedac462bb750f3`
- SQLite: `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`
- Original formal ZIP: `302782a47f347ce2b75a7813903f5d0b4c29fae2e0a837ccdc98b7b3439b4d4e`
- SQLite integrity: `ok`
- Foreign-key violations: 0
- Embedded verifier: `PASS`

## Tests

| Gate | Command | Result |
|---|---|---:|
| Task 7 structure/freeze | `python -m unittest -v tests/regression/test_task7_project_initialization.py` | 7/7 |
| Task 6 | `(cd legacy && python -m unittest -v task6_work/test_task6_migration.py)` | 22/22 |
| Task 5 | `(cd legacy/task5_work && python -m unittest -v test_task5_import.py)` | 10/10 |
| Task 3 | `(cd legacy && python -m unittest discover -v -s task4_work/task3_package/06_构建与测试 -p 'test_task3_review.py')` | 13/13 |
| Task 4 | `(cd legacy && python -m unittest discover -v -s task4_work/task4_package/05_构建与测试 -p 'test_task4*.py')` | 9/9 |

Total executable historical regression: 54/54.

## Repository boundary

The new repository retains about 20 MB of minimal legacy material required by the 54 tests. It intentionally omits copied font files, the 34 MB Task 5 input ZIP, caches, preview images outside the packages, and unrelated intermediate workspaces. The original external workspace remains unchanged and is the recovery source for omitted historical material.

Large raw archives are not tracked during Task 7. A private Git LFS or external source-archive policy must be approved before importing them into Git.

## Remaining boundary

- No remote is configured. The repository is private/local until Joy explicitly connects a private remote.
- Task 8 has not started.
- The 34 missing-source-answer questions and 2026 non-official solution status are unchanged.
- Legacy compatibility views remain and cannot be deleted until consumer migration is verified.
