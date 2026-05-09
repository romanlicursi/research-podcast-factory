Create a cream-of-the-crop NotebookLM notebook from a topic, generate NotebookLM media, then process finished audio into Spotify.

Arguments: $ARGUMENTS

Supported flags:
- `--dry-run`: Research/propose the whole pipeline without creating notebooks, generating media, or uploading.
- `--sources-only`: Stop after source curation.
- `--no-upload`: Create the NotebookLM notebook and media, but do not upload to Spotify.
- `--upload-only`: Skip source curation and process existing/ready NotebookLM audio into Spotify.
- `--force`: Re-upload even if state says the same audio was already uploaded.
- `--max-sources N`: Target N final sources. Default: 10. Hard range: 6-14.
- `--audience "<text>"`: Override audience framing.
- `--title "<text>"`: Override NotebookLM title.

## Purpose

This is the single-command version of Roman's full workflow:

topic
→ truth-seeking research frame
→ cream-of-the-crop accessible source curation
→ NotebookLM notebook creation
→ source import and failed-source cleanup
→ optimized Audio/Video/Study Guide/Flashcards prompts
→ NotebookLM media generation
→ audio polling/download
→ Spotify podcast upload
→ persistent state for resume/idempotency

Internally, follow the standards from:

- `/research-notebook-factory` for source curation, NotebookLM creation, and prompt generation.
- `/process-podcasts` for polling, downloading, Spotify show mapping, uploading, and state handling.

Do not literally call those slash commands. Execute their workflows directly in this run, using the same standards and state file.

## Hard Constraints

- Consumer NotebookLM automation requires local NotebookLM auth and usually a browser/MCP session. The Mac must be on and Claude Code must have working NotebookLM tools/browser automation.
- This is a local automation workflow. Consumer NotebookLM requires a logged-in browser/MCP path.
- Daily NotebookLM generation limits are normal. If hit, save state and give exact resume instructions.
- Spotify show creation requires explicit user confirmation unless config says auto-create.
- Never upload duplicate audio unless `--force` is present.

## State

Use:

`~/Documents/NotebookLM-Pipeline/state.json`

Initialize if missing:

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

Write state immediately after every mutation.

For each notebook, track:

- notebook_id
- notebook_name
- notebook_url
- topic
- audience
- created_by: "notebook-podcast-factory"
- source_count
- source_urls
- source_notes
- rejected_sources
- prompt_pack.audio
- prompt_pack.video
- prompt_pack.study_guide
- prompt_pack.flashcards
- media_status.mind_map
- media_status.report
- media_status.video
- media_status.flashcards
- audio_status
- local_audio_path
- audio_fingerprint
- spotify_show_id
- uploaded_episode_id
- uploaded_at
- last_error

Merge with existing state. Never erase fields written by `/process-podcasts`.

## Phase 1: Preflight

1. Parse `$ARGUMENTS` for topic and flags.
2. If `--upload-only`, skip directly to Phase 8.
3. Check NotebookLM auth/tool availability:
   - Prefer `mcp__notebooklm__get_health` if available.
   - Prefer `mcp__notebooklm__create_notebook` for fresh notebook creation.
   - If `create_notebook` is not visible, tell Roman to restart Claude Code so the patched NotebookLM MCP reloads. Then offer a resume/manual path.
   - If `create_notebook` reports Google sign-in, run `mcp__notebooklm__setup_auth` with the browser visible, let Roman complete login, then retry `create_notebook`.
   - If direct NotebookLM tools are unavailable, use browser automation if available.
   - If neither is available, perform source curation and produce a manual import pack, then stop.
4. Check Spotify auth unless `--no-upload`, `--dry-run`, or `--sources-only`:
   ```bash
   /Users/romanlicursi/.local/bin/save-to-spotify auth status --json
   ```
5. Load/init state.

## Phase 2: Research Frame

Extract:

- topic
- audience
- central question
- desired angle
- likely disciplines
- required primary sources
- major scholarly debates
- forbidden failure modes

Default audience:

"an intelligent 21-year-old man trying to understand the topic seriously, without ideological hand-holding"

Default angle:

"truth-seeking, historically and philosophically honest, charitable to strong opposing views, allergic to low-quality commentary"

Ask at most one clarifying question only if the topic is too ambiguous to search.

## Phase 3: Cream-of-the-Crop Source Curation

Follow the `/research-notebook-factory` standard:

- Search broadly.
- Prefer primary sources, authoritative reference entries, peer-reviewed open scholarship, university-hosted PDFs, public-domain editions, and truly landmark thought leadership.
- Reject source spam, SEO summaries, weak blogs, inaccessible paywalled material, CAPTCHA pages, Cloudflare blocks, broken PDFs, institution-only pages, and shallow commentary.
- Verify access before finalizing.

Each final source must pass:

1. Substance
2. Credibility
3. Access

Target 8-12 final sources unless `--max-sources` says otherwise.

For each final source, produce:

- title
- URL
- type
- why it earns a slot
- how NotebookLM should treat it
- access status

Also record rejected/optional sources with reasons.

If `--sources-only` or `--dry-run`, stop after producing the final source pack and prompt pack. Do not create NotebookLM or upload anything.

## Phase 4: Create NotebookLM Notebook

Use direct NotebookLM MCP tools if they exist. Prefer the local patched tool:

`mcp__notebooklm__create_notebook`

This tool should create the notebook with NotebookLM's authenticated browser profile, title it, register it in the local NotebookLM MCP library, and return:

- `notebook_id`
- `notebook_url`
- registered notebook metadata

If this tool is missing, Claude Code is probably still running an old MCP process. Tell Roman:

> Restart Claude Code so the patched NotebookLM MCP exposes `create_notebook`, then rerun this command.

If the tool returns an error saying NotebookLM is showing Google sign-in, do **not** assume the Create button selector is broken. Run:

`mcp__notebooklm__setup_auth`

with the browser visible, wait for Roman to complete Google login, then retry `create_notebook`.

Only fall back to browser automation or manual creation if Roman wants to proceed without restarting.

Autonomous target behavior:

1. Call `create_notebook` with the generated title, description, topics, content types, use cases, and tags.
2. Verify the returned notebook URL/id.
3. Add all final source URLs.
4. Open Sources and verify actual imported titles/count.
5. Remove failed imports, wrong pages, 404s, empty pages, or CAPTCHA pages.
6. If too many sources fail and fewer than 6 strong sources remain, search again and replenish.
7. Save notebook URL/ID and source metadata to state.

If login, CAPTCHA, or UI breakage blocks notebook creation, stop and output the manual import pack.

If `add_source` fails with an "Add source" selector/button error, do not immediately fall back to manual import. Roman patched the local NotebookLM MCP source-ingestion selectors in `dist/notebooklm/sources.js` and `dist/notebooklm/selectors.js`; restart Claude Code so the MCP reloads, then retry `add_source`. If the failure persists after restart, use the manual import pack.

## Phase 5: Prompt Pack

Generate and save four prompts.

### Audio

```text
Make this a long-form, rigorous, truth-seeking episode on [TOPIC] for [AUDIENCE]. Treat the listener as intelligent and skeptical. Do not flatten the topic into ideology, apologetics, therapeutic slogans, or cheap contrarianism.

Use the primary sources and scholarship to explain: [CORE QUESTIONS / FIGURES / EVENTS / CONCEPTS].

Separate clearly: what the primary sources say, what the strongest scholarship argues, what is contested, and what remains uncertain. Treat [SOURCE CAVEATS] as caveats, not settled fact.

Focus on [KEY THEMES]. Let the strongest opposing views speak in their strongest form before synthesizing.

End with a clear synthesis: what can the listener honestly conclude, what should remain open, and what would be worth studying next.
```

