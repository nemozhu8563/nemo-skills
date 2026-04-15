---
name: baoyu-cover-image
description: Generate elegant cover images for articles. Analyzes content and creates eye-catching hand-drawn style cover images with multiple style options. Use when user asks to "generate cover image", "create article cover", or "make a cover for article".
---

# Cover Image Generator

Generate hand-drawn style cover images for articles with multiple style options.

## Usage

```bash
# From markdown file (auto-select style based on content)
/baoyu-cover-image path/to/article.md

# Specify a style
/baoyu-cover-image path/to/article.md --style blueprint
/baoyu-cover-image path/to/article.md --style warm
/baoyu-cover-image path/to/article.md --style dark-atmospheric

# Without title text
/baoyu-cover-image path/to/article.md --no-title

# Combine options
/baoyu-cover-image path/to/article.md --style minimal --no-title

# From direct text input
/baoyu-cover-image
[paste content or describe the topic]

# Direct input with style
/baoyu-cover-image --style playful
[paste content]
```

## Options

| Option | Description |
|--------|-------------|
| `--style <name>` | Specify cover style (see Style Gallery below) |
| `--aspect <ratio>` | Aspect ratio: 2.35:1 (cinematic/WeChat, default), 16:9 (widescreen), 1:1 (social) |
| `--lang <code>` | Output language for title text (en, zh, ja, etc.) |
| `--no-title` | Generate cover without title text (visual only) |
| `--image-dir <path>` | Override auto-detected image directory |

**Note on WeChat Official Account covers**: When using kie-image-gen backend, 2.35:1 is generated as 21:9 (2.33:1), which is visually identical and accepted by WeChat. For exact 2.35:1 cropping, use `scripts/crop-to-wechat.js` in kie-image-gen skill.

## Style Gallery

| Style | Description |
|-------|-------------|
| `elegant` (Default) | Refined, sophisticated, understated |
| `flat-doodle` | Bold outlines, pastel colors, cute rounded shapes |
| `blueprint` | Technical schematics, engineering precision |
| `bold-editorial` | Magazine cover impact, dramatic typography |
| `chalkboard` | Black chalkboard, colorful chalk drawings |
| `dark-atmospheric` | Cinematic dark mode, glowing accents |
| `editorial-infographic` | Magazine explainer, visual storytelling |
| `fantasy-animation` | Ghibli/Disney inspired, whimsical charm |
| `intuition-machine` | Technical briefing, bilingual labels |
| `minimal` | Ultra-clean, zen-like, focused |
| `nature` | Organic, calm, earthy |
| `notion` | Clean SaaS dashboard, productivity styling |
| `pixel-art` | Retro 8-bit, nostalgic gaming aesthetic |
| `playful` | Fun, creative, whimsical |
| `retro` | Halftone dots, vintage badges, classic |
| `sketch-notes` | Hand-drawn, educational, warm |
| `vector-illustration` | Flat vector, black outlines, retro colors |
| `vintage` | Aged paper, historical, expedition style |
| `warm` | Friendly, approachable, human-centered |
| `watercolor` | Soft hand-painted, natural warmth |

Detailed style definitions: `references/styles/<style>.md`

## Auto Style Selection

When no `--style` is specified, the system analyzes content to select the best style:

| Content Signals | Selected Style |
|----------------|----------------|
| Architecture, system design, engineering | `blueprint` |
| Product launch, keynote, marketing, brand | `bold-editorial` |
| Education, classroom, tutorial, teaching | `chalkboard` |
| Entertainment, creative, premium, cinematic | `dark-atmospheric` |
| Technology explainer, science, research | `editorial-infographic` |
| Storytelling, children, fantasy, magical | `fantasy-animation` |
| Technical docs, academic, bilingual | `intuition-machine` |
| Personal story, emotion, growth, life | `warm` |
| Simple, zen, focus, essential | `minimal` |
| Fun, easy, beginner, casual | `playful` |
| Nature, eco, wellness, health, organic | `nature` |
| Pop culture, 80s/90s nostalgia, badges | `retro` |
| Product, SaaS, dashboard, productivity | `notion` |
| Productivity, workflow, app, tools, cute | `flat-doodle` |
| Gaming, retro tech, developer, 8-bit | `pixel-art` |
| Educational, tutorial, knowledge sharing | `sketch-notes` |
| Creative proposals, brand, toy-like | `vector-illustration` |
| History, exploration, heritage, biography | `vintage` |
| Lifestyle, travel, food, personal | `watercolor` |
| Business, professional, strategy, analysis | `elegant` |

