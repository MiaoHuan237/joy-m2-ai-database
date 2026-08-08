# Joy M2 repository rules

## Read first

1. Read `PROJECT_STATE.md` for the current version and active task.
2. Read the current task brief or plan only when it is relevant.
3. Read `PROJECT_CONTEXT.md` only for first handoff, major redesign, or an unclear invariant.
4. Do not scan `legacy/` or the 497-question Markdown by default. Query the V1.18 SQLite or open only the files needed for the task.

## Frozen baseline

- V1.18 is the read-only golden baseline in `releases/V1.18/`.
- Never edit files under `releases/V1.18/` or `data/baselines/V1.18/` in place.
- The baseline contains 497 complete questions: one complete question per record, with all subparts retained inside that record.
- Do not split or independently select `(a)`, `(b)`, `(i)`, or `(ii)` subparts.
- SQLite is the sole formal source of truth. CSV, Markdown, reports, and statistics are derived outputs.
- Preserve answer identity: 392 `source_provided`, 71 `ai_solved_verified`, and 34 `missing_from_source`.
- `missing_from_source` questions may remain student-selectable, but their answer fields stay empty and teacher outputs must show the true status.
- Do not alter stable IDs, question boundaries, source text, reviewed Chinese text, answer provenance, Joy Level, tags, images, corrections, hashes, or selection state during code refactoring.
- Do not write a candidate batch into formal SQLite/CSV or raise the release version without Joy's explicit approval.

## Scope and directory rules

- `src/joy_m2/`: new maintained code. Task 7 only establishes its package boundary; pipeline migration begins in Task 8.
- `tests/`: new unit, integration, and regression tests.
- `legacy/`: minimal Task 3–6 compatibility snapshot. Read it only for migration or regression diagnosis; do not build new features there.
- `data/raw/`: local source archive landing area. It is ignored until a Git/LFS storage policy is approved.
- `data/staging/`: disposable candidate output. Never treat it as formal data.
- `releases/`: immutable formal releases.
- Keep M1 data out of this repository.
- Current engineering scope excludes App/API work and new question generation.

## Commands

Run Task 7 and frozen-baseline checks:

```bash
python -m unittest -v tests/regression/test_task7_project_initialization.py
python releases/V1.18/verify_task6_release.py releases/V1.18
```

Run the 54 executable legacy regressions only for release gates or migration work:

```bash
(cd legacy && python -m unittest -v task6_work/test_task6_migration.py)
(cd legacy/task5_work && python -m unittest -v test_task5_import.py)
(cd legacy && python -m unittest discover -v -s task4_work/task3_package/06_构建与测试 -p 'test_task3_review.py')
(cd legacy && python -m unittest discover -v -s task4_work/task4_package/05_构建与测试 -p 'test_task4*.py')
```

## Development workflow

- One Task per branch and short conversation. Use a worktree after the repository has a stable `main` branch.
- Separate code refactors from formal data changes in different Tasks and commits.
- Use test-first development for behavior changes. Run targeted tests during development and the full gate before a release or merge.
- Do not silence a failing gate by weakening assertions, changing frozen hashes, or deleting compatibility coverage.
- Do not add dependencies without documenting the reason in `pyproject.toml` and the relevant decision record.
- Never commit passwords, API keys, access tokens, private keys, `.env` files, local caches, or generated staging databases.

## Completion gate

Before claiming a Task complete, run fresh relevant tests, inspect `git diff`, update `PROJECT_STATE.md`, and state any remaining limitation. Formal data changes additionally require a new version, migration record, audit report, Joy approval record, hashes, and a rollback package.
