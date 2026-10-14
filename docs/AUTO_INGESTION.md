# Auto-ingestion phase 1 — operational checkpoint

This is an approval-preserving local orchestration layer, **not a completed
universal ingestion system**. Existing source adapters, exact approvals,
parent-bound V1.23 preflight, atomic writer and independent verifier remain
authoritative. There is no formal publication operation.

## Run

From the active `task8b-pipeline-migration` worktree, with the existing project
Python environment (including the project's existing PDF dependency):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python3 -B scripts/run_auto_ingestion.py \
  --config data/staging/auto-ingestion-config-20261014.json
```

The real-machine config is ignored runtime data; it is not shipped in Git.
Its `inventory_roots` are explicit authorized directories. `receipts` contains
the original accepted 2023 and 2025 receipts, in that order. `jobs` contains
distinct stable source IDs, a supported kind and exact input paths. Example
shape (substitute real paths; these are not approval credentials):

```json
{
  "inventory_roots": ["/absolute/authorized/incoming"],
  "receipts": ["/absolute/2023/REAL_BATCH_IMPORT_RECEIPT.json", "/absolute/2025/REAL_BATCH_IMPORT_RECEIPT.json"],
  "jobs": [{
    "source_id": "actual-batch-id",
    "kind": "hkdse_pdf",
    "inputs": {
      "staging": "/absolute/staging.json",
      "pp": "/absolute/pp.pdf",
      "ms": "/absolute/ms.pdf",
      "pass_a": "/absolute/verified-pass-a.json",
      "pass_b": "/absolute/verified-pass-b.json"
    },
    "transcription_approval": "/absolute/received-transcription-approval.txt",
    "import_approval": "/absolute/received-import-approval.txt"
  }]
}
```

Supported jobs:

- `hkdse_pdf`: consolidate existing extraction/evidence passes through Task10B,
  check controlled taxonomy, wait for exact transcription approval, then
  canonicalize/preflight; wait for exact import approval before candidate write.
- `v123_canonical`: input `package`, an existing authoritative canonical root;
  preflight and exact import gate remain mandatory.
- `structured_draft`: count and identify existing structured input and source
  PDFs; unsupported profiles stay in review. This is not approved transcription.

An approval file contains only the exact **actually received** user statement.
Never copy a requested statement into that file without user approval. Running
the same command after receipt resumes the affected batch, not the whole source
extraction. Ordinary controlled values need no per-question approval.

The current runner does **not** autonomously OCR arbitrary PDFs, infer missing
mathematics, split unknown textbooks, invent taxonomy or turn an unrecognized
draft into approved input. New files are inventoried automatically, but unknown
profiles are not silently scheduled as writer jobs. Existing MMD/PDF adapters
can supply their established canonical/evidence outputs; this module does not
create a generic parser or modify their contracts.

## Persistence, recovery and safety

Runtime root: `data/staging/auto-ingestion/` (ignored).

- `state.sqlite3`: source/job identity, content revision, attempts, result,
  exact consumed approval/receipt evidence and latest inventory snapshot.
- `last_run.json`: current file inventory and batch review/approval outcomes.
- `cycle.lock`: repository-scoped nonblocking lock across the complete cycle.
- `pending-write.json`: fsynced intent before writer publication; after a crash,
  reconstruct exact preflight/approval/prefix and verify existing output before
  completing the receipt. Never rebuild an existing successful output.
- `receipts/`, `candidates/`, `proposals/`, `packages/`: runner-owned results.

Receipt/verification failure after writer intent stops later writes, preventing
forked candidate generations. Independent source errors remain isolated. Input,
approval, package and parent changes invalidate waiting results. Changed
accepted sources require review, not automatic re-import. A cached proposal is
reconsolidated from actual passes when processed; cached canonical files must
exactly match the existing bridge's output for the approved proposal.

Ordinary failed revisions retry three times, then wait for changed input or an
operator investigation. A pending writer intent is a recovery obligation and
is never ignored merely because the ordinary retry limit was reached. Do not
manually delete intent, candidate, receipt or journal to force another append.
The lock coordinates this runner's processes, not unrelated legacy scripts:
never run an external candidate writer concurrently. New operational receipts
outside the configured prefix block writes until reconciliation.

No-change runs still check file identities, but skip adapters and model calls.
There is no model client. Runtime failure returns exit 2; BUSY or human-gated
results are structured in JSON. `new_questions=null` means not established by
authoritative preflight, not zero. Inventory entries are not unique original
questions. A filename or draft's declared success does not establish approval.

## Real Oxford trial — 2026-10-14

- Batch: `JOY-M2-STG-MOCK-2025-26-C-SET1-20260903`.
- Draft: `joy_m2_mock_2025_26_c_set1_staging.json`, SHA
  `c7c3cdaee820398d64398e815d7305854a5c08b7955142549b435a57e931419e`.
- 13 entries, 13 question text fields and 13 solution-outline fields; declared
  100 marks. This field-presence check is not a full mathematical/MS review.
- Exact PP SHA:
  `1ad699a747fdd00d77de2afe51273403f632f0e0c8e2960c257f0cd57d5203d5`.
- Exact MS SHA:
  `d47915b639e6e5adb5e17ad46e8dfa6b02e14c84889417ecb7eda9576cb90580`.
- Both actual PDFs match the draft's source declarations; no re-upload needed.
- Two real intake runs: first processed 1 job; second processed 0,
  `no_change=true`, model calls 0, approximately 0.06 seconds on this machine.
  The scoped directory contained 89 files / 87 distinct content hashes.

**Remaining specific access gap:** Task10B's strict HKDSE loader requires
`question_kind=public_exam_question` and `HKDSE-YYYY-M2-Qxx` identity. The Oxford
draft has `MOCK-C1-2025-26-Qxx` and solution outlines, not that approved schema.
Do not rename IDs, claim public-exam provenance or treat outlines as full MS.
The minimal next decision is a narrowly scoped Oxford mock-source mapping and
evidence/approval profile, preserving existing HKDSE/Task9A/V123 contracts.
No broad framework or historical cleanup is needed. This trial is **intake-only**;
real authoritative E2E acceptance and periodic scheduling remain incomplete.

The verified original 2023/2025 prefix remains generation000002, additions25,
total664, digest `9d6b16cf357e7d32268552ab17c74a16a409d502d7873aa6c7a3854f77edebb9`.
It was replayed read-only, not appended again. HKDSE2024's Q11 local defect,
human acceptance evidence and unapproved proposal remain unchanged. It is not a
VERIFIED batch and does not prevent Oxford intake.

## Phase 2 approval simplification — recommendation only

Consider removing manual transcription approval only for a separately approved
source profile whose normal batches have all of these machine gates:

1. Exact PP/MS identity, complete question/page/subpart/mark/image closure,
   two independently validated extraction results and immutable evidence.
2. All formulas/conditions agree; no unresolved local defects, missing MS,
   uncertain source ownership or unsupported layout.
3. Controlled vocabulary validation, deterministic canonical output and
   provenance-preserving source/answer bindings.
4. Independent verifier PASS, replay idempotence, stale-parent rejection,
   crash recovery and unchanged formal baselines.
5. Multiple real batches reviewed with measured discrepancy rates, documented
   sampling/audit criteria and an explicit human decision changing the policy.

Escalate mathematical ambiguity, missing content, integrity risk and unsupported
source profiles. Ordinary known taxonomy values need no separate question-level
approval. Keep exact import approval and formal promotion approval until a
separate measured decision explicitly changes those contracts. No approval gate
is removed here, and no periodic automation has been configured.

## Verification checkpoint

- Maintained suite:1265/1265 PASS,0ERROR/skip/expectedFailure. It collected before
  the final post-verification cache-corruption regression was added.
- Final focused runner suite:30/30 PASS, including that new negative control.
  This is separately reported, not an invented1266-test single full run.
- Independent final review:Critical0/Important0/Minor0; reviewer independently
  ran30 tests and pending-approval/parent corruption checks (writer calls0).
- Legacy attribution:9PASS/2knownFAIL, unchanged historical SQLite deterministic
  hash and frozen-byte-equivalence categories; not suppressed or relabeled PASS.
- V1.18 validator PASS; actual accepted candidate verifier24/24 PASS and563
  protected identities unchanged. Formal SQLite and dirty userAGENTS unchanged.

Full runner command for maintained tests (the legacy attribution module is a
separate documented gate, not skipped tests):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python3 -B - <<'PY'
from pathlib import Path
import unittest
names = ['.'.join(p.with_suffix('').parts)
         for folder in ('unit', 'integration', 'regression')
         for p in sorted((Path('tests') / folder).glob('test_*.py'))
         if p.name != 'test_task8b_legacy_pipeline_behavior.py']
result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromNames(names))
raise SystemExit(not result.wasSuccessful())
PY
```
