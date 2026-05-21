---
name: baoyu-post-to-x
description: Post content and articles to X (Twitter). Supports regular posts with images/videos and X Articles (long-form Markdown). Uses real Chrome with CDP to bypass anti-automation.
---

# Post to X (Twitter)

Post content, images, videos, and long-form articles to X using real Chrome browser (bypasses anti-bot detection).

## Script Directory

**Important**: All scripts are located in the `scripts/` subdirectory of this skill.

**Agent Execution Instructions**:
1. Determine this SKILL.md file's directory path as `SKILL_DIR`
2. Script path = `${SKILL_DIR}/scripts/<script-name>.ts`
3. Replace all `${SKILL_DIR}` in this document with the actual path

**Script Reference**:
| Script | Purpose |
|--------|---------|
| `scripts/x-browser.ts` | Regular posts (text + images) |
| `scripts/x-video.ts` | Video posts (text + video) |
| `scripts/x-quote.ts` | Quote tweet with comment |
| `scripts/x-article.ts` | Long-form article publishing (Markdown) |
| `scripts/md-to-html.ts` | Markdown → HTML conversion |
| `scripts/copy-to-clipboard.ts` | Copy content to clipboard |
| `scripts/paste-from-clipboard.ts` | Send real paste keystroke |

## Prerequisites

- Google Chrome or Chromium installed
- `bun` installed (for running scripts)
- First run: log in to X in the opened browser window

## References

- **Regular Posts**: See `references/regular-posts.md` for manual workflow, troubleshooting, and technical details
- **X Articles**: See `references/articles.md` for long-form article publishing guide

---

## Regular Posts

Text + up to 4 images.

```bash
# Preview mode (doesn't post)
npx -y bun ${SKILL_DIR}/scripts/x-browser.ts "Hello from Claude!" --image ./screenshot.png

# Actually post
npx -y bun ${SKILL_DIR}/scripts/x-browser.ts "Hello!" --image ./photo.png --submit
```

> **Note**: `${SKILL_DIR}` represents this skill's installation directory. Agent replaces with actual path at runtime.

**Parameters**:
| Parameter | Description |
|-----------|-------------|
| `<text>` | Post content (positional argument) |
| `--image <path>` | Image file path (can be repeated, max 4) |
| `--submit` | Actually post (default: preview only) |
| `--profile <dir>` | Custom Chrome profile directory |

---

## Video Posts

Text + video file (MP4, MOV, WebM).

```bash
# Preview mode (doesn't post)
npx -y bun ${SKILL_DIR}/scripts/x-video.ts "Check out this video!" --video ./clip.mp4

# Actually post
npx -y bun ${SKILL_DIR}/scripts/x-video.ts "Amazing content" --video ./demo.mp4 --submit
```

**Parameters**:
| Parameter | Description |
|-----------|-------------|
| `<text>` | Post content (positional argument) |
| `--video <path>` | Video file path (required) |
| `--submit` | Actually post (default: preview only) |
| `--profile <dir>` | Custom Chrome profile directory |

**Video Limits**:
- Regular accounts: 140 seconds max
- X Premium: up to 60 minutes
- Supported formats: MP4, MOV, WebM
- Processing time: 30-60 seconds depending on file size

---

## Quote Tweets

Quote an existing tweet with your comment - a way to share content while giving credit to the original creator.

```bash
# Preview mode (doesn't post)
npx -y bun ${SKILL_DIR}/scripts/x-quote.ts https://x.com/user/status/123456789 "Great insight!"

# Actually post
npx -y bun ${SKILL_DIR}/scripts/x-quote.ts https://x.com/user/status/123456789 "I agree!" --submit
```

**Parameters**:
| Parameter | Description |
|-----------|-------------|
| `<tweet-url>` | URL of the tweet to quote (positional argument) |
| `<comment>` | Your comment text (positional argument, optional) |
| `--submit` | Actually post (default: preview only) |
| `--profile <dir>` | Custom Chrome profile directory |

---

## X Articles

Long-form Markdown articles (requires X Premium).

