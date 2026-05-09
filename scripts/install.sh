#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

mkdir -p "$CODEX_HOME/skills/research-podcast-factory"
mkdir -p "$CLAUDE_HOME/commands"

rsync -a --delete "$ROOT/codex-skill/research-podcast-factory/" "$CODEX_HOME/skills/research-podcast-factory/"
cp "$ROOT/claude-commands/"*.md "$CLAUDE_HOME/commands/"

mkdir -p "$HOME/Documents/NotebookLM-Pipeline" "$HOME/Downloads/notebooklm-audio"

echo "Installed:"
echo "  Codex skill:  $CODEX_HOME/skills/research-podcast-factory"
echo "  Claude cmds:  $CLAUDE_HOME/commands"
echo "  Queue dir:    $HOME/Documents/NotebookLM-Pipeline"
