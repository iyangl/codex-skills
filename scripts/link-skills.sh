
#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO_DIR/skills"
DST="$HOME/.codex/skills"
BACKUP_ROOT="$HOME/.codex/skills_backup/$(date +%Y%m%d%H%M%S)"
mkdir -p "$DST"

for skill_dir in "$SRC"/*; do
  [ -d "$skill_dir" ] || continue
  name="$(basename "$skill_dir")"
  target="$DST/$name"

  if [ -L "$target" ]; then
    rm "$target"
  elif [ -e "$target" ]; then
    mkdir -p "$BACKUP_ROOT"
    mv "$target" "$BACKUP_ROOT/$name"
  fi

  ln -s "$skill_dir" "$target"
done

echo "linked: $SRC -> $DST"
