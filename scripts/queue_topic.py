#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Append a podcast topic to the local research podcast queue.")
    parser.add_argument("topic", help="Short topic or question")
    parser.add_argument("--audience", default="Roman, curious skeptical listener")
    parser.add_argument(
        "--mode",
        default="local-notebooklm",
        choices=["local-notebooklm", "cloud-enterprise", "cloud-native"],
    )
    parser.add_argument(
        "--queue",
        default="~/Documents/NotebookLM-Pipeline/topic_queue.jsonl",
        help="JSONL queue path",
    )
    args = parser.parse_args()

    queue_path = Path(os.path.expanduser(args.queue))
    queue_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "topic": args.topic.strip(),
        "audience": args.audience.strip(),
        "mode": args.mode,
        "status": "new",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if not record["topic"]:
        raise SystemExit("topic is required")

    with queue_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(json.dumps({"queued": True, "path": str(queue_path), "record": record}, ensure_ascii=False))


if __name__ == "__main__":
    main()
