# Task 9B Mathpix MMD Adapter Completion Evidence

Evidence date: 2026-09-11 (Asia/Shanghai)

Branch: `task8b/pipeline-migration`

Implementation commit: `35778b80f931ecf4903ca553ab0fb1b1bb5e8110`

Formal baseline: V1.18, 497 complete-question records

## 1. Result and authority

Task 9B is `CLOSED / PASS` locally. It implements the approved Mathpix
MMD/MMD.ZIP parser mode plus the explicit source-mapping fallback and emits
only a canonical Task 9A staging package after the mode-specific authority
gate. It does not approve an import, write a database, create a V1.19 formal
artifact, or promote a release.

Authority and implementation checkpoints:

- Design: `d19baa812213c8015dbb63a9ce3f431eaa077f42`
  (`docs: define Task 9B MMD adapter design`).
- Implementation Plan: `e46bd5b856591b36f69fbaa5fc80738335ba3c66`
  (`docs: add Task 9B implementation plan`).
- Reviewed representative fixtures: `c1125252efea59805f616d6347960b81f5d4f08c`
  (`test: add reviewed Task 9B fixtures`).
- Independent golden reconciliation: `141d2c8daf431a7512d689395c5b31f84c8a8251`
  (`test: reconcile Task 9B golden authority`).
- Implementation: `35778b80f931ecf4903ca553ab0fb1b1bb5e8110`
  (`feat: add deterministic Mathpix MMD adapter`).

The final independent implementation review reported `CLEAN`: Critical 0,
Important 0, Minor 0. Task 9B has no unresolved implementation blocker.

## 2. Implemented contract

The public API is:

```python
adapt_mmd_package(
    selection_manifest_path,
    source_path,
    output_dir,
    config,
) -> AdaptedImportPackage
```

The only public Task 9B carriers are `MmdSelection`, `MmdAdapterManifest`,
`MmdAdapterIssue`, `MmdAdapterBlockedError`, and `AdaptedImportPackage`.

The implementation preserves the approved D0-D7 dependency order:

1. strict selection-manifest validation before source access;
2. bounded plain/ZIP inventory safety and integrity validation;
3. fixture-scoped deterministic line/state parsing into private source IR;
4. explicit occurrence and answer binding;
5. candidate-count closure;
6. bilingual rendering and provenance mapping;
7. explicit image binding and canonical package publication.

All output is written atomically beneath the configured staging root. Failure
leaves no partial output. No `extractall()` path exists, all archive members are
validated before selected content is read, and source/archive discovery order,
absolute paths, temporary roots, ZIP timestamps, permissions, and comments are
excluded from semantic identity.

## 3. RED-first and review evidence

Every production behavior followed a valid RED before its minimal GREEN. Final
review remediations additionally locked:

- display-aware local and separate-answer boundaries;
- source-target versus inventory NFC/casefold collision detection;
- present-image resolution in private source IR;
- full atomic/image grammar validation inside local and separate solutions;
- plain-MMD solution-only image symlink escape at D3 without promoting that
  image to candidate or source-map authority.

The final symlink-escape counterexample first failed because no
`MmdAdapterBlockedError` was raised. After the minimal correction it passes as
the exact `archive_member_unsafe / image_target_normalized_escape` blocker.
Solution-only image tokens remain outside candidate `image_paths`, source-map
image references, manifest image files, and staging.

## 4. Golden equivalence

The independently authored golden tree imports no Task 9B production adapter,
parser, or helper. Its committed artifacts are:

| File | Bytes | SHA-256 |
|---|---:|---|
| `records/candidates.json` | 122015 | `2f63c6d9c50ed0ce76262333ece9c586aecd8f3bfab20fb7905aa0713dee5ba8` |
| `source/source-map.json` | 182646 | `258d5469a79ba62f7f66e2f121090d5782e2e1a59b54f2db6b1509c91e02bfde` |
| `import_manifest.json` | 1908 | `532b1877dc0ab4c327cebacff9edb1888ddb2fb2f8b028e02cda1c88945fa78e` |

Adapter output and the independent golden produce equal Task 9A candidates,
issues, counts, status, report, and digest:

