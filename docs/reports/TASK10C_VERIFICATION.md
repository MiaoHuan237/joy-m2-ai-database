# Task 10C V1.20 Promotion Readiness Verification

Date: 2026-09-17 (Asia/Shanghai)

Status: `READY FOR FINAL PROMOTION AUTHORIZATION`

## 1. Authority and implementation

- Design/Plan closure commit:
  `59f9f52443405b7e467da8c69855bc45d3dd8223`
  (`docs: close V1.20 promotion authority`).
- Implementation commit:
  `06bd83768a6619d69a9394ed1b9bf16564c15759`
  (`feat: add V1.20 promotion readiness`).
- Formal publication was not executed. `releases/V1.20/` remains absent.
- No current-release pointer or index was created or changed.

The implementation is the smallest append-only V1.19-to-V1.20 promotion
extension. It accepts only the exact verified generation-000003 Task 10A
candidate, builds under a non-formal staging root, verifies independently, and
requires an exact digest-bound human approval before formal publication.

## 2. Frozen input authority

| Authority | Exact identity |
|---|---|
| V1.18 SQLite | `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7` |
| V1.18 count | 497 |
| V1.19 SQLite | `5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff` |
| V1.19 count | 502 |
| V1.20 candidate generation | `000003` |
| V1.20 candidate digest | `88cc945b6296652c88041e8e51a5c586300c2201a9f48e21abde80d97da3a7b3` |
| V1.20 candidate SQLite | `d8ff5bf9e38f27e23e72c39ae41cb297b4223fde5d2bc149178a7033fe9769d1` |
| V1.20 candidate manifest | `673a598b7d5b59394ebaf1307943f90a293c165ecc7aa349c23c2947397f5052` |

The candidate verifier is 24/24 PASS. Its ordered batch ledger is exactly:

1. `JOY-M2-HKDSE-2012-PP-MS` — 14 questions;
2. `JOY-M2-HKDSE-2013-PP-MS` — 14 questions;
3. `JOY-M2-HKDSE-2014-PP-MS` — 13 questions.

The closure is 502 baseline + 41 promoted = 543 formal questions.

## 3. TDD and verifier closure

The public-contract RED collected 43 tests and produced 33 PASS / 10 expected
contract FAIL / 0 ERROR. The initial behavior RED collected 12 tests and failed
only because Task 10C behavior was still absent. Review-driven REDs then proved
and closed exact DDL, lexical symlink, candidate-input error handling, manifest
artifact authority, SQLite schema/metadata/inherited-relation authority, all
three candidate-root overlap rules, and publication cleanup ownership.

The final focused suite is 30/30 PASS. The independent verifier exposes exactly
21 ordered checks and both real dry-run trees pass 21/21. Parsed corruption
returns structured FAIL; malformed JSON retains the approved input-format
exception boundary. Verification is read-only and never repairs artifacts.

Independent final re-review result:

- Critical: 0
- Important: 0
- Minor: 0

## 4. Deterministic dry-run result

Two independently built non-formal roots are byte-identical file-for-file:

- `data/staging/task10c-v120-promotion-dry-run-a/`
- `data/staging/task10c-v120-promotion-dry-run-b/`

Their exact identities are:

| Artifact / identity | SHA-256 or size |
|---|---|
| Release digest | `1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf` |
| Formal SQLite SHA-256 | `b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292` |
| Formal SQLite size | 9,768,960 bytes |
| SQLite semantic SHA-256 | `e3f3d2b09fa7869ee266d3afb01e6160406764c96127adfaf236a8deee8700ba` |
| Manifest SHA-256 | `19ac2e43ded74a3f3eaf75c184b5eb231c9f1b0b152f5914cd822a321b045098` |
| Manifest size | 6,643 bytes |
| Rollback SHA-256 | `27298a8e5983b31fc5349fbc41e49f821bd98ded17f5a9c94f5d37e94996a3db` |
| SHA256SUMS SHA-256 | `f6727df2d70fe2a44b2ff026a49e2bf0f6d178b8ff829026b84bc36253b74913` |

SQLite `integrity_check` is `ok`, foreign-key errors are 0, the formal view has
543 rows, the inherited V1.19 view has 502 rows, the promoted table has 41 rows,
all 41 are `published` and selectable, and the ordered ledger has 3 rows.

## 5. Artifact, publication, and rollback safety

The exact formal tree, if and only if final approval is later consumed, is:

```text
releases/V1.20/
  Joy_M2_Complete_Question_DB_V1_20.sqlite3
  manifest.json
  SHA256SUMS.txt
  rollback.json
```

No candidate image is declared, so no image file is present in this release
tree. Manifest, filesystem, SHA256SUMS, ArtifactRef, rollback, candidate, batch,
and promotion identities close independently. A failed unpublished build
discards only its private tree. Post-rename cleanup removes a target only while
its complete fingerprint still equals the owned source; externally changed
targets are retained for manual recovery. The rollback receipt authorizes only
removal of the exact digest-matching V1.20 tree and never rewrites V1.19.

The reported 2014 result-printing field typo was searched read-only. No
persistent repository accessor was found; it remains a one-off,
non-authoritative operational script defect and generation 000003 was not
rebuilt or altered for it.

## 6. Fresh gates

| Gate | Result |
|---|---:|
| Task 10C focused | 30/30 PASS |
| Complete maintained suite excluding attributed legacy behavior | 935/935 PASS |
| Task 9A | 41/41 PASS |
| Task 9B | 342/342 PASS |
| Task 9C | 71/71 PASS |
| Task 9D | 48/48 PASS |
| Task 10A | 144/144 PASS |
| Task 10B | 50/50 PASS |
| Formal V1.19 candidate verifier | 16/16 PASS |
| Formal V1.19 promotion verifier | 18/18 PASS |
| Current V1.20 candidate verifier | 24/24 PASS |
| Task 7 | 7/7 PASS |
| V1.18 independent validator | PASS |
| `git diff --check` | PASS |

All maintained suites report zero skips and zero expected failures. The legacy
attribution surface remains the approved 9 PASS / 2 FAIL categories only:
deterministic SQLite hash attribution and frozen artifact byte-equivalence.
Those are not maintained blockers.

## 7. Final gate

Formal current remains V1.19 / 502. Formal V1.20 is not published. The only
next action is an explicit human decision using exactly:

```text
USER APPROVED RELEASE PROMOTION V1.20 1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf
```

Until that exact statement is received, publication is forbidden.

