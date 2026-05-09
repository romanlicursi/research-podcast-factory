# Cloud Options

There are three realistic paths.

## 1. Personal NotebookLM With A Mac Runner

Use this if you want the actual NotebookLM Audio Overview.

```text
iPhone Shortcut
  -> queue
  -> Mac runner
  -> local NotebookLM operator
  -> NotebookLM
  -> save-to-spotify
```

This is the easiest path to get working today. Claude Code can be the operator for this path, and Codex can help maintain the workflow, but the actual system is phone -> queue -> Mac -> NotebookLM -> Spotify. The tradeoff is that your Mac must be awake and logged in.

## 2. NotebookLM Enterprise

Use this if you have Google Cloud NotebookLM Enterprise access.

```text
iPhone Shortcut
  -> authenticated cloud endpoint
  -> source curation
  -> NotebookLM Enterprise API
  -> audio output
  -> Spotify publishing
```

This is the cleanest true cloud path for NotebookLM-style work, but it requires enterprise access and credentials.

## 3. NotebookLM-Like Generator

Use this if phone-to-Spotify matters more than using NotebookLM itself.

```text
iPhone Shortcut
  -> cloud endpoint
  -> web search and source ingestion
  -> synthesis
  -> TTS dialogue
  -> Spotify publishing
```

This path can run fully in the cloud. The cost is that you now own the quality of the source selection, prompting, and audio format.
