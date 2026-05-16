# Migration Inventory

This inventory is the execution gate for publishing nemo-managed skills into the vault-local `.agents/skills` entrypoint. Only `migrate_now` entries are eligible for publish. `delete`, `archive`, `merge`, `pending_user_decision`, and other non-publish states must not be selected by publish scripts.

| Item | Type | Mapping status | Retention decision | Notes |
| --- | --- | --- | --- | --- |
| `article-clip-obsidian` | `skill_dir` | `migrate_now` | `keep` | Obsidian 剪藏入库主链路 |
| `article-illustrate` | `skill_dir` | `migrate_now` | `keep` | 文章视觉统一入口，调度封面和正文插图 |
| `article-review` | `skill_dir` | `delete` | `delete` | 由 dbs-ai-check 替代，不再发布 |
| `baoyu-article-illustrator` | `skill_dir` | `migrate_now` | `provider` | article-illustrate 的正文插图子 skill |
| `baoyu-comic` | `skill_dir` | `delete` | `delete` | 用户已确认删除，不再发布 |
| `baoyu-compress-image` | `skill_dir` | `delete` | `delete` | 用户已确认删除，不再发布 |
| `baoyu-cover-image` | `skill_dir` | `migrate_now` | `provider` | article-illustrate 的封面图子 skill |
| `baoyu-danger-gemini-web` | `skill_dir` | `delete` | `delete` | 废弃高风险 Gemini Web 渠道，不再发布 |
| `baoyu-danger-x-to-markdown` | `skill_dir` | `delete` | `delete` | 用户已确认删除，不再发布 |
| `baoyu-image-gen` | `skill_dir` | `migrate_now` | `keep` | 普通图片生成主入口/router |
| `baoyu-infographic` | `skill_dir` | `migrate_now` | `keep` | 信息图独立入口 |
| `baoyu-post-to-x` | `skill_dir` | `migrate_now` | `keep` | X / X Articles 发布链路 |
| `baoyu-slide-deck` | `skill_dir` | `delete` | `delete` | 用户已确认删除，不再发布 |
| `baoyu-translate` | `skill_dir` | `migrate_now` | `keep` | 文档翻译/本地化入口 |
| `baoyu-url-to-markdown` | `skill_dir` | `migrate_now` | `keep` | 普通网页转 Markdown，不承担 Obsidian 入库 |
| `baoyu-xhs-images` | `skill_dir` | `archive` | `archive` | 不进入本轮 .agents 发布目标，保留历史删除状态 |
| `bullet-viral-post` | `skill_dir` | `pending_user_decision` | `pending_user_decision` | 暂不发布，等待后续确认 |
| `content-reviewer` | `skill_dir` | `delete` | `delete` | 由 dbs-ai-check 替代，不再发布 |
| `decompose-article` | `skill_dir` | `delete` | `delete` | 用户已确认删除，不再发布 |
| `humanizer-zh` | `skill_dir` | `delete` | `delete` | 由 dbs-ai-check 替代，不再发布 |
| `idea-spark` | `skill_dir` | `delete` | `delete` | 用户已确认删除，不再发布 |
| `inbox-processor` | `skill_dir` | `delete` | `delete` | 用户已确认删除，不再发布 |
| `interdisciplinary-research` | `skill_dir` | `migrate_now` | `keep` | 跨学科研究方法和信源约束 |
| `json-canvas` | `skill_dir` | `migrate_now` | `keep` | Obsidian Canvas 创建和编辑 |
| `kie-image-gen` | `skill_dir` | `migrate_now` | `provider` | kie.ai / Nano Banana 图像 provider |
| `llm-wiki` | `skill_dir` | `migrate_now` | `keep` | 知识库吸收和治理总入口 |
| `llm-wiki-bootstrap` | `skill_dir` | `migrate_now` | `keep` | domain 初始化批量吸收 |
| `llm-wiki-ingest` | `skill_dir` | `migrate_now` | `keep` | 单篇 source/clipping/conversation 吸收 |
| `llm-wiki-query-writeback` | `skill_dir` | `migrate_now` | `keep` | 知识库问答和稳定判断回写 |
| `llm-wiki-weekly-lint` | `skill_dir` | `migrate_now` | `keep` | 周期性知识质量检查 |
| `markitdown-client` | `skill_dir` | `delete` | `delete` | 当前不用它做 Obsidian 适配链路 |
| `nemo-writer` | `skill_dir` | `migrate_now` | `keep` | 中文长文写作唯一主入口 |
| `obsidian-archive` | `skill_dir` | `delete` | `delete` | 旧文章检查职责改由只读脚本承接 |
| `obsidian-bases` | `skill_dir` | `migrate_now` | `keep` | Obsidian Bases 官方 skill |
| `obsidian-markdown` | `skill_dir` | `migrate_now` | `keep` | Obsidian Markdown 官方 skill |
| `publish-article` | `skill_dir` | `migrate_now` | `keep` | 发布后归档和 frontmatter 更新 |
| `tryvalo-imagegen` | `skill_dir` | `migrate_now` | `provider` | TryValo/new-api/gpt-image-2 图像 provider |
| `wechat-article-writer` | `skill_dir` | `delete` | `delete` | 旧公众号文章工作流已退役，不并入 nemo-writer |
| `wechat-publisher` | `skill_dir` | `migrate_now` | `keep` | Markdown 发布到微信公众号草稿箱 |
| `writing-clone` | `skill_dir` | `delete` | `delete` | 旧素材池初稿工作流已退役，不并入 nemo-writer |
| `zhihu-collection-sync` | `skill_dir` | `migrate_now` | `keep` | 批量同步知乎收藏并复用剪藏链路 |
