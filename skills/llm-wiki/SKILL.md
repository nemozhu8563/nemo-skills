---
name: llm-wiki
description: Use when the user names llm-wiki/LLM Wiki or asks to bootstrap, ingest, absorb, process, 提炼, 总结, or 吸收 an Obsidian source/article/clipping/conversation as wiki knowledge; optionally extract reusable AI_Media expression assets; check source processing status; ask wiki-grounded questions with write-back; or run weekly lint.
---

# LLM Wiki

Main entrypoint for the multi-domain LLM Wiki system.

Use this skill when the user is talking about any of these jobs:

- 初始化 / 继续初始化 / bootstrap
- 剪藏后吸收一篇新资料进入 wiki
- 用 llm-wiki 总结 / 提炼 / 吸收某篇文章、source note、剪藏或本轮对话
- 基于现有 wiki 提问，并考虑把稳定判断回写
- 做 weekly lint / 健康检查 / 维护
- 检查某篇 `02_Sources` 文章是否已处理 / 还在哪个状态

## Meaning of 总结 / 提炼 in LLM Wiki

When the user says `用 llm-wiki 总结`, `提炼`, `吸收`, `改成那篇文章`, or asks to include the current conversation with a source, treat it as **knowledge absorption**, not a normal source-note summary.

Default behavior:

1. extract durable judgments / distinctions / questions
2. update existing `03_Notes` pages first
3. create a new concept / question / synthesis page only when necessary
4. when useful or requested, separately extract reusable AI_Media expression assets into `04_Projects/AI_Media/80_Assets/*.md`
5. leave only a short processing record in the source note
6. update `llm_domain`, `llm_status`, and `llm_note`

Do not satisfy this request by pasting a long summary or conversation recap back into the original `02_Sources` note.

If the same source can support different viewpoints for different MOCs, absorb the relevant viewpoint into each matching page. Do not force a single "correct" angle when the material is reusable from multiple knowledge angles.

## Grounding order

Read these first before routing:

- `02_Sources/LLM Wiki 处理台.base`
- `.llm-wiki/domains.json`
- `.llm-wiki/contracts/llm-wiki-policy-gate-v1.md`
- `.llm-wiki/contracts/llm-wiki-state-machine-v1.md`
- `.llm-wiki/contracts/llm-wiki-reason-codes-v1.md`
- `05_Templates/scripts/llm_wiki_policy_gate.py`

Then load the specific domain's MOC / Index / Log only after you know the target domain.

Keep `006` as the pilot reference pattern, not as the only domain.

## Source-status / intake checking order

When the user asks questions like:

- 这篇处理了吗
- 还有哪些没处理
- 这篇是在待分流还是已吸收
- 02 里哪些文章还没进 llm-wiki

Do **not** start with global search.

Use this order:

1. check `02_Sources/LLM Wiki 处理台.base` first as the operational intake board
2. check the source note's frontmatter (`llm_status`, `llm_domain`, `ddc`, `llm_note`)
3. check `.llm-wiki` truth-layer artifacts (`domains.json`, routing / bootstrap reports) when status needs confirmation
4. use global search only as a final cross-check for downstream absorption evidence in `03_Notes`, `00_MOC`, or other derived references

Interpretation rule:

- `Base = day-to-day operating board`
- `frontmatter = note-local operational status surface`
- `.llm-wiki = truth layer / governance record`
- `global search = fallback verification layer`

If the Base and `.llm-wiki` disagree, trust `.llm-wiki` and propose a Base/frontmatter sync.

Minimum frontmatter contract for these checks:

- `llm_status`
- `llm_domain`
- `ddc`
- `llm_note`

Default interpretation:

- blank `llm_status` means `new` / `待分流`
- these fields are operational metadata, not the canonical truth layer

## Domain resolution

Resolve target domain in this order:

1. explicit `domain_id`
2. explicit target `MOC`
3. source / question clearly scoped to one domain's existing Index / Log / kernel pages
4. if still ambiguous, propose the best `1-3` candidate domains instead of silently guessing

The registry in `.llm-wiki/domains.json` is the operating truth for:

- `domain_id`
- parent / child relationship
- lifecycle state
- topology state
- currently recognized operating surfaces

## Routing

Choose one lane quickly, then load the matching subskill.

### 1. Bootstrap / initialization

Use `../llm-wiki-bootstrap/SKILL.md` when the user wants to:

- initialize one domain or a batch of domains from existing materials
- continue bulk absorption
- keep auto-processing source batches
- treat a domain as still being in bootstrap mode

### 2. Ingest one source

Use `../llm-wiki-ingest/SKILL.md` when the user provides one new article, clipping, note, transcript, or conversation context and wants it absorbed / summarized / extracted into the wiki.

Also use this lane when the user asks whether one concrete source in `02_Sources` has already been processed, because the first job is intake-state confirmation before deciding whether a new ingest is needed.

This lane also owns the optional AI_Media expression-asset pass when the user asks about 素材采集、表达素材、开头、钩子、金句、标题、案例、类比、论证片段, or when a source clearly contains reusable writing material.

### 3. Query -> write-back

Use `../llm-wiki-query-writeback/SKILL.md` when the user asks a knowledge question and wants the answer grounded in the wiki, with possible write-back if a durable new judgment emerges.

### 4. Weekly lint / health check

Use `../llm-wiki-weekly-lint/SKILL.md` when the user wants a maintenance pass, health check, merge/split review, or weekly domain review.

## Shared operating rules

These rules apply in every lane:

- `update first, create only when necessary`
- Prefer updating existing domain pages in `03_Notes` before creating new pages.
- Treat `02_Sources/_clippings` and `02_Sources/_legacy` as primary source territory.
- Treat `04_Projects` material as derived source territory and only extract judgment-layer content from it.
- Keep AI_Media expression assets separate from wiki knowledge: `03_Notes` stores stable judgments; `80_Assets` stores reusable expression moves; topic-only evidence stays in `materials.md`.
- Do not copy article rhetoric, narrative scaffolding, or packaging into wiki pages.
- If a page receives a substantive change, update its `updated_at` and `source_refs`.
- If the kernel map changes materially, update `Index`; if the system state changed materially, update `Log`.
- Before write batches, promotion, demotion, bootstrap exit, or independent-surface mutation, use the canonical gate in `05_Templates/scripts/llm_wiki_policy_gate.py`.
- Normal source absorption into existing `03_Notes` pages should pass as `ingest_write --ingest-risk normal`, regardless of `bootstrap` or `steady_state`.
- Do not send material to review merely because its topic mentions law, medicine, mental health, education, family, investment, accident, self-harm, or public health.
- Review is triggered by write-action risk, not topic keywords: concrete operational advice, factual/legal/medical responsibility conclusions, unstable facts that cannot be abstracted into a durable viewpoint, identifiable private information propagation, too-ambiguous source material, or new independent surfaces / lifecycle changes.
- For `02_Sources` source-status checks, prefer Base/frontmatter inspection over repo-wide search.
- When a new `02_Sources` note appears without `llm_status`, treat it as an intake candidate rather than assuming it was already absorbed.

## Lifecycle boundary

Lifecycle and topology are explicit registry states, not thread-local guesses.

- `bootstrap` vs `steady_state` does not decide whether normal source absorption may write. Both may update existing knowledge pages when the extracted content is a durable viewpoint / distinction / judgment.
- `bootstrap` means repeated batch absorption is still expected; `steady_state` means operate more locally and keep changes smaller.
- `independent_root` / `parent_managed` / `promotion_candidate` / `promoted_independent` controls whether the domain can own independent operating surfaces.
- Same-direction query write-back is `propose_only` by default.
- Same-direction query write-back may auto-apply only when explicit maintenance mode is ON through `05_Templates/scripts/llm_wiki_policy_gate.py`.
- New-direction write-back always requires confirmation.
- Promotion is system-proposed, user-confirmed.

## Output contract

Default response shape:

1. chosen lane + resolved domain
2. relevant registry state
3. what was read / changed / proposed
4. evidence grounded in the current wiki
5. gate decision or blocker
6. next step
