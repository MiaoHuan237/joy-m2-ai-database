# F6 Selected Batch / V1.24 Candidate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> for the recommended Native / Inline execution, or
> superpowers:subagent-driven-development only if the user selects it.
> Execute task-by-task; checkbox completion requires observed evidence.

**Goal:** Prepare an exact-approved four-question F6 school-source package and
the minimal V1.24 candidate mechanism, then stop at the required real-data gates.

**Architecture:** One source-specific F6 module feeds fixed V1.24 candidate
siblings. The six V1.23 candidate modules are normative counterparts, not
mutable templates at runtime. The source adapter uses module-local APIs;
package-wide exports, scheduler and historical modules remain untouched.

**Tech Stack:** Python 3.12, unittest, standard-library SQLite/JSON/hashlib and
the already-installed pypdf; no new dependency or service.

**Spec:** `docs/superpowers/specs/2026-10-20-f6-selected-batch-v124-candidate-design.md`.
Human approval binds the technical Design at commit
`b480a608df851dde318719f4fbf88bffb1489658`, file SHA-256
`7ef92371a9876fc9b0ee100324de4b489f99ba491696ea46f8edf8b4192e13fc`.
Only the Design's approval/checkpoint status is synchronized with this Plan.

**Status:** WRITTEN PLAN — PENDING HUMAN REVIEW AND EXECUTION CONFIRMATION.
No implementation or real transcription/import approval has been granted by
the instruction to create this Plan.

## Global Constraints

- Work only in the existing
  `/Users/miaohuanjoy/Desktop/joy-m2-ai-database-current/.worktrees/task8b-pipeline-migration`.
  Do not create another worktree, switch branches or rewrite history.
- Preserve user-owned AGENTS.md exactly; current SHA
  `75ffa9680b18a0875fde8d36a8ca3e0ebda0603f10e8dc788e71ea8353d0311d`.
- Formal baseline V1.23 / 677; SQLite SHA
  `28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd`,
  10928128 bytes; manifest SHA
  `54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498`,
  6728 bytes; release digest
  `84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc`.
- Baseline schema `task13-v123-formal-v1`; read only
  `formal_complete_questions_v123`; metadata table `release_metadata_v2`.
  Read exactly 677 unique published/selectable records, never count inherited
  candidate tables again. Use escaped read-only SQLite URIs and query_only.
- V1.24 genesis
  `797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a`;
  reconstruct from the exact Design §2 canonical projection, including LF.
- Source type `school_mock`; source ID `HKSYCIA-WTS-M2-MOCK-2015-16`.
  Selected batch:
  `JOY-M2-STG-F6-MOCK-2015-16-0428-20260905-Q01-Q03-Q06-Q08`.
- Selected IDs Q01,Q03,Q06,Q08 in original order, 4 complete questions / 24
  marks. Retain the other 8 and the original 12-row / 100-mark draft unchanged.
- No source relabeling, automatic post-preflight salvage, changed fingerprint,
  changed duplicate/collision contract, AI solution masquerading as source,
  guessed text, automatic transcription/import approval, or promotion.
- Frozen V1.18–V1.23, prior candidates, 2024 evidence and approvals are immutable.
  No `releases/V1.24/`, no V1.25, no new HKDSE/Oxford bridge or runner job.
- Exact runtime/schema/file identities and all field mappings are Design
  §§2–6, not values inferred from a year or generation number.
- Only the Design §7 closed file scope is writable. Missing necessary scope
  requires a focused decision, not a test waiver.

## Review Focus

1. A sub-batch with correct count but wrong IDs/order must fail; held items
   cannot leak in or be renumbered. Pin in Task 3.
2. Q6 solution printed Q7 and Q8 editorial annotation must remain distinct
   from source question numbering and source mathematics. Pin in Tasks 3–4.
3. Reserved URI characters and source changes between validation/publication
   must not open a wrong database or publish inconsistent bytes. Pin in Tasks
   2, 4 and 6B.
4. A forged approval/preflight pair agreeing on a wrong parent is still invalid;
   unchanged parent artifacts and complete-prefix indexing matter. Pin in
   Tasks 6A, 6B, 7 and 8.