### Video

```text
Create a clear, serious explainer video on [TOPIC] for [AUDIENCE]. The tone should be rigorous, calm, and intellectually honest, not preachy, sentimental, partisan, sentimental, or anti-religious/anti-modern by default.

Structure it around the central question: [CENTRAL QUESTION].

Cover the core concepts in order: [ORDERED CONCEPTS].

Use the sources to distinguish primary evidence from later interpretation. Be honest about what is troubling, contested, or easy to overstate.

End with a sober synthesis: what can the listener honestly learn from this material without pretending certainty they do not have?
```

### Study Guide

```text
Create a study guide that helps an intelligent beginner master [TOPIC]. Include: a concise thesis map, 10-15 key concepts, main figures/texts/events, strongest arguments on each major side, common misunderstandings, source hierarchy, short-answer questions, essay questions, glossary, and a final "what to believe, what to doubt, what to study next" section.
```

### Flashcards

```text
Create flashcards for the core concepts, figures, texts, debates, and distinctions needed to understand [TOPIC]. Keep card fronts short and card backs precise. Include primary-source concepts, scholarly terms, contested interpretations, and common misunderstandings. Do not make vague cards.
```

Customize these templates to the actual topic. Do not paste generic placeholders.

## Phase 6: Generate NotebookLM Media

Generate in this order:

1. Mind Map
2. Study Guide / Report
3. Flashcards using custom prompt
4. Video Overview using custom prompt if available
5. Audio Overview using custom prompt, Deep Dive, Long

If audio limit is reached:

- Save prompt pack and media state.
- Mark `audio_status` as `limit_reached`.
- If `--no-upload` is not present, explain that upload can resume later via this command or `/process-podcasts`.
- Continue generating non-audio outputs if possible.

## Phase 7: Wait for Audio

If `--no-upload`, stop after media generation and summary.

Otherwise:

1. Poll NotebookLM audio status every ~30 seconds.
2. Timeout after 12 minutes.
3. If ready, download to:
   `/Users/romanlicursi/Downloads/notebooklm-audio`
4. Compute fingerprint:
   ```bash
   md5 -q "<file_path>"
   ```
5. Save local path/fingerprint/status to state.

If `download_audio` fails with a selector/button/menu error, do not immediately ask Roman to download manually. Roman patched the local NotebookLM MCP audio selectors in `dist/notebooklm/audio.js` and `dist/notebooklm/selectors.js`; restart Claude Code so the MCP reloads, then retry `download_audio`. If it still fails after restart, then ask Roman for a manual download path and continue the Spotify upload from that file.

If timeout or limit:

- Save state.
- Give resume instruction:
  `/notebook-podcast-factory --upload-only`
  or
  `/process-podcasts`

## Phase 8: Spotify Upload

Use `/process-podcasts` logic directly.

1. List Spotify shows:
   ```bash
   /Users/romanlicursi/.local/bin/save-to-spotify shows --json
   ```
2. Match notebook title to show title.
3. If unmatched, ask before creating a show unless config says auto-create.
4. If already uploaded and no `--force`, skip.
5. Upload:
   ```bash
   /Users/romanlicursi/.local/bin/save-to-spotify upload "<local_audio_path>" --title "<episode_title>" --show-id "<spotify_show_id>" --json
   ```
6. Save episode ID/URI and uploaded_at.

## Phase 9: Summary

Report:

- notebook title and URL/ID
- final source count
- sources added
- rejected sources and why
- media generated/queued
- audio status
- local audio path if downloaded
- Spotify episode link/ID if uploaded
- exact resume command if anything remains

## Quality Bar

Do not optimize for speed over source quality.

Do not add inaccessible papers.

Do not upload duplicate audio.

Do not claim cloud/offline automation unless using a real cloud API.

If the NotebookLM UI/API cannot execute autonomously, fall back gracefully to a complete manual import pack rather than pretending success.
