# Task 10A V1.20 Multi-Batch Candidate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkboxes for execution tracking.

**Status:** HUMAN GATE A AUTHORITY APPROVED — INDEPENDENT REVIEW PASSED; IMPLEMENTATION NOT AUTHORIZED

**Goal:** Add a versioned, append-only V1.20 candidate lifecycle that builds
one deterministic candidate from the immutable formal V1.19 baseline plus an
ordered sequence of independently preflighted and parent-bound approved
batches, without changing any historical V1.19 contract or implementing
formal V1.20 promotion.

**Architecture:** Keep every Task 9A–9D V1.19 public model/API/digest/schema
unchanged. Add exact V1.20 carriers, a narrow Task 9B V1.20 target projection,
an effective-state preflight, parent-bound approval, full-prefix candidate
rebuild, and an independent verifier. Each candidate generation is built in a
private staging sibling, verified, and atomically published without replacing
the prior generation.

**Tech Stack:** Python 3.12 standard library, frozen dataclasses, `pathlib`,
`hashlib`, canonical JSON, `sqlite3`, `unittest`, existing `PipelineConfig`,
`ArtifactRef`, and `VerificationReport`. No new dependency is authorized.

**Spec:**
`docs/superpowers/specs/2026-09-13-task10a-v120-multi-batch-candidate-design.md`

## Global Constraints

- [ ] Do not begin any implementation step until this Design and Plan are
      independently reviewed, committed, pushed, and the user gives exact
      `V1.20 AUTHORITY IMPLEMENTATION AUTHORIZATION`.
- [ ] Never edit files under `releases/V1.18/`, `data/baselines/V1.18/`, or
      `releases/V1.19/`.
- [ ] Preserve exact V1.18 SHA/count and exact V1.19 SHA/count/release digest.
- [ ] Preserve every Task 9A–9D V1.19 public signature, type, literal digest,
      approval statement, schema, and test meaning.
- [ ] Write behavior tests before the production behavior they specify; an
      import, fixture, setup, syntax, or environment failure is not a valid
      behavior RED.
- [ ] Never weaken historical tests to fit new implementation.
- [ ] Never create a formal `releases/V1.20/` tree in this Plan.
- [ ] Real V1.20 batches require their own exact parent-bound approval. A
      synthetic test approval never authorizes real data.
- [ ] Keep formal retrieval on V1.19/502. Candidate preview is explicit and
      staging-only.
- [ ] Do not read or hash the historical V1.16 ZIP.
- [ ] Do not add CLI, App/API, PDF/OCR, generic workflow/version frameworks,
      arbitrary future versions, or new question generation.

Use the bundled project runtime when the host has no `python` command:

