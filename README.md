# nemo-skills

`nemo-skills` is the source-of-truth repository for skills you actively maintain.

## Source of truth rule
- Edit migrated skills here, not in the Obsidian vault.
- Publish managed copies back into the vault with `scripts/publish-to-vault.ps1`.
- Verify generated copies with `scripts/verify-publish.ps1`.
- Roll back with `scripts/rollback-publish.ps1`.

## Current vault target
- Vault root: `C:\Users\zkl\OneDrive\Obsdian\Obsidian`
- Managed destination root: `C:\Users\zkl\OneDrive\Obsdian\Obsidian\.skills`

## Default safety rules
- Because both this repo and the vault live under OneDrive, live links / junctions are default-forbidden.
- The default mode is publish/materialize managed copies.
- Generated copies carry `do not edit here` warnings and drift metadata.

## Batch 1
- `obsidian-bases`
- `obsidian-markdown`
- `json-canvas`

## Batch 2
- `interdisciplinary-research`

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
