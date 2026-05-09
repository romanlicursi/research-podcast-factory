---
name: research-podcast-factory
description: Turn a short topic or question into a source-grounded research podcast workflow for NotebookLM and Spotify. Use when the user asks to make a podcast, NotebookLM notebook, Audio Overview, source pack, prompt pack, Spotify episode, or local research-audio workflow for a learning topic.
---

# Research Podcast Factory

Use this skill to reduce the user's input to one short topic while preserving the rigorous workflow already developed: excellent accessible sources, NotebookLM prompts, audio generation, and Spotify delivery.

## Fast Intake

Accept very short requests. Do not make the user retype standards.

Examples:

```text
Use $research-podcast-factory: Simone Weil for a skeptical agnostic
```

```text
Podcast topic: Dostoevsky's answer to atheism and old Christianity
```

Infer defaults:

- Audience: Roman, curious and skeptical, wants depth without fake certainty.
- Source bar: best available sources, accessible without institutional login.
- Output: NotebookLM source list, prompt pack, long-form Audio Overview, Spotify episode.
- Voice: serious, clear, non-corporate, no AI-slop phrasing.
- State: preserve resume points and avoid duplicate Spotify uploads.

If the topic is ambiguous, ask one concise clarifying question. Otherwise proceed.

## Workflow

1. Normalize the topic into:
   - working title
   - core question
   - intended listener
   - source standards
   - excluded angles, if obvious

2. Choose execution mode:
   - **Local NotebookLM mode** when the user wants actual personal NotebookLM. Requires the Mac, authenticated browser, and NotebookLM MCP/browser tools.
   - **Manual import mode** when NotebookLM tools are unavailable. Produce the source pack and prompt pack.

3. Curate sources:
   - Prefer primary texts, peer-reviewed/open-access scholarship, university pages, reputable archives, and respected long-form analysis.
   - Check that each source is actually usable by the target system.
   - Reject paywalls, abstract-only pages, dead PDFs, weak SEO summaries, and sources that cannot be legally/practically ingested.
   - Record rejected sources and why.

4. Build prompt pack:
   - audio overview prompt
   - study guide prompt
   - flashcards prompt
   - mind map/report prompt when useful
   - caveats telling NotebookLM how to treat source types

5. Generate and publish:
   - Create/import notebook and sources when using NotebookLM.
   - Trigger/poll/download audio.
   - Upload audio with `save-to-spotify`.
   - Store state after each step.

## Local Topic Queue

The local queue is optional. It is useful when the user wants to save multiple topics and process them later.

Use `scripts/queue_topic.py` to append local topic requests to `~/Documents/NotebookLM-Pipeline/topic_queue.jsonl`.

Queue record shape:

```json
{
  "topic": "...",
  "audience": "Roman, curious skeptical listener",
  "mode": "local-notebooklm",
  "status": "new",
  "created_at": "ISO timestamp"
}
```

## Local Reality

Consumer NotebookLM is not a normal public API target. It depends on a logged-in browser/UI path. Do not promise full background execution unless a working local NotebookLM tool or browser path is available.

When publishing to Spotify, prefer JSON mode so the runner can store episode IDs and skip duplicates.

## Existing Local Pieces

Known useful commands/files:

```text
~/.claude/commands/notebook-podcast-factory.md
~/.claude/commands/process-podcasts.md
~/Documents/NotebookLM-Pipeline/state.json
/Users/romanlicursi/.local/bin/save-to-spotify
```
