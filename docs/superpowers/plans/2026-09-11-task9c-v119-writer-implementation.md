# Task 9C V1.19 Incremental Candidate Writer Implementation Plan

> Authority: `docs/superpowers/specs/2026-09-11-task9c-v119-writer-design.md`

Date: 2026-09-11 (Asia/Shanghai)

Status: APPROVED — INDEPENDENT REVIEW PASSED

Task 9A: CLOSED / PASS

Task 9B: CLOSED / PASS

First real V1.19 write: HUMAN GATE B — NOT AUTHORIZED

## Goal

Implement and independently verify the narrow Task 9C V1.19 candidate writer
using only in-memory or OS-temporary repository roots. The writer consumes one
exact READY Task 9A preflight plus a synthetic/test-only or later user-issued
digest-bound import approval, copies frozen V1.18, adds the approved candidate
schema and artifacts, verifies the complete candidate independently, and
publishes one atomic staging tree.

No step in this Plan authorizes a real repository V1.19 artifact, a real batch
approval/import, formal-row merge, export, release, or promotion.

## Fixed environment and commands

From the existing `task8b/pipeline-migration` worktree:

```bash
PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
export PYTHONPATH=src
```

Never use the absent system `python` as a reason to alter repository setup.
The exported source-layout import path applies to every `$PY` test and validator
command in this Plan.
All tests use `tempfile.TemporaryDirectory()` or an equivalent OS-temporary
root passed to `PipelineConfig`. They may read the frozen V1.18 SQLite only
through its existing path/typed evidence and must never write beside it.

## Exact scope

Phase A may modify only:

```text
src/joy_m2/errors.py
src/joy_m2/ingest/__init__.py
src/joy_m2/ingest/writer_models.py
src/joy_m2/ingest/writer.py
src/joy_m2/ingest/writer_verification.py
tests/unit/test_v119_writer_models.py
```

Phase B may modify the two Phase A API scaffolds and additionally create only:

```text
src/joy_m2/ingest/writer_profiles.py
tests/unit/test_v119_writer_primitives.py
tests/integration/test_v119_writer.py
```

Phase B may additionally modify `tests/unit/test_v119_writer_models.py` only
to replace its Phase A scaffold-only `NotImplementedError` assertion with an
exact wrong-request rejection/no-filesystem-mutation assertion. Preserve all
other content in that Phase A test module unchanged. No model or additional
production file is authorized by this lifecycle migration.

After Phase A implementation is reviewed and committed, one separate docs-only
checkpoint may modify only `PROJECT_STATE.md`. After Phase B implementation is
reviewed and committed, its separate closure checkpoint may modify only
`PROJECT_STATE.md` and `docs/reports/TASK9C_VERIFICATION.md`.

No existing Task 9A/9B production or tests, Task 8 pipeline, database, audit,
export, release, CLI, data, releases, legacy, or frozen artifact may change.

---

## Execution precondition — Plan authority gate

No Task 1 test may be created or modified while this Plan is a draft. Before
Phase A RED begins, all of the following must be true:

1. the Task 9C Design is independently reviewed with Critical=0 and
   Important=0 and committed;
2. this Plan is independently reviewed with Critical=0 and Important=0;
3. every Plan review finding is remediated docs-only and re-reviewed;
4. this Plan is marked approved and committed as a Plan-only checkpoint;
5. the Plan commit is ordinarily pushed and the worktree is clean.

The Plan checkpoint commit message is:

```text
docs: add Task 9C implementation plan
```

Only after this gate closes may Task 1 establish the first Phase A RED.

---

## Task 1 — Phase A public-contract RED

**Modify/create only:**

```text
tests/unit/test_v119_writer_models.py
```

### Step 1: Lock `ImportApproval`

Write exact-field/order/type/no-default/frozen tests for:

```python
ImportApproval(
    batch_id,
    preflight_sha256,
    target_release_version,
    statement,
)
```

Cover exact `V1.19`, lowercase SHA-256, exact one-line statement, CR/LF batch
rejection, false/mismatched statements, wrong types, subclasses, and mutation.
Use only synthetic test approval data; do not create or imply a real approval.

### Step 2: Lock `V119WriterContract`

Assert the exact 12 fields/order, exact fixed scalar values, exact baseline/
candidate table and candidate-view tuples, defensive tuple copying, no mutable
alias, wrong type/value/ordering/duplicate rejection, no defaults, and frozen
behavior. Reject `bool` as `expected_user_version`.

