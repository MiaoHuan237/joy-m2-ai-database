# V1.23 Promotion Readiness — generation 000003

Status: PASS — EXACT-APPROVED V1.23 FORMALLY PUBLISHED.
Updated: 2026-10-20 (Asia/Shanghai).

The readiness evidence below is historical as of2026-10-19. Its unapproved/
absent-target statements describe that checkpoint only. The final section records
the subsequent actual human approval, publication, migration audit and fresh gates.

## Authority and boundaries

Human-approved Design: `docs/superpowers/specs/2026-10-14-v123-promotion-readiness-design.md`,
original commit `1c66a8e9daaaa991fc72b3ca891d87251051831b`,
SHA `dac063c914b2a7003295d1306d39b0390329f408bace59c9f14d0e943e943541`.
Plan checkpoint `8b349752a637fb5babf6ebf1eb4da152f46af579`; subsequent explicit
human Plan approval and Native / Inline implementation authorization received.
This report is evidence, not received promotion approval.

Formal querying remains V1.22 / 639 published records. No real publisher or
candidate writer was called. No query pointer, scheduler, source adapter,
taxonomy, difficulty, transcription, approval or historical data changed.
The user's AGENTS.md remains unstaged with SHA
`75ffa9680b18a0875fde8d36a8ca3e0ebda0603f10e8dc788e71ea8353d0311d`.

## Fixed input

- Baseline DB: `releases/V1.22/Joy_M2_Complete_Question_DB_V1_22.sqlite3`.
- Baseline DB SHA: `a474846a5b1d10a0fe48a259522fbb327747319f4a114452bf9f294405d8d9e0`; 10510336 bytes.
- Baseline manifest SHA: `441e00ac1536b959b40b6177bd17a6f14632a287f85145e202a51bcf137ddc8b`; 7915 bytes.
- Baseline release digest: `89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b`.
- Candidate generation: 000003; digest `c5c51df58d64349d58bd71469fe67a72cced56e77369126d6fec66bb2fcc955a`.
- Candidate DB SHA: `b7e2247e004cc4c91c339693de4f106edef11bb7067e34b52887547a8006cb01`; 10764288 bytes.
- Candidate manifest SHA: `febe70a572b82783bf6199679bf1a2024294d98b44b4fbe047a2349a3830a076`; 5664 bytes.
- Candidate root: `data/staging/auto-ingestion/candidates/8531b270990b350afbbcdc16eff2fddf63a1f33d7a451402199344eae2447a20`.
- Received approvals were reconstructed from actual receipts and canonical
  evidence; each prefix independently passed all24 candidate checks. No generated
  approval statement was consumed as human authorization.

| Ordinal | Accepted batch | Appended records |
|---|---|---:|
| 000001 | JOY-M2-HKDSE-2023-PP-MS | 12 |
| 000002 | JOY-M2-HKDSE-2025-PP-MS | 13 |
| 000003 | JOY-M2-STG-MOCK-2025-26-C-SET1-20260903 | 13 |

639 preserved +38 appended =677 records, not677 distinct original questions.
2023/2025 are another source of known originals; 2024 is not included.
The exact parent/preflight/approval chain remains the approved Design §3 chain.

## RED/GREEN and implementation

| Step | Assertion RED | GREEN evidence |
|---|---|---|
| API/models | 6 missing-API failures; then20 validation failures, zero errors | 96/96 model and historical-export checks |
| Primitives | 15 failures, zero errors | 12/12 models/primitives |
| Independent formal verifier | 33 failures, zero errors; independently serialized fixture | 24/24 models/primitives/verifier |
| Builder | 20 failures, zero errors | 36/36 cumulative focused |
| Publication/lifecycle | 7 publication +7 lifecycle failures, zero errors | 46/46 focused and V123 historical replay |

Checkpoints: `94cb717`, `6703041`, `ffb5aa5`, `d463de7`, `cfc20e6`.
Missing imports/setup failures were not used as behavioral RED.
The fixture and corruption re-hashing use test-owned literals/SQL/serialization,
not builder output as an expected oracle. Production verifier imports no builder
projections or DDL. Malformed JSON remains InputFormatError; parsed invalid
values return structured FAIL. Read-only SQLite uses escaped URI paths.

Focused controls cover baseline schema forgery, altered Oxford source/solution,
inherited rows, candidate bytes/parent/approval, manifest types, schema corruption,
all639/all38 projections, exact ledger/counts, output overlap/symlinks, no-replace
competition, private copy tamper, and unchanged-owned versus changed-tree cleanup.
Real lifecycle approval literal remains None; isolated tests cover both phases.

## Real non-formal dry-runs

Two independent roots:
- `data/staging/task13-v123-promotion-readiness/dry-run-a-000001`
- `data/staging/task13-v123-promotion-readiness/dry-run-b-000001`

