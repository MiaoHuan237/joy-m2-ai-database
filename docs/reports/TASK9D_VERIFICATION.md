# Task 9D V1.19 Promotion Completion Evidence

Evidence date: 2026-09-13 (Asia/Shanghai)

Branch: `task8b/pipeline-migration`

Implementation commit: `b5a47f4a231b2374ae6db0931a6754a52d11296e`

Current formal authority: V1.19, 502 complete-question records

## 1. Result and authority

Task 9D is `CLOSED / PASS`. The exact Human Gate D statement was received, the
approved public API atomically published the verified dry-run to
`releases/V1.19/`, and the formal tree independently verifies all 18 checks.

Authority and implementation checkpoints:

- Design: `4f9924a712d02feb889cbd24e5c3867a9daba31c`
  (`docs: define Task 9D V1.19 promotion design`).
- Implementation Plan: `d1057affd79e7fd81119cd62bdc08d0982958cd3`
  (`docs: add Task 9D promotion implementation plan`).
- Public-surface scope alignment:
  `7af421fdce7a722da6f43aec7d3cd6656d7675b9`.
- Implementation: `b5a47f4a231b2374ae6db0931a6754a52d11296e`
  (`feat: add verified V1.19 promotion pipeline`).
- Post-Gate-D lifecycle and symlink-root safety:
  `d1954a96e5783a9bfb4d28b4b86b77bbac8c50fd`
  (`fix: preserve V1.19 release root identity`).
- Formal four-file release: `e8b55147d6e0fcaa6e1e842393534adcfda96680`
  (`release: publish formal V1.19`).

The final post-publication independent implementation reviews reported Critical
0, Important 0, and Minor 0. There is no unresolved Task 9D blocker.

## 2. Exact input authority

The real dry-run consumes only:

- frozen V1.18 SQLite SHA-256
  `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`;
- verified Task 9C candidate root
  `data/staging/task9c-v119-real-0918-interval-candidate/`;
- candidate SQLite SHA-256
  `9d30cf444e9d6686128f884d5a3cf57f4e58ce544b7933d7a0a47ec0e8212d20`;
- candidate manifest SHA-256
  `b2e0b4607b49f5e1e097fd036dd0614c67128976e7d282f4e2783eb092be9634`;
- batch ID `TASK9B-REAL-0918-INTERVAL-REPRODUCTION-001`;
- preflight SHA-256
  `4aa3ff8b419a0fcca57c805d5f10f252658cb30c00f6cf1b74c95ab3009333c9`;
- exact Gate C statement binding that batch, preflight, and V1.19.

The candidate verifier closes all 16 ordered checks to `PASS`. Gate C is input
authority only and does not authorize formal publication.

## 3. Implemented contract

The approved public APIs are:

```python
build_v119_promotion(
    request: V119PromotionBuildRequest,
    config: PipelineConfig,
) -> V119PromotionArtifacts

verify_v119_promotion(
    request: V119PromotionVerificationRequest,
    config: PipelineConfig,
) -> VerificationReport

publish_v119_release(
    request: V119PublicationRequest,
    config: PipelineConfig,
) -> V119PromotionArtifacts
```

The builder copies the verified candidate SQLite into a private staging tree,
adds the exact formal promotion relations, changes only the five approved
candidate rows to formal `published` records, creates the 502-row formal view,
and writes canonical manifest, hash closure, and rollback artifacts. It does
not enrich, reinterpret, reclassify, or regenerate question content.

The independent verifier closes these 18 ordered checks:

1. `release_directory`
2. `promotion_contract`
3. `candidate_verification`
4. `manifest_contract`
5. `authority_binding`
6. `filesystem_closure`
7. `sha256sums_closure`
8. `artifact_references`
9. `rollback_contract`
10. `sqlite_readability`
11. `sqlite_integrity`
12. `sqlite_foreign_keys`
13. `sqlite_schema`
14. `baseline_preservation`
15. `promotion_projection`
16. `formal_query`
17. `count_closure`
18. `publication_boundary`

All checks must pass. Verification is read-only and never repairs artifacts.
Malformed manifest JSON is an input-format exception; parsed but invalid
content closes to a structured `FAIL` report.

## 4. RED-first and remediation evidence

Public contracts first produced 9/9 expected RED failures because the Task 9D
models and APIs did not exist, then reached 9/9 GREEN. Before behavior
production was written, the combined behavior gate collected 18 test methods
and produced 23 expected failing subtests with zero setup/import errors.

Independent review findings were converted to focused REDs before each minimum
correction. The principal remediation checkpoint produced 14 expected failures
and 1 expected error across seven targeted tests. Later resource-lifetime,
manifest-rebind race, and root-symlink regressions each independently
demonstrated their failure before correction. The final Task 9D focused suite
is 48/48 PASS, including:

