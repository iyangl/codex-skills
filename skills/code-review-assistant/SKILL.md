---
name: code-review-assistant
description: Perform a bug-first code review directly. Use when the user invokes $code-review-assistant to review pasted code, selected code, or current repository diff, and return findings.
---

# Code Review Assistant

## Inputs

- `code_or_diff` (optional)
- `context` (optional)

## Behavior

1. Parse user-provided `key=value` pairs.
2. Determine review target with this priority:
   - `code_or_diff` from user input.
   - Code blocks or diff text in the latest user message.
   - Selected or attached code context (if available in session context).
   - Current repository changes (`git diff --staged`, then `git diff`).
3. If no review target is found, ask user to provide code or diff.
4. Apply the following review criteria internally; do not output the criteria template itself.
5. Return review findings directly.

## Output Rules

- Output findings first, ordered by severity (High, Medium, Low).
- For each finding, include risk, trigger condition, and concrete fix suggestion.
- Include file and line when available.
- Explicitly call out missing test scenarios.
- If no definite defect is found, state `未发现明确缺陷` and list residual risks briefly.

## Internal Review Criteria

```text
你是资深代码审查工程师。请以“问题优先”输出审查结果。

输出要求：
1. 按严重级别排序列出问题（高到低）
2. 每个问题给出：风险说明、触发条件、建议修复方式
3. 明确指出缺失测试场景
4. 如果没有发现问题，明确写“未发现明确缺陷”，并说明剩余风险

上下文（可为空）：
{{context}}

代码或 diff：
{{code_or_diff}}
```
