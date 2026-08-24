# Task 8B Completion Evidence

Evidence date: 2026-08-23 (Asia/Shanghai); final delivery synchronized 2026-08-24.

Branch: `task8b/pipeline-migration`

Completion evidence commit: `6969f3d88b00537386212bc91203c837cac58915`

Python: `3.12.13`

Formal release: V1.18, 497 complete-question records (45 retained V1.17 + 452
Task 6).

## 1. Result and authority

Task 8B is `CLOSED / PASS`. The completion evidence is committed, the
post-commit clean-tree checkpoint passed, and the GitHub branch and annotated
tag backup are complete. Maintained V1.17 and V1.18 replay outputs match their
approved protected/frozen authorities, all maintained and frozen gates pass,
and no formal data changed.

Fresh legacy generation is attribution evidence only. Its known SQLite/report
differences remain the approved `9 PASS / 2 FAIL` attribution surface; neither
failure overrides the passing maintained/frozen result, and no third failure
category appeared.

The completion evidence commit is
`6969f3d88b00537386212bc91203c837cac58915`. Its post-commit rerun passed with a
clean working tree, clean staging area, and 0 untracked files.

## 2. Test-first evidence

The initial Task 8 regression collected 3 tests and produced 1 PASS / 2 FAIL,
exit 1. The two failing methods contained only the already adjudicated gaps:

- fresh legacy SQLite/report bytes were incorrectly treated as maintained
  acceptance authority for both profiles;
- maintained V1.17 ZIP entries were incorrectly required to recreate the legacy
  categorized directory layout.

After migrating those assertions to the approved authority hierarchy, the same
command collected 3 tests and produced 3/3 PASS, exit 0, with no skips or
expected failures:

```bash
$task8_python -m unittest -v tests.regression.test_task8b_pipeline_equivalence
```

The regression now locks maintained-to-approved bytes, fresh legacy attribution,
compatibility objects, V1.17/V1.18 end-to-end routing, V1.18's narrow
`audit_passed -> published` SQLite serialization projection, archive closure and
metadata, independent-root determinism, and frozen-tree immutability.

## 3. Core artifact hash authority mapping

Each row is SHA-256. `approved` is the acceptance authority, `maintained` is a
fresh maintained replay, and `fresh legacy` is provenance comparison only.

### V1.17

| Artifact | approved | maintained | fresh legacy | classification |
|---|---|---|---|---|
| `Joy_M2_Complete_Question_DB_V1_17.sqlite3` | `58f32e547c4ff0cdd2ae25a9368ea288cbaa70af52869b779d698233aee93fab` | `58f32e547c4ff0cdd2ae25a9368ea288cbaa70af52869b779d698233aee93fab` | `b7db31f8821ec6d44e1d176f7c87ad0768406cd4032096df77915da7763b8d51` | deterministic SQLite hash attribution |
| `Joy_M2_Complete_Questions_V1_17.csv` | `308728abb9936cd0feb84ac7e30922833b60565a2942656311aa9e23aed1e2ba` | `308728abb9936cd0feb84ac7e30922833b60565a2942656311aa9e23aed1e2ba` | `308728abb9936cd0feb84ac7e30922833b60565a2942656311aa9e23aed1e2ba` | MATCH |
| `complete_questions_45_approved_v1_17.json` | `f8d4ab5db3275308c570ad44c09f5c784267f26c38552193725c683f5fc0edbc` | `f8d4ab5db3275308c570ad44c09f5c784267f26c38552193725c683f5fc0edbc` | `f8d4ab5db3275308c570ad44c09f5c784267f26c38552193725c683f5fc0edbc` | MATCH |
| `differentiation_application_taxonomy_v1_1.json` | `6010077380a772bbf856b9b2ee4ccf970308113005079a06da8486ac0b2c7926` | `6010077380a772bbf856b9b2ee4ccf970308113005079a06da8486ac0b2c7926` | `6010077380a772bbf856b9b2ee4ccf970308113005079a06da8486ac0b2c7926` | MATCH |
| `Joy_M2_微分应用45题_知识文档_V1.17.md` | `b98cd00688cb5cfaf8b89a10f10e5cbdead085a1914e0c874ba6d9004a1a3ee2` | `b98cd00688cb5cfaf8b89a10f10e5cbdead085a1914e0c874ba6d9004a1a3ee2` | `b98cd00688cb5cfaf8b89a10f10e5cbdead085a1914e0c874ba6d9004a1a3ee2` | MATCH |
| `Joy_M2_V1.17_正式入库报告.md` | `cbe8ba91ea9dcca7501408a4bbf480a6c04ba845acf7c94a7d46766e3fddcb31` | `cbe8ba91ea9dcca7501408a4bbf480a6c04ba845acf7c94a7d46766e3fddcb31` | `4cfbfb6b4bcb480dd2d9a7f26f187e611ffb4bc51bf46bbdcfbd9912dd77f803` | frozen artifact byte-equivalence attribution |
| `PROJECT_STATE.md` | `9294622f3c436b8ebfe791f6ccc6f3415b658856896db0eaa14f17577bb805ba` | `9294622f3c436b8ebfe791f6ccc6f3415b658856896db0eaa14f17577bb805ba` | `9294622f3c436b8ebfe791f6ccc6f3415b658856896db0eaa14f17577bb805ba` | MATCH |

