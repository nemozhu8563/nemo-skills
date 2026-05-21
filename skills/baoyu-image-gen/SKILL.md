---
name: baoyu-image-gen
description: Main image-generation router for ordinary image requests. Use Codex native image generation as the required first attempt when available; use local provider scripts such as OpenAI, Google, kie-image-gen, or tryvalo-imagegen only when explicitly requested, needed for file/API automation, or as non-SVG raster fallback.
---

# Image Generation Router

Main image-generation router for ordinary image requests.

Default split:
- **Prompt layer**: Nemo skills decide the visual concept and write the prompt.
- **Render layer**: Codex native image generation is the default and required first attempt when available.
- **Provider fallback**: Local scripts and provider skills are fallback or explicitly selected non-SVG raster backends. This means Nemo's current providers only; do not import or document upstream provider families as user-facing options unless they are implemented here.

## Routing Policy

1. If the current Codex session exposes Codex native image generation, use it first.
2. If the user explicitly names a backend (`tryvalo-imagegen`, `kie-image-gen`, Google, OpenAI API/new-api), use that backend.
3. If Codex native image generation writes to a generated-images directory instead of the requested output path, copy the generated raster file to the requested output path and leave the original file in place.
4. If the workflow requires deterministic filesystem output and the native renderer cannot provide or expose a local raster artifact in this surface, keep the prompt file and use the local provider script as fallback.
5. Provider fallbacks must generate raster images such as PNG, JPEG, or WebP. Never generate SVG as a fallback image.
6. If neither Codex native image generation nor a non-SVG raster provider route is available, report that no usable image-generation route was found instead of fabricating an SVG or placeholder.
7. If reference-image editing, batch generation, custom API base URLs, or exact CLI automation is required, use the local provider script/backend that supports it.
8. Do not ask the user to choose among providers unless provider choice materially affects the result and cannot be inferred.

Batch generation is represented by repeated local provider runs or the existing `--n` option where the chosen local provider supports it. Reference-image generation is an image-to-image/reference-editing route and should use the local backend that accepts `--ref`.

When using Codex native image generation, pass the final prompt directly to the official image-generation capability. Preserve the generated prompt file whenever the calling workflow created one, so the prompt remains part of the article/project asset trail.

## Local Provider CLI

Use this section only for fallback, explicit provider requests, or workflows that need script-controlled output paths.

## Script Directory

**Important**: All scripts are located in the `scripts/` subdirectory of this skill.

**Agent Execution Instructions**:
1. Determine this SKILL.md file's directory path as `SKILL_DIR`
2. Script path = `${SKILL_DIR}/scripts/<script-name>.ts`
3. Replace all `${SKILL_DIR}` in this document with the actual path

**Script Reference**:
| Script | Purpose |
|--------|---------|
| `scripts/main.ts` | CLI entry point for image generation |

## Quick Start

```bash
# Basic generation (auto-detect provider)
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A cat" --image cat.png

# With aspect ratio
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A landscape" --image landscape.png --ar 16:9

# High quality (2k)
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A cat" --image cat.png --quality 2k

# Specific provider
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A cat" --image cat.png --provider openai

# From prompt files
npx -y bun ${SKILL_DIR}/scripts/main.ts --promptfiles system.md content.md --image out.png

# With reference images (Google multimodal only)
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "Make blue" --image out.png --ref source.png
```

## Commands

### Basic Image Generation

```bash
# Generate with prompt
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A sunset over mountains" --image sunset.png

# Shorthand
npx -y bun ${SKILL_DIR}/scripts/main.ts -p "A cute robot" --image robot.png
```

### Aspect Ratios

```bash
# Common ratios: 1:1, 16:9, 9:16, 4:3, 3:4, 2.35:1
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A portrait" --image portrait.png --ar 3:4

# Or specify exact size
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "Banner" --image banner.png --size 1792x1024
```

### Reference Images (Google Multimodal)

```bash
# Image editing with reference
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "Make it blue" --image blue.png --ref original.png

# Multiple references
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "Combine these styles" --image out.png --ref a.png b.png
```

### Quality Presets

```bash
# Normal quality (default)
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A cat" --image cat.png --quality normal

# High quality (2k resolution)
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A cat" --image cat.png --quality 2k
```

### Output Formats

```bash
# Plain output (prints saved path)
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A cat" --image cat.png

# JSON output
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A cat" --image cat.png --json
```

## Options

