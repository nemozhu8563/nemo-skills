---
name: article-illustrate
description: Complete article illustration solution. Generates cover image and article illustrations in one workflow with unified style. Analyzes content, recommends 3 suitable styles for user selection, then generates cover and all illustrations. Use when user asks to "illustrate article", "add images to article", "generate article visuals", or "配图".
---

# Article Illustrate

Complete article illustration solution: cover image + article illustrations in one unified workflow.

## Usage

```bash
# Auto-recommend styles based on content
/article-illustrate path/to/article.md

# Specify a style directly (skip recommendation)
/article-illustrate path/to/article.md --style warm
```

## Options

| Option | Description |
|--------|-------------|
| `--style <name>` | Skip recommendation, use specified style |
| `--image-dir <path>` | Override auto-detected image directory |

## Style Gallery

20 styles available (same as baoyu-cover-image and baoyu-article-illustrator):

| Style | Description | Best For |
|-------|-------------|----------|
| `elegant` | Refined, sophisticated, professional | Business, thought leadership |
| `flat-doodle` | Bold outlines, pastel colors, cute | Productivity, SaaS, workflows |
| `blueprint` | Technical schematics, engineering | Architecture, system design |
| `bold-editorial` | Magazine cover impact | Product launch, marketing |
| `chalkboard` | Black chalkboard, chalk drawings | Education, tutorials |
| `dark-atmospheric` | Cinematic dark mode, glowing | Entertainment, premium |
| `editorial-infographic` | Magazine explainer | Tech explainers, journalism |
| `fantasy-animation` | Ghibli/Disney whimsical | Storytelling, children's |
| `intuition-machine` | Technical briefing, bilingual | Academic, technical docs |
| `minimal` | Ultra-clean, zen-like | Philosophy, core concepts |
| `nature` | Organic, calm, earthy | Sustainability, wellness |
| `notion` | Clean SaaS dashboard | Knowledge sharing, productivity |
| `pixel-art` | Retro 8-bit gaming | Gaming, developer content |
| `playful` | Fun, creative, whimsical | Tutorials, beginner guides |
| `retro` | 80s/90s vibrant nostalgic | Pop culture, entertainment |
| `sketch-notes` | Hand-drawn, educational | Knowledge sharing, tutorials |
| `vector-illustration` | Flat vector, retro colors | Educational, creative |
| `vintage` | Aged paper, historical | Biography, heritage |
| `warm` | Friendly, approachable | Personal growth, lifestyle |
| `watercolor` | Soft hand-painted | Lifestyle, travel, creative |

## Workflow

### Step 1: Analyze Content

1. Read article content from provided file path
2. Extract key information:
   - Main topic and themes
   - Tone (serious, playful, technical, personal, etc.)
   - Target audience
   - Content type (tutorial, concept, case study, etc.)

### Step 2: Recommend Styles

Based on content analysis, recommend 3 most suitable styles using AskUserQuestion:

**Present style options**:
- Style A (recommended): [style name] - [why it fits the content]
- Style B: [style name] - [why it fits the content]
- Style C: [style name] - [why it fits the content]

Wait for user selection before proceeding.

### Step 3: Generate Cover Image

Call baoyu-cover-image skill with selected style:
```bash
/baoyu-cover-image path/to/article.md --style [selected-style]
```

**Aspect Ratio**: Cover image uses **21:9** (2.33:1) by default
- Suitable for WeChat Official Account cover images
- Cinematic widescreen effect
- When using kie-image-gen backend, 2.35:1 is automatically mapped to 21:9

**Note**: baoyu-cover-image will automatically:
- Detect Obsidian vault configuration
- Use `assets/${noteFileName}/` if configured
- Generate cover with actual title text (not placeholders)
- Insert image reference with proper URL encoding

### Step 4: Generate Article Illustrations

Call baoyu-article-illustrator skill with same style:
```bash
/baoyu-article-illustrator path/to/article.md --style [selected-style]
```

**Aspect Ratio**: Article illustrations use **16:9** (standard widescreen)
- Better reading experience in article body
- Suitable for mobile viewing
- Not too wide, fits article content width
- Standard video/presentation ratio

This will:
- Analyze article structure
- Identify positions needing illustrations
- Generate all illustrations in the same assets folder
- Insert them into the article using Obsidian wiki-link format: `![[assets/{article-name}/illustration-xxx.png]]`

### Step 5: Output Summary

```
Article Illustration Complete!

Article: [article path]
Style: [selected style]

Generated:
- Cover image: cover.png
- Article illustrations: X images

All images saved to: [image directory]
All illustrations inserted into article.
```

## Notes

- Cover image and all illustrations use the same unified style
- One-step workflow: user only needs to select style once
- All images automatically saved to Obsidian attachments directory
- Illustrations automatically inserted into article with proper formatting
- Typical generation time: 30-60 seconds for cover + 3-5 illustrations

**Aspect Ratio Standards**:
- **Cover image**: 21:9 (2.33:1) - Cinematic widescreen, suitable for WeChat Official Account covers
- **Article illustrations**: 16:9 - Standard widescreen, better reading experience in article body

