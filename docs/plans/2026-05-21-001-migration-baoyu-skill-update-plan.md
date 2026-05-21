---
status: active
created: 2026-05-21
type: migration-plan
origin: docs/brainstorms/baoyu-skill-update-requirements-2026-05-21.md
---

# Baoyu Skill Update Execution Plan

## Problem Frame

The local Nemo skill set has drifted from the newer upstream Baoyu skill set, but the target is not a wholesale sync. The implementation should selectively absorb useful workflow rules while preserving Nemo's own source of truth, provider routing, Obsidian clipping path, and API-first WeChat publisher.

The origin document is `docs/brainstorms/baoyu-skill-update-requirements-2026-05-21.md`. This plan treats it as the source of truth.

Plan depth: Standard.

## Scope

In scope:

- Consolidate image generation around `skills/baoyu-image-gen`.
- Add or clarify batch and reference-image behavior using Nemo's own providers only.
- Update visual skill rules for safer raster generation behavior.
- Update X Article publishing guidance and verification around image upload safety.
- Remove `skills/baoyu-url-to-markdown` as an active entrypoint.
- Make `article-clip-obsidian` the documented URL clipping path.
- Keep `wechat-publisher` as Nemo's own API-first publisher and absorb only compatible reliability ideas.
- Update mapping and retention docs so publish surface matches the new decisions.

Out of scope:

- Adding `baoyu-imagine`.
- Importing upstream provider families or generic API-base compatibility.
- Migrating upstream `baoyu-post-to-wechat` as a skill.
- Replacing `wechat-publisher` templates with upstream Baoyu themes.
- Adding browser/CDP publishing as the primary WeChat path.
- Migrating unrelated upstream Baoyu skills.

## Key Decisions

1. `baoyu-image-gen` stays as the public image router.

   Rationale: the local router already captures the desired split between prompt layer, native image generation, and local provider fallback. Upstream `baoyu-imagine` overlaps too much and brings provider complexity that the origin document explicitly rejects.

2. `kie-image-gen` and `tryvalo-imagegen` are treated as provider channels, not primary user-facing routes.

   Rationale: they may still be useful for local rendering, but the user-facing decision should happen in `baoyu-image-gen`.

3. URL clipping moves to `article-clip-obsidian`.

   Rationale: `article-clip-obsidian` already defines the web-access acquisition contract and Obsidian output contract. Keeping `baoyu-url-to-markdown` as a second public path recreates the duplicate entrypoint problem.

4. `wechat-publisher` remains API-first.

   Rationale: the local publisher already handles Obsidian Markdown, WeChat API credentials, proxy, cover upload, article image upload, templates, and diagnostics. Upstream browser publishing is intentionally excluded.

5. Publish-generated vault copies are updated only after source changes verify clean.

   Rationale: this repository is the source of truth. Vault copies under `.agents/skills` are managed artifacts.

## Implementation Units

### U1: Normalize Active Skill Inventory

Purpose:

- Make retention and mapping documents reflect the accepted migration surface before touching behavior.

Files:

- `docs/mapping.json`
- `docs/migration-inventory.md`
- `docs/skill-retention.md`
- `docs/upstream-notes.md`
- `README.md`

Changes:

- Change `baoyu-url-to-markdown` from active migration to delete/retired.
- Update the retention note that currently says `article-clip-obsidian` handles Obsidian clipping while `baoyu-url-to-markdown` handles generic Markdown conversion.
- Update migration inventory and README references so they no longer present `baoyu-url-to-markdown` as a retained active tool.
- Reword the image provider boundary so `kie-image-gen` and `tryvalo-imagegen` are provider channels under `baoyu-image-gen`, not equal public choices.
- Record that upstream `baoyu-post-to-wechat` is not being migrated because `wechat-publisher` remains the local WeChat path.

Test scenarios:

- Mapping consistency: `docs/mapping.json` no longer lists `baoyu-url-to-markdown` with `migrate_now`.
- Retention consistency: `docs/skill-retention.md` no longer lists `baoyu-url-to-markdown` under Publish Now.
- Inventory consistency: `docs/migration-inventory.md` and `README.md` no longer advertise `baoyu-url-to-markdown` as keep/publish/current.
- Boundary consistency: retention docs still list `article-clip-obsidian`, `baoyu-image-gen`, `wechat-publisher`, `baoyu-post-to-x`, and `baoyu-translate` as active.

