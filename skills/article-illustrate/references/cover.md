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

Cover prompts must follow the Baoyu cover prompt system. Load these files before writing the prompt:

- `../baoyu-cover-image/references/base-prompt.md`
- `../baoyu-cover-image/references/styles/<style>.md` when the selected style exists there

Write `cover-prompts.md` as a Baoyu-style cover prompt with:

- Image specifications from the Baoyu base prompt
- Core principles from the Baoyu base prompt, especially hand-drawn quality and non-photographic imagery
- Article topic, angle, and core message
- Selected style reference and any style fallback
- Cover concept, main visual metaphor, composition, focal point, and color scheme
- Title text, subtitle, and language when text is included
- Constraints: no placeholder text, no fake UI unless requested, no cluttered text

Do not use an unconstrained freeform image prompt for covers. If the desired cover is realistic or photographic, explicitly override only when the user asks for that visual direction.

## Handoff

Render through `baoyu-image-gen` after the Baoyu prompt is written. If using a legacy sub-skill for compatibility, call `baoyu-cover-image` with the selected article-level style and the same output directory.
