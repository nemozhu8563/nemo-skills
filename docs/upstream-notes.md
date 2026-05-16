# Upstream Notes

Track origin and maintenance posture here before migrating later batches.

## Batch 1
- `obsidian-bases`: treated as nemo-maintained after migration.
- `obsidian-markdown`: treated as nemo-maintained after migration.
- `json-canvas`: treated as nemo-maintained after migration.

## Batch 2
- `interdisciplinary-research`: treated as nemo-maintained after migration with bundled demo PDF.

## Batch 3 (baoyu family)
- `baoyu-article-illustrator`
- `baoyu-comic`
- `baoyu-compress-image`
- `baoyu-cover-image`
- `baoyu-danger-gemini-web`
- `baoyu-danger-x-to-markdown`
- `baoyu-image-gen`
- `baoyu-infographic`
- `baoyu-post-to-x`
- `baoyu-slide-deck`
- `baoyu-url-to-markdown`
- `baoyu-xhs-images`

Maintenance posture for Batch 3: treat as nemo-maintained snapshots (can diverge from upstream and keep local adaptations).

## Batch 4 (low-risk article workflow skills)
- `article-clip-obsidian`: includes `convert.js` helper and README; treat the whole directory as source-of-truth.
- `article-illustrate`: markdown-only skill; no special packaging needs found.
- `article-review`: markdown-only skill; no special packaging needs found.
- `bullet-viral-post`: bundled markdown/text references are part of the source tree and should publish intact.
- `decompose-article`: includes `references/template.md`; keep relative path structure unchanged.
- `idea-spark`: markdown-only skill; no special packaging needs found.
- `writing-clone`: markdown-only skill; no special packaging needs found.

Maintenance posture for Batch 4: treat as nemo-maintained working copies published back into the vault with managed markers.

## Batch 5 (workflow utility skills)
- `kie-image-gen`: preserve `scripts/` helpers and `cover-prompt.md` together as one source tree.
- `llm-wiki`, `llm-wiki-bootstrap`, `llm-wiki-ingest`, `llm-wiki-query-writeback`, `llm-wiki-weekly-lint`: preserve `agents/openai.yaml` alongside `SKILL.md` for each entry.
- `markitdown-client`: preserve `agents/openai.yaml` alongside `SKILL.md`.
- `obsidian-archive`: preserve `references/DDC-ZK-spec.md` alongside `SKILL.md`.

Maintenance posture for Batch 5: treat the nested helper/reference files as first-class managed assets; publish should preserve relative paths exactly.

## Batch 6 (publishing helpers except wechat-publisher)
- `publish-article`: markdown-only workflow helper; no packaging blockers found.
- `wechat-article-writer`: preserve bundled `assets/` and `references/` directories alongside `SKILL.md`.
- `zhihu-collection-sync`: preserve `agents/` and `scripts/` helper directories alongside `SKILL.md`.

Maintenance posture for Batch 6: treat bundled content, helper scripts, and agent configs as first-class managed assets.

## Batch 7 (wechat-publisher Bun-first repackaging)\n- `wechat-publisher`: now maintained as a Bun-first source tree with `bun.lock`, no vendored `node_modules/`, and user-level `.agents/wechat-publisher.json` runtime config.\n\nMaintenance posture for Batch 7: edit the authoritative files in `nemo-skills`, keep rebuildable dependencies out of source control, and treat the user-level `.agents` config as the only canonical operator config location.

## Needs later review
- `content-reviewer.md` / `inbox-processor.md`: standalone prompts, defer until prompt-file publish path is exercised.

