# V1.21 Formal Promotion Readiness Verification

Date: 2026-09-19 (Asia/Shanghai)

Status: `READY FOR FINAL V1.21 PROMOTION AUTHORIZATION`

## 1. Authority and implementation

The approved Design and RED-first Plan are:

- `docs/superpowers/specs/2026-09-19-v121-formal-promotion-readiness-design.md`
- `docs/superpowers/plans/2026-09-19-v121-formal-promotion-readiness.md`

Implementation checkpoints:

- `6eb48ce` — `docs: define V1.21 promotion readiness`
- `e7cdf4d` — `docs: plan V1.21 promotion readiness`
- `45dbb19` — `feat: add V1.21 promotion contracts`
- `5f690ee` — `feat: add V1.21 promotion readiness`
- `3eef866` — `fix: preserve V1.21 verification failure boundary`

The final review result is Critical 0 / Important 0. The review remediation
preserves the approved error boundary: malformed JSON raises the existing
input-format exception, while parsed-but-invalid candidate or formal manifests
produce a structured 21-check `FAIL` report without mutation.

## 2. Exact input authority

| Authority | Exact value |
|---|---|
| Formal baseline | V1.20 / 543 questions |
| V1.20 SQLite SHA-256 | `b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292` |
| V1.20 release digest | `1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf` |
| V1.21 candidate generation | `000004` |
| V1.21 candidate digest | `ecf624e3cb9fd8e7b1e0c664ddc5d51ef67f2d7f16f277c276be828eba32282c` |
| Candidate SQLite SHA-256 | `6e27e5b5eff5a701b4671a3e12ee538eed985147d86c23edef1e9489f714a53c` |
| Candidate manifest SHA-256 | `dc82e04639a4b54e24bbf7eceeb4ecec8a3751dfa7e8595f260b9d894d91fc83` |
| Accepted batches | 2015, 2016, 2017, 2018; 12 questions each |
| Promotion closure | 543 baseline + 48 promoted = 591 formal |

The real generation verifier is 24/24 PASS. V1.18, V1.19, and formal V1.20
remain unchanged. No `releases/V1.21/` directory exists.

## 3. RED-to-GREEN evidence

- Public-contract RED: 6 collected, 0 PASS / 6 expected contract FAIL / 0
  ERROR; the nine public symbols were absent.
- Primitive behavior RED: 5 collected and failed only because behavior was
  absent.
- Integration behavior RED: 9 collected normally and failed at the approved
  `NotImplementedError` scaffolds.
- Final focused suite: 26/26 PASS, including the review-driven parsed-invalid
  manifest safe-failure controls.
- V1.21 candidate regression: 44/44 PASS.
- V1.20 promotion regression: 30/30 PASS.

## 4. Deterministic real dry-runs

Two independently built, non-formal staging roots are byte-identical:

- `data/staging/task11-v121-promotion-dry-run-a/`
- `data/staging/task11-v121-promotion-dry-run-b/`

Each independently verifies 21/21 PASS and contains exactly:

```text
Joy_M2_Complete_Question_DB_V1_21.sqlite3
manifest.json
rollback.json
SHA256SUMS.txt
```

No image artifact is declared or present. Exact identities for both roots:

| Artifact / identity | SHA-256 or size |
|---|---|
| Release digest | `f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3` |
| Formal SQLite SHA-256 | `93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a` |
| Formal SQLite size | 10,063,872 bytes |
| SQLite semantic SHA-256 | `0a4e70acb1cc657207dd0fefb1e20581d34baadda804219ae2fbbfb2b5ca817f` |
| Manifest SHA-256 | `a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40` |
| Manifest size | 7,913 bytes |
| Rollback SHA-256 | `c7170aa0eabb0f3d8e20df265d7ca5dd1c8aadd32e3836ca13c3143d1f450bb2` |
| SHA256SUMS SHA-256 | `357bd18b4d77b545cf6deafde4216e9c82ba86187d8b405d3ee1bb1b12cb892f` |

The SQLite formal view contains 591 ordered rows. The first 543 rows equal the
formal V1.20 projection; the last 48 equal the candidate records with only the
approved publication authority transition to `published` and selectable.

## 5. Atomicity and rollback

Build and publication use private sibling trees and no-replace atomic rename.
Path overlap, symlink, existing-output, wrong candidate, and wrong approval
cases reject before publication. Isolated rollback proof removed an unchanged
digest-bound copied tree, retained an externally changed tree for manual
recovery, and left formal V1.20 unchanged.

The publication API was exercised only in isolated temporary repositories.
It has not been called against this repository's formal release root.

## 6. Fresh verification

| Gate | Result |
|---|---:|
| V1.21 promotion focused | 26/26 PASS |
| Complete maintained suite excluding attributed legacy behavior | 1005/1005 PASS |
| V1.21 candidate | 44/44 PASS |
| V1.21 real candidate verifier | 24/24 PASS |
| V1.19 candidate verifier | 16/16 PASS |
| V1.19 formal verifier | 18/18 PASS |
| V1.20 formal verifier | 21/21 PASS |
| Task 10C | 30/30 PASS |
| Task 10B | 50/50 PASS |
| Task 10A | 144/144 PASS |
| Task 9D | 48/48 PASS |
| Task 9C | 71/71 PASS |
| Task 9B | 342/342 PASS |
| Task 9A | 41/41 PASS |
| Task 7 | 7/7 PASS |
| Task 8 equivalence | 3/3 PASS |
| Task 6 oracle | 22/22 PASS |
| Task 3–6 gates | 54/54 PASS |
| V1.18 independent validator | PASS |

All maintained tests report zero failures, errors, skips, expected failures,
or unexpected successes. Legacy attribution remains the approved 9 PASS / 2
FAIL surface only: deterministic SQLite hash attribution and frozen artifact
byte-equivalence attribution. It is not a maintained blocker.

## 7. Frozen and publication boundary

- Formal V1.18 remains 497 questions with SQLite SHA-256
  `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`.
- Formal V1.19 remains 502 questions with SQLite SHA-256
  `5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff`.
- Formal V1.20 remains 543 questions with SQLite SHA-256
  `b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292`.
- Tracked release trees, all four V1.21 candidate generations, and the four
  approved canonical input packages preserve their exact verified authority.
- Ignored Python `__pycache__` files are runtime caches and are excluded from
  release identity; no tracked or formal artifact changed.
- No 2019 ingestion, V1.22 work, current-release pointer, PR, merge, rebase,
  squash, or formal V1.21 publication occurred.

## 8. Final human gate

The only next authorized action is an exact digest-bound human decision. Until
that statement is received, formal V1.21 publication remains prohibited.

```text
USER DECISION REQUIRED — FINAL V1.21 PROMOTION AUTHORIZATION

USER APPROVED RELEASE PROMOTION V1.21 f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3
```
