# AI_Media Expression Assets

Use this reference when `llm-wiki-ingest` processes a source that may also produce reusable AI_Media writing material.

## Job

Extract only reusable expression assets from a source after, or alongside, normal LLM Wiki knowledge absorption.

This is not a source summary lane. It is a write-back lane for future writing moves such as:

- title patterns
- opening hooks
- judgment sentences or quotes
- argument structures
- reusable examples
- analogies or explanation frames

## Read First

Before writing assets, inspect the current AI_Media contract:

- `04_Projects/AI_Media/AGENTS.md`
- `04_Projects/AI_Media/80_Assets/README.md`
- `04_Projects/AI_Media/00_System/字段规范.md`
- the target asset file under `04_Projects/AI_Media/80_Assets/`

Use existing asset format in the target file. Do not invent a parallel schema.

## Boundary

- `02_Sources/_clippings` keeps the raw source and provenance.
- `03_Notes` keeps stable knowledge, judgments, distinctions, and questions.
- `04_Projects/AI_Media/80_Assets/*.md` keeps reusable expression assets.
- A Topic's `materials.md` keeps evidence or examples that serve only that one topic.
- `00_System` keeps durable writing/platform/process rules.

The same source can branch into both `03_Notes` and `80_Assets`, but the two outputs must stay semantically separate.

`derived_refs` is an index of downstream outputs, not a status flag.

## Targets

Write accepted assets to the smallest matching file:

| Asset | Target |
| --- | --- |
| titles, title formulas, keywords | `80_Assets/titles.md` |
| openings, scene entries, hooks, contrarian entry points | `80_Assets/hooks.md` |
| judgment sentences, quotable expressions | `80_Assets/quotes.md` |
| argument frames, problem-method-result structures | `80_Assets/arguments.md` |
| reusable cases or proof examples | `80_Assets/examples.md` |
| metaphors, analogies, explanation frames | `80_Assets/analogies.md` |

## Acceptance Bar

An asset candidate must pass all of these:

- reusable across more than one future AI_Media topic
- traceable to a real source via `source_ref` or source URL/path
- improves future writing structure, entry, explanation, judgment, or persuasion
- distinct enough from existing nearby assets to be worth adding
- concise enough to be searched and reused later
- not merely a fact, summary, generic slogan, or one-topic-only evidence

If no candidate passes the acceptance bar, extract zero assets and report the skipped source with a short reason. Do not create placeholder, filler, or weak entries just to satisfy a default count.

Treat any suggested count such as `3-6` as an upper bound, not a quota.

## Do Not Extract

Do not write to `80_Assets` when the candidate is:

- a raw clipping, source summary, or full paragraph copied for storage
- a stable conceptual judgment that belongs in `03_Notes`
- a fact or example that only supports one active Topic
- a generic opening such as "AI is changing everything"
- a title/hook that is catchy but not faithful to the source
- private, credential-like, or operationally sensitive material
- a weak paraphrase made only to fill a template

## Workflow

1. Finish normal source classification and target-page mapping first.
2. Decide whether an AI_Media asset pass is in scope:
   - explicit user request
   - source is about writing, content, tools, AI practice, product judgment, or public expression
   - source contains a clear reusable title/hook/quote/argument/example/analogy
3. Read only the relevant target asset files.
4. Propose accepted candidates in the change package.
5. If the ingest gate returns `confirm` because of write-action risk, include asset writes in the same confirmation package.
6. After approval, or when normal ingest is allowed, append entries to the target asset files and update their `updated` field when present.
7. Update the source-local processing note with either:
   - `AI_Media assets: <n> -> <targets>`
   - `AI_Media assets: 0, reason: <short reason>`

## Entry Shape

Follow the target file's existing style. A compact new entry should include:

```md
## YYYY-MM-DD-source-title-short-label

- asset_kind:
- source_ref:
- source_url:
- source_path:
- author:
- source_date:
- category:
- status: candidate

### 原始素材

### 可复用结构

### 适用场景

### 注意事项
```

Omit unknown optional fields instead of inventing them. Preserve source language only when the exact expression matters; otherwise prefer a reusable Chinese structure faithful to the source.

## Output Note

In the final user response, report asset extraction separately from wiki absorption:

- wiki targets updated or proposed
- asset targets updated or skipped
- skip reason when output is zero
