# nemo-skills

`nemo-skills` is the source-of-truth repository for skills you actively maintain.

## Source of truth rule
- Edit migrated skills here, not in the Obsidian vault.
- Publish managed copies back into the vault with `scripts/publish-to-vault.ps1`.
- Verify generated copies with `scripts/verify-publish.ps1`.
- Roll back with `scripts/rollback-publish.ps1`.

## Current vault target
- Vault root: `C:\Users\zkl\OneDrive\Obsdian\Obsidian`
- Managed destination root: `C:\Users\zkl\OneDrive\Obsdian\Obsidian\.agents\skills`
- Rollback backup root: `C:\Users\zkl\OneDrive\Obsdian\Obsidian\.agents\.nemo-backups\skills`

## Default safety rules
- Because both this repo and the vault live under OneDrive, live links / junctions are default-forbidden.
- The default mode is publish/materialize managed copies.
- Generated copies carry `do not edit here` warnings and drift metadata.

## Current publish set

The publish set is controlled by `docs/mapping.json`. Only entries with `status: "migrate_now"` are eligible for `scripts/publish-to-vault.ps1`.

Primary entrypoints:

- `article-clip-obsidian`
- `article-illustrate`
- `baoyu-image-gen`
- `baoyu-infographic`
- `baoyu-post-to-x`
- `baoyu-url-to-markdown`
- `baoyu-translate`
- `interdisciplinary-research`
- `json-canvas`
- `llm-wiki`
- `nemo-writer`
- `obsidian-bases`
- `obsidian-markdown`
- `publish-article`
- `wechat-publisher`
- `zhihu-collection-sync`

Provider/sub-skill surfaces:

- `baoyu-cover-image`
- `baoyu-article-illustrator`
- `kie-image-gen`
- `tryvalo-imagegen`
- `llm-wiki-bootstrap`
- `llm-wiki-ingest`
- `llm-wiki-query-writeback`
- `llm-wiki-weekly-lint`

Retired or non-publish entries are documented in `docs/skill-retention.md`.
