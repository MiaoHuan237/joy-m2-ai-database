# Task 3 逐题复核结果契约

每个来源分区输出一个 JSON 数组；数组内每个对象对应一整道题，不拆小问。所有文本使用 UTF-8。

## 必填字段

```json
{
  "question_id": "M2QD-DA-...",
  "source_section": "教材例题|应试训练|甲部特训|乙部特训",
  "checks": {
    "question_boundary": "pass|issue",
    "english_text": "pass|issue",
    "chinese_text": "pass|revised|issue",
    "formula_symbols_units": "pass|issue",
    "subparts_and_marks": "pass|unknown|issue",
    "necessary_images": "pass|not_required|issue",
    "answer_pairing": "pass|missing|issue",
    "answer_mathematics": "pass|needs_correction|blocked"
  },
  "question_text_zh_reviewed": "完整、自然且数学信息不变的中文题干",
  "solution_verified": "经数学复核后的完整答案；无答案或阻断时可为空",
  "answer_status_reviewed": "source_provided|missing_from_source|web_found_verified|ai_solved_verified|generated_unverified",
  "answer_verification_status": "checked_pass|needs_correction|corrected_verified|not_checked",
  "primary_type": "受控主类型之一",
  "tags": ["受控标签"],
  "difficulty_level": 1,
  "difficulty_dimensions": {
    "概念数": 0,
    "推理链长度": 0,
    "建模强度": 0,
    "代数负担": 0,
    "条件处理": 0,
    "易错风险": 0
  },
  "difficulty_evidence": "一句说明为什么是该 Level",
  "correction_status": "none|suspected|confirmed|corrected_verified",
  "corrections": [
    {
      "field": "question_text_zh|question_text_original|solution_original|marks_total|image_paths|source_file/source_member|solution_source_file/solution_source_member|source_member_sha256|solution_source_member_sha256",
      "error_origin": "mathpix_conversion|source_original|database_mapping|translation",
      "original": "原文或原值",
      "corrected": "建议订正文或新值",
      "reason": "数学或语言理由",
      "evidence": "原始MMD位置、图片名或独立复算依据"
    }
  ],
  "duplicate_status": "new|adapted|historical_reference|exact_duplicate",
  "duplicate_reference": "相关题ID；没有则为空字符串",
  "duplicate_evidence": "重复/改编判断依据；没有则简述未发现",
  "unresolved_issues": [],
  "audit_notes": "简短审计说明",
  "record_status": "audit_passed|audit_pending|blocked"
}
```

## 判定边界

- `audit_passed`：八项检查没有 `issue`、`needs_correction`、`blocked` 或 `not_checked`，主类型/标签/Level 完整，且没有未关闭疑点。
- `audit_pending`：存在可修订问题或需 Joy 判断的来源原错，但题目仍可保留。
- `blocked`：题目边界、关键图片、核心数学条件或答案严重缺失，当前无法可靠使用。
- 英文原题不得直接覆盖；英文疑点写入 `corrections`。
- 中文可在 `question_text_zh_reviewed` 中规范化；若发生实质修订，`chinese_text=revised` 并记录校订。
- 分值来源不可靠时使用 `unknown`，不得自行猜分。
- 题目或答案来源文件/成员映射错误必须以 `database_mapping` 记录，并在修正前保持 `audit_pending`。
- 来源成员映射发生变化时，必须同步记录对应成员 SHA-256 的旧值和新值，避免文件名与哈希自相矛盾。
- 标签只标题目明确要求的能力；不能因答案顺带使用某方法而贴标。
- Level 依据整题最高稳定认知要求；六维评分每项仅允许0、1、2，总分仅作参考。
- `official_marking_available` 不在分区结果中改写；本资料不是 HKEAA 官方评分。
- Joy 确认前不得使用 `approved_for_import`。
