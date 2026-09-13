# Task 9D Formal V1.19 Promotion Implementation Plan

> **Execution:** Follow this Plan task by task. Do not create this repository's
> `releases/V1.19/`. Stop after the verified dry-run and technical checkpoint at
> HUMAN GATE D.

**Goal:** Implement and independently verify a deterministic promotion layer
that converts the exact approved Task 9C real candidate into a 502-question
formal V1.19 release tree under staging, while preserving V1.18 and requiring a
separate digest-bound approval before formal publication.

**Architecture:** The builder re-verifies the typed Task 9C candidate, copies it
to a private staging build, adds the exact formal promotion tables/view and
version metadata in one transaction, writes canonical manifest/sums/rollback,
and atomically publishes only to a non-formal staging dry-run root. An
independent verifier reconstructs every authority and semantic digest. A
separate publication API accepts only the exact Gate D carrier and atomically
creates the otherwise absent formal root; it is tested only in temporary repo
roots and is not invoked against the real repository in this Plan.

**Authority:**
`docs/superpowers/specs/2026-09-13-task9d-v119-promotion-design.md` at Design
commit `4f9924a712d02feb889cbd24e5c3867a9daba31c`.

**Baseline before execution:** branch `task8b/pipeline-migration`; Design HEAD;
clean index/worktree; exact V1.18 SHA
`fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`;
real candidate SQLite SHA
`9d30cf444e9d6686128f884d5a3cf57f4e58ce544b7933d7a0a47ec0e8212d20`;
real candidate verifier 16/16 PASS; `releases/V1.19/` absent.

**Runtime:** use the established Codex Python runtime with `PYTHONPATH=src` if
`python` is unavailable.

---

## Closed scope

### Phase A and B implementation files

- Create `src/joy_m2/ingest/promotion_models.py`
- Create `src/joy_m2/ingest/promotion.py`
- Create `src/joy_m2/ingest/promotion_verification.py`
- Modify `src/joy_m2/ingest/__init__.py`
- Create `tests/unit/test_v119_promotion_models.py`
- Create `tests/unit/test_v119_promotion_primitives.py`
- Create `tests/integration/test_v119_promotion.py`

### Completion evidence

- Modify `PROJECT_STATE.md`
- Create `docs/reports/TASK9D_VERIFICATION.md`

### Explicitly excluded

No other `src/`, `tests/`, config, script, CLI, Task 9A/9B/9C, database,
export, release, data, legacy, frozen, or formal release file may change.
Generated real dry-runs are ignored staging evidence only. Formal
`releases/V1.19/` creation, pointer/index changes, promotion execution, and
Phase 2A remain forbidden before Gate D.

---

## Task 0 — Baseline and immutable evidence

**No files modified.**

1. Confirm branch, HEAD, upstream, clean worktree/index, and no untracked files.
2. Hash and count V1.18; record a full V1.18 tree fingerprint.
3. Hash and fingerprint both the synthetic and real Task 9C candidate trees.
4. Reconstruct the real Task 9A preflight from
   `data/staging/task9b-real-0918-canonical-approved-a`, create the exact Gate C
   `ImportApproval`, and run `verify_v119_candidate()` against
   `data/staging/task9c-v119-real-0918-interval-candidate`.
5. Assert batch, preflight, five candidates, 502 projection, 16/16 verifier PASS,
   and `releases/V1.19/` absence.
6. Run Task 9A 41/41, Task 9B current maintained equivalent, Task 9C 71/71,
   V1.18 validator PASS, and `git diff --check`.

Any mismatch stops as `BLOCKED — TASK 9D BASELINE DRIFT` before changes.

---

## Task 1 — Phase A public contract RED

**Files:**

- Create `tests/unit/test_v119_promotion_models.py`
- Later create `src/joy_m2/ingest/promotion_models.py`
- Later create signature-only `src/joy_m2/ingest/promotion.py`
- Later create signature-only `src/joy_m2/ingest/promotion_verification.py`
- Later modify `src/joy_m2/ingest/__init__.py`

### Step 1.1 — Write tests before production

