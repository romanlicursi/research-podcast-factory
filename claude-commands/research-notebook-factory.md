Create a high-signal NotebookLM research notebook from a topic using rigorous source curation, access checks, and reusable media prompts.

Arguments: $ARGUMENTS

Supported flags:
- `--dry-run`: Research and propose sources/prompts, but do not create or modify NotebookLM.
- `--sources-only`: Stop after producing the vetted source list and curation notes.
- `--no-notebook`: Same as dry notebook creation; produce a complete import pack for manual NotebookLM use.
- `--max-sources N`: Target N final sources. Default: 10. Hard range: 6-14.
- `--audience "<text>"`: Override the audience framing.
- `--title "<text>"`: Override the NotebookLM title.

## Purpose

This command captures Roman's "cream of the crop" notebook workflow:

topic
→ define the truth-seeking learning frame
→ find the strongest accessible sources
→ reject weak, broken, paywalled, or institution-only material
→ create/prepare a NotebookLM notebook
→ add sources
→ verify imports
→ generate optimized prompts for Audio Overview, Video Overview, Study Guide/Report, Mind Map, and Flashcards
→ write durable state for later `/process-podcasts`

The goal is not to collect "a lot" of sources. The goal is a compact, powerful research notebook that helps Roman understand a topic deeply without ideological spoon-feeding, fake neutrality, or filler.

## Operating Standard

Act like a ruthless research editor.

The final notebook should contain the minimum set of sources that gives maximum understanding. Prefer 8-12 excellent sources over 25 mediocre ones.

Every recommended source must pass all three tests:

1. **Substance**: It materially improves understanding of the topic.
2. **Credibility**: It is primary text, peer-reviewed scholarship, a respected encyclopedia/reference, a major scholarly book chapter/sample, or a genuinely important thought-leadership source.
3. **Access**: Roman can actually use it in NotebookLM without institutional login, paywall, CAPTCHA, broken URL, or empty import.

If a source is influential but contested, include it only with a curation note explaining how NotebookLM should treat it. Do not hide caveats in chat; put them in the prompt pack.

## Phase 1: Parse the Request

Extract:

- `topic`
- `audience`
- `desired angle`
- `emotional/intellectual intent`
- `forbidden failure modes`

Defaults if not specified:

- Audience: "an intelligent 21-year-old man trying to understand the topic seriously, without ideological hand-holding"
- Angle: "truth-seeking, historically and philosophically honest, charitable to strong opposing views"
- Forbidden failure modes:
  - politically correct flattening
  - partisan or ideological capture
  - vague self-help
  - low-quality pop commentary
  - source spam
  - paywalled or unusable material

Ask at most one clarifying question only if the topic is too ambiguous to search. Otherwise proceed.

## Phase 2: Build the Research Frame

Before searching, write a short internal research frame:

- What is the central question?
- What would count as a strong answer?
- Which disciplines matter? Examples: history, psychology, theology, philosophy, sociology, literary criticism, economics, anthropology.
- What primary sources are mandatory?
- What scholarly debates or schools of interpretation must be represented?
- What would be tempting but low-value filler?

Use this frame to guide source selection.

## Phase 3: Source Discovery

Search broadly, then narrow hard.

Prioritize in this order:

1. **Primary sources**
   - Original essays, books, speeches, texts, interviews, datasets, legal/official documents, historical documents.
   - Use public-domain or openly hosted editions when possible.

2. **Canonical scholarly orientation**
   - Stanford Encyclopedia of Philosophy, Internet Encyclopedia of Philosophy, Oxford/Cambridge/major university open chapters, major academic reference works.

3. **Peer-reviewed open-access scholarship**
   - Journal articles, institutional repositories, university-hosted PDFs, DOAJ/open journals, PubMed/PMC where relevant.

4. **Landmark books or book chapters**
   - Include only if an accessible full text, author excerpt, publisher sample, or legally available chapter exists.
   - If only a sales page exists, do not add it as a NotebookLM source. Mention it separately as "optional outside reading" only if truly important.

