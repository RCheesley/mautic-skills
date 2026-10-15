#!/usr/bin/env bash
# Symlink every skill in ./skills into an agent's skills directory.
# Claude Code: ~/.claude/skills (default) · Codex: CODEX_SKILLS_DIR=~/.codex/skills
# Cursor / Gemini CLI / Copilot / other: AGENT_SKILLS_DIR=<path>
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="$REPO_ROOT/skills"
TARGET_DIR="${AGENT_SKILLS_DIR:-${CODEX_SKILLS_DIR:-${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}}}"

mkdir -p "$TARGET_DIR"
linked=0; skipped=0

for skill_path in "$SOURCE_DIR"/*; do
  [ -d "$skill_path" ] || continue
  [ -f "$skill_path/SKILL.md" ] || { echo "skip: $(basename "$skill_path") (no SKILL.md)"; continue; }
  skill_name="$(basename "$skill_path")"
  target_path="$TARGET_DIR/$skill_name"

  if [ -L "$target_path" ]; then
    if [ "$(readlink "$target_path" || true)" = "$skill_path" ]; then
      echo "skip: $skill_name (already linked)"
    else
      echo "skip: $skill_name (symlink exists but points elsewhere: $(readlink "$target_path"))"
    fi
    skipped=$((skipped + 1)); continue
  fi
  if [ -e "$target_path" ]; then
    echo "skip: $skill_name (target already exists at $target_path)"
    skipped=$((skipped + 1)); continue
  fi
  ln -s "$skill_path" "$target_path"
  echo "linked: $skill_name -> $target_path"
  linked=$((linked + 1))
done

echo
echo "done: linked=$linked skipped=$skipped target_dir=$TARGET_DIR"
