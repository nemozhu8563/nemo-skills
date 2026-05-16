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

For each image, write one prompt file with:

- Illustration theme
- Insert position
- Purpose in the article
- Selected article-level style
- Visual composition
- Main subject and supporting elements
- Any labels or captions, in the article language unless specified otherwise
- Filename slug

## Handoff

Render sequentially through `baoyu-image-gen` and report progress as `Generated X/N`.

If using a legacy sub-skill for compatibility, call `baoyu-article-illustrator` with the selected article-level style and the same output directory.
