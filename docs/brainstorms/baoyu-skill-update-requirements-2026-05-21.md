# Baoyu Skill Update Migration Requirements

Date: 2026-05-21
Status: Requirements accepted for implementation

## Summary

This migration updates the local Nemo skill set by selectively absorbing useful upstream Baoyu skill changes while keeping Nemo's own routing, providers, and publishing workflows as the source of truth.

The migration should be aggressive about removing duplicate public entrypoints. Do not import upstream provider sprawl or browser workflows when the local skill already has a simpler, preferred path.

## Goals

- Keep `skills/baoyu-image-gen` as the single public image-generation router.
- Route image generation through Nemo's own provider capabilities, not upstream `baoyu-imagine` provider families.
- Absorb useful visual-generation rules from upstream Baoyu skills where they improve local quality and safety.
- Keep `skills/wechat-publisher` as Nemo's own API-first WeChat publisher.
- Remove `skills/baoyu-url-to-markdown` completely and route URL clipping through `skills/article-clip-obsidian`.
- Keep migrations small, explicit, and publishable into the Obsidian vault after source verification.

## In Scope

### 1. `skills/baoyu-image-gen`

Requirements:

- Keep `baoyu-image-gen` as the public entrypoint.
- Do not add upstream `baoyu-imagine` as a new local skill.
- Use Nemo's own provider layer only.
- Integrate batch generation into `baoyu-image-gen` using Nemo's own providers.
- Add or preserve reference-image support as image-to-image capability.
- Preserve the local routing rule: prefer Codex native image generation first; use local provider scripts only when local paths, batch output, reference images, or explicit provider execution are needed.
- Keep `kie-image-gen` and `tryvalo-imagegen` as provider/compatibility channels only if needed by local routing; they should not become the main user-facing path.

Do not absorb:

- Upstream `baoyu-imagine` provider zoo.
- GPT Image 2 / DashScope / MiniMax / Jimeng / Seedream / Replicate / Z.AI / Azure / OpenRouter routing unless already supported by Nemo's own provider path.
- Generic API-base compatibility as a feature goal.
- Provider selection complexity that duplicates local routing rules.

### 2. Visual Skill Rules

Affected skills:

- `skills/article-illustrate`
- `skills/baoyu-article-illustrator`
- `skills/baoyu-cover-image`
- `skills/baoyu-infographic`

Requirements:

- Absorb upstream rules that make raster generation safer and clearer.
- Prefer Codex native image generation for ordinary image output.
- Do not use SVG, HTML, canvas, or Mermaid as fake substitutes for requested raster images.
- Do not repair generated image text by programmatically overlaying text with ImageMagick, Pillow, Canvas, SVG, or similar tools.
- If generated text is wrong, handle it by regenerating, reducing/removing text in the prompt, or asking the user.
- For article-scale illustration work, create prompt files first, then run batch generation.
- Keep explicit confirmation behavior unless the user clearly asks for direct generation.

### 3. `skills/baoyu-post-to-x`

Requirements:

- Absorb upstream X publishing workflow improvements that fit the local skill.
- Respect the user's selected browser-control mode when a mode is specified.
- For X Articles, upload images through the toolbar Media button, not by pasting image paths or clipboard images into article body content.
- Treat placeholder disappearance plus image count increase as the safe upload gate.
- Preserve local final-publish safety: preview or draft preparation is allowed, but actual final publishing should remain explicit.

### 4. `skills/baoyu-translate`

Requirements:

- Absorb upstream translation workflow refinements where they improve local clarity.
- Refresh subagent or prompt templates if the upstream version is more precise.
- Keep the local three-mode translation behavior unless a checked upstream change clearly improves it.

### 5. Remove `skills/baoyu-url-to-markdown`

Requirements:

- Delete `skills/baoyu-url-to-markdown` as a current entrypoint.
- Remove it from `docs/mapping.json`, retention docs, and any publish list that treats it as active.
- Route URL-to-Obsidian clipping through `skills/article-clip-obsidian`.
- Keep `article-clip-obsidian` grounded in `web-access` for acquisition and local conversion scripts for Obsidian clipping output.

