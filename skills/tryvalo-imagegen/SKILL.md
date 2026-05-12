---
name: tryvalo-imagegen
description: Provider/channel for TryValo/new-api /v1/images/generations and gpt-image-2 style requests. Prefer `baoyu-image-gen` for ordinary user-facing image requests; use this skill directly only when the TryValo/new-api backend is explicitly required.
---

# TryValo Image Generation

Use TryValo/new-api's OpenAI-compatible image endpoint:

```text
POST /v1/images/generations
```

Default model: `gpt-image-2`.

## When To Use

Use this skill when the user wants to generate images through TryValo/new-api, especially with phrases like:

- "用 gpt-image-2 生成图片"
- "TryValo 画一张图"
- "生成横版/竖版/方图"
- "调用 /v1/images/generations"
- "给我一张海报/封面/插图"

## Setup

The script reads config from environment variables or this skill's own `nemo-skills` env file.

Required token, one of:

```bash
TRYVALO_API_KEY=sk-...
TRYVALO_TOKEN=sk-...
NEW_API_TOKEN=sk-...
```

Optional:

```bash
TRYVALO_BASE_URL=https://api.tryvalo.com
TRYVALO_IMAGE_MODEL=gpt-image-2
```

Load order:

1. Process environment
2. `~/nemo-skills/tryvalo-imagegen.env`

For skills under `nemo-skills`, do not put every tool's secrets into one shared `.env`. Prefer a per-skill config file named after the skill:

```bash
~/nemo-skills/tryvalo-imagegen.env
```

This keeps each skill portable and avoids mixing unrelated API keys.

Example:

```bash
TRYVALO_API_KEY=sk-...
TRYVALO_BASE_URL=https://api.tryvalo.com
TRYVALO_IMAGE_MODEL=gpt-image-2
```

## Script

Determine this skill directory as `SKILL_DIR`, then run:

```bash
bun ${SKILL_DIR}/scripts/generate_image.js --prompt "A minimal glass perfume bottle, studio lighting" --output image.png
```

Common options:

| Option | Description | Default |
| --- | --- | --- |
| `--prompt <text>` | Image prompt. Positional prompt also works. | required |
| `--output <path>` | Save image to this path. If omitted, print URL/base64 summary. | none |
| `--model <id>` | Image model. | `TRYVALO_IMAGE_MODEL` or `gpt-image-2` |
| `--size <size>` | `1024x1024`, `1536x1024`, `1024x1536`, `auto`, `square`, `landscape`, `portrait`. | `1024x1024` |
| `--quality <value>` | `high`, `auto`, `medium`, `low`, `standard`, `hd`. | `high` |
| `--n <count>` | Number of images. | `1` |
| `--response-format <value>` | `url` or `b64_json`. Defaults to `b64_json` when saving, otherwise `url`. | auto |
| `--watermark <true/false>` | Add watermark flag for compatible channels. | omitted |
| `--json` | Print machine-readable result summary. | false |
| `--dry-run` | Print request payload without calling the API. | false |

## gpt-image-2 Size Rules

Do not promise native 2K or 4K output for `gpt-image-2`.

Use these practical sizes:

| User asks for | Send |
| --- | --- |
| square / 方图 | `1024x1024` |
| landscape / 横版 / 16:9-ish | `1536x1024` |
| portrait / 竖版 / 9:16-ish | `1024x1536` |
| auto | `auto` |

If the user asks for 2K or 4K, explain that the image endpoint should generate the largest supported size with `quality=high`, then upscale downstream. Do not send `2K`, `4K`, `2048x2048`, or `4096x4096` as `size` unless the user explicitly says their mapped upstream supports it.

## Natural-Language Defaults

When the user does not specify details:

- Use `model=gpt-image-2`.
- Use `quality=high`.
- Use `n=1`.
- Use `size=1024x1024`.
- If the user says "横版", use `1536x1024`.
- If the user says "竖版", use `1024x1536`.
- If saving to a local file, prefer `response_format=b64_json`; if the API returns a URL anyway, download it.

## Examples

Generate and save a square image:

```bash
bun ${SKILL_DIR}/scripts/generate_image.js \
  --prompt "A clean app icon, glassmorphism, blue and white" \
  --output icon.png
```

Generate a landscape poster:

```bash
bun ${SKILL_DIR}/scripts/generate_image.js \
  --prompt "A premium technology product poster, metallic texture, studio lighting" \
  --size landscape \
  --output poster.png
```

Inspect the exact API payload:

```bash
bun ${SKILL_DIR}/scripts/generate_image.js \
  --prompt "A ceramic tea cup by a window" \
  --size 1536x1024 \
  --dry-run --json
```
