---
name: todo-assistant
description: Manage todos across projects with a global skill and project-scoped default view. Use when the user needs todo operations like add, list, update, delete, mark done, or wants to view all projects while defaulting to the current project.
---

# Todo Assistant

## Overview

Use a global todo store while keeping default output scoped to the current project.

## Data Store

- Script: `scripts/todo_store.py`
- Default DB path: `~/.codex/todo-assistant/todos.json`
- Todo fields: `id`, `project`, `title`, `description`, `status`, `priority`, `due_date`, `created_at`, `updated_at`
- ID format: `<PROJECT_CODE>-<seq>` (for example `OS-1`), and `update/delete` support shorthand `seq` or `#seq` in current project.

## Workflow

1. Prefer omitting `--project` so the script uses the current `cwd` as the absolute project path (same as `pwd`/`$PWD`). Use `--project` only when targeting a different project.
2. Map user intent to one command: `add`, `list`, `done`, `update`, `delete`, `projects`.
3. Execute `scripts/todo_store.py`.
4. Return concise results.

## Intent Mapping

- Add todo: `add`
  - Require `title`.
  - Optional: `description`, `priority` (`low|medium|high`), `due_date` (`YYYY-MM-DD`).
- View todos: `list`
  - Default: current project only, exclude done items.
  - If user asks “全部项目/所有项目/all projects”, use `--all-projects`.
  - If user asks to include done, add `--include-done`.
- View completed todos: `done`
  - Default: current project only.
  - If user asks “全部项目/所有项目/all projects”, use `--all-projects`.
- Modify todo: `update`
  - Require `id`.
  - `id` supports full ID (`OS-3`) or shorthand (`3` / `#3`, current project only).
  - Allow changing: `title`, `description`, `status`, `priority`, `due_date`.
  - “完成/done” maps to `status=done`.
- Delete todo: `delete`
  - Require `id`.
  - `id` supports full ID (`OS-3`) or shorthand (`3` / `#3`, current project only).
- Project summary: `projects`
  - Show each project and counts by status.

## Command Patterns

Use absolute script path:
`/Users/sunpure/.codex/skills/todo-assistant/scripts/todo_store.py`

Examples:

```bash
python3 /Users/sunpure/.codex/skills/todo-assistant/scripts/todo_store.py list
python3 /Users/sunpure/.codex/skills/todo-assistant/scripts/todo_store.py done
python3 /Users/sunpure/.codex/skills/todo-assistant/scripts/todo_store.py add --title "修复登录按钮状态"
python3 /Users/sunpure/.codex/skills/todo-assistant/scripts/todo_store.py update --id 3 --status done
python3 /Users/sunpure/.codex/skills/todo-assistant/scripts/todo_store.py delete --id 3
python3 /Users/sunpure/.codex/skills/todo-assistant/scripts/todo_store.py projects
```

## Output Rules

- Default response only shows current project todos.
- All-project view is opt-in.
- Keep responses compact and task-oriented.
- Never fabricate todo IDs; always use script results.
