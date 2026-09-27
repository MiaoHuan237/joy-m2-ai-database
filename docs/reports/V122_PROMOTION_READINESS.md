# V1.22 Promotion Readiness — 2019–2022

Technical checkpoint, 2026-09-27. **NOT A PUBLICATION APPROVAL.**
The readiness sections below are historical pre-publication evidence; the final
section records the subsequent explicit human approval and formal publication.
Full maintained gate: 1117/1117 PASS; independent implementation review is closed.
At the readiness checkpoint, no real V1.22 formal directory or query-default
transition had occurred. See the subsequent publication section for current state.

## Locked authority

Design/Plan: 2026-09-27-v122-promotion-readiness, checkpoint `174ee6d`.
Exact-surface test enumeration follow-up: `31b4b35`, independently reviewed.
Engineering baseline: `ac132bb071a90055059adfa0912aa4f97c7d8ba7`.
Independent Design/Plan review: Critical 0 / Important 0 after explicit
human-evidence and dependency-valid RED sequencing clarifications.

Formal production remains V1.21, 591 whole questions:

- SQLite: `93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a`
- Manifest: `a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40`
- Release: `f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3`

Exact generation 000004 candidate:

- Digest: `82b10a551f70eebda2e0aa4d10c962e317767e936b4f0d9aa798629bb8070d46`
- SQLite: `f1adf0ff7c2034445b1ee4724c03e8c66c6026c5e94d37cc469e1b350c2a9a7a`
- Manifest: `dc974a1f3180fc3d7d416385242d21aec78266f4e52f5a9de5732f31d57a5403`
- Directory: `data/staging/task12-v122-hkdse-2022/candidate-generation-000004`
- Receipt: adjacent `REAL_BATCH_IMPORT_RECEIPT.json`.

Ledger is 000001/2019, 000002/2020, 000003/2021, 000004/2022,
each `JOY-M2-HKDSE-<year>-PP-MS`, 12 questions each. Exact preflight/parent
pairs are preserved in Design §2 and reverified through maintained APIs,
not inferred from the receipt. Candidate verifier: 24/24 PASS.

## Actual dry-run identities

Two independent output roots:
`data/staging/task12-v122-promotion-readiness/dry-run-a` and `dry-run-b`.
Both independently verify 21/21 PASS. All four constrained files are
byte-identical, not just semantically equal.

- Release digest: `89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b`
- Semantic digest: `964cceff64cdeaedf663d1f9be98aaaf6adf3ffe2cddf6a18447ea141948a1c4`

| File | Bytes | SHA-256 |
|---|---:|---|
| Joy_M2_Complete_Question_DB_V1_22.sqlite3 | 10510336 | `a474846a5b1d10a0fe48a259522fbb327747319f4a114452bf9f294405d8d9e0` |
| manifest.json | 7915 | `441e00ac1536b959b40b6177bd17a6f14632a287f85145e202a51bcf137ddc8b` |
| SHA256SUMS.txt | 268 | `43d735861736a7bd799d231d44b029855645d3bbc81894ae9326fced685e48c6` |
| rollback.json | 657 | `77da28191e73459e74f36f0417c092843adb8e3288606b4167620068248901ac` |

The 591 inherited records are value-identical. Each of 48 promoted rows
matches its approved candidate except the prescribed publication state;
639 unique whole-question IDs, formal order 1–639, published/selectable new
rows. Historical candidate tables are not counted again. SQLite integrity,
foreign keys, user_version 122, schema and manifest/SHA/file closure PASS.
No standalone image files: approved PDF figure locators remain unchanged.

## Safety and human boundary

Protected-tree fingerprint comparison covers V1.18–V1.21, all four candidate
generations/canonical packages, and all four source/transcription/approval
roots. No source re-transcription, taxonomy, marks or difficulty changes.
Final before/after protected-tree snapshot comparison: byte-for-byte identical.
No actual V1.16 historical ZIP discovery/read/hash was performed.

Only eventual formal target: `releases/V1.22/`, containing the four files
above. It is currently absent. No formal default-query pointer is changed.
Rollback receipt only describes digest-bound removal of that future release
tree; no rollback has run, and candidates/baselines are never rollback targets.

The trusted real lifecycle approval literal remains None. Isolated tests
exercise absent, approved, wrong-identity and no-replace states. Generated
manifest/receipt statements are not human authority.

## Execution evidence