Use dynamic package attribute checks so the initial RED is an assertion failure
for absent approved contracts, not an accidental import/setup error. Lock:

- exact six dataclass names, fields, field order, annotations, no defaults, and
  frozen behavior;
- exact `V119PromotionContract` values and wrong-value rejection;
- exact nested carrier types and defensive `Path` resolution;
- exact `ArtifactRef` kinds, ordered tuple copying, digest/runtime type checks;
- `ReleasePromotionApproval` exact lowercase digest and one-line Gate D syntax;
- import approval cannot substitute for Gate D approval;
- exact three function signatures and annotations;
- exact nine-name append-only `joy_m2.ingest.__all__` extension with the
  existing 22 names unchanged.

Run:

```bash
$PY -m unittest -v tests.unit.test_v119_promotion_models
```

Record collected/pass/fail/error/skip/expected-failure/exit. The only valid RED
is absent Task 9D public contract. Any unrelated error stops.

### Step 1.2 — Minimum public GREEN

Implement the exact frozen models. Add exact annotated API scaffolds that raise
`NotImplementedError("Task 9D promotion behavior is not implemented")` without
reading or writing. Export only the approved names.

Re-run the focused module to all PASS. Verify existing Task 9C model/API tests
remain GREEN and `git diff --check` passes.

No promotion behavior, SQL, hashing, filesystem build, or verifier behavior is
allowed in this step.

---

## Task 2 — Phase B complete behavior RED gate

All tests in Tasks 2.1–2.4 must be authored and both new behavior test modules
must reach valid RED against the same unchanged `NotImplementedError` scaffolds
before any production behavior is implemented.

### Task 2.1 — Primitive/schema/oracle tests

**File:** create `tests/unit/test_v119_promotion_primitives.py`.

Freeze independent literal oracles for:

- the exact two-table DDL, 33-column view SQL, keys, constraints, and mapping;
- canonical JSON, exact SHA256SUMS line format, path ordering, no self-hash;
- exact manifest and rollback nested schemas/types/order semantics;
- exact promotion-identity payload and literal digest oracle;
- exact SQLite semantic payload, ASCII-whitespace SQL normalization, SQLite
  value projection, relation ordering, and literal digest oracle;
- five candidate rows mapped without rewriting, enrichment, deduplication, or
  omission;
- baseline raw/reviewed Chinese fields kept distinct;
- canonical relative paths, symlink rejection, exact integer-not-bool rules.

Do not copy the production projection implementation into the oracle. Expected
payloads and hashes are literal test authority.

### Task 2.2 — Builder and formal-verifier tests

**File:** create `tests/integration/test_v119_promotion.py`.

Build a five-row synthetic Task 9C candidate under a temporary repository by
using the committed Task 9A/9C public APIs. Test:

- successful staging build and exact tree;
- Task 9C candidate re-verification happens before build;
- exact 497 baseline preservation in all 55 columns and schema objects;
- exact five promoted rows, exact 502-row ordered formal view, no formal-view
  candidate status/selectability, no ID collision;
- missing explanation/tags/difficulty/incomplete enrichment preserved;
- user_version/release metadata/formal schema exact;
- manifest, source evidence, database byte+semantic hashes, SHA and rollback
  closure;
- images copied byte-identically if declared, with zero-image real shape valid;
- malformed JSON raises `InputFormatError`; parsed-invalid artifacts return
  structured FAIL; verifier never mutates.

### Task 2.3 — Required negative controls

Add independent tests for every Design negative:

- wrong baseline SHA and baseline row mutation;
- wrong candidate DB SHA, candidate manifest SHA, batch, preflight, import
  statement, candidate verification result, count, missing row, duplicate ID;
- output outside staging and pre-existing output conflict;
- missing/extra/symlink artifact, manifest mismatch, sums mismatch,
  ArtifactRef mismatch, rollback mismatch;
- unreadable/integrity/FK/schema/metadata/projection/formal-view corruption;
- source text, answer, provenance, primary type, or missing-enrichment mutation;
- release digest and semantic digest mismatch.

Each negative must fail its specific check and must not repair any artifact.

### Task 2.4 — Publication and determinism tests

