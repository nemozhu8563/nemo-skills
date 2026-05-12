---
name: llm-wiki-ingest
description: Use when one Obsidian source/article/clipping/note/transcript/conversation should be ingested, absorbed, processed, 提炼, 总结, or 吸收 into an LLM Wiki domain, especially when the expected output is durable 03_Notes knowledge rather than a long source-note summary.
---

# LLM Wiki Ingest

Use this skill for normal day-to-day source absorption into a target domain.

## Summary wording means extraction

If the user says `总结`, `提炼`, `吸收`, `ingest`, `absorb`, or `用 llm-wiki` for a source, interpret the request as LLM Wiki extraction:

- write durable knowledge into existing `03_Notes` pages, or create a concept / question / synthesis page only when needed
- update source frontmatter and add a short processing record
- do not paste a long article summary or conversation recap into the source note as the main output

If the user explicitly asks for a source-local abstract only, do that outside this ingest lane.

## Read these files first

- `02_Sources/LLM Wiki 处理台.base` when the source lives under `02_Sources`
- `.llm-wiki/domains.json`
- `05_Templates/scripts/llm_wiki_policy_gate.py`
- the target domain's MOC
- the target domain's `Wiki Index` / `Wiki Log`, if they exist

Load the specific target pages only after you know which pages the source should update.

## Steady-state ingest workflow

### 1. Resolve target domain and classify the source

First resolve which domain should absorb the source.

- prefer explicit user-specified `domain_id` / MOC
- otherwise map from current note family / existing domain pages
- if still ambiguous, propose candidate domains instead of silently filing it

Decide whether it is:

- `primary source` — usually from `02_Sources/_clippings` or `02_Sources/_legacy`
- `derived source` — usually from `04_Projects`

For `02_Sources` material, check the intake board before doing anything else:

1. open `02_Sources/LLM Wiki 处理台.base`
2. inspect the note's `llm_status`, `llm_domain`, `ddc`, and `llm_note`
3. if status is blank, treat it as `new` / 待分流
4. only then confirm against `.llm-wiki` routing or bootstrap artifacts if needed

Do not start with global search just to answer "has this source been processed?"

Interpret those fields narrowly:

- they are the note's operational intake metadata
- they help decide whether this is a fresh ingest candidate or a routed / review / absorbed item
- they do **not** replace `.llm-wiki` as the truth / governance layer

For derived sources, extract only durable judgment or clarified distinctions. Do not absorb presentation rhetoric.

### 2. Map the source to 1-3 target pages

Default to existing pages. Good targets are usually:

- one concept page
- one question page
- sometimes one synthesis page

### 3. Apply the update-first rule

Prefer:

1. sharpen an existing definition
2. add a missing boundary or counterexample
3. revise a current synthesis judgment
4. only then consider a new page

### 4. Produce a change package before writing

In `steady_state`, do not silently write first.

Call the canonical gate in `05_Templates/scripts/llm_wiki_policy_gate.py` before any write:

- `bootstrap` -> ingest may `allow`
- `steady_state` -> ingest should return `confirm` unless a valid confirmation token is provided

Your change package should contain:

- resolved domain + registry state
- source path and source type
- target pages
- what each page would gain or change
- whether any new page is required and why
- whether `Index` or `Log` also need updates
- whether the gate decision is `allow`, `confirm`, or `deny`

Keep it short and reviewable.

### 5. After approval, apply the edits

When the user approves:

- update the target wiki pages
- refresh `updated_at`
- append real `source_refs`
- update `Index` if topology changed
- update `Log` with the substantive ingest event
- if the domain is `parent_managed`, do not create or mutate independent Index / Log / lint surfaces; surface a promotion proposal instead

## Creation bar

Create a new page only when the source introduces a durable concept, stable repeated question, or new synthesis that truly lacks a home.

## If the thread is still in bootstrap mode

If the registry says the target domain is still `bootstrap`, switch to `../llm-wiki-bootstrap/SKILL.md` behavior instead of enforcing steady-state confirmation.