### Step 3: Lock request/result carriers

Test exact fields/order/types/no-default/frozen behavior for:

- `V119WriteRequest`;
- `V119VerificationRequest`;
- `V119CandidateArtifacts`.

Require exact Task 9A preflight, exact approval/contract, `Path` instances but
not strings, resolved transport locators, exact `ArtifactRef` members, image
tuple defensive copying/order/type, and exact existing `VerificationReport`.

### Step 4: Lock error and final public surface

Assert:

- `ImportApprovalError` is a direct maintained `PipelineError` subtype and is
  imported only from `joy_m2.errors`;
- exact signatures for `build_v119_candidate` and `verify_v119_candidate`;
- exact 22-name `joy_m2.ingest.__all__` and order from Design section 5;
- invoking either API scaffold raises exactly
  `NotImplementedError("Task 9C writer behavior is not implemented")` with no
  filesystem change.

### Step 5: Prove valid RED

Run:

```bash
$PY -m unittest -v tests.unit.test_v119_writer_models
```

Valid RED requirements:

- the test module remains collectable by using an import-safe helper that turns
  an absent Task 9C module/name into an assertion failure rather than a module-
  collection error;
- runtime imports reach the expected missing Task 9C contract/API surface;
- every failure is caused by absent Task 9C types/error/surface;
- no ERROR, syntax, fixture, environment, Task 9A, or Task 9B failure;
- record collected/PASS/FAIL/ERROR/exit code and exact gaps.

Stop and repair only the test if the signal is not this approved RED.

---

## Task 2 — Phase A minimal public-contract GREEN

**Modify/create only:**

```text
src/joy_m2/errors.py
src/joy_m2/ingest/writer_models.py
src/joy_m2/ingest/writer.py
src/joy_m2/ingest/writer_verification.py
src/joy_m2/ingest/__init__.py
```

### Step 1: Add the approved error and carriers

Add only `ImportApprovalError` to `errors.py`. Implement the five exact frozen
carriers in `writer_models.py`, with small private validation helpers only when
needed. Do not modify another model module or add compatibility aliases.

### Step 2: Add signature-only API scaffolds

Create the two owner modules with the exact signatures and the fixed
`NotImplementedError`. They perform no validation, hashing, SQLite access,
filesystem access, output creation, or behavior.

### Step 3: Add package exports

Create `ingest/__init__.py` with exactly the Design's 22-name `__all__`. Import
only those public Task 9A, Task 9B, and Task 9C names. Do not export helpers or
`ImportApprovalError`.

### Step 4: GREEN and regression

Run:

```bash
$PY -m unittest -v tests.unit.test_v119_writer_models
$PY -m unittest -v tests.unit.test_ingest_models
$PY -m unittest -v tests.integration.test_ingest_preflight
$PY -m unittest -v tests.unit.test_mmd_adapter_models tests.unit.test_mmd_archive tests.unit.test_mmd_parser tests.integration.test_mmd_adapter
git diff --check
```

Require Phase A focused GREEN, Task 9A public models `14/14`, Task 9A
integration `41/41`, Task 9B `214/214`, zero skip, zero expected failure, and
exact Phase A scope.

---

## Task 3 — Phase A independent review and checkpoint

### Step 1: Independent implementation review

Review carrier exactness, type/tuple/path validation, statement closure, error
ownership, signature-only stubs, package surface, no I/O, exact scope, Task
9A/9B preservation, and frozen boundaries. Classify findings Critical,
Important, or Minor.

For every Critical/Important finding, add a valid focused RED first and make
the minimum Phase A correction. Re-run review until Critical=0 and Important=0.

### Step 2: Full checkpoint gates

Run the complete required gates in the final section of this Plan. Confirm no
V1.19 artifact, V1.18 exact SHA/count, and no non-scope diff.

### Step 3: Commit and push

Stage only the exact Phase A files and commit:

```text
feat: add Task 9C writer public contracts
```

Verify parent, exact committed paths, `git diff-tree --check HEAD^ HEAD`, clean
tree/staging/untracked, then ordinary push without force.

### Step 4: Separate docs-only state sync

Update only `PROJECT_STATE.md` with the Phase A commit, RED/GREEN evidence,
review result, frozen state, and next action. Independently review, commit:

```text
docs: record Task 9C public contract checkpoint
```

Then ordinary push. Do not mix implementation or tests into this commit.

---

## Task 4 — Phase B complete behavior RED gate