5. **High-value thought leadership**
   - Only use when it is genuinely field-shaping or unusually clarifying.
   - Label it as interpretation/commentary, not foundational research.

Avoid:

- SEO summaries
- random blogs
- generic podcasts
- shallow YouTube commentary
- politicized advocacy with no scholarship
- sources that mostly quote other sources
- duplicate versions of the same argument
- inaccessible JSTOR/Taylor & Francis/Cambridge/Oxford pages unless the full text is actually open
- anything that fails import/access checks

## Phase 4: Access Checks

For each candidate source, verify access before recommending it.

Use these checks when available:

- Open the URL.
- For PDFs or downloads, run:
  ```bash
  curl -L -I --max-time 15 "<url>"
  ```
- For webpages, confirm the page returns `200 OK` and visible text is present.
- For PDFs, confirm it is a real PDF or an importable page with useful visible text.
- Avoid sources that return:
  - 401/403/404
  - CAPTCHA
  - institution login
  - "purchase access"
  - empty body
  - redirect loops
  - Cloudflare blocks

If a source is academically excellent but inaccessible, do not put it in the final source list. Add it to "Rejected / Optional Outside Reading" with the reason.

## Phase 5: Final Source Pack

Produce a final source list with 6-14 sources.

For each source include:

- Title
- URL
- Type: primary, reference, peer-reviewed scholarship, book chapter/sample, thought leadership
- Why it earns a slot
- How NotebookLM should treat it
- Access status

Use this quality mix unless the topic demands otherwise:

- 2-4 primary sources
- 1-2 authoritative reference/orientation sources
- 3-6 peer-reviewed or university-grade scholarship sources
- 0-2 thought-leadership/commentary sources

Then produce a brief "source interpretation note" for NotebookLM:

- which sources are foundational
- which are contested
- which are primary vs secondary
- what not to overstate

## Phase 6: NotebookLM Creation / Import

If `--dry-run`, `--sources-only`, or `--no-notebook` is present, do not create the notebook. Produce the full import pack and stop at the requested point.

Otherwise, use available NotebookLM tools if present. Prefer direct NotebookLM MCP tools over browser automation.

For fresh notebook creation, prefer the patched NotebookLM MCP tool:

`mcp__notebooklm__create_notebook`

If this tool is missing, Claude Code is probably still running an old NotebookLM MCP process. Tell Roman to restart Claude Code so the patched server reloads, then rerun the command. If Roman wants to proceed immediately, fall back to browser automation if available or produce a manual import pack.

If `create_notebook` returns an error saying NotebookLM is showing Google sign-in, run `mcp__notebooklm__setup_auth` with the browser visible, wait for Roman to complete Google login, then retry `create_notebook`. Do not treat that as a source-curation or NotebookLM UI failure.

If neither direct NotebookLM tools nor browser automation are available, stop and give Roman the exact source URLs and prompts to paste manually.

Notebook workflow:

1. Create a new NotebookLM notebook with `create_notebook`.
2. Verify the returned notebook URL/id and title.
3. Add the final source URLs.
4. Open Sources and verify the imported source count and titles.
5. Remove failed imports, 404s, empty pages, CAPTCHA pages, or wrong documents.
6. If fewer than 6 strong sources remain, search again and replenish.
7. Record notebook metadata in:
   `~/Documents/NotebookLM-Pipeline/state.json`

If `add_source` fails with an "Add source" selector/button error, do not immediately fall back to manual import. Roman patched the local NotebookLM MCP source-ingestion selectors in `dist/notebooklm/sources.js` and `dist/notebooklm/selectors.js`; restart Claude Code so the MCP reloads, then retry `add_source`. If the failure persists after restart, use the manual import pack.

Extend state.json using this shape:

