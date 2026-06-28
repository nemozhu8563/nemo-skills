---
name: publish-article
description: 文章发布闭环助手。用于文章已经发布、创建公众号草稿后需要回写本地状态、补齐 AI_Media operations.md、记录发布 URL、发布时间、渠道、资产、复盘和后续数据快照待办。触发场景包括“这篇文章已经发布了”“补一下发布状态”“把公众号链接写回本地”“闭合 operations.md”“发布后归档”等。
---

# Publish Article

这个技能负责发布后的本地状态闭环，不负责实际发布到平台。真正上传到微信公众号时使用 `wechat-publisher`；发布完成或拿到平台链接以后，再用本技能补齐 vault 里的状态。

## 判断对象

优先判断文章属于哪种结构：

1. **新 AI_Media Topic**：目录形态为 `04_Projects/AI_Media/<topic>/`，包含 `topic.md`、`materials.md`、`content.md`、`operations.md`，也可能有 `content-*.md` 变体。
2. **历史文章**：旧目录或旧单文件仍使用 `published_article`、`publish_date`、`published_url`、`channel` 等字段。

新 AI_Media Topic 必须以 `operations.md` 作为发布事实主记录。不要把 `published_url`、`views`、`likes`、`channel` 这类发布字段继续扩散到 `content.md` 或 `topic.md` frontmatter。

## 必要输入

如果用户没有提供，先询问缺失项：

- 已发布或已创建草稿的文件路径。
- 发布平台：`wechat` / `zhihu` / `x` / 其他。
- 发布状态：`drafted` / `published` / `skipped`。
- 最终标题。
- 发布 URL 或草稿标识；没有公开 URL 时说明原因。
- 发布时间，默认使用当前日期。
- 数据来源：例如 `wechat-publisher`、`manual_public_page`、`public_link`、`wechat_mp_screenshot`。

## 新 AI_Media Topic 闭环

当目标文件位于 `04_Projects/AI_Media/<topic>/` 下时：

1. 找到同目录 `operations.md`；如果缺失，先报告缺失，不要凭空改写其他文件充当替代。
2. 在 `operations.md` 的“发布记录”表中找到对应平台行：
   - 将状态从 `planned` 改为 `published` 或 `drafted`。
   - 补齐最终标题、URL、发布时间和数据来源。
   - 如果表中没有该平台行，按既有表头新增一行。
3. 更新 `operations.md` frontmatter：
   - `status: tracking`，除非所有复盘和回写都已经完成，才可改为 `closed`。
   - `updated: <YYYY-MM-DD>`。
   - `platforms` 包含实际发布平台。
   - `review_status` 缺失时设为 `pending`。
   - `writeback_status` 缺失时设为 `pending`；如果已经完成部分 skill、系统规则或资产回写，可设为 `partial`。
4. 将实际使用的封面和正文配图写入 `asset_refs`，保持已有条目，不重复。
5. 将质检、改稿复盘、skill 回写记录或 workflow issue 写入 `review_refs`，保持已有条目，不重复。
6. 在“回写项”中保留后续任务：
   - T+24h 数据快照。
   - T+72h 数据快照。
   - T+7d 数据快照。
   - 需要回写 `03_Notes`、`80_Assets` 或系统规则的事项。
7. 如果实际发布的是 `content-*.md` 变体，可以在该变体 frontmatter 保留：
   - `status: published`
   - `published_at: <YYYY-MM-DD>`
   - `<platform>_url: <URL>`
   但这只是变体状态，发布事实仍以 `operations.md` 为主。

## 历史文章兼容

只有在目标不是新 AI_Media Topic 时，才使用旧字段：

| 字段 | 更新规则 |
| --- | --- |
| `type` | 可保留或改为 `published_article`，以原文件结构为准 |
| `status` | 改为 `published` / `已发布` / `已完成`，匹配原文件语言 |
| `publish_date` | 当前日期或用户指定日期 |
| `published_url` | 平台 URL |
| `channel` | 发布渠道 |

不要把历史兼容字段迁回新 Topic 模板。

## 完成标准

完成后检查：

- `operations.md` 发布记录能追溯到平台 URL 或草稿标识。
- 对应平台状态不再停在 `planned`。
- `operations.md` frontmatter 至少进入 `tracking`。
- 已发布正文或变体的状态与 `operations.md` 不冲突。
- 数据快照、复盘和回写待办没有丢失。

## 示例

用户：

```text
这篇公众号已经发布了：https://mp.weixin.qq.com/s/xxx
文件是 04_Projects/AI_Media/某个选题/content-nemo-writer-v2.md
```

助手应执行：

```text
1. 读取同目录 operations.md。
2. 将公众号行改成 published，写入最终标题、URL、发布时间和数据来源。
3. 将 operations.md status 改为 tracking。
4. 补 asset_refs / review_refs / 数据快照待办。
5. 如果 content-nemo-writer-v2.md 还没有发布状态，再补 status、published_at、wechat_url。
```

不要只改正文 frontmatter 后就结束。
