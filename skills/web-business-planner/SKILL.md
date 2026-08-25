---
name: web-business-planner
description: "Plan a search-driven Web business from a locked opportunity by researching SERP, alternatives, intent and journey gaps, defining page-level function contracts, and writing a non-cannibalizing page-matrix.json. Use for Web 出海页面规划、SaaS/工具/内容/线索站信息架构、SERP 研究、页面矩阵、一页一意图、primary keyword 归属、页面功能契约；not for opportunity discovery, source-pack collection, page implementation, deployment, or inventing UI fields and actions outside the contract."
---

# Web Business Planner

把已锁定机会拆成有限、互不争抢搜索意图且各自承担明确用户动作的页面集合，并在任何 UI 或代码之前先冻结页面功能契约。

## Dependency And Scope

- 机器契约来自同级必需依赖 `web-business-pipeline`；优先使用 `WEB_BUSINESS_PIPELINE_SKILL_DIR`，其次解析 `../web-business-pipeline` 或项目 `.agents/skills/web-business-pipeline`。
- 写入前必须运行中央 `scripts/pipeline.py status --project-dir <project-dir>` 和 `validate`。依赖不存在、当前状态不匹配或中央校验失败时停止。
- 起点：初次建站为 `candidate_locked`；优化/扩展模式仅由 `$web-business-expander` 在 `grow` 中调用。
- 终点：初次建站进入 `planned`；优化/扩展模式保持 `grow`。
- 本 Skill 所有产物：`page-matrix.json`。不得直接编辑 `pipeline-state.json`；状态只能由中央 CLI 写入。

## Router Rules

- every page owns one primary keyword and one intent key
- normalized aliases do not overlap
- every page has a page-level function contract
- commercial role and next step use only existing page-contract fields
- non-base locales have demand evidence and complete content plans
- 完整全链路或当前阶段不明时，回到 `$web-business-pipeline`；机会发现仍由匹配的上游方法负责，只有 Steam/Roblox 游戏找词才使用 `$game-keyword-radar`。
- 同一项目同一时间只允许一个阶段 Skill 写产物；发现上游契约错误时停止并交回总编排器。

## Compact Workflow

1. 运行中央 `status` 和 `validate`。初次模式只接受 `candidate_locked`；优化/扩展模式必须由 `$web-business-expander` 明确传入当前 `grow` 变更批次及 `optimize-existing`/`expand-new` 模式。
2. 围绕锁定机会与目标客户做只读 SERP、替代方案和竞品研究，记录 query、地区/语言、检查时间、结果 URL、页面类型、搜索意图和未满足需求。机会地图同时检查关键词覆盖、页面/工具缺口、信任差距、承接差距和价值事件路径；竞品只用于信息架构判断，不复制文案、品牌或视觉。
3. 先为每页写功能契约，并用现有 `page_type`、`search_intent`、`user_goal`、`allowed_actions` 和 `non_goals` 表达 discovery、utility 或 commercial-support 角色及允许的下一步。契约没有的字段、按钮、状态、卡片或导航不得进入后续原型和实现；没有真实产品、合法去向和需求证据时，不得为了商业化发明 CTA、价格、支付、下载或 Affiliate 链接。
4. 写 `page-matrix.json`：每页一个稳定 `page_id`、唯一 `primary_keyword`、别名、`intent_key`、locale 和 search intent。规范化后主词、别名或 intent key 冲突时合并或重划，不继续。
5. 基础语言外的 locale 必须有独立需求证据和完整内容计划；翻译能力或模板可用不算需求。
6. 初次模式运行 `gate --target planned`，通过后才 `transition --to planned`。优化/扩展模式只运行 `validate --stage planned` 并把结果交回 expander，不改状态；现有页必须沿用稳定 `page_id`，新增页才创建新 ID。

中央命令形态：

```bash
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" status --project-dir <project-dir>
python3 "$WEB_BUSINESS_PIPELINE_SKILL_DIR/scripts/pipeline.py" validate --project-dir <project-dir>
```

## Output Contract

- 可追溯 SERP/竞品意图摘要
- 页面级功能契约
- 用现有字段表达的页面意图/承接角色，不新增 Schema 字段或虚构商业动作
- 无关键词蚕食的 page-matrix.json
- planned gate 或 optimization/expansion validation 结果
- 最终回复分开列出：已验证事实、推断、人工决定、missing evidence、当前状态和下一阶段。
- 文件存在、模型判断、计划执行或授权记录都不能冒充 gate 通过、真实执行或线上回读。

## Write And Action Boundary

- 只写页面矩阵及用户明确要求的本地规划说明。
- 不修改候选锁、证据包、页面实现、状态文件或远端系统。
- 研究是只读；登录、验证码、付费墙或不可控页面出现时停止并报告。
- 网络：read-only public SERP and competitor research through an available approved browser/web tool。
- 交互：required when page scope or locale choice materially branches the product。
- 临时日志、缓存和浏览器会话不得写进站点项目、Skill 目录或 Obsidian vault。

## Non-goals

- 批量抓取或复制竞品内容
- 在功能契约之外发明 UI 元素
- 因为模板能生成就增加语言或页面
