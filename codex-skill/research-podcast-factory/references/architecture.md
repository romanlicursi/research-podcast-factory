# Research Podcast Factory Architecture

## Recommended Paths

### 1. Local NotebookLM, Phone Trigger

Best when the user wants actual personal NotebookLM output.

Flow:

```text
iPhone Shortcut / text capture
  -> queue record
  -> Mac runner
  -> Claude Code / Codex command
  -> NotebookLM MCP/browser
  -> Audio Overview
  -> save-to-spotify
  -> Spotify
```

Tradeoff: the Mac must be awake, logged in, and able to run the browser workflow.

### 2. NotebookLM Enterprise Cloud

Best if the user has Google Cloud NotebookLM Enterprise API access.

Flow:

```text
iPhone Shortcut / webhook
  -> Cloud Run / workflow
  -> source curation
  -> NotebookLM Enterprise API
  -> audio overview
  -> save-to-spotify or Spotify publishing service
```

Tradeoff: requires enterprise access, credentials, and Google Cloud setup.

### 3. Cloud-Native Replacement

Best if the user wants fully cloud phone-to-Spotify and can accept a NotebookLM-like podcast rather than actual NotebookLM.

Flow:

```text
iPhone Shortcut / webhook
  -> Cloud Run / worker
  -> web search + source ingestion
  -> LLM synthesis
  -> TTS/dialogue generation
  -> save-to-spotify
  -> Spotify
```

Tradeoff: not NotebookLM; quality depends on custom source curation and prompt design.

## Minimum Viable Phone Intake

Use an iOS Shortcut:

1. Ask for text.
2. POST JSON to a webhook or append a row to a Google Sheet.
3. Record only topic, timestamp, and optional mode.

Example JSON:

```json
{
  "topic": "Simone Weil's Christianity for a skeptical agnostic",
  "mode": "local-notebooklm"
}
```

## Best Near-Term Recommendation

Use local NotebookLM mode with phone queue first. It preserves the actual NotebookLM experience and requires the least new infrastructure. Later, add cloud-native mode for topics where exact NotebookLM output matters less than fully cloud delivery.

