# Joy M2 AI Database — Codex Project Context

Updated: 2026-08-08 (Asia/Singapore)<br>
Formal release: V1.18<br>
Current engineering scope: option B, engineering refactor; no App/API product expansion

## 1. Project goal

The project belongs to Joy Teacher AI and serves Hong Kong DSE Extended Mathematics Module 2. It converts textbooks, public-exam questions, Mathpix material, practice sets, source answers, and teacher review into a traceable complete-question database. It must support reliable retrieval and later worksheet generation without losing source identity, formulas, images, corrections, or answer provenance.

M1 is a separate project and must not be mixed into this database. JoyMathBook V3 remains the default future LaTeX teaching-output template.

## 2. Technology and structure

- Runtime: Python 3.12.x.
- Formal data: SQLite 3 with `PRAGMA user_version=118`.
- Derived artifacts: UTF-8 BOM CSV, JSON, Markdown, SHA-256 manifests, deterministic ZIP.
- Tests: Python standard-library `unittest`.
- No server, web process, external API, password, or API-key dependency exists.

Repository structure:

```text
AGENTS.md                  durable Codex rules
PROJECT_STATE.md           concise current state
PROJECT_CONTEXT.md         this handoff document
src/joy_m2/                maintained package boundary
tests/                     new unit/integration/regression tests
data/baselines/V1.18/      immutable facts and hash lock
data/raw/                  local source landing area
data/staging/              disposable candidates
releases/V1.18/            frozen formal release
legacy/                    minimal Task 3–6 compatibility snapshot
docs/                      architecture, decisions, reports, plans, specs
scripts/                   thin operational wrappers only
```

`legacy/` is intentionally not the future architecture. It keeps current behavior executable until Task 8 migrates code into `src/joy_m2/`. Codex should not scan it during ordinary tasks.

## 3. Completed capabilities

- V1.18 covers all 497 complete questions in the V2 layer.
- V1.17's 45 reviewed differentiation-application questions remain unchanged; Task 6 added 452 questions from 23 source batches.
- V1.16 compatibility data remains: 1,517 legacy question rows, 24 sources, and 12 topics.
- Answer identity is explicit: 392 `source_provided`, 71 `ai_solved_verified`, 34 `missing_from_source`.
- Difficulty distribution is L1×11, L2×54, L3×140, L4×190, L5×102.
- The release contains 16 primary types, 397 controlled tags, 3,574 question-tag links, 59 structured corrections, and 34 image references.
- Exact duplicates: 0. Audit blockers: P0=0 and P1=0.
- SQLite, CSV, Markdown, reports, audit JSON, manifest, SHA-256 list, deterministic package builder, and an independent release verifier are available.
- Task 3–6 have 54 executable regression tests: 13 + 9 + 10 + 22.

## 4. Important design decisions

1. One complete question equals one record. All `(a)(b)(i)(ii)` subparts stay inside that record and cannot be independently selected.
2. SQLite is the sole formal truth. CSV, Markdown, reports, and statistics are regenerated from final SQLite.
3. Preserve the source language. English source text cannot be overwritten by Chinese; a Chinese source is not given a fabricated English version.
4. `source_provided`, `ai_solved_verified`, and `missing_from_source` are distinct identities. Independently solved answers are never called official, publisher, or HKEAA answers.
5. `missing_from_source` does not block formal import or student selection. Its solution remains empty and teacher output shows the true status.
6. Joy Level 1–5 is a teaching difficulty for the whole question, not an HKEAA classification.
7. Each question has one primary type and multiple controlled tags. Dirty Markdown/table text is not a valid tag.
8. Source corrections are never silent: original content, correction, reason, evidence, and review state remain traceable.
9. Preserve source IDs, members, original numbers, pages, images, and SHA-256. Missing original ZIP files cannot be claimed as re-read.
10. Exact duplicates block import. Adaptations may remain if their relationship is recorded.
11. A candidate batch must pass audit with no unresolved issue and receive Joy's explicit approval before formal SQLite/CSV or version changes.
12. Legacy `leaf / complete / both` compatibility stays until every consumer is migrated and verified. New consumers later use `selectable_complete_questions_v2`.
13. V1.16 facts, V1.17's 45 V2 rows, and the V1.18 release are frozen baselines.
14. The same frozen input must produce deterministic outputs and an independently verifiable package.

## 5. Known issues

- Several original Mathpix ZIP archives are absent from the historical V1.16 delivery, so those batches cannot be rebuilt from the earliest source files.
- Task 3's old delivery lacks one historical package builder; the currently executable Task 3 gate is 13 tests.
- The Task 5/6 code is still version-coupled and lives under `legacy/`; there is no unified maintained CLI yet.
- The 34 `missing_from_source` questions still need separately sourced or independently reviewed answers before their answer status can change.
- The 12 questions from the 2026 paper use independently verified non-official solutions; Q8(a)'s disconnected-domain integration constant remains a documented rigor risk.
- Worksheet/student/teacher consumers have not yet completed end-to-end V2-view migration, so compatibility views cannot be removed.
- Large raw archives are not committed during Task 7; a private Git LFS or external source-archive policy must be decided before adding them.

## 6. Start and test commands

```bash
python --version
python -m unittest -v tests/regression/test_task7_project_initialization.py
python releases/V1.18/verify_task6_release.py releases/V1.18
```

Full legacy gate:

```bash
(cd legacy && python -m unittest -v task6_work/test_task6_migration.py)
(cd legacy/task5_work && python -m unittest -v test_task5_import.py)
(cd legacy && python -m unittest discover -v -s task4_work/task3_package/06_构建与测试 -p 'test_task3_review.py')
(cd legacy && python -m unittest discover -v -s task4_work/task4_package/05_构建与测试 -p 'test_task4*.py')
```

## 7. Refactor target and immutable behavior

The approved refactor is option B: standardize repository layout, dependencies, audit, migrations, tests, and release workflow before product expansion. Task 7 only establishes the repository and baseline. Task 8 will separately migrate code from `legacy/` into focused `src/joy_m2/audit`, `db`, `export`, and `release` modules and later add a unified CLI.

Refactoring must not change V1.18 IDs, boundaries, texts, answers, provenance, difficulties, types, tags, images, corrections, selection state, hashes, answer distributions, compatibility tables, or user-visible complete-question behavior. It must not split subparts, fabricate source answers, overwrite formal releases, remove compatibility views early, add M1, or begin App/API work.

## 8. Acceptance criteria

- The project is a valid Git repository with small durable instructions, clear paths, Python 3.12 metadata, and no secrets.
- `releases/V1.18/` remains byte-identical to the approved release; its verifier returns `PASS`.
- V2 remains 497 unique complete questions; V1.17 45 and Task 6 452 remain unchanged.
- Answer distribution remains 392/71/34; difficulty remains 11/54/140/190/102; corrections remain 59; exact duplicates remain 0.
- SQLite `integrity_check=ok`, foreign-key errors 0, CSV 497-row exact mirror, Markdown 497 unique questions with 34 missing-source-answer markers.
- Task 3–6 executable regressions remain 54/54.
- Any failed gate stops completion; frozen hashes and assertions may not be weakened to obtain a pass.
- Formal data changes later require a new version, migration, audit report, Joy approval record, hashes, and rollback package.