## File Management

### Output Directory

**Standard Mode** (no Obsidian detected):
```
cover-image/{topic-slug}/
├── source-{slug}.{ext}    # Source files (text, images, etc.)
├── prompts/
│   └── cover.md
└── cover.png
```

**Obsidian Mode** (vault detected):
```
{detected-attachment-folder}/
├── cover.png
└── cover-prompts.md    # Prompt saved separately for reference
```

Where `{detected-attachment-folder}` is read from Obsidian configuration
(e.g., `attachments/`, `images/`, or vault root).

**Slug Generation** (Standard mode only):
1. Extract main topic from content (2-4 words, kebab-case)
2. Example: "The Future of AI" → `future-of-ai`

### Conflict Resolution

If `cover-image/{topic-slug}/` already exists:
- Append timestamp: `{topic-slug}-YYYYMMDD-HHMMSS`
- Example: `ai-future` exists → `ai-future-20260118-143052`

### Source Files

Copy all sources with naming `source-{slug}.{ext}`:
- `source-article.md` (main text content)
- `source-logo.png` (image from conversation)

Multiple sources supported: text, images, files from conversation.

## Workflow

### Step 1: Analyze Content

1. **Save source content** (if not already a file):
   - If user provides a file path: use as-is
   - If user pastes content: save to `source.md` in target directory

2. **Extract key information**:
   - **Main topic**: What is the article about?
   - **Core message**: What's the key takeaway?
   - **Tone**: Serious, playful, inspiring, educational?
   - **Keywords**: Identify style-signaling words

3. **Language detection**:
   - Detect **source language** from content
   - Detect **user language** from conversation context
   - Note if source_language ≠ user_language (will ask in Step 3)

### Step 2: Determine Options

1. **Style selection**:
   - If `--style` specified, use that style
   - Otherwise, scan content for style signals and auto-select 3 candidates
   - Default to `elegant` if no clear signals

2. **Aspect ratio**:
   - If `--aspect` specified, use that ratio
   - Otherwise, prepare options: 2.35:1 (cinematic), 16:9 (widescreen), 1:1 (social)

### Step 2.5: Detect Image Directory

**Purpose**: Find the appropriate directory for storing generated cover image.

**Detection Priority**:
1. Check if current directory is an Obsidian vault (has `.obsidian/` folder)
2. If yes, read Obsidian configuration:
   - Check `.obsidian/app.json` for `attachmentFolderPath`
   - Check `.obsidian/workspace.json` for attachment settings
3. If configured, use that directory (relative to article file location)
4. Otherwise, use current logic: `cover-image/{topic-slug}/`

**Obsidian Config Detection**:
- Attachment folder path: `attachmentFolderPath` in `.obsidian/app.json`
- Special values:
  - `"."` (vault root)
  - `"/"` (vault root)
  - `"attachments"` (vault-level attachments folder)
  - `"assets/${noteFileName}"` (per-note assets folder - RECOMMENDED)
  - Any relative path
- Default: `"attachments"` if not configured

**Path Handling**:
- For Obsidian mode with `assets/${noteFileName}`:
  - Extract article filename without extension
  - Create directory: `assets/{article-name}/`
  - Save images: `assets/{article-name}/cover.png`, `assets/{article-name}/illustration-1.png`, etc.
  - Use Obsidian wiki-link format: `![[assets/{article-name}/cover.png]]`
- For Obsidian mode with other paths: Save directly to detected directory (e.g., `attachments/cover.png`)
- For standard mode: Save to `cover-image/{topic-slug}/cover.png`

**IMPORTANT - Image Reference Format**:
- When inserting images into Obsidian markdown, use wiki-link format
- Wiki-link format: `![[path/to/image.png]]`
- No need to URL encode spaces - Obsidian handles them automatically
- Example: `![[assets/我用 Article Clip 搭了个素材库：3个月积累500+篇精选文章/cover.png]]`
- Do NOT use alt text in wiki-links (Obsidian uses filename as alt text)

### Step 3: Confirm Options

**Purpose**: Let user confirm all options in a single step before generation.

**IMPORTANT**: Present ALL options in a single confirmation step using AskUserQuestion. Do NOT interrupt workflow with multiple separate confirmations.

