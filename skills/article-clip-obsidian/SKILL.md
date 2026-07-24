---
name: article-clip-obsidian
description: Acquire articles through web-access, normalize them into an article package, and convert them to Obsidian format. Use when user asks to "download article", "clip article", "save article", provides an article URL, or wants to save web content to their Obsidian vault. If the user explicitly asks to save and absorb/extract into LLM Wiki, clip first and then hand the saved source note to llm-wiki; do not run LLM Wiki for ordinary clipping requests.
---

# Article Clip Obsidian

Acquire articles with `web-access`, normalize the capture into `content.md + assets/`, then convert it to the vault's Obsidian clipping format.

## Source of Truth

This skill is managed from the sibling `nemo-skills` repository. In the current vault, `.agents/skills/article-clip-obsidian/` is a symbolic link to this source directory, not a generated copy. Edit the `nemo-skills` source directly (or through that symlink); no publish or managed-copy verification step is required.

## Workflow

## LLM Wiki Boundary

This skill owns source capture only. It saves the original article as a clipping; it does not extract durable knowledge, update `03_Notes`, or decide whether old wiki pages should change unless the user explicitly asks for LLM Wiki absorption in the same request.

Default behavior:

- `保存` / `剪藏` / `下载` / `导入 URL` means clip only.
- Do not call `llm-wiki` automatically after ordinary clipping.
- Every ordinary clipping starts with `llm_status: new`. Do not add `llm_domain`, `llm_note`, or `derived_refs` during capture; those fields describe an actual absorption result, not the capture itself.

Explicit handoff behavior:

- If the user says `保存并吸收`, `剪藏后用 llm-wiki`, `入库后提取`, `save and ingest`, or an equivalent explicit request, finish and verify the clipping first.
- After clipping verification succeeds, immediately pass the generated source note path to `../llm-wiki/SKILL.md` / `llm-wiki-ingest` and execute the full absorption chain in the same request. Do not stop after clipping or merely suggest the handoff.
- Treat the saved clipping as a primary source. Let `llm-wiki` resolve the domain, check the intake board, apply the update-first rule, and obey its policy gate before writing `03_Notes`.
- Report the clipping result and the LLM Wiki result as separate outcomes. If absorption is blocked by domain ambiguity or a confirmation gate, report that the clipping succeeded but the combined `保存并吸收` request is waiting at the absorption gate.

## Non-Negotiable Output Contract

When this skill is triggered by a user asking to download, clip, save, or import a URL into the Obsidian vault, follow this contract unless the user explicitly names a different destination:

- Markdown output must be created under `02_Sources/_clippings`.
- Image output must be created under `assets/YYYYMMDDHHmm 标题/`.
- Do not route clippings to project-specific working folders such as `04_Projects/AI_Media/素材池/_clippings` based on prior workflow habits or inferred content-production context.
- Do not hand-create a simplified note as a substitute for this workflow. Use `web-access-adapter.js` and `convert.js` as the leaf path.
- Do not silently degrade to a text-only clipping when the source has images. If remote image localization fails, fix the capture by downloading the images locally and passing them through `assets`, then rerun the adapter and converter.
- A clipping is not complete while any remote Markdown image reference remains in the note.
- A clipping is not complete until all Obsidian embeds point to existing local files.

### 1. Resolve web-access

Before any network acquisition, resolve the `web-access` skill in this exact order:

1. Project skill under the target vault: `.agents/skills/web-access/`, then legacy `.skills/web-access/`
2. Global Codex skill: `~/.codex/skills/web-access/`
3. Legacy fallback path below, only when neither project nor global `web-access` exists

From the vault root, use the resolver:

```bash
node .agents/skills/article-clip-obsidian/resolve-web-access-skill.js "$PWD"
```

Load and follow the returned `skillFile` when `status` is `found`. Do not use `~/.agents/skills/web-access/` as a normal candidate; this workflow has one global source at `~/.codex/skills/web-access/`.

### 2. Acquire Article Through web-access