**Modify/create tests only:**

```text
tests/unit/test_v119_writer_primitives.py
tests/integration/test_v119_writer.py
```

Do not modify `writer.py`, `writer_verification.py`, or create
`writer_profiles.py` until all four behavior groups import and fail for the
approved scaffold `NotImplementedError`/absent private behavior only.
Both test modules must remain collectable: probe the not-yet-created private
`writer_profiles` module inside test bodies and convert absence into explicit
assertion failure. Missing private production must never cause collection
ERROR.

### Group 1: Database/profile/projection RED

In unit and integration tests, independently lock:

- all fixed contract values and exact table/view sets;
- the complete normalized four-table/one-view DDL contract, column order,
  types, nullability, keys/checks, default ABORT policy, no extra objects;
- one exact batch row and contiguous candidate order;
- all 25 Task 9A candidate fields and exact JSON-column mappings;
- image-binding and taxonomy rows/order;
- `user_version=119`, integrity/FK closure;
- V1.18 pre-existing schema SQL and logical contents unchanged;
- 497 formal V2 rows and zero published/selectable Task 9 rows.

### Group 2: Image RED

Lock:

- exact `.jpg`/`.jpeg` -> `.jpg` and `.png` -> `.png` mapping;
- case-insensitive suffix decision while preserving evidence spelling;
- unsupported/empty suffix raises `InputFormatError` before temp/output;
- package containment, regular-file, readability, size and SHA validation;
- ordered bindings and exact source/destination projection;
- same digest+extension physical dedup without binding loss;
- conflicting extensions and byte-distinct destination collision each raise
  `InputFormatError` before temp/output;
- byte-identical staging and no unreferenced file copy.

### Group 3: Manifest/sums/rollback/verifier RED

Lock exact canonical JSON formula, final LF, 15-key top-level manifest, every
nested exact key/type/value/order projection, fixed identities, path exclusion,
artifact kinds, exact candidate tree, and non-recursive hashing.

Lock SHA256SUMS exact two-space grammar, sorted unique paths, final LF, no
binary marker/escape/comment/blank/extra line, exact file closure, and exclusion
of itself. Lock rollback exact six-key schema, exact baseline object, sorted
complete path list including rollback and sums, and declarative-only semantics.

Test verifier exception matrix and the exact ordered 16-check report. Every
structured outcome has the full tuple with exact `PASS`/`FAIL` detail; missing
or failed prerequisites safely fail dependent checks. Cover malformed JSON,
parsed-invalid JSON/digests/types, missing/unreadable/malformed sums, missing/
extra/tampered artifacts, wrong ArtifactRef, SQLite open/integrity/FK/schema/
row/count failures, non-mutation, and no crash.

### Group 4: Builder gates/transaction/determinism/atomicity RED

Lock exact request/config/preflight/approval types; independent Task 9A
manifest and preflight digest reconstruction; READY/count/issue/candidate
closure; CR/LF batch rejection; baseline ArtifactRef/bytes/schema/count; safe
package/output paths; and no re-preflight/source-file reads.

Lock one immediate transaction, fixed object/insert order, one deterministic
VACUUM/header normalization, verifier-before-publication, final-directory
non-overwrite, single atomic rename, injected failure rollback/cleanup, source/
baseline/unrelated staging non-mutation, and no partial destination.

Snapshot the actual worktree's `data/staging/` and `releases/` state before and
after every builder test group. Assert that no Task 9C/V1.19 candidate tree or
`releases/V1.19/` appears there and that both snapshots are identical. This
real-repository guard is independent of the temporary `PipelineConfig` root and
must be GREEN in both success and injected-failure cases.

Build equivalent approved inputs under at least two distinct temporary roots
and require identical database, image, manifest, rollback, sums bytes and all
ArtifactRef values except paths. Test empty image/taxonomy variants only if
valid under the frozen READY carrier.

### Validate all RED groups

Freeze the following exact test classes and run each RED group separately:

```bash
# Group 1 — profile/DDL plus database projection
$PY -m unittest -v \
  tests.unit.test_v119_writer_primitives.V119WriterProfileRedTests \
  tests.integration.test_v119_writer.V119DatabaseProjectionRedTests

# Group 2 — image serialization
$PY -m unittest -v \
  tests.unit.test_v119_writer_primitives.V119ImageProjectionRedTests

# Group 3 — manifest/sums/rollback/verifier
$PY -m unittest -v \
  tests.unit.test_v119_writer_primitives.V119ManifestAndVerificationRedTests

# Group 4 — builder gates/determinism/atomicity
$PY -m unittest -v \
  tests.integration.test_v119_writer.V119BuilderBoundaryRedTests \
  tests.integration.test_v119_writer.V119DeterminismAndAtomicityRedTests
```