Model RED: 6 FAIL / 0 ERROR; GREEN 6/6, existing model/export gates 46/46.
Independent fixture verifier RED: 3 FAIL / 0 ERROR; GREEN 3/3.
Builder RED: 3 FAIL / 0 ERROR; primitive/build GREEN 9/9.
Publication RED: 3 FAIL / 0 ERROR before publication behavior.
No import/setup failure was used as behavioral RED.

A competing identical output exposed an ownership-cleanup defect; its new
regression failed before adding the V1.22-only successful-rename guard.
Race/lifecycle gate: 5/5 PASS. Historical production modules were not modified.
Existing-target rejection keeps the existing PipelineConfig error family;
the test asserts PipelineError and byte preservation rather than redesigning it.

Independent implementation reviewer: Critical 0 / Important 0 / Minor 0,
including independent temporary-root reproduction and re-verification.
Two initial Important findings were corrected with observed RED→GREEN:
strict recursive JSON types reject self-consistent float/bool authority forgeries;
unreadable SQLite now returns a structured FAIL instead of a native exception.
Verifier remediation: 2 tests / 6 assertion failures / 0 ERROR before correction,
5/5 GREEN afterward. Valid independent fixture remains 21/21 PASS.
Both actual dry-run roots were independently reverified after the corrections.
Historical formal verifiers: V1.19 18/18, V1.20 21/21, V1.21 21/21 PASS.

The first full-suite attempt overlapped staging-writing dry-runs/focused tests;
a historical whole-staging non-mutation assertion detected that interference.
That contaminated run was stopped and is not counted as a passing gate.
The next serial run exposed one omitted historical exact-export assertion:
1117 collected, 1116 PASS, one FAIL, zero ERROR. The Plan enumeration was
corrected in `31b4b35` before appending the approved nine literal names to
`test_v119_writer_models.py`; its full historical prefix remains unchanged.
Independent narrow review: Critical 0 / Important 0 / Minor 0, single test PASS.
The final serialized maintained run: **1117/1117 PASS**, zero failure/error,
skip, expected failure or unexpected success. No historical gate was waived.
Fresh separate promotion focused gate: **34/34 PASS**.
Legacy executable Task 3–6 gates: **54/54 PASS** (13 + 9 + 10 + 22).
V1.18 independent validator: PASS / 497, including hash, integrity and FK checks.
The separate known legacy attribution suite was not rerun; its historical
9 PASS / 2 FAIL is not presented as fresh evidence or a maintained waiver.

Runtime detailed evidence: `data/staging/task12-v122-promotion-readiness/READINESS.json`
and ignored `tmp/pdfs/task12-v122-promotion-readiness/` gate logs.

Final human gate: `USER DECISION REQUIRED — FINAL V1.22 PROMOTION AUTHORIZATION`.
The only proposed approval statement is:

```text
USER APPROVED RELEASE PROMOTION V1.22 89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b
```

This statement is offered for human decision, not recorded as received approval.
No 2023 ingestion, V1.23, real V1.22 promotion or approval consumption.

## Subsequent human-approved publication — 2026-09-27

The user supplied the exact approval statement above. At engineering HEAD
`c5f946b88966447603b77b9ab4186ea14c74d088`, a fresh maintained gate passed
1117/1117 with zero failures/errors/skips/expected failures. The maintained
publisher then consumed the exact typed approval once and atomically created
`releases/V1.22/`; no rebuild, import replay or overwrite was performed.

Independent post-publication verifier: **21/21 PASS**. Candidate: **24/24 PASS**.
The formal four-file tree exactly matches both dry-runs and all hashes listed
above. Formal query count is **639**, inherited V1.21 view remains **591**;
SQLite integrity and foreign keys PASS. All 275 protected files in historical
formal releases, four candidate generations and source/approval roots are unchanged.

Design §6's trusted lifecycle literal is updated from None to the actual
human-approved digest; no logic or production behavior changes. Post-publication
maintained regression: **1117/1117 PASS**, zero failures/errors/skips/expected
failures. Independent publication review: **Critical 0 / Important 0**; the
single documentation-tense Minor was clarified. The raw operational receipt is retained locally at
`tmp/pdfs/task12-v122-promotion-readiness/PUBLICATION_RECEIPT.json`.
The formal manifest contains the migration/provenance/hash evidence and
`rollback.json` records the existing digest-bound rollback boundary. No rollback
or application query-default configuration change occurred. No next batch is started.
