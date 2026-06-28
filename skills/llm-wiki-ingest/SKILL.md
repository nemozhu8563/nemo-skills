---
name: llm-wiki-ingest
description: Use when one Obsidian source/article/clipping/note/transcript/conversation should be ingested, absorbed, processed, 提炼, 总结, or 吸收 into an LLM Wiki domain, especially when the expected output is durable 03_Notes knowledge and, when useful, reusable AI_Media expression assets rather than a long source-note summary.
---

# LLM Wiki Ingest

Use this skill for normal day-to-day source absorption into a target domain.

## Summary wording means extraction

If the user says `总结`, `提炼`, `吸收`, `ingest`, `absorb`, or `用 llm-wiki` for a source, interpret the request as LLM Wiki extraction:

- write durable knowledge into existing `03_Notes` pages, or create a concept / question / synthesis page only when needed
- update source frontmatter and add a short processing record
- do not paste a long article summary or conversation recap into the source note as the main output

If the user explicitly asks for a source-local abstract only, do that outside this ingest lane.

## Optional AI_Media expression assets

When the source is relevant to AI_Media writing, or the user asks about 素材采集、表达素材、标题、开头、钩子、金句、类比、案例、论证片段, run the optional asset pass in `references/ai-media-expression-assets.md`.

This pass is separate from wiki absorption:

- `03_Notes` gets durable judgments, distinctions, and questions
- `04_Projects/AI_Media/80_Assets/*.md` gets reusable expression assets only when candidates pass the acceptance bar
- topic-specific evidence stays in the target Topic's `materials.md`
- weak sources may produce `0` assets with a short skip reason

## Read these files first

- `02_Sources/LLM Wiki 处理台.base` when the source lives under `02_Sources`
- `.llm-wiki/domains.json`
- `05_Templates/scripts/llm_wiki_policy_gate.py`
- the target domain's MOC
- the target domain's `Wiki Index` / `Wiki Log`, if they exist

Load the specific target pages only after you know which pages the source should update.

## Source ingest workflow

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

### 4. Gate the write by action risk

`bootstrap` and `steady_state` use the same knowledge logic. If a source has extractable durable viewpoints, distinctions, or judgments, write them into the best existing `03_Notes` pages. Do not require user authorization just because the domain is `steady_state`.

Call the canonical gate in `05_Templates/scripts/llm_wiki_policy_gate.py` before write batches:

- normal absorption into existing pages -> `ingest_write --ingest-risk normal` should return `allow`
- review-worthy absorption -> `ingest_write --ingest-risk review` should return `confirm` unless a valid confirmation token is provided

Do **not** use topic words as the review trigger. Legal, medical, psychology, public-health, accident, education, family, parenting, investment, or self-harm-adjacent material can still be absorbed when the write is an abstracted viewpoint rather than advice or fact adjudication.

Use `--ingest-risk review` only when the proposed write would:

- become concrete operational advice, such as treatment, diagnosis, legal action, emergency handling, or investment instruction
- make factual, legal, medical, or accident-responsibility conclusions that the source does not already settle
- rely on current or unstable facts that cannot be safely abstracted into a durable viewpoint
- propagate identifiable private information beyond the source note
- depend on source material that is too short, ambiguous, or contextless to extract a stable point
- create new page families, independent Index / Log / lint surfaces, lifecycle changes, promotion, or demotion

For normal absorption, apply the edits directly and report the concise change package after writing. For review-worthy absorption, stop with a pre-write package containing:

- resolved domain + registry state
- source path and source type
- target pages
- what each page would gain or change
- whether any new page is required and why
- whether `Index` or `Log` also need updates
- whether AI_Media expression assets are proposed, skipped, or out of scope
- whether the gate decision is `allow`, `confirm`, or `deny`

Keep it short and reviewable.

### 5. Apply the edits

When the gate returns `allow`, or when the user approves a `confirm` package:

- update the target wiki pages
- refresh `updated_at`
- append real `source_refs`
- update `Index` if topology changed
- update `Log` with the substantive ingest event
- append approved AI_Media expression assets to the correct `80_Assets/*.md` file only if the optional asset pass produced accepted candidates
- if the domain is `parent_managed`, do not create or mutate independent Index / Log / lint surfaces; surface a promotion proposal instead

## Creation bar

Create a new page only when the source introduces a durable concept, stable repeated question, or new synthesis that truly lacks a home.

## If the thread is still in bootstrap mode

If the registry says the target domain is still `bootstrap`, switch to `../llm-wiki-bootstrap/SKILL.md` behavior for batching and progress reporting. Do not treat `steady_state` itself as a confirmation requirement.
