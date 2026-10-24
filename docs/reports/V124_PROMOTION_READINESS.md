# V1.24 Promotion Readiness — generation000008

2026-10-24。状态：**技术准备完成，等待最终精确 promotion 批准**。
尚未正式发布；当前正式库仍是V1.23/677。本次未调用真实candidate writer、
未续期入库委托、未处理81个待核实或8个前置复习单元。

## 固定输入与批准链

- 候选根：`data/staging/vector-ch12-v124-S08-delegated-20261024-000001/candidate-generation-000008`
- Candidate digest：`3f14589da452207d0088cd44689aded7ffbadea0768a85d808a67ae526a5f3ab`
- Candidate SQLite：`Joy_M2_V1.24_candidate.sqlite3`，11378688bytes，
  SHA `93acb2b4c333c4cb881c327389569898ab110ab2f436f00f1d40586e0ed4f8a0`
- Candidate manifest：676520bytes，
  SHA `34cd37e27370a72e332d7047d9699d3910d853e1276132ce33ec26df4786de94`
- Baseline V1.23：677，schema `task13-v123-formal-v1`；
  SQLite SHA `28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd`；
  release digest `84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc`；
  manifest SHA `54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498`。

每个批次ID共同前缀为 `JOY-M2-OSM-M2B12-VECTOR-20261023-001-`：

| suffix | 条数 | 实际入库授权类型 |
|---|---:|---|
| S01 | 16 | 用户精确 import 批准 |
| S02 | 14 | 用户精确 import 批准 |
| S03 | 4 | 用户精确 import 批准 |
| S04 | 14 | 本章委托执行决定 |
| S05 | 11 | 本章委托执行决定 |
| S06 | 32 | 本章委托执行决定 |
| S07 | 20 | 本章委托执行决定 |
| S08 | 3 | 本章委托执行决定 |

合计114；顺序及genesis/parent链不变。S04来源映射仍绑定用户实际发送的
14题精确批准；S05–S08来源/入库决定如实为delegated。
历史独立candidate verifier **24/24 PASS**，八批存储载体及原回执回放一致。
按既有historical/live=False合同核验当时来源、范围、集合、parent与决定；
scope完成标记只禁止后续执行，不追溯撤销以前有效接受。本轮未创建任何新决定。

## 实际双dry-run与正式等价查询

非正式根：
- `data/staging/v124-promotion-readiness/20261024-000001/dry-run-a`
- `data/staging/v124-promotion-readiness/20261024-000001/dry-run-b`

两根全部**76文件逐字节一致**，并非仅语义或题数相同。
各自独立formal verifier **22/22 PASS**；恢复副本另22/22 PASS。

- **677+114=791**，`formal_complete_questions_v124` 返回791个唯一ID，
  全部published/selectable（仅非正式等价输出中的状态）。
- baseline677行逐字段一致；新增114行与已批准candidate逐字段一致，
  仅执行合同规定的发布状态、selectable及正式投影变化。
- 八批查询计数分别16/14/4/14/11/32/20/3。
- 未将继承的历史candidate tables重复计入正式view。
- 791是记录数，不是全库去重后的独立原题数。正式新增记录目前仍为0，
  只有最终批准并成功发布后才成为正式V1.24内容。

## 图片与来源覆盖

72个实际原图JPEG，合计833787bytes，分布于56条新记录。
有序角色绑定：question54、solution18。原始图像SHA、角色、来源映射、
输出相对路径、声明集合及完整artifact closure均核验。
所有72图在dry-run及恢复副本内解码成功，不依赖旧staging图片定位。

实际查看恢复图：EX12A-Q03五边形题图、QUIZ12-Q01合成向量题图及(a)解答图；
与对应完整题及小问/来源答案角色一致。全114条正文/答案逐字段核验，
另抽查共享条件EX12A-Q09、位置/分点EX12B-Q03、单位/模长EX12C-Q08、
空间加减EX12C-Q09、平行Q17、共线Q18及外心SUP12-Q20。
这不是再次宣称全章数学转录逐题复审通过。

