# Task 9C V1.19 Temporary Writer Completion Evidence

Evidence date: 2026-09-11 (Asia/Shanghai)

Branch: `task8b/pipeline-migration`

Implementation commit: `1881a3aff5e064646395516102e5f3d39a2b619c`

Formal baseline: V1.18, 497 complete-question records

## 1. Result and authority

Task 9C temporary-root implementation is `CLOSED / PASS`. It implements the
approved deterministic V1.19 candidate writer and independent verifier, but it
does not authorize or perform the first real repository V1.19 write, import, or
promotion.

Authority and implementation checkpoints:

- Design: `9dbe183f6506ac350cb52f6ae8c3daba12b06874`
  (`docs: define Task 9C V1.19 writer design`).
- Implementation Plan: `94d35c106946aa80e41d058ce4927ed8dfcb0cd7`
  (`docs: add Task 9C implementation plan`).
- Reproducible test environment correction:
  `5e034dc96a91c00357725f97053e1176ec180d2b`.
- Phase A public contracts:
  `fbbcea03c9d5775e6553ccbe2460ee098ecd3fc4`
  (`feat: add Task 9C writer public contracts`).
- Phase A closure: `a3a6b8bb4818d3bd9c60fa1ee35c1ea18bc2bba6`.
- Lifecycle-test migration authority:
  `bfac168ac128a3d243055402df0c887a89136df8`.
- Phase B implementation: `1881a3aff5e064646395516102e5f3d39a2b619c`
  (`feat: add verified V1.19 candidate writer`).

The final independent implementation review reported Critical 0, Important 0,
and Minor 0. Task 9C has no unresolved implementation blocker.

## 2. Implemented contract

The public APIs are:

```python
build_v119_candidate(
    request: V119WriteRequest,
    config: PipelineConfig,
) -> V119CandidateArtifacts

verify_v119_candidate(
    request: V119VerificationRequest,
    config: PipelineConfig,
) -> VerificationReport
```

The writer accepts only the exact approved typed request, digest-bound Task 9A
preflight authority, exact import approval, frozen V1.18 baseline identity, and
approved V1.19 writer contract. It copies the baseline, adds only the approved
candidate tables and view, projects candidate records without making them
formal/selectable, stages byte-identical content-addressed images, and writes a
canonical manifest, `SHA256SUMS`, and declarative rollback receipt. Publication
uses a single atomic no-replace directory rename after a successful independent
verification; failure removes only the private temporary tree.

The verifier is read-only and closes the ordered 16-check contract:

1. `candidate_directory`
2. `manifest_contract`
3. `preflight_approval_binding`
4. `filesystem_closure`
5. `sha256sums_closure`
6. `artifact_references`
7. `rollback_contract`
8. `image_projection`
9. `sqlite_readability`
10. `sqlite_integrity`
11. `sqlite_foreign_keys`
12. `sqlite_schema`
13. `sqlite_projection`
14. `baseline_preservation`
15. `count_closure`
16. `publication_boundary`

All required checks passing closes the report to `PASS`; any failed check
closes it to `FAIL`. Verification never repairs, deletes, rewrites, or
regenerates candidate artifacts.

## 3. RED-first and remediation evidence

Phase A first established a valid 9-test RED caused only by the absent public
Task 9C contracts, then reached 9/9 GREEN.

Before Phase B production changed, tests established and validated all four
approved behavior RED groups: database/profile/projection, image handling,
manifest/sums/rollback/verifier, and builder gates/transaction/determinism/
atomicity. Imports and fixtures were valid; failures reached the approved Phase
A `NotImplementedError` or absent private behavior rather than setup errors. A
recorded early builder subset collected 5 tests and produced 5 expected RED
failures with 0 errors. The complete Phase B behavior suite later reached
35/35 GREEN and expanded through independent-review negative controls to the
final 71/71 GREEN.

Every Critical or Important review finding was first reproduced by a focused
contract RED before the minimum approved-scope correction. Final remediations
lock exact carrier reconstruction, canonical artifact paths, hostile path and
symlink boundaries, SQLite header/schema/projection closure, large/nested JSON
format handling, rogue-file closure, verifier exception/report semantics,
atomic publication, and non-mutation. Final review found no remaining Critical,
Important, or Minor issue.

## 4. Deterministic temporary-root evidence

A representative one-candidate write with one image was executed only beneath
independent OS temporary roots. Equivalent roots produced identical SQLite,
manifest, sums, rollback, image bytes, and `ArtifactRef` identities.

