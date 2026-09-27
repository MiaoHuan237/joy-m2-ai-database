# V1.22 Promotion Readiness — fixed 2019–2022 envelope

Date: 2026-09-27. Authority: user's autonomous readiness authorization;
formal publication requires a later exact human approval.

## 1. Purpose and decisions

Prove the existing approved candidate can become 639 published/selectable whole
questions without changing content. Formal current remains V1.21/591.
Use independent fixed-version modules patterned on the committed V1.21
promotion, not a generic engine and not mutation of historical modules.
Direct reuse of V1.21 constants is invalid; a generic framework is unnecessary.
This Design authorizes its Plan, independent review, RED-first implementation,
isolated publication tests, staging dry-runs, regression and ordinary commits/push.
It does not authorize real publication, rollback, next ingestion or V1.23.

## 2. Exact input envelope (verified, not inferred)

At engineering baseline `ac132bb071a90055059adfa0912aa4f97c7d8ba7`:

| Identity | Value |
|---|---|
| baseline | V1.21, 591 whole questions |
| baseline SQLite SHA / size | `93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a` / 10063872 |
| baseline manifest SHA / size | `a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40` / 7913 |
| baseline release digest | `f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3` |
| candidate directory | `data/staging/task12-v122-hkdse-2022/candidate-generation-000004` |
| candidate digest | `82b10a551f70eebda2e0aa4d10c962e317767e936b4f0d9aa798629bb8070d46` |
| candidate SQLite SHA / size | `f1adf0ff7c2034445b1ee4724c03e8c66c6026c5e94d37cc469e1b350c2a9a7a` / 10330112 |
| candidate manifest SHA / size | `dc974a1f3180fc3d7d416385242d21aec78266f4e52f5a9de5732f31d57a5403` / 6851 |
| generation / batches / additions / formal total | 4 / 4 / 48 / 639 |

Both builder and independent verifier require all 24 candidate checks PASS and
exact hashes/sizes, typed approved prefix and manifest identities. Ledger order
is 2019, 2020, 2021, 2022, 12 questions each, with these exact preflight/parent pairs:

| Year | Preflight | Parent |
|---|---|---|
| 2019 | `674624abcd338b2fa3683b982300a30082e3d0e62f95f97e3e8d25e12d1d0fa5` | `7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7` |
| 2020 | `f57e4aea6fa36d3721ca6705214c47316010a2db58ed7a092fe08f2e68d63530` | `83c5efa109132c85dca8b96679ac97d4d9a59dd94e0cc76a57c80871a944ff07` |
| 2021 | `f2d387304b68d3648bd2501a52aa0517e3218ac71833c78a322450603010b6b6` | `877cafa7425b53a08835277c828b346f29112ecbfce82ae861336a2575047cfc` |
| 2022 | `ae96a9a971fafdd6e900ced6f80ee39d4c1365e166b5d4efa7fbcc47383b1fad` | `20342ba339ef8200ee6d941683d12698c2504c0872548a26717b2771ee2d1707` |

Batch IDs are exactly `JOY-M2-HKDSE-<year>-PP-MS`. Every approval string and
ordered authority artifact must be reconstructed by existing V1.22 APIs.
No candidate regeneration or import replay writes are needed.

## 3. Normative fixed counterpart and explicit delta

The V1.21 promotion Design dated 2026-09-19 §§4–11 and committed implementations
`v121_promotion_models.py`, `v121_promotion.py`, `v121_promotion_verification.py`
at the engineering baseline above are the normative algorithm/shape counterpart.
Only the following explicit deltas are authorized in NEW V1.22 files:

- target V1.22 / v122 / V122 / user_version 122 / new task12 namespace;
- baseline V1.21 / v121 / formal_complete_questions_v121 / 591;
- exact identity literals and ledger in §2;
- new formal orders 592–639, 48 additions, 4 batches;
- formal_complete_questions_v122 is the UNION ALL of the existing V1.21
  formal view once and new task12 promoted table once, ordered by formal_order;
- promotion schema keys use task12-v122, baseline schema task11-v121-formal-v1;
- independent preservation check named `v121_preservation`.

This is an audited role-specific port, not global replacement: inherited
task10/task11 objects and all historical schema/metadata remain unchanged.
Independent verifier duplicates its own constants, DDL and identity projections;
it must not import builder functions to decide correctness.

## 4. Public surface and formal projection

Append exactly these nine exports, retaining the entire historical prefix:
V122PromotionContract, V122PromotionBuildRequest,
V122PromotionVerificationRequest, V122ReleasePromotionApproval,
V122PublicationRequest, V122PromotionArtifacts, build_v122_promotion,
verify_v122_promotion, publish_v122_release.

Carriers have exact counterpart fields/order/types/no-default/frozen validations,
substituting exact V122 candidate/promotion carrier types. Public functions have
the counterpart `(request, config: PipelineConfig)` signature and return
V122PromotionArtifacts / VerificationReport / V122PromotionArtifacts respectively.

The 14 contract values in counterpart field order are:

```text
V1.22
task12-v122-formal-manifest-v1
task12-v122-formal-v1
task12-v122-promotion-identity-v1
task12-v122-formal-rollback-v1
122
Joy_M2_Complete_Question_DB_V1_22.sqlite3
manifest.json
SHA256SUMS.txt
rollback.json
images/sha256
task12_v122_promoted_questions_v1
task12_v122_promotion_v1
formal_complete_questions_v122
```