历史677条中已有图片引用保持原样；不为本轮重打包无关历史图片，
不将新72图闭合结论扩大成所有历史引用已本地化。

来源答案：114条均source_provided；canonical source-coverage如实为
**110 worked_solution、4 final_answers_only**，其中图形构造解不是新增文字详解。
仅最终答案的ID：
- `OSM-M2B12-C-EX12A-Q01`
- `OSM-M2B12-C-EXAMPLE-Q01`
- `OSM-M2B12-C-DRILL-Q01`
- `OSM-M2B12-C-PUBLIC-Q01`

独立explanation为missing114；difficulty为NULL114，未估填。
分值保留原文及原始证据，不发明当前schema中不存在的marks列。
出版者教材解答不标作HKEAA官方MS。原MMD排版/list wrappers、已披露的
非必要插图限制等保持；此发布不承诺原MMD本身可直接作为完整LaTeX编译。

现有exact标签查询（允许同题多标签，不能相加作题数）：

| 标签 | 新增114内匹配数 |
|---|---:|
| circumcenter | 1 |
| coefficient-comparison | 12 |
| collinear | 8 |
| parallel | 20 |
| plane-vector | 53 |
| section-formula | 47 |
| space-vector | 23 |
| unit-vector | 11 |
| vector | 114 |
| 向量基础知识 | 45 |

加减、位置、模长未另造新标签；其存在由上述正文抽查确认，
不把“没有独立标签”误报成“没有相关题”。未更改分类来制造命中。

## 验证与独立复审

- 最终V124专项：**30/30 PASS**，36.720s。
- 新鲜串行合并执行：78modules/1607tests，1605PASS、2FAIL，
  errors/skips/expected-failures均0，906.803s。
- 按既有维护集合分开核算：**77modules/1596 maintained tests全部PASS**。
- 唯一历史归因模块 `tests.regression.test_task8b_legacy_pipeline_behavior`：
  **9PASS/2knownFAIL**，Task5 SQLite冻结字节hash、Task6冻结artifact字节重建。
  这两项已在起始HEAD之前的PROJECT_STATE、V123 readiness和vector Plan明确单列。
  本次未增加排除、跳过、改断言、改旧hash；完整失败证据保留。
  不能称1607/1607通过，也不将此旧归因规则套用于V124字节一致性。
- 四组旧版本可执行回归：22+10+13+9=**54/54 PASS**。
- V1.18 validator：PASS，497记录、完整性/FK/全部hash检查通过。
- 历史V1.19–V1.23 formal verifiers、批准来源、API及回放包含在维护测试内。
- Design/Plan独立复核完成；实现独立复核最终 **Critical0/Important0/Minor0**。
  独立reviewer实际复跑原28项和2项清理竞态，最终30项由主执行者重跑；
  不把作者结果伪称reviewer亲自执行。
- 复审关闭：核验后源快照变化必须在rename前拒绝；parsed-invalid
  JSON surrogate图片路径返回结构化FAIL。两项均有有效RED→GREEN。
- 独立reviewer逐条复核1607项结果，并在原始起始提交核实历史归因界线。
- 初次整轮因并发focused临时staging触发旧全目录不变性检查，主动中止；
  不计作通过。之后所有生成完成后重新严格串行，得到上述实际结果。
- 943个受保护输入/正式文件在dry-run、恢复及最终测试后SHA不变；
  用户AGENTS SHA仍
  `75ffa9680b18a0875fde8d36a8ca3e0ebda0603f10e8dc788e71ea8353d0311d`，
  未暂存/提交。现有正式V1.18–V1.23、原双包、旧candidate及批准证据不变。