5. A duplicate plus eligible input remains a blocked batch, and a repeated
   accepted batch cannot become another generation. Pin in Tasks 5 and 8.

---

## Execution and evidence conventions

Recommended execution is Native / Inline because these tasks share tightly
ordered interfaces; use one separate whole-implementation reviewer after
focused GREEN. Written Plan approval/execution confirmation is still required.

Run from the existing worktree:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=src:.
JOY_PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

Commands below use `"$JOY_PY" -B -m unittest -v <module-or-class>`.
No dependency installation. Set up the environment again after a new shell.

For each behavioral group: write its tests → run and record valid RED → minimal
GREEN → rerun the group and earlier dependent tests → inspect diff. Red output
must identify the expected missing behavior, not an import, fixture, setup,
syntax, path or stale-baseline failure. A guard test may assert that a module
does not yet exist; that is API-existence RED only, not later behavior RED.
Once scaffolded, test helpers may translate `NotImplementedError` into explicit
assertion failure on a valid call; do not count an unrelated exception as RED.
Negative tests assert the intended exception/status/check, not `Exception`.

Keep commands, counts, failure reason and changed-path evidence under a NEW
ignored run directory in `data/staging/task14-v124-f6/`; never overwrite old
evidence. Each task checkpoint explicitly stages only its listed source/test
paths and, when synchronized, PROJECT_STATE.md / the task verification report.
Use normal commits and ordinary upstream push; no AGENTS.md, generated
databases, PDFs or ignored approvals in Git. A network failure is reported as
backup status, not permission to repeat a successful operation.

### Exact file responsibilities

| File | Responsibility / normative counterpart |
|---|---|
| `src/joy_m2/ingest/v124_models.py` | 13 exact immutable carriers; `v123_models.py` |
| `src/joy_m2/ingest/v124_manifest.py` | strict 18-field loader; `v123_manifest.py` |
| `src/joy_m2/ingest/v124_writer_profiles.py` | fixed baseline/genesis/DDL/24 check names; `v123_writer_profiles.py` |
| `src/joy_m2/ingest/v124_preflight.py` | exact baseline + effective-parent classification; `v123_preflight.py` |
| `src/joy_m2/ingest/v124_writer.py` | prefix reconstruction and atomic private-copy append; `v123_writer.py` |
| `src/joy_m2/ingest/v124_verification.py` | independent read-only 24-check verifier; `v123_verification.py` |
| `src/joy_m2/ingest/f6_school_mock.py` | fixed selection/source/approval/5-file bridge; `publisher_mock.py` as interface reference only |
| `tests/unit/test_v124_models.py` | API/carriers/manifest and primitive checks |
| `tests/integration/test_f6_school_mock.py` | synthetic source fixtures, review and bridge |
| `tests/integration/test_v124_preflight.py` | synthetic canonical helper, genesis and verified-parent preflight |
| `tests/integration/test_v124_candidate.py` | independent candidate fixture, writer/verifier, prefix/replay |
| `tests/regression/test_v124_historical_replay.py` | historical identity/API/replay and no formal writes |
| `docs/reports/F6_V124_CANDIDATE_VERIFICATION.md` | fresh engineering and operational evidence, clearly separated |
| `PROJECT_STATE.md` | current checkpoint and next human gate |

Counterpart revision is `2f45dc98f8b37c9d007891f72ad165fd5f265fed`.
Do not edit those counterpart files, package `__init__.py`, historical tests,
automation config or AGENTS.md. Test fixture helpers live inside the allowed
new test modules; no extra maintained fixture framework.

## Task 1 — Importable carriers and minimal API scaffolds

**Files:** create the six `v124_*` modules and `f6_school_mock.py` initially
with only tested declarations/scaffolds; create `tests/unit/test_v124_models.py`.

**Interfaces:** produce the 13 V124 dataclasses from Design §6 and the four
candidate module-local function signatures; F6 `inspect_proposal(inputs,
config) -> dict` and `build_package(inputs, approval_text, output_dir,
config) -> Path`. Also scaffold the counterpart private `_genesis_digest()`
and `_formal_indexes(path)` signatures consumed in Task 2; cover them with API
existence assertions before introducing stubs. Do not add package-wide exports.

