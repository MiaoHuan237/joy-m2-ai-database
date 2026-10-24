# V1.24 promotion readiness — fixed chapter generation 000008

2026-10-24. Authority: user's current readiness/execution request authorizes
local written scope, independent review and Native/Inline implementation.
This is not a claim that the user reviewed these newly written words.
No formal publication approval exists.

## 1. Fixed inputs and preserved authority

Existing worktree / branch task8b/pipeline-migration, starting HEAD
1adb934461e77b4624615fdc499d8e84908f8e8b. AGENTS.md remains user-owned/unstaged.
Baseline V1.23: 677 records; task13-v123-formal-v1.
SQLite SHA 28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd,
10928128 bytes. Manifest SHA
54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498, 6728 bytes.
Release digest 84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc.

Candidate root:
data/staging/vector-ch12-v124-S08-delegated-20261024-000001/candidate-generation-000008.
Digest 3f14589da452207d0088cd44689aded7ffbadea0768a85d808a67ae526a5f3ab.
SQLite SHA 93acb2b4c333c4cb881c327389569898ab110ab2f436f00f1d40586e0ed4f8a0,
11378688 bytes; manifest SHA
34cd37e27370a72e332d7047d9699d3910d853e1276132ce33ec26df4786de94,
676520 bytes. Candidate schema task14-v124-ch12-candidate-v1.
Ledger JOY-M2-OSM-M2B12-VECTOR-20261023-001-S01 through S08:
16,14,4,14,11,32,20,3; 114 additions, total791.
Fresh existing historical candidate verifier passed24/24 before writing this spec.

Use exact ChapterVerificationRequest and verify_chapter_candidate, not the
manual-only V124 carrier. Preserve exact historical batches/approvals/preflights.
S01–S03 human exact import; S04–S08 ChapterImportDecision. Source review types
also stay distinct. Historical validation uses existing live=False rules:
scope completion expiry prevents future execution but does not invalidate
previously accepted in-scope decisions. Never remove REVOKED or renew authority.
Reject invalid evidence, changed package/source/baseline or mixed parent chain.
Read stored preflight/receipt carriers; do not rerun writers or mint decisions.

## 2. Counterpart and minimal interface

Pinned counterpart: three v123_promotion*.py modules at starting HEAD and
2026-10-14-v123-promotion-readiness-design.md. New version-specific siblings,
not a generic engine and not global edits to historical constants.
Module-local API only (no package-root export changes):
V124PromotionContract, V124PromotionBuildRequest,
V124PromotionVerificationRequest, V124ReleasePromotionApproval,
V124PublicationRequest, V124PromotionArtifacts;
build_v124_promotion(request,config), verify_v124_promotion(request,config),
publish_v124_release(request,config). Frozen exact carriers match counterpart,
except candidate is exact ChapterVerificationRequest.
Contract fields/order match counterpart; role-specific names use V1.24,
task14-v124-formal-manifest-v1, task14-v124-formal-v1,
task14-v124-promotion-identity-v1, task14-v124-formal-rollback-v1,
user_version124, Joy_M2_Complete_Question_DB_V1_24.sqlite3,
task14_v124_promoted_questions_v1, task14_v124_promotion_v1,
formal_complete_questions_v124. Other filenames/image_root unchanged.
Semantic schema task14-v124-sqlite-semantic-v1.

## 3. Exact content and image projection

Copy candidate SQLite into private non-formal output, transactionally append
promotion metadata/table/view. Promote only task14_v124_candidates_v1 rows,
ordered aggregate_order678–791; eight batch ordinals.
Copy first30 candidate column values exactly, rename order/id/source-image
columns as counterpart, append published/1. No content enrichment.
View unions formal_complete_questions_v123 once with new114 once.
Preserve every inherited table/view/row/schema and metadata except the twelve
counterpart release metadata keys with task14 role,677/114/791/8 values.
Formal view791 unique IDs/order1–791, all published/selectable.
All baseline677 values and new114 source fields compared, not only counts.

