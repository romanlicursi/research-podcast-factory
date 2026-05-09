#!/usr/bin/env python3
"""Small phone-friendly topic inbox.

Run this on a Mac, then point an iOS Shortcut at:

  http://<mac-lan-ip>:8765/topic

The request body can be JSON:

  {"topic": "Simone Weil for a skeptical agnostic", "mode": "local-notebooklm"}
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs


DEFAULT_QUEUE = "~/Documents/NotebookLM-Pipeline/topic_queue.jsonl"
VALID_MODES = {"local-notebooklm", "cloud-enterprise", "cloud-native"}


def append_record(queue_path: Path, record: dict) -> dict:
    topic = str(record.get("topic", "")).strip()
    if not topic:
        raise ValueError("topic is required")

    mode = str(record.get("mode", "local-notebooklm")).strip()
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of: {', '.join(sorted(VALID_MODES))}")

    queued = {
        "topic": topic,
        "audience": str(record.get("audience", "Roman, curious skeptical listener")).strip(),
        "mode": mode,
        "status": "new",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "topic_webhook",
    }

    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(queued, ensure_ascii=False) + "\n")
    return queued


def build_handler(queue_path: Path):
    class TopicHandler(BaseHTTPRequestHandler):
        server_version = "ResearchPodcastFactory/0.1"

        def do_GET(self):  # noqa: N802
            if self.path.rstrip("/") in {"", "/health"}:
                self._json(200, {"ok": True, "queue": str(queue_path)})
                return
            self._json(404, {"ok": False, "error": "use POST /topic"})

        def do_POST(self):  # noqa: N802
            if self.path.rstrip("/") != "/topic":
                self._json(404, {"ok": False, "error": "use POST /topic"})
                return

            try:
                payload = self._read_payload()
                record = append_record(queue_path, payload)
            except Exception as exc:
                self._json(400, {"ok": False, "error": str(exc)})
                return

            self._json(201, {"ok": True, "queued": record})

        def _read_payload(self) -> dict:
            length = int(self.headers.get("content-length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length else ""
            content_type = self.headers.get("content-type", "")
            if "application/json" in content_type:
                return json.loads(raw or "{}")
            if "application/x-www-form-urlencoded" in content_type:
                parsed = parse_qs(raw)
                return {key: values[-1] for key, values in parsed.items()}
            if raw.strip():
                return {"topic": raw.strip()}
            return {}

        def _json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "application/json; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args) -> None:
            print(f"{self.address_string()} - {fmt % args}")

    return TopicHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a phone-friendly topic webhook.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--queue", default=DEFAULT_QUEUE)
    args = parser.parse_args()

    queue_path = Path(os.path.expanduser(args.queue))
    server = ThreadingHTTPServer((args.host, args.port), build_handler(queue_path))
    print(json.dumps({"listening": f"http://{args.host}:{args.port}", "queue": str(queue_path)}))
    server.serve_forever()


if __name__ == "__main__":
    main()
