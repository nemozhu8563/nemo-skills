---
name: github-project-card
description: |
  将 GitHub 开源项目写成中文短介绍卡片。用于用户说要介绍 GitHub 项目、开源项目速写、GitHub Trending 短推、两张图配文、项目推荐、项目拆解、把 repo 写成 X/即刻/公众号短内容，或要求沿用“项目定义 + 大白话价值 + 技术可信度 + 功能清单 + 趋势判断”的模板。
---

# GitHub Project Card

Use this skill to turn a GitHub repository or open-source tool into a concise Chinese content card with a clear personal judgment. The target is not a full review or install guide; it is a readable short post for X, 即刻, 朋友圈, 公众号短文, or a topic pool note.

Default to the X version unless the user asks for a longer post. Keep the X version within 280 characters including the visible link text. If a link is included, remember X usually counts a URL as one shortened link, but still keep the draft visibly short.

## Core Style

Write like a smart operator explaining why this project matters.

The default structure:

1. One-sentence definition: `{Project}` 是一个 `{开源/自托管/本地优先/AI 原生}` 的 `{工具类型}`，支持 `{核心能力}`。
2. Plain-language value: `{Project}` 的思路很直接：`{用普通人能懂的话说清楚怎么用、解决什么问题}`。
3. Credibility layer: mention the stack, engines, integrations, protocol, model support, deployment method, or ecosystem signals that prove it is real.
4. User-visible features: list only what readers can judge quickly, such as batch processing, multi-user, history, API, Docker, privacy, templates, browser UI, plugins, or automation.
5. Trend lift: use the project as evidence for a broader shift, such as open-source self-hosting, local-first tools, AI-assisted development, agent workflows, or small teams rebuilding SaaS utilities.

Keep the language short, concrete, and non-technical where possible. Technical terms are fine when they provide credibility, but do not turn the post into documentation.

## Evidence Rules

- Do not invent capabilities, tech stacks, license terms, Star counts, benchmarks, or screenshots.
- If repo facts are missing or likely stale, verify from the repo, README, releases, docs, or screenshots before writing.
- If only the user's notes are available, write from those notes and mark uncertain facts as needing verification.
- Prefer exact project names, repo slugs, and visible feature names.
- Do not overstate maturity. Say "看起来已经能用" only when there is evidence such as UI screenshots, releases, Docker docs, examples, or active commits.
- For X drafts, keep Star counts human-readable. Prefer rounded display such as `60K Star`, `8K Star`, or `1.4K Star` after verifying the exact current number.

## Two-Image Pattern

When the post has two images, make the images do different jobs:

1. Image 1: first-impression proof
   - GitHub README top section with project name, badges, short description, and first feature list
   - README hero/product screenshot when it carries the project positioning
   - official product UI
   - CLI running screenshot if there is no UI
   - purpose: prove "this is a real project"

2. Image 2: capability proof
   - feature list
   - before/after result
   - supported formats/models/platforms
   - settings/admin page
   - Docker/deploy screen
   - release/activity evidence
   - purpose: prove "this is useful enough to try"

Avoid using a repository file-list screenshot as the default first image. It proves the repo exists, but it usually does not communicate the product. One image should establish realness; the other should establish usefulness.
Avoid using a generic GitHub repo top/header screenshot as Image 1. If README does not contain a product image, use a screenshot of the README introduction section itself, not the repository chrome.
Images are optional. If the available screenshots are weak, blurry, redundant, or do not add evidence, post with one good image or text only. Never force a low-quality second image just to satisfy a template.

## Visual Source Priority

When the user wants actual images, use this priority order:

1. Official GitHub-page visual
   - README hero image
   - README product screenshot
   - README intro section that already explains the product clearly
   - embedded official demo image from the repo page
2. Real GitHub README screenshot
   - the top README section with the value prop and first feature bullets
   - a lower README section that proves supported formats, integrations, workflow, or output
3. Generated fallback
   - when the repo page does not provide a strong, readable, official visual
   - or when the official visual is factually correct but too plain to work as an X cover image

