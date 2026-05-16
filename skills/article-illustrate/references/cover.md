# Article Cover Reference

Use for article cover, title image, WeChat cover, or first-viewport article visual requests.

## Goal

Create one strong visual anchor for the article. The cover should communicate the article's topic and emotional angle before the reader starts reading.

## Defaults

- Aspect ratio: `21:9` for WeChat/article covers.
- Output file: `cover.png`.
- Prompt file: `cover-prompts.md`.
- Include title text unless the user asks for `--no-title` or a pure visual cover.
- Keep title text short. Prefer the real article title or a compressed version under 8 Chinese characters when possible.

## Prompt Shape

Write the prompt with:

- Article topic and angle
- Selected article-level style
- Main visual metaphor
- Composition and focal point
- Color scheme
- Title text, subtitle, and language when text is included
- Constraints: no placeholder text, no fake UI unless requested, no cluttered text

## Handoff

Render through `baoyu-image-gen`. If using a legacy sub-skill for compatibility, call `baoyu-cover-image` with the selected article-level style and the same output directory.
