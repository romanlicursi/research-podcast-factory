---
name: research-podcast-factory
description: Turn a short topic, question, or phone-captured idea into a source-grounded research podcast workflow for NotebookLM and Spotify. Use when the user asks to make a podcast, NotebookLM notebook, Audio Overview, source pack, prompt pack, Spotify episode, phone-first intake, or cloud/local automation for a learning topic.
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
   - **Cloud NotebookLM Enterprise mode** only if the user has Google Cloud NotebookLM Enterprise access and credentials.
   - **Cloud-native podcast mode** when the user wants phone-to-Spotify with no Mac dependency. Use search/RAG + LLM synthesis + TTS/podcast generation + `save-to-spotify`, not consumer NotebookLM.

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

## Phone-First Intake

The lowest-friction intake should be a one-line capture from the phone:

```text
podcast: <topic>
```

Good capture surfaces:

- iOS Shortcut that appends to a Google Sheet, GitHub issue, or webhook.
- Text message/email to a dedicated inbox that a runner polls.
- Telegram/Discord bot if the user wants chat-style capture.
- Apple Reminders as a local-only option when the Mac is on.

Prefer a queue record with this shape:

```json
{
  "topic": "...",
  "audience": "Roman, curious skeptical listener",
  "mode": "local-notebooklm|cloud-enterprise|cloud-native",
  "status": "new",
  "created_at": "ISO timestamp"
}
```

Use `scripts/queue_topic.py` to append local topic requests to `~/Documents/NotebookLM-Pipeline/topic_queue.jsonl`.

## Cloud Reality

Consumer NotebookLM is not a normal cloud API target. It depends on a logged-in browser/UI path. Do not promise fully cloud consumer NotebookLM unless a real API becomes available.

Cloud options:

- **Best true NotebookLM cloud path:** NotebookLM Enterprise API on Google Cloud, if available to the user. This can support cloud notebook/audio workflows with proper credentials.
- **Best personal NotebookLM path:** Mac mini or always-on Mac runner using authenticated browser/MCP, triggered from a phone queue.
- **Best no-Mac path:** Replace NotebookLM with a cloud-native research podcast generator using web search, source ingestion, LLM synthesis, TTS, and `save-to-spotify`.

Make the tradeoff explicit before building.

## Existing Local Pieces

Known useful commands/files:

```text
~/.claude/commands/notebook-podcast-factory.md
~/.claude/commands/process-podcasts.md
~/Documents/NotebookLM-Pipeline/state.json
/Users/romanlicursi/.local/bin/save-to-spotify
```

When publishing to Spotify, prefer JSON mode so the runner can store episode IDs and skip duplicates.

