# V1.21 Formal Promotion Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove that exact V1.21 generation `000004` can produce a deterministic,
independently verified 591-question formal-equivalent release tree without
creating `releases/V1.21/` before the final human gate.

**Architecture:** Add a version-specific V1.21 successor to the committed V1.20
promotion pipeline. The builder re-verifies the typed four-batch candidate,
creates an unpublished private release tree under staging, adds only the exact
promotion projection, invokes an independently implemented verifier, and
publishes the dry-run atomically. The real publication API is implemented and
tested only in isolated temporary repositories during readiness.

**Tech Stack:** Python 3 standard library, frozen dataclasses, `unittest`,
SQLite, canonical JSON, SHA-256, atomic filesystem rename.

**Spec:**
`docs/superpowers/specs/2026-09-19-v121-formal-promotion-readiness-design.md`

## Global Constraints

- Exact input generation: `000004` only.
- Candidate digest:
  `ecf624e3cb9fd8e7b1e0c664ddc5d51ef67f2d7f16f277c276be828eba32282c`.
- Candidate SQLite SHA-256:
  `6e27e5b5eff5a701b4671a3e12ee538eed985147d86c23edef1e9489f714a53c`.
- Candidate manifest SHA-256:
  `dc82e04639a4b54e24bbf7eceeb4ecec8a3751dfa7e8595f260b9d894d91fc83`.
- Formal baseline remains immutable V1.20/543 with SQLite SHA-256
  `b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292`.
- Promotion is a status/authority transition only: preserve all content,
  taxonomy, difficulty, provenance, source/MS evidence, IDs, and ordering.
- `releases/V1.21/` must remain absent throughout readiness.
- No 2019 ingestion, V1.22 work, generic promotion refactor, dependency, CLI,
  release pointer, force push, merge, rebase, or squash.
- Every behavior change follows observed RED then minimum GREEN.
- Final stop is `USER DECISION REQUIRED — FINAL V1.21 PROMOTION AUTHORIZATION`.

---

### Task 1: Read-only baseline and immutable fingerprints

**Files:** None.

**Interfaces:**
- Consumes: committed V1.20 formal release and V1.21 generation `000004`.
- Produces: recorded exact pre-change tree fingerprints and gate results.

- [ ] **Step 1: Confirm repository state and formal boundary**

Run:

```bash
git branch --show-current
git rev-parse HEAD
git status --short --untracked-files=all
test ! -e releases/V1.21
```

Expected: branch `task8b/pipeline-migration`, clean worktree/staging except the
Plan while it is being authored, and no formal V1.21 root.

- [ ] **Step 2: Verify exact candidate identities**

Read the generation-000004 manifest and compute SHA-256 for its SQLite and
manifest. Assert generation 4, batches 4, additions 48, projection 591, the
three fixed identities in Global Constraints, and ledger batch counts
`12/12/12/12`.

- [ ] **Step 3: Run current candidate and historical formal gates**

Run the V1.21 focused 44-test command, independently verify the real candidate
24/24, verify formal V1.20 21/21, run the V1.19 formal verifier, and run the
V1.18 validator. Record exact output and hashes for final comparison.

- [ ] **Step 4: Fingerprint immutable trees**

Record `(relative_path, type, size, sha256)` for `releases/V1.18`,
`releases/V1.19`, `releases/V1.20`, generation `000001` through `000004`, and
the four canonical 2015–2018 packages. These fingerprints become end-gate
oracles; they are not committed as generated data.

### Task 2: Public contract RED then minimum GREEN

**Files:**
- Create: `tests/unit/test_v121_promotion_models.py`
- Create: `src/joy_m2/ingest/v121_promotion_models.py`
- Create: `src/joy_m2/ingest/v121_promotion.py`
- Create: `src/joy_m2/ingest/v121_promotion_verification.py`
- Modify: `src/joy_m2/ingest/__init__.py`
- Modify: `tests/unit/test_v119_writer_models.py`
- Modify: `tests/unit/test_v119_promotion_models.py`
- Modify: `tests/unit/test_v120_promotion_models.py`
- Modify: `tests/regression/test_v119_historical_replay.py`
- Modify: `tests/integration/test_hkdse_pdf_adapter.py`

**Interfaces:**
- Consumes: `V121CandidateVerificationRequest`, `ArtifactRef`,
  `VerificationReport`, `PipelineConfig`.
- Produces: six frozen V1.21 promotion carriers and three public API signatures
  exactly as Design section 5.

- [ ] **Step 1: Write exact public-contract tests before production files**

