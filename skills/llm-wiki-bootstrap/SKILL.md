---
name: llm-wiki-bootstrap
description: Continue or initialize one Obsidian LLM Wiki domain by repeatedly absorbing existing sources into the domain wiki. Use when the user says 初始化、继续初始化、批量吸收、先把现有知识做成 wiki, or wants bootstrap to keep running without per-package confirmation for a bootstrap-state domain.
---

# LLM Wiki Bootstrap

Use this skill while the target domain is still in `bootstrap`.

This is not a different knowledge logic from steady-state ingest. It is the same single-source absorption loop, repeated in batches, with a different confirmation policy.

## Read these files first

- `02_Sources/LLM Wiki 处理台.base`
- `.llm-wiki/domains.json`
- `05_Templates/scripts/llm_wiki_policy_gate.py`
- the target domain's MOC
- if they exist, the target domain's `Wiki Index` and `Wiki Log`

## Bootstrap policy

- For a domain whose lifecycle is `bootstrap`, per-source or per-package ingest confirmation is not required.
- Keep processing until you hit a real blocker or the user explicitly says initialization is complete.
- Ask only if the work would leave the target domain scope, introduce a clearly new page family, or conflict with the domain's current operating surfaces.
- Before each write batch, check the gate with `05_Templates/scripts/llm_wiki_policy_gate.py`.
- Bootstrap exit itself is not automatic: `bootstrap -> steady_state` requires confirmation via the canonical gate.
- If the target domain is `parent_managed`, do not create or mutate independent Index / Log / lint surfaces.

For `02_Sources` queue checks, use this minimal frontmatter contract on candidate notes:

- `llm_status`
- `llm_domain`
- `ddc`
- `llm_note`

Default interpretation:

- blank `llm_status` means `new` / `待分流`
- frontmatter is queue-local operational metadata
- `.llm-wiki` remains the canonical truth / governance layer

## Batch workflow

### 1. Build or refresh the candidate queue

Prefer this order:

1. `02_Sources/LLM Wiki 处理台.base` views such as `待分流`, `已路由待吸收`, `待复核`
2. `02_Sources/_clippings` and `02_Sources/_legacy`
2. already-known domain source lists in `Index`
3. only then relevant derived material in `04_Projects`

For bootstrap queue construction, prefer the Base as the first operating surface and use raw folder listing only as a fallback or reconciliation pass.

If a candidate's Base position and note-local frontmatter disagree with `.llm-wiki`, trust `.llm-wiki` and treat the Base/frontmatter as needing sync.

Do not start bootstrap queue discovery with repo-wide search. Use search only as a fallback when reconciling downstream references or investigating suspected drift.

### 2. Process one source at a time

For each source:

1. classify it as `primary` or `derived`
2. identify the best `1-3` target pages
3. update existing pages first
4. create a new page only if the schema's `create only when necessary` bar is met
5. avoid copying rhetorical wrappers from source material
6. if the change would require new independent operating surfaces for a `parent_managed` domain, stop and surface a promotion proposal instead of writing

### 3. After each small batch

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
