#!/usr/bin/env python3
"""Smoke tests for portable parts of the repo."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_queue_cli(tmp: Path) -> None:
    queue = tmp / "queue.jsonl"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/queue_topic.py"), "Dostoevsky and doubt", "--queue", str(queue)],
        check=True,
        text=True,
        capture_output=True,
    )
    records = [json.loads(line) for line in queue.read_text(encoding="utf-8").splitlines()]
    assert records[0]["topic"] == "Dostoevsky and doubt"
    assert records[0]["status"] == "new"

def test_required_files() -> None:
    required = [
        "README.md",
        "claude-commands/notebook-podcast-factory.md",
        "claude-commands/process-podcasts.md",
        "claude-commands/research-notebook-factory.md",
        "codex-skill/research-podcast-factory/SKILL.md",
        "scripts/install.sh",
        "docs/save-to-spotify.md",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    assert not missing, f"missing files: {missing}"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        test_queue_cli(tmp)
    test_required_files()
    print("smoke tests passed")


if __name__ == "__main__":
    main()
