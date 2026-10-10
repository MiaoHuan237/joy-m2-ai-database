# V1.23 candidate authority — implementation evidence

Status: IN PROGRESS. Approved Design/Plan base: c7d54371bc809c204799f94ab6908bd6bd9641eb.
Human Native / Inline execution approval received 2026-10-10. No real import approval.

## Task 1 — models / API scaffolds / strict loader

- Module existence RED: 1 collected, 1 assertion FAIL, 0 ERROR, exit 1.
- Model-contract existence RED: 15 collected, 1 PASS / 14 assertion FAIL, 0 ERROR, exit 1; exact model GREEN 15/15. These assertions establish missing public contracts, not preflight/writer behavior.
- API RED: 3 collected, exact suffix and five function assertions fail (6 subtest failures), 0 ERROR, exit 1; models/API GREEN 17/17.
- Six historical export suites: 55 collected, six exact-surface failures before the approved expectation migration. All old exports/order retained; only the exact 18-name suffix appended (old promotion tail remains checked).
- Loader behavior RED: 16 collected, 28 assertion/subtest FAIL, 0 ERROR, exit 1. Only operation-under-test NotImplementedError is converted to assertion failure. Valid fixture setup precedes the operation.
- Loader GREEN and additional nested-carrier/tuple isolation preservation checks: 35 new tests; combined six historical modules 90/90, no skip/expectedFailure. UTF-8/JSON/nonfinite/duplicate keys, wrong target/schema/types/order, unsafe paths, inventory and hash/size controls included.
- Scoped inline review: compared all 13 field/type envelopes, fixed V1.22/639 baseline and V1.23 namespace/genesis, five API annotations, exact export suffix and six historical test diffs. Preflight/bridge/writer/verifier remain NotImplementedError; profile module is docstring-only. No later behavior ported.
- User AGENTS SHA remains `75ffa9680b18a0875fde8d36a8ca3e0ebda0603f10e8dc788e71ea8353d0311d`; excluded from every task commit.

## Task 2 — approved-transcription canonical bridge

- Effective RED: 11 collected, 1 API PASS, 14 assertion/subtest FAIL, 0 ERROR, exit 1. A preliminary forged-record fixture used the validating constructor and was corrected before recording behavioral RED; that setup error is not RED evidence.
- GREEN: 11 bridge + 35 model/loader + 50 existing Task10B = 96/96 PASS, no skips/expected failures.
- Independent files in two roots are byte-identical. Four non-manifest files exactly match V122 for the same synthetic verified carrier; only manifest target/schema changes. Two duplicate-looking synthetic source records are both retained, including MS, subparts, marks, taxonomy, difficulty and PDF region references. No canonical image assets are invented.
- Forged proposal/record/approval, nonverified input, symlink/path escape/source overlap, existing destination and atomic publication failure are independently exercised. Failure leaves no new output/owned temporary tree.
- Scoped inline review: only the V123 bridge/imports implement behavior; neutral projection and safety helpers are reused, all historical bridge bodies remain unchanged. Real 2023 source/approval not consumed yet.

## Task 3 — genesis preflight

- RED: 23 collected, 27 assertion/subtest failures, 0 errors, exit 1. Strict package-load smoke passes before calling the scaffold. Two preservation/API tests are already GREEN; no setup errors count as RED.
- GREEN: 23/23 focused; Tasks1–3 69/69, no skips/expected failures. Effective state 639/empty ledger/fixed reconstructed genesis, one synthetic net-new projects640; not a prediction for real2023.
- Tests cover all four 2019–2022 inherited layers and historical image reference identity, complete639 indexing, frozen counts, malformed/invalid candidate issues, taxonomy, exact duplicates despite fuller MS, truthful second-source hash collisions, adaptations and candidate-ID exclusion, ambiguity, mixed duplicate batch blocking, package blocker vs per-record counts, and untrusted file omission.
- Copied-baseline negative controls reach metadata version/schema, view/count/unique-ID/published/selectable checks independently of outer file hashes. Escaped-space/#/Unicode URI baseline copies are read-only. No formal file changes.
- Scoped review: no candidate DDL/writer or verified-parent branch implemented. Genesis helper reconstructs the literal approved projection using neutral canonical-JSON/hash helpers. The copied formal reader explicitly checks published/selectable state and query-only immutable URI under the approved V123 contract; historical readers are unchanged.
- Protected snapshot: 292/292 files unchanged; user AGENTS SHA unchanged; releases/V1.23 absent.