- status: `READY FOR USER IMPORT APPROVAL`;
- candidates: 17;
- issues: 0;
- before/detected/new/projected: 497/17/17/514;
- duplicate/rejected/ambiguous/approved: 0/0/0/0;
- preflight SHA-256:
  `49ab71e26cf2256581ecb5ada14b0eefc601317169ee897599aeb9a39976187b`.

This status is test evidence only. No user import approval was issued and no
question was imported.

## 5. Fresh verification gates

| Gate | Result | Exit |
|---|---:|---:|
| Task 9B focused, including explicit source mapping | 342/342 PASS | 0 |
| Maintained suite excluding separately attributed legacy module | 464/464 PASS | 0 |
| Task 9A integration | 41/41 PASS | 0 |
| Task 7 | 7/7 PASS | 0 |
| Task 8 equivalence | 3/3 PASS | 0 |
| Release focused | 48/48 PASS | 0 |
| Task 3 legacy gate | 13/13 PASS | 0 |
| Task 4 legacy gate | 9/9 PASS | 0 |
| Task 5 legacy gate | 10/10 PASS | 0 |
| Task 6 legacy oracle | 22/22 PASS | 0 |
| Task 3-6 total | 54/54 PASS | 0 |
| V1.18 independent validator | PASS; 497/452/45, integrity ok, 0 FK errors | 0 |
| Legacy attribution suite | 9 PASS / 2 FAIL | 1 (approved baseline) |

All passing maintained suites reported zero skips and zero expected failures.
The two legacy attribution failures remain exactly the approved deterministic
SQLite hash and frozen artifact byte-equivalence categories; no third failure
appeared.

## 6. Frozen and delivery boundaries

- V1.18 SQLite SHA-256 remains
  `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`.
- V1.18 remains at 497 complete questions.
- V1.19 artifacts: 0; imported questions: 0.
- No file under `data/`, `releases/`, `legacy/`, or frozen baselines changed.
- The actual V1.16 ZIP was not searched, read, or rehashed.
- No CLI, Task 8C, Phase 2A, Task 9C writer, Task 9D import, or promotion began.
- Working tree and staging were clean after the implementation commit.
- Ordinary push to `origin/task8b/pipeline-migration` was attempted but GitHub
  connectivity was unavailable. Remote synchronization remains a delivery-only
  retry; no force push or history rewrite occurred.

## 7. Explicit source-mapping extension checkpoint

The approved extension keeps parser mode unchanged and adds a separate
`joy_m2.ingest.source_mapping` module with exactly:

```text
SourceMappingProposal
SourceMappingApproval
propose_mmd_source_mapping
adapt_mmd_package_from_mapping
```

Authority checkpoints are `c11f463` (mode Design), `4a5b6a3` (diagnostic
closure), `ea6bf7f` (implementation Plan), and `78a5262` (final diagnostic
envelopes). The implementation and this closure evidence are committed
together as `feat: add explicit MMD source mapping`.

All four extension RED groups were established before production. Subsequent
independent-review findings were remediated test-first, including source-free
M0 closure, span and complete-question validation, UTF-8 boundaries, image
inventory and NFC/casefold precedence, Mode A compatibility, exact enrichment,
and review-preview preservation. Final dual independent review is Critical 0,
Important 0, Minor 0.

The proposal API emits deterministic `source_mapping.json` and
`SOURCE_MAPPING_REVIEW.md` only. A proposal is not authority and cannot be
consumed without the exact, separately typed source-mapping approval. Mapping
approval remains distinct from Task 9A import approval.

## 8. Next boundary

Task 9B closure grants no writer, import, or promotion authority. For the first
real ambiguous source, execution may generate a deterministic proposed source
mapping but must stop at `USER DECISION REQUIRED — SOURCE MAPPING REVIEW`.
Without exact `USER APPROVED SOURCE MAPPING <source_id> <mapping_sha256>` text,
the mapping may not be consumed, no canonical package may be created, and Task
9A preflight may not run. The later real digest-bound batch import and formal
promotion remain separate HUMAN GATES C and D.

## 9. Conclusion

`TASK 9B MMD ADAPTER — CLOSED / PASS`

Implementation blockers: `NONE`.

Remote delivery retry: `PENDING GITHUB NETWORK RECOVERY`.
