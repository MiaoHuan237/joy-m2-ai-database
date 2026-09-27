# V1.22 Promotion Readiness Implementation Plan

> Use superpowers:executing-plans. Execute continuously under the user's
> autonomous authorization, with independent Design/Plan and final review.

**Spec:** `docs/superpowers/specs/2026-09-27-v122-promotion-readiness-design.md`.
**Goal:** Two byte-identical, independently verified 639-question staging
releases from the exact four-batch candidate. Do not publish the real release.
**Architecture:** New fixed-version counterpart modules; historical modules
remain untouched. No generic version engine or real candidate rebuild.
**Stack:** Python standard library, unittest, SQLite, canonical JSON, SHA-256.

## Global constraints

Design §2 is the exact input oracle. V1.21/591 remains formal. Candidate
`82b10a551f70eebda2e0aa4d10c962e317767e936b4f0d9aa798629bb8070d46`
is not a release digest. No real approval may be constructed or consumed.
No `releases/V1.22`, 2023, V1.23, formal pointer update, source revision,
dependency, CLI, force push or history rewrite. Use existing worktree.

Commands below use `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:.` and the project's
Codex Python runtime when `python` is unavailable. Keep full gate logs in ignored
`tmp/pdfs/task12-v122-promotion-readiness/`. No setup/import/fixture error is RED.

## Closed file scope

- NEW: `src/joy_m2/ingest/v122_promotion_models.py`, `v122_promotion.py`,
  `v122_promotion_verification.py` in the same directory.
- MODIFY: `src/joy_m2/ingest/__init__.py`, append nine exports only.
- NEW: `tests/unit/test_v122_promotion_models.py`,
  `tests/unit/test_v122_promotion_primitives.py`,
  `tests/integration/test_v122_promotion.py`.
- MODIFY: `tests/unit/test_v121_promotion_models.py` and
  `tests/unit/test_v122_models.py`, `tests/unit/test_v119_promotion_models.py`,
  `tests/regression/test_v119_historical_replay.py`, preserve exact historical export prefixes
  and add the approved suffix.
- MODIFY: `tests/regression/test_v122_historical_replay.py`, replace only the
  perpetual-absence assumption with the explicit lifecycle gate and its controls.
- DOC: this Plan, its Design, `PROJECT_STATE.md`,
  `docs/reports/V122_PROMOTION_READINESS.md`.
- Ignored runtime: the two exact roots in Design §6. No other tracked scope.

### Task 1: Lock baseline and immutable evidence

**Files:** ignored runtime evidence only.
**Interfaces:** consumes actual generation 4; produces verified input snapshot.

- [ ] Read AGENTS/PROJECT_STATE and candidate receipt, confirm Git branch/HEAD.
- [ ] Run `python tmp/pdfs/task10b-hkdse-2022/import_approved_2022.py verify`.
  Expected: 24/24 PASS, exact Design §2 identities and 2019–2022 ledger.
- [ ] Fingerprint all files under formal V1.18–V1.21, all four task12 candidate
  and canonical roots, and the four Task 10B source/transcription/approval roots.
  Record actual file lists, sizes, hashes; do not infer from receipt summaries.
- [ ] Run historical formal verifiers through existing read-only replay and
  `python releases/V1.18/verify_task6_release.py releases/V1.18`.
  Expected: all PASS; no real V1.22 root.

### Task 2: Public-model/API RED then minimum GREEN

**Files:** new models tests, three new production files, ingest exports,
all listed existing exact-export tests.
**Interfaces:** produces Design §4 six carriers and three callable signatures.

- [ ] Write dynamic getattr assertions so missing APIs yield FAIL, not import
  errors. Cover exact fields/order/types/defaults/frozen and all 14 literals,
  bad nested types, digest/approval statement, ArtifactRef kinds and tuple copy.
- [ ] Run `python -m unittest -v tests.unit.test_v122_promotion_models`.
  Expected: missing new API/model assertion FAIL, zero ERROR.
- [ ] Implement only exact models and callable stubs; no build/verify/publish
  behavior. Preserve existing export prefix in all listed older tests.
- [ ] Rerun model tests and existing model suites. Expected: all PASS.

### Task 3: Dependency-valid primitive and verifier RED/GREEN

**Files:** new primitives/integration tests and new verifier.
**Interfaces:** consumes GREEN models/stubs; produces independently verified fixture.

- [ ] Build a read-only exact V122 candidate request helper from the four
  committed canonical packages, existing preflights and exact approvals; verify
  the existing candidate. Copy inputs for temporary roots, never call writer.