All network access must load and follow the resolved `web-access` skill first.

Use `web-access` to choose the lightest reliable acquisition route:
- Public article or documentation page: Jina/WebFetch/curl can be enough.
- WeChat, Zhihu, X/Twitter, Xiaohongshu, login-required pages, or dynamic pages: use Chrome CDP through `web-access`.
- When CDP is used, follow `web-access` requirements: run its dependency check, show its automation-risk notice to the user, use a self-created background tab, check site-pattern references when available, and close the tab when done.

#### CDP recovery before asking the user

Treat CDP connectivity and website login as separate states. A failed `check-deps.mjs` only proves that the automation proxy is not attached yet; it does **not** prove that the user is logged out.

For a browser-backed source, recover in this order before asking the user to do anything:

1. Start the configured browser when it is not running, then rerun `check-deps.mjs` after a brief wait.
2. If it still fails, use an unsandboxed local check to inspect the browser process, the configured debugging port, and `http://127.0.0.1:<port>/json/version`. A response containing `webSocketDebuggerUrl` means CDP is available; rerun `check-deps.mjs` and continue.
3. Only after CDP is confirmed available should the agent infer login state from the target page itself. Do not tell the user to log in, enable debugging, or otherwise change their browser until the target page demonstrably shows a login wall or the local checks show that CDP cannot be enabled automatically.

Report the actual condition precisely: for example, say “automation has not attached to Chrome yet” rather than “you are not logged in.”

The acquisition result must be normalized into a capture JSON with this shape:

```json
{
  "url": "https://example.com/article",
  "title": "Article title",
  "author": "Author name",
  "published_at": "2026-05-01T09:00:00+08:00",
  "captured_at": "2026-05-03T10:20:00+08:00",
  "platform": "example.com",
  "markdown": "# Article title\n\nArticle body...",
  "assets": [
    { "path": "C:/tmp/article-assets/001.jpg", "filename": "001.jpg" }
  ]
}
```

Required fields:
- `url`
- non-empty `markdown`

Recommended fields:
- `title`
- `author`
- `published_at`
- `captured_at`
- `platform`
- `assets` when images were downloaded locally

If `title` or `platform` is missing, the adapter uses a safe fallback. Missing, blank, or placeholder `author` values such as `unknown` stay absent from the final note. Missing `published_at` is not inferred from capture time. If `url` or `markdown` is missing, the adapter fails.

### 3. Create Article Package

Run the adapter against the capture JSON:

```bash
node .agents/skills/article-clip-obsidian/web-access-adapter.js \
  /tmp/article-capture.json \
  /tmp/article-clip-temp
```

The adapter creates:
- `/tmp/article-clip-temp/content.md`
- `/tmp/article-clip-temp/assets/` when local images were provided

The adapter also scans Markdown image references such as `![alt](https://...)`. Any remaining remote image is downloaded into the package `assets/` directory and rewritten to `./assets/NNN.ext`. If a remote image cannot be downloaded after retries, the adapter fails instead of silently leaving a remote image in the note.

### 4. Convert to Obsidian Format

Run the conversion script from the vault root:

```bash
node .agents/skills/article-clip-obsidian/convert.js \
  /tmp/article-clip-temp/content.md \
  02_Sources/_clippings \
  assets
```

In the current vault, use `.agents/skills/article-clip-obsidian/...`; it is a symlink to the `nemo-skills` source. Use `.skills/...` only if that is the active skill path in another target vault.

The `02_Sources/_clippings` argument is the default destination. Change it only when the user explicitly asks for a different destination in the current request.

