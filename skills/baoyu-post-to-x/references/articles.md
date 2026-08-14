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

# Replace an existing draft body and keep its current cover
npx -y bun ${SKILL_DIR}/scripts/x-article.ts article.md --edit-url https://x.com/compose/articles/edit/123456

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

\`\`\`x-plain
Exact prompt or configuration text stays selectable and keeps its line breaks.
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
4. **Cover deduplication**: If the selected cover resolves to the same file as the first inline image, that first embed is removed from the body
5. **Insertion**: Images are processed from the end of the article; standalone placeholders are selected with real pointer/keyboard input before using the X Article toolbar media upload
6. **Retry gate**: Each inline image is uploaded up to 3 times until the editor image count increases and the matching placeholder disappears stably
7. **Position gate**: Every image must increase the image count between its locked previous/next text-only anchors in both the editor and final preview; image blocks and caption controls are skipped when resolving anchors
8. **Mobile ratio gate**: Inline images taller than 1:1.8 are rejected before Chrome opens; split combined screenshots into logical steps or explicitly use `--allow-tall-images`

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
| fenced block with language `x-plain` | `<p>` with `<br>`; no inline Markdown parsing |
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
   - Lock the nearest previous/next text blocks and current image count between them
   - Select the standalone placeholder using real pointer/keyboard input so Draft.js receives the selection
   - Open Insert -> Media and upload the image file
   - Retry upload up to 3 times if the editor does not show a new image
   - If X inserts the image but leaves the placeholder text behind, delete only that placeholder and require the deletion to remain stable
   - Require a new image block between the locked text anchors before continuing
9. **Verify**: Recheck every locked image position and confirm no image placeholders remain
10. **Preview**: Open preview, recheck all locked positions, and leave Chrome there
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
- **Images not inserting**: Verify placeholders exist in pasted content; the script retries each inline upload up to 3 times before failing closed.
- **Images inserted but placeholders remain**: The script uses real keyboard selection to remove the specific placeholder only after the image appears, waits for Draft.js rerenders, and refuses to upload a duplicate or open preview if cleanup is unstable.
- **Image count is correct but positions are wrong**: The script now locks surrounding text anchors before each upload and verifies them again in the editor and preview. An anchor mismatch stops before handoff.
- **Tall screenshot is blurry or awkward on mobile**: Split vertically combined screenshots at the natural page/step boundaries. The default preflight blocks body images taller than 1:1.8 before Chrome opens; use `--allow-tall-images` only for intentionally tall artwork.
- **Content not pasting**: Check HTML clipboard: `npx -y bun ${SKILL_DIR}/scripts/copy-to-clipboard.ts html --file /tmp/test.html`
- **Clipboard script not found in Chinese/OneDrive paths**: Ensure `x-utils.ts` uses `fileURLToPath(import.meta.url)` for script directory resolution on macOS and Windows.
- **Nested Bun command fails on Windows**: Ensure helper script calls use `npx.cmd`; macOS/Linux should continue to use `npx`.

## How It Works

1. `md-to-html.ts` converts Markdown to HTML:
   - Extracts frontmatter (title, cover)
   - Converts markdown to HTML
   - Renders `x-plain` fences as selectable verbatim text without blockquote or emphasis conversion
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
