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

## Learning-loop boundary

Do not treat the `learning-loop` book stack as ordinary `llm-wiki` intake backlog.

Default ignore scope:

- `02_Sources/_books/<book-slug>/`
- `02_Sources/_intake/books/<book-slug>/`
- `04_Projects/学习/<book-title>/`

These layers belong to the learning system, not to normal wiki queue operations.

Default rule:

- do not route lesson notes, course maps, curriculum files, study-session notes, or raw book packages into domains by default
- do not催办 these layers as stale source backlog
- only engage when the user explicitly wants a learner-owned durable judgment promoted into `03_Notes`
- if the task is about study progress, review rhythm, or organizing the learning package itself, route to `learning-loop` instead of normal `llm-wiki`

## Meaning of 总结 / 提炼 in LLM Wiki

When the user says `用 llm-wiki 总结`, `提炼`, `吸收`, `改成那篇文章`, or asks to include the current conversation with a source, treat it as **knowledge absorption**, not a normal source-note summary.

Default behavior:

1. extract durable judgments / distinctions / questions
2. update existing `03_Notes` pages first
3. create a new concept / question / synthesis page only when necessary
4. when useful or requested, separately extract reusable AI_Media expression assets into `04_Projects/AI_Media/80_Assets/*.md`
5. leave only a short processing record in the source note
6. record the actual contribution in `llm_note`, merge every known downstream target into `derived_refs` without dropping prior values, and update `llm_status` only after the absorption completion gate passes

Do not satisfy this request by pasting a long summary or conversation recap back into the original `02_Sources` note.

If the same source can support different viewpoints for different MOCs, absorb the relevant viewpoint into each matching page. Do not force a single "correct" angle when the material is reusable from multiple knowledge angles.

## Absorption completion gate

`llm_status: absorbed` is a verified outcome, not a processing label. A source may be marked `absorbed` only after all of these conditions pass:

1. At least one target under `03_Notes` was substantively updated, or the run confirmed that the durable knowledge already exists there and added this source as supporting evidence.
2. Merge new targets into the source note's existing `derived_refs`; preserve every known downstream target and list all knowledge-page and accepted expression-asset targets from both prior and current runs.
3. Every accepted AI_Media expression-asset entry has a per-entry `source_ref` pointing to the local source note. Source URL/path may remain as additional provenance, but cannot replace `source_ref`. Do not add aggregate-file frontmatter `source_refs` merely to satisfy this gate.
4. The source note's `llm_note` says what the source contributed. Do not use a generic record such as `已处理`.
5. 普通 `03_Notes` 不再使用 frontmatter `source_refs`；少量人工确认的核心来源可写在正文底部 `## 核心来源`，但它不是完整关系存储，也不是完成门必填项。
6. Read back the source and all targets after writing. Verify file existence, complete forward `derived_refs`, asset-entry `source_ref` to the local source note, and that the recorded contribution matches the actual write.
7. Set `llm_status: absorbed` only after steps 1-6 pass, then read back the source once more to confirm the terminal state.

If the source was examined but has no stable value to add, set `llm_status: ignore` and record the reason in `llm_note`; do not pretend it was absorbed. If the durable knowledge already existed and the source only adds corroborating evidence, it may be `absorbed`, but `llm_note` must explicitly say `仅补强证据，未改变结论` and the Source-side evidence must still pass.

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
2. check the source note's `llm_status`; for a claimed terminal state, also inspect `llm_note` and `derived_refs`
3. check `.llm-wiki` governance artifacts (`domains.json`, policy, lifecycle, topology, routing / bootstrap reports) for governance context; never use a registry or report as absorption proof
4. use global search only as a final cross-check for downstream absorption evidence in `03_Notes`, `00_MOC`, or other derived references

Interpretation rule:

- `Base = day-to-day operating board`
- `frontmatter = note-local operational status surface`
- `.llm-wiki = governance truth for domain registry, policy, lifecycle, topology, and routing context`
- `source frontmatter + verified downstream targets = source absorption-state truth`
- `global search = fallback verification layer`

If the Base and `.llm-wiki` disagree about domain registry, policy, lifecycle, topology, or routing context, trust `.llm-wiki`. For source absorption state, trust only source frontmatter plus verified target evidence. Never derive or sync `llm_status: absorbed` from a registry, routing record, bootstrap report, or lint report; complete the absorption gate or report the evidence gap.

Every newly captured source note still follows the shared five-field capture contract:

- `type: source`
- `status: active`
- non-empty `title`
- non-empty `source`
- explicit `llm_status: new`

For historical compatibility, a missing or blank `llm_status` is read as `new` / `待分流`; new capture entrypoints should still write `llm_status: new` explicitly.

Among LLM Wiki-specific fields, only `llm_status` is an intake field. `llm_domain` and `ddc` are optional routing aids, not capture requirements. `review` and `ignore` require a reason in `llm_note`; `llm_note` and `derived_refs` become absorption evidence only when the completion gate requires them. These fields are operational metadata, and `llm_status` alone is never sufficient absorption proof.

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
- Exclude the `learning-loop` book stack from normal queue discovery and source-status pressure by default: `02_Sources/_books/...`, `02_Sources/_intake/books/...`, and `04_Projects/学习/...` stay in the learning system unless the user explicitly requests promotion of a mature judgment into `03_Notes`.
- Keep AI_Media expression assets separate from wiki knowledge: `03_Notes` stores stable judgments; `80_Assets` stores reusable expression moves; topic-only evidence stays in `materials.md`.
- Do not copy article rhetoric, narrative scaffolding, or packaging into wiki pages.
- If a `03_Notes` page receives a substantive change, update its `updated` field when present. Do not add frontmatter `source_refs`; use Source `derived_refs` for the complete machine relation, and add `## 核心来源` only for a small set of manually confirmed core sources. If an AI_Media expression-asset entry is added, give it a per-entry `source_ref` to the local source note; source URL/path may remain as additional provenance but cannot replace that link.
- Never repair an `absorbed` label by changing status alone. Repair or complete the target write, asset-entry `source_ref` provenance, merged source `derived_refs`, contribution note, and read-back evidence first.
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