```json
{
  "notebooks": {
    "<notebook_id>": {
      "notebook_name": "<title>",
      "topic": "<topic>",
      "audience": "<audience>",
      "created_by": "research-notebook-factory",
      "source_count": 10,
      "source_urls": [],
      "source_notes": [],
      "prompt_pack": {
        "audio": "",
        "video": "",
        "study_guide": "",
        "flashcards": ""
      },
      "audio_status": "not_started",
      "spotify_show_id": null,
      "last_error": null
    }
  }
}
```

Do not overwrite existing `/process-podcasts` state fields. Merge carefully.

## Phase 7: Prompt Pack

Generate prompts in the same spirit Roman liked: specific, rigorous, audience-aware, and honest about source hierarchy and controversy.

### Audio Overview Prompt

Use this structure:

```text
Make this a long-form, rigorous, truth-seeking episode on [TOPIC] for [AUDIENCE]. Treat the listener as intelligent and skeptical. Do not flatten the topic into ideology, apologetics, therapeutic slogans, or cheap contrarianism.

Use the primary sources and scholarship to explain: [CORE QUESTIONS / FIGURES / EVENTS / CONCEPTS].

Separate clearly: what the primary sources say, what the strongest scholarship argues, what is contested, and what remains uncertain. Treat [SOURCE CAVEATS] as caveats, not settled fact.

Focus on [KEY THEMES]. Let the strongest opposing views speak in their strongest form before synthesizing.

End with a clear synthesis: what can the listener honestly conclude, what should remain open, and what would be worth studying next.
```

### Video Overview Prompt

Use this structure:

```text
Create a clear, serious explainer video on [TOPIC] for [AUDIENCE]. The tone should be rigorous, calm, and intellectually honest, not preachy, sentimental, partisan, or anti-religious/anti-modern by default.

Structure it around the central question: [CENTRAL QUESTION].

Cover the core concepts in order: [ORDERED CONCEPTS].

Use the sources to distinguish primary evidence from later interpretation. Be honest about what is troubling, contested, or easy to overstate.

End with a sober synthesis: what can the listener honestly learn from this material without pretending certainty they do not have?
```

### Study Guide / Report Prompt

If NotebookLM supports custom reports, use:

```text
Create a study guide that helps an intelligent beginner master [TOPIC]. Include:

1. A concise thesis map of the whole topic.
2. The 10-15 key concepts, each defined precisely.
3. The main figures/texts/events and why they matter.
4. Strongest arguments on each major side.
5. Common misunderstandings to avoid.
6. Source hierarchy: primary, scholarly interpretation, contested commentary.
7. Short-answer questions.
8. Essay questions.
9. A glossary.
10. A final "what to believe, what to doubt, what to study next" section.
```

### Flashcards Prompt

Use:

```text
Create flashcards for the core concepts, figures, texts, debates, and distinctions needed to understand [TOPIC]. Keep card fronts short and card backs precise. Include primary-source concepts, scholarly terms, contested interpretations, and common misunderstandings. Do not make vague cards.
```

## Phase 8: Generate NotebookLM Media

If using NotebookLM directly:

1. Generate Mind Map first.
2. Generate Study Guide / Report.
3. Generate Flashcards with the custom prompt.
4. Generate Video Overview with the custom prompt if available.
5. Generate Audio Overview last or when limits allow, using Long + Deep Dive.

If NotebookLM daily Audio Overview limit is reached:

- Do not treat it as failure.
- Save the audio prompt in state.json.
- Tell Roman exactly where to paste it later.
- Continue with non-audio outputs when possible.

## Phase 9: Summary

End with a concise report:

- Notebook title
- Notebook URL or ID if available
- Final source count
- Sources added
- Sources rejected and why
- Media generated or queued
- Audio prompt saved or submitted
- Whether `/process-podcasts` can now pick it up

## Quality Bar

If the source list feels padded, stop and improve it.

If a source is inaccessible, remove it.

If a source is famous but low-signal for the exact topic, leave it out.

If the topic is controversial, do not enforce false balance. Represent serious disagreement, not every opinion.

If the user asks for "cream of the crop," optimize for maximum learning per source, not neutrality theater.