Using isolated temporary repository roots only, test:

- publication rejects absent/wrong Gate D approval, wrong digest/statement,
  CR/LF, and reused `ImportApproval`;
- exact approved publish creates only `releases/V1.19/` and keeps V1.18 exact;
- existing formal target conflicts without overwrite;
- copy, byte-compare, rename, and post-verify failures clean only the private
  temporary tree according to the Design;
- publication never accepts a caller-supplied target or private sibling as a
  public verification root;
- two equivalent roots produce byte-identical SQLite, identical semantic
  digest, manifest, sums, rollback, images, release digest, and checks.

### Step 2.5 — Prove complete behavior RED before production

Run separately and together:

```bash
$PY -m unittest -v tests.unit.test_v119_promotion_primitives
$PY -m unittest -v tests.integration.test_v119_promotion
$PY -m unittest -v \
  tests.unit.test_v119_promotion_primitives \
  tests.integration.test_v119_promotion
```

Imports, fixtures, Phase A carriers, and requests must succeed. Failures must
reach only the Task 9D behavior `NotImplementedError` or missing private
behavior explicitly targeted by the tests. Record every expected failure group.
No production behavior file may change until this gate is valid.

---

## Task 3 — Minimum builder implementation

**File:** modify `src/joy_m2/ingest/promotion.py` only.

Implement the minimum build path in dependency order:

1. exact carrier/config/contract reconstruction;
2. independent `verify_v119_candidate()` PASS requirement;
3. candidate manifest, database SHA, batch, preflight, counts, import statement,
   and fixed real-envelope validation where applicable;
4. new staging output containment and no-conflict gate;
5. private build root and immutable before fingerprints;
6. candidate DB byte copy and exact one-transaction SQL projection;
7. deterministic image copy;
8. semantic SQLite digest and promotion identity;
9. canonical rollback, manifest, and SHA closure;
10. call independent promotion verifier;
11. atomic no-replace staging rename;
12. final verification and exact ArtifactRefs;
13. cleanup only private build state on failure.

Run the positive builder/schema/mapping/identity subsets after each dependency;
do not weaken remaining RED assertions.

---

## Task 4 — Independent verifier implementation

**File:** modify `src/joy_m2/ingest/promotion_verification.py` only.

Implement the exact ordered 18 checks without importing builder-only manifest,
SQL, row-projection, or digest constructors. Duplicate the frozen literal
contract where independence requires it. The verifier may reuse stable generic
Task 9C hashing/path primitives, but must independently reconstruct candidate,
manifest, SQLite, promoted-row, view, semantic-digest, SHA, rollback, and
publication expectations.

Preserve the error boundary:

- absent required root/input may raise approved input-missing exception;
- malformed JSON syntax raises `InputFormatError`;
- parsed-invalid/corrupt/mismatched artifacts return structured FAIL;
- verifier never mutates.

Run every negative subset and then the full primitives/integration pair.

---

## Task 5 — Gate-D publication implementation

**File:** modify `src/joy_m2/ingest/promotion.py` only.

Implement the separate `publish_v119_release()` path exactly as Design section
13. It must derive `releases/V1.19` through `PipelineConfig`, reverify staging,
bind exact Gate D digest, use a private sibling plus byte equality, atomically
rename no-replace, verify the exact final root, and apply the narrow failure
cleanup rules.

No test may point this API at the real repository. The real API must not be
called during Task 9D technical preparation.

Run publication, rollback, conflict, and Gate D negative subsets, then the full
Task 9D suite.

---

## Task 6 — Focused GREEN and independent implementation review

Run:

```bash
$PY -m unittest -v \
  tests.unit.test_v119_promotion_models \
  tests.unit.test_v119_promotion_primitives \
  tests.integration.test_v119_promotion
git diff --check
```

Require all PASS, skip 0, expectedFailure 0. Inspect the exact seven-file
implementation scope and confirm no formal root/data/frozen changes.

Request a strict independent implementation review for:

- exact Design/Plan conformity;
- no V1.18 mutation or source reinterpretation;
- 497+5/502 closure and nullable enrichment preservation;
- candidate/import approval binding;
- independent verifier and canonical artifacts;
- determinism, atomicity, rollback, and Gate D non-bypass;
- API/scope/frozen boundaries.

