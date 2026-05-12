---
name: zhihu-collection-sync
description: Sync Zhihu collections into the Obsidian vault with URL dedupe, reusing the existing article-clip-obsidian leaf flow. Use when the user wants to bulk-import one or more Zhihu collections without re-downloading URLs that already exist in the vault.
---

# Zhihu Collection Sync

Batch-sync Zhihu collections into `02_Sources/_clippings/`.

The syncer:

- lists Zhihu collections
- paginates collection items
- only handles `article` and `answer`
- skips URLs already present in existing clipping metadata
- reuses `article-clip` + `.skills/article-clip-obsidian/convert.js`
- post-processes newly imported files so new imports end up with `source=<url>`

## Main commands

### 1. Sync all collections

```bash
python .skills/zhihu-collection-sync/scripts/sync.py --all-collections
```

### 2. Sync one or more collections

```bash
python .skills/zhihu-collection-sync/scripts/sync.py \
  --collection-id 913293216
```

## Selection rules

Exactly one collection mode is allowed:

- `--all-collections`
- repeatable `--collection-id <id>`

## Runtime notes

- The skill reuses `article-clip` plus `node .skills/article-clip-obsidian/convert.js` as the leaf path.
- Collection API calls use a persistent browser session and may require one-time Zhihu login in the managed Edge profile.
- Existing URL detection scans both `source` and `refs` in current clipping files.

## Deliverables

Every successful run should leave:

- one or more new clipping files under `02_Sources/_clippings/`
- a JSON summary printed to stdout
- explicit unsupported-type reporting
- no duplicate clipping writes
