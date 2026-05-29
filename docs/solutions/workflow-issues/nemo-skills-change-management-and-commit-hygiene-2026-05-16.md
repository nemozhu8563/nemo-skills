---
title: Nemo Skills Change Management and Commit Hygiene
date: 2026-05-16
category: docs/solutions/workflow-issues
module: nemo-skills
problem_type: workflow_issue
component: development_workflow
severity: medium
applies_when:
  - "Maintaining source-of-truth skill definitions in nemo-skills"
  - "Publishing or syncing managed skill copies into the Obsidian vault"
  - "Retiring overlapping writer or publishing skills without restoring stale entrypoints"
  - "Updating cross-platform publishing workflows that must work on macOS and Windows paths"
  - "Separating functional skill decisions from mechanical line-ending normalization"
related_components:
  - documentation
  - tooling
tags: [nemo-skills, managed-skills, skill-boundaries, baoyu-post-to-x, nemo-writer, commit-hygiene, cross-platform]
---

# Nemo Skills Change Management and Commit Hygiene

## Context

A `nemo-skills` cleanup session started with a status question about what had changed, then turned into a controlled submission pass across several decisions:

- Keep and submit `article-quality-check`.
- Delete the newly introduced `nemo-post-to-x` entry instead of adding another X publishing surface.
- Keep `baoyu-post-to-x`, but make the X Articles path safer for macOS and Windows.
- Submit the `nemo-writer` metadata and boundary cleanup.
- Submit the migration decision that retires `writing-clone` and `wechat-article-writer`.
- Commit the remaining line-ending churn separately after the functional decisions.

The final commits were:

- `13c7b4b` Add a dedicated Chinese article quality gate
- `4ca4e55` Keep X Articles publishing behind preview verification
- `f9e8c54` Make Nemo Writer the source of truth for technical essays
- `1caf4cf` Retire legacy writing workflow entries
- `e382241` Normalize skill source line endings

## Guidance

Treat `nemo-skills` changes as workflow-contract changes, not just file edits. Group commits by the durable decision they record:

```bash
# Inspect the actual scope first.
git status --short
git diff --stat
git diff --ignore-space-at-eol --shortstat

# Validate the migration map before staging.
node -e "JSON.parse(require('fs').readFileSync('docs/mapping.json','utf8')); console.log('mapping ok')"

# Check whitespace on the targeted files.
git diff --check -- docs/mapping.json skills prompts scripts
```

For publish-surface changes, stage by decision:

```bash
git add docs/mapping.json skills/article-quality-check
git commit -m "Add a dedicated Chinese article quality gate"

git add skills/baoyu-post-to-x
git commit -m "Keep X Articles publishing behind preview verification"

git add skills/nemo-writer
git commit -m "Make Nemo Writer the source of truth for technical essays"

git add docs/mapping.json docs/migration-inventory.md docs/skill-retention.md
git commit -m "Retire legacy writing workflow entries"
```

Keep line-ending changes out of those functional commits. After the semantic commits are done, confirm no content diff remains when ignoring line endings, then commit the mechanical normalization alone:

```bash
git diff --ignore-space-at-eol --name-only
git add -A
git commit -m "Normalize skill source line endings"
```

When a publishing skill touches browser automation, platform paths, or account-side effects, add a representative render or import verification before calling it ready:

```bash
npx -y bun --version
npx -y bun -e "const mod = await import('./skills/baoyu-post-to-x/scripts/md-to-html.ts'); if (typeof mod.parseMarkdown !== 'function') throw new Error('parseMarkdown missing'); console.log('import ok')"
```

For Obsidian article publishing flows, also test a temporary vault shape that includes both a cover and an inline image. The useful check is that `assets/<article-name>/cover.png` becomes the cover and the first body screenshot remains inline.

## Why This Matters

Skill repositories are partly code and partly operating contract. A single broad "submit everything" commit makes it hard to tell which change created a new entrypoint, which retired an old one, which changed cross-platform behavior, and which only normalized line endings.

Decision-based commits preserve the reasoning:

- `article-quality-check` became a dedicated diagnosis skill rather than being folded into writer behavior.
- `baoyu-post-to-x` stayed behind preview verification because X Articles composition is browser- and account-dependent.
- `nemo-writer` became the single source of truth for Nemo-style Chinese technical long-form writing.
- `writing-clone` and `wechat-article-writer` were retired instead of merged back into the writer.
- Line-ending normalization was isolated so future diffs stay readable across Windows and macOS.

## When to Apply

- A skill repo has multiple related but separable migration decisions.
- The user makes a sequence of keep/delete/submit decisions and then says to commit everything.
- `docs/mapping.json`, skill manifests, and skill bodies change in the same session.
- Functional changes are mixed with CRLF/LF churn.
- A publishing skill involves Chrome, X Articles, covers, inline images, or other browser-side state.
- Managed skill copies must stay downstream of the `nemo-skills` source repository.

## Examples

Use this split when the session contains both product decisions and cleanup:

```text
13c7b4b Add a dedicated Chinese article quality gate
4ca4e55 Keep X Articles publishing behind preview verification
f9e8c54 Make Nemo Writer the source of truth for technical essays
1caf4cf Retire legacy writing workflow entries
e382241 Normalize skill source line endings
```

Use this validation bundle before the final report:

```bash
node -e "JSON.parse(require('fs').readFileSync('docs/mapping.json','utf8')); console.log('mapping ok')"
npx -y bun --version
git diff --check -- docs/mapping.json skills prompts scripts
npx -y bun -e "await import('./skills/baoyu-post-to-x/scripts/md-to-html.ts'); console.log('import ok')"
```

If the X publishing flow changed, add a temporary Obsidian-vault test with:

- a markdown article
- `assets/<article-name>/cover.png`
- one inline `![[image.png]]` body image

The expected result is: cover path resolves to `cover.png`, the body image remains in `contentImages`, and `## Links` is stripped from the generated HTML.

## Related

- `README.md` for the source-of-truth and managed-copy publish rules.
- `docs/mapping.json` for the canonical migrate/delete/archive status.
- `docs/migration-inventory.md` and `docs/skill-retention.md` for human-readable retention decisions.
- `skills/baoyu-post-to-x/SKILL.md` and `skills/baoyu-post-to-x/references/articles.md` for the X Articles preview and cross-platform path rules.
