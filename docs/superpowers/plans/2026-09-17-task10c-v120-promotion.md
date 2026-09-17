# Task 10C Formal V1.20 Promotion Readiness Plan

**Authority:** `docs/superpowers/specs/2026-09-17-task10c-v120-promotion-design.md`

**Goal:** Prove that exact V1.20 candidate generation `000003` can produce a
deterministic, independently verified 543-question formal release tree without
creating `releases/V1.20/` before the final human gate.

## Task 0 — Baseline

No writes. Confirm branch/HEAD/clean state, exact V1.18 and V1.19 identities,
exact candidate digest/SQLite/manifest, ordered 3-batch ledger, 41 additions,
543 projection, current candidate verifier 24/24 PASS, and formal V1.20 absence.
Fingerprint immutable formal and candidate trees for end-of-task comparison.

## Task 1 — Public contract RED then minimum GREEN

Create `tests/unit/test_v120_promotion_models.py` first. Lock the exact six
frozen carriers, fields/order/types/no-defaults, exact contract values, strict
approval statement, signatures, and append-only public surface. Run a valid RED
for absent Task 10C contracts.

Then create `src/joy_m2/ingest/v120_promotion_models.py`, signature-only
`v120_promotion.py` and `v120_promotion_verification.py`, and minimally append
the nine public names in `src/joy_m2/ingest/__init__.py`. Scaffolds raise a
Task-10C-specific `NotImplementedError` and perform no I/O. Reach model GREEN.

## Task 2 — Complete behavior RED before production behavior

Before replacing any scaffold, create:

- `tests/unit/test_v120_promotion_primitives.py`
- `tests/integration/test_v120_promotion.py`

Lock independent literal oracles for DDL/view schema, canonical JSON, sums,
manifest, rollback, promotion identity, SQLite semantic identity, 502-row
baseline equivalence, exact 41-row status-only projection, 3-batch ledger,
21-check verifier closure, two-root determinism, atomic cleanup, and isolated
temporary-repository publication.

Required negatives include wrong/older candidate digest or bytes, wrong ledger
order/count/parent/approval, baseline mutation, content/taxonomy/provenance
mutation, candidate-only formal rows, missing/extra/symlink artifacts,
manifest/sums/rollback mismatch, SQLite integrity/schema/view/count corruption,
wrong promotion approval, existing target, and publication failure cleanup.

Run both behavior modules against unchanged scaffolds. Both must be valid RED
because Task 10C behavior is absent; import/setup/fixture/environment errors are
not valid RED.

## Task 3 — Minimum implementation GREEN

Implement only the Design in:

- `src/joy_m2/ingest/v120_promotion.py`
- `src/joy_m2/ingest/v120_promotion_verification.py`

The builder re-verifies the exact typed candidate before any output, builds in
a private staging sibling, transactionally adds the V1.20 promotion projection,
writes deterministic artifacts, independently verifies, and atomically renames
without replacement. The verifier independently reconstructs all identities.
The publication API is exercised only in isolated temporary roots.

Run model, primitive, and integration suites to full GREEN. Run Task 10A and
Task 9D focused regressions after each material fix.

## Task 4 — Real readiness dry-runs

Reconstruct the exact three approved batches from their immutable canonical
packages and approvals, verify generation `000003` 24/24 PASS, then build:

```text
data/staging/task10c-v120-promotion-dry-run-a
data/staging/task10c-v120-promotion-dry-run-b
```

Verify both 21/21 PASS. Compare every relative file byte-for-byte, all
ArtifactRefs, SQLite SHA, semantic digest, manifest SHA, and release digest.
Confirm exact artifacts and 543 published/selectable formal rows. Do not call
the real publication API and do not create `releases/V1.20/`.

## Task 5 — Rollback, immutability, and defect attribution

Validate the rollback receipt in an isolated copy: it may remove only the exact
digest-matching V1.20 tree and never rewrite V1.19. Re-fingerprint V1.18,
V1.19, the three candidate generations, and their approvals. Confirm unchanged.

Search the operational output field typo. Add a RED and smallest fix only if a
persistent repository access is found. Do not rebuild generation `000003` for a
non-authoritative reporting typo.

## Task 6 — Maintained gates and independent review

Run Task 9A, Task 9B, Task 9C, Task 9D, Task 10A, Task 10B, Task 10C, V1.18
validator, formal V1.19 verifier, current V1.20 candidate verifier 24/24,
`git diff --check`, and zero skip/expected-failure checks. Perform independent
review focused on exact candidate binding, ledger/count closure, preservation,
determinism, atomicity, rollback, and gate bypass. Remediate until Critical 0
and Important 0.

## Task 7 — Evidence, commit, push, stop

Update `PROJECT_STATE.md` and create `docs/reports/TASK10C_VERIFICATION.md` with
exact current formal/candidate/dry-run identities, test results, review result,
and publication absence. Commit Design/Plan, implementation/tests, and closure
evidence in reviewable commits; ordinary push only. Never commit staging builds.

Stop with:

```text
USER DECISION REQUIRED — FINAL V1.20 PROMOTION AUTHORIZATION
```

Show the exact required statement:

```text
USER APPROVED RELEASE PROMOTION V1.20 <release_digest>
```

No subsequent task, ingest, or formal publication begins in this Plan.