Dependencies:

- None.

### U2: Consolidate `baoyu-image-gen` Routing

Purpose:

- Make `baoyu-image-gen` the single image router and remove upstream provider-zoo assumptions from the user-facing contract.

Files:

- `skills/baoyu-image-gen/SKILL.md`
- `skills/baoyu-image-gen/scripts/main.ts`
- `skills/baoyu-image-gen/scripts/types.ts`
- `skills/baoyu-image-gen/scripts/providers/openai.ts`
- `skills/baoyu-image-gen/scripts/providers/google.ts`
- `skills/kie-image-gen/SKILL.md`
- `skills/tryvalo-imagegen/SKILL.md`

Changes:

- Update the routing policy to say all normal image requests start at `baoyu-image-gen`.
- Keep Codex native image generation as the first route when available.
- Keep local provider execution for filesystem output, batch output, reference images, or explicit backend requests.
- Clarify that local provider support means Nemo's current providers only.
- Ensure reference-image support is documented as image-to-image/reference editing.
- Ensure batch generation is expressed as repeated local provider runs or `--n` support where the script already supports it, without importing upstream provider families.
- Reclassify `kie-image-gen` and `tryvalo-imagegen` docs as provider/compatibility channels if they remain published.

Test scenarios:

- Native-first behavior: a normal prompt-only request should tell the agent to use Codex native image generation first.
- Filesystem-output behavior: a request requiring a specific local output path should allow local provider script use.
- Reference-image behavior: a request with one or more source images should route to the local provider path that supports references.
- Batch behavior: a request for multiple images should be represented through the local provider capabilities, not upstream `baoyu-imagine`.
- Provider boundary: no doc or CLI help suggests adding upstream GPT Image 2, DashScope, MiniMax, Jimeng, Seedream, Replicate, Z.AI, Azure, or OpenRouter unless already implemented locally.

Dependencies:

- U1 should land first so public surface decisions are settled.

### U3: Update Visual Skill Safety Rules

Purpose:

- Make article visual skills follow the accepted raster-generation and text-handling policy.

Files:

- `skills/article-illustrate/SKILL.md`
- `skills/article-illustrate/references/cover.md`
- `skills/article-illustrate/references/body-illustrations.md`
- `skills/article-illustrate/references/output-contract.md`
- `skills/baoyu-article-illustrator/SKILL.md`
- `skills/baoyu-article-illustrator/references/usage.md`
- `skills/baoyu-article-illustrator/references/prompt-construction.md`
- `skills/baoyu-cover-image/SKILL.md`
- `skills/baoyu-cover-image/references/base-prompt.md`
- `skills/baoyu-infographic/SKILL.md`
- `skills/baoyu-infographic/references/base-prompt.md`

Changes:

- Add a shared rule in the relevant docs: SVG, HTML, canvas, and Mermaid are not substitutes for requested raster generation.
- Add a text policy: do not repair bad generated text by overlaying text with bitmap/vector tooling.
- State the approved recovery paths for image text problems: regenerate, lower/remove text, or ask the user.
- Keep prompt-file-first behavior for article-scale batch illustration workflows.
- Preserve explicit confirmation behavior unless the user clearly asks for direct generation.

Test scenarios:

- Cover request: a cover image request should end with a real raster generation route, not an SVG fallback.
- Body illustration batch: the workflow should create prompts before generation.
- Infographic text problem: instructions should forbid programmatic text overlay repair and prefer regeneration or reduced text.
- Direct-generation request: when the user explicitly asks to generate directly, the skill should not force an extra confirmation loop.

Dependencies:

- U2 should land first or in parallel if the implementer only edits docs. If any visual skill invokes provider details, align it with U2 wording.

### U4: Refresh `baoyu-post-to-x` Article Publishing Rules

Purpose:

- Preserve local X publishing behavior while absorbing the safe upload handling from upstream.

Files:

- `skills/baoyu-post-to-x/SKILL.md`
- `skills/baoyu-post-to-x/references/articles.md`
- `skills/baoyu-post-to-x/scripts/x-article.ts`
- `skills/baoyu-post-to-x/scripts/x-browser.ts`
- `skills/baoyu-post-to-x/scripts/x-utils.ts`

Changes:

- Keep final X Article publish manual/explicit.
- Ensure article image upload uses the toolbar Media flow, not clipboard image paste into article body.
- Keep or add the hard gate that a placeholder disappears and article image count increases after each insert.
- Document the user-selected browser-control mode rule where applicable.
- Avoid changing regular post behavior unless shared helper changes require it.

Test scenarios:

- X Article preview: running the article path should compose/open preview and not final-publish automatically.
- Cover handling: a dedicated cover remains a cover and does not consume the first inline image.
- Inline image insertion: each inserted image must remove the matching placeholder and increase the image count.
- Failure handling: if insertion fails, the script should not silently delete placeholders or continue to preview.
- Browser-mode respect: when a profile or mode is specified, docs and script behavior should not override it silently.

Dependencies:

- U1 can land first, but U4 is otherwise independent.

### U5: Retire `baoyu-url-to-markdown`

Purpose:

- Remove the duplicate generic URL conversion entrypoint and route clipping to `article-clip-obsidian`.

Files:

- `skills/baoyu-url-to-markdown/SKILL.md`
- `skills/baoyu-url-to-markdown/scripts/constants.ts`
- `skills/baoyu-url-to-markdown/scripts/cdp.ts`
- `skills/baoyu-url-to-markdown/scripts/html-to-markdown.ts`
- `skills/baoyu-url-to-markdown/scripts/main.ts`
- `skills/baoyu-url-to-markdown/scripts/paths.ts`
- `skills/article-clip-obsidian/SKILL.md`
- `docs/mapping.json`
- `docs/migration-inventory.md`
- `docs/skill-retention.md`
- `docs/upstream-notes.md`
- `README.md`

Changes:

- Delete `skills/baoyu-url-to-markdown` unless dependency search finds an active local reference that requires a temporary compatibility note.
- If a temporary compatibility note is required, make it explicit and plan a follow-up deletion; do not keep it as active.
- Ensure `article-clip-obsidian` remains the URL clipping route for Obsidian output.
- Remove active publish mapping for `baoyu-url-to-markdown`.
- Update every current-facing index or inventory that still lists `baoyu-url-to-markdown` as keep/current/publishable.

Test scenarios:

- Reference scan: no active skill depends on `skills/baoyu-url-to-markdown` after deletion.
- Mapping scan: `baoyu-url-to-markdown` is not publishable as active, meaning it is absent from `migrate_now` and cannot be selected by `--only-migrate-now`.
- Public-doc scan: current-facing docs such as `README.md`, `docs/migration-inventory.md`, `docs/skill-retention.md`, and `docs/upstream-notes.md` do not describe `baoyu-url-to-markdown` as retained.
- Clipping route: URL clipping instructions point to `article-clip-obsidian` and `web-access`.
- Generated vault behavior: if publish is run, removed managed copies are handled intentionally rather than left as active stale skills.

Dependencies:

- U1 should happen before or with U5.

### U6: Keep `wechat-publisher` Local and Add Only Compatible Reliability Work

Purpose:

- Keep the local WeChat publisher as the only WeChat publishing path, while absorbing small reliability improvements that fit the API-first model.

Files:

- `skills/wechat-publisher/SKILL.md`
- `skills/wechat-publisher/README.md`
- `skills/wechat-publisher/wechat-publisher.example.json`
- `skills/wechat-publisher/index.js`
- `skills/wechat-publisher/lib/config.js`
- `skills/wechat-publisher/lib/config.test.js`
- `skills/wechat-publisher/lib/image.js`
- `skills/wechat-publisher/lib/image.test.js`
- `skills/wechat-publisher/lib/publish.js`
- `skills/wechat-publisher/lib/publish.test.js`
- `skills/wechat-publisher/lib/wechat.js`
- `skills/wechat-publisher/lib/wechat.test.js`
- `skills/wechat-publisher/templates/styles.js`
- `skills/wechat-publisher/templates/styles.test.js`