| Artifact | Bytes | SHA-256 | Kind |
|---|---:|---|---|
| `Joy_M2_V1.19_candidate.sqlite3` | 9412608 | `2853cbdda4b2f918eef250ac5407102a54084aa24fd2dcf7639237c80c1b621b` | `sqlite` |
| `candidate_manifest.json` | 2546 | `c08c9525f285b1d8e3183d156637345bffd069c75d4c778df4b6d2ff44f4d07c` | `manifest` |
| `SHA256SUMS` | 419 | `8a1f47afadc8a16997ca5fe7ac9b68855721ba759e998189d2d8330dffd366bf` | `sha256sums` |
| `rollback.json` | 629 | `c3dd2c0e2c631d3ef1d44d855c2ccaeb8c740af9594ec558ff358eda6313d308` | `rollback` |
| `images/sha256/49/493231680e26fa7591a1fbe8c6c8cbe9a9429ec0608ce8865e5ad62a674e8a7e.png` | 25 | `493231680e26fa7591a1fbe8c6c8cbe9a9429ec0608ce8865e5ad62a674e8a7e` | `image` |

The representative candidate used approved schema
`task9-v119-candidate-v1`, SQLite `user_version=119`, baseline count 497,
candidate count 1, and projected count 498. Its independent verification report
was `PASS`. These hashes are temporary-root implementation evidence, not an
approval or precomputed identity for a future real batch.

## 5. Fresh verification gates

| Gate | Result | Exit |
|---|---:|---:|
| Task 9C focused | 71/71 PASS | 0 |
| Maintained suite excluding `tests.regression.test_task8b_legacy_pipeline_behavior` | 535/535 PASS | 0 |
| Task 9A Models/Manifest | 14/14 PASS | 0 |
| Task 9A integration | 41/41 PASS | 0 |
| Task 9B focused adapter | 214/214 PASS | 0 |
| Task 7 | 7/7 PASS | 0 |
| Task 8 equivalence | 3/3 PASS | 0 |
| Release focused plus Task 3A | 48/48 PASS | 0 |
| Public Models | 66/66 PASS | 0 |
| Models + Config | 80/80 PASS | 0 |
| Audit focused | 21/21 PASS | 0 |
| Database focused | 14/14 PASS | 0 |
| Export focused | 22/22 PASS | 0 |
| Export + Database | 36/36 PASS | 0 |
| Task 3-6 executable legacy gates | 54/54 PASS | 0 |
| V1.18 independent validator | PASS; 497/452/45, integrity ok, 0 FK errors | 0 |
| Legacy attribution suite | 9 PASS / 2 FAIL | 1 (approved baseline) |

All passing maintained suites reported zero skips and zero expected failures.
The two legacy attribution failures remain exactly the approved deterministic
SQLite hash and frozen artifact byte-equivalence categories; no third failure
appeared.

## 6. Frozen and zero-write boundaries

- Frozen V1.18 SQLite SHA-256 remains
  `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`.
- V1.18 remains at 497 complete questions.
- Real repository V1.19 artifacts: 0; imported questions: 0.
- No file under `data/`, `releases/`, `legacy/`, or frozen baselines changed.
- The actual V1.16 ZIP was not searched, read, or rehashed.
- No real import approval, import, release promotion, CLI, Task 8C, or Phase 2A
  began.
- Task 9A remains the deterministic read-only preflight; Task 9B remains the
  staging-only MMD adapter.

## 7. Human Gate B proposal

No real output root has been selected or created. If the user authorizes the
first repository write, the proposed new strict descendant of `data/staging/`
must contain exactly:

```text
<approved-output-dir>/
  Joy_M2_V1.19_candidate.sqlite3
  candidate_manifest.json
  SHA256SUMS
  rollback.json
  images/sha256/<prefix>/<digest><canonical-extension>  # zero or more
```

The frozen source baseline is V1.18 at SHA-256
`fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`
and 497 questions. The approved candidate schema is
`task9-v119-candidate-v1` with SQLite `user_version=119`. For the reviewed Task
9B 17-candidate preflight, the projected count is 514, but a real write must
bind and revalidate the exact approved preflight and approval at execution.
Equivalent inputs and roots must produce identical candidate bytes and SHA-256
identities. Rollback is declarative removal of the complete unpromoted candidate
tree; publication failure cleans only its private temporary tree. V1.18 is
opened as the immutable source baseline and must remain byte-identical.

Human Gate B grants no Task 9D import approval or promotion authority. A future
authorization must select the exact repository output directory and bind the
approved preflight/approval before any artifact is written.

## 8. Conclusion

`TASK 9C TEMPORARY WRITER — CLOSED / PASS`

Implementation blockers: `NONE`.

Next action: `USER DECISION REQUIRED — FIRST V1.19 WRITE AUTHORIZATION`.