Do not preserve a compatibility wrapper unless implementation verification shows another active skill still depends on it.

### 6. `skills/wechat-publisher`

Requirements:

- Keep Nemo's own `wechat-publisher` as the only WeChat publishing skill.
- Do not migrate upstream `baoyu-post-to-wechat` as an entrypoint.
- Keep API-first publishing through the local config model.
- If multi-account support is added, implement it in Nemo's own config shape, with `default` as the default account.
- Keep Nemo's existing template system as the presentation layer.
- Absorb only reliability features that fit the current API-first model, such as:
  - account-specific publish settings,
  - comment controls if supported by the existing API flow,
  - better image format and WebP handling,
  - clearer diagnostics for cover upload vs article image upload,
  - optional citation or external-link footnote behavior if it fits the local article pipeline.

Do not absorb:

- Upstream Chrome profile publishing workflow.
- Browser/CDP publishing as the primary path.
- Upstream `EXTEND.md` account model.
- Upstream theme system as a replacement for local templates.
- 贴图 / image-text publishing.
- Telegram QR code behavior.
- Any WeChat browser automation feature that makes the local API-first tool harder to maintain.

## Out of Scope

- Migrating unrelated upstream Baoyu skills such as `baoyu-comic`, `baoyu-image-cards`, `baoyu-slide-deck`, `baoyu-diagram`, `baoyu-wechat-summary`, `baoyu-youtube-transcript`, `baoyu-post-to-weibo`, `baoyu-xhs-images`, `baoyu-compress-image`, or `baoyu-danger-*`.
- Adding new third-party provider dependencies.
- Replacing Nemo's Obsidian clipping pipeline with a generic URL-to-Markdown skill.
- Rewriting local publishing tools around upstream browser automation.
- Publishing generated `.agents/skills` copies before source changes are verified.

## Acceptance Criteria

- `baoyu-image-gen` remains the single public image router.
- No local `baoyu-imagine` skill is added.
- Batch and reference-image behavior, if implemented, use Nemo's own provider capabilities.
- Visual skills explicitly ban fake raster substitutes and programmatic bitmap text repair.
- `baoyu-post-to-x` documents or implements the X Article image upload safety gate.
- `baoyu-url-to-markdown` is removed from the active source tree and active mapping/retention docs.
- `article-clip-obsidian` is the documented path for URL clipping into Obsidian.
- `wechat-publisher` remains API-first and local-template-based.
- `wechat-publisher` does not import upstream Baoyu browser publishing or theme systems.
- Changed source skills pass the repo's relevant verification scripts.
- If the vault managed copies are updated, publish and verify each changed entry with the existing publish scripts.

## Implementation Constraints

- Edit source files under `skills/` in this repository first.
- Treat generated vault copies as publish artifacts, not edit targets.
- Preserve unrelated dirty changes already present in the worktree.
- Keep diffs small and reviewable.
- Prefer deletion over compatibility layers where no active dependency requires the old entrypoint.
- Do not add new dependencies unless explicitly requested later.

## Verification Plan

- Review `docs/mapping.json` and retention docs after deleting or reclassifying entries.
- Run source-level checks for changed packages or scripts.
- For `wechat-publisher`, run existing package tests if implementation touches JavaScript code.
- For publishable skill changes, run:

```bash
node scripts/verify-publish.mjs --entry-id <skill-id>
```

- If publishing to the Obsidian vault is part of the implementation, run:

```bash
node scripts/publish-to-vault.mjs --entry-id <skill-id> --mode OverwriteManagedClean
node scripts/verify-publish.mjs --entry-id <skill-id>
```

## Open Decisions

- Whether `kie-image-gen` and `tryvalo-imagegen` stay as separately publishable compatibility skills for one more cycle or become internal-only provider references.
- Whether optional WeChat citation or external-link footnote behavior should be added now or deferred until a real publishing need appears.