Prefer the repo's own introduction image over a hand-made image whenever the official visual already explains the product well enough.
If the available GitHub-page images are inconsistent, blurry, duplicated, or only show repository chrome, do not force them just because they are official.
If the official image reads like documentation evidence but does not have enough visual pull for an X post, do not force it as the main image.

## Image Decision Rule

Decide whether to use images before deciding how many to use.

Use an image only when it helps a reader understand the project faster than text alone.
For X specifically, also judge whether the image has enough stopping power in a fast-scrolling feed.

Good image candidates:

- README hero/product screenshot
- README intro section with clear product definition and feature summary
- real product UI
- dashboard or settings screen that proves a concrete capability
- before/after result that is visually obvious

Usually avoid these in short posts:

- abstract flowcharts
- architecture diagrams
- Mermaid screenshots
- dependency graphs
- screenshots that require zooming in to read tiny text
- screenshots that only make sense after a long explanation

Flowcharts are not automatically useful. In most X posts they should be skipped, because they add cognitive load and do not help the reader decide whether the project is worth opening.

## X Visual Standard

Do not stop at "technically correct". Judge whether the image is actually post-worthy on X.

An X-suitable image should satisfy most of these:

- a fast-scrolling viewer can understand the topic in under 1 second
- the subject is visually concentrated, not a wall of documentation text
- the image has one obvious focal point instead of several weak ones
- the image still feels readable and intentional after X-style downscaling
- the visual gives either curiosity, clarity, or a concrete result preview

Treat these as weak-for-X even if they are true screenshots:

- plain README text blocks with no visual focal point
- dense code or terminal blocks used as the primary image
- screenshots whose value depends on careful reading
- repo pages that look like generic documentation rather than a product or result

If an official README or repo screenshot is accurate but visually flat, prefer generated fallback for the main cover image. In that case, the official screenshot can still be used as a secondary proof image if the user wants two images.

Default policy:

- 2 images only when both images are individually strong and play different roles
- 1 image when there is one strong proof image and the second candidate is weak
- 0 images when the available visuals are generic, abstract, low-quality, or non-essential

When the user asks you to actually prepare images, do not stop at a text-only image plan. Save concrete image files locally and make sure they follow the same two-image split:

- Image 1 should still be first-impression proof.
- Image 2 should still be capability proof.
- Prefer real screenshots of the repo README, product UI, dashboard, settings page, or rendered feature section over generic Open Graph cards when possible.
- Use Open Graph cards only as fallback when the repo or product does not offer a better first-screen asset, and only if the user has not forbidden repo-top style visuals.
- After capturing each image, inspect the actual image content, not only the file path or file size.

## Screenshot QA

Do not treat a screenshot as usable until it passes this checklist:

- the image shows the project itself, not the whole desktop or unrelated apps
- the main subject is readable at normal chat width without zooming in
- the image does not accidentally include Codex windows, chat panes, system popups, or other workspace noise
- the image is not clipped so aggressively that the repo name, feature heading, or proof context is lost
- Image 1 still answers "what is this"
- Image 2 still answers "why try this"
- if the image is intended for X, it still has enough visual pull after you ignore the small text

If a captured screenshot fails any of the checks above, discard it and re-capture or switch to another visual source. Do not keep a bad screenshot just because a file was already saved.

## Generated-Image Fallback

If strong GitHub-page visuals cannot be obtained, use `article-illustrate` as the fallback instead of inventing an ad hoc image workflow.

Fallback contract:

- route: `cover-only`
- style: `notion`
- allow a small amount of functional text when it helps explain the product
- the picture must explain the product's rough function at a glance
- prefer an article-style functional explainer image over an atmospheric poster
- when replacing a weak README screenshot for X, optimize for "one-glance understanding plus visual pull", not strict documentation fidelity

Fallback scene guidance:

- show the input, transformation layer, and output when the project is a converter, parser, pipeline, or automation tool
- show the core interface and result state when the project is a UI product
- show a simple before/after or source/result contrast when the project improves content, code, media, or documents
- use short labels, captions, or tiny callouts when they materially improve comprehension
- keep the text load low enough that the image still reads as a visual, not a slide
- for X covers, prefer one strong central composition over two weak explanatory zones