Then run both complete modules together:

```bash
$PY -m unittest -v tests.unit.test_v119_writer_primitives tests.integration.test_v119_writer
```

Record actual counts and every expected failure. Imports and Phase A public
contracts must be GREEN. No missing dependency, syntax, fixture, setup, or
environment error is a valid behavior RED. Only after every group is valid RED
may Phase B production change.

---

## Task 5 — Phase B minimal production GREEN

**Modify/create production files only:**

```text
src/joy_m2/ingest/writer_profiles.py
src/joy_m2/ingest/writer.py
src/joy_m2/ingest/writer_verification.py
```

The only test file modification in this Task is the previously authorized
single lifecycle-test replacement in `tests/unit/test_v119_writer_models.py`;
the two Phase B test files were already frozen by the complete RED gate.

### Step 1: Implement deterministic private profile primitives

In `writer_profiles.py`, define only frozen constants, exact DDL, and low-level
canonical JSON/SHA-256/path primitives that cannot decide an expected semantic
projection. Builder-only manifest/rollback/row/image projection logic belongs
in `writer.py`. Verifier-only parsing and expected-value reconstruction belongs
in `writer_verification.py`. The verifier must independently reconstruct every
expected semantic object from the typed request and parsed artifacts; it must
not call or import a builder projection/render helper. Shared constants, exact
DDL text, and content-agnostic canonical-byte/hash primitives are permitted.
No public export or Task 9A/9B change.

Run Group 1 and Group 2 tests after the minimum code for each dependency, but
do not weaken or add behavior beyond the pre-established tests.

### Step 2: Implement independent verifier

Replace only the `writer_verification.py` scaffold. Validate the exact request
and exception matrix, parse independently, always return the full ordered
16-check tuple for structured outcomes, and never repair/delete/rewrite. Safely
short-circuit dependencies and close status from all checks.

Run Group 3 selected tests until GREEN.

### Step 3: Implement builder

Replace only the `writer.py` scaffold. In order:

1. validate exact request/config/contract/preflight/approval and recompute the
   frozen path-free Task 9A digests;
2. validate baseline and all consumed image bytes before output/temp creation;
3. create one private temporary sibling under the staging parent;
4. copy V1.18, perform the exact transaction and deterministic SQLite finish;
5. stage deduplicated images and canonical rollback/manifest/sums;
6. construct a verification request with the same typed authority;
7. call the independent verifier and require PASS;
8. atomically rename once to the previously absent final destination;
9. return exact final-path artifact references;
10. on every exception remove only the known temp sibling.

Run Group 4 selected tests until GREEN.

### Step 4: Unified focused GREEN

Before the unified run, perform the one authorized Phase A lifecycle-test
migration in `tests/unit/test_v119_writer_models.py`: replace only the obsolete
scaffold `NotImplementedError` expectation. Call each API with an exact
`object()` request and one valid exact `PipelineConfig`; each call must raise
the existing `PipelineError` family. Create a sentinel before both calls,
compare the complete before/after tree including each entry kind and file
bytes, and assert that no output or private temporary entry appears. This is
required because the same final gate runs the Phase A public-contract module
against the implemented Phase B entry points; every other line and assertion
in that Phase A test module remains unchanged.

Run:

```bash
$PY -m unittest -v tests.unit.test_v119_writer_models tests.unit.test_v119_writer_primitives tests.integration.test_v119_writer
```

Require all PASS, zero skip, zero expected failure, and no repository V1.19
artifact.

---

## Task 6 — Phase B regression, independent review, and remediation

### Step 1: Complete regressions

Run every command in the final gate section. Confirm Task 9A/9B byte and digest
authority, Task 8, Release, legacy, V1.18 SHA/count, and exact scope.

### Step 2: Independent implementation review

Independently review:

- approval/preflight forgery resistance and Task 9A digest ownership;
- exact DDL/projection and V1.18 logical preservation;
- image safety/dedup/collision and destination authority;
- manifest/sums/rollback recursion-free identity;
- verifier exception/report/check closure and non-mutation;
- SQLite determinism, transaction, atomicity, failure cleanup;
- public/private API and package surface;
- no real V1.19 artifact, import, or promotion.

