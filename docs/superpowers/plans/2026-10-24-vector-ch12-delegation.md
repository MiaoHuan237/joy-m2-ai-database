# Vector chapter12 limited delegation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Native / Inline execution is explicitly authorized; separate technical review remains mandatory.

**Goal:** Safely continue the fixed117-unit chapter scope into V1.24 candidates without fabricating exact human batch approvals.

**Architecture:** Pinned external chapter grant, explicit delegated decisions/carriers, and a closed branch in existing candidate engines. Manual APIs and all historical prefix identities remain unchanged.

**Tech Stack:** Existing Python standard library, SQLite, unittest; no dependencies.

**Spec:** `docs/superpowers/specs/2026-10-24-vector-ch12-delegation-design.md`

## Global Constraints

- Formal V1.23/677 and V1.18–V1.23 files immutable; no promotion.
- Fixed S04-14 +103 later IDs;44 held,8 prerequisite,34 accepted excluded.
- No fake USER APPROVED statements or synthetic approvals on real inputs.
- Preserve user's AGENTS.md and all old evidence/candidates. No scheduler edits.
- User authorized engineering execution without another routine Plan gate.

## Review Focus

- Candidate-carried grant must not establish its own trust: Task1 negative test.
- Revocation after staging before rename must fail without replacing parent: Task3.
- Manual prefixes inside mixed ledgers retain their exact prior digest: Task3.
- A valid ID with unrelated source spans must fail source correspondence: Task2.
- Historical accepted evidence after grant expiry remains verifiable, but cannot authorize a new write: Tasks1/3.

### Task 1: Pinned authority and decision evidence

**Files:** new `src/joy_m2/ingest/vector_ch12_delegation.py`, `tests/unit/test_vector_ch12_delegation.py`.
**Interfaces:** `load_chapter_grant(repo: Path, *, live: bool) -> ChapterGrant`; immutable grant carries ordered IDs and pinned package/member/baseline identities. `validate_selection(grant, mapping, accepted_ids) -> tuple[str,...]` rejects IDs/order/content outside scope. Private test fixtures may inject independent pins only below the public trust boundary.

- [ ] Add importable fail-closed scaffold; write tests for pinned bytes, substituted/self-asserted grant, revoked/missing grant, changed baseline/input, held/prerequisite/accepted IDs and empty/exhausted selection. Expected behavioral RED, never missing import/setup.
- [ ] Implement strict read-only validation, canonical decision serialization and explicit actor labels; run `python -B -m unittest tests.unit.test_vector_ch12_delegation -v`. Expected GREEN.
- [ ] Commit only scoped authority code/tests and ledger the result.

### Task 2: Source decisions and canonical correspondence

**Files:** same authority module/tests, `vector_ch12.py`, new `vector_ch12_delegated_models.py`.
**Interfaces:** explicit chapter source decision and adaptation entry, reusing shape/package/span/image/render validators and canonical files; import decision binds source decision, actual canonical manifest/file closure, preflight and parent. Manual SourceMappingApproval path unchanged.

- [ ] Tests: fake reviewer/no review, wrong mapping or selected IDs, valid ID with wrong source section/spans, changed ZIP, altered canonical bytes and forged exact-human string reject. New delegated entry produces the same canonical bytes as a genuinely approved identical mapping in synthetic fixtures; no fake manual carrier is constructed by implementation.
- [ ] Implement minimal shared private adaptation body and separate public delegated entry; exact old public signature and output remain.
- [ ] Run focused authority plus vector chapter mapping/integration tests; expected GREEN, commit scoped files.

### Task 3: Mixed candidate engine and independent verifier

**Files:** delegated models and authority module, `v124_writer.py`, `v124_verification.py`, `v124_preflight.py`, `v124_writer_profiles.py`, new `tests/integration/test_vector_ch12_delegated_candidate.py`.
**Interfaces:** explicit delegated build/verify/preflight request carriers; mixed ledger with old manual entries; new chapter schema branch, no alteration of old manual models/signatures. Closed private profile parameters, not runtime monkeypatching.

- [ ] Build independent synthetic fixture over the existing approved baseline test setup. Valid RED for first delegated generation ONLY after source decision/canonical dependencies GREEN.
- [ ] Implement delegated identity/schema/authority storage, source verification and atomic writer branch. Test manual-prefix digest preservation, READY/exact-parent, duplicate IDs, forged nested carrier, direct writer bypass, no-replace and failure cleanup.
- [ ] After first generation GREEN, test and implement verified delegated-parent preflight and second append; test stale parent and changed live grant immediately before publication.
- [ ] Historical verifier can inspect accepted decisions after revocation, but new source/import/writer operations reject them. Test both stages, never an eternal nonexistence assertion.
- [ ] Run new integration and all existing V1.24/vector tests; expected GREEN. Commit scoped code/tests.

### Task 4: Independent review and real S04 checkpoint

**Files:** scoped report and PROJECT_STATE; ignored runtime records only.
**Interfaces:** verified live grant + current gen3 + existing S04 canonical/READY preflight -> explicit delegated decision -> next candidate/receipt/local backup.

- [ ] Run maintained gates once at this integrated checkpoint; record actual counts. Separate reviewer checks full diff, bypasses, authority/prefix semantics and mutations. Fix Critical/Important with behavioral RED→GREEN and re-review as repository policy requires.
- [ ] Under cycle.lock, revalidate source, live grant, exact S04 payload, current parent and independent content review. Reuse canonical/preflight only if identical/current. No real write before this gate passes.
- [ ] Append using the new writer; independent verifier; save receipt; local archive and isolated byte comparison using existing backup utilities. Existing successful receipt -> verify/reuse, no rebuild.
- [ ] Update progress with actual candidate count, not published count; preserve203 unique destinations. Commit docs only, no ignored source/database artifacts or AGENTS.md.

### Task 5: Continue authorized natural groups

**Files:** new ignored proposals/reviews/decisions/canonical/receipts; progress checkpoints.
**Interfaces:** same validated source and delegated candidate entry, natural groups of the remaining103 fixed IDs.

- [ ] Reuse existing indexed fragments; review only missing boundaries/source/answer/image evidence. Hold material uncertainty before selecting; preserve reasons and all original bytes.
- [ ] Separate content review, actual proposal/digest, canonical, latest-parent READY preflight, delegated decision, atomic append, verify, backup, progress. Repeat until scope exhausted or a real runtime/authority/content blocker requires stopping. No ordinary per-batch human gate.
- [ ] Final fresh immutable-file/checkpoint verification and concise counts. No automatic publication.