- [ ] Write `V124ApiTests.test_modules_and_exact_signatures`: use
  `importlib.util.find_spec` and assertion guards before import; assert exactly
  the Design signatures, then unchanged `joy_m2.ingest.__all__`.
- [ ] Run `tests.unit.test_v124_models.V124ApiTests`; record missing-API
  assertion RED without module-level import/setup error.
- [ ] Add importable declarations. Unimplemented function bodies raise
  `NotImplementedError`; no source, writer or classification behavior.
- [ ] Write `V124ModelTests`: field counts/order exactly
  `[18,3,9,5,5,34,5,5,3,25,3,3,8]` in Design order; frozen/no-default rules,
  nested types, tuple copying, exact bool/int distinctions, wrong historical
  target/carrier rejection, and exact approval binding.
- [ ] Run the model class, verify behavioral RED on valid constructed inputs;
  implement only V124 counterpart carrier validation and constants.
- [ ] Run both classes GREEN. Check:
  `V124CandidateBuildRequest(approved_batches, output_dir, contract)` and
  `V124CandidateVerificationRequest(candidate_dir, approved_batches, contract)`
  retain counterpart field order. No behavior tests are yet claimed GREEN.
- [ ] Commit explicit seven source files and model test:
  `feat: establish V1.24 candidate and F6 module boundaries`.

## Task 2 — Strict manifest, fixed primitives and exact formal loader

**Files:** modify `v124_manifest.py`, `v124_writer_profiles.py`,
`v124_preflight.py`, `tests/unit/test_v124_models.py`; create
`tests/integration/test_v124_preflight.py`.

**Interfaces:** `load_v124_import_manifest(path: Path) -> V124BatchImportManifest`;
private `_genesis_digest() -> str` and
`_formal_indexes(path: Path) -> tuple[dict[str, object], frozenset[str], frozenset[str]]`.
Tests define `_contract()`, `_make_package(parent: Path) -> Path`,
`_request(package: Path, parent=None) -> V124PreflightRequest`, and
`_fingerprint(root: Path)` (sorted relative path/SHA/size tuples).

- [ ] Write `V124ManifestTests` asserting exact 18 fields, six ordered file
  groups, policy literals and target; reject extra/missing/duplicate JSON keys,
  wrong types/version, unsafe relative paths and invalid file evidence.
  Write `V124PrimitiveTests` independently hashing the literal Design genesis
  projection with LF; assert exact digest, DDL names and first order 678.
- [ ] Run those classes RED; implement strict loader and fixed primitives.
  Reuse only the version-neutral helper list permitted by the Design.
- [ ] Write `V124BaselineTests` in the preflight test module: SHA/size/manifest,
  metadata, query view, all 677 unique rows, published/selectable, controlled
  vocabulary, and unchanged source-image JSON. Deliberately corrupt isolated
  copies to reach inner schema/view/count checks, without touching originals.
  Reserved `#`, `%`, space and Unicode paths must use escaped read-only URIs.
- [ ] Run baseline tests RED; implement `_formal_indexes` with exact V1.23
  authority, not patched calls to a V1.22 reader. Integrity/FK/metadata failures
  must reject; read-only missing paths must never create a database.
- [ ] Define synthetic canonical test packages by copying existing
  `tests/fixtures/task10a/v120-batch-{a,b,c}` into isolated staging and replacing
  only their local manifest target/schema. Preserve the original fixtures.
  No real F6 text or approval is used in candidate test packages.
- [ ] Run all Task 1–2 classes GREEN; inspect that inherited candidate tables
  are not added to the formal-view count. Commit:
  `feat: validate V1.24 manifests baseline and genesis`.

## Task 3 — Fixed F6 selected proposal validation

**Files:** modify `f6_school_mock.py`; create
`tests/integration/test_f6_school_mock.py`.

