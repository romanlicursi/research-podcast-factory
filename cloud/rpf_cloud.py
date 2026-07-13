from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import shutil
import sqlite3
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

UTC = timezone.utc
TERMINAL = {"complete", "failed", "cancelled", "needs_google_auth", "needs_spotify_auth"}


def iso(dt: datetime | None = None) -> str:
    return (dt or datetime.now(UTC)).isoformat()


def parse_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    db_path: Path
    workspace_dir: Path
    static_dir: Path
    api_token: str
    public_base_url: str
    poll_seconds: int
    max_attempts: int
    retry_base_seconds: int
    max_upload_mb: int
    claude_model: str
    claude_effort: str
    claude_budget: float
    agent_timeout: int
    mcp_config: str
    spotify_show_id: str
    spotify_new_show: str
    unpaywall_email: str
    telegram_token: str
    telegram_chat_id: str
    mock_agent: bool

    @classmethod
    def from_env(cls) -> "Settings":
        root = Path(os.getenv("RPF_DATA_DIR", "/data"))
        return cls(
            data_dir=root,
            db_path=Path(os.getenv("RPF_DB_PATH", str(root / "jobs.sqlite3"))),
            workspace_dir=Path(os.getenv("RPF_WORKSPACE_DIR", str(root / "jobs"))),
            static_dir=Path(__file__).parent / "static",
            api_token=os.getenv("RPF_API_TOKEN", ""),
            public_base_url=os.getenv("RPF_PUBLIC_BASE_URL", "").rstrip("/"),
            poll_seconds=int(os.getenv("RPF_POLL_SECONDS", "10")),
            max_attempts=int(os.getenv("RPF_MAX_ATTEMPTS", "6")),
            retry_base_seconds=int(os.getenv("RPF_RETRY_BASE_SECONDS", "60")),
            max_upload_mb=int(os.getenv("RPF_MAX_UPLOAD_MB", "40")),
            claude_model=os.getenv("RPF_CLAUDE_MODEL", "opus"),
            claude_effort=os.getenv("RPF_CLAUDE_EFFORT", "high"),
            claude_budget=float(os.getenv("RPF_CLAUDE_MAX_BUDGET_USD", "12")),
            agent_timeout=int(os.getenv("RPF_AGENT_TIMEOUT_SECONDS", "7200")),
            mcp_config=os.getenv("RPF_CLAUDE_MCP_CONFIG", "/config/mcp.json"),
            spotify_show_id=os.getenv("RPF_SPOTIFY_SHOW_ID", ""),
            spotify_new_show=os.getenv("RPF_SPOTIFY_NEW_SHOW", "Research Podcast Factory"),
            unpaywall_email=os.getenv("UNPAYWALL_EMAIL", ""),
            telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("TELEGRAM_ALLOWED_CHAT_ID", ""),
            mock_agent=os.getenv("RPF_MOCK_AGENT", "false").lower() == "true",
        )


