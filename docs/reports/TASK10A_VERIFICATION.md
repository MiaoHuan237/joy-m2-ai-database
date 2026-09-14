# Task 10A V1.20 Multi-Batch Candidate Completion Evidence

Evidence date: 2026-09-14 (Asia/Shanghai)

Branch: `task8b/pipeline-migration`

Authority commit: `76b61016928dc865ee895a0963a399aaa959789e`

Maintained-test migration commit: `7eabedfa0096272e4c9ec60a470a9231c848a4f0`

Implementation commit: `c2668332e4c912d19e149361ca143637899422c7`

Formal authority: V1.19, 502 complete-question records

## 1. Result and boundary

Task 10A implementation is `CLOSED / PASS`. It adds the approved non-formal,
append-only V1.20 multi-batch candidate lifecycle over the immutable formal
V1.19 release. Final independent implementation review reported Critical 0,
Important 0, and Minor 0.

This checkpoint does not contain a real V1.20 batch or candidate. No new real
source was read, adapted, or preflighted; no persistent repository candidate
generation was written; and `releases/V1.20/` does not exist. Formal promotion,
a current release pointer, and any retrieval switch remain outside Task 10A
authority.

## 2. Implemented public contract

The exact approved V1.20 suffix appended to `joy_m2.ingest.__all__` is:

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
load_v120_import_manifest
adapt_mmd_package_v120
preflight_v120_import
build_v120_candidate
verify_v120_candidate
```

The Task 9A-9D V1.19 names remain the exact ordered public prefix. The explicit
source-mapping module similarly preserves its historical four-name prefix and
adds only `adapt_mmd_package_from_mapping_v120` as the approved suffix.

## 3. Authority and lifecycle closure

The implementation provides:

- strict V1.20 canonical import-manifest loading;
- parser-mode and explicit-source-mapping projection into the same V1.20
  canonical package contract;
- effective-state preflight against formal V1.19 or an independently verified
  prior V1.20 candidate;
- exact parent-bound approvals of the form
  `USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> V1.20 PARENT <parent_candidate_digest>`;
- a deterministic ordered batch ledger with fixed genesis, contiguous ordinals,
  unique batch/preflight identities, and count closure;
- full-prefix candidate rebuild in a private staging sibling;
- atomic no-replace publication of one immutable candidate generation; and
- a verifier independent of writer/preflight projection helpers.

Duplicate and collision checks use the complete effective state: immutable
V1.19 plus every earlier V1.20 batch. Stale preflights, wrong-parent approvals,
duplicate batch identities, source/package rebinding, baseline rebinding,
private-tree tampering, symlink escapes, and output collisions are rejected
without replacing a prior generation.

## 4. Candidate and verifier contract

The candidate database uses SQLite `user_version=120` and the exact Task 10A
ledger, candidate, image, and taxonomy objects. It retains the formal V1.19
view unchanged and adds only non-formal V1.20 candidate state.

The independent verifier closes these 24 ordered checks:

1. `candidate_directory`
2. `candidate_contract`
3. `baseline_authority`
4. `batch_authority_artifacts`
5. `parent_chain`
6. `approval_binding`
7. `preflight_reconstruction`
8. `filesystem_closure`
9. `sha256sums_closure`
10. `artifact_references`
11. `rollback_contract`
12. `image_projection`
13. `sqlite_readability`
14. `sqlite_integrity`
15. `sqlite_foreign_keys`
16. `sqlite_schema`
17. `v119_preservation`
18. `batch_ledger`
19. `candidate_projection`
20. `effective_collision_closure`
21. `count_closure`
22. `candidate_digest`
23. `deterministic_identity`
24. `formal_boundary`

All checks must pass. Verification is read-only and does not repair, rewrite,
delete, or regenerate candidate artifacts.

## 5. RED-first and independent-review evidence

Behavior was introduced through the approved model, manifest, adapter
projection, preflight, writer primitive, candidate lifecycle, and historical
replay RED-to-GREEN sequence. The pre-existing V1.19 public-surface assertions
were migrated in the separate test-only checkpoint so that they continue to
enforce an exact historical prefix plus only the approved V1.20 suffix; they
were not weakened to subset checks.

Independent review findings were converted to focused regressions before their
minimum corrections. The final suite locks exact typed/config authority,
parent and package rebinding, duplicate batch IDs, semantic batch ordering,
exact JSON type equality including `bool` versus `int`, no-replace races,
owned-state-only cleanup, non-ASCII normalization compatibility, and
historical V1.19 replay. Final review found no remaining Critical, Important,
or Minor issue.

## 6. Deterministic synthetic evidence

The three approved Task 10A fixture groups demonstrate:

- a first batch from the fixed V1.19 genesis state;
- a second batch against accumulated V1.20 effective state;
- a third batch whose semantic manifest order is preserved independently of
  filesystem discovery and candidate-ID lexical order;
- deterministic full-prefix rebuild across independent roots;
- stable manifest, SQLite, receipt, artifact-reference, and candidate-digest
  identities;
- byte-identical content-addressed image reuse; and
- failure of a later batch without mutation of any earlier candidate.

These are synthetic test authorities only. They are not approval for any real
source or batch.

## 7. Fresh verification gates

| Gate | Result | Exit |
|---|---:|---:|
| Task 10A focused | 143/143 PASS | 0 |
| Complete maintained suite excluding the attributed legacy behavior module | 854/854 PASS | 0 |
| Formal V1.19 independent verifier | 18/18 PASS | 0 |
| V1.18 independent validator | PASS; 497/452/45, integrity ok, 0 FK errors | 0 |
| `git diff --check` | PASS | 0 |

All maintained tests reported zero skips and zero expected failures. The
separately attributed legacy behavior surface remains historical evidence and
is not altered by Task 10A.

## 8. Frozen identity preservation

| Authority | Identity |
|---|---|
| Frozen V1.18 SQLite | `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7` |
| Frozen V1.18 complete-question count | 497 |
| Formal V1.19 SQLite | `5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff` |
| Formal V1.19 complete-question count | 502 |
| Formal V1.19 release digest | `7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d` |

No file under `releases/V1.18/`, `data/baselines/V1.18/`, or
`releases/V1.19/` changed. The historical V1.16 ZIP was not searched, read, or
rehashed. No formal V1.20 directory, database, manifest, approval, release, or
promotion artifact exists.

## 9. Next operational gate

The implementation is ready to accept a future explicitly selected real
MMD/MMD.ZIP source, but this checkpoint supplies no such source authority.
When a source is provided, the first approved action is read-only V1.20
adaptation and preflight against the latest independently verified effective
state. The workflow must then stop for the exact parent-bound per-batch Human
Gate before invoking the candidate writer.

Formal V1.20 promotion requires a separate Design, Plan, independent review,
and explicit human authorization; it is not implied by a ready preflight or a
non-formal candidate.

## 10. Conclusion

`TASK 10A V1.20 MULTI-BATCH CANDIDATE IMPLEMENTATION — CLOSED / PASS`

`WAIT FOR REAL SOURCE`
