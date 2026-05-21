---
name: article-illustrate
description: Unified article visual skill. Use when the user asks to illustrate an article, generate article visuals, make a cover for an article, add body illustrations, or 给文章配图. It routes article-visual intents to cover and body-illustration references, keeps one visual style across the article, and renders through baoyu-image-gen with Codex native image generation as the required first attempt.
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
   - **Mandatory Baoyu prompt contract**: article visuals must use the prompt structure from the Baoyu visual sub-skills, not freeform scene prompts.
   - For covers, construct the prompt from `../baoyu-cover-image/references/base-prompt.md` plus the selected `../baoyu-cover-image/references/styles/<style>.md` when that style exists.
   - For body illustrations, construct each prompt with `../baoyu-article-illustrator/references/prompt-construction.md` templates such as `Comparison`, `Process Flow`, `Framework`, `Timeline`, or `Scene`, plus the matching style reference under `../baoyu-article-illustrator/references/styles/`.
   - If a selected article-level style has no exact body-illustration style file, choose the closest Baoyu body style and record that mapping in the prompt file.
   - Do not write ordinary descriptive prompts such as "create an illustration of..." unless they are inside the Baoyu template structure.
6. Render through `baoyu-image-gen`.
   - Use Codex native image generation as the required first attempt whenever the current Codex session exposes it.
   - If Codex native image generation succeeds but writes outside the article asset directory, copy the generated raster image into the output-contract path and leave the original generated file in place.
   - If Codex native image generation is unavailable or fails, try a non-SVG raster fallback backend through `baoyu-image-gen` only when a local provider route is available.
   - Never generate or insert SVG images for article visuals.
   - If neither Codex native image generation nor a non-SVG raster fallback is available, stop and report that no usable image-generation route was found.
7. Save images and prompt files using the output contract.
8. Insert body illustration links into the article when body illustrations are generated.

## Sub-Skills

`baoyu-cover-image` and `baoyu-article-illustrator` are compatibility sub-skills, but their prompt systems are authoritative. This skill owns the article-level decision, shared style, output directory, and insertion flow; Baoyu sub-skills own the cover/body prompt shape. Call or mirror their bounded prompt construction after this skill has selected the route and style. Do not bypass their references when generating article images.

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
