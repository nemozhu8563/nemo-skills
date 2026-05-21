---
name: wechat-publisher
description: "Use when publishing Obsidian Markdown to WeChat Official Account drafts or when the user says 发到公众号、推到公众号草稿箱、发布到微信公众平台、把这篇 md 发公众号、用代理发送到公众号. Handles frontmatter titles, Obsidian syntax, WeChat-hosted article images, cover image selection, credentials, proxy, whitelist, and errors such as invalid ip, invalid media_id, or invalid appsecret."
---

# WeChat Publisher

Convert Obsidian Markdown files to WeChat Official Account HTML and upload to WeChat draft box.

This is the only WeChat publishing skill in `nemo-skills`. Do not migrate or invoke upstream Baoyu browser/CDP WeChat publishing as the primary path.

## Configuration

Before processing any files, ensure WeChat credentials are configured in your user-level `.agents` directory:

- macOS / Linux: `~/.agents/wechat-publisher.json`
- Windows: `%USERPROFILE%\\.agents\\wechat-publisher.json`

You can bootstrap from `wechat-publisher.example.json` in this skill directory.

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

If credentials are missing, notify the user and provide the resolved config path.

Optional override for testing or custom environments:
- `WECHAT_PUBLISHER_CONFIG=/custom/path/wechat-publisher.json`

## Processing Workflow

Execute the following steps in order:

1. **Check configuration** - Verify WeChat AppID/AppSecret exist
2. **Parse Markdown** - Extract content, frontmatter, and images
3. **Process Obsidian syntax**:
   - Convert wikilinks `[[Page]]` to plain text
   - Remove standalone hashtag tags (e.g., `#tag`)
   - Preserve frontmatter data
   - Remove trailing `## Links` section from article body
4. **Upload local article images** directly to WeChat article image API
   - Replace local image links with WeChat-hosted URLs
   - Keep existing remote image URLs as-is
5. **Replace image links** in content with uploaded URLs
6. **Generate HTML** using the specified template
7. **Save preview HTML** to temp directory for debugging
8. **Choose thumbnail source**
   - Prefer `cover.png`, `cover.jpg`, `cover.jpeg`, or `cover.webp`
   - Search next to the article first, then next to embedded image assets
   - Fall back to the first article image only if no dedicated cover exists
9. **Upload cover** through WeChat thumbnail upload
10. **Upload to WeChat** draft box
   - Use frontmatter `title` as article title when present

## Runtime

- Default publish command: `bun run publish -- <markdown-file> [template]`
- Do not run `node index.js ...` directly inside this skill directory. Use the package script entrypoint so runtime choices stay centralized.
- Do not use `bun run index.js` for real WeChat uploads. On this machine, Bun's fetch-backed HTTP stack can close multipart image uploads unexpectedly.
- Default install path: run `bun install` from this skill directory when `node_modules/` is missing
- Remove generated `node_modules/` after ad-hoc local publishing or validation; managed skill copies must not carry generated dependencies.
- Default test command: `bun test`

## Templates

Available templates (default: `template-tech`):

| Template ID | Name |
|-------------|------|
| `template-minimal` | 简约专业 |
| `template-tech` | 科技蓝 |
| `template-elegant` | 优雅黑 |
| `template-fresh` | 清新绿 |
| `template-minimal-bw` | 极简黑白 |
| `template-warm-orange` | 暖橙活力 |
| `template-dark` | 深色护眼 |
| `template-business` | 商务正式 |

## Parameters

- `filePath`: Path to the Obsidian Markdown file (required)
- `template`: Template name (optional, defaults to `template-tech`)

## Error Handling

On failure:
- Log error message to console
- Send system notification via node-notifier
- Report specific failure reason (config missing, image upload failed, WeChat API error)

## Troubleshooting Order

When publishing fails, do not jump straight to repeated retries. Check in this order:

1. **`invalid ip`**
   - Trust the IP reported by WeChat, not a generic "what is my IP" site
   - If WeChat still sees the local mainland egress, your proxy rule is not actually applied

2. **Proxy routing**
   - If your proxy tool sends mainland destinations direct, add an explicit rule for `api.weixin.qq.com`
   - Only continue after WeChat starts reporting the proxy egress IP

3. **WeChat whitelist**
   - Add the exact IP WeChat reports
   - If you switch proxy nodes, update the whitelist again

4. **`invalid media_id`**
   - Treat cover upload as a separate step from article image upload
   - Verify the dedicated cover file is accepted by WeChat

5. **Article images missing in the final draft**
   - Confirm local article images were uploaded to WeChat's article image endpoint
   - A preview HTML file containing `<img>` does not guarantee those images will display inside WeChat drafts

## Preview File

After conversion, save preview HTML to system temp directory and display the file path. This allows users to verify the generated HTML and styles before publishing.
