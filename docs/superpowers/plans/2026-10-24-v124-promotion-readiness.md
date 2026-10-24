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
- [x] Add callable discovery assertions and approval wrong-version/digest/carrier
  tests; import via guarded discovery so missing capability fails an assertion.
- [x] Run unit module; observe valid RED, implement exact models/stubs, GREEN.
- [x] Check no package-root exports/history changes; commit task files.

### Task 2: Primitives and independent formal verifier

Files: v124_promotion_verification.py, tests/fixtures/v124_promotion.py,
test_v124_promotion_primitives.py, integration verifier tests.
Consumes Task1 carriers; produces verify_v124_promotion -> VerificationReport.
- [x] Construct test-owned literal SQL/JSON fixture from pinned candidate copy,
  independent of production builder/verifier helpers; expectedcounts8/114/791,
  baseline schema task13-v123-formal-v1 and72 images.
- [x] Assert canonical JSON/SQL semantic normalization, path validation, valid
  fixture22PASS and parsed-invalid FAIL; run before implementation (behavior RED).
- [x] Implement independent literal projections/digests and22checks. Read actual
  historic candidate via existing verifier; no decision creation.
- [x] Add tampered content/role/path/image/ledger/approval/schema and rehashed
  manifest tests; preserve malformed JSON exception. GREEN targeted modules.

### Task 3: Deterministic builder and safety

Files: v124_promotion.py, integration builder tests.
Consumes typed request and verifier; produces V124PromotionArtifacts.
- [x] Assert two actual builds preserve677 and project114, include72images,
 76files byte-identical; stub yields behavior RED, not fixture failure.
- [x] Implement pinned input validation, private copy, exact transaction/image
  projection/artifacts and atomic no-replace with existing safety primitive.
- [x] Assert protected path/symlink/alias/existing output/foreign race rejection,
  failed verification cleanup and preserved source bytes; fix scope-limited
  defects RED/GREEN. Commit verified production/tests.

### Task 4: Publication/lifecycle and independent implementation review

Files: same three modules/tests, no real release.
Consumes successful Task3 output, exact V124ReleasePromotionApproval.
- [x] In isolated repo roots test wrong/absent approval means target absent;
  exact synthetic approval yields identical76files, wrong identity/no-replace
  fail, private mutation/verification failure cleanup, foreign mutation retained.
- [x] Implement publish_v124_release only after behavioral RED; run GREEN.
- [x] Fresh independent reviewer reads whole diff/spec/tests, C0/I0 required;
  remediate with regression RED/GREEN and required re-review.

### Task 5: Real readiness acceptance and handoff

Runtime: data/staging/v124-promotion-readiness/ new numbered output.
Docs: readiness report,PROJECT_STATE. No code except reviewed defects.
- [x] Load stored8batches, verify24/24; fingerprint all protected inputs/formals.
- [x] Build two new roots,verify22/22 each, compare all76bytes,791unique published
  formal-equivalent IDs; each batch count and all114source fields unchanged.
- [x] Query actualtag/content samples; decode all72images and preserve ordered
  role/reference mappings; preserve final-only/partial/missing statuses.
- [x] Fresh serial maintained suite (all discovered maintained modules),
  historical formal verifiers/V118validator and identity replay; no skipped gate.
- [x] Existing explicit backup/restore, verify restored outputs/content/images;
  do not snapshot live SQLite sidecars. Preserve source/evidence backup closure.
- [x] Write exact release/hash/file-list/report, commit only scoped files,
  ordinary push and remote check (network failure is recorded, not a data gate).
- [x] Stop FINAL V1.24 PROMOTION AUTHORIZATION with actualdigest and statement;
  releases/V1.24 still absent; no claim of actual114formal additions yet.

## Execution evidence — 2026-10-24

Native/Inline completed within scope; independent Design/Plan and implementation
review C0/I0 (implementation alsoM0). Fresh focused30/30. Two real roots76files
byte-identical; candidate24/24, eachformal22/22; 1110-file local restore and72images
PASS. Actual identity and full file list are in V124_PROMOTION_READINESS.md.

Maintained means the established current set:77modules1596tests allPASS.
The fresh combined78module1607test execution also ran the separately attributed
legacy module11tests9PASS/2knownFAIL. This is not1607PASS. Existing exclusion is
explicit in prior V123 readiness and vector Plan; no new test excluded/changed.
Separate reviewer checked every completion and original-HEAD attribution rules.
Executablelegacy54/54 andV118validatorPASS. No V124 assertion/hash weakened.

Ordinary push attempted; HTTP2 transport failure is not a local readiness gate.
Final docs commit/remote readback and evidence checkpoint outcome are recorded in
the ignored readiness root. Local worktree/branch remain; no merge/history rewrite.
Final exact release approval is still absent. No real publication was performed.
