from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import runner

rpf_cloud = runner.rpf_cloud


class CloudRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.env = patch.dict(
            os.environ,
            {
                "RPF_DATA_DIR": str(root),
                "RPF_DB_PATH": str(root / "jobs.sqlite3"),
                "RPF_WORKSPACE_DIR": str(root / "jobs"),
                "RPF_API_TOKEN": "test-secret",
                "RPF_MOCK_AGENT": "true",
                "RPF_MAX_ATTEMPTS": "2",
            },
            clear=False,
        )
        self.env.start()
        self.settings = rpf_cloud.Settings.from_env()
        self.db = rpf_cloud.Database(self.settings)
        self.client = TestClient(rpf_cloud.create_app(self.settings))
        self.headers = {"X-RPF-Token": "test-secret"}

    def tearDown(self) -> None:
        self.env.stop()
        self.tmp.cleanup()

    def test_token_required(self) -> None:
        self.assertEqual(self.client.get("/api/jobs").status_code, 401)
        self.assertEqual(self.client.get("/api/jobs", headers=self.headers).status_code, 200)

    def test_create_upload_and_atomic_claim(self) -> None:
        response = self.client.post(
            "/api/jobs",
            headers=self.headers,
            data={
                "topic": "Avoidant attachment evidence",
                "audience": "Roman",
                "instructions": "Be rigorous",
                "max_sources": "10",
            },
            files=[("files", ("paper.pdf", b"%PDF-test", "application/pdf"))],
        )
        self.assertEqual(response.status_code, 201, response.text)
        job = response.json()
        stored = self.db.get_job(job["id"])
        self.assertEqual(len(stored["uploads"]), 1)
        self.assertTrue(Path(stored["uploads"][0]["path"]).exists())
        self.assertIsNotNone(self.db.claim_next())
        self.assertIsNone(self.db.claim_next())

    def test_shortcut_and_mock_worker(self) -> None:
        response = self.client.post(
            "/api/shortcut",
            headers=self.headers,
            json={"topic": "Simone Weil and attention", "max_sources": 8},
        )
        self.assertEqual(response.status_code, 201, response.text)
        worker = rpf_cloud.Worker(self.settings, self.db)
        worker.research.discover = lambda topic, max_sources: {
            "topic": topic,
            "generated_at": rpf_cloud.iso(),
            "selected": [],
            "errors": [],
        }
        self.assertTrue(worker.run_once())
        job = self.db.get_job(response.json()["id"])
        self.assertEqual(job["status"], "complete")
        self.assertEqual(job["spotify_episode_id"], "mock-episode")
        self.assertTrue(job["audio_fingerprint"])
        self.assertEqual(self.db.list_events(job["id"])[-1]["stage"], "complete")

    def test_agent_parser(self) -> None:
        parsed = rpf_cloud.AgentRunner._extract_structured(
            json.dumps(
                {
                    "structured_output": {
                        "status": "audio_pending",
                        "stage": "waiting",
                        "summary": "Still generating",
                    }
                }
            )
        )
        self.assertEqual(parsed["status"], "audio_pending")


if __name__ == "__main__":
    unittest.main()