### V1.18

| Artifact | approved | maintained | fresh legacy | classification |
|---|---|---|---|---|
| `Joy_M2_Complete_Question_DB_V1_18.sqlite3` | `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7` | `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7` | `9269290f7cbf2f430f919692c6b3da91e2a740ebfb99a5e61f5d31cae17e57e3` | deterministic SQLite hash attribution |
| `Joy_M2_Complete_Questions_V1_18.csv` | `94e4b8060f80c485b6cd4c20d0cd9bbe7c4b0939f289ad38762900f9bceec2c5` | `94e4b8060f80c485b6cd4c20d0cd9bbe7c4b0939f289ad38762900f9bceec2c5` | `94e4b8060f80c485b6cd4c20d0cd9bbe7c4b0939f289ad38762900f9bceec2c5` | MATCH |
| `complete_questions_452_task6_audited.json` | `8cfb90179a0d79db0af86612874536c334191a30a340c70e1bc269d8eae76c83` | `8cfb90179a0d79db0af86612874536c334191a30a340c70e1bc269d8eae76c83` | `8cfb90179a0d79db0af86612874536c334191a30a340c70e1bc269d8eae76c83` | MATCH |
| `task6_audit_report.json` | `e26fd867fb6293d44f59acaaa536c583a651822ae5162c3ea415e282d64f3a84` | `e26fd867fb6293d44f59acaaa536c583a651822ae5162c3ea415e282d64f3a84` | `e26fd867fb6293d44f59acaaa536c583a651822ae5162c3ea415e282d64f3a84` | MATCH |
| `Joy_M2_完整题497题_知识文档_V1.18.md` | `0117cc647bb27f1dcfc3cb6d3d40384e2cfa6cc8ad96a4eaf1848ebc245ecf7f` | `0117cc647bb27f1dcfc3cb6d3d40384e2cfa6cc8ad96a4eaf1848ebc245ecf7f` | `0117cc647bb27f1dcfc3cb6d3d40384e2cfa6cc8ad96a4eaf1848ebc245ecf7f` | MATCH |
| `Joy_M2_V1.18_正式入库报告.md` | `cabd7e4b5127bb8b999f8147458440901d491897376789e9c61e3ea4e5e6de0b` | `cabd7e4b5127bb8b999f8147458440901d491897376789e9c61e3ea4e5e6de0b` | `1a7ddfa76155a9d7567c3daee344238348e3b1c1e3235098c1d0b2655e43b87b` | frozen artifact byte-equivalence attribution |
| `PROJECT_STATE.md` | `a6ee879f5d432491cc5dd639abe485090d4cd63bc0ddc2d3376f503af0e63f09` | `a6ee879f5d432491cc5dd639abe485090d4cd63bc0ddc2d3376f503af0e63f09` | `a6ee879f5d432491cc5dd639abe485090d4cd63bc0ddc2d3376f503af0e63f09` | MATCH |

## 4. Compatibility objects and package closure

The regression constructs local, non-production compatibility objects from only
the approved identity, release version, maintained artifact mapping, protected
manifest hashes, and historical scalars.

- V1.17 identity: `V1.17`, `candidate`, `complete-question-v1.0`.
- V1.17 historical scalars: baseline SQLite
  `d647244f54e9e54b25ec4885f16c47171c7521552876a5fa925a16d65d8c7714`,
  Task 4 candidate
  `5145b3da050d510cf6cf052a66cddf20ce2939ae3879618d3341f8399f48b97d`,
  and the approved missing-archive compatibility constant
  `5f73f541f5c2da5bf3e5540daf7dbfb40566a339eaee79ef3e25d8eabd0404ae`.
- V1.18 identity: `V1.18`, `candidate`, `complete-question-v1.0`.
- V1.18 historical scalar: baseline V1.17 SQLite
  `58f32e547c4ff0cdd2ae25a9368ea288cbaa70af52869b779d698233aee93fab`.
- Fresh legacy bytes are absent from both compatibility objects.