class Database:
    def __init__(self, settings: Settings):
        self.settings = settings
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        settings.workspace_dir.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.settings.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("pragma journal_mode=wal")
        conn.execute("pragma foreign_keys=on")
        return conn

    def _init(self) -> None:
        with self.connect() as conn:
            conn.executescript("""
            create table if not exists jobs (
              id text primary key,
              topic text not null,
              audience text not null,
              instructions text not null,
              max_sources integer not null,
              status text not null,
              stage text not null,
              attempts integer not null default 0,
              next_attempt_at text,
              created_at text not null,
              updated_at text not null,
              uploads_json text not null default '[]',
              research_json text,
              result_json text,
              notebook_url text,
              audio_path text,
              audio_fingerprint text,
              spotify_episode_id text,
              spotify_url text,
              error text,
              cancel_requested integer not null default 0
            );
            create table if not exists events (
              id integer primary key autoincrement,
              job_id text not null references jobs(id) on delete cascade,
              stage text not null,
              message text not null,
              created_at text not null
            );
            create index if not exists jobs_due on jobs(status, next_attempt_at, created_at);
            """)

    def event(self, job_id: str, stage: str, message: str) -> None:
        with self.connect() as conn:
            conn.execute("insert into events(job_id,stage,message,created_at) values(?,?,?,?)", (job_id, stage, message, iso()))

    def create_job(self, topic: str, audience: str, instructions: str, max_sources: int, uploads: list[dict[str, str]]) -> dict[str, Any]:
        job_id = str(uuid.uuid4())
        now = iso()
        with self.connect() as conn:
            conn.execute("""insert into jobs(id,topic,audience,instructions,max_sources,status,stage,created_at,updated_at,uploads_json,next_attempt_at)
                          values(?,?,?,?,?,'queued','queued',?,?,?,?,?)""",
                         (job_id, topic, audience, instructions, max_sources, now, now, json.dumps(uploads), now))
            conn.execute("insert into events(job_id,stage,message,created_at) values(?,?,?,?)", (job_id, "queued", "Job queued", now))
        return self.get_job(job_id)

    def _row(self, row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        d["uploads"] = parse_json(d.pop("uploads_json", "[]"), [])
        d["research"] = parse_json(d.pop("research_json", None), None)
        d["result"] = parse_json(d.pop("result_json", None), None)
        d["cancel_requested"] = bool(d["cancel_requested"])
        return d

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute("select * from jobs where id=?", (job_id,)).fetchone()
        if not row:
            raise KeyError(job_id)
        return self._row(row)

    def list_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("select * from jobs order by created_at desc limit ?", (limit,)).fetchall()
        return [self._row(r) for r in rows]

    def list_events(self, job_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("select stage,message,created_at from events where job_id=? order by id", (job_id,)).fetchall()
        return [dict(r) for r in rows]

    def update(self, job_id: str, **values: Any) -> None:
        if not values:
            return
        encoded: dict[str, Any] = {}
        for key, value in values.items():
            if key in {"uploads", "research", "result"}:
                encoded[key + "_json"] = json.dumps(value)
            elif key == "cancel_requested":
                encoded[key] = int(bool(value))
            else:
                encoded[key] = value
        encoded["updated_at"] = iso()
        clause = ",".join(f"{k}=?" for k in encoded)
        with self.connect() as conn:
            conn.execute(f"update jobs set {clause} where id=?", (*encoded.values(), job_id))

    def claim_next(self) -> dict[str, Any] | None:
        now = iso()
        with self.connect() as conn:
            conn.execute("begin immediate")
            row = conn.execute("""select id from jobs where status in ('queued','retry','audio_pending')
                                and coalesce(next_attempt_at,'') <= ? and cancel_requested=0
                                order by created_at limit 1""", (now,)).fetchone()
            if not row:
                conn.commit()
                return None
            conn.execute("update jobs set status='running',stage='starting',attempts=attempts+1,updated_at=? where id=?", (now, row["id"]))
            conn.commit()
        return self.get_job(row["id"])

    def retry(self, job_id: str) -> None:
        self.update(job_id, status="queued", stage="queued", next_attempt_at=iso(), error=None, cancel_requested=False)
        self.event(job_id, "queued", "Job queued again")


class ShortcutRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=2000)
    audience: str = "Roman, curious skeptical listener"
    instructions: str = ""
    max_sources: int = Field(default=10, ge=6, le=20)


class Researcher:
    def __init__(self, settings: Settings):
        self.settings = settings

    def discover(self, topic: str, max_sources: int) -> dict[str, Any]:
        candidates: list[dict[str, Any]] = []
        errors: list[str] = []
        with httpx.Client(timeout=25, headers={"User-Agent": "research-podcast-factory/1.0"}) as client:
            try:
                data = client.get("https://api.openalex.org/works", params={"search": topic, "per-page": min(max_sources * 2, 25), "sort": "cited_by_count:desc"}).json()
                for item in data.get("results", []):
                    loc = item.get("best_oa_location") or item.get("primary_location") or {}
                    candidates.append({"source":"OpenAlex","title":item.get("display_name"),"year":item.get("publication_year"),"doi":item.get("doi"),"url":loc.get("pdf_url") or loc.get("landing_page_url") or item.get("doi"),"citations":item.get("cited_by_count",0),"type":item.get("type")})
            except Exception as exc:
                errors.append(f"OpenAlex: {exc}")
            try:
                search = client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params={"db":"pubmed","term":topic,"retmode":"json","retmax":max_sources}).json()
                ids = search.get("esearchresult", {}).get("idlist", [])
                if ids:
                    summary = client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params={"db":"pubmed","id":",".join(ids),"retmode":"json"}).json().get("result", {})
                    for pmid in ids:
                        item = summary.get(pmid, {})
                        candidates.append({"source":"PubMed","title":item.get("title"),"year":item.get("pubdate"),"url":f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/","pmid":pmid,"type":"journal-article"})
            except Exception as exc:
                errors.append(f"PubMed: {exc}")
        seen: set[str] = set()
        selected = []
        for item in sorted(candidates, key=lambda x: x.get("citations", 0), reverse=True):
            key = (item.get("doi") or item.get("url") or item.get("title") or "").lower()
            if not key or key in seen:
                continue
            seen.add(key)
            selected.append(item)
            if len(selected) >= max_sources:
                break
        return {"topic": topic, "generated_at": iso(), "selected": selected, "errors": errors}


RESULT_SCHEMA = {"type":"object","properties":{"status":{"type":"string","enum":["complete","audio_pending","needs_google_auth","needs_spotify_auth","failed"]},"stage":{"type":"string"},"summary":{"type":"string"},"notebook_url":{"type":["string","null"]},"audio_path":{"type":["string","null"]},"spotify_episode_id":{"type":["string","null"]},"spotify_url":{"type":["string","null"]},"retry_after_seconds":{"type":["integer","null"]},"error":{"type":["string","null"]}},"required":["status","stage","summary"]}


class AgentRunner:
    def __init__(self, settings: Settings):
        self.settings = settings

    @staticmethod
    def _extract_structured(text: str) -> dict[str, Any]:
        data = json.loads(text)
        if isinstance(data, dict) and isinstance(data.get("structured_output"), dict):
            return data["structured_output"]
        if isinstance(data, dict) and all(k in data for k in ("status", "stage", "summary")):
            return data
        raise ValueError("Claude returned no structured_output")

    def run(self, job: dict[str, Any], workspace: Path) -> dict[str, Any]:
        if self.settings.mock_agent:
            audio = workspace / "mock-audio.m4a"
            audio.write_bytes(b"mock audio")
            return {"status":"complete","stage":"complete","summary":"Mock job complete","audio_path":str(audio),"spotify_episode_id":"mock-episode","spotify_url":"https://open.spotify.com/episode/mock"}
        prompt = (Path(__file__).parent / "prompts" / "headless-system.md").read_text(encoding="utf-8")
        prompt += "\n\nJOB MANIFEST:\n" + json.dumps(job, indent=2)
        prompt += f"\n\nWorkspace: {workspace}\nRepository root: {Path(__file__).parents[1]}"
        cmd = ["claude","-p","--output-format","json","--json-schema",json.dumps(RESULT_SCHEMA),"--permission-mode","bypassPermissions","--model",self.settings.claude_model,"--effort",self.settings.claude_effort,"--max-budget-usd",str(self.settings.claude_budget)]
        if Path(self.settings.mcp_config).exists():
            cmd += ["--mcp-config", self.settings.mcp_config]
        proc = subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=self.settings.agent_timeout, cwd=workspace)
        (workspace / "claude.stdout.json").write_text(proc.stdout, encoding="utf-8")
        (workspace / "claude.stderr.txt").write_text(proc.stderr, encoding="utf-8")
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[-4000:] or f"Claude exited {proc.returncode}")
        return self._extract_structured(proc.stdout)