- [ ] Add primitive projection/identity/type tests; observe assertions fail against
  stubs before implementing corresponding helpers.
- [ ] Construct a temporary formal-equivalent fixture in test code from literal
  Design DDL, exact candidate bytes and independently serialized artifacts (do not
  use the production builder). Verify its SQL/field/count identities in test setup.
  Add independent verifier positive and corruption tests, observe missing verifier
  report assertions fail, then implement the independent verifier and obtain GREEN.
- [ ] Add real-input build tests: 591 unchanged + exact 48, all published,
  deterministic four files over two roots, schema/FK/view, image evidence,
  manifest/hash/ledger/corruption and wrong-envelope negative controls.
- [ ] Add isolated publication tests: absent/wrong approval rejects, exact
  test-root approval succeeds, wrong copied bytes rejects, no-replace,
  symlink/location rejection, cleanup fault injection and rollback receipt.
- [ ] Run each test group before its production behavior. Builder/publication
  assertions using an unavailable dependency do not count as RED; defer those runs
  until their valid fixtures are available. Record exact fail reason and zero ERROR.

### Task 4: Minimal fixed-version GREEN and lifecycle closure

**Files:** new builder/verifier, permitted lifecycle test only.
**Interfaces:** consumes validated RED; produces independently verified artifacts.

- [ ] With verifier GREEN, run builder tests against builder stub, confirm valid
  missing-behavior RED, then implement builder. With builder GREEN, run publication
  tests against publication stub, confirm valid RED, then implement publication.
  Implement the Design's role-specific counterpart delta. Preserve all
  historical files and inherited objects. Keep verifier independent from builder.
- [ ] Run `python -m unittest -v tests.unit.test_v122_promotion_models
  tests.unit.test_v122_promotion_primitives tests.integration.test_v122_promotion`.
  Expected: all PASS, no skip/expected failure.
- [ ] Lock lifecycle states in isolated roots: before approval absent; after
  exact approval present and exact digest verified; forged approval or changed
  identity fails. Real readiness still explicitly checks absence. Historical
  replay must retain all existing frozen hashes and read-only checks.
  Use the Design §6 checked-in approval literal, left None for this task; never
  derive approval from a generated manifest/receipt. Tests supply approval only
  for isolated roots. A later human-approved value update does not change logic.
- [ ] Any defect: add independent failing negative control before correction.
  Rerun focused suite after each correction.

### Task 5: Actual dry-runs, complete gates and independent review

**Files:** ignored runtime, readiness report, PROJECT_STATE.
**Interfaces:** produces actual release identity, never real publication.

- [ ] Build under two distinct non-formal roots using exact generation 4.
  Independent formal verifier PASS 21/21 for both; compare every file byte,
  ArtifactRef/hash/size, semantic digest and release digest. Query 639 unique
  complete records and compare original 591 + approved 48 field-by-field.
- [ ] Run all maintained unittest modules excluding only the existing legacy
  attribution module `tests.regression.test_task8b_legacy_pipeline_behavior`.
  Record fresh actual totals, zero skips/expected failures. If attribution is
  run, report the known two failures separately, never waive new failures.
- [ ] Run independent candidate verifier, all historical formal verifiers,
  V1.18 validator and read-only replay; compare every Task 1 fingerprint.
- [ ] Run `git diff --check` and exact scope inspection. Expected: PASS.
- [ ] Fresh independent implementation reviewer checks entire change against
  Design, not just tests; Critical/Important must be zero after remediation.
  Review focus: inherited candidate double counting, exact source provenance,
  false-pass verifier corruptions, publication race/ownership cleanup, schema
  and byte preservation, and lifecycle approval versus mere file existence.
- [ ] Update report/state with actual identities, gates and no-publication state.
  Explicitly distinguish candidate digest from computed release digest.

### Task 6: Engineering checkpoint and human gate

**Files:** only closed scope above.
**Interfaces:** consumes complete gates/review; produces committed readiness.

- [ ] Stage explicit approved paths, ordinary commit; inspect commit scope,
  `git diff-tree --check HEAD^ HEAD`, `git diff --check`, clean index/worktree.
- [ ] Ordinary push current branch; verify actual remote HEAD and ahead/behind.
  Network failure is reported without force or history changes.
- [ ] Confirm all frozen identities and no real `releases/V1.22`.
- [ ] Stop at `USER DECISION REQUIRED — FINAL V1.22 PROMOTION AUTHORIZATION`.
  Supply actual release digest approval statement and exact output files,
  rollback/no-default-query-change boundary. Do not consume this statement.