```bash
# Preview mode
npx -y bun ${SKILL_DIR}/scripts/x-article.ts article.md

# With cover image
npx -y bun ${SKILL_DIR}/scripts/x-article.ts article.md --cover ./cover.jpg

# Compose and open preview. Final publish is manual.
npx -y bun ${SKILL_DIR}/scripts/x-article.ts article.md
```

**Parameters**:
| Parameter | Description |
|-----------|-------------|
| `<markdown>` | Markdown file path (positional argument) |
| `--cover <path>` | Cover image path |
| `--title <text>` | Override article title |
| `--submit` | Ignored for X Articles; final publish is manual after preview |

**Frontmatter** (optional):
```yaml
---
title: My Article Title
cover_image: /path/to/cover.jpg
---
```

**Default Obsidian cover**:

If no `--cover` is provided, X Articles first checks:

```text
<vault-root>/assets/<markdown-filename-without-.md>/cover.png
```

When that file exists, it is used as the cover and the first inline screenshot remains in the article body.

**Markdown Syntax**:

X Articles supports both standard Markdown and Obsidian wikilink syntax:

| Syntax Type | Format | Example |
|-------------|--------|---------|
| Standard image | `![alt](path)` | `![Photo](./image.jpg)` |
| Obsidian wikilink | `![[path\]\]` | `![[image.png\]\]` |
| Obsidian with alt | `![[path\|alt\]\]` | `![[photo.png|My photo\]\]` |
| Remote images | `![alt](https://...)` or `![[https://...\]\]` | `![[https://example.com/img.png\]\]` |

**Remote Image Download**:

- Remote images (http/https URLs) are automatically downloaded to temp directory
- Supports redirects (301/302) with 30s timeout
- Downloaded files are cached using MD5 hash of URL

---

## Notes

- First run requires manual login (session is saved)
- X Articles stop at preview by design; the account owner clicks final Publish manually
- X Articles treat image placeholders as a hard safety gate: after each image insert, the matching placeholder must disappear; before preview, global `IMAGE_PLACEHOLDER` count must be zero
- Browser remains open after operation for review
- Supports macOS, Linux, and Windows

## Extension Support

Custom configurations via EXTEND.md.

**Check paths** (priority order):
1. `.baoyu-skills/baoyu-post-to-x/EXTEND.md` (project)
2. `~/.baoyu-skills/baoyu-post-to-x/EXTEND.md` (user)

If found, load before workflow. Extension content overrides defaults.


## User-Learned Best Practices & Constraints

> **Auto-Generated Section**: This section is maintained by `skill-evolution-manager`. Do not edit manually.

### User Preferences
- 发布 Obsidian 长文到 X 时，默认要兼容原稿里的内部引用、图片嵌入和尾部 Links。

### Known Fixes & Workarounds
- 兼容 Obsidian 内部引用 [[path|alias]]，生成 HTML 时要退化成普通文字。
- 兼容文章末尾的 ## Links 区块，生成 X 长文时自动去掉。
- 识别到 ![[image.png]] 这类 Obsidian 图片时，要保留为图片占位并走后续替换流程。
- 如果发布过程卡在浏览器交互或连接阶段，汇报时要区分清楚：是内容转换成功但浏览器接管失败，不要笼统说成没发成功。
- X Articles 默认只组稿并打开预览页，不自动点击最终发布。
- 默认优先使用 `assets/<文章文件名>/cover.png` 作为封面，不能把第一张正文截图吞掉当封面。
- 在 macOS / Windows 的中文、空格或 OneDrive 路径下运行时，脚本目录必须通过 `fileURLToPath(import.meta.url)` 解析，避免 URL 编码路径导致剪贴板脚本找不到。
- Windows 下从脚本再调用 Bun 时要走 `npx.cmd`，macOS/Linux 继续用 `npx`。
- X Articles 中文界面的新建入口可能显示为「撰写」或只有 `aria-label="create"`，不要只依赖旧的 `empty_state_button_text` 选择器。
- 正文图片插入必须验证“占位符消失且正文图片数量增加”；如果图片没插入，不要把占位符静默清掉后继续到发布/预览。

### Custom Instruction Injection

当浏览器里已经出现编辑好的文章时，优先说明内容已灌入页面，只是最后的自动提交或连接回执失败。
