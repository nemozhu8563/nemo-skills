# Skill Retention Decisions

This file is the human-readable retention source for the current migration. It mirrors `docs/mapping.json` and explains why only selected skills publish to `.agents/skills`.

## Publish Now

- `article-clip-obsidian`
- `article-illustrate`
- `baoyu-image-gen`
- `baoyu-infographic`
- `baoyu-post-to-x`
- `baoyu-translate`
- `baoyu-url-to-markdown`
- `interdisciplinary-research`
- `json-canvas`
- `llm-wiki`
- `llm-wiki-bootstrap`
- `llm-wiki-ingest`
- `llm-wiki-query-writeback`
- `llm-wiki-weekly-lint`
- `nemo-writer`
- `obsidian-bases`
- `obsidian-markdown`
- `publish-article`
- `wechat-publisher`
- `zhihu-collection-sync`
- `baoyu-article-illustrator`
- `baoyu-cover-image`
- `kie-image-gen`
- `tryvalo-imagegen`

## Delete Or Do Not Migrate

- `article-review`
- `baoyu-comic`
- `baoyu-compress-image`
- `baoyu-danger-gemini-web`
- `baoyu-danger-x-to-markdown`
- `baoyu-slide-deck`
- `content-reviewer`
- `decompose-article`
- `humanizer-zh`
- `idea-spark`
- `inbox-processor`
- `markitdown-client`
- `obsidian-archive`
- `wechat-article-writer`
- `writing-clone`

## Archive / Pending

- `baoyu-xhs-images`: archive for this migration; not part of the current .agents entry surface.
- `bullet-viral-post`: pending user decision; do not publish until explicitly requested.

## Boundary Rules

- `dbs-*` stays in the vault `.agents/skills` diagnostic layer and is not managed by this repo mapping.
- `nemo-writer` is the only Nemo-style Chinese technical long-form writing entrypoint.
- `writing-clone` and `wechat-article-writer` are retired and must not be merged into `nemo-writer`.
- `dbs-ai-check` is the only AI-style detection entrypoint and stays outside this repo mapping.
- `article-illustrate` is the user-facing article visual entrypoint; `baoyu-cover-image` and `baoyu-article-illustrator` are provider/sub-skill surfaces.
- `baoyu-image-gen` is the ordinary image-generation router; `kie-image-gen` and `tryvalo-imagegen` are providers.
- `article-clip-obsidian` handles Obsidian clipping; `baoyu-url-to-markdown` handles generic Markdown conversion.