Changes:

- State that `wechat-publisher` is the only WeChat publishing skill.
- Keep config rooted in the existing user-level config file.
- Keep existing template IDs and do not replace them with upstream Baoyu themes.
- Improve image diagnostics where current tests show a gap: cover upload vs article image upload, WebP handling, and media-id failures.
- Keep optional citation or external-link footnote behavior deferred unless a clear local article-pipeline need appears during implementation.
- Treat multi-account support and account-specific publish settings as gated optional work: implement them only if the current code already has a small, backward-compatible extension path and they do not expand the migration beyond reliability cleanup.

Test scenarios:

- Default account: existing single-account config continues to work without migration.
- Cover upload failure: errors identify the cover upload path separately from article image upload.
- Article image failure: errors identify the article image upload path separately from cover upload.
- Template behavior: existing template tests still pass and no upstream theme IDs become required.
- Config compatibility: `wechat-publisher.example.json` documents the new shape without breaking the old shape.
- Optional multi-account compatibility, only if implemented: when `accounts.default` exists, publishing uses that account by default; when an account is specified, credentials and account-specific defaults come from that account.

Dependencies:

- U1 should land first for public-surface clarity.
- U6 can be implemented independently from image and X work.

### U7: Refresh `baoyu-translate` From Upstream Workflow Docs

Purpose:

- Update translation instructions where upstream refined workflow or subagent templates are clearer, without changing the local three-mode model.

Files:

- `skills/baoyu-translate/SKILL.md`
- `skills/baoyu-translate/references/refined-workflow.md`
- `skills/baoyu-translate/references/subagent-prompt-template.md`
- `skills/baoyu-translate/references/workflow-mechanics.md`

Changes:

- Compare local references against upstream refined workflow guidance.
- Absorb wording or sequencing improvements that do not change the local quick/normal/refined mode contract.
- Preserve local first-time setup, EXTEND.md behavior, glossary behavior, chunking behavior, and output directory structure unless upstream has a clearly better version that matches the origin requirements.

Test scenarios:

- Quick mode: still translates directly and saves `translation.md`.
- Normal mode: still analyzes, assembles prompt, translates, and offers later refinement.
- Refined mode: still analyzes, drafts, reviews, revises, and polishes.
- Chunked long content: shared prompt and chunk merge behavior remain documented.
- Image-language reminder: translated articles still include the post-translation image-language check.

Dependencies:

- None. U7 can be implemented in parallel with U2-U6.

### U8: Publish Verification and Vault Sync

Purpose:

- Verify source changes and publish managed copies only after source behavior and docs are aligned.

Files:

- `scripts/publish-to-vault.mjs`
- `scripts/verify-publish.mjs`
- `scripts/rollback-publish.mjs`
- `docs/mapping.json`
- Changed skill directories from U2-U7

Changes:

- Run source checks relevant to changed units.
- Verify changed entries after source edits.
- Publish changed managed entries into the vault only after source verification is clean.
- Verify published entries again.
- If `baoyu-url-to-markdown` is deleted, handle its generated vault copy explicitly. `publish-to-vault.mjs` refuses non-`migrate_now` entries and does not delete retired targets by itself, so the implementation must either add and verify a deliberate retirement path or manually remove the managed vault copy after confirming its `.nemo-managed.json` / `.nemo-manifest.json` ownership and backing it up.
- Document the chosen retirement action in the implementation notes so future publish runs do not recreate or leave stale active copies.

Test scenarios:

- Verify each changed active entry returns clean.
- Publish each changed active entry without unmanaged drift.
- Removed entry does not reappear as active in generated vault copies, and `.agents/skills/baoyu-url-to-markdown` is absent or intentionally archived after the retirement step.
- Negative publish selection: `baoyu-url-to-markdown` is not selected by `node scripts/verify-publish.mjs --only-migrate-now` and is refused by `node scripts/publish-to-vault.mjs --entry-id baoyu-url-to-markdown --mode OverwriteManagedClean --dry-run` after its mapping status changes away from `migrate_now`.
- Existing unrelated dirty files are not reverted or bundled accidentally.

Dependencies:

- U1-U7 complete.

