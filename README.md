# codex-skills

这个仓库用于集中管理个人 Codex 自定义 skills，便于多台电脑同步。

## 仓库结构

```text
codex-skills/
├── skills/                 # 自定义 skills（版本管理）
│   ├── ccg-workflow/
│   ├── code-review-assistant/
│   ├── commit-message-assistant/
│   └── todo-assistant/
└── scripts/
    └── link-skills.sh      # 将仓库中的 skills 链接到 ~/.codex/skills
```

说明：`~/.codex/skills/.system` 是 Codex 内置系统技能，不在本仓库管理范围内。

## Skills 说明

| Skill | 作用 | 典型触发场景 |
|---|---|---|
| `ccg-workflow` | 把 CCG 的 6 阶段工作流移植到 Codex（单模型版），保留阶段化 prompt 映射与 `feat` 模式判定。 | 需要按“研究→构思→计划→执行→优化→评审”推进一个功能。 |
| `code-review-assistant` | Bug-first 代码审查，优先输出缺陷与风险。 | 让 Codex 审查粘贴代码、选中代码、或当前仓库 diff。 |
| `commit-message-assistant` | 基于真实 git 变更生成 3 条中文提交信息，并给出推荐。 | 需要快速生成规范 commit message。 |
| `todo-assistant` | 跨项目 todo 管理，默认按当前项目视图展示。 | 新增/查询/更新/完成/删除待办事项。 |

## 本机接入

1. 克隆仓库到本地（例如 `/Users/sunpure/Documents/Code/codex-skills`）。
2. 运行链接脚本：

```bash
/Users/sunpure/Documents/Code/codex-skills/scripts/link-skills.sh
```

3. 检查 `~/.codex/skills` 下是否已生成对应软链接。

## Windows 接入（Git Bash）

在 Windows 上推荐使用 Git Bash 运行脚本。

1. 打开 Git Bash，进入仓库目录（例如 `E:/Development/Codes/codex-skills`）。
2. 运行脚本（避免因可执行位或隐藏字符导致失败，建议用 bash 直接执行）：

```bash
bash scripts/link-skills.sh
```

3. 如果脚本需要创建符号链接失败，开启 Windows Developer Mode，或以管理员权限运行 Git Bash。
4. 检查 `C:\Users\<你>\.codex\skills` 下是否已生成对应软链接。

## 多机同步流程

1. 在任一机器修改 `skills/*`。
2. 提交并推送：`git add -A && git commit -m "..." && git push`。
3. 在其他机器拉取：`git pull --rebase`。
4. 首次接入该机器时执行一次 `scripts/link-skills.sh`。

## 维护建议

- 每个 skill 的行为定义以 `skills/<skill>/SKILL.md` 为准。
- 新增 skill 时，优先保持 `description` 精准，便于被正确触发。
- 尽量避免把与 skill 无关的临时文件提交到仓库。