Avoid these fallback-image mistakes:

- decorative concept art
- abstract AI glow imagery
- large blocks of explanatory text
- screenshots recreated from imagination
- diagrams so dense that they need a caption to be understood

## Default Output

Use this when the user asks for a finished short post.

```markdown
{项目名} 是一个{定位}，支持{核心能力}。

{图 1 建议：项目首页 / 产品界面 / README 展示图}

{项目名} 的思路很直接：{大白话价值说明}。

项目基于{技术栈/关键依赖/生态}，集成/支持{关键能力}，并提供{用户可感知功能列表}。

{图 2 建议：功能证明图 / 效果图 / 支持范围截图}

{从单个项目上升到趋势判断}

{一句关于 AI 编程、开源生态、小团队产品化、隐私/自托管/local-first 的收束判断}
```

## Output Variants

### Standard Card

Use 5-7 short paragraphs. Best for 公众号短文、即刻、知识星球、长一点的 X post.

### Short X Version

Use 3-5 short paragraphs, 280 characters or less. Keep one trend judgment, not three. Include the GitHub link unless the user says the link will be attached separately.

```markdown
{项目名} 是一个{开源/自托管/本地优先}的{工具类型}，用来{核心用途}。

它的思路很直接：{大白话价值}。

支持{关键功能 1、2、3}。

目前 GitHub {简化后的 Star 数}。

GitHub：{repo_url}

{一句趋势判断}
```

### Image Plan Only

Use this when the user asks which two images to pair.

```markdown
**图 1：{图片类型}**
作用：建立真实感。
建议画面：{具体截图位置}

**图 2：{图片类型}**
作用：建立能力感。
建议画面：{具体截图位置}

不要用：{重复、弱证据、容易误导的图片}
```

## Ending Rotation

Do not reuse the same ending every time. Pick one:

- SaaS replacement: 很多以前只能靠在线网站完成的小工具，现在都在被开源 + 自托管重新做一遍。
- Product judgment: 这类项目不一定要复杂，只要把一个高频小痛点做稳定，就已经有很强的使用价值。
- AI coding: AI 编程降低了工具类项目的开发门槛，个人开发者和小团队能更快做出可用产品。
- Local-first/privacy: 只要涉及文件、隐私或批量处理，本地优先和自托管就会越来越有吸引力。
- Ecosystem: 真正值得看的不是单个 repo，而是这一类能力正在被重新打包成开源基础设施。

## Tone Calibration

- Prefer "思路很直接" over "功能强大".
- Prefer "浏览器打开就能用" over "提供 Web UI".
- Prefer "所有转换都在自己的服务器里完成" over "隐私友好".
- Prefer "以前只能用在线网站" over "替代传统 SaaS".
- Avoid fake excitement, empty adjectives, and generic praise.
- Do not write "值得关注" unless you say what makes it worth attention.

## If The User Gives Only A Repo URL

1. Fetch current repo evidence before writing when network access is available.
2. Extract: project definition, README value prop, supported features, tech stack, deploy/run method, screenshot candidates, and maturity signals.
3. Draft the card.
4. Include two image recommendations unless the user explicitly asks for text only.
5. If the user asks for images/screenshots, first try to save strong official visuals from the GitHub page or README itself.
6. After capture, judge both evidence quality and X suitability. If the screenshot is accurate but visually weak for X, do not ship it as the main image.
7. If strong official visuals are not available, or if the official visuals are too plain for X, call `article-illustrate` to generate a `cover-only` fallback image in `notion` style, and make the image explain the product function clearly with a small amount of helpful text when needed.
8. Save actual local image files that match the chosen route instead of only describing them.

## If The User Asks To Compare With Their Old Style

Frame the difference as:

- old style: project information / collection-card
- this skill: project plus judgment / personal column
- main upgrade: the reader remembers the author's judgment, not only the repo
