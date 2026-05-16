---
name: article-illustrate
description: Unified article visual skill. Use when the user asks to illustrate an article, generate article visuals, make a cover for an article, add body illustrations, or 给文章配图. It routes article-visual intents to cover and body-illustration references, keeps one visual style across the article, and renders through baoyu-image-gen with Codex official image generation preferred.
---

# Article Visuals

Unified entrypoint for article visuals. Use this skill for article covers, body illustrations, or a full article visual package.

This skill is intentionally article-scoped. For standalone infographics or one-image structural summaries, use `baoyu-infographic` instead.

## Routing

Infer the article-visual intent from the user request:

| User intent | Route |
|-------------|-------|
| "配图", "给文章加图", "生成文章视觉", "cover + illustrations" | Full package: cover + body illustrations |
| "封面", "标题图", "cover", "头图" | Cover only |
| "正文配图", "插图", "illustrations", "body visuals" | Body illustrations only |

If the intent is unclear but the input is an article, default to the full package. Ask only when the user request implies mutually exclusive outputs, such as "只要一张图" without saying whether it is cover or body.

## References

Load only the references needed for the chosen route:

- Full package: read `references/style-system.md`, `references/cover.md`, `references/body-illustrations.md`, and `references/output-contract.md`
- Cover only: read `references/style-system.md`, `references/cover.md`, and `references/output-contract.md`
- Body illustrations only: read `references/style-system.md`, `references/body-illustrations.md`, and `references/output-contract.md`

## Workflow

1. Read the article file or article text.
2. Determine the route from the request.
3. Analyze article topic, audience, tone, publishing channel, and language.
4. Select or confirm one article-level visual style.
   - If the user provides `--style`, use it.
   - Otherwise recommend 3 styles and ask once.
5. Generate prompt files for the selected route.
6. Render through `baoyu-image-gen`.
   - Prefer Codex official image generation when available.
   - Use provider backends only when explicitly requested, official generation is unavailable, or deterministic local file output is required.
7. Save images and prompt files using the output contract.
8. Insert body illustration links into the article when body illustrations are generated.

## Sub-Skills

`baoyu-cover-image` and `baoyu-article-illustrator` are compatibility sub-skills. This skill owns the article-level decision, shared style, and route. Call sub-skills only for their bounded slice after this skill has selected the route and style, or when the user explicitly asks for that slice directly.

## Options

| Option | Description |
|--------|-------------|
| `--style <name>` | Use the specified article-level visual style |
| `--image-dir <path>` | Override the detected article asset directory |
| `--cover-only` | Generate only the article cover |
| `--body-only` | Generate only body illustrations |
| `--no-title` | Generate cover without title text |

## Completion

Report:

- Article path or title
- Selected route
- Style
- Prompt files written
- Images generated
- Insertions made, if any
- Renderer/backend used
