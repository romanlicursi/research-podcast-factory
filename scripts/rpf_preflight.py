#!/usr/bin/env python3
"""Local preflight checks for the research podcast workflow."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


DEFAULT_STATE = "~/Documents/NotebookLM-Pipeline/state.json"
DEFAULT_DOWNLOAD_DIR = "~/Downloads/notebooklm-audio"


def run_json(cmd: list[str]) -> tuple[bool, dict | str]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False, timeout=30)
    except Exception as exc:
        return False, str(exc)
    if proc.returncode != 0:
        return False, proc.stderr.strip() or proc.stdout.strip()
    try:
        return True, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return False, proc.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Check local workflow readiness.")
    parser.add_argument("--state", default=DEFAULT_STATE)
    parser.add_argument("--download-dir", default=DEFAULT_DOWNLOAD_DIR)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    state_path = Path(os.path.expanduser(args.state))
    download_dir = Path(os.path.expanduser(args.download_dir))
    save_to_spotify = shutil.which("save-to-spotify") or "/Users/romanlicursi/.local/bin/save-to-spotify"

    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str | dict = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    add("repo files", all((repo_root / path).exists() for path in [
        "claude-commands/notebook-podcast-factory.md",
        "claude-commands/process-podcasts.md",
        "claude-commands/research-notebook-factory.md",
        "codex-skill/research-podcast-factory/SKILL.md",
        "scripts/queue_topic.py",
        "scripts/topic_webhook.py",
    ]), str(repo_root))

    add("state file", state_path.exists(), str(state_path))
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            add("state json", isinstance(state.get("notebooks"), dict), f"{len(state.get('notebooks', {}))} notebooks")
        except Exception as exc:
            add("state json", False, str(exc))

    download_dir.mkdir(parents=True, exist_ok=True)
    add("download dir", download_dir.exists(), str(download_dir))

    add("save-to-spotify binary", Path(save_to_spotify).exists(), save_to_spotify)
    if Path(save_to_spotify).exists():
        ok, detail = run_json([save_to_spotify, "auth", "status", "--json"])
        add("save-to-spotify auth", ok and bool(isinstance(detail, dict) and detail.get("token_valid")), detail)

    claude = shutil.which("claude")
    add("claude cli", bool(claude), claude or "not found")

    result = {"ok": all(check["ok"] for check in checks), "checks": checks}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    for check in checks:
        marker = "ok" if check["ok"] else "fail"
        print(f"[{marker}] {check['name']}: {check['detail']}")
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
