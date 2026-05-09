#!/usr/bin/env python3
"""Inspect a topic queue and print the Claude Code command to run next."""

from __future__ import annotations

import argparse
import json
import os
import shlex
from pathlib import Path


DEFAULT_QUEUE = "~/Documents/NotebookLM-Pipeline/topic_queue.jsonl"


def read_records(queue_path: Path) -> list[dict]:
    if not queue_path.exists():
        return []
    records: list[dict] = []
    with queue_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{queue_path}:{line_number}: invalid JSON: {exc}") from exc
            record["_line"] = line_number
            records.append(record)
    return records


def command_for(record: dict) -> str:
    topic = record["topic"]
    audience = record.get("audience")
    mode = record.get("mode", "local-notebooklm")
    parts = ["/notebook-podcast-factory", shlex.quote(topic)]
    if audience:
        parts.extend(["--audience", shlex.quote(audience)])
    if mode != "local-notebooklm":
        parts.extend(["--mode", shlex.quote(mode)])
    return " ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Show queued podcast topics.")
    parser.add_argument("--queue", default=DEFAULT_QUEUE)
    parser.add_argument("--next", action="store_true", help="Print only the next new topic command.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    args = parser.parse_args()

    queue_path = Path(os.path.expanduser(args.queue))
    records = read_records(queue_path)
    pending = [record for record in records if record.get("status", "new") == "new"]

    if args.json:
        print(json.dumps({"queue": str(queue_path), "pending": pending}, ensure_ascii=False, indent=2))
        return

    if not pending:
        print(f"No new topics in {queue_path}")
        return

    selected = pending[:1] if args.next else pending
    for record in selected:
        print(f"#{record['_line']}: {record['topic']}")
        print(command_for(record))


if __name__ == "__main__":
    main()