22项formal检查：
- `release_directory`: PASS
- `promotion_contract`: PASS
- `candidate_verification`: PASS
- `candidate_binding`: PASS
- `manifest_contract`: PASS
- `filesystem_closure`: PASS
- `sha256sums_closure`: PASS
- `artifact_references`: PASS
- `rollback_contract`: PASS
- `sqlite_readability`: PASS
- `sqlite_integrity`: PASS
- `sqlite_foreign_keys`: PASS
- `sqlite_schema`: PASS
- `v123_preservation`: PASS
- `batch_ledger_closure`: PASS
- `promotion_projection`: PASS
- `formal_query`: PASS
- `count_closure`: PASS
- `provenance_closure`: PASS
- `deterministic_identity`: PASS
- `publication_boundary`: PASS
- `image_projection`: PASS

## 真实发布身份与最终批准

Release digest：`52f0fb8b88ad9abdf64968336b9244da11d67904fcd46c7929e5139d74fc6273`

正式等价SQLite SHA：`c43479ea211ac4e93b7a325c80042816858f0b585b6a7be763f758e62a1c8da6`

SQLite语义SHA：`2e0c4e47de59d0a6c005f4aeddb34055099061dbe75e7d9bc4a4cd310566e20f`
Manifest SHA：`b59b69a86a8c8a59feff51af4b15f52c5bdb86113b3415015dff6f6ce088009b`

唯一待创建正式根：`releases/V1.24/`。
**本次确认该目录仍不存在，从未为测试先发布再删除。**

以下只是请用户发送的批准模板，**不是已经收到的批准**：

```text
USER APPROVED RELEASE PROMOTION V1.24 52f0fb8b88ad9abdf64968336b9244da11d67904fcd46c7929e5139d74fc6273
```

执行时仍须重新验证固定输入、dry-run字节及精确批准，不消费变化后的旧身份。
rollback声明仅允许目标release digest精确匹配时移除该release tree，
保护V1.23/677及原candidate；本轮不执行rollback。
没有调整持久化查询默认版本或current pointer。

## 本地备份、代码与运行证据

主数据归档：
`dist/backups/v124-promotion-readiness-20261024-000001.zip`，
212365073bytes，
SHA `068c25e3f8b84e2ccb7d3b88a2af1ad8eaf082e0a13ef3a65ad45b99d139a798`。
**1110个明确文件**已校验并恢复；包含两份dry-run、受保护输入、
双包、canonical、批准/委托证据及实现/审阅资料。
恢复的76个发布文件与原输出字节一致；72图解码、独立formal22/22 PASS。
历史verifier仍使用其原固定绝对证据路径；归档包含原证据字节，
但不声称已测试离线重定位全部历史批准路径。

最终门禁日志/报告另沿同一显式归档机制补存；其实际结果见同根
`FINAL_EVIDENCE_BACKUP.json`，Git实际同步结果见`GIT_SYNC.json`。
以上都是**本地备份，不是异地备份**；Git只备份工程/docs，不等于ignored数据备份。

实现提交：36c4a2f（scope/plan）、5d901f5（models/scaffold）、
3510abc6c11213cccbb952680815540732507540（builder/verifier/tests）。
最终文档提交及远端状态以实际Git读回和上述运行记录为准，不预填未发生的push成功。

运行证据根：
`data/staging/v124-promotion-readiness/20261024-000001/`：
PINNED_INPUT、READINESS、QUERY_CONTENT_EVIDENCE、PROTECTED_BEFORE、
INDEPENDENT_REVIEW、BACKUP_RESTORE、FINAL_GATES。
原始测试日志：
`.superpowers/sdd/2026-10-24-v124-promotion-readiness/`。
无新依赖、调度器、来源adapter、版本框架或package-root export。

## 完整正式artifact清单（76文件）

下列路径全部相对于待创建的 `releases/V1.24/`。
SHA256SUMS自身SHA在此外部闭包中列出；不要求文件自包含自身hash。

