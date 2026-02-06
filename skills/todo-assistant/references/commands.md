# Todo Command Reference

Default script path:

`/Users/sunpure/.codex/skills/todo-assistant/scripts/todo_store.py`

## Basic Operations

- ID format:
  - Full: `<PROJECT_CODE>-<seq>` (example: `OS-1`)
  - Short (current project): `1` or `#1`
- List current project open todos:
  - `python3 .../todo_store.py list --project "<project_path>"`
- List current project done todos:
  - `python3 .../todo_store.py done --project "<project_path>"`
- Add:
  - `python3 .../todo_store.py add --project "<project_path>" --title "..." --priority medium`
- Update:
  - `python3 .../todo_store.py update --id 1 --status in_progress`
- Mark done:
  - `python3 .../todo_store.py update --id 1 --status done`
- Delete:
  - `python3 .../todo_store.py delete --id 1`

## Cross-Project

- List all projects:
  - `python3 .../todo_store.py list --all-projects --include-done`
- List done todos across all projects:
  - `python3 .../todo_store.py done --all-projects`
- Project summary:
  - `python3 .../todo_store.py projects`