**Interfaces:** `inspect_proposal(inputs: dict[str, Path],
config: PipelineConfig) -> dict` uses Task 2 formal vocabulary. Exact input
keys/record schema/report and exception boundaries are Design §4.

- [ ] First test the F6 module's pinned profile/input identity declarations
  against Design §§3–4, using guarded attribute assertions. Record this as
  constant/API RED only, then add those literal declarations and prove GREEN.
  Only then construct the fixture patches below; absent patch targets or
  failed fixture setup must not count as source-validation behavior RED.
- [ ] Implement test-only `make_school_fixture(root)` generating synthetic
  19-page PP / 15-page school-MS PDFs, a 12-row original draft, retained review
  and four-row proposal. Use pypdf and isolated directories. A scoped
  `unittest.mock.patch` may replace private pinned source/staging/review
  SHA/size values with these test artifacts' expected identities and use
  `SYNTHETIC-F6-SOURCE` / `SYNTHETIC-F6-Q01-Q03-Q06-Q08` as parent/selected
  batch IDs. Assert the production constants equal the Design before entering
  the patch, and that they are restored afterwards. This is test isolation;
  production has no configurable identity bypass. Keep the source profile,
  question IDs, page/order, marks and selection constraints. Clearly label synthetic text/approval
  material, and never write it into real source or receipt directories.
- [ ] Write `F6ProposalTests.test_fixed_selection_waits_for_one_batch_approval`:

  ```python
  self.assertEqual(result["status"], "AWAITING_TRANSCRIPTION_APPROVAL")
  self.assertEqual((result["record_count"], result["marks"]), (4, 24))
  self.assertEqual(result["source_type"], "school_mock")
  self.assertEqual(result["issues"], [])
  self.assertEqual(result["required_approval"],
      f"USER APPROVED PDF TRANSCRIPTION BATCH {payload['batch_id']} {digest}")
  ```

  Also assert exact result keys and original draft/review bytes unchanged.
- [ ] Add negative subtests for Oxford/HKDSE profile, all12 selection, swapped
  IDs, renumbered Q6, duplicated/overlapping/incomplete partition, marks,
  difficulty/page drift, bools, missing/extra keys, invalid PDF/page counts,
  symlink inputs, stale hashes, digest mutation and absent separators.
  Require typed structural rejection, not a generic exception.
- [ ] Add review subtests: outline/missing solution, false review flags,
  issues, unknown primary/tag and necessary figure return REVIEW_REQUIRED,
  exact reasons and no required_approval. No guessed/cleared review.
- [ ] Add `test_q6_printed_number_and_q8_annotation_are_separate` and
  `test_digest_binds_notes_selection_and_is_path_independent`: reference
  digest is computed independently from canonical semantic JSON with NO LF;
  only expected editorial paragraphs move to review_notes, no math changes.
- [ ] Run `tests.integration.test_f6_school_mock.F6ProposalTests` RED;
  implement exact fixed-profile loader, review validation and inspection.
  Check six review flags against the pinned reviewed content, not merely a
  caller's claimed digest. Identity agreement is not a new content review.
- [ ] Run Tasks 1–3 GREEN; commit:
  `feat: validate F6 complete-question sub-batch evidence`.

## Task 4 — Exact source-approved F6 canonical bridge

**Files:** modify `f6_school_mock.py` and `test_f6_school_mock.py`.

**Interfaces:** `build_package(inputs, approval_text, output_dir, config) -> Path`;
consumes Task 3 eligible proposal and Task 2 manifest loader. No preflight
dependency; candidate bytes have independently specified expected values.

- [ ] Write `F6CanonicalTests` using the synthetic fixture only. Assert exact
  five paths and every Design §5 candidate field, original source question
  numbers, school identity, answer text, Q6/Q8 evidence, no held IDs, empty
  Chinese/translation_status=missing, no diagrams/explanation and incomplete
  enrichment. Independently assemble expected source-map and answer payload.
- [ ] Test no/malformed/wrong/parent12-row/stale approval; missing or outline
  MS despite an exact text must not create output. Assert old approval cannot
  bind revised content or selection; report does not constitute receipt.
