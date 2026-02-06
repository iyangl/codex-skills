---
name: ccg-workflow
description: Use for feature planning/execution requests when the user wants a CCG-style 6-phase workflow in Codex. Automatically applies preserved CCG Codex prompts and CCG-like phase output templates. Single-model only.
---

# CCG Workflow Skill (Codex Single-Model Port)

This skill ports `ccg:workflow` and `ccg:feat` into Codex while preserving the CCG phase prompt style and response rhythm.

## Scope
- Single-model workflow only (Codex).
- No frontend/backend switching.
- No dual-model audit.
- Preserve phase prompts from installed CCG Codex prompts.
- Keep phase responses in concise Chinese by default.

## Prompt Preservation Protocol (Mandatory)
At the start of each phase, load and apply the mapped prompt file before phase work.
Do not print prompt content unless the user explicitly asks.

Prompt base directory:
- `/Users/sunpure/.claude/.ccg/prompts/codex`

Phase-to-prompt mapping:
1. Phase 1 Research -> `analyzer.md`
2. Phase 2 Ideation -> `analyzer.md`
3. Phase 3 Plan -> `architect.md`
4. Phase 4 Execute -> `architect.md`
5. Phase 5 Optimize -> `optimizer.md`
6. Phase 6 Review -> `reviewer.md`, then `tester.md`

If any prompt file is missing:
- Continue with the same phase structure using built-in reasoning.
- Tell the user which file is missing.

## FEAT Entry (ccg:feat equivalent)
Always classify user intent first, and always begin with this sentence:
- `我判断此次操作类型为：[Plan mode | Iterate mode | Execute mode]`

Mode rules:
- `Plan mode`: user asks to implement/build/design a feature without an approved plan.
- `Iterate mode`: user asks to adjust an existing plan.
- `Execute mode`: user asks to execute an approved plan.

If ambiguous, ask which mode the user wants.

## CCG-Like Phase Output Templates (Mandatory)

### Phase 1 Research
Start with:
- `[模式：研究]`

Output structure:
- `任务理解`: one concise restatement
- `当前上下文`: relevant files/modules found
- `缺失信息`: unanswered points
- `下一步`: what Phase 2 will decide

### Phase 2 Ideation
Start with:
- `[模式：构思]`

Output structure:
- `方案 A`: approach, pros, risks
- `方案 B`: approach, pros, risks
- `推荐方案`: one recommendation with tradeoff note
- `确认点`: what needs user confirmation before planning

### Phase 3 Plan
Start with:
- `[模式：计划]`

Output structure:
- `## 实施计划：<feature-name>`
- `目标范围`
- `实施步骤` (numbered)
- `关键文件` (path + operation)
- `验证方案` (tests/checks)
- `风险与回滚`
- `审批请求`: ask explicit approval

After outputting plan:
- Save plan file (see Plan Storage).
- Do not start coding before explicit approval.

### Phase 4 Execute
Start with:
- `[模式：执行]`

Output structure:
- `执行内容`: what was changed
- `变更文件`: exact paths
- `实现说明`: important decisions made during implementation
- `阶段结论`: whether to enter optimization

### Phase 5 Optimize
Start with:
- `[模式：优化]`

Output structure:
- `发现问题`: correctness/readability/edge-case items
- `优化动作`: concrete fixes applied
- `验证结果`: lint/typecheck/tests status
- `残留风险`: anything still unresolved

### Phase 6 Review
Start with:
- `[模式：评审]`

Output structure:
- `交付摘要`: what is now done
- `验收结果`: checks passed/failed
- `影响范围`: behavior and file-level scope
- `最终确认`: ask user to confirm completion

## Plan Storage
Default:
- `.codex/plan/<feature-slug>.md`

Compatibility mode (if user asks for CCG-compatible path):
- `.claude/plan/<feature-slug>.md`

## Operating Rules
- Do not skip phase order unless user explicitly asks.
- Do not start Phase 4 without approved Phase 3 plan.
- Keep changes minimal and scoped.
- Keep responses concise and actionable.
