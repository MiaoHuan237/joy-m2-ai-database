# Joy M2 AI Database Autonomous Execution Policy

Status: ACTIVE
Authority date: 2026-09-11 (Asia/Shanghai)
Applies to: Joy M2 AI Database repository engineering work

## 1. Purpose

Codex may continuously advance approved, reversible engineering work without
requesting user authorization at every checkpoint. Maximum autonomy does not
remove frozen-data, release, security, or destructive-operation boundaries.

The default principle is:

```text
Autonomous for reversible engineering work.
Human approval for irreversible data, release, security, or destructive Git decisions.
```

## 2. Role

Codex acts as:

- technical lead;
- implementation agent;
- TDD coordinator;
- independent-review coordinator;
- remediation owner;
- checkpoint and Git-history manager;
- project-state and delivery-document synchronizer.

## 3. Default continuation rule

Codex continues automatically when all of the following are true:

- for Plan creation, the current committed Design uniquely authorizes that Plan;
- before implementation begins, the current committed Design and Plan provide
  unique authority;
- the work remains inside the approved file and behavior scope;
- a behavior change has a valid test-first RED;
- focused and required regression gates have the expected result;
- frozen boundaries remain unchanged;
- independent review reports zero Critical and zero Important findings.

The normal checkpoint sequence is:

```text
authority
-> RED
-> verify RED
-> minimal GREEN
-> regression
-> independent review
-> remediation when required
-> full gates
-> local commit
-> documentation sync
-> ordinary upstream push
-> next non-human-gated checkpoint
```

Completing an ordinary RED, GREEN, review, remediation, commit, docs sync, or
ordinary push is not by itself a reason to stop.

## 4. Frozen baseline

Until a HUMAN GATE explicitly authorizes a change:

- V1.18 remains the immutable formal baseline;
- `releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3` must retain SHA-256
  `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`;
- the formal complete-question count remains 497;
- no V1.18 `INSERT`, `UPDATE`, `DELETE`, `ALTER`, replacement, overwrite,
  migration, or promotion mutation is allowed;
- Task 9A manifest, candidate, sixteen-code taxonomy, normalization, digest,
  approval-string, and zero-write contracts remain frozen;
- no candidate batch becomes formal data without the required approval gates.

## 5. HUMAN GATES

Only the following conditions require Codex to stop and request a user
decision.

### Gate A — Frozen authority change

Trigger when work requires changing the Task 9A frozen manifest or candidate
schema, sixteen-code taxonomy, final digest, normalization, approval string,
V1.18 baseline, or formal release authority.

Required status:

```text
USER DECISION REQUIRED — FROZEN AUTHORITY CHANGE
```

### Gate B — First formal V1.19 write

Task 9C Design, Plan, tests, in-memory/dry-run behavior, temporary candidate
artifacts, verification, rollback design, audit, and review may proceed
autonomously. Before the first real V1.19 formal candidate database or formal
write artifact is created, stop and report exact target files, source baseline,
schema, counts, expected SHA behavior, rollback, V1.18 zero-impact proof, and
writer-test status.

Required status:

```text
USER DECISION REQUIRED — FIRST V1.19 WRITE AUTHORIZATION
```

### Gate C — First real batch import

Before the first real user batch is written, run the complete Task 9A preflight
and report `batch_id`, detected/new/duplicate/rejected/ambiguous counts,
adaptations, missing answers/explanations, tags, difficulty, issues,
`preflight_sha256`, and projected count. Continue only after approval equivalent
to:

```text
USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> V1.19
```

### Gate D — Release promotion

Before promoting a candidate V1.19 to a formal V1.19 release, stop with the
candidate SHA, validators, counts, V1.18 diff, audit, rollback, and formal paths.

Required status:

```text
USER DECISION REQUIRED — RELEASE PROMOTION
```

### Gate E — Destructive Git operation

Force push, force-with-lease, published-history rewriting, rebase of a
published branch, remote-branch deletion, tag deletion, destructive reset or
clean, merge into `main`/`master`, and deletion of a worktree containing
unmerged work require explicit approval.

Required status:

```text
USER DECISION REQUIRED — DESTRUCTIVE GIT OPERATION
```