## Sequencing

Recommended order:

1. U1: normalize inventory and mapping.
2. U5: retire `baoyu-url-to-markdown`, because it affects mapping and publish surface.
3. U2 and U3: align image router and visual skill policy.
4. U4, U6, and U7: update X, WeChat, and translation independently.
5. U8: verify and publish managed copies only after source changes are stable.

Parallel-safe work:

- U4 and U7 can run in parallel after U1.
- U6 can run in parallel if the implementer owns only `skills/wechat-publisher`.
- U2 and U3 should coordinate wording because visual skills reference image routing policy.

## Risk Notes

- Existing worktree changes must be preserved. Implementation should inspect current diffs before editing any file already dirty.
- Deleting `skills/baoyu-url-to-markdown` may expose hidden references in docs or mapping; run a reference scan before final deletion.
- Multi-account support in `wechat-publisher` can grow scope quickly. Keep the first implementation compatibility-focused: existing single-account config must keep working.
- Provider consolidation should avoid silently breaking explicit `kie-image-gen` or `tryvalo-imagegen` user requests if those skills are still published.
- Publishing to the vault can create generated diffs under `.agents/skills`; treat those as artifacts and keep the source repo changes reviewable first.
- Changing `baoyu-url-to-markdown` to a retired/deleted mapping is not enough to remove the managed vault copy. Plan the generated-copy retirement as its own verified operation.
- The current worktree may already contain implementation edits. Review `git status --short` and file-level diffs before editing, and do not overwrite unrelated in-progress changes.

## Verification Checklist

- `docs/mapping.json` and `docs/skill-retention.md` agree about active, deleted, and provider-only skills.
- `docs/migration-inventory.md`, `docs/upstream-notes.md`, and `README.md` do not advertise retired skills as current.
- No local `baoyu-imagine` directory exists.
- `baoyu-url-to-markdown` is not active in source mapping or retention docs.
- The generated vault copy for `baoyu-url-to-markdown` is either absent or explicitly archived after verifying managed ownership.
- `article-clip-obsidian` is the documented URL clipping route.
- `baoyu-image-gen` describes native-first routing, own providers, batch, and reference-image behavior.
- Visual skills forbid SVG/HTML/canvas/Mermaid raster substitution and programmatic text repair.
- X Article docs/scripts keep manual final publish and image upload safety gates.
- `wechat-publisher` tests pass if JavaScript code changes.
- `baoyu-translate` still documents quick, normal, and refined modes.
- Changed active skills verify clean before vault publishing.

Suggested verification commands:

```bash
rg -n "baoyu-url-to-markdown|url-to-markdown" README.md docs skills -g "!docs/brainstorms/**" -g "!docs/plans/**"
node scripts/verify-publish.mjs --entry-id article-clip-obsidian
node scripts/verify-publish.mjs --entry-id baoyu-image-gen
node scripts/verify-publish.mjs --entry-id baoyu-post-to-x
node scripts/verify-publish.mjs --entry-id baoyu-translate
node scripts/verify-publish.mjs --entry-id wechat-publisher
node scripts/verify-publish.mjs --only-migrate-now
```

If `wechat-publisher` JavaScript changes:

```bash
cd skills/wechat-publisher
bun test
```

If managed vault copies are published:

```bash
node scripts/publish-to-vault.mjs --entry-id <changed-skill-id> --mode OverwriteManagedClean
node scripts/verify-publish.mjs --entry-id <changed-skill-id>
```

If `baoyu-url-to-markdown` is retired:

```bash
node scripts/publish-to-vault.mjs --entry-id baoyu-url-to-markdown --mode OverwriteManagedClean --dry-run
```

Expected result after mapping changes: the command must refuse to publish the non-`migrate_now` entry. Then verify and remove or archive the existing `.agents/skills/baoyu-url-to-markdown` managed copy through the chosen retirement path instead of relying on publish to delete it.

## Deferred Decisions

- Decide during implementation whether `kie-image-gen` and `tryvalo-imagegen` remain separately published compatibility skills for one cycle or become internal-only provider references.
- Defer WeChat citation/external-link footnotes unless implementation finds a concrete local article-pipeline need.