Any Critical or Important finding requires a focused regression RED and minimum
fix before re-review. Zero Critical and zero Important are required.

Suggested implementation commit after PASS:

```text
feat: add verified V1.19 promotion pipeline
```

Commit only the seven implementation files, verify parent/scope/diff/clean tree,
and ordinary-push the current branch. Do not publish V1.19.

---

## Task 7 — Exact real-candidate dual dry-run

**No tracked file is modified.** Generated outputs are ignored staging data.

1. Reconstruct exact real preflight and Gate C approval.
2. Verify the original real candidate and record its full tree fingerprint.
3. Choose two new absent strict descendants of `data/staging/`, for example:
   `task9d-v119-real-promotion-dry-run-a` and `...-b`.
4. Build and verify both through public APIs.
5. Compare complete file bytes, formal SQLite SHA and semantic SHA, manifest,
   sums, rollback, images, release digest, and 18 ordered checks.
6. Query exact 497/5/502 counts and all five preserved payload/provenance/
   enrichment values.
7. Re-hash V1.18 and both Task 9C candidates before/after.
8. Assert `releases/V1.19/` remained absent throughout.

Do not delete or rewrite the real Task 9C candidates. The two dry-run trees are
non-formal evidence and may remain under ignored staging until Gate D.

---

## Task 8 — Full maintained regression and final independent review

Run fresh:

```bash
$PY -m unittest -v tests.integration.test_ingest_preflight
$PY -m unittest -v \
  tests.unit.test_mmd_adapter_models \
  tests.unit.test_mmd_archive \
  tests.unit.test_mmd_parser \
  tests.integration.test_mmd_adapter \
  tests.unit.test_mmd_source_mapping \
  tests.integration.test_mmd_explicit_mapping
$PY -m unittest -v \
  tests.unit.test_v119_writer_models \
  tests.unit.test_v119_writer_primitives \
  tests.integration.test_v119_writer
$PY -m unittest -v \
  tests.unit.test_v119_promotion_models \
  tests.unit.test_v119_promotion_primitives \
  tests.integration.test_v119_promotion
$PY releases/V1.18/verify_task6_release.py releases/V1.18
git diff --check
```

Require Task 9A 41/41, Task 9B 342/342 or current equivalent, Task 9C 71/71,
Task 9D all PASS, validator PASS, zero skips/expected failures, unchanged V1.18
SHA/count, unchanged synthetic and real candidates, and absent formal V1.19.

Repeat independent review after the real dry-run. Require Critical 0 /
Important 0.

---

## Task 9 — Completion evidence, commit, push, and stop

**Files:**

- Modify `PROJECT_STATE.md`
- Create `docs/reports/TASK9D_VERIFICATION.md`

Record:

- Design/Plan/implementation commits and independent review results;
- exact RED evidence and final focused/regression counts;
- V1.18 497/SHA and unchanged tree;
- exact candidate/batch/preflight/import approval;
- dual-root output SQLite SHA, semantic SHA, manifest SHA, sums SHA, rollback
  SHA, release digest, and verification result;
- expected four core formal files plus zero current images;
- 497 baseline + 5 promoted = 502;
- exact rollback and future atomic publication action;
- no current-release pointer/index update;
- `releases/V1.19/` absent;
- Task 9D `READY FOR PROMOTION AUTHORIZATION`;
- HUMAN GATE D `REQUIRED`.

Request independent docs/evidence review. After PASS, commit only these two
files with:

```text
docs: record Task 9D promotion readiness
```

Ordinary-push. Verify local/remote HEAD, clean worktree/index, dry-run evidence,
and formal-root absence. Do not create a tag or PR.

Final output must stop at:

```text
USER DECISION REQUIRED — FINAL V1.19 PROMOTION AUTHORIZATION
```

and display the only valid next statement with the actual dry-run digest:

```text
USER APPROVED RELEASE PROMOTION V1.19 <actual release_digest>
```

No code, docs, Git, or formal publication work continues after this stop.
