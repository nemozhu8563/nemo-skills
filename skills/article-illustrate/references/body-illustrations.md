# Article Body Illustrations Reference

Use for article body illustrations, section images, paragraph visuals, or visual aids inserted into the article.

## Goal

Body illustrations should help the reader understand, remember, or feel a specific part of the article. They are not decorative fillers.

## Selection

Identify illustration positions by looking for:

- Abstract concepts that need a visual metaphor
- Workflows or steps that need a process image
- Comparisons or tradeoffs that benefit from visual contrast
- Core arguments that deserve reinforcement
- Story moments that need atmosphere or scene-setting

Default to 3-5 illustrations for a normal long article. Use fewer for short articles. More is acceptable when every image has a clear job.

## Prompt Shape

Body illustration prompts must follow the Baoyu article-illustrator prompt system. Load these files before writing prompts:

- `../baoyu-article-illustrator/references/prompt-construction.md`
- `../baoyu-article-illustrator/references/styles/<style>.md` when the selected style exists there

For each image, choose one Baoyu prompt template from `prompt-construction.md`:

- `Comparison` for tradeoffs or contrasts
- `Process Flow` for workflows, delivery loops, or step-by-step logic
- `Framework` for concepts, decision criteria, or mental models
- `Timeline` for chronological arguments
- `Scene` only for atmosphere or lived moments that do not need labels

Then write one prompt file with the chosen template and:

- Illustration theme
- Insert position
- Purpose in the article
- Selected article-level style and any closest Baoyu body-style fallback
- Concrete layout structure before visual details
- Actual labels or captions from the article language
- Semantic color mapping
- Visual relationships and connection arrows when relevant
- Filename slug
- For Chinese articles, all visible text in generated images must be Simplified Chinese. Do not use English labels, English acronyms, pinyin, bilingual labels, or placeholder text unless the article explicitly requires them.

Do not write ordinary freeform scene prompts for body images unless the prompt is explicitly using the Baoyu `Scene` template.

## Handoff

Render sequentially through `baoyu-image-gen` and report progress as `Generated X/N`.

If using a legacy sub-skill for compatibility, call `baoyu-article-illustrator` with the selected article-level style and the same output directory.
