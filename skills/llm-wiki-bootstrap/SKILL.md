---
name: llm-wiki-bootstrap
description: Continue or initialize one Obsidian LLM Wiki domain by repeatedly absorbing existing sources into the domain wiki. Use when the user says 初始化、继续初始化、批量吸收、先把现有知识做成 wiki, or wants bootstrap to keep running without per-package confirmation for a bootstrap-state domain.
---

# LLM Wiki Bootstrap

Use this skill while the target domain is still in `bootstrap`, or when the user explicitly wants batch absorption behavior.

This is not a different knowledge logic from steady-state ingest. It is the same single-source absorption loop, repeated in batches. The difference is batching and progress reporting, not a stricter or looser truth standard.

## Read these files first

- `02_Sources/LLM Wiki 处理台.base`
- `.llm-wiki/domains.json`
- `05_Templates/scripts/llm_wiki_policy_gate.py`
- the target domain's MOC
- if they exist, the target domain's `Wiki Index` and `Wiki Log`

## Bootstrap policy

- For normal absorption into existing `03_Notes` pages, per-source or per-package ingest confirmation is not required.
- Keep processing until you hit a real blocker or the user explicitly says initialization is complete.
- Ask only if the work would leave the target domain scope, introduce a clearly new page family, conflict with the domain's current operating surfaces, or hit a review-worthy write risk.
- Before each write batch, check the gate with `05_Templates/scripts/llm_wiki_policy_gate.py` using `ingest_write --ingest-risk normal` for ordinary page updates.
- Bootstrap exit itself is not automatic: `bootstrap -> steady_state` requires confirmation via the canonical gate.
- If the target domain is `parent_managed`, do not create or mutate independent Index / Log / lint surfaces.
- Do not pull the `learning-loop` book stack into bootstrap queue construction by default. `02_Sources/_books/...`, `02_Sources/_intake/books/...`, and `04_Projects/学习/...` belong to the learning system unless the user explicitly wants a mature learner-owned judgment promoted into `03_Notes`.

Do not send material to review merely because the topic mentions law, medicine, mental health, public health, accident, education, family, parenting, investment, or self-harm. Send it to review only when the write would become concrete advice, make responsibility/fact conclusions, rely on unstable facts, propagate private information, lack enough context, or require new independent operating surfaces.

For `02_Sources` queue checks, keep the shared five-field capture contract distinct from LLM Wiki-only metadata. Every newly captured source note should have `type: source`, `status: active`, non-empty `title`, non-empty `source`, and explicit `llm_status: new`.

Default interpretation:

- a missing or blank historical `llm_status` means `new` / `待分流`; new capture entrypoints still write `new` explicitly
- among LLM Wiki-specific fields, only `llm_status` is an intake field
- `llm_domain` and `ddc` are optional routing aids, not capture requirements
- `review` and `ignore` require a reason in `llm_note`; `llm_note` and `derived_refs` are absorption evidence when closing the completion gate
- frontmatter is queue-local operational metadata
- `.llm-wiki` remains governance truth for domain registry, policy, lifecycle, topology, and routing context
- source frontmatter plus verified target evidence is the truth for source absorption state

## Batch workflow

### 1. Build or refresh the candidate queue

Prefer this order:

1. `02_Sources/LLM Wiki 处理台.base` views such as `待分流`, `已路由待吸收`, `待复核`
2. `02_Sources/_clippings` and `02_Sources/_legacy`
2. already-known domain source lists in `Index`
3. only then relevant derived material in `04_Projects`

For bootstrap queue construction, prefer the Base as the first operating surface and use raw folder listing only as a fallback or reconciliation pass.

If a candidate's Base position disagrees with `.llm-wiki` about domain registry, policy, lifecycle, topology, or routing context, trust `.llm-wiki`. For absorption state, never derive or sync `llm_status: absorbed` from a registry, routing record, bootstrap report, or lint report; source frontmatter and the full evidence chain must pass the completion gate.

Do not start bootstrap queue discovery with repo-wide search. Use search only as a fallback when reconciling downstream references or investigating suspected drift.

Explicitly exclude `02_Sources/_books/...`, `02_Sources/_intake/books/...`, and `04_Projects/学习/...` from the default bootstrap queue. Do not treat lesson notes, course maps, curriculum files, study-session notes, or raw book packages as batch-ingest candidates unless the user explicitly asks for judgment promotion.

### 2. Process one source at a time

For each source:

1. classify it as `primary` or `derived`
2. identify the best `1-3` target pages
3. update existing pages first
4. create a new page only if the schema's `create only when necessary` bar is met
5. avoid copying rhetorical wrappers from source material
6. if the change would require new independent operating surfaces for a `parent_managed` domain, stop and surface a promotion proposal instead of writing

### 3. Close the completion gate for every source

Batching never lowers the single-source completion standard. For each source:

1. Actually update at least one `03_Notes` target, or confirm that the durable knowledge already exists and add the source as corroborating evidence.
2. Add the source to every `03_Notes` target's frontmatter `source_refs`.
3. For every accepted AI_Media expression asset, add a per-entry `source_ref` pointing to the local source note. Source URL/path may remain as additional provenance, but cannot replace `source_ref`; do not add aggregate-file frontmatter `source_refs` merely for this gate.
4. On the source, merge new targets into existing `derived_refs`, preserving every known knowledge-page and accepted expression-asset target from prior and current runs, and write an `llm_note` that says what the source contributed.
5. Read back the source and all targets; verify file existence, forward `derived_refs`, reverse `03_Notes` `source_refs`, asset-entry `source_ref` to the local source note, and the recorded contribution.
6. Only then set `llm_status: absorbed`, and read the source back once more. Never bulk-fill `absorbed` as metadata repair.

If the knowledge already existed, the source may be absorbed only after the evidence links are added and `llm_note` says `仅补强证据，未改变结论`. If no stable value can be added or corroborated, use `llm_status: ignore` with a reason in `llm_note`.

### 4. After each small batch

Refresh the operating files as needed:

- update changed wiki pages in `03_Notes`
- update the domain `Wiki Index` if kernel coverage changed and the domain is allowed to own one
- append a substantive entry to the domain `Wiki Log` if it exists and the domain is allowed to own one
- refresh the target `MOC` only when navigation materially improves

## Creation bar

A new page is justified only when at least one of these is true:

- a durable concept has no good home yet
- a repeatedly asked judgment question deserves its own question page
- multiple pages now compress into a stable synthesis page

Do not create a page just because:

- the source has a fresh outline
- the example is vivid but the idea is already covered
- the wording is new but the knowledge structure is not

## Progress reporting

After each bootstrap pass, report:

- target domain + registry state
- sources absorbed in this pass
- pages updated
- pages created, if any, and why
- index/log/MOC changes
- the next recommended queue

## Stop condition

Bootstrap ends only when the user explicitly says initialization is done.
