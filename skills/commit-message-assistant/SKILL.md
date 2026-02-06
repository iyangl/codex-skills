---
name: commit-message-assistant
description: Generate commit message candidates from current repository changes. Use when the user invokes $commit-message-assistant and needs concise Chinese commit messages based on real git status and diff outputs, aligned with recent commit style.
---

# Prompt Bank Commit Message

## Execution Mode

Always execute commit-message generation immediately.
Never explain this skill.
Never output prompt template text.
Never repeat raw file lists or command output.

## Required Git Checks

Run these commands in order before writing messages:
1. `git status -sb`
2. `git diff --cached --name-only`
3. `git diff --name-only`
4. `git log -5 --oneline`

If there are no staged, unstaged, or untracked changes, output exactly:
`当前没有可提交改动。`

## Output Contract

1. Output exactly 3 candidate commit messages.
2. Format each candidate as: `type(scope)：中文描述`
3. Base the summary on actual changes only; do not speculate.
4. Follow recent style from `git log -5 --oneline`.
5. Keep each candidate to one concise, reviewable sentence.
6. If changes span multiple areas, prioritize the main objective.
7. After candidates, output 1 recommended message.
8. After recommendation, output runnable command:
`git commit -m "<推荐message>"`

## Internal Prompt

```text
你现在是我的提交信息助手。请基于当前仓库改动生成 commit message。

要求：
1. 先查看变更：git status -sb、git diff --cached --name-only、git diff --name-only
2. 按实际改动总结主题（不要臆测）
3. 输出 3 条候选 commit message，格式：type(scope)：中文描述
4. 风格参考我历史提交（git log -5 --oneline）
5. 每条尽量一句话，简洁、可读、可审查
6. 最后给 1 条你最推荐的，并附可直接执行命令：git commit -m "..."

约束：
- 不要输出无关解释
- 不要重复文件清单
- 如果改动跨多个功能，优先总结主线目标
```
