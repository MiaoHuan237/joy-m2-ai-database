# Oxford publisher-mock implementation plan

Execution: Native / Inline, explicitly authorized by the user. Design:
`../specs/2026-10-14-publisher-mock-source-design.md`.

1. Preserve incoming Git/AGENTS and frozen identities. Read actual Oxford draft
   and all relevant PP/MS pages. Record concrete differences and evidence,
   not generic completeness claims. No real approval fabrication.
2. Write behavioral RED tests for a strict publisher proposal loader/digest and
   approval gate. Implement only those behaviors; proposals with unresolved
   content, outlines or necessary unsupported figures remain review-required.
3. RED then GREEN the V1.23 canonical bridge and runner continuation. Use
   synthetic reviewed content in isolated roots for preflight/write/recovery.
   Reuse historical APIs without changing exported surfaces.
4. RED then GREEN exclusive hashed checkpoint backup and safe new-root restore.
   Make an actual ignored-data backup and verify restored byte identities.
5. Prepare the real Oxford evidence/proposal, run the configured job twice and
   verify no duplicate output/model invocation. Without exact transcription
   approval, stop before canonical/preflight; list the actual remaining gate.
6. Fresh focused and maintained regressions; independent whole-change review
   (Critical/Important zero), repair within scope, frozen identity comparison.
   Update operations/state docs, explicit scoped commit and ordinary push.
   Never include the user's AGENTS change or runtime evidence in the commit.

Real acceptance continues on a later exact approval: regenerate nothing unless
bound inputs changed; canonical then parent-bound preflight then import gate;
writer then independent verifier then identical rerun/recovery check. Only then
propose a periodic execution schedule. This ordering is not permission to
consume a requested approval statement as an actual received approval.
