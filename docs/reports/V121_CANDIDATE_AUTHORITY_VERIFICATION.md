# V1.21 Next-Version Candidate Authority Verification

Date: 2026-09-18 (Asia/Shanghai)

Status: `V1.21 CANDIDATE AUTHORITY — CLOSED / PASS`

## 1. Authority and implementation

Human Gate A authorized an append-only V1.21 staging candidate lifecycle over
the immutable formal V1.20 release. The implementation is deliberately
versioned and narrow: it adds exact V1.21 carriers, a strict manifest loader,
the approved HKDSE transcription bridge, read-only preflight, a deterministic
candidate writer, and an independent verifier. It does not generalize the
historical V1.20 modules and creates no formal V1.21 release or promotion API.

Implementation checkpoints:

- `983c8db` — `docs: define V1.21 candidate authority`
- `e30bb78` — `feat: add V1.21 candidate contracts`
- `3b674d2` — `feat: add V1.21 HKDSE canonical bridge`
- `e8d7c18` — `feat: add V1.21 import preflight`
- `1961a6e` — `feat: add V1.21 candidate writer and verifier`
- `aaa4ac0` — `test: close V1.21 candidate authority gaps`

All new behavior was established with feature-missing or behavior-missing RED
before minimum GREEN. Review remediation added exact formal/parent duplicate,
stale preflight/approval, failed-append preservation, and append-only public
surface regression coverage.

Independent implementation review result:

- Critical: 0
- Important: 0
- Minor: 0

## 2. Frozen baseline

| Release | SQLite SHA-256 | Size | Questions |
|---|---|---:|---:|
| V1.18 | `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7` | 9,363,456 | 497 |
| V1.19 | `5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff` | 9,478,144 | 502 |
| V1.20 | `b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292` | 9,768,960 | 543 |

V1.20 release digest remains
`1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf`.
No `releases/V1.21/` directory exists.

## 3. V1.21 contract closure

- Target identity: exactly `V1.21`.
- Baseline: exactly formal V1.20/543.
- Genesis candidate digest:
  `331192032f184a44ed383e6dacc2f06fbacb60ad94414298fcb935ff56cb5906`.
- Every approval binds batch ID, preflight digest, target version, and exact
  parent candidate digest.
- Parent candidates are independently verified before their effective state
  participates in preflight or append.
- Stale preflight and stale approval replay are rejected without changing the
  parent candidate.
- Duplicate/collision authority includes both formal V1.20 and all accepted
  V1.21 parent batches.
- Candidate publication is atomic and staging-only. Formal V1.20 and every
  historical object are preserved byte-for-byte.

## 4. Fresh verification

| Gate | Result |
|---|---:|
| V1.21 focused | 44/44 PASS |
| Maintained suite excluding attributed legacy behavior | 979/979 PASS |
| Task 9A | 41/41 PASS |
| Task 9B | 342/342 PASS |
| Task 9C | 71/71 PASS |
| Task 9D | 48/48 PASS |
| Task 10A | 144/144 PASS |
| Task 10B | 50/50 PASS |
| Task 10C | 30/30 PASS |
| V1.18 independent validator | PASS |
| V1.19 candidate verifier | 16/16 PASS |
| V1.19 formal verifier | 18/18 PASS |
| V1.20 formal verifier | 21/21 PASS |

All maintained suites have zero skips and zero expected failures.
`git diff --check` passes.

## 5. First real 2015 operational result

The previously approved transcription was reused without OCR or content
changes:

- batch: `JOY-M2-HKDSE-2015-PP-MS`
- approved transcription digest:
  `41e284c25e41759f72debd192e58c00288d14a355e704978d80587c201e970fc`
- records: 12
- marks: 100

Two independent V1.21 canonical roots were byte-identical. The initial
preflight correctly blocked all 12 records because their historical `Txx`
module proposals and free-form English tags are not controlled V1.20 taxonomy.
Its diagnostic preflight SHA-256 is
`94a5980b50bac188809e7dbc461bdda4927bdf149f13c7ee7867c5b463a6c062`.

A taxonomy-only proposal was therefore generated at
`data/staging/task11-v121-hkdse-2015/taxonomy-remediation-proposal/`. It changes
only `module_proposal` and `tag_proposals`; question text, official marking
scheme, pages, marks, subparts, figures, methods, difficulty, source hashes,
and record order are unchanged. Its new transcription digest is:

`9dc9cbf54fccc4aac856292e7d2202b134999967c1317c7523201fe155054cd1`

The next allowed action is exact human transcription approval. Canonical
regeneration, authoritative import preflight, candidate write, and promotion
remain unstarted for this revised payload.