**Determine which questions to ask**:

| Question | When to Ask |
|----------|-------------|
| Style | Always (required) |
| Aspect ratio | Always (offer common options) |
| Language | Only if `source_language ≠ user_language` |

**Present options** (use AskUserQuestion with all applicable questions):

**Question 1 (Style)** - always:
- Style A (recommended): [style name] - [brief description]
- Style B: [style name] - [brief description]
- Style C: [style name] - [brief description]
- Custom: Provide custom style reference

**Question 2 (Aspect)** - always:
- 2.35:1 Cinematic (Recommended) - ultra-wide, dramatic
- 16:9 Widescreen - standard video/presentation
- 1:1 Square - social media optimized

**Question 3 (Language)** - only if source ≠ user language:
- [Source language] (matches content)
- [User language] (your preference)

**Language handling**:
- If source language = user language: Just inform user (e.g., "Title will be in Chinese")
- If different: Ask which language to use for title text

### Step 4: Generate Cover Concept

Create a cover image concept based on selected style:

**Title** (if included, max 8 characters):
- Distill the core message into a punchy headline
- Use hooks: numbers, questions, contrasts, pain points
- Skip if `--no-title` flag is used

**Visual Elements**:
- Style-appropriate imagery and icons
- 1-2 symbolic elements representing the topic
- Metaphors or analogies that fit the style

**CRITICAL - Title Text in Prompts**:
- NEVER use placeholder text like "主标题", "副标题", "Title", "Subtitle" in prompts
- ALWAYS use the actual title text directly
- ❌ BAD: "黑板上方用粉笔手写主标题，黑板下方用粉笔手写副标题"
- ✅ GOOD: "黑板上方用粉笔手写大标题：我用 Article Clip 搭了个素材库。黑板下方用粉笔手写小字：3个月积累500+篇精选文章"
- This ensures the AI generates the actual title, not the literal words "主标题" or "副标题"

### Step 5: Create Prompt File

Save prompt to `prompts/cover.md` with confirmed options.

**All prompts are written in the user's confirmed language preference.**

**Prompt Format**:

```markdown
Cover theme: [topic in 2-3 words]
Style: [selected style name]
Aspect ratio: [confirmed aspect ratio]

[If title included:]
Title text: [8 characters or less, in confirmed language]
Subtitle: [optional, in confirmed language]

Visual composition:
- Main visual: [description matching style]
- Layout: [positioning based on title inclusion and aspect ratio]
- Decorative elements: [style-appropriate elements]

Color scheme:
- Primary: [style primary color]
- Background: [style background color]
- Accent: [style accent color]

Style notes: [specific style characteristics to emphasize]

[If no title:]
Note: No title text, pure visual illustration only.
```

### Step 6: Generate Image

**Image Generation Skill Selection**:
1. Check available image generation skills
2. If multiple skills available, ask user to choose

**Output Path Calculation**:
- **Obsidian mode**: `{detected-directory}/cover.png` (e.g., `attachments/cover.png`)
- **Standard mode**: `cover-image/{topic-slug}/cover.png`

**Aspect Ratio Mapping** (for kie-image-gen backend):
- If aspect ratio is `2.35:1`, map to `21:9` (2.33:1, visually identical)
- Other ratios pass through unchanged: `16:9`, `1:1`, etc.

**Generation**:
Call selected image generation skill with prompt file, output path, and mapped aspect ratio.

### Step 7: Output Summary

```
Cover Image Generated!

Topic: [topic]
Style: [style name]
Aspect: [aspect ratio]
Title: [cover title] (or "No title - visual only")
Language: [confirmed language]
Location: [output path]

Preview the image to verify it matches your expectations.
```

## Notes

- Cover should be instantly understandable at small preview sizes
- Title (if included) must be readable and impactful
- Visual metaphors work better than literal representations
- Maintain style consistency throughout the cover
- Image generation typically takes 10-30 seconds
- Title text uses user's confirmed language preference
- Aspect ratio: 2.35:1 for cinematic/dramatic, 16:9 for widescreen, 1:1 for social media

## Extension Support

Custom styles and configurations via EXTEND.md.

**Check paths** (priority order):
1. `.baoyu-skills/baoyu-cover-image/EXTEND.md` (project)
2. `~/.baoyu-skills/baoyu-cover-image/EXTEND.md` (user)

If found, load before Step 1. Extension content overrides defaults.
