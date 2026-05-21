# nemo-skills

`nemo-skills` is the source-of-truth repository for skills you actively maintain.

## Source of truth rule
- Edit migrated skills here, not in the Obsidian vault.
- Publish managed copies back into the vault with `node scripts/publish-to-vault.mjs` or `bun scripts/publish-to-vault.mjs`.
- Verify generated copies with `node scripts/verify-publish.mjs` or `bun scripts/verify-publish.mjs`.
- Roll back with `node scripts/rollback-publish.mjs` or `bun scripts/rollback-publish.mjs`.

## Current vault target
- Vault root: `C:\Users\zkl\OneDrive\Obsdian\Obsidian`
- Managed destination root: `C:\Users\zkl\OneDrive\Obsdian\Obsidian\.agents\skills`
- Rollback backup root: `C:\Users\zkl\OneDrive\Obsdian\Obsidian\.agents\.nemo-backups\skills`

## Default safety rules
- Because both this repo and the vault live under OneDrive, live links / junctions are default-forbidden.
- The default mode is publish/materialize managed copies.
- Generated copies carry `do not edit here` warnings and drift metadata.

## Current publish set

The publish set is controlled by `docs/mapping.json`. Only entries with `status: "migrate_now"` are eligible for publish.

Common commands:

```bash
# Publish one skill
node scripts/publish-to-vault.mjs --entry-id article-illustrate --mode OverwriteManagedClean

# Verify one skill
node scripts/verify-publish.mjs --entry-id article-illustrate

# Publish all migrate_now entries
node scripts/publish-to-vault.mjs --only-migrate-now --mode OverwriteManagedClean

# Roll back a publish batch
node scripts/rollback-publish.mjs --batch-id 20260516T111507Z --entry-id article-illustrate
```

On macOS/Linux, the scripts infer a sibling vault at `../Obsidian` when `docs/mapping.json` points at a Windows path. Pass `--vault-root <path>` to target a different vault.

Primary entrypoints:

- `article-clip-obsidian`
- `article-illustrate`
- `baoyu-image-gen`
- `baoyu-infographic`
- `baoyu-post-to-x`
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

Retired or non-publish entries are documented in `docs/skill-retention.md`. URL clipping into Obsidian is handled by `article-clip-obsidian`; the former `baoyu-url-to-markdown` entrypoint is retired.
