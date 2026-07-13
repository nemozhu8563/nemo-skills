# Article Clip Obsidian

将网页文章保存为 Obsidian vault 里的标准 clipping。

底层分成三层：

1. `web-access` 获取文章内容，按页面情况选择 Jina/WebFetch/curl/Chrome CDP。
2. `web-access-adapter.js` 把获取结果标准化成 `content.md + assets/`。
3. `convert.js` 把标准文章包转换成 Obsidian note 和 wiki-link 图片引用。

`article-clip` 仍可作为兼容 fallback，但不再是默认获取层。

`web-access` 解析顺序固定为：目标 vault 的项目级 `.agents/skills/web-access/`，然后 legacy `.skills/web-access/`，然后全局 `~/.codex/skills/web-access/`。只有项目和全局都不存在时才进入 legacy fallback；不要把 `~/.agents/skills/web-access/` 当成常规候选。

如果 Markdown 里还残留 `![alt](https://...)` 远程图片，adapter 会默认下载到本地 `assets/` 并改写引用。下载失败会报错中断，不会静默生成半本地、半远程的 note。

## Source of Truth

本目录是源头目录。当前 vault 里的 `.agents/skills/article-clip-obsidian/` 是指向本目录的软链接，不是 managed copy。直接修改 `nemo-skills` 源头（或通过该软链接修改）即可，无需 publish / verify。

## Files

```text
skills/article-clip-obsidian/
├── SKILL.md
├── README.md
├── convert.js
├── convert.test.js
├── resolve-web-access-skill.js
├── resolve-web-access-skill.test.js
├── web-access-adapter.js
└── web-access-adapter.test.js
```

## Dependencies

- Node.js 18+
- `web-access` skill for all network acquisition
- Optional: `article-clip` CLI for legacy fallback

No package-level npm dependencies are required for the adapter or tests.

## Capture Package Contract

The adapter consumes a JSON capture:

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

Required:

- `url`
- non-empty `markdown`

Optional fields:

- `title`: heading, first text line, or URL-derived title
- `author`: keep only a real non-empty value; otherwise omit it, including placeholders such as `unknown`
- `published_at`: keep only a real non-empty publication time; do not infer it from capture time
- `captured_at`: use the current time when absent; this is internal filename-timestamp input only
- `platform`: URL hostname

## Usage

From the vault root, after acquiring content with `web-access` and writing a capture JSON:

```bash
node .agents/skills/article-clip-obsidian/resolve-web-access-skill.js "$PWD"

node .agents/skills/article-clip-obsidian/web-access-adapter.js \
  /tmp/article-capture.json \
  /tmp/article-clip-temp

node .agents/skills/article-clip-obsidian/convert.js \
  /tmp/article-clip-temp/content.md \
  02_Sources/_clippings \
  assets
```

In the current vault, `.agents/skills/article-clip-obsidian/...` is a symlink to this source directory. Use `.skills/...` only if that is the active skill path in another target vault.

Legacy fallback:

```bash
article-clip "URL" --out /tmp/article-clip-temp --verbose

node .agents/skills/article-clip-obsidian/convert.js \
  /tmp/article-clip-temp/content.md \
  02_Sources/_clippings \
  assets
```

## Output Format

### Filename

- Format: `YYYYMMDDHHmm 标题.md`
- Timestamp source: `fetched_at` / `captured_at`
- Duplicate target: fail before overwrite

### Frontmatter

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

`author` 和 `published` 只在真实非空值存在时输出。最终 note 不输出 `created`、`refs`、`ddc`、`llm_domain`、`llm_note`、`platform` 或内部的 `captured_at` / `fetched_at`。

### Images

Local package image references:

```markdown
![alt](./assets/001.jpg)
```

Converted Obsidian references:

```markdown
![[assets/YYYYMMDDHHmm 标题/001.jpg]]
```

Linked Markdown images are unwrapped during conversion:

```markdown
[![alt](./assets/001.jpg)](https://example.com/media-page)
```

becomes:

```markdown
![[assets/YYYYMMDDHHmm 标题/001.jpg]]
```

## Tests

Run from the `nemo-skills` repo root:

```bash
node --test \
  skills/article-clip-obsidian/convert.test.js \
  skills/article-clip-obsidian/web-access-adapter.test.js \
  skills/article-clip-obsidian/resolve-web-access-skill.test.js
```

The tests cover:

- Existing converter behavior
- Title and filename sanitization
- Zhihu placeholder notice cleanup
- Required URL validation and legacy `canonical_url` input compatibility
- Optional author/publication preservation without placeholder or capture-time fabrication
- Asset copying and reference rewriting
- Remote Markdown image localization
- Remote image download failure reporting
- Linked image unwrap to normal Obsidian embeds
- Missing date metadata failure instead of `NaNNaN...` filenames
- Duplicate output protection
- web-access resolver order: project before global before fallback
- Adapter-to-converter integration
- Sparse adapter-to-converter output without fabricated optional fields

## Changelog

### v1.2.0 (2026-07-11)

- Switched the current vault entrypoint documentation from managed copy to symlink source-of-truth semantics.
- Standardized final clipping frontmatter on `type/status/title/source/llm_status`, with optional real `author` and `published` values.
- Stopped fabricating `author: unknown` and publication time from capture time.
- Kept capture time only as internal filename-timestamp input.

### v1.1.3 (2026-06-03)

- Preserved full cleaned article title in frontmatter `source` while keeping filenames short.
- Failed clearly on missing date metadata instead of generating `NaNNaN...` filenames.
- Blocked accidental overwrite of existing clipping notes.
- Added explicit `web-access` resolution order: project, global, then fallback.
- Updated current vault command examples to use `.agents/skills/article-clip-obsidian/...`.

### v1.1.2 (2026-05-05)

- Converted linked Markdown images to plain Obsidian image embeds.
- Added regression coverage for X/Jina image links that arrive as `[![...](image)](media-page)`.

### v1.1.1 (2026-05-04)

- Localized remote Markdown image references in the adapter.
- Made remote image download failures explicit instead of silently leaving remote images in notes.
- Added regression coverage for skipped X/Jina image cases.

### v1.1.0 (2026-05-03)

- Added `web-access` as the default acquisition layer.
- Added `web-access-adapter.js` for `content.md + assets/` package generation.
- Added Node built-in test coverage for converter and adapter behavior.
- Kept `article-clip` as a legacy fallback path.

### v1.0.0 (2026-03-06)

- Initial version.
- Supported article-clip downloads for Twitter/X, Zhihu, and WeChat.
- Converted article packages to Obsidian clipping format.