Every Critical/Important finding requires a focused valid RED before the
minimum approved-scope correction. Re-run focused/full gates and review until
Critical=0 and Important=0.

### Step 3: Commit and push implementation

Stage only the exact Phase B production/test files and commit:

```text
feat: add verified V1.19 candidate writer
```

Verify exact parent/files, both diff checks, clean tree/staging/untracked, then
ordinary push without force.

### Step 4: Closure docs checkpoint

Update only:

```text
PROJECT_STATE.md
docs/reports/TASK9C_VERIFICATION.md
```

Record Design/Plan/Phase A/Phase B commits, RED evidence, exact final counts,
deterministic temporary-root artifact hashes, V1.18 SHA/count, zero real V1.19
artifacts/imports, independent review, no blocker, and HUMAN GATE B as the next
action. Independently review, commit:

```text
docs: close Task 9C temporary writer checkpoint
```

Ordinary push after exact docs-only scope and gates.

---

## Final required gates

The Plan-only checkpoint runs `git diff --check`, exact one-file scope, Task 9A
public models `14/14`, Task 9A integration `41/41`, Task 9B `214/214`, Task 7
`7/7`, and the V1.18 validator before its commit; it runs no not-yet-authorized
Task 9C test.

The Phase A checkpoint runs the first command below with only
`tests.unit.test_v119_writer_models`, then every existing regression command
below and the complete maintained enumeration. It must not name either absent
Phase B test module.

The Phase B and final docs checkpoints run all three Task 9C focused modules,
then every remaining command and the complete maintained enumeration:

```bash
$PY -m unittest -v tests.unit.test_v119_writer_models tests.unit.test_v119_writer_primitives tests.integration.test_v119_writer
$PY -m unittest -v tests.unit.test_ingest_models
$PY -m unittest -v tests.integration.test_ingest_preflight
$PY -m unittest -v tests.unit.test_mmd_adapter_models tests.unit.test_mmd_archive tests.unit.test_mmd_parser tests.integration.test_mmd_adapter
$PY -m unittest -v tests.regression.test_task7_project_initialization
$PY -m unittest -v tests.regression.test_task8b_pipeline_equivalence
$PY -m unittest -v tests.unit.test_release_primitives tests.integration.test_release_pipeline tests.unit.test_v117_release_transformer
$PY releases/V1.18/verify_task6_release.py releases/V1.18
git diff --check
```

Run the complete maintained suite with this exact deterministic module
enumeration, excluding only the separately attributed legacy behavior module:

```bash
MODULES=$(rg --files tests \
  | rg '(^|/)test_[^/]*\.py$' \
  | rg -v '^tests/regression/test_task8b_legacy_pipeline_behavior\.py$' \
  | sort \
  | sed 's#/#.#g; s#\.py$##')
$PY -m unittest -v $MODULES
```

Record the actual collected/PASS count at each checkpoint because Phase A and
Phase B add tests. Require every collected test PASS with zero skip/expected
failure, and record the exact excluded module path. Run the four Task 3–6
executable legacy commands in `AGENTS.md` and require `54/54 PASS`. Run
`tests.regression.test_task8b_legacy_pipeline_behavior` separately and permit
only the existing `9 PASS / 2 FAIL` deterministic-SQLite/frozen-byte baseline.

At every gate also prove:

- frozen V1.18 SQLite SHA is
  `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`;
- formal complete question count is 497;
- repository `data/`, `releases/`, `legacy/`, Task 8, Task 9A, and Task 9B are
  unchanged except separately authorized docs checkpoints;
- no actual V1.19 database/manifest/sums/rollback/image tree exists;
- no actual import approval/import/promotion occurred;
- exact phase scope, no new repository staging artifact, and both diff checks.

## Human Gate B exit

After Task 9C temporary-root implementation, review, commits, docs sync, and
ordinary push are complete, do not create a repository V1.19 artifact. Report:

- exact proposed candidate target files;
- frozen source baseline and SHA/count;
- exact approved schema/user_version;
- projected counts;
- expected deterministic SHA behavior;
- rollback declaration and cleanup plan;
- V1.18 zero-impact proof;
- writer/verifier and full-gate status.

Then stop with exactly:

```text
USER DECISION REQUIRED — FIRST V1.19 WRITE AUTHORIZATION
```

Task 9D real preflight/approval remains HUMAN GATE C and formal promotion
remains HUMAN GATE D. Do not proceed to either.
