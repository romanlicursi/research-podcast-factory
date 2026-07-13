from __future__ import annotations

import json
import uuid
from typing import Any

import rpf_cloud


def create_job_fixed(self: rpf_cloud.Database, topic: str, audience: str, instructions: str, max_sources: int, uploads: list[dict[str, str]]) -> dict[str, Any]:
    job_id = str(uuid.uuid4())
    now = rpf_cloud.iso()
    with self.connect() as conn:
        conn.execute(
            """insert into jobs(
                 id,topic,audience,instructions,max_sources,status,stage,
                 created_at,updated_at,uploads_json,next_attempt_at
               ) values(?,?,?,?,?,'queued','queued',?,?,?,?)""",
            (job_id, topic, audience, instructions, max_sources, now, now, json.dumps(uploads), now),
        )
        conn.execute(
            "insert into events(job_id,stage,message,created_at) values(?,?,?,?)",
            (job_id, "queued", "Job queued", now),
        )
    return self.get_job(job_id)


rpf_cloud.Database.create_job = create_job_fixed

if __name__ == "__main__":
    rpf_cloud.main()