Independent formal verifier:21/21 PASS each. Candidate verifier:24/24 PASS.
All four constrained files are byte-identical, including SQLite; no semantic-only
substitution. Read-only queries verify677 unique IDs, all published/selectable,
639 baseline rows unchanged and38 projection rows field-identical except the
approved status/order/authority projection. All inherited audit tables remain.

Actual release digest:
`84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc`

Formal-equivalent SQLite SHA:
`28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd`

Semantic SHA:
`531e7cf69eec75096f500e2de62dcb0eba0ad68d4d0663dc3bd5faa84e7e1c6d`

Manifest SHA:
`54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `Joy_M2_Complete_Question_DB_V1_23.sqlite3` | 10928128 | `28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd` |
| `SHA256SUMS.txt` | 268 | `e4bb590258ceb0745a2fd4097a9978b60224d46211deb8e17d1cff121a22fb39` |
| `manifest.json` | 6728 | `54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498` |
| `rollback.json` | 657 | `f7d9aa1d07d14ed3357991a9de7b0834d98947c9f2b56598f231242fbb284951` |

SHA256SUMS binds the other three files, with no self-entry. Manifest and rollback
close over the fixed input, ledger and six existing authority references.
The six references do not become six additional formal artifacts.

Oxford source `OXFORD-M2-2025-26-C-SET1` returns13 IDs Q01–Q13, each with its
nonempty approved publisher solution, identical to candidate content. These are
publisher mock answers, not HKEAA official MS. Independent explanations are not
invented. PDF/page/region figure locators remain unchanged; zero standalone
canonical image files are fabricated or claimed.

## Full gates and independent review

Fresh post-repair serial maintained suite: 65 modules, 1331/1331 PASS in563.728s;
failures0, errors0, skipped0, expectedFailures0. Focused promotion plus historical
replay:51/51 PASS. Historical replay runs the V1.19–V1.22 formal verifiers and
candidate replay checks; separate V1.18 validator PASS/497. Each real candidate
prefix passes24/24, both real dry-runs pass21/21 under the repaired verifier.
All784 protected formal/source/approval/candidate/AGENTS file identities match
the pre-execution snapshot. Real releases/V1.23 is absent.

Independent fresh-context implementation reviewer: Critical0/Important0/Minor0
after targeted repairs and re-review. Initial findings were ownership cleanup,
extra filesystem nodes, noncanonical SHA256SUMS bytes, and EOF whitespace.
The verifier now rejects empty extra directories/FIFOs and non-LF sums bytes.
Cleanup claims owned output into an exclusive mode0700 quarantine, rechecks its
identity/bytes, and never overwrites a competitor when restoring changed evidence.
Recovery conflict preserves both the competitor and quarantined evidence.
Initial boundary controls observed7 assertion failures/0errors, then3/3 GREEN;
the remaining fingerprint/rename race observed1 assertion failure/0errors, then
4/4 GREEN. An additional restore-conflict control passes, giving5 boundary tests
included in the final full gate. The reviewer independently reproduced competitor
and quarantine preservation in a system temporary directory, not real releases.

The first full run was NOT accepted:1326 tests/1failure/0errors. Its historical
V1.19 staging-immutability assertion detected backup-files.json and backup evidence
created concurrently by the executor. The narrow historical test passed unchanged;
the accepted1331-test rerun was fully serial with no concurrent staging work.
No historical assertion was weakened or failure waived.

Review rulings: canonical sums was treated as Important because byte identity is
binding; EOF whitespace was repaired to satisfy the mandatory diff gate. Real
publication/live rollback and new mathematical transcription review were outside
review authority. Final full gates, backup and reporting remained executor duties,
not claims supplied by the reviewer. All in-scope required findings are resolved.

Evidence/log root: `data/staging/task13-v123-promotion-readiness/`.
Only known legacy attribution module is excluded from maintained discovery;
its historical9PASS/2FAIL attribution is not a waiver for a maintained failure.

## Backup and recovery

Existing Oxford archive:
`dist/backups/oxford-c1-accepted-20261014-000003.zip`,
SHA `317afa362a7bfcbe5c256b1c611f90b599013b8fcf4f804c8c73685d6a37b149`.
All665 archive members verified; all10 selected candidate files are covered.

New non-overwriting local archive:
`dist/backups/v123-promotion-readiness-20261019-000001.zip`,
SHA `3b14de979d67272b5265ea51b0b2a2a2120fdafbc0f894c25d9ae91745a93fda`.
795 explicit files cover protected inputs, both dry-run trees and identity evidence.
Existing backup CLI was used; no live state SQLite or sidecars included.
Archive manifest/bytes and795 isolated restored files independently match.
Restore root: `tmp/v123-promotion-readiness-restore-20261019-000001`.
This is local recovery, not off-device backup. Git does not back up ignored data.
The archive is the immutable-input/dry-run snapshot; Design/Plan headers reflect
the checkpoint at archive creation. Final engineering and readiness documentation
are separately preserved by the task Git checkpoint, not claimed as archive data.

## Rollback / eventual target

No live rollback executed. The receipt permits only
`remove_release_tree_if_release_digest_matches`, with exact four-file closure
and protected V1.22 identity. Unexpectedly changed outputs are retained for
manual recovery. No default query pointer adjustment is part of this work.

After a future exact human promotion approval, the only formal target is:
`releases/V1.23/`, containing exactly the four artifact names above.
Real `releases/V1.23/` is still absent.

## Historical final human gate (2026-10-19; now satisfied)

USER DECISION REQUIRED — FINAL V1.23 PROMOTION AUTHORIZATION

The following is the required future statement, NOT a received approval:

```text
USER APPROVED RELEASE PROMOTION V1.23 84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc
```

Final target paths, to be created only after that exact human authorization:

- `releases/V1.23/Joy_M2_Complete_Question_DB_V1_23.sqlite3`
- `releases/V1.23/manifest.json`
- `releases/V1.23/SHA256SUMS.txt`
- `releases/V1.23/rollback.json`

All required implementation/readiness gates passed. Task-only engineering/docs
are committed normally; the delivery response reports the exact commit and actual
remote synchronization result. AGENTS.md is excluded from staging and commits.
Never treat this report, a generated statement or an import approval as received
release approval. No2024/2025 reimport or V1.24 work is authorized. Stop here.

## Exact-approved formal publication and migration audit — 2026-10-20

The following exact statement was actually received from the human in this
conversation, separately from the earlier generated request:

```text
USER APPROVED RELEASE PROMOTION V1.23 84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc
```

Execution reused the existing publisher, both dry-run trees and original
generation000003. Under existing `cycle.lock`, no pending intent/newer receipt,
three candidate prefixes24/24, both dry-run verifiers21/21, approved identity,
four-file equality and784 protected identities were checked before publication.
The publisher was called once with the exact typed human approval; its private
copy and atomic no-replace publication produced `releases/V1.23/`.
No candidate writer, repeated ingestion or database rebuild was called.

Formal independent verifier21/21 PASS. All four formal files have the identical
bytes/SHA/sizes listed above and match both dry-runs. The formal view
`formal_complete_questions_v123` returns677 unique published/selectable IDs.
All639 baseline records and38 approved promotion projections match field-for-field;
ledger remains2023(12),2025(13),Oxford(13). Oxford13 publisher solutions are
queryable and unchanged, not HKEAA official MS. Answers:572 source_provided,
71 ai_solved_verified,34 missing_from_source. No content/enrichment/figure change.
No persistent query pointer or scheduler configuration changed.

The Design §8 lifecycle literal now records the actually received digest, not a
manifest-discovered approval. All unapproved/wrong/missing approval controls and
candidate-writer formal-root rejection remain. No production code changed.
Fresh post-publication focused/historical51/51 PASS in108.271s; serial
maintained65modules1331/1331 PASS in560.267s; failures/errors/skips/expectedFailures
all0. V1.18 validator PASS/497; historical formal verifiers/replays passed.
Separate read-only operational reviewer: Critical0/Important0/Minor0, including
an independently rerun formal verifier and all784 protected hashes/sizes.

Runtime received approval, publication receipt and fresh logs:
`data/staging/task13-v123-promotion-readiness/publication-20261020-000001/`.
Pre-publication HEAD:`92fd257801f8d49bd0fff7c3b772652591f33d84`.
All formalV1.18–V1.22, old candidate generations, sources, approvals,2024 evidence
and user's unstaged AGENTS.md retain their original identities. Real V1.23 now
exists as exactly the four declared files; it is no longer merely candidate data.

Rollback remains identity-guarded removal of only this exact release tree.
No live rollback or persistent query switch was executed. The existing V1.22
remains a recoverable unchanged formal baseline. Mathematical retranscription
and live rollback were outside the operational review; no such results are claimed.
Final Git commit/push results are reported separately at delivery. Do not infer
ignored-data backup or off-device storage from Git synchronization.

Post-publication local archive:
`dist/backups/v123-published-20261020-000001.zip`, SHA
`46e1b4a738378d72c81a90c27fb624d192e088413e78743b3ff59d4d0fb583c7`.
The existing explicit-list backup CLI archived805 static files: protected input/
dry-run evidence, formal four-file output, exact received approval, receipt and
fresh gate logs. No live state SQLite/sidecars or user AGENTS.md were archived.
All805 original/archive/isolated-restored byte identities matched; restore root
`tmp/v123-published-restore-20261020-000001`. Mutable status documents are preserved
by the separate Git checkpoint, not claimed as part of this data snapshot.
This is local recovery only, not off-device backup.
