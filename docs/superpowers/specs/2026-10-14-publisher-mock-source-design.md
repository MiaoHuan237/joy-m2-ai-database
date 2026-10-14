# Oxford publisher-mock evidence mapping

The user explicitly authorizes inline implementation of this bounded source
extension. This is not transcription approval or import approval. The existing
auto-ingestion phase-1 journal, lock, receipt recovery, V1.23 preflight, atomic
writer and independent verifier remain authoritative.

## Source and evidence

Use source_type `publisher_mock`, publisher `Oxford`, session `2025/26`, paper
`C Set 1`, module `M2`, language `zh-Hant`. Preserve the original staging batch
ID and each `MOCK-C1-2025-26-Qnn` ID; source ID is
`OXFORD-M2-2025-26-C-SET1`. Do not change HKDSE loaders or public exports.

A reviewed JSON proposal binds source PDF hashes, original staging hash,
ordered original question IDs/numbers, PP/MS physical page numbers, marks,
question text, publisher solution text, solution evidence level, controlled
taxonomy, unchanged difficulty, source limitations and per-record review
evidence. Its digest is canonical JSON SHA-256, without local paths or time.
The runtime resolves actual PDF paths separately and verifies hashes. Hashes
establish identity, not mathematical completeness: the review evidence must
describe question/subpart/formula/mark/figure and MS comparison explicitly.

Evidence levels are `full_publisher_ms`, `outline`, `missing`. A proposal with
an outline, missing evidence, unresolved issue or unreviewed content is not
approval-eligible and cannot become canonical even with matching approval text.
Do not silently promote the existing thirteen solution outlines to full MS.
Necessary figures not represented by the approved input block this first
text-only Oxford bridge; no false empty image projection. Source mistakes are
preserved and disclosed, not silently corrected. No batch splitting to evade
an unresolved issue.

Exact approval remains `USER APPROVED PDF TRANSCRIPTION BATCH <batch> <digest>`.
Any content/evidence/taxonomy change invalidates it. Only after this approval
does the bridge emit the existing V1.23 manifest and 23-field candidates.
Publisher answers use `source_provided`, never the claim HKDSE official MS.
Source-map carries publisher/session/paper, original IDs, page anchors and
source hashes. Independent explanation remains missing unless actually sourced.
No public schema/dedup/promotion changes. Real import retains the exact current
verified parent and separate exact approval.

## Execution and recovery

Add one internal publisher module and a `publisher_mock` job branch in the
existing runner. On every changed-input run validate the proposal, actual
sources and controlled taxonomy; compare cached canonical bytes against a
fresh reconstruction. Reuse existing serialized writer intent/recovery and
accepted receipt logic. No model calls on unchanged runs.

Provide a small checkpoint archive utility with explicit input files, a hashed
manifest and immutable exclusive output. Acquire the runner lock; do not back
up live SQLite transactions. Restore only into a new empty recovery directory,
never into original/formal locations. Verify all archived bytes before restore
and test corruption rejection. Local archives are not off-device backups.

## Closed scope and acceptance

New internal modules `publisher_mock.py`, `ingestion_backup.py`, their dedicated
tests and a thin backup script; minimal edits to `automation.py`,
`automation_v123.py`, operations guide and PROJECT_STATE; this Design/Plan.
Runtime review/proposals/archives remain ignored. Preserve dirty AGENTS and
all formal/candidate/source/approval files. No scheduling before real acceptance.

RED-first tests cover evidence identity, source profile/order, outline/missing
and figure rejection, digest/approval tampering, taxonomy, deterministic
canonical output, real existing preflight with synthetic data, exact approval
continuation, receipt recovery/idempotence, backup restore and corruption.
Run current maintained gates, independent implementation review, actual Oxford
source review and independent existing candidate replay. Stop at the first
unsatisfied real human gate; never describe a synthetic write as the real pilot.