Copy the exact candidate SQLite into a private staging tree. In one transaction
add promotion metadata, the promoted table and formal view, with counterpart
DDL/constraints under §3 deltas. For only the 48 projected rows, change
record_status candidate→published, selectable 0→1, authority_kind to
task12_v122_promoted; counterpart column renames only. All other field values
are exact, including PP/MS provenance, figures, taxonomy and missing explanations.
The inherited 591-row formal view remains value-identical. Do not double-count
historical candidate tables. Preserve every prior schema object/table row except
the exact release_metadata_v2 keys from counterpart §7.4 mapped to §3 and
new task12 metadata keys. All old task11 metadata keys remain unchanged.

## 5. Artifacts, identity, verification and safety

Exactly four current files, no standalone images (PDF graph references retained):
Joy_M2_Complete_Question_DB_V1_22.sqlite3, manifest.json, SHA256SUMS.txt, rollback.json.
Manifest exact keys, nested structure, strict types, artifact references,
UTF-8 canonical JSON + LF, sorted SHA closure, semantic projection and release
digest follow counterpart §§8–10 with only §§2–4 deltas. Final release digest is
computed from actual formal-equivalent bytes, never from candidate digest alone.
Two independent builds must be byte-identical for all four files, relative
ArtifactRef hash/size/kind, semantic digest and release digest; paths may differ.

The independent verifier has the same 21 ordered checks, with only
v120_preservation→v121_preservation. All required checks must PASS. It verifies
baseline objects and values, approved new row projection, source/approval chain,
SQLite integrity/FK/schema, ledger, unique IDs, 639 published/selectable rows,
manifest/SHA/filesystem closure, exact types (not bool-as-int), deterministic
identity and allowed location. Malformed input/context exceptions and parsed
corruption structured FAIL behavior remain the counterpart behavior.

Builder outputs only under non-formal staging; formal-root attempts fail.
Publication API tests run only in isolated repository roots. The later real gate:

```text
USER APPROVED RELEASE PROMOTION V1.22 <actual_release_digest>
```

Exact typed approval must bind reverified dry-run and private copied bytes.
Atomic no-replace publication targets only `releases/V1.22`. Existing targets
conflict. Failure cleanup only removes owned unchanged private/new output,
never candidate or historical formal roots. Rollback receipt retains counterpart
digest-bound remove-release-tree action; no rollback execution is authorized now.
No formal default-query or pointer mutation is implemented; formal current stays
V1.21 until separately approved publication/documentation transition.

## 6. Lifecycle and closed scope

Historical tests must not assert V1.22 is forever absent. In isolated tests,
unapproved formal creation is denied, and after exact test-root approval the
published identity must match. For the real repository, absence is required
during readiness; once an explicit real approval is recorded, any existing
V1.22 must match that approval and independent verifier. Never invent a real
approval, waive historical protection or relax byte equality.

The real-repository regression's trusted approval input is a checked-in literal
`APPROVED_V122_RELEASE_DIGEST = None` in `test_v122_historical_replay.py`, not a
manifest, generated receipt, environment variable or discovered file. It remains
None throughout this readiness task; the real target must therefore be absent.
Only a subsequent exact human publication authorization may replace that value
with the approved digest (an evidence-value update, not a lifecycle logic change).
The gate helper accepts this explicit input: None requires absence; a non-None
value must be an exact lowercase SHA-256, requires a present independently verified
release, and must equal the verified release identity. Wrong/malformed values or
missing approved output fail. Isolated tests exercise both values and mismatches.
Readiness code must never infer or automatically set this literal from dry-run
results. The publication API still requires its separate exact typed approval.

NEW production: three `src/joy_m2/ingest/v122_promotion*.py` counterpart modules.
MODIFIED production: `src/joy_m2/ingest/__init__.py` append-only exports only.
NEW tests: `tests/unit/test_v122_promotion_models.py`,
`tests/unit/test_v122_promotion_primitives.py`,
`tests/integration/test_v122_promotion.py`.
MODIFIED tests: only existing public-surface prefix assertions and V1.22
lifecycle absence assertions proven to need the explicit conditional gate;
the Plan must enumerate their exact paths before implementation.
DOC: this Design, its Plan, `docs/reports/V122_PROMOTION_READINESS.md`, PROJECT_STATE.md.
Ignored runtime: `data/staging/task12-v122-promotion-readiness/**`,
`tmp/pdfs/task12-v122-promotion-readiness/**`.
No changes to historical production, source/candidate inputs, formal releases,
CLI, dependencies, 2023 ingestion or V1.23.

## 7. Acceptance and final stop

Design/Plan independent review then commit before production. API/model RED
first (missing API assertions, not imports), model GREEN and callable stubs;
then dependency-ordered valid primitive/build/verifier/publication behavior RED
before each corresponding implementation. Missing builder fixture is not verifier
or publication RED. Establish an independently constructed temporary formal fixture
for verifier RED, then verifier GREEN, builder RED/GREEN, publication RED/GREEN.
Do not call setup/import errors valid behavior RED. Preserve separate test-root
publication and real-root no-publication safety. Full maintained suite with zero
skips/expected failures; historical formal verifiers and V1.18 validator; fresh
candidate verification and frozen/source fingerprints; independent review with
Critical=0/Important=0; ordinary engineering/docs commits and push.

Stop at USER DECISION REQUIRED — FINAL V1.22 PROMOTION AUTHORIZATION with actual
release/SQLite/manifest/semantic identities, four-file closure, ledger/counts,
determinism, rollback boundary and exact approval statement. Do not consume it.