```bash
CODEX_PYTHON=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

Every RED/GREEN record must include collected, PASS, FAIL, ERROR, skip,
expected-failure, and exit code.

## Closed Future File Scope

Current Task 0 docs-only scope is exactly this Design, this Plan, and
`PROJECT_STATE.md`. After that checkpoint, a later explicit implementation
authorization is closed to the following future implementation and completion
scope; the `PROJECT_STATE.md` entry below denotes its later completion update:

```text
NEW       src/joy_m2/ingest/v120_models.py
NEW       src/joy_m2/ingest/v120_manifest.py
NEW       src/joy_m2/ingest/v120_projection.py
NEW       src/joy_m2/ingest/v120_preflight.py
NEW       src/joy_m2/ingest/v120_writer_profiles.py
NEW       src/joy_m2/ingest/v120_writer.py
NEW       src/joy_m2/ingest/v120_verification.py
MODIFIED  src/joy_m2/ingest/adapter.py
MODIFIED  src/joy_m2/ingest/source_mapping.py
MODIFIED  src/joy_m2/ingest/__init__.py
NEW       tests/unit/test_v120_models.py
NEW       tests/integration/test_v120_adapter_projection.py
NEW       tests/integration/test_v120_preflight.py
NEW       tests/unit/test_v120_writer_primitives.py
NEW       tests/integration/test_v120_candidate.py
NEW       tests/regression/test_v119_historical_replay.py
FIXTURE   tests/fixtures/task10a/v120-batch-a/**
FIXTURE   tests/fixtures/task10a/v120-batch-b/**
FIXTURE   tests/fixtures/task10a/v120-batch-c/**
DOC       PROJECT_STATE.md
NEW DOC   docs/reports/TASK10A_VERIFICATION.md
```

`PROJECT_STATE.md` is updated now for the docs-only Gate-A authority checkpoint
and may be updated again only after a future implementation review.
`docs/reports/TASK10A_VERIFICATION.md` is future-only completion evidence and
must not be created at Gate A. No ninth production module, fourth fixture
group, project script, dependency, or formal-data path may be added without a
reviewed scope amendment.

## Task 0 — Authority checkpoint and implementation hold

**Files:**

- Create:
  `docs/superpowers/specs/2026-09-13-task10a-v120-multi-batch-candidate-design.md`
- Create:
  `docs/superpowers/plans/2026-09-13-task10a-v120-multi-batch-candidate.md`
- Modify: `PROJECT_STATE.md`

- [ ] Verify both authority documents have zero open placeholder or conflicting
      V1.19/V1.20 statement.
- [ ] Obtain independent authority review with Critical 0 and Important 0.
- [ ] Run current maintained and frozen baseline gates.
- [ ] Commit docs only and ordinary-push the existing branch.
- [ ] Stop at:

```text
USER DECISION REQUIRED — V1.20 AUTHORITY IMPLEMENTATION AUTHORIZATION
```

No following checkbox is authorized by Task 0 completion alone.

## Task 1 — Phase A: Versioned public authority-model RED to GREEN

**Files:**

- Create: `tests/unit/test_v120_models.py`
- Create: `src/joy_m2/ingest/v120_models.py`

### Step 1.1 — Write exact model tests first

- [ ] Add `V120ModelContractTests` that independently locks exact fields,
      field order, annotations, no defaults, frozen behavior, exact runtime
      types, tuple copying, path rules, lowercase SHA rules, `bool` rejection,
      fixed literals, and illegal-envelope rejection for:

```text
V120BatchImportManifest
V120AdaptedImportPackage
V120BatchLedgerEntry
V120EffectiveState
V120PreflightRequest
V120ImportPreflightReport
V120ImportPreflightResult
V120ImportApproval
V120ApprovedBatch
V120CandidateContract
V120CandidateBuildRequest
V120CandidateVerificationRequest
V120CandidateArtifacts
```

- [ ] Lock the exact 18-field manifest, exact 34-field report, exact fixed
      baseline/target constants, genesis state, contiguous ledger invariants,
      count closure, candidate/issue ordering, exact approval statement,
      approved-batch/request/result carriers, ArtifactRef kinds, and exact
      contract tuples.
- [ ] Assert current `BatchImportManifest`, `ImportPreflightReport`, and all
      V1.19 writer/promotion models remain byte-for-byte/source-signature
      compatible and reject V1.20 exactly as before.

Run before creating production:

```bash
$CODEX_PYTHON -m unittest -v tests.unit.test_v120_models
```

Expected RED: module/symbols do not exist. Test discovery and all historical
imports succeed; no unrelated existing test fails.

### Step 1.2 — Add the minimum carriers

- [ ] Create only the approved frozen dataclasses and their exact validation in
      `v120_models.py`.
- [ ] Reuse unchanged `ImportFileEvidence`, `ImportCandidate`,
      `ImportAdaptation`, `ImportIssue`, `ArtifactRef`, and
      `VerificationReport`; do not clone them.
- [ ] Do not add builder, parser, preflight, digest, filesystem, or SQLite
      behavior.

Run:

```bash
$CODEX_PYTHON -m unittest -v tests.unit.test_v120_models
$CODEX_PYTHON -m unittest -v tests.unit.test_ingest_models \
  tests.unit.test_v119_writer_models tests.unit.test_v119_promotion_models
```

Expected GREEN: every new model test and all selected historical model tests
pass with zero skips/expected failures.

## Task 2 — Phase B: V1.20 canonical target-projection RED to GREEN

**Files:**

- Create: `tests/integration/test_v120_adapter_projection.py`
- Create: `src/joy_m2/ingest/v120_manifest.py`
- Create: `src/joy_m2/ingest/v120_projection.py`
- Modify: `src/joy_m2/ingest/adapter.py`
- Modify: `src/joy_m2/ingest/source_mapping.py`

### Step 2.1 — API-existence RED, then no-behavior projection scaffolds

- [ ] Before creating/modifying any Phase-B production file, test the exact
      modules, symbols, signatures, annotations, return types, and module-level
      export boundary for `load_v120_import_manifest()`,
      `adapt_mmd_package_v120()`, and
      `adapt_mmd_package_from_mapping_v120()`.
- [ ] Run only those API tests. Missing modules/symbols are valid only for this
      API-existence RED.
- [ ] Create the minimum V1.20 manifest/projection modules and entry-point
      signatures. Every entry point and private projector must immediately
      raise `NotImplementedError`; no validation, file read/write, hashing,
      projection, cleanup, or adaptation behavior is allowed.
- [ ] Re-run only API-existence tests to GREEN.

### Step 2.2 — Prove projection behavior RED

- [ ] Use existing reviewed Task 9B representative and explicit-mapping
      fixtures; do not copy an external real-user archive into Git.
- [ ] Test the exact results of both V1.20 adapter entry points.
- [ ] Test `load_v120_import_manifest()` with strict UTF-8/JSON, V1.20-new
      duplicate-key rejection, exact-key, exact-type, and V1.19/V1.20
      separation cases without changing the historical loader.
- [ ] Lock package layout, canonical V1.20 manifest bytes, file evidence, and
      output atomicity.
- [ ] Lock same valid source-selection/mapping equivalence: V1.19 and V1.20
      candidate JSON, raw source, source-map, answer, and image bytes are
      identical; only versioned manifest schema/target authority differs.
- [ ] Lock outer-ZIP order/metadata/root independence and exact V1.19 adapter
      replay.

Run after the signature-only scaffolds but before any Phase-B behavior:

```bash
$CODEX_PYTHON -m unittest -v tests.integration.test_v120_adapter_projection
```

Expected RED: every test imports and reaches the intentional
`NotImplementedError`; import/setup/fixture/test-construction failure is not a
valid behavior RED. Existing Task 9B imports and fixtures remain valid.

### Step 2.3 — Implement one narrow target projector

- [ ] Create `v120_manifest.py` with only the strict V1.20 typed manifest
      decoder; do not broaden historical `load_import_manifest()`.
- [ ] Add only validated output projection and V1.20 manifest/result assembly
      to `v120_projection.py`.
- [ ] Refactor the two existing adapter paths only enough to send already
      validated Source IR/output components through the projector.
- [ ] Keep both historical V1.19 entry-point signatures and output bytes exact.
- [ ] Append the V1.20 explicit-mapping entry point only to
      `source_mapping.__all__`; do not export it from root `joy_m2.ingest`.
- [ ] Add no target-version field to `MmdSelection` or `MmdAdapterManifest`.

Run:

```bash
$CODEX_PYTHON -m unittest -v \
  tests.integration.test_v120_adapter_projection \
  tests.integration.test_mmd_adapter \
  tests.integration.test_mmd_explicit_mapping
```

Expected GREEN: V1.20 projection passes and current Task 9B count remains
unchanged and fully green.

## Task 3 — Phases C–G behavior RED and H/I API scaffolds

**Files:**

- Modify: `tests/unit/test_v120_models.py`
- Create/modify: `tests/integration/test_v120_preflight.py`
- Create/modify: `tests/integration/test_v120_candidate.py`
- Create: `src/joy_m2/ingest/v120_preflight.py`
- Create: `src/joy_m2/ingest/v120_writer.py`
- Create: `src/joy_m2/ingest/v120_verification.py`
- Create future fixtures:
  `tests/fixtures/task10a/v120-batch-{a,b,c}/**`

No preflight, writer, or verifier behavior beyond the signature-only scaffolds,
and no approval consumption/binding behavior, may be added until its
corresponding group below has a valid RED. Task 3 establishes all C–G behavior
REDs; Tasks 5.1 and 6.1 independently establish the detailed verifier-I and
writer-H REDs before implementing those layers.

### Step 3.1 — API-existence RED, then no-behavior scaffolds

- [ ] Before creating any of the three production modules, add exact module,
      symbol, parameter-name/order/annotation, return-annotation, and no-extra-
      authority tests for `preflight_v120_import()`, `build_v120_candidate()`,
      and `verify_v120_candidate()`.
- [ ] Run the API test alone. Missing module/symbol/signature is valid only for
      this API-existence RED.
- [ ] Create the three minimal modules containing required imports, exact
      signatures, and an immediate `NotImplementedError`; no validation, file
      read, hash, SQLite, output, cleanup, or report behavior is allowed.
- [ ] Re-run only the API-existence tests to GREEN.

The scaffolds make subsequent behavior tests importable. A subsequent import
or signature failure is not an acceptable behavior RED.

### Step 3.2 — Phase C effective-state and digest RED

- [ ] First batch over exact V1.19 produces genesis parent digest
      `4ff624aca875b0191fe8a617516d2919c6d700ce69c5a3b5d236adcf7ecc59f1`.
- [ ] Exact V1.19 SHA/size/release digest/formal 502-row view are required.
- [ ] V1.18, an altered V1.19, a 497-row-only projection, wrong manifest
      identity, or wrong release digest fails before a READY result.
- [ ] `before_count`, `parent_batch_count`, and projected count close.
- [ ] Independent literal construction of the exact 13-key preflight payload
      locks manifest/preflight digest values and cross-root equality.

### Step 3.3 — Phase D approval binding RED

- [ ] Using the already-GREEN exact carriers, lock statement/binding behavior:

```text
USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> V1.20 PARENT <parent_candidate_digest>
```

- [ ] Reject wrong batch/digest/target/parent/statement, reordered/noncontiguous
      batch tuples, and a preflight/approval pair from a different parent.
- [ ] Assert the historical V1.19 approval statement/parser remains unchanged.

### Step 3.4 — Phase E first-batch RED

- [ ] Lock one READY first batch against formal V1.19, zero prior batches,
      correct genesis parent, exact file/candidate/image/report/digest closure,
      and no writes.
- [ ] Lock duplicate/collision against any of the 502 formal rows and unchanged
      sixteen-code issue semantics.

### Step 3.5 — Phase F second-batch RED

- [ ] Use an independently authored, internally valid batch-A candidate
      generation as the parent oracle; it must not be produced by the writer
      under test.
- [ ] Lock second READY batch against `502 + len(A)`, exact parent digest,
      ledger prefix, and projected aggregate count.
- [ ] A stale preflight after changing the parent generation and an approval
      reused against another parent must fail.

### Step 3.6 — Phase G third-batch/order/collision RED

- [ ] Lock three accepted batches in semantic acceptance order A/B/C.
- [ ] Physical fixture/member/filesystem order changes do not change results.
- [ ] Semantic batch tuple reorder changes parent-chain validity and candidate
      identity; it is never silently sorted.
- [ ] Lock duplicate/ID/source/fragment/normalized-text/image collisions against
      formal V1.19 and any earlier V1.20 batch.
- [ ] Lock identical content-addressed images as one physical file with all
      ordered bindings, and different-byte destination claims as rejection.

Run both new test modules before production:

```bash
$CODEX_PYTHON -m unittest -v \
  tests.unit.test_v120_models \
  tests.integration.test_v120_preflight \
  tests.integration.test_v120_candidate
```

Expected RED: all modules, symbols, signatures, carriers, and fixtures load
correctly; every behavior case reaches an immediate scaffold
`NotImplementedError`. No import/setup/fixture/test-construction failure is
accepted. Record every expected failure by phase.

## Task 4 — Phase C/E minimum genesis preflight GREEN

**Files:**

- Modify: `src/joy_m2/ingest/v120_preflight.py`
- Modify: `src/joy_m2/ingest/v120_models.py`

- [ ] Use the already-GREEN exact V1.20 carriers; do not change their contract
      to make behavior tests pass.
- [ ] Implement exact formal V1.19 validation, genesis state, V1.20 manifest
      reconstruction, Task 9A canonical package validation, compact 502-row
      indexes, exact issue taxonomy, report/count closure, and 13-key digest.
- [ ] Implement the minimum V1.20-private normalization/collision behavior in
      the authorized V1.20 modules. Do not extract a shared collision module
      and do not change historical `preflight.py` or `preflight_import()`.
- [ ] Keep preflight strictly read-only and support only
      `parent_candidate=None` at this checkpoint.

Run:

```bash
$CODEX_PYTHON -m unittest -v \
  tests.integration.test_v120_preflight.V120GenesisPreflightTests \
  tests.integration.test_v120_preflight.V120FormalBaselineCollisionTests
```

Expected GREEN: Phase C/E genesis and formal-baseline collision tests pass;
later parent/writer/verifier groups remain deliberate RED.

## Task 5 — Phase I: Independent verifier RED to GREEN

The verifier is implemented before parent-based Phase F GREEN because
`V120PreflightRequest.parent_candidate` deliberately requires a fully verified
parent. This dependency-aware order does not weaken RED-first: Task 3 has
already proved the C–G behavior REDs and the verifier API-existence RED; Step
5.1 now establishes the complete verifier-I primitive/behavior RED before any
verifier behavior is implemented. Step 6.1 later establishes writer-H RED, and
Task 9 establishes any newly uncovered J RED before its correction.

**Files:**

- Create: `tests/unit/test_v120_writer_primitives.py`
- Modify: `tests/integration/test_v120_candidate.py`
- Create: `src/joy_m2/ingest/v120_writer_profiles.py`
- Modify: `src/joy_m2/ingest/v120_verification.py`

### Step 5.1 — Complete primitive/verifier RED before production

- [ ] Independently author exact normalized DDL, manifest, authority, rollback,
      SHA, and candidate-digest oracles plus a minimal valid parent candidate
      tree. The candidate-digest oracle must literally construct the exact
      ten-key image-projection objects, ordered binding array, and per-candidate
      `candidate_image_paths` arrays without importing production digest code.
- [ ] Lock the exact 24 ordered verifier checks.
- [ ] Lock malformed JSON as `InputFormatError`; parsed-invalid/mismatch as a
      structured FAIL report; verifier non-mutation in both cases.
- [ ] Lock missing/extra/tampered artifacts, wrong ArtifactRef, SQLite
      integrity/FK/schema/row failure, noncontiguous ledger, wrong parent chain,
      wrong preflight/approval, duplicate leakage, wrong counts/digest, and a
      formal/release path.
- [ ] Lock candidate-root symlink leaf, symlink ancestor, symlink loop, resolved
      escape, and symlinked-artifact cases as structured FAIL with no mutation.
- [ ] Run tests and confirm failures are missing verifier behavior, not a bad
      oracle or fixture.

### Step 5.2 — Implement independent read-only verifier

- [ ] Add exact DDL constants and pure canonical/hash/path helpers in
      `v120_writer_profiles.py`.
- [ ] Implement `verify_v120_candidate()` without importing/calling either the
      writer or production preflight implementation.
- [ ] Reconstruct every approved batch preflight/approval and effective-state
      prefix; inspect the complete tree and SQLite independently.
- [ ] Keep the verifier read-only; require a symlink-free strict staging
      descendant and fail the formal boundary for any `releases/V1.20` path.

Run:

```bash
$CODEX_PYTHON -m unittest -v \
  tests.unit.test_v120_writer_primitives \
  tests.integration.test_v120_candidate.V120VerifierTests
```

Expected GREEN: primitive and verifier tests pass; writer publication tests
remain RED.

## Task 6 — Phase H: Aggregate full-prefix writer RED to GREEN

**Files:**

- Modify: `tests/integration/test_v120_candidate.py`
- Modify: `src/joy_m2/ingest/v120_writer.py`

### Step 6.1 — Complete writer RED group

- [ ] Lock exact public signature and no extra authority argument.
- [ ] Lock first full-prefix candidate tree, exact layout, four Task 10 tables,
      33-column preview view, user version 120, V1.19 logical preservation,
      candidate status/selectability, authority artifacts, content-addressed
      images, manifest, sums, rollback, and candidate digest.
- [ ] Lock the builder calling the independent verifier before publication.
- [ ] Lock missing approval, non-READY preflight, stale parent, wrong tuple
      order, image mutation, output conflict, package/output/baseline overlap,
      and source-swap/TOCTOU controls.
- [ ] Independently lock output symlink leaf, existing symlink ancestor,
      symlink loop, resolved staging escape, and symlinked staged-artifact
      rejection before any approved output is created.
- [ ] Confirm the complete writer group is valid RED before creating
      `v120_writer.py`.

### Step 6.2 — Implement minimum full-prefix writer

- [ ] Revalidate all nested authority before creating a temp directory.
- [ ] Start from exact V1.19 bytes for every build; never copy a prior candidate
      database.
- [ ] Build one private staging sibling, use one SQLite transaction, stage
      artifacts deterministically, run the verifier, and atomically rename
      without replacement.
- [ ] Enforce a symlink-free strict staging descendant for both private and
      final roots; lexical containment alone is insufficient.
- [ ] Clean only the writer-owned private tree on failure.

Run:

```bash
$CODEX_PYTHON -m unittest -v tests.integration.test_v120_candidate
```

Expected GREEN for first-batch writer and verifier groups. Multi-batch and
determinism groups may remain RED until Tasks 7–9.

## Task 7 — Phase F: Second approved batch accumulation GREEN

**Files:**

- Modify: `src/joy_m2/ingest/v120_preflight.py`
- Modify: `src/joy_m2/ingest/v120_writer.py`
- Modify: `src/joy_m2/ingest/v120_verification.py`

- [ ] Require parent verification PASS, then derive the exact effective state
      independently from the verified parent manifest, SQLite, and complete
      approved prefix. Take `candidate_digest` from the verified manifest,
      never from generic `VerificationReport` fields.
- [ ] Preflight batch B against formal V1.19 plus batch A.
- [ ] Rebuild A+B from V1.19; do not mutate A's candidate root.
- [ ] Enforce ordinal 2, parent digest equality, count closure, batch/row/image
      provenance, and complete prefix verification.
- [ ] Prove a failed/rejected B leaves A byte-identical and creates no B output.

Run:

```bash
$CODEX_PYTHON -m unittest -v \
  tests.integration.test_v120_preflight.V120SecondBatchTests \
  tests.integration.test_v120_candidate.V120SecondBatchCandidateTests
```

Expected GREEN: all Phase F tests pass.

## Task 8 — Phase G: Cross-batch collision and third-order GREEN

**Files:**

- Modify only, if tests prove needed:
  `src/joy_m2/ingest/v120_preflight.py`
- Modify only, if tests prove needed:
  `src/joy_m2/ingest/v120_verification.py`

- [ ] Make all already-proven cross-batch duplicate/collision RED cases GREEN
      without changing code names, evidence objects, issue ordering, or counts.
- [ ] Make A/B/C order and parent-chain tests GREEN.
- [ ] Confirm exact duplicate against an earlier candidate is not new, and any
      blocking batch remains unappendable as a whole.
- [ ] Confirm enrichment remains non-blocking and no data is auto-filled.

Run:

```bash
$CODEX_PYTHON -m unittest -v \
  tests.integration.test_v120_preflight \
  tests.integration.test_v120_candidate
```

Expected GREEN: every Phase C–I behavior group passes.

## Task 9 — Phase J: Deterministic rebuild, atomicity, and rollback

**Files:**

- Modify: `tests/integration/test_v120_candidate.py`
- Modify only after a newly observed valid RED:
  `src/joy_m2/ingest/v120_writer.py`
- Modify only after a newly observed valid RED:
  `src/joy_m2/ingest/v120_verification.py`

- [ ] Before any correction, prove RED for every uncovered determinism or
      atomicity case.
- [ ] Build the same A/B/C logical prefix under independent absolute roots,
      temp roots, and package roots; compare complete tree bytes, SQLite byte
      SHA, manifest, sums, rollback, authority artifacts, images, candidate
      digest, rebased ArtifactRef identity, and ordered checks. ArtifactRefs
      are compared as candidate-relative path plus `sha256`, `size_bytes`, and
      `kind`; their root-specific absolute `path` fields are never required to
      be equal.
- [ ] Reorder only physical files/members and retain identical output.
- [ ] Reorder semantic batch tuple and require parent-chain rejection.
- [ ] Inject failure before transaction, during transaction, during file write,
      before verification, during verification, and at no-replace rename;
      previous candidates and both formal baselines remain unchanged.
- [ ] Keep independent leaf/ancestor/loop/artifact-symlink cases; removing any
      one production symlink check must fail its matching regression.
- [ ] Lock declarative rollback shape and candidate-digest/closure precondition.

Run:

```bash
$CODEX_PYTHON -m unittest -v tests.integration.test_v120_candidate
```

Expected GREEN: every Phase J case passes with no leaked temp tree.

## Task 10 — Phase K: Historical V1.19 replay and public surface

**Files:**

- Create: `tests/regression/test_v119_historical_replay.py`
- Modify: `src/joy_m2/ingest/__init__.py`

### Step 10.1 — Public-surface RED

- [ ] Before modifying `__init__.py`, test the exact current `__all__` as an
      unchanged prefix and the exact approved V1.20 append-only suffix.
- [ ] Test `joy_m2.ingest.source_mapping.__all__` as its unchanged historical
      four-name prefix plus only `adapt_mmd_package_from_mapping_v120`; assert
      that explicit-mapping name remains absent from root `joy_m2.ingest`.
- [ ] Confirm private profile/projection/filesystem helpers and approval error
      classes are absent.
- [ ] Run and record the missing-public-surface RED.

### Step 10.2 — Append only approved public names

- [ ] Export only Design-approved V1.20 carriers and functions, after their
      implementation is GREEN.
- [ ] Do not reorder/remove/alias current V1.19 names.

### Step 10.3 — Literal historical replay

- [ ] Re-run the frozen Task 9A literal manifest/preflight digest oracle.
- [ ] Re-run Task 9B canonical/golden equivalence and explicit mapping.
- [ ] Re-run Task 9C historical approval, candidate byte identity, and verifier.
- [ ] Re-run Task 9D release digest, dry-run/formal identity, verifier, and
      Gate-D statement.
- [ ] Assert no V1.19 constant was changed to V1.20 and no historical parser
      accepts V1.20.

Run:

```bash
$CODEX_PYTHON -m unittest -v tests.regression.test_v119_historical_replay
$CODEX_PYTHON -m unittest -v \
  tests.integration.test_ingest_preflight \
  tests.integration.test_mmd_adapter \
  tests.integration.test_mmd_explicit_mapping \
  tests.integration.test_v119_writer \
  tests.integration.test_v119_promotion
```

Expected GREEN: exact historical results and public surface pass.

## Task 11 — Phase L: Real operational read-only dry-run and Human Gate

This phase does not authorize a real candidate write.

**Files:** No tracked production/test/fixture change is expected.

- [ ] Obtain explicit source/privacy/access authority for the selected real
      MMD/MMD.ZIP before reading it.
- [ ] Adapt it only to a disposable temporary/staging package with the V1.20
      target projection.
- [ ] Run exact V1.20 preflight against the latest independently verified
      effective candidate state.
- [ ] Report source/canonical identities, parent candidate digest, batch ID,
      preflight SHA, detected/new/duplicate/rejected/ambiguous/adaptation and
      enrichment counts, issues, and projected aggregate count.
- [ ] Reconfirm V1.18 and formal V1.19 bytes/counts and zero formal V1.20
      artifacts.
- [ ] Stop before writer invocation and require this exact per-batch form:

```text
USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> V1.20 PARENT <parent_candidate_digest>
```

A prior V1.19 approval, source-mapping approval, synthetic approval, or approval
for a different parent is invalid.

## Task 12 — Full gates, independent implementation review, and checkpoint

### Step 12.1 — Focused and maintained gates

Run:

```bash
$CODEX_PYTHON -m unittest -v \
  tests.unit.test_v120_models \
  tests.integration.test_v120_adapter_projection \
  tests.integration.test_v120_preflight \
  tests.unit.test_v120_writer_primitives \
  tests.integration.test_v120_candidate \
  tests.regression.test_v119_historical_replay

rg --files tests \
  | rg '(^|/)test_[^/]*\.py$' \
  | rg -v '^tests/regression/test_task8b_legacy_pipeline_behavior\.py$' \
  | sort \
  | sed 's#/#.#g; s#\.py$##' \
  | xargs $CODEX_PYTHON -m unittest -v
$CODEX_PYTHON releases/V1.18/verify_task6_release.py releases/V1.18
```

The deterministic module enumeration is required because the maintained test
subdirectories are namespace-style; recursive `unittest discover -s tests`
collects zero tests in the approved runtime and is not a valid gate.

- [ ] Run the formal V1.19 independent verifier through its existing committed
      verification test/command and require 18/18 PASS.
- [ ] Require all collected maintained tests PASS with zero skip and zero
      expected failure. The count must be the actual new total, not a guessed
      target; it must be no lower than the current 711-test baseline plus all
      newly collected Task 10 tests.
- [ ] Require `git diff --check` PASS.
- [ ] Re-hash V1.18/V1.19 and verify 497/502 counts and exact release digest.
- [ ] Confirm `releases/V1.20/` does not exist.

### Step 12.2 — Independent implementation review

- [ ] Review exact scope and public types.
- [ ] Review historical V1.19 non-mutation and literal replay.
- [ ] Review append-only ledger order, genesis/prefix digests, stale approval
      rejection, effective-state duplicate detection, full-prefix rebuild,
      independent verifier, atomicity/rollback, candidate/formal separation,
      and YAGNI boundary.
- [ ] Require Critical 0 and Important 0. Convert every finding to a focused
      RED before remediation and re-review.

### Step 12.3 — Commit and push

- [ ] Inspect exact diff and ensure only this Plan's closed file scope changed.
- [ ] Commit implementation separately from completion docs and any future real
      data/candidate evidence.
- [ ] Use explicit `git add <paths>`, never `git add .`.
- [ ] Ordinary-push the current upstream only after full gates and clean review.
- [ ] Update `PROJECT_STATE.md` and create
      `docs/reports/TASK10A_VERIFICATION.md` in a separate docs checkpoint.

Suggested implementation commit:

```text
feat: add V1.20 multi-batch candidate authority
```

Suggested completion-doc commit:

```text
docs: close Task 10A V1.20 candidate implementation
```

Do not create a formal release commit or promotion tag.

## Required Exit Evidence

Implementation, if later authorized, is complete only when all of the following
are demonstrated:

- [ ] first V1.20 batch from clean V1.19 baseline;
- [ ] second valid batch against accumulated state;
- [ ] third-batch semantic ordering and path/order determinism;
- [ ] stale preflight and wrong-parent approval rejection;
- [ ] duplicate/collision against V1.19 and earlier V1.20 batches;
- [ ] failed later batch preserves every prior generation;
- [ ] ledger-to-question/source/mapping provenance closure;
- [ ] deterministic full-prefix rebuild and independent verification;
- [ ] formal V1.19 stays 502 and formal retrieval stays V1.19;
- [ ] V1.18/V1.19 formal bytes and historical authority remain exact;
- [ ] no formal V1.20 tree, promotion model, promotion API, or promotion action;
- [ ] complete maintained and frozen gates PASS;
- [ ] independent review reports Critical 0 / Important 0.

## Final Hold Point

This Plan is intentionally not self-authorizing. After the current docs-only
checkpoint is reviewed, committed, and pushed, stop at:

```text
USER DECISION REQUIRED — V1.20 AUTHORITY IMPLEMENTATION AUTHORIZATION
```

No test, fixture, production file, candidate artifact, or database write in
Tasks 1–12 may begin before that exact next authorization.
