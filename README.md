# nemo-skills

`nemo-skills` is the source-of-truth repository for skills you actively maintain.

## Source of truth rule
- Edit migrated skills here, not in the Obsidian vault.
- Publish managed copies back into the vault with `node scripts/publish-to-vault.mjs` or `bun scripts/publish-to-vault.mjs`.
- Verify generated copies with `node scripts/verify-publish.mjs` or `bun scripts/verify-publish.mjs`.
- Roll back with `node scripts/rollback-publish.mjs` or `bun scripts/rollback-publish.mjs`.

## Required vault target
- Scripts do not infer a default vault. Always pass `--vault-root <path>`.
- Current vault root: `/Users/nemo/Documents/Obsidian`
- Managed destination root: `<vault-root>/.agents/skills`
- Rollback backup root: `<vault-root>/.agents/.nemo-backups/skills`

## Default safety rules
- Because both this repo and the vault live under OneDrive, live links / junctions are default-forbidden.
- The default mode is publish/materialize managed copies.
- Generated copies carry `do not edit here` warnings and drift metadata.

## Current publish set

The publish set is controlled by `docs/mapping.json`. Only entries with `status: "migrate_now"` are eligible for publish.

Common commands:

```bash
# Publish one skill
node scripts/publish-to-vault.mjs --vault-root /Users/nemo/Documents/Obsidian --entry-id article-illustrate --mode OverwriteManagedClean

# Verify one skill
node scripts/verify-publish.mjs --vault-root /Users/nemo/Documents/Obsidian --entry-id article-illustrate

# Publish all migrate_now entries
node scripts/publish-to-vault.mjs --vault-root /Users/nemo/Documents/Obsidian --only-migrate-now --mode OverwriteManagedClean

# Roll back a publish batch
node scripts/rollback-publish.mjs --vault-root /Users/nemo/Documents/Obsidian --batch-id 20260516T111507Z --entry-id article-illustrate
```

The target vault is intentionally required at call time. This keeps AI/tooling invocations explicit and prevents accidental publishes into stale OneDrive vault paths.

Primary entrypoints:

- `article-clip-obsidian`
- `article-illustrate`
- `baoyu-image-gen`
- `baoyu-infographic`
- `baoyu-post-to-x`
- `baoyu-translate`
- `ebook-to-markdown`
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