Use dynamic `getattr(joy_m2.ingest, name, None)` so collection succeeds while
symbols are absent. Lock this exact suffix:

```python
EXPORTS = (
    "V121PromotionContract",
    "V121PromotionBuildRequest",
    "V121PromotionVerificationRequest",
    "V121ReleasePromotionApproval",
    "V121PublicationRequest",
    "V121PromotionArtifacts",
    "build_v121_promotion",
    "verify_v121_promotion",
    "publish_v121_release",
)
```

Tests assert exact dataclass fields/order/types/no-defaults/frozen behavior,
the fourteen exact contract literals, exact typed carrier rejection, isolated
tuple conversion for images, exact ArtifactRef kinds, exact function
annotations, and exact approval statement:

```text
USER APPROVED RELEASE PROMOTION V1.21 <release_digest>
```

- [ ] **Step 2: Run public-contract RED**

Run:

```bash
python -m unittest -v tests.unit.test_v121_promotion_models
```

Expected: collected tests fail because the nine V1.21 promotion public symbols
do not exist. Import/setup/syntax errors are invalid RED.

- [ ] **Step 3: Implement the six carriers**

Create `v121_promotion_models.py` with the exact Design section-5 dataclasses.
Validation must use exact runtime types, canonicalize paths without filesystem
I/O, reject bool-as-int, reject non-lowercase/non-64-hex digests, preserve image
tuple isolation, and accept no compatibility aliases or defaults.

- [ ] **Step 4: Add signature-only API scaffolds**

Create exact annotated functions:

```python
def build_v121_promotion(
    request: V121PromotionBuildRequest,
    config: PipelineConfig,
) -> V121PromotionArtifacts:
    raise NotImplementedError("V1.21 promotion behavior is not implemented")

def verify_v121_promotion(
    request: V121PromotionVerificationRequest,
    config: PipelineConfig,
) -> VerificationReport:
    raise NotImplementedError("V1.21 promotion verification is not implemented")

def publish_v121_release(
    request: V121PublicationRequest,
    config: PipelineConfig,
) -> V121PromotionArtifacts:
    raise NotImplementedError("V1.21 publication behavior is not implemented")
```

Append the nine exports. Update the five named historical public-surface tests
only to preserve their old exact prefix/slices and recognize the new suffix.

- [ ] **Step 5: Run public-contract GREEN and historical surface regressions**

Run the new model suite plus all five modified historical modules. Expected:
all PASS while every behavior scaffold still raises `NotImplementedError`.

- [ ] **Step 6: Commit the public contract checkpoint**

Stage only the files named in this task and commit:

```text
feat: add V1.21 promotion contracts
```

### Task 3: Complete behavior RED before behavior implementation

**Files:**
- Create: `tests/unit/test_v121_promotion_primitives.py`
- Create: `tests/integration/test_v121_promotion.py`

**Interfaces:**
- Consumes: Task 2 public carriers and scaffolds.
- Produces: executable literal oracles for all builder, verifier, determinism,
  rollback, path, publication, and historical-preservation behavior.

- [ ] **Step 1: Write independent primitive oracles**

Lock the exact 21 check names, promotion/candidate/baseline constants, exact
promotion and promoted-table DDL, exact formal-view SQL, canonical JSON bytes,
SHA256SUMS syntax, rollback mapping, promotion identity keys, and semantic
SQLite identity schema. Literal tests must not import private builder helpers.

- [ ] **Step 2: Write successful-build and projection tests**

The integration fixture reconstructs the exact four typed approved batches,
independently verifies generation `000004`, builds in `TemporaryDirectory`
below a temporary staging root, then asserts:

```python
self.assertEqual(report.status, "PASS")
self.assertEqual(len(report.checks), 21)
self.assertEqual(formal_count, 591)
self.assertEqual(promoted_count, 48)
self.assertEqual(baseline_rows, v120_rows)
self.assertTrue(all(row.record_status == "published" for row in promoted))
self.assertTrue(all(row.selectable == 1 for row in promoted))
```

Also assert exact four-file tree, empty images, batch counts `12/12/12/12`,
candidate digest/SQLite/manifest binding, and no candidate-only rows in the
formal view.

- [ ] **Step 3: Write negative verifier tests**

Each independent case mutates only one dimension and expects structured FAIL:
wrong/older candidate, candidate bytes, ledger order/parent/approval/count,
baseline row, promoted content/taxonomy/provenance, status/selectable/authority,
manifest structure/type/digest, sums, rollback, missing/extra/symlink artifact,
SQLite schema/integrity/foreign keys/view/count, provenance link, deterministic
identity, and non-formal/formal boundary. Malformed JSON must retain the existing
approved input-format exception boundary.