- Gate D source-swap/TOCTOU rejection and post-copy approval rebinding;
- complete baseline and candidate relation preservation;
- nonzero-image source-to-formal projection;
- upstream size, canonical JSON, exact file and directory closure;
- malformed and parsed-invalid JSON boundaries, including rebind races;
- successful and partial-open SQLite connection closure;
- atomic no-replace build/publication and owned-state-only cleanup;
- leaf, ancestor, and loop symlink rejection before verification/publication;
- clean-clone reproducibility without ignored staging fixtures.

## 5. Real dual-root dry-run

The final implementation built and independently verified two new non-formal
roots:

- `data/staging/task9d-v119-real-promotion-dry-run-a/`
- `data/staging/task9d-v119-real-promotion-dry-run-b/`

Their complete file trees are byte-identical. Each verifier report is 18/18
`PASS`. Both bind:

| Identity | Value |
|---|---|
| release digest | `7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d` |
| formal SQLite SHA-256 | `5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff` |
| formal SQLite semantic SHA-256 | `25b19d20af337f83455e8da7e5339a00986a494c0241d167e9097476898be104` |
| manifest SHA-256 | `cd048408df5e062592d5ed8553b3461860c876b0264660ab65c78c428584a510` |
| `SHA256SUMS.txt` SHA-256 | `e0c944526d816d89caf8cd996443a5bfcff62cfde59ca8950f98c8a7aec6a5c5` |
| rollback SHA-256 | `e05e194cc4125e8d14516ace38203d3813a5653eb0ea663a9cef8117ced9f681` |
| formal SQLite size | 9,478,144 bytes |
| baseline / promoted / total | 497 / 5 / 502 |
| formal images | 0 |

The published formal tree contains exactly four core files and no images:

```text
releases/V1.19/
  Joy_M2_Complete_Question_DB_V1_19.sqlite3
  manifest.json
  SHA256SUMS.txt
  rollback.json
```

The formal tree is byte-identical to both approved dry-run roots and independently
closes all 18 verifier checks to `PASS`.

## 6. Determinism and preservation

The two dry-runs have identical SQLite bytes, semantic digest, manifest bytes,
hash receipt, rollback bytes, artifact references, release digest, and ordered
verification results. The old 497 records and all inherited baseline relations
remain equal to V1.18 except the explicitly approved release metadata
projection. All Task 9C candidate-only relations remain equal to the verified
candidate. The five promoted rows preserve question, solution, translation,
source, missing-explanation, empty/missing-tag, null/missing-difficulty, and
incomplete-enrichment values exactly.

V1.18 remains byte-identical at 497 questions. The real Task 9C candidate
SQLite and manifest hashes remain unchanged. The historical V1.16 ZIP was not
searched, read, or rehashed.

## 7. Fresh verification gates

| Gate | Result | Exit |
|---|---:|---:|
| Task 9A integration | 41/41 PASS | 0 |
| Task 9B focused | 342/342 PASS | 0 |
| Task 9C focused | 71/71 PASS | 0 |
| Task 9D focused | 48/48 PASS | 0 |
| Complete maintained suite excluding the attributed legacy behavior module | 711/711 PASS | 0 |
| V1.18 independent validator | PASS; 497/452/45, integrity ok, 0 FK errors | 0 |
| `git diff --check` | PASS | 0 |

All maintained suites have zero skips and zero expected failures. The separately
attributed legacy baseline is unchanged and is not a Task 9D completion gate.

## 8. Rollback and completed publication

Because V1.18 is never modified, rollback before publication removes only the
Task 9D-owned failed private tree. The canonical rollback receipt is declarative
and grants no deletion authority by itself. After approved publication, removal
of the complete V1.19 tree is allowed only when both its release digest and
complete artifact closure still match; rollback never rewrites V1.18.

After the exact Gate D approval, publication performed these steps:

1. independently verify the approved dry-run root;
2. bind its release digest to the exact approval carrier;
3. copy to a private sibling beneath `releases/`;
4. compare the complete source/private fingerprints;
5. rebind the private snapshot to Gate D;
6. atomically rename without replacement to `releases/V1.19/`;
7. independently verify and rebind the final formal root.

Before rename, a failure cleans only the Task 9D-owned private tree. After
rename, a failed verification removes the just-created V1.19 tree only when its
release digest and complete tree fingerprint still match the preverified source;
if that state changed, promotion raises `PromotionError` and leaves it untouched.
There is no current-release pointer or index in this repository, so no
pointer/index update is required or authorized.

## 9. Human Gate D

Human Gate D was satisfied by the exact statement:

```text
USER APPROVED RELEASE PROMOTION V1.19 7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d
```

The statement bound the approved release digest and was consumed only by
`publish_v119_release()`. No approval was inferred or reused. The formal tree
exists, no current-release pointer/index was created, and no next implementation
task is authorized.

## 10. Conclusion

`TASK 9D FORMAL V1.19 PROMOTION — CLOSED / PASS`

`WAIT FOR EXPLICIT NEXT-TASK AUTHORIZATION`
