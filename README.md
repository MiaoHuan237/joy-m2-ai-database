# Joy M2 AI Database

Joy M2 AI Database is the structured question bank for Hong Kong DSE Extended Mathematics Module 2. The current formal release is V1.18 with 497 complete questions. Each record represents one complete question and retains all internal subparts.

This repository is in the engineering-refactor phase. Task 7 establishes the Git project, standard directories, frozen V1.18 baseline, and regression boundary. The Task 5/6 pipeline remains unchanged under `legacy/`; migration to maintained modules under `src/joy_m2/` is reserved for Task 8.

## Quick start

Requirements: Python 3.12.x and Git.

```bash
python --version
python -m unittest -v tests/regression/test_task7_project_initialization.py
python releases/V1.18/verify_task6_release.py releases/V1.18
```

The V1.18 verifier should return `status=PASS`, `question_count=497`, `task6_question_count=452`, `existing_v117_question_count=45`, `csv_row_count=497`, and `markdown_question_count=497`.

## Repository map

| Path | Responsibility |
|---|---|
| `AGENTS.md` | Small, durable rules automatically loaded by Codex |
| `PROJECT_STATE.md` | Current version, active Task, blockers, and next step |
| `PROJECT_CONTEXT.md` | Full handoff context for a new environment or major redesign |
| `src/joy_m2/` | Maintained Python package boundary; pipeline modules arrive in Task 8 |
| `tests/` | New unit, integration, and regression gates |
| `data/baselines/V1.18/` | Immutable baseline lock and expected facts |
| `data/raw/` | Local source landing area; not tracked until storage policy is approved |
| `data/staging/` | Disposable candidate output; never formal data |
| `releases/V1.18/` | Frozen V1.18 formal release and independent verifier |
| `legacy/` | Minimal compatibility snapshot needed for Task 3–6 regression |
| `docs/` | Architecture, decisions, reports, specifications, and plans |

## Data rules

- SQLite is the only formal source of truth; CSV, Markdown, reports, and statistics are derived from it.
- V1.18 has 392 source-provided answers, 71 independently verified non-official solutions, and 34 questions whose source provides no answer.
- Missing-source-answer questions remain valid for student use, but must not be presented as answered in teacher materials.
- V1.18 formal assets are never edited in place. Future changes use a new release and migration.
- M1 data, App/API product development, new question generation, and Task 8 pipeline restructuring are outside Task 7.

## Full legacy regression gate

Run these commands only for a migration/release gate or when diagnosing legacy behavior:

```bash
(cd legacy && python -m unittest -v task6_work/test_task6_migration.py)
(cd legacy/task5_work && python -m unittest -v test_task5_import.py)
(cd legacy && python -m unittest discover -v -s task4_work/task3_package/06_构建与测试 -p 'test_task3_review.py')
(cd legacy && python -m unittest discover -v -s task4_work/task4_package/05_构建与测试 -p 'test_task4*.py')
```

Expected total: Task 6 × 22, Task 5 × 10, Task 3 × 13, Task 4 × 9 = 54 passing tests.
