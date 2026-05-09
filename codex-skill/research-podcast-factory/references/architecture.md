# Research Podcast Factory Architecture

## Local NotebookLM Workflow

Best when the user wants actual personal NotebookLM output.

Flow:

```text
topic
  -> source curation
  -> NotebookLM MCP/browser
  -> Audio Overview
  -> downloaded audio
  -> save-to-spotify
  -> Spotify
```

Tradeoff: the Mac must be awake, logged in, and able to run the browser workflow. Claude Code can be the operator for this path; Codex can help maintain the skill and scripts.

## Optional Local Queue

Use the queue when the user wants to save a list of topics and process them later.

```text
queue_topic.py
  -> topic_queue.jsonl
  -> queue_worker.py --next
  -> /notebook-podcast-factory ...
```

## Save To Spotify

`save-to-spotify` uploads an existing audio file to Spotify as an episode. It does not generate audio. In this workflow, NotebookLM generates the audio and `save-to-spotify` publishes the downloaded file.