The two independent maintained builds produced identical ZIP hashes:

- V1.17: `3da6cff55d586c5cc3acd1bc600eeb7706027f145915febea4295ff19c9491a9`.
- V1.18: `99387b7f379f1081ccf2e0adc33289a2889117d1f2f8e7983435f8fe1ecb4666`.

Every ZIP entry is exactly
`ReleaseContract.archive_root/<candidate-root-relative-path>`, the file set
equals the declared candidate artifacts, names are sorted, timestamps are
`1980-01-01 00:00:00`, Unix modes are `0644`, `create_system` is 3, and
compression is DEFLATE. The legacy V1.17 categorized `01_数据/`, `02_知识文档/`
layout remains historical attribution only and is not reconstructed.

## 5. Commands and results

`$task8_python` is:

```text
/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

| Gate | Result | Exit |
|---|---:|---:|
| Explicit complete maintained suite | 195/195 PASS | 0 |
| Public Models | 66/66 PASS | 0 |
| Models + Config | 80/80 PASS | 0 |
| Audit | 21/21 PASS | 0 |
| Task 3A | 6/6 PASS | 0 |
| Database | 14/14 PASS | 0 |
| Export | 22/22 PASS | 0 |
| Export + Database | 36/36 PASS | 0 |
| Release focused | 48/48 PASS | 0 |
| Task 7 | 7/7 PASS | 0 |
| Task 8 completion | 3/3 PASS | 0 |
| Task 3 legacy gate | 13/13 PASS | 0 |
| Task 4 legacy gate | 9/9 PASS | 0 |
| Task 5 legacy gate | 10/10 PASS | 0 |
| Task 6 legacy oracle | 22/22 PASS | 0 |
| Task 3-6 total | 54/54 PASS | 0 |
| V1.18 independent validator | PASS; 497/452/45, integrity ok, 0 FK errors | 0 |
| Legacy attribution suite | 9 PASS / 2 FAIL | 1 (approved attribution baseline) |

All passing unittest gates reported 0 skips and 0 expected failures. The two
legacy attribution failures were exactly:

1. `Task5LegacyBehaviorTests.test_build_is_deterministic_and_matches_reviewed_core_hashes`
   — deterministic SQLite hash attribution.
2. `Task6LegacyBehaviorTests.test_build_matches_all_seven_frozen_primary_artifacts`
   — frozen artifact byte-equivalence attribution.

No third failure appeared. The plan's broad discovery command was also executed;
because the current test subdirectories are namespace-style directories, it
reported `Ran 0 tests`. The explicit ten-module command above is the actual
complete maintained collection and passed 195/195.

## 6. Frozen and historical boundaries

- `releases/V1.18/` remained byte-for-byte unchanged before and after all builds.
- `data/baselines/V1.18/` remained byte-for-byte unchanged before and after all
  builds.
- The V1.18 independent verifier passed with 497 complete questions, including
  45 retained V1.17 and 452 Task 6 records.
- Compatibility tables and views remain present; logical digests of `questions`,
  `sources`, `topics`, and `question_topics` match their frozen input databases.
- V1.17 uses an explicit release decision; V1.18 uses no V1.17 decision.
- V1.18 audit carriers retain `audit_passed`; only frozen SQLite serialization
  persists `published`.
- The actual missing V1.16 ZIP was not searched, read, or rehashed. The maintained
  request/evidence has no archive carrier, and the manifest scalar comes only
  from the approved historical constant.
- No formal candidate was promoted and no file under `data/`, `releases/`, or
  `legacy/` was modified.

## 7. Remaining boundaries

- CLI and consumer migration are not implemented.
- Task 8C is `NOT STARTED — PENDING EXPLICIT AUTHORIZATION`.
- Branch backup is `COMPLETE`: `origin/task8b/pipeline-migration` and the local
  branch both point to `6969f3d88b00537386212bc91203c837cac58915`.
- Annotated tag backup is `COMPLETE`:
  `joy-m2-task8b-closed-20260824` points to the same commit.
- Post-commit clean-tree checkpoint: `PASS`; working tree and staging are clean,
  with 0 untracked files.
- Pull request creation, merge, formal promotion, and legacy removal were not
  performed.
- No next implementation task is authorized. The next action is
  `WAIT FOR EXPLICIT NEXT-TASK AUTHORIZATION`; any future stage must first
  establish new Design / Plan authority before implementation.

## 8. Conclusion

`TASK 8B VERIFICATION — PASS`

Status: `TASK 8B — CLOSED / PASS`.

Post-commit clean-tree checkpoint: `PASS`.

GitHub backup: `COMPLETE`.
