#!/usr/bin/env python3
"""Smoke tests for portable parts of the repo."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


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


def test_webhook(tmp: Path) -> None:
    queue = tmp / "webhook.jsonl"
    port = free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "scripts/topic_webhook.py"),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--queue",
            str(queue),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        time.sleep(0.5)
        body = json.dumps({"topic": "Simone Weil and attention"}).encode("utf-8")
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/topic",
            data=body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["ok"] is True
        records = [json.loads(line) for line in queue.read_text(encoding="utf-8").splitlines()]
        assert records[0]["topic"] == "Simone Weil and attention"
        assert records[0]["source"] == "topic_webhook"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_required_files() -> None:
    required = [
        "README.md",
        "claude-commands/notebook-podcast-factory.md",
        "claude-commands/process-podcasts.md",
        "claude-commands/research-notebook-factory.md",
        "codex-skill/research-podcast-factory/SKILL.md",
        "scripts/install.sh",
        "docs/iphone-shortcut.md",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    assert not missing, f"missing files: {missing}"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        test_queue_cli(tmp)
        test_webhook(tmp)
    test_required_files()
    print("smoke tests passed")


if __name__ == "__main__":
    main()