- [ ] Test two unrelated roots byte-for-byte (all five files), manifest
  hashes/sizes/roundtrip, source/output overlap, existing target/artifact
  ancestors, symlink/dangling-symlink paths and cleanup on injected failure.
  Inject source change after validation; require rejection before rename and
  no published output. Include reserved URI/path characters.
- [ ] Run `tests.integration.test_f6_school_mock.F6CanonicalTests` RED;
  implement minimal atomic no-replace mapping with validated byte snapshots
  and source recheck. No canonical image creation or source text enrichment.
- [ ] Run the full F6 module plus earlier tests GREEN. Commit:
  `feat: map exactly approved F6 sources to V1.24 canonical`.

## Task 5 — Genesis preflight

**Files:** modify `v124_preflight.py` and `test_v124_preflight.py`.

**Interfaces:** `preflight_v124_import(request: V124PreflightRequest,
config: PipelineConfig) -> V124ImportPreflightResult`; parent=None initially.
Task 2 `_request` constructs valid inputs; no writer invocation in fixture setup.

- [ ] Write `V124GenesisPreflightTests` for synthetic TASK10-A: status exactly
  `READY FOR USER IMPORT APPROVAL`, before=677, parent genesis, zero parent
  ledger, detected/new based on actual synthetic rows, approved_count=0,
  projected=677+new. Independently compute digest projection expectations.
- [ ] Add counterpart collision/classification cases including full-answer
  exact duplicate, truthful second source with matching hashes, ambiguous
  matches, adaptation boundaries, mixed duplicate/eligible rows and malformed
  record/file integrity issues. Preserve all sixteen codes, sorting, blocking
  severity and unreadable-file versus rejected-record count distinctions.
  Query a few baseline examples from each formal layer including the promoted
  2023/2025/Oxford rows; do not output the full corpus.
- [ ] Add relocation determinism, zero-write, exact schema/metadata failures,
  forged equal genesis values and old-target approval/model rejection.
  Do not call unimplemented parent processing or claim its failure is RED.
- [ ] Run the genesis class RED; implement only no-parent preflight using the
  frozen V123 predicates/projections with Design's V124 substitutions.
- [ ] Run Tasks 1–5 GREEN. Commit:
  `feat: preflight V1.24 batches against the formal baseline`.

## Task 6A — Independent first-generation candidate verifier

**Files:** modify `v124_verification.py`; create `test_v124_candidate.py`.

**Interfaces:** `verify_v124_candidate(request: V124CandidateVerificationRequest,
config: PipelineConfig) -> VerificationReport`. Tests define
`_approved(package, config, parent=None) -> V124ApprovedBatch` restricted to
synthetic TASK10-A/B/C; it must reject real F6 batch IDs.
Define `_independent_candidate(root, approved_batches, contract)` in this test
file: test-owned SQLite/JSON construction, no production builder call.

- [ ] Assemble one valid synthetic approved preflight from Task 5. Build the
  test artifact with independently stated table/view SQL, ledger/projections,
  authority files, manifest/sums/rollback and candidate digest. Read the frozen
  baseline through a private copy only. Do not import production candidate
  builder, `_populate_database`, serializer/projection functions or DDL as
  the oracle. Independently check fixture SQLite integrity/FK and count before
  calling the verifier, so fixture mistakes cannot be recorded as verifier RED.
- [ ] Write `V124FirstVerifierTests`: valid artifact PASS with all24 named
  checks, read-only bytes unchanged. Check all historical objects/rows and
  candidate/selectable=0, baseline=677 and first aggregate order678.
- [ ] Corrupt each closure/authority layer separately: wrong genesis with equal
  forged supplied fields, source/canonical field change, file SHA/size/extra/
  missing file, manifest shape, schema, inherited record, ledger order/count,
  image identity, rollback and digest. Assert the relevant structured failure.
  Preserve counterpart missing-root/malformed-JSON exception boundaries.
- [ ] Run `tests.integration.test_v124_candidate.V124FirstVerifierTests` RED;
  implement independent reconstruction and all24 checks, including the exact
  `v123_preservation` label. Do not modify the oracle to match a broken verifier.
