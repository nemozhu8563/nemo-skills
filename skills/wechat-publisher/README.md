# WeChat Publisher Skill

Convert Obsidian Markdown files to WeChat Official Account HTML and upload to draft box.

## Features

- Parse Obsidian Markdown (frontmatter, wikilinks, tags)
- Use frontmatter `title` as the WeChat article title
- Strip trailing `## Links` section from the article body
- Support 8 professional HTML templates
- Upload local article images directly to WeChat
- Prefer `cover.png` or similar dedicated cover files for the thumbnail
- Direct upload to WeChat draft box
- Optional proxy support for WeChat API requests
- System notifications for errors

## Installation

1. Install dependencies with Bun:
```bash
cd wechat-publisher
bun install
```

2. Configure WeChat credentials in your user-level `.agents` directory:
- macOS / Linux: `~/.agents/wechat-publisher.json`
- Windows: `%USERPROFILE%\\.agents\\wechat-publisher.json`

You can bootstrap it from the bundled example file:
```bash
cp wechat-publisher.example.json ~/.agents/wechat-publisher.json
```

Example config:
```json
{
  "wechat": {
    "appId": "your_app_id",
    "appSecret": "your_app_secret"
  },
  "proxy": {
    "enabled": false,
    "url": "http://127.0.0.1:10808"
  },
  "defaults": {
    "template": "template-tech"
  }
}
```

3. Optional override for nonstandard environments:
```bash
export WECHAT_PUBLISHER_CONFIG=/custom/path/wechat-publisher.json
```

## Usage

As a Codex / Claude skill:
```
Use wechat-publisher to publish ./article.md
```

Or directly:
```bash
bun run index.js ./article.md template-tech
```

## Publish Behavior

- Local article images are uploaded to WeChat's article image endpoint, then replaced in the article body
- Existing remote image URLs are kept as-is
- Cover selection prefers `cover.png`, `cover.jpg`, `cover.jpeg`, or `cover.webp`
- If no dedicated cover exists, the first article image is used as fallback
- The generated preview HTML is saved to a temp file before upload

## Testing

Run the Bun-native test suite:
```bash
bun test
```

The tests use temporary config paths and should not read your real `.agents` credentials.

## Troubleshooting

If WeChat returns `invalid ip`:

- Trust the IP reported by WeChat itself
- If your proxy tool routes mainland domains directly, add an explicit rule for `api.weixin.qq.com`
- Whitelist the exact IP that WeChat reports

If WeChat returns `invalid media_id`:

- Check the cover upload separately from article image upload
- Make sure the chosen cover file is a valid local image that WeChat accepts

If images show in preview but not in the final draft:

- Recheck that local article images were uploaded to WeChat, not to an external image host

## Templates

- `template-minimal` - 简约专业
- `template-tech` - 科技蓝 (default)
- `template-elegant` - 优雅黑
- `template-fresh` - 清新绿
- `template-minimal-bw` - 极简黑白
- `template-warm-orange` - 暖橙活力
- `template-dark` - 深色护眼
- `template-business` - 商务正式

## Requirements

- Bun 1.3+
- WeChat Official Account API access
