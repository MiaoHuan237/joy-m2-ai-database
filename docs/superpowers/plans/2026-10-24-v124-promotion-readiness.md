# V1.24 fixed generation000008 promotion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans.

**Goal:**677+114=791 release-equivalent records and72 original images, awaiting
exact human promotion approval.
**Architecture:** Three version-specific siblings of pinned V123 promotion;
historical ChapterVerificationRequest independently validates mixed authority.
**Tech Stack:** Existing Python stdlib/sqlite3/unittest, no dependencies.
**Spec:** docs/superpowers/specs/2026-10-24-v124-promotion-readiness-design.md.

## Global Constraints

- Native/Inline under current user execution authorization, not claimed user
  word-for-word review; independent local Design/Plan review before code.
- Fixed candidate3f14589da452207d0088cd44689aded7ffbadea0768a85d808a67ae526a5f3ab.
- No real publication, real writer, grant renewal, source/content edits or AGENTS edits.
- Closed paths and exact identities/counts/roles are those in the spec.
- Test-only synthetic approval in isolated roots never authorizes real release.

## Review Focus

- Historical expired grant validation must remain valid without enabling new write.
- Image role/list alignment and output-relative resolution, not only file existence.
- Parsed-invalid nested manifest must return FAIL rather than Python type crash.
- Output descendants of nonselected historical evidence must remain protected.
- Cleanup ownership/races must retain another writer's output.

### Task 1: Carriers and callable scaffold

Files: new v124_promotion_models.py, two callable module scaffolds;
test_v124_promotion_models.py.
Produces exact counterpart typed contracts with ChapterVerificationRequest.
- [ ] Add callable discovery assertions and approval wrong-version/digest/carrier
  tests; import via guarded discovery so missing capability fails an assertion.
- [ ] Run unit module; observe valid RED, implement exact models/stubs, GREEN.
- [ ] Check no package-root exports/history changes; commit task files.

### Task 2: Primitives and independent formal verifier

Files: v124_promotion_verification.py, tests/fixtures/v124_promotion.py,
test_v124_promotion_primitives.py, integration verifier tests.
Consumes Task1 carriers; produces verify_v124_promotion -> VerificationReport.
- [ ] Construct test-owned literal SQL/JSON fixture from pinned candidate copy,
  independent of production builder/verifier helpers; expectedcounts8/114/791,
  baseline schema task13-v123-formal-v1 and72 images.
- [ ] Assert canonical JSON/SQL semantic normalization, path validation, valid
  fixture22PASS and parsed-invalid FAIL; run before implementation (behavior RED).
- [ ] Implement independent literal projections/digests and22checks. Read actual
  historic candidate via existing verifier; no decision creation.
- [ ] Add tampered content/role/path/image/ledger/approval/schema and rehashed
  manifest tests; preserve malformed JSON exception. GREEN targeted modules.

### Task 3: Deterministic builder and safety

Files: v124_promotion.py, integration builder tests.
Consumes typed request and verifier; produces V124PromotionArtifacts.
- [ ] Assert two actual builds preserve677 and project114, include72images,
 76files byte-identical; stub yields behavior RED, not fixture failure.
- [ ] Implement pinned input validation, private copy, exact transaction/image
  projection/artifacts and atomic no-replace with existing safety primitive.
- [ ] Assert protected path/symlink/alias/existing output/foreign race rejection,
  failed verification cleanup and preserved source bytes; fix scope-limited
  defects RED/GREEN. Commit verified production/tests.

### Task 4: Publication/lifecycle and independent implementation review

Files: same three modules/tests, no real release.
Consumes successful Task3 output, exact V124ReleasePromotionApproval.
- [ ] In isolated repo roots test wrong/absent approval means target absent;
  exact synthetic approval yields identical76files, wrong identity/no-replace
  fail, private mutation/verification failure cleanup, foreign mutation retained.
- [ ] Implement publish_v124_release only after behavioral RED; run GREEN.
- [ ] Fresh independent reviewer reads whole diff/spec/tests, C0/I0 required;
  remediate with regression RED/GREEN and required re-review.

### Task 5: Real readiness acceptance and handoff

Runtime: data/staging/v124-promotion-readiness/ new numbered output.
Docs: readiness report,PROJECT_STATE. No code except reviewed defects.
- [ ] Load stored8batches, verify24/24; fingerprint all protected inputs/formals.
- [ ] Build two new roots,verify22/22 each, compare all76bytes,791unique published
  formal-equivalent IDs; each batch count and all114source fields unchanged.
- [ ] Query actualtag/content samples; decode all72images and preserve ordered
  role/reference mappings; preserve final-only/partial/missing statuses.
- [ ] Fresh serial maintained suite (all discovered maintained modules),
  historical formal verifiers/V118validator and identity replay; no skipped gate.
- [ ] Existing explicit backup/restore, verify restored outputs/content/images;
  do not snapshot live SQLite sidecars. Preserve source/evidence backup closure.
- [ ] Write exact release/hash/file-list/report, commit only scoped files,
  ordinary push and remote check (network failure is recorded, not a data gate).
- [ ] Stop FINAL V1.24 PROMOTION AUTHORIZATION with actualdigest and statement;
  releases/V1.24 still absent; no claim of actual114formal additions yet.