- [ ] **Step 4: Write atomicity, determinism, and isolated publication tests**

Tests require two output roots to be byte-identical; existing outputs conflict;
private-build and post-rename failures remove only owned unchanged output;
changed output is retained; symlink/overlap paths reject before writes; wrong
Gate approval rejects; isolated publication creates only the exact V1.21 target;
and conservative rollback never modifies V1.20.

- [ ] **Step 5: Run and record both valid behavior RED groups**

Run:

```bash
python -m unittest -v tests.unit.test_v121_promotion_primitives
python -m unittest -v tests.integration.test_v121_promotion
```

Both groups must collect normally and fail only because the three behavior
scaffolds are unimplemented. Public-contract, fixture, import, setup, and
environment errors are invalid RED. Do not edit production behavior until both
groups have valid RED evidence.

### Task 4: Independent verifier minimum GREEN

**Files:**
- Modify: `src/joy_m2/ingest/v121_promotion_verification.py`

**Interfaces:**
- Consumes: exact `V121PromotionVerificationRequest` and release bytes.
- Produces: read-only `VerificationReport` with exactly 21 ordered checks.

- [ ] **Step 1: Implement independent parsing and safe-failure primitives**

Implement local canonical JSON, SHA, sums parser, exact-key/type/path checks,
schema normalization, read-only SQLite access, semantic projection, and report
closure. Do not import builder-private identity/manifest helpers.

- [ ] **Step 2: Implement all 21 verifier checks**

Close candidate 24/24 verification, exact three hashes/generation, baseline
identity, ledger, filesystem/SHA/ArtifactRef/rollback, SQLite schema/integrity/
foreign keys, 543-row V1.20 equality, 48 exact promoted rows, 591 count,
provenance, release digest, and publication boundary.

- [ ] **Step 3: Run verifier-oriented tests**

Run primitive tests and the integration tests that build literal independent
release trees. Expected: verifier cases GREEN; builder tests remain RED because
the builder scaffold is unchanged.

### Task 5: Builder, dry-run, and isolated publication minimum GREEN

**Files:**
- Modify: `src/joy_m2/ingest/v121_promotion.py`

**Interfaces:**
- Consumes: exact typed candidate authority plus the independent verifier.
- Produces: deterministic dry-run artifacts and an isolated, Gate-bound
  publication implementation.

- [ ] **Step 1: Validate before output**

Reconstruct exact request types, verify candidate 24/24, require generation 4,
the three fixed candidate identities, exact four-entry ledger, counts
543/4/48/591, zero images, and resolved path/symlink/overlap safety before
creating any output leaf.

- [ ] **Step 2: Build the private formal-equivalent SQLite**

Copy the candidate SQLite byte source into a private sibling. In one transaction
insert the exact promotion row, copy 48 ordered candidate rows into the promoted
table changing only status/selectable authority, create the formal view, apply
the exact metadata delta, and verify the first 543 and last 48 row closures.

- [ ] **Step 3: Write deterministic artifacts**

Write canonical rollback, compute semantic and byte identities, compute the
promotion digest, write the exact manifest, and write sorted SHA256SUMS. The
tree must contain exactly the four Design artifacts.

- [ ] **Step 4: Independently verify and atomically publish the staging root**

Call only public `verify_v121_promotion()` on the private root, require 21/21
PASS, atomically rename without replacement to the requested staging output,
reverify the public staging root, and return exact ArtifactRefs. Failure cleanup
uses strict ownership fingerprints.

- [ ] **Step 5: Implement isolated final publication behavior**

Require exact `V121ReleasePromotionApproval`, reverify the dry-run, bind the
release digest, copy into a private sibling of the derived formal target,
compare byte-for-byte, rename without replacement, and post-verify. Implement
conservative digest-and-tree-bound cleanup exactly as the Design specifies.

- [ ] **Step 6: Run complete focused GREEN**

Run all three new promotion modules together. Require all PASS, zero skips, zero
expected failures. Then run V1.21 candidate 44/44 and V1.20 promotion 30/30.

- [ ] **Step 7: Commit behavior and tests**

Stage only Task 2–5 production/test paths and commit:

```text
feat: add V1.21 promotion readiness
```

### Task 6: Real generation-000004 readiness dry-runs

**Files:** Generated ignored output only below `data/staging/`.

