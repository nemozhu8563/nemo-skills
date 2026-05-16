---
name: llm-wiki-query-writeback
description: Answer questions from a target Obsidian LLM Wiki domain and decide whether a durable new judgment should be written back. Use when the user asks a domain question and wants the answer grounded in existing wiki pages rather than free-floating chat memory.
---

# LLM Wiki Query Write-Back

Use this skill when the user is asking the wiki to think, not just to store a new source.

## Read these files first

- `.llm-wiki/domains.json`
- `05_Templates/scripts/llm_wiki_policy_gate.py`
- the target domain's `Wiki Index`
- the target domain's `Wiki Log`
- the specific concept / question / synthesis pages relevant to the question

Read only the pages needed for the current query.

## Query-first workflow

### 1. Ground the answer in the wiki

Start from the target domain's wiki pages, not from generic model memory.

Answer with:

- the current wiki's best judgment
- the page names carrying that judgment
- any tension, gap, or unresolved contradiction you found

### 2. Detect whether a durable new judgment emerged

A write-back is justified when the conversation produced something more durable than a one-off phrasing, for example:

- a reusable heuristic
- a sharper boundary
- a comparison that will likely matter again
- a clarified disagreement or correction

Do not write back ephemeral wording improvements or conversation-only examples.

### 3. Choose the write-back policy

#### Same direction

If the write-back stays within the current domain direction and only sharpens existing pages:

- prepare a concise write-back package
- call the canonical gate in `05_Templates/scripts/llm_wiki_policy_gate.py`
- if maintenance mode is ON for this domain, the gate may return `allow_apply`
- otherwise the gate should return `propose_only`

#### New direction

Always ask before writing if the result would:

- create a new page family
- open a new conceptual branch
- materially shift the domain topology
- move beyond the current domain scope

Use the canonical gate for this case too; it should return `confirm`.

### 4. If writing back

Update the smallest number of pages that can hold the new judgment.

Usually this is `1-2` pages plus `Log`.

When edits are substantive:

- update `updated_at`
- add the relevant `source_refs` if the query synthesized from source-backed pages
- append a `query -> write-back` entry to the target domain log if it exists

## Output contract

Return in this order:

1. resolved domain + registry state
2. wiki-grounded answer
3. pages consulted
4. candidate write-back, if any
5. whether it is same-direction or new-direction
6. gate decision