The converter:
- Generates filename: `YYYYMMDDHHmm 标题.md` using `fetched_at`
- Keeps the full cleaned article title in frontmatter `title`; only filenames and asset directories are shortened for filesystem safety
- Stores the original URL in frontmatter `source`
- Includes `author` and `published` only when the package provides them
- Sets `llm_status: new` so every entry uses the same intake state
- Does not output `created`, `refs`, `ddc`, `llm_domain`, `llm_note`, or `platform`
- Transforms frontmatter to the vault clipping standard
- Moves local images to `assets/YYYYMMDDHHmm 标题/`
- Updates local image references to wiki-link format: `![[assets/YYYYMMDDHHmm 标题/001.jpg]]`
- Converts linked Markdown images like `[![alt](./assets/001.jpg)](https://...)` into plain Obsidian embeds like `![[assets/YYYYMMDDHHmm 标题/001.jpg]]`
- Fails instead of overwriting when the target note already exists.

### 5. Legacy Fallback: article-clip

If the resolver returns `status: "fallback"`, or if resolved `web-access` acquisition fails and the target is known to work better with `article-clip`, use it as a fallback:

```bash
article-clip "URL" --out /tmp/article-clip-temp --verbose
```

Then run `convert.js` as in step 4.

This fallback is for compatibility only. The default acquisition path is `web-access`.

### 6. Report Results

After conversion, report:
- Note location
- Number of images processed
- Acquisition route used: web-access route or legacy article-clip fallback
- Any issues encountered
- Whether LLM Wiki absorption was requested and, if so, the separate handoff result

Before reporting completion, verify:
- The note path starts with `02_Sources/_clippings/`, unless the user explicitly requested another destination.
- No Markdown image reference points to `http://` or `https://`.
- No platform image CDN such as `pbs.twimg.com` remains in the note body.
- Every `![[assets/...]]` embed points to an existing local file.
- The note frontmatter includes the clipping standard fields: `type: source`, `status: active`, `tags: [source]`, `title`, `source` containing the original URL, and `llm_status: new`.
- Optional `author` and `published` fields are present only when available; `created`, `refs`, `ddc`, `llm_domain`, `llm_note`, and `platform` are absent.

Example: `Article saved to 02_Sources/_clippings/202603061234 文章标题.md with 5 images. Acquisition: web-access CDP.`

## Obsidian Format Standards

Frontmatter:

```yaml
---
type: source
status: active
tags: [source]
title: "文章标题"
source: "原始URL"
llm_status: new
author: "作者名" # optional
published: YYYY-MM-DD # optional
---
```

File structure:
- Markdown: `02_Sources/_clippings/YYYYMMDDHHmm 标题.md`
- Images: `assets/YYYYMMDDHHmm 标题/001.jpg`, `002.jpg`, etc.
- Flat structure in `_clippings`

## Error Handling

- **web-access dependency check fails**: Follow `web-access` setup guidance before trying CDP. If CDP is not needed, use a lighter web-access route.
- **Login required**: Ask the user to log in through their normal Chrome only when the target content cannot be obtained without login.
- **Empty capture**: Do not convert. Re-check the web-access route, scroll/lazy-load state, DOM extraction target, or fallback path.
- **Adapter fails**: Fix the capture JSON so it includes a valid `url` and non-empty `markdown`. If the failure is remote image localization, retry the capture or download the listed image manually and include it in `assets`.
- **Remote image localization fails**: Treat this as a recoverable workflow error, not permission to skip images. Use a reliable downloader such as `curl` to localize the images first, include them in capture `assets`, and rerun `web-access-adapter.js` followed by `convert.js`.
- **article-clip fallback fails**: Report the failure and return to `web-access` route selection instead of retrying blindly.
- **Output file already exists**: The converter fails before overwriting. Inspect the existing clipping, then choose a new capture timestamp/title or report the duplicate.
- **Zhihu placeholder images**: If Zhihu exports only failed `data:image/svg+xml` lazy-load placeholders and no actual image references, the converter removes the noisy `图片下载提示` section.

## Notes

- Use capture time (`captured_at` / `fetched_at`) for filename timestamp.
- If publication time is available, normalize `published_at` to optional frontmatter `published`; it does not control the filename.
- Preserve original content structure and formatting where possible.
- Handle Chinese characters properly in filenames.
- Clean up temporary capture/package directories after successful conversion.