## Task 4A — first-generation writer / verifier

- Effective RED: 23 collected, 27 assertion/subtest failures, 0 errors, exit 1, at writer/verifier scaffolds. Earlier private-API setup errors were excluded. GREEN: 23/23 focused, 93/93 cumulative including public API; no skips/expected failures.
- Fixed DDL adds only task13 tables/view and private user_version123. First synthetic batch yields640; all inherited schema SQL, tables/views/metadata and image fields remain exact. New rows remain candidate/selectable0.
- Writer and verifier independently reconstruct genesis and bind report/approval. All24 checks, malformed-context exceptions vs parsed corruption FAIL, canonical reconstruction, closure, FK/schema/count/image/rollback tampering, no-replace/fault cleanup and two-root ALL-byte determinism are exercised.
- Scoped inline review: first-generation only. Single-batch projection and SQLite insertion; no prefix replay reconstruction. Multi-batch writer explicitly remains unimplemented and parent preflight remains a scaffold. Pure hash/JSON/path/SQL/image helpers reuse their version-neutral implementations.
- GREEN development corrected a wrong helper import and fixed expected_user_version123 in the verifier contract; these implementation errors were not new RED evidence. A test prerequisite used the same output twice and now uses a separate control directory without relaxing assertions.

## Task 4B1 — verified-parent preflight

- RED: 9/9 failures, 0 errors, exit1, exclusively at parent-preflight scaffold after first-generation build and independent PASS. GREEN: 9 focused; candidate + genesis-preflight suites56/56 PASS, no skips/expected failures.
- Exact parent digest/ledger/count640→641, accepted-parent duplicate and ID collision, retained2022 formal IDs, taxonomy union, missing closure/wrong-version/genesis-reset/stale-request refusal, concurrent parent-change rejection and equivalent-root digest equality are covered. Parent bytes remain unchanged.
- A synthetic taxonomy test initially used B's different tag after intentionally removing formal vocabulary; its input now uses A's actual accepted taxonomy to isolate parent-derived vocabulary. No taxonomy contract or assertion was weakened.
- Scoped review: only parent-preflight and tests changed; first-generation writer remains limited to one batch. All639 baseline rows plus verified parent rows form indexes; independent verification runs before and after parent reads.

## Execution rulings

## Task 4B2 — ordered multi-batch writer / verifier

- RED: 8 collected, 9 assertion/subtest failures, 0 errors, exit1; every second-batch operation follows verified A and READY B bound to A. The already-safe nonmatching-generation verifier refusal passed before prefix support. Added URI hardening test independently failed on missing immutable flag, not an input/setup error.
- GREEN: 9 focused / 111 cumulative V123 tests PASS, zero skips/expected failures. Full(A,B) gives641, third preflight642 and detects collisions against BOTH A and B. No real-data count is predicted.
- Full prefix replay, stale B/C approvals, old target, null/empty/genesis reset, duplicate/truncated/reordered/substituted batches, forged counts/candidates, changed canonical bytes, no-replace, failed-publication preservation, two-root byte equality and all read-only connections are covered.
- Scope review: only after 4B1 GREEN are full-prefix reconstruction and multi-batch database insertion enabled. All readonly SQLite connections in V123 use escaped absolute URI, mode=ro&immutable=1 and query_only=ON. The parent-preflight hardening is an owning-task in-scope correction under Plan Global Constraints, not historical reader changes.
- Protected baseline/source/candidate snapshot292/292 unchanged; AGENTS hash unchanged; releases/V1.23 absent.

## Execution rulings

- Final independent review and any remediation re-review follow the approved Plan (stronger than the inline skill's no-re-review default); cost: additional review time only.
- The skill's self-ignored per-plan workspace holds disposable logs/ledger under Design section 10's scratch allowance, not an extra maintained entry point.

## Remaining gates

Tasks 5–6, independent whole-implementation review, fresh final maintained/frozen gates and approved-2023 canonical/read-only preflight remain pending. No real writer, V1.23 formal release or next-year ingestion is authorized.