- [ ] Run earlier suites plus this class GREEN; commit:
  `feat: independently verify first V1.24 candidate generation`.

## Task 6B — First-generation atomic writer

**Files:** modify `v124_writer.py` and `test_v124_candidate.py`.

**Interfaces:** `build_v124_candidate(request: V124CandidateBuildRequest,
config: PipelineConfig) -> V124CandidateArtifacts`; requires Tasks 5 and 6A.

- [ ] Write `V124FirstWriterTests`: real synthetic READY result plus exact
  synthetic approval builds a verified one-batch generation. Compare semantic
  records/authority against independent expected projections, not against a
  second call to the same builder. Verify all677 original formal rows and
  inherited schema/metadata exactly preserved; new rows are not published.
- [ ] Cover forged preflight/candidate/manifest envelope, stale package bytes,
  wrong approval/genesis, existing output, existing artifact ancestors,
  symlink escape, source overlap, formal-root refusal, injected pre-rename
  failure and reserved URI characters. Preserve every parent/formal/source
  byte; cleanup only the temporary output owned by this attempt.
- [ ] Run the first-writer class RED, then implement private baseline copy,
  approved canonical reconstruction, collision defense, new namespace append,
  independent verifier and atomic no-replace publication.
- [ ] Build two independent synthetic roots; compare every contract-bound
  artifact byte, not just semantic hashes. Run Tasks 1–6B GREEN; commit:
  `feat: build approved first V1.24 candidate atomically`.

## Task 7 — Verified-parent preflight

**Files:** modify `v124_preflight.py` and `test_v124_preflight.py`.

**Interfaces:** Task 6B generation + V124CandidateVerificationRequest enters
Task 5 request as parent_candidate; result binds exact parent digest and ledger.

- [ ] Write `V124ParentPreflightTests` with a genuine GREEN synthetic first
  generation; assert its independent verification in setup. Test exact parent
  digest, parent taxonomy/indexes, full baseline retained, before=677+parent
  candidates and projected count closure.
- [ ] Test duplicate/collision against parent and formal rows, corrupted parent,
  substituted old version, changed parent during indexing, missing prefix
  authority, wrong root/request, genesis reuse and reordered ledger. Equivalent
  verified-parent roots must produce identical preflight digest.
- [ ] Run this class RED only after the first-generation setup passes.
  Implement verified prefix loading/index augmentation and change detection.
- [ ] Run all earlier suites GREEN and commit:
  `feat: bind V1.24 preflight to verified candidate parents`.

## Task 8 — Multi-batch writer/verifier and idempotent boundaries

**Files:** modify `v124_writer.py`, `v124_verification.py`,
`test_v124_candidate.py`.

**Interfaces:** ordered tuple of V124ApprovedBatch results from Tasks 5/7;
existing build/verification signatures unchanged. No new runner API.

- [ ] Write `V124MultiBatchTests`: second batch uses Task 7 READY parent;
  builder creates generation2 with exact ordered prefix and independent PASS.
  Third preflight indexes the entire accepted prefix, not only its last batch.
- [ ] Assert stale approval against a newer parent, duplicate batch ID, same
  source repeat, substituted canonical bytes, reordered prefix, forged counts/
  READY classifications and wrong existing generation all fail without changing
  prior files. Test verifier independently, including forged nested authority.
- [ ] Test idempotent boundaries explicitly: a repeated write to an existing
  artifact is no-replace, repeated batch in the prefix is rejected, and a
  read-only verification of the existing receipt-bound request returns the
  same identity. A replay must not be described as a new acceptance.
  Do not add a new receipt service or claim scheduler integration.
- [ ] Run this class RED only with Task 7 GREEN. Implement exact counterpart
  multi-prefix reconstruction and 24-check verification.
- [ ] Verify two-root multi-generation byte determinism; injected failure leaves
  all prior generations unchanged. Run all focused suites GREEN; commit:
  `feat: preserve V1.24 multi-batch parent and replay authority`.

## Task 9 — Historical regression, independent review and engineering checkpoint

