# Cloud and Phone Runner

This directory moves the existing Research Podcast Factory off the Mac and onto a persistent server.

```text
iPhone PWA or Shortcut
  -> authenticated FastAPI queue
  -> durable SQLite worker
  -> OpenAlex and PubMed discovery
  -> headless Claude Code
  -> authenticated NotebookLM MCP or browser
  -> resumable Audio Overview polling
  -> save-to-spotify
```

## Deploy

```bash
cd cloud
cp .env.example .env
openssl rand -hex 32
# place the result in RPF_API_TOKEN
docker compose up -d --build
curl http://localhost:8787/health
```

Put HTTPS in front of port 8787. Keep ports 6080 and 9222 private, preferably through Tailscale.

## Claude authentication

Run `claude setup-token` once and copy the printed token into `CLAUDE_CODE_OAUTH_TOKEN` in `.env`.

## Google and NotebookLM authentication

The worker runs Chromium with a persistent profile in `/config/chrome-profile`. Open the private noVNC console on port 6080 from your phone, sign into Google and NotebookLM once, then close it. Configure your working NotebookLM MCP in `/config/mcp.json` and point it at the same Chrome profile or remote debugging port `9222`.

The system intentionally does not hard-code a specific unofficial NotebookLM package. Copy the MCP implementation and selector patches that already make your desktop workflow work.

## Spotify authentication

```bash
docker compose exec worker save-to-spotify auth login --no-browser
docker compose exec worker save-to-spotify shows --json
```

Open the printed authorization URL on your phone, paste the redirect URL back into the prompt, then put the show ID in `RPF_SPOTIFY_SHOW_ID`.

## Phone use

Open the public HTTPS URL on iPhone, enter the API token, then add the app to your Home Screen. You can submit a topic, instructions, and PDFs from Files.

For an iOS Shortcut, POST JSON to `/api/shortcut` with the `X-RPF-Token` header:

```json
{
  "topic": "What does the strongest evidence say about avoidant attachment?",
  "audience": "Roman, curious skeptical listener",
  "instructions": "Emphasize causality and measurement limits.",
  "max_sources": 10
}
```

## Durable states

The worker stores jobs and event history in SQLite and supports:

```text
queued
running
retry
audio_pending
needs_google_auth
needs_spotify_auth
complete
failed
cancelled
```

When NotebookLM is still generating, the Claude operator returns `audio_pending`. The worker schedules another attempt rather than holding a browser and agent process open.

## Tests

```bash
cd cloud
python -m unittest discover -s tests -v
```

The tests use a mock agent and temporary SQLite database. They do not contact Claude, Google, or Spotify.