class Worker:
    def __init__(self, settings: Settings, db: Database):
        self.settings = settings
        self.db = db
        self.research = Researcher(settings)
        self.agent = AgentRunner(settings)

    def notify(self, message: str) -> None:
        if self.settings.telegram_token and self.settings.telegram_chat_id:
            try:
                httpx.post(f"https://api.telegram.org/bot{self.settings.telegram_token}/sendMessage", json={"chat_id":self.settings.telegram_chat_id,"text":message}, timeout=15)
            except Exception:
                pass

    def run_once(self) -> bool:
        job = self.db.claim_next()
        if not job:
            return False
        job_id = job["id"]
        workspace = self.settings.workspace_dir / job_id
        workspace.mkdir(parents=True, exist_ok=True)
        try:
            self.db.event(job_id, "researching", "Discovering scholarly sources")
            research = job.get("research") or self.research.discover(job["topic"], job["max_sources"])
            (workspace / "research.json").write_text(json.dumps(research, indent=2), encoding="utf-8")
            self.db.update(job_id, stage="operating_notebooklm", research=research)
            result = self.agent.run(self.db.get_job(job_id), workspace)
            status = result["status"]
            values: dict[str, Any] = {"status":status,"stage":result.get("stage",status),"result":result,"notebook_url":result.get("notebook_url"),"audio_path":result.get("audio_path"),"spotify_episode_id":result.get("spotify_episode_id"),"spotify_url":result.get("spotify_url"),"error":result.get("error")}
            audio_path = result.get("audio_path")
            if audio_path and Path(audio_path).exists():
                values["audio_fingerprint"] = hashlib.sha256(Path(audio_path).read_bytes()).hexdigest()
            if status == "audio_pending":
                values["next_attempt_at"] = iso(datetime.now(UTC) + timedelta(seconds=int(result.get("retry_after_seconds") or 180)))
            self.db.update(job_id, **values)
            self.db.event(job_id, values["stage"], result.get("summary", status))
            if status == "complete":
                self.notify(f"Research podcast complete\n{job['topic']}\n{result.get('spotify_url') or ''}")
            elif status in {"needs_google_auth", "needs_spotify_auth"}:
                self.notify(f"Research podcast needs attention\n{job['topic']}\n{status}")
        except Exception as exc:
            job = self.db.get_job(job_id)
            if job["attempts"] < self.settings.max_attempts:
                delay = self.settings.retry_base_seconds * (2 ** max(job["attempts"] - 1, 0))
                self.db.update(job_id, status="retry", stage="retry", error=str(exc), next_attempt_at=iso(datetime.now(UTC)+timedelta(seconds=delay)))
                self.db.event(job_id, "retry", f"Attempt failed, retry scheduled: {exc}")
            else:
                self.db.update(job_id, status="failed", stage="failed", error=str(exc))
                self.db.event(job_id, "failed", str(exc))
                self.notify(f"Research podcast failed\n{job['topic']}\n{exc}")
        return True


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    db = Database(settings)
    app = FastAPI(title="Research Podcast Factory")
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

    def auth(x_rpf_token: str | None = Header(default=None)) -> None:
        if not settings.api_token or not x_rpf_token or not hmac.compare_digest(settings.api_token, x_rpf_token):
            raise HTTPException(status_code=401, detail="Invalid API token")

    @app.get("/")
    def home(): return FileResponse(settings.static_dir / "index.html")

    @app.get("/health")
    def health(): return {"ok": True}

    @app.get("/api/jobs", dependencies=[Depends(auth)])
    def list_jobs(limit: int = 50): return {"jobs": db.list_jobs(min(max(limit, 1), 100))}

    @app.get("/api/jobs/{job_id}", dependencies=[Depends(auth)])
    def get_job(job_id: str):
        try: job = db.get_job(job_id)
        except KeyError: raise HTTPException(404, "Job not found")
        job["events"] = db.list_events(job_id)
        return job

    @app.post("/api/shortcut", status_code=201, dependencies=[Depends(auth)])
    def shortcut(body: ShortcutRequest): return db.create_job(body.topic.strip(), body.audience.strip(), body.instructions.strip(), body.max_sources, [])

    @app.post("/api/jobs", status_code=201, dependencies=[Depends(auth)])
    async def create_job(topic: str = Form(...), audience: str = Form("Roman, curious skeptical listener"), instructions: str = Form(""), max_sources: int = Form(10), files: list[UploadFile] = File(default=[])):
        if len(topic.strip()) < 3: raise HTTPException(422, "Topic is required")
        temp_id = str(uuid.uuid4())
        upload_dir = settings.workspace_dir / temp_id / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        uploads = []
        max_bytes = settings.max_upload_mb * 1024 * 1024
        for upload in files:
            safe = Path(upload.filename or "upload").name
            data = await upload.read(max_bytes + 1)
            if len(data) > max_bytes: raise HTTPException(413, f"{safe} exceeds {settings.max_upload_mb} MB")
            path = upload_dir / safe
            path.write_bytes(data)
            uploads.append({"name":safe,"path":str(path),"content_type":upload.content_type or "application/octet-stream"})
        job = db.create_job(topic.strip(), audience.strip(), instructions.strip(), max_sources, uploads)
        final_dir = settings.workspace_dir / job["id"] / "uploads"
        final_dir.parent.mkdir(parents=True, exist_ok=True)
        if upload_dir.exists():
            shutil.move(str(upload_dir), str(final_dir))
            for item in uploads: item["path"] = str(final_dir / item["name"])
            db.update(job["id"], uploads=uploads)
        shutil.rmtree(settings.workspace_dir / temp_id, ignore_errors=True)
        return db.get_job(job["id"])

    @app.post("/api/jobs/{job_id}/retry", dependencies=[Depends(auth)])
    def retry(job_id: str):
        try: db.get_job(job_id)
        except KeyError: raise HTTPException(404, "Job not found")
        db.retry(job_id)
        return db.get_job(job_id)

    @app.post("/api/jobs/{job_id}/cancel", dependencies=[Depends(auth)])
    def cancel(job_id: str):
        try: job = db.get_job(job_id)
        except KeyError: raise HTTPException(404, "Job not found")
        if job["status"] not in TERMINAL:
            db.update(job_id, cancel_requested=True, status="cancelled", stage="cancelled")
            db.event(job_id, "cancelled", "Cancellation requested")
        return db.get_job(job_id)

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["api", "worker", "once"])
    args = parser.parse_args()
    settings = Settings.from_env()
    db = Database(settings)
    if args.mode == "api":
        import uvicorn
        uvicorn.run(create_app(settings), host="0.0.0.0", port=8787)
    else:
        worker = Worker(settings, db)
        if args.mode == "once":
            worker.run_once(); return
        while True:
            worked = worker.run_once()
            time.sleep(1 if worked else settings.poll_seconds)


if __name__ == "__main__":
    main()
