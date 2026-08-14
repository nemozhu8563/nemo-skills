# nemo-skills

`nemo-skills` is the Nemo-maintained source collection inside the parent [awesome-skills](../README.md) directory. The parent README owns the overall source and installation policy; this repository owns only its self-maintained packages.

## Scope

- Keep Nemo-maintained Skills under `skills/<skill-name>`.
- Do not use this repository as the umbrella inventory for upstream clones or project-local Skills.
- Consumers link directly to the relevant package directory; do not create a copied installation.

## Legacy migration tooling

`docs/mapping.json` and the publish/verify/rollback scripts remain as historical migration and recovery tooling. They are not the installation path for new Skills; create a scoped symlink instead.

## Nemo-owned entrypoint inventory

Primary entrypoints:

- `article-clip-obsidian`
- `article-illustrate`
- `baoyu-image-gen`
- `baoyu-infographic`
- `baoyu-post-to-x`
- `baoyu-translate`
- `ebook-to-markdown`
- `interdisciplinary-research`
- `llm-wiki`
- `nemo-writer`
- `publish-article`
- `wechat-publisher`
- `zhihu-collection-sync`

## Explicitly project-scoped entrypoints

- `nemo-domain-launch` is linked only from `game-site` and `payforplus`; it is not a global or Obsidian entrypoint.

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
