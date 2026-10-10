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

## Execution rulings

## Task 2 — approved-transcription canonical bridge

- Effective RED: 11 collected, 1 API PASS, 14 assertion/subtest FAIL, 0 ERROR, exit 1. A preliminary forged-record fixture used the validating constructor and was corrected before recording behavioral RED; that setup error is not RED evidence.
- GREEN: 11 bridge + 35 model/loader + 50 existing Task10B = 96/96 PASS, no skips/expected failures.
- Independent files in two roots are byte-identical. Four non-manifest files exactly match V122 for the same synthetic verified carrier; only manifest target/schema changes. Two duplicate-looking synthetic source records are both retained, including MS, subparts, marks, taxonomy, difficulty and PDF region references. No canonical image assets are invented.
- Forged proposal/record/approval, nonverified input, symlink/path escape/source overlap, existing destination and atomic publication failure are independently exercised. Failure leaves no new output/owned temporary tree.
- Scoped inline review: only the V123 bridge/imports implement behavior; neutral projection and safety helpers are reused, all historical bridge bodies remain unchanged. Real 2023 source/approval not consumed yet.

## Execution rulings (continued)

- Final independent review and any remediation re-review follow the approved Plan (stronger than the inline skill's no-re-review default); cost: additional review time only.
- The skill's self-ignored per-plan workspace holds disposable logs/ledger under Design section 10's scratch allowance, not an extra maintained entry point.

## Remaining gates

Tasks 3–6, full candidate implementation, independent whole-implementation review, fresh final maintained/frozen gates and approved-2023 canonical/read-only preflight remain pending. No real writer, V1.23 formal release or next-year ingestion is authorized.
