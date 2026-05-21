# Article Visual Output Contract

Keep prompts and images together so article visuals remain reproducible.

## Directory

For Obsidian articles, prefer:

```text
assets/{article-file-name}/
├── cover.png
├── cover-prompts.md
├── prompts/
│   ├── illustration-{slug}.md
│   └── ...
├── illustration-{slug}.png
└── ...
```

If the vault has a configured attachment directory, use that directory while preserving the article-specific subfolder when practical.

## Metadata To Preserve

Each prompt file should make these facts visible:

- Route: cover or body illustration
- Baoyu prompt source: cover base prompt or body template name
- Article title/path
- Style
- Style fallback, if the selected article-level style maps to a different Baoyu body style
- Aspect ratio
- Output image path
- Renderer/backend
- Reference images, if any

## Insertions

For body illustrations in Obsidian, insert wiki-links:

```markdown
![[assets/{article-file-name}/illustration-{slug}.png]]
```

Leave one blank line before and after the image link. Do not insert a cover image into the body unless the user asks.

## Completion Checks

Before reporting completion:

- Confirm every generated visual is a raster file such as PNG, JPEG, or WebP; SVG, HTML, canvas, Mermaid, or screenshots of markup are not acceptable substitutes.
- Confirm cover prompt uses `baoyu-cover-image` base prompt structure when a cover was generated.
- Confirm each body prompt names a Baoyu body template such as `Comparison`, `Process Flow`, `Framework`, `Timeline`, or `Scene`.
- Confirm every generated body illustration has been copied into the article asset directory.
- Confirm every inserted wiki-link points to a non-empty local image file.
- For Chinese articles, check that visible image text is Chinese; regenerate any image with English labels unless the article explicitly requested English.
- Do not repair bad generated text by programmatically overlaying bitmap or vector text. Regenerate, reduce/remove text, or ask the user.