For the new114 rows only, candidate declares72 independent original JPEGs,833787 bytes. Copy each exact
candidate relative path/bytes once; preserve every ordered question/solution
image binding and role. Verify parallel source-path/hash/role/formal-path arrays,
each formal image resolves within output, exact SHA and size, declared closure
equals all referenced images; reject missing/extra/reordered/role-altered data.
The72-file local closure does not include inherited677 image references (whose
historical string/object paths retain their original semantics). Do not copy
unrelated historic resources or clear inherited image references.
Preserve known limitations, final-only answers, partial coverage and missing
explanations without promoting them to worked solutions or mathematical proof.
In dry-run and restored copy open/decode all72 actual files, not staging aliases.

## 4. Artifacts, identity, independent verification

Exact output set: database,manifest.json,SHA256SUMS.txt,rollback.json plus72
declared images =76 files. Authority files remain immutable referenced evidence
in manifest; their exact ordered projections and genuine type are bound to
release identity. Backup includes their source dependencies, not only refs.
Counterpart canonical JSON/SQLite semantic ordering/SHA sums unchanged in
method, independently implemented in verifier. Identity includes actual output
SQLite hash/size/semantic hash, exact baseline/candidate projections, ledger,
authority refs, image artifacts, contract/counts/rollback action. No timestamps,
absolute roots or predicted release digest.
Two independent builds must match every relative file byte/hash/size, including
all images and SQLite. No semantic-only fallback.

Verifier retains21 ordered checks (v123_preservation replaces v122_preservation)
and adds image_projection as22nd. It does not import builder helpers/DDL/oracle.
Both builder and verifier require exact pinned input identities and24 candidate
checks. Parsed-invalid manifest returns structured FAIL; malformed JSON retains
InputFormatError. Exact carrier/config and missing root exceptions retained.
All SQLite reads use escaped URI, mode=ro&immutable=1.

## 5. Publication and path/rollback boundary

Readiness writes only new descendants of data/staging/v124-promotion-readiness/.
API build output is strict staging descendant, no symlink/alias/existing output
or ancestor/descendant overlap with any input, canonical, prior candidate,
source/approval evidence, formal releases or user's files. Protect all existing
vector-ch12-* and vector-ch12-mapping trees, plus counterpart historic roots.
No repository releases/V1.24 may exist during readiness, even temporarily.
Later publisher requires exact statement:
USER APPROVED RELEASE PROMOTION V1.24 <actual_release_digest>
This document is not approval. Publication derives config.new_formal_target,
copies verified private snapshot, atomic no-replace, verifies again and fails
closed on digest/race. Cleanup only owned and unchanged outputs; foreign changes
retain evidence. Rollback describes remove_release_tree_if_release_digest_matches,
protecting V1.23; no live rollback or persistent query-default change.
Isolated tests cover pre-approval absence and post-approval exact identity,
wrong digest, changed snapshot, no-replace, failure cleanup and foreign races.

## 6. Closed scope, tests and gates

New production only: src/joy_m2/ingest/v124_promotion_models.py,
v124_promotion.py, v124_promotion_verification.py.
New tests only: tests/unit/test_v124_promotion_models.py,
tests/unit/test_v124_promotion_primitives.py,
tests/integration/test_v124_promotion.py,
tests/fixtures/v124_promotion.py (test-owned independent literal fixture).
Existing tests unchanged unless real lifecycle assertion conflicts; any change
must preserve all historic behavior and be documented/reviewed explicitly.
Docs: this spec, matching plan, docs/reports/V124_PROMOTION_READINESS.md,
PROJECT_STATE.md. Runtime only new readiness staging and existing dist/backups.
No dependency, scheduler, adapter, old engine/schema/API or AGENTS changes.

Tests: valid behavioral RED -> models/scaffold -> primitives -> independent
fixture verifier -> builder -> publication/lifecycle; tampered manual/delegated
evidence, expiry vs historic validity, exact baseline schema and ledger,
rebound-content attacks,72-image closure/role/path/bytes, malformed manifest,
path safety/no-replace/cleanup, deterministic complete trees. Do not use
missing import/setup as RED or builder output as independent verifier oracle.
Final fresh maintained suite, focused suite, old formal verifiers/V118 validator,
frozen identity fingerprints, actual114 query/content/image spotchecks,
independent implementation review C0/I0, local explicit-file backup and isolated
restore. Existing tooling only. No remote-sync precondition is added; ordinary
push allowed, success only after actual remote equality check.
81 held and8 prerequisite units excluded, unchanged.
Stop at FINAL V1.24 PROMOTION AUTHORIZATION with actual verified release digest.