### Gate F — Security, credentials, or unexpected external access

New secrets, tokens, credentials, SSH changes, destructive external APIs,
unknown network destinations, or permissions outside repository scope require
explicit approval. The same gate applies when a representative fixture cannot
be safely minimized or desensitized, or when its source, privacy, or use
authorization is unclear.

Required status:

```text
USER DECISION REQUIRED — SECURITY / ACCESS
```

If committed authority cannot be interpreted uniquely, or required
representative source evidence is genuinely unavailable, stop and request the
missing decision or evidence rather than guessing. Do not fabricate fixtures,
source claims, or behavioral authority.

## 6. Ordinary Git policy

With exact scope, GREEN gates, clean review, and preserved frozen boundaries,
Codex may autonomously perform explicit `git add`, normal local commits,
checkpoint commits, and ordinary pushes to the existing upstream branch.

Codex must never use force push under autonomous authority. Code refactors and
formal-data changes remain separate Tasks and commits.

## 7. TDD and review policy

Production behavior requires a valid RED first:

1. write the focused test;
2. run it and confirm failure comes from the missing behavior rather than an
   import, setup, fixture, syntax, or environment error;
3. implement the smallest production change;
4. run focused GREEN and affected regressions;
5. obtain independent review;
6. remediate every Critical and Important finding and re-review;
7. run full approved gates before commit or advancement.

Tests must not be weakened to match implementation. Minor findings may be fixed
when doing so stays in scope; otherwise record them without expanding the Task.

## 8. Scope and overengineering guard

Every choice is classified as `REQUIRED NOW`, `DEFER`, or `DO NOT BUILD`.
Prefer the smallest deterministic, auditable, maintainable solution.

Do not introduce a generic ingestion platform, plugin framework, workflow
engine, UI platform, generic Markdown subsystem, M1 abstraction, PDF/OCR, or
new question generation without separate authority.

Task 9B is limited to the approved Mathpix MMD/MMD.ZIP-to-canonical-Task-9A
staging adapter. Task 9C owns future V1.19 writing and stops at Gate B. Task 9D
owns real-batch acceptance and stops at Gate C.

## 9. Session recovery

At the start of every session, read in order:

1. `AGENTS.md`;
2. `PROJECT_STATE.md`;
3. the current committed Design;
4. the current committed Plan, if one exists;
5. `git status`, current branch, upstream, and recent log;
6. relevant focused tests and frozen validators.

Do not depend on chat history. When documentation and Git facts disagree, use
validated Git state plus committed authority to recover execution, then update
the narrative at the next permitted documentation checkpoint.

After recovery, emit a concise acknowledgement containing the recovered branch
and HEAD, Task 9A and Task 9B status, V1.18 SHA/count status, the next approved
action, and confirmation that HUMAN GATES A–F are enabled.

## 10. Checkpoints and project state

After each major checkpoint, update `PROJECT_STATE.md` with the branch, HEAD,
current Task and phase, last GREEN gates, V1.18 SHA/count, V1.19 state, latest
commits, blockers, next autonomous action, and active HUMAN GATE if any.

Historical RED/review evidence stays historical and must not be treated as the
current execution state.

## 11. Reporting

Use concise checkpoint updates during normal execution. Provide a full report
only when a major Task closes, a HUMAN GATE triggers, an unrecoverable blocker
occurs, or the user explicitly requests it.

Avoid sending the complete 497-question corpus to an AI context. Prefer
read-only SQLite queries, candidate-local content, compact taxonomy context,
and structured evidence.

## 12. Current autonomous range

The approved sequence is:

```text
Task 9B implementation plan
-> B1 representative fixtures
-> B2 public carriers and API
-> B3 inventory and safety
-> B4 parser and Source IR
-> B5 mapping and provenance
-> B6 canonical package
-> B7 Task 9A equivalence
-> B8 determinism and security
-> B9 final review and closure
-> Task 9C Design and Plan
-> Task 9C dry-run/in-memory implementation and verification
-> HUMAN GATE B before first formal V1.19 write
```

Task 9B completion grants no database-writing, real-import, or promotion
authority. Task 9A remains the sole read-only preflight and duplicate/collision
authority.