**Files:** create `tests/regression/test_v124_historical_replay.py`,
`docs/reports/F6_V124_CANDIDATE_VERIFICATION.md`; update PROJECT_STATE.md.
Remediation may touch only approved Task 1–8 files, with its own valid RED.

**Interfaces:** reuse existing historical verifier requests/read-only replay
helpers; new regression extends coverage to exact published V1.23, not another
publication. Current formal view remains V1.23 and its677 rows.

- [ ] Add `V124HistoricalReplayTests` asserting unchanged package exports,
  historical model/API/digest ordering, all formal database identities and
  historical candidate/source/approval evidence. Use
  `tests.regression.test_v123_historical_replay` and
  `tests.integration.test_v123_promotion.selected_candidate/promotion_contract`
  for the existing verified V1.23 request, without rebuilding it.
- [ ] Assert no call can write a V124 candidate into a formal release path;
  do not introduce a permanent “V1.24 must never exist” historical invariant.
  Existing V1.23 approved-publication tests remain unchanged.
- [ ] Run all five new focused modules and existing HKDSE/Oxford/automation
  tests with fresh results. Record baseline/source/AGENTS/runner/old-candidate
  hashes before and after; use explicit known evidence paths, no broad scan.
- [ ] Obtain one separate whole-implementation reviewer under the repository
  independent-review requirement. Supply approved Design/Plan, task diff,
  RED/GREEN evidence and frozen identities. Reviewer checks source truthfulness,
  no approval bypass, independent oracle, duplicate handling, race/atomic
  boundaries and closed scope. Record actual reviewer/method, not self-review
  labelled independent. Remediate all Critical/Important findings and re-review.
- [ ] Run current maintained suite serially, discovering current test modules
  rather than copying the historical1331 count:

  ```bash
  "$JOY_PY" -B - <<'PY'
  from pathlib import Path
  import unittest
  modules = [".".join(p.with_suffix("").parts)
             for p in sorted(Path("tests").rglob("test_*.py"))]
  excluded = "tests.regression.test_task8b_legacy_pipeline_behavior"
  modules = [m for m in modules if m != excluded]
  loader = unittest.TestLoader()
  suite = unittest.TestSuite(loader.loadTestsFromName(m) for m in modules)
  result = unittest.TextTestRunner(verbosity=2).run(suite)
  print("maintained_modules", len(modules), "tests_run", result.testsRun)
  assert result.wasSuccessful() and not result.skipped
  assert not result.expectedFailures and not result.unexpectedSuccesses
  PY
  "$JOY_PY" -B releases/V1.18/verify_task6_release.py releases/V1.18
  git diff --check
  ```

  The single excluded legacy attribution module is the pre-existing maintained
  policy, not a new waiver. No new exclusion, skipped test or weaker hash.
  Historical formal verifiers through V1.23 and old candidate replay must
  actually pass in the included tests. Record current counts and log paths.
- [ ] Record independent review Critical0/Important0, all fresh gates, protected
  identity results, exact changed paths and any Minor limitation in the report.
  Explicitly distinguish synthetic engineering success from real F6 approval.
- [ ] Commit task paths explicitly (`feat: complete F6 V1.24 candidate gates`),
  synchronize docs and normal push. Do not stage AGENTS.md or runtime data.
  Proceed automatically to Task 10 after engineering gates, not to a real writer.

## Task 10 — Real F6 four-question transcription gate

**Files:** NEW ignored
`data/staging/f6-mock-1516-selected/proposal-000001/` (choose next unused ordinal
if already present; first inspect existing results rather than regenerate).
Report/state updates only if evidence has materially advanced.

**Interfaces:** validated F6 `inspect_proposal`; no canonical before exact
source approval. Actual source paths, hashes and review SHA are Design §3.

- [ ] Reuse the existing original staging and retained source review. Verify
  only the exact consumed PP/MS/staging/review files and needed page evidence;
  do not re-OCR, repeat the whole-paper preparation or scan other sources.
- [ ] Produce the four-row proposal using the fixed text/annotation separation,
  IDs/pages/marks/difficulty/taxonomy and held partition. Keep all12 old records
  untouched. Compare each selected question/solution with the retained
  evidence and independently check its mathematics; no problem is suppressed
  just because the four rows were initially chosen.
