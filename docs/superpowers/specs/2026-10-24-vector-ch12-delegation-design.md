# Vector chapter12 limited delegation

Authority: the user's 2026-10-24 chapter-continuation instruction authorizes
this minimal implementation, Native / Inline, with independent technical review.
It does not authorize promotion or pretend that future batches have human exact
approvals. No further routine engineering approval is requested.

## Fixed scope and trust

The external user authorization and scope evidence are retained in
`data/staging/vector-ch12-delegation-20261024-000001/`.
`USER_AUTHORIZATION.txt` SHA256 is
`1a86614c58e0fdcb0b5e8586a2a23264da30d4a992ba035a458af3d956c8993a`.
`SCOPE_RECORD.json` SHA256 is
`3468bcaa245a90df3174a76ea9cb300cac5407c9821b322a5b29598969c280e2`.
These independently pinned bytes, not an arbitrary grant supplied by a caller
or found inside a candidate, establish the authorized set. The record is an
immutable audit input; its original NOT_IMPLEMENTED status is historical, not
an approval carrier and must not be rewritten.

117 IDs are authorized: revised S04's14 and103 later units. The44 held,
8 prerequisite and34 previously accepted IDs are disjoint and excluded.
The two ZIP identities and their selected MMD identities are fixed by that
record. An ID is not sufficient by itself: its original section, number and
precise source spans must correspond to the retained unit inventory.
No regeneration of the203-unit inventory is authorized.

The sole target is V1.24 over frozen formal V1.23/677. Changes to the input
bytes, formal baseline, or revocation invalidate new delegated operations.
A `REVOKED` marker in the external authorization directory is fail-closed
regardless of its contents; absence is meaningful only after the pinned grant
and its required files validate. The runner must also honor a newly received
human revocation immediately, even before persisting that marker. Missing,
symlinked or malformed authority is not active. No permissions service is added.
Historical verification of already accepted records remains possible after
revocation; eligibility for NEW writes additionally requires live authority.
Scope exhaustion forbids another new delegated decision, not historical replay.

## Evidence and decisions

Source decisions are explicitly named delegated decisions, never manufactured
USER APPROVED strings. Each binds grant SHA, batch, ordered selected IDs,
mapping SHA, fixed packages and a separate content review artifact identifying
the independent reviewer, zero Critical/Important, and reviewed mapping SHA.
The review states source limitations and answer coverage; program validation
does not claim to prove mathematical correctness. A review artifact is evidence
of an actually performed separate review, not a replacement for one.

Import decisions additionally bind the actual canonical file closure, READY
preflight SHA, verified current parent and target V1.24. The writer and independent
verifier each revalidate the grant, decision, source-to-canonical correspondence,
and ordinary preflight/collision closure. Historical manual batches keep their
original exact statements and schemas. The first S04 source decision can use
the received exact human source approval and existing identical canonical.

## Compatible candidate path

Keep all existing public manual carriers/signatures and byte identities intact.
Introduce explicitly named chapter-delegated carriers and entry points; no
arbitrary subclass acceptance, approval-shaped duck typing, monkeypatching,
global context, or fake historical approval objects. Shared private engine
operations may take an explicit, closed chapter/manual profile.

Mixed ledgers preserve every original manual entry. A separate candidate schema
branch records delegated decisions honestly. Candidate digest reconstruction
selects the identity schema for EACH prefix: S01–S03 reconstruct to their old
digests; the first delegated prefix introduces the chapter schema. Parent-bound
preflight must independently verify both profiles. The existing canonical
manifest and question/source/image semantics do not change.

New entry points reuse the existing loader, normalization, duplicate checks,
SQLite projection, no-replace atomic publish and independent integrity checks.
Delegation is checked before work and again immediately before publication.
The operation uses cycle.lock and rechecks the actual latest receipt/parent
under that lock. A successful batch is returned idempotently, never rebuilt.
No publisher or daily scheduler changes are included.

## Quality and content work

Complete questions retain all subparts, conditions and necessary images.
Only explicit source fragments may be combined. Answer coverage stays truthful;
missing level/marks/explanation is allowed only under the existing contract.
Uncertain mathematical/source relationships become held, with provenance and
reason, before source selection. A bound failed batch is retained unchanged;
any new selection is a new proposal and decision. Accepted subsets cannot be
silently edited. A blocked preflight never becomes a write decision.

After code verification and independent review, reuse S04's actual canonical
and preflight if their identity/current parent still match, append, verify and
backup. Then process the103 IDs in natural groups with new decisions, preserving
all203 unit destinations. No artificial batch-size cap; no automatic held-unit
inclusion. Local backup/restoration is not off-device backup.

## Closed implementation scope

New chapter-only files under `src/joy_m2/ingest/`: `vector_ch12_delegation.py`,
`vector_ch12_delegated_models.py`. Add explicit shared-engine branches only in
`vector_ch12.py`, `v124_writer.py`, `v124_verification.py`, `v124_preflight.py`,
`v124_writer_profiles.py`. Preserve `v124_models.py` public manual definitions;
if pure validation extraction is needed it must preserve all old behavior.
Tests: `tests/unit/test_vector_ch12_delegation.py`,
`tests/integration/test_vector_ch12_delegated_candidate.py`, small synthetic
fixtures/helpers only. Docs: this design, corresponding plan, execution report
and PROJECT_STATE. Runtime evidence stays in new ignored staging directories.
No package-root exports, dependency, generic framework, scheduler, formal
release, new source or changed historical source approval interface.

## Tests and release gate

Test-first: trusted scope and revocation, unauthorized/held/prerequisite/already
accepted IDs, swapped/changed ZIP/member, altered mapping/selection/review,
missing review, bad READY/preflight/parent, canonical mismatch, direct writer
bypass, nested carrier forgery, untrusted rehashed candidate grant, mixed prefix
replay, next delegated parent, no-replace/failure cleanup, live authority change
before rename, and historical manual output identity. Synthetic approvals never
authorize real data. Fresh focused and maintained regression plus independent
review with no unresolved Critical/Important precede the first real delegated
append. Source review and engineering review are different evidence.

Promotion remains an explicit human gate. No releases/V1.24 is created.