| Option | Description |
|--------|-------------|
| `--prompt <text>`, `-p` | Prompt text |
| `--promptfiles <files...>` | Read prompt from files (concatenated) |
| `--image <path>` | Output image path (required) |
| `--provider google\|openai` | Force provider (default: google) |
| `--model <id>`, `-m` | Model ID |
| `--ar <ratio>` | Aspect ratio (e.g., `16:9`, `1:1`, `4:3`) |
| `--size <WxH>` | Size (e.g., `1024x1024`) |
| `--quality normal\|2k` | Quality preset (default: normal) |
| `--ref <files...>` | Reference images (Google multimodal only) |
| `--n <count>` | Number of images |
| `--json` | JSON output |
| `--help`, `-h` | Show help |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | - |
| `GOOGLE_API_KEY` | Google API key | - |
| `OPENAI_IMAGE_MODEL` | OpenAI model | `gpt-image-1.5` |
| `GOOGLE_IMAGE_MODEL` | Google model | `gemini-3-pro-image-preview` |
| `OPENAI_BASE_URL` | Custom OpenAI endpoint | - |
| `GOOGLE_BASE_URL` | Custom Google endpoint | - |

**Load Priority**: CLI args > `process.env` > `<cwd>/.baoyu-skills/.env` > `~/.baoyu-skills/.env`

## Provider & Model Strategy

### Auto-Selection

1. If `--provider` specified → use it
2. If only one API key available → use that provider
3. If both available → default to Google (multimodal LLMs more versatile)

### API Selection by Model Type

| Model Category | API Function | Example Models |
|----------------|--------------|----------------|
| Google Multimodal | `generateText` | `gemini-2.0-flash-exp-image-generation` |
| Google Imagen | `experimental_generateImage` | `imagen-3.0-generate-002` |
| OpenAI | `experimental_generateImage` | `gpt-image-1`, `dall-e-3` |

### Available Models

**Google**:
- `gemini-3-pro-image-preview` - Default, multimodal generation
- `gemini-2.0-flash-exp-image-generation` - Gemini 2.0 Flash
- `imagen-3.0-generate-002` - Imagen 3

**OpenAI**:
- `gpt-image-1.5` - Default, GPT Image 1.5
- `gpt-image-1` - GPT Image 1
- `dall-e-3` - DALL-E 3

## Quality Presets

| Preset | OpenAI | Google | Use Case |
|--------|--------|--------|----------|
| `normal` | 1024x1024 | Default | Covers, illustrations |
| `2k` | 2048x2048 | "2048px" in prompt | Infographics, slides |

## Aspect Ratio Handling

- **Multimodal LLMs**: Embedded in prompt (e.g., `"... aspect ratio 16:9"`)
- **Image-only models**: Uses `aspectRatio` or `size` parameter
- **Common ratios**: 1:1, 16:9, 9:16, 4:3, 3:4, 2.35:1

## Examples

### Generate Cover Image

```bash
npx -y bun ${SKILL_DIR}/scripts/main.ts \
  --prompt "A minimalist tech illustration with blue gradients" \
  --image cover.png --ar 2.35:1 --quality 2k
```

### Generate Social Media Post

```bash
npx -y bun ${SKILL_DIR}/scripts/main.ts \
  --prompt "Instagram post about coffee" \
  --image post.png --ar 1:1
```

### Edit Image with Reference

```bash
npx -y bun ${SKILL_DIR}/scripts/main.ts \
  --prompt "Change the background to sunset" \
  --image edited.png --ref original.png --provider google
```

### Batch Generation from Prompt File

```bash
# Create prompt file with detailed instructions, then either use --n when
# the selected provider supports it or run the same prompt for named outputs.
npx -y bun ${SKILL_DIR}/scripts/main.ts \
  --promptfiles style-guide.md scene-description.md \
  --image scene.png --n 3
```

## Error Handling

- **Missing API key**: Clear error with setup instructions
- **Generation failure**: Auto-retry once, then error
- **Invalid aspect ratio**: Warning, proceed with default
- **Reference images with image-only model**: Warning, ignore refs

## Extension Support

Custom configurations via EXTEND.md.

**Check paths** (priority order):
1. `.baoyu-skills/baoyu-image-gen/EXTEND.md` (project)
2. `~/.baoyu-skills/baoyu-image-gen/EXTEND.md` (user)

If found, load before workflow. Extension content overrides defaults.
