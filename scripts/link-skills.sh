
#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO_DIR/skills"
DST="$HOME/.codex/skills"
mkdir -p "$DST"

for skill_dir in "$SRC"/*; do
  [ -d "$skill_dir" ] || continue
  name="$(basename "$skill_dir")"
  target="$DST/$name"

  if [ -L "$target" ]; then
    rm "$target"
  elif [ -e "$target" ]; then
    mv "$target" "$target.local.bak.$(date +%Y%m%d%H%M%S)"
  fi

  ln -s "$skill_dir" "$target"
done

echo "linked: $SRC -> $DST"
