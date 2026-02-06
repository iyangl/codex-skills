#!/usr/bin/env python3
"""Persistent todo storage with project-scoped defaults."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB = Path.home() / ".codex" / "todo-assistant" / "todos.json"
VALID_STATUS = {"open", "in_progress", "done"}
VALID_PRIORITY = {"low", "medium", "high"}
STATUS_ALIASES = {
    "open": "open",
    "todo": "open",
    "new": "open",
    "in_progress": "in_progress",
    "in-progress": "in_progress",
    "doing": "in_progress",
    "done": "done",
    "close": "done",
    "closed": "done",
    "finish": "done",
    "finished": "done",
    "完成": "done",
    "关闭": "done",
}

NEW_ID_RE = re.compile(r"^([A-Z0-9]{2,6})-(\d+)$")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_project(project: str | None) -> str:
    if project:
        return str(Path(project).expanduser().resolve())
    return str(Path.cwd().resolve())


def validate_due_date(value: str | None) -> str | None:
    if value is None:
        return None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("due_date must be YYYY-MM-DD")
    return value


def make_base_project_code(project_path: str) -> str:
    name = Path(project_path).name
    tokens = re.findall(r"[A-Za-z0-9]+", name)
    if len(tokens) >= 2:
        code = "".join(token[0] for token in tokens[:4]).upper()
    elif len(tokens) == 1:
        code = tokens[0][:4].upper()
    else:
        code = "PRJ"
    code = re.sub(r"[^A-Z0-9]", "", code)
    if not code:
        code = "PRJ"
    if len(code) < 2:
        code = (code + "X")[:2]
    return code[:6]


def get_project_code(data: dict[str, Any], project: str) -> str:
    project_codes = data.setdefault("project_codes", {})
    if project in project_codes:
        return project_codes[project]

    used_codes = set(project_codes.values())
    base = make_base_project_code(project)
    candidate = base
    index = 2
    while candidate in used_codes:
        suffix = str(index)
        keep = max(1, 6 - len(suffix))
        candidate = f"{base[:keep]}{suffix}"
        index += 1

    project_codes[project] = candidate
    return candidate


def parse_new_id(item_id: str) -> tuple[str, int] | None:
    match = NEW_ID_RE.fullmatch(item_id)
    if not match:
        return None
    return match.group(1), int(match.group(2))


def extract_seq(item_id: str) -> int | None:
    parsed_new = parse_new_id(item_id)
    if parsed_new:
        return parsed_new[1]
    return None


def normalize_status(raw_status: str) -> str:
    key = raw_status.strip().lower()
    if key in STATUS_ALIASES:
        return STATUS_ALIASES[key]
    raise ValueError("status must be one of: open, in_progress, done")


def next_seq_for_project(items: list[dict[str, Any]], project: str, code: str) -> int:
    max_seq = 0
    for item in items:
        if item.get("project") != project:
            continue
        parsed = parse_new_id(str(item.get("id", "")))
        if parsed and parsed[0] == code:
            max_seq = max(max_seq, parsed[1])
    return max_seq + 1


def normalize_db(data: dict[str, Any]) -> bool:
    items = data.get("items", [])
    project_codes = data.setdefault("project_codes", {})
    changed = False

    # Normalize project paths.
    for item in items:
        project = resolve_project(item.get("project"))
        if item.get("project") != project:
            item["project"] = project
            changed = True

    # Bootstrap mapping from already-migrated IDs.
    used_codes = set(project_codes.values())
    for item in items:
        project = item.get("project", "")
        parsed = parse_new_id(str(item.get("id", "")))
        if not parsed:
            continue
        code, _ = parsed
        existing = project_codes.get(project)
        if existing is None and code not in used_codes:
            project_codes[project] = code
            used_codes.add(code)
            changed = True

    # Ensure all projects have a stable code.
    for project in sorted({str(item.get("project", "")) for item in items if item.get("project")}):
        if project not in project_codes:
            _ = get_project_code(data, project)
            changed = True

    return changed


def load_db(db_path: Path) -> dict[str, Any]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        data = {"version": 2, "next_id": 1, "project_codes": {}, "items": []}
        save_db(db_path, data)
        return data

    try:
        data = json.loads(db_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in DB: {db_path}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("DB root must be an object")

    data.setdefault("version", 2)
    data.setdefault("next_id", 1)
    data.setdefault("project_codes", {})
    data.setdefault("items", [])

    if not isinstance(data["items"], list):
        raise RuntimeError("DB items must be a list")
    if not isinstance(data["project_codes"], dict):
        raise RuntimeError("DB project_codes must be an object")

    if normalize_db(data):
        save_db(db_path, data)

    return data


def save_db(db_path: Path, data: dict[str, Any]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_item(items: list[dict[str, Any]], query: str, lookup_project: str) -> dict[str, Any] | None:
    q = query.strip()

    # Full ID lookup only accepts the new format: <CODE>-<seq>
    if parse_new_id(q.upper()) is not None:
        exact_matches = [item for item in items if str(item.get("id", "")).lower() == q.lower()]
        if len(exact_matches) == 1:
            return exact_matches[0]
        if len(exact_matches) > 1:
            raise RuntimeError(f"Ambiguous ID: {query}")

    shorthand_match = re.fullmatch(r"#?0*(\d+)", q)
    if shorthand_match:
        seq = int(shorthand_match.group(1))
        scoped_matches = []
        for item in items:
            if item.get("project") != lookup_project:
                continue
            item_seq = extract_seq(str(item.get("id", "")))
            if item_seq == seq:
                scoped_matches.append(item)
        if len(scoped_matches) == 1:
            return scoped_matches[0]
        if len(scoped_matches) > 1:
            raise RuntimeError(f"Ambiguous shorthand ID: {query}. Use full ID.")

    return None


def format_item(item: dict[str, Any], include_project: bool) -> str:
    item_id = str(item.get("id", ""))
    seq = extract_seq(item_id)
    short = f"[#{seq}] " if seq is not None else ""
    due = f" due:{item['due_date']}" if item.get("due_date") else ""
    project = f" project:{item.get('project')}" if include_project else ""
    return (
        f"{short}[{item_id}] [{item.get('status')}] [{item.get('priority')}] "
        f"{item.get('title')}{due}{project}"
    )


def filter_items(items: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    filtered = list(items)

    if args.all_projects:
        if args.project:
            project = resolve_project(args.project)
            filtered = [i for i in filtered if i.get("project") == project]
    else:
        project = resolve_project(args.project)
        filtered = [i for i in filtered if i.get("project") == project]

    if args.status and args.status != "all":
        status = normalize_status(args.status)
        filtered = [i for i in filtered if i.get("status") == status]
    elif not args.include_done:
        filtered = [i for i in filtered if i.get("status") != "done"]

    status_rank = {"open": 0, "in_progress": 1, "done": 2}
    filtered.sort(key=lambda i: (status_rank.get(i.get("status", "open"), 9), i.get("updated_at", "")))
    return filtered


def cmd_add(args: argparse.Namespace) -> int:
    db_path = Path(args.db).expanduser()
    data = load_db(db_path)

    created_at = now_iso()
    project = resolve_project(args.project)
    due_date = validate_due_date(args.due_date)

    if args.priority not in VALID_PRIORITY:
        print("priority must be one of: low, medium, high", file=sys.stderr)
        return 2

    code = get_project_code(data, project)
    item_id = f"{code}-{next_seq_for_project(data['items'], project, code)}"

    item = {
        "id": item_id,
        "project": project,
        "title": args.title.strip(),
        "description": (args.description or "").strip(),
        "status": "open",
        "priority": args.priority,
        "due_date": due_date,
        "created_at": created_at,
        "updated_at": created_at,
    }

    data["items"].append(item)
    data["next_id"] = int(data.get("next_id", 1)) + 1
    save_db(db_path, data)

    if args.format == "json":
        print(json.dumps(item, ensure_ascii=False))
    else:
        print(f"Added {item_id}: {item['title']}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    db_path = Path(args.db).expanduser()
    data = load_db(db_path)
    items = filter_items(data["items"], args)

    if args.format == "json":
        print(json.dumps(items, ensure_ascii=False))
        return 0

    if not items:
        print("No todos.")
        return 0

    if args.all_projects and not args.project:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            grouped[str(item.get("project", ""))].append(item)
        for project, project_items in sorted(grouped.items()):
            print(f"Project: {project}")
            for item in project_items:
                print(f"- {format_item(item, include_project=False)}")
    else:
        for item in items:
            print(format_item(item, include_project=False))

    return 0


def cmd_done(args: argparse.Namespace) -> int:
    list_args = argparse.Namespace(
        db=args.db,
        project=args.project,
        all_projects=args.all_projects,
        status="done",
        include_done=True,
        format=args.format,
    )
    return cmd_list(list_args)


def cmd_update(args: argparse.Namespace) -> int:
    db_path = Path(args.db).expanduser()
    data = load_db(db_path)

    lookup_project = resolve_project(args.lookup_project)
    item = resolve_item(data["items"], args.id, lookup_project)
    if item is None:
        print(f"Todo not found: {args.id}", file=sys.stderr)
        return 1

    old_id = str(item.get("id", ""))
    changed = False

    if args.title is not None:
        item["title"] = args.title.strip()
        changed = True

    if args.description is not None:
        item["description"] = args.description.strip()
        changed = True

    if args.status is not None:
        item["status"] = normalize_status(args.status)
        changed = True

    if args.priority is not None:
        if args.priority not in VALID_PRIORITY:
            print("priority must be one of: low, medium, high", file=sys.stderr)
            return 2
        item["priority"] = args.priority
        changed = True

    if args.due_date is not None:
        item["due_date"] = validate_due_date(args.due_date)
        changed = True

    if args.clear_due_date:
        item["due_date"] = None
        changed = True

    if args.project is not None:
        new_project = resolve_project(args.project)
        if new_project != item.get("project"):
            code = get_project_code(data, new_project)
            others = [existing for existing in data["items"] if existing is not item]
            new_id = f"{code}-{next_seq_for_project(others, new_project, code)}"
            item["project"] = new_project
            item["id"] = new_id
            changed = True

    if not changed:
        print("No fields updated.")
        return 0

    item["updated_at"] = now_iso()
    save_db(db_path, data)

    if args.format == "json":
        print(json.dumps(item, ensure_ascii=False))
    else:
        if old_id != item.get("id"):
            print(f"Updated {old_id} -> {item['id']}.")
        else:
            print(f"Updated {item['id']}.")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    db_path = Path(args.db).expanduser()
    data = load_db(db_path)

    lookup_project = resolve_project(args.project)
    item = resolve_item(data["items"], args.id, lookup_project)
    if item is None:
        print(f"Todo not found: {args.id}", file=sys.stderr)
        return 1

    item_id = str(item.get("id", ""))
    data["items"] = [existing for existing in data["items"] if str(existing.get("id", "")) != item_id]
    save_db(db_path, data)
    print(f"Deleted {item_id}.")
    return 0


def cmd_projects(args: argparse.Namespace) -> int:
    db_path = Path(args.db).expanduser()
    data = load_db(db_path)

    grouped: dict[str, dict[str, int]] = defaultdict(
        lambda: {"open": 0, "in_progress": 0, "done": 0, "total": 0}
    )
    for item in data["items"]:
        project = str(item.get("project", ""))
        status = str(item.get("status", "open"))
        grouped[project]["total"] += 1
        if status in {"open", "in_progress", "done"}:
            grouped[project][status] += 1

    if args.format == "json":
        print(json.dumps(grouped, ensure_ascii=False))
        return 0

    if not grouped:
        print("No projects.")
        return 0

    for project, stats in sorted(grouped.items()):
        print(
            f"{project}: total={stats['total']} open={stats['open']} "
            f"in_progress={stats['in_progress']} done={stats['done']}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Todo storage")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to todo database JSON file")

    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a todo item")
    p_add.add_argument("--project", help="Project path; default current working directory")
    p_add.add_argument("--title", required=True, help="Todo title")
    p_add.add_argument("--description", default="", help="Todo description")
    p_add.add_argument("--priority", default="medium", choices=sorted(VALID_PRIORITY))
    p_add.add_argument("--due-date", help="Due date YYYY-MM-DD")
    p_add.add_argument("--format", choices=["text", "json"], default="text")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List todos")
    p_list.add_argument("--project", help="Project path; default current working directory")
    p_list.add_argument("--all-projects", action="store_true", help="List across all projects")
    p_list.add_argument("--status", choices=["open", "in_progress", "done", "all"], help="Filter by status")
    p_list.add_argument("--include-done", action="store_true", help="Include done items")
    p_list.add_argument("--format", choices=["text", "json"], default="text")
    p_list.set_defaults(func=cmd_list)

    p_done = sub.add_parser("done", help="List done todos")
    p_done.add_argument("--project", help="Project path; default current working directory")
    p_done.add_argument("--all-projects", action="store_true", help="List across all projects")
    p_done.add_argument("--format", choices=["text", "json"], default="text")
    p_done.set_defaults(func=cmd_done)

    p_update = sub.add_parser("update", help="Update a todo item")
    p_update.add_argument("--id", required=True, help="Todo ID, supports full ID (OS-1) or shorthand (#1 / 1)")
    p_update.add_argument("--lookup-project", help="Project path used for shorthand ID lookup")
    p_update.add_argument("--title")
    p_update.add_argument("--description")
    p_update.add_argument("--status", help="open | in_progress | done (supports aliases like close/closed)")
    p_update.add_argument("--priority", choices=sorted(VALID_PRIORITY))
    p_update.add_argument("--due-date", help="Due date YYYY-MM-DD")
    p_update.add_argument("--clear-due-date", action="store_true")
    p_update.add_argument("--project", help="Move todo to another project path")
    p_update.add_argument("--format", choices=["text", "json"], default="text")
    p_update.set_defaults(func=cmd_update)

    p_delete = sub.add_parser("delete", help="Delete a todo item")
    p_delete.add_argument("--id", required=True, help="Todo ID, supports full ID (OS-1) or shorthand (#1 / 1)")
    p_delete.add_argument("--project", help="Project path used for shorthand ID lookup")
    p_delete.set_defaults(func=cmd_delete)

    p_projects = sub.add_parser("projects", help="Show project summary")
    p_projects.add_argument("--format", choices=["text", "json"], default="text")
    p_projects.set_defaults(func=cmd_projects)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