**Interfaces:**
- Consumes: the exact operational typed four-batch authority.
- Produces: two non-formal byte-identical V1.21 dry-run trees and exact evidence.

- [ ] **Step 1: Reconstruct exact typed authority without modifying it**

Use the committed 2015–2018 canonical packages, preflights, import approvals,
and parent chain to construct `V121CandidateVerificationRequest`. Require the
real generation `000004` verifier to return 24/24 before building.

- [ ] **Step 2: Build two independent real dry-runs**

Create only:

```text
data/staging/task11-v121-promotion-dry-run-a
data/staging/task11-v121-promotion-dry-run-b
```

Never use `releases/V1.21/` as an intermediate path.

- [ ] **Step 3: Verify both and compare complete trees**

Require each independent verifier to return 21/21 PASS. Compare relative paths,
file types, bytes, ArtifactRefs, formal SQLite SHA, semantic SHA, manifest SHA,
rollback SHA, sums SHA, and release digest. All must be identical.

- [ ] **Step 4: Exercise rollback only in an isolated copied tree**

Prove exact-digest rollback can remove only the copied V1.21 tree, while a
changed digest or byte fingerprint preserves it for manual recovery. Confirm
V1.20's tree fingerprint never changes.

### Task 7: Complete gates and independent review

**Files:** No new scope unless a tested defect lies inside the approved files.

**Interfaces:**
- Consumes: complete implementation and both dry-runs.
- Produces: fresh regression evidence and Critical 0 / Important 0 review.

- [ ] **Step 1: Run all maintained gates serially where staging is shared**

Run Task 9A, Task 9B, Task 9C, Task 9D, Task 10A, Task 10B, Task 10C, V1.21
candidate, and V1.21 promotion suites. Record exact counts; require no failures,
skips, or expected failures.

- [ ] **Step 2: Run historical and formal gates**

Run Task 7, Task 8 equivalence, Task 6 oracle, Task 3–6 gates, V1.18 validator,
formal V1.19 verifier, formal V1.20 verifier, and real candidate 24/24.

- [ ] **Step 3: Recompare immutable fingerprints and Git scope**

Require V1.18/V1.19/V1.20, all four generations, packages, data, releases,
legacy, and frozen artifacts to equal Task 1 fingerprints. Require
`releases/V1.21/` absent and `git diff --check` PASS.

- [ ] **Step 4: Perform independent review**

Review exact generation binding, parent chain, 543+48 closure, baseline and
addition preservation, determinism, atomicity, rollback, Gate bypass, public
surface, and V1.22/2019 exclusion. Remediate only in approved files and repeat
review until Critical 0 and Important 0.

### Task 8: Evidence, commits, ordinary push, and final stop

**Files:**
- Create: `docs/reports/V121_PROMOTION_READINESS_VERIFICATION.md`
- Modify: `PROJECT_STATE.md`

**Interfaces:**
- Consumes: verified dry-run identities, regression output, and review result.
- Produces: the readiness checkpoint and exact final human approval syntax.

- [ ] **Step 1: Write closure evidence without claiming publication**

Record current formal V1.20/543, generation 000004, 48 additions, projected
591, all three candidate hashes, both dry-run identities, 21/21 verifier,
rollback, complete gates, review result, and formal V1.21 absence. Set status:

```text
READY FOR FINAL V1.21 PROMOTION AUTHORIZATION
```

- [ ] **Step 2: Run final fresh verification**

Repeat focused V1.21 promotion, complete maintained suite, historical/formal
verifiers, immutable hashes/counts, both dry-run 21/21, byte comparison,
`git diff --check`, scope inspection, and clean staging checks.

- [ ] **Step 3: Commit closure docs**

Stage only the report and `PROJECT_STATE.md`, then commit:

```text
docs: record V1.21 promotion readiness
```

- [ ] **Step 4: Ordinary push and remote verification**

Push the current branch without force. Confirm local and remote HEAD match and
ahead/behind is `0/0`. Do not create a PR or tag unless separately authorized.

- [ ] **Step 5: Stop before real publication**

Report exact commits, tests, review, frozen identities, dry-run release digest,
formal SQLite/semantic/manifest hashes, hash and rollback closure, exact four
formal artifacts, and confirmation that `releases/V1.21/` remains absent. End:

```text
USER DECISION REQUIRED — FINAL V1.21 PROMOTION AUTHORIZATION

USER APPROVED RELEASE PROMOTION V1.21 <exact_release_digest>
```

Do not publish, ingest 2019, or begin V1.22.
