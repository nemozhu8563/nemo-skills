# X Articles - Detailed Guide

Publish Markdown articles to X Articles editor with rich text formatting and images.

## Prerequisites

- X Premium subscription (required for Articles)
- Google Chrome installed
- `bun` installed

## Usage

```bash
# Publish markdown article (preview mode)
npx -y bun ${SKILL_DIR}/scripts/x-article.ts article.md

# With custom cover image
npx -y bun ${SKILL_DIR}/scripts/x-article.ts article.md --cover ./cover.jpg

# Compose and open preview. Final publish is manual.
npx -y bun ${SKILL_DIR}/scripts/x-article.ts article.md

# Prepare a deterministic package for Chrome-assisted/manual verification
npx -y bun ${SKILL_DIR}/scripts/x-article-package.ts article.md
```

## Markdown Format

```markdown
---
title: My Article Title
cover_image: /path/to/cover.jpg
---

# Title (becomes article title)

Regular paragraph text with **bold** and *italic*.

## Section Header

More content here.

![Image alt text](./image.png)

- List item 1
- List item 2

1. Numbered item
2. Another item

> Blockquote text

[Link text](https://example.com)

\`\`\`
Code blocks become blockquotes (X doesn't support code)
\`\`\`
```

## Frontmatter Fields

| Field | Description |
|-------|-------------|
| `title` | Article title (or uses first H1) |
| `cover_image` | Cover image path or URL |
| `cover` | Alias for cover_image |
| `image` | Alias for cover_image |

## Image Handling

1. **Cover Image**: `--cover`, then `assets/<article filename>/cover.png`, then frontmatter, then first image
2. **Remote Images**: Automatically downloaded to temp directory
3. **Placeholders**: Images in content use `[[IMAGE_PLACEHOLDER_N]]` format
4. **Insertion**: Placeholders are found, selected, and replaced with actual images

For Obsidian articles, the preferred cover convention is:

```text
<vault-root>/assets/<markdown-filename-without-.md>/cover.png
```

When that file exists, it is used as the cover and all inline screenshots remain inline.

## Markdown to HTML Script

Convert markdown and inspect structure:

```bash
# Get JSON with all metadata
npx -y bun ${SKILL_DIR}/scripts/md-to-html.ts article.md

# Output HTML only
npx -y bun ${SKILL_DIR}/scripts/md-to-html.ts article.md --html-only

# Save HTML to file
npx -y bun ${SKILL_DIR}/scripts/md-to-html.ts article.md --save-html /tmp/article.html
```

JSON output:
```json
{
  "title": "Article Title",
  "coverImage": "/path/to/cover.jpg",
  "contentImages": [
    {
      "placeholder": "[[IMAGE_PLACEHOLDER_1]]",
      "localPath": "/tmp/x-article-images/img.png",
      "blockIndex": 5
    }
  ],
  "html": "<p>Content...</p>",
  "totalBlocks": 20
}
```

## X Article Package Script

Use `x-article-package.ts` when the article has many inline screenshots or when the X editor rejects automated image paste events. It reuses the same Markdown parser as `x-article.ts`, then writes a deterministic package:

- `manifest.json`: title, cover path, ordered image list, placeholders, and verification safety notes
- `article.html`: rich HTML body with image placeholders
- `article.txt`: plain-text body with image placeholders
- `operator-checklist.md`: Chrome-assisted publishing checklist

```bash
npx -y bun ${SKILL_DIR}/scripts/x-article-package.ts article.md
npx -y bun ${SKILL_DIR}/scripts/x-article-package.ts article.md --output-dir /tmp/x-package
npx -y bun ${SKILL_DIR}/scripts/x-article-package.ts article.md --title "Custom title" --cover ./cover.png
```

This replaces the old separate `nemo-post-to-x` package-only flow. Keep `baoyu-post-to-x` as the single entrypoint for X publishing.

## Supported Formatting

| Markdown | HTML Output |
|----------|-------------|
| `# H1` | Title only (not in body) |
| `## H2` - `###### H6` | `<h2>` |
| `**bold**` | `<strong>` |
| `*italic*` | `<em>` |
| `[text](url)` | `<a href>` |
| `> quote` | `<blockquote>` |
| `` `code` `` | `<code>` |
| ```` ``` ```` | `<blockquote>` (X limitation) |
| `- item` | `<ul><li>` |
| `1. item` | `<ol><li>` |
| `![](img)` | Image placeholder |

## Workflow

1. **Parse Markdown**: Extract title, cover, content images, generate HTML
2. **Launch Chrome**: Real browser with CDP, persistent login
3. **Navigate**: Open `x.com/compose/articles`
4. **Create Article**: Click create button if on list page
5. **Upload Cover**: Use file input for cover image
6. **Fill Title**: Type title into title field
7. **Paste Content**: Copy HTML to clipboard, paste into editor
8. **Insert Images**: For each placeholder (reverse order):
   - Find placeholder text in editor
   - Select the placeholder
   - Copy image to clipboard
   - Paste to replace selection
   - If X inserts the image but leaves the placeholder text behind, delete only that placeholder immediately
9. **Verify**: Confirm no image placeholders remain and the expected images are in the editor
10. **Preview**: Open preview and leave Chrome there
11. **Publish**: Manual only; the account owner clicks the final X Publish button

## Example Session

```
User: /post-to-x article ./blog/my-post.md --cover ./thumbnail.png

Claude:
1. Parses markdown: title="My Post", 3 content images
2. Launches Chrome with CDP
3. Navigates to x.com/compose/articles
4. Clicks create button
5. Uploads thumbnail.png as cover
6. Fills title "My Post"
7. Pastes HTML content
8. Inserts 3 images at placeholder positions
9. Opens preview and reports: "Article composed and preview opened. Publish manually after review."
```

## Troubleshooting

- **No create button**: Ensure X Premium subscription is active
- **Cover upload fails**: Check file path and format (PNG, JPEG)
- **Images not inserting**: Verify placeholders exist in pasted content
- **Images inserted but placeholders remain**: The script now treats this as an insertion cleanup failure, removes the specific placeholder after the image appears, and refuses to open preview if any `IMAGE_PLACEHOLDER` text remains.
- **Content not pasting**: Check HTML clipboard: `npx -y bun ${SKILL_DIR}/scripts/copy-to-clipboard.ts html --file /tmp/test.html`
- **Clipboard script not found in Chinese/OneDrive paths**: Ensure `x-utils.ts` uses `fileURLToPath(import.meta.url)` for script directory resolution on macOS and Windows.
- **Nested Bun command fails on Windows**: Ensure helper script calls use `npx.cmd`; macOS/Linux should continue to use `npx`.

## How It Works

1. `md-to-html.ts` converts Markdown to HTML:
   - Extracts frontmatter (title, cover)
   - Converts markdown to HTML
   - Replaces images with unique placeholders
   - Downloads remote images locally
   - Uses `assets/<article>/cover.png` as the default Obsidian cover when present
   - Returns structured JSON

2. `x-article.ts` publishes via CDP:
   - Launches real Chrome (bypasses detection)
   - Uses persistent profile (saved login)
   - Navigates and fills editor via DOM manipulation
   - Pastes HTML from system clipboard
   - Finds/selects/replaces each image placeholder
   - Opens preview and stops there; final publish is manual
