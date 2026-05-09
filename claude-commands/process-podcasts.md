Generate NotebookLM audio overviews and upload them to Spotify as podcast episodes.

Flags: $ARGUMENTS
- `--dry-run`: Show what would happen without making changes
- `--force`: Re-upload even if audio fingerprint matches previous upload

## Overview

This skill automates the full pipeline: generate audio in NotebookLM, poll until ready, download, and upload to Spotify via `save-to-spotify`. State is tracked in `~/Documents/NotebookLM-Pipeline/state.json` so the process is resumable and idempotent.

## Instructions

Execute each phase sequentially. After every mutation, write state.json immediately.

### Phase 1: Preflight

1. Check NotebookLM auth: call `mcp__notebooklm__get_health`. If `authenticated=false`, run `mcp__notebooklm__setup_auth` and re-check. If still not authenticated, stop and tell the user.

2. Check Spotify auth:
```bash
/Users/romanlicursi/.local/bin/save-to-spotify auth status --json
```
If `token_valid` is false, tell the user to run `save-to-spotify auth login` and stop.

3. Load or initialize state file at `~/Documents/NotebookLM-Pipeline/state.json`. If it doesn't exist, create it with this structure:
```json
{
  "version": 1,
  "config": {
    "auto_create_shows": false,
    "episode_title_format": "{notebook_name} — {date}",
    "download_dir": "/Users/romanlicursi/Downloads/notebooklm-audio"
  },
  "notebooks": {}
}
```
Ensure the download directory exists (`mkdir -p`).

4. List all notebooks via `mcp__notebooklm__list_notebooks`.

### Phase 2: Selection

Show a numbered table of all notebooks with columns:
| # | Name | Description | State |

State is derived from state.json for known notebooks:
- `new` — not in state.json yet
- `generating` — audio generation in progress
- `ready` — audio ready to download
- `downloaded` — audio downloaded locally
- `uploaded` — already uploaded to Spotify
- `error` — last attempt failed (show last_error)

Ask the user which notebooks to process. Accept:
- `all` — process everything
- Comma-separated numbers like `1,3,5`
- A range like `1-4`

If `$ARGUMENTS` contains `--dry-run`: for each selected notebook, print what action would be taken (generate/poll/download/upload/skip) and stop. Do not make any changes.

### Phase 3: Spotify Show Mapping

1. List existing shows:
```bash
/Users/romanlicursi/.local/bin/save-to-spotify shows --json
```

2. For each selected notebook, try to match it to an existing show by name (case-insensitive substring match of notebook name in show title, or vice versa).

3. For unmatched notebooks:
   - If `config.auto_create_shows` is true: create a show automatically using:
     ```bash
     /Users/romanlicursi/.local/bin/save-to-spotify shows create --title "<notebook_name>" --json
     ```
   - Otherwise: list the unmatched notebooks and ask the user for each one whether to:
     - Create a new show with the notebook name
     - Map to an existing show (by number)
     - Skip this notebook

4. Store the `spotify_show_id` in state.json for each notebook.

### Phase 4: Sequential Generate + Download + Upload

Process each selected notebook one at a time. Resume from wherever it left off based on `audio_status` in state.json:

#### Status: `uploaded` (and no `--force`)
Skip. Print "Already uploaded, skipping."

#### Status: `downloaded`
Go directly to Upload step.

#### Status: `ready`
Go directly to Download step.

#### Status: `generating`
Go directly to Poll step.

#### Status: `not_started` or `new` or absent
**Generate**: Call `mcp__notebooklm__generate_audio` with `notebook_id`. Update state to `generating`. Write state.json.

**Poll**: Call `mcp__notebooklm__get_audio_status` with `notebook_id` every ~30 seconds. Timeout after 12 minutes (24 polls).
- If status becomes `ready`: update state, continue to Download.
- If timeout: set state to `error`, set `last_error` to "Audio generation timed out after 12 minutes", write state.json, continue to next notebook.
- If rate-limit error: ask user whether to continue with upload-only notebooks or stop entirely. Write state.json and print: "Run `/process-podcasts` again to resume where you left off."

**Download**: Call `mcp__notebooklm__download_audio` with `notebook_id` and `destination_dir` set to the config download_dir. Update `local_audio_path` in state.
- Compute md5 of the downloaded file:
  ```bash
  md5 -q "<file_path>"
  ```
- Store as `audio_fingerprint` in state. Update status to `downloaded`. Write state.json.
- On failure: retry once. If the error mentions a selector, download button, more menu, or NotebookLM Studio UI change, tell Roman to restart Claude Code so the patched NotebookLM MCP audio selectors reload, then retry before asking for manual download. If it still fails after restart, ask Roman for the manually downloaded file path and continue the Spotify upload from that file. For other failures, set state to `error`, set `last_error`, write state.json, continue to next notebook.

**Upload**:
- **Idempotency check**: If `audio_fingerprint` matches the existing fingerprint in state AND `uploaded_episode_id` exists AND `--force` is NOT set: skip upload, print "Audio unchanged, skipping re-upload."
- Format episode title using `config.episode_title_format`. Replace `{notebook_name}` with the notebook name and `{date}` with today's date (YYYY-MM-DD).
- Upload:
  ```bash
  /Users/romanlicursi/.local/bin/save-to-spotify upload "<local_audio_path>" --title "<episode_title>" --show-id "<spotify_show_id>" --json
  ```
- Parse the JSON output for the episode ID/URI. Store `uploaded_episode_id` and `uploaded_at` (ISO timestamp) in state. Update status to `uploaded`. Write state.json.
- On failure: set state to `error`, set `last_error`, write state.json, continue to next notebook.

**After each step**: Always write state.json immediately so progress survives interruption.

### Phase 5: Summary Report

Print a results table:
| Notebook | Status | Audio File | Spotify Episode |
Show totals: X uploaded, Y skipped, Z failed.

If any failed, print:
> Run `/process-podcasts` again to resume where you left off.

## Error Handling

- **Auth expired (either service)**: Stop immediately, write state.json, report what completed so far.
- **Audio generation timeout**: Mark as error, skip, continue to next notebook.
- **Upload failure**: Log error in state, continue to next notebook.
- **Rate limit**: Ask user to stop or continue with upload-only items. Write state, print resume instruction.
- **Download failure**: Retry once, then mark error, continue.

## State File

Path: `~/Documents/NotebookLM-Pipeline/state.json`

This file is the source of truth for resumability. Always read it at startup, always write after every mutation. The schema is designed to be extensible for future commands like `/research-notebook-factory`.

## CLI Reference

- Upload: `save-to-spotify upload <file> --title <title> --show-id <id> --json`
- Create show: `save-to-spotify shows create --title <title> --json`
- List shows: `save-to-spotify shows --json`
- Auth check: `save-to-spotify auth status --json`
- Binary path: `/Users/romanlicursi/.local/bin/save-to-spotify`