- [ ] Independently check source/annotation separation, all subparts and
  source-provided identity. Run inspect_proposal and calculate the actual
  semantic digest via an independent canonical serialization comparison.
  No fake signature, fabricated receipt or request template as approval.
- [ ] If a selected question has a real issue, preserve the proposal and report
  only its exact evidence/decision at PDF TRANSCRIPTION REVIEW. Do not silently
  drop it, add another question or widen the permitted subset.
- [ ] Otherwise stop at **USER DECISION REQUIRED — PDF TRANSCRIPTION APPROVAL**:
  selected batch ID, actual digest,4 questions/24marks, school identity,
  Q6 printed-number clarification, Q8 editorial note, selected/held IDs,
  source/evidence paths, unknown taxonomy counts, current formal677 unchanged.
  Provide the exact one-batch approval statement returned by the API.

## Task 11 — Conditional continuation after actual source approval

This task is in the sequence but cannot run until the user provides the exact
Task 10 approval. Do not treat Plan/execution approval as source approval.

**Files:** new ignored canonical/preflight evidence under
`data/staging/task14-v124-f6/`; actual received approval stored without editing
the old source review. No real candidate output yet.

- [ ] Reverify the received statement against unchanged proposal/source
  identities. Reuse an existing matching approved package if present; otherwise
  call F6 build_package once, validate five-file closure and exact projection.
- [ ] Recover current actual V1.24 candidate receipts. If none, use the
  independently reconstructed genesis; if already advanced, independently
  verify the complete current prefix. Never substitute old V1.23 generation3.
  A conflict is reported; no rollback or silent choice of an older parent.
- [ ] Run authoritative V124 preflight, compare equivalent-root deterministic
  results if not already recorded for the identical inputs, and report actual
  counts, issues, provenance relationship, digest and exact current parent.
- [ ] If blocked, keep all selected rows and report the exact classification
  and evidence. Do not manufacture a smaller READY batch.
- [ ] If READY, stop at **USER DECISION REQUIRED — REAL BATCH IMPORT** with:

  ```text
  USER APPROVED IMPORT BATCH <actual batch_id> <actual preflight_sha256> V1.24 PARENT <actual parent_candidate_digest>
  ```

  This is a requested approval, never a received one. Show detected/new/
  duplicate/rejected/ambiguous/adaptations, missing answer/explanation/image
  summaries, projected count and all issues. No promise of four new originals.
- [ ] Real writer execution is a separate exact-approved continuation, not
  automatically checked off here. It must recover the latest verified parent,
  revalidate unchanged READY/package authority under existing cycle.lock, verify
  any already accepted receipt first, append atomically only once if needed,
  independently verify and use existing local backup/recovery policy. No new
  automation registration or formal publication is implied.

## Coverage and written-Plan self-review

| Approved Design | Owning Plan tasks |
|---|---|
| §1 authority, reduced review and scope | Global constraints; 9–11 |
| §2 exact baseline, namespace and genesis | 1–2,5–8 |
| §3 fixed source/selection/held evidence | 3–4,10 |
| §4 proposal/digest/approval | 3–4,10–11 |
| §5 five-file/23-field canonical projection | 4,11 |
| §6 models/effective state/atomicity/24-check verifier | 1–2,5–9 |
| §7 closed files, valid RED and regression | file map; 1–9 |
| §8 user gates, no formal growth claim | 10–11 |

Self-review checks: source digest no-LF versus genesis LF distinguished; strict
loader precedes F6 mapping; first generation is genuinely usable before parent
preflight; parent preflight precedes multi-batch writer; independent verifier
oracle is not builder output; module-local APIs preserve all historical exports;
all five Review Focus items have explicit tests. No scope expansion or omitted
Design requirement identified in this document review. This is author
self-review, not an independent implementation review or passing test result.

Current stop: **USER DECISION REQUIRED — F6 / V1.24 IMPLEMENTATION PLAN REVIEW**.
Recommend Native / Inline; await written Plan approval and execution confirmation.
