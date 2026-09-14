# Task 10B HKDSE PDF / PP-MS Adapter Verification

Evidence date: 2026-09-14 (Asia/Shanghai)

Branch: `task8b/pipeline-migration`

Implementation base: `2e85ac2b196c65800ef96ef6bfac10779e803452`

Final implementation commit: `fb473648a4abfc4e0f6071e2d4a34d44c243d6f9`

## 1. Result and boundary

Task 10B engineering implementation is `COMPLETED / PASS`. The maintained
adapter accepts only an exact `joy_m2_staging_batch_v1` manifest and the
SHA-256/page-count-bound HKDSE M2 PP/MS source pair. It produces two
non-authoritative extraction passes, a deterministic transcription proposal,
an exact human approval envelope, and—only after approval—a canonical Task 10A
V1.20 import package.

The 2012 real-source pilot is not part of this engineering checkpoint. It must
stop at `USER DECISION REQUIRED — PDF TRANSCRIPTION REVIEW`; no canonical
bridge, Task 10A preflight, writer, database mutation, or release operation is
authorized before the exact transcription approval is received.

## 2. Contract and implementation

The approved authority is:

- Design: `docs/superpowers/specs/2026-09-14-task10b-hkdse-pdf-adapter-design.md`;
- Plan: `docs/superpowers/plans/2026-09-14-task10b-hkdse-pdf-adapter.md`.

The exact append-only public suffix contains eight frozen carriers, one domain
error, and five APIs:

1. `extract_hkdse_pdf_embedded_pass`
2. `load_hkdse_pdf_extraction_pass`
3. `propose_hkdse_pdf_transcription`
4. `approve_hkdse_pdf_transcription`
5. `adapt_verified_hkdse_pdf_transcription_v120`

The implementation validates strict JSON shape, source SHA-256 and PDF page
counts, complete-question order and mark closure, exact pass identity, and
deterministic issue/status/digest closure. Embedded extraction assigns text
only when every declared page has one record owner. It never trims, rewrites,
solves, or normalizes source mathematics. The canonical bridge writes the
existing Task 10A package shape atomically beneath staging and performs no
deduplication, preflight, database write, or publication.

## 3. RED-first evidence

The implementation was developed through the approved staged RED gates:

| Gate | Valid RED evidence | Final result |
|---|---:|---:|
| Public models | 8 expected failures, 0 errors | GREEN |
| Source/pass loader | 10 expected failure signals, 0 errors | GREEN |
| Embedded extraction | 4 expected failures, 0 errors | GREEN |
| Comparison/proposal | 18 expected failure signals, 0 errors | GREEN |
| Approval | 8 expected failure signals, 0 errors | GREEN |
| Canonical bridge | 6 expected failures, 0 errors | GREEN |
| Root public surface | 1 expected failure, 0 errors | GREEN |
| Safety edge cases | 4 expected failures, 0 errors | GREEN |

Independent review then found two Important gaps. The first RED produced two
failures proving that a reconstructed verified carrier without a valid
approval could reach the canonical bridge. The second RED proved that a
same-page-count PDF replacement could bind the approved SHA to replacement
text. The minimum corrections now reconstruct and bind the exact approval and
use one file-descriptor byte snapshot for PDF SHA, page count, and text.
Both regressions pass, and final independent re-review reports Critical 0 /
Important 0.

## 4. Fresh verification gates

| Gate | Result | Exit |
|---|---:|---:|
| Task 10B focused | 50/50 PASS | 0 |
| Complete maintained suite excluding attributed legacy behavior | 904/904 PASS | 0 |
| Task 9A integration | 41/41 PASS | 0 |
| Task 9B focused | 342/342 PASS | 0 |
| Task 9C focused | 71/71 PASS | 0 |
| Task 9D focused | 48/48 PASS | 0 |
| Task 10A focused | 143/143 PASS | 0 |
| Formal V1.19 candidate verifier | 16/16 PASS | 0 |
| Formal V1.19 independent verifier | 18/18 PASS | 0 |
| V1.18 independent validator | PASS | 0 |
| `git diff --check` | PASS | 0 |

All maintained tests reported zero skips and zero expected failures. The
explicit module enumeration is required because the namespace-style test
directories cause plain recursive discovery to collect zero tests in the
approved runtime.

## 5. Frozen identity and zero-write proof

| Authority | SHA-256 | Count |
|---|---|---:|
| Frozen V1.18 SQLite | `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7` | 497 |
| Formal V1.19 SQLite | `5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff` | 502 |

`releases/V1.20/` does not exist. No V1.20 candidate, formal database, import,
promotion, or release was created. The actual historical V1.16 ZIP was not
searched, read, or rehashed; its compatibility digest remains a historical
constant only.

## 6. Independent review and remaining gate

Final independent implementation re-review: Critical 0 / Important 0.
The approved implementation scope and root API are closed. The only next
operational action is the exact 2012 two-pass pilot from the SHA-bound source
pair. That pilot must remain ignored staging evidence and stop for human
transcription review. Task 10A preflight and all writes remain prohibited until
the exact approval statement is supplied.
