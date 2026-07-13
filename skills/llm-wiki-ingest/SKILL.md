---
name: llm-wiki-ingest
description: Use when one Obsidian source/article/clipping/note/transcript/conversation should be ingested, absorbed, processed, 提炼, 总结, or 吸收 into an LLM Wiki domain, especially when the expected output is durable 03_Notes knowledge and, when useful, reusable AI_Media expression assets rather than a long source-note summary.
---

# LLM Wiki Ingest

Use this skill for normal day-to-day source absorption into a target domain.

## Summary wording means extraction

If the user says `总结`, `提炼`, `吸收`, `ingest`, `absorb`, or `用 llm-wiki` for a source, interpret the request as LLM Wiki extraction:

- write durable knowledge into existing `03_Notes` pages, or create a concept / question / synthesis page only when needed
- close the absorption evidence chain in the source and target notes before marking the source absorbed
- do not paste a long article summary or conversation recap into the source note as the main output

If the user explicitly asks for a source-local abstract only, do that outside this ingest lane.

## Optional AI_Media expression assets

When the source is relevant to AI_Media writing, or the user asks about 素材采集、表达素材、标题、开头、钩子、金句、类比、案例、论证片段, run the optional asset pass in `references/ai-media-expression-assets.md`.

This pass is separate from wiki absorption:

- `03_Notes` gets durable judgments, distinctions, and questions
- `04_Projects/AI_Media/80_Assets/*.md` gets reusable expression assets only when candidates pass the acceptance bar
- topic-specific evidence stays in the target Topic's `materials.md`
- weak sources may produce `0` assets with a short skip reason

## Learning-loop boundary

Do not ingest the `learning-loop` book stack as ordinary wiki source material.

Default ignore scope:

- `02_Sources/_books/<book-slug>/`
- `02_Sources/_intake/books/<book-slug>/`
- `04_Projects/学习/<book-title>/`

If the source comes from these layers:

- do not treat it as normal intake backlog
- do not absorb raw lesson or session artifacts into a domain by default
- only extract when the user explicitly wants to promote a learner-owned durable judgment into `03_Notes`
- otherwise route the work back to `learning-loop`

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
2. inspect the note's `llm_status`; blank is the same intake state as `new`
3. if status is blank, treat it as `new` / 待分流
4. if it claims `absorbed`, inspect `llm_note`, complete `derived_refs`, every `03_Notes` target's reverse `source_refs`, and every accepted asset entry's `source_ref` to the local source note before accepting the claim
5. only then consult `.llm-wiki` routing or bootstrap artifacts for governance context; never use those artifacts as absorption proof

Do not start with global search just to answer "has this source been processed?"

Interpret those fields narrowly:

- every newly captured source note still follows the shared five-field contract: `type: source`, `status: active`, non-empty `title`, non-empty `source`, and explicit `llm_status: new`
- they are the note's operational intake metadata
- they help decide whether this is a fresh ingest candidate or a routed / review / absorbed item
- they do **not** replace `.llm-wiki` for domain registry, policy, lifecycle, topology, or routing governance
- among LLM Wiki-specific fields, only `llm_status` is an intake field; a missing or blank historical value is read as `new`, while new capture entrypoints should write `new` explicitly
- `llm_domain` and `ddc` are optional routing aids; `review` and `ignore` require a reason in `llm_note`, while `llm_note` and `derived_refs` are absorption evidence when the completion gate requires them

Absorption-state truth comes from source frontmatter plus verified target evidence. Never derive or sync `llm_status: absorbed` from `.llm-wiki` registry entries, routing records, bootstrap reports, or lint reports.

For derived sources, extract only durable judgment or clarified distinctions. Do not absorb presentation rhetoric.
For the `learning-loop` book stack, raise the bar further: raw study progress, lesson sequencing, and package organization stay in that system unless the user explicitly asks for judgment promotion.

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

### 5. Apply the edits and close the absorption gate

When the gate returns `allow`, or when the user approves a `confirm` package:

1. Update at least one target wiki page under `03_Notes`, or confirm that the durable knowledge already exists there and use this source as additional evidence.
2. Refresh `updated_at` on substantively changed `03_Notes` pages and append a real frontmatter `source_refs` entry pointing back to the source on every `03_Notes` target.
3. Update `Index` if topology changed and update `Log` with the substantive ingest event when those surfaces are allowed. If the domain is `parent_managed`, do not create or mutate independent Index / Log / lint surfaces; surface a promotion proposal instead.
4. Append approved AI_Media expression assets only when the optional asset pass produced accepted candidates. Add a per-entry `source_ref` pointing to the local source note. Source URL/path may remain as additional provenance, but cannot replace `source_ref`; do not add aggregate-file frontmatter `source_refs` merely for this gate.
5. On the source note, merge the new targets into existing `derived_refs`. Preserve every known prior target and list every knowledge page and accepted expression-asset target from both prior and current runs. Write `llm_note` as a concise statement of what was added, corrected, distinguished, or strengthened.
6. Before changing the source status, read back the source and all downstream files. Verify that every file exists, every `03_Notes` target has reverse `source_refs`, every accepted asset entry has `source_ref` to the local source note, every known target is present in `derived_refs`, and `llm_note` matches the actual contribution.
7. Only after steps 1-6 pass, set `llm_status: absorbed`, then read back the source once more to verify the terminal state. Never mark a source absorbed by changing status alone.

If the knowledge was already present, still add this source to the `03_Notes` target's frontmatter `source_refs`, merge the target into the source's existing `derived_refs`, and write `llm_note` with the explicit wording `仅补强证据，未改变结论`. If the source has no stable value to add or corroborate, set `llm_status: ignore` and explain why in `llm_note`; do not mark it absorbed.

## Creation bar

Create a new page only when the source introduces a durable concept, stable repeated question, or new synthesis that truly lacks a home.

## If the thread is still in bootstrap mode

If the registry says the target domain is still `bootstrap`, switch to `../llm-wiki-bootstrap/SKILL.md` behavior for batching and progress reporting. Do not treat `steady_state` itself as a confirmation requirement.