| 相对路径 | bytes | SHA-256 |
|---|---:|---|
| `Joy_M2_Complete_Question_DB_V1_24.sqlite3` | 11706368 | `c43479ea211ac4e93b7a325c80042816858f0b585b6a7be763f758e62a1c8da6` |
| `SHA256SUMS.txt` | 11212 | `2859f9b68a1f234498dcce5219319d458faebdc420f5d0132d437ce531ae869d` |
| `images/sha256/00/0047cf8ea9e6b69a348e091fa63abd464efa4398db02b9e29580317afabff34e.jpg` | 11231 | `0047cf8ea9e6b69a348e091fa63abd464efa4398db02b9e29580317afabff34e` |
| `images/sha256/01/0152cb2d7f9c2224276578f3696be620221beb9d8afb2aff747528772506aee6.jpg` | 6199 | `0152cb2d7f9c2224276578f3696be620221beb9d8afb2aff747528772506aee6` |
| `images/sha256/03/03dddc2edc7b70e8b3537d07b0bd23ef8d8d379db42739f3e037a2859b52c7d6.jpg` | 10916 | `03dddc2edc7b70e8b3537d07b0bd23ef8d8d379db42739f3e037a2859b52c7d6` |
| `images/sha256/04/0426e930fd328228bb3441a420adeca7a3c99220c7b73b6436518bbb560c85ee.jpg` | 9013 | `0426e930fd328228bb3441a420adeca7a3c99220c7b73b6436518bbb560c85ee` |
| `images/sha256/0a/0a8e0a3846a4530aaed3d14ea665823a5eec5382faa112464e5b0402fb95b718.jpg` | 13137 | `0a8e0a3846a4530aaed3d14ea665823a5eec5382faa112464e5b0402fb95b718` |
| `images/sha256/0b/0bd17703fb0181644574b0ee2a622543af668c1235a85f374962720a4d4bb2aa.jpg` | 9979 | `0bd17703fb0181644574b0ee2a622543af668c1235a85f374962720a4d4bb2aa` |
| `images/sha256/16/162638f111e181f309fce0c8fb0b52a534268012edcd3ce8e0cb3cd54dfefd40.jpg` | 10929 | `162638f111e181f309fce0c8fb0b52a534268012edcd3ce8e0cb3cd54dfefd40` |
| `images/sha256/17/17d5788ab41a8af935f19dda8c7b3975d3dede2ef35bc7976f3500187cf82c1b.jpg` | 11255 | `17d5788ab41a8af935f19dda8c7b3975d3dede2ef35bc7976f3500187cf82c1b` |
| `images/sha256/1d/1d65cc539ae869f84fdb1cdc1d6a0ae416f9ad30805a66e0a1e7c4946dc0258b.jpg` | 10973 | `1d65cc539ae869f84fdb1cdc1d6a0ae416f9ad30805a66e0a1e7c4946dc0258b` |
| `images/sha256/1e/1e93e494e49eaa982be7823e06e4e320ad05480fa1cb1932c86d9c60ec19b2ab.jpg` | 12915 | `1e93e494e49eaa982be7823e06e4e320ad05480fa1cb1932c86d9c60ec19b2ab` |
| `images/sha256/28/28c75ff3c0c858022f08ffee8d4c8deb7113861341ae01692ed06b766aaa2d07.jpg` | 38353 | `28c75ff3c0c858022f08ffee8d4c8deb7113861341ae01692ed06b766aaa2d07` |
| `images/sha256/2d/2ddfa8cc6d7b67e355339f77978bbe2e35a6131a5ec7c8cb9d0ef9abfb9ad3a7.jpg` | 10092 | `2ddfa8cc6d7b67e355339f77978bbe2e35a6131a5ec7c8cb9d0ef9abfb9ad3a7` |
| `images/sha256/32/3272896097a8c1bcf63b2318f96643564e3f45214d234c7add9917550b4c065f.jpg` | 14783 | `3272896097a8c1bcf63b2318f96643564e3f45214d234c7add9917550b4c065f` |
| `images/sha256/33/338001bc38d986aa461907e6316d7b116495d134a174cfa2cba7747c76d9f541.jpg` | 9680 | `338001bc38d986aa461907e6316d7b116495d134a174cfa2cba7747c76d9f541` |
| `images/sha256/37/3711388e91f38e6f4c355d172122937aad9454b754a7d18835b5829fed9e61bd.jpg` | 11972 | `3711388e91f38e6f4c355d172122937aad9454b754a7d18835b5829fed9e61bd` |
| `images/sha256/38/383b9f04e5a611bbe50a8aba9720588ab7bb573d5228dac0e43d84ae55798783.jpg` | 8809 | `383b9f04e5a611bbe50a8aba9720588ab7bb573d5228dac0e43d84ae55798783` |
| `images/sha256/3e/3e7f96c9426b11c7431275b7090f2bf288a0dd175539b173a26b84a497bb9f52.jpg` | 14646 | `3e7f96c9426b11c7431275b7090f2bf288a0dd175539b173a26b84a497bb9f52` |
| `images/sha256/3f/3f8c3363993eb294f618a53cd8b7adffe0ceb5944cf7443ad8b5e40f86e76ef1.jpg` | 14309 | `3f8c3363993eb294f618a53cd8b7adffe0ceb5944cf7443ad8b5e40f86e76ef1` |
| `images/sha256/40/4040ef6f5a67a7703f01f7e277cefc689f5f4050b5338c503da501eb115e3358.jpg` | 15600 | `4040ef6f5a67a7703f01f7e277cefc689f5f4050b5338c503da501eb115e3358` |
| `images/sha256/44/4496650a142e088302a26d070cb0606db964ea9e781d34a7f146e3e19c375408.jpg` | 8542 | `4496650a142e088302a26d070cb0606db964ea9e781d34a7f146e3e19c375408` |
| `images/sha256/4d/4d66159f416ee28c376640bdf0b863849b3dbef1b0e795fd9e31b5750e477953.jpg` | 11348 | `4d66159f416ee28c376640bdf0b863849b3dbef1b0e795fd9e31b5750e477953` |
| `images/sha256/53/53e026b97513ec7e09b2e3018b8d6bb5baa514c73989e552757f9c0be1061cee.jpg` | 21763 | `53e026b97513ec7e09b2e3018b8d6bb5baa514c73989e552757f9c0be1061cee` |
| `images/sha256/54/541aae23732cf858d09a65e987babff4b808fdf3b754816a419b54c22ea3d7ea.jpg` | 11868 | `541aae23732cf858d09a65e987babff4b808fdf3b754816a419b54c22ea3d7ea` |
| `images/sha256/54/54e9b3fdae51c17a1c1159fec5be0a0e32a46ac1885d3d2984a92cce2dc1a7f0.jpg` | 7769 | `54e9b3fdae51c17a1c1159fec5be0a0e32a46ac1885d3d2984a92cce2dc1a7f0` |
| `images/sha256/59/597b7cedc8f3aca1dd0d03eb7cfa1277cc74d0c6a0b51324da7ccec77d7ebb93.jpg` | 3533 | `597b7cedc8f3aca1dd0d03eb7cfa1277cc74d0c6a0b51324da7ccec77d7ebb93` |
| `images/sha256/60/600caeb5baa02a631a1092caba3745150240a5bc5b73ee441ebd0fbd2356cafc.jpg` | 14017 | `600caeb5baa02a631a1092caba3745150240a5bc5b73ee441ebd0fbd2356cafc` |
| `images/sha256/61/61e1e99b8f5866ee25b672e56e4af3b262cc5da37972368e7d52b0b52943537f.jpg` | 8665 | `61e1e99b8f5866ee25b672e56e4af3b262cc5da37972368e7d52b0b52943537f` |
| `images/sha256/67/67ceff51dd6744ac94c9edf850f27b1108b38e24076a47795f609ba08a0008ee.jpg` | 9377 | `67ceff51dd6744ac94c9edf850f27b1108b38e24076a47795f609ba08a0008ee` |
| `images/sha256/6c/6c291c32dbd5740908886984024788842efde15a445f23e43d388a81f88927f4.jpg` | 11496 | `6c291c32dbd5740908886984024788842efde15a445f23e43d388a81f88927f4` |
| `images/sha256/70/70425215407e87caa30317b5b3ac590936a095c018785c6b5199c274931e2bd9.jpg` | 11081 | `70425215407e87caa30317b5b3ac590936a095c018785c6b5199c274931e2bd9` |
| `images/sha256/76/76cf3c324e6eef5223a759fd26ed8421db08d4f36215dcb1d665005ed7e34d96.jpg` | 9649 | `76cf3c324e6eef5223a759fd26ed8421db08d4f36215dcb1d665005ed7e34d96` |
| `images/sha256/78/782bd21025c25dc83a3de6ef694aae1f469049f0fda97503220c660cf56670e7.jpg` | 7383 | `782bd21025c25dc83a3de6ef694aae1f469049f0fda97503220c660cf56670e7` |
| `images/sha256/79/792db0693dbec160082c93a92f26f359bd9d2d9c7bafcfea5fb109fe47c8f660.jpg` | 14587 | `792db0693dbec160082c93a92f26f359bd9d2d9c7bafcfea5fb109fe47c8f660` |
| `images/sha256/79/79cb9a2406a41adc6eebd9e865c71a55d84e2fe44b17ebf451a236b7e9c1572f.jpg` | 10960 | `79cb9a2406a41adc6eebd9e865c71a55d84e2fe44b17ebf451a236b7e9c1572f` |
| `images/sha256/7f/7f2b079dda12df3a92123ed45f97ac85a4f4e9bdf30e6f0e45bbde5c3726f4e0.jpg` | 10787 | `7f2b079dda12df3a92123ed45f97ac85a4f4e9bdf30e6f0e45bbde5c3726f4e0` |
| `images/sha256/86/863ddafb1a91c19a25df7c37e864f00a88f68629361908909accc1fe17e635f9.jpg` | 20737 | `863ddafb1a91c19a25df7c37e864f00a88f68629361908909accc1fe17e635f9` |
| `images/sha256/86/864dc59902ca8f5e8349aa1a51a64ddbd4a8c2486b91ac39977c606bac05e2a9.jpg` | 10369 | `864dc59902ca8f5e8349aa1a51a64ddbd4a8c2486b91ac39977c606bac05e2a9` |
| `images/sha256/89/8917cd9bd9c0da356fbd54f72cac0dc8953e2eff1e8ce582aec7a4a001f13fc4.jpg` | 11628 | `8917cd9bd9c0da356fbd54f72cac0dc8953e2eff1e8ce582aec7a4a001f13fc4` |
| `images/sha256/8c/8c1a0faff106204f86ea5a56d3b48c0ddcfebb9a1a5df45497b7444c5510c01e.jpg` | 12420 | `8c1a0faff106204f86ea5a56d3b48c0ddcfebb9a1a5df45497b7444c5510c01e` |
| `images/sha256/8c/8c7931a56354f1b62b3b80079826cec353047b75c4b7fb81ec9a88f34ff24e4e.jpg` | 12557 | `8c7931a56354f1b62b3b80079826cec353047b75c4b7fb81ec9a88f34ff24e4e` |
| `images/sha256/96/969c851e229e3c81383dafe51830a34bedddec88bb14b4387b1e0fca6c08926d.jpg` | 12437 | `969c851e229e3c81383dafe51830a34bedddec88bb14b4387b1e0fca6c08926d` |
| `images/sha256/9a/9aba15c447105617e5f9b386b93ef14017b0c8d73a8df3a8e7c30cd1941f1cac.jpg` | 14892 | `9aba15c447105617e5f9b386b93ef14017b0c8d73a8df3a8e7c30cd1941f1cac` |
| `images/sha256/9c/9cbf1098c9d57ff414fc1edb1c20b94770ed7aa758b606c1a008a86a920524d0.jpg` | 10992 | `9cbf1098c9d57ff414fc1edb1c20b94770ed7aa758b606c1a008a86a920524d0` |
| `images/sha256/a1/a1d8832a505234772441f30402d0d9e1ed7b8a750078c4a76fdc877396718a75.jpg` | 10875 | `a1d8832a505234772441f30402d0d9e1ed7b8a750078c4a76fdc877396718a75` |
| `images/sha256/aa/aa799a8dfa59e9ab75fcb0226e8ac5d57fb0d559a89a55973a303ad81df1a957.jpg` | 11704 | `aa799a8dfa59e9ab75fcb0226e8ac5d57fb0d559a89a55973a303ad81df1a957` |
| `images/sha256/ab/ab174d411de3ffc3ac0836f5ad9b95fb5a242951f158a8ec43bbef076d9e7e9b.jpg` | 10400 | `ab174d411de3ffc3ac0836f5ad9b95fb5a242951f158a8ec43bbef076d9e7e9b` |
| `images/sha256/ac/ac44db43e66ddb996a4c3f03ce46422917bbf5853ff3789fd42e1ec76dcc9c9d.jpg` | 10002 | `ac44db43e66ddb996a4c3f03ce46422917bbf5853ff3789fd42e1ec76dcc9c9d` |
| `images/sha256/ae/ae6b836cc6f772f4afa8bf7ef8a28eb43ef6e5404f9d5e23fef9ea28b4aa798c.jpg` | 12087 | `ae6b836cc6f772f4afa8bf7ef8a28eb43ef6e5404f9d5e23fef9ea28b4aa798c` |
| `images/sha256/b2/b20de90c406373c7a97ee521851ff89dcdf76bf4c1717aa550d8feca6cc1477b.jpg` | 7752 | `b20de90c406373c7a97ee521851ff89dcdf76bf4c1717aa550d8feca6cc1477b` |
| `images/sha256/b6/b60abb9e4465f692cb22f0bbfd28402933c4d34959040d171171fc71d84490ec.jpg` | 9716 | `b60abb9e4465f692cb22f0bbfd28402933c4d34959040d171171fc71d84490ec` |
| `images/sha256/b8/b820cb592b2b359a33044fc4215f3d6d442900391085518f27449257bde10aa5.jpg` | 11393 | `b820cb592b2b359a33044fc4215f3d6d442900391085518f27449257bde10aa5` |
| `images/sha256/bb/bbf6f9a9bc24cdfcfc44ec015b96a140a5fb6d4b84f1c3234e5cd5285e485e3e.jpg` | 11662 | `bbf6f9a9bc24cdfcfc44ec015b96a140a5fb6d4b84f1c3234e5cd5285e485e3e` |
| `images/sha256/be/be8e31b95c5f68029550ab876b00e7cdc78a4e6c5450fc8b0e0d3207604ae07c.jpg` | 12823 | `be8e31b95c5f68029550ab876b00e7cdc78a4e6c5450fc8b0e0d3207604ae07c` |
| `images/sha256/c0/c0c1ae294f1418b9b6c327215b3f57cf5243a12f4905cb3c1c96e727716f61af.jpg` | 11911 | `c0c1ae294f1418b9b6c327215b3f57cf5243a12f4905cb3c1c96e727716f61af` |
| `images/sha256/c2/c2d5093dbcabc74dcb825852277e3d3541552fed164a102500905250c7a7775a.jpg` | 11383 | `c2d5093dbcabc74dcb825852277e3d3541552fed164a102500905250c7a7775a` |
| `images/sha256/c4/c402f6aa03d2dbae519a88e1af05abd81194b89b7be2afcc0d4d0d07841d04e6.jpg` | 5026 | `c402f6aa03d2dbae519a88e1af05abd81194b89b7be2afcc0d4d0d07841d04e6` |
| `images/sha256/c4/c46d301c9a161bcb2e71190936139024667cd94167d13946607d6d958e6a1a60.jpg` | 10919 | `c46d301c9a161bcb2e71190936139024667cd94167d13946607d6d958e6a1a60` |
| `images/sha256/cd/cd9854ead9af09002f78347c114f13c8eb8f575f096bace629ef391ca875a634.jpg` | 13046 | `cd9854ead9af09002f78347c114f13c8eb8f575f096bace629ef391ca875a634` |
| `images/sha256/ce/ce0b519cc96edf075da8473f3aad1e4dc2783fcbd884937b77cc7d3fbd437ea4.jpg` | 9313 | `ce0b519cc96edf075da8473f3aad1e4dc2783fcbd884937b77cc7d3fbd437ea4` |
| `images/sha256/d4/d47d9c07e133939fe0ee469a23e3f6cd8dfdb4be42916436c5ae4b8a27d2a90d.jpg` | 13938 | `d47d9c07e133939fe0ee469a23e3f6cd8dfdb4be42916436c5ae4b8a27d2a90d` |
| `images/sha256/d7/d78cae2ca911159dfc166a6b6f15b6edfecf4f523c90fb0ebbf01cb37d7da4d4.jpg` | 9038 | `d78cae2ca911159dfc166a6b6f15b6edfecf4f523c90fb0ebbf01cb37d7da4d4` |
| `images/sha256/da/dad2cb05a18675369c554a9eb88d0ee76a48b6536217122f4ccf2b8976cc88de.jpg` | 9009 | `dad2cb05a18675369c554a9eb88d0ee76a48b6536217122f4ccf2b8976cc88de` |
| `images/sha256/e0/e06e989676b5c939ba28abf494ac0b6d6e2815ad4b9581e349ec2e109bb29911.jpg` | 9918 | `e06e989676b5c939ba28abf494ac0b6d6e2815ad4b9581e349ec2e109bb29911` |
| `images/sha256/e2/e2583dff090c737bcc6c06725e5562fb6e4b794e152a7802d1603d7bee07415e.jpg` | 4538 | `e2583dff090c737bcc6c06725e5562fb6e4b794e152a7802d1603d7bee07415e` |
| `images/sha256/e7/e712a959daba0d19a963cd8ca677351ace5a944389326d3e07584b14ad77af39.jpg` | 14567 | `e712a959daba0d19a963cd8ca677351ace5a944389326d3e07584b14ad77af39` |
| `images/sha256/ea/ea0103149984f25f8a7dd2224457926a7f5e680ecfa0aec2a5b29183e48810ca.jpg` | 13307 | `ea0103149984f25f8a7dd2224457926a7f5e680ecfa0aec2a5b29183e48810ca` |
| `images/sha256/ea/ea548ed63e14647f3f86d4b9747a13e356acfe8a3690da082cb7f1b538896767.jpg` | 12452 | `ea548ed63e14647f3f86d4b9747a13e356acfe8a3690da082cb7f1b538896767` |
| `images/sha256/f0/f0e88c0b3e336ea5df6e43293cf88058e59a1216c0ba82ad957182fb713dc8e6.jpg` | 10288 | `f0e88c0b3e336ea5df6e43293cf88058e59a1216c0ba82ad957182fb713dc8e6` |
| `images/sha256/f2/f2fb2b6255192d7d60cc5bf313d1db78785ca47ac4d547c6fae1d0ee8d738f3c.jpg` | 10334 | `f2fb2b6255192d7d60cc5bf313d1db78785ca47ac4d547c6fae1d0ee8d738f3c` |
| `images/sha256/f4/f452d40394c330d33552c733f466df0fa75544e9d2d4cd1b47f94e40952b2bd3.jpg` | 12825 | `f452d40394c330d33552c733f466df0fa75544e9d2d4cd1b47f94e40952b2bd3` |
| `images/sha256/f6/f6292d2c6f1e89fb2ed0973784e90cb0907e38558132c7c65df4d075456407fe.jpg` | 14909 | `f6292d2c6f1e89fb2ed0973784e90cb0907e38558132c7c65df4d075456407fe` |
| `images/sha256/fd/fd4d87abbfdd2cef840020e34a15a72f9ab481adf48a872a683b70a6831eb928.jpg` | 5004 | `fd4d87abbfdd2cef840020e34a15a72f9ab481adf48a872a683b70a6831eb928` |
| `manifest.json` | 693135 | `b59b69a86a8c8a59feff51af4b15f52c5bdb86113b3415015dff6f6ce088009b` |
| `rollback.json` | 6993 | `79b1de9ed75bcbc2146e19f6164ebd624cb00507d19faa91124cfda3bfed2ecc` |
