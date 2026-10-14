# Auto-ingestion phase 1

Authority: the user explicitly approved the lightweight orchestration design
and requested immediate implementation on 2026-10-14, retaining exact batch
transcription/import approvals. This is not approval of any real data payload.
Phase 1 is not the long-term approval policy.

## Scope

Add a local, stdlib-only operational runner, not a replacement workflow engine.
Use a separate SQLite journal under ignored `data/staging/auto-ingestion/`.
Formal V1.18–V1.22, old generations, sources, receipts and user AGENTS remain
immutable. No promotion API, remote service, model client or new taxonomy.

The runner inventories configured local JSON roots and explicit source bundles;
stable batch/source identity plus content revision distinguishes copies from
changes. Counts are record entries, not new original questions. Unknown schemas
and missing sources are reported, never interpreted as approved input.

An explicit job binds a source ID and either an existing V1.23 canonical package
or the existing HKDSE staging/PDF/extraction-pass contract. The runner calls the
existing proposal, exact approval, canonical bridge, preflight, writer and
independent verifier. Complete questions remain indivisible. No arbitrary shell
hooks or dynamically imported processors. Unsupported material is isolated in
review without suppressing another independent job.

Oxford 2025/26 C Set 1 is the real intake trial. Its 13-record draft and matching
PDFs are not HKDSE public-exam input. Existing adapter requires public-exam IDs;
report that exact access limitation rather than changing IDs or pretending the
draft's solution outlines are complete official MS. A successful intake/replay
trial is not a successful real import. No schedule until the authorized E2E
acceptance actually succeeds.

## Durable execution

One repository-scoped nonblocking OS file lock spans journal updates and all
writer operations. SQLite transactions persist each completed job and approval
evidence. Process death releases the lock. An unchanged inventory/approval/
parent snapshot returns immediately without parser or model calls. Failed jobs
retry at most three attempts per revision; changed input creates a new revision.
Do not automatically re-run an accepted source with changed contents.

Approval text is supplied in separate files, never generated as received
approval. Before write, re-run authoritative preflight against the independently
verified current prefix and require exact approval binding. Existing output is
verified and recovered, never overwritten. A mismatched/unreceipted foreign
output is blocked. Receipts retain ordered packages/approvals and candidate
identity so recovery does not depend on trusting journal status.

Before first use, explicitly configure the already accepted ordered receipt
prefix (2023 then 2025). Reconstruct and verify it; journal imports are not a
substitute for candidate verification. New receipts extend, never reorder it.
Publication is absent: formal V1.23 needs its separate existing authority gate.

## Deliverable and limits

Scope: `src/joy_m2/ingest/automation.py`, `automation_v123.py`, a thin
`scripts/run_auto_ingestion.py`, dedicated unit/integration tests, this Design,
its Plan, one operations guide and PROJECT_STATE. No old public export change.
Runtime config/reports/DB go only to ignored staging/audit roots.
Tests cover unchanged reruns, content changes, independent failure isolation,
bounded retries, lock contention, exact approval continuation, stale parents,
candidate recovery and source/frozen preservation. Use real existing APIs with
synthetic test data; never forge a real trial's approval.

Phase 2 recommendations are advisory only: measure independent extraction
agreement, formula/subpart/mark/image/source closure, controlled taxonomy and
false-negative audit rates before considering removal of transcription gates.

