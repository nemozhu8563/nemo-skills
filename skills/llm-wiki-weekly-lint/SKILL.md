---
name: llm-wiki-weekly-lint
description: Run a maintenance and knowledge-quality check on an Obsidian LLM Wiki domain or vault slice, with source intake, wiki body, query write-back, solution absorption, project backflow, topology, report-writing, registry consistency, and promotion-pressure checks. Use when the user asks for weekly lint, health check, 知识质量检查, 知识质量报告, 合并拆分复核, 旧判断刷新, solution-to-note absorption, project backflow, or wants to see whether the wiki is still growing by updating old pages instead of hoarding sources.
---

# LLM Wiki Weekly Lint

Use this skill to review whether a target domain or vault slice is still behaving like a wiki instead of a clipping graveyard.

For a full 知识质量检查 pass, read `references/知识质量检查.md` after the files below. Keep `SKILL.md` as the operating entry point and use the reference for the detailed checklist and report buckets.

Treat `05_Templates/笔记整理归档SOP.md` as the current directory-identity rule source: `02_Sources` keeps raw evidence, `03_Notes` keeps durable judgments, `04_Projects` keeps project operating truth, `docs/solutions` keeps CE method assets, and `.llm-wiki` keeps governance state.

## Read these files first

- `02_Sources/LLM Wiki 处理台.base`
- `.llm-wiki/domains.json`
- `05_Templates/笔记整理归档SOP.md`
- `05_Templates/scripts/llm_wiki_policy_gate.py`
- the target domain's MOC
- the target domain's `Wiki Index` / `Wiki Log` if they exist

Then inspect only the pages and source queues needed to answer the checklist.

## Default behavior

Run this skill as 自动执行优先：先吸收和小修，再报告不确定项。

Automatically do safe, local, reversible work when the target is clear:

- absorb a source into an existing `03_Notes` page when the durable judgment and target page are obvious
- add missing `source_refs` to an existing note
- set source-local `llm_status`, `llm_domain`, `ddc`, and `llm_note` after absorption
- add a short durable principle from `docs/solutions` to an existing note
- add project or published-article references to an existing note without editing protected published bodies
- refresh small SOP/checklist wording when the current rule is already settled

Only report instead of editing when the action is broad, destructive, ambiguous, or structural:

- merging or splitting notes
- creating or promoting domains
- deleting docs or templates
- rewriting project operating facts without current verification
- editing protected published article bodies
- moving large folders

## Lint workflow

### 1. Review the source layer

Check whether new sources were actually mapped into target pages and whether stale low-value candidates are piling up.

Use `02_Sources/LLM Wiki 处理台.base` as the first-pass source operations board:

- `待分流` -> intake backlog not yet classified
- `已路由待吸收` -> routed but not yet merged into wiki pages
- `待复核` -> ambiguous / sensitive candidates requiring another pass
- `已吸收` -> already completed source items

When drilling into one candidate, inspect the minimal note-local frontmatter contract:

- `llm_status`
- `llm_domain`
- `ddc`
- `llm_note`

Default interpretation:

- blank `llm_status` means `new` / `待分流`
- these fields describe operational state only
- `.llm-wiki` remains the canonical truth / governance layer

Do not begin this review with repo-wide search unless you are specifically validating downstream references or reconciling a suspected mismatch.

### 2. Review the wiki body

Look for:

- duplicated definitions
- question-page overlap
- synthesis pages that no longer reflect the current judgment
- obvious cases where a new summary page was created instead of updating an old page

### 3. Review query -> write-back behavior

Look for repeated questions that should become pages, and for durable judgments that were discussed but never written back.

### 4. Review solution absorption

Inspect relevant `docs/solutions` entries as reusable method assets, not raw source material.

Classify each sampled solution as one of:

- write durable principles, boundaries, or repeated judgments into `03_Notes`
- update affected `04_Projects` operating or project-state documents
- no absorption needed

Do not copy full CE retrospectives into `02_Sources` or `03_Notes`.

### 5. Review project backflow

Inspect relevant `04_Projects` material for facts, rules, and workflows that should stay project-local versus judgments or methods that should flow out.

Classify sampled project material as one of:

- keep in project
- write a stable judgment into `03_Notes`
- generate or update a reusable method asset in `docs/solutions`
- refresh the project document against current facts

Protect published article bodies only when they live under `04_Projects/AI_Media` or the Zhihu output directory and have non-empty `published_url` frontmatter.

### 6. Review operating files

Check whether `Index` still matches the kernel map and whether `Log` records the major ingest and write-back events.

### 7. Review topology pressure

Check at least:

- is a parent domain getting too mixed?
- is any child MOC repeatedly behaving like an independent domain?
- is there any registry inconsistency?
- should any child MOC be proposed for promotion?

If the answer is yes, emit a structured proposal rather than silently promoting.

## Minimum output

Every lint pass should produce a compact Chinese report with these buckets:

1. `已自动完成`
2. `需要确认`
3. `暂不处理 / 保留原位`
4. `下次候选`

Use the six check surfaces internally; do not force users to read the internal taxonomy unless it helps explain a decision.

By default, write the report to `.llm-wiki/reports/知识质量检查-YYYYMMDD.md`, using the local date.

## Default write policy

Lint is automation-first with guardrails.

- Do safe absorptions and small fixes directly.
- Keep source/project/solution originals in place; absorb only durable judgments, boundaries, principles, or reusable methods.
- Do not perform broad rewrites unless the user explicitly asks to turn findings into an edit pass.
- If you make substantive fixes, update `Log` when the domain uses one.
- If lint findings would create or mutate independent operating surfaces, call `05_Templates/scripts/llm_wiki_policy_gate.py` first.
