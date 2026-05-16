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
- Article title/path
- Style
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
